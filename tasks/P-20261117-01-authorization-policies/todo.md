# Lista de tareas: P-20261117-01-authorization-policies

**Plan:** [plan.md](plan.md). **Actualizado:** 2026-11-18. **Estado del plan:** Completed.

C09 clínico aceptado por el usuario el 2026-11-17 y plan clínico Completed. Se ejecuta T01 → T02 → T03 hasta C01, sin delegación; El usuario amplió el alcance hasta C02 el 2026-11-17 y autorizó el paso por C01 a T04–T06; no se atribuye aceptación formal de C01. La evidencia se añade después de ejecutar; ninguna casilla de checkpoint representa aceptación anticipada.

## T01 · Caracterizar matriz de roles y acciones publicadas

**Estado:** Done. **Propietario:** calidad de `accounts`. **Alcance:** S.

**Descripción:** fijar con pruebas el conjunto y orden actual de `allowedActions` para propietario/asistente, cuenta activa/inactiva y dispositivo pendiente/activo/revocado.

**Entradas y dependencias:** C09 de Etapa 2 aceptado; `get_access` y catálogo de operaciones vigentes.

**Datos, contratos, transacciones y consumidores:** solo pruebas. Conserva JSON y significado remoto; no cambia datos ni consumidores.

**Criterios de aceptación:**
- [x] La matriz cubre todos los estados de cuenta/dispositivo y ambos roles sin omitir acciones.
- [x] El orden actual y las excepciones de registro/reactivación quedan caracterizados.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_accounts tests.test_operations -v`.
- [x] `./.venv/Scripts/python.exe test-support/accounts/check.py`.
- [x] Manual: comparar `GET A/access` para ambos roles y una instalación pendiente/revocada con la matriz aprobada.

**Archivos previstos:** `tests/test_accounts.py`, `tests/test_operations.py`.

**Evidencia (2026-11-17):** 12 combinaciones reales de `get_access`/`account_context` con DAOs sustituidos, lista y orden explícitos y cobertura del catálogo publicado (66 acciones, `AcceptInvitation` por ruta propia). Cuenta inactiva de asistente denegada; propietario con instalación activa solo publica `SetAccountStatus`; pendiente publica registro y revocada ninguna acción. Se conserva la doble posición de `SetPatientClinicalSectionReview`. Probe accounts correcto sobre PostgreSQL/Keycloak Test, incluida comparación HTTP de acceso pendiente/revocado, roles, páginas y aislamiento; su base aleatoria se elimina en finally.

Comandos: `uv run --locked python -m unittest tests.test_accounts tests.test_operations -v` falló primero por permisos de caché uv; con `UV_CACHE_DIR=.tmp/uv-cache` el aislamiento de Windows bloqueó asyncio. Fuera del aislamiento, el comando detectó el import previo `test_foundation` sin PYTHONPATH. Comando final: `UV_CACHE_DIR=.tmp/uv-cache`, `PYTHONPATH=tests`, `uv run --locked --offline python -m unittest tests.test_accounts tests.test_operations -v`: **13 pruebas, 7,886 s, OK**. `./.venv/Scripts/python.exe test-support/accounts/check.py`: **OK**, fuera del aislamiento. No cambió código de producto. Python 3.15.1 y uv.lock inspeccionados; unittest/AsyncMock según https://docs.python.org/3.15/library/unittest.html y https://docs.python.org/3.15/library/unittest.mock.html#unittest.mock.AsyncMock. Sin dependencia nueva.

## T02 · Caracterizar secciones, resultados y audiencias clínicas

**Estado:** Done. **Propietario:** calidad de `clinical_records` y `sync`. **Alcance:** M.

**Descripción:** fijar la correspondencia acción→sección, niveles de lectura/escritura, recibos y entidad→audiencia para las ocho secciones.

**Entradas y dependencias:** T01; políticas actuales en `access_cases.py`, `operations_cases.py` y `download_cases.py`.

**Datos, contratos, transacciones y consumidores:** pruebas y fixtures ficticios; conserva recibos históricos, capturas y deltas.

**Criterios de aceptación:**
- [x] Toda acción clínica y audiencia existente tiene casos para `none`, `read` y `read_write`.
- [x] Duplicados/GET de escritura y recibos ambiguos conservan fail-closed.
- [x] Captura/delta prueban grupos invisibles y totales autorizados.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_clinical_permissions tests.test_downloads -v`.
- [x] `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py` y `./.venv/Scripts/python.exe test-support/clinical_downloads/check.py`.
- [x] Manual: seguir una escritura y su reintento tras reducir permiso, comprobando que no devuelve contenido anterior.

**Archivos previstos:** `tests/test_clinical_permissions.py`, `tests/test_downloads.py`, `test-support/clinical_permissions/check.py`.

**Evidencia (2026-11-17):** `UV_CACHE_DIR=.tmp/uv-cache`, `PYTHONPATH=tests`, `uv run --locked --offline python -m unittest tests.test_clinical_permissions tests.test_downloads -v`: **14 pruebas, 0,006 s, OK**. Cada acción clínica fija sección y evalúa resultado, lectura y audiencia en los tres niveles; revisión compartida conserva sección validada. `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py`: **OK**, matriz HTTP de ocho secciones/tres niveles con todas las acciones y ambas revisiones, defaults, permisos vigentes, reintentos y GET tras reducción, rollback y revocación. Para cambios de Etapa 2 sobre ID inexistente, read_write devuelve 404 antes de errores de payload; none/read devuelven 403. `./.venv/Scripts/python.exe test-support/clinical_downloads/check.py`: **OK**, captura opt-in, alcance parcial, delta, época y fallo de auditoría. Los probes usan PostgreSQL/Keycloak Test y eliminan sus bases aleatorias. No se acredita todavía la matriz exhaustiva entidad→audiencia ni todos los grupos invisibles/totales de C01.

**Discrepancia AU-32, decisión pendiente:** el probe crea por INSERT un recibo histórico ficticio de `SetPatientClinicalSectionReview` sin sección, con resultado rechazado sin cuerpo clínico, y su auditoría correspondiente; todas las restricciones siguen activas. Con todas las secciones en none, GET devuelve **200** y el resultado rechazado anterior; debería denegar por alcance ambiguo. Al habilitar conditions=read_write, repetir con sección conditions devuelve **403** por diferencia frente a NULL. `get_operation` solo exige permiso clínico cuando `clinical_section is not None`; la migración 20261116_02 conserva NULL en revisiones históricas ambiguas. No se ha cambiado código de producto ni se afirma divulgación de cuerpo clínico en este fixture. La aserción del probe caracteriza el 200 observado, no demuestra cumplimiento de AU-32. Conforme al §2 del plan, se detiene esta parte para decisión del usuario. T02 no está Done; T03 sigue Todo por dependencia.

**Fallos de preparación corregidos:** el primer INSERT del fixture omitía auditoría y PostgreSQL rechazó el commit (23514); se añadió la auditoría sin desactivar restricciones. La primera matriz esperaba 200 en cambios de atenciones inexistentes, pero el código devuelve 404; se recorrió el caso real y se fijó esa respuesta en la prueba. Última ejecución completa del probe: OK con la discrepancia explícita.

**Fuentes de herramientas:** Python 3.15.1 y SQLAlchemy 2.1.6 según manifiesto/lockfile, sin instalaciones o cambios de versión. AsyncSession.begin y SQL parametrizado reutilizan el patrón existente: https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncSession.begin y https://docs.sqlalchemy.org/en/21/core/sqlelement.html#sqlalchemy.sql.expression.text (documentación oficial de la rama 2.1, ahora muestra parche 2.1.9; patrón ejecutado con 2.1.6).

