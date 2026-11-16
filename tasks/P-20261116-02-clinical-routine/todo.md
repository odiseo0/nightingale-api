# Lista de tareas: P-20261116-02-clinical-routine

**Plan:** [plan.md](plan.md). **Estado del plan:** In progress. **Creado:** 2026-11-16. **Actualizado:** 2026-11-16.

El usuario autorizó T01 → T02 → T03 hasta C01 y, tras aceptarlo, T04 → T05 → T06 hasta C02. T19–T27 permanecen Todo. C01–C06 están aceptados; C07–C09 siguen pendientes de revisión y aceptación expresa.

El plan sucesor de Etapa 1 y el plan original quedaron Completed con C08 y C06 aceptados el 2026-11-16. Esta aceptación de cierres no autoriza ejecutar T01 de Etapa 2 ni acepta anticipadamente sus checkpoints. Trabajo secuencial, sin delegación, sin dependencias nuevas, commits, despliegues, datos reales ni cambios en otros repositorios.

## Resumen de estados

| ID | Tarea | Dependencia para iniciar | Estado | Alcance |
|---|---|---|---|---|
| T01 | Registrar decisiones de Etapa 2 | Aprobación del plan | Done | S |
| T02 | Definir datos, contratos y acceso | T01 | Done | M |
| T03 | Registrar línea base y casos ficticios | T02 | Done | M |
| T04 | Preparar secciones y migraciones de alcance | T03 y C01 aceptado | Done | M |
| T05 | Conectar configuración y resultados | T04 | Done | M |
| T06 | Comprobar aislamiento de permisos | T05 | Done | M |
| T07 | Persistir atenciones y proyección inicial de timeline | T06 y C02 aceptado | Done | M |
| T08 | Conectar atenciones y última visita | T07 | Done | M |
| T09 | Comprobar atención y última visita | T08 | Done | M |
| T10 | Persistir notas e historia | T09 y C03 aceptado | Done | M |
| T11 | Conectar notas | T10 | Done | M |
| T12 | Comprobar notas | T11 | Done | M |
| T13 | Persistir mediciones e historia | T12 y C04 aceptado | Done | M |
| T14 | Conectar tomas, correcciones y resúmenes | T13 | Done | M |
| T15 | Comprobar mediciones y trabajo offline | T14 | Done | M |
| T16 | Persistir vacunas e historia | T15 y C05 aceptado | Done | M |
| T17 | Conectar vacunas | T16 | Done | M |
| T18 | Comprobar vacunas | T17 | Done | M |
| T19 | Persistir antecedentes e historia | T18 y C06 aceptado | Done | M |
| T20 | Conectar antecedentes | T19 | Done | M |
| T21 | Comprobar antecedentes | T20 | Done | M |
| T22 | Integrar Etapa 1 en timeline | T21 y C07 aceptado | Done | M |
| T23 | Conectar historial integrado | T22 | Done | M |
| T24 | Completar captura y delta de Etapa 2 | T23 | Done | M |
| T25 | Comprobar historial y sincronización | T24 | Done | M |
| T26 | Publicar api-v1.3 y actualizar fuentes | T25 y C08 aceptado | Done | M |
| T27 | Ejecutar cierre integral de Etapa 2 | T26 | Done | M |

## T01 · Registrar decisiones de Etapa 2

**Estado:** Done. **Propietario:** documentación funcional. **Alcance:** S.

**Descripción:** integrar en las fuentes vigentes las decisiones O02/O03/O06/O07/O08/O14/O15, registrar la aprobación del plan y conservar los estados pendientes de Etapa 1.

**Entradas y dependencias:** plan aprobado y especificación clínica vigente. Sin dependencia de código.

**Datos, contratos, transacciones y consumidores:** solo documentación; no cambia producto ni consumidores.

**Criterios de aceptación:**
- [x] La especificación registra atención sin cierre, última visita, `serviceId` conservado, cinco mediciones, vacunas/antecedentes, permisos y descarga elegida.
- [x] El registro de decisiones y el índice enlazan este plan sin aceptar revisiones ajenas.
- [x] Plan/todo contienen las mismas 27 tareas y nueve checkpoints sin estados contradictorios.

**Verificación:**
- [x] Revisar enlaces locales, anclas, alcance, exclusiones y estados.
- [x] `git diff --check`.
- [x] Confirmar que no se modificó código, migraciones ni contratos generados.

**Evidencia 2026-11-16:** `docs/patient-clinical-record.md` 0.4, `docs/decisions.md` D13, `tasks/README.md`, `plan.md` y esta lista. D13 integra O02/O03/O06/O07/O08/O14/O15; las referencias antiguas a esos pendientes se actualizaron para Etapa 2. `git diff --check` terminó con código 0. No se modificó código, migraciones ni contratos generados. C01 sigue pendiente.

**Archivos probables:**
- `docs/patient-clinical-record.md`
- `docs/decisions.md`
- `tasks/README.md`
- `tasks/P-20261116-02-clinical-routine/plan.md`
- `tasks/P-20261116-02-clinical-routine/todo.md`

## T02 · Definir datos, contratos y acceso

**Estado:** Done. **Propietario:** documentación física, HTTP, acceso y sync. **Alcance:** M.

**Descripción:** incorporar a las fuentes únicas las once tablas, quince acciones, lecturas, permisos, timeline, descarga y compatibilidad `api-v1.3`.

**Entradas y dependencias:** T01; §§5–7 del plan aprobado.

**Datos, contratos, transacciones y consumidores:** define el diseño futuro sin implementarlo. Debe fijar FK, nulabilidad, versiones, historias, límites, auditoría, captura/delta y efectos en consumidores.

**Criterios de aceptación:**
- [x] Cada tabla tiene propietario, columnas, tipos, claves, restricciones, índices y conservación coherentes.
- [x] Acciones, rutas, payloads, permisos y proyecciones coinciden sin duplicar fuentes.
- [x] Las reglas de tiempo, corrección, anulación, historial y descarga no dejan pendientes de Etapa 2 sin resolver.

**Verificación:**
- [x] Revisión cruzada de columnas/FK/acciones/rutas con Python de biblioteca estándar.
- [x] Revisar referencias oficiales y versiones resueltas en `pyproject.toml`/`uv.lock`.
- [x] `git diff --check`.

**Evidencia 2026-11-16:** `database-schema.md` §11 define once tablas, cambios existentes, F82–F119, restricciones, índices e inventario objetivo; `api-v1.md` §11 define quince acciones, modelos, lecturas, permisos, captura/delta y publicación futura `api-v1.3`; `access-design.md`, `architecture.md` y `quality.md` incorporan acceso, propietarios y casos. Revisión cruzada con Python estándar: OK para 11 tablas, 15 acciones únicas, 7 grupos de rutas, 5 secciones y F82–F119. `git diff --check`: código 0. Versiones revisadas: Alembic 1.20.1, FastAPI 0.159.1, Pydantic 2.14.1 y SQLAlchemy 2.1.6; no se eligió ni usó una API nueva. Referencias oficiales conservadas en plan §11. Sin migraciones, modelos, rutas ni artefactos generados.

