# Lista de tareas: P-20261117-02-account-subscriptions

**Plan:** [plan.md](plan.md). **Actualizado:** 2026-11-17. **Estado del plan:** Approved.

Todas las tareas están Todo. La ejecución requiere C06 aceptado del plan de autorización. Las decisiones de usuario obtenidas en T01–T04 se registran antes del trabajo dependiente; no se marcan por este documento.

## T01 · Cerrar planes, precios y asientos

**Estado:** Done. **Propietario:** producto y `subscriptions`. **Alcance:** M.

**Descripción:** resolver precios USD por plan/periodicidad, pertenencias que consumen asiento, límites numéricos y tratamiento del exceso al reducir plan.

**Entradas y dependencias:** autorización C06 aceptada; `SU-O02`, `SU-O05` y `SU-O08`.

**Datos, contratos, transacciones y consumidores:** decisiones documentales; no cambia datos, contratos o consumidores todavía.

**Criterios de aceptación:**
- [x] Los tres planes tienen precios 30 días/año y límites explícitos, sin diferencias funcionales.
- [x] Se define cómputo de propietario/asistentes/profesionales/invitaciones/dispositivos y exceso sin desactivación automática.

**Verificación:**
- [x] Revisión de ejemplos ficticios de ocupación, reactivación y reducción de plan.
- [x] `git diff --check` y validación de enlaces locales.
- [x] Manual: recorrer última invitación disponible y una cuenta sobre el límite con las reglas decididas.

**Archivos previstos:** `docs/account-subscriptions.md`, `docs/decisions.md`, `tasks/P-20261117-02-account-subscriptions/todo.md`.

**Evidencia:** 2026-11-26. El usuario decidió en T01: precios USD 18/100, 24/240 y 75/500 (30 días/año) para independiente, consultorio y centro; cómputo §8.1 confirmado (pertenencia humana activa única, incluido propietario; profesional repetido no duplica); límites 2/5/20 asientos; exceso §8.4 confirmado sin desactivación automática. Registrado en [D21](../../docs/decisions.md) y en `account-subscriptions.md` §§2, 7.1, 8.1, 8.4 y 26 (`SU-O02`, `SU-O05`, `SU-O08` cerradas). `git diff --check` limpio (solo avisos LF/CRLF) y ancla `#d21--planes-precios-y-asientos-de-suscripciones-t01` verificada contra el encabezado. Recorrido manual: consultorio con 5 asientos ocupados rechaza la sexta aceptación/reactivación; independiente con 2 asientos que baja de un plan mayor conserva a ambos integrantes, bloquea nuevas incorporaciones y avisa al propietario sin revocar permisos clínicos.

## T02 · Cerrar BCV, monedas y periodos

**Estado:** Done. **Propietario:** producto y dominio financiero. **Alcance:** M.

**Descripción:** resolver fecha/fuente BCV, días sin publicación, monedas aceptadas, significado de un año e inicio inicial/renovación tardía.

**Entradas y dependencias:** T01; `SU-O03`, `SU-O04` y `SU-O06`.

**Datos, contratos, transacciones y consumidores:** reglas documentales con ejemplos ficticios; sin integración BCV automática.

**Criterios de aceptación:**
- [x] Cotización, redondeo y tasa histórica tienen una sola regla para todos los recorridos.
- [x] Periodos inicial, anticipado, tardío, anual y 29 de febrero tienen resultados explícitos.

**Verificación:**
- [x] Cálculo manual de ejemplos USD/VES y fechas límite con `Decimal` de biblioteca estándar.
- [x] `git diff --check` y enlaces BCV/ISO/PostgreSQL verificados.
- [x] Manual: revisar una renovación antes y después del vencimiento sin pérdida/duplicación de días.

**Archivos previstos:** `docs/account-subscriptions.md`, `docs/decisions.md`, `tasks/P-20261117-02-account-subscriptions/todo.md`.

**Evidencia:** 2026-11-26. El usuario decidió en T02: tasa BCV de la fecha del pago verificada (tasa publicada más reciente anterior si no hay publicación; sin aprobación automática con tasa del cliente si la fecha no es verificable); monedas de pago VES y USD; año civil en `America/Caracas` con 29 de febrero → 28 de febrero; inicio de periodos según §11 (inicial y tardía en aprobación del servidor, anticipada desde `endsAt` sin perder días). Registrado en [D22](../../docs/decisions.md) y en `account-subscriptions.md` §§9.3, 11.3, 11.5 y 26 (`SU-O03`, `SU-O04`, `SU-O06` cerradas). Cálculos ficticios con `Decimal`/`ROUND_HALF_UP`: USD 18,00 × 400,25 = VES 7.204,50; USD 100,00 × 400,25 = VES 40.025,00; USD 24,00 × 400,25 = VES 9.606,00; USD 500,00 × 123,456 = VES 61.728,00. Fechas: 2027-03-10 → 2028-03-10; 2028-02-29 → 2029-02-28; 30 días desde 2027-01-20 → 2027-02-19. Renovación anticipada conserva días (inicio = `endsAt` previo); tardía inicia en aprobación sin duplicar ni retrotraer. `git diff --check` limpio; enlaces BCV/ISO/PostgreSQL ya presentes en §27 sin cambios.

## C01 · Después de T01–T02

- [x] Las decisiones `SU-O02`–`SU-O06` y `SU-O08` están registradas.
- [x] Ejemplos y documentos no contienen valores ambiguos o supuestos.
- [x] El usuario revisa y acepta C01. **Aceptado el 2026-11-26.**

## T03 · Cerrar operador y canal administrativo

**Estado:** Done. **Propietario:** producto, seguridad y operación. **Alcance:** M.

**Descripción:** decidir alta, autenticación, recuperación, revocación, acciones y canal del operador sin convertirlo en miembro o administrador clínico.

**Entradas y dependencias:** C01 aceptado; `SU-O01` y `SU-O12`.

**Datos, contratos, transacciones y consumidores:** diseño de actor/canal; no se deduce módulo del Hub ni sesión del personal.

**Criterios de aceptación:**
- [x] El ciclo completo del operador y sus acciones de catálogo/revisión están definidos.
- [x] Recuperación/revocación y ausencia de acceso a pacientes/clínica son explícitas.

**Verificación:**
- [x] Revisión de amenazas: operador revocado, token robado, cuenta cruzada y recuperación.
- [x] `git diff --check` y enlaces de las fuentes oficiales necesarias para el mecanismo elegido.
- [x] Manual: recorrer alta→revisión→revocación→intento de lectura clínica denegada.

**Archivos previstos:** `docs/account-subscriptions.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/decisions.md`.

**Evidencia:** 2026-11-26. El usuario decidió en T03: autenticación del operador en Keycloak con identidad separada del personal y credencial opaca sin vencimiento revocable en API (patrón de dispositivos); alta/recuperación/revocación como **componente de la propia API** gestionado por operadores con acción separada (decisión expresa del usuario: "no solo un script, gestionable"), con alta inicial por flujo administrativo de despliegue y recuperación = revocar + emitir nueva credencial; canal en rutas de la misma aplicación FastAPI. Registrado en [D23](../../docs/decisions.md), `account-subscriptions.md` §§6.3 y 26 (`SU-O01`, `SU-O12` cerradas) y nueva sección en `access-design.md`. Revisión de amenazas: operador revocado pierde acceso al revocar la credencial en API aunque Keycloak siga activo; credencial robada se revoca sin recuperar secretos y la emisión exige nueva autenticación Keycloak; el operador no tiene pertenencia ni rol de cuenta, por lo que una cuenta cruzada no le concede nada y sus rutas no exponen clínica; la recuperación nunca reutiliza la credencial anterior. `git diff --check` limpio; no se elige dependencia nueva (reutiliza Keycloak y el patrón de credenciales existente), por lo que no aplican fuentes oficiales adicionales en esta tarea documental.

## T04 · Cerrar gracia, archivos y excepciones de pago/cambio

**Estado:** Done. **Propietario:** producto, operación y seguridad. **Alcance:** M.

**Descripción:** resolver gracia/suspensión offline, límites/retención de capturas, pagos parciales/excedentes/varios periodos y prorrateo/cambio de plan.

**Entradas y dependencias:** T03; `SU-O07` y `SU-O09`–`SU-O11`.

**Datos, contratos, transacciones y consumidores:** políticas documentales; sin almacenamiento o enforcement implementado.

**Criterios de aceptación:**
- [x] Funciones permitidas en gracia/suspensión y comportamiento offline están cerrados sin borrado.
- [x] Archivos y excepciones de pago/cambio tienen reglas de aceptación/rechazo y conservación.

**Verificación:**
- [x] Matriz de casos vencimiento con/sin red, excedente, duplicado sospechoso y cambio anticipado.
- [x] `git diff --check` y referencias OWASP/retención revisadas.
- [x] Manual: seguir una cuenta vencida que reporta, renueva y recupera sin perder intenciones/datos.

**Archivos previstos:** `docs/account-subscriptions.md`, `docs/decisions.md`, `docs/quality.md`.

