# Lista de tareas: P-20261116-01-clinical-review-refactor

**Plan:** [plan.md](plan.md). **Estado del plan:** In progress. **Creado:** 2026-11-16. **Actualizado:** 2026-11-16.

El usuario aprobó el plan sucesor, aceptó C01–C07 y autorizó finalizar. T01–T20 quedan comprobadas. C08 permanece pendiente de revisión y aceptación expresa por el usuario. El plan anterior `P-20261115-02-patient-clinical-data` conserva su C06 pendiente y no inicia nuevas tareas.

## Resumen de estados

| ID | Tarea | Dependencia | Estado | Alcance |
|---|---|---|---|---|
| T01 | Registrar plan y línea base | Ninguna | Done | S |
| T02 | Restaurar aceptación transaccional | T01 | Done | S |
| T03 | Corregir validación de duración | T02 | Done | XS |
| T04 | Persistir alcance y definir política común | T03 y C01 aceptado | Done | M |
| T05 | Aplicar política a duplicados y resultados | T04 | Done | M |
| T06 | Probar revocación y secciones independientes | T05 | Done | M |
| T07 | Impedir altas ya anuladas | T06 y C02 aceptado | Done | S |
| T08 | Corregir transiciones de revisión | T07 | Done | M |
| T09 | Completar historial de nacimiento | T08 | Done | S |
| T10 | Incluir referencias clínicas requeridas | T09 y C03 aceptado | Done | S |
| T11 | Auditar delta clínico | T10 | Done | S |
| T12 | Impedir reasignación de identidad clínica | T11 | Done | M |
| T13 | Unificar acceso y lecturas clínicas | T12 y C04 aceptado | Done | M |
| T14 | Unificar revisiones de sección | T13 | Done | M |
| T15 | Unificar escrituras y simplificar despacho | T14 y C05 aceptado | Done | M |
| T16 | Reducir DAO y cerrar calidad estructural | T15 | Done | M |
| T17 | Hacer contratos reproducibles | T16 y C06 aceptado | Done | S |
| T18 | Actualizar fuentes de comportamiento y datos | T17 | Done | M |
| T19 | Actualizar especificación y evidencia de ejecución | T18 | Done | S |
| T20 | Ejecutar cierre integral | T19 y C07 aceptado | Done | M |

## T01 · Registrar plan y línea base

**Estado:** Done. **Propietario:** documentación. **Alcance estimado:** S.

**Descripción:** crear el plan sucesor y su única lista de ejecución, enlazar el plan anterior detenido en C06 y registrar alcance, métricas, dependencias y criterios de aceptación.

**Entradas y dependencias:** revisión de `d548ae3...HEAD`, especificación clínica y aprobación expresa del usuario. Sin dependencias de código.

**Datos, contratos, transacciones y consumidores:** ninguno. No cambia producto, sincronización ni consumidores.

**Criterios de aceptación:**
- [x] El plan contiene las doce observaciones, los dos bloqueos de verificación y su trazabilidad a tareas.
- [x] La línea base fija 1.729 líneas en `clinical_records/application` y el objetivo máximo de 950.
- [x] El plan anterior conserva C06 pendiente y ningún checkpoint se acepta por cuenta del agente.

**Verificación:**
- [x] Revisión documental de enlaces, estados, secuencia T01–T20 y checkpoints C01–C08.
- [x] `git diff --check`.
- [x] No se modificó código, migraciones, contratos generados ni otros repositorios.

**Archivos:**
- `tasks/P-20261116-01-clinical-review-refactor/plan.md`
- `tasks/P-20261116-01-clinical-review-refactor/todo.md`

**Evidencia:** el usuario aprobó el plan el 2026-11-16 y solicitó expresamente crear estos dos archivos y detenerse. El plan enlaza el anterior, registra la pausa en C06, las ocho desviaciones de especificación, cuatro de estándares y los bloqueos `change_log`/agenda. La reducción objetivo es al menos 45 %, sin compactar código ni eliminar reglas o pruebas.

## T02 · Restaurar aceptación transaccional

**Estado:** Done. **Propietario:** `sync`. **Alcance estimado:** S.

**Descripción:** declarar `ChangeLog.__tablename__ = "change_log"` para que el ORM use la tabla física existente y añadir una regresión de correspondencia entre el modelo y el esquema.

**Entradas y dependencias:** T01. Causa confirmada en `src/api/sync/repository/models.py`, `src/core/db/model.py` y `migrations/versions/20261026_01_operation_acceptance.py`.

**Datos, contratos, transacciones y consumidores:** conserva la tabla `change_log`, operaciones, recibos, auditoría y grupos en la misma transacción. No cambia contratos ni consumidores.

**Criterios de aceptación:**
- [x] El alta de dispositivo confirma efecto, recibo, auditoría y journal sin `relation "change_logs" does not exist`.
- [x] La correspondencia ORM/esquema queda cubierta por una prueba de regresión.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_operations.py" -v`: 7 pruebas, OK; incluye la regresión ORM/esquema.
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_accounts_structure.py" -v`: 45 pruebas, OK.
- [x] `./.venv/Scripts/python.exe test-support/sync/check.py`: correcto con PostgreSQL 18/Keycloak Test; duplicado concurrente, rollback atómico, respuesta perdida, acceso vigente y lote independiente.
- [x] Revisión del diff: no se creó un alias, una tabla alternativa ni una migración de datos.

**Archivos modificados:**
- `src/api/sync/repository/models.py`
- `tests/test_operations.py`

