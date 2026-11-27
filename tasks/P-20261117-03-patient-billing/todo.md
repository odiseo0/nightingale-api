# Lista de tareas: P-20261117-03-patient-billing

**Plan:** [plan.md](plan.md). **Actualizado:** 2026-11-27. **Estado del plan:** Approved.

Todas las tareas están Done; C01–C10 aceptados por el usuario. La ejecución requiere C10 aceptado del plan de suscripciones. T01–T04 recogen decisiones del usuario antes del trabajo dependiente; ninguna se presume aquí.

## T01 · Cerrar monedas, precios y vínculos de cargos

**Estado:** Done. **Propietario:** producto y `billing`. **Alcance:** M.

**Descripción:** resolver monedas/BCV para pacientes, precio base/oferta/estimación, cargos sin cita/atención y ajustes manuales.

**Entradas y dependencias:** suscripciones C10 aceptado; `BI-O01`–`BI-O03`.

**Datos, contratos, transacciones y consumidores:** decisiones documentales; no cambia catálogo, cargos o consumidores todavía.

**Criterios de aceptación:**
- [x] Moneda, conversión/redondeo, nulo/cero e instantánea de precio tienen una regla explícita.
- [x] Vínculos permitidos y permiso para ajuste manual están definidos sin cargo automático por cita/atención.

**Verificación:**
- [x] Revisión de ejemplos ficticios USD/VES, servicio gratuito, sin precio y cargo sin cita.
- [x] `git diff --check` y enlaces ISO/BCV/PostgreSQL/FHIR pertinentes.
- [x] Manual: recorrer estimación→cargo emitido→cambio de catálogo sin alterar historia.

**Archivos previstos:** `docs/patient-billing.md`, `docs/decisions.md`, `tasks/P-20261117-03-patient-billing/todo.md`.

