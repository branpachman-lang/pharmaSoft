from pathlib import Path
root = Path(__file__).resolve().parents[3]
backend = (root / 'PharmaBackend/README.md').read_text(encoding='utf-8')
common = backend[backend.index('## Despliegue en producción'):backend.index('## Actividad autónoma S13')]
intro = '''# PharmaFrontend

SPA de PharmaSoft con Angular 22.2. Las dependencias están fijadas en package-lock.json.

## Desarrollo y verificación

Ejecutar `npm ci`, `npm start` (puerto 4200), `npm test -- --watch=false` y `npm run build -- --stats-json`.

'''
end = '''
### Construcción y publicación de la SPA

1. Ejecutar `npm ci` y `npm run build -- --stats-json`. Se genera `dist/pharma-frontend/browser/`. El API de producción usa `/api/v1`, del mismo origen. `environment.ts` se integra al compilar y no cambia mediante variables de Docker. No poner secretos en Angular.
2. Prueba local: `docker compose -f deploy/docker-compose.yml up -d`; Nginx publica 8081. Backend y Oracle se arrancan por separado. El alias backend apunta al anfitrión de Docker Desktop.
3. Producción: copiar los archivos a un directorio de release, conservar los chunks anteriores y activar el nuevo index.html al final mediante cambio atómico del directorio vigente. El volumen de dist usado en la práctica permite la simulación sin detener Nginx, pero no garantiza un despliegue atómico.
4. Comprobar encabezados de index.html, main y CSS con `curl -I`; navegar a Productos y Ventas; comprobar que un error muestra Código de seguimiento.
5. Reversión: reactivar el directorio de release anterior completo, conservar archivos con hash usados por pestañas abiertas y validar que el contrato de API siga siendo compatible. No borrar la caché del navegador como procedimiento de despliegue.

Variables de infraestructura de la SPA: el compose actual no tiene variables obligatorias. Puerto 8081, alias backend:8080 y rutas de volúmenes se configuran en deploy/docker-compose.yml; el nombre de dominio y TLS se configuran en Nginx. Las variables del backend de la tabla anterior pertenecen únicamente al proceso de Java.

## Actividad autónoma S13

Se conserva la carga sin precarga global como decisión basada en las mediciones del informe. MainLayout se descarga al acceder a la zona autenticada. Los errores leen requestId del cuerpo y, como alternativa, de X-Request-Id. Informe: repositorio PharmaBackend, docs/informe-s13.pdf.
'''
(root / 'pharma-frontend/README.md').write_text(intro + common + end, encoding='utf-8')
(root / 'pharma-frontend/docs/s13/solicitud-incorporacion.md').write_text('''Título: perf(spa): diferir diseño autenticado y mostrar seguimiento de errores

Destino: develop. Origen: feature/optimizacion-produccion-pacho.

MainLayout se carga al acceder a la zona autenticada, reduciendo el Initial total de 313,59 kB a 305,78 kB. Los errores muestran el requestId recibido del backend para facilitar la atención de soporte.

Incluye guía de despliegue, puertos, variables, reversión y recomendaciones para tres locales. Se midieron cinco navegaciones por variante de precarga y se mantiene la carga bajo demanda.

Validación: 51 pruebas del frontend aprobadas y compilaciones de producción con estadísticas. Evidencias e informe en el backend. Revisar y añadir por separado el trabajo previo del frontend que aún no está confirmado.
''', encoding='utf-8')
