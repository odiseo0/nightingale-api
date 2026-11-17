# Lista de tareas: P-20261117-02-account-subscriptions

**Plan:** [plan.md](plan.md). **Actualizado:** 2026-11-17. **Estado del plan:** Approved.

Todas las tareas están Todo. La ejecución requiere C06 aceptado del plan de autorización. Las decisiones de usuario obtenidas en T01–T04 se registran antes del trabajo dependiente; no se marcan por este documento.

## T01 · Cerrar planes, precios y asientos

**Estado:** Todo. **Propietario:** producto y `subscriptions`. **Alcance:** M.

**Descripción:** resolver precios USD por plan/periodicidad, pertenencias que consumen asiento, límites numéricos y tratamiento del exceso al reducir plan.

**Entradas y dependencias:** autorización C06 aceptada; `SU-O02`, `SU-O05` y `SU-O08`.

**Datos, contratos, transacciones y consumidores:** decisiones documentales; no cambia datos, contratos o consumidores todavía.

**Criterios de aceptación:**
- [ ] Los tres planes tienen precios 30 días/año y límites explícitos, sin diferencias funcionales.
- [ ] Se define cómputo de propietario/asistentes/profesionales/invitaciones/dispositivos y exceso sin desactivación automática.

**Verificación:**
- [ ] Revisión de ejemplos ficticios de ocupación, reactivación y reducción de plan.
- [ ] `git diff --check` y validación de enlaces locales.
- [ ] Manual: recorrer última invitación disponible y una cuenta sobre el límite con las reglas decididas.

**Archivos previstos:** `docs/account-subscriptions.md`, `docs/decisions.md`, `tasks/P-20261117-02-account-subscriptions/todo.md`.

**Evidencia:** pendiente.

## T02 · Cerrar BCV, monedas y periodos

**Estado:** Todo. **Propietario:** producto y dominio financiero. **Alcance:** M.

**Descripción:** resolver fecha/fuente BCV, días sin publicación, monedas aceptadas, significado de un año e inicio inicial/renovación tardía.

**Entradas y dependencias:** T01; `SU-O03`, `SU-O04` y `SU-O06`.

**Datos, contratos, transacciones y consumidores:** reglas documentales con ejemplos ficticios; sin integración BCV automática.

**Criterios de aceptación:**
- [ ] Cotización, redondeo y tasa histórica tienen una sola regla para todos los recorridos.
- [ ] Periodos inicial, anticipado, tardío, anual y 29 de febrero tienen resultados explícitos.

**Verificación:**
- [ ] Cálculo manual de ejemplos USD/VES y fechas límite con `Decimal` de biblioteca estándar.
- [ ] `git diff --check` y enlaces BCV/ISO/PostgreSQL verificados.
- [ ] Manual: revisar una renovación antes y después del vencimiento sin pérdida/duplicación de días.

**Archivos previstos:** `docs/account-subscriptions.md`, `docs/decisions.md`, `tasks/P-20261117-02-account-subscriptions/todo.md`.

**Evidencia:** pendiente.

## C01 · Después de T01–T02

- [ ] Las decisiones `SU-O02`–`SU-O06` y `SU-O08` están registradas.
- [ ] Ejemplos y documentos no contienen valores ambiguos o supuestos.
- [ ] El usuario revisa y acepta C01.

## T03 · Cerrar operador y canal administrativo

**Estado:** Todo. **Propietario:** producto, seguridad y operación. **Alcance:** M.

**Descripción:** decidir alta, autenticación, recuperación, revocación, acciones y canal del operador sin convertirlo en miembro o administrador clínico.

**Entradas y dependencias:** C01 aceptado; `SU-O01` y `SU-O12`.

**Datos, contratos, transacciones y consumidores:** diseño de actor/canal; no se deduce módulo del Hub ni sesión del personal.

**Criterios de aceptación:**
- [ ] El ciclo completo del operador y sus acciones de catálogo/revisión están definidos.
- [ ] Recuperación/revocación y ausencia de acceso a pacientes/clínica son explícitas.

**Verificación:**
- [ ] Revisión de amenazas: operador revocado, token robado, cuenta cruzada y recuperación.
- [ ] `git diff --check` y enlaces de las fuentes oficiales necesarias para el mecanismo elegido.
- [ ] Manual: recorrer alta→revisión→revocación→intento de lectura clínica denegada.