**Archivos probables:**
- `docs/database-schema.md`
- `docs/api-v1.md`
- `docs/access-design.md`
- `docs/architecture.md`
- `docs/quality.md`

## T03 · Registrar línea base y casos ficticios

**Estado:** Done. **Propietario:** calidad. **Alcance:** M.

**Descripción:** registrar el estado real de suite, estructura, analizador, migraciones y contratos, y preparar los casos E06–E14/E22–E24 con marcadores de privacidad.

**Entradas y dependencias:** T02 y comandos documentados en `test-support/README.md`.

**Datos, contratos, transacciones y consumidores:** solo evidencia de línea base y datos ficticios en entornos aislados.

**Criterios de aceptación:**
- [x] Los resultados y fallos previos quedan separados, sin convertir diagnósticos históricos en éxito.
- [x] Los casos preparados cubren todos los tipos clínicos, permisos, rollback, concurrencia y sync del plan.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -v`.
- [x] `./.venv/Scripts/python.exe -m scripts.export_contracts --check`, `alembic heads`/SQL offline y analizador documentado.
- [x] Revisar casos ficticios y `git diff --check`.

**Línea base ejecutada el 2026-11-16:**

| Comando | Resultado real y clasificación |
|---|---|
| `./.venv/Scripts/python.exe -m unittest discover -s tests -v` | **170 pruebas en 59,105 s, OK**, incluidos los controles de estructura. No hubo fallos nuevos. |
| `./.venv/Scripts/python.exe -m scripts.export_contracts --check` | **Fallo previo del árbol actual:** `AssertionError: Stale generated contract: openapi.json`, código 1. El cierre anterior había pasado; no se modificaron fuentes ejecutables ni se regeneraron artefactos en esta sesión. Queda pendiente, no se convierte en éxito. |
| `./.venv/Scripts/python.exe -m alembic heads` | Un head: `20261116_03`. |
| `./.venv/Scripts/python.exe -m alembic upgrade head --sql` | SQL offline generado sin conexión en `.tmp/clinical-stage2/baseline/offline.sql`, 1934 líneas. No prueba aplicar el diseño futuro ni integridad/concurrencia. |
| `node .../basedpyright/index.js --pythonpath .venv/Scripts/python.exe --pythonversion 3.15 src --outputjson` | **15 errores históricos**, 0 avisos, 141 archivos, 10,123 s; código 1. Coincide con T20 del sucesor: accounts/patients/users, Valkey y sentinels. Ninguno nuevo ni supresiones. Salida temporal en `.tmp/clinical-stage2/baseline/basedpyright.json`. |

No se conectó a la base personal ni se usó SQLite. No se ejecutaron probes PostgreSQL/Keycloak en esta fase documental; la línea base no acredita consumidores, operación o producción.

**Casos ficticios preparados, no ejecutados:**

| Caso | Entrada ficticia y marcador privado | Resultado que deberá comprobarse |
|---|---|---|
| E06 | Atención sin cita con motivo `PRIV-E06-MOTIVO`; reserva aparte sin `serviceId` | Guarda motivo sin inventar servicio/cita; reserva conserva su rechazo actual |
| E07 | Nota `PRIV-E07-NOTA` con autor/fecha | Conserva versiones; no crea condición/diagnóstico ni cambia última visita |
| E08 | Pesos 70 y 69 kg, `PRIV-E08-SERIE` | Dos tomas válidas ordenadas por `measuredAt` |
| E09 | Corrección 700→70 kg, `PRIV-E09-CORRECCION` | Historia conserva 700; vista/serie usa 70 |
| E10 | Toma histórica cargada hoy, `PRIV-E10-HISTORICO` | Hecho/captura/aceptación separados; no desplaza toma más reciente |
| E11 | Captura offline `PRIV-E11-OFFLINE` y respuesta perdida | Aceptación conserva fecha clínica; mismo operationId no repite efecto |
| E12 | Presión con diastólica nula, `PRIV-E12-PRESION` | Conserva incertidumbre; no crea cero ni mezcla tomas |
| E13 | Vacuna declarada `PRIV-E13-VACUNA`, fecha `2020-05` | Conserva fuente/precisión y detalles ausentes; no afirma administración actual |
| E14 | Dos atenciones válidas y una anulada, `PRIV-E14-VISITA` | Última visita por `occurredAt`/cuenta; citas/notas/ficha no la alteran |
| E22 | Dos ediciones de una versión y reintento `PRIV-E22-IDEMPOTENCIA` | Una sola escritura, conflicto de versión y resultado autorizado recuperable |
| E23 | Asistente con secciones combinadas y revocación, `PRIV-E23-REVOCACION` | Sin lectura/resultado/captura/delta fuera de alcance ni fuga por errores/totales |
| E24 | Hechos antiguos `PRIV-E24-HISTORIA` fuera de ventana | Captura/delta los conserva; cursor/recibo vencido no borra historia funcional |

Todos los marcadores son sintéticos. Las pruebas futuras deben buscarlos en errores, logs, auditoría, cursores y timeline para demostrar su ausencia. Integridad, rollback y concurrencia usarán PostgreSQL Test 18.3 aislado y Keycloak Test; ningún caso queda comprobado por esta preparación.

**Archivos probables:**
- `tasks/P-20261116-02-clinical-routine/todo.md`
- Evidencia temporal ignorada en `.tmp/clinical-stage2/baseline/`

## C01 · Diseño de Etapa 2

- [x] Decisiones integradas y diseño físico/HTTP/acceso/sync completo y coherente; revisión técnica realizada, no aceptación del usuario.
- [x] Línea base y casos ficticios registrados con evidencia real, incluidos fallos previos.
- [x] El usuario aceptó C01 el 2026-11-16 y autorizó T04 → T05 → T06 hasta C02.

**Evidencia de revisión C01:** T01–T03 Done; 27 tareas y nueve checkpoints coinciden entre plan/lista. Revisión cruzada: 11 tablas, F82–F119, 15 acciones únicas, siete grupos de rutas, cinco secciones, captura/delta y compatibilidad presentes. Enlaces de los bloques nuevos resueltos. Los chequeos generales de enlaces detectaron solo destinos históricos ausentes fuera de los bloques nuevos (`nightingale-desktop-docs/README.md`, `master-plan.md`, `technical-architecture.md`, `srs.md`, `decisions/transactional-sync-three-projects.md`); se conservan como límites previos.

Suite: 170 pruebas OK. Contratos: fallo previo por `openapi.json` desactualizado. Analizador: 15 errores históricos, sin nuevos. Alembic: head `20261116_03` y SQL offline correcto. `git diff --check`: código 0; solo avisos LF/CRLF. C08/C06 anteriores se conservan aceptados como ya estaban; C01 y T04 no se aceptan/inician.

## T04 · Preparar secciones y migraciones de alcance

**Estado:** Done. **Propietario:** `accounts` y `sync`. **Alcance:** M.

**Descripción:** ampliar pertenencias, recibos, capturas, cursores y audiencias con `encounters`, `notes`, `measurements`, `immunizations` y `antecedents`, conservando filtrado cerrado.

**Entradas y dependencias:** T03 y C01 aceptado; diseño físico de T02.

**Datos, contratos, transacciones y consumidores:** migración aditiva con `read_write` inicial para asistentes. Datos nuevos quedan excluidos hasta que el consumidor solicite clínica. Cambios de niveles conservan la época.

**Criterios de aceptación:**
- [x] Los conjuntos cerrados de recibos/capturas/cursores/audiencias admiten las cinco secciones sin duplicados.
- [x] Una captura anterior o sin clínica no recibe proyecciones nuevas.
- [x] La migración pasa upgrade/downgrade/upgrade y fallo sin DDL parcial.

**Verificación:**
- [x] Pruebas unitarias de alcance y audiencias en `tests/test_clinical_permissions.py` y descargas.
- [x] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [x] Revisar que el filtrado ocurre antes de validar o construir proyecciones.

**Evidencia T04:** migración `20261116_04`, cinco columnas y conjuntos cerrados ampliados; modelos/dominio/audiencias/cursores actualizados. Ocho pruebas unitarias OK. SQL offline y head correctos. Primer probe sin servicio: `WinError 1225`; se inició PostgreSQL Test 18.3 y la repetición pasó upgrade/downgrade/upgrade, rollback de revisión fallida, permisos SQL y escritores. Sin base personal ni SQLite.

**Archivos probables:**
- `migrations/versions/20261116_04_stage2_clinical_sections.py`
- `src/api/accounts/domain/accounts.py`
- `src/api/accounts/repository/models.py`
- `src/api/sync/domain/downloads.py`
- `tests/test_clinical_permissions.py` y pruebas de descarga

## T05 · Conectar configuración y resultados

**Estado:** Done. **Propietario:** `accounts` y `sync`. **Alcance:** M.

**Descripción:** conectar valores iniciales, consulta/configuración por propietario, acciones permitidas y autorización de resultados para las nuevas secciones.

**Entradas y dependencias:** T04 y política actual de `access_cases.py`.

**Datos, contratos, transacciones y consumidores:** cambios de permiso conservan versión/época/recibo/auditoría/journal juntos. Payloads anteriores omiten las nuevas secciones y obtienen su default documentado.

**Criterios de aceptación:**
- [x] Propietario configura cada sección; asistentes existentes/nuevos conservan el valor inicial acordado.
- [x] `read`/`none` impide escrituras, duplicados y resultados; `read_write` los permite sin mezclar secciones.
- [x] Acciones permitidas no contienen duplicados ni permisos incompatibles con el estado del dispositivo.

**Verificación:**
- [x] Pruebas enfocadas de cuentas, operaciones y permisos clínicos.
- [x] `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py`.
- [x] Probar duplicado/GET desde nueva instalación autorizada y después de revocar.

**Evidencia T05:** contexto, altas, configuración, acciones permitidas y alcance de resultados usan ocho secciones. Ocho pruebas y 53 controles estructurales OK. Basedpyright acotado: un diagnóstico histórico `Err[Never]`, ninguno nuevo. El primer probe requirió iniciar Keycloak Test; después detectó que recibos de payloads antiguos omitían defaults. Se corrigió la normalización del modelo validado y el probe final pasó configuración, idempotencia, carreras, rollback y revocación.

**Archivos probables:**
- `src/api/accounts/domain/accounts.py`
- `src/api/accounts/application/accounts_cases.py`
- `src/api/accounts/application/invitations_cases.py`
- `src/api/clinical_records/application/access_cases.py`
- `src/api/sync/application/operations_cases.py`

## T06 · Comprobar aislamiento de permisos

**Estado:** Done. **Propietario:** calidad de acceso. **Alcance:** M.

**Descripción:** probar las cinco secciones en lecturas, acciones, resultados, capturas y carreras de revocación, sin requerir todavía datos clínicos nuevos.

**Entradas y dependencias:** T05; matriz Q01/Q02/Q04/Q06/Q07 y casos CL-16–CL-19 adaptados.

**Datos, contratos, transacciones y consumidores:** bases aleatorias y datos ficticios. Sin cambios de contrato.

**Criterios de aceptación:**
- [x] Ninguna sección filtra datos por errores, totales, duplicados, resultados o deltas fuera de alcance.
- [x] Cambio de niveles incrementa versión/época e invalida capturas/cursores/SSE.
- [x] La carrera revocación/aceptación conserva un orden comprobable.

**Verificación:**
- [x] `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py` con PostgreSQL/Keycloak Test.
- [x] Probe `clinical_downloads` pertinente al cambio de época; no cambió SSE.
- [x] Revisar auditoría sin cuerpos, filtros ni cursores.

**Evidencia T06:** probes `clinical_permissions` y `clinical_downloads` correctos en bases aleatorias eliminadas al terminar. Cubren cinco secciones, `none`/`read`, resultados/duplicados, captura/delta, época, auditoría, rollback y revocación. Las quince acciones futuras conservan alcance pero devuelven `UNSUPPORTED_OPERATION` hasta su implementación; no se acredita funcionalidad clínica ni integración de consumidores.

**Archivos probables:**
- `tests/test_clinical_permissions.py`
- `test-support/clinical_permissions/check.py`
- `test-support/clinical_downloads/check.py`

## C02 · Permisos de Etapa 2

- [x] Las nuevas secciones y resultados aplican acceso vigente sin filtraciones.
- [x] Migraciones, carreras y cambio de época terminan correctamente.
- [x] El usuario aceptó C02 el 2026-11-16 y autorizó T07 → T08 → T09 hasta C03.

**Evidencia C02:** suite completa 171 pruebas en 59,309 s, OK. Persistencia y probes `clinical_permissions`/`clinical_downloads` correctos con PostgreSQL Test 18.3 y Keycloak Test, bases aleatorias eliminadas. Head/SQL offline `20261116_04`, `git diff --check` correcto. Basedpyright: 15 errores históricos, 0 avisos, sin nuevos. `export_contracts --check` conserva el fallo de `openapi.json` desactualizado; publicación corresponde a T26. T07 no se inició.

## T07 · Persistir atenciones y proyección inicial de timeline

**Estado:** Done. **Propietario:** `encounters` y `clinical_records`. **Alcance:** M.

**Descripción:** implementar atención actual/historia, FK a ficha/cita/profesional, guardas de identidad y la primera proyección de `patient_clinical_timeline`, usada de inmediato por atenciones.

**Entradas y dependencias:** T06 y C02 aceptado; §§5.1/5.2/5.7 del plan y FHIR Encounter.

**Datos, contratos, transacciones y consumidores:** nuevas tablas y UQ técnica en citas. Estado/historia/timeline comparten aceptación. No cambia reserva ni escribe en `appointment_histories`.

**Criterios de aceptación:**
- [x] Atención sin cita y varias por cita persisten sin ciclo de cierre ni UQ por cita.
- [x] No se puede cruzar paciente/cuenta/cita/profesional ni reasignar identidad.
- [x] Historia y timeline coinciden con el estado actual al commit y son reconstruibles.

**Verificación:**
- [ ] SQL offline, instalación desde vacío y actualización desde head anterior.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py` y casos SQL de FK/guardas/historia.
- [ ] Comprobar que `CompleteAppointment`, cancelación y ausencia no crean atención.

