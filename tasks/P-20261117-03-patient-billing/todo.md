# Lista de tareas: P-20261117-03-patient-billing

**Plan:** [plan.md](plan.md). **Actualizado:** 2026-11-17. **Estado del plan:** Approved.

Todas las tareas están Todo. La ejecución requiere C10 aceptado del plan de suscripciones. T01–T04 recogen decisiones del usuario antes del trabajo dependiente; ninguna se presume aquí.

## T01 · Cerrar monedas, precios y vínculos de cargos

**Estado:** Todo. **Propietario:** producto y `billing`. **Alcance:** M.

**Descripción:** resolver monedas/BCV para pacientes, precio base/oferta/estimación, cargos sin cita/atención y ajustes manuales.

**Entradas y dependencias:** suscripciones C10 aceptado; `BI-O01`–`BI-O03`.

**Datos, contratos, transacciones y consumidores:** decisiones documentales; no cambia catálogo, cargos o consumidores todavía.

**Criterios de aceptación:**
- [ ] Moneda, conversión/redondeo, nulo/cero e instantánea de precio tienen una regla explícita.
- [ ] Vínculos permitidos y permiso para ajuste manual están definidos sin cargo automático por cita/atención.

**Verificación:**
- [ ] Revisión de ejemplos ficticios USD/VES, servicio gratuito, sin precio y cargo sin cita.
- [ ] `git diff --check` y enlaces ISO/BCV/PostgreSQL/FHIR pertinentes.
- [ ] Manual: recorrer estimación→cargo emitido→cambio de catálogo sin alterar historia.

**Archivos previstos:** `docs/patient-billing.md`, `docs/decisions.md`, `tasks/P-20261117-03-patient-billing/todo.md`.

**Evidencia:** pendiente.

## T02 · Cerrar reportes, parciales/excedentes y pagos directos

**Estado:** Todo. **Propietario:** producto y operación financiera. **Alcance:** M.

**Descripción:** resolver campos/referencia del reporte, pagos parciales/excedentes/aplicación y alta directa por personal.

**Entradas y dependencias:** T01; `BI-O04`, `BI-O06` y `BI-O07`.

**Datos, contratos, transacciones y consumidores:** reglas documentales, sin procesamiento bancario o pagos reales.

**Criterios de aceptación:**
- [ ] Captura/datos obligatorios y referencia mínima están definidos sin datos bancarios innecesarios.
- [ ] Parcial, excedente, varios cargos y `staff_entry` tienen estados/saldos esperados explícitos.

**Verificación:**
- [ ] Matriz ficticia de dos pagos parciales, excedente, duplicado sospechoso y efectivo directo.
- [ ] `git diff --check` y revisión de consistencia con la especificación aprobada.
- [ ] Manual: calcular saldo después de cada operación y repetición sin doble efecto.

**Archivos previstos:** `docs/patient-billing.md`, `docs/decisions.md`, `docs/quality.md`.

**Evidencia:** pendiente.

## T03 · Cerrar permisos financieros y correcciones

**Estado:** Todo. **Propietario:** producto, `accounts` y seguridad. **Alcance:** M.

**Descripción:** decidir acciones/valores iniciales de asistentes y reglas para cargos con pagos, anulaciones y constancia de reembolso.

**Entradas y dependencias:** T02; `BI-O05` y `BI-O08`.

**Datos, contratos, transacciones y consumidores:** diseño de permisos/corrección; sin acceso clínico heredado ni reembolso real.

**Criterios de aceptación:**
- [ ] Lectura, cargos, revisión, corrección y analítica tienen propietario/defaults explícitos.
- [ ] Anulación/corrección conserva historia/saldo y no declara devolución de fondos.

**Verificación:**
- [ ] Matriz owner/asistente/paciente/operador para cada acción financiera y clínica negativa.
- [ ] `git diff --check` y enlaces a D14/especificación de autorización.
- [ ] Manual: revisar asistente con lectura solamente y revisor sin permiso clínico.

**Archivos previstos:** `docs/patient-billing.md`, `docs/access-design.md`, `docs/decisions.md`.

**Evidencia:** pendiente.

## C01 · Después de T01–T03

- [ ] `BI-O01`–`BI-O08` están resueltos y registrados.
- [ ] Ejemplos de precios, reportes, saldos, permisos y correcciones son coherentes.
- [ ] El usuario revisa y acepta C01.

## T04 · Cerrar concesión, offline, archivos y panel

**Estado:** Todo. **Propietario:** producto, Hub/API y operación. **Alcance:** M.

**Descripción:** resolver vigencia/revocación del enlace, cancelar/reprogramar cita, trabajo offline, límites/retención de archivos e indicadores iniciales.