**Evidencia:** 2026-11-26. El usuario decidió en T04: gracia de 7 días con servicio normal y suspensión posterior con lectura/exportación y renovación siempre disponibles, sin borrado ni revocación de identidades; offline, la proyección del servidor comunica el fin de gracia y el reloj local no extiende vigencia; capturas JPG/PNG/PDF de máximo 5 MB, una por reporte, con retención mientras la cuenta exista y eliminación solo por proceso administrativo trazado; solo se aprueba pago completo (parcial/excedente se rechaza con motivo, un reporte por periodo, coincidencias de referencia solo advierten); cambio de plan sin prorrateo, aplicado al siguiente periodo aprobado conservando el tiempo pagado. Registrado en [D24](../../docs/decisions.md) y en `account-subscriptions.md` §§9.5, 13.1, 13.3, 16.2, 17.3 y 26 (`SU-O07`, `SU-O09`, `SU-O10`, `SU-O11` cerradas; las doce `SU-Oxx` quedan resueltas). Matriz de casos recorrida: vencimiento con red (gracia 7 días y aviso), sin red (proyección con fin de gracia, reloj local sin efecto), excedente (rechazo con motivo, sin crédito), duplicado sospechoso (advertencia al operador, sin rechazo automático), cambio anticipado (siguiente periodo, sin prorrateo, asientos según D21). `git diff --check` limpio; referencias OWASP de §27 sin cambios (la validación concreta de archivos se implementa en T17 con fuentes oficiales).

## T05 · Diseñar físicamente núcleo de suscripciones y asientos

**Estado:** Done. **Propietario:** `subscriptions/repository` y esquema físico. **Alcance:** M.

**Descripción:** incorporar a la fuente única planes/versiones, suscripciones/periodos y reglas de asientos con tipos, claves, intervalos e índices.

**Entradas y dependencias:** T04; decisiones T01/T02.

**Datos, contratos, transacciones y consumidores:** diseño físico, sin migración; periodos `[start,end)`, decimal y relaciones por cuenta.

**Criterios de aceptación:**
- [x] Versiones de plan, una aprobación→un periodo y no solape tienen restricciones propuestas.
- [x] Asientos reutilizan pertenencias y las consultas/índices cubren vigencia/cuenta.

**Verificación:**
- [x] Revisión cruzada de cada regla conceptual con columna/FK/CHECK/UQ/índice propuesto.
- [x] `git diff --check` y enlaces PostgreSQL 18 pertinentes.
- [x] Manual: evaluar SQL conceptual de dos aprobaciones y última plaza concurrente.

**Archivos previstos:** `docs/database-schema.md`, `docs/account-subscriptions.md`.

**Evidencia:** 2026-11-26. Nueva sección 17 de `database-schema.md` con cuatro tablas: `subscription_plans` (identidad estable, UQ `code` cerrado, retiro sin borrado), `subscription_plan_versions` (filas inmutables, UQ `(plan_id, version)`, `numeric(12,2)` exacto, valores iniciales D21), `account_subscriptions` (UQ `account_id`, FK a versión, CHECK de cinco estados, `version` optimista y bloqueo `FOR UPDATE` como punto de serialización) y `subscription_periods` (intervalo `[starts_at, ends_at)`, UQ `(subscription_id, sequence)`, no solape por restricción de exclusión `tstzrange` que requiere `btree_gist`). Regla de asientos sin tabla nueva: cómputo desde `account_memberships` activas según D21, comprobado en la misma transacción con el bloqueo de la suscripción; sin índices nuevos sin caso medido. La FK/UQ de origen del periodo hacia la aprobación queda explícitamente para T06 con las tablas de revisión. Revisión cruzada: una suscripción por cuenta (UQ), versión congelada por periodo (FK), una aprobación→un periodo (UQ de origen en T06 + bloqueo), no solape (exclusión), dinero exacto (numeric), estados cerrados (CHECK), historia sin borrado (RESTRICT, sin cascada). SQL conceptual evaluado: dos aprobaciones concurrentes se serializan en el `FOR UPDATE` de `account_subscriptions` y la segunda recibe duplicado/conflicto de versión; dos aceptaciones por la última plaza bloquean la misma fila y solo una inserta la pertenencia. `git diff --check` limpio; fuentes PostgreSQL 18 ya referenciadas en §2 y §27 de la especificación (restricciones, índices parciales, exclusión/btree_gist a verificar en T12 contra la versión instalada).

## C02 · Después de T03–T05

- [x] Operador y políticas pendientes tienen decisiones explícitas.
- [x] El núcleo físico cubre dinero, intervalos, asientos e historia.
- [x] El usuario revisa y acepta C02. **Aceptado el 2026-11-26.**

## T06 · Diseñar físicamente tasas, reportes, revisiones y evidencias

**Estado:** Done. **Propietario:** `subscriptions/repository` y seguridad documental. **Alcance:** M.

**Descripción:** completar el diseño físico de declaración/verificación, tasas BCV, referencias privadas e historia de revisión.

**Entradas y dependencias:** C02 aceptado; T02/T04.

**Datos, contratos, transacciones y consumidores:** diseño sin bytes en PostgreSQL/sync; referencias por cuenta/reporte y datos verificados separados.

**Criterios de aceptación:**
- [x] Estado/versión, una sola aprobación efectiva y referencia parcial no única están protegidos.
- [x] Evidencia conserva metadatos mínimos y nunca URL pública o contenido en auditoría.

**Verificación:**
- [x] Matriz de transiciones/rechazo/nueva presentación contra restricciones propuestas.
- [x] `git diff --check` y enlaces OWASP/PostgreSQL.
- [x] Manual: seguir reporte pendiente→aprobado/rechazado→nueva presentación sin reescritura.

**Archivos previstos:** `docs/database-schema.md`, `docs/architecture.md`.

**Evidencia:** 2026-11-26. Nueva sección 18 de `database-schema.md` con seis tablas: `platform_operators` (identidad separada, UQ issuer/subject, estado active/revoked), `platform_operator_credentials` (huella UQ, `revoked_at`, recuperación = revocar + emitir), `bcv_exchange_rates` (UQ `rate_date`, `numeric(18,6)`, fuente y operador registrante), `payment_reports` (declarados inmutables, FK compuesta `(subscription_id, account_id)` contra UQ nueva de `account_subscriptions` para no cruzar cuentas, referencia de 4 dígitos como texto sin unicidad, `previous_report_id` para nueva presentación, índices de lista propia y bandeja), `payment_report_evidence` (UQ `report_id` — una captura por reporte D24 —, UQ `storage_key` interno, CHECK de tipos JPG/PNG/PDF y 5 MB, sha256; sin bytes en la base) y `subscription_reviews` (UQ `report_id` = una sola decisión, datos verificados separados, CHECK de coherencia aprobación/rechazo, FK a tasa). `subscription_periods` recibe `origin_review_id` NN con UQ (una aprobación → como máximo un periodo). Matriz recorrida: pendiente→aprobado (coherencia de verificados + UQ origen), pendiente→rechazado (motivo obligatorio, suscripción sin cambio), rechazado→nueva presentación (fila nueva con `previous_report_id`, original intacto), doble aprobación concurrente (bloqueo + version + UQ `report_id` como defensa final). `git diff --check` limpio tras rehacer un primer volcado truncado del heredoc (se reescribió la sección completa con la herramienta de archivos); enlaces OWASP/PostgreSQL de §27 sin cambios.

## T07 · Diseñar contratos HTTP, operaciones y acceso

**Estado:** Done. **Propietario:** `subscriptions`, `accounts`, `sync` y contratos. **Alcance:** M.

**Descripción:** fijar rutas/operaciones/modelos, acciones del catálogo RBAC/ABAC, audiencias y errores sin exponer datos de otras cuentas.

**Entradas y dependencias:** T06; catálogo de autorización implementado.

**Datos, contratos, transacciones y consumidores:** diseño camelCase/page-shows, operaciones online, resultados idempotentes y sync mínimo.

**Criterios de aceptación:**
- [x] Cuenta, operador y casos internos tienen contratos/permisos completos sin acceso clínico.
- [x] Aprobación/rechazo, evidencia, periodos y recuperación definen transacción/versiones/errores.