**Archivos probables:**
- `migrations/versions/20261116_05_clinical_encounters.py`
- `src/api/encounters/repository/models.py`
- `src/api/encounters/repository/dao.py`
- `src/api/clinical_records/repository/models.py` y DAO de timeline
- Pruebas de estructura/persistencia pertinentes

## T08 · Conectar atenciones y última visita

**Estado:** Done. **Propietario:** `encounters` y `sync`. **Alcance:** M.

**Descripción:** implementar alta, edición, anulación, lista, detalle, historia y última visita de atenciones, con permisos y auditoría.

**Entradas y dependencias:** T07; acceso compartido, aceptación existente y reglas temporales del plan.

**Datos, contratos, transacciones y consumidores:** quince acciones del plan se incorporan por bloques; este bloque añade tres. Resultados conservan `clinical_section=encounters`; sync publica el estado actual.

**Criterios de aceptación:**
- [x] Autor, `occurredAt`, captura local, aceptación, versión e historia son correctos y no se aceptan instantes futuros.
- [x] Última visita usa la atención válida más reciente de la cuenta/paciente y devuelve nulos si no existe.
- [x] Lecturas/escrituras/duplicados aplican permisos y auditoría sin contenido clínico.

**Verificación:**
- [ ] Pruebas de esquema/casos y recorridos HTTP con datos ficticios.
- [ ] Probe nuevo `test-support/encounters/check.py` con rollback y respuesta perdida.
- [ ] Comprobar lista/detalle/historia, empate de última visita y contrato en memoria.