**Entradas y dependencias:** C01 aceptado; `BI-O09`–`BI-O12`.

**Datos, contratos, transacciones y consumidores:** políticas documentales; no implementa interfaz Hub completa ni cuenta general de paciente.

**Criterios de aceptación:**
- [ ] Concesión limitada por cita/cargo/acción y efectos de cambio de cita están cerrados.
- [ ] Offline, capturas/comprobantes y fechas/monedas del primer panel tienen reglas explícitas.

**Verificación:**
- [ ] Matriz enlace válido/vencido/revocado, cita reprogramada/cancelada y equipo offline.
- [ ] `git diff --check` y referencias OWASP/retención revisadas.
- [ ] Manual: seguir paciente que reporta, pierde enlace y personal que revisa sin filtrar otros objetos.

**Archivos previstos:** `docs/patient-billing.md`, `docs/access-design.md`, `docs/quality.md`, `docs/decisions.md`.

**Evidencia:** pendiente.

## T05 · Diseñar físicamente precios, cargos, pagos y saldos

**Estado:** Todo. **Propietario:** `billing/repository` y esquema físico. **Alcance:** M.

**Descripción:** añadir a la fuente única precios base/oferta, cargos/historias, pagos/aplicaciones y restricciones de saldo/moneda.

**Entradas y dependencias:** T04; decisiones T01/T02.

**Datos, contratos, transacciones y consumidores:** diseño sin migración; decimal, FK compuestas, versiones e instantáneas.

**Criterios de aceptación:**
- [ ] Un reporte aprobado→un pago y pagos vigentes≤cargo salvo excedente decidido tienen protección física.
- [ ] Cuenta/paciente/cita/atención/servicio y precio histórico tienen claves/restricciones/índices propuestos.

**Verificación:**
- [ ] Revisión cruzada de cada regla conceptual con tipo/FK/CHECK/UQ/índice.
- [ ] `git diff --check` y fuentes PostgreSQL 18 pertinentes.
- [ ] Manual: evaluar dos aprobaciones y cambio/cancelación de cargo contra el diseño.

**Archivos previstos:** `docs/database-schema.md`, `docs/patient-billing.md`.

**Evidencia:** pendiente.

## T06 · Diseñar físicamente reportes, evidencias y concesiones

**Estado:** Todo. **Propietario:** `billing/repository` y seguridad de acceso. **Alcance:** M.

**Descripción:** diseñar declaración/verificación, metadatos de captura/comprobante y concesiones privadas de paciente con vigencia/revocación.

**Entradas y dependencias:** T05; T03/T04.

**Datos, contratos, transacciones y consumidores:** bytes fuera de DB/sync, secretos con huella si aplica y proyecciones mínimas.

**Criterios de aceptación:**
- [ ] Declarados/verificados/historia no se reescriben y objetos/concesiones no cruzan cuentas.
- [ ] Captura/comprobante y secreto de enlace no se exponen en auditoría/logs/journal.

**Verificación:**
- [ ] Revisión de ciclo reporte/concesión y todos sus estados contra restricciones.
- [ ] `git diff --check` y enlaces OWASP/PostgreSQL.
- [ ] Manual: evaluar reutilización, sustitución y revocación de enlace sin acceso por UUID.

**Archivos previstos:** `docs/database-schema.md`, `docs/architecture.md`, `docs/access-design.md`.

**Evidencia:** pendiente.

## C02 · Después de T04–T06

- [ ] `BI-O09`–`BI-O12` están resueltos y el diseño cubre concesión/archivos/analítica.
- [ ] Las restricciones físicas protegen saldo, efecto único, aislamiento e historia.
- [ ] El usuario revisa y acepta C02.

## T07 · Diseñar contratos del personal y paciente

**Estado:** Todo. **Propietario:** `billing`, contratos y acceso. **Alcance:** M.

**Descripción:** fijar rutas/operaciones/modelos para precios, cargos, reportes, revisión, pagos, correcciones, comprobantes y concesiones.

**Entradas y dependencias:** C02 aceptado; catálogo de autorización.

**Datos, contratos, transacciones y consumidores:** camelCase, page/shows, operaciones idempotentes, errores seguros y límites de archivos.

**Criterios de aceptación:**
- [ ] Cada acción tiene actor/objeto/versión/transacción/resultado y permiso explícito.
- [ ] Paciente recibe solo proyección mínima y no puede aprobar/corregir ni ver otros cargos.

