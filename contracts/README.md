# Contratos de API v1

Fuente ejecutable: `src.application:app` y los modelos de `src/api/*/domain`, con la base de `src/core/schema`. El [contrato explicado](../docs/api-v1.md) conserva permisos y reglas de uso; no es otra fuente editable de los esquemas.

Los JSON de `api-v1/` son generados. No editarlos a mano:

```powershell
uv run --locked python -m scripts.export_contracts
uv run --locked python -m scripts.export_contracts --check
```

El exportador no conecta a PostgreSQL, no abre OIDC, no carga `.env` local y no arranca el listener. Usa una URI ficticia no accesible solo para importar la app existente. El campo `x-generated` identifica origen, versión, HEAD y SHA-256 del código/manifiesto/lock/exportador con saltos de línea normalizados. `manifest.json` conserva las huellas de los cinco artefactos y sus conteos. Un cambio de fuente exige volver a exportar; `--check` detecta copias antiguas.

- `openapi.json`: rutas y modelos HTTP reales; salud incluida y respuesta SSE descrita como `text/event-stream`.
- `public-models.schema.json`: catálogo `$defs` con los modelos HTTP, extraídos del OpenAPI y referencias locales ajustadas. El consumidor elige `#/$defs/<nombre>`; no representa una raíz que acepte todo el protocolo.
- `accepted-operations.schema.json`: envoltorio y los 42 payloads conocidos de operaciones por lote. Describe entradas válidas para esas acciones; no sustituye reglas de negocio ni permisos. El servidor recibe también payloads inválidos o acciones desconocidas para devolver su rechazo idempotente, como explica OpenAPI. AcceptInvitation usa su ruta propia.
- `sse.schema.json`: representación lógica de los avisos; el transporte usa los campos SSE event/id/retry/data, no el JSON completo de ese modelo como un único data.
- `capabilities.json`: capacidades públicas y vínculo de cada acción con su modelo de código, sin datos de cuentas.

`examples.json` es una fuente de ejemplos ficticios, no un artefacto generado. El cliente de prueba sustituye `{{deviceId}}` por el ID que acaba de emitir API y envía los demás objetos tal como están. El mismo ID de operación se conserva al reintentar. Los UUID fijos pertenecen solo a cada base de prueba nueva.

Guía de consumo y límites: [Rust](../docs/rust-api-guide.md). Comprobación real de los ejemplos:

```powershell
.\.venv\Scripts\python.exe test-support/contracts/check.py
```

Los paquetes Python no incluyen estos contratos como una segunda fuente. Esta entrega no genera un cliente Rust ni acredita su uso en el escritorio o Hub. Los JSON y la guía se revisan aquí antes de compartirlos con los consumidores.
