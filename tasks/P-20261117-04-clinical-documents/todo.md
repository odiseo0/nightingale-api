# Lista de tareas: P-20261117-04-clinical-documents

**Plan:** [plan.md](plan.md). **Actualizado:** 2026-11-17. **Estado del plan:** Approved.

Todas las tareas están Todo. La ejecución requiere C10 aceptado de facturación. T01–T04 recogen decisiones y fuentes antes del trabajo dependiente; la aprobación de la especificación no responde estos pendientes.

## T01 · Cerrar requisitos jurídicos, datos mínimos y profesional a cargo

**Estado:** Todo. **Propietario:** producto, cumplimiento y `clinical_documents`. **Alcance:** M.

**Descripción:** revisar requisitos venezolanos aplicables, campos mínimos de cuenta/profesional/paciente y regla para emitir sobre atención de otro profesional.

**Entradas y dependencias:** facturación C10 aceptada; `CD-O01`, `CD-O02` y `CD-O12`.

**Datos, contratos, transacciones y consumidores:** decisiones/fuentes documentales; no acredita validez legal por pruebas técnicas.

**Criterios de aceptación:**
- [ ] Requisitos/fuentes oficiales o revisión competente y límites para uso real quedan registrados.
- [ ] Datos ausentes y relación emisor/atención tienen reglas explícitas sin inventar información.

**Verificación:**
- [ ] Revisión de enlaces oficiales y matriz de campos obligatorios/opcionales por tipo documental.
- [ ] `git diff --check` y ejemplos ficticios de datos ausentes/otro profesional.
- [ ] Manual: recorrer emisión válida, profesional ajeno y documento sin dato opcional.

**Archivos previstos:** `docs/clinical-documents.md`, `docs/decisions.md`, `docs/quality.md`.

**Evidencia:** pendiente.

## T02 · Cerrar permisos y numeración

**Estado:** Todo. **Propietario:** producto, `accounts` y seguridad. **Alcance:** M.

**Descripción:** decidir permisos iniciales de asistentes para lectura/borradores/sustitución/anulación y formato/secuencia/huecos de números REC/ORD.

**Entradas y dependencias:** T01; `CD-O03` y `CD-O04`.

**Datos, contratos, transacciones y consumidores:** diseño de acceso/secuencias, sin permisos clínicos heredados ni reutilización de números.

**Criterios de aceptación:**
- [ ] Owner/profesional/asistente/paciente tienen acciones y defaults explícitos.
- [ ] Prefijo, ámbito, reinicio, ceros, huecos y no reutilización están definidos.

**Verificación:**
- [ ] Matriz de acciones y ejemplos ficticios de dos emisiones/anulación/secuencia anual.
- [ ] `git diff --check` y enlaces a D14/especificación de autorización.
- [ ] Manual: revisar asistente que prepara pero no emite y número de documento sustituido.

**Archivos previstos:** `docs/clinical-documents.md`, `docs/access-design.md`, `docs/decisions.md`.

**Evidencia:** pendiente.

## T03 · Cerrar contenido y emisión online/offline

**Estado:** Todo. **Propietario:** producto clínico y arquitectura. **Alcance:** M.

**Descripción:** resolver campos de medicamento/posología/cantidad, texto libre o catálogo de exámenes/motivo y emisión online u offline.

**Entradas y dependencias:** T02; `CD-O05`–`CD-O07`.

**Datos, contratos, transacciones y consumidores:** reglas documentales; si offline se elige, numeración/conflictos deben quedar diseñados antes de T25.

**Criterios de aceptación:**
- [ ] Obligatoriedad por tipo y copia farmacia/paciente queda cerrada sin inferencias clínicas.
- [ ] Online/offline define autoridad, números, versiones, recuperación y límites de la rama T25.

**Verificación:**
- [ ] Ejemplos ficticios de receta multi-medicamento, orden multi-examen y emisión desconectada según elección.
- [ ] `git diff --check` y enlaces FHIR pertinentes.
- [ ] Manual: seguir respuesta perdida y dos dispositivos emitiendo bajo la regla elegida.

**Archivos previstos:** `docs/clinical-documents.md`, `docs/decisions.md`, `docs/architecture.md`.

**Evidencia:** pendiente.

## C01 · Después de T01–T03

- [ ] `CD-O01`–`CD-O07` y `CD-O12` están resueltos con fuentes/límites.
- [ ] Validación, permisos, numeración y rama online/offline son coherentes.
- [ ] El usuario revisa y acepta C01.

## T04 · Cerrar plantillas, QR, enlace y retención

**Estado:** Todo. **Propietario:** producto, presentación y seguridad. **Alcance:** M.

**Descripción:** decidir tamaño/paginación/textos fijos, proyección/antienumeración QR, vigencia/herencia del enlace y almacenamiento/retención de PDF.