**Verificación:**
- [ ] Cobertura de todos los casos §18 de la especificación sin rutas duplicadas.
- [ ] `git diff --check` y validación de enlaces/anclas.
- [ ] Manual: recorrer respuesta perdida en reporte/aprobación y descarga con enlace revocado.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/contracts.md`, `docs/patient-billing.md`.

**Evidencia:** pendiente.

## T08 · Diseñar sync, analítica e integración entre componentes

**Estado:** Todo. **Propietario:** arquitectura, `sync` y `analytics`. **Alcance:** M.

**Descripción:** fijar propietario de concesiones, audiencia financiera, versiones/época, eventos mínimos y consultas operativas/ETL.

**Entradas y dependencias:** T07; T04/T06.

**Datos, contratos, transacciones y consumidores:** capturas/deltas/SSE sin bytes, analítica pesada en almacén separado cuando aplique.

**Criterios de aceptación:**
- [ ] Entidad→audiencia→permiso y cambios de alcance/recuperación están completos.
- [ ] Servicios/patients/appointments/encounters interactúan por casos/tipos sin repositorios ajenos.

**Verificación:**
- [ ] Matriz de proyección para owner/asistente/paciente y permiso revocado.
- [ ] `git diff --check` y revisión de dependencias arquitectónicas.
- [ ] Manual: seguir pago aprobado desde commit hasta delta/aviso/indicador sin evidencia.

**Archivos previstos:** `docs/architecture.md`, `docs/api-v1.md`, `docs/quality.md`.

**Evidencia:** pendiente.

## T09 · Implementar dominio de dinero, precios y saldos

**Estado:** Todo. **Propietario:** `billing/domain`. **Alcance:** M.

**Descripción:** implementar valores monetarios, conversión si se aprobó, resolución base/oferta y cálculo puro de pagos/saldos.

**Entradas y dependencias:** C02 aceptado; T01/T02 y adaptadores T07.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/red, `Decimal`, moneda/tasa/redondeo explícitos.

**Criterios de aceptación:**
- [ ] Nulo/cero, USD/VES y precios base/oferta producen resultados exactos.
- [ ] Parciales/pagado/excedente/anulado calculan saldo sin mezclar monedas ni revalorizar.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_money -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [ ] Manual: comparar ejemplos ficticios de T01/T02 con cada resultado y total.

**Archivos previstos:** `src/api/billing/domain/money.py`, `src/api/billing/domain/pricing.py`, `tests/test_billing_money.py`.

**Evidencia:** pendiente.

## C03 · Después de T07–T09

- [ ] Contratos e integración cubren actores, sync y analítica.
- [ ] Dinero, precios y saldos pasan pruebas de dominio.
- [ ] El usuario revisa y acepta C03.

## T10 · Implementar dominio de cargos, reportes y pagos

**Estado:** Todo. **Propietario:** `billing/domain`. **Alcance:** M.

**Descripción:** implementar modelos/transiciones de borrador/cargo abierto/cancelado, reporte/revisión, pago y concesión.

**Entradas y dependencias:** C03 aceptado; T02–T04/T07.

**Datos, contratos, transacciones y consumidores:** esquemas estrictos base, contenido financiero sin bytes ni SQL.

**Criterios de aceptación:**
- [ ] Borrador no es visible al paciente y solo personal con acción puede aprobar/corregir.
- [ ] Rechazo/nueva presentación/anulación y estados de concesión conservan historia.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_domain -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure tests.test_billing_domain -v`.
- [ ] Manual: validar transiciones permitidas/prohibidas y datos declarados frente a verificados.

**Archivos previstos:** `src/api/billing/domain/charges.py`, `src/api/billing/domain/payments.py`, `tests/test_billing_domain.py`.

**Evidencia:** pendiente.

## T11 · Implementar persistencia de precios y cargos

**Estado:** Todo. **Propietario:** `billing/repository`, `services` y migraciones. **Alcance:** M.

**Descripción:** crear migración/modelos/DAOs para precios base/oferta, cargos e historias con relaciones e instantáneas.

**Entradas y dependencias:** T10; T05.

**Datos, contratos, transacciones y consumidores:** DAOs derivados commit=False, FK/CHECK/UQ, privilegios mínimos y sin cambio de citas.

**Criterios de aceptación:**
- [ ] Migración up/down/reapply protege moneda, importes, vínculos y versiones.
- [ ] Cambiar precio actual no reescribe cargo y rol operativo no ejecuta DDL.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_persistence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: probar cruce de cuenta/paciente/cita y modificación de instantánea con SQL.

**Archivos previstos:** `migrations/versions/<revisión>_billing_charges.py`, `src/api/billing/repository/models.py`, `src/api/billing/repository/dao.py`, `src/api/services/repository/models.py`, `tests/test_billing_persistence.py`.

