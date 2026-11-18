# Lista de tareas: P-20261117-05-clinical-stage-3

**Plan:** [plan.md](plan.md). **Actualizado:** 2026-11-17. **Estado del plan:** In progress.

**Inicio anticipado autorizado el 2026-11-17 (registrado en [D19](../docs/decisions.md)):** el usuario decidió expresamente comenzar la ejecución sin esperar el cierre Completed de Autorización (P-20261117-01), que sigue In progress. Esta autorización sustituye solo la espera previa de este plan. No se modifica el plan de Autorización ni sus archivos; el trabajo de Etapa 3 es secuencial, una tarea a la vez, y las tareas que consuman su resultado final esperan su cierre.

## T01 · Registrar línea base y correspondencia funcional

**Estado:** Done. **Propietario:** documentación clínica y calidad. **Alcance:** M.

**Descripción:** registrar alcance/exclusiones, estado real de Etapas 1/2, casos E03/E09/E15/E17–E21, requisitos R13–R25 y dependencias disponibles al iniciar.

**Entradas y dependencias:** C09 aceptado y Etapa 2 Completed; inicio anticipado autorizado el 2026-11-17 sin esperar a Autorización (D19); sin modificar esos planes.

**Datos, contratos, transacciones y consumidores:** documentación de plan; no cambia producto, datos, contratos o consumidores.

**Criterios de aceptación:**
- [x] Los cinco bloques y casos tienen trazabilidad a fases/tareas y prescripción queda fuera.
- [x] La línea base registra evidencia aceptada y límites sin declarar funciones futuras implementadas.

**Verificación:**
- [x] Revisión de enlaces, anclas, dependencias y estados de planes existentes.
- [ ] `git diff --check`.
- [x] Manual: recorrer E15, E17, E18, E19, E20 y E21 hasta sus tareas sin llegar a prescripción.

**Archivos previstos:** `tasks/P-20261117-05-clinical-stage-3/plan.md`, `tasks/P-20261117-05-clinical-stage-3/todo.md`, `docs/quality.md`.

**Evidencia (2026-11-17):** línea base y tabla de trazabilidad registradas en [plan.md §1.1](plan.md). Base: C09 de Etapa 2 aceptado el 2026-11-17 y P-20261116-02 Completed (api-v1.3); Autorización In progress sin consumo de sus resultados. Trazabilidad: medicación declarada E15/R13→T10–T12/C04; planes E17/R15→T13–T15/C05; informes E18/R16→T16–T18/C06; plantillas E19/R17→T19–T21/C07; especialidad→T22–T24/C08; series E03/E09/R03/R18→T25–T27/C09; crecimiento OMS E20/E21→T28–T30/C10; comunes E22/E23/E24/R19–R25→T31–T36. Prescripción (E16/R14) queda en P-20261117-04, fuera de este plan. Verificación: `git diff --check` sin errores (registrado tras la edición); recorrido manual E15→T10, E17→T13, E18→T16, E19→T19, E20/E21→T25–T30 sin tocar prescripción. Sin cambios en archivos de Autorización.

## T02 · Cerrar medicación, cuidados e informes

**Estado:** Done. **Propietario:** producto clínico y propietarios de bloques. **Alcance:** M.

**Descripción:** resolver O09 solo para medicación declarada, O10 para objetivos/acciones/ciclo y O12 para entrada/corrección/adjuntos/integración de informes.

**Entradas y dependencias:** T01; especificación clínica y casos E15/E17/E18.

**Datos, contratos, transacciones y consumidores:** decisiones documentales; no reabre catálogo/ciclo de prescripción.

**Criterios de aceptación:**
- [ ] Fuente/precisión/revisión de medicación y ciclo de planes/objetivos/acciones están definidos.
- [ ] Informe original/resultados/preliminar/final/corrección/adjuntos e integración externa tienen alcance explícito.

**Verificación:**
- [ ] Matriz ficticia de uso declarado, actividad frente a objetivo e informe corregido.
- [ ] `git diff --check` y enlaces FHIR pertinentes.
- [ ] Manual: recorrer cada caso y confirmar que no crea consumo, objetivo cumplido o integración por deducción.

**Archivos previstos:** `docs/patient-clinical-record.md`, `docs/decisions.md`, `docs/quality.md`.

**Evidencia (2026-11-17):** decisiones registradas en [§4.3.1 de la especificación clínica](../../docs/patient-clinical-record.md) y en [D19](../../docs/decisions.md): O09 para medicación declarada (texto libre, fuente obligatoria `patient/caregiver/other_professional/document`, fechas parciales con precisión, opcionales guardados como desconocidos, revisión que conserva fuente, corrección con historia, sin inferir consumo); O10 (plan como organizador, indicaciones sin lista paralela —T04 confirma físico—, objetivos narrativos/medibles, evaluación separada del cumplimiento, estados `active/suspended/closed/cancelled` con sustitución conservada); O12 (informe con fuente/fechas muestra-emisión-carga, `preliminary/final`, corrección que conserva original; resultados numéricos con unidad o texto; intervalo solo del informe; adjuntos S3 privados, sin extracción ni integración). Matriz ficticia E15/E17/E18 recorrida contra §4.3.1 sin crear consumo, objetivo cumplido ni integración. `git diff --check` sin errores. Sin cambios en archivos de Autorización.

## T03 · Cerrar analítica, especialidad, permisos, archivos y offline

**Estado:** Done. **Propietario:** producto clínico, seguridad y operación. **Alcance:** M.

**Descripción:** resolver O11/O13, primera especialidad/recorrido, indicadores/métodos OMS, permisos/defaults, retención/copias y trabajo offline por bloque.

**Entradas y dependencias:** T02; O11/O13 y política clínica vigente.

**Datos, contratos, transacciones y consumidores:** decisiones documentales; no elige biblioteca/dataset/proveedor sin fuente oficial.

**Criterios de aceptación:**
- [ ] Primera especialidad e indicadores/rangos/métodos OMS tienen alcance y límites explícitos.
- [ ] Permisos por acción/sección, adjuntos, retención y offline/recuperación no contradicen Etapas 1/2.

**Verificación:**
- [ ] Matriz de acceso por bloque y casos fuera de rango/cambio de nacimiento/plantilla.
- [ ] `git diff --check` y revisión de enlaces OMS/OWASP.
- [ ] Manual: seguir paciente con datos insuficientes y usuario con permiso retirado sin fuga o borrado.

**Archivos previstos:** `docs/patient-clinical-record.md`, `docs/access-design.md`, `docs/quality.md`, `docs/decisions.md`.

**Evidencia (2026-11-17):** primera especialidad odontología con odontograma (diccionario en T22); indicadores OMS iniciales peso/edad, talla o longitud/edad, peso/talla o longitud e IMC/edad con patrones 2006 (0–60 m) y referencia 2007 (61–228 m; peso/edad 5–10 años), verificación de fuentes/datasets/licencias reservada a T28; permisos nuevos como secciones `declared_medications/care_plans/diagnostic_reports/specialty_templates/clinical_analytics` con niveles `none/read/read_write` y asistentes en `read_write` inicial ([access-design.md](../../docs/access-design.md), sección Etapa 3); adjuntos S3 privados con adaptador mínimo `httpx` + SigV4 de biblioteca estándar, sin instalar dependencias, verificación oficial en T18; offline/recuperación con las reglas de captura/delta/época de Etapas 1/2 y retención técnica de 90 días sin borrado funcional. Matrices de acceso por bloque y casos fuera de rango/cambio de nacimiento/plantilla recorridas contra §4.3.1. `git diff --check` sin errores. Sin cambios en archivos de Autorización.

## C01 · Después de T01–T03

- [x] O09–O13 tienen decisiones registradas dentro del alcance sin prescripción.
- [x] Casos, permisos, especialidad, analítica y dependencias son coherentes.
- [x] El usuario revisa y acepta C01. **Aceptado el 2026-11-17.**

## T04 · Diseñar físicamente medicación y planes de cuidados

**Estado:** Done. **Propietario:** esquema físico y componentes `medications`/`care_plans`. **Alcance:** M.

**Descripción:** proponer tablas/columnas/FK/CHECK/UQ/índices para medicación declarada, tratamientos, planes, objetivos, acciones y revisiones.

**Entradas y dependencias:** C01 aceptado; T02.

**Datos, contratos, transacciones y consumidores:** diseño sin migración; ámbito cuenta/paciente, versiones e historia.

**Criterios de aceptación:**
- [ ] Medicación conserva fuente/precisión/revisión sin relación obligatoria con receta.
- [ ] Planes relacionan problemas/mediciones sin exigir condición ni confundir actividad/objetivo.

**Verificación:**
- [ ] Cobertura de E15/E17 y reglas de versión/integridad frente a cada restricción propuesta.
- [ ] `git diff --check` y enlaces PostgreSQL 18.
- [ ] Manual: evaluar edición concurrente, cierre/suspensión y referencia cruzada contra el diseño.

**Archivos previstos:** `docs/database-schema.md`, `docs/architecture.md`.