**Archivos previstos:** `docs/account-subscriptions.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/decisions.md`.

**Evidencia:** pendiente.

## T04 · Cerrar gracia, archivos y excepciones de pago/cambio

**Estado:** Todo. **Propietario:** producto, operación y seguridad. **Alcance:** M.

**Descripción:** resolver gracia/suspensión offline, límites/retención de capturas, pagos parciales/excedentes/varios periodos y prorrateo/cambio de plan.

**Entradas y dependencias:** T03; `SU-O07` y `SU-O09`–`SU-O11`.

**Datos, contratos, transacciones y consumidores:** políticas documentales; sin almacenamiento o enforcement implementado.

**Criterios de aceptación:**
- [ ] Funciones permitidas en gracia/suspensión y comportamiento offline están cerrados sin borrado.
- [ ] Archivos y excepciones de pago/cambio tienen reglas de aceptación/rechazo y conservación.

**Verificación:**
- [ ] Matriz de casos vencimiento con/sin red, excedente, duplicado sospechoso y cambio anticipado.
- [ ] `git diff --check` y referencias OWASP/retención revisadas.
- [ ] Manual: seguir una cuenta vencida que reporta, renueva y recupera sin perder intenciones/datos.

**Archivos previstos:** `docs/account-subscriptions.md`, `docs/decisions.md`, `docs/quality.md`.

**Evidencia:** pendiente.

## T05 · Diseñar físicamente núcleo de suscripciones y asientos

**Estado:** Todo. **Propietario:** `subscriptions/repository` y esquema físico. **Alcance:** M.

**Descripción:** incorporar a la fuente única planes/versiones, suscripciones/periodos y reglas de asientos con tipos, claves, intervalos e índices.

**Entradas y dependencias:** T04; decisiones T01/T02.

**Datos, contratos, transacciones y consumidores:** diseño físico, sin migración; periodos `[start,end)`, decimal y relaciones por cuenta.

**Criterios de aceptación:**
- [ ] Versiones de plan, una aprobación→un periodo y no solape tienen restricciones propuestas.
- [ ] Asientos reutilizan pertenencias y las consultas/índices cubren vigencia/cuenta.

**Verificación:**
- [ ] Revisión cruzada de cada regla conceptual con columna/FK/CHECK/UQ/índice propuesto.
- [ ] `git diff --check` y enlaces PostgreSQL 18 pertinentes.
- [ ] Manual: evaluar SQL conceptual de dos aprobaciones y última plaza concurrente.

**Archivos previstos:** `docs/database-schema.md`, `docs/account-subscriptions.md`.

**Evidencia:** pendiente.

## C02 · Después de T03–T05

- [ ] Operador y políticas pendientes tienen decisiones explícitas.
- [ ] El núcleo físico cubre dinero, intervalos, asientos e historia.
- [ ] El usuario revisa y acepta C02.

## T06 · Diseñar físicamente tasas, reportes, revisiones y evidencias

**Estado:** Todo. **Propietario:** `subscriptions/repository` y seguridad documental. **Alcance:** M.

**Descripción:** completar el diseño físico de declaración/verificación, tasas BCV, referencias privadas e historia de revisión.

**Entradas y dependencias:** C02 aceptado; T02/T04.

**Datos, contratos, transacciones y consumidores:** diseño sin bytes en PostgreSQL/sync; referencias por cuenta/reporte y datos verificados separados.

**Criterios de aceptación:**
- [ ] Estado/versión, una sola aprobación efectiva y referencia parcial no única están protegidos.
- [ ] Evidencia conserva metadatos mínimos y nunca URL pública o contenido en auditoría.

**Verificación:**
- [ ] Matriz de transiciones/rechazo/nueva presentación contra restricciones propuestas.
- [ ] `git diff --check` y enlaces OWASP/PostgreSQL.
- [ ] Manual: seguir reporte pendiente→aprobado/rechazado→nueva presentación sin reescritura.

**Archivos previstos:** `docs/database-schema.md`, `docs/architecture.md`.

**Evidencia:** pendiente.

## T07 · Diseñar contratos HTTP, operaciones y acceso

**Estado:** Todo. **Propietario:** `subscriptions`, `accounts`, `sync` y contratos. **Alcance:** M.