**Archivos probables:**
- `src/api/encounters/domain/encounters.py`
- `src/api/encounters/application/encounters_cases.py`
- `src/api/encounters/infrastructure/encounters_api.py`
- `src/api/sync/domain/operations.py` y composición de operaciones
- `tests/test_encounters.py` y `test-support/encounters/check.py`

## T09 · Comprobar atención y última visita

**Estado:** Done. **Propietario:** calidad de atención. **Alcance:** M.

**Descripción:** comprobar E06/E14, aislamiento, versiones, anulación, empates y ausencia de efectos automáticos sobre citas.

**Entradas y dependencias:** T08 y casos ficticios de T03.

**Datos, contratos, transacciones y consumidores:** datos ficticios, sin cambios de contrato ni integración de escritorio.

**Criterios de aceptación:**
- [x] Motivo sin servicio/cita se conserva y la reserva actual sigue exigiendo `serviceId`.
- [x] Citas futuras/canceladas/ausentes, edición de ficha o nota no alteran última visita.
- [x] Versiones antiguas no sobrescriben y anulación retira la atención del cálculo.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_encounters.py" -v`.
- [ ] `./.venv/Scripts/python.exe test-support/encounters/check.py` con carreras reales.
- [ ] Revisar auditoría, aislamiento y rollback sin datos parciales.

**Archivos probables:**
- `tests/test_encounters.py`
- `test-support/encounters/check.py`

**Evidencia T07–T09:** migración `20261116_05`, modelos/DAOs de atenciones y timeline; tres acciones, cuatro lecturas, captura/delta y permisos conectados. Casos E06/E11/E14, varias atenciones por cita, duplicados, carrera de versiones, anulación, rollback, captura y privacidad comprobados en `test-support/encounters/check.py`. Se corrigieron UQ de historia, nombre físico singular de timeline, nombres DAO y serialización UTC/Z detectados por pruebas reales.

## C03 · Atención clínica

- [x] Atenciones, vínculos, correcciones y última visita cumplen E06/E14 sin ciclo de cierre.
- [x] Persistencia, HTTP, acceso, idempotencia y carreras tienen evidencia real.
- [x] El usuario aceptó C03 el 2026-11-16 y autorizó T10 → T11 → T12 hasta C04.

**Evidencia C03:** 180 pruebas en 63,090 s, OK; 58 controles estructurales incluidos. Persistencia y descargas clínicas correctas; probe de atenciones correcto. Head `20261116_05` y SQL offline correctos. Basedpyright: 15 errores históricos, 0 avisos, sin nuevos. Catálogo documental coincide con código; `export_contracts --check` llega a `openapi.json` desactualizado, pendiente de T26. `git diff --check` correcto. T10 no se inició.

## T10 · Persistir notas e historia

**Estado:** Done. **Propietario:** `clinical_records`. **Alcance:** M.

**Descripción:** implementar notas actuales e historias con cuerpo, autor, tiempo, vínculo opcional con atención y proyección de timeline.

**Entradas y dependencias:** T09 y C03 aceptado; §5.3 del plan.

**Datos, contratos, transacciones y consumidores:** dos tablas nuevas; nota/atención deben pertenecer a la misma ficha. Historia y timeline comparten transacción.

**Criterios de aceptación:**
- [x] Una nota puede existir sin atención y otra vincularse sin cruzar paciente/cuenta.
- [x] Cuerpo no vacío, versiones consecutivas e historia append-only.

**Verificación:**
- [ ] Pruebas de dominio y persistencia para nulos, texto, FK, versiones e inmutabilidad.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Confirmar que una nota no cambia última visita ni crea condiciones.

**Archivos probables:**
- `migrations/versions/20261116_06_patient_notes.py`
- `src/api/clinical_records/repository/models.py`
- `src/api/clinical_records/repository/dao.py`
- `tests/test_notes.py`

## T11 · Conectar notas

**Estado:** Done. **Propietario:** `clinical_records` y `sync`. **Alcance:** M.

**Descripción:** conectar alta, edición, anulación, lista, detalle e historia de notas, reutilizando acceso, aceptación y proyecciones existentes.

**Entradas y dependencias:** T10; O06 y patrón de escrituras de Etapa 1.

**Datos, contratos, transacciones y consumidores:** tres acciones nuevas, alcance `notes`, efecto/historia/timeline/recibo/auditoría/grupo atómicos.

**Criterios de aceptación:**
- [x] Edición conserva versiones sin cierre ni motivo obligatorio; `NO_CHANGES` no añade historia.
- [x] Duplicados, respuesta perdida y revocación aplican el permiso vigente.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_notes.py" -v`.
- [ ] Probe nuevo `test-support/notes/check.py` con HTTP, rollback y respuesta perdida.
- [ ] Revisar contratos en memoria y ausencia de cuerpos en auditoría.

**Archivos probables:**
- `src/api/clinical_records/domain/notes.py`
- `src/api/clinical_records/application/notes_cases.py`
- `src/api/clinical_records/infrastructure/notes_api.py`
- `src/api/sync/domain/operations.py` y composición
- `tests/test_notes.py` y `test-support/notes/check.py`

## T12 · Comprobar notas

**Estado:** Done. **Propietario:** calidad de notas. **Alcance:** M.