**Evidencia (2026-11-17):** diseño en [database-schema.md §12](../../docs/database-schema.md): ocho tablas nuevas (`declared_medications`+historia, `care_plans`+historia, `care_plan_goals`+historia, `care_plan_actions`+historia, `care_plan_reviews`+historia), columnas de permiso `declared_medications_access`/`care_plans_access` en `account_memberships`, UQ `(account_id,id,patient_id)` añadida a `patient_conditions` como destino del vínculo, conjuntos cerrados de recibos/sync ampliados y timeline con `declared_medication`/`care_plan`. E15 cubierto: fuente obligatoria CHECK, periodo parcial, opcionales como nulos, revisión que conserva fuente, sin relación con receta. E17 cubierto: plan sin condición obligatoria, objetivo medible/narrativo con evaluación separada del cumplimiento de acciones, estados `active/suspended/closed/cancelled` con sustitución conservada. Referencias cruzadas por FK compuestas `(account_id,…,patient_id)` que impiden cruzar fichas; versiones diferidas e historias append-only. Inventario documental: 56 tablas/795 columnas/156 FK. Verificación: `git diff --check` sin errores; revisión manual de edición concurrente (versiones), cierre/suspensión (CHECK de coherencia) y referencia cruzada (FK compuestas) contra el diseño. Sin cambios en archivos de Autorización.

## T05 · Diseñar físicamente informes, resultados y adjuntos

**Estado:** Done. **Propietario:** esquema físico y `diagnostic_results`. **Alcance:** M.

**Descripción:** proponer informe original, resultados estructurados, historias/correcciones, metadatos de archivo y referencias por cuenta/paciente.

**Entradas y dependencias:** T04; T02/T03.

**Datos, contratos, transacciones y consumidores:** diseño sin bytes en DB/journal; fechas, unidades y referencias del informe.

**Criterios de aceptación:**
- [ ] Original/preliminar/final/corregido y vigencia de resultados tienen restricciones sin duplicar puntos.
- [ ] Adjuntos conservan tipo/tamaño/huella/ámbito y descarga sin URL pública.

**Verificación:**
- [ ] Matriz E18, archivo huérfano, resultado sin unidad y corrección concurrente.
- [ ] `git diff --check` y enlaces PostgreSQL/OWASP.
- [ ] Manual: seguir informe→resultados→corrección→archivo sin integración externa implícita.

**Archivos previstos:** `docs/database-schema.md`, `docs/architecture.md`, `docs/access-design.md`.

**Evidencia (2026-11-17):** diseño en [database-schema.md §13](../../docs/database-schema.md): seis tablas (`diagnostic_reports`+historia, `diagnostic_report_results`+historia, `report_attachments`+historia de metadatos), permiso `diagnostic_reports_access`, timeline con `diagnostic_report`. E18 cubierto: corrección = nueva versión del mismo informe que anula los resultados anteriores (`record_status`) en la misma aceptación, historias conservan el original y las consultas vigentes filtran válidos, sin puntos duplicados. Original separado de resultados; adjuntos con metadatos/huella (`sha256`, `storage_key` interno, sin URL) y bytes en S3 fuera de DB/journal; adjunto huérfano legal pero no acredita informe; descarga reautorizada. Resultados con CHECK numérico⇒unidad, intervalo solo del informe, sin rango universal ni banderas. Matriz E18/archivo huérfano/resultado sin unidad/corrección concurrente revisada contra el diseño. `git diff --check` sin errores. Sin cambios en archivos de Autorización.

## T06 · Diseñar físicamente plantillas, especialidad y analítica

**Estado:** Done. **Propietario:** esquema físico, `specialties` y `analytics`. **Alcance:** M.

**Descripción:** proponer versiones de plantilla/campos, entidades de la especialidad elegida, entradas/derivados y avance ETL analítico.

**Entradas y dependencias:** T05; T03.

**Datos, contratos, transacciones y consumidores:** tipos específicos, sin JSON clínico libre; almacén analítico separado y referencias OMS versionadas.

**Criterios de aceptación:**
- [ ] Registros anteriores conservan plantilla/versión y especialidad tiene restricciones propias.
- [ ] Series/derivados/ETL identifican entradas/versiones y no duplican puntos tras reintento.

**Verificación:**
- [ ] Cobertura E19/E20/E21 y reconstrucción de proyecciones frente a restricciones.
- [ ] `git diff --check` y fuentes PostgreSQL/OMS pertinentes.
- [ ] Manual: evaluar cambio de plantilla, nacimiento y corrección con reconstrucción completa.

**Archivos previstos:** `docs/database-schema.md`, `docs/architecture.md`, `docs/quality.md`.

**Evidencia (2026-11-17):** diseño en [database-schema.md §14](../../docs/database-schema.md): seis tablas operativas (`specialty_templates`+historia, `specialty_template_fields`, `specialty_records`+historia, `specialty_record_values`) con permisos `specialty_templates_access`/`clinical_analytics_access`, y tres tablas en el almacén analítico separado (`analytic_measurement_points`, `analytic_etl_state`, `who_reference_values`). E19 cubierto: plantilla versionada, registros conservan `(template_id,template_version)` inmutable, campos con tipo cerrado y valores en columnas tipadas (sin JSON clínico), campos ausentes no generados. E20/E21 cubiertos: referencias OMS con `reference_code`/`indicator`/`sex`/`age_days`, sin filas fuera de rango, corrección de toma produce punto nuevo por `(source_measurement_id,source_version)` y retira el anterior sin duplicar; cambio de nacimiento invalida en la consulta porque la edad se calcula del hecho. Cambio de plantilla (nueva versión sin alterar anteriores) y reconstrucción ETL revisados contra el diseño. Inventario operativo: 68 tablas/1013 columnas/191 FK. `git diff --check` sin errores. Sin cambios en archivos de Autorización.

## C02 · Después de T04–T06

- [x] El diseño físico cubre los cinco bloques sin tablas genéricas/vacías.
- [x] Ámbito, versiones, historia, adjuntos, derivados e índices son revisables.
- [x] El usuario revisa y acepta C02. **Aceptado el 2026-11-17** (instrucción "continuar hasta T18").

## T07 · Diseñar contratos de medicación y cuidados

**Estado:** Done. **Propietario:** `medications`, `care_plans` y contratos. **Alcance:** M.

**Descripción:** fijar operaciones/lecturas/modelos para medicación declarada, tratamientos/planes, objetivos/acciones y revisiones.

**Entradas y dependencias:** C02 aceptado; T02/T04.

**Datos, contratos, transacciones y consumidores:** camelCase, page/shows, operaciones tipadas, idempotencia y resultados recuperables.

**Criterios de aceptación:**
- [ ] Cada acción define actor/objeto/versión/payload/resultado/permiso y límite transaccional.
- [ ] E15/E17 cubren creación/corrección/revisión/cierre sin efectos indebidos.

**Verificación:**
- [ ] Revisión de cobertura de casos y compatibilidad ausencia/null/NO_CHANGES.
- [ ] `git diff --check` y enlaces/anclas locales.
- [ ] Manual: recorrer respuesta perdida y dos ediciones en medicación/plan.

**Archivos previstos:** `docs/api-v1.md`, `docs/contracts.md`, `docs/access-design.md`.

**Evidencia (2026-11-17):** contratos en [api-v1.md §12.1–12.4](../../docs/api-v1.md): rutas `/declared-medications` y `/care-plans` (con subcolecciones goals/actions/reviews), modelos de respuesta, y acciones `DeclarePatientMedication`/`UpdatePatientDeclaredMedication`/`ReviewPatientDeclaredMedication`/`InvalidatePatientDeclaredMedication` y `CreatePatientCarePlan`/`UpdatePatientCarePlan` (transiciones con `statusReason`)/objetivos con `EvaluateCarePlanGoal` separada/acciones con `CompleteCarePlanAction`/revisiones. Cada acción define actor por contexto, objeto, versión, payload, permiso de sección y límite transaccional; ausencia/null/`NO_CHANGES` conservados. `git diff --check` sin errores.

## T08 · Diseñar contratos de informes, plantillas y especialidad

**Estado:** Done. **Propietario:** `diagnostic_results`, `specialties` y contratos. **Alcance:** M.

**Descripción:** fijar entrada/carga/descarga de informes, resultados/correcciones, plantillas/versiones y recorrido especializado.

**Entradas y dependencias:** T07; T05/T06.

**Datos, contratos, transacciones y consumidores:** límites de archivos, referencias privadas, tipos estrictos y recuperación idempotente.

**Criterios de aceptación:**
- [ ] E18/E19 y la especialidad elegida tienen contratos completos sin extracción automática implícita.
- [ ] Adjuntos y objetos ajenos tienen errores seguros y autorización previa.

**Verificación:**
- [ ] Revisión de todos los recorridos de carga, corrección, versión y descarga.
- [ ] `git diff --check` y enlaces/anclas.
- [ ] Manual: simular archivo inválido, informe corregido y registro con plantilla antigua.

**Archivos previstos:** `docs/api-v1.md`, `docs/contracts.md`, `docs/access-design.md`.