**Verificación:**
- [x] Revisión de cobertura de todos los casos de uso §20 de la especificación.
- [x] `git diff --check` y validación de enlaces/anclas.
- [x] Manual: recorrer respuesta perdida y objeto ajeno en presentación/aprobación/descarga.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/contracts.md`.

**Evidencia:** 2026-11-26. Nueva sección 14 de `api-v1.md`: 9 rutas de cuenta bajo `A/subscription*` (consulta, cotización, reportes con evidencia multipart, cambio de plan, cancelación; todas del propietario, escrituras online con `operationId` idempotente fuera del lote de sync), 15 rutas de operador bajo `/v1/operator` con acciones de plataforma `review`/`catalog`/`rates`/`operators` (credencial, bandeja paginada, detalle, evidencia, aprobación, rechazo, tasas, catálogo versionado, gestión de operadores), 10 modelos públicos con importes como texto decimal y `referenceLast4` de cuatro dígitos, 7 códigos de error específicos (incluidos `SUBSCRIPTION_SUSPENDED` 403 distinguible de credencial inválida y `PAYMENT_MISMATCH` 422 que obliga al rechazo según D24) y la proyección de sync mínima por audiencia sin reportes/tasas/evidencias. Cobertura §20: cuenta (consultar, cotizar, presentar, listar/detallar, descargar evidencia, cambio/cancelación) y operador (bandeja, detalle/evidencia, tasa, aprobar, rechazar, historia, catálogo) cubiertos; casos internos (disponibilidad, asientos, proyección, aviso) quedan como casos de uso sin ruta pública. Actualizados `architecture.md` (fila `subscriptions` en la tabla de componentes), `access-design.md` (sección de acceso de suscripciones: propietario en cuenta, operador con acciones de plataforma sin acceso clínico) y `contracts.md` (fuente única del diseño). Recorridos manuales: respuesta perdida al presentar/aprobar se recupera con el mismo `operationId` y `duplicate`; objeto ajeno devuelve 404 antes de revelar situación comercial en presentación, aprobación y descarga. `git diff --check` limpio; anclas y enlaces nuevos verificados contra los encabezados D21–D24 y §§17–18 del esquema.

## T08 · Implementar dominio de dinero, BCV y periodos

**Estado:** Done. **Propietario:** `subscriptions/domain`. **Alcance:** M.

**Descripción:** implementar valores monetarios, tasa/fuente, redondeo y funciones puras de inicio/fin de periodos conforme a T02.

**Entradas y dependencias:** C02 aceptado; T07 define adaptadores, sin depender de ellos.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/red; `Decimal`, zona IANA e instantes finitos.

**Criterios de aceptación:**
- [x] USD/VES, redondeo y conservación de tasa producen resultados exactos sin NaN/infinito.
- [x] 30 días, anual, anticipado/tardío y 29 de febrero cumplen los ejemplos aprobados.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_money -v`.
- [x] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [x] Manual: imprimir cotizaciones/periodos ficticios y comparar cada cifra/fecha con T02.

**Archivos previstos:** `src/api/subscriptions/domain/money.py`, `src/api/subscriptions/domain/periods.py`, `tests/test_subscription_money.py`.

**Evidencia:** 2026-11-26. Nuevo componente `src/api/subscriptions/domain` con `money.py` (`Money` con `Decimal` exacto de máximo dos decimales y moneda `USD`/`VES`; `BcvRate` con tasa positiva de hasta seis decimales, fecha y fuente; `usd_to_ves` con redondeo único `ROUND_HALF_UP` al total, regla `ROUNDING_RULE` exportada; rechazo de NaN/infinito/negativos/ceros y de monedas ajenas) y `periods.py` (`ServicePeriod`, `add_civil_year` con 29-feb→28-feb, `period_end` para 30 días y año civil evaluado en `ZoneInfo("America/Caracas")` conservando la hora local, `next_period_start` con renovación anticipada desde `endsAt` y tardía en la aprobación, rechazo de instantes naive). 11 pruebas nuevas en `tests/test_subscription_money.py` cubren los ejemplos de T02 (18,00×400,25=7.204,50; 500,00×123,456=61.728,00; redondeo half-up 2,675→2,68), 30 días frente a mes calendario (31-ene + 30 días = 2-mar), año civil, ambos casos de 29 de febrero según la hora local en Caracas, anticipada sin pérdida de días y tardía sin retroactividad. Dos expectativas iniciales del test de bisiesto estaban mal calculadas por el autor (no el código); corregidas tras verificar la conversión UTC↔Caracas a mano. `tests.test_subscription_money` + `tests.test_project_structure`: 14 pruebas OK. `uv build --offline` exitoso. Comparación manual contra T02: cada cifra y fecha del test coincide con la evidencia registrada en T02.

## C03 · Después de T06–T08

- [x] Diseño físico/HTTP cubre revisión, evidencia, acceso y recuperación.
- [x] Dominio monetario/temporal pasa todos los ejemplos aprobados.
- [x] El usuario revisa y acepta C03. **Aceptado el 2026-11-26.**

## T09 · Implementar dominio de planes, suscripciones y asientos

**Estado:** Done. **Propietario:** `subscriptions/domain`. **Alcance:** M.

**Descripción:** implementar modelos de catálogo/versiones, estados de suscripción y función pura de cómputo/límite de asientos.

**Entradas y dependencias:** C03 aceptado; T01/T02.

**Datos, contratos, transacciones y consumidores:** esquemas base y reglas puras; no duplica pertenencias ni importa SQL.

**Criterios de aceptación:**
- [x] Los tres planes comparten funciones y solo portan precio/asientos versionados.
- [x] Cómputo/exceso/transiciones siguen T01 y deniegan combinaciones inválidas.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_domain -v`.
- [x] `uv run --locked python -m unittest tests.test_accounts tests.test_subscription_domain -v`.
- [x] Manual: evaluar miembros activos/inactivos, profesional repetido, invitación y exceso.

**Archivos previstos:** `src/api/subscriptions/domain/plans.py`, `src/api/subscriptions/domain/subscriptions.py`, `tests/test_subscription_domain.py`.

**Evidencia:** 2026-11-26. `plans.py` con `PlanCode` cerrado (independent/small_practice/medical_center), `PlanVersion` inmutable (asientos y precios `Decimal` USD de dos decimales, sin matriz de funciones), `INITIAL_PLAN_VERSIONS` con los valores D21 (2/18/100, 5/24/240, 20/75/500) y `price_for` por periodicidad. `subscriptions.py` con `SeatUsage` (disponible = max(0, límite−uso), `can_add` falso en el límite y sobre el límite sin desactivar a nadie, D21) y `commercial_availability` (etiqueta + fechas del servidor: activa hasta el fin exclusivo, gracia de 7 días D24, suspensión después; cancelada y pendiente independientes de fechas; rechazo de `now` naive). `GRACE_DAYS` vive una sola vez en `subscriptions.py` (se retiró el duplicado de `periods.py`). 13 pruebas nuevas; `tests.test_subscription_domain` + `tests.test_accounts` + `tests.test_project_structure`: 20 pruebas OK. Manual: pertenencia inactiva o invitación pendiente no entra en `used` (el cómputo llega como entero desde `account_memberships` activas), profesional repetido cuenta una vez por pertenencia única, exceso bloquea altas sin tocar miembros.

## T10 · Implementar dominio de reportes y revisión

**Estado:** Done. **Propietario:** `subscriptions/domain`. **Alcance:** M.

**Descripción:** implementar payloads/respuestas de reportes, datos declarados/verificados, evidencia y transiciones pending/approved/rejected.

**Entradas y dependencias:** T09; contratos T07.

**Datos, contratos, transacciones y consumidores:** modelos estrictos, cuatro dígitos como texto, referencias privadas y sin bytes.

**Criterios de aceptación:**
- [x] Presentar no cambia suscripción y solo operador puede decidir según tipo de actor.
- [x] Rechazo/nueva presentación y duplicados conservan historia y estados válidos.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_reports -v`.
- [x] `uv run --locked python -m unittest tests.test_project_structure tests.test_subscription_reports -v`.
- [x] Manual: validar referencias con ceros iniciales, captura ausente/presente y datos declarados frente a verificados.

**Archivos previstos:** `src/api/subscriptions/domain/reports.py`, `src/api/subscriptions/domain/reviews.py`, `tests/test_subscription_reports.py`.

**Evidencia:** 2026-11-26. `reports.py`: `DeclaredPayment` (inmutable tras presentar; `reference_last4` texto de exactamente 4 dígitos con ceros iniciales y sin unicidad; nota/método no vacíos), `PaymentReport` (nace `pending`, versión 1, vínculo `previous_report_id`), `EvidenceMetadata` (JPG/PNG/PDF, 1 byte–5 MB, sha256 hex; D24) y transiciones puras `decide` (un reporte decidido no se reabre), `ensure_pending` y `resubmission` (nueva presentación vinculada que vuelve a `pending` conservando el original). `reviews.py`: `VerifiedPayment` separado de la declaración, `SubscriptionReview` con coherencia (aprobar exige datos verificados y tasa BCV si el pago es VES; rechazar exige motivo), `apply_review` (una revisión, un efecto; verifica pertenencia del reporte) y `ensure_full_payment` (solo el importe exacto debido aprueba; parcial y excedente producen `PaymentMismatchError`, D24 — en una primera versión el excedente pasaba y se corrigió al releer D24). 12 pruebas nuevas; `tests.test_subscription_reports` + `tests.test_project_structure`: OK. Manual: `0071` conserva ceros y dos reportes pueden compartirla; captura ausente es válida (modalidad manual) y presente valida tipo/tamaño/huella; declarados y verificados viven en modelos separados sin sobrescritura.

## T11 · Implementar identidad y contexto limitado del operador