**Descripción:** fijar rutas/operaciones/modelos, acciones del catálogo RBAC/ABAC, audiencias y errores sin exponer datos de otras cuentas.

**Entradas y dependencias:** T06; catálogo de autorización implementado.

**Datos, contratos, transacciones y consumidores:** diseño camelCase/page-shows, operaciones online, resultados idempotentes y sync mínimo.

**Criterios de aceptación:**
- [ ] Cuenta, operador y casos internos tienen contratos/permisos completos sin acceso clínico.
- [ ] Aprobación/rechazo, evidencia, periodos y recuperación definen transacción/versiones/errores.

**Verificación:**
- [ ] Revisión de cobertura de todos los casos de uso §20 de la especificación.
- [ ] `git diff --check` y validación de enlaces/anclas.
- [ ] Manual: recorrer respuesta perdida y objeto ajeno en presentación/aprobación/descarga.

**Archivos previstos:** `docs/api-v1.md`, `docs/access-design.md`, `docs/architecture.md`, `docs/contracts.md`.

**Evidencia:** pendiente.

## T08 · Implementar dominio de dinero, BCV y periodos

**Estado:** Todo. **Propietario:** `subscriptions/domain`. **Alcance:** M.

**Descripción:** implementar valores monetarios, tasa/fuente, redondeo y funciones puras de inicio/fin de periodos conforme a T02.

**Entradas y dependencias:** C02 aceptado; T07 define adaptadores, sin depender de ellos.

**Datos, contratos, transacciones y consumidores:** dominio sin SQL/red; `Decimal`, zona IANA e instantes finitos.

**Criterios de aceptación:**
- [ ] USD/VES, redondeo y conservación de tasa producen resultados exactos sin NaN/infinito.
- [ ] 30 días, anual, anticipado/tardío y 29 de febrero cumplen los ejemplos aprobados.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_money -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure -v` y `uv build --offline`.
- [ ] Manual: imprimir cotizaciones/periodos ficticios y comparar cada cifra/fecha con T02.

**Archivos previstos:** `src/api/subscriptions/domain/money.py`, `src/api/subscriptions/domain/periods.py`, `tests/test_subscription_money.py`.

**Evidencia:** pendiente.

## C03 · Después de T06–T08

- [ ] Diseño físico/HTTP cubre revisión, evidencia, acceso y recuperación.
- [ ] Dominio monetario/temporal pasa todos los ejemplos aprobados.
- [ ] El usuario revisa y acepta C03.

## T09 · Implementar dominio de planes, suscripciones y asientos

**Estado:** Todo. **Propietario:** `subscriptions/domain`. **Alcance:** M.

**Descripción:** implementar modelos de catálogo/versiones, estados de suscripción y función pura de cómputo/límite de asientos.

**Entradas y dependencias:** C03 aceptado; T01/T02.

**Datos, contratos, transacciones y consumidores:** esquemas base y reglas puras; no duplica pertenencias ni importa SQL.

**Criterios de aceptación:**
- [ ] Los tres planes comparten funciones y solo portan precio/asientos versionados.
- [ ] Cómputo/exceso/transiciones siguen T01 y deniegan combinaciones inválidas.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_domain -v`.
- [ ] `uv run --locked python -m unittest tests.test_accounts tests.test_subscription_domain -v`.
- [ ] Manual: evaluar miembros activos/inactivos, profesional repetido, invitación y exceso.

**Archivos previstos:** `src/api/subscriptions/domain/plans.py`, `src/api/subscriptions/domain/subscriptions.py`, `tests/test_subscription_domain.py`.

**Evidencia:** pendiente.

## T10 · Implementar dominio de reportes y revisión

**Estado:** Todo. **Propietario:** `subscriptions/domain`. **Alcance:** M.

**Descripción:** implementar payloads/respuestas de reportes, datos declarados/verificados, evidencia y transiciones pending/approved/rejected.

**Entradas y dependencias:** T09; contratos T07.

**Datos, contratos, transacciones y consumidores:** modelos estrictos, cuatro dígitos como texto, referencias privadas y sin bytes.