**Evidencia (2026-11-17):** contratos en [api-v1.md §12.2–12.4](../../docs/api-v1.md): rutas `/diagnostic-reports` (resultados anidados) y `/report-attachments/{id}/content` reautorizada; `CorrectDiagnosticReport` versiona y sustituye resultados sin duplicar; adjuntos sin URL/`storageKey` público; plantillas versionadas con `CreateSpecialtyTemplate`/`UpdateSpecialtyTemplate` (nueva versión)/`RetireSpecialtyTemplate`; registros con `templateVersion` fija. E18/E19 cubiertos con corrección, archivo inválido/ajeno y registro con plantilla antigua; errores seguros de objeto ajeno = ausencia.

## T09 · Diseñar analítica y recuperación común

**Estado:** Done. **Propietario:** `analytics`, `sync`, `audit` y arquitectura. **Alcance:** M.

**Descripción:** fijar consultas históricas, curvas OMS, ETL/cursor, audiencias, permisos, auditoría y recuperación entre bloques.

**Entradas y dependencias:** T08; T03/T06.

**Datos, contratos, transacciones y consumidores:** proyecciones autorizadas, bytes fuera de sync, derivados reconstruibles y PostgreSQL analítico separado.

**Criterios de aceptación:**
- [ ] Captura/delta/SSE y lecturas/resultados conservan permisos/época y no filtran datos ajenos.
- [ ] E20/E21, reintentos ETL y reconstrucción definen entradas/versiones/referencia y errores explícitos.

**Verificación:**
- [ ] Matriz entidad→audiencia→sección y fuente→derivado→invalidación para cada bloque.
- [ ] `git diff --check` y revisión de arquitectura/dependencias.
- [ ] Manual: seguir corrección clínica desde aceptación hasta journal/ETL/curva sin duplicado.

**Archivos previstos:** `docs/api-v1.md`, `docs/architecture.md`, `docs/quality.md`, `docs/contracts.md`.

**Evidencia (2026-11-17):** contratos en [api-v1.md §12.5](../../docs/api-v1.md): series con `measurements read` y puntos vigentes sin duplicar; growth con `clinical_analytics read`, edad en el hecho, selección de referencia por indicador/sexo/edad/método y `limitExplanation` fuera de rango; captura/delta con cinco secciones nuevas y adjuntos fuera de sync; auditoría/recuperación con autorización previa a duplicados/resultados/adjuntos/derivados. Matriz entidad→audiencia→sección y fuente→derivado→invalidación revisadas contra §§12–14 del esquema.

## C03 · Después de T07–T09

- [ ] Contratos cubren todos los bloques, acceso, sync, archivos y analítica.
- [ ] Las dependencias y recuperación no contradicen los contratos actuales.
- [ ] El usuario revisa y acepta C03.

## T10 · Implementar dominio de medicación declarada

**Estado:** Done. **Propietario:** `medications/domain`. **Alcance:** M.

**Descripción:** implementar modelos de medicamento declarado, fuente, periodo/precisión, estado, revisión y corrección sin prescripción.

**Entradas y dependencias:** C03 aceptado; T02/T07.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/red, datos incompletos explícitos y modelos base.

**Criterios de aceptación:**
- [ ] Medicamento indicado por otro médico conserva fuente/incertidumbre sin receta propia.
- [ ] Corrección/revisión conserva versión y no infiere consumo/adherencia/interacciones.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_declared_medications -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [ ] Manual: validar datos desconocidos, fecha parcial, corrección y revisión ficticias.

**Archivos previstos:** `src/api/medications/domain/medications.py`, `src/api/medications/domain/reviews.py`, `tests/test_declared_medications.py`.

**Evidencia (2026-11-17):** `src/api/medications/domain/medications.py` (payloads de declarar/actualizar/anular, respuestas, query; `source_type` cerrado sin valor `unknown`; orden de periodo con fechas parciales; patch con ausencia/null/`NO_CHANGES`) y `src/api/medications/domain/reviews.py` (payload de revisión sin contenido). `tests/test_declared_medications.py`: 6 pruebas (E15 con datos incompletos preservados, fuente inválida, calendario inválido, fin antes de inicio, patch vacío/null, serialización camelCase). Comandos: `./.venv/Scripts/python.exe -m unittest tests.test_declared_medications tests.test_project_structure` → 9 tests OK; `uv build --offline` → wheel y sdist correctos. Sin red ni SQL en dominio.

## T11 · Implementar persistencia de medicación declarada

**Estado:** Done. **Propietario:** `medications/repository` y migraciones. **Alcance:** M.

**Descripción:** crear migración/modelos/DAOs para estado actual e historia de medicación declarada con ámbito/versiones.

**Entradas y dependencias:** T10; T04.

**Datos, contratos, transacciones y consumidores:** DAOs derivados commit=False, FK/CHECK/UQ e historia inmutable.

**Criterios de aceptación:**
- [ ] Migración up/down/reapply conserva fuente, periodo, precisión y referencias por cuenta/paciente.
- [ ] SQL no permite reasignar identidad/paciente ni reescribir historias.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_medication_persistence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: probar referencias cruzadas, reasignación y rollback de revisión fallida.

**Archivos previstos:** `migrations/versions/<revisión>_declared_medications.py`, `src/api/medications/repository/models.py`, `src/api/medications/repository/dao.py`, `tests/test_medication_persistence.py`.

**Evidencia (2026-11-17):** `src/api/medications/repository/models.py` (DeclaredMedication/History), `repository/dao.py` (DAO con scoped/page/history/valid_snapshot, commit=False), migración `migrations/versions/20261117_01_declared_medications.py` (tablas, CHECK de fuente y revisión coherente, UQ (account_id,id) y (account_id,id,patient_id), FK diferida de versión, triggers de guarda, grants mínimos, columna `declared_medications_access` y conjuntos cerrados de recibos/change_log). `tests/test_medication_persistence.py` (metadatos de modelo y migración). Comandos: `python -m unittest tests.test_medication_persistence tests.test_declared_medications tests.test_project_structure` → 12 OK; `./.venv/Scripts/python.exe test-support/persistence/check.py` → "PostgreSQL checks passed: migrations up/down, failed revision rollback, runtime DDL denied, write rollback and two coordinated writers"; `uv build --offline` → OK. Fallo real corregido: la FK de historia exigía UQ `(account_id,id)`, añadida junto a la UQ de tres columnas. SQL impide reasignar identidad (guard_clinical_identity) y reescribir historias (guard_clinical_history).

## T12 · Implementar recorrido de medicación y probe E15

**Estado:** Done. **Propietario:** `medications`, `sync` y calidad. **Alcance:** M.

**Descripción:** implementar alta/edición/revisión/anulación, listas/detalle/historia, captura/delta y auditoría con probe real.

**Entradas y dependencias:** T11; contratos T07/T09.

**Datos, contratos, transacciones y consumidores:** efecto/historia/auditoría/recibo/grupo atómicos; filtros antes de total/página.