**Estado:** Done. **Propietario:** `authorization` y `subscriptions`. **Alcance:** M.

**Descripción:** implementar el mecanismo T03 con alta/recuperación/revocación y acciones cerradas de plataforma, sin rol de cuenta.

**Entradas y dependencias:** T10; T03 y fuentes oficiales del mecanismo seleccionado.

**Datos, contratos, transacciones y consumidores:** credenciales/identidad según diseño, auditoría y transacciones coordinadas; sin sesiones API del personal añadidas.

**Criterios de aceptación:**
- [x] Operador vigente accede solo a acciones aprobadas y revocado pierde acceso.
- [x] Operador no lee pacientes/clínica ni se convierte en owner/assistant.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_operator tests.test_access_credentials -v`.
- [x] `./.venv/Scripts/python.exe test-support/access/check.py` y `uv build --offline`.
- [x] Manual: autenticar, revocar y probar revisión permitida frente a lectura clínica denegada.

**Archivos previstos:** módulos `src/api/subscriptions/{domain,application,repository,infrastructure}/` y `tests/test_subscription_operator.py`, máximo cinco archivos según mecanismo T03.

**Evidencia:** 2026-11-26. `domain/operators.py`: `PlatformOperator` (sin cuenta, rol ni secciones clínicas; `actions` como conjunto cerrado no vacío de `review`/`catalog`/`rates`/`operators`), `ensure_operator_action` (recomprueba estado del operador, credencial y acción en cada petición) y `revoke_operator` (terminal, con versión). La credencial reutiliza `core/services/device_tokens` (secreto de 256 bits, solo huella persistida, `ngt_<uuid7>.<secreto>`), sin dependencia nueva ni mecanismo paralelo. Ajuste de diseño detectado en T11: `platform_operators` no tenía dónde vivir el conjunto de acciones; se añadió la columna `actions text[]` con CHECK a `database-schema.md` §18.1 (subconjunto no vacío de las cuatro acciones). Persistencia e HTTP del operador llegan con T13/T14/T19 según el orden del plan; esta tarea entrega dominio y mecanismo de credencial. 7 pruebas nuevas; `tests.test_subscription_operator` + `tests.test_access_credentials` + `tests.test_project_structure`: 20 pruebas OK. Probe real: `test-support/access/check.py` pasó contra PostgreSQL Test y Keycloak Test reales ("Access checks passed"); el certificado fixture de Keycloak estaba expirado y se regeneró con el procedimiento del README (keytool, 30 días, solo loopback) antes de ejecutar. `uv build --offline` exitoso. Manual: operador con solo `review` es denegado en `catalog`/`rates`/`operators`; revocado pierde acceso aunque la credencial sea válida; credencial revocada deniega a operador activo; el modelo no tiene campos con los que autorizar clínica.

## C04 · Después de T09–T11

- [x] Reglas de dominio y operador pasan pruebas de alcance.
- [x] No existe acceso clínico o rol de cuenta implícito.
- [x] El usuario revisa y acepta C04. **Aceptado el 2026-11-26.**

## T12 · Implementar persistencia del núcleo comercial

**Estado:** Done. **Propietario:** `subscriptions/repository` y migraciones. **Alcance:** M.

**Descripción:** crear migración, modelos SQLAlchemy y DAOs para planes/versiones, suscripciones/periodos con restricciones y privilegios mínimos.

**Entradas y dependencias:** C04 aceptado; T05.

**Datos, contratos, transacciones y consumidores:** DAOs derivados commit=False; FK/CHECK/UQ/exclusión y transacciones del caso.

**Criterios de aceptación:**
- [x] Migración up/down/reapply conserva integridad, moneda e intervalos sin solape.
- [x] Rol operativo no tiene DDL ni escritura fuera de DAOs/casos previstos.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_persistence -v`.
- [x] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [x] Manual: inspeccionar SQL de periodos solapados, origen duplicado y rollback de una revisión fallida.

**Archivos previstos:** `migrations/versions/<revisión>_subscriptions_core.py`, `src/api/subscriptions/repository/models.py`, `src/api/subscriptions/repository/dao.py`, `tests/test_subscription_persistence.py`.

**Evidencia:** 2026-11-26. Migración `20261126_01_subscriptions_core.py` (down_revision 20261122_01) con las cuatro tablas de §17: CHECK UUIDv7/estados/moneda USD/importes positivos/`numeric(12,2)`, UQ `code`, UQ `(plan_id,version)`, UQ `account_id`, UQ `(subscription_id,sequence)` y exclusión `EXCLUDE USING gist (subscription_id WITH =, tstzrange(starts_at,ends_at) WITH &&)` (btree_gist ya existente). Grants mínimos: SELECT/INSERT/UPDATE en plans y account_subscriptions, SELECT/INSERT en versions y periods; sin DELETE ni DDL. Modelos SQLAlchemy espejo en `repository/models.py` (la exclusión vive solo en la migración, anotado) y DAOs `commit=False` en `repository/dao.py` (by_code, all_plans, insert_plan/version, latest_version, by_account_for_update, insert_subscription/period, latest_period). `tests/test_subscription_persistence.py` (6 pruebas contra PostgreSQL Test real con base aleatoria eliminada al terminar): grants del runtime sin DELETE/DDL, UQ/CHECK de versiones y precios, una suscripción por cuenta, periodos que se tocan sin solapar y rechazo de solape/duplicado/intervalo vacío, rollback sin estado parcial y downgrade/reapply. Ajustes durante la ejecución: la base aleatoria se crea una vez por clase (el helper fija el nombre al cargar); el fixture requirió membership del propietario, `account_sync_heads` y `kind='clinic'` por los triggers existentes de cuentas; asyncpg exige `datetime` para timestamptz. El inventario de sellos del probe de persistencia se actualizó de 85 a 91 (seis columnas created_at/updated_at nuevas), como en migraciones anteriores. Resultados: 6/6 pruebas OK; `test-support/persistence/check.py` pasó ("PostgreSQL checks passed: migrations up/down, failed revision rollback, runtime DDL denied..."); 42 pruebas de dominio/estructura OK; `uv build --offline` exitoso; `git diff --check` limpio.

## T13 · Implementar persistencia de reportes y revisión

**Estado:** Done. **Propietario:** `subscriptions/repository` y migraciones. **Alcance:** M.

**Descripción:** añadir tasas, reportes, revisiones y metadatos de evidencia con historia y coordinación de estados.

**Entradas y dependencias:** T12; T06.

**Datos, contratos, transacciones y consumidores:** misma sesión/DAOs commit=False, sin bytes ni URL pública; aislamiento por cuenta.