**Resolución AU-32 autorizada por el usuario el 2026-11-17:** corrección mínima confirmada, sin catálogo anticipado: get_operation reutiliza clinical_result_section y reconoce la revisión de sección dinámica para denegar recibos clínicos sin sección antes de get_scoped. Prueba enfocada: `uv run --locked --offline python -m unittest tests.test_operations tests.test_clinical_permissions tests.test_downloads -v`, con UV_CACHE_DIR/PYTHONPATH anteriores: **22 pruebas, 6,545 s, OK**; cubre tres acciones representativas × tres niveles sin lectura/auditoría de resultado y conserva recibo administrativo sin sección. Probe clinical_permissions **OK**, GET ambiguo 403 tanto con none como con escritura; reintento 403. Probe clinical_downloads ampliado **OK**, total de página coincide con itemCount y elementos autorizados; un cambio de conditions invisible devuelve groups=[] y avanza cursor. Se reutiliza el probe existente para verificar este criterio de T02; no se crea otro sistema de pruebas. La evidencia previa del fallo se conserva como historia, ya resuelta. T02 Done.

## T03 · Fijar correspondencia del catálogo en documentación vigente

**Estado:** Done. **Propietario:** documentación de acceso/arquitectura. **Alcance:** M.

**Descripción:** incorporar a las fuentes vigentes la tabla acción→descriptor→regla de objeto y entidad→audiencia, sin duplicar modelos HTTP ni declarar código implementado.

**Entradas y dependencias:** T01–T02; especificación aprobada y resultados de caracterización.

**Datos, contratos, transacciones y consumidores:** documentación de diseño; no cambia esquema físico, transacciones o consumidores.

**Criterios de aceptación:**
- [x] Todas las acciones/audiencias actuales tienen una única correspondencia prevista y regla de compatibilidad.
- [x] Se distinguen autenticación, contexto de cuenta y atributos del recurso.
- [x] Cualquier discrepancia encontrada queda registrada como pendiente, no corregida silenciosamente.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_authorization_structure tests.test_accounts_structure -v`.
- [x] `git diff --check` y validación de enlaces locales de los documentos modificados.
- [x] Manual: recorrer una acción administrativa, una clínica y una regla de objeto desde ruta hasta descriptor.

**Archivos previstos:** `docs/access-design.md`, `docs/architecture.md`, `docs/api-v1.md`.

**Evidencia:** access-design contiene la única correspondencia prevista de acciones/objetos/audiencias; arquitectura y api-v1 enlazan esa fuente. Comparación ejecutada mediante Python con get_capabilities().value.operation_catalog y PROJECTION_SCHEMAS: **66 acciones publicadas y 25 entidades**, sin diferencias; AcceptInvitation queda aparte. Recorridos manuales: UpdateAccountPolicy → authorized_context → owner → management_cases; CreatePatientNote → sección notes → read_write → notes_cases; UpdateService → service_permission/profesional propio → owner → services_cases. Lecturas/resultados/audiencias siguen sus propietarios hasta fases posteriores. AU-32 conserva hallazgo, permiso y corrección explícitos. Enlaces locales de los tres documentos y git diff --check: OK. Controles de estructura: **55 pruebas, 0,526 s, OK**. Suite de C01 tras corregir AU-32: **199 pruebas, 66,070 s, OK**. No se cambió comportamiento fuera de AU-32 autorizado.

## C01 · Después de T01–T03

- [x] Suite y probes de línea base pasan con datos ficticios.
- [x] Cobertura documental exhaustiva; solo AU-32 cambia comportamiento con permiso expreso.
- [x] El usuario revisa y acepta C01.

**Comprobaciones de línea base ejecutadas antes de resolver AU-32:** con las mismas variables `UV_CACHE_DIR`/`PYTHONPATH` y fuera del aislamiento de Windows, `uv run --locked --offline python -m unittest discover -s tests -v`: **199 pruebas, 65,122 s, OK**. `uv run --locked --offline python -m unittest tests.test_authorization_structure tests.test_accounts_structure -v`: **55 pruebas, 0,296 s, OK**. No sustituyen T03 ni la aceptación de C01. `git diff --check`: OK. El diff propio solo contiene pruebas, evidencia y cierre clínico autorizado; `src/`, migraciones, dependencias y contratos generados no tienen cambios. Se conservan los cambios concurrentes ajenos en D19, el índice de tareas y P-20261117-05-clinical-stage-3.

## T04 · Introducir descriptores y evaluación pura de políticas

**Estado:** Done. **Propietario:** `accounts/domain`. **Alcance:** M.

**Descripción:** crear un catálogo tipado y funciones puras para rol base, sección/nivel, estados de acceso y referencias de reglas de objeto.

**Entradas y dependencias:** C01 aceptado; correspondencia documentada en T03.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/sesión; no cambia persistencia ni contratos públicos.

**Criterios de aceptación:**
- [x] El catálogo cubre exactamente las acciones actuales y deniega descriptores desconocidos.
- [x] Las funciones reproducen la matriz T01/T02 sin `Any`, `cast` ni reglas arbitrarias.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_authorization_policies -v`.
- [x] `uv run --locked python -m unittest tests.test_authorization_structure tests.test_accounts_structure -v`.
- [x] Manual: inspeccionar decisiones representativas de owner, assistant y cada nivel clínico.

**Archivos previstos:** `src/api/accounts/domain/policies.py`, `tests/test_authorization_policies.py`.

**Evidencia:** catálogo puro con 66 acciones publicadas más AcceptInvitation privado, rol base, ocho secciones/nivel read_write, regla de objeto y posiciones de publicación. No SQL, proveedor, constantes de producto en core ni dependencias nuevas. `uv run --locked --offline python -m unittest tests.test_authorization_policies tests.test_authorization_structure tests.test_accounts_structure -v` con UV_CACHE_DIR/PYTHONPATH anteriores: **59 pruebas, 0,439 s, OK**. Revisados owner/assistant, niveles, registro pendiente, revocado, reactivación y revisión dinámica. El control estructural anterior prohibía toda función de dominio; ahora admite funciones síncronas puras según el plan aprobado y prohíbe además repositorios propios/ajenos y core.services. No se añade una excepción por archivo ni se admite SQL/proveedores en dominio.

## T05 · Derivar `AccessResponse.allowedActions` del catálogo

**Estado:** Done. **Propietario:** `accounts`. **Alcance:** S.

**Descripción:** sustituir la composición manual de acciones por evaluación del catálogo, conservando forma, nombres y orden publicados.

**Entradas y dependencias:** T04; pruebas de caracterización T01.

**Datos, contratos, transacciones y consumidores:** misma lectura transaccional de contexto; respuesta pública equivalente y sin cambios de sync.

