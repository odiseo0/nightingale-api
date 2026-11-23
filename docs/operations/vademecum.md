# Importación administrativa del vademecum

**Alcance:** carga local/administrativa del release definido por D20. No es un endpoint, no forma parte del arranque y no acredita despliegue, revisión profesional o consumo por el escritorio.

## Precondiciones

- PostgreSQL Test o la base administrativa elegida tiene aplicada la migración `20261122_01` o posterior.
- El proceso usa `VADEMECUM_IMPORT_DATABASE_URI` con una identidad administrativa que puede escribir las cinco tablas `vademecum_*`. No uses la identidad `nightingale_app` del runtime: esta solo tiene SELECT.
- La fuente es `vademecum/vademecum_venezuela_2026-11-03.json`. No se importan productos históricos ni evidencia suplementaria.

## Comando

Desde la raíz, con la URI administrativa ya presente en el entorno y sin escribirla en archivos o logs:

```bash
./.venv/Scripts/python.exe scripts/import_vademecum.py --file vademecum/vademecum_venezuela_2026-11-03.json
```

El proceso valida todo el contenido y las estadísticas antes de abrir la escritura. Después inserta por lotes y activa el release en la misma transacción. Un error revierte inserciones y cambio de release activo.

La salida JSON incluye `datasetId`, `sourceSha256`, `products`, `monographs` y `status=imported|existing`. Repetir exactamente los mismos bytes devuelve `existing` y no cambia datos ni activación. Si el resultado de conexión es desconocido, consulta el release por huella antes de repetir; no cambies la fuente para forzar otra carga.

`VALIDATION_ERROR` indica JSON/modelo, duplicados, referencias o estadísticas inválidas. URI ausente/inválida, archivo ilegible y fallo de base terminan con código 2 y sin mostrar credenciales. Los releases anteriores se conservan; esta versión no tiene retención ni administración HTTP.

## Comprobación aislada

```bash
./.venv/Scripts/python.exe test-support/vademecum/check.py
```

El probe usa PostgreSQL Test y Keycloak Test, crea una base aleatoria y la elimina al terminar. No usa SQLite ni datos de pacientes. Los resultados reales y límites se registran en la tarea del plan.