**Evidencia:** pendiente.

## T12 · Implementar persistencia de reportes, pagos y concesiones

**Estado:** Todo. **Propietario:** `billing/repository` y migraciones. **Alcance:** M.

**Descripción:** añadir reportes/revisiones/evidencias, pagos/aplicaciones, comprobantes y concesiones con restricciones de efecto/saldo.

**Entradas y dependencias:** T11; T06.

**Datos, contratos, transacciones y consumidores:** misma sesión commit=False; sin bytes/secretos en journal y referencias por cuenta.

**Criterios de aceptación:**
- [ ] Una aprobación genera como máximo un pago y carreras SQL no exceden el cargo.
- [ ] Concesión/evidencia/comprobante no cruza cuenta y anulaciones conservan historia.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_persistence tests.test_billing_domain -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: intentar doble pago de origen, exceso concurrente y acceso por concesión ajena.

**Archivos previstos:** `migrations/versions/<revisión>_billing_payments.py`, `src/api/billing/repository/models.py`, `src/api/billing/repository/dao.py`, `tests/test_billing_persistence.py`.

**Evidencia:** pendiente.

## C04 · Después de T10–T12

- [ ] Dominio y persistencia pasan pruebas de integridad/privilegios.
- [ ] Instantáneas, saldo, efecto único y concesiones están protegidos.
- [ ] El usuario revisa y acepta C04.

## T13 · Integrar precios base/oferta con servicios

**Estado:** Todo. **Propietario:** `services` y `billing`. **Alcance:** M.

**Descripción:** añadir precios a contratos/casos de catálogo/oferta y resolver precio efectivo mediante caso público para cargos.

**Entradas y dependencias:** C04 aceptado; T01/T09.

**Datos, contratos, transacciones y consumidores:** propiedad profesional/oferta, operaciones existentes versionadas y proyecciones autorizadas.

**Criterios de aceptación:**
- [ ] Solo profesional/oferta autorizada modifica precios y miembros reciben lo permitido.
- [ ] Base/override/nulo/cero y cambios de versión se resuelven sin alterar citas/cargos anteriores.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_services tests.test_billing_pricing -v`.
- [ ] `./.venv/Scripts/python.exe test-support/services/check.py`.
- [ ] Manual: editar precio, resolverlo en dos cuentas y comprobar instantánea histórica.

**Archivos previstos:** `src/api/services/domain/services.py`, `src/api/services/domain/offers.py`, `src/api/services/application/services_cases.py`, `src/api/services/application/offers_cases.py`, `tests/test_billing_pricing.py`.

**Evidencia:** pendiente.

## T14 · Implementar cargos por el personal

**Estado:** Todo. **Propietario:** `billing` y `sync`. **Alcance:** M.

**Descripción:** implementar crear/editar borrador, emitir, consultar/listar y cancelar cargo con relaciones e instantáneas.

**Entradas y dependencias:** T13; T03/T07.

**Datos, contratos, transacciones y consumidores:** efecto/historia/auditoría/recibo/grupo en una transacción; sin cargo automático.

**Criterios de aceptación:**
- [ ] Borrador editable/emitido inmutable según regla y cancelación conserva historia/pagos.
- [ ] Objetos cruzados, ajuste no autorizado y cambios de precio concurrentes se rechazan coherentemente.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_charges tests.test_operations -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: crear desde cita y atención sin cita, emitir/cancelar y revisar versión/historia/auditoría.

**Archivos previstos:** `src/api/billing/application/charge_cases.py`, `src/api/billing/infrastructure/charges_api.py`, `tests/test_billing_charges.py`.

**Evidencia:** pendiente.

## T15 · Reutilizar almacenamiento privado para capturas

**Estado:** Todo. **Propietario:** `core/services`, `subscriptions` y `billing`. **Alcance:** M.

**Descripción:** extraer solo el soporte común demostrado del plan de suscripciones y conectar capturas de billing sin duplicar adaptador ni cambiar su comportamiento.

**Entradas y dependencias:** T14; storage de suscripciones C06 y T04.

**Datos, contratos, transacciones y consumidores:** bytes fuera de DB/sync/webroot; validación/límites propios y referencias autorizadas.

**Criterios de aceptación:**
- [ ] Ambos componentes usan soporte común sin imports de repositorios ni regresión de suscripciones.
- [ ] Tipo/tamaño/nombre, descarga reautorizada y logs cumplen seguridad.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_evidence tests.test_subscription_evidence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/subscriptions/check.py` y `uv build --offline`.
- [ ] Manual: cargar evidencia en ambos dominios y comprobar aislamiento cruzado/ausencia en logs.