**Entradas y dependencias:** C01 aceptado; `CD-O08`–`CD-O11`.

**Datos, contratos, transacciones y consumidores:** decisiones documentales; QR separado del enlace privado y sin contenido clínico público.

**Criterios de aceptación:**
- [ ] Ambas plantillas y desbordamiento conservan contenido/firma/QR sin truncar.
- [ ] QR, concesión/sustitutos y retención/copias tienen reglas explícitas sin borrado por anulación.

**Verificación:**
- [ ] Revisión de bocetos ficticios y matriz enlace válido/revocado/sustituto/QR anulado.
- [ ] `git diff --check` y fuentes OWASP/retención revisadas.
- [ ] Manual: evaluar contenido largo, paciente con sustituto y verificador público sin enlace privado.

**Archivos previstos:** `docs/clinical-documents.md`, `docs/access-design.md`, `docs/quality.md`, `docs/decisions.md`.

**Evidencia:** pendiente.

## T05 · Diseñar físicamente documentos, elementos e historias

**Estado:** Todo. **Propietario:** `clinical_documents/repository` y esquema físico. **Alcance:** M.

**Descripción:** incorporar cabecera común, elementos tipados, snapshots/emisiones e historias con tipos, claves, orden y conservación.

**Entradas y dependencias:** T04; T01–T03.

**Datos, contratos, transacciones y consumidores:** diseño sin migración; FK compuestas, UUID, estados/versiones y contenido inmutable.

**Criterios de aceptación:**
- [ ] Cuenta/paciente/tipo estables, cita/atención coherentes y elementos ordenados tienen restricciones.
- [ ] Sustitución/anulación/historia no reescribe emisión ni mezcla tipos mediante JSON libre.

**Verificación:**
- [ ] Revisión cruzada de reglas conceptuales con columnas/FK/CHECK/UQ/índices.
- [ ] `git diff --check` y fuentes PostgreSQL 18 pertinentes.
- [ ] Manual: evaluar dos documentos por cita, sustitución y cambio de paciente contra el diseño.

**Archivos previstos:** `docs/database-schema.md`, `docs/clinical-documents.md`.

**Evidencia:** pendiente.

## T06 · Diseñar físicamente artefactos, secuencias, concesiones y credenciales

**Estado:** Todo. **Propietario:** `clinical_documents/repository`, `accounts` y seguridad. **Alcance:** M.

**Descripción:** diseñar PDF/plantilla/huella, secuencias por cuenta/tipo, concesiones reutilizadas y ampliación de credenciales profesionales.

**Entradas y dependencias:** T05; T02/T04 y soporte de facturación.

**Datos, contratos, transacciones y consumidores:** bytes fuera de DB/sync, secretos con huella si aplica y snapshots profesionales.

**Criterios de aceptación:**
- [ ] Un artefacto→una emisión/plantilla y número único coordinado tienen restricciones/índices.
- [ ] Concesión y credenciales no cruzan cuentas ni exponen secreto/PDF en logs/journal.

**Verificación:**
- [ ] Matriz render pendiente/listo/fallido, doble emisión y enlace revocado contra restricciones.
- [ ] `git diff --check` y enlaces PostgreSQL/OWASP.
- [ ] Manual: evaluar reintento PDF y cambio de colegiatura posterior sin alterar emisión.

**Archivos previstos:** `docs/database-schema.md`, `docs/architecture.md`, `docs/access-design.md`.

**Evidencia:** pendiente.

## C02 · Después de T04–T06

- [ ] `CD-O08`–`CD-O11` están resueltos y el diseño físico es completo.
- [ ] Instantáneas, secuencias, artefactos, concesiones y credenciales tienen reglas verificables.
- [ ] El usuario revisa y acepta C02.

## T07 · Diseñar contratos, acceso, sync, timeline y QR

**Estado:** Todo. **Propietario:** `clinical_documents`, contratos, `sync` y acceso. **Alcance:** M.

**Descripción:** fijar rutas/operaciones/modelos de staff/paciente/verificador, permisos, audiencias, entradas de timeline y errores.

**Entradas y dependencias:** C02 aceptado; catálogo de autorización y concesión de facturación.

**Datos, contratos, transacciones y consumidores:** camelCase/page-shows, operaciones idempotentes, archivos privados y QR mínimo.

**Criterios de aceptación:**
- [ ] Cada acción tiene actor/objeto/versión/transacción/resultado y proyección autorizada.
- [ ] Timeline/snapshot/delta/SSE y QR excluyen contenido no permitido y definen recuperación.

