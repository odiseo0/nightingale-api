# Lista de tareas: P-20261117-01-authorization-policies

**Plan:** [plan.md](plan.md). **Actualizado:** 2026-11-17. **Estado del plan:** Approved.

Todas las tareas están Todo. No iniciar hasta cumplir la precondición de C09 descrita en el plan. La evidencia se añade después de ejecutar; ninguna casilla de checkpoint representa aceptación anticipada.

## T01 · Caracterizar matriz de roles y acciones publicadas

**Estado:** Todo. **Propietario:** calidad de `accounts`. **Alcance:** S.

**Descripción:** fijar con pruebas el conjunto y orden actual de `allowedActions` para propietario/asistente, cuenta activa/inactiva y dispositivo pendiente/activo/revocado.

**Entradas y dependencias:** C09 de Etapa 2 aceptado; `get_access` y catálogo de operaciones vigentes.

**Datos, contratos, transacciones y consumidores:** solo pruebas. Conserva JSON y significado remoto; no cambia datos ni consumidores.

**Criterios de aceptación:**
- [ ] La matriz cubre todos los estados de cuenta/dispositivo y ambos roles sin omitir acciones.
- [ ] El orden actual y las excepciones de registro/reactivación quedan caracterizados.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_accounts tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/accounts/check.py`.
- [ ] Manual: comparar `GET A/access` para ambos roles y una instalación pendiente/revocada con la matriz aprobada.

**Archivos previstos:** `tests/test_accounts.py`, `tests/test_operations.py`.

**Evidencia:** pendiente.

## T02 · Caracterizar secciones, resultados y audiencias clínicas

**Estado:** Todo. **Propietario:** calidad de `clinical_records` y `sync`. **Alcance:** M.

**Descripción:** fijar la correspondencia acción→sección, niveles de lectura/escritura, recibos y entidad→audiencia para las ocho secciones.

**Entradas y dependencias:** T01; políticas actuales en `access_cases.py`, `operations_cases.py` y `download_cases.py`.

**Datos, contratos, transacciones y consumidores:** pruebas y fixtures ficticios; conserva recibos históricos, capturas y deltas.

**Criterios de aceptación:**
- [ ] Toda acción clínica y audiencia existente tiene casos para `none`, `read` y `read_write`.
- [ ] Duplicados/GET de escritura y recibos ambiguos conservan fail-closed.
- [ ] Captura/delta prueban grupos invisibles y totales autorizados.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_permissions tests.test_downloads -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py` y `./.venv/Scripts/python.exe test-support/clinical_downloads/check.py`.
- [ ] Manual: seguir una escritura y su reintento tras reducir permiso, comprobando que no devuelve contenido anterior.

**Archivos previstos:** `tests/test_clinical_permissions.py`, `tests/test_downloads.py`, `test-support/clinical_permissions/check.py`.

**Evidencia:** pendiente.

## T03 · Fijar correspondencia del catálogo en documentación vigente

**Estado:** Todo. **Propietario:** documentación de acceso/arquitectura. **Alcance:** M.

**Descripción:** incorporar a las fuentes vigentes la tabla acción→descriptor→regla de objeto y entidad→audiencia, sin duplicar modelos HTTP ni declarar código implementado.

**Entradas y dependencias:** T01–T02; especificación aprobada y resultados de caracterización.

**Datos, contratos, transacciones y consumidores:** documentación de diseño; no cambia esquema físico, transacciones o consumidores.

**Criterios de aceptación:**
- [ ] Todas las acciones/audiencias actuales tienen una única correspondencia prevista y regla de compatibilidad.
- [ ] Se distinguen autenticación, contexto de cuenta y atributos del recurso.
- [ ] Cualquier discrepancia encontrada queda registrada como pendiente, no corregida silenciosamente.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_authorization_structure tests.test_accounts_structure -v`.
- [ ] `git diff --check` y validación de enlaces locales de los documentos modificados.
- [ ] Manual: recorrer una acción administrativa, una clínica y una regla de objeto desde ruta hasta descriptor.

**Archivos previstos:** `docs/access-design.md`, `docs/architecture.md`, `docs/api-v1.md`.

**Evidencia:** pendiente.

## C01 · Después de T01–T03

- [ ] Suite y probes de línea base pasan con datos ficticios.
- [ ] La cobertura del catálogo es exhaustiva y no hay cambios de comportamiento.
- [ ] El usuario revisa y acepta C01.

## T04 · Introducir descriptores y evaluación pura de políticas

**Estado:** Todo. **Propietario:** `accounts/domain`. **Alcance:** M.

**Descripción:** crear un catálogo tipado y funciones puras para rol base, sección/nivel, estados de acceso y referencias de reglas de objeto.

**Entradas y dependencias:** C01 aceptado; correspondencia documentada en T03.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/sesión; no cambia persistencia ni contratos públicos.

**Criterios de aceptación:**
- [ ] El catálogo cubre exactamente las acciones actuales y deniega descriptores desconocidos.
- [ ] Las funciones reproducen la matriz T01/T02 sin `Any`, `cast` ni reglas arbitrarias.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_authorization_policies -v`.
- [ ] `uv run --locked python -m unittest tests.test_authorization_structure tests.test_accounts_structure -v`.
- [ ] Manual: inspeccionar decisiones representativas de owner, assistant y cada nivel clínico.