**Archivos previstos:** `src/core/services/private_evidence.py`, `src/api/subscriptions/application/evidence_cases.py`, `src/api/billing/application/evidence_cases.py`, `tests/test_billing_evidence.py`, `tests/test_subscription_evidence.py`.

**Evidencia:** pendiente.

## C05 · Después de T13–T15

- [ ] Precios/cargos y almacenamiento común pasan sin regresión de suscripciones.
- [ ] Borradores/ajustes/archivos respetan permisos e historia.
- [ ] El usuario revisa y acepta C05.

## T16 · Implementar concesión y proyección de cargo para paciente

**Estado:** Todo. **Propietario:** acceso limitado API y `billing`. **Alcance:** M.

**Descripción:** implementar emisión/validación/revocación de concesión según T04 y lectura mínima de cargo/saldo relacionado con cita.

**Entradas y dependencias:** C05 aceptado; D16 y contratos T07.

**Datos, contratos, transacciones y consumidores:** concesión por objeto/acción, huella de secreto si aplica, auditoría y sin cuenta general.

**Criterios de aceptación:**
- [ ] Enlace válido lee solo cargo permitido; vencido/revocado/ajeno no revela existencia.
- [ ] Cancelar/reprogramar cita sigue T04 y no abre otros cargos/historia clínica.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_patient_access -v`.
- [ ] `./.venv/Scripts/python.exe test-support/access/check.py` y pruebas ASGI del módulo.
- [ ] Manual: usar enlace con distintos UUID/acciones y revocar antes de lectura/descarga.

**Archivos previstos:** módulos de concesión definidos en T08, `src/api/billing/application/patient_cases.py`, `src/api/billing/infrastructure/patient_api.py`, `tests/test_billing_patient_access.py`, máximo cinco archivos.

**Evidencia:** pendiente.

## T17 · Implementar reporte del paciente con captura

**Estado:** Todo. **Propietario:** `billing` y acceso limitado. **Alcance:** M.

**Descripción:** implementar presentación online, listas/detalle/resultado propios, idempotencia y probe HTTP real con captura obligatoria.

**Entradas y dependencias:** T16; T02/T07.

**Datos, contratos, transacciones y consumidores:** reporte/metadatos/recibo/auditoría atómicos, bytes fuera de transacción y saldo sin cambios.

**Criterios de aceptación:**
- [ ] Presentar crea `pending` sin pago y respuesta perdida recupera mismo reporte/captura.
- [ ] Paciente no aprueba ni accede a reportes/cargos fuera de concesión.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_reports tests.test_billing_patient_access -v`.
- [ ] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [ ] Manual: cortar respuesta tras commit, reintentar y verificar un solo reporte y saldo original.

**Archivos previstos:** `src/api/billing/application/report_cases.py`, `src/api/billing/infrastructure/reports_api.py`, `tests/test_billing_reports.py`, `test-support/billing/check.py`.

**Evidencia:** pendiente.

## T18 · Implementar bandeja de revisión del personal

**Estado:** Todo. **Propietario:** `billing` y seguridad financiera. **Alcance:** M.

**Descripción:** implementar pendientes/historia, detalle, evidencia y datos mínimos de paciente/cargo para asistente revisor.

**Entradas y dependencias:** T17; permisos T03.

**Datos, contratos, transacciones y consumidores:** autorización antes de total/página, lecturas auditadas y sin contenido clínico.