**Verificación:**
- [ ] Cobertura de todos los casos §23 de la especificación y dependencias entre componentes.
- [ ] `git diff --check` y validación de enlaces/anclas.
- [ ] Manual: recorrer emisión con respuesta perdida, descarga revocada y QR de anulado.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/contracts.md`, `docs/quality.md`.

**Evidencia:** pendiente.

## T08 · Implementar dominio común de documentos e instantáneas

**Estado:** Todo. **Propietario:** `clinical_documents/domain`. **Alcance:** M.

**Descripción:** implementar cabecera, estados draft/issued/superseded/annulled, snapshots comunes y reglas de edición/versiones.

**Entradas y dependencias:** C02 aceptado; T07.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/red, tipos base, fechas finitas y ámbito estable.

**Criterios de aceptación:**
- [ ] Borrador editable/emisión inmutable/sustitución/anulación tienen transiciones cerradas.
- [ ] Cuenta/paciente/tipo/vínculos y datos ausentes no se cambian o inventan por patch.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_document_domain -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [ ] Manual: validar patch vacío/nulo, reimpresión y cambio de datos posterior a emisión.

**Archivos previstos:** `src/api/clinical_documents/domain/documents.py`, `src/api/clinical_documents/domain/snapshots.py`, `tests/test_clinical_document_domain.py`.

**Evidencia:** pendiente.

## T09 · Implementar dominio y validación de récipes

**Estado:** Todo. **Propietario:** `clinical_documents/domain`. **Alcance:** M.

**Descripción:** implementar elementos de medicamento, posología/cantidad, orden e indicaciones conforme a T03 y copias previstas.

**Entradas y dependencias:** T08; T03/T07.

**Datos, contratos, transacciones y consumidores:** modelos estrictos sin catálogo obligatorio, red o cálculo clínico automático.

**Criterios de aceptación:**
- [ ] Al menos un medicamento y campos por copia se validan sin truncar/inferir dosis.
- [ ] Emitir no crea medicación declarada, condición, dispensación o recomendación.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_prescriptions -v`.
- [ ] `uv run --locked python -m unittest tests.test_clinical_document_domain tests.test_prescriptions -v`.
- [ ] Manual: validar uno/varios medicamentos, datos opcionales ausentes y posología extensa.

**Archivos previstos:** `src/api/clinical_documents/domain/prescriptions.py`, `tests/test_prescriptions.py`.

**Evidencia:** pendiente.

## C03 · Después de T07–T09

- [ ] Contratos y dominio común/récipe cubren los recorridos aprobados.
- [ ] No hay contenido inferido ni emisión por guardar borrador.
- [ ] El usuario revisa y acepta C03.

## T10 · Implementar dominio y validación de órdenes

**Estado:** Todo. **Propietario:** `clinical_documents/domain`. **Alcance:** M.

**Descripción:** implementar motivo/diagnóstico, exámenes ordenados, notas e indicaciones según T03 sin seguimiento de laboratorio.

**Entradas y dependencias:** C03 aceptado; T07.

**Datos, contratos, transacciones y consumidores:** modelos tipados sin resultados, agenda, muestra o facturación derivada.

**Criterios de aceptación:**
- [ ] Motivo y al menos un examen cumplen contrato sin ayuno/preparación automática.
- [ ] Emitir no crea DiagnosticReport, resultado, cita de laboratorio o cargo.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_diagnostic_orders -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure tests.test_diagnostic_orders -v`.
- [ ] Manual: validar varios exámenes/notas, indicaciones largas y ausencia de cumplimiento derivado.

**Archivos previstos:** `src/api/clinical_documents/domain/orders.py`, `tests/test_diagnostic_orders.py`.

**Evidencia:** pendiente.

## T11 · Integrar credenciales profesionales y datos del paciente

**Estado:** Todo. **Propietario:** `accounts`, `patients` y `clinical_documents`. **Alcance:** M.

**Descripción:** añadir campos aprobados al perfil profesional y casos de selección/snapshot de cuenta, emisor, paciente y documento elegido.

**Entradas y dependencias:** T10; T01/T06.

**Datos, contratos, transacciones y consumidores:** casos públicos, versiones/permisos de perfil, datos actuales copiados al emitir.

**Criterios de aceptación:**
- [ ] Solo profesional autorizado edita credenciales y datos declarados/verificados no se confunden.
- [ ] Paciente con múltiples/ausentes documentos y sexo/nacimiento opcional produce snapshot sin inferencias.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_accounts tests.test_document_snapshots -v`.
- [ ] `./.venv/Scripts/python.exe test-support/accounts/check.py` y `./.venv/Scripts/python.exe test-support/patients/check.py`.
- [ ] Manual: editar credenciales tras emisión y verificar que el snapshot anterior no cambia.

**Archivos previstos:** `src/api/accounts/domain/accounts.py`, `src/api/accounts/application/management_cases.py`, `src/api/clinical_documents/application/snapshot_cases.py`, `tests/test_document_snapshots.py`.