**Criterios de aceptación:**
- [ ] Presentar no cambia suscripción y solo operador puede decidir según tipo de actor.
- [ ] Rechazo/nueva presentación y duplicados conservan historia y estados válidos.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_reports -v`.
- [ ] `uv run --locked python -m unittest tests.test_project_structure tests.test_subscription_reports -v`.
- [ ] Manual: validar referencias con ceros iniciales, captura ausente/presente y datos declarados frente a verificados.

**Archivos previstos:** `src/api/subscriptions/domain/reports.py`, `src/api/subscriptions/domain/reviews.py`, `tests/test_subscription_reports.py`.

**Evidencia:** pendiente.

## T11 · Implementar identidad y contexto limitado del operador

**Estado:** Todo. **Propietario:** `authorization` y `subscriptions`. **Alcance:** M.

**Descripción:** implementar el mecanismo T03 con alta/recuperación/revocación y acciones cerradas de plataforma, sin rol de cuenta.

**Entradas y dependencias:** T10; T03 y fuentes oficiales del mecanismo seleccionado.

**Datos, contratos, transacciones y consumidores:** credenciales/identidad según diseño, auditoría y transacciones coordinadas; sin sesiones API del personal añadidas.

**Criterios de aceptación:**
- [ ] Operador vigente accede solo a acciones aprobadas y revocado pierde acceso.
- [ ] Operador no lee pacientes/clínica ni se convierte en owner/assistant.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_operator tests.test_access_credentials -v`.
- [ ] `./.venv/Scripts/python.exe test-support/access/check.py` y `uv build --offline`.
- [ ] Manual: autenticar, revocar y probar revisión permitida frente a lectura clínica denegada.

**Archivos previstos:** módulos `src/api/subscriptions/{domain,application,repository,infrastructure}/` y `tests/test_subscription_operator.py`, máximo cinco archivos según mecanismo T03.

**Evidencia:** pendiente.

## C04 · Después de T09–T11

- [ ] Reglas de dominio y operador pasan pruebas de alcance.
- [ ] No existe acceso clínico o rol de cuenta implícito.
- [ ] El usuario revisa y acepta C04.

## T12 · Implementar persistencia del núcleo comercial

**Estado:** Todo. **Propietario:** `subscriptions/repository` y migraciones. **Alcance:** M.

**Descripción:** crear migración, modelos SQLAlchemy y DAOs para planes/versiones, suscripciones/periodos con restricciones y privilegios mínimos.

**Entradas y dependencias:** C04 aceptado; T05.

**Datos, contratos, transacciones y consumidores:** DAOs derivados commit=False; FK/CHECK/UQ/exclusión y transacciones del caso.

**Criterios de aceptación:**
- [ ] Migración up/down/reapply conserva integridad, moneda e intervalos sin solape.
- [ ] Rol operativo no tiene DDL ni escritura fuera de DAOs/casos previstos.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_persistence -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: inspeccionar SQL de periodos solapados, origen duplicado y rollback de una revisión fallida.

**Archivos previstos:** `migrations/versions/<revisión>_subscriptions_core.py`, `src/api/subscriptions/repository/models.py`, `src/api/subscriptions/repository/dao.py`, `tests/test_subscription_persistence.py`.

**Evidencia:** pendiente.

## T13 · Implementar persistencia de reportes y revisión

**Estado:** Todo. **Propietario:** `subscriptions/repository` y migraciones. **Alcance:** M.

**Descripción:** añadir tasas, reportes, revisiones y metadatos de evidencia con historia y coordinación de estados.

**Entradas y dependencias:** T12; T06.

**Datos, contratos, transacciones y consumidores:** misma sesión/DAOs commit=False, sin bytes ni URL pública; aislamiento por cuenta.

**Criterios de aceptación:**
- [ ] Una aprobación ordinaria produce como máximo un efecto y referencias parciales no son UQ global.
- [ ] Declaración/historia no se reescribe y evidencia no cruza cuentas.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_persistence tests.test_subscription_reports -v`.
- [ ] `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: intentar doble aprobación SQL, modificar declaración y cruzar evidencia/cuenta.

**Archivos previstos:** `migrations/versions/<revisión>_subscription_reports.py`, `src/api/subscriptions/repository/models.py`, `src/api/subscriptions/repository/dao.py`, `tests/test_subscription_persistence.py`.

**Evidencia:** pendiente.

## T14 · Implementar administración versionada de planes

**Estado:** Todo. **Propietario:** `subscriptions/application` e `infrastructure`. **Alcance:** M.