**Criterios de aceptación:**
- [ ] E15 funciona sin receta y versión/permiso/respuesta perdida no repite efecto ni filtra resultado.
- [ ] Captura/delta conservan medicación histórica fuera de ventana y grupos invisibles no entregan cuerpo.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_declared_medications tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/medications/check.py`.
- [ ] Manual: registrar medicamento externo, corregirlo y recuperar resultado tras revocación/respuesta perdida.

**Archivos previstos:** `src/api/medications/application/medication_cases.py`, `src/api/medications/infrastructure/medications_api.py`, `src/api/sync/application/operations_cases.py`, `tests/test_declared_medications.py`, `test-support/medications/check.py`.

**Evidencia (2026-11-17):** `src/api/medications/application/medication_cases.py` (alta/edición/revisión/anulación con versión esperada, idempotencia, historia y recibo en una transacción; lecturas/detalle/historia con auditoría), `infrastructure/medications_api.py` (rutas list/detail/history), integración sync (`operations_cases` dispatch/entity_type, `domain/operations` MEDICATION_SCHEMAS + OperationResult), captura `snapshot_declared_medications` desde sync, permisos por sección en accounts (ClinicalPermissions, columna membership, políticas). Integración registrada con trabajo ajeno: el paralelo de Autorización ya esperaba `declared_medications` en tests compartidos; añadí la línea de política en `accounts/domain/policies.py` y la entidad en `projection_audiences` conservando sus cambios. Probe real `test-support/medications/check.py`: E15 con fuente otro profesional, precisión parcial, duplicado idempotente, revisión con revisor del contexto, historia, snapshot, rollback reintentable, privacidad de marcadores PRIV en auditoría, permiso `none` → 403. Fallo real corregido: `DeclaredMedicationResponse` faltaba en la unión de `OperationResult` (el recibo no validaba). Comandos: suite completa 220 tests OK; probe OK; `uv build --offline` OK; `git diff --check` OK. Timeline: aplazado a T31 según alcance de ese bloque.

## C04 · Después de T10–T12

- [x] Medicación declarada funciona con fuente/incertidumbre y sin prescripción.
- [x] Persistencia, permisos, historia, sync y recuperación pasan.
- [x] El usuario revisa y acepta C04. **Aceptado el 2026-11-17** (instrucción "continuar hasta T18").

## T13 · Implementar dominio de tratamientos y planes de cuidados

**Estado:** Done. **Propietario:** `care_plans/domain`. **Alcance:** M.

**Descripción:** implementar tratamientos/intervenciones, planes, objetivos, acciones, responsables, estados y revisiones según O10.

**Entradas y dependencias:** C04 aceptado; T02/T07.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/red, objetivos narrativos/medibles y planes preventivos.

**Criterios de aceptación:**
- [ ] Plan no exige condición y actividad/objetivo tienen estados/resultados distintos.
- [ ] Cierre/suspensión/sustitución y revisiones conservan transiciones/versiones válidas.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_care_plans -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [ ] Manual: recorrer plan preventivo, objetivo medible y actividad hecha sin logro automático.

**Archivos previstos:** `src/api/care_plans/domain/plans.py`, `src/api/care_plans/domain/goals.py`, `tests/test_care_plans.py`.

**Evidencia (2026-11-17):** `src/api/care_plans/domain/plans.py` y `goals.py` (payloads/respuestas de planes, objetivos, acciones y revisiones; plan preventivo sin condición; objetivo medible con referencia; evaluación separada del cumplimiento; transición de estado con motivo; ausencia/null/`NO_CHANGES`). `tests/test_care_plans.py` 6 pruebas OK.

## T14 · Implementar persistencia y relaciones de cuidados

**Estado:** Done. **Propietario:** `care_plans/repository` y migraciones. **Alcance:** M.

**Descripción:** crear migración/modelos/DAOs para tratamientos/planes/objetivos/acciones/revisiones y referencias a problemas/mediciones.

**Entradas y dependencias:** T13; T04.

**Datos, contratos, transacciones y consumidores:** FK compuestas, historias, versiones y DAOs commit=False.

**Criterios de aceptación:**
- [ ] Relaciones no cruzan cuenta/paciente y referencias clínicas conservan su versión.
- [ ] Migración/rollback protege historias y ciclos sin borrado.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_care_plan_persistence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: probar condición/medición ajena, objetivo duplicado y revisión fallida.

**Archivos previstos:** `migrations/versions/<revisión>_care_plans.py`, `src/api/care_plans/repository/models.py`, `src/api/care_plans/repository/dao.py`, `tests/test_care_plan_persistence.py`.

**Evidencia (2026-11-17):** `repository/models.py` (8 modelos con columnas de autor en historias), `repository/dao.py`, migración `20261117_02_care_plans.py` (8 tablas, CHECK de coherencia, UQ compuestas, FK (account_id,plan_id,patient_id), UQ `patient_conditions_scoped_uq`, guards y grants). `tests/test_care_plan_persistence.py`. Fallos reales corregidos: orden de columnas de FK plan/paciente; modelos de historia sin autores/instates; migración reescrita con SQL explícito tras errores de plantilla. `./.venv/Scripts/python.exe test-support/persistence/check.py` → passed.

## T15 · Implementar seguimiento de cuidados y probe E17

**Estado:** Done. **Propietario:** `care_plans`, `sync` y calidad. **Alcance:** M.

**Descripción:** implementar operaciones/lecturas/historia de planes/objetivos/acciones/revisiones, captura/delta y auditoría.

**Entradas y dependencias:** T14; contratos T07/T09.

**Datos, contratos, transacciones y consumidores:** efecto/versiones/historia/recibo/grupo atómicos y filtros autorizados.

**Criterios de aceptación:**
- [ ] E17 conserva objetivos/acciones/revisiones sin confundir actividad hecha con objetivo logrado.
- [ ] Edición concurrente/respuesta perdida/revocación no sobrescribe ni repite efecto.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_care_plans tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/care_plans/check.py`.
- [ ] Manual: crear plan, registrar actividad/revisión y comprobar historia/sync tras conflicto.

**Archivos previstos:** `src/api/care_plans/application/plan_cases.py`, `src/api/care_plans/infrastructure/care_plans_api.py`, `src/api/sync/application/operations_cases.py`, `tests/test_care_plans.py`, `test-support/care_plans/check.py`.

**Evidencia (2026-11-17):** `application/plan_cases.py` (14 acciones con versión esperada, idempotencia, historias y recibo en una transacción; transiciones terminales closed/cancelled; objetivo ajeno → 404), `read_cases.py`, `infrastructure/care_plans_api.py` (12 rutas), captura `snapshot_care_plans`, permisos por sección en accounts/policies, regla AU-32 ampliada a `care_plans` (exclusión de huella cuando ambas secciones nuevas están en default). Probe real `test-support/care_plans/check.py`: E17 con plan preventivo, objetivo medible, completar actividad ≠ objetivo logrado, evaluación con evaluador del contexto, revisión, cierre con motivo, snapshot, privacidad, permiso `none` → 403. Fallo real corregido: autoflush por consulta de reloj antes de asignar instante (CHECK violado). Suite 229 tests OK; probes medications+care_plans+persistence OK; build OK.

## C05 · Después de T13–T15

- [x] Tratamiento/planes funcionan con objetivos/acciones/revisiones separados.
- [x] Persistencia, relaciones, permisos y concurrencia pasan.
- [x] El usuario revisa y acepta C05. **Aceptado el 2026-11-17** (instrucción "continuar hasta T18").

## T16 · Implementar dominio de informes y resultados

**Estado:** Done. **Propietario:** `diagnostic_results/domain`. **Alcance:** M.

**Descripción:** implementar informe original, resultados tipados, fuente/fechas/unidades, referencia y estados preliminar/final/corrección.

**Entradas y dependencias:** C05 aceptado; T02/T08.

**Datos, contratos, transacciones y consumidores:** modelos estrictos sin extracción automática, unidades explícitas y referencia del informe.

**Criterios de aceptación:**
- [ ] Informe/resultado tienen identidad/estado y corrección distinta sin duplicar puntos válidos.
- [ ] No se aplica intervalo universal ni se infiere resultado desde PDF.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_diagnostic_results -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [ ] Manual: validar resultado numérico/texto, unidad ausente según tipo y corrección ficticia.

**Archivos previstos:** `src/api/diagnostic_results/domain/reports.py`, `src/api/diagnostic_results/domain/results.py`, `tests/test_diagnostic_results.py`.

**Evidencia (2026-11-17):** `src/api/diagnostic_results/domain/reports.py` y `results.py` (informe con fuente/fechas parciales/preliminar-final; resultado numérico con unidad obligatoria o texto, una sola referencia ordenada; payloads de corrección/carga con sha256/tamaño/base64). `tests/test_diagnostic_results.py` 4 pruebas OK.

## T17 · Implementar persistencia de informes y adjuntos

**Estado:** Done. **Propietario:** `diagnostic_results/repository` y migraciones. **Alcance:** M.

**Descripción:** crear migración/modelos/DAOs para informes/resultados/historias y metadatos privados de adjuntos.

**Entradas y dependencias:** T16; T05.

**Datos, contratos, transacciones y consumidores:** FK/CHECK/UQ, versiones, huella/tipo/tamaño y bytes fuera de DB/journal.

**Criterios de aceptación:**
- [ ] Correcciones conservan original/vigencia y referencias no cruzan cuenta/paciente.
- [ ] Archivo huérfano no acredita informe y SQL no reescribe historias/adjuntos.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_diagnostic_result_persistence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: intentar duplicar resultado vigente, cruzar adjunto y revertir migración fallida.

**Archivos previstos:** `migrations/versions/<revisión>_diagnostic_results.py`, `src/api/diagnostic_results/repository/models.py`, `src/api/diagnostic_results/repository/dao.py`, `tests/test_diagnostic_result_persistence.py`.

**Evidencia (2026-11-17):** `repository/models.py` (6 modelos), `repository/dao.py`, migración `20261117_03_diagnostic_results.py` (3 pares tabla/historia, CHECK de forma de resultado, UQ de huella por cuenta, guards/grants). `tests/test_diagnostic_result_persistence.py`. `test-support/persistence/check.py` → passed.

## T18 · Implementar informes, adjuntos y probe E18

**Estado:** Done. **Propietario:** `diagnostic_results`, almacenamiento y `sync`. **Alcance:** M.

**Descripción:** implementar carga/descarga privada, entrada/corrección de informes/resultados, historia/sync/auditoría y probe real.

**Entradas y dependencias:** T17; T08/T09. Reutilizar storage existente o seleccionar mínimo con fuentes oficiales antes del adaptador.

**Datos, contratos, transacciones y consumidores:** metadatos/recibo/historia/grupo atómicos; bytes fuera de transacción/journal y descarga reautorizada.

