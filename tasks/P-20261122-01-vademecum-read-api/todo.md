# Lista de tareas: P-20261122-01-vademecum-read-api

**Plan:** [plan.md](plan.md). **Actualizado:** 2026-11-22. **Estado del plan:** Completed.

El usuario aprobó el plan el 2026-11-22 y autorizó su ejecución secuencial. Se conserva todo el trabajo existente y no se crea otro plan. Ningún checkpoint está aceptado.

Comandos comunes desde la raíz cuando correspondan:

- Suite: `./.venv/Scripts/python.exe -m unittest discover -s tests -v`.
- Probe: `./.venv/Scripts/python.exe test-support/vademecum/check.py`.
- Contratos: `./.venv/Scripts/python.exe -m scripts.export_contracts --check`.
- Build: `uv build --offline`.

## T01 · Registrar el plan y la decisión del componente

**Estado:** Done. **Propietario:** tareas/documentación. **Alcance:** S.

**Descripción:** incorporar el plan aprobado al índice y registrar D20 con fuente autoritativa, alcance, acceso y decisión de componente interno.

**Entradas y dependencias:** plan aprobado; `plan.md` y `todo.md` ya creados durante la planificación. No depende de otro plan.

**Datos, contratos, transacciones y consumidores:** solo documentación. No cambia datos, rutas, transacciones, sincronización o consumidores.

**Criterios de aceptación:**
- [x] `tasks/README.md` registra el plan aprobado y su ejecución In progress, sin marcar checkpoints aceptados.
- [x] D20 fija fuente, lectura online, personal autorizado, revisión visible y exclusiones sin declarar implementación.

**Verificación:**
- [x] `git diff --check`: pasó; solo avisos de conversión LF/CRLF ya presentes en el árbol.
- [x] Enlaces relativos del plan, su entrada en el índice y D20: 16 destinos existentes. Una exploración amplia detectó el enlace ajeno preexistente `docs/decisions.md` → `nightingale-desktop-docs/README.md`, ausente; no se modificó.
- [x] Manual: D20 y el índice conservan fuente, acceso, revisión visible, arquitectura interna y exclusiones aprobadas.

**Evidencia:** comandos ejecutados desde la raíz el 2026-11-22; no se crearon tablas, rutas ni migraciones.

**Archivos previstos:** `tasks/README.md`, `docs/decisions.md`, `tasks/P-20261122-01-vademecum-read-api/plan.md`, `tasks/P-20261122-01-vademecum-read-api/todo.md`.

## T02 · Publicar el diseño HTTP, acceso y físico

**Estado:** Done. **Propietario:** vademecum/documentación. **Alcance:** M.

**Descripción:** trasladar a las fuentes vigentes las cuatro rutas, modelos públicos, autorización, cinco tablas, releases, importación administrativa y búsqueda acotada.

**Entradas y dependencias:** T01; plan aprobado y esquema de monografía.

**Datos, contratos, transacciones y consumidores:** diseño para revisión C01; no crea tablas ni modifica consumidores. Define futura transacción de importación y lecturas online sin sync.

**Criterios de aceptación:**
- [x] `api-v1.md` §13 y `access-design.md` definen rutas, campos, advertencias, errores y acceso owner/assistant sin permiso clínico nuevo.
- [x] `database-schema.md` §16 define columnas, claves, FK, índices, JSONB, activación única y permisos runtime; `architecture.md` registra propiedad y dependencias.

**Verificación:**
- [x] `git diff --check`: pasó. Enlaces de las secciones nuevas: 5 destinos existentes.
- [x] Script focal confirmó las cuatro rutas de §5.1 y sus parámetros/respuestas.
- [x] Manual: recorrido importación→release activo→producto→monografía y rechazos trazados; la guarda vigente devuelve 404 a outsider/pertenencia inactiva y 403 a cuenta/dispositivo no autorizado.