**Archivos previstos:** `src/api/accounts/domain/policies.py`, `tests/test_authorization_policies.py`.

**Evidencia:** pendiente.

## T05 · Derivar `AccessResponse.allowedActions` del catálogo

**Estado:** Todo. **Propietario:** `accounts`. **Alcance:** S.

**Descripción:** sustituir la composición manual de acciones por evaluación del catálogo, conservando forma, nombres y orden publicados.

**Entradas y dependencias:** T04; pruebas de caracterización T01.

**Datos, contratos, transacciones y consumidores:** misma lectura transaccional de contexto; respuesta pública equivalente y sin cambios de sync.

**Criterios de aceptación:**
- [ ] Todas las combinaciones T01 devuelven exactamente las mismas acciones y orden.
- [ ] `permissionEpoch`, estados y permisos clínicos permanecen iguales.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_accounts tests.test_authorization_policies -v`.
- [ ] `./.venv/Scripts/python.exe test-support/accounts/check.py`.
- [ ] Manual: comparar antes/después las respuestas `A/access` de propietario y asistente en los estados soportados.

**Archivos previstos:** `src/api/accounts/application/accounts_cases.py`, `tests/test_accounts.py`.

**Evidencia:** pendiente.

## T06 · Autorizar acciones administrativas del lote mediante descriptores

**Estado:** Todo. **Propietario:** `sync` y `accounts`. **Alcance:** M.

**Descripción:** sustituir las listas owner/member del despacho administrativo por descriptores, sin alterar orden de autenticación, bloqueos, recibos o ejecución.

**Entradas y dependencias:** T05; casos administrativos y probes de sync/team.

**Datos, contratos, transacciones y consumidores:** misma transacción de aceptación; efectos, recibos, auditoría y grupos conservados.

**Criterios de aceptación:**
- [ ] Owner/assistant obtienen los mismos rechazos y efectos para todas las acciones administrativas.
- [ ] Registro, invitación y reactivación conservan sus excepciones explícitas.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_operations tests.test_account_changes -v`.
- [ ] `./.venv/Scripts/python.exe test-support/sync/check.py` y `./.venv/Scripts/python.exe test-support/team/check.py`.
- [ ] Manual: enviar una acción owner-only como asistente y una operación válida como propietario, revisando estado y recibo.

**Archivos previstos:** `src/api/sync/application/operations_cases.py`, `tests/test_operations.py`, `tests/test_account_changes.py`.

**Evidencia:** pendiente.

## C02 · Después de T04–T06

- [ ] Pruebas de catálogo, acceso y operaciones administrativas pasan.
- [ ] Las acciones publicadas y las ejecutables coinciden sin cambios contractuales.
- [ ] El usuario revisa y acepta C02.

## T07 · Unificar sección/nivel de escrituras y resultados clínicos

**Estado:** Todo. **Propietario:** `clinical_records` y `sync`. **Alcance:** M.

**Descripción:** resolver sección/nivel desde el catálogo para ejecución, duplicados y GET de resultados, conservando alcance persistido y auditoría.

**Entradas y dependencias:** C02 aceptado; caracterización T02.

**Datos, contratos, transacciones y consumidores:** recibos y efectos en la misma transacción; sin cambios físicos o de respuesta.

**Criterios de aceptación:**
- [ ] Las ocho secciones aplican idéntica correspondencia en ejecución y recuperación.
- [ ] `read`/`none` no obtiene resultados de escritura y recibos ambiguos fallan cerrados.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_permissions tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [ ] Manual: repetir una operación clínica tras cada nivel de permiso y verificar ausencia de cuerpo/conflicto informativo.

**Archivos previstos:** `src/api/clinical_records/application/access_cases.py`, `src/api/sync/application/operations_cases.py`, `tests/test_clinical_permissions.py`.