**Descripción:** implementar casos/rutas de operador para crear/versionar/retirar planes y precios sin alterar periodos/cotizaciones anteriores.

**Entradas y dependencias:** T13; operador T11 y contratos T07.

**Datos, contratos, transacciones y consumidores:** operaciones online idempotentes, historia/auditoría y versiones esperadas.

**Criterios de aceptación:**
- [ ] Nuevas cotizaciones usan versión vigente y las históricas permanecen estables.
- [ ] Solo acción de catálogo autorizada cambia planes; retirar conserva historia.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_catalog -v`.
- [ ] `uv build --offline` y `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: cambiar precio/asientos y comprobar que una suscripción anterior conserva valores.

**Archivos previstos:** `src/api/subscriptions/application/catalog_cases.py`, `src/api/subscriptions/infrastructure/catalog_api.py`, `src/application.py`, `tests/test_subscription_catalog.py`.

**Evidencia:** pendiente.

## C05 · Después de T12–T14

- [ ] Migraciones, privilegios y catálogo versionado pasan.
- [ ] Los datos históricos no cambian al editar planes.
- [ ] El usuario revisa y acepta C05.

## T15 · Implementar tasas BCV y cotizaciones

**Estado:** Todo. **Propietario:** `subscriptions`. **Alcance:** M.

**Descripción:** implementar registro/selección de tasas por operador y cotización de plan/periodicidad para cuenta autorizada.

**Entradas y dependencias:** C05 aceptado; T02/T08/T14.

**Datos, contratos, transacciones y consumidores:** tasa/fuente histórica, decimal exacto, operaciones online y lectura propia.

**Criterios de aceptación:**
- [ ] Cotización conserva plan/versión, USD, tasa/fecha/fuente, VES y redondeo.
- [ ] Días sin publicación y correcciones siguen T02 sin elegir tasa del cliente.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_quotes tests.test_subscription_money -v`.
- [ ] `uv build --offline` y pruebas HTTP ASGI incluidas en el módulo enfocado.
- [ ] Manual: cotizar dos periodicidades y repetir tras nueva tasa sin alterar la primera cotización.

**Archivos previstos:** `src/api/subscriptions/application/quote_cases.py`, `src/api/subscriptions/infrastructure/quotes_api.py`, `tests/test_subscription_quotes.py`.

**Evidencia:** pendiente.

## T16 · Integrar límite de asientos con pertenencias y planes

**Estado:** Todo. **Propietario:** `accounts` y `subscriptions`. **Alcance:** M.

**Descripción:** invocar el caso de asientos al aceptar/reactivar/cambiar plan con coordinación transaccional y proyección de consumo.

**Entradas y dependencias:** T15; catálogo de autorización y T01.

**Datos, contratos, transacciones y consumidores:** misma transacción de invitación/pertenencia/cambio, recibo/auditoría/época conservados.

**Criterios de aceptación:**
- [ ] Dos aceptaciones/reactivaciones no superan el límite y la última plaza tiene un solo ganador.
- [ ] Reducción con exceso no desactiva usuarios y bloquea nuevas incorporaciones según T01.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_seats tests.test_account_changes -v`.
- [ ] `./.venv/Scripts/python.exe test-support/team/check.py` y `./.venv/Scripts/python.exe test-support/persistence/check.py`.
- [ ] Manual: disputar última plaza con dos conexiones y revisar miembros/versión/recibo finales.

**Archivos previstos:** `src/api/accounts/application/invitations_cases.py`, `src/api/subscriptions/application/seat_cases.py`, `tests/test_subscription_seats.py`, `test-support/team/check.py`.

**Evidencia:** pendiente.

## T17 · Seleccionar e implementar almacenamiento privado de evidencias

**Estado:** Todo. **Propietario:** `core/services`, `subscriptions` y seguridad. **Alcance:** M.

**Descripción:** comparar la opción mínima con APIs/versiones oficiales, justificar elección e implementar carga/descarga autorizada y limpieza segura.

**Entradas y dependencias:** T16; T04, manifiesto/lockfile y guía docs-first.

**Datos, contratos, transacciones y consumidores:** bytes fuera de DB/sync/webroot, nombres generados, validación real y límites T04.