**Criterios de aceptación:**
- [ ] Solo acción de revisión abre bandeja/evidencia y no concede notas/diagnósticos.
- [ ] Totales/páginas/descarga no filtran otras cuentas ni observaciones internas al paciente.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_review tests.test_clinical_permissions -v`.
- [ ] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [ ] Manual: comparar asistente lector/revisor/sin permiso y objeto de otra cuenta.

**Archivos previstos:** `src/api/billing/application/review_cases.py`, `src/api/billing/infrastructure/reviews_api.py`, `tests/test_billing_review.py`.

**Evidencia:** pendiente.

## C06 · Después de T16–T18

- [ ] Paciente reporta sin cambiar saldo y personal revisa con alcance mínimo.
- [ ] Enlaces, evidencias, idempotencia y aislamiento pasan.
- [ ] El usuario revisa y acepta C06.

## T19 · Implementar aprobación atómica y saldo

**Estado:** Todo. **Propietario:** `billing`, `sync` y `audit`. **Alcance:** M.

**Descripción:** implementar decisión de revisor, datos verificados, pago/aplicación y saldo coordinado con una única operación efectiva.

**Entradas y dependencias:** C06 aceptado; T02/T09/T12.

**Datos, contratos, transacciones y consumidores:** reporte/pago/cargo/historia/auditoría/recibo/grupo en una transacción; sin red dentro.

**Criterios de aceptación:**
- [ ] Aprobación crea un pago y saldo correcto una vez, con revisor real e instantánea de moneda/tasa.
- [ ] Dos revisores/parciales/respuesta perdida no duplican pago ni exceden cargo.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_approval tests.test_billing_money -v`.
- [ ] `./.venv/Scripts/python.exe test-support/billing/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [ ] Manual: disputar aprobación y último saldo, revisar SQL/recuperación tras corte de respuesta.

**Archivos previstos:** `src/api/billing/application/review_cases.py`, `src/api/sync/application/operations_cases.py`, `tests/test_billing_approval.py`, `test-support/billing/check.py`.

**Evidencia:** pendiente.

## T20 · Implementar rechazo y nueva presentación

**Estado:** Todo. **Propietario:** `billing`. **Alcance:** M.

**Descripción:** añadir rechazo con motivo seguro y nueva presentación relacionada sin reabrir ni reescribir el original.

**Entradas y dependencias:** T19; T02/T10.

**Datos, contratos, transacciones y consumidores:** cargo/pagos anteriores sin cambio, revisión/recibo/auditoría atómicos.

**Criterios de aceptación:**
- [ ] Rechazo no crea pago ni cambia saldo/cita y conserva evidencia/motivo.
- [ ] Nueva presentación mantiene cadena e historia y puede aprobarse solo una vez.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_reports tests.test_billing_approval -v`.
- [ ] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [ ] Manual: rechazar, corregir, reenviar y aprobar verificando saldo e historia completa.

**Archivos previstos:** `src/api/billing/application/review_cases.py`, `src/api/billing/application/report_cases.py`, `tests/test_billing_reports.py`.

**Evidencia:** pendiente.

## T21 · Implementar pagos directos del personal

**Estado:** Todo. **Propietario:** `billing`. **Alcance:** M.

**Descripción:** implementar el alta `staff_entry` aprobada en T02 con origen/actor/evidencia propios, sin simular reporte del paciente.

**Entradas y dependencias:** T20; decisión T02. Si se excluye, registrar exclusión y verificar rechazo del contrato sin crear recorrido alternativo.

**Datos, contratos, transacciones y consumidores:** pago/aplicación/historia/auditoría/recibo coordinados; online/offline según T04.

**Criterios de aceptación:**
- [ ] Solo permiso de alta directa registra pago y respeta moneda/saldo/efecto único.
- [ ] Origen y actor diferencian claramente staff_entry de patient_report en lecturas/analítica.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_direct_payments -v` o rechazo contractual si se excluyó.
- [ ] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [ ] Manual: registrar efectivo permitido y comparar con pago de paciente en saldo/historia.

**Archivos previstos:** `src/api/billing/application/direct_payment_cases.py`, `src/api/billing/infrastructure/payments_api.py`, `tests/test_billing_direct_payments.py`.

**Evidencia:** pendiente.

## C07 · Después de T19–T21

- [ ] Aprobación/rechazo/alta directa conservan efecto único y saldo.
- [ ] Carreras y orígenes de pago quedan demostrados.
- [ ] El usuario revisa y acepta C07.

## T22 · Implementar anulación y correcciones financieras

**Estado:** Todo. **Propietario:** `billing`. **Alcance:** M.

**Descripción:** implementar anulación/corrección de pagos y cargos según T03 sin borrar ni declarar reembolso real.

**Entradas y dependencias:** C07 aceptado; `BI-O08` resuelto.

**Datos, contratos, transacciones y consumidores:** nuevas versiones/eventos, saldo recalculado, auditoría/recibo/grupo atómicos.

**Criterios de aceptación:**
- [ ] Pago anulado deja de sumar al vigente y cargo con pagos sigue la política aprobada.
- [ ] Historia/comprobante/reporte permanecen y solo acción de corrección autorizada cambia estado.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_corrections tests.test_billing_money -v`.
- [ ] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [ ] Manual: anular pago total/parcial y revisar saldo, historia y ausencia de afirmación de devolución.

**Archivos previstos:** `src/api/billing/application/correction_cases.py`, `tests/test_billing_corrections.py`, `test-support/billing/check.py`.

**Evidencia:** pendiente.

## T23 · Implementar comprobante administrativo no fiscal

**Estado:** Todo. **Propietario:** `billing`, `core/services` y documentación técnica. **Alcance:** M.

**Descripción:** seleccionar formato/biblioteca con fuentes oficiales de versión y generar/consultar comprobante privado con instantánea y estado.

**Entradas y dependencias:** T22; manifiesto/lockfile y guía docs-first.