**Evidencia:** pendiente.

## T12 · Implementar persistencia de documentos, elementos e historias

**Estado:** Todo. **Propietario:** `clinical_documents/repository` y migraciones. **Alcance:** M.

**Descripción:** crear migración/modelos/DAOs para cabecera, elementos tipados, snapshots e historias con aislamiento e inmutabilidad.

**Entradas y dependencias:** T11; T05.

**Datos, contratos, transacciones y consumidores:** DAOs derivados commit=False, FK/CHECK/UQ y privilegios mínimos.

**Criterios de aceptación:**
- [ ] Migración up/down/reapply protege ámbito, orden de elementos y versiones/historias.
- [ ] SQL no permite cruzar cuenta/paciente/cita/atención ni reescribir emisión.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_document_persistence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: intentar reasignar paciente, reordenar emisión y borrar historia con rol operativo.

**Archivos previstos:** `migrations/versions/<revisión>_clinical_documents.py`, `src/api/clinical_documents/repository/models.py`, `src/api/clinical_documents/repository/dao.py`, `tests/test_clinical_document_persistence.py`.

**Evidencia:** pendiente.

## C04 · Después de T10–T12

- [ ] Órdenes, snapshots y persistencia pasan pruebas de dominio/integridad.
- [ ] No hay inferencias, cruces de cuenta o historia reescrita.
- [ ] El usuario revisa y acepta C04.

## T13 · Implementar persistencia de artefactos, secuencias y concesiones

**Estado:** Todo. **Propietario:** `clinical_documents/repository` y migraciones. **Alcance:** M.

**Descripción:** añadir artefactos/plantillas/huellas, secuencias REC/ORD y relación con concesiones existentes según T06.

**Entradas y dependencias:** C04 aceptado; T02/T04/T06.

**Datos, contratos, transacciones y consumidores:** metadatos solamente, estados de render y número único coordinado.

**Criterios de aceptación:**
- [ ] Secuencias concurrentes no repiten número y artefacto pertenece a una emisión/plantilla.
- [ ] Concesión/documento no cruza cuentas y anulación conserva archivo/historia.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_document_persistence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: disputar secuencia, duplicar artefacto y cruzar concesión con SQL.

**Archivos previstos:** `migrations/versions/<revisión>_document_artifacts.py`, `src/api/clinical_documents/repository/models.py`, `src/api/clinical_documents/repository/dao.py`, `tests/test_clinical_document_persistence.py`.

**Evidencia:** pendiente.

## T14 · Implementar borradores y vista previa

**Estado:** Todo. **Propietario:** `clinical_documents` y `sync`. **Alcance:** M.

**Descripción:** implementar crear/editar/listar/detallar borradores, vista previa identificada y probe HTTP base sin número/acceso paciente.

**Entradas y dependencias:** T13; T02/T07.

**Datos, contratos, transacciones y consumidores:** versión/historia/auditoría/recibo/grupo en aceptación, vínculo automático desde cita.

**Criterios de aceptación:**
- [ ] Asistente/profesional con permiso edita sin emitir y cuenta/paciente/tipo permanecen estables.
- [ ] Vista previa/borrador no tiene número emitido, timeline público, paciente ni QR de vigencia.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_document_drafts tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_documents/check.py`.
- [ ] Manual: crear desde cita/atención, editar con versión antigua y comprobar que paciente no lo ve.

**Archivos previstos:** `src/api/clinical_documents/application/draft_cases.py`, `src/api/clinical_documents/infrastructure/documents_api.py`, `tests/test_clinical_document_drafts.py`, `test-support/clinical_documents/check.py`.

**Evidencia:** pendiente.

## T15 · Implementar emisión atómica y numeración

**Estado:** Todo. **Propietario:** `clinical_documents`, `sync` y `audit`. **Alcance:** M.

**Descripción:** implementar validación profesional, snapshots, número, vínculos, historia/timeline y trabajo durable de PDF en una aceptación.

**Entradas y dependencias:** T14; T01–T03/T13.

**Datos, contratos, transacciones y consumidores:** documento/secuencia/historia/timeline/auditoría/recibo/grupo/trabajo coordinados; sin red dentro.

**Criterios de aceptación:**
- [ ] Solo profesional autorizado emite y repetición/respuesta perdida conserva número/contenido.
- [ ] Edición o revocación concurrente no mezcla versiones ni permite efecto con acceso viejo.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_document_issuance tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_documents/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [ ] Manual: disputar edición/emisión y dos emisiones; revisar números, snapshot, SQL y recibo.

**Archivos previstos:** `src/api/clinical_documents/application/issuance_cases.py`, `src/api/sync/application/operations_cases.py`, `src/api/clinical_records/application/history_cases.py`, `tests/test_clinical_document_issuance.py`, `test-support/clinical_documents/check.py`.

**Evidencia:** pendiente.

## C05 · Después de T13–T15

- [ ] Persistencia, borradores y emisión atómica pasan.
- [ ] Números, snapshots, timeline y recibos no se duplican ni mezclan.
- [ ] El usuario revisa y acepta C05.

## T16 · Seleccionar e implementar base de renderizado PDF

**Estado:** Todo. **Propietario:** `core/services`, `clinical_documents` y documentación técnica. **Alcance:** M.

**Descripción:** comparar opciones mínimas con documentación oficial de versión, justificar elección e implementar render versionado sin contenido clínico propio.

**Entradas y dependencias:** C05 aceptado; manifiesto/lockfile y guía docs-first.

**Datos, contratos, transacciones y consumidores:** plantilla/versión, bytes fuera de journal y sin llamadas dentro de transacción.

**Criterios de aceptación:**
- [ ] Decisión/versión/fuente oficial y límites quedan registrados sin dependencia injustificada.
- [ ] El motor genera PDF válido, repetible para snapshot/plantilla y sin datos ficticios de relleno.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_document_rendering -v`.
- [ ] `uv build --offline` y revisión de lockfile/artefactos si cambia una dependencia justificada.
- [ ] Manual: inspeccionar PDF mínimo con datos ficticios, metadatos y ausencia de contenido no registrado.