**Criterios de aceptación:**
- [x] Una aprobación ordinaria produce como máximo un efecto y referencias parciales no son UQ global.
- [x] Declaración/historia no se reescribe y evidencia no cruza cuentas.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_persistence tests.test_subscription_reports -v`.
- [x] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [x] Manual: intentar doble aprobación SQL, modificar declaración y cruzar evidencia/cuenta.

**Archivos previstos:** `migrations/versions/<revisión>_subscription_reports.py`, `src/api/subscriptions/repository/models.py`, `src/api/subscriptions/repository/dao.py`, `tests/test_subscription_persistence.py`.

**Evidencia:** 2026-11-26. Migración `20261126_02_subscription_reports.py` con las seis tablas de §18: `platform_operators` (UQ issuer/subject, CHECK de `actions text[]` no vacío y subconjunto de las cuatro acciones), `platform_operator_credentials` (huella UQ 64 hex, `revoked_at`), `bcv_exchange_rates` (UQ `rate_date`, `numeric(18,6)` positivo), `payment_reports` (FK compuesta `(subscription_id,account_id)` contra la UQ nueva `uq_account_subscriptions_id_account`, referencia de 4 dígitos como texto sin unicidad, índices de lista propia y bandeja), `payment_report_evidence` (UQ `report_id` y `storage_key`, tipos/tamaño D24, sha256) y `subscription_reviews` (UQ `report_id`, CHECK de coherencia aprobación/rechazo, FK a tasa). `subscription_periods` recibe `origin_review_id` NN con FK y UQ (una aprobación → como máximo un periodo). Grants mínimos sin DELETE. Modelos y DAO actualizados (`origin_review_id` en `insert_period`). Dos correcciones durante la ejecución: la UQ `(id,account_id)` debe crearse antes de `payment_reports` (orden de sentencias) y el downgrade debe eliminar las tablas dependientes antes de la UQ. 19 pruebas (10 de persistencia + 9 de dominio de reportes) OK contra PostgreSQL Test real: doble decisión rechazada por UQ, doble periodo por origen rechazado, reporte cruzado de cuenta rechazado por FK compuesta, `0071` repetida permitida, evidencia única por reporte con tipo/tamaño validados, tasa única por fecha, rollback limpio y downgrade/reapply por etapas. Probe `test-support/persistence/check.py` pasado tras actualizar el inventario de sellos a 99 (+8 columnas). `uv build --offline` y `git diff --check` limpios.

## T14 · Implementar administración versionada de planes

**Estado:** Done. **Propietario:** `subscriptions/application` e `infrastructure`. **Alcance:** M.

**Descripción:** implementar casos/rutas de operador para crear/versionar/retirar planes y precios sin alterar periodos/cotizaciones anteriores.

**Entradas y dependencias:** T13; operador T11 y contratos T07.

**Datos, contratos, transacciones y consumidores:** operaciones online idempotentes, historia/auditoría y versiones esperadas.

**Criterios de aceptación:**
- [x] Nuevas cotizaciones usan versión vigente y las históricas permanecen estables.
- [x] Solo acción de catálogo autorizada cambia planes; retirar conserva historia.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_catalog -v`.
- [x] `uv build --offline` y `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [x] Manual: cambiar precio/asientos y comprobar que una suscripción anterior conserva valores.

**Archivos previstos:** `src/api/subscriptions/application/catalog_cases.py`, `src/api/subscriptions/infrastructure/catalog_api.py`, `src/application.py`, `tests/test_subscription_catalog.py`.

**Evidencia:** 2026-11-26. `application/operator_cases.py` autentica la credencial opaca (huella → operador vigente) y recomprueba la acción de plataforma con el dominio de T11; `application/catalog_cases.py` implementa listar planes con historia, crear versión (siguiente número, control optimista por `expectedVersion` → `VersionConflict`, plan retirado → `PlanRetired`) y retirar conservando historia, todo dentro de `transaction(db)` con DAOs `commit=False`. `infrastructure/catalog_api.py` expone `GET /v1/operator/plans`, `POST .../{code}/versions` (201) y `.../retirement` con 401/403/404/409; router añadido en `src/api/api.py`. La migración `20261126_01` ahora siembra el catálogo inicial D21 con UUIDv7 fijos (dos sentencias separadas: asyncpg no admite multi-comando preparado). Se creó `SubscriptionPlanVersionDAO` separado tras detectar que `insert_version` usaba el modelo equivocado, y la autenticación se movió dentro de la transacción porque el SELECT previo autoinicia la sesión. 4 pruebas nuevas contra PostgreSQL Test: credencial ausente/inválida y acción denegada; listado de los tres planes D21; versión nueva conserva la histórica y el `expectedVersion` viejo da conflicto; retiro conserva historia y bloquea versiones nuevas. Verificación conjunta: 17 pruebas (persistencia+catálogo+estructura) OK, probe de persistencia pasado, `uv build --offline` OK, `git diff --check` limpio. Límite registrado: la idempotencia por `operationId` con recibo llega con la integración de operaciones de T20; aquí la concurrencia se cubre con la versión esperada.

## C05 · Después de T12–T14

- [x] Migraciones, privilegios y catálogo versionado pasan.
- [x] Los datos históricos no cambian al editar planes.
- [x] El usuario revisa y acepta C05. **Aceptado el 2026-11-26.**

## T15 · Implementar tasas BCV y cotizaciones

**Estado:** Done. **Propietario:** `subscriptions`. **Alcance:** M.

**Descripción:** implementar registro/selección de tasas por operador y cotización de plan/periodicidad para cuenta autorizada.

**Entradas y dependencias:** C05 aceptado; T02/T08/T14.

**Datos, contratos, transacciones y consumidores:** tasa/fuente histórica, decimal exacto, operaciones online y lectura propia.

**Criterios de aceptación:**
- [x] Cotización conserva plan/versión, USD, tasa/fecha/fuente, VES y redondeo.
- [x] Días sin publicación y correcciones siguen T02 sin elegir tasa del cliente.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_quotes tests.test_subscription_money -v`.
- [x] `uv build --offline` y pruebas HTTP ASGI incluidas en el módulo enfocado.
- [x] Manual: cotizar dos periodicidades y repetir tras nueva tasa sin alterar la primera cotización.

**Archivos previstos:** `src/api/subscriptions/application/quote_cases.py`, `src/api/subscriptions/infrastructure/quotes_api.py`, `tests/test_subscription_quotes.py`.

**Evidencia:** 2026-11-26. `domain/quotes.py` (solicitudes/respuestas de tasa y cotización con `Decimal` exacto y `roundingRule` fija), `BcvRateDAO` (inserción, por fecha, última en o antes de una fecha, página ordenada descendente) y `application/quote_cases.py`: `register_rate` (acción `rates`, duplicado por fecha → `RateDateExists` 409), `list_rates` paginado, `build_quote` (versión vigente del plan × tasa más reciente publicada en o antes de hoy en `America/Caracas`, D22; sin publicación → `RateUnavailable` 503, plan retirado → 409, desconocido → 404) y `create_quote` (propietario con dispositivo registrado vía `get_account_context`; asistente → 403). Rutas `GET/POST /v1/operator/bcv-rates` y `POST /v1/accounts/{id}/subscription/quotes` cableadas. La cotización es una respuesta calculada con `quoteId`/`quotedAt`: el diseño físico aprobado (§§17–18) no persiste cotizaciones; la aprobación congela su propia copia (§9.4). 3 pruebas nuevas contra PostgreSQL Test: registro/listado/duplicado/credencial inválida; selección de tasa con día sin publicación (25-nov usa la del 24), dos periodicidades (18,00→7.204,50 y 500,00→200.125,00 con tasa ficticia 400,25), sin tasa previa → no disponible; una tasa nueva no altera la cotización anterior y produce otra con 410,00→7.380,00. Las pruebas usan una sesión por operación porque las lecturas autoinician la transacción de la sesión (mismo comportamiento que una petición por sesión en producción). El recorrido HTTP completo del propietario con Keycloak real queda para el probe de T18; aquí se cubrió el caso de uso con contexto real de cuentas. `uv build --offline` OK.

## T16 · Integrar límite de asientos con pertenencias y planes

**Estado:** Done. **Propietario:** `accounts` y `subscriptions`. **Alcance:** M.

**Descripción:** invocar el caso de asientos al aceptar/reactivar/cambiar plan con coordinación transaccional y proyección de consumo.

**Entradas y dependencias:** T15; catálogo de autorización y T01.

**Datos, contratos, transacciones y consumidores:** misma transacción de invitación/pertenencia/cambio, recibo/auditoría/época conservados.

**Criterios de aceptación:**
- [x] Dos aceptaciones/reactivaciones no superan el límite y la última plaza tiene un solo ganador.
- [x] Reducción con exceso no desactiva usuarios y bloquea nuevas incorporaciones según T01.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_seats tests.test_account_changes -v`.
- [x] `./.venv/Scripts/python.exe test-support/team/check.py` y `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [x] Manual: disputar última plaza con dos conexiones y revisar miembros/versión/recibo finales.

**Archivos previstos:** `src/api/accounts/application/invitations_cases.py`, `src/api/subscriptions/application/seat_cases.py`, `tests/test_subscription_seats.py`, `test-support/team/check.py`.

**Evidencia:** 2026-11-26. `subscriptions/application/seat_cases.py`: `ensure_seat_available` bloquea la fila de la suscripción (`FOR UPDATE`) como punto de serialización, cuenta pertenencias activas vía el caso de accounts `count_active_members` (nuevo, con `AccountMembershipDAO.count_active`) y aplica `SeatUsage` de D21; cuentas sin suscripción no se limitan aquí (enforcement comercial es T24). Integración en `accounts/application/invitations_cases.py` en los dos puntos que ocupan asiento: aceptación de invitación (creación o reactivación de pertenencia) y `SetMembershipStatus` hacia `active`; ambos devuelven `AccountRuleError("SEAT_LIMIT_REACHED")` → 409, añadido a la lista de códigos 409 permitidos en `src/api/errors.py`. No hay ciclo de imports (accounts_cases no importa invitations_cases). 3 pruebas nuevas contra PostgreSQL Test: límite 2 con propietario deja una plaza y al ocuparla deniega; pertenencia inactiva libera su plaza; cuenta sin suscripción no se limita; **carrera real con dos conexiones** por la última plaza produce exactamente un `accepted` y un `denied` y 2 activos finales. Regresión: `test-support/team/check.py` pasó ("directed invitations, 72-hour expiry, atomic acceptance... concurrent revoke/accept and lost response") y `tests.test_account_changes` sigue verde (7 pruebas conjuntas). El cambio de plan con exceso (sin desactivación) se aplica en T23 sobre este mismo caso. `test-support/team/check.py` no necesitó cambios.

## T17 · Seleccionar e implementar almacenamiento privado de evidencias

**Estado:** Done. **Propietario:** `core/services`, `subscriptions` y seguridad. **Alcance:** M.

**Descripción:** comparar la opción mínima con APIs/versiones oficiales, justificar elección e implementar carga/descarga autorizada y limpieza segura.

**Entradas y dependencias:** T16; T04, manifiesto/lockfile y guía docs-first.

**Datos, contratos, transacciones y consumidores:** bytes fuera de DB/sync/webroot, nombres generados, validación real y límites T04.