**Datos, contratos, transacciones y consumidores:** artefacto fuera de journal, trabajo durable tras commit si aplica y descarga reautorizada.

**Criterios de aceptación:**
- [ ] Elección/versión/fuente oficial queda registrada sin dependencia injustificada.
- [ ] Comprobante identifica pago/cargo/importe/fecha/estado, no factura fiscal ni reembolso, y no cambia historia.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_receipts -v`.
- [ ] `uv build --offline` y revisión de lockfile/artefactos si cambia una dependencia justificada.
- [ ] Manual: generar/descargar con staff/paciente autorizado y ajeno; inspeccionar archivo ficticio y logs.

**Archivos previstos:** `src/core/services/billing_receipts.py`, `src/api/billing/application/receipt_cases.py`, `src/api/billing/infrastructure/receipts_api.py`, `tests/test_billing_receipts.py`, `docs/operations/development.md`.

**Evidencia:** pendiente.

## T24 · Implementar audiencia financiera en snapshot/delta/SSE

**Estado:** Todo. **Propietario:** `sync` y `billing`. **Alcance:** M.

**Descripción:** publicar cargos/pagos/saldos/comprobante por referencia según permisos, con filtrado/época/recuperación y avisos mínimos.

**Entradas y dependencias:** T23; T08.

**Datos, contratos, transacciones y consumidores:** proyecciones validadas, grupos completos, cursores/streams y bytes excluidos.

**Criterios de aceptación:**
- [ ] Solo audiencia financiera autorizada recibe estados y grupos invisibles avanzan sin cuerpo.
- [ ] Capturas/comprobantes no viajan en journal y aviso perdido se recupera por captura/delta.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_downloads tests.test_events tests.test_billing_sync -v`.
- [ ] `./.venv/Scripts/python.exe test-support/downloads/check.py` y `./.venv/Scripts/python.exe test-support/events/check.py`.
- [ ] Manual: aprobar con stream caído y recuperar pago/saldo sin bytes ni otras secciones.

**Archivos previstos:** `src/api/sync/application/snapshot_cases.py`, `src/api/sync/application/download_cases.py`, `src/api/sync/application/events_cases.py`, `src/api/sync/domain/downloads.py`, `tests/test_billing_sync.py`.

**Evidencia:** pendiente.

## C08 · Después de T22–T24

- [ ] Correcciones, comprobantes y sync pasan con historia/privacidad intactas.
- [ ] La recuperación no duplica pagos ni entrega archivos.
- [ ] El usuario revisa y acepta C08.

## T25 · Implementar preparación offline y reautorización

**Estado:** Todo. **Propietario:** `billing`, `sync` y consumidores API. **Alcance:** M.

**Descripción:** habilitar solo los borradores/pagos directos offline aprobados en T04, con intenciones conservadas y validación remota actual.

**Entradas y dependencias:** C08 aceptado; `BI-O10` resuelto.

**Datos, contratos, transacciones y consumidores:** UUID/operación local, proyección no autoritativa y aceptación con permiso/versión/saldo actuales.

**Criterios de aceptación:**
- [ ] Reloj/caché local no concede permiso ni fija saldo; reporte/aprobación/corrección permanecen online.
- [ ] Rechazo remoto conserva intención local y respuesta perdida recupera el mismo efecto.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_offline tests.test_billing_sync -v`.
- [ ] `./.venv/Scripts/python.exe test-support/billing/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [ ] Manual: preparar borrador sin red, cambiar permiso/precio y sincronizar sin efecto indebido o pérdida local.

**Archivos previstos:** `src/api/billing/application/offline_cases.py`, `tests/test_billing_offline.py`, `test-support/billing/check.py`.

**Evidencia:** pendiente.

## T26 · Implementar analítica de facturación

**Estado:** Todo. **Propietario:** `billing` y `analytics`. **Alcance:** M.

**Descripción:** implementar indicadores T04 con fecha/moneda explícitas y dimensiones autorizadas sin consultas ilimitadas en operación.

**Entradas y dependencias:** T25; `BI-O12` resuelto.

**Datos, contratos, transacciones y consumidores:** proyecciones acotadas/ETL separado según volumen; sin evidencias o contenido clínico.