**Archivos previstos:** `src/core/services/clinical_document_renderer.py`, `tests/test_document_rendering.py`, `docs/operations/development.md`, `pyproject.toml` y `uv.lock` solo si una dependencia queda justificada.

**Evidencia:** pendiente.

## T17 · Implementar plantilla de récipe con dos copias

**Estado:** Todo. **Propietario:** presentación de `clinical_documents`. **Alcance:** M.

**Descripción:** implementar encabezado, profesional/paciente, copia farmacia/paciente, indicaciones, firma en blanco, QR y paginación según T04.

**Entradas y dependencias:** T16; T03/T04.

**Datos, contratos, transacciones y consumidores:** snapshot emitido o vista previa marcada, plantilla versionada y datos ficticios de prueba.

**Criterios de aceptación:**
- [ ] Farmacia/paciente muestran exactamente sus campos y posología sin truncado.
- [ ] Contenido largo pagina con identificación/número y firma/QR en las copias requeridas.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_prescription_rendering -v`.
- [ ] Script de prueba de T16 para renderizar/inspeccionar PDFs ficticios en `.tmp` y `uv build --offline`.
- [ ] Manual: revisar visualmente una página y varias páginas, datos ausentes y vista previa de borrador.

**Archivos previstos:** `src/api/clinical_documents/application/prescription_templates.py`, `tests/test_prescription_rendering.py`, recursos de plantilla ficticios necesarios.

**Evidencia:** pendiente.

## T18 · Implementar plantilla de orden de diagnóstico

**Estado:** Todo. **Propietario:** presentación de `clinical_documents`. **Alcance:** M.

**Descripción:** implementar encabezado, motivo/diagnóstico, tabla de exámenes/notas, indicaciones, firma, QR y paginación.

**Entradas y dependencias:** T17; T03/T04.

**Datos, contratos, transacciones y consumidores:** snapshot tipado, sin preparación/ayuno automático ni resultados.

**Criterios de aceptación:**
- [ ] Todos los exámenes/notas/indicaciones aparecen sin contenido inventado o truncado.
- [ ] Páginas adicionales conservan número/identificación/firma/QR según T04.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_order_rendering -v`.
- [ ] Script de render/inspección de T16 y `uv build --offline`.
- [ ] Manual: inspeccionar orden corta/larga, motivo extenso y campos opcionales ausentes.

**Archivos previstos:** `src/api/clinical_documents/application/order_templates.py`, `tests/test_order_rendering.py`, recursos de plantilla ficticios necesarios.

**Evidencia:** pendiente.

## C06 · Después de T16–T18

- [ ] Motor y ambas plantillas generan PDF válidos y legibles.
- [ ] No hay truncado, datos ficticios clínicos o posología omitida.
- [ ] El usuario revisa y acepta C06.

## T19 · Implementar worker, almacenamiento y descarga de artefactos

**Estado:** Todo. **Propietario:** `clinical_documents`, workers y almacenamiento. **Alcance:** M.

**Descripción:** procesar intenciones duraderas, guardar PDF mediante soporte privado común, recuperar fallos y autorizar descargas.

**Entradas y dependencias:** C06 aceptado; almacenamiento de facturación y T11 de especificación.

**Datos, contratos, transacciones y consumidores:** estados pending/ready/failed, huella/tamaño/plantilla, reintentos sin nueva emisión.