**Descripción:** comprobar E07, acceso independiente, aislamiento, correcciones y ausencia de efectos clínicos automáticos.

**Entradas y dependencias:** T11 y marcadores ficticios de privacidad.

**Datos, contratos, transacciones y consumidores:** datos ficticios, sin cambios funcionales.

**Criterios de aceptación:**
- [x] La nota conserva autor/fecha/versiones y no crea diagnóstico, condición ni última visita.
- [x] Objeto ajeno, versión antigua y permiso retirado no revelan ni alteran datos.

**Verificación:**
- [ ] Pruebas unitarias y `./.venv/Scripts/python.exe test-support/notes/check.py`.
- [ ] Comprobar errores/logs/auditoría sin marcadores clínicos.
- [ ] Ejecutar estructura y contratos pertinentes.

**Archivos probables:**
- `tests/test_notes.py`
- `test-support/notes/check.py`

## C04 · Notas

- [x] E07 y las reglas de edición/historia/acceso están comprobadas.
- [x] No existen efectos clínicos automáticos ni contenido sensible en auditoría.
- [x] El usuario aceptó C04 el 2026-11-16 y autorizó T13 → T14 → T15 hasta C05.

**Evidencia T10–T12/C04:** migración `20261116_06`, modelos/DAOs, tres acciones y tres lecturas; timeline y captura de estado válido. Pruebas unitarias de ausencia/null, autor y capacidades; probe real E07 con notas independientes/vinculadas, duplicados, NO_CHANGES, versiones, anulación, rollback, sync y permisos. Persistencia y 58 controles estructurales correctos. Basedpyright acotado: 0 errores/avisos. Cierre: 183 pruebas en 56,355 s, OK; head `20261116_06`; analizador global conserva 15 errores históricos; contratos llegan al límite conocido de `openapi.json`. `git diff --check` correcto. T13 no se inició.

## T13 · Persistir mediciones e historia

**Estado:** Done. **Propietario:** dominio y `clinical_records`. **Alcance:** M.

**Descripción:** implementar cinco tipos de medición, valores Decimal/UCUM, presión por componentes, tiempos, contexto, historia y timeline.

**Entradas y dependencias:** T12 y C04 aceptado; §5.4 del plan y FHIR Observation/Vital Signs.

**Datos, contratos, transacciones y consumidores:** dos tablas nuevas, formas cerradas por tipo, sin unidades alternativas ni derivados de Etapa 3.

**Criterios de aceptación:**
- [x] Cada tipo exige su valor y unidad; presión admite un componente ausente y exige al menos uno.
- [x] Rangos, valores finitos, tiempos y forma combinada se protegen sin inventar ceros.
- [x] Estado actual/historia/timeline conservan versión y contenido al commit.

**Verificación:**
- [ ] Pruebas de dominio para tipos, unidades, rangos, NaN/infinito, nulos y fechas.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py` y SQL de restricciones.
- [ ] Revisar fuentes oficiales y ausencia de dependencias nuevas.

**Archivos probables:**
- `migrations/versions/20261116_07_patient_measurements.py`
- `src/api/clinical_records/domain/measurements.py`
- `src/api/clinical_records/repository/models.py`
- `src/api/clinical_records/repository/dao.py`
- `tests/test_measurements.py`

## T14 · Conectar tomas, correcciones y resúmenes

**Estado:** Done. **Propietario:** `clinical_records` y `sync`. **Alcance:** M.

**Descripción:** conectar nueva toma, corrección, anulación, lista, detalle, historia y últimos valores por tipo, incluida edad en la fecha de la toma.

**Entradas y dependencias:** T13; R09/R19/R20 y reglas de nacimiento existentes.

**Datos, contratos, transacciones y consumidores:** tres acciones nuevas y proyecciones de estado actual. Nueva toma usa ID nuevo; corrección conserva historia; último valor usa `measuredAt`, no carga.

**Criterios de aceptación:**
- [x] Dos tomas coexisten; corrección actualiza la serie sin dejar el valor anterior como válido.
- [x] Edad devuelve `ageYears`/`ageAsOf` y versión de ficha usada, o nulo si falta nacimiento; no se persiste.
- [x] Historia, permisos, recibo, auditoría, timeline y sync comparten aceptación.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_measurements.py" -v`.
- [ ] Probe nuevo `test-support/measurements/check.py` con tomas/corrección/histórico/empates.
- [ ] Probar duplicados, versión antigua, rollback y respuesta perdida.

**Archivos probables:**
- `src/api/clinical_records/application/measurements_cases.py`
- `src/api/clinical_records/infrastructure/measurements_api.py`
- `src/api/sync/domain/operations.py` y composición
- `tests/test_measurements.py`
- `test-support/measurements/check.py`

## T15 · Comprobar mediciones y trabajo offline

**Estado:** Done. **Propietario:** calidad de mediciones. **Alcance:** M.

**Descripción:** comprobar E08–E12, captura local/aceptación, aislamiento, revocación y carreras sin introducir analítica de Etapa 3.

**Entradas y dependencias:** T14 y casos ficticios preparados.

**Datos, contratos, transacciones y consumidores:** datos ficticios y bases aisladas. No acredita aplicación SQLite ni curvas.

**Criterios de aceptación:**
- [x] 700→70 conserva historia y usa 70; dos pesos y carga histórica ordenan por hecho.
- [x] Presión incompleta y captura offline conservan incertidumbre y marcas separadas.
- [x] Permiso retirado bloquea lecturas, resultados, duplicados y sync sin filtrar contenido.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe test-support/measurements/check.py` con PostgreSQL/Keycloak Test.
- [ ] Probar carrera de dos correcciones y rollback inmediato/diferido.
- [ ] Revisar que no se calculan IMC, percentiles o alertas.

**Archivos probables:**
- `tests/test_measurements.py`
- `test-support/measurements/check.py`

## C05 · Mediciones

- [x] E08–E12 y reglas de historia/tiempo/acceso están comprobados.
- [x] No hay unidades alternativas, derivados de Etapa 3 ni efectos parciales.
- [x] El usuario aceptó C05 el 2026-11-16 y autorizó T16 → T17 → T18 hasta C06.

**Evidencia T13–T15:** migración `20261116_07`, cinco tipos con Decimal/UCUM, presión por componentes, historias/timeline, tres acciones, cuatro lecturas y captura de toda serie válida. El límite técnico de peso cambió a 1000 kg porque 500 impedía ejecutar E09 con 700→70; fuentes actualizadas. Probe real cubre series, historia, offline, presión, edad, carreras, rollback, sync y permisos. Persistencia y pruebas unitarias correctas. Cierre: 188 pruebas en 63,250 s, OK; head `20261116_07`; analizador global 15 errores históricos, sin nuevos; contratos llegan a `openapi.json` desactualizado; `git diff --check` correcto. T16 no se inició.

## T16 · Persistir vacunas e historia

**Estado:** Done. **Propietario:** `clinical_records`. **Alcance:** M.

**Descripción:** implementar vacunas actuales e historias con fecha parcial, fuente, tipo de registro, atención opcional y detalles opcionales.

**Entradas y dependencias:** T15 y C05 aceptado; §5.5 del plan y FHIR Immunization.

**Datos, contratos, transacciones y consumidores:** dos tablas nuevas, sin catálogo externo ni recomendaciones. `administered_here` exige atención válida de la misma ficha.

**Criterios de aceptación:**
- [x] Vacuna/fecha/fuente conservan precisión y administración frente a declaración.
- [x] Producto, dosis, lote, vía, sitio, lugar y responsable pueden faltar sin impedir el registro.
- [x] Historia, timeline e identidad cumplen las reglas comunes.

**Verificación:**
- [ ] Pruebas de dominio para fecha parcial, tipo de registro, fuente y campos opcionales.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py` y FK/calendario.
- [ ] Confirmar que no se crean recomendaciones, reacciones o alergias automáticamente.