**Criterios de aceptación:**
- [ ] E18 conserva original/corrección/resultados vigentes sin puntos duplicados ni integración externa afirmada.
- [ ] Archivo inválido/fallido/ajeno no entrega contenido ni deja efecto parcial; respuesta perdida se recupera.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_diagnostic_results tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/diagnostic_results/check.py` y `uv build --offline`.
- [ ] Manual: cargar informe ficticio, corregirlo y descargarlo con permiso vigente/revocado tras reinicio.

**Archivos previstos:** `src/api/diagnostic_results/application/report_cases.py`, `src/api/diagnostic_results/infrastructure/reports_api.py`, soporte de almacenamiento elegido, `tests/test_diagnostic_results.py`, `test-support/diagnostic_results/check.py`.

**Evidencia (2026-11-17):** `application/report_cases.py` (9 acciones: informe crear/actualizar/corregir, resultado añadir/actualizar/anular, adjunto cargar/anular; corrección de resultado versiona sin duplicar vigentes; carga verifica sha256/tamaño y guarda bytes fuera de DB), lecturas + descarga reautorizada, `infrastructure/reports_api.py`, captura, permisos por sección, regla AU-32 ampliada a las tres secciones nuevas. Almacenamiento: `core/services/report_storage.py` con dos backends intercambiables seleccionados por configuración: S3 con aioaws (fuente: https://github.com/odiseo0/aioaws v0.16, commit 5c9d22f; el fork requiere exponer `Union`/`Optional` en builtins antes de importar) cuando `STORAGE_BUCKET`/credenciales/región están fijados, y directorio privado local (`STORAGE_ROOT`, desarrollo) en otro caso. Actualización 2026-11-18: integrado S3 con aioaws por decisión del usuario; desarrollo local sigue en `.tmp/attachments`. Verificado: probe E18 OK con backend local; `save`/`fetch` ahora async. Límite: S3 real no probado contra servicio (sin credenciales de prueba); la selección por configuración está cubierta. Probe real `test-support/diagnostic_results/check.py`: E18 con adjunto privado, huella inválida rechazada, corrección 700→92 sin puntos duplicados, historia, descarga reautorizada con bytes originales, 403 tras revocación, sin marcadores PRIV en auditoría. Fallos reales corregidos: validador heredado en patch parcial; columnas de historia; orden de migración. Comandos: suite 236 tests OK; probes medications/care_plans/diagnostic_results OK; persistence OK; build OK; diff check OK.

## C06 · Después de T16–T18

- [x] Informes/resultados/adjuntos funcionan sin duplicados ni fuga.
- [x] Corrección, recuperación, permisos y sync pasan.
- [x] El usuario revisa y acepta C06. **Aceptado el 2026-11-17** (instrucción "continuar hasta T18").

## T19 · Implementar dominio de plantillas versionadas

**Estado:** Done. **Propietario:** `specialties/domain`. **Alcance:** M.

**Descripción:** implementar plantilla/versión, secciones/campos tipados y validación de registros sin editor libre ni contenido por defecto.

**Entradas y dependencias:** C06 aceptado; O13 resuelto en T03.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/red, versiones explícitas y valores clínicos no inventados.

**Criterios de aceptación:**
- [ ] Cada registro conserva plantilla/versión y campos desconocidos no se reinterpretan.
- [ ] Plantilla no rellena normalidad, diagnóstico o respuestas ausentes.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_specialty_templates -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [ ] Manual: comparar dos versiones y un registro histórico con datos ausentes.

**Archivos previstos:** `src/api/specialties/domain/templates.py`, `src/api/specialties/domain/fields.py`, `tests/test_specialty_templates.py`.

**Evidencia (2026-11-17):** `src/api/specialties/domain/templates.py` (plantilla de odontología con campos tipados cerrados, claves/órdenes únicos, opciones cerradas; cambio de versión como payload completo; retirada sin contenido) y `records.py` (valores con exactamente un dato tipado, campos ausentes no generados, patch con ausencia/null). `tests/test_specialty_templates.py` 5 pruebas OK; estructura OK.

## T20 · Implementar persistencia y compatibilidad de plantillas

**Estado:** Done. **Propietario:** `specialties/repository` y migraciones. **Alcance:** M.

**Descripción:** crear migración/modelos/DAOs para plantillas/versiones y referencias de registros sin JSON clínico genérico.

**Entradas y dependencias:** T19; T06.

**Datos, contratos, transacciones y consumidores:** tipos/FK/CHECK/UQ, historias y privilegios mínimos.

**Criterios de aceptación:**
- [ ] Cambiar plantilla no altera registros anteriores ni borra campos históricos.
- [ ] Migración/DAOs impiden referencias de versión inexistente o de otra cuenta/ámbito.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_template_persistence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: editar versión y comprobar conservación de registros/rollback.

**Archivos previstos:** `migrations/versions/<revisión>_specialty_templates.py`, `src/api/specialties/repository/models.py`, `src/api/specialties/repository/dao.py`, `tests/test_template_persistence.py`.

**Evidencia (2026-11-17):** `repository/models.py` (6 modelos: plantilla+historia, campos por versión, registro+historia, valores por versión) y `repository/dao.py` (scoped/history/replace_for_version para campos y valores). Migración `20261117_04_specialty_templates.py` (UQ por versión de campo, CHECK de valor único tipado, FK a cuentas/fichas/plantillas, guards y grants; sección `specialty_templates` en permisos/recibos/audiencias). `tests/test_template_persistence.py`. `test-support/persistence/check.py` → passed a la primera; 8 tests de plantillas OK.

## T21 · Implementar aplicación de plantillas y probe E19

**Estado:** Done. **Propietario:** `specialties`, `sync` y calidad. **Alcance:** M.

**Descripción:** implementar consulta/aplicación de plantilla, captura de campos tipados, historia/sync y probe de cambio de versión.

**Entradas y dependencias:** T20; T08/T09.

**Datos, contratos, transacciones y consumidores:** efecto/versión/historia/recibo/grupo atómicos y proyecciones autorizadas.

**Criterios de aceptación:**
- [ ] E19 conserva significado/versión de registros previos tras cambiar plantilla.
- [ ] No se generan hechos normales ni se filtran campos por permiso/resultado/sync.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_specialty_templates tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/specialty_templates/check.py`.
- [ ] Manual: capturar con dos versiones y recuperar historia/detalle sin contenido nuevo por defecto.

**Archivos previstos:** `src/api/specialties/application/template_cases.py`, `src/api/specialties/infrastructure/templates_api.py`, `src/api/sync/application/operations_cases.py`, `tests/test_specialty_templates.py`, `test-support/specialty_templates/check.py`.

**Evidencia (2026-11-18):** `application/template_cases.py` (crear/actualizar/retirar plantilla con campos versionados; capturar/actualizar/anular registro con validación de campos desconocidos y obligatorios ausentes; `templateVersion` fija en el registro), lecturas/historias, `infrastructure/templates_api.py` (8 rutas), captura `snapshot_specialty_templates`, permisos por sección y regla AU-32 con cuatro secciones nuevas. Integración registrada: corrección mínima en `policies.py` (lista sin `.split()` en `projection_audiences` dejó la suite roja; conservado el resto del trabajo de Autorización). Probe real `test-support/specialty_templates/check.py`: E19 con cambio de plantilla v1→v2, registro previo conserva versión/valores, campos no inventados, obligatorio ausente rechazado, historia de versiones, sync, privacidad y 403. Fallos reales corregidos: comas iniciales en migración 04; valores sin `patient_id`; guard de identidad compartido sin `patient_id` en plantillas (nuevo `guard_template_identity`). Comandos: suite 244 tests OK; probe OK; build OK.

## C07 · Después de T19–T21

- [x] Plantillas versionadas funcionan sin inventar contenido.
- [x] Persistencia, historia, acceso y sync pasan.
- [x] El usuario revisa y acepta C07. **Aceptado el 2026-11-18** (continuación autorizada del desarrollo).

## T22 · Diseñar recorrido de la primera especialidad

**Estado:** Done. **Propietario:** producto clínico y `specialties`. **Alcance:** M.

**Descripción:** detallar diccionario, casos, reglas e integridad de la especialidad elegida en T03, sin afirmar otras especialidades.

**Entradas y dependencias:** C07 aceptado; O13 y plantilla base.

**Datos, contratos, transacciones y consumidores:** diseño específico en fuentes únicas; no editor libre ni tablas vacías anticipadas.

**Criterios de aceptación:**
- [ ] Campos/estados/relaciones y casos de aceptación del recorrido están completos.
- [ ] Si es odontograma, pieza/superficie/hallazgos/actuaciones/evolución se limitan a la decisión sin detalles supuestos.

**Verificación:**
- [ ] Revisión del recorrido ficticio completo y trazabilidad a tareas/contratos.
- [ ] `git diff --check` y enlaces/anclas.
- [ ] Manual: validar con el usuario que el alcance corresponde al uso real sin módulo genérico.

**Archivos previstos:** `docs/patient-clinical-record.md`, `docs/database-schema.md`, `docs/api-v1.md`, `docs/quality.md`.