**Criterios de aceptación:**
- [ ] Caída antes/después de guardar recupera el mismo documento/artefacto sin número nuevo.
- [ ] Descarga reautoriza y PDF/URL/huella no aparece en journal/logs.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_document_artifacts -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_documents/check.py`.
- [ ] Manual: inyectar fallo de render/storage, reiniciar y descargar con staff autorizado/ajeno.

**Archivos previstos:** `src/api/clinical_documents/application/artifact_cases.py`, `src/api/clinical_documents/infrastructure/artifacts_api.py`, `src/core/services/private_evidence.py` solo si el soporte común lo requiere, `tests/test_document_artifacts.py`, `test-support/clinical_documents/check.py`.

**Evidencia:** pendiente.

## T20 · Implementar sustitución, anulación e historia

**Estado:** Todo. **Propietario:** `clinical_documents`. **Alcance:** M.

**Descripción:** implementar nuevo documento sustituto, referencias recíprocas, anulación terminal y consulta de historia sin borrar artefactos.

**Entradas y dependencias:** T19; T02/T08.

**Datos, contratos, transacciones y consumidores:** versiones/estados/historia/auditoría/recibo/grupo coordinados; sin reimpresión como versión nueva.

**Criterios de aceptación:**
- [ ] Sustituto recibe nuevo ID/número y original queda superseded con ambos consultables.
- [ ] Anulación conserva motivo/actor/estado y carrera sustituir/anular tiene orden verificable.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_document_history -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_documents/check.py`.
- [ ] Manual: sustituir, anular, reimprimir y consultar cadena completa con PDF/estado correcto.

**Archivos previstos:** `src/api/clinical_documents/application/history_cases.py`, `tests/test_clinical_document_history.py`, `test-support/clinical_documents/check.py`.

**Evidencia:** pendiente.

## T21 · Extender concesiones del paciente para documentos

**Estado:** Todo. **Propietario:** acceso limitado API y `clinical_documents`. **Alcance:** M.

**Descripción:** reutilizar concesiones de facturación para read/download de documentos emitidos relacionados con cita y sustitutos según T04.

**Entradas y dependencias:** T20; concesiones C06 de facturación y D17.

**Datos, contratos, transacciones y consumidores:** objeto/acción/vigencia/revocación, proyección clínica mínima y auditoría de lectura/descarga.

**Criterios de aceptación:**
- [ ] Paciente no ve borradores ni otros documentos/historia y enlace revocado/ajeno falla cerrado.
- [ ] Sustituto hereda solo bajo T04 y anulado/sustituido muestra estado sin borrar descargas previas.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_document_patient_access tests.test_billing_patient_access -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_documents/check.py` y `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [ ] Manual: leer/descargar original/sustituto y revocar sin regresión de concesiones financieras.

**Archivos previstos:** soporte de concesión definido en facturación, `src/api/clinical_documents/application/patient_cases.py`, `src/api/clinical_documents/infrastructure/patient_api.py`, `tests/test_document_patient_access.py`, máximo cinco archivos.

**Evidencia:** pendiente.

## C07 · Después de T19–T21

- [ ] Artefactos, sustitución/anulación y acceso paciente pasan sin regresión de billing.
- [ ] Fallos no repiten emisión y concesiones no abren otra historia clínica.
- [ ] El usuario revisa y acepta C07.

## T22 · Implementar verificación pública mínima del QR

**Estado:** Todo. **Propietario:** `clinical_documents` y seguridad pública. **Alcance:** M.

**Descripción:** implementar resolución/verificación de número/fecha/profesional/estado según T04 con límites y antienumeración.

**Entradas y dependencias:** C07 aceptado; `CD-O09` resuelto.

**Datos, contratos, transacciones y consumidores:** endpoint público separado del micrositio/enlace privado, sin paciente ni contenido clínico.

**Criterios de aceptación:**
- [ ] Vigente/sustituido/anulado/inexistente devuelve solo proyección aprobada sin oráculo adicional.
- [ ] Rate limit/antienumeración y logs no contienen secreto QR, medicamentos, diagnóstico o exámenes.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_document_verification -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_documents/check.py` y pruebas de límite HTTP.
- [ ] Manual: escanear QR ficticio de cada estado y comparar con intento de descarga privada sin concesión.

**Archivos previstos:** `src/api/clinical_documents/application/verification_cases.py`, `src/api/clinical_documents/infrastructure/verification_api.py`, `tests/test_document_verification.py`.

**Evidencia:** pendiente.

## T23 · Implementar audiencias documentales en sync y timeline

**Estado:** Todo. **Propietario:** `sync`, `clinical_records` y `clinical_documents`. **Alcance:** M.

**Descripción:** publicar estados/referencias por permiso en captura/delta/SSE/timeline con filtrado antes de contar y sin PDF.

**Entradas y dependencias:** T22; T07.

**Datos, contratos, transacciones y consumidores:** proyecciones validadas, grupos completos, época/cursor y avisos mínimos.

**Criterios de aceptación:**
- [ ] Audiencias/secciones autorizadas reciben estados y grupos invisibles avanzan sin cuerpo.
- [ ] Timeline no contiene medicamentos/exámenes y captura/delta recupera cambios sin bytes.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_downloads tests.test_events tests.test_clinical_document_sync -v`.
- [ ] `./.venv/Scripts/python.exe test-support/downloads/check.py` y `./.venv/Scripts/python.exe test-support/events/check.py`.
- [ ] Manual: cambiar permiso con stream/captura abierta y recuperar sin contenido retirado.