**Evidencia:** pendiente.

## T08 · Integrar reglas de catálogo profesional y bloqueos

**Estado:** Todo. **Propietario:** `services`, `schedule` y `sync`. **Alcance:** M.

**Descripción:** referenciar reglas de objeto desde descriptores y conservar en sus componentes las comprobaciones de profesional propio, oferta y bloqueo global.

**Entradas y dependencias:** T07; casos públicos `service_permission` y `block_permission`.

**Datos, contratos, transacciones y consumidores:** mismos bloqueos profesional/cuenta y proyecciones en varias cuentas; sin importar repositorios ajenos.

**Criterios de aceptación:**
- [ ] Owner sin profesional propietario no edita catálogo/perfil ajeno.
- [ ] Bloqueos globales/locales y proyecciones mantienen motivos y alcance actuales.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_services tests.test_schedule tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/services/check.py` y `./.venv/Scripts/python.exe test-support/schedule/check.py`.
- [ ] Manual: intentar editar servicio y bloqueo global de otro profesional con UUID conocidos.

**Archivos previstos:** `src/api/services/application/services_cases.py`, `src/api/schedule/application/blocks_cases.py`, `src/api/sync/application/operations_cases.py`, `tests/test_services.py`, `tests/test_schedule.py`.

**Evidencia:** pendiente.

## T09 · Unificar lecturas y secciones legibles con el catálogo

**Estado:** Todo. **Propietario:** `accounts` y `clinical_records`. **Alcance:** M.

**Descripción:** usar el catálogo para `clinical_read_scope`, secciones legibles y acciones de lectura/historia/resumen sin cambiar DAOs ni proyecciones.

**Entradas y dependencias:** T07; rutas clínicas existentes ya concentran acceso en casos compartidos.

**Datos, contratos, transacciones y consumidores:** lecturas y auditoría en transacciones breves; filtros antes de contar/paginar.

**Criterios de aceptación:**
- [ ] Detalle, lista, historia, resumen y última visita aplican la misma sección/nivel.
- [ ] Objetos ajenos conservan 404 uniforme y totales sin fuga.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_permissions tests.test_clinical_history -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_history/check.py` y `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py`.
- [ ] Manual: consultar una lista y su detalle con permiso de otra sección y comprobar denegación uniforme.

**Archivos previstos:** `src/api/accounts/application/accounts_cases.py`, `src/api/clinical_records/application/access_cases.py`, `tests/test_clinical_permissions.py`, `tests/test_clinical_history.py`.

**Evidencia:** pendiente.

## C03 · Después de T07–T09

- [ ] Escrituras, resultados, lecturas y reglas de objeto pasan sus pruebas.
- [ ] Probes reales no muestran ampliación/reducción de acceso.
- [ ] El usuario revisa y acepta C03.

## T10 · Derivar audiencias de snapshot/delta del catálogo

**Estado:** Todo. **Propietario:** `sync`. **Alcance:** M.

**Descripción:** conectar correspondencia entidad→audiencia→sección con captura materializada y filtrado incremental, conservando ventanas y grupos completos.

**Entradas y dependencias:** C03 aceptado; proyecciones actuales y caracterización T02.

**Datos, contratos, transacciones y consumidores:** captura REPEATABLE READ, journal y proyecciones validadas; sin cambiar cursores públicos.

**Criterios de aceptación:**
- [ ] Toda entidad actual usa la misma correspondencia en captura y delta.
- [ ] Totales, grupos invisibles y retiradas conservan comportamiento autorizado.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_downloads tests.test_clinical_history -v`.
- [ ] `./.venv/Scripts/python.exe test-support/downloads/check.py` y `./.venv/Scripts/python.exe test-support/clinical_downloads/check.py`.
- [ ] Manual: crear captura con subconjunto clínico y verificar que no contiene otras audiencias incluso en páginas posteriores.

**Archivos previstos:** `src/api/sync/application/download_cases.py`, `src/api/sync/application/snapshot_cases.py`, `src/api/sync/domain/downloads.py`, `tests/test_downloads.py`.

**Evidencia:** pendiente.

## T11 · Aplicar el mismo alcance a cursores, época y SSE

**Estado:** Todo. **Propietario:** `sync`. **Alcance:** M.

**Descripción:** reutilizar las decisiones de secciones/audiencia en validación de posición, reautorización de eventos y cierre por cambio de época.

**Entradas y dependencias:** T10; contratos de cursor/SSE existentes.

**Datos, contratos, transacciones y consumidores:** consultas breves, listener y leases sin cambios; no hay datos clínicos en avisos.

**Criterios de aceptación:**
- [ ] Cursor, delta y stream rechazan alcance/época incompatibles de forma equivalente.
- [ ] Revocación cierra streams y heartbeat/aviso no filtra contenido.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_events tests.test_downloads -v`.
- [ ] `./.venv/Scripts/python.exe test-support/events/check.py`.
- [ ] Manual: mantener un stream, reducir una sección y observar cierre/recuperación con nueva captura.