**Evidencia:** inspección del dataset confirmó 6.264 registros únicos, 868 IDs de monografía únicos, 120 referencias por producto, 1.116 productos sin monografía y 222 ATC vacíos. No se creó código ni migraciones.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/database-schema.md`, `docs/architecture.md`.

## C01 · Después de T01–T02

- [x] El diseño cubre mapeo fuente→público, acceso, persistencia, importación y advertencias.
- [x] Los enlaces focales y `git diff --check` pasan; no hay código o migraciones nuevos.
- [x] El usuario revisó y aceptó C01 el 2026-11-22 y autorizó continuar.

## T03 · Modelar monografías con Pydantic

**Estado:** Done. **Propietario:** `vademecum/domain`. **Alcance:** M.

**Descripción:** crear modelos tipados para toda la monografía 1.0.0, sus objetos anidados, conjuntos cerrados, nulabilidad, fuentes, procedencia y revisión.

**Entradas y dependencias:** C01 aceptado; `monograph.schema.json`; BaseModel del proyecto y Pydantic 2.14.1 resuelto. Consultar y registrar la documentación oficial de esa versión antes de usar validadores o tipos no presentes en el proyecto.

**Datos, contratos, transacciones y consumidores:** esquemas fuente/públicos sin SQL ni transacciones. La salida conserva camelCase y todos los datos clínicos de la monografía.

**Criterios de aceptación:**
- [x] Todos los campos y enums del esquema tienen representación tipada, con extras rechazados y nulos solo donde se permiten.
- [x] Las 868 monografías autoritativas validan y hacen round-trip exacto; IDs, fechas y conjuntos inválidos reciben errores focales.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_monographs -v`: 7 pruebas, OK.
- [x] Control estructural amplio: 57/58 pasaron. El comando por módulos del plan encuentra un fallo de importación preexistente en `test_accounts_structure.py`; con discovery, el único error es el ya documentado `UsersStructureTests` por falta de `src/api/users/repository/dao.py`. No se modificó trabajo de users.
- [x] Manual automático: una monografía simple, la más completa y una combinación conservan exactamente su JSON fuente.

**Evidencia:** Pydantic 2.14.1 instalado; documentación oficial registrada en `models.md`, `validators.md` y `serialization.md` bajo `https://github.com/pydantic/pydantic/blob/v2.14.1/docs/concepts/`. La primera ejecución detectó trimming y fechas demasiado estrictas; se corrigieron para respetar el esquema y la fuente, luego pasó la matriz completa. `git diff --check` pasó.

**Archivos previstos:** `src/api/vademecum/domain/monographs.py`, `src/api/vademecum/domain/__init__.py`, `tests/test_vademecum_monographs.py`.

## T04 · Modelar catálogo, productos y consultas

**Estado:** Done. **Propietario:** `vademecum/domain`. **Alcance:** M.

**Descripción:** crear modelos de importación del dataset vigente, producto, referencia por producto, contexto de catálogo, consultas y respuestas paginadas.

**Entradas y dependencias:** T03; dataset autoritativo y diseño C01.

**Datos, contratos, transacciones y consumidores:** contratos de entrada/salida sin persistencia. Ignora explícitamente histórico y suplementario; no incorpora administración cruda ni sync.

**Criterios de aceptación:**
- [x] Los modelos cubren los diez estados de vínculo y cinco de resolución, referencias opcionales y texto/ATC vacíos sin inventar hechos clínicos.
- [x] Las respuestas incluyen contexto e `items`/`total`; las 6.264 proyecciones excluyen administración fuente, histórico y suplementario.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_contracts -v`: 8 pruebas, OK.
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_monographs tests.test_vademecum_contracts -v`: 15 pruebas, OK.
- [x] Manual automático: producto vinculado, producto sin información y referencia de combinación revisados; JSON público tiene exactamente los campos aprobados.

**Evidencia:** el dataset completo valida con 6.264 productos, 868 monografías, 9.036 históricos ignorados y 282 suplementarios ignorados. Se detectaron 885 instantes fuente sin offset; se normalizan como hora de registro `America/Caracas` y se serializan en UTC con `Z`. Documentación Pydantic 2.14.1 de serialización: `https://github.com/pydantic/pydantic/blob/v2.14.1/docs/concepts/serialization.md`. `git diff --check` pasó.