**Archivos previstos:** `src/api/sync/application/snapshot_cases.py`, `src/api/sync/application/download_cases.py`, `src/api/sync/application/events_cases.py`, `src/api/sync/domain/downloads.py`, `tests/test_clinical_document_sync.py`.

**Evidencia:** pendiente.

## T24 · Implementar borradores offline y reautorización

**Estado:** Todo. **Propietario:** `clinical_documents`, `sync` y consumidores API. **Alcance:** M.

**Descripción:** admitir intenciones locales de borrador con UUID/versión, conservación ante rechazo y validación remota de permisos/relaciones.

**Entradas y dependencias:** T23; T03.

**Datos, contratos, transacciones y consumidores:** copia local no autoritativa, `operationId`, fecha local sin autoridad y emisión separada.

**Criterios de aceptación:**
- [ ] Borrador offline no recibe número/emisión/acceso paciente y reloj local no concede permiso.
- [ ] Rechazo conserva intención y respuesta perdida recupera mismo borrador/versión sin duplicado.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_document_offline tests.test_clinical_document_sync -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_documents/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [ ] Manual: preparar sin red, revocar permiso/cambiar vínculo y sincronizar sin efecto indebido o pérdida local.

**Archivos previstos:** `src/api/clinical_documents/application/offline_cases.py`, `tests/test_clinical_document_offline.py`, `test-support/clinical_documents/check.py`.

**Evidencia:** pendiente.

## C08 · Después de T22–T24

- [ ] QR, sync/timeline y borradores offline pasan con privacidad/recuperación.
- [ ] Ningún mecanismo público/local concede emisión o contenido indebido.
- [ ] El usuario revisa y acepta C08.

## T25 · Resolver rama de emisión offline elegida

**Estado:** Todo. **Propietario:** `clinical_documents` y `sync`. **Alcance:** M.

**Descripción:** si T03 aprobó offline, implementar su numeración/conflictos/recuperación; si eligió online, verificar rechazo explícito sin cambiar alcance.

**Entradas y dependencias:** C08 aceptado; diseño offline completo T03/T07. Si excede M, detener y replanificar antes de codificar.

**Datos, contratos, transacciones y consumidores:** rama elegida con permisos vigentes al aceptar, identidad de operación y números sin duplicado.

**Criterios de aceptación:**
- [ ] Rama offline aprobada no repite números/emisiones entre dispositivos, o rama online rechaza emisión local sin efecto remoto.
- [ ] Respuesta perdida/revocación conserva intención y nunca asigna vigencia por reloj del cliente.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_clinical_document_offline tests.test_clinical_document_issuance -v`.
- [ ] `./.venv/Scripts/python.exe test-support/clinical_documents/check.py`.
- [ ] Manual: ejecutar el escenario de dos dispositivos definido en T03 y comprobar el resultado elegido.

**Archivos previstos:** módulos definidos por T03/T07, `tests/test_clinical_document_offline.py`, `test-support/clinical_documents/check.py`, máximo cinco archivos o replanificación previa.

**Evidencia:** pendiente.

## T26 · Completar concurrencia, aislamiento y recuperación

**Estado:** Todo. **Propietario:** calidad de `clinical_documents`. **Alcance:** M.

**Descripción:** ampliar probes para numeración, edición/emisión, revocación, sustitución/anulación, concesiones y caídas tras commit.

**Entradas y dependencias:** T25; flujo completo.

**Datos, contratos, transacciones y consumidores:** PostgreSQL/Keycloak/storage Test y datos ficticios, con limpieza al terminar.

**Criterios de aceptación:**
- [ ] Ninguna carrera repite número/mezcla contenido ni acceso viejo produce efecto posterior.
- [ ] Logs/auditoría/sync/QR/errores no contienen PDF, secretos, medicamentos, diagnóstico o exámenes.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe test-support/clinical_documents/check.py` y `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] `uv run --locked python -m unittest discover -s tests -v`.
- [ ] Manual: revisar bloqueos, SQL final, artefactos y evidencia para cada fallo inyectado.

**Archivos previstos:** `test-support/clinical_documents/check.py`, `test-support/persistence/check.py`, `tests/test_document_patient_access.py`.

**Evidencia:** pendiente.

## T27 · Completar pruebas visuales y fallos de artefactos

**Estado:** Todo. **Propietario:** calidad de presentación y workers. **Alcance:** M.

**Descripción:** cubrir contenido mínimo/máximo, saltos, datos ausentes, versión de plantilla, PDF corrupto/fallido y recuperación repetida.

**Entradas y dependencias:** T26; plantillas T17/T18.

**Datos, contratos, transacciones y consumidores:** PDFs ficticios en `.tmp`, estados/artefactos aislados y sin datos reales.

**Criterios de aceptación:**
- [ ] Ninguna combinación trunca medicamento/posología/examen/indicación ni inventa datos faltantes.
- [ ] Reintento conserva emisión/número/plantilla y deja un artefacto vigente verificable por huella.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_prescription_rendering tests.test_order_rendering tests.test_document_artifacts -v`.
- [ ] Scripts reales de render/inspección de T16 y `uv build --offline`.
- [ ] Manual: inspeccionar visualmente el conjunto ficticio final y comparar número/contenido/huella tras fallos.