**Criterios de aceptación:**
- [x] Todas las combinaciones T01 devuelven exactamente las mismas acciones y orden.
- [x] `permissionEpoch`, estados y permisos clínicos permanecen iguales.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_accounts tests.test_authorization_policies -v`.
- [x] `./.venv/Scripts/python.exe test-support/accounts/check.py`.
- [x] Manual: comparar antes/después las respuestas `A/access` de propietario y asistente en los estados soportados.

**Archivos previstos:** `src/api/accounts/application/accounts_cases.py`, `tests/test_accounts.py`.

**Evidencia:** get_access llama published_actions; conserva autenticación, transacción, estado, niveles y época. Prueba independiente de T01 de doce estados con lista exacta y orden: OK. `uv run --locked --offline python -m unittest tests.test_accounts tests.test_authorization_policies -v`: **9 pruebas, 2,038 s, OK**. `./.venv/Scripts/python.exe test-support/accounts/check.py`: **OK**, OIDC/PostgreSQL Test, respuestas HTTP y acceso pendiente/revocado. Sin cambios contractuales.

## T06 · Autorizar acciones administrativas del lote mediante descriptores

**Estado:** Done. **Propietario:** `sync` y `accounts`. **Alcance:** M.

**Descripción:** sustituir las listas owner/member del despacho administrativo por descriptores, sin alterar orden de autenticación, bloqueos, recibos o ejecución.

**Entradas y dependencias:** T05; casos administrativos y probes de sync/team.

**Datos, contratos, transacciones y consumidores:** misma transacción de aceptación; efectos, recibos, auditoría y grupos conservados.

**Criterios de aceptación:**
- [x] Owner/assistant obtienen los mismos rechazos y efectos para todas las acciones administrativas.
- [x] Registro, invitación y reactivación conservan sus excepciones explícitas.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_operations tests.test_account_changes -v`.
- [x] `./.venv/Scripts/python.exe test-support/sync/check.py` y `./.venv/Scripts/python.exe test-support/team/check.py`.
- [x] Manual: enviar una acción owner-only como asistente y una operación válida como propietario, revisando estado y recibo.

**Archivos previstos:** `src/api/sync/application/operations_cases.py`, `tests/test_operations.py`, `tests/test_account_changes.py`.

**Evidencia:** la guarda owner-only de accept_operation obtiene el descriptor del catálogo; se retiran las listas duplicadas de administración/servicios/ofertas en esa guarda. Autenticación, orden de bloqueos, relecturas, registro, invitación, reactivación, reglas de objeto, recibos y ejecución permanecen en sus casos actuales. Lo desconocido conserva UNSUPPORTED_OPERATION, no recibe permiso de negocio. `uv run --locked --offline python -m unittest tests.test_operations tests.test_account_changes -v`: **12 pruebas, 8,249 s, OK**, incluidas 32 decisiones independientes (16 acciones × owner/assistant), antes de get_scoped. Probes reales `./.venv/Scripts/python.exe test-support/sync/check.py` y `./.venv/Scripts/python.exe test-support/team/check.py`: **OK**, duplicado concurrente, rollback, respuesta perdida, acceso vigente, lotes independientes, invitación dirigida/72 h/aceptación y revocación concurrentes. Los fixtures ejercen acciones válidas del propietario y denegaciones del asistente; no cambian tablas ni transacciones.

## C02 · Después de T04–T06

- [x] Pruebas de catálogo, acceso y operaciones administrativas pasan.
- [x] Las acciones publicadas y las ejecutables coinciden sin cambios contractuales.
- [x] El usuario aceptó C02 el 2026-11-17 y autorizó T07 → T08 → T09 hasta C03.

**Cierre técnico C02 · 2026-11-17:** T01–T06 Done. El usuario autorizó pasar C01 hasta C02; la aceptación formal de C01 no se atribuye al agente. C02 fue aceptado después por el usuario; T07–T09 se habilitaron hasta C03.

- `UV_CACHE_DIR=.tmp/uv-cache`, `PYTHONPATH=tests`, `uv run --locked --offline python -m unittest discover -s tests -v`: **205 pruebas, 69,794 s, OK**, sobre el árbol compartido actual.
- `uv run --locked --offline python -m unittest tests.test_authorization_policies tests.test_authorization_structure tests.test_accounts_structure -v`: **59 pruebas, 0,567 s, OK**.
- Probes accounts (T05), sync/team (T06), clinical_permissions y clinical_downloads (T02/AU-32): OK en servicios Test aislados; cada probe valida el clúster y elimina su base aleatoria. No se usa base personal/producción.
- `uv run --locked --offline python -m scripts.export_contracts --check`: **falla** en openapi.json por metadatos de origen desactualizados: difieren sourceSha256 (incluye todos los fuentes modificados) y sourceHead; los demás campos de x-generated coinciden. Comparación adicional en memoria con scripts.export_contracts.documents, URI ficticia inaccesible y sin .env: los **cinco cuerpos JSON coinciden exactamente** con contracts/api-v1 al excluir solo x-generated. No se reescribieron generados; no se declara --check correcto. La primera comparación dejó el cwd en el temporal y Windows impidió retirarlo; se corrigió el finally y se eliminó solo ese directorio vacío verificado.
- Fuente oficial para el descriptor derivado del BaseModel existente: Pydantic **2.14.1**, https://raw.githubusercontent.com/pydantic/pydantic/v2.14.1/docs/concepts/models.md#basic-model-usage (modelos anotados y asignación de campos); la URL de documentación /2.14 no estaba accesible, se comprobó el tag exacto. Sin dependencias/APIs nuevas fuera del patrón existente. Las decisiones puras no usan framework de políticas.
- Revisión: no hay cambios en migraciones, tablas, dependencias, rutas, modelos HTTP, contractVersion ni modelRevision. Se conserva orden de allowedActions y ambas posiciones de revisión. Única corrección de comportamiento: denegación AU-32 expresamente autorizada. Clínica, audiencias, cursores y SSE no se unifican aún; corresponden a T07–T12.
- Cambios ajenos preservados: D19 y P-20261117-05-clinical-stage-3, su entrada de índice, docs/quality.md y la ampliación concurrente de tests/test_downloads.py. No commits, remotos, despliegues ni cambios en Rust/Hub. API local comprobada no acredita consumidores ni producción.

## T07 · Unificar sección/nivel de escrituras y resultados clínicos

**Estado:** Done. **Propietario:** `clinical_records` y `sync`. **Alcance:** M.

**Descripción:** resolver sección/nivel desde el catálogo para ejecución, duplicados y GET de resultados, conservando alcance persistido y auditoría.

**Entradas y dependencias:** C02 aceptado; caracterización T02.

**Datos, contratos, transacciones y consumidores:** recibos y efectos en la misma transacción; sin cambios físicos o de respuesta.

**Criterios de aceptación:**
- [x] Las ocho secciones aplican idéntica correspondencia en ejecución y recuperación.
- [x] `read`/`none` no obtiene resultados de escritura y recibos ambiguos fallan cerrados.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_clinical_permissions tests.test_operations -v`.
- [x] `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [x] Manual: repetir una operación clínica tras cada nivel de permiso y verificar ausencia de cuerpo/conflicto informativo.

**Archivos previstos:** `src/api/clinical_records/application/access_cases.py`, `src/api/sync/application/operations_cases.py`, `tests/test_clinical_permissions.py`.

**Evidencia (2026-11-17):** clinical_result_section reutiliza clinical_section_for_action; clinical_result_allowed reutiliza la evaluación de nivel de accounts/domain. Se retira la tabla clínica duplicada sin consumidores restantes. GET reconoce recibos clínicos ambiguos desde policy.sections y conserva AU-32 antes de leer cuerpos. `uv run --locked --offline python -m unittest tests.test_clinical_permissions tests.test_operations -v`: **17 pruebas, 7,946 s, OK**, con UV_CACHE_DIR=.tmp/uv-cache y PYTHONPATH=tests fuera del aislamiento de Windows. Probes `clinical_permissions/check.py` y `sync/check.py`: **OK** en PostgreSQL/Keycloak Test, incluidos niveles, duplicados, GET, ambigüedad, rollback y respuesta perdida. No cambian recibos, esquema, auditoría ni límites de transacción.