**Criterios de aceptación:**
- [ ] La decisión/versión/fuente oficial queda registrada y no hay dependencia injustificada.
- [ ] Tipo/tamaño/nombre, aislamiento y descarga reautorizada cumplen OWASP sin logs sensibles.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_evidence -v`.
- [ ] `uv build --offline` y revisión de lockfile/artefactos si cambia una dependencia justificada.
- [ ] Manual: subir archivo válido/falso/grande, descargar con cuenta autorizada/ajena y revisar logs.

**Archivos previstos:** `src/core/services/subscription_evidence.py`, `src/settings/`, `src/api/subscriptions/application/evidence_cases.py`, `tests/test_subscription_evidence.py`, `docs/operations/development.md`.

**Evidencia:** pendiente.

## C06 · Después de T15–T17

- [ ] Cotización, asientos y evidencia privada pasan pruebas enfocadas/reales.
- [ ] La elección de almacenamiento está sustentada y no hay fuga de archivos.
- [ ] El usuario revisa y acepta C06.

## T18 · Implementar presentación y consulta de reportes por la cuenta

**Estado:** Todo. **Propietario:** `subscriptions` y `sync`. **Alcance:** M.

**Descripción:** implementar reporte online con evidencia, listas/detalle propios, recuperación idempotente y probe HTTP real.

**Entradas y dependencias:** C06 aceptado; contratos T07.

**Datos, contratos, transacciones y consumidores:** cuenta/propietario autorizado, reporte/metadatos/recibo/auditoría atómicos; bytes fuera de transacción.

**Criterios de aceptación:**
- [ ] Presentar deja `pending` sin activar/extender y respuesta perdida recupera el mismo reporte.
- [ ] Una cuenta no lista/detalla/descarga reportes de otra.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_reports -v`.
- [ ] `./.venv/Scripts/python.exe test-support/subscriptions/check.py`.
- [ ] Manual: enviar reporte, cortar respuesta tras commit, reintentar y verificar un único registro/periodo ausente.

**Archivos previstos:** `src/api/subscriptions/application/report_cases.py`, `src/api/subscriptions/infrastructure/reports_api.py`, `tests/test_subscription_reports.py`, `test-support/subscriptions/check.py`.

**Evidencia:** pendiente.

## T19 · Implementar bandeja y detalle de revisión del operador

**Estado:** Todo. **Propietario:** `subscriptions` y seguridad. **Alcance:** M.

**Descripción:** implementar lista paginada de pendientes/historia, detalle y descarga de evidencia con filtros autorizados.

**Entradas y dependencias:** T18; operador T11.

**Datos, contratos, transacciones y consumidores:** page/shows, autorización antes de total, lecturas auditadas sin contenido sensible.

**Criterios de aceptación:**
- [ ] Operador ve solo campos/acciones de revisión y ninguna información clínica.
- [ ] Paginación/descarga reautoriza y no revela cuentas fuera de su alcance.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_operator tests.test_subscription_reports -v`.
- [ ] `./.venv/Scripts/python.exe test-support/subscriptions/check.py`.
- [ ] Manual: revisar páginas/filtros y evidencia con operador válido, revocado y acción de catálogo solamente.

**Archivos previstos:** `src/api/subscriptions/application/review_cases.py`, `src/api/subscriptions/infrastructure/reviews_api.py`, `tests/test_subscription_operator.py`.

**Evidencia:** pendiente.

## T20 · Implementar aprobación atómica y periodos únicos

**Estado:** Todo. **Propietario:** `subscriptions`, `sync` y `audit`. **Alcance:** M.

**Descripción:** implementar aprobación con datos verificados, tasa/precio congelados, cálculo de periodo y todos los efectos en una transacción.

**Entradas y dependencias:** T19; T12/T13 y reglas T02.

**Datos, contratos, transacciones y consumidores:** reporte/suscripción/periodo/historia/auditoría/recibo/grupo coordinados; sin red dentro.

**Criterios de aceptación:**
- [ ] Aprobación inicial/extensión crea exactamente un periodo coherente y una decisión de operador.
- [ ] Respuesta perdida/dos operadores no duplican periodo, días, recibo o historia.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_approval tests.test_subscription_money -v`.
- [ ] `./.venv/Scripts/python.exe test-support/subscriptions/check.py` y `./.venv/Scripts/python.exe test-support/sync/check.py`.
- [ ] Manual: ejecutar carrera de aprobación, comparar operador real, SQL y recuperación tras respuesta perdida.