**Criterios de aceptación:**
- [ ] Pendiente/anulado no suma a cobrado/vigente y cargos/pagos/saldos usan la fecha elegida.
- [ ] Totales por moneda no revalorizan historia y filtros de profesional/servicio/paciente respetan permisos.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_billing_metrics -v`.
- [ ] `uv build --offline` y consultas ficticias acotadas incluidas en pruebas.
- [ ] Manual: contrastar panel con SQL de cargos/pagos/anulaciones en dos monedas y fechas distintas.

**Archivos previstos:** `src/api/billing/application/metrics_cases.py`, `src/api/billing/infrastructure/metrics_api.py`, `tests/test_billing_metrics.py`.

**Evidencia:** pendiente.

## T27 · Completar seguridad, concurrencia y recuperación

**Estado:** Todo. **Propietario:** calidad de `billing`. **Alcance:** M.

**Descripción:** ampliar probes para IDs cruzados, permisos clínicos/financieros, concesiones, doble revisor, último saldo, archivos y caídas.

**Entradas y dependencias:** T26; flujo completo.

**Datos, contratos, transacciones y consumidores:** PostgreSQL/Keycloak/storage Test aislados y datos ficticios; limpieza al terminar.

**Criterios de aceptación:**
- [ ] Ninguna carrera duplica/excede pagos ni revocación antigua permite efecto posterior.
- [ ] Logs/auditoría/sync/errores/analítica no filtran capturas, secretos, clínicas o datos bancarios innecesarios.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe test-support/billing/check.py` y `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] `uv run --locked python -m unittest discover -s tests -v`.
- [ ] Manual: revisar bloqueos, SQL final, archivos y evidencia para cada fallo inyectado.

**Archivos previstos:** `test-support/billing/check.py`, `test-support/persistence/check.py`, `tests/test_billing_patient_access.py`.

**Evidencia:** pendiente.

## C09 · Después de T25–T27

- [ ] Offline, analítica, seguridad y carreras pasan localmente.
- [ ] No hay mezcla de monedas/fechas, fuga o pérdida de intenciones.
- [ ] El usuario revisa y acepta C09.

## T28 · Generar contratos y actualizar documentación

**Estado:** Todo. **Propietario:** contratos y documentación técnica. **Alcance:** M.

**Descripción:** exportar OpenAPI/esquemas/capacidades/ejemplos de staff/paciente y alinear fuentes con implementación/versiones/límites.

**Entradas y dependencias:** C09 aceptado; app/modelos reales.

**Datos, contratos, transacciones y consumidores:** artefactos con origen/HEAD/huella, datos ficticios y sin edición manual.

**Criterios de aceptación:**
- [ ] Dos generaciones/`--check` y ejemplos de cargo/reporte/pago/concesión/sync son reproducibles.
- [ ] Documentación no afirma banco, factura fiscal, Rust/Hub, datos reales o producción.

**Verificación:**
- [ ] `uv run --locked python -m scripts.export_contracts` y `uv run --locked python -m scripts.export_contracts --check`.
- [ ] `./.venv/Scripts/python.exe test-support/contracts/check.py` y `git diff --check`.
- [ ] Manual: consumir ejemplos de staff/paciente y recuperación mediante cliente ASGI real.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/rust-api-guide.md`, artefactos generados por el exportador.

**Evidencia:** pendiente.

## T29 · Ejecutar cierre integral y registrar evidencia

**Estado:** Todo. **Propietario:** calidad y mantenimiento del plan. **Alcance:** M.

**Descripción:** ejecutar suite, probes, migraciones, contratos y build; revisar diff y registrar resultados/límites en las fuentes de evidencia.

**Entradas y dependencias:** T28; entregable completo.

**Datos, contratos, transacciones y consumidores:** servicios Test/datos ficticios, sin despliegue, commits o cambios en otros repositorios.

**Criterios de aceptación:**
- [ ] Todos los comandos pertinentes pasan y límites externos/operativos quedan explícitos.
- [ ] No quedan artefactos temporales no necesarios, trabajo ajeno alterado o aceptaciones automáticas.

**Verificación:**
- [ ] `uv run --locked python -m unittest discover -s tests -v` y probes `billing`, `subscriptions`, `services`, `access`, `sync`, `downloads`, `events`, `persistence` y `contracts` mediante sus `check.py`.
- [ ] `uv build --offline`, `uv run --locked python -m scripts.export_contracts --check` y `git diff --check`.
- [ ] Manual: precio→cargo→enlace→captura→reporte→aprobación→pago→comprobante→sync→analítica con datos ficticios.

**Archivos previstos:** `tasks/P-20261117-03-patient-billing/plan.md`, `tasks/P-20261117-03-patient-billing/todo.md`, `docs/operations/development.md`, `docs/quality.md`.

**Evidencia:** pendiente.

## C10 · Después de T28–T29

- [ ] Suite, probes, migraciones, contratos y build pasan.
- [ ] El recorrido completo funciona localmente y conserva límites externos.
- [ ] El usuario revisa y acepta C10 antes de reutilizar concesiones en documentos clínicos.
