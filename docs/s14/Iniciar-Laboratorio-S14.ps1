param([ValidateRange(1, 240)][int]$ExpiracionMinutos = 30)

$ErrorActionPreference = 'Stop'
$lab = $PSScriptRoot
$backend = (Resolve-Path -LiteralPath (Join-Path $lab '../..')).Path
$frontend = Join-Path (Split-Path -Parent $backend) 'pharma-frontend'
$evidencia = Join-Path $lab ('laboratorio-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $evidencia -Force | Out-Null
$java = 'C:/Users/USUARIO/.jdks/ms-21.0.12.1/bin/java.exe'
$jar = (Resolve-Path -LiteralPath (Join-Path $backend 'target/PharmaBackend-0.0.1-SNAPSHOT.jar')).Path
$redis = 'pharmasoft-s14-redis'
$nginx = 'pharmasoft-s14-web'
$api = 'http://127.0.0.1:18084'
$base = 'http://127.0.0.1:18085'
$proceso = $null
$redisId = $null
$nginxId = $null
$variables = @('DB_URL','DB_USERNAME','DB_PASSWORD','JWT_SECRET','S14_LAB_LOGIN','S14_BASE_URL','S14_BROWSER_CHANNEL')
$anteriores = @{}
foreach ($variable in $variables) { $anteriores[$variable] = [Environment]::GetEnvironmentVariable($variable, 'Process') }

try {
    foreach ($puerto in @(18084, 18085, 16384)) {
        if (Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue) { throw "Puerto $puerto ocupado." }
    }
    $env:DB_URL = 'jdbc:oracle:thin:@//127.0.0.1:1522/FREEPDB1'
    $env:DB_USERNAME = 'PHARMA_S14'
    $env:DB_PASSWORD = 'S14a_' + [Guid]::NewGuid().ToString('N')
    $clave = Read-Host 'Elige una clave temporal para los tres usuarios S14' -AsSecureString
    try {
        $env:S14_LAB_LOGIN = [System.Net.NetworkCredential]::new('', $clave).Password
    } finally {
        $clave.Dispose()
    }
    if ([string]::IsNullOrWhiteSpace($env:S14_LAB_LOGIN) -or
        [Text.Encoding]::UTF8.GetByteCount($env:S14_LAB_LOGIN) -gt 72) {
        throw 'Escribe una clave de 1 a 72 bytes.'
    }
    $bytesJwt = New-Object byte[] 32
    $generador = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generador.GetBytes($bytesJwt)
        $env:JWT_SECRET = [Convert]::ToBase64String($bytesJwt)
    } finally {
        $generador.Dispose()
        [Array]::Clear($bytesJwt, 0, $bytesJwt.Length)
    }
    $env:S14_BASE_URL = $base
    $env:S14_BROWSER_CHANNEL = 'chrome'

    $crypto = Get-ChildItem 'C:/Users/USUARIO/.m2/repository/org/springframework/security/spring-security-crypto' -Recurse -File -Filter '*.jar' |
        Where-Object Name -NotMatch 'sources|javadoc' | Select-Object -Last 1
    $commons = Get-ChildItem 'C:/Users/USUARIO/.m2/repository/commons-logging/commons-logging' -Recurse -File -Filter '*.jar' |
        Where-Object Name -NotMatch 'sources|javadoc' | Select-Object -Last 1
    try {
        $hash = & $java -cp "$($crypto.FullName);$($commons.FullName)" (Join-Path $lab 'HashLaboratorio.java')
        if ($LASTEXITCODE -or $hash -notmatch '^\$2[aby]\$\d\d\$[./a-zA-Z0-9]{53}$') { throw 'Falló el hash sintético.' }
    } finally {
        Remove-Item Env:S14_LAB_LOGIN -ErrorAction SilentlyContinue
    }

    $usuarios = @(
        @{ nombre = 'admin_s14'; dni = '00001402'; cargo = 'Administrador'; rol = 'ADMIN' },
        @{ nombre = 'vendedor_s14'; dni = '00001403'; cargo = 'Vendedor'; rol = 'VENDEDOR' },
        @{ nombre = 'almacen_s14'; dni = '00001404'; cargo = 'Almacenero'; rol = 'ALMACENERO' }
    )
    $alta = foreach ($usuario in $usuarios) {
        $nombre = $usuario.nombre
        $dni = $usuario.dni
        $cargo = $usuario.cargo
        $rol = $usuario.rol
        @"
insert into roles (nombre) select '$rol' from dual where not exists (select 1 from roles where nombre='$rol');
insert into empleados (dni,nombres,apellidos,cargo,email,estado,fecha_creacion)
select '$dni','$cargo','Sintetico S14','$cargo','$nombre@example.invalid',true,systimestamp from dual
where not exists (select 1 from empleados where dni='$dni');
merge into usuarios u using (select id from empleados where dni='$dni') e on (u.username='$nombre')
when matched then update set u.password='$hash'
when not matched then insert (username,password,estado,empleado_id,fecha_creacion)
values ('$nombre','$hash',true,e.id,systimestamp);
insert into usuario_roles (usuario_id,rol_id)
select u.id,r.id from usuarios u cross join roles r where u.username='$nombre' and r.nombre='$rol'
and not exists (select 1 from usuario_roles ur where ur.usuario_id=u.id and ur.rol_id=r.id);
"@
    }
    $sql = @"
whenever sqlerror exit sql.sqlcode rollback
alter session set container=FREEPDB1;
alter user PHARMA_S14 identified by "$env:DB_PASSWORD";
connect PHARMA_S14/"$env:DB_PASSWORD"@//127.0.0.1:1521/FREEPDB1
$($alta -join "`n")
commit;
exit
"@
    $resultado = $sql | docker exec -i oracle-local sqlplus -s / as sysdba 2>&1
    if ($LASTEXITCODE -or ($resultado -match 'ORA-\d+|SP2-\d+')) {
        $codigos = [regex]::Matches(($resultado -join ' '), '(?:ORA|SP2)-\d+') | ForEach-Object Value
        throw ('Falló la preparación de las cuentas sintéticas: ' + ($codigos -join ', '))
    }

    $redisId = docker run --pull never --rm -d --name $redis -p '127.0.0.1:16384:6379' redis:7-alpine
    if ($LASTEXITCODE -or $redisId -notmatch '^[a-f0-9]{64}$') { throw 'Falló Redis de laboratorio.' }
    $argsJava = @('-jar', ('"' + $jar + '"'), '--spring.profiles.active=prod',
        '--server.address=0.0.0.0', '--server.port=18084', '--spring.data.redis.port=16384',
        '--spring.data.redis.host=127.0.0.1', '--spring.flyway.enabled=true',
        '--logging.level.org.flywaydb=INFO', '--spring.jpa.show-sql=false',
        "--app.cors.allowed-origins=$base", "--app.jwt.expiracion-minutos=$ExpiracionMinutos")
    $proceso = Start-Process -FilePath $java -ArgumentList $argsJava -WindowStyle Hidden -PassThru `
        -WorkingDirectory $evidencia -RedirectStandardOutput (Join-Path $evidencia 'backend.log') `
        -RedirectStandardError (Join-Path $evidencia 'backend-error.log')
    $salud = $null
    for ($intento = 0; $intento -lt 50; $intento++) {
        if ($proceso.HasExited) { throw 'El backend se cerró durante el arranque.' }
        try {
            $salud = Invoke-RestMethod "$api/actuator/health" -TimeoutSec 2
            if ($salud.status -eq 'UP') { break }
        } catch { }
        Start-Sleep -Seconds 1
    }
    if ($salud.status -ne 'UP') { throw 'El backend no alcanzó el estado UP.' }
    $compilacion = (Resolve-Path -LiteralPath (Join-Path $frontend 'dist/pharma-frontend/browser')).Path
    $conf = Join-Path $evidencia 'nginx.conf'
    $configNginx = (Get-Content -Raw -LiteralPath (Join-Path $frontend 'deploy/nginx.conf')).Replace(
        'host.docker.internal:8080','host.docker.internal:18084')
    [IO.File]::WriteAllText($conf, $configNginx, [Text.UTF8Encoding]::new($false))
    $nginxId = docker run --pull never --rm -d --name $nginx -p '127.0.0.1:18085:80' `
        --mount "type=bind,source=$compilacion,target=/usr/share/nginx/html,readonly" `
        --mount "type=bind,source=$conf,target=/etc/nginx/conf.d/default.conf,readonly" nginx:1.27-alpine
    if ($LASTEXITCODE -or $nginxId -notmatch '^[a-f0-9]{64}$') { throw 'Falló Nginx de laboratorio.' }
    $redisPing = docker exec $redis redis-cli ping
    $web = Invoke-WebRequest "$base/ventas" -TimeoutSec 8 -UseBasicParsing
    if ($redisPing -ne 'PONG' -or $web.StatusCode -ne 200) { throw 'Falló la comprobación de Redis o Nginx.' }
    Write-Output "PharmaSoft: $base"
    Write-Output "Backend: $api/actuator/health"
    Write-Output 'Oracle PHARMA_S14 · backend UP · Redis PONG · SPA HTTP 200'
    Write-Output 'Usuarios de ensayo: admin_s14, vendedor_s14 y almacen_s14.'
    Write-Output "Registro de acceso: $(Join-Path $evidencia 'backend.log')"
    Read-Host 'Deja esta terminal abierta. Pulsa Enter aquí para detener el laboratorio' | Out-Null
} finally {
    if ($nginxId -match '^[a-f0-9]{64}$') { docker stop $nginxId | Out-Null }
    if ($null -ne $proceso -and -not $proceso.HasExited) { Stop-Process -Id $proceso.Id }
    if ($redisId -match '^[a-f0-9]{64}$') { docker stop $redisId | Out-Null }
    foreach ($variable in $variables) { [Environment]::SetEnvironmentVariable($variable, $anteriores[$variable], 'Process') }
}