**Archivos probables:**
- `migrations/versions/20261116_08_patient_immunizations.py`
- `src/api/clinical_records/domain/immunizations.py`
- `src/api/clinical_records/repository/models.py`
- `src/api/clinical_records/repository/dao.py`
- `tests/test_immunizations.py`

## T17 · Conectar vacunas

**Estado:** Done. **Propietario:** `clinical_records` y `sync`. **Alcance:** M.

**Descripción:** conectar registro, edición, anulación, lista, detalle e historia de vacunas con permisos y sincronización.

**Entradas y dependencias:** T16 y patrones de aceptación/historia existentes.

**Datos, contratos, transacciones y consumidores:** tres acciones nuevas, alcance `immunizations`, estado actual e historia en una aceptación.

**Criterios de aceptación:**
- [x] Una vacuna histórica declarada no usa fecha de carga como administración ni afirma atención actual.
- [x] `administered_here` sin atención válida se rechaza; correcciones conservan historia.
- [x] Duplicados, respuesta perdida y revocación aplican alcance vigente.

**Verificación:**
- [ ] Pruebas unitarias y probe nuevo `test-support/immunizations/check.py`.
- [ ] Probar HTTP, idempotencia, rollback y filtros de lista/historia.
- [ ] Revisar contrato en memoria y privacidad de auditoría.

**Archivos probables:**
- `src/api/clinical_records/application/immunizations_cases.py`
- `src/api/clinical_records/infrastructure/immunizations_api.py`
- `src/api/sync/domain/operations.py` y composición
- `tests/test_immunizations.py`
- `test-support/immunizations/check.py`

## T18 · Comprobar vacunas

**Estado:** Done. **Propietario:** calidad de vacunas. **Alcance:** M.

**Descripción:** comprobar E13, fechas parciales, fuentes, acceso y ausencia de evaluación o avisos.

**Entradas y dependencias:** T17 y casos ficticios de T03.

**Datos, contratos, transacciones y consumidores:** datos ficticios, sin cambios funcionales.

**Criterios de aceptación:**
- [x] Vacuna antigua conserva precisión/fuente y no afirma administración actual.
- [x] Objeto ajeno y permiso retirado no filtran datos; ninguna recomendación o efecto automático aparece.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_immunizations.py" -v`.
- [ ] `./.venv/Scripts/python.exe test-support/immunizations/check.py`.
- [ ] Revisar logs/auditoría y rollback sin contenido parcial.

**Archivos probables:**
- `tests/test_immunizations.py`
- `test-support/immunizations/check.py`

## C06 · Vacunas

- [x] E13 y las reglas de administración/declaración, historia y acceso están comprobadas.
- [x] No existen catálogo, calendario, recomendación o efectos automáticos fuera de alcance.
- [x] El usuario aceptó C06 el 2026-11-16. T01–T27 están Done. C01–C08 están aceptados; C09 espera decisión del usuario.

**Evidencia T16–T18/C06:** migración `20261116_08`, estado/historia, fechas parciales, detalles opcionales, tres acciones, tres lecturas, timeline y captura. Probe real E13 cubre declared/administered_here, atención válida, duplicados, corrección, anulación, rollback, permisos y privacidad. Persistencia y cuatro pruebas unitarias correctas; basedpyright acotado 0 errores/avisos. Cierre: 192 pruebas en 66,050 s, OK; head `20261116_08`; analizador global conserva 15 errores históricos; contratos llegan a `openapi.json` desactualizado; `git diff --check` correcto. T19 no se inició.

## T19 · Persistir antecedentes e historia

**Estado:** Done. **Propietario:** `clinical_records`. **Alcance:** M.

**Descripción:** implementar antecedentes personales/familiares/otros con relato, persona relacionada, fecha/fuente, historia y timeline.

**Entradas y dependencias:** T18 y C06 aceptado; §5.6 del plan y FHIR FamilyMemberHistory como referencia conceptual.

**Datos, contratos, transacciones y consumidores:** dos tablas nuevas, sin crear condiciones ni codificación automática.

**Criterios de aceptación:**
- [x] `family` exige descripción de la persona relacionada y no atribuye su condición al paciente.
- [x] Relato no vacío, fecha/fuente opcionales e historia/versiones correctas.

**Verificación:**
- [ ] Pruebas de dominio para categorías, persona relacionada, texto, fecha y fuente.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py` y reglas combinadas.
- [ ] Confirmar que no se escribe una condición a partir del relato.

**Archivos probables:**
- `migrations/versions/20261116_09_patient_antecedents.py`
- `src/api/clinical_records/domain/antecedents.py`
- `src/api/clinical_records/repository/models.py`
- `src/api/clinical_records/repository/dao.py`
- `tests/test_antecedents.py`

## T20 · Conectar antecedentes

**Estado:** Done. **Propietario:** `clinical_records` y `sync`. **Alcance:** M.

**Descripción:** conectar alta, edición, anulación, lista, detalle e historia de antecedentes, con filtros de categoría/estado.

**Entradas y dependencias:** T19 y aceptación compartida.

**Datos, contratos, transacciones y consumidores:** tres acciones nuevas, alcance `antecedents`, historia/timeline/recibo/auditoría/grupo atómicos.

**Criterios de aceptación:**
- [x] Relato, fuente y correcciones conservan contexto e incertidumbre sin análisis automático.
- [x] Filtros preceden a conteo/paginación y duplicados/revocación usan permiso vigente.

**Verificación:**
- [ ] Pruebas unitarias y probe nuevo `test-support/antecedents/check.py`.
- [ ] Probar HTTP, idempotencia, rollback, filtros y respuesta perdida.
- [ ] Revisar contrato en memoria y privacidad.

**Archivos probables:**
- `src/api/clinical_records/application/antecedents_cases.py`
- `src/api/clinical_records/infrastructure/antecedents_api.py`
- `src/api/sync/domain/operations.py` y composición
- `tests/test_antecedents.py`
- `test-support/antecedents/check.py`

## T21 · Comprobar antecedentes

**Estado:** Done. **Propietario:** calidad de antecedentes. **Alcance:** M.

**Descripción:** comprobar categorías, incertidumbre, aislamiento, permisos y ausencia de atribución automática.

**Entradas y dependencias:** T20 y marcadores ficticios de privacidad.

**Datos, contratos, transacciones y consumidores:** datos ficticios, sin cambios funcionales.

**Criterios de aceptación:**
- [x] Antecedente familiar conserva persona relacionada y no crea condición del paciente.
- [x] Permisos, errores, historias y resultados no revelan otra cuenta o sección.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_antecedents.py" -v`.
- [ ] `./.venv/Scripts/python.exe test-support/antecedents/check.py`.
- [ ] Revisar privacidad, versiones y rollback.