**Archivos previstos:** `src/api/vademecum/domain/catalog.py`, `src/api/vademecum/domain/products.py`, `tests/test_vademecum_contracts.py`.

## C02 · Después de T03–T04

- [x] Las 868 monografías validan y los modelos de producto/catálogo cumplen el mapeo C01.
- [x] Pruebas focales y `git diff --check` pasan; el único fallo estructural ajeno ya registrado permanece sin cambios.
- [x] El usuario revisó y aceptó C02 el 2026-11-22 y reiteró la autorización de continuar hasta C05.

## T05 · Añadir persistencia del vademecum

**Estado:** Done. **Propietario:** `vademecum/repository`. **Alcance:** M.

**Descripción:** añadir los cinco modelos SQLAlchemy y una migración PostgreSQL reversible con claves, restricciones, índices, activación única y permisos SELECT para runtime.

**Entradas y dependencias:** C02 aceptado; diseño físico T02; SQLAlchemy 2.1.6, Alembic 1.20.1 y PostgreSQL 18 del proyecto. Consultar/registrar documentación oficial de JSONB, restricciones e índices según las APIs usadas.

**Datos, contratos, transacciones y consumidores:** crea tablas globales internas por release; no toca datos existentes, operaciones o sync. La migración no importa el dataset ni activa un release.

**Criterios de aceptación:**
- [x] Las cinco tablas implementan el diseño aceptado, con FK por release, UQ, checks de forma/estado e índice único parcial activo.
- [x] Runtime recibe SELECT sin escrituras; upgrade, downgrade y reupgrade conservan el resto del esquema.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_import -v`: 2 pruebas, OK. Generación offline de Alembic también pasó.
- [x] `./.venv/Scripts/python.exe test-support/persistence/check.py`: pasó en PostgreSQL Test aislado. El primer intento detectó multi-SQL no admitido por asyncpg; se separaron las sentencias y la repetición pasó.
- [x] Probe focal PostgreSQL: cinco tablas, constraints, índice parcial activo, SELECT permitido e INSERT denegado con SQLSTATE 42501; downgrade a `20261120_01` conserva `accounts` y reupgrade pasa.

**Evidencia:** fuentes oficiales registradas: SQLAlchemy 2.1 `https://docs.sqlalchemy.org/en/21/dialects/postgresql.html#sqlalchemy.dialects.postgresql.JSONB` y `https://docs.sqlalchemy.org/en/21/core/constraints.html`; PostgreSQL 18 `https://www.postgresql.org/docs/18/indexes-partial.html`; Alembic `https://alembic.sqlalchemy.org/en/latest/ops.html`. La URL específica 1.20.1 no devolvió contenido; se usó la referencia oficial vigente sin afirmar cambios de versión.

**Archivos previstos:** `src/api/vademecum/repository/models.py`, `src/api/vademecum/repository/__init__.py`, `migrations/versions/20261122_01_vademecum.py`, `tests/test_accounts_structure.py`.

## T06 · Implementar la importación transaccional

**Estado:** Done. **Propietario:** `vademecum/application` y `repository`. **Alcance:** M.

**Descripción:** crear DAOs de importación/lectura y un caso que valide, ensambl e inserte un release completo por lotes y lo active al final.

**Entradas y dependencias:** T05; modelos T03/T04; transacción y DAO base existentes.

**Datos, contratos, transacciones y consumidores:** escribe solo las cinco tablas del componente mediante una identidad administrativa. Una transacción cubre inserción y activación; application no ejecuta SQL ni operaciones directas sobre la sesión. No emite sync ni afecta consumidores.