## T08 · Integrar reglas de catálogo profesional y bloqueos

**Estado:** Done. **Propietario:** `services`, `schedule` y `sync`. **Alcance:** M.

**Descripción:** referenciar reglas de objeto desde descriptores y conservar en sus componentes las comprobaciones de profesional propio, oferta y bloqueo global.

**Entradas y dependencias:** T07; casos públicos `service_permission` y `block_permission`.

**Datos, contratos, transacciones y consumidores:** mismos bloqueos profesional/cuenta y proyecciones en varias cuentas; sin importar repositorios ajenos.

**Criterios de aceptación:**
- [x] Owner sin profesional propietario no edita catálogo/perfil ajeno.
- [x] Bloqueos globales/locales y proyecciones mantienen motivos y alcance actuales.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_services tests.test_schedule tests.test_operations -v`.
- [x] `./.venv/Scripts/python.exe test-support/services/check.py` y `./.venv/Scripts/python.exe test-support/schedule/check.py`.
- [x] Manual: intentar editar servicio y bloqueo global de otro profesional con UUID conocidos.

**Archivos previstos:** `src/api/services/application/services_cases.py`, `src/api/schedule/application/blocks_cases.py`, `src/api/sync/application/operations_cases.py`, `tests/test_services.py`, `tests/test_schedule.py`.

**Evidencia (2026-11-17):** se distinguen own_professional, own_catalog y own_offer en los descriptores y se usan las referencias para coordinación, permiso de servicio/bloqueo y GET de resultados. Las consultas/propiedad permanecen intactas en services, schedule y accounts; no se editaron esos casos porque ya aplican profesional propio, vínculo activo, cuenta y proyección restringida. `uv run --locked --offline python -m unittest tests.test_authorization_policies tests.test_services tests.test_schedule tests.test_operations -v`: **30 pruebas, 11,465 s, OK**, incluida igualdad exacta descriptor→grupos existentes de servicios/ofertas/bloqueos. Probes `services/check.py` y `schedule/check.py`: **OK**, con PostgreSQL/Keycloak Test. Se recorrieron casos de servicio/oferta de profesional ajeno (404), asistente sin catálogo (403), bloqueo global ajeno (404), motivo global nulo para asistente y proyecciones por cuenta; el propietario no evita esas relaciones. Se conservan bloqueos/orden y estado remoto. Sin cambios físicos o contractuales.

## T09 · Unificar lecturas y secciones legibles con el catálogo

**Estado:** Done. **Propietario:** `accounts` y `clinical_records`. **Alcance:** M.

**Descripción:** usar el catálogo para `clinical_read_scope`, secciones legibles y acciones de lectura/historia/resumen sin cambiar DAOs ni proyecciones.

**Entradas y dependencias:** T07; rutas clínicas existentes ya concentran acceso en casos compartidos.

**Datos, contratos, transacciones y consumidores:** lecturas y auditoría en transacciones breves; filtros antes de contar/paginar.

**Criterios de aceptación:**
- [x] Detalle, lista, historia, resumen y última visita aplican la misma sección/nivel.
- [x] Objetos ajenos conservan 404 uniforme y totales sin fuga.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_clinical_permissions tests.test_clinical_history -v`.
- [x] `./.venv/Scripts/python.exe test-support/clinical_history/check.py` y `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py`.
- [x] Manual: consultar una lista y su detalle con permiso de otra sección y comprobar denegación uniforme.

**Archivos previstos:** `src/api/accounts/application/accounts_cases.py`, `src/api/clinical_records/application/access_cases.py`, `tests/test_clinical_permissions.py`, `tests/test_clinical_history.py`.

**Evidencia (2026-11-17):** readable_clinical_sections obtiene el orden cerrado desde el catálogo, sin una segunda lista de ocho secciones; clinical_read_scope reutiliza clinical_level_allows(read) después de identidad/contexto/dispositivo y cuenta activa. Se recorrieron listas, detalles, historias, resumen de mediciones y última visita: usan la misma guarda; clinical-history filtra por readable_clinical_sections antes de conteo/página. No se modificaron DAOs ni proyecciones. `uv run --locked --offline python -m unittest tests.test_clinical_permissions tests.test_clinical_history -v`: **11 pruebas, 0,239 s, OK**, incluida lectura de ocho secciones × tres niveles y dispositivo obligatorio. Probes `clinical_history/check.py` y `clinical_permissions/check.py`: **OK** sobre PostgreSQL/Keycloak Test; historial parcial total=5 sin notas/vacunas, detalle prohibido 403, aislamiento 404 y fallo de auditoría sin entrega. No se cambian respuestas ni permisos.

## C03 · Después de T07–T09

- [x] Escrituras, resultados, lecturas y reglas de objeto pasan sus pruebas.
- [x] Probes reales no muestran ampliación/reducción de acceso.
- [x] El usuario aceptó C03 el 2026-11-17 y autorizó T10 → T11 → T12 hasta C04.

**Cierre técnico C03 · 2026-11-17:** C02 aceptado por el usuario; T07–T09 Done, secuenciales y sin delegación. C03 fue aceptado después por el usuario; T10–T12 se habilitaron hasta C04.

- `UV_CACHE_DIR=.tmp/uv-cache`, `PYTHONPATH=tests`, `uv run --locked --offline python -m unittest discover -s tests -v`: **207 pruebas, 69,962 s, OK** sobre el árbol compartido actual.
- `uv run --locked --offline python -m unittest tests.test_authorization_policies tests.test_authorization_structure tests.test_accounts_structure -v`: **60 pruebas, 0,423 s, OK**; estructura activa en accounts, clinical_records, sync, services y schedule.
- Probes reales `access`, `sync`, `services`, `schedule`, `clinical_permissions` y `clinical_history`, mediante `./.venv/Scripts/python.exe test-support/<nombre>/check.py`: **OK**, PostgreSQL/Keycloak Test con bases aleatorias retiradas por los probes. Las pruebas enfocadas y los recorridos figuran en T07/T08/T09. Servicios y agenda se comprobaron antes del último reemplazo mecánico de la condición equivalente de bloqueo profesional por la referencia own_professional; la suite final cubre el código final. No se cambió el orden de bloqueos.
- Revisión del diff: no hay nuevo comportamiento de acceso en esta fase; se conserva AU-32 corregido y autorizado en C02, read/none no recuperan escrituras, ambigüedad falla cerrada, objetos ajenos mantienen ausencia, motivos globales y proyecciones conservan alcance. No hay cambios en DAOs, modelos HTTP, rutas, versiones de contrato, transacciones, tablas, migraciones o dependencias. No se instalaron herramientas ni se usaron APIs nuevas de framework; se reutilizan las fuentes y versiones registradas en C02.
- Se conserva el trabajo ajeno en D19, P-20261117-05-clinical-stage-3, docs/quality.md, docs/patient-clinical-record.md y tests/test_downloads.py; no se revirtieron cambios ni se tocaron Rust/Hub. Sin commits, remotos o despliegues. Consumidores, operación con datos reales y producción no se acreditan.
- Persiste el límite ya registrado de metadatos de generados (sourceSha256/sourceHead); no se reescriben contratos dentro de T07–T09 ni se declara export_contracts --check correcto. Las audiencias/capturas/cursor/SSE se integran en T10–T12 después de aceptar C03.

## T10 · Derivar audiencias de snapshot/delta del catálogo

**Estado:** Done. **Propietario:** `sync`. **Alcance:** M.