**Archivos probables:**
- `tests/test_antecedents.py`
- `test-support/antecedents/check.py`

## C07 · Antecedentes

- [x] Las tres categorías, fuentes, correcciones y accesos tienen evidencia real.
- [x] No se crean condiciones ni otras funciones fuera de alcance.
- [x] El usuario aceptó C07 el 2026-11-16 y autorizó T22 → T23 → T24 → T25 hasta C08.

**Evidencia T19–T21/C07:** migración `20261116_09`, estado/historia, tres categorías, persona relacionada obligatoria en family, tres acciones, tres lecturas, timeline y captura. Probe real cubre incertidumbre, duplicados, corrección, anulación, rollback, permisos, privacidad y ausencia de condiciones. Persistencia y cuatro pruebas unitarias correctas; basedpyright acotado 0 errores/avisos. Cierre: 196 pruebas en 77,570 s, OK; head `20261116_09`; analizador global conserva 15 errores históricos; contratos llegan a `openapi.json` desactualizado; `git diff --check` correcto. T22 no se inició.

## T22 · Integrar Etapa 1 en timeline

**Estado:** Done. **Propietario:** `clinical_records`. **Alcance:** M.

**Descripción:** actualizar las escrituras de condiciones/alergias y rellenar la proyección timeline de los registros existentes sin copiar contenido ni reescribir historias.

**Entradas y dependencias:** T21 y C07 aceptado; estados actuales de Etapa 1.

**Datos, contratos, transacciones y consumidores:** migración de backfill idempotente y cambios en el flujo compartido de Etapa 1. La fecha de inicio conocida conserva precisión; si falta, se usa solo la marca de referencia documentada sin llamarla inicio clínico.

**Criterios de aceptación:**
- [x] Backfill y reejecución producen las mismas referencias/versiones sin duplicados.
- [x] Altas, ediciones, refutaciones y anulaciones de Etapa 1 actualizan timeline en la misma transacción.
- [x] La reconstrucción coincide con los estados actuales y no copia texto clínico.

**Verificación:**
- [ ] Migración desde head anterior con datos ficticios y comparación SQL antes/después.
- [ ] `./.venv/Scripts/python.exe test-support/conditions/check.py` y `allergies/check.py`.
- [ ] Probar rollback entre estado, historia, timeline, recibo y grupo.

**Archivos probables:**
- `migrations/versions/20261116_10_stage1_timeline.py`
- `src/api/clinical_records/application/entries_cases.py`
- `src/api/clinical_records/application/timeline_cases.py`
- `src/api/clinical_records/repository/dao.py`
- Pruebas de condiciones/alergias/persistencia

## T23 · Conectar historial integrado

**Estado:** Done. **Propietario:** `clinical_records`. **Alcance:** M.

**Descripción:** implementar `GET .../clinical-history` sobre timeline con filtros por sección/tipo/fecha/estado, precisión visible y paginación autorizada.

**Entradas y dependencias:** T22; todas las fuentes de Etapas 1 y 2 ya implementadas.

**Datos, contratos, transacciones y consumidores:** lectura de referencias actuales sin contenido clínico duplicado. Detalle se obtiene por la ruta de cada fuente y vuelve a autorizar.

**Criterios de aceptación:**
- [x] Filtros de sección se aplican antes de contar/paginar y ninguna fuente prohibida aparece en items/total.
- [x] Fechas parciales conservan precisión y el orden es estable sin afirmar exactitud desconocida.
- [x] Anulados se excluyen por defecto y cada referencia permite resolver solo el detalle autorizado.

**Verificación:**
- [ ] Pruebas unitarias y probe nuevo `test-support/clinical_history/check.py`.
- [ ] Probar permisos parciales, empates, backfill, corrección/anulación y aislamiento.
- [ ] Fallo de auditoría revierte y no entrega datos.

**Archivos probables:**
- `src/api/clinical_records/domain/history.py`
- `src/api/clinical_records/application/history_cases.py`
- `src/api/clinical_records/infrastructure/history_api.py`
- `src/api/clinical_records/repository/dao.py`
- `tests/test_clinical_history.py` y `test-support/clinical_history/check.py`

## T24 · Completar captura y delta de Etapa 2

**Estado:** Done. **Propietario:** `sync` y componentes propietarios. **Alcance:** M.

**Descripción:** materializar atenciones válidas, notas/antecedentes actuales válidos, todas las tomas válidas, vacunas vigentes y referencias necesarias, sin historias ni timeline adicional.

**Entradas y dependencias:** T23; alcance O15 elegido y captura REPEATABLE READ existente.

**Datos, contratos, transacciones y consumidores:** nuevas proyecciones tipadas en captura/journal. `includeClinical=false` conserva la captura anterior; `true` incluye solo secciones legibles de Etapas 1 y 2.