**Criterios de aceptación:**
- [x] La decisión/versión/fuente oficial queda registrada y no hay dependencia injustificada.
- [x] Tipo/tamaño/nombre, aislamiento y descarga reautorizada cumplen OWASP sin logs sensibles.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_evidence -v`.
- [x] `uv build --offline` y revisión de lockfile/artefactos si cambia una dependencia justificada.
- [x] Manual: subir archivo válido/falso/grande, descargar con cuenta autorizada/ajena y revisar logs.

**Archivos previstos:** `src/core/services/subscription_evidence.py`, `src/settings/`, `src/api/subscriptions/application/evidence_cases.py`, `tests/test_subscription_evidence.py`, `docs/operations/development.md`.

**Evidencia:** 2026-11-26. Decisión docs-first aplicada con la escalera de minimal-code: **no se creó `subscription_evidence.py` ni dependencia nueva**; la captura reutiliza `src/core/services/report_storage.py` (adaptador S3 con `aioaws` fijado en `uv.lock` por Etapa 3/D19, con alternativa local bajo `STORAGE_ROOT`), cuya selección y fuentes ya quedaron justificadas; la reutilización queda registrada en `docs/operations/development.md`. `domain/reports.py` añade `detect_content_type` (firma real JPEG/PNG/PDF, nunca el `Content-Type` del cliente, OWASP). `application/evidence_cases.py`: `store_evidence` valida tamaño (1 byte–5 MB, D24) y firma antes de escribir; guarda los bytes fuera de la transacción (un fallo posterior deja un archivo huérfano sin efecto comercial, §13.3) y confirma la fila de metadatos con bloqueo del reporte (404 ajeno/inexistente, `ReportNotPending`, `EvidenceAlreadyPresent` — una captura por reporte); `upload_evidence` exige propietario con dispositivo; `read_evidence` devuelve bytes+tipo y la reautorización ocurre en la ruta (conocer `storage_key` no concede nada; el `storage_key` local no contiene URL). 3 pruebas nuevas contra PostgreSQL Test y almacenamiento local real: PNG válido guardado con metadatos y sha256 y descargado idéntico; GIF por firma, vacío y >5 MB rechazados; segunda captura rechazada; reporte ajeno 404; reporte decidido no admite captura; sin evidencia → `EvidenceNotFound`. Un fallo del fixture (la revisión de prueba no actualizaba el estado del reporte, cosa que el caso real hace en su transacción) se corrigió en el propio test. 6 pruebas conjuntas con estructura OK; `uv build --offline` OK; los archivos de prueba se eliminan en `asyncTearDown`.

## C06 · Después de T15–T17

- [x] Cotización, asientos y evidencia privada pasan pruebas enfocadas/reales.
- [x] La elección de almacenamiento está sustentada y no hay fuga de archivos.
- [x] El usuario revisa y acepta C06. **Aceptado el 2026-11-26.**

## T18 · Implementar presentación y consulta de reportes por la cuenta

**Estado:** Done. **Propietario:** `subscriptions` y `sync`. **Alcance:** M.

**Descripción:** implementar reporte online con evidencia, listas/detalle propios, recuperación idempotente y probe HTTP real.

**Entradas y dependencias:** C06 aceptado; contratos T07.

**Datos, contratos, transacciones y consumidores:** cuenta/propietario autorizado, reporte/metadatos/recibo/auditoría atómicos; bytes fuera de transacción.

**Criterios de aceptación:**
- [x] Presentar deja `pending` sin activar/extender y respuesta perdida recupera el mismo reporte.
- [x] Una cuenta no lista/detalla/descarga reportes de otra.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_reports -v`.
- [x] `./.venv/Scripts/python.exe test-support/subscriptions/check.py`.
- [x] Manual: enviar reporte, cortar respuesta tras commit, reintentar y verificar un único registro/periodo ausente.

**Archivos previstos:** `src/api/subscriptions/application/report_cases.py`, `src/api/subscriptions/infrastructure/reports_api.py`, `tests/test_subscription_reports.py`, `test-support/subscriptions/check.py`.

**Evidencia:** 2026-11-26. `report_cases.py`: `submit_report` (propietario con dispositivo; autenticación y escritura en una sola transacción porque la sesión autoinicia con el primer SELECT), `_persist_report` (resuelve versión vigente del plan — retirado/desconocido → `PlanUnavailable` 409 —, crea la suscripción `pending_activation` en la primera relación comercial según §10.2, inserta el reporte `pending` con `operationId` como PK: repetir la misma intención recupera el mismo reporte y un contenido distinto da `IdempotencyConflict` 409), `list_reports` paginado y `report_detail` con resultado de revisión y periodo concedido. `reports_api.py`: 5 rutas bajo `A/subscription/reports` (crear 201, listar, detalle, subir evidencia multipart 201, descargar con `no-store`). Nuevo probe `test-support/subscriptions/check.py` con Keycloak/PostgreSQL reales y cuenta creada por `bootstrap_practice` + invitación/aceptación/registro de dispositivos reales: asistente 403, outsider 404, presentar deja `pending` sin periodos y suscripción `pending_activation`, reintento recupera el mismo reporte (1 fila), conflicto 409, firma falsa 422 antes de la captura válida 201, duplicado 409, descarga idéntica con `no-store`, asistente 403 en evidencia, y `storageKey` ausente de las respuestas. Correcciones durante la ejecución: el contrato §14.4 usaba `days30/year1` y se alineó a `days_30/year_1` (convención snake de valores enumerados del proyecto); el bug de sesión autoiniciada (auth fuera de la transacción) se corrigió en `submit_report` y `upload_evidence` (este último con el patrón de tres fases: pre-chequeo corto, bytes fuera de la transacción, re-chequeo con bloqueo e inserción); el probe ordena la firma falsa antes de la captura válida porque el duplicado se detecta primero. 16 pruebas unitarias/de integración OK, probe pasado, `uv build --offline` OK, `git diff --check` limpio.

## T19 · Implementar bandeja y detalle de revisión del operador

**Estado:** Done. **Propietario:** `subscriptions` y seguridad. **Alcance:** M.

**Descripción:** implementar lista paginada de pendientes/historia, detalle y descarga de evidencia con filtros autorizados.

**Entradas y dependencias:** T18; operador T11.

**Datos, contratos, transacciones y consumidores:** page/shows, autorización antes de total, lecturas auditadas sin contenido sensible.

**Criterios de aceptación:**
- [x] Operador ve solo campos/acciones de revisión y ninguna información clínica.
- [x] Paginación/descarga reautoriza y no revela cuentas fuera de su alcance.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_operator tests.test_subscription_reports -v`.
- [x] `./.venv/Scripts/python.exe test-support/subscriptions/check.py`.
- [x] Manual: revisar páginas/filtros y evidencia con operador válido, revocado y acción de catálogo solamente.

**Archivos previstos:** `src/api/subscriptions/application/review_cases.py`, `src/api/subscriptions/infrastructure/reviews_api.py`, `tests/test_subscription_operator.py`.

**Evidencia:** 2026-11-26. `review_cases.py`: `list_reports_for_operator` (acción `review`, filtros `status`/`accountId`, page/shows con orden `(createdAt, id)` y autorización antes de contar), `report_detail_for_operator` (declaración completa, metadatos de evidencia, resultado de revisión con periodo concedido, cadena de nuevas presentaciones y **advertencias de coincidencia de referencia parcial** — solo advierten, nunca rechazan, §12.6/D24) y `read_evidence_for_operator` (reautoriza la acción en cada descarga; `storage_key` jamás sale). `reviews_api.py`: `GET /v1/operator/payment-reports`, `/{id}` y `/{id}/evidence` con `no-store`; el filtro `accountId` usa alias camelCase (los parámetros sueltos de FastAPI no heredan el alias generator — detectado por el probe). Los modelos del operador no incluyen datos clínicos ni `storageKey`. Probe ampliado: sin credencial 401, operador con solo `catalog` 403, bandeja de pendientes con el reporte, filtro por cuenta ajena vacío, detalle con declaración/evidencia sin claves, descarga idéntica con `no-store` y **operador revocado pierde acceso con la misma credencial** (403). 20 pruebas unitarias OK y probe completo pasado; `uv build --offline` OK. La bandeja no registra lecturas en auditoría todavía: la evidencia de auditoría de decisiones llega con T20 (aprobación/rechazo), registrado como límite.

## T20 · Implementar aprobación atómica y periodos únicos

**Estado:** Done. **Propietario:** `subscriptions`, `sync` y `audit`. **Alcance:** M.

**Descripción:** implementar aprobación con datos verificados, tasa/precio congelados, cálculo de periodo y todos los efectos en una transacción.

**Entradas y dependencias:** T19; T12/T13 y reglas T02.

**Datos, contratos, transacciones y consumidores:** reporte/suscripción/periodo/historia/auditoría/recibo/grupo coordinados; sin red dentro.

**Criterios de aceptación:**
- [x] Aprobación inicial/extensión crea exactamente un periodo coherente y una decisión de operador.
- [x] Respuesta perdida/dos operadores no duplican periodo, días, recibo o historia.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_money -v` (la cobertura de aprobación vive en el probe HTTP real y en las pruebas de persistencia; no se creó `tests/test_subscription_approval.py` separado para no duplicar el recorrido).
- [x] `./.venv/Scripts/python.exe test-support/subscriptions/check.py` (incluye la carrera de dos operadores y la recuperación tras respuesta perdida). `test-support/sync/check.py` no aplica aún: la proyección comercial en sync llega en T22.
- [x] Manual: ejecutar carrera de aprobación, comparar operador real, SQL y recuperación tras respuesta perdida.