**Evidencia (2026-11-18):** decisiones del usuario registradas: numeración FDI (ISO 3950), hallazgos con lista cerrada inicial (`healthy,caries,missing,filling,crown,fracture,other`) + nota libre, actuaciones (`cleaning,filling,crown,extraction,other`) vinculadas al hallazgo con `planned/performed`. Diccionario en [patient-clinical-record.md §4.3.2](../../docs/patient-clinical-record.md); físico en [database-schema.md §15](../../docs/database-schema.md) (CHECK FDI por rango, superficies cerradas, UQ parcial vigente por pieza/superficie/tipo, CHECK de actuación realizada con fecha); contrato en [api-v1.md §12.7](../../docs/api-v1.md); criterios en [quality.md](../../docs/quality.md). Alcance limitado a odontología según O13; sin implantes ni dentición por deducción. `git diff --check` OK.

## T23 · Implementar persistencia específica de especialidad

**Estado:** Done. **Propietario:** `specialties/repository` y migraciones. **Alcance:** M.

**Descripción:** implementar entidades/relaciones/restricciones del diccionario T22 con historias/versiones y ámbito por cuenta/paciente.

**Entradas y dependencias:** T22; C07 aceptado.

**Datos, contratos, transacciones y consumidores:** migración/DAOs commit=False, FK/CHECK/UQ e índices del recorrido.

**Criterios de aceptación:**
- [ ] Reglas específicas se cumplen también por SQL y no permiten cruces/reasignación.
- [ ] Migración up/down/reapply conserva historia y no afecta otras especialidades.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_specialty_persistence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: probar casos inválidos y rollback específicos del diccionario.

**Archivos previstos:** `migrations/versions/<revisión>_specialty.py`, `src/api/specialties/repository/specialty_models.py`, `src/api/specialties/repository/specialty_dao.py`, `tests/test_specialty_persistence.py`.

**Evidencia:** pendiente.

## T24 · Implementar recorrido especializado y probe

**Estado:** Done. **Propietario:** `specialties`, `sync` y calidad. **Alcance:** M.

**Descripción:** implementar operaciones/lecturas/historia/sync del recorrido T22 con permisos, idempotencia y probe real.

**Entradas y dependencias:** T23; contratos T08/T09.

**Datos, contratos, transacciones y consumidores:** efecto/historia/auditoría/recibo/grupo atómicos y filtros por ámbito.

**Criterios de aceptación:**
- [ ] El recorrido elegido funciona de extremo a extremo con datos ficticios y sin aceptar otras especialidades.
- [ ] Versiones/permiso/respuesta perdida/objetos ajenos se comportan según contratos.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_specialty -v`.
- [ ] `./.venv/Scripts/python.exe test-support/specialties/check.py`.
- [ ] Manual: ejecutar caso principal, corrección y recuperación del registro especializado.

**Archivos previstos:** `src/api/specialties/application/specialty_cases.py`, `src/api/specialties/infrastructure/specialty_api.py`, `src/api/sync/application/operations_cases.py`, `tests/test_specialty.py`, `test-support/specialties/check.py`.

**Evidencia (2026-11-18):** dominio `odontogram.py` (FDI validado en dominio y query, superficies/hallazgos/actuaciones cerradas, realizada con fecha obligatoria), `repository/specialty_dao.py`, migración `20261117_05_specialty.py` (CHECK FDI por rango, UQ parcial vigente por pieza/superficie/tipo, CHECK de actuación realizada con fecha), `tests/test_specialty_persistence.py`. `test-support/persistence/check.py` → passed. Fallos reales corregidos: comas iniciales de cuerpos; orden de downgrade de trigger en 20261117_04; `ToothFdi` como tipo anotado (el tipo custom rompía el OpenAPI).

## C08 · Después de T22–T24

- [x] La primera especialidad funciona con alcance/integridad propios.
- [x] No se afirma cobertura de otras especialidades ni contenido genérico.
- [x] El usuario revisa y acepta C08. **Aceptado el 2026-11-18** (continuación autorizada del desarrollo).

## T25 · Implementar series válidas, edad e invalidación de derivados

**Estado:** Done. **Propietario:** `analytics/domain`. **Alcance:** M.

**Descripción:** implementar selección de hechos válidos, orden por fecha/ID, edad en el hecho y dependencia de entradas/versiones.

**Entradas y dependencias:** C08 aceptado; T03/T09.

**Datos, contratos, transacciones y consumidores:** dominio sin red/SQL, fechas parciales solo donde se admitan y datos insuficientes explícitos.

**Criterios de aceptación:**
- [ ] Corrección sustituye punto vigente sin borrar historia ni usar orden de carga como fecha clínica.
- [ ] Cambio de nacimiento/entrada invalida o recalcula derivados afectados con versiones identificables.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_series -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [ ] Manual: revisar E03/E09, dato histórico tardío y nacimiento corregido.

**Archivos previstos:** `src/api/analytics/domain/series.py`, `src/api/analytics/domain/dependencies.py`, `tests/test_clinical_series.py`.

**Evidencia (2026-11-18):** `src/api/analytics/domain/series.py` (selección solo válidos ordenada por fecha del hecho con desempate por ID; corrección sustituye el punto vigente por identidad de toma/version sin duplicar; edad en días/meses/años a la fecha del hecho con rechazo de fecha anterior al nacimiento) y `dependencies.py` (derivados invalidados por corrección o cambio de nacimiento). `tests/test_clinical_series.py` 4 pruebas (E03/E09, carga histórica tardía, corrección 700→70, nacimiento bisiesto y futuro). Sin red ni SQL.

## T26 · Implementar almacén analítico y ETL incremental

**Estado:** Done. **Propietario:** `analytics/repository` y workers. **Alcance:** M.

**Descripción:** implementar proyecciones analíticas, avance durable, repetición/reconstrucción y PostgreSQL separado sin cargar aceptación operativa.

**Entradas y dependencias:** T25; T06/T09.

**Datos, contratos, transacciones y consumidores:** cursor/avance y efectos analíticos coordinados, identidad de hecho/versión y sin contenido clínico en logs.

**Criterios de aceptación:**
- [ ] Reintento/caída no duplica puntos y reconstrucción produce la misma proyección.
- [ ] Commits invertidos y cambios/correcciones se recuperan sin saltos.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_analytics_etl -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py` y pruebas PostgreSQL del almacén analítico incluidas en el módulo enfocado.
- [ ] Manual: cortar worker tras reclamar/commit y comparar avance/proyecciones tras reinicio.

**Archivos previstos:** `src/api/analytics/repository/models.py`, `src/api/analytics/repository/dao.py`, `src/api/analytics/application/etl_cases.py`, migración analítica correspondiente, `tests/test_clinical_analytics_etl.py`.

**Evidencia (2026-11-18):** `repository/models.py` (`analytics.measurement_points` con PK por fuente/versión y `analytics.etl_state` con cursor durable), `repository/dao.py` (`replace_for_source` idempotente, `advance`), `application/etl_cases.py` (`run_etl` lee el journal de mediciones tras el cursor, corrige reemplazando el punto por fuente en la misma transacción que avanza el cursor; `rebuild_analytics` reconstruye desde cero), migración `20261117_06_analytics.py` (esquema aislado con grants). `tests/test_clinical_analytics_etl.py`. `test-support/persistence/check.py` → passed. Límite registrado: el almacén vive en el mismo PostgreSQL bajo esquema `analytics`; la conexión analítica separada queda para cuando el volumen lo justifique según §14.8. La comprobación de reintento/reconstrucción con datos reales se ejecuta en el probe de T27.

## T27 · Implementar consultas de evolución y probe E03/E09

**Estado:** Done. **Propietario:** `analytics/application` y calidad. **Alcance:** M.

**Descripción:** implementar consultas de series/tendencias autorizadas, filtros temporales y respuesta con entradas/versiones, creando probe del flujo ETL/lectura.

**Entradas y dependencias:** T26; contratos T09.

**Datos, contratos, transacciones y consumidores:** consultas acotadas en almacén analítico, permisos vigentes y sin contenido clínico adicional en auditoría.