**Archivos previstos:** `src/api/sync/application/events_cases.py`, `src/api/sync/application/download_cases.py`, `tests/test_events.py`.

**Evidencia:** pendiente.

## T12 · Conservar versiones y épocas al cambiar permisos/pertenencias

**Estado:** Todo. **Propietario:** `accounts` y `sync`. **Alcance:** M.

**Descripción:** conectar cambios de niveles/estado a la misma definición de alcance, preservando versiones, `NO_CHANGES`, época y proyecciones atómicas.

**Entradas y dependencias:** T11; `SetMemberClinicalPermissions`, `SetMembershipStatus` y dispositivos de cuenta.

**Datos, contratos, transacciones y consumidores:** cambio, recibo, auditoría, journal y época en una transacción; defaults anteriores intactos.

**Criterios de aceptación:**
- [ ] Cambios efectivos incrementan exactamente una vez y `NO_CHANGES` no altera versión/época.
- [ ] Desactivar/reactivar conserva niveles y clientes antiguos mantienen defaults.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_account_changes tests.test_clinical_permissions -v`.
- [ ] `./.venv/Scripts/python.exe test-support/team/check.py` y `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py`.
- [ ] Manual: repetir un mismo cambio, comprobar `NO_CHANGES` y recuperación desde una captura anterior.

**Archivos previstos:** `src/api/accounts/application/invitations_cases.py`, `src/api/accounts/application/accounts_cases.py`, `tests/test_account_changes.py`.

**Evidencia:** pendiente.

## C04 · Después de T10–T12

- [ ] Captura, delta, SSE y cambios de alcance pasan.
- [ ] No hay diferencias de versión/época o recuperación.
- [ ] El usuario revisa y acepta C04.

## T13 · Demostrar carreras de aceptación/revocación y cambio de sección

**Estado:** Todo. **Propietario:** calidad de acceso/transacciones. **Alcance:** M.

**Descripción:** ampliar probes PostgreSQL con barreras reales para revocación global/cuenta, cambio de sección y aceptación concurrente.

**Entradas y dependencias:** C04 aceptado; servicios Test aislados y orden de bloqueos existente.

**Datos, contratos, transacciones y consumidores:** bases ficticias eliminadas al terminar; sin datos reales o cambios de esquema.

**Criterios de aceptación:**
- [ ] Si revocación confirma primero no hay efecto posterior; si aceptación confirma primero su hecho persiste.
- [ ] Cambio de sección y captura/escritura concurrente no entrega alcance retirado.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe test-support/access/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py` y `uv run --locked python -m unittest discover -s tests -v`.
- [ ] Manual: revisar trazas de bloqueo y SQL final, comprobando un único orden y ausencia de filas parciales.

**Archivos previstos:** `test-support/access/check.py`, `test-support/sync/check.py`, `test-support/clinical_permissions/check.py`.

**Evidencia:** pendiente.

## T14 · Ejecutar matriz HTTP de aislamiento y no divulgación

**Estado:** Todo. **Propietario:** calidad de autorización HTTP. **Alcance:** M.

**Descripción:** cubrir IDs cruzados, rol/sección manipulados, resultados previos, páginas/totales y errores para todos los grupos de acciones.

**Entradas y dependencias:** T13; catálogo conectado a lecturas/escrituras/sync.

**Datos, contratos, transacciones y consumidores:** fixtures ficticios y estado remoto; no cambia contratos ni consumidores.

