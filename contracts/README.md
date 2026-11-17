# Contratos generados de Nightingale API

Origen editable: esquemas Pydantic de `src/api/*/domain` y `src.application:app`. Generador: `scripts/export_contracts.py`. Revisión: **api-v1.3**, contrato remoto **1**. No editar `api-v1/` a mano.

## Generar y comprobar

```powershell
.\.venv\Scripts\python.exe -m scripts.export_contracts
.\.venv\Scripts\python.exe -m scripts.export_contracts --check
.\.venv\Scripts\python.exe -m scripts.export_contracts --output .tmp/contracts-review
.\.venv\Scripts\python.exe test-support/contracts/check.py
```

`--output` permite una ruta explícita dentro del repositorio para revisar sin sustituir los artefactos publicados. El manifiesto conserva origen, revisión, HEAD y huellas de código y archivos. Los recuentos proceden del catálogo real, no de cifras fijas.

## Contenido

- `api-v1/openapi.json`: rutas y modelos HTTP reales.
- `api-v1/nightingale-api.md`: especificación portable y guía de consumo para el escritorio; documento fuente, no JSON generado.
- `api-v1/public-models.schema.json`: definiciones y referencias locales.
- `api-v1/accepted-operations.schema.json`: envoltura y payloads del catálogo actual.
- `api-v1/sse.schema.json`: eventos SSE.
- `api-v1/capabilities.json`: acciones, acciones online y límites.
- `api-v1/manifest.json`: origen, revisión y huellas.
- `examples.json`: solicitudes ficticias comprobadas con cliente ASGI, PostgreSQL y Keycloak Test.

La [guía Rust](../docs/rust-api-guide.md) explica consumo, recuperación y límites. No acredita un cliente Rust/Hub, una integración externa ni producción.