**Archivos previstos:** `src/api/subscriptions/application/review_cases.py`, `src/api/sync/application/operations_cases.py`, `tests/test_subscription_approval.py`, `test-support/subscriptions/check.py`.

**Evidencia:** 2026-11-26. `approve_report` en `review_cases.py` confirma en **una sola transacción**: autenticación del operador (`review`), bloqueo del reporte con `expectedVersion`, datos verificados separados, regla D22 de tasa (para VES la tasa debe ser la publicada en la fecha del pago verificado o la más reciente anterior — el operador no puede elegir otra, `RateMismatch` 422), importe exacto debido (`PaymentMismatch` 422, D24), cálculo del periodo con el dominio de T08 (inicial en aprobación, anticipado desde `endsAt`), revisión con `operationId` como PK (respuesta perdida → `duplicate=true` sin segundo periodo; otra decisión → `REPORT_NOT_PENDING` 409), `origin_review_id` único, suscripción `active` con versión incrementada y evidencia de auditoría vía `record_control` con `actor_kind='operator'` (el esquema ya lo admitía). Ruta `POST /v1/operator/payment-reports/{id}/approval`; `REPORT_NOT_PENDING` añadido a los códigos 409. Defecto real detectado por el probe: los métodos de periodos vivían en el DAO de suscripciones (modelo equivocado, mismo patrón que T14) — se creó `SubscriptionPeriodDAO`. Probe ampliado y pasado: mismatch 422, aprobación 200 con secuencia 1 y suscripción activa, duplicado con `duplicate=true` y un solo periodo, segundo operador 409, exactamente 1 revisión/1 periodo/1 evento de auditoría en SQL, el propietario ve el periodo concedido en su detalle, y **carrera de dos operadores con conexiones concurrentes: exactamente un 200 y un 409, dos periodos en total**. Suite completa del componente: 69 pruebas OK; build y diff limpios. Límite: el resultado idempotente se apoya en la PK de la revisión, no en `operation_receipts`; la integración con recibos/sync se evalúa en T22.

## C07 · Después de T18–T20

- [x] Presentar no activa y aprobar activa/extiende una sola vez.
- [x] Bandeja, evidencia, aislamiento y respuestas perdidas pasan.
- [x] El usuario revisa y acepta C07. **Aceptado el 2026-11-26.**

## T21 · Implementar rechazo y nueva presentación

**Estado:** Done. **Propietario:** `subscriptions`. **Alcance:** M.

**Descripción:** añadir rechazo con motivo seguro y nueva presentación relacionada sin reabrir/reescribir historia.

**Entradas y dependencias:** C07 aceptado; T04/T10.

**Datos, contratos, transacciones y consumidores:** suscripción/periodo anterior sin cambio; revisión/auditoría/recibo en una transacción.

**Criterios de aceptación:**
- [x] Rechazo no crea pago/periodo ni cambia acceso comercial anterior.
- [x] Nueva presentación conserva vínculo e historia y vuelve a pending sin duplicar aprobación anterior.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_reports -v` (la aprobación se cubre en el probe; no existe `test_subscription_approval.py` separado, ver T20).
- [x] `./.venv/Scripts/python.exe test-support/subscriptions/check.py`.
- [x] Manual: rechazar, corregir, reenviar y aprobar una sola vez revisando toda la cadena.

**Archivos previstos:** `src/api/subscriptions/application/review_cases.py`, `src/api/subscriptions/application/report_cases.py`, `tests/test_subscription_reports.py`.

**Evidencia:** 2026-11-26. `reject_report` en `review_cases.py`: misma disciplina transaccional que la aprobación (operador `review`, bloqueo del reporte, `expectedVersion` → 409, revisión con `operationId` como PK — mismo id recupera `duplicate=true` —, motivo obligatorio vía dominio/pydantic, `mark_decided` y auditoría `RejectPaymentReport`); la suscripción y los periodos no se tocan y la declaración/evidencia quedan intactas (§15). La nueva presentación ya estaba soportada por `submit_report` con `previousReportId` (T18). Ruta `POST /v1/operator/payment-reports/{id}/rejection`. Probe ampliado y pasado a la primera: versión vieja 409, rechazo 200 con motivo seguro, duplicado `duplicate=true`, el propietario ve `decision=rejected` + motivo + `grantedPeriod` nulo, la nueva presentación queda `pending` vinculada al original (que permanece `rejected`), y su aprobación concede exactamente la secuencia siguiente (3) una sola vez. 20 pruebas unitarias OK, build y diff limpios.

## T22 · Implementar proyección comercial en snapshot/delta/SSE

**Estado:** Done. **Propietario:** `sync` y `subscriptions`. **Alcance:** M.

**Descripción:** publicar disponibilidad/plan/asientos según audiencia, con versión comercial y recuperación sin evidencia ni datos financieros innecesarios.

**Entradas y dependencias:** T21; contratos T07.

**Datos, contratos, transacciones y consumidores:** captura/grupos/cursor/época aplicables, avisos mínimos y proyecciones validadas antes del commit.

**Criterios de aceptación:**
- [x] Miembros/propietario reciben solo su proyección y captura/delta recuperan aprobaciones perdidas.
- [x] Capturas, tasas, reportes y evidencias no aparecen en audiencias generales.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_downloads tests.test_events tests.test_subscription_sync -v`.
- [x] `./.venv/Scripts/python.exe test-support/downloads/check.py` y `./.venv/Scripts/python.exe test-support/events/check.py`.
- [x] Manual: aprobar con aviso perdido, reconectar y recuperar versión/periodo sin captura en el journal.

**Archivos previstos:** `src/api/sync/application/snapshot_cases.py`, `src/api/sync/application/download_cases.py`, `src/api/sync/application/events_cases.py`, `src/api/sync/domain/downloads.py`, `tests/test_subscription_sync.py`.

**Evidencia:** 2026-11-26. Dos entidades nuevas en el catálogo de proyecciones: `subscription` (audiencia `members`: planCode, status efectivo, currentPeriodEndsAt, graceEndsAt, subscriptionVersion, updatedAt) y `subscription_admin` (audiencia `owner`: añade seats{used,limit}); registradas en `projection_audiences` (policies) y `PROJECTION_SCHEMAS` (downloads) — el test de catálogo existente obligó a registrar ambas. `projection_cases.py` construye las proyecciones como modelos validados (nunca reportes, tasas, motivos ni evidencias), `snapshot_subscription` se integra en `create_snapshot` y `publish_subscription_change` añade el grupo al journal con `permission_changed=False` (la disponibilidad no es un cambio de permisos, §18.4). **Decisión de diseño descubierta en la implementación:** `change_log` exige un recibo de operación de un miembro con dispositivo (FK + trigger de frontera que exige `accepted_at = completed_at` y auditoría de staff coincidente); por tanto el delta solo publica el cambio comercial de la primera presentación (acción `SubmitPaymentReport`, con recibo, auditoría y huella — que además sirve de registro durable de idempotencia), y las decisiones del operador se recuperan por captura (snapshot), que siempre refleja el estado vigente. api-v1 §14.6 actualizado con esta regla exacta. El `now` del recibo se comparte con el journal para satisfacer el trigger. 3 pruebas nuevas (`test_subscription_sync`): grupo mínimo con audiencias correctas y sin campos prohibidos, epoch sin cambio, snapshot reflejando la aprobación y delta solo con la presentación; la aprobación con aviso perdido se recupera por snapshot (verificado en la prueba y por los probes). Regresiones: probes `downloads`, `events` y `subscriptions` pasados tras el cambio; 17 pruebas de sync/descargas OK; build y diff limpios.

## T23 · Implementar renovación, cambio de plan y cancelación

**Estado:** Done. **Propietario:** `subscriptions`. **Alcance:** M.

**Descripción:** completar compras anticipadas/tardías, cambio según T04 y cancelación conservando tiempo pagado e historia.

**Entradas y dependencias:** T22; T01/T02/T04.

**Datos, contratos, transacciones y consumidores:** coordinación suscripción/plan/reporte/periodo, recibos y cambios en una aceptación.

**Criterios de aceptación:**
- [x] Anticipado no pierde días, tardío usa inicio aprobado y periodos no se solapan.
- [x] Cambio/cancelación respeta asientos, prorrateo elegido y tiempo pagado sin borrado.

**Verificación:**
- [x] `uv run --locked python -m unittest tests.test_subscription_renewals tests.test_subscription_seats -v`.
- [x] `./.venv/Scripts/python.exe test-support/subscriptions/check.py`.
- [x] Manual: renovar antes/después, cambiar plan y cancelar con carrera de aprobación/cambio.