**Criterios de aceptación:**
- [ ] Cuenta A no descubre objetos/recibos/resultados de B por éxito, error, total o página.
- [ ] Credenciales y campos de actor/fecha manipulados no alteran autoridad.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_authorization tests.test_clinical_permissions tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/access/check.py` y `./.venv/Scripts/python.exe test-support/contracts/check.py`.
- [ ] Manual: repetir una selección de ataques con servidor real y revisar logs/auditoría sin datos sensibles.

**Archivos previstos:** `tests/test_authorization.py`, `tests/test_clinical_permissions.py`, `test-support/access/check.py`.

**Evidencia:** pendiente.

## T15 · Comprobar compatibilidad de contratos y ejemplos generados

**Estado:** Todo. **Propietario:** contratos y consumidores API. **Alcance:** S.

**Descripción:** demostrar que la refactorización conserva OpenAPI, esquemas, capacidades, ejemplos y `AccessResponse` sin editar generados manualmente.

**Entradas y dependencias:** T14; exportador y ejemplos existentes.

**Datos, contratos, transacciones y consumidores:** `contractVersion`/`modelRevision` y huellas públicas conservados salvo diferencia justificada y aprobada.

**Criterios de aceptación:**
- [ ] Dos generaciones y `--check` producen artefactos idénticos.
- [ ] Ejemplos de acceso/resultados/cursores mantienen semántica y no exponen políticas internas.

**Verificación:**
- [ ] `uv run --locked python -m scripts.export_contracts` y `uv run --locked python -m scripts.export_contracts --check`.
- [ ] `./.venv/Scripts/python.exe test-support/contracts/check.py` y `uv build --offline`.
- [ ] Manual: comparar capacidades y ejemplos de propietario/asistente con la línea base T01.

**Archivos previstos:** `scripts/export_contracts.py` solo si se detecta un defecto de exportación; artefactos generados según el exportador, sin edición manual.

**Evidencia:** pendiente.

## C05 · Después de T13–T15

- [ ] Carreras y matriz HTTP pasan en PostgreSQL/Keycloak Test.
- [ ] Contratos, ejemplos y build conservan compatibilidad.
- [ ] El usuario revisa y acepta C05.

## T16 · Actualizar arquitectura, acceso y explicación contractual

**Estado:** Todo. **Propietario:** documentación técnica. **Alcance:** M.

**Descripción:** sustituir el diseño previsto por la estructura real del catálogo, sus propietarios y garantías, conservando historia y límites externos.

**Entradas y dependencias:** C05 aceptado; diff y evidencia reales.

**Datos, contratos, transacciones y consumidores:** documentación alineada al código; sin declarar integración Rust/Hub o producción.

**Criterios de aceptación:**
- [ ] La documentación describe una única fuente para descubrimiento/ejecución y propiedad por recurso.
- [ ] Comentarios/docs antiguos no describen listas distribuidas retiradas.

**Verificación:**
- [ ] `git diff --check` y validación de enlaces locales.
- [ ] `uv run --locked python -m unittest tests.test_project_structure tests.test_accounts_structure -v`.
- [ ] Manual: recorrer documentación y código para una acción de cada categoría.

**Archivos previstos:** `docs/architecture.md`, `docs/access-design.md`, `docs/api-v1.md`.

**Evidencia:** pendiente.

## T17 · Ejecutar cierre integral y registrar evidencia/límites

**Estado:** Todo. **Propietario:** calidad y mantenimiento del plan. **Alcance:** M.

**Descripción:** ejecutar suite, probes afectados, contratos, build y revisión de diff; registrar resultados, tiempos y límites en las fuentes de evidencia.

**Entradas y dependencias:** T16; todos los cambios completos.

**Datos, contratos, transacciones y consumidores:** verificación final sobre el entregable; sin datos reales, despliegue o cambios en otros repositorios.

**Criterios de aceptación:**
- [ ] Todos los comandos pertinentes pasan y cualquier límite previo se conserva explícito.
- [ ] No hay archivos temporales no necesarios, trabajo ajeno alterado ni aceptaciones automáticas.

**Verificación:**
- [ ] `uv run --locked python -m unittest discover -s tests -v` y todos los probes `access`, `accounts`, `sync`, `team`, `services`, `schedule`, `clinical_permissions`, `clinical_history`, `clinical_downloads`, `downloads`, `events`, `contracts` y `persistence` mediante sus `check.py` reales.
- [ ] `uv build --offline`, `uv run --locked python -m scripts.export_contracts --check` y `git diff --check`.
- [ ] Manual: flujo owner/assistant → cambio de permiso → reintento/resultado → nueva captura → SSE/recuperación, con datos ficticios.

**Archivos previstos:** `tasks/P-20261117-01-authorization-policies/plan.md`, `tasks/P-20261117-01-authorization-policies/todo.md`, `docs/operations/development.md`, `docs/quality.md`.

**Evidencia:** pendiente.

## C06 · Después de T16–T17

- [ ] Suite, probes, contratos y build pasan sobre el entregable.
- [ ] La documentación registra evidencia y límites sin acreditar consumidores/producción.
- [ ] El usuario revisa y acepta C06 antes de extender políticas desde otros planes.