**Descripción:** conectar correspondencia entidad→audiencia→sección con captura materializada y filtrado incremental, conservando ventanas y grupos completos.

**Entradas y dependencias:** C03 aceptado; proyecciones actuales y caracterización T02.

**Datos, contratos, transacciones y consumidores:** captura REPEATABLE READ, journal y proyecciones validadas; sin cambiar cursores públicos.

**Criterios de aceptación:**
- [x] Toda entidad actual usa la misma correspondencia en captura y delta.
- [x] Totales, grupos invisibles y retiradas conservan comportamiento autorizado.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_downloads tests.test_clinical_history -v`.
- [x] `./.venv/Scripts/python.exe test-support/downloads/check.py` y `./.venv/Scripts/python.exe test-support/clinical_downloads/check.py`.
- [x] Manual: crear captura con subconjunto clínico y verificar que no contiene otras audiencias incluso en páginas posteriores.

**Archivos previstos:** `src/api/sync/application/download_cases.py`, `src/api/sync/application/snapshot_cases.py`, `src/api/sync/domain/downloads.py`, `tests/test_downloads.py`.

**Evidencia (2026-11-17):** projection_audiences describe las 25 entidades; las audiencias clínicas derivan de los descriptores de escritura. Captura filtra por la misma regla que delta antes de contar/materializar; revisión compartida exige sección de su proyección validada. Se conserva CLINICAL_AUDIENCES como valor derivado para consumidores de prueba existentes, sin tabla editable duplicada. Entidades/audiencias desconocidas o combinaciones incompatibles no se entregan. `uv run --locked --offline python -m unittest tests.test_downloads tests.test_clinical_history -v`: **10 pruebas, 0,027 s, OK**, con UV_CACHE_DIR=.tmp/uv-cache y PYTHONPATH=tests. Probes downloads y clinical_downloads: **OK**, PostgreSQL/Keycloak Test; captura RR/base coherente, páginas inmutables, itemCount/total autorizados, retirada de ventana, grupos invisibles completos con avance, alcance clínico, vencimiento/época y rollback. No cambia contrato, DAO ni ventana. Las páginas clínicas parciales y el delta invisible conservan ausencia de otras secciones.

## T11 · Aplicar el mismo alcance a cursores, época y SSE

**Estado:** Done. **Propietario:** `sync`. **Alcance:** M.

**Descripción:** reutilizar las decisiones de secciones/audiencia en validación de posición, reautorización de eventos y cierre por cambio de época.

**Entradas y dependencias:** T10; contratos de cursor/SSE existentes.

**Datos, contratos, transacciones y consumidores:** consultas breves, listener y leases sin cambios; no hay datos clínicos en avisos.

**Criterios de aceptación:**
- [x] Cursor, delta y stream rechazan alcance/época incompatibles de forma equivalente.
- [x] Revocación cierra streams y heartbeat/aviso no filtra contenido.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_events tests.test_downloads -v`.
- [x] `./.venv/Scripts/python.exe test-support/events/check.py`.
- [x] Manual: mantener un stream, reducir una sección y observar cierre/recuperación con nueva captura.

**Archivos previstos:** `src/api/sync/application/events_cases.py`, `src/api/sync/application/download_cases.py`, `tests/test_events.py`.

**Evidencia (2026-11-17):** sync_scope_matches concentra audiencia de rol, época y secciones legibles para posición de delta, captura y reautorización SSE. Cada canal conserva sus comprobaciones de identidad, objeto, tiempo y su código de error. Listener, leases, transacciones breves y firmas no cambian. `uv run --locked --offline python -m unittest tests.test_events tests.test_downloads -v`: **14 pruebas, 3,149 s, OK**. Probe real `events/check.py`: **OK**, dos procesos Uvicorn en Test, heartbeat mínimo, aviso sin avance aplicado, límite global, pérdida/recuperación de listeners y cierre por revocación. Se amplió el mismo probe: asistente abre stream con captura clínica, propietario retira notes, stream emite access_revoked sin data y termina; cursor previo devuelve 410; nueva captura excluye notes y su delta devuelve 200. Se conservan los fixtures y la limpieza del probe. No se promete borrado de datos ya descargados.

## T12 · Conservar versiones y épocas al cambiar permisos/pertenencias

**Estado:** Done. **Propietario:** `accounts` y `sync`. **Alcance:** M.

**Descripción:** conectar cambios de niveles/estado a la misma definición de alcance, preservando versiones, `NO_CHANGES`, época y proyecciones atómicas.

**Entradas y dependencias:** T11; `SetMemberClinicalPermissions`, `SetMembershipStatus` y dispositivos de cuenta.

**Datos, contratos, transacciones y consumidores:** cambio, recibo, auditoría, journal y época en una transacción; defaults anteriores intactos.