**Criterios de aceptación:**
- [x] Captura/delta incluyen hechos históricos y correcciones/anulaciones sin filtrar por ventana de citas.
- [x] Referencias de pacientes/profesionales/atenciones están completas, incluso con fichas inactivas/completas.
- [x] Permisos, época, grupos completos, auditoría y rollback se conservan.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe test-support/clinical_downloads/check.py` ampliado para todos los tipos.
- [ ] Probar captura anterior, permisos parciales, grupos invisibles, cambio de época y fallo de auditoría.
- [ ] Validar proyecciones antes del commit y ausencia de historias/timeline/adjuntos.

**Archivos probables:**
- `src/api/clinical_records/application/snapshot_cases.py`
- `src/api/encounters/application/snapshot_cases.py`
- `src/api/sync/application/snapshot_cases.py`
- `src/api/sync/domain/downloads.py`
- `test-support/clinical_downloads/check.py`

## T25 · Comprobar historial y sincronización

**Estado:** Done. **Propietario:** calidad de historial/sync. **Alcance:** M.

**Descripción:** probar la vista integrada y la recuperación de todos los tipos, incluidos aislamiento, datos antiguos, grupos invisibles, SSE y revocación.

**Entradas y dependencias:** T24; E11/E22–E24 y Q01–Q08/Q13/Q16.

**Datos, contratos, transacciones y consumidores:** datos ficticios y bases aleatorias. No acredita consumidor Rust/Hub ni operación.

**Criterios de aceptación:**
- [x] Historial y descarga no omiten ni filtran hechos por fecha, tipo, cuenta, permiso o resultado.
- [x] Una anulación incremental retira el hecho de la vista ordinaria y una captura posterior no lo incluye.
- [x] Recuperación con cursor/época conserva grupos completos y no borra historia funcional; no cambió SSE.

**Verificación:**
- [ ] Probes `clinical_history`, `clinical_downloads`, `downloads`, `retention`, `events` y `collaboration` según el cambio.
- [ ] Probar respuesta perdida, cursor vencido, permiso retirado y fallo de evidencia.
- [ ] Revisar logs/auditoría/cursores sin contenido clínico.

**Archivos probables:**
- `test-support/clinical_history/check.py`
- `test-support/clinical_downloads/check.py`
- Pruebas unitarias de descarga/permisos

## C08 · Historial y descarga

- [x] Historial integrado, captura, delta, recuperación y permisos tienen evidencia completa.
- [x] No hay omisiones, fugas ni borrado de historia funcional por retención técnica.
- [x] El usuario aceptó C08 el 2026-11-16 y autorizó T26 → T27 hasta C09.

**Evidencia T22–T25/C08:** backfill idempotente `20261116_10` y escrituras de Etapa 1 en timeline. Ruta integrada sin permiso global, siete tipos, fechas parciales y detalles autorizados. Probe cubre captura con todos los hechos, corrección/anulación delta, captura posterior sin anulados, permisos parciales y rollback de auditoría. Persistencia y dos pruebas unitarias correctas. Cierre: 198 pruebas en 62,498 s, OK; probes `clinical_history` y `clinical_downloads` correctos; head `20261116_10`; analizador global conserva 15 errores históricos; contratos llegan a `openapi.json` desactualizado; `git diff --check` correcto. T26 no se inició.

## T26 · Publicar api-v1.3 y actualizar fuentes

**Estado:** Done. **Propietario:** contratos y documentación. **Alcance:** M.

**Descripción:** publicar `modelRevision=api-v1.3`, generar contratos/ejemplos desde la app real y actualizar especificación, esquema, acceso, calidad, arquitectura, tareas y guías afectadas.

**Entradas y dependencias:** T25 y C08 aceptado; código y pruebas completos.

**Datos, contratos, transacciones y consumidores:** `contractVersion=1` permanece. Los generados incluyen origen/HEAD/huellas; no se editan a mano. La guía distingue servidor comprobado de consumidor pendiente.

**Criterios de aceptación:**
- [x] Dos generaciones son idénticas y `--check` pasa; rutas/acciones/modelos coinciden con el código.
- [x] Documentación y estados no contienen contradicciones ni aceptaciones atribuidas al agente.
- [x] Ejemplos ficticios se comprueban contra PostgreSQL/Keycloak Test.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe -m scripts.export_contracts` y después `--check`.
- [ ] `./.venv/Scripts/python.exe test-support/contracts/check.py`.
- [ ] Revisar enlaces, estados, fuentes y `git diff --check`.

**Archivos probables:**
- `src/api/sync/domain/capabilities.py` y exportador si hace falta
- `contracts/api-v1/` y `contracts/examples.json` generados
- `docs/api-v1.md`, `database-schema.md`, `access-design.md`, `quality.md`, `architecture.md` y `contracts.md`
- `docs/patient-clinical-record.md`, `docs/rust-api-guide.md`, `docs/sources.md`, `tasks/README.md`
- `tasks/P-20261116-02-clinical-routine/plan.md` y `todo.md`

## T27 · Ejecutar cierre integral de Etapa 2

**Estado:** Done. **Propietario:** calidad y evidencia. **Alcance:** M.

**Descripción:** ejecutar toda la matriz y revisar el diff final contra el HEAD anterior al plan, separando servidor, consumidores, operación y producción.

**Entradas y dependencias:** T26; comandos y probes documentados.

**Datos, contratos, transacciones y consumidores:** no añade comportamiento. Usa datos ficticios y servicios Test, sin base personal ni despliegue.

**Criterios de aceptación:**
- [x] Suite, estructura, probes, migraciones, contratos, build, analizador y `git diff --check` tienen resultados reales registrados.
- [x] E06–E14/E22–E24 están comprobados y no existen diagnósticos nuevos o trabajo fuera de alcance.
- [x] La evidencia separa API de integración Rust/Hub, operación, datos reales y producción pendientes.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe -m unittest discover -s tests -v` y todos los probes existentes/nuevos.
- [ ] `scripts.export_contracts --check`, build offline e inspección del paquete, analizador comparado y revisión final del diff.
- [ ] Registrar comandos, resultados, fallos, límites y limpieza de temporales en esta lista.

**Archivos probables:**
- `tasks/P-20261116-02-clinical-routine/todo.md`
- Evidencia temporal ignorada en `.tmp/clinical-stage2/`

## C09 · Etapa 2 lista para revisión

- [x] Todas las funciones aprobadas y sus casos de aceptación están comprobados según la matriz.
- [x] Contratos, documentación, build y revisión final son coherentes con el entregable.
- [ ] El usuario revisa y decide sobre C09. No se inicia Etapa 3 ni se aceptan automáticamente este plan o los anteriores.

**Evidencia T26–T27/C09:** publicación `api-v1.3` con `contractVersion=1`: 78 rutas, 127 esquemas y 66 acciones; dos generaciones y `--check` correctos; probe real de contratos correcto. Suite: 198 pruebas en 72,864 s, OK. Los 25 probes pasan: 19 anteriores y seis nuevos de Etapa 2. Persistencia, SQL offline/head `20261116_10`, build offline e inspección del wheel correctos. Basedpyright: 15 errores históricos, 0 avisos, sin nuevos. `git diff --check` correcto. El único fallo del cierre fue una expectativa antigua `UNSUPPORTED_OPERATION`; se corrigió a `VALIDATION_ERROR` para acciones ya implementadas y los once probes clínicos se repitieron con éxito. API comprobada con datos ficticios y servicios Test; integración Rust/Hub, operación con datos reales y producción quedan pendientes.

## Reglas de ejecución y evidencia

- Trabajar una tarea a la vez y sin delegación. No iniciar una tarea hasta cumplir su dependencia y obtener la aceptación del checkpoint que la habilite.
- Aplicar `minimal-code`: recorrer el caso real, reutilizar helpers/casos/DAOs existentes y no crear capas o abstracciones anticipadas.
- Aplicar `docs-first-framework-code`: revisar manifiesto/lockfile y fuentes oficiales de la versión antes de cambiar una API de framework; registrar los enlaces en la tarea.
- No añadir dependencias, commits, despliegues, datos reales ni cambios en Rust/Hub. No iniciar Etapa 3.
- Conservar tipos reales, sentinels de Python 3.15, ausencia frente a null, validación única, camelCase, paginación y sync incremental. No usar `Any`, `cast` ni supresiones nuevas.
- Para integridad/concurrencia usar PostgreSQL Test 18.3 aislado y Keycloak Test; eliminar las bases aleatorias al terminar. SQLite no acredita esas reglas.
- Registrar por tarea archivos, entradas, datos/contratos, límites de transacción, efecto en sync/consumidores, comandos, resultados, fallos y límites. Las pruebas escritas pero no ejecutadas no son evidencia.
- Solo el usuario acepta checkpoints. La aprobación del plan no acepta C01–C09 ni los checkpoints pendientes de Etapa 1.
