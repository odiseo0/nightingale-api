# Estado y evidencia

**Plan:** [P-20261021-01-api-foundation](plan.md). **Estado:** In progress. **Usuario:** autorizó continuar tras corregir las anotaciones; T04 en curso.

## Tareas

| ID | Estado | Evidencia / condición |
|---|---|---|
| T01 | Done | Comprobaciones documentales realizadas; evidencia histórica en `docs/sources.md` |
| T02 | Done | Alcance acotado a herramientas de proceso ya elegidas por el usuario, versiones/lockfile comprobados; entorno PostgreSQL O08 aplazado hasta antes de T07 |
| T03 | Done | Base y corrección de anotaciones comprobadas; el usuario autorizó continuar. Evidencia en `docs/operations/development.md` |
| T04 | In progress | OIDC externo y permisos vigentes confirmados; propuestas de sesiones, dispositivos y Hub en `docs/access-design.md`. O01/O02 aún parciales |
| T05 | Todo | Depende de T04; contrato, cursor, recuperación y compatibilidad |
| T06 | Todo | Depende de T04; reglas administrativas y estados |
| T07 | Todo | Espera C04; persistencia técnica |
| T08 | Todo | Depende de T07; autorización/aislamiento |
| T09 | Todo | Espera C05; pacientes |
| T10 | Todo | Depende de T09; servicios |
| T11 | Todo | Depende de T10; agenda |
| T12 | Todo | Espera C06; citas/aceptación |
| T13 | Todo | Depende de T12; descarga/recuperación |
| T14 | Todo | Depende de T13; fallos y concurrencia |
| T15 | Todo | Espera C07; adaptación al Hub |
| T16 | Todo | Espera C08; trabajo duradero |
| T17 | Todo | Depende de T16; recordatorios/entregas |
| T18 | Todo | Depende de T17; webhooks/n8n |
| T19 | Todo | Espera C09; acuerdo de lista de espera |
| T20 | Todo | Espera C10; lista de espera |
| T21 | Todo | Depende de T20; indicadores |
| T22 | Todo | Depende de T21; operación/restauración |
| T23 | Todo | Espera C11; integración/aceptación |

## Revisión del usuario

- [x] C01 — el usuario autorizó comenzar la fundación el 2026-10-21.
- [x] C02 — habilitación para las herramientas de proceso añadidas por el usuario; PostgreSQL de prueba sigue en O08, sin aprobación de esquema.
- [x] C03 — el usuario pidió corregir AsyncIterator en contextos asíncronos y autorizó continuar; corrección y pruebas realizadas.
- [ ] C04 — acuerdos previos de acceso, sync y dominio.
- [ ] C05 — persistencia técnica y aislamiento.
- [ ] C06 — pacientes, servicios y agenda.
- [ ] C07 — citas, sync y pruebas concurrentes.
- [ ] C08 — contrato/adaptador del Hub.
- [ ] C09 — workers e integraciones.
- [ ] C10 — acuerdo de lista de espera.
- [ ] C11 — lista de espera, indicadores y operación.
- [ ] C12 — aceptación de versión y cierre.

## Registro de comprobaciones

- 2026-10-21: inspección inicial sin `.git`, código ni manifiestos; el usuario añadió `docs/nightingale-api.md` como fuente de alcance.
- 2026-10-21: lectura de fuentes actuales del escritorio y copia local de Free-Win Orders; véase [procedencia](../../docs/sources.md).
- 2026-10-21: inventario de 11 Markdown sin archivos de producto; 39 enlaces locales y 3 anclas correctos; 23 tareas/12 checkpoints coherentes; §§1–8 de la especificación preservadas. Sin incidencias en esos controles. Diagrama revisado como texto, sin renderizar.
- Al cerrar T01 no se habían ejecutado instalación ni pruebas de producto. Esa nota es histórica; la continuación actual se detalla abajo.

### Continuación T02/T03 · 2026-10-21

- El usuario creó Git, instaló dependencias y añadió código base; autorizó iniciar la fundación. Se conservó su selección de versiones.
- Se añadió el extra asyncio de SQLAlchemy: faltaba greenlet y el import asíncrono fallaba. `uv` actualizó manifiesto/lockfile e instaló greenlet 3.5.6 sin actualizar las otras dependencias.
- `uv sync --locked --offline`: correcto; construcción de wheel/sdist correcta. Se inspeccionaron ambos artefactos: contienen `src.application`, no contienen `.env`, `.venv`, caché ni temporales. El comando instalado apunta a `src.application:main`.
- 10 pruebas unittest correctas. La ejecución aislada se bloqueó en el socket interno de asyncio de Windows; las mismas pruebas pasaron fuera del aislamiento, sin cambiar el producto para eludir ese fallo.
- HTTP local real: `/health/live` respondió 200 y `/health/ready` 503 con base no configurada. El proceso temporal se detuvo.
- Sin tablas, migraciones, credenciales reales, workers, CI, integración de consumidores ni despliegue. No se ha comprobado PostgreSQL real. C03 no se marca aceptado por estas pruebas.

### Corrección de T03 e inicio de T04 · 2026-10-21

- `lifespan` y `session`, ambas con `@asynccontextmanager`, usan `AsyncGenerator` en vez de `AsyncIterator`. Se conserva AsyncIterator en la dependencia sin decorador. No se cambió el comportamiento.
- Las 10 pruebas existentes pasaron. Comprobación AST: los dos contextos decorados usan AsyncGenerator. No hay CLI de basedpyright en este entorno; no se afirma una ejecución de ese analizador.
- El usuario autorizó continuar y eligió proveedor externo OIDC, con permisos y dispositivos en API. Confirmó permisos vigentes al aceptar y conservación de intenciones rechazadas para revisión.
- Propuesta de seguridad creada en `docs/access-design.md`; concesiones del Hub, proveedor, sesiones y vínculo de dispositivo aún requieren cierre. T04 no se marca Done ni se implementa acceso.