**Fuente oficial:** SQLAlchemy 2.1.6, [Declarative Table with `mapped_column()`](https://docs.sqlalchemy.org/en/21/orm/declarative_tables.html): `__tablename__` fija el nombre de la tabla generada por el mapeo.

## T03 · Corregir validación de duración

**Estado:** Done. **Propietario:** `schedule`. **Alcance estimado:** XS.

**Descripción:** sustituir `TypeError` por `ValueError` en `integer_duration`, conservando límites y reglas de disponibilidad.

**Entradas y dependencias:** T02 y los dos errores reproducidos en `src/api/schedule/domain/schedule.py:383`.

**Datos, contratos, transacciones y consumidores:** sin datos ni transacciones. Las entradas inválidas devuelven `ValidationError` y HTTP 422; no cambian consumidores válidos.

**Criterios de aceptación:**
- [x] `durationMinutes=true` y `durationMinutes=1.5` se rechazan como errores de validación, no como excepciones internas.
- [x] Los valores enteros válidos y las reglas de disponibilidad se conservan.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_schedule.py" -v`: 12 pruebas, OK; `true` y `1.5` producen `ValidationError`.
- [x] `./.venv/Scripts/python.exe test-support/schedule/check.py`: correcto; ambos valores producen HTTP 422 y disponibilidad, bloqueos, versiones y rollback se conservan.
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -v`: 166 pruebas en 62,479 s, OK.

**Archivos modificados:**
- `src/api/schedule/domain/schedule.py`
- `test-support/schedule/check.py`

**Fuente oficial:** Pydantic 2.14.1, [Validators — raising validation errors](https://docs.pydantic.dev/2.14/concepts/validators/): `ValueError` se convierte en error de validación; `TypeError` no es una de las excepciones documentadas para ese fin.

## C01 · Base ejecutable

- [x] La suite no conserva los dos errores de `integer_duration`.
- [x] `test-support/sync/check.py` termina correctamente con PostgreSQL/Keycloak reales.
- [x] El usuario revisa y acepta C01 antes de autorizar T04. Aprobación expresa recibida después de presentar T02/T03.

**Evidencia y límites:** T02/T03 están comprobadas según los comandos anteriores. Se usaron solo datos ficticios y bases aleatorias del clúster PostgreSQL Test; no se usó SQLite ni la base personal. No se añadieron dependencias, capas, contratos, migraciones, `Any`, `cast` o supresiones. No se ejecutó el resto de probes ni se comprobó integración con consumidores o producción, fuera del alcance de C01. T04 no se inició.

**Fallos durante la ejecución, conservados:** el patrón planificado `test_*sync*.py` descubrió 0 pruebas y terminó con código 5; se ejecutó `test_operations.py` como prueba enfocada real de sync. Una llamada directa a `tests.test_accounts_structure.SyncStructureTests` no resolvió el import auxiliar; el descubrimiento documentado de `test_accounts_structure.py` pasó 45 pruebas. El primer probe encontró Keycloak Test detenido (`WinError 10061`); se inició el servicio Test. Después el PEM no correspondía al almacén ficticio activo y TLS falló; se exportó el certificado público desde ese mismo almacén a `fixture.pem` y el probe real terminó correctamente. Estas incidencias de entorno/comandos no se contaron como éxitos ni se ocultaron.

## T04 · Persistir alcance y definir política común

**Estado:** Done. **Propietario:** `sync`, `accounts` y `clinical_records`. **Alcance estimado:** M.

**Descripción:** añadir `clinical_section` a los recibos y una función tipada que determine la sección de cada acción clínica y el nivel de escritura exigido.

**Entradas y dependencias:** T03 y C01 aceptado. `docs/api-v1.md` §§3, 5 y 10; `docs/database-schema.md` §§9–10.

**Datos, contratos, transacciones y consumidores:** migración aditiva en `operation_receipts`. Las nuevas escrituras guardan alcance junto al recibo. Las rutas, acciones, `contractVersion=1` y `modelRevision=api-v1.2` no cambian.

**Criterios de aceptación:**
- [x] Cada operación clínica nueva persiste `profile`, `conditions` o `allergies` según corresponda.
- [x] El backfill resuelve recibos conocidos y cualquier revisión histórica ambigua queda sin alcance recuperable, sin adivinarlo.
- [x] La política común exige `read_write` para resultados de escritura y no usa `Any`, `cast` ni supresiones.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_clinical_permissions.py" -v`: 7 pruebas, OK; matriz completa y niveles `none`/`read`/`read_write`.
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_operations.py" -v`: 7 pruebas, OK.
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_accounts_structure.py" -v`: 45 pruebas, OK.
- [x] `./.venv/Scripts/python.exe test-support/persistence/check.py`: upgrade/downgrade/upgrade, rollback de revisión fallida y guardas correctos. La regresión crea recibos bajo el head anterior y comprueba `allergies` para revisión aceptada, `NULL` para rechazada y ambigua, `profile` para acción conocida e inmutabilidad posterior.
- [x] `./.venv/Scripts/python.exe test-support/conditions/check.py`: correcto; recibos nuevos de revisión y condición persisten `conditions`, los no clínicos quedan `NULL`.
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -v`: 168 pruebas en 66,039 s, OK.
- [x] `git diff --check`.

**Archivos modificados:**
- `migrations/versions/20261116_02_clinical_result_scope.py`
- `src/api/sync/repository/models.py`
- `src/api/sync/application/operations_cases.py`
- `src/api/clinical_records/application/access_cases.py`
- `tests/test_clinical_permissions.py`
- `test-support/persistence/check.py`
- `test-support/conditions/check.py`

**Fuentes oficiales:** Alembic 1.20.1, [Operation Reference](https://alembic.sqlalchemy.org/en/latest/ops.html), para ejecutar DDL dentro de `upgrade()`/`downgrade()`; PostgreSQL 18, [constraint triggers](https://www.postgresql.org/docs/18/sql-createtrigger.html) y [SET CONSTRAINTS](https://www.postgresql.org/docs/18/sql-set-constraints.html), para conservar la evaluación diferida y la inmutabilidad durante el backfill.

**Fallos y correcciones comprobados:** la primera dependencia apuntaba a `20261115_04` y Alembic detectó dos heads; se corrigió a la cabeza real `20261116_01`. La primera regresión histórica falló con `cannot ALTER TABLE ... because it has pending trigger events`; se añadió `SET CONSTRAINTS ALL IMMEDIATE` antes de deshabilitar y rehabilitar el guarda. La prueba final confirma backfill, journal e inmutabilidad. Se mejoró el mensaje del primer assert de migración para incluir `stdout` cuando Alembic informa el error allí.

**Límites:** T04 persiste y define la política, pero aún no la aplica a duplicados/GET ni añade auditoría de recuperaciones; ese trabajo pertenece a T05 y no se inició. No cambian contratos, consumidores, rutas ni acciones. Solo PostgreSQL Test aislado y datos ficticios.

## T05 · Aplicar política a duplicados y resultados

**Estado:** Done. **Propietario:** `sync`. **Alcance estimado:** M.

**Descripción:** usar la política antes de consultar o devolver recibos en lote y GET, y auditar las recuperaciones clínicas correctas sin contenido sensible.

**Entradas y dependencias:** T04 y la política de alcance persistida.

**Datos, contratos, transacciones y consumidores:** ninguna forma pública nueva. Duplicados y resultados mantienen su esquema solo cuando el permiso sigue vigente. La evidencia se confirma en la misma transacción de lectura.

**Criterios de aceptación:**
- [x] `read` y `none` no devuelven estados, `originalResult` ni conflictos informativos de escrituras clínicas.
- [x] `SetPatientClinicalSectionReview` se autoriza por su sección real, tanto en lote como en GET.
- [x] Un fallo de auditoría impide entregar la lectura y no deja efectos parciales.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_operations.py" -v`: 8 pruebas, OK; duplicado y GET comparten sección, deniegan antes de leer el recibo y ejecutan evidencia.
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_clinical_permissions.py" -v`: 7 pruebas, OK.
- [x] Probe de permisos: fallo real de evidencia devuelve 503 sin nueva auditoría ni resultado entregado; las rutas no clínicas no añaden evidencia clínica.
- [x] Revisión del flujo: lote autoriza por acción/payload antes del recibo; GET consulta solo acción/sección, autoriza y después lee/valida el resultado.

**Archivos modificados:**
- `src/api/sync/application/operations_cases.py`
- `src/api/sync/repository/dao.py`
- `tests/test_operations.py`

## T06 · Probar revocación y secciones independientes

**Estado:** Done. **Propietario:** calidad de acceso. **Alcance estimado:** M.

**Descripción:** ampliar las pruebas de permisos para reintento por lote, GET y revisión compartida en ambas secciones, incluidas carreras y nuevas instalaciones.

**Entradas y dependencias:** T05; casos CL-16–CL-19 y E22/E23.

**Datos, contratos, transacciones y consumidores:** solo datos ficticios en bases aleatorias. Comprueba revocación, época y recuperación autorizada sin cambiar contratos.

**Criterios de aceptación:**
- [x] Condiciones=`none` no oculta una revisión de alergias permitida y alergias=`none` impide recuperarla aunque condiciones=`read_write`.
- [x] Reintentos después de revocación se rechazan antes de cualquier cuerpo o conflicto informativo.
- [x] Una carrera de revocación y una nueva instalación aplican exactamente la misma política en lote y GET.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_clinical_permissions.py" -v`: 7 pruebas, OK.
- [x] `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py`: correcto con PostgreSQL/Keycloak Test; ambas direcciones, reintento idéntico y con contenido cambiado, GET, nuevo dispositivo y carrera de revocación/lectura con denegación posterior.
- [x] Seis recuperaciones autorizadas dejaron evidencia solo con el ID de operación; sin nombres, sustancias, cuerpos, filtros ni cursores. El rollback no añadió evidencia.

**Archivos modificados:**
- `test-support/clinical_permissions/check.py`

**Fallo de prueba corregido:** el primer fallo ficticio de auditoría usó `RuntimeError`, que ASGI propaga en vez de traducir a 503. Se sustituyó por `DAOError`, el canal temporal del producto, y la ejecución final confirmó 503 sin efectos parciales.

## C02 · Resultados autorizados

- [x] Los casos E22/E23 y las combinaciones cruzadas de permisos terminan correctamente.
- [x] La migración de alcance es reversible y los recibos ambiguos fallan cerrados.
- [x] El usuario revisa y acepta C02 antes de autorizar T07. Aprobación expresa recibida después de presentar T05/T06.

**Evidencia común:** 169 pruebas en 59,082 s, OK; probes reales de permisos clínicos, sync y condiciones correctos; migración reversible y backfill comprobados en T04. Basedpyright sobre `operations_cases.py`, `dao.py` y `access_cases.py`: 0 errores, 0 avisos. `git diff --check` correcto. Solo PostgreSQL/Keycloak Test y datos ficticios. T07 no se inició.

## T07 · Impedir altas ya anuladas

**Estado:** Done. **Propietario:** dominio clínico. **Alcance estimado:** S.

**Descripción:** rechazar `entered-in-error` en los payloads de creación de condiciones y alergias/intolerancias, conservando el valor en respuestas e invalidaciones.

**Entradas y dependencias:** T06 y C02 aceptado; `docs/api-v1.md:377`.

**Datos, contratos, transacciones y consumidores:** cambia solo la validación de altas inválidas. No cambia estados válidos, historiales ni rutas.

**Criterios de aceptación:**
- [x] Las dos altas directas como `entered-in-error` devuelven error de validación sin efecto ni recibo de aceptación.
- [x] Las invalidaciones y respuestas históricas con ese estado siguen funcionando.

**Verificación:**
- [x] `test_conditions.py`: 4 pruebas, OK; `test_allergies.py`: 3 pruebas, OK.
- [x] Probes reales de condiciones y alergias: altas directas como `entered-in-error` producen `VALIDATION_ERROR`; anulaciones, historiales y respuestas existentes se conservan.
- [x] Los validadores se añadieron solo a los payloads de creación, no a las respuestas ni a las invalidaciones.

**Archivos modificados:**
- `src/api/clinical_records/domain/conditions.py`
- `src/api/clinical_records/domain/allergies.py`
- `tests/test_conditions.py`
- `tests/test_allergies.py`
- `test-support/conditions/check.py`
- `test-support/allergies/check.py`

## T08 · Corregir transiciones de revisión

**Estado:** Done. **Propietario:** aplicación clínica. **Alcance estimado:** M.

**Descripción:** calcular pertinencia anterior y posterior y derivar revisiones solo cuando se gana el primer registro pertinente o se pierde el último.

**Entradas y dependencias:** T07; reglas de `has_entries`, `unknown` y `none_known` del plan y `docs/api-v1.md`.

**Datos, contratos, transacciones y consumidores:** efecto, revisión derivada, historias, recibo y grupo permanecen en una aceptación. No cambian modelos públicos.

**Criterios de aceptación:**
- [x] Editar un registro ya refutado conserva `none_known`, su fuente y su historial, sin nueva revisión derivada.
- [x] Añadir pertinencia deriva `has_entries`; retirar la última deriva `unknown`, incluidas carreras coherentes.

**Verificación:**
- [x] Probes reales de condiciones y alergias: correctos; editar un refutado conserva exactamente la respuesta de revisión y el total de historial.
- [x] Altas pertinentes derivan `has_entries`; retirar la última pertinencia deriva `unknown`; carreras alta/ausencia conocida y rollbacks se conservan.
- [x] La derivación recibe la pertinencia anterior y finaliza sin efecto cuando no cambia; no se añadieron capas ni tipos permisivos.

**Archivos modificados:**
- `src/api/clinical_records/application/conditions_cases.py`
- `src/api/clinical_records/application/allergies_cases.py`
- `test-support/conditions/check.py`
- `test-support/allergies/check.py`

## T09 · Completar historial de nacimiento

**Estado:** Done. **Propietario:** `patients`. **Alcance estimado:** S.

**Descripción:** usar `ClinicalHistoryQuery`, admitir `afterVersion` y ordenar los cambios por `patient_version` ascendente.

**Entradas y dependencias:** T08; contrato común de historiales en `docs/api-v1.md:342`.

**Datos, contratos, transacciones y consumidores:** amplía el filtro de lectura sin cambiar la tabla ni las escrituras. Permite huecos de versión producidos por otras ediciones administrativas.

**Criterios de aceptación:**
- [x] `afterVersion` filtra antes de contar/paginar y devuelve versiones ascendentes aunque no sean consecutivas.
- [x] Los permisos administrativos, ausencia de cambios y totales autorizados se conservan.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -p "test_clinical_profile.py" -v`: 5 pruebas, OK.
- [x] `./.venv/Scripts/python.exe test-support/clinical_profile/check.py`: correcto; cambios intercalados producen versiones 2/4/6, `afterVersion=2` devuelve 4/6 en orden y total 2.
- [x] Página 2 con `shows=1` devuelve solo versión 6; `afterVersion=6` devuelve items vacío/total 0; parámetro desconocido devuelve 422.

**Archivos modificados:**
- `src/api/clinical_records/infrastructure/clinical_api.py`
- `src/api/patients/application/patients_cases.py`
- `src/api/patients/repository/dao.py`
- `tests/test_clinical_profile.py`
- `test-support/clinical_profile/check.py`

## C03 · Reglas e historial coherentes

- [x] Creación, refutación, anulación y edición de registros no pertinentes cumplen las reglas.
- [x] El historial de nacimiento admite filtro y orden correctos.
- [x] El usuario revisa y acepta C03 antes de autorizar T10. Aprobación expresa recibida después de presentar T07–T09.

**Evidencia común:** 170 pruebas en 61,671 s y 45 controles de estructura, OK. Probes reales de condiciones, alergias y perfil clínico correctos con PostgreSQL/Keycloak Test y datos ficticios. Basedpyright sobre los archivos de dominio, aplicación, infraestructura y DAO tocados: 0 errores y 0 avisos. `git diff --check` correcto. No se regeneraron contratos en esta fase; T10 no se inició.

## T10 · Incluir referencias clínicas requeridas

**Estado:** Done. **Propietario:** `sync` y `patients`. **Alcance estimado:** S.

**Descripción:** reunir pacientes requeridos por citas y por todas las proyecciones clínicas antes de materializar las fichas administrativas.

**Entradas y dependencias:** T09 y C03 aceptado; `docs/api-v1.md:383`.

**Datos, contratos, transacciones y consumidores:** no cambia modelos ni tablas. La captura REPEATABLE READ incluye las referencias necesarias, sin historias clínicas.

**Criterios de aceptación:**
- [x] Un paciente inactivo/completo sin citas en la ventana conserva su ficha y sus datos clínicos vinculados en la captura.
- [x] Una captura con `includeClinical=false` conserva contenido y forma anteriores.

**Verificación:**
- [x] `./.venv/Scripts/python.exe test-support/clinical_downloads/check.py`: correcto; paciente inactivo/completo sin citas conserva ficha, identificadores y proyecciones clínicas.
- [x] `includeClinical=false` no incorpora esa ficha inactiva ni contenido clínico; permisos parciales solo incluyen secciones autorizadas.
- [x] La captura reúne `patientId` de citas y de las cuatro proyecciones clínicas antes de `snapshot_patients`.

**Archivos modificados:**
- `src/api/sync/application/snapshot_cases.py`
- `test-support/clinical_downloads/check.py`

**Fallo de fixture corregido:** marcar completitud por SQL fue rechazado por la integridad. La preparación final usa operaciones reales con documento, teléfono, base de identificación, completitud e inactivación.

## T11 · Auditar delta clínico

**Estado:** Done. **Propietario:** `sync`. **Alcance estimado:** S.

**Descripción:** registrar las lecturas de cambios con alcance clínico usando solo metadatos permitidos y revertir la respuesta si la evidencia falla.

**Entradas y dependencias:** T10; `docs/api-v1.md:387`.

**Datos, contratos, transacciones y consumidores:** no altera grupos, cursores ni proyecciones. La evidencia se escribe en la transacción breve de lectura.

**Criterios de aceptación:**
- [x] Una página delta clínica correcta registra actor, dispositivo, cuenta, acción, resultado, correlación e instante.
- [x] Un fallo de evidencia devuelve el error temporal común sin entregar datos; capturas sin clínica no añaden auditoría clínica.

**Verificación:**
- [x] `./.venv/Scripts/python.exe test-support/clinical_downloads/check.py`: dos deltas clínicos registran `ReadClinicalChanges`; un fallo devuelve 503 sin incrementar evidencia.
- [x] La evidencia contiene actor, dispositivo, cuenta, acción, resultado, correlación e instante; no cuerpos, filtros, nombres, sustancias ni cursores.
- [x] Grupos invisibles, avance de cursor y capturas sin clínica conservan comportamiento y no añaden esa auditoría.

**Archivos modificados:**
- `src/api/sync/application/download_cases.py`
- `test-support/clinical_downloads/check.py`

## T12 · Impedir reasignación de identidad clínica

**Estado:** Done. **Propietario:** migraciones e integridad clínica. **Alcance estimado:** M.

**Descripción:** añadir una guarda SQL compartida que impida modificar cuenta, ID o paciente en perfiles, condiciones y alergias actuales.

**Entradas y dependencias:** T11; `docs/database-schema.md:1687` y las guías oficiales de triggers de PostgreSQL 18.

**Datos, contratos, transacciones y consumidores:** nueva migración reversible, sin cambios HTTP. Las escrituras válidas conservan su transacción y contenido.

**Criterios de aceptación:**
- [x] Cambiar clínicamente una fila actual sigue permitido; cambiar cuenta, ID o paciente se rechaza sin efecto.
- [x] La guarda cubre las tres tablas y la migración pasa upgrade/downgrade/upgrade sin DDL parcial tras fallo.

**Verificación:**
- [x] `./.venv/Scripts/python.exe test-support/persistence/check.py`: upgrade/downgrade/upgrade, backfill y fallo sin DDL parcial correctos.
- [x] `nightingale_runtime` no puede cambiar paciente en perfil, ID en condición ni cuenta en alergia; cada transacción revierte.
- [x] Probes de perfil, condiciones y alergias confirman escrituras normales, historias, carreras y rollback sin regresiones.

**Archivos modificados:**
- `migrations/versions/20261116_03_clinical_identity_guards.py`
- `test-support/persistence/check.py`
- `test-support/clinical_profile/check.py`
- `test-support/conditions/check.py`
- `test-support/allergies/check.py`

**Fuente oficial:** PostgreSQL 18, [Trigger definition](https://www.postgresql.org/docs/18/trigger-definition.html) y [CREATE TRIGGER](https://www.postgresql.org/docs/18/sql-createtrigger.html): una función `BEFORE UPDATE FOR EACH ROW` compartida puede comparar `OLD`/`NEW` y abortar la transacción.

**Fallos corregidos:** la regresión de alcance ahora baja explícitamente a `20261116_01`, no `-1`. La primera guarda evaluaba `NEW.id` en perfil; se aisló esa comprobación para las tablas que sí tienen ID y las escrituras normales volvieron a pasar antes de probar las reasignaciones.

## C04 · Descarga e integridad completas

- [x] E01/E24, referencias administrativas, auditoría de delta y guardas de identidad terminan correctamente.
- [x] Las migraciones y los probes reales no muestran efectos parciales.
- [x] El usuario revisa y acepta C04 antes de autorizar T13. Aprobación expresa recibida después de presentar T10–T12.

**Evidencia común:** 170 pruebas en 68,120 s y 45 controles de estructura, OK. Probes reales de descarga clínica, persistencia, perfil, condiciones y alergias correctos. Basedpyright de `snapshot_cases.py` y `download_cases.py`: 0 errores/avisos. `git diff --check` correcto. T13 no se inició.

## T13 · Unificar acceso y lecturas clínicas

**Estado:** Done. **Propietario:** `clinical_records`. **Alcance estimado:** M.

**Descripción:** extraer acceso/auditoría a `access_cases.py` y reutilizar lecturas y paginación en perfil, condiciones y alergias.

**Entradas y dependencias:** T12 y C04 aceptado; `minimal-code` y las reglas de arquitectura.

**Datos, contratos, transacciones y consumidores:** ningún cambio funcional. Las rutas y proyecciones conservan forma, permisos y auditoría.

**Criterios de aceptación:**
- [x] Desaparecen los helpers paralelos de acceso/lectura sin perder filtros, totales, historias ni evidencia.
- [x] Las entradas/salidas quedan anotadas con tipos reales, sin `Any`, `cast` ni supresiones.

**Verificación:**
- [x] Suite completa y probes de perfil, condiciones, alergias y descarga: filtros, totales, historias, permisos y evidencia conservados.
- [x] `./.venv/Scripts/python.exe -m scripts.export_contracts --output .tmp/clinical-review/c05`: 60 rutas, 98 esquemas HTTP y 51 acciones.
- [x] Controles de estructura y basedpyright de `clinical_records/application`: sin infracciones ni diagnósticos; sin `Any`, `cast` o supresiones.

**Archivos modificados:**
- `src/api/clinical_records/application/access_cases.py`
- `src/api/clinical_records/application/clinical_cases.py`
- `src/api/clinical_records/application/conditions_cases.py`
- `src/api/clinical_records/application/allergies_cases.py`

## T14 · Unificar revisiones de sección

**Estado:** Done. **Propietario:** `clinical_records`. **Alcance estimado:** M.

**Descripción:** concentrar en `entries_cases.py` la lectura, historia, confirmación y derivación de revisiones de condiciones y alergias.

**Entradas y dependencias:** T13 y las reglas corregidas en T08.

**Datos, contratos, transacciones y consumidores:** conserva estados, versiones, historias, audiencias y grupos de ambas secciones.

**Criterios de aceptación:**
- [x] Una sola implementación cubre las dos secciones y elimina las copias paralelas.
- [x] `none_known`, pertinencia y transiciones de versión coinciden con C04.

**Verificación:**
- [x] Probes de condiciones y alergias: estados, `none_known`, versiones, idempotencia, permisos y rollback conservados.
- [x] Carreras y coherencia revisión/historia/journal comprobadas en PostgreSQL Test; descarga clínica también correcta.
- [x] `entries_cases.py` concentra respuesta, historia, confirmación, lectura y derivación con callbacks tipados; no se creó un framework ni otra capa.

**Archivos modificados:**
- `src/api/clinical_records/application/entries_cases.py`
- `src/api/clinical_records/application/conditions_cases.py`
- `src/api/clinical_records/application/allergies_cases.py`

## C05 · Lecturas y revisiones simplificadas

- [x] El comportamiento coincide con C04 y la duplicación de lecturas/revisiones quedó retirada.
- [x] Los contratos en memoria y los probes reales se conservan.
- [x] El usuario revisa y acepta C05 antes de autorizar T15. Aprobación expresa condicionada a corregir el genérico de `clinical_page`, ya comprobada.

**Evidencia común:** 170 pruebas en 60,561 s y 45 controles de estructura, OK. Probes reales de condiciones, alergias, perfil y descarga clínica correctos. Exportación en memoria: 60 rutas, 98 esquemas HTTP y 51 acciones. Basedpyright de `clinical_records/application`: 0 errores/avisos. `git diff --check` correcto. La aplicación clínica baja de 1.796 a 1.658 líneas; la meta global de 950 queda para T16, no se compactó código ni se inició T15.

## T15 · Unificar escrituras y simplificar despacho

**Estado:** Done. **Propietario:** `clinical_records` y `sync`. **Alcance estimado:** M.

**Descripción:** reutilizar un flujo tipado para alta/edición/anulación y sustituir la cascada de despacho por una tabla basada en los catálogos existentes.

**Entradas y dependencias:** T14 y C05 aceptado; catálogos de `src/api/sync/domain/operations.py`.

**Datos, contratos, transacciones y consumidores:** conserva operaciones, huellas, versiones, recibos, historias, grupos y orden de bloqueos. No crea otro sistema de comandos.

**Criterios de aceptación:**
- [x] Las escrituras clínicas comparten un solo flujo y el despacho tabular elimina la cascada sin cambiar efectos.
- [x] Las huellas anteriores, duplicados, conflictos y rollbacks se conservan.

**Verificación:**
- [x] `test_operations.py`: 8 pruebas, OK; 48 huellas anteriores y validación única conservadas.
- [x] Probes reales de sync, condiciones y alergias: duplicados, historias, recibos, grupos, carreras y rollback correctos.
- [x] Una sola función coordina alta/edición/anulación; el despacho usa catálogos/handlers y conserva la selección de revisión compartida.

**Archivos modificados:**
- `src/api/clinical_records/application/entries_cases.py`
- `src/api/clinical_records/application/conditions_cases.py`
- `src/api/clinical_records/application/allergies_cases.py`
- `src/api/sync/application/operations_cases.py`

**Fallo corregido:** el probe detectó validación de fechas al anular; se restauró su exclusión antes de repetir los tres probes con éxito.

**Revisión de legibilidad posterior:** `create` y `valid` tienen tipos explícitos en condiciones y alergias; `EntryAdapter` y `apply_entry_write` documentan su contrato. Basedpyright: 0 errores/avisos; suite posterior: 170 pruebas en 62,783 s, OK.

## T16 · Reducir DAO y cerrar calidad estructural

**Estado:** Done. **Propietario:** repositorio y aplicación clínica. **Alcance estimado:** M.

**Descripción:** unificar únicamente métodos DAO idénticos, completar anotaciones y retirar código muerto demostrado por referencias.

**Entradas y dependencias:** T15; objetivo de 950 líneas y controles de arquitectura.

**Datos, contratos, transacciones y consumidores:** conserva consultas, orden, `commit=False` y restricciones. No modifica contratos.

**Criterios de aceptación:**
- [x] El usuario aceptó el diseño actual en C06 y revisó la meta inicial de 950 líneas; resultado: 1.673 líneas, sin compactar código ni eliminar reglas.
- [x] Los controles de estructura y el análisis comparado no muestran infracciones ni diagnósticos nuevos.

**Verificación:**
- [x] `wc -l src/api/clinical_records/application/*.py`: 1.673 líneas, no cumple el máximo 950.
- [x] Suite completa: 170 pruebas, OK; estructura: 45 pruebas, OK.
- [x] Basedpyright de aplicación clínica, DAO y despacho: 0 errores/avisos, sin relajar configuración.
- [x] `clinical_page` usa parámetros de tipo PEP 695 y elimina el aviso Ruff UP047; análisis y pruebas enfocadas correctos.

**Archivos modificados:**
- `src/api/clinical_records/repository/dao.py`
- `src/api/clinical_records/application/access_cases.py`
- `src/api/clinical_records/application/entries_cases.py`
- `src/api/clinical_records/application/conditions_cases.py`
- `src/api/clinical_records/application/allergies_cases.py`
- `tests/test_accounts_structure.py`
- `tests/test_authorization_structure.py`

**Decisión en C06:** el usuario aceptó el diseño actual y autorizó continuar. Las bases DAO y lecturas idénticas están unificadas, con 1.673 líneas y sin compactar sentencias ni retirar validaciones. La meta inicial de 950 queda revisada por esta decisión expresa.

## C06 · Refactorización comprobada

- [x] El usuario aceptó el diseño actual y revisó la meta inicial del 45 %; resultado: 3,1 % (1.729 → 1.673), sin supresiones o compactación artificial.
- [x] Estructura, suite y probes clínicos conservan el comportamiento corregido.
- [x] El usuario revisa y acepta C06 antes de autorizar T17. Aprobación expresa recibida después de presentar el límite.

**Evidencia común:** 170 pruebas en 63,422 s, OK. Probes reales de condiciones, alergias y sync correctos. Basedpyright de aplicación clínica, DAO y despacho: 0 errores/avisos. `git diff --check` correcto. T17 no se inició.

## T17 · Hacer contratos reproducibles

**Estado:** Done. **Propietario:** contratos. **Alcance estimado:** S.

**Descripción:** incluir `sourceHead` y `sourceSha256` en el manifiesto, alinear su documentación y regenerar todos los artefactos desde la app real.

**Entradas y dependencias:** T16 y C06 aceptado; `scripts/export_contracts.py` y `contracts/README.md`.

**Datos, contratos, transacciones y consumidores:** no cambia el comportamiento remoto. Actualiza metadatos y artefactos generados sin editarlos a mano.

**Criterios de aceptación:**
- [x] Dos generaciones producen archivos idénticos y `--check` termina correctamente.
- [x] Manifiesto, origen, HEAD, huellas, ejemplos y referencias coinciden con el código real.

**Verificación:**
- [x] Dos ejecuciones de `./.venv/Scripts/python.exe -m scripts.export_contracts` producen 60 rutas, 98 esquemas y 51 acciones idénticas; `diff -rq` sin diferencias y `--check` correcto.
- [x] `./.venv/Scripts/python.exe test-support/contracts/check.py`: esquemas, referencias, permisos, ejemplos, snapshot/delta y SSE correctos.
- [x] Manifiesto con `sourceHead=287b361963d1b4ae1cf46f630c3af1a791a5aa73` y `sourceSha256`, además de huellas por archivo.

**Archivos modificados:**
- `scripts/export_contracts.py`
- `contracts/api-v1/` generado

**Fallo corregido:** el primer cambio referenció `metadata` fuera de su ámbito y produjo `NameError`; se reutilizó `openapi.json["x-generated"]`. El análisis del exportador conserva el diagnóstico previo `reportAttributeAccessIssue` en `get_capabilities().value` (línea 51), no introducido por este cambio.

## T18 · Actualizar fuentes de comportamiento y datos

**Estado:** Done. **Propietario:** documentación de API, datos y acceso. **Alcance estimado:** M.

**Descripción:** completar tablas vacías y reflejar alcance de recibos, auditoría, integridad y simplificación en las fuentes únicas.

**Entradas y dependencias:** T17; implementación y contratos ya comprobados.

**Datos, contratos, transacciones y consumidores:** documenta el comportamiento real sin crear una segunda definición editable de los esquemas generados.

**Criterios de aceptación:**
- [x] Las tablas de rutas/acciones, alcance de recibos, auditoría y guardas coinciden con el código.
- [x] Cada contrato conserva una sola fuente y los enlaces locales resuelven.

**Verificación:**
- [x] Exportador: correspondencia de rutas/acciones con la app correcta; revisión de FK y guardas contra las migraciones.
- [x] `./.venv/Scripts/python.exe -m scripts.export_contracts --check`: 60 rutas, 98 esquemas y 51 acciones.
- [x] `git diff --check` y revisión de comentarios/docstrings afectados.

**Archivos modificados:**
- `docs/api-v1.md`
- `docs/database-schema.md`
- `docs/access-design.md`
- `docs/architecture.md`
- `docs/contracts.md`

## T19 · Actualizar especificación y evidencia de ejecución

**Estado:** Done. **Propietario:** documentación funcional y de tareas. **Alcance estimado:** S.

**Descripción:** retirar estados antiguos y registrar el plan sucesor, las comprobaciones y los límites sin aceptar revisiones por cuenta del agente.

**Entradas y dependencias:** T18 y C07 aún por revisar; evidencia real disponible hasta ese punto.

**Datos, contratos, transacciones y consumidores:** solo estados y evidencia documental. C06 del plan anterior sigue pendiente.

**Criterios de aceptación:**
- [x] La especificación y el índice describen el estado real sin contradicciones ni aceptaciones automáticas.
- [x] Plan/todo del sucesor y evidencia del plan anterior son consistentes entre sí.

**Verificación:**
- [x] Tareas T01–T20, dependencias y checkpoints C01–C08 comparados entre `plan.md` y `todo.md`.
- [x] El plan anterior conserva C06 pendiente; el índice identifica el sucesor activo y no atribuye aceptaciones nuevas.
- [x] `git diff --check`; suite completa: 170 pruebas en 54,726 s, OK.

**Archivos modificados:**
- `docs/patient-clinical-record.md`
- `tasks/README.md`
- `tasks/P-20261116-01-clinical-review-refactor/plan.md`
- `tasks/P-20261116-01-clinical-review-refactor/todo.md`

## C07 · Contratos y documentación revisados

- [x] Exportación reproducible y fuentes de comportamiento/datos coherentes.
- [x] Especificación, índice y evidencia no contienen estados contradictorios ni aceptaciones automáticas.
- [x] El usuario revisa y acepta C07 antes de autorizar T20. Aprobación expresa recibida después de presentar T17–T19.

**Evidencia común:** dos generaciones idénticas y `--check`; probe real de contratos correcto; suite de 170 pruebas en 54,726 s, OK; `git diff --check` correcto. El diagnóstico previo del exportador en línea 51 se conserva documentado. T20 no se inició.

## T20 · Ejecutar cierre integral

**Estado:** Done. **Propietario:** calidad y evidencia. **Alcance estimado:** M.

**Descripción:** ejecutar la matriz completa y revisar el diff final contra `f733271`, separando funciones comprobadas, fallos previos y límites.

**Entradas y dependencias:** T19 y C07 aceptado; comandos del plan y `test-support/README.md`.

**Datos, contratos, transacciones y consumidores:** no añade comportamiento. Usa solo datos ficticios, PostgreSQL/Keycloak Test y artefactos temporales ignorados.

**Criterios de aceptación:**
- [x] Suite, probes, migraciones, contratos, build, estructura, medida de líneas y `git diff --check` tienen resultados registrados.
- [x] La revisión final confirma las doce observaciones y los dos bloqueos corregidos, sin diagnósticos nuevos ni trabajo fuera de alcance.
- [x] La evidencia distingue API comprobada de integración Rust/Hub, operación y producción pendientes.

**Verificación:**
- [x] `./.venv/Scripts/python.exe -m unittest discover -s tests -v`: 170 pruebas en 64,456 s, OK.
- [x] Los diecinueve probes reales pasan: access, accounts, sync, team, patients, services, schedule, appointments, persistence, downloads, retention, events, collaboration, clinical_permissions, clinical_profile, conditions, allergies, clinical_downloads y contracts.
- [x] Persistencia: upgrade/downgrade/upgrade, backfill, guardas y rollback sin DDL parcial.
- [x] Contratos: dos generaciones idénticas y `--check`, 60 rutas/98 esquemas/51 acciones; build offline correcto en `.tmp/clinical-review/build`.
- [x] Basedpyright completo: 15 diagnósticos históricos, 0 avisos; ninguno nuevo. La anotación `__tablename__: str` evita el diagnóstico adicional de `change_log`.
- [x] `wc -l`: 1.675 líneas en aplicación clínica, diseño aceptado por el usuario en C06; `git diff --check` correcto.

**Archivos modificados:**
- `tasks/P-20261116-01-clinical-review-refactor/todo.md`
- `tasks/README.md`
- `src/api/sync/repository/models.py` (solo anotación de tipo)
- Contratos regenerados tras la anotación.

**Revisión y límites:** el diff final cubre las doce observaciones y los dos bloqueos sin cambios en otros repositorios, commits o despliegues. API comprobada con PostgreSQL/Keycloak Test y datos ficticios. Integración Rust/Hub, operación y producción no se comprobaron. Los 15 diagnósticos históricos de `accounts`, `patients`, `users`, Valkey y sentinels se conservan sin supresiones.

## C08 · Corrección y refactorización listas para revisión

- [x] Todas las observaciones y bloqueos están corregidos y comprobados según la matriz aprobada.
- [x] La reducción de código, la legibilidad y la conexión entre componentes son revisables en el diff.
- [ ] El usuario revisa este plan sucesor y después vuelve a C06 de `P-20261115-02-patient-clinical-data`; ningún plan se marca aceptado o completado automáticamente.

## Reglas de ejecución y evidencia

- Trabajar una tarea a la vez, sin delegación y sin iniciar la siguiente hasta cumplir su dependencia y la aceptación del checkpoint correspondiente.
- Aplicar `minimal-code` en cada cambio y `docs-first-framework-code` antes de usar una API de framework; registrar las fuentes exactas en la tarea.
- No añadir dependencias, commits, despliegues, cambios en otros repositorios ni datos reales. No iniciar Etapa 2.
- Conservar los sentinels de Python 3.15 y los diagnósticos históricos documentados sin ocultarlos. No introducir `Any`, `cast` ni supresiones nuevos.
- Al terminar cada tarea, registrar archivos, comandos, resultados reales, fallos, límites y efecto en datos, permisos, sincronización y consumidores. Las pruebas propuestas no cuentan como evidencia ejecutada.
- Eliminar los temporales creados que no se necesiten y conservar el trabajo ajeno. Solo el usuario acepta checkpoints.