**Criterios de aceptación:**
- [x] Cambios efectivos incrementan exactamente una vez y `NO_CHANGES` no altera versión/época.
- [x] Desactivar/reactivar conserva niveles y clientes antiguos mantienen defaults.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_account_changes tests.test_clinical_permissions -v`.
- [x] `./.venv/Scripts/python.exe test-support/team/check.py` y `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py`.
- [x] Manual: repetir un mismo cambio, comprobar `NO_CHANGES` y recuperación desde una captura anterior.

**Archivos previstos:** `src/api/accounts/application/invitations_cases.py`, `src/api/accounts/application/accounts_cases.py`, `tests/test_account_changes.py`.

**Evidencia (2026-11-17):** changes_scope registra las siete acciones actuales que invalidan alcance; los casos de pertenencia/aceptación, gestión de cuenta/dispositivo y registro usan ese dato después de sus guardas/NO_CHANGES existentes. clinical_permission_values deriva las ocho columnas de permisos del catálogo y conserva perfil/valores iniciales. Se tocó management_cases además de los archivos previstos porque allí pertenecen SetAccountStatus y revocación/restauración; no se trasladaron consultas ni reglas a core. `uv run --locked --offline python -m unittest tests.test_account_changes tests.test_clinical_permissions -v`: **13 pruebas, 0,298 s, OK**. Probes team y clinical_permissions: **OK**; este último verifica explícitamente por SQL que cambio efectivo sube versión/época una vez y que duplicado/conflicto/NO_CHANGES no las alteran. Desactivar/reactivar conserva los ocho niveles; payload anterior mantiene defaults read_write; fallo de journal revierte y reintento confirma una vez. SSE y clinical_downloads se repitieron con T12 final: **OK**, cursor anterior 410, stream cerrado y captura nueva con alcance actual. Auditoría, recibo, journal y época conservan transacción y orden actuales.

## C04 · Después de T10–T12

- [x] Captura, delta, SSE y cambios de alcance pasan.
- [x] No hay diferencias de versión/época o recuperación.
- [x] El usuario revisa y acepta C04.

**Cierre técnico C04 · 2026-11-17:** C03 aceptado por el usuario. T10–T12 Done, secuenciales y sin delegación. El usuario autorizó después continuar hasta C06, pasando C04/C05 sin atribuir aceptación formal; T13–T17 quedan habilitadas en orden.

- `UV_CACHE_DIR=.tmp/uv-cache`, `PYTHONPATH=tests`, `uv run --locked --offline python -m unittest discover -s tests -v`: **210 pruebas, 70,365 s, OK**. Tras el ajuste final equivalente de tipado y audiencia nula, `uv run --locked --offline python -m unittest tests.test_downloads tests.test_account_changes -v`: **12 pruebas, 0,037 s, OK**.
- `uv run --locked --offline python -m unittest tests.test_authorization_policies tests.test_authorization_structure tests.test_accounts_structure -v`: **60 pruebas, 0,502 s, OK**. Sin Any, cast, supresiones, importaciones de repositorios ajenos o SQL nuevo en aplicación/dominio.
- Probes downloads, clinical_downloads, events, team y clinical_permissions: **OK** mediante sus check.py, PostgreSQL/Keycloak Test aislados. Events y clinical_downloads se repitieron después de integrar T12; clinical_permissions se repitió con la aserción SQL explícita de NO_CHANGES. Events arranca/cierra dos API locales; los probes validan clúster y eliminan sus bases aleatorias. No base personal/producción.
- Captura y delta comparten entidad→audiencia/sección; audiencia desconocida/incompatible se deniega. Se mantiene el orden, ventanas, retiradas, grupos completos/invisibles y totales de datos válidos. Capturas, cursor y SSE usan la misma comparación de rol/sección/época; una reducción cierra stream, invalida cursor y permite recuperación con captura nueva. Firmas, listener, leases, modelos JSON, rutas, contractVersion y modelRevision no cambian. Sin tablas, migraciones, dependencias, commits o despliegues.
- Se reutilizan BaseModel, tipos, helpers y APIs de prueba existentes; no se eligió framework ni API externa nueva. Las versiones/fuentes oficiales vigentes se registraron en C02. No se añadieron constantes de producto a core; CLINICAL_AUDIENCES conserva solo un nombre compatible de valor derivado para las pruebas existentes.
- Diff revisado y git diff --check correctos; enlaces locales comprobados al cierre. Trabajo ajeno preservado en D19, plan de Etapa 3, docs/database-schema.md, docs/patient-clinical-record.md, docs/quality.md y la prueba previa de audiencias de tests/test_downloads.py. Los cambios propios en ese test son adiciones; no se borraron las aserciones existentes.
- Persisten los límites anteriores de consumidores Rust/Hub, operación con datos reales y producción, y los metadatos de contratos generados desactualizados (sourceSha256/sourceHead). No se reescribieron generados ni se declara export_contracts --check correcto. Las carreras adicionales y matriz exhaustiva de seguridad/contratos corresponden a T13–T15 tras aceptar C04.

## T13 · Demostrar carreras de aceptación/revocación y cambio de sección

**Estado:** Done. **Propietario:** calidad de acceso/transacciones. **Alcance:** M.

**Descripción:** ampliar probes PostgreSQL con barreras reales para revocación global/cuenta, cambio de sección y aceptación concurrente.

**Entradas y dependencias:** C04 aceptado; servicios Test aislados y orden de bloqueos existente.

**Datos, contratos, transacciones y consumidores:** bases ficticias eliminadas al terminar; sin datos reales o cambios de esquema.

**Criterios de aceptación:**
- [x] Si revocación confirma primero no hay efecto posterior; si aceptación confirma primero su hecho persiste.
- [x] Cambio de sección y captura/escritura concurrente no entrega alcance retirado.

**Verificación:**
- [x] `./.venv/Scripts/python.exe test-support/access/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [x] `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py` y `uv run --locked python -m unittest discover -s tests -v`.
- [x] Manual: revisar trazas de bloqueo y SQL final, comprobando un único orden y ausencia de filas parciales.

**Archivos previstos:** `test-support/access/check.py`, `test-support/sync/check.py`, `test-support/clinical_permissions/check.py`.

**Evidencia en curso (2026-11-17):** se añadieron barreras de prueba después de escritura real y antes de commit, con asyncio.Event y pg_blocking_pids observado desde otra sesión. Sync cubre dos órdenes para revocación global y por cuenta (4 carreras): revocación primero no deja ficha ni recibo; aceptación primero conserva ambos; GET tras revocar devuelve 401/403 según ámbito. Clinical_permissions cubre dos órdenes de cambio de notes y escritura, más captura concurrente. La captura RR puede devolver TEMPORARY_FAILURE 503 al esperar un cambio confirmado; el reintento nuevo excluye notes. Una escritura denegada sin recibo devuelve 404 al consultar su resultado; una escritura previa autorizada exige permiso actual y devuelve 403 tras retirada. SQL prueba 0 o 1 efecto/recibo según orden.

Los probes sync y clinical_permissions pasan con código actual y PostgreSQL Test en la revisión clínica aprobada 20261116_10 mediante un wrapper temporal en memoria de migrate, sin cambiar archivos. **No sustituye integración de head:** el nuevo trabajo ajeno añadió 20261117_01_declared_medications; su historia refiere (account_id,id) sin clave única de esa pareja y la migración falla antes de los probes. No se modifica esa migración sin decisión; el cierre integral en head sigue pendiente. Los primeros intentos de fixture esperaban 201 para una captura serializada y 403 para un recibo inexistente; se corrigieron las expectativas según el comportamiento contractual real, sin tocar producto. Suite actual compartida: `uv run --locked --offline python -m unittest discover -s tests -v`, UV_CACHE_DIR=.tmp/uv-cache, PYTHONPATH=tests: **219 pruebas, 61,495 s, OK**, incluidas pruebas ajenas nuevas.

Fuentes de las barreras: PostgreSQL Test 18.3, https://www.postgresql.org/docs/18/functions-info.html#FUNCTIONS-INFO-SESSION-TABLE (pg_backend_pid/pg_blocking_pids), y Python 3.15.1, https://docs.python.org/3.15/library/asyncio-sync.html#asyncio.Event; se reutilizan AsyncSession.scalar/text existentes, sin dependencias o SQL de producto nuevo.


**Cierre del alcance T13:** los tres probes pasan sobre la revisión clínica aprobada; access también OK. Las carreras y la suite cumplen la aceptación de autorización. La prueba integral del nuevo head ajeno permanece como bloqueo externo de T17/C06 y no se presenta como pasada.

**Integración posterior de T13:** el otro agente añadió la UQ y completó los imports; sin modificar su migración, `test-support/sync/check.py` pasa en **head 20261117_01** con las cuatro carreras global/cuenta. `test-support/clinical_permissions/check.py` también pasa en head tras conservar el nuevo default declaredMedications en expectativas de prueba; las carreras de sección/captura y la ausencia de efectos/recibos quedan demostradas en el árbol integrado. El bloqueo anterior queda resuelto; se conserva su evidencia histórica.

## T14 · Ejecutar matriz HTTP de aislamiento y no divulgación

**Estado:** Done. **Propietario:** calidad de autorización HTTP. **Alcance:** M.

**Descripción:** cubrir IDs cruzados, rol/sección manipulados, resultados previos, páginas/totales y errores para todos los grupos de acciones.

**Entradas y dependencias:** T13; catálogo conectado a lecturas/escrituras/sync.

**Datos, contratos, transacciones y consumidores:** fixtures ficticios y estado remoto; no cambia contratos ni consumidores.