**Criterios de aceptación:**
- [x] Duplicados, referencias rotas, estadísticas discrepantes o contenido inválido se rechazan antes de abrir la transacción.
- [x] La misma huella no escribe; un release nuevo inserta por lotes y activa al final. La prueba PostgreSQL completa queda en C03.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_import -v`: 8 pruebas, OK.
- [x] `VademecumStructureTests`: 5/5 controles pasan dentro de discovery; `UsersStructureTests` conserva su error ajeno por DAO ausente.
- [x] Unit: rollback forzado y activación atómica se comprobarán en el probe real C03; idempotencia con huella existente comprobada sin escrituras.

**Evidencia:** se reutilizó `to_slug` para las estadísticas que la fuente calcula sin signos; `linkedMonographs` incluye vínculos históricos solo para validar la cifra, sin importarlos. Búsqueda conserva la normalización aprobada. `git diff --check` pasó.

**Archivos previstos:** `src/api/vademecum/application/import_cases.py`, `src/api/vademecum/application/__init__.py`, `src/api/vademecum/repository/dao.py`, `tests/test_vademecum_import.py`.

## T07 · Añadir el comando administrativo de importación

**Estado:** Done. **Propietario:** scripts/operación. **Alcance:** S.

**Descripción:** crear un script `--file` que seleccione `VADEMECUM_IMPORT_DATABASE_URI` antes de cargar la fábrica de sesión, ejecute el caso y devuelva resumen o error controlado.

**Entradas y dependencias:** T06; patrón de `scripts/create_practice.py`.

**Datos, contratos, transacciones y consumidores:** proceso administrativo separado del servidor; no configura arranque, lee secretos de archivos ni crea otro sistema CLI. La transacción pertenece a T06.

**Criterios de aceptación:**
- [x] URI ausente/inválida, archivo ilegible o contenido inválido terminan con código 2 sin escrituras ni trazas con secretos.
- [x] Una ejecución válida informa huella, release, conteos y `imported`/`existing`.

**Verificación:**
- [x] `./.venv/Scripts/python.exe scripts/import_vademecum.py --help`: pasó. URI ausente/inválida, archivo inexistente y contenido inválido: código 2 esperado.
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_import -v`: 8 pruebas, OK.
- [x] Comando real contra base Test migrada: importación y repetición válidas; guía creada.

**Archivos previstos:** `scripts/import_vademecum.py`, `docs/operations/vademecum.md`, `test-support/README.md`.

## C03 · Después de T05–T07

- [x] PostgreSQL Test acredita migración reversible, SELECT runtime, importación completa, idempotencia, rollback y activación atómica.
- [x] La fuente completa produce 6.264 productos y 868 monografías; referencias, ingredientes, vínculos y conteos coinciden.
- [x] El usuario revisó y aceptó C03 junto con el cierre el 2026-11-22.

**Evidencia:** comando real importó y repitió la fuente; rollback forzado conservó release activo; nuevo release activó al final; dos importaciones concurrentes distintas terminaron con cuatro releases y uno activo; runtime SELECT/UPDATE/DELETE produjo lo permitido/denegado esperado. Se corrigieron JSON `null` frente a SQL `NULL` y fabricante vacío→nulo; la matriz completa posterior pasó. Las bases temporales se eliminaron.

## T08 · Implementar lecturas y acceso de productos

**Estado:** Done. **Propietario:** `vademecum/application` y `repository`. **Alcance:** M.

**Descripción:** reutilizar contexto de cuenta y añadir consultas del release activo para lista/detalle, búsqueda normalizada, filtro `monographId`, orden y paginación.

**Entradas y dependencias:** C03 aceptado; `get_account_context` y modelos T04.

**Datos, contratos, transacciones y consumidores:** lecturas online de datos globales, autorizadas por cuenta/dispositivo. Sin datos de pacientes, auditoría clínica, sync o escrituras.

**Criterios de aceptación:**
- [x] Owner/assistant activos leen; credencial inválida, outsider, cuenta inactiva o dispositivo no autorizado no reciben contenido.
- [x] DAO implementa nombre/registro/principio activo/alias/ID canónico/ATC, normalización, escape literal, filtro, total y orden; la matriz real queda en C04.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_access -v`: 5 pruebas, OK.
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_access tests.test_vademecum_import -v`: 13 pruebas, OK tras corregir una afirmación de identidad en el test.
- [x] Proyecciones conservan vínculos e ingredientes; ausencia de release/producto y página vacía cubiertas por casos/DAO; recorrido HTTP completo pendiente de C04.