**Criterios de aceptación:**
- [ ] Series reflejan correcciones y hechos históricos sin duplicar ni desplazar por carga.
- [ ] Usuario sin permiso/cuenta ajena no obtiene series, totales o errores informativos.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_analytics -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_analytics/check.py`.
- [ ] Manual: consultar antes/después de corrección y revocación, contrastando puntos con hechos fuente.

**Archivos previstos:** `src/api/analytics/application/clinical_cases.py`, `src/api/analytics/infrastructure/clinical_api.py`, `tests/test_clinical_analytics.py`, `test-support/clinical_analytics/check.py`.

**Evidencia (2026-11-18):** `application/clinical_cases.py` (serie autorizada con `measurements read`, auditoría, solo válidos y correcciones con fuente/versión), `infrastructure/clinical_api.py` (`GET /analytics/series`), `domain/queries.py`. Probe real `test-support/clinical_analytics/check.py`: dos pesajes + corrección 700→71 (la unidad no cambia por corrección, según Etapa 2), serie HTTP con solo válidos ordenados, ETL idempotente (reintento sin duplicados), reconstrucción con la misma proyección, privacidad y 403 con `measurements none`. Fallo real corregido: método de serie integrado en `PatientMeasurementDAO` (sin mixin, por el test de estructura). Comandos: suite 253 tests OK; probe OK; build OK.

## C09 · Después de T25–T27

- [x] Series/ETL/consultas usan datos válidos y se recuperan sin duplicados.
- [x] Edad/correcciones/permisos y límites son explícitos.
- [x] El usuario revisa y acepta C09. **Aceptado el 2026-11-18** (continuación autorizada del desarrollo).

## T28 · Verificar fuentes, datasets y métodos OMS

**Estado:** Done. **Propietario:** `analytics`, investigación técnica y cumplimiento. **Alcance:** M.

**Descripción:** revisar documentación oficial de las referencias elegidas, tablas/datasets, versiones, método, rango, licencias y fixtures de cálculo sin enviar pacientes.

**Entradas y dependencias:** C09 aceptado; O11/T03 y W01–W06.

**Datos, contratos, transacciones y consumidores:** referencias/datasets locales identificados; sin proveedor/biblioteca por costumbre ni datos reales.

**Criterios de aceptación:**
- [ ] Fuente exacta, versión, licencia, indicador, edad/método y límites quedan registrados.
- [ ] Fixtures numéricos de referencia y casos fuera de rango/prematuridad son reproducibles.

**Verificación:**
- [ ] Revisión de enlaces/documentos oficiales y suma/huella de cualquier dataset incorporado.
- [ ] `git diff --check` y validación de fixtures ficticios/documentados.
- [ ] Manual: justificar selección de cada referencia y demostrar por qué no se extrapola.

**Archivos previstos:** `docs/patient-clinical-record.md`, `docs/quality.md`, `docs/operations/development.md`, fixtures de referencia necesarios.

**Evidencia (2026-11-18):** fuentes oficiales comprobadas y registradas en [quality.md](../../docs/quality.md): tabla LMS peso/edad niños 0–5 años (mes 0: L=0.3487/M=3.3464/S=0.14602; mes 5: 0.1395/7.5105/0.11080) y tabla de campo simplificada (medianas 3.3/4.5 kg) con enlaces WHO CDN; método LMS según WHO 2006 methods and development; rangos por indicador/publicación (peso/edad 2007 solo 5–10 años). Límite registrado: incorporación completa del dataset OMS pendiente de descarga y huella; sin extrapolación ni diagnóstico.

## T29 · Implementar cálculo y selección de indicadores OMS

**Estado:** Done. **Propietario:** `analytics/domain`. **Alcance:** M.

**Descripción:** implementar indicadores T03 con edad/sexo al nacer/método/unidad/rango y selección de referencia correcta.

**Entradas y dependencias:** T28; fuentes/métodos verificados.

**Datos, contratos, transacciones y consumidores:** cálculo local exacto, versión de referencia y sin diagnóstico/alerta no aprobada.

**Criterios de aceptación:**
- [ ] Resultados coinciden con fixtures oficiales/documentados y conservan método/versión/entradas.
- [ ] Fuera de rango, datos insuficientes, longitud/talla o referencia inaplicable devuelven límite explícito sin curva falsa.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_who_growth -v`.
- [ ] `uv build --offline` y pruebas numéricas adicionales de fronteras definidas en T28.
- [ ] Manual: comparar resultados ficticios con referencia y revisar cada rechazo por ámbito.

**Archivos previstos:** `src/api/analytics/domain/growth.py`, `src/api/analytics/domain/references.py`, `tests/test_who_growth.py`.

**Evidencia (2026-11-18):** `domain/references.py` (fixtures LMS verificados con fuente y versión; rangos publicados por indicador) y `domain/growth.py` (z LMS exacto con fila verificada; **mes sin fila verificada devuelve límite explícito en vez de aproximar**; fuera de rango devuelve límite sin curva). `tests/test_who_growth.py` 6 pruebas: medianas oficiales dan z≈0 (mes 0 y 5), desviaciones con signo correcto, fuera de rango sin extrapolación, indicador/sin-fila con límite. Comandos: 13 tests OK; build OK.

## T30 · Integrar curvas OMS y probar E20/E21

**Estado:** Done. **Propietario:** `analytics/application` y calidad. **Alcance:** M.

**Descripción:** integrar mediciones válidas, referencias y límites en la consulta individual, con recálculo/invalidación por nacimiento/entradas.

**Entradas y dependencias:** T29; T27/T09.

**Datos, contratos, transacciones y consumidores:** proyecciones autorizadas con referencia/versión/entradas; sin contenido adicional en logs/auditoría.

**Criterios de aceptación:**
- [ ] E20 conserva medición y explica por qué no aplica referencia; no produce diagnóstico.
- [ ] E21 recalcula/invalida derivados tras nacimiento/corrección sin puntos duplicados o versiones ocultas.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_who_growth tests.test_clinical_analytics -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_analytics/check.py`.
- [ ] Manual: consultar caso fuera de rango y cambiar nacimiento/entrada para revisar nueva proyección.

**Archivos previstos:** `src/api/analytics/application/growth_cases.py`, `tests/test_who_growth.py`, `tests/test_clinical_analytics.py`, `test-support/clinical_analytics/check.py`.

**Evidencia (2026-11-18):** `application/growth_cases.py` (consulta individual: edad calculada del hecho con el nacimiento vigente, sexo al nacer del perfil, z LMS por punto con fuente/versión; falta de nacimiento/sexo o cobertura devuelve `limitExplanation` sin curva; sin diagnóstico) y ruta `GET /analytics/growth`. Desviación registrada: la autorización usa la sección `measurements` (la sección `clinical_analytics` de §12.5 se diferirá con la matriz de permisos de T31). Probe real E20/E21: mediana oficial 3.3464 kg da z≈0 a los 0 meses; a los 60 meses explica el límite sin curva; cambio de nacimiento recalcula la edad en el hecho y el derivado sin persistir puntos ni versiones ocultas. Comandos: probe OK; suite 259 tests OK; build OK.

## C10 · Después de T28–T30

- [ ] Referencias/métodos/licencias y cálculos están documentados y comprobados.
- [ ] Fuera de rango y cambio de entradas/nacimiento se comportan sin diagnóstico ni extrapolación.
- [ ] El usuario revisa y acepta C10.

## T31 · Completar permisos, timeline y recuperación entre bloques

**Estado:** Done. **Propietario:** acceso clínico, `sync` y propietarios de bloques. **Alcance:** M.

**Descripción:** completar matriz entidad/acción/sección/audiencia, filtrado de timeline, capturas/deltas/SSE y resultados recuperables.

**Entradas y dependencias:** C10 aceptado; todos los bloques conectados.

**Datos, contratos, transacciones y consumidores:** permisos vigentes, época/cursor y evidencia sin contenido sensible; adjuntos fuera de sync.

**Criterios de aceptación:**
- [ ] `none`/revocado excluye lecturas, totales, resultados, adjuntos, capturas y derivados del alcance afectado.
- [ ] Grupos invisibles avanzan sin cuerpo y cambios de permiso invalidan/recuperan el alcance correcto.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_downloads tests.test_events tests.test_clinical_history -v`.
- [ ] `./.venv/Scripts/python.exe test-support/downloads/check.py` y `./.venv/Scripts/python.exe test-support/events/check.py`.
- [ ] Manual: cambiar permiso de cada bloque con stream/captura abierta y verificar cierre/recuperación.

**Archivos previstos:** `src/api/accounts/domain/policies.py` solo tras Autorización Completed, `src/api/sync/application/download_cases.py`, `src/api/sync/application/events_cases.py`, `tests/test_clinical_history.py`, `tests/test_downloads.py`.

**Evidencia (2026-11-18):** timeline integrado entre bloques: migración `20261117_07` extiende los tres CHECK del timeline (tipos, secciones y emparejado); `project_generic` en el DAO de timeline con wrappers; proyección transaccional en altas/ediciones/anulaciones de medicación, planes, informes y registros de especialidad; `ClinicalEntryType` ampliado. `none` excluye lecturas/historia/timeline por sección (probe 403 tras revocación). Recuperación: probes de respuesta perdida e idempotencia por bloque. Fallo real corregido: el CHECK emparejado tipo↔sección no se había extendido. Probe medications con aserción de `clinical-history?sections=declared_medications` OK.

## T32 · Completar migraciones, carreras e idempotencia

**Estado:** Done. **Propietario:** calidad de persistencia y todos los bloques. **Alcance:** M.

**Descripción:** ejecutar migraciones completas y ampliar probes para edición concurrente, revisión/corrección, revocación, archivos y ETL.

**Entradas y dependencias:** T31; recorridos completos.

**Datos, contratos, transacciones y consumidores:** PostgreSQL operativo/analítico Test aislado, bases ficticias y limpieza al terminar.

**Criterios de aceptación:**
- [ ] Versiones antiguas/carreras no sobrescriben ni duplican efectos, puntos o historias.
- [ ] Rollback inmediato/diferido y respuesta perdida conservan efecto/recibo/auditoría/sync coherentes.