**Archivos previstos:** `src/api/subscriptions/application/review_cases.py`, `src/api/sync/application/operations_cases.py`, `tests/test_subscription_approval.py`, `test-support/subscriptions/check.py`.

**Evidencia:** pendiente.

## C07 · Después de T18–T20

- [ ] Presentar no activa y aprobar activa/extiende una sola vez.
- [ ] Bandeja, evidencia, aislamiento y respuestas perdidas pasan.
- [ ] El usuario revisa y acepta C07.

## T21 · Implementar rechazo y nueva presentación

**Estado:** Todo. **Propietario:** `subscriptions`. **Alcance:** M.

**Descripción:** añadir rechazo con motivo seguro y nueva presentación relacionada sin reabrir/reescribir historia.

**Entradas y dependencias:** C07 aceptado; T04/T10.

**Datos, contratos, transacciones y consumidores:** suscripción/periodo anterior sin cambio; revisión/auditoría/recibo en una transacción.

**Criterios de aceptación:**
- [ ] Rechazo no crea pago/periodo ni cambia acceso comercial anterior.
- [ ] Nueva presentación conserva vínculo e historia y vuelve a pending sin duplicar aprobación anterior.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_reports tests.test_subscription_approval -v`.
- [ ] `./.venv/Scripts/python.exe test-support/subscriptions/check.py`.
- [ ] Manual: rechazar, corregir, reenviar y aprobar una sola vez revisando toda la cadena.

**Archivos previstos:** `src/api/subscriptions/application/review_cases.py`, `src/api/subscriptions/application/report_cases.py`, `tests/test_subscription_reports.py`.

**Evidencia:** pendiente.

## T22 · Implementar proyección comercial en snapshot/delta/SSE

**Estado:** Todo. **Propietario:** `sync` y `subscriptions`. **Alcance:** M.

**Descripción:** publicar disponibilidad/plan/asientos según audiencia, con versión comercial y recuperación sin evidencia ni datos financieros innecesarios.

**Entradas y dependencias:** T21; contratos T07.

**Datos, contratos, transacciones y consumidores:** captura/grupos/cursor/época aplicables, avisos mínimos y proyecciones validadas antes del commit.

**Criterios de aceptación:**
- [ ] Miembros/propietario reciben solo su proyección y captura/delta recuperan aprobaciones perdidas.
- [ ] Capturas, tasas, reportes y evidencias no aparecen en audiencias generales.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_downloads tests.test_events tests.test_subscription_sync -v`.
- [ ] `./.venv/Scripts/python.exe test-support/downloads/check.py` y `./.venv/Scripts/python.exe test-support/events/check.py`.
- [ ] Manual: aprobar con aviso perdido, reconectar y recuperar versión/periodo sin captura en el journal.

**Archivos previstos:** `src/api/sync/application/snapshot_cases.py`, `src/api/sync/application/download_cases.py`, `src/api/sync/application/events_cases.py`, `src/api/sync/domain/downloads.py`, `tests/test_subscription_sync.py`.

**Evidencia:** pendiente.

## T23 · Implementar renovación, cambio de plan y cancelación

**Estado:** Todo. **Propietario:** `subscriptions`. **Alcance:** M.

**Descripción:** completar compras anticipadas/tardías, cambio según T04 y cancelación conservando tiempo pagado e historia.

**Entradas y dependencias:** T22; T01/T02/T04.

**Datos, contratos, transacciones y consumidores:** coordinación suscripción/plan/reporte/periodo, recibos y cambios en una aceptación.

**Criterios de aceptación:**
- [ ] Anticipado no pierde días, tardío usa inicio aprobado y periodos no se solapan.
- [ ] Cambio/cancelación respeta asientos, prorrateo elegido y tiempo pagado sin borrado.

**Verificación:**
- [ ] `uv run --locked python -m unittest tests.test_subscription_renewals tests.test_subscription_seats -v`.
- [ ] `./.venv/Scripts/python.exe test-support/subscriptions/check.py`.
- [ ] Manual: renovar antes/después, cambiar plan y cancelar con carrera de aprobación/cambio.

**Archivos previstos:** `src/api/subscriptions/application/subscription_cases.py`, `tests/test_subscription_renewals.py`, `test-support/subscriptions/check.py`.

**Evidencia:** pendiente.

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
