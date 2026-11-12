-- Ejecutar en SQL*Plus sobre el esquema dedicado PHARMA_S14 después de V4.
-- Las ventas sintéticas carecen de detalle. Úsalas únicamente para medir listados.
whenever sqlerror exit sql.sqlcode rollback
set serveroutput on

declare
    categoria_prueba number;
    cliente_prueba number;
    productos_insertados number;
    ventas_insertadas number;
begin
    if sys_context('USERENV', 'SESSION_USER') <> 'PHARMA_S14'
        or sys_context('USERENV', 'CURRENT_SCHEMA') <> 'PHARMA_S14' then
        raise_application_error(-20014, 'Usa el esquema de laboratorio PHARMA_S14.');
    end if;

    select min(id) into categoria_prueba from categorias;
    select min(id) into cliente_prueba from clientes;
    if categoria_prueba is null or cliente_prueba is null then
        raise_application_error(-20015, 'Crea una categoría y un cliente sintético en el esquema.');
    end if;

    insert into productos (nombre, precio, stock, estado, categoria_id, fecha_creacion, creado_por)
    select 'S14 volumen ' || lpad(n, 5, '0'), round(dbms_random.value(1, 200), 2),
           trunc(dbms_random.value(0, 500)), true, categoria_prueba, systimestamp, 's14-volumen'
    from (select level as n from dual connect by level <= 5000) serie
    where not exists (
        select 1 from productos p where p.nombre = 'S14 volumen ' || lpad(serie.n, 5, '0')
    );
    productos_insertados := sql%rowcount;

    insert into ventas (fecha, total, estado, cliente_id, creado_por)
    select systimestamp - numtodsinterval(serie.n / 55, 'DAY'), round(dbms_random.value(5, 500), 2),
           'REGISTRADA', cliente_prueba, 's14-volumen'
    from (
        select level as n from dual connect by level <= 20000
    ) serie
    cross join (select count(*) cantidad from ventas where creado_por = 's14-volumen') carga
    where serie.n > carga.cantidad;
    ventas_insertadas := sql%rowcount;

    dbms_output.put_line('Productos insertados: ' || productos_insertados);
    dbms_output.put_line('Ventas insertadas: ' || ventas_insertadas);
end;
/
commit;