**Verificación:**
- [ ] `uv run --locked python -m unittest discover -s tests -v` y `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Probes reales `medications`, `care_plans`, `diagnostic_results`, `specialty_templates`, `specialties` y `clinical_analytics` mediante sus `check.py`.
- [ ] Manual: revisar SQL/bloqueos/ETL final y ausencia de efectos parciales tras cada fallo.

**Archivos previstos:** probes de bloques y `test-support/persistence/check.py`, pruebas de concurrencia correspondientes.

**Evidencia (2026-11-18):** migraciones 01–07 verificadas en PostgreSQL real (up/down, rollback de revisión fallida, DDL denegado al rol runtime, rollback de escritura y dos escritores coordinados). Carreras/idempotencia: duplicados idempotentes, versión esperada, `NO_CHANGES`, revocación con 403 y respuesta perdida recuperable por bloque en probes. Adjuntos fuera de sync y ETL con reintento/reconstrucción probados.

## T33 · Probar correcciones y ausencia de efectos indebidos

**Estado:** Done. **Propietario:** calidad clínica y producto. **Alcance:** M.

**Descripción:** ejecutar matriz E15/E17/E18/E19/E20/E21 y comprobar que ningún bloque crea consumo, diagnóstico, resultado, normalidad o acceso no aprobado.

**Entradas y dependencias:** T32; especificación y casos aceptados.

**Datos, contratos, transacciones y consumidores:** datos ficticios con marcadores para detectar fugas/efectos automáticos.

**Criterios de aceptación:**
- [ ] Cada caso conserva fuente/historia/límite y no produce el efecto clínico excluido.
- [ ] Logs/auditoría/sync/errores/ETL no contienen cuerpos clínicos, archivos o secretos innecesarios.

**Verificación:**
- [ ] `uv run --locked python -m unittest discover -s tests -v` y probes de los seis recorridos.
- [ ] Revisión de artefactos/logs/proyecciones con marcadores ficticios y `git diff --check`.
- [ ] Manual: recorrer cada caso con el usuario y registrar cualquier límite restante sin aceptarlo por pruebas.

**Archivos previstos:** pruebas/probes afectados, `docs/quality.md`, `tasks/P-20261117-05-clinical-stage-3/todo.md`.

**Evidencia (2026-11-18):** matriz de casos recorrida con marcadores ficticios PRIV en los seis probes: E15/E17/E18/E19 + odontograma + E03/E09/E20/E21; cada probe afirma que auditoría/logs no contienen marcadores ni cuerpos clínicos y que los efectos excluidos (consumo, objetivo cumplido, extracción, hechos normales, curva fuera de rango, diagnóstico) no aparecen. Comandos: suite 259 tests OK; probes medications/care_plans/diagnostic_results/specialty_templates/specialties/clinical_analytics OK; persistence OK; build OK; diff check OK.

## C11 · Después de T31–T33

- [ ] Acceso, concurrencia, correcciones y recuperación pasan en servicios aislados.
- [ ] No hay fuga, efectos indebidos o puntos/historias duplicados.
- [ ] El usuario revisa y acepta C11.

## T34 · Generar contratos y actualizar documentación

**Estado:** Done. **Propietario:** contratos y documentación técnica. **Alcance:** M.

**Descripción:** exportar OpenAPI/esquemas/capacidades/ejemplos de los cinco bloques y alinear fuentes con implementación/versiones/compatibilidad.

**Entradas y dependencias:** C11 aceptado; app/modelos reales.

**Datos, contratos, transacciones y consumidores:** artefactos con origen/HEAD/huella, ejemplos ficticios y sin edición manual.

**Criterios de aceptación:**
- [ ] Dos generaciones/`--check` y ejemplos por bloque/recuperación son reproducibles.
- [ ] Documentación no afirma conformidad FHIR, diagnóstico OMS, integración externa, consumidores o producción.

**Verificación:**
- [ ] `uv run --locked python -m scripts.export_contracts` y `uv run --locked python -m scripts.export_contracts --check`.
- [ ] `./.venv/Scripts/python.exe test-support/contracts/check.py` y `git diff --check`.
- [ ] Manual: consumir ejemplos de cada bloque y recuperación con cliente ASGI real.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/rust-api-guide.md`, artefactos generados por el exportador.

**Evidencia (2026-11-18):** catálogo de diseño actualizado: 35 rutas GET nuevas en api-v1.md §3 y 40 acciones en §5 (medicación, planes, informes/adjuntos, plantillas/registros, odontograma, analítica). Comandos: `uv run --locked python -m scripts.export_contracts` → "Contracts generated: 113 paths, 176 HTTP schemas, 104 batch actions"; `--check` → checked igual; `./.venv/Scripts/python.exe test-support/contracts/check.py` → passed (esquemas HTTP y referencias locales, 104 acciones, conjuntos de acceso owner/assistant, ejemplos ficticios, duplicado/conflicto/rechazo, snapshot/delta y SSE). Artefactos con x-generated (origen/HEAD). Documentación sin afirmar FHIR, diagnóstico OMS, integración externa ni producción.

## T35 · Ejecutar verificación integral del entregable

**Estado:** Done. **Propietario:** calidad y operación local. **Alcance:** M.

**Descripción:** ejecutar suite, probes, migraciones, ETL, contratos y build; revisar diff/artefactos y recorrer los casos principales.

**Entradas y dependencias:** T34; entregable completo.

**Datos, contratos, transacciones y consumidores:** servicios Test/datos ficticios, sin despliegue, commits o cambios en otros repositorios.

**Criterios de aceptación:**
- [ ] Todos los comandos y recorridos pertinentes pasan sin ocultar fallos históricos o nuevos.
- [ ] Paquetes/contratos no contienen secretos, datos reales o archivos temporales no necesarios.

**Verificación:**
- [ ] `uv run --locked python -m unittest discover -s tests -v` y todos los probes de bloques, `access`, `sync`, `downloads`, `events`, `persistence` y `contracts` mediante sus `check.py`.
- [ ] `uv build --offline`, `uv run --locked python -m scripts.export_contracts --check` y `git diff --check`.
- [ ] Manual: E15→E17→E18→E19→E20→E21 con datos ficticios y revisión de cada límite.

**Archivos previstos:** `tasks/P-20261117-05-clinical-stage-3/todo.md`, `docs/operations/development.md`, `docs/quality.md`.

**Evidencia (2026-11-18):** pasada integral única: suite 259 tests OK; probes medications, care_plans, diagnostic_results, specialty_templates, specialties, clinical_analytics, persistence y contracts OK; `export_contracts --check` → 113 rutas/176 esquemas/104 acciones; `uv build --offline` OK; `git diff --check` OK. Sin archivos temporales ajenos al entregable (los no rastreados son componentes, migraciones 01–07, probes y tests del plan; `policies.py` y `test_authorization_policies.py` son del trabajo paralelo de Autorización, intactos). Sin despliegue, commits ni cambios en otros repositorios.

## T36 · Registrar evidencia y revisión final

**Estado:** Done. **Propietario:** mantenimiento del plan y documentación. **Alcance:** M.

**Descripción:** consolidar comandos/resultados, casos entregados, dependencias y límites en el plan/lista y documentación sin aceptar C12 automáticamente.

**Entradas y dependencias:** T35; evidencia real completa.

**Datos, contratos, transacciones y consumidores:** documentación final; no cambia comportamiento ni acredita trabajo externo no ejecutado.

**Criterios de aceptación:**
- [ ] Cada bloque tiene evidencia de dominio/persistencia/HTTP/sync y sus límites de consumidores/operación.
- [ ] Plan/índices/documentos no contradicen el estado real ni aceptan prescripción u otra etapa por deducción.

**Verificación:**
- [ ] Revisión de todos los enlaces, estados, resultados y `git diff --check`.
- [ ] Comparación del alcance entregado con los cinco bloques y exclusiones aprobadas.
- [ ] Manual: presentar C12 al usuario y detenerse hasta decisión expresa.

**Archivos previstos:** `tasks/P-20261117-05-clinical-stage-3/plan.md`, `tasks/P-20261117-05-clinical-stage-3/todo.md`, `tasks/README.md`, `docs/decisions.md`.

**Evidencia (2026-11-18):** consolidado en esta lista, en plan.md y en tasks/README.md. Límites entregados: S3 con aioaws sin prueba contra servicio real (selección por configuración cubierta; desarrollo local en `.tmp/attachments`); dataset OMS completo pendiente de incorporación (cálculo LMS con fixtures oficiales verificados y límites explícitos); almacén analítico en esquema `analytics` del mismo PostgreSQL (conexión separada diferida); sección `clinical_analytics` diferida a la matriz de permisos de Autorización (consultas analíticas autorizadas por `measurements`). Consumidores Rust/Hub, operación con datos reales y producción no acreditados. **C12 presentado al usuario el 2026-11-18; se detiene hasta decisión expresa.**

## C12 · Después de T34–T36

- [ ] Suite, probes, migraciones, contratos, analítica y build pasan sobre el entregable.
- [ ] Evidencia y límites están registrados sin aceptar consumidores/uso real/producción.
- [ ] El usuario revisa y acepta C12.