**Archivos previstos:** `src/api/vademecum/application/read_cases.py`, `src/api/vademecum/repository/dao.py`, `src/api/vademecum/domain/errors.py`, `tests/test_vademecum_access.py`.

## T09 · Exponer las rutas de productos

**Estado:** Done. **Propietario:** `vademecum/infrastructure`. **Alcance:** S.

**Descripción:** añadir endpoints tipados de lista/detalle con bearer, sesión inyectada, consulta validada y traducción de resultados a 401/403/404/503.

**Entradas y dependencias:** T08; contratos T04 y reglas de transporte existentes.

**Datos, contratos, transacciones y consumidores:** solo endpoints; no esquemas o helpers de negocio en infrastructure. Respuestas GET online sin sync.

**Criterios de aceptación:**
- [x] Lista/detalle declaran response models reales, contexto, advertencias y vínculos; parámetros desconocidos producen 422.
- [x] Objeto ausente=404 y catálogo no cargado=503; respuestas no contienen claves administrativas crudas.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_products_api -v`: 5 pruebas ASGI, OK.
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_access tests.test_vademecum_products_api -v`: 10 pruebas, OK.
- [x] Rutas llamadas mediante ASGI con casos tipados; owner/assistant con PostgreSQL/Keycloak real queda en C04.

**Archivos previstos:** `src/api/vademecum/infrastructure/products_api.py`, `src/api/vademecum/infrastructure/__init__.py`, `tests/test_vademecum_products_api.py`.

## T10 · Exponer lecturas de monografías

**Estado:** Done. **Propietario:** `vademecum`. **Alcance:** M.

**Descripción:** añadir consultas y rutas de lista/detalle para monografías del release activo, con reconstrucción y validación del documento completo.

**Entradas y dependencias:** T09; modelos T03 y acceso T08.

**Datos, contratos, transacciones y consumidores:** lecturas online del documento JSONB validado; sin búsqueda clínica, escrituras, sync o archivos externos.

**Criterios de aceptación:**
- [x] Lista busca nombre, alias y ATC con paginación; detalle valida y devuelve todas las secciones, fuentes, procedencia y revisión.
- [x] Combinaciones, ATC vacío y revisión pendiente conservan significado; ID ausente devuelve 404 tras autorización.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_monographs_api -v`: 6 pruebas, OK.
- [x] `./.venv/Scripts/python.exe -m unittest tests.test_vademecum_monographs tests.test_vademecum_monographs_api -v`: 13 pruebas, OK.
- [x] ASGI comparó documento completo y ATC vacío con la fuente; combinación real queda en C04.

**Archivos previstos:** `src/api/vademecum/application/read_cases.py`, `src/api/vademecum/repository/dao.py`, `src/api/vademecum/infrastructure/monographs_api.py`, `tests/test_vademecum_monographs_api.py`.

## C04 · Después de T08–T10

- [x] `./.venv/Scripts/python.exe test-support/vademecum/check.py` pasó con PostgreSQL/Keycloak Test y aplicación ASGI real.
- [x] El probe cubre cuatro rutas, owner/assistant, 401/403/404/422/503, búsquedas, vínculos, productos sin información, advertencias y documentos completos.
- [x] El usuario revisó y aceptó C04 junto con el cierre el 2026-11-22.

**Evidencia:** importación/idempotencia/rollback también pasaron en el probe. Se corrigió solo el orden de pertenencia/dispositivo del fixture y compatibilidad con `_IncludedRouter`; la ejecución final pasó y eliminó la base temporal.

## T11 · Conectar y publicar contratos

**Estado:** Done. **Propietario:** API/contratos. **Alcance:** M.

**Descripción:** incluir los routers en la app, exportar artefactos desde el árbol real y documentar el consumo online por el escritorio.

**Entradas y dependencias:** C04 comprobado; rutas comprobadas y exportador existente. El usuario autorizó continuar hasta C05.

**Datos, contratos, transacciones y consumidores:** publica cuatro GET y sus esquemas. No cambia `contractVersion`, catálogo de operaciones, sync o almacenamiento local; no acredita un consumidor Rust real.

**Criterios de aceptación:**
- [x] OpenAPI/modelos contienen exactamente las cuatro rutas implementadas y la comparación documental pasa.
- [x] Referencia portable y guía Rust explican autenticación, consulta, advertencias, paginación y ausencia de offline.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m scripts.export_contracts` y después `--check`: 117 rutas, 205 esquemas, 104 acciones; reproducibles.
- [x] `./.venv/Scripts/python.exe test-support/contracts/check.py`: pasó con PostgreSQL/Keycloak Test.
- [x] Script focal localizó cuatro operationId y response models; `Monograph` y modelos de página/detalle existen en `$defs`.