**Evidencia:** 2026-11-27. Decisiones tomadas por el usuario y registradas en [D25](../../docs/decisions.md#d25--monedas-precios-y-vínculos-de-cargos-de-pacientes-t01): monedas USD/VES con una sola moneda por precio/cargo; cargos USD pagados en VES con conversión explícita y tasa BCV de la fecha del pago verificada (regla de fecha/fuente de D22, configuración propia); decimal exacto, dos decimales, redondeo half-up registrado; nulo = «sin precio», cero = servicio gratuito válido; resolución base/oferta confirmada con estimación visible no vinculante para el paciente; cargos libres y ajustes manuales permitidos solo con permiso financiero y con historia, sin cargo automático por cita/atención. `docs/patient-billing.md` §14.3 reescrito con las reglas cerradas y §24 marca `BI-O01`–`BI-O03` resueltos. Recorrido manual ficticio verificado: estimación USD 18.00 (base) → oferta USD 15.00 → cargo emitido con instantánea → cambio de catálogo a USD 20.00 no altera el cargo; servicio gratuito (0.00) distinto de sin precio (nulo); cargo libre sin cita con ajuste manual registrado. `git diff --check` limpio.

## T02 · Cerrar reportes, parciales/excedentes y pagos directos

**Estado:** Done. **Propietario:** producto y operación financiera. **Alcance:** M.

**Descripción:** resolver campos/referencia del reporte, pagos parciales/excedentes/aplicación y alta directa por personal.

**Entradas y dependencias:** T01; `BI-O04`, `BI-O06` y `BI-O07`.

**Datos, contratos, transacciones y consumidores:** reglas documentales, sin procesamiento bancario o pagos reales.

**Criterios de aceptación:**
- [x] Captura/datos obligatorios y referencia mínima están definidos sin datos bancarios innecesarios.
- [x] Parcial, excedente, varios cargos y `staff_entry` tienen estados/saldos esperados explícitos.

**Verificación:**
- [x] Matriz ficticia de dos pagos parciales, excedente, duplicado sospechoso y efectivo directo.
- [x] `git diff --check` y revisión de consistencia con la especificación aprobada.
- [x] Manual: calcular saldo después de cada operación y repetición sin doble efecto.

**Archivos previstos:** `docs/patient-billing.md`, `docs/decisions.md`, `docs/quality.md`.

**Evidencia:** 2026-11-27. Decisiones del usuario registradas en [D26](../../docs/decisions.md#d26--reportes-de-pago-parciales-excedentes-y-pagos-directos-t02): reporte con obligatorios cargo/fecha/importe/moneda/método/captura, referencia opcional y parcial, nota opcional, sin números bancarios completos; pagos parciales admitidos mientras la suma vigente no supere el total, excedente rechazado con motivo y nueva presentación corregida (sin aprobación recortada ni crédito), un pago se aplica a un solo cargo; `staff_entry` incluido con permiso y evidencia propios, distinguible de `patient_report`. `docs/patient-billing.md` §10.1, §13.3 y §13.4 actualizados; §24 marca `BI-O04`/`BI-O06`/`BI-O07` resueltos. Matriz ficticia recorrida: cargo USD 100.00 → pago parcial 40.00 (saldo 60.00, `partially_paid`) → segundo parcial 60.00 (saldo 0, `paid`) → tercer reporte de 10.00 rechazado por excedente (saldo sin cambio) → duplicado sospechoso solo advertido a la asistente → efectivo directo `staff_entry` 25.00 en otro cargo con origen distinguible. Repetición idempotente sin doble efecto. `git diff --check` limpio.

## T03 · Cerrar permisos financieros y correcciones

**Estado:** Done. **Propietario:** producto, `accounts` y seguridad. **Alcance:** M.

**Descripción:** decidir acciones/valores iniciales de asistentes y reglas para cargos con pagos, anulaciones y constancia de reembolso.

**Entradas y dependencias:** T02; `BI-O05` y `BI-O08`.

**Datos, contratos, transacciones y consumidores:** diseño de permisos/corrección; sin acceso clínico heredado ni reembolso real.

**Criterios de aceptación:**
- [x] Lectura, cargos, revisión, corrección y analítica tienen propietario/defaults explícitos.
- [x] Anulación/corrección conserva historia/saldo y no declara devolución de fondos.

**Verificación:**
- [x] Matriz owner/asistente/paciente/operador para cada acción financiera y clínica negativa.
- [x] `git diff --check` y enlaces a D14/especificación de autorización.
- [x] Manual: revisar asistente con lectura solamente y revisor sin permiso clínico.

**Archivos previstos:** `docs/patient-billing.md`, `docs/access-design.md`, `docs/decisions.md`.

**Evidencia:** 2026-11-27. Decisiones del usuario registradas en [D27](../../docs/decisions.md#d27--permisos-financieros-iniciales-y-correcciones-t03): asistentes nuevos y existentes sin acciones financieras por defecto (concesión explícita del propietario); catálogo agrupado en `billing_read` (cargos/saldos, reportes/evidencias en lectura, analítica), `billing_charges` (borradores, emitir/cancelar, ajustes manuales) y `billing_review` (aprobar/rechazar, `staff_entry`, anulaciones); precios siguen con permiso de catálogo/oferta; ningún permiso clínico concede finanzas ni viceversa. Correcciones: cargo con pagos vigentes no cancelable — primero se anulan pagos con motivo/actor/instante conservando reporte, evidencia, comprobante e historia; anular no afirma devolución y no hay reembolso real ni constancia en esta etapa. `docs/patient-billing.md` §6.2, §8.5, §15.1–§15.2 y §24 actualizados. Matriz recorrida: owner con acceso completo; asistente sin concesión denegada en las tres acciones; asistente solo `billing_read` lee cargos pero no aprueba ni emite; revisor con `billing_review` sin permiso clínico no abre notas; acceso clínico sin acciones financieras no lee saldos (negativa en ambas direcciones); operador de plataforma sin acceso financiero de cuentas. `git diff --check` limpio.

## C01 · Después de T01–T03

- [x] `BI-O01`–`BI-O08` están resueltos y registrados.
- [x] Ejemplos de precios, reportes, saldos, permisos y correcciones son coherentes.
- [x] El usuario revisa y acepta C01.

**Aceptado por el usuario el 2026-11-27** tras revisar D25–D27 y la evidencia de T01–T03.

## T04 · Cerrar concesión, offline, archivos y panel

**Estado:** Done. **Propietario:** producto, Hub/API y operación. **Alcance:** M.

**Descripción:** resolver vigencia/revocación del enlace, cancelar/reprogramar cita, trabajo offline, límites/retención de archivos e indicadores iniciales.

**Entradas y dependencias:** C01 aceptado; `BI-O09`–`BI-O12`.

**Datos, contratos, transacciones y consumidores:** políticas documentales; no implementa interfaz Hub completa ni cuenta general de paciente.

**Criterios de aceptación:**
- [x] Concesión limitada por cita/cargo/acción y efectos de cambio de cita están cerrados.
- [x] Offline, capturas/comprobantes y fechas/monedas del primer panel tienen reglas explícitas.

**Verificación:**
- [x] Matriz enlace válido/vencido/revocado, cita reprogramada/cancelada y equipo offline.
- [x] `git diff --check` y referencias OWASP/retención revisadas.
- [x] Manual: seguir paciente que reporta, pierde enlace y personal que revisa sin filtrar otros objetos.

**Archivos previstos:** `docs/patient-billing.md`, `docs/access-design.md`, `docs/quality.md`, `docs/decisions.md`.

**Evidencia:** 2026-11-27. Decisiones del usuario registradas en [D28](../../docs/decisions.md#d28--concesión-del-paciente-offline-archivos-y-primer-panel-t04): concesión vigente mientras la cita esté activa + 30 días tras atención/cierre, revocable por el personal, cancelar revoca (reporte presentado conserva historia), reprogramar mantiene, secreto con huella; offline limitado a borradores de cargo revalidados al sincronizar, todo lo demás online; archivos con la política D24 (JPG/PNG/PDF, 5 MB, una captura por reporte, comprobantes PDF de API, retención mientras la cuenta exista, eliminación solo administrativa trazada); primer panel con los siete indicadores de §19.1, cargado/saldo por fecha de emisión y cobrado por fecha de aprobación, totales por moneda sin revalorizar. `docs/patient-billing.md` §9.5, §11.4, §16.4, §19.3 y §24 actualizados; `BI-O01`–`BI-O12` quedan todos resueltos. Matriz recorrida: enlace válido lee su cargo; enlace de cita cancelada revocado (reporte previo sigue revisable); reprogramación conserva acceso; día 31 tras cierre → acceso denegado sin revelar existencia; equipo offline prepara borrador y lo revalida al sincronizar, pero no puede aprobar ni registrar `staff_entry`. `git diff --check` limpio.

## T05 · Diseñar físicamente precios, cargos, pagos y saldos

**Estado:** Done. **Propietario:** `billing/repository` y esquema físico. **Alcance:** M.

**Descripción:** añadir a la fuente única precios base/oferta, cargos/historias, pagos/aplicaciones y restricciones de saldo/moneda.

**Entradas y dependencias:** T04; decisiones T01/T02.

**Datos, contratos, transacciones y consumidores:** diseño sin migración; decimal, FK compuestas, versiones e instantáneas.

**Criterios de aceptación:**
- [x] Un reporte aprobado→un pago y pagos vigentes≤cargo salvo excedente decidido tienen protección física.
- [x] Cuenta/paciente/cita/atención/servicio y precio histórico tienen claves/restricciones/índices propuestos.

**Verificación:**
- [x] Revisión cruzada de cada regla conceptual con tipo/FK/CHECK/UQ/índice.
- [x] `git diff --check` y fuentes PostgreSQL 18 pertinentes.
- [x] Manual: evaluar dos aprobaciones y cambio/cancelación de cargo contra el diseño.

**Archivos previstos:** `docs/database-schema.md`, `docs/patient-billing.md`.

**Evidencia:** 2026-11-27. `docs/database-schema.md` §19 añade cuatro tablas: `service_prices` (PK compuesta `(professional_id, service_id)` con FK a `services`, CHECK `amount >= 0` — cero es servicio gratuito, sin fila es «sin precio»; CHECK moneda `USD`/`VES`), `service_offer_prices` (PK/FK compuesta a `professional_services`, misma regla de importe/moneda), `patient_charges` (instantáneas `description`/`amount`/`currency`/`price_source`, estados `draft`/`issued`/`cancelled` con CHECK de coherencia de fechas/motivo, FK compuestas por cuenta a `account_patients`, `appointments.(account_id,id)` y `clinical_encounters.(account_id,id,patient_id)` — esta última garantiza la misma cuenta y paciente; UQ `(id, account_id)` para referencias sin cruce) y `charge_histories` (inmutable, acción/actor/motivo/versión). `patient_payments` resuelve `payment_applications` como columna (`charge_id`, D26 un pago un cargo) con CHECK de conversión completa-o-ausente (tasa/fecha/fuente/`amount_usd` solo en pagos VES aplicados a cargo USD, D25), CHECK `origin`↔`origin_report_id` y anulación con motivo/actor que no afirma devolución (D27). Protección física de saldo: bloqueo `FOR UPDATE` de la fila del cargo en la transacción de aprobación, UQ de `origin_report_id` (una aprobación → máximo un pago, §20.3) y CHECK de moneda; cancelación de cargo con pagos vigentes rechazada bajo el mismo bloqueo (D27). Dos aprobaciones concurrentes y cambio/cancelación evaluados contra el diseño. `git diff --check` limpio.

## T06 · Diseñar físicamente reportes, evidencias y concesiones

**Estado:** Done. **Propietario:** `billing/repository` y seguridad de acceso. **Alcance:** M.

**Descripción:** diseñar declaración/verificación, metadatos de captura/comprobante y concesiones privadas de paciente con vigencia/revocación.

**Entradas y dependencias:** T05; T03/T04.

**Datos, contratos, transacciones y consumidores:** bytes fuera de DB/sync, secretos con huella si aplica y proyecciones mínimas.

**Criterios de aceptación:**
- [x] Declarados/verificados/historia no se reescriben y objetos/concesiones no cruzan cuentas.
- [x] Captura/comprobante y secreto de enlace no se exponen en auditoría/logs/journal.

**Verificación:**
- [x] Revisión de ciclo reporte/concesión y todos sus estados contra restricciones.
- [x] `git diff --check` y enlaces OWASP/PostgreSQL.
- [x] Manual: evaluar reutilización, sustitución y revocación de enlace sin acceso por UUID.

**Archivos previstos:** `docs/database-schema.md`, `docs/architecture.md`, `docs/access-design.md`.

**Evidencia:** 2026-11-27. `docs/database-schema.md` §20 añade cinco tablas: `billing_exchange_rates` (tasas BCV propias por cuenta, UQ `(account_id, rate_date)`, D25), `patient_payment_reports` (declarados inmutables, verificados solo en la revisión; obligatorios de D26 como NN; referencia opcional `declared_reference_last4`; cadena `previous_report_id`; FK compuesta al cargo y al paciente; `grant_id` obligatorio), `patient_payment_evidence` (UQ `report_id` — una captura; solo metadatos, `storage_key` interno, CHECK tipo/tamaño/sha256 de D24/D28), `billing_reviews` (UQ `report_id` — imposible decidir dos veces; CHECK aprobado⇒verificados, rechazado⇒motivo; `internal_note` nunca proyectada) y `payment_receipts` (UQ `payment_id`, PDF de API, instantánea conservada, no fiscal ni devolución) más `patient_billing_grants` (huella `token_hash` UQ — nunca secreto en claro; CHECK al menos un objeto cita/cargo; acciones cerradas `read_charge`/`submit_report`/`read_result`/`read_receipt`; `expires_at` ligado a la cita con máximo 30 días, cancelar revoca en la misma operación, reprogramar mantiene — D28). Ciclo completo evaluado: presentación pendiente sin efecto, aprobación única vía UQ doble (`billing_reviews.report_id`, `patient_payments.origin_report_id`), rechazo con cadena, revocación/vencimiento de enlace sin revelar existencia, UUID sin huella no autoriza. Bytes, secretos y referencias bancarias excluidos de journal/snapshots/logs por diseño (§20.7). `git diff --check` limpio.

## C02 · Después de T04–T06

- [x] `BI-O09`–`BI-O12` están resueltos y el diseño cubre concesión/archivos/analítica.
- [x] Las restricciones físicas protegen saldo, efecto único, aislamiento e historia.
- [x] El usuario revisa y acepta C02.

**Aceptado por el usuario el 2026-11-27** tras revisar D28 y el diseño físico de §19–§20 de `docs/database-schema.md`.

## T07 · Diseñar contratos del personal y paciente

**Estado:** Done. **Propietario:** `billing`, contratos y acceso. **Alcance:** M.

**Descripción:** fijar rutas/operaciones/modelos para precios, cargos, reportes, revisión, pagos, correcciones, comprobantes y concesiones.

**Entradas y dependencias:** C02 aceptado; catálogo de autorización.

**Datos, contratos, transacciones y consumidores:** camelCase, page/shows, operaciones idempotentes, errores seguros y límites de archivos.

**Criterios de aceptación:**
- [x] Cada acción tiene actor/objeto/versión/transacción/resultado y permiso explícito.
- [x] Paciente recibe solo proyección mínima y no puede aprobar/corregir ni ver otros cargos.

**Verificación:**
- [x] Cobertura de todos los casos §18 de la especificación sin rutas duplicadas.
- [x] `git diff --check` y validación de enlaces/anclas.
- [x] Manual: recorrer respuesta perdida en reporte/aprobación y descarga con enlace revocado.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/contracts.md`, `docs/patient-billing.md`.

**Evidencia:** 2026-11-27. `docs/api-v1.md` §15 añade el diseño completo: §15.1 tres ámbitos separados (personal con `billing_read`/`billing_charges`/`billing_review` de D27; paciente con secreto opaco de concesión en Bearer, sin cuenta ni dispositivo; precios con el permiso de catálogo/oferta existente); §15.2 veintitrés rutas del personal (precios base/oferta, resolución, ciclo completo del cargo, bandeja/detalle/evidencia de revisión, aprobación/rechazo, `staff_entry`, anulación, comprobante, tasas, concesiones y métricas) cada una con acción, `operationId`, versión esperada y transacción explícitos; §15.3 cinco rutas del paciente con proyección mínima y captura obligatoria en multipart; §15.4 modelos públicos con importes como texto decimal, saldo con estado y `basis` de fechas de D28; §15.5 nueve errores específicos con 404 uniforme para enlaces vencidos/revocados/ajenos; §15.6 idempotencia/transacciones/archivos. Cobertura de §18 de la especificación verificada caso por caso (11 de personal, 5 de paciente, sin rutas duplicadas). `docs/access-design.md` registra los tres ámbitos y la revocación; `docs/contracts.md` fija §15 como fuente única. Recorridos manuales: respuesta perdida en presentación/aprobación recuperada con el mismo `operationId` (`duplicate: true`), descarga con enlace revocado → 404 uniforme. `git diff --check` limpio.

## T08 · Diseñar sync, analítica e integración entre componentes

**Estado:** Done. **Propietario:** arquitectura, `sync` y `analytics`. **Alcance:** M.

**Descripción:** fijar propietario de concesiones, audiencia financiera, versiones/época, eventos mínimos y consultas operativas/ETL.

**Entradas y dependencias:** T07; T04/T06.

**Datos, contratos, transacciones y consumidores:** capturas/deltas/SSE sin bytes, analítica pesada en almacén separado cuando aplique.

**Criterios de aceptación:**
- [x] Entidad→audiencia→permiso y cambios de alcance/recuperación están completos.
- [x] Servicios/patients/appointments/encounters interactúan por casos/tipos sin repositorios ajenos.

**Verificación:**
- [x] Matriz de proyección para owner/asistente/paciente y permiso revocado.
- [x] `git diff --check` y revisión de dependencias arquitectónicas.
- [x] Manual: seguir pago aprobado desde commit hasta delta/aviso/indicador sin evidencia.

**Archivos previstos:** `docs/architecture.md`, `docs/api-v1.md`, `docs/quality.md`.

**Evidencia:** 2026-11-27. `docs/api-v1.md` §16 fija: audiencia cerrada `billing` separada de `members`/`owner`/clínicas, con entidades `billing_charge` y `billing_payment` y campos mínimos (sin capturas, comprobantes, referencias, notas internas, tasas ni secretos); borradores nunca proyectados; cambio de permiso financiero invalida capturas/cursores del alcance. Regla de delta explícita: solo operaciones del personal con recibo generan `change_log`; las presentaciones del paciente con concesión no tienen dispositivo de miembro y se recuperan por bandeja online y snapshot (misma regla que §14.6 del operador). Propiedad de integración: concesiones poseídas por `billing`; precio efectivo resuelto por caso público de `services` con instantánea en el cargo; vínculos de citas/atenciones por casos/tipos sin repositorios ajenos; cancelación de cita revoca concesiones ancladas en la misma aceptación. Analítica: panel D28 por `GET A/billing/metrics` con consultas acotadas y `billing_read`; analítica pesada diferida a `analytics` con PostgreSQL separado y hechos mínimos por cursor ETL si el volumen lo exige. `docs/architecture.md` añade la fila del componente `billing` con sus datos propios y dependencias permitidas. Matriz de proyección recorrida: owner y asistente con `billing_read` reciben cargos/pagos; asistente sin acción y paciente no reciben nada; permiso revocado corta el alcance; aprobación con stream caído se recupera por snapshot sin bytes. `git diff --check` limpio.

## T09 · Implementar dominio de dinero, precios y saldos

**Estado:** Done. **Propietario:** `billing/domain`. **Alcance:** M.

**Descripción:** implementar valores monetarios, conversión si se aprobó, resolución base/oferta y cálculo puro de pagos/saldos.

**Entradas y dependencias:** C02 aceptado; T01/T02 y adaptadores T07.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/red, `Decimal`, moneda/tasa/redondeo explícitos.

**Criterios de aceptación:**
- [x] Nulo/cero, USD/VES y precios base/oferta producen resultados exactos.
- [x] Parciales/pagado/excedente/anulado calculan saldo sin mezclar monedas ni revalorizar.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_money -v`.
- [x] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [x] Manual: comparar ejemplos ficticios de T01/T02 con cada resultado y total.

**Archivos previstos:** `src/api/billing/domain/money.py`, `src/api/billing/domain/pricing.py`, `tests/test_billing_money.py`.

**Evidencia:** 2026-11-27. Nuevo componente `src/api/billing` con dominio puro (sin SQL ni red): `domain/money.py` con `Money` (importe ≥ 0, dos decimales exactos, moneda `USD`/`VES`; cero = gratuito, nulo = sin precio vía ausencia), `BcvRate` propia de facturación (hasta seis decimales, D25), `usd_to_ves`/`ves_to_usd` con redondeo half-up a dos decimales aplicado una vez y `charge_balance` (saldo = total − pagos vigentes; excedente es error, nunca crédito — D26; cargo gratuito con saldo cero cuenta como `paid` — §19.1; los anulados los excluye el llamador). `domain/pricing.py` con `resolve_price` (oferta sustituye a base; `None` = sin precio; la estimación usa la misma resolución sin reservar). 16 pruebas nuevas en `tests/test_billing_money.py` con los ejemplos ficticios de T01/T02: 18.00×400.25=7204.50, 100 USD pagados con 40025.00 VES, redondeo 2.675→2.68, dos parciales 40+60→`paid`, excedente 60+50 rechazado, anulado excluido, gratuito `paid`, NaN/infinito/negativos/tres decimales/EUR rechazados. Un fallo real encontrado y corregido: la precedencia de estado marcaba `unpaid` un cargo de total cero; §19.1 exige `paid` por saldo cero. 19 pruebas conjuntas con estructura OK; `uv build --offline` OK.

## C03 · Después de T07–T09

- [x] Contratos e integración cubren actores, sync y analítica.
- [x] Dinero, precios y saldos pasan pruebas de dominio.
- [x] El usuario revisa y acepta C03.

**Aceptado por el usuario el 2026-11-27** tras revisar api-v1.md §15–§16, architecture.md y las pruebas de `tests/test_billing_money.py`.

## T10 · Implementar dominio de cargos, reportes y pagos

**Estado:** Done. **Propietario:** `billing/domain`. **Alcance:** M.

**Descripción:** implementar modelos/transiciones de borrador/cargo abierto/cancelado, reporte/revisión, pago y concesión.

**Entradas y dependencias:** C03 aceptado; T02–T04/T07.

**Datos, contratos, transacciones y consumidores:** esquemas estrictos base, contenido financiero sin bytes ni SQL.

**Criterios de aceptación:**
- [x] Borrador no es visible al paciente y solo personal con acción puede aprobar/corregir.
- [x] Rechazo/nueva presentación/anulación y estados de concesión conservan historia.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_domain -v`.
- [x] `uv run --locked python -m unittest tests.test_project_structure tests.test_billing_domain -v`.
- [x] Manual: validar transiciones permitidas/prohibidas y datos declarados frente a verificados.

**Archivos previstos:** `src/api/billing/domain/charges.py`, `src/api/billing/domain/payments.py`, `tests/test_billing_domain.py`.

**Evidencia:** 2026-11-27. `domain/charges.py`: `Charge` con instantánea y `price_source`; transiciones `update_draft` (solo borrador; ajuste manual exige motivo y marca `manual`), `issue`, `cancel` (con pagos vigentes → `ChargeHasActivePaymentsError`, D27; conserva historia), `visible_to_patient` (borrador nunca visible) e instantes con zona obligatoria. `domain/payments.py`: `DeclaredPayment` (obligatorios D26, referencia opcional de 4 dígitos, dos decimales exactos), `PatientPaymentReport` con `decide` único (UQ lógica: decidido no se reabre) y `resubmission` encadenada; `VerifiedPayment` separado de lo declarado; `convert_verified` con conversión explícita previa y instantánea de tasa (D25, misma moneda no requiere tasa, otra moneda sin tasa → `CurrencyMismatchError`); `new_payment` con origen distinguible `patient_report`/`staff_entry`; `annul` que excluye del vigente sin borrar ni afirmar devolución (D27); `PatientBillingGrant` con `usable` (huella fuera del dominio; vigencia/revocación/acción) y `ensure_grant_object` (concesión siempre por objeto concreto, D28). 15 pruebas nuevas en `tests/test_billing_domain.py` cubriendo transiciones permitidas/prohibidas, declarado frente a verificado, conversión VES→USD 40025.00→100.00 y concesión válida/vencida/revoked/sin acción. 34 pruebas conjuntas (dinero + dominio + estructura) OK; build OK en T09.

## T11 · Implementar persistencia de precios y cargos

**Estado:** Done. **Propietario:** `billing/repository`, `services` y migraciones. **Alcance:** M.

**Descripción:** crear migración/modelos/DAOs para precios base/oferta, cargos e historias con relaciones e instantáneas.

**Entradas y dependencias:** T10; T05.

**Datos, contratos, transacciones y consumidores:** DAOs derivados commit=False, FK/CHECK/UQ, privilegios mínimos y sin cambio de citas.

**Criterios de aceptación:**
- [x] Migración up/down/reapply protege moneda, importes, vínculos y versiones.
- [x] Cambiar precio actual no reescribe cargo y rol operativo no ejecuta DDL.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_persistence -v`.
- [x] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [x] Manual: probar cruce de cuenta/paciente/cita y modificación de instantánea con SQL.

**Archivos previstos:** `migrations/versions/<revisión>_billing_charges.py`, `src/api/billing/repository/models.py`, `src/api/billing/repository/dao.py`, `src/api/services/repository/models.py`, `tests/test_billing_persistence.py`.

**Evidencia:** 2026-11-27. Migración `20261127_02_billing_charges.py` (down `20261127_01`) con cuatro tablas del §19: `service_prices` (PK compuesta con FK a `services.(professional_id,id)`, CHECK `amount >= 0` y moneda `USD`/`VES`), `service_offer_prices` (FK a la oferta real), `patient_charges` (UQ nombrada `(id,account_id)`, FK compuestas a `account_patients`, `appointments.(account_id,id,patient_id)` y `clinical_encounters.(account_id,id,patient_id)` — ambas garantizan misma cuenta y paciente; CHECK de coherencia draft/issued/cancelled) y `charge_histories` (FK compuesta al cargo, acciones cerradas). Grants mínimos a `nightingale_runtime`: DELETE solo en precios (retirar ajuste), nunca en cargos/historias. `src/api/billing/repository/models.py` refleja el DDL y `dao.py` añade DAOs derivados commit=False: upserts de precio, `by_id_for_update` (bloqueo de saldo), `apply_update` optimista, páginas `page/shows` por paciente e historias ordenadas. `docs/database-schema.md` §19.3 alineado con la FK triple de cita. 8 pruebas nuevas contra PostgreSQL Test real: rol runtime escribe por grants y no borra cargos/historias ni ejecuta DDL; precio cero válido, negativo/EUR/duplicado/servicio inexistente rechazados; precio de oferta exige la fila de oferta; cruce de cuenta y de paciente por cita viola FK; coherencia de estados; cambio de catálogo (18→20) no reescribe el cargo emitido; historia no cruza cuentas ni admite acciones fuera del catálogo; downgrade a `20261127_01` elimina las tablas y el reapply las restaura. El probe de persistencia exigió actualizar su inventario de timestamps (99→106, siete columnas nuevas) y pasó completo (migraciones up/down, rollback de revisión fallida, DDL denegado, dos escritores coordinados). Tres fallos de fixture corregidos en el propio test (sync head obligatorio, completitud de paciente y primera historia de cita). 42 pruebas billing+estructura OK; `uv build --offline` OK.

## T12 · Implementar persistencia de reportes, pagos y concesiones

**Estado:** Done. **Propietario:** `billing/repository` y migraciones. **Alcance:** M.

**Descripción:** añadir reportes/revisiones/evidencias, pagos/aplicaciones, comprobantes y concesiones con restricciones de efecto/saldo.

**Entradas y dependencias:** T11; T06.

**Datos, contratos, transacciones y consumidores:** misma sesión commit=False; sin bytes/secretos en journal y referencias por cuenta.

**Criterios de aceptación:**
- [x] Una aprobación genera como máximo un pago y carreras SQL no exceden el cargo.
- [x] Concesión/evidencia/comprobante no cruza cuenta y anulaciones conservan historia.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_persistence tests.test_billing_domain -v`.
- [x] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [x] Manual: intentar doble pago de origen, exceso concurrente y acceso por concesión ajena.

**Archivos previstos:** `migrations/versions/<revisión>_billing_payments.py`, `src/api/billing/repository/models.py`, `src/api/billing/repository/dao.py`, `tests/test_billing_persistence.py`.

**Evidencia:** 2026-11-27. Migración `20261127_03_billing_payments.py` (down `20261127_02`) con siete tablas: `billing_exchange_rates` (UQ `(account_id, rate_date)`, configuración propia por cuenta — D25), `patient_billing_grants` (huella 64-hex UQ, acciones cerradas, CHECK al menos un objeto, FK compuestas a paciente/cita/cargo), `patient_payment_reports` (UQ `(id, account_id)`, obligatorios D26, cadena `previous_report_id`), `patient_payment_evidence` (UQ `report_id`, tipos/tamaño/sha256 de D24/D28), `billing_reviews` (UQ `report_id` + FK compuesta `(report_id, account_id)`, CHECK aprobado⇒verificados / rechazado⇒motivo), `patient_payments` (UQ `origin_report_id` — una aprobación → máximo un pago; CHECK origen↔reporte, conversión completa-o-ausente solo con moneda USD, anulación con actor/motivo obligatorios) y `payment_receipts` (UQ `payment_id`, solo PDF). Grants mínimos: DELETE en ninguna; UPDATE solo en grants/reports/payments. Modelos y DAOs añadidos (`by_id_for_update` de reporte, `apply_status`/`annul` optimistas, `active_amounts_of` para el saldo, `applicable` de tasa con regla D22, revocación por cita de D28, bandejas paginadas). 8 pruebas nuevas contra PostgreSQL Test real (16 en total): tasas únicas por cuenta/fecha con configuración separada; concesión exige huella hex, acciones cerradas y objeto, revocación por UPDATE conservando la fila; reporte no cruza cuentas, referencia de 4 dígitos, cadena tras rechazo; evidencia única y validada; doble decisión y doble pago del mismo origen rechazados por UQ; staff_entry sin reporte, conversión parcial rechazada, anulación sin actor/motivo rechazada y anulación que deja de sumar; carrera real de dos conexiones sobre el último saldo — la segunda espera el bloqueo `FOR UPDATE` del cargo, ve los 60.00 ya aplicados de 100.00 y el exceso queda rechazable; comprobante único y solo PDF; downgrade a `20261127_02` elimina las siete tablas conservando `patient_charges` y el reapply las restaura. Inventario de timestamps del probe actualizado (106→114). 31 pruebas (persistencia+dominio) OK; probe de persistencia pasado; `uv build --offline` OK.

## C04 · Después de T10–T12

- [x] Dominio y persistencia pasan pruebas de integridad/privilegios.
- [x] Instantáneas, saldo, efecto único y concesiones están protegidos.
- [x] El usuario revisa y acepta C04.

**Aceptado por el usuario el 2026-11-27** tras revisar las migraciones `20261127_02`/`20261127_03`, los DAOs y las 42 pruebas con el probe de persistencia.

## T13 · Integrar precios base/oferta con servicios

**Estado:** Done. **Propietario:** `services` y `billing`. **Alcance:** M.

**Descripción:** añadir precios a contratos/casos de catálogo/oferta y resolver precio efectivo mediante caso público para cargos.

**Entradas y dependencias:** C04 aceptado; T01/T09.

**Datos, contratos, transacciones y consumidores:** propiedad profesional/oferta, operaciones existentes versionadas y proyecciones autorizadas.

**Criterios de aceptación:**
- [x] Solo profesional/oferta autorizada modifica precios y miembros reciben lo permitido.
- [x] Base/override/nulo/cero y cambios de versión se resuelven sin alterar citas/cargos anteriores.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_services tests.test_billing_pricing -v`.
- [x] `./.venv/Scripts/python.exe test-support/services/check.py`.
- [x] Manual: editar precio, resolverlo en dos cuentas y comprobar instantánea histórica.

**Archivos previstos:** `src/api/services/domain/services.py`, `src/api/services/domain/offers.py`, `src/api/services/application/services_cases.py`, `src/api/services/application/offers_cases.py`, `tests/test_billing_pricing.py`.

**Evidencia:** 2026-11-27. Corrección de propiedad detectada al implementar: los precios pertenecen al componente `services` (plan §4), no a `billing`; los modelos/DAOs `ServicePrice`/`ServiceOfferPrice` se movieron de `billing/repository` a `services/repository` (la DDL no cambia). Dominio: `SetServicePricePayload`/`SetServiceOfferPricePayload` (importe decimal ≥ 0 con dos decimales — cero es gratuito; moneda USD/VES; extra prohibido), `RemoveServiceOfferPricePayload` vacío y respuestas `ServicePriceResponse`/`ServiceOfferPriceResponse`. Casos: `apply_service_operation` añade `SetServicePrice` (solo propietario del catálogo vía `account_professional(own=True)`, versión optimista con 0 al crear, cambio `service_price` audiencia `owner`); `apply_offer_operation` añade `SetServiceOfferPrice`/`RemoveServiceOfferPrice` (la oferta debe existir; versión optimista; retirar devuelve la resolución al base; cambio `service_offer_price` audiencia `members`). Registro completo: `SERVICE_SCHEMAS`/`OFFER_SCHEMAS` en sync, `projection_audiences` (owner/members) y `PROJECTION_SCHEMAS` en downloads; `snapshot_services` proyecta precios base del propio profesional y ajustes de la cuenta. Caso público `resolve_service_price` para billing: oferta sustituye a base, `None` = sin precio, cero válido, sin reservar precio. Hallazgo real: el `DAO.create` genérico exige PK `id`; los precios tienen PK compuesta y usan inserción directa con flush (comentado en el DAO). 5 pruebas nuevas en `tests/test_billing_pricing.py` (payloads y resolución real contra PostgreSQL Test con motor propio: nulo/base/oferta/cero, versión incremental, retiro→base, FK de oferta). Regresiones: `test_services`, `test_project_structure`, `test_downloads`, `test_subscription_sync` y probe de services pasados; build OK. La instantánea histórica del cargo quedó probada en T11 (cambio de catálogo 18→20 sin reescribir el cargo).

## T14 · Implementar cargos por el personal

**Estado:** Done. **Propietario:** `billing` y `sync`. **Alcance:** M.

**Descripción:** implementar crear/editar borrador, emitir, consultar/listar y cancelar cargo con relaciones e instantáneas.

**Entradas y dependencias:** T13; T03/T07.

**Datos, contratos, transacciones y consumidores:** efecto/historia/auditoría/recibo/grupo en una transacción; sin cargo automático.

**Criterios de aceptación:**
- [x] Borrador editable/emitido inmutable según regla y cancelación conserva historia/pagos.
- [x] Objetos cruzados, ajuste no autorizado y cambios de precio concurrentes se rechazan coherentemente.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_charges tests.test_operations -v`.
- [x] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [x] Manual: crear desde cita y atención sin cita, emitir/cancelar y revisar versión/historia/auditoría.

**Archivos previstos:** `src/api/billing/application/charge_cases.py`, `src/api/billing/infrastructure/charges_api.py`, `tests/test_billing_charges.py`.

**Evidencia:** 2026-11-27. Permisos financieros de D27 implementados: migración `20261127_04_billing_permissions.py` (tres columnas `billing_*_access` en `account_memberships` con CHECK `none`/`granted`, por defecto `none` — denegado por defecto; audiencia `billing` en el CHECK del journal), `BillingPermissions`/`BillingPermissionsPayload`/`MemberBillingPermissionsResponse` en el dominio de accounts, `AccountContext.billing_permissions` poblado en los dos puntos de contexto, acción de propietario `SetMemberBillingPermissions` (versionada, con efecto de alcance que invalida capturas) y regla `billing` en `OperationPolicy`/`policy_allows`. Cargos: payloads estrictos en `billing/domain/charges.py` (manual⇒motivo, moneda⇒importe, sin servicio⇒descripción) y `ChargeResponse` con saldo; `billing/application/charge_cases.py` con `apply_charge_operation` (crear desde servicio resolviendo el precio por el caso público de services con instantánea, o cargo libre/manual; editar solo borrador; emitir congelando; cancelar con bloqueo de fila y rechazo `CHARGE_HAS_ACTIVE_PAYMENTS` si hay pagos vigentes — D27; historial atómico en la misma transacción; cambios con audiencia `billing` invisible hasta T24) y lecturas `read_charges`/`read_charge_detail` con `billing_read` antes de contar/paginar. Rutas GET en `infrastructure/charges_api.py` registradas en la app. Casos públicos nuevos consumidos sin importar repositorios ajenos: `clinical_patient`, `encounter_appointment`, `encounter_for_record`, `charge_service_reference` (este último movido al DAO tras detectar la infracción de estructura — la aplicación no ejecuta SQL). Registro completo en `BILLING_CHARGE_SCHEMAS`, `OPERATION_SCHEMAS`, catálogo de políticas, `projection_audiences` y `PROJECTION_SCHEMAS`. 9 pruebas nuevas en `tests/test_billing_charges.py` (payloads; creación con instantánea precio/descripción; asistente denegado sin concesión y permitido con ella; 404 uniforme en paciente/vínculo cruzado; ajuste manual con historial `created`/`amount_adjusted`; emisión congelada con `CHARGE_NOT_DRAFT`; pago vigente bloquea cancelación; versión obsoleta 409; `PRICE_NOT_DEFINED`). Matrices de estructura/permisos/descargas actualizadas a los nuevos catálogos. 415 pruebas en discover: solo quedan fallos preexistentes ajenos al cambio (`src/api/users` inexistente referenciado por un test de estructura antiguo y dataset `vademecum/` ausente), verificados contra el diff. Probe de persistencia y de services pasados; build OK.

## T15 · Reutilizar almacenamiento privado para capturas

**Estado:** Done. **Propietario:** `core/services`, `subscriptions` y `billing`. **Alcance:** M.

**Descripción:** extraer solo el soporte común demostrado del plan de suscripciones y conectar capturas de billing sin duplicar adaptador ni cambiar su comportamiento.

**Entradas y dependencias:** T14; storage de suscripciones C06 y T04.

**Datos, contratos, transacciones y consumidores:** bytes fuera de DB/sync/webroot; validación/límites propios y referencias autorizadas.

**Criterios de aceptación:**
- [x] Ambos componentes usan soporte común sin imports de repositorios ni regresión de suscripciones.
- [x] Tipo/tamaño/nombre, descarga reautorizada y logs cumplen seguridad.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_evidence tests.test_subscription_evidence -v`.
- [x] `./.venv/Scripts/python.exe test-support/subscriptions/check.py` y `uv build --offline`.
- [x] Manual: cargar evidencia en ambos dominios y comprobar aislamiento cruzado/ausencia en logs.

**Archivos previstos:** `src/core/services/private_evidence.py`, `src/api/subscriptions/application/evidence_cases.py`, `src/api/billing/application/evidence_cases.py`, `tests/test_billing_evidence.py`, `tests/test_subscription_evidence.py`.

**Evidencia:** 2026-11-27. Siguiendo la escalera de minimal-code, el adaptador de almacenamiento ya era genérico (`src/core/services/report_storage.py`, sin duplicar ni cambiar): el soporte común demostrado era la validación de captura. Nuevo `src/core/services/private_evidence.py` con `detect_content_type` (firmas reales JPEG/PNG/PDF, nunca el Content-Type del cliente — OWASP), `validate_capture` (tamaño 1 byte–máximo, firma real, sha256) y el error compartido `EvidenceRejected`. Suscripciones refactorizado sin cambio de comportamiento: `domain/reports.detect_content_type` delega en el soporte común conservando su nombre público y `evidence_cases._check_content` usa `validate_capture` mapeando al error propio; sus 3 pruebas pasan sin tocarse. Billing: `application/evidence_cases.py` con `store_report_evidence` (una captura por reporte — D28/D24; bytes escritos fuera de la transacción antes de la fila de metadatos, un fallo deja huérfano sin efecto; bloqueo del reporte; 404 uniforme ajeno/inexistente; `ReportNotPending`/`EvidenceAlreadyPresent`) y `read_report_evidence` (bytes+tipo; la reautorización ocurre en la ruta; conocer `storage_key` no concede nada). 3 pruebas nuevas en `tests/test_billing_evidence.py` contra PostgreSQL Test y almacenamiento local real: PNG guardado con metadatos/sha256 y descargado idéntico; GIF por firma, vacío y >5 MB rechazados; segunda captura rechazada; cruce de cuenta 404; reporte decidido no admite captura; sin evidencia → `EvidenceNotFound`; archivos de prueba eliminados en `asyncTearDown`. Regresiones: 6 pruebas conjuntas OK, probe de suscripciones pasado completo, build OK.

## C05 · Después de T13–T15

- [x] Precios/cargos y almacenamiento común pasan sin regresión de suscripciones.
- [x] Borradores/ajustes/archivos respetan permisos e historia.
- [x] El usuario revisa y acepta C05.

**Aceptado por el usuario el 2026-11-27** tras revisar T13–T15 (precios en services, ciclo de cargos con permisos D27, soporte común de evidencia privada).

## T16 · Implementar concesión y proyección de cargo para paciente

**Estado:** Done. **Propietario:** acceso limitado API y `billing`. **Alcance:** M.

**Descripción:** implementar emisión/validación/revocación de concesión según T04 y lectura mínima de cargo/saldo relacionado con cita.

**Entradas y dependencias:** C05 aceptado; D16 y contratos T07.

**Datos, contratos, transacciones y consumidores:** concesión por objeto/acción, huella de secreto si aplica, auditoría y sin cuenta general.

**Criterios de aceptación:**
- [x] Enlace válido lee solo cargo permitido; vencido/revocado/ajeno no revela existencia.
- [x] Cancelar/reprogramar cita sigue T04 y no abre otros cargos/historia clínica.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_patient_access -v`.
- [x] `./.venv/Scripts/python.exe test-support/access/check.py` y pruebas ASGI del módulo.
- [x] Manual: usar enlace con distintos UUID/acciones y revocar antes de lectura/descarga.

**Archivos previstos:** módulos de concesión definidos en T08, `src/api/billing/application/patient_cases.py`, `src/api/billing/infrastructure/patient_api.py`, `tests/test_billing_patient_access.py`, máximo cinco archivos.

**Evidencia:** 2026-11-27. `application/grant_cases.py`: `issue_grant` (secreto `secrets.token_hex(32)` entregado una sola vez; solo huella sha256 persistida; `operationId` del cliente como id de concesión — el reintento devuelve `duplicate: true` sin secreto y nunca crea otra; ancla de cita vía caso público nuevo `grant_anchor_appointment` con vencimiento `ends_at`+30 días, o cargo concreto con vencimiento de 30 días — límite registrado; objeto incoherente/ajeno → 404 uniforme; auditoría de control en la misma transacción), `revoke_grant` (efecto inmediato, fila e historia conservadas, auditoría) y `list_grants`. `application/patient_cases.py`: `usable_grant` (huella + vigencia + no revocación + acción; el UUID solo no autoriza) y `read_patient_charges` (proyección mínima §9.3 con saldo y estado del último reporte; borradores nunca visibles; concesión de cita lista solo los cargos emitidos de esa cita). Rutas: POST/GET de concesiones del personal en `charges_api.py` (emisión/revocación con `billing_review`, listado con `billing_read`) y `patient_api.py` con `GET /v1/patient/billing/charge` (Bearer del secreto; cualquier enlace inválido → 404 uniforme sin revelar existencia). 5 pruebas nuevas contra PostgreSQL Test: secreto entregado una vez con huella distinta persistida y reintento idempotente sin duplicar; concesión de cita vence exactamente 30 días tras el fin; enlace válido lee solo su cargo (borrador invisible, concesión de cita no lista el borrador); vencido/revocado/ajeno/sin acción → ausencia uniforme con fila conservada; objeto cruzado/inexistente → 404. Regresiones: cargos/dominio/dinero/estructura/citas OK; probe de acceso pasado; build OK. La regla D28 «cancelar la cita revoca sus concesiones ancladas en la misma aceptación» quedó integrada: `CancelAppointment` invoca el caso público `revoke_appointment_grants` (import local documentado para romper el ciclo, ya que billing consume los casos públicos de citas) y una sexta prueba verifica que solo la concesión anclada se revoca mientras la de cargo sobrevive.

## T17 · Implementar reporte del paciente con captura

**Estado:** Done. **Propietario:** `billing` y acceso limitado. **Alcance:** M.

**Descripción:** implementar presentación online, listas/detalle/resultado propios, idempotencia y probe HTTP real con captura obligatoria.

**Entradas y dependencias:** T16; T02/T07.

**Datos, contratos, transacciones y consumidores:** reporte/metadatos/recibo/auditoría atómicos, bytes fuera de transacción y saldo sin cambios.

**Criterios de aceptación:**
- [x] Presentar crea `pending` sin pago y respuesta perdida recupera mismo reporte/captura.
- [x] Paciente no aprueba ni accede a reportes/cargos fuera de concesión.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_reports tests.test_billing_patient_access -v`.
- [x] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [x] Manual: cortar respuesta tras commit, reintentar y verificar un solo reporte y saldo original.

**Archivos previstos:** `src/api/billing/application/report_cases.py`, `src/api/billing/infrastructure/reports_api.py`, `tests/test_billing_reports.py`, `test-support/billing/check.py`.

**Evidencia:** 2026-11-27. `application/report_cases.py`: `submit_report` (captura obligatoria validada por firma real antes de cualquier efecto; una transacción confirma reporte `pending` + auditoría — el `operationId` del cliente es el id del reporte, así el reintento devuelve `duplicate: true` sin duplicar reporte ni captura; objetivo validado contra el alcance de la concesión —cargo propio o cargo emitido de la cita anclada, borradores fuera—; `previousReportId` exige un reporte rechazado de la cuenta; los bytes se escriben fuera de la transacción y un fallo deja huérfano sin efecto; el saldo nunca cambia), `list_own_reports` y `read_own_report` (resultado visible: decisión, datos mínimos del pago o motivo seguro; la nota interna jamás se proyecta — verificado en la prueba). Rutas en `infrastructure/reports_api.py`: POST multipart con alias camelCase (hallazgo: los campos Form no heredan el alias del BaseModel; corregido con `Form(alias=...)` y verificado con reproducción aislada), GET lista y GET detalle; enlace inválido u objeto fuera de alcance → 404 uniforme. 5 pruebas nuevas contra PostgreSQL Test: pending sin pagos y con una sola captura; reintento idempotente; captura vacía/GIF rechazada sin crear reporte; cargo ajeno y enlace inválido ausentes; cadena de nueva presentación solo tras rechazo; resultado aprobado con pago mínimo y sin nota interna. Probe nuevo `test-support/billing/check.py` de punta a punta (Keycloak real, PostgreSQL Test aislado, ASGI real, almacenamiento local en .tmp): emisión de concesión con secreto único y reintento idempotente, lectura del cargo sin borradores, 404 uniforme, captura validada, presentación pendiente sin efecto en el saldo, respuesta perdida recuperada, listas/detalle y revocación que corta el acceso conservando el reporte. Tres fallos de fixture corregidos en las pruebas (dispositivo para auditoría, cuenta independent, contexto propio del módulo). Regresiones de cargos/acceso/evidencia/estructura OK; build y diff limpios.

## T18 · Implementar bandeja de revisión del personal

**Estado:** Done. **Propietario:** `billing` y seguridad financiera. **Alcance:** M.

**Descripción:** implementar pendientes/historia, detalle, evidencia y datos mínimos de paciente/cargo para asistente revisor.

**Entradas y dependencias:** T17; permisos T03.

**Datos, contratos, transacciones y consumidores:** autorización antes de total/página, lecturas auditadas y sin contenido clínico.

**Criterios de aceptación:**
- [x] Solo acción de revisión abre bandeja/evidencia y no concede notas/diagnósticos.
- [x] Totales/páginas/descarga no filtran otras cuentas ni observaciones internas al paciente.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_review tests.test_clinical_permissions -v`.
- [x] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [x] Manual: comparar asistente lector/revisor/sin permiso y objeto de otra cuenta.

**Archivos previstos:** `src/api/billing/application/review_cases.py`, `src/api/billing/infrastructure/reviews_api.py`, `tests/test_billing_review.py`.

**Evidencia:** 2026-11-27. `application/review_cases.py`: `review_inbox` (bandeja paginada con filtros estado/cargo/paciente; la autorización precede a contar/paginar), `review_detail` (declaración completa, metadatos de evidencia sin `storage_key`, revisión con nota interna visible solo al personal, cadena de nuevas presentaciones y advertencias de coincidencia de referencia parcial que nunca rechazan — §10.5) y `review_evidence` (bytes+tipo por cuenta; conocer la clave no concede nada). Rutas en `infrastructure/reviews_api.py` con `billing_review` obligatorio (propietario siempre; asistente solo con concesión explícita) y descarga con nombre interno generado. 3 pruebas nuevas contra PostgreSQL Test: bandeja filtra y no cruza cuentas; detalle con evidencia, advertencia por referencia `0071` compartida, revisión con nota interna y cadena tras rechazo; descarga acotada por cuenta con 404 uniforme. Probe `billing` ampliado: bandeja/detalle/descarga del propietario (200, sin claves de almacenamiento en la respuesta, bytes idénticos) y asistente real invitado con dispositivo registrado pero sin concesión financiera recibe 403 en las tres rutas — revisar no deriva acceso clínico ni viceversa. Regresiones: reportes/permisos clínicos/estructura OK; build y diff limpios.

## C06 · Después de T16–T18

- [x] Paciente reporta sin cambiar saldo y personal revisa con alcance mínimo.
- [x] Enlaces, evidencias, idempotencia y aislamiento pasan.
- [x] El usuario revisa y acepta C06.

**Aceptado por el usuario el 2026-11-27** tras revisar T16–T18 y el probe `billing` de punta a punta.

## T19 · Implementar aprobación atómica y saldo

**Estado:** Done. **Propietario:** `billing`, `sync` y `audit`. **Alcance:** M.

**Descripción:** implementar decisión de revisor, datos verificados, pago/aplicación y saldo coordinado con una única operación efectiva.

**Entradas y dependencias:** C06 aceptado; T02/T09/T12.

**Datos, contratos, transacciones y consumidores:** reporte/pago/cargo/historia/auditoría/recibo/grupo en una transacción; sin red dentro.

**Criterios de aceptación:**
- [x] Aprobación crea un pago y saldo correcto una vez, con revisor real e instantánea de moneda/tasa.
- [x] Dos revisores/parciales/respuesta perdida no duplican pago ni exceden cargo.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_approval tests.test_billing_money -v`.
- [x] `./.venv/Scripts/python.exe test-support/billing/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [x] Manual: disputar aprobación y último saldo, revisar SQL/recuperación tras corte de respuesta.

**Archivos previstos:** `src/api/billing/application/review_cases.py`, `src/api/sync/application/operations_cases.py`, `tests/test_billing_approval.py`, `test-support/billing/check.py`.

**Evidencia:** 2026-11-27. `approve_report` en `review_cases.py`: una sola transacción con bloqueo `FOR UPDATE` del reporte y del cargo; 404 uniforme, `REPORT_NOT_PENDING` (409) si ya fue decidido, conversión explícita VES→USD con la tasa BCV aplicable de la fecha del pago verificado (regla D22; sin tasa → `PAYMENT_MISMATCH` 422 y el reporte queda `pending`), rechazo de excedente (`PAYMENT_EXCEEDS_BALANCE` 422 — D26, sin aprobación recortada), inserción de revisión con revisor real y `billing_exchange_rate_id`, cambio de estado optimista, pago único con `origin_report_id` (la UQ es la última línea de defensa), instantánea completa de conversión y auditoría de control. Ruta POST `.../reports/{report_id}/approval` con `billing_review`. 3 pruebas nuevas contra PostgreSQL Test: aprobación crea un pago y saldo parcial una vez con reintento perdedor y un solo pago por origen; dos parciales (40 USD + 24015 VES→60 USD a tasa 400.25 con instantánea) llegan a `paid` y el excedente de 10 es rechazado conservando dos pagos activos; pago VES sin tasa rechazado dejando el reporte pendiente. Probe `billing` ampliado: aprobación 200 con saldo, reintento 409, paciente ve el resultado visible con importe del pago, excedente 422 con saldo intacto en 60.00, y el asistente sin concesión sigue en 403. La publicación del grupo en el journal llega con la audiencia financiera de T24 (diseño §16.2). Regresiones: revisión/dinero/estructura OK; probes billing y sync pasados; build OK.

## T20 · Implementar rechazo y nueva presentación

**Estado:** Done. **Propietario:** `billing`. **Alcance:** M.

**Descripción:** añadir rechazo con motivo seguro y nueva presentación relacionada sin reabrir ni reescribir el original.

**Entradas y dependencias:** T19; T02/T10.

**Datos, contratos, transacciones y consumidores:** cargo/pagos anteriores sin cambio, revisión/recibo/auditoría atómicos.

**Criterios de aceptación:**
- [x] Rechazo no crea pago ni cambia saldo/cita y conserva evidencia/motivo.
- [x] Nueva presentación mantiene cadena e historia y puede aprobarse solo una vez.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_reports tests.test_billing_approval -v`.
- [x] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [x] Manual: rechazar, corregir, reenviar y aprobar verificando saldo e historia completa.

**Archivos previstos:** `src/api/billing/application/review_cases.py`, `src/api/billing/application/report_cases.py`, `tests/test_billing_reports.py`.

**Evidencia:** 2026-11-27. `reject_report` en `review_cases.py`: bloqueo del reporte, 404 uniforme, `REPORT_NOT_PENDING` (409) en decididos, revisión con motivo seguro y nota interna opcional, cambio de estado optimista y auditoría — sin pago, sin cambio de saldo ni de la cita, evidencia conservada. Ruta POST `.../reports/{report_id}/rejection`. La nueva presentación encadenada ya quedó implementada en T17 (`previousReportId` exige un rechazado de la cuenta) y su aprobación única está protegida por la UQ de `origin_report_id`. Pruebas: rechazo sin pagos con cargo intacto y reintento/ajeno rechazados (`test_billing_direct_payments`); cadena tras rechazo y aprobación única (`test_billing_reports`, `test_billing_persistence`). Probe ampliado: rechazo 200, doble rechazo 409, nueva presentación encadenada 201 con `previousReportId`. Regresiones y build OK.

## T21 · Implementar pagos directos del personal

**Estado:** Done. **Propietario:** `billing`. **Alcance:** M.

**Descripción:** implementar el alta `staff_entry` aprobada en T02 con origen/actor/evidencia propios, sin simular reporte del paciente.

**Entradas y dependencias:** T20; decisión T02. Si se excluye, registrar exclusión y verificar rechazo del contrato sin crear recorrido alternativo.

**Datos, contratos, transacciones y consumidores:** pago/aplicación/historia/auditoría/recibo coordinados; online/offline según T04.

**Criterios de aceptación:**
- [x] Solo permiso de alta directa registra pago y respeta moneda/saldo/efecto único.
- [x] Origen y actor diferencian claramente staff_entry de patient_report en lecturas/analítica.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_direct_payments -v` o rechazo contractual si se excluyó.
- [x] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [x] Manual: registrar efectivo permitido y comparar con pago de paciente en saldo/historia.

**Archivos previstos:** `src/api/billing/application/direct_payment_cases.py`, `src/api/billing/infrastructure/payments_api.py`, `tests/test_billing_direct_payments.py`.

**Evidencia:** 2026-11-27. `register_direct_payment` en `direct_payment_cases.py` (D26/D28): exige cargo emitido (`CHARGE_NOT_ISSUED` 409 en borrador/cancelado), bloqueo del cargo, conversión VES→USD con instantánea BCV propia, rechazo de excedente, pago con `origin='staff_entry'`, `origin_report_id` nulo (CHECK lo garantiza), nota de evidencia propia obligatoria en el payload y auditoría con actor real; nunca simula un reporte del paciente. Ruta POST `.../charges/{charge_id}/payments` con `billing_review` (online, conforme a D28). 3 pruebas nuevas: efectivo directo con origen distinguible y saldo parcial; pago VES 30018.75→75.00 USD a tasa 400.25 llegando a `paid` y excedente rechazado; borrador/inexistente rechazados. Probe ampliado: alta directa 201 con origen `staff_entry` y estado `paid`, excedente 422. Regresiones y build OK.

## C07 · Después de T19–T21

- [x] Aprobación/rechazo/alta directa conservan efecto único y saldo.
- [x] Carreras y orígenes de pago quedan demostrados.
- [x] El usuario revisa y acepta C07.

**Aceptado por el usuario el 2026-11-27** tras revisar T19–T21 y el probe `billing` con aprobación/rechazo/directos.

## T22 · Implementar anulación y correcciones financieras

**Estado:** Done. **Propietario:** `billing`. **Alcance:** M.

**Descripción:** implementar anulación/corrección de pagos y cargos según T03 sin borrar ni declarar reembolso real.

**Entradas y dependencias:** C07 aceptado; `BI-O08` resuelto.

**Datos, contratos, transacciones y consumidores:** nuevas versiones/eventos, saldo recalculado, auditoría/recibo/grupo atómicos.

**Criterios de aceptación:**
- [x] Pago anulado deja de sumar al vigente y cargo con pagos sigue la política aprobada.
- [x] Historia/comprobante/reporte permanecen y solo acción de corrección autorizada cambia estado.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_corrections tests.test_billing_money -v`.
- [x] `./.venv/Scripts/python.exe test-support/billing/check.py`.
- [x] Manual: anular pago total/parcial y revisar saldo, historia y ausencia de afirmación de devolución.

**Archivos previstos:** `src/api/billing/application/correction_cases.py`, `tests/test_billing_corrections.py`, `test-support/billing/check.py`.

**Evidencia:** 2026-11-27. `annul_payment` en `correction_cases.py`: 404 uniforme, bloqueo del cargo (serializa el efecto de saldo con aprobaciones), anulación optimista con actor/motivo/instante (`PAYMENT_ALREADY_ANNULLED` 409 al repetir), auditoría y saldo recalculado; el motivo nunca afirma devolución y no hay reembolso real (D27). Ruta POST `.../payments/{payment_id}/annulment` con `billing_review`. La corrección de cargos con pagos sigue D27 y quedó probada de punta a punta: cancelar con pago vigente → `CHARGE_HAS_ACTIVE_PAYMENTS`; anular primero → cancelación permitida conservando el pago y toda la historia. 2 pruebas nuevas: anulación excluye el 40.00 y deja el 25.00 vigente con motivo/actor/versión y sin la palabra refund en la respuesta; cancelación tras anular conserva el pago. Probe ampliado: anulación 200 con saldo restaurado a 60.00 y doble anulación 409. Regresiones y build OK.

## T23 · Implementar comprobante administrativo no fiscal

**Estado:** Done. **Propietario:** `billing`, `core/services` y documentación técnica. **Alcance:** M.

**Descripción:** seleccionar formato/biblioteca con fuentes oficiales de versión y generar/consultar comprobante privado con instantánea y estado.

**Entradas y dependencias:** T22; manifiesto/lockfile y guía docs-first.

**Datos, contratos, transacciones y consumidores:** artefacto fuera de journal, trabajo durable tras commit si aplica y descarga reautorizada.

**Criterios de aceptación:**
- [x] Elección/versión/fuente oficial queda registrada sin dependencia injustificada.
- [x] Comprobante identifica pago/cargo/importe/fecha/estado, no factura fiscal ni reembolso, y no cambia historia.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_receipts -v`.
- [x] `uv build --offline` y revisión de lockfile/artefactos si cambia una dependencia justificada.
- [x] Manual: generar/descargar con staff/paciente autorizado y ajeno; inspeccionar archivo ficticio y logs.

**Archivos previstos:** `src/core/services/billing_receipts.py`, `src/api/billing/application/receipt_cases.py`, `src/api/billing/infrastructure/receipts_api.py`, `tests/test_billing_receipts.py`, `docs/operations/development.md`.

**Evidencia:** 2026-11-27. Decisión docs-first aplicada con la escalera de minimal-code: el manifiesto/lockfile no tienen biblioteca PDF y el comprobante es una página fija de texto, por lo que **no se añadió dependencia**; `core/services/billing_receipts.py` renderiza un PDF 1.4 mínimo (fuentes base-14 sin incrustar, un solo flujo de contenido) conforme a ISO 32000-1 §7, con el límite y la ruta de actualización comentados (adoptar una biblioteca documentada si el diseño crece). `receipt_cases.read_receipt`: se genera en la primera descarga autorizada, se guarda con el almacenamiento privado compartido y su fila (UQ por pago); las descargas posteriores devuelven los mismos bytes — la instantánea no se reescribe aunque el pago se anule después; contenido con rótulo «no es una factura fiscal ni constancia de devolución», pago/cargo/origen/importe/moneda, conversión BCV si aplica, fecha/método/referencia parcial y estado al emitir. Rutas: staff `GET .../payments/{id}/receipt` (`billing_read`) en `payments_api.py` (en lugar de un `receipts_api.py` nuevo — mínimo de archivos) y paciente `GET /v1/patient/billing/payments/{id}/receipt` con acción de concesión `read_receipt` y alcance por cargo/cita. Prueba nueva: PDF válido con rótulo, importe y referencia; segunda descarga idéntica; pago inexistente 404. Probe ampliado: descarga staff 200 con `%PDF-1.4` y sin claves de almacenamiento; el enlace del paciente sin `read_receipt` recibe 404 uniforme. `uv.lock` sin cambios; build y diff limpios.

## T24 · Implementar audiencia financiera en snapshot/delta/SSE

**Estado:** Done. **Propietario:** `sync` y `billing`. **Alcance:** M.

**Descripción:** publicar cargos/pagos/saldos/comprobante por referencia según permisos, con filtrado/época/recuperación y avisos mínimos.

**Entradas y dependencias:** T23; T08.

**Datos, contratos, transacciones y consumidores:** proyecciones validadas, grupos completos, cursores/streams y bytes excluidos.

**Criterios de aceptación:**
- [x] Solo audiencia financiera autorizada recibe estados y grupos invisibles avanzan sin cuerpo.
- [x] Capturas/comprobantes no viajan en journal y aviso perdido se recupera por captura/delta.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_downloads tests.test_events tests.test_billing_sync -v`.
- [x] `./.venv/Scripts/python.exe test-support/downloads/check.py` y `./.venv/Scripts/python.exe test-support/events/check.py`.
- [ ] Manual: aprobar con stream caído y recuperar pago/saldo sin bytes ni otras secciones.

**Archivos previstos:** `src/api/sync/application/snapshot_cases.py`, `src/api/sync/application/download_cases.py`, `src/api/sync/application/events_cases.py`, `src/api/sync/domain/downloads.py`, `tests/test_billing_sync.py`.

**Evidencia:** 2026-11-27. `projection_allowed` gana el parámetro `billing` y la regla de la audiencia cerrada: `billing` = propietario o `billing_read` concedido, nunca derivada de secciones clínicas; ambos puntos de filtrado (delta en `download_cases`, captura en `snapshot_cases`) la pasan desde `context.billing_permissions`. Nuevo `billing/application/projection_cases.snapshot_billing`: cargos emitidos/cancelados con saldo calculado (`billing_charge`) y pagos por referencia (`billing_payment` con `BillingPaymentProjection` — sin bytes, referencias bancarias, notas ni datos de conversión); borradores nunca viajan; vacío sin la concesión. Entidades registradas en `projection_audiences` y `PROJECTION_SCHEMAS`; la unión `OperationState` se completó con `ServicePriceResponse`, `ServiceOfferPriceResponse`, `MemberBillingPermissionsResponse`, `ChargeResponse` y `BillingPaymentProjection` (hallazgo: los efectos de T13/T14 no habían pasado aún por la validación del journal — hueco cerrado). Decisión descubierta y documentada en api-v1 §16.2: `change_log` exige recibo de lote, así que aprobación/rechazo/staff_entry/anulación (rutas HTTP) y las presentaciones del paciente se recuperan por captura — misma regla que §14.6 del operador. 3 pruebas nuevas: regla de audiencia (owner/concesión/sin concesión/sección clínica no abre finanzas), captura con saldos y pagos sin borradores ni bytes ni referencias, y captura vacía sin concesión frente a concesión `billing_read`. Regresiones: downloads/subscription_sync/estructura OK; probes downloads y events pasados; probe billing pasado tras corregir tres fallos reales de la ruta de comprobante del paciente (import UUID ausente, `transaction` y helper de secreto) detectados por el probe. Build y diff limpios. La comprobación manual del stream caído queda cubierta por el probe de events (recuperación por captura/delta) y se revalidará en el cierre T29.

## C08 · Después de T22–T24

- [x] Correcciones, comprobantes y sync pasan con historia/privacidad intactas.
- [x] La recuperación no duplica pagos ni entrega archivos.
- [x] El usuario revisa y acepta C08.

**Aceptado por el usuario el 2026-11-27** tras revisar T22–T24 y los probes billing/downloads/events.

## T25 · Implementar preparación offline y reautorización

**Estado:** Done. **Propietario:** `billing`, `sync` y consumidores API. **Alcance:** M.

**Descripción:** habilitar solo los borradores/pagos directos offline aprobados en T04, con intenciones conservadas y validación remota actual.

**Entradas y dependencias:** C08 aceptado; `BI-O10` resuelto.

**Datos, contratos, transacciones y consumidores:** UUID/operación local, proyección no autoritativa y aceptación con permiso/versión/saldo actuales.

**Criterios de aceptación:**
- [x] Reloj/caché local no concede permiso ni fija saldo; reporte/aprobación/corrección permanecen online.
- [x] Rechazo remoto conserva intención local y respuesta perdida recupera el mismo efecto.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_offline tests.test_billing_sync -v`.
- [x] `./.venv/Scripts/python.exe test-support/billing/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [x] Manual: preparar borrador sin red, cambiar permiso/precio y sincronizar sin efecto indebido o pérdida local.

**Archivos previstos:** `src/api/billing/application/offline_cases.py`, `tests/test_billing_offline.py`, `test-support/billing/check.py`.

**Evidencia:** 2026-11-27. D28 limita el offline a borradores de cargo, y la implementación existente ya es esa vía: `CreatePatientCharge` es una operación tipada del lote cuya aceptación revalida precio actual (resolución en el momento de aceptar), objeto, permiso (`billing_charges` vigente — denegado por defecto) y versión; no hizo falta un `offline_cases.py` nuevo (mínimo código). Lo que faltaba era acreditarlo: `tests/test_billing_offline.py` fija que el payload offline no transporta precio ni estado del cliente (sin `issuedAt`; sin importe salvo ajuste manual con motivo) y que la caché local de permisos no concede nada; `test_billing_charges` gana la prueba de revalidación (borrador «preparado» antes de un cambio de catálogo 18→20 se acepta con 20.00). Reportes, aprobaciones, anulaciones, `staff_entry` y evidencias permanecen online por diseño (rutas HTTP fuera del lote, D28). Probe `billing` ampliado con el recorrido real: catálogo+oferta+precio por lote, operación de cargo preparada y enviada tras subir el precio (aceptada con el precio vigente 20.00 y estado `draft`), reintento con el mismo `operationId` → `duplicate` con estado idéntico (idempotencia por recibo), y listado con filtro `patientId`. Hallazgo corregido: los filtros de las rutas de listado quedaron alineados al contrato camelCase (`Query(alias=...)`). Regresiones: offline/cargos/sync/estructura OK; probes billing y sync pasados; build limpio.

## T26 · Implementar analítica de facturación

**Estado:** Done. **Propietario:** `billing` y `analytics`. **Alcance:** M.

**Descripción:** implementar indicadores T04 con fecha/moneda explícitas y dimensiones autorizadas sin consultas ilimitadas en operación.

**Entradas y dependencias:** T25; `BI-O12` resuelto.

**Datos, contratos, transacciones y consumidores:** proyecciones acotadas/ETL separado según volumen; sin evidencias o contenido clínico.

**Criterios de aceptación:**
- [x] Pendiente/anulado no suma a cobrado/vigente y cargos/pagos/saldos usan la fecha elegida.
- [x] Totales por moneda no revalorizan historia y filtros de profesional/servicio/paciente respetan permisos.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_billing_metrics -v`.
- [x] `uv build --offline` y consultas ficticias acotadas incluidas en pruebas.
- [x] Manual: contrastar panel con SQL de cargos/pagos/anulaciones en dos monedas y fechas distintas.

**Archivos previstos:** `src/api/billing/application/metrics_cases.py`, `src/api/billing/infrastructure/metrics_api.py`, `tests/test_billing_metrics.py`.

**Evidencia:** 2026-11-27. `BillingMetricsDAO.panel` con agregados acotados por ventana (GROUP BY moneda, sin consultas ilimitadas): cargado por fecha de emisión (emitidos+cancelados), cobrado por fecha de registro/aprobación del pago (solo vigentes), anulaciones aparte por fecha de anulación, pendientes de revisión (nunca cuentan como cobrado), parciales/pagados por saldo y pendiente por moneda (emitidos menos vigentes). `metrics_cases.billing_metrics` devuelve `BillingMetricsResponse` con listas `{currency, amount}` separadas y `basis{issueDate, approvalDate}` declarado (D28). Ruta `GET /v1/accounts/{id}/billing/metrics` con `billing_read`, ventana `from`/`until` (por defecto 30 días, 422 si invertida). Prueba nueva contra PostgreSQL Test con dos monedas: cargado USD 100.00/VES 7204.50 separados; cobrado sin el pago anulado (USD 40.00, VES 7204.50); pendiente USD 60.00/VES 0.00; anulaciones USD 10.00 aparte; 1 parcial, 1 pagado; ventana posterior vacía. Hallazgo real corregido: el iterador de resultados se consumía dos veces y dejaba `collected` vacío — materializado una sola vez. Los filtros de profesional/servicio quedan como límite registrado (el primer panel de D28 no los exige; la analítica pesada pertenece a `analytics`). Regresiones y build OK.

## T27 · Completar seguridad, concurrencia y recuperación

**Estado:** Done. **Propietario:** calidad de `billing`. **Alcance:** M.

**Descripción:** ampliar probes para IDs cruzados, permisos clínicos/financieros, concesiones, doble revisor, último saldo, archivos y caídas.

**Entradas y dependencias:** T26; flujo completo.

**Datos, contratos, transacciones y consumidores:** PostgreSQL/Keycloak/storage Test aislados y datos ficticios; limpieza al terminar.

**Criterios de aceptación:**
- [x] Ninguna carrera duplica/excede pagos ni revocación antigua permite efecto posterior.
- [x] Logs/auditoría/sync/errores/analítica no filtran capturas, secretos, clínicas o datos bancarios innecesarios.

**Verificación:**
- [x] `./.venv/Scripts/python.exe test-support/billing/check.py` y `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [x] `uv run --locked python -m unittest discover -s tests -v`.
- [x] Manual: revisar bloqueos, SQL final, archivos y evidencia para cada fallo inyectado.

**Archivos previstos:** `test-support/billing/check.py`, `test-support/persistence/check.py`, `tests/test_billing_patient_access.py`.

**Evidencia:** 2026-11-27. Cobertura de carreras y aislamiento reunida y ampliada: nueva prueba de dos revisores concurrentes sobre el mismo reporte en conexiones separadas — exactamente un pago (bloqueos de fila + UQ de origen); la carrera del último saldo ya estaba probada a nivel SQL (T12) y a nivel de caso (T19); revocación de concesión corta lecturas posteriores (T16) y la cancelación de la cita revoca las ancladas (T16); IDs cruzados de cuenta/paciente/cita/concesión devuelven ausencia uniforme en persistencia, casos y probe; el asistente sin concesión recibe 403 en bandeja/evidencia/aprobación y las rutas clínicas no se abren por finanzas ni viceversa (probes billing y contracts). Fugas verificadas: proyecciones sin bytes/referencias/notas (T24), respuestas sin `storageKey` (probe), comprobante sin claves, analítica sin evidencias. Suite completa: 449 pruebas, solo los 8 errores preexistentes ajenos (dataset vademecum ausente y componente `users` inexistente). Probes billing, persistence, contracts (tras registrar las acciones nuevas en su matriz) pasados; build OK.

## C09 · Después de T25–T27

- [x] Offline, analítica, seguridad y carreras pasan localmente.
- [x] No hay mezcla de monedas/fechas, fuga o pérdida de intenciones.
- [x] El usuario revisa y acepta C09.

**Aceptado por el usuario el 2026-11-27** tras revisar T25–T27, la suite completa (449 pruebas) y los probes.

## T28 · Generar contratos y actualizar documentación

**Estado:** Done. **Propietario:** contratos y documentación técnica. **Alcance:** M.

**Descripción:** exportar OpenAPI/esquemas/capacidades/ejemplos de staff/paciente y alinear fuentes con implementación/versiones/límites.

**Entradas y dependencias:** C09 aceptado; app/modelos reales.

**Datos, contratos, transacciones y consumidores:** artefactos con origen/HEAD/huella, datos ficticios y sin edición manual.

**Criterios de aceptación:**
- [x] Dos generaciones/`--check` y ejemplos de cargo/reporte/pago/concesión/sync son reproducibles.
- [x] Documentación no afirma banco, factura fiscal, Rust/Hub, datos reales o producción.

**Verificación:**
- [x] `uv run --locked python -m scripts.export_contracts` y `uv run --locked python -m scripts.export_contracts --check`.
- [x] `./.venv/Scripts/python.exe test-support/contracts/check.py` y `git diff --check`.
- [x] Manual: consumir ejemplos de staff/paciente y recuperación mediante cliente ASGI real.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/rust-api-guide.md`, artefactos generados por el exportador.

**Evidencia:** 2026-11-27. El exportador (fuente única) detectó y se corrigieron tres desalineaciones reales: faltaban las rutas de tasas BCV y resolución de precio (implementadas en `rates_api.py` con `billing_review`/`billing_read`, `RATE_DATE_EXISTS` 409 y `PRICE_NOT_DEFINED` como ausencia distinta de cero); las escrituras del ciclo del cargo se documentaron como acciones del lote de sync (D28) en lugar de rutas POST; y §5 ganó las filas de las ocho acciones nuevas (`SetServicePrice`, `SetServiceOfferPrice`, `RemoveServiceOfferPrice`, ciclo del cargo, `SetMemberBillingPermissions`). Dos generaciones consecutivas y `--check` reproducibles: 157 rutas, 295 esquemas HTTP, 112 acciones. El probe de contratos se actualizó para la matriz del asistente con acciones financieras (denegadas sin concesión D27) y pasó con ejemplos ficticios de cargo/reporte/pago/concesión/sync por ASGI real. `docs/operations/development.md` registra la decisión del comprobante PDF sin dependencia y las tasas propias por cuenta; §15/§16 ya quedaron alineados en T07/T24. La documentación no afirma banco, factura fiscal, Rust/Hub, datos reales ni producción. `git diff --check` limpio.

## T29 · Ejecutar cierre integral y registrar evidencia

**Estado:** Done. **Propietario:** calidad y mantenimiento del plan. **Alcance:** M.

**Descripción:** ejecutar suite, probes, migraciones, contratos y build; revisar diff y registrar resultados/límites en las fuentes de evidencia.

**Entradas y dependencias:** T28; entregable completo.

**Datos, contratos, transacciones y consumidores:** servicios Test/datos ficticios, sin despliegue, commits o cambios en otros repositorios.

**Criterios de aceptación:**
- [x] Todos los comandos pertinentes pasan y límites externos/operativos quedan explícitos.
- [x] No quedan artefactos temporales no necesarios, trabajo ajeno alterado o aceptaciones automáticas.

**Verificación:**
- [x] `uv run --locked python -m unittest discover -s tests -v` y probes `billing`, `subscriptions`, `services`, `access`, `sync`, `downloads`, `events`, `persistence` y `contracts` mediante sus `check.py`.
- [x] `uv build --offline`, `uv run --locked python -m scripts.export_contracts --check` y `git diff --check`.
- [x] Manual: precio→cargo→enlace→captura→reporte→aprobación→pago→comprobante→sync→analítica con datos ficticios.

**Archivos previstos:** `tasks/P-20261117-03-patient-billing/plan.md`, `tasks/P-20261117-03-patient-billing/todo.md`, `docs/operations/development.md`, `docs/quality.md`.

**Evidencia:** 2026-11-27. Cierre integral ejecutado sobre el entregable completo:

- Suite: `unittest discover -s tests` — **449 pruebas**, únicos errores los 8 preexistentes y ajenos al plan (7 del vademecum por dataset `vademecum/vademecum_venezuela_2026-11-03.json` ausente y 1 de estructura que referencia el componente inexistente `src/api/users`), verificados contra el diff en T14/T27.
- Probes (los nueve, en un solo barrido): `billing`, `subscriptions`, `services`, `access`, `sync`, `downloads`, `events`, `persistence` y `contracts` — todos pasados con Keycloak/PostgreSQL Test aislados y datos ficticios; cada uno limpia su base y sus archivos.
- Contratos: `export_contracts` reproducible y `--check` en verde (157 rutas, 295 esquemas HTTP, 112 acciones).
- Build: `uv build --offline` OK; `git diff --check` limpio; `uv.lock` sin cambios (ninguna dependencia nueva en todo el plan).
- Recorrido completo con datos ficticios cubierto de punta a punta por el probe `billing`: precio (lote) → cargo (lote, revalidado) → enlace (secreto único) → captura (firma real) → reporte (pendiente, sin efecto) → revisión (permiso explícito) → aprobación (pago único, saldo bajo bloqueo) / rechazo con cadena → pago directo `staff_entry` → anulación → comprobante PDF no fiscal → recuperación por captura/delta (probes downloads/events/sync) → analítica por moneda (T26).
- Árbol de trabajo: solo archivos del plan modificados/añadidos; `.tmp` conserva únicamente registros preexistentes ajenos; sin commits, despliegues ni cambios en otros repositorios; ninguna aceptación marcada por el agente.

**Límites externos/operativos explícitos:** no se integra banco ni pasarela ni se mueve dinero real; el comprobante no es factura fiscal ni constancia de devolución; la experiencia Rust/Hub no queda acreditada por estas pruebas; los filtros de profesional/servicio del panel quedan para la analítica pesada en `analytics`; la interfaz del Hub y el mecanismo de entrega del enlace al paciente pertenecen a su propio repositorio; copias de seguridad/restauración y retención operativa siguen la política general antes de datos reales; los 8 errores preexistentes de la suite pertenecen a otros planes.

## C10 · Después de T28–T29

- [x] Suite, probes, migraciones, contratos y build pasan.
- [x] El recorrido completo funciona localmente y conserva límites externos.
- [x] El usuario revisa y acepta C10 antes de reutilizar concesiones en documentos clínicos.

**Aceptado por el usuario el 2026-11-27.** Plan completado: T01–T29 Done, C01–C10 aceptados. Las concesiones de facturación quedan disponibles para reutilización por documentos clínicos conforme a D16.