**Archivos previstos:** `tests/test_prescription_rendering.py`, `tests/test_order_rendering.py`, `tests/test_document_artifacts.py`, `test-support/clinical_documents/check.py`.

**Evidencia:** pendiente.

## C09 · Después de T25–T27

- [ ] Rama offline elegida, carreras, aislamiento y recuperación pasan.
- [ ] Todos los PDF ficticios son legibles, completos y sin fuga.
- [ ] El usuario revisa y acepta C09.

## T28 · Generar contratos y actualizar documentación

**Estado:** Todo. **Propietario:** contratos y documentación técnica. **Alcance:** M.

**Descripción:** exportar OpenAPI/esquemas/capacidades/ejemplos de staff/paciente/QR y alinear fuentes con implementación/versiones/límites.

**Entradas y dependencias:** C09 aceptado; app/modelos reales.

**Datos, contratos, transacciones y consumidores:** artefactos con origen/HEAD/huella, datos ficticios y sin edición manual.

**Criterios de aceptación:**
- [ ] Dos generaciones/`--check` y ejemplos de borrador/emisión/paciente/QR/sync son reproducibles.
- [ ] Documentación no afirma validez jurídica, firma física, farmacia/laboratorio, Rust/Hub o producción.

**Verificación:**
- [ ] `uv run --locked python -m scripts.export_contracts` y `uv run --locked python -m scripts.export_contracts --check`.
- [ ] `./.venv/Scripts/python.exe test-support/contracts/check.py` y `git diff --check`.
- [ ] Manual: consumir ejemplos de staff/paciente/verificación y recuperación mediante cliente ASGI real.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/rust-api-guide.md`, artefactos generados por el exportador.

**Evidencia:** pendiente.

## T29 · Ejecutar cierre integral y registrar evidencia

**Estado:** Todo. **Propietario:** calidad y mantenimiento del plan. **Alcance:** M.

**Descripción:** ejecutar suite, probes, migraciones, contratos, PDF y build; revisar diff y registrar resultados/límites en las fuentes de evidencia.

**Entradas y dependencias:** T28; entregable completo.

**Datos, contratos, transacciones y consumidores:** servicios Test/datos ficticios, sin despliegue, commits o cambios en otros repositorios.

**Criterios de aceptación:**
- [ ] Todos los comandos pertinentes pasan y límites jurídicos/externos/operativos quedan explícitos.
- [ ] No quedan artefactos temporales no necesarios, trabajo ajeno alterado o aceptaciones automáticas.

**Verificación:**
- [ ] `uv run --locked python -m unittest discover -s tests -v` y probes `clinical_documents`, `clinical_history`, `clinical_downloads`, `billing`, `access`, `sync`, `downloads`, `events`, `persistence` y `contracts` mediante sus `check.py`.
- [ ] `uv build --offline`, `uv run --locked python -m scripts.export_contracts --check`, scripts de render/inspección y `git diff --check`.
- [ ] Manual: borrador→emisión→PDF→firma impresa ficticia→paciente/QR→sustitución/anulación→recuperación con datos ficticios.

**Archivos previstos:** `tasks/P-20261117-04-clinical-documents/plan.md`, `tasks/P-20261117-04-clinical-documents/todo.md`, `docs/operations/development.md`, `docs/quality.md`.

**Evidencia:** pendiente.

## C10 · Después de T28–T29

- [ ] Suite, probes, migraciones, contratos, PDF y build pasan.
- [ ] El recorrido completo funciona localmente y conserva límites jurídicos/externos.
- [ ] El usuario revisa y acepta C10 antes de cualquier uso real.