**Archivos previstos:** `src/api/api.py`, `contracts/api-v1/`, `contracts/api-v1/nightingale-api.md`, `docs/rust-api-guide.md`.

## T12 · Ejecutar verificación integral y registrar evidencia

**Estado:** Done. **Propietario:** vademecum/calidad. **Alcance:** M.

**Descripción:** ejecutar la matriz completa, revisar el diff propio y registrar comandos, resultados y límites sin aceptar checkpoints en nombre del usuario.

**Entradas y dependencias:** T11; todos los componentes y probes implementados.

**Datos, contratos, transacciones y consumidores:** verificación y documentación de evidencia. No cambia alcance ni corrige fallos ajenos sin decisión nueva.

**Criterios de aceptación:**
- [x] Pruebas focales, probe real, contratos, build y diff pasan para el componente; la suite conserva un fallo ajeno explícito.
- [x] La evidencia distingue importación/API local de revisión profesional, escritorio, producción y fallo previo no relacionado.

**Verificación:**
- [x] Seis módulos focales de §8: **39 pruebas, OK**. `test-support/vademecum/check.py`: pasó con PostgreSQL/Keycloak Test y app conectada.
- [x] `uv build --offline`: wheel y sdist creados correctamente. `scripts.export_contracts --check` y `git diff --check`: pasaron.
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -v`: 307 pruebas ejecutadas, 306 sin fallo y un error preexistente de `UsersStructureTests` porque `src/api/users/repository/dao.py` no existe. No se modificó users.

**Evidencia y límites:** se revisó el recorrido búsqueda→producto→monografía y el estado Git. No hay archivos temporales nuevos en Git. La revisión profesional del contenido, consumidor Rust, despliegue, producción y verificación de fuentes externas no se acreditan. C01/C02 fueron aceptados; C03/C04 están comprobados y quedan para revisión junto con C05 por la autorización expresa de ejecución continua.

**Revisión posterior:** se detectó que el registro vigente `P.B.1.289/12` no alcanzaba el caso de lectura por contener `/`. Se cambió el parámetro a `{registration_number:path}` y se añadieron pruebas literal/codificada en unit y probe real. Resultado: 40 pruebas focales OK, probe PostgreSQL/Keycloak OK, contratos regenerados/`--check` OK, `uv build --offline` y `git diff --check` OK. El usuario aprobó entonces todos los checkpoints y el cierre.

**Archivos previstos:** `tasks/P-20261122-01-vademecum-read-api/plan.md`, `tasks/P-20261122-01-vademecum-read-api/todo.md`, `tasks/README.md`, documentación de evidencia que corresponda al resultado real.

## C05 · Después de T11–T12

- [x] Todos los controles que cubren el componente pasan y la evidencia registra límites reales; la suite solo conserva el error ajeno documentado.
- [x] El diff conserva trabajo ajeno y no introduce archivos temporales o afirmaciones no comprobadas.
- [x] El usuario revisó y aceptó C05 el 2026-11-22 después de la corrección y verificación; plan Completed.