**Criterios de aceptación:**
- [x] Cuenta A no descubre objetos/recibos/resultados de B por éxito, error, total o página.
- [x] Credenciales y campos de actor/fecha manipulados no alteran autoridad.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_authorization tests.test_clinical_permissions tests.test_operations -v`.
- [x] `./.venv/Scripts/python.exe test-support/access/check.py` y `./.venv/Scripts/python.exe test-support/contracts/check.py`.
- [x] Manual: repetir una selección de ataques con servidor real y revisar logs/auditoría sin datos sensibles.

**Archivos previstos:** `tests/test_authorization.py`, `tests/test_clinical_permissions.py`, `test-support/access/check.py`.

**Evidencia (2026-11-17):** `uv run --locked --offline python -m unittest tests.test_authorization tests.test_clinical_permissions tests.test_operations -v`: **23 pruebas, 19,913 s, OK** (antes de añadir el caso de compatibilidad de T15). Probes access, sync y clinical_permissions en head compartido: **OK**. Se añaden ataques HTTP de campos userId/deviceId/role/issuedAt al emitir token y actorUserId/deviceId/accountId/role/acceptedAt al lote: 422 sin eco del valor ni efecto. Clínicos: UUID de nota conocida/ausente reciben 403 bajo sección retirada y 404 para actor ajeno; sin texto ni ID en error; lista ajena 404. Probes previos/finales por componente cubren cuenta, ficha, servicio, bloqueo, recibo, página y total. Se revisan errores/auditoría mínima sin tokens/payloads/cuerpos. `contracts/check.py` se ejecutó y falla por OpenAPI guardado anterior a la ampliación concurrente de medicación; la regeneración y repetición quedan en T15, sin atribuirle éxito a ese primer intento. Un intento inicial coincidió con un import incompleto ajeno (NameError); el otro agente lo completó y la repetición pasa. No se ocultó el fallo.

## T15 · Comprobar compatibilidad de contratos y ejemplos generados

**Estado:** Done. **Propietario:** contratos y consumidores API. **Alcance:** S.

**Descripción:** demostrar que la refactorización conserva OpenAPI, esquemas, capacidades, ejemplos y `AccessResponse` sin editar generados manualmente.

**Entradas y dependencias:** T14; exportador y ejemplos existentes.

**Datos, contratos, transacciones y consumidores:** `contractVersion`/`modelRevision` y huellas públicas conservados salvo diferencia justificada y aprobada.

**Criterios de aceptación:**
- [x] Dos generaciones y `--check` producen artefactos idénticos.
- [x] Ejemplos de acceso/resultados/cursores mantienen semántica y no exponen políticas internas.

**Verificación:**
- [x] `uv run --locked python -m scripts.export_contracts` y `uv run --locked python -m scripts.export_contracts --check`.
- [x] `./.venv/Scripts/python.exe test-support/contracts/check.py` y `uv build --offline`.
- [x] Manual: comparar capacidades y ejemplos de propietario/asistente con la línea base T01.

**Archivos previstos:** `scripts/export_contracts.py` solo si se detecta un defecto de exportación; artefactos generados según el exportador, sin edición manual.

**Evidencia parcial real (2026-11-17):** el usuario autorizó corregir la huella antigua: se omite únicamente declaredMedications=read_write al serializar el payload ya validado para la huella. No cambia validación, ejecución, nueve permisos ni respuestas. Prueba independiente con hash anterior de ocho campos: omitido/default → duplicate con resultado NO_CHANGES; read/none → IDEMPOTENCY_CONFLICT. `uv run --locked --offline python -m unittest tests.test_operations -v`: **10 pruebas, 10,369 s, OK**. `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py`: **OK** en head 20261117_01, incluye el mismo reintento HTTP, versión intacta y carreras reales.

Fuente oficial para exclusión anidada de la versión instalada Pydantic 2.14.1: https://raw.githubusercontent.com/pydantic/pydantic/v2.14.1/docs/concepts/serialization.md#advanced-include-and-exclude. Sin nuevas dependencias ni validación duplicada.

Dos ejecuciones consecutivas de `uv run --locked --offline python -m scripts.export_contracts`, comparación Get-FileHash y `--check`: **OK**, 81 rutas/131 esquemas HTTP/70 acciones. Se preservan contractVersion=1 y modelRevision=api-v1.3. Comparación contra HEAD: las 66 acciones anteriores siguen presentes; solo se añaden las cuatro de medicación del trabajo concurrente D19, con sus tres lecturas y noveno permiso. No se presenta esa ampliación ajena como parte de la normalización. Intentos previos de comparar generaciones coincidieron con cambios de fuentes ajenos; la comparación consecutiva posterior pasó.

`uv build --offline`: **OK**, wheel y sdist. Verificación zipfile/tarfile: 179 módulos fuente del wheel coinciden byte por byte con el árbol de esa ejecución; policies.py incluido, sin .env, .tmp o __pycache__; sdist de 258 entradas sin esos archivos. El aviso de uv sobre caché dentro del árbol no se convirtió en inclusión real.

**Fallo histórico:** `contracts/check.py` falló al migrar la revisión concurrente `20261117_02_care_plans`, primero por SQL inválido y luego por `IndexError` al construir el patrón de fecha. La repetición que consta en C05 superó este fallo.

## C05 · Después de T13–T15

**Revalidación del 2026-11-18:** el probe contractual aplicó todas las migraciones sobre PostgreSQL aislado y llegó a comparar `/openapi.json`. La comparación falló porque el contrato generado precede a las rutas nuevas de cuidados, informes y especialidades. `scripts.export_contracts --check` detectó 24 rutas nuevas fuera de su inventario. El usuario indicó que esas rutas se incorporen al cerrar la Etapa 3. Se conserva el control estricto y queda pendiente la prueba integral sobre los artefactos de esa etapa. `uv build --offline` produjo el wheel y el sdist.

- [x] Carreras y matriz HTTP pasan en PostgreSQL/Keycloak Test.
**Cierre técnico:** con los contratos de Etapa 3 ya generados, se comparó una exportación temporal con los seis archivos guardados. Solo difirieron el origen y las huellas derivadas. Se regeneraron y `--check` pasó con 113 rutas, 176 esquemas y 104 acciones. `contracts/check.py` pasó con PostgreSQL y Keycloak locales, incluidos los conjuntos de acceso y los ejemplos ficticios. Contra `8f30a5a`, se conservan las 66 acciones originales en orden, el conjunto online y ambos campos de versión. `uv build --offline` pasó.

- [x] Contratos, ejemplos y build conservan compatibilidad.
- [ ] El usuario revisa y acepta C05.

## T16 · Actualizar arquitectura, acceso y explicación contractual

**Estado:** Done. **Propietario:** documentación técnica. **Alcance:** M.

**Descripción:** sustituir el diseño previsto por la estructura real del catálogo, sus propietarios y garantías, conservando historia y límites externos.

**Entradas y dependencias:** C05 aceptado; diff y evidencia reales.

**Datos, contratos, transacciones y consumidores:** documentación alineada al código; sin declarar integración Rust/Hub o producción.

**Criterios de aceptación:**
- [x] La documentación describe una única fuente para descubrimiento/ejecución y propiedad por recurso.
- [x] Comentarios/docs antiguos no describen listas distribuidas retiradas.

**Verificación:**
- [x] `git diff --check` y validación de enlaces locales.
- [x] `uv run --locked python -m unittest tests.test_project_structure tests.test_accounts_structure -v`.
- [x] Manual: recorrer documentación y código para una acción de cada categoría.

**Archivos previstos:** `docs/architecture.md`, `docs/access-design.md`, `docs/api-v1.md`.

**Trabajo preparado y comprobado sin cerrar la dependencia C05:** arquitectura y acceso describen las funciones reales, fuente ejecutable única, propietarios por objeto y límites de transacción. Se corrigen referencias futuras de T03 y de Etapa 2, conservando el diseño concurrente de Etapa 3. La tabla refleja la extensión de medicación D19 sin atribuirla a este plan. Recorridos revisados: UpdateAccountPolicy → descriptor owner → management; CreatePatientNote → notes/read_write → notes; UpdateService → own_catalog → service_permission; snapshot/delta → projection_allowed; recuperación/SSE → sync_scope_matches.

`uv run --locked --offline python -m unittest tests.test_project_structure tests.test_accounts_structure -v`: **53 pruebas, 9,766 s, OK**. Comprobación pathlib/re de enlaces relativos en access-design, architecture y api-v1: **29 enlaces, OK**. `git diff --check`: **OK**, solo avisos LF/CRLF. Cierre formal de T16 pendiente de T15/C05 y de revisar cualquier ampliación concurrente posterior.

Para el cierre de T16 se ajustó la explicación de la huella a las cuatro secciones añadidas por Etapa 3. Se comprobaron 46 enlaces locales y pasaron 53 pruebas de estructura del proyecto y cuentas con `PYTHONPATH=tests`.

## T17 · Ejecutar cierre integral y registrar evidencia/límites

**Estado:** Done. **Propietario:** calidad y mantenimiento del plan. **Alcance:** M.

**Descripción:** ejecutar suite, probes afectados, contratos, build y revisión de diff; registrar resultados, tiempos y límites en las fuentes de evidencia.

**Entradas y dependencias:** T16; todos los cambios completos.

**Datos, contratos, transacciones y consumidores:** verificación final sobre el entregable; sin datos reales, despliegue o cambios en otros repositorios.

**Criterios de aceptación:**
- [x] Todos los comandos pertinentes pasan y cualquier límite previo se conserva explícito.
- [x] No hay archivos temporales no necesarios, trabajo ajeno alterado ni aceptaciones automáticas.

**Verificación:**
- [x] Suite y los trece probes indicados con los `check.py` reales y el intérprete de `.venv`.
- [x] `uv build --offline`, `python -m scripts.export_contracts --check` y `git diff --check`.
- [x] Flujo owner/assistant → cambio de permiso → reintento/resultado → nueva captura → SSE/recuperación, revisado mediante los probes HTTP con datos ficticios.

**Archivos previstos:** `tasks/P-20261117-01-authorization-policies/plan.md`, `tasks/P-20261117-01-authorization-policies/todo.md`, `docs/operations/development.md`, `docs/quality.md`.

**Cierre parcial real (2026-11-17):** suite `uv run --locked --offline python -m unittest discover -s tests -v`, UV_CACHE_DIR=.tmp/uv-cache y PYTHONPATH=tests: **226 pruebas, 87,521 s, OK**. Incluye las pruebas concurrentes existentes en ese momento. Los intentos sin permiso de sockets fallaron/bloquearon en el entorno aislado; la ejecución con acceso local completó la suite. No se confunden con fallos de producto.

Se ejecutaron los trece check.py reales en orden. **access, accounts, sync: exit 0**; sync acredita ambos órdenes de revocación global/cuenta en PostgreSQL. **team, services, schedule, clinical_permissions, clinical_history, clinical_downloads, downloads: exit 1** al aplicar la nueva migración ajena 20261117_02_care_plans por SQL inválido. **events, contracts, persistence: exit 1** en la misma revisión ya editada por su propietario, con IndexError: Replacement index 4 out of range al construir DATE.format. Ningún fallo acredita los cuerpos de esos probes. No se modifica ni retira la migración: el usuario indicó que la cierre el otro agente.

Los nuevos defaults de medicación se conservan en las expectativas de clinical_downloads sin retirar las comprobaciones anteriores. No se ha repetido el cierre tras nuevas modificaciones del otro agente. **T17/C06 pendientes** de una migración compartida válida y repetición de suite/probes/contratos/build sobre fuentes estables. No se declaran consumidores Rust/Hub ni producción probados; no commits, remotos, despliegues ni cambios en otros repositorios.

**Revalidación del bloqueo en la siguiente continuación:** se volvió a ejecutar `./.venv/Scripts/python.exe test-support/contracts/check.py` en PostgreSQL Test aislado: **exit 1** antes del cuerpo contractual, al crear care_plans en 20261117_02. El SQL compartido carece de coma tras account_id y de nombres en varias columnas text; no se cambia esa migración ajena. El tipo de error cambió durante las ediciones concurrentes, pero la condición pendiente sigue siendo la misma: head no migra. La suite de 226 pruebas anterior no demuestra el estado posterior a esas ediciones. Se mantiene C06 sin completar.

**Tercera comprobación consecutiva del bloqueo:** `test-support/contracts/check.py` vuelve a terminar con exit 1 durante la migración 20261117_02: PostgresSyntaxError cerca de patient_id. El propietario ya cambió los nombres de columnas, pero el head aún no migra. No hay un proceso propio pendiente de observar ni una comprobación integral que pueda completar sin ese cambio externo. El objetivo C06 queda bloqueado hasta que el otro agente cierre la migración; se conserva la autorización para retomar el cierre.

**Revalidación del 2026-11-18:** la suite `python -m unittest discover -s tests -q` con `PYTHONPATH=tests` y acceso a sockets locales pasó **244 pruebas**. Después de reutilizar el descriptor en la recuperación de recibos, `tests.test_operations` pasó **10 pruebas**. Las pruebas de catálogo y estructura pasaron **60 pruebas**. `git diff --check`, el build y la revisión de 16 enlaces locales de la especificación RBAC/ABAC pasaron. El bloqueo de migraciones quedó superado. El contrato integral sigue pendiente por el alcance de Etapa 3 registrado en C05.

**Probes del 2026-11-18:** pasaron `access`, `accounts`, `sync`, `team`, `services`, `schedule`, `clinical_history`, `downloads` y `events`. `clinical_permissions` y `clinical_downloads` pasaron al repetir con los nuevos campos y secciones esperados. La prueba de captura concurrente también verifica `DEPENDENCY_UNAVAILABLE` cuando PostgreSQL obliga a repetir la lectura. `persistence` llegó a la reversión de `20261117_04_specialty_templates` y falló al ejecutar `DROP TRIGGER guard_template_identity ON nightingale.specialty_templates` después de eliminar esa tabla. Queda pendiente repetir persistencia cuando Etapa 3 corrija esa reversión.

**Persistencia de autorización aislada de Etapa 3:** se ejecutó `check_result_scope_backfill` del probe de persistencia en una base PostgreSQL ficticia, con revisión final `20261116_03`. La prueba bajó a `20261116_01`, insertó los recibos históricos y volvió a subir. Pasaron las comprobaciones de asignación de sección, de recibos que conservan sección nula y de inmutabilidad. Se eliminó la base de prueba. La reversión completa desde el head compartido sigue pendiente del fallo de especialidades.

**Revalidación sobre `8b72ccc` y los cambios locales:** pasaron **259 pruebas** de la suite. `persistence/check.py` pasó la subida y reversión de todas las migraciones, además de los controles de rollback, permisos de base y concurrencia. `contracts/check.py`, el exportador y el build pasaron según la evidencia de T15. Se retiraron así los dos bloqueos del árbol compartido.

## C06 · Después de T16–T17

Pasaron los trece probes del cierre. En la primera ejecución, SSE consultó readiness antes de que uno de los procesos API recibiera el cierre de la conexión. El probe ahora espera y exige un `503` observado en cada proceso antes de seguir. Dos repeticiones pasaron con recuperación del aviso y cierre tras revocación. La evidencia corresponde a servicios locales y datos ficticios. Rust, Hub y producción quedan fuera de estas pruebas.

- [x] Suite, probes, contratos y build pasan sobre el entregable.
- [x] La documentación registra evidencia y límites sin acreditar consumidores/producción.
- [x] El usuario aceptó C06 el 2026-11-18 y pidió registrar los cambios en Git.