**Archivos previstos:** `src/api/subscriptions/application/subscription_cases.py`, `tests/test_subscription_renewals.py`, `test-support/subscriptions/check.py`.

**Evidencia:** 2026-11-26. `subscription_cases.py`: `get_subscription` (propietario; respuesta §14.4 con estado efectivo, periodo, gracia y asientos), `change_plan` (D24 sin prorrateo: actualiza `plan_version_id` con control optimista; plan retirado/desconocido → 409; el periodo ya aprobado conserva su versión — verificado en SQL) y `cancel_subscription` (marca `cancelled` sin tocar periodos). Ambos cambios escriben recibo + auditoría de staff y publican el grupo en el journal con el mismo instante (patrón de T22). Corrección de dominio derivada de §16.3: `commercial_availability` con estado `cancelled` mantiene `active` hasta el fin del tiempo pagado y solo después devuelve `cancelled` (test de dominio actualizado). Renovaciones: ya resueltas por `compute_period` en la aprobación (T20) — la prueba lo acredita de punta a punta: anticipada comienza exactamente en el `endsAt` previo (sin perder días, secuencia 2), tardía comienza en la aprobación (secuencia 3) y la exclusión de solapes rechazó un fixture mal construido durante la prueba (la restricción funciona). Rutas `GET A/subscription`, `POST .../plan-changes`, `POST .../cancellation`. Probe ampliado: lectura del propietario con asientos 2/2, asistente 403, cambio con versión vieja 409, cambio a consultorio con límite 5, cancelación que conserva `active` con periodo vigente. La reducción de plan con exceso no desactiva a nadie y bloquea altas vía el chequeo de asientos de T16 (usa la versión vigente de la suscripción). 76 pruebas del componente OK, probe pasado, build y diff limpios.

## C08 · Después de T21–T23

- [ ] Rechazo, sync, renovación, cambio y cancelación pasan.
- [ ] No hay solapes, pérdida de historia o evidencia en sincronización.
- [ ] El usuario revisa y acepta C08.

## T24 · Aplicar gracia, suspensión y política offline

**Estado:** Todo. **Propietario:** `subscriptions`, `accounts` y `sync`. **Alcance:** M.

**Descripción:** integrar disponibilidad comercial con autorización personal sin modificar roles/tokens y con las funciones permitidas decididas en T04.

**Entradas y dependencias:** C08 aceptado; `SU-O07` resuelto.

**Datos, contratos, transacciones y consumidores:** comprobación tras autenticación/autorización, errores específicos futuros y proyección offline versionada.

**Criterios de aceptación:**
- [ ] Suscripción no concede permisos y rol no evita suspensión; renovación/consulta mínima permanece disponible.
- [ ] Reloj local no extiende servicio y suspensión no borra datos/intenciones ni revoca identidades.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_access tests.test_authorization_policies -v`.
- [ ] `./.venv/Scripts/python.exe test-support/subscriptions/check.py` y `./.venv/Scripts/python.exe test-support/access/check.py`.
- [ ] Manual: recorrer activa→gracia→suspensión→renovación con y sin red, verificando datos/permisos conservados.

**Archivos previstos:** `src/api/subscriptions/application/access_cases.py`, `src/api/accounts/domain/policies.py`, `src/api/sync/application/operations_cases.py`, `tests/test_subscription_access.py`.

**Evidencia:** pendiente.

## T25 · Implementar indicadores administrativos

**Estado:** Todo. **Propietario:** `subscriptions` y `analytics`. **Alcance:** M.

**Descripción:** añadir consultas acotadas de cuentas/planes/estados, vencimientos, pendientes, periodos, importes históricos y asientos.

**Entradas y dependencias:** T24; operador con acción de indicadores.

**Datos, contratos, transacciones y consumidores:** consultas fuera de escrituras, totales por moneda y sin pacientes/contenido clínico.

**Criterios de aceptación:**
- [ ] Pendientes no cuentan como verificado y VES no se revaloriza ni mezcla con USD.
- [ ] Filtros, autorización, fechas y uso/exceso de asientos coinciden con estados persistidos.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_metrics -v`.
- [ ] `uv build --offline` y consultas de volumen ficticio acotadas en el probe.
- [ ] Manual: contrastar un panel pequeño con SQL de periodos/reportes/asientos y monedas separadas.

**Archivos previstos:** `src/api/subscriptions/application/metrics_cases.py`, `src/api/subscriptions/infrastructure/metrics_api.py`, `tests/test_subscription_metrics.py`.

**Evidencia:** pendiente.

## T26 · Completar seguridad, concurrencia y recuperación

**Estado:** Todo. **Propietario:** calidad de `subscriptions`. **Alcance:** M.

**Descripción:** ampliar probes para accesos cruzados, doble operador, última plaza, cambio/aprobación, archivos y caídas tras commit.

**Entradas y dependencias:** T25; flujo completo.

**Datos, contratos, transacciones y consumidores:** PostgreSQL/Keycloak Test y almacenamiento ficticio aislado; bases/archivos eliminados al terminar.

**Criterios de aceptación:**
- [ ] Ninguna carrera duplica periodos/excede asientos ni una revocación antigua permite efectos posteriores.
- [ ] Logs/auditoría/sync/errores no contienen capturas, secretos, claves o datos bancarios innecesarios.

**Verificación:**
- [ ] `./.venv/Scripts/python.exe test-support/subscriptions/check.py` y `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] `uv run --locked python -m unittest discover -s tests -v`.
- [ ] Manual: revisar trazas de bloqueo, artefactos y SQL final para cada fallo inyectado.

**Archivos previstos:** `test-support/subscriptions/check.py`, `test-support/persistence/check.py`, `tests/test_subscription_access.py`.

**Evidencia:** pendiente.

## C09 · Después de T24–T26

- [ ] Enforcement, indicadores, seguridad y carreras pasan localmente.
- [ ] No hay borrado, fuga o mezcla de monedas/estados.
- [ ] El usuario revisa y acepta C09.

## T27 · Generar contratos y actualizar documentación

**Estado:** Todo. **Propietario:** contratos y documentación técnica. **Alcance:** M.

**Descripción:** exportar OpenAPI/esquemas/capacidades/ejemplos reales y alinear fuentes con implementación, versiones y compatibilidad.

**Entradas y dependencias:** C09 aceptado; app real y modelos Pydantic.

**Datos, contratos, transacciones y consumidores:** artefactos con origen/HEAD/huella, sin edición manual ni secretos/ejemplos reales.

**Criterios de aceptación:**
- [ ] Dos generaciones/`--check` y ejemplos de cuenta/operador/revisión/sync son reproducibles.
- [ ] Documentación no afirma banco, BCV vivo, producción o consumidores no probados.

**Verificación:**
- [ ] `uv run --locked python -m scripts.export_contracts` y `uv run --locked python -m scripts.export_contracts --check`.
- [ ] `./.venv/Scripts/python.exe test-support/contracts/check.py` y `git diff --check`.
- [ ] Manual: consumir ejemplos de cotización, reporte, aprobación y recuperación con cliente ASGI real.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/rust-api-guide.md`, artefactos generados por el exportador.

**Evidencia:** pendiente.

## T28 · Ejecutar cierre integral y registrar evidencia

**Estado:** Todo. **Propietario:** calidad y mantenimiento del plan. **Alcance:** M.

**Descripción:** ejecutar suite, probes, migraciones, contratos y build; revisar diff y registrar resultados/límites en las fuentes de evidencia.

**Entradas y dependencias:** T27; entregable completo.

**Datos, contratos, transacciones y consumidores:** solo datos ficticios y servicios Test; sin despliegue, commits o cambios en otros repositorios.

**Criterios de aceptación:**
- [ ] Todos los comandos pertinentes pasan y los límites externos/operativos quedan explícitos.
- [ ] No quedan archivos temporales necesarios fuera de `.tmp`, trabajo ajeno alterado o aceptaciones automáticas.

**Verificación:**
- [ ] `uv run --locked python -m unittest discover -s tests -v` y probes `subscriptions`, `access`, `accounts`, `team`, `sync`, `downloads`, `events`, `persistence` y `contracts` mediante sus `check.py`.
- [ ] `uv build --offline`, `uv run --locked python -m scripts.export_contracts --check` y `git diff --check`.
- [ ] Manual: cotización→captura→reporte→aprobación→periodo→sync→renovación/cancelación con dos operadores y datos ficticios.

**Archivos previstos:** `tasks/P-20261117-02-account-subscriptions/plan.md`, `tasks/P-20261117-02-account-subscriptions/todo.md`, `docs/operations/development.md`, `docs/quality.md`.

**Evidencia:** pendiente.

## C10 · Después de T27–T28

- [ ] Suite, probes, migraciones, contratos y build pasan.
- [ ] El recorrido completo funciona localmente y la evidencia conserva límites externos.
- [ ] El usuario revisa y acepta C10 antes de depender de suscripciones en producción.
