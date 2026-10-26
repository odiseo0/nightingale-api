# Estado y evidencia: P-20261024-01-desktop-shared-api

**Plan:** [plan.md](plan.md). **Estado:** In progress. **Actualizado:** 2026-10-26.

El usuario aprobó el plan al pedir «Por favor, implementa este plan». El usuario aceptó después C01 al decir «Válido, puedes continuar con el objetivo, por favor». Tras revertir la primera continuación, autorizó retomar el trabajo con su estilo de código. C01 conserva su aceptación. Una tarea a la vez, sin delegación. Los estados se registran solo tras comprobar.

## Resumen

| ID | Estado | Resultado |
|---|---|---|
| T01 | Done | Documentar el plan sucesor |
| T02 | Done | Fijar el contrato HTTP v1 |
| T03 | Done | Ampliar el esquema de diseño |
| T04 | Done | Recuperar la base de proceso |
| T05 | Done | Preparar el entorno aislado |
| T06 | Done | Preparar migraciones y coordinación |
| T07 | Done | Registro propio, recibos y resultados atómicos comprobados |
| T08 | Done | Emitir credenciales de dispositivo |
| T09 | Done | Alta atómica y seis lecturas HTTP propias comprobadas |
| T10 | Done | Invitaciones dirigidas y pertenencias comprobadas |
| T11 | Done | Cuenta, perfil y dispositivos por cuenta comprobados |
| T12 | Done | Consulta protegida, controles y mantenimiento comprobados |
| T13 | Done | Borradores, documentos opcionales y aislamiento comprobados |
| T14 | Done | Contactos reutilizables, vínculos y constancias comprobados |
| T15 | Done | Completitud y documentos declarados con integridad diferida comprobados |
| T16 | Todo | Gestionar catálogo propio |
| T17 | Todo | Gestionar ofertas por cuenta |
| T18 | Todo | Gestionar reglas semanales |
| T19 | Todo | Gestionar excepciones diarias |
| T20 | Todo | Gestionar bloqueos |
| T21 | Todo | Consultar disponibilidad |
| T22 | Todo | Crear citas |
| T23 | Todo | Confirmar citas |
| T24 | Todo | Reprogramar citas |
| T25 | Todo | Cancelar citas |
| T26 | Todo | Registrar resultado de asistencia |
| T27 | Todo | Proteger historia funcional |
| T28 | Todo | Descargar cambios confirmados |
| T29 | Todo | Materializar snapshot coherente |
| T30 | Todo | Recuperar tras vencimiento |
| T31 | Todo | Avisar cambios por SSE |
| T32 | Todo | Probar colaboración concurrente |
| T33 | Todo | Entregar el contrato y su evidencia |
| T34 | Done | Reglas y ampliación comprobadas; 45 tareas y 15 checkpoints |
| T35 | Done | Contrato 1.1: camelCase, page/shows y avance incremental separado |
| T36 | Done | Errores comunes y transacción comprobados; C12 para revisión |
| T37 | Done | Esquemas base y modelos de authorization comprobados |
| T38 | Done | Tres DAOs derivados; commit y rollback PostgreSQL comprobados |
| T39 | Done | Cuatro rutas y casos corregidos; C13 listo para revisión |
| T40 | Done | Esquemas base y cinco modelos de accounts separados |
| T41 | Done | Cinco DAOs derivados, ámbito y commit real comprobados |
| T42 | Done | Casos y sync corregidos; C14 listo para revisión |
| T43 | Done | Soporte de cursores retirado; listas usan LIMIT/OFFSET |
| T44 | Done | Script pequeño probado con configuración inválida y PostgreSQL real |
| T45 | Done | Corrección comprobada; C15 listo para revisión |

## Registros de tarea

### T01: Documentar el plan sucesor

**Estado:** Done. **Propietario:** documentación. **Tamaño previsto:** S.

**Entrada/dependencias:** plan aprobado y fuentes actuales.

**Aceptación:**

- [x] La aprobación y la sustitución quedan registradas sin cambiar aceptaciones previas.
- [x] Las 33 tareas y 11 checkpoints conservan sus IDs y dependencias.
- [x] El índice dirige al plan nuevo y conserva los pendientes posteriores.

**Comprobación:** Revisar sucesión, estados e IDs. Controles documentales de enlaces, IDs, diccionario y huellas; sin pruebas de producto ni build.

**Archivos previstos:** tasks/README.md; plan.md; todo.md; plan.md y todo.md del plan anterior. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** No afecta a transacciones ejecutables; fija alcance y orden para API y su consumidor Rust.

**Evidencia:** T01: control Node.js 24.18.0 de IDs: 33 tareas y 11 checkpoints, mismas tareas en plan/lista y dependencias secuenciales; sucesión enlazada sin aceptar checkpoints anteriores o nuevos. Índice y encabezados históricos revisados.

### T02: Fijar el contrato HTTP v1

**Estado:** Done. **Propietario:** contratos y acceso. **Tamaño previsto:** M.

**Entrada/dependencias:** T01 comprobada.

**Aceptación:**

- [x] El catálogo enumera todas las rutas, permisos y modelos de entrada/salida previstos.
- [x] Las operaciones tienen claves, campos permitidos y resultados definidos por acción.
- [x] Acceso y decisiones distinguen token sin vencimiento, OIDC y exclusiones.

**Comprobación:** Contrastar cada ruta y operación con el plan aprobado. Controles documentales de enlaces, IDs, diccionario y huellas; sin pruebas de producto ni build.

**Archivos previstos:** docs/api-v1.md; docs/contracts.md; docs/access-design.md; docs/decisions.md; AGENTS.md. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Fuente del transporte y acceso para Rust; no crea rutas ni modelos Python.

**Evidencia:** T02: catálogo contrastado con el plan aprobado: 47 rutas de diseño y 42 acciones únicas, sin duplicados. Tabla de campos/permisos/resultados y JSON ficticio válidos; Markdown corregido y comprobado. Sin rutas, DTO ni artefactos ejecutables creados.

### T03: Ampliar el esquema de diseño

**Estado:** Done. **Propietario:** datos. **Tamaño previsto:** M.

**Entrada/dependencias:** T02 comprobada.

**Aceptación:**

- [x] El diccionario cubre versiones, margen de ausencia y las diez tablas técnicas.
- [x] Las claves, ámbitos, índices y conservación tienen reglas explícitas.
- [x] Las reglas antiguas sustituidas se identifican; no cambia código ni se ejecuta SQL.

**Comprobación:** Contrastar diccionario, referencias y reglas frente a contrato. Controles documentales de enlaces, IDs, diccionario y huellas; sin pruebas de producto ni build.

**Archivos previstos:** docs/database-schema.md; docs/nightingale-api.md; README.md; docs/operations/development.md; docs/contracts.md (alineación de alcance). Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Fuente única del diseño persistente; describe el límite atómico y proyecciones, sin migraciones.

**Evidencia:** T03: 27 diccionarios, 300 columnas, 53 FK con columnas/tipos compatibles y destinos PK/UQ contrastados; 17 diagramas de entidades del núcleo con 189 atributos coincidentes. 49 archivos protegidos de código/pruebas/manifiesto/lockfile/configuración conservan SHA-256. Sin SQL, ORM, migraciones, instalación o render nuevo.

### T04: Recuperar la base de proceso

**Estado:** Done. **Propietario:** composición. **Tamaño previsto:** M.

**Entrada/dependencias:** T03 comprobada; C01 aceptado. Nueva autorización para continuar con el estilo actual; no repetir la reescritura retirada.

**Aceptación:**

- [x] Arranque y cierre administran recursos por lifespan sin conexiones al importar.
- [x] Configuración y salud tienen pruebas que corresponden al código actual.
- [x] El punto de entrada del manifiesto usa la app de módulo y el paquete se construye. Por instrucción posterior del usuario, se omite la prueba HTTP separada del wheel.

**Comprobación:** Iniciar sin base y con configuración inválida; comprobar cierre. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/application.py; src/api/health.py; src/core/utils/__init__.py; src/settings/db_settings.py; tests/test_foundation.py. Motor/sesiones/exportaciones de core.db quedan intactos. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** No hay negocio ni sync; habilita recursos de HTTP y PostgreSQL.

**Evidencia:** 12 pruebas de unittest correctas con Python 3.15.1 del entorno existente; configuración, app de módulo, salud, timeout, cierre, dependencia de sesiones y destino del comando de pyproject.toml. uv build --offline construye sdist y wheel sin cambios en manifiesto ni lockfile. Las huellas SHA-256 de session.py, deps.py y core/db/__init__.py coinciden con el estado previo del usuario. Sin PostgreSQL real. El usuario pidió omitir la comprobación HTTP separada del wheel y su solicitud de permiso; no se acredita esa ejecución ni se exige para continuar. Esto no acepta C02.

### T05: Preparar el entorno aislado

**Estado:** Done. **Propietario:** operación. **Tamaño previsto:** M.

**Entrada/dependencias:** T04 comprobada.

**Recorrido concreto:** usar las herramientas locales comprobadas, sin Docker ni actualizar PostgreSQL personal. Preparar primero un realm ficticio y comandos para carpetas separadas bajo .tmp; después comprobar servicios y OIDC. No incorporar adaptadores de acceso de producto en esta tarea. La comprobación HTTP separada del wheel queda excluida por instrucción del usuario.

**Aceptación:**

- [x] Entorno local separa desarrollo y pruebas sin Docker ni bases personales.
- [x] Keycloak conserva su perfil Authorization Code con PKCE y sujetos ficticios; registrar evidencia real o impedimento, sin sustituir proveedor.
- [x] Se fijan versiones/artefactos y comandos locales comprobados; no se despliega.

**Comprobación:** Comprobar servicios, aislamiento y flujo OIDC real. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** entorno de prueba sin requisito de Docker; .env.example; test-support/oidc/realm.json; docs/operations/development.md; pyproject.toml/uv.lock. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Proveedor externo fuera de las transacciones; API permanece como único dueño operativo.

**Evidencia:** PostgreSQL 18.3 nativo: Test 127.0.0.1:55433 y Development 127.0.0.1:55432 responden con distintos system_identifier; arranque/cierre comprobados mediante postgres.ps1. Java Corretto 21.0.6 y Keycloak 26.8.1 ZIP oficial; SHA1 oficial coincidente 616f35b37fb9ce12f07487bd7fe52ecc3684bdd4; SHA256 local 4cd312c889af358a819a74a6c6f068f9ea159a6959e49924607cec95cfd4c1a4. Realm importado y check.py correcto: tres sujetos distintos, canje S256, audiencia/emisor y rechazos de código repetido, verifier incorrecto, PKCE ausente y password grant. HTTPS 18443 con PEM de prueba validado por SSLContext; no verify=False ni cambios a cookies Secure. Las pruebas no validan firmas para la API ni su autorización, que pertenecen a T08. Keycloak y PostgreSQL Development detenidos al terminar; Test sigue activo para T06. Sin Docker, dependencias Python nuevas, bases personales o despliegue. Fuentes y comandos en test-support/README.md.

### T06: Preparar migraciones y coordinación

**Estado:** Done. **Propietario:** persistencia. **Tamaño previsto:** M.

**Entrada/dependencias:** T05 comprobada.

**Recorrido concreto y división:** T06.1 incorpora Alembic 1.20.1, configuración async y una revisión útil para separar el esquema operativo y sus permisos (manifiesto/lockfile, alembic.ini, env.py y revisión). T06.2 añade bootstrap de roles ficticios, comprobaciones PostgreSQL y comandos documentados. No crear las 27 tablas ni modelos vacíos: identidad, cuentas y su coordinación completa se añaden con sus casos T08/T09. Las pruebas iniciales usan filas de prueba para comprobar rollback y bloqueo con la fábrica existente; no se presentan como autorización o sync de producto. Cada recorrido se comprueba antes del siguiente.

**Aceptación:**

- [x] Alembic migra la base técnica; tablas de acceso/cuenta se añaden con su caso, no todos los componentes de antemano.
- [x] Identidades SQL separadas; aplicación conserva el commit al usar db.begin() y el DAO existente con commit=False.
- [x] Pruebas PostgreSQL demuestran rollback y orden de coordinación inicial.

**Comprobación:** `uv run --locked python test-support/persistence/check.py`: migrar desde vacío, provocar fallo, comprobar rollback, permisos y coordinación inicial con conexiones reales. `uv run --locked python -m unittest discover -s tests -v`; `uv build --offline` al cerrar C02. La comprobación HTTP separada del wheel queda omitida por petición del usuario.

**Archivos previstos:** alembic.ini; migrations/env.py; migrations/versions/; src/core/db/; tests/persistence/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Técnica y acceso inicial; cada componente añadirá después su migración, con prueba real.

**Evidencia:** Alembic 1.20.1 y Mako 1.4.3 añadidos con uv; ninguna otra versión resuelta cambió. SQL offline comprobado; revisión 20261024_01 aplicada/revertida/reaplicada en base aleatoria del clúster Test 18.3. Crea solo namespace y permisos, sin tablas de negocio. Revisión ficticia fallida revierte su tabla y mantiene la versión previa. Identidad operativa no crea tablas en public/nightingale ni asume el rol migrador. Un create real del DAO existente con commit=False se revierte al fallar otra escritura; el DAO no se modificó. Dos conexiones distintas, barreras y pg_blocking_pids demuestran espera y observación del commit anterior. Preparación consulta PostgreSQL real; zona y codec funcionan tras corregir solo await_ por run_async en el hook de session.py. 12 pruebas unitarias finales correctas mediante uv run --locked; build offline correcto. Cada ejecución elimina solo su base de nombre generado; clúster Test detenido al terminar. No autorización, idempotencia, tablas de producto, consumidor de escritorio ni concurrencia entre dos procesos de API acreditados.

### T07: Aceptar operaciones con idempotencia

**Estado:** Done. **Propietario:** sync. **Tamaño previsto:** M.

**Entrada/dependencias:** T09 comprobada; orden T08 → T09 → T07 aprobado por el usuario el 2026-10-25. Recibos y autorización usan las identidades, pertenencias y dispositivos reales de esas tareas.

**División de ejecución (2026-10-26):** T07.1 define envoltorios/resultados y persistencia técnica de recibos, journal y auditoría con migración. T07.2 coordina autorización vigente, registro propio de dispositivo (único efecto inicial), versiones, dependencias e idempotencia en la misma transacción. Las acciones posteriores conservan sus tareas y devuelven UNSUPPORTED_OPERATION. T07.3 conecta lote/consulta de resultado a HTTP y comprueba límites antes de efectos. T07.4 prueba PostgreSQL real: duplicados concurrentes, respuesta perdida tras commit, conflicto de cuerpo, aislamiento, rollback integral y reautorización. Sin trabajo paralelo ni aceptación anticipada de C03.

**Aceptación:**

- [x] Cada operación usa autorización, versión y recibo dentro de una transacción.
- [x] Misma clave y cuerpo recuperan resultado; otro cuerpo produce conflicto.
- [x] Lotes conservan independencia; fallos temporales no quedan fijados como rechazos.

**Comprobación:** Repetir simultáneamente y cortar la respuesta después del commit. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/sync/application/; src/api/sync/repository/; src/api/sync/infrastructure/; src/application.py; tests/sync/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Efecto, versión, historia, auditoría, recibo y cambios comparten commit; reautoriza duplicados.

**Evidencia (2026-10-26):** Lote y consulta de resultado HTTP conectados, con RegisterAccountDevice como primer efecto real. El registro exige instalación propia y autorización vigente; no restaura una autorización revocada. Cuenta/control/filas/recibo mantienen el orden de bloqueo tras identidad. Misma sesión y commit=False coordinan acceso, versión 1, época, posición, grupo owner, recibo y hecho audit; no corresponde historia funcional de citas a esta acción. La revisión 20261026_01 añade las tres tablas técnicas, restricciones/FK, inmutabilidad y control diferido del grupo/frontera; rol operativo sin UPDATE/DELETE en historia. transaction(db) traduce DBAPIError después del rollback, conserva errores de programación/cancelación y no abre otra sesión.

Probe test-support/sync/check.py correcto con PostgreSQL/Keycloak reales: dos solicitudes concurrentes producen accepted/duplicate y un solo efecto/recibo/auditoría/grupo; omisión de campos opcionales conserva huella y otro cuerpo produce conflicto. Payload inválido conserva texto exacto para la huella y solo guarda rechazo seguro. Claves aisladas por actor/cuenta y recuperación desde otra instalación propia ya autorizada. Respuesta perdida en ASGI tras commit recupera el resultado sin efecto nuevo. Fallos CHECK inmediato y de grupo diferido revierten acceso/época/posición/recibo/auditoría/cambio y permiten reintentar. Un lote con fallo temporal y dependencia temporal conserva el independiente y no fija recibos temporales. La prueba observa pg_blocking_pids y relee la revocación tras esperar un bloqueo real. Límites 1–100 operaciones, 1 MiB de cuerpo y 64 KiB por operación, orden de dependencias y campos extra rechazan antes de efectos. Recibo ficticio antiguo devuelve 410, conserva clave/huella tras purga y rechaza contenido distinto; se sustituye el reloj del DAO para preparar esa fixture, sin cambiar el reloj del servicio.

Suite final de 71 pruebas correcta en 33.383 s; 25 controles de estructura y tres generales sin excepciones nuevas. Probes finales de acceso, cuentas, sync y persistencia correctos; upgrade/downgrade/reaplicación del head (12 tablas), fallo de migración sin DDL parcial, permisos y dos escritores. uv build --offline produce sdist/wheel; inspección de 111 entradas confirma rutas/casos nuevos y ausencia de módulos retirados o archivos privados. git diff --check correcto. Sin nuevas dependencias, cambios a fábrica/DAO base/esquema base, commits, despliegues, servicios iniciados/detenidos ni otros repositorios. Solo bases ficticias verificadas y eliminadas. No se ejecuta la prueba HTTP separada del wheel. Sin consumidor Rust/Hub ni caída TCP real; catálogo posterior, invitaciones, gestión de permisos, consulta de auditoría, snapshot, descarga y SSE siguen en sus tareas. Detenido en C03 sin aceptar.

### T08: Emitir credenciales de dispositivo

**Estado:** Done. **Propietario:** access. **Tamaño previsto:** M.

**Entrada/dependencias:** T06 comprobada y C02 aceptado; nuevo orden aprobado T08 → T09 → T07.

**División de ejecución:** T08.0 adapta salud y arranque a la instrucción expresa: DI existente y Uvicorn directo, sin restaurar lifespan/main. T08.1 prepara identidad externa y credencial opaca, con sus pruebas enfocadas. T08.2 añade persistencia y límites transaccionales de emisión/rotación/revocación. T08.3 monta rutas reales y comprueba OIDC/PostgreSQL. Sin tareas paralelas ni aceptación anticipada de T08.

**Aceptación:**

- [x] OIDC solo sirve para emitir tokens opacos por dispositivo sin vencimiento.
- [x] Solo se conserva huella; rotación y revocación tienen comprobación real.
- [x] No se aceptan ID tokens, identidades declaradas ni dispositivos ajenos.

**Comprobación:** Emitir, usar, rotar y revocar; probar firma/emisor/audiencia incorrectos. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/access/application/; src/api/access/repository/; src/api/access/infrastructure/; src/settings/; tests/access/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Autentica actor/dispositivo para todos los consumidores; proveedor fuera del commit.

**Evidencia:** 21 pruebas unitarias correctas (12 de base adaptadas a DI/Uvicorn y nueve de credenciales). PostgreSQL 18.3 aplica/revierte/reaplica la revisión 20261025_01: app_users, devices y device_tokens con claves, huellas de 32 octetos, un token vigente por instalación e identidades/revocaciones protegidas. Integración HTTP por ASGI contra PostgreSQL y Keycloak 26.8.1 reales correcta: canje S256 previo, firma/JWKS real, rechazo de ID token e identidad inyectada, almacenamiento de solo huella, UTC, no-store/correlación, rotación concurrente con un solo éxito, aislamiento entre instalaciones y usuarios, revocación terminal y carrera revocar/rotar. Dos fallos CHECK reales revierten usuario/dispositivo o revocación anterior. No se ejecuta un servidor API ni el test HTTP del wheel. Cuatro rutas reales: auth/config, auth/device-tokens, rotate-token y revoke. Las lecturas de cuenta/pertenencias y la aceptación de operaciones siguen en T09/T07. PyJWT 2.15.1 con crypto 50.0.2, cffi 2.1.1 y pycparser 3.12; HTTPX existente 0.28.1 declarado de forma directa. Sin cambiar versiones previas ni añadir capas al DAO.

### T09: Habilitar una consulta independiente

**Estado:** Done. **Propietario:** accounts y authorization. **Tamaño previsto:** M.

**Entrada/dependencias:** T08 comprobada históricamente; corrección T34–T45 comprobada y C15 aceptado antes de retomar. El trabajo parcial se conserva sin acreditarlo como terminado.

**División de ejecución revisada:** T09.1 conserva el esquema de cuenta, pertenencias, profesional, vínculo y control sync comprobado en T40–T42. La autorización por dispositivo se registra mediante operación en T07. Tras C15, T09.2 revisa la evidencia del alta administrativa por script pequeño de T44, sin ruta pública ni permiso obtenido solo por OIDC. T09.3 conecta las lecturas propias ya corregidas a endpoints con page/shows, LIMIT/OFFSET e items/total. T09.4 contrasta SQL, HTTP y script con dos identidades ficticias antes de pasar a T07. La corrección no añade cambios físicos ni da por terminada T09.

**Aceptación:**

- [x] Alta administrativa crea propietario, cuenta, pertenencia y profesional juntos.
- [x] Consultas propias no revelan otra cuenta ni crean permisos al autenticar.
- [x] Solo el ámbito independiente se habilita por esta etapa.

**Comprobación:** Crear consulta con sujeto ficticio; consultar con dos identidades. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/accounts/application/; src/api/accounts/repository/; src/api/accounts/infrastructure/; scripts/create_practice.py; tests/test_accounts.py; test-support/accounts/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Bootstrap atómico; no alta pública ni modificación del escritorio.

**Evidencia (2026-10-26):** Se reutilizan los casos existentes y se conectan GET /v1/me, /v1/accounts, /v1/accounts/{account_id}, /v1/accounts/{account_id}/access, /v1/me/professional y /v1/me/devices. Probe de cuentas correcto con PostgreSQL/Keycloak ya activos: tres identidades, dos cuentas, alta/script/rollback/concurrencia existentes, lecturas HTTP sin permisos creados por autenticación, aislamiento, páginas sucesivas/vacías, errores 401/403/404/422, no-store/correlación y revocación vigente. Los registros de dispositivo y pertenencias aún son fixtures; su operación pertenece a T07. Suite completa: 63 pruebas correctas en 44.633 s, incluidos controles de estructura. uv build --offline y git diff --check correctos. Sin dependencias ni cambios físicos; no prueba HTTP separada del wheel ni consumidores. C03 no aceptado.

### T10: Gestionar invitaciones

**Estado:** Done. **Propietario:** accounts. **Tamaño previsto:** M.

**Entrada/dependencias:** T07 comprobada y C03 aceptado; T08/T09 ya comprobadas en el orden revisado.

**División de ejecución:** T10.1 añade esquemas/DAO y migración de invitaciones. T10.2 conecta crear/revocar invitación y estado de asistentes al recorrido atómico existente. T10.3 añade listas y aceptación dirigida al destinatario, sin requerir una pertenencia anterior. T10.4 prueba aislamiento, caducidad, respuesta perdida y carrera aceptación/revocación en PostgreSQL real. No se renumeran IDs ni se abre trabajo paralelo.

**Aceptación:**

- [x] Invitación ligada a destinatario vence en 72 horas y se acepta una vez.
- [x] Solo propietario invita o cambia estado de asistentes.
- [x] Revocación y aceptación concurrentes dejan un único resultado autorizado.

**Comprobación:** Aceptar con usuario correcto, ajeno, vencimiento y respuesta perdida. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/accounts/application/; src/api/accounts/repository/; src/api/accounts/infrastructure/; src/application.py; tests/accounts/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Membresía, recibo, época de acceso y cambios juntos; no correo ni Hub.

**Evidencia (2026-10-26):** Migración 20261026_02 y DAO de invitaciones, listas propias/por cuenta con estado efectivo y LIMIT/OFFSET, aceptación dirigida e idempotente. CreateInvitation/RevokeInvitation/SetMembershipStatus usan el recorrido de T07; aceptación interna no se admite en el lote público. Un grupo conserva invitación y pertenencia completas, junto con recibo, auditoría y época. Una aceptación rechazada sin pertenencia no crea una para satisfacer F41 ni guarda recibo de éxito. No hay alta de dispositivo implícita.

71 pruebas correctas en 30.896 s y controles de estructura activos. test-support/team/check.py correcto con PostgreSQL/Keycloak reales: destinatario ajeno, 72 h, expiración efectiva, aceptación concurrente con un solo efecto, propietario/asistente, no transferencia de propiedad, cambios de pertenencia, revocar frente a aceptar, rollback integral con CHECK real y reintento, respuesta perdida tras commit en ASGI y recuperación. Probe de persistencia aplica/revierte/reaplica head de 13 tablas y prueba fallo de revisión sin DDL parcial. Build offline y git diff --check correctos. Servicios previos conservados, bases ficticias eliminadas. Sin nuevas dependencias, correo, Hub, consumidor ni aceptación de C04.

### T11: Gestionar cuenta y dispositivos autorizados

**Estado:** Done. **Propietario:** accounts. **Tamaño previsto:** M.

**Entrada/dependencias:** T10 comprobada.

**División de ejecución:** T11.1 añade cambios tipados de cuenta/política/estado/perfil y control de dispositivos al caso de aceptación. T11.2 conecta equipo y dispositivos de cuenta con proyecciones propias. T11.3 prueba permisos, versiones, recuperación administrativa, revocación entre cuentas y rollback. Esta etapa aún no tiene tablas de agenda/citas: no crear validadores vacíos ni acreditar su compatibilidad futura; sus tareas deben conectar esas restricciones antes de habilitarlas.

**Aceptación:**

- [x] Propietario cambia datos y políticas sin desplazar citas existentes en el alcance actual; la compatibilidad con agenda/citas aún sin implementar se conserva como límite de sus tareas.
- [x] Dispositivo se registra por el actor comprobado y no se restaura a sí mismo tras revocación.
- [x] Cambiar cuenta o acceso actualiza versiones, época y registro de cambios; la descarga conserva su tarea pendiente.

**Comprobación:** Revocar una instalación en una cuenta sin afectar las otras. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/accounts/application/; src/api/accounts/repository/; src/api/accounts/infrastructure/; src/application.py; tests/accounts/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** No confirma permisos locales; revalida referencias bajo coordinación por cuenta/profesional.

**Evidencia (2026-10-26):** UpdateAccountDetails/Policy/SetAccountStatus, UpdateProfessionalProfile y Revoke/RestoreAccountDevice reutilizan la aceptación atómica, versiones y proyecciones explícitas. El propietario puede reactivar cuenta inactiva desde dispositivo habilitado y recuperar su resultado; otras acciones quedan bloqueadas. Las identidades afectadas se bloquean en orden antes del control de cuenta; profesional antes del control al editar cuenta/perfil. Listas de miembros/dispositivos solo para propietario y profesionales para miembros, con DAO LIMIT/OFFSET y metadatos de authorization consumidos por casos públicos, sin repositorios ajenos.

74 pruebas correctas en 38.592 s. Probe de equipo real correcto: cambios tipados, texto normalizado en huella, null/campo de identidad rechazados, zona desconocida, límites de política, versión obsoleta/NO_CHANGES, reactivación y resultado perdido consultable, aislamiento del mismo dispositivo entre dos cuentas, rechazo de autorrestauración y de restauración de dispositivo global revocado. Carrera real restauración local/revocación global termina sin bloqueo ni acceso con token revocado. Probe de credenciales correcto tras ampliar los bloqueos. Build y git diff --check correctos. No hay tablas de agenda/citas ni validación de compatibilidad con ellas en este punto; no se acredita ese recorrido futuro. Sin dependencias nuevas, consumidores, snapshot o descarga implementados. C04 no aceptado.

### T12: Registrar y consultar auditoría

**Estado:** Done. **Propietario:** audit. **Tamaño previsto:** M.

**Entrada/dependencias:** T11 comprobada.

**División de ejecución:** T12.1 añade eventos de controles técnicos y consulta de auditoría por propietario, con filtros y paginación en DAO. T12.2 añade mantenimiento limitado de detalles de resultados vencidos, sin borrar recibos, journal ni auditoría. T12.3 comprueba correlación, ausencia de secretos, aislamiento, rechazo de permisos y mantenimiento repetible en PostgreSQL real; cierra documentación/pruebas y se detiene en C04.

**Aceptación:**

- [x] Aceptaciones y controles de acceso guardan evidencia técnica sin cuerpos personales.
- [x] Solo propietario consulta auditoría de su cuenta.
- [x] Mantenimiento elimina solo artefactos temporales/resultados vencidos previstos.

**Comprobación:** Recorrer una operación por correlación y revisar errores/logs. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/audit/; src/api/sync/repository/; scripts/; src/application.py; tests/audit/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Auditoría atómica con efecto; consulta y retención distintas de historia funcional.

**Evidencia (2026-10-26):** GET /v1/accounts/{account_id}/audit-events comprueba propietario/dispositivo/pertenencia/cuenta vigentes, filtra en DAO por fecha/acción/tipo/objeto y pagina con orden (occurredAt,id). El filtro de clave usa parámetro JSONB tipado. Invitaciones y auditoría serializan sus nuevos instantes en UTC con Z mediante la base existente. Alta administrativa, emisión, rotación y revocación guardan hechos mínimos en su transacción; no se registran secretos ni cuerpos. Las denegaciones HTTP 401/403/404 guardan correlación y solo actor/ámbito comprobados en una transacción propia; si falla su almacén, conservan el rechazo HTTP original sin acreditar persistencia del hecho durante esa caída. Las lecturas correctas no copian datos a auditoría.

scripts/purge_expired_results.py exige MAINTENANCE_DATABASE_URI explícita y permiso UPDATE; selecciona la URI solo en su proceso y reutiliza la fábrica existente. Retira solo result_json/asigna purged_at de resultados vencidos, sin borrar claves, huellas, estados/versiones, recibos, journal o auditoría. No hay purga anticipada de snapshots aún inexistentes ni tarea periódica añadida.

76 pruebas correctas en 48.992 s, incluidos 25 controles de estructura y tres generales sin excepciones nuevas. Los cinco probes de acceso/cuentas/sync/equipo/persistencia pasan con PostgreSQL 18.3 y Keycloak 26.8.1 reales. Equipo verifica aislamiento y filtros, correlación de denegación, consulta por propietario, ausencia de campos secretos, UTC, fallo CHECK de auditoría que revierte la rotación y mantenimiento en subprocess (rol operativo denegado; administrativo retira un resultado; repetición cero). Se conservan conteos de recibos/journal/auditoría por cuenta y huella del resultado retirado; consulta da 410 y otra huella sigue en conflicto. Fixtures antiguas usan reloj del DAO sustituido, sin cambiar PostgreSQL. Migraciones hasta 20261026_02 (13 tablas), reversión, reaplicación y fallo de revisión sin DDL parcial correctos.

Build offline de sdist/wheel correcto; inspección de 117 entradas confirma componentes nuevos y ausencia de archivos privados. Sintaxis/espacios: 41 archivos Python y 14 Markdown; 68 enlaces locales revisados, con cinco destinos históricos ausentes ya conocidos. git diff --check correcto. Fábrica, dependencias, DAO base, esquema base, manifiesto, lockfile y create_practice.py conservados. Servicios previos conservados y solo bases ficticias verificadas/eliminadas. Sin commits, despliegues ni otros repositorios; se omite el test HTTP separado del wheel. No consumidores, TCP real, pacientes/agenda/citas, snapshot, descarga, SSE ni producción acreditados. La compatibilidad de cambios de zona con reservas reales se mantiene como límite para sus tareas. Detenido en C04, sin aceptar.

### T13: Registrar fichas borrador

**Estado:** Done. **Propietario:** patients. **Tamaño previsto:** M.

**Entrada/dependencias:** T12 comprobada y C04 aceptado.

**División de ejecución (2026-10-26):** T13.1 añade esquemas de borrador/documento, modelos y migración física. T13.2 integra registro/edición/actividad con la aceptación existente y lecturas por cuenta. T13.3 activa los controles de estructura y comprueba aislamiento, versiones, concurrencia y rollback en PostgreSQL real. Una parte a la vez; T14 no comienza antes de comprobar T13.

**Aceptación:**

- [x] Alta crea identidad estable, ficha y documentos declarados opcionales juntos.
- [x] Edición respeta versión y solo afecta a la ficha autorizada.
- [x] Listados y detalle filtran cuenta, actividad y completitud.

**Comprobación:** Guardar borrador, editar desde dos versiones y buscar dentro de cuenta. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/patients/domain/; src/api/patients/application/; src/api/patients/repository/; src/api/patients/infrastructure/; tests/patients/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Identidad global no concede datos globales; produce proyección autorizada por cuenta.

**Evidencia (2026-10-26):** RegisterPatient, UpdatePatientProfile y SetPatientProfileStatus usan la aceptación existente. Tres GET autorizados ofrecen ficha, lista y documentos, con q literal por nombre/documento, estado/completitud, LIMIT/OFFSET y total por cuenta. La revisión 20261026_03 crea identidad mínima, ficha compuesta y documentos con restricciones, unicidad solo verificada y conservación de identidad/constancias. No adjunta una identidad global existente ni fusiona documentos declarados coincidentes. phonenumbers 9.0.41 es la única dependencia nueva, prevista por el contrato; valida estructura/longitud y conserva ceros significativos. Las demás versiones se conservan.

Probe test-support/patients/check.py correcto con PostgreSQL/Keycloak reales: propietario/asistente y dos cuentas, duplicado concurrente, edición desde dos versiones, búsqueda literal, datos ajenos ocultos, fechas futuras rechazadas, fallo CHECK en el segundo documento y fallo diferido del journal con rollback íntegro, reintento y respuesta perdida tras commit en ASGI. 86 pruebas correctas (48.949 s), incluidos cinco controles nuevos de estructura y cinco de validación. Persistencia aplica/revierte/reaplica head con 16 tablas; build offline y diff --check correctos. Solo bases ficticias aisladas; servicios previos conservados. Sin completar fichas, contactos, citas, consumidores o prueba HTTP del wheel; esas tareas siguen pendientes.

### T14: Gestionar contactos y vínculos

**Estado:** Done. **Propietario:** patients. **Tamaño previsto:** M.

**Entrada/dependencias:** T13 comprobada.

**División de ejecución (2026-10-26):** T14.1 define contactos/vínculos y su migración. T14.2 añade seis acciones y cuatro lecturas al componente existente. T14.3 comprueba hermanos, límites de cuenta, versiones, vigencia y conservación con PostgreSQL real. T15 conserva la integridad diferida de completitud; T14 no habilita completar fichas.

**Aceptación:**

- [x] Un contacto se reutiliza entre pacientes de una cuenta sin convertirse en usuario.
- [x] Claves compuestas impiden contactos o verificadores de otra cuenta.
- [x] Estado y vigencia no borran la relación ni conceden representación o acceso.

**Comprobación:** Hermanos con responsable común; contacto ajeno y fin de vigencia. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/patients/domain/; src/api/patients/application/; src/api/patients/repository/; src/api/patients/infrastructure/; tests/patients/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Control conjunto de completitud; vínculos unverified, sin Hub ni verificación legal.

**Evidencia (2026-10-26):** seis acciones y cuatro lecturas en patients; creación/edición/actividad de contactos y vínculos, con versiones, recibo y grupo atómicos. La revisión 20261026_04 crea las dos tablas con FK compuestas, vigencia, claves/constancias inmutables y permisos sin DELETE. Las lecturas resuelven nombres/teléfono vigentes; el journal conserva estados de entidades sin copiar sus nombres relacionados. No se crea usuario, paciente ni permiso por crear contacto o vínculo.

Probe real de pacientes correcto: hermanos con contacto común, consulta en ambos sentidos, paginación, actualización compartida, cierre/reactivación con vigencia, contacto ajeno oculto y SQLSTATE 23503 de FK de contacto/verificador de otra cuenta. Una constancia verificada preparada solo como fixture administrativa se conserva al desactivar por API; la API no ofrece verificación. 88 pruebas correctas (50.378 s); migración aplicada/revertida/reaplicada con 18 tablas, build offline y diff --check correctos. T15 conserva completar fichas y la integridad diferida entre requisitos. Servicios previos conservados, solo bases ficticias y ningún consumidor ni despliegue.

### T15: Completar fichas y añadir documentos declarados

**Estado:** Done. **Propietario:** patients. **Tamaño previsto:** M.

**Entrada/dependencias:** T14 comprobada.

**División de ejecución (2026-10-26):** T15.1 añade SetPatientCompletion y AddPatientIdentifier con la regla de identificación y un caso compartido de elegibilidad en fecha de cita. T15.2 protege retirada de requisitos antes de efectos e integridad diferida PostgreSQL de fichas/documentos/contactos/vínculos. T15.3 prueba adultos/menores, cambio de base sin cambiar identidad, pérdida de requisitos y concurrencia, y cierra C05 para revisión. No se añaden rutas de citas ni verificación.

**Aceptación:**

- [x] Documento declarado basta para own_document sin inspección física.
- [x] Excepción menor se revalida por fecha de cita y responsable vigente.
- [x] Retirar un requisito exige otra base válida o paso explícito a borrador.

**Comprobación:** Completar adulto/menor y retirar único contacto requerido. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/patients/domain/; src/api/patients/application/; src/api/patients/repository/; src/api/patients/infrastructure/; tests/patients/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Sin fusión, verificación ni corrección global; conservación de intención y versiones.

**Evidencia (2026-10-26):** SetPatientCompletion y AddPatientIdentifier reutilizan la aceptación. own_document acepta declared sin inspección física; añadir documento y cambiar la base conserva patient_id. El caso booking_patient comprueba requisitos en el instante y día local de cita, incluyendo cumpleaños y fin exclusivo de vigencia, dentro de la futura transacción autorizada de Citas. Es un caso compartido probado directamente: T22 conserva conectarlo al alta real de cita, aún inexistente. Se documenta el corte administrativo del 29 de febrero, sin afirmar edad legal.

Antes de escribir, los cambios de ficha/contacto/vínculo comprueban todos los dependientes completos y rechazan COMPLETENESS_CONFLICT sin efecto parcial. 20261026_05 añade integridad diferida coordinada por cuenta e identidad, también ante cambios SQL directos. El probe real comprueba adulto con declared, menor con responsable unverified, límite de edad en Caracas, expiración futura del responsable, retiro del único requisito rechazado, paso explícito a draft, y rollback al invalidar el único documento. Dos conexiones distintas retiran los teléfonos de dos responsables: un commit y un rechazo 23514, sin ficha complete inválida. Las rutas reautorizan una instalación nueva y una cuenta inactiva antes de leer o recuperar recibos.

Suite final de 91 pruebas correcta (63.974 s); seis probes reales correctos (acceso/cuentas/sync/equipo/pacientes/persistencia), migraciones con upgrade/downgrade/reaplicación del head de 18 tablas y build offline correcto. Revisión de 54 Python y 14 Markdown; 68 enlaces locales sin nueva ausencia, cinco destinos históricos ausentes. Wheel de 130 entradas con componentes nuevos y sin archivos privados; diff --check correcto. Sin cambios a fábrica, DAO base, esquema base ni scripts de alta; única dependencia nueva phonenumbers 9.0.41. Bases ficticias eliminadas y servicios existentes conservados. Sin prueba HTTP del wheel, consumidores, cita real, snapshot/descarga/SSE, commits, despliegue u otros repositorios. Detenido en C05 para revisión, sin aceptar ni iniciar T16.

### T16: Gestionar catálogo propio

**Estado:** Todo. **Propietario:** services. **Tamaño previsto:** M.

**Entrada/dependencias:** T15 comprobada y C05 aceptado.

**Aceptación:**

- [ ] Solo el profesional propietario crea o modifica su catálogo.
- [ ] Duración entera 1–1440 y estados tienen reglas explícitas.
- [ ] Cambios no recalculan citas ni permiten editar catálogo ajeno.

**Comprobación:** Modificar base y probar propiedad/versión. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/services/domain/; src/api/services/application/; src/api/services/repository/; src/api/services/infrastructure/; tests/services/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Catálogo global del profesional; cambios se proyectan en cuentas afectadas sin filtrar catálogo privado.

**Evidencia:** pendiente.

### T17: Gestionar ofertas por cuenta

**Estado:** Todo. **Propietario:** services. **Tamaño previsto:** M.

**Entrada/dependencias:** T16 comprobada.

**Aceptación:**

- [ ] Oferta comprueba cuenta, profesional y propiedad del servicio.
- [ ] Ajuste nulo usa base y ajuste positivo válido se conserva al reservar.
- [ ] Inactividad no cancela citas previas ni afecta otras ofertas.

**Comprobación:** Ofertar servicio propio en dos cuentas y rechazar ajeno. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/services/domain/; src/api/services/application/; src/api/services/repository/; src/api/services/infrastructure/; tests/services/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Transacción de servicio/oferta/versiones/cambios; sin escritura directa de citas.

**Evidencia:** pendiente.

### T18: Gestionar reglas semanales

**Estado:** Todo. **Propietario:** schedule. **Tamaño previsto:** M.

**Entrada/dependencias:** T17 comprobada.

**Aceptación:**

- [ ] Minutos 0–1439/1–1440, día ISO y vigencia cumplen el diccionario.
- [ ] Unión de tramos y unicidad de fin abierto no duplican disponibilidad.
- [ ] Cambio conserva citas y rechaza incompatibilidad bajo coordinación.

**Comprobación:** Jornada partida y fin 1440 con zona. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/schedule/domain/; src/api/schedule/application/; src/api/schedule/repository/; src/api/schedule/infrastructure/; tests/schedule/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** No tabla de reservas duplicada; carrera se repetirá con Citas en T32.

**Evidencia:** pendiente.

### T19: Gestionar excepciones diarias

**Estado:** Todo. **Propietario:** schedule. **Tamaño previsto:** M.

**Entrada/dependencias:** T18 comprobada y C06 aceptado.

**Aceptación:**

- [ ] Excepción activa sustituye horario habitual de esa fecha.
- [ ] closed exige extremos nulos; replacement un único intervalo válido.
- [ ] Inactivar conserva fila y no mueve citas.

**Comprobación:** Cerrar día y reabrir mediante inactivación. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/schedule/domain/; src/api/schedule/application/; src/api/schedule/repository/; src/api/schedule/infrastructure/; tests/schedule/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Control por profesional y fecha; disponibilidad derivada.

**Evidencia:** pendiente.

### T20: Gestionar bloqueos

**Estado:** Todo. **Propietario:** schedule. **Tamaño previsto:** M.

**Entrada/dependencias:** T19 comprobada.

**Aceptación:**

- [ ] Cuenta nula afecta toda actividad del profesional; valor limita ámbito.
- [ ] Bloqueos no cancelan reservas ni revelan motivos de cuentas ajenas.
- [ ] Creación/edición incompatibles con cita vigente se rechazan.

**Comprobación:** Vacaciones globales y bloqueo limitado. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/schedule/domain/; src/api/schedule/application/; src/api/schedule/repository/; src/api/schedule/infrastructure/; tests/schedule/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Coordinación común con Citas; no decisiones por consulta previa aislada.

**Evidencia:** pendiente.

### T21: Consultar disponibilidad

**Estado:** Todo. **Propietario:** schedule y appointments. **Tamaño previsto:** M.

**Entrada/dependencias:** T20 comprobada.

**Aceptación:**

- [ ] Combina reglas, excepciones, bloqueos y ocupación sin persistir huecos.
- [ ] Devuelve intervalos libres con fin exclusivo y duración solicitada válida.
- [ ] No revela datos de reservas en otras cuentas.

**Comprobación:** Comparar intervalo contiguo, cierre y ocupación global. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/schedule/application/; src/api/schedule/infrastructure/; src/api/appointments/application/; src/application.py; tests/schedule/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Consulta compuesta mediante contratos; no reserva ni garantiza futura aceptación.

**Evidencia:** pendiente.

### T22: Crear citas

**Estado:** Todo. **Propietario:** appointments. **Tamaño previsto:** M.

**Entrada/dependencias:** T21 comprobada y C07 aceptado.

**Aceptación:**

- [ ] Aceptación exige ficha completa, oferta activa, intervalo válido y permisos actuales.
- [ ] Exclusión global del profesional protege dos cuentas concurrentes.
- [ ] Primera versión, snapshots, recibo, auditoría y cambios se conservan juntos.

**Comprobación:** Dos reservas simultáneas y fallo entre cita e historia. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/appointments/domain/; src/api/appointments/application/; src/api/appointments/repository/; src/api/appointments/infrastructure/; tests/appointments/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Límite atómico completo; sin proveedores ni avisos HTTP dentro del commit.

**Evidencia:** pendiente.

### T23: Confirmar citas

**Estado:** Todo. **Propietario:** appointments. **Tamaño previsto:** M.

**Entrada/dependencias:** T22 comprobada.

**Aceptación:**

- [ ] Solo scheduled con versión y actor válidos pasa a confirmed.
- [ ] Conserva intervalo y registra confirmación/historia en el mismo commit.
- [ ] Confirmación repetida sin cambio no añade transición.

**Comprobación:** Confirmar, duplicar operación y usar versión antigua. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/appointments/domain/; src/api/appointments/application/; src/api/appointments/repository/; src/application.py; tests/appointments/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** En esta etapa actor staff; no endpoints de paciente o Hub.

**Evidencia:** pendiente.

### T24: Reprogramar citas

**Estado:** Todo. **Propietario:** appointments. **Tamaño previsto:** M.

**Entrada/dependencias:** T23 comprobada.

**Aceptación:**

- [ ] Conserva ID, referencias estables, duración y snapshots acordados.
- [ ] Nuevo intervalo válido pasa a scheduled con confirmación nula.
- [ ] Fallo conserva íntegra la reserva anterior.

**Comprobación:** Reprogramar confirmada, provocar conflicto y comprobar rollback. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/appointments/domain/; src/api/appointments/application/; src/api/appointments/repository/; src/application.py; tests/appointments/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Cita/historia/versión/resultados/cambios atómicos; sin conciliación Hub en esta etapa.

**Evidencia:** pendiente.

### T25: Cancelar citas

**Estado:** Todo. **Propietario:** appointments. **Tamaño previsto:** M.

**Entrada/dependencias:** T24 comprobada y C08 aceptado.

**Aceptación:**

- [ ] Solo estado vigente y versión actual permiten cancelar.
- [ ] Conserva intervalo, confirmación previa e historia; libera ocupación.
- [ ] Duplicados no añaden otra versión ni otra cancelación.

**Comprobación:** Cancelar y reservar intervalo liberado. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/appointments/domain/; src/api/appointments/application/; src/api/appointments/repository/; src/application.py; tests/appointments/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Transición terminal; no borrado físico ni espera automatizada.

**Evidencia:** pendiente.

### T26: Registrar resultado de asistencia

**Estado:** Todo. **Propietario:** appointments. **Tamaño previsto:** M.

**Entrada/dependencias:** T25 comprobada.

**Aceptación:**

- [ ] completed requiere inicio alcanzado; no_show inicio más margen vigente.
- [ ] Solo personal autorizado registra el resultado.
- [ ] Estado terminal conserva reserva histórica y no se reabre.

**Comprobación:** Reloj controlado antes/después del margen y estado terminal. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/appointments/domain/; src/api/appointments/application/; src/api/appointments/repository/; src/application.py; tests/appointments/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Regla administrativa; sin historia clínica ni ausencia deducida del silencio.

**Evidencia:** pendiente.

### T27: Proteger historia funcional

**Estado:** Todo. **Propietario:** appointments. **Tamaño previsto:** M.

**Entrada/dependencias:** T26 comprobada.

**Aceptación:**

- [ ] Versiones empiezan en 1 y avanzan sin huecos hasta el máximo actual.
- [ ] Valores actuales y última historia coinciden, incluidos snapshots e instantes.
- [ ] Identidad ordinaria no puede reescribir ni borrar historia.

**Comprobación:** Intentar hueco, versión futura y actualización/eliminación. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/appointments/repository/; migrations/versions/; src/api/appointments/infrastructure/; tests/appointments/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Restricciones diferidas e historia inmutable; no sustituye auditoría ni recibos.

**Evidencia:** pendiente.

### T28: Descargar cambios confirmados

**Estado:** Todo. **Propietario:** sync. **Tamaño previsto:** M.

**Entrada/dependencias:** T27 comprobada y C09 aceptado.

**Aceptación:**

- [ ] Todo escritor usa contador transaccional de cuenta; no omite commits.
- [ ] Página no divide grupo de una operación y entrega retiradas de vista.
- [ ] Cursor firmado queda ligado a cuenta, alcance y época de acceso.

**Comprobación:** Commits invertidos y continuación de varias páginas. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/sync/application/; src/api/sync/repository/; src/api/sync/infrastructure/; src/settings/; tests/sync/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** No usar secuencia precommit o fecha local como orden; productor responde tras commit.

**Evidencia:** pendiente.

### T29: Materializar snapshot coherente

**Estado:** Todo. **Propietario:** sync. **Tamaño previsto:** M.

**Entrada/dependencias:** T28 comprobada.

**Aceptación:**

- [ ] Datos y cursor base proceden de una vista PostgreSQL coherente.
- [ ] Páginas inmutables vencen en 15 minutos y no mantienen transacción entre peticiones.
- [ ] Cambio de ventana conserva protocolo de intenciones pendientes.

**Comprobación:** Crear mientras hay cambios y continuar desde cursor base. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/sync/application/; src/api/sync/repository/; src/api/sync/infrastructure/; migrations/versions/; tests/sync/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Ventana -30/+180 días por defecto; sin réplica indiscriminada de historia.

**Evidencia:** pendiente.

### T30: Recuperar tras vencimiento

**Estado:** Todo. **Propietario:** sync. **Tamaño previsto:** M.

**Entrada/dependencias:** T29 comprobada.

**Aceptación:**

- [ ] Retención mínima de cambios/resultados completos es de 90 días.
- [ ] Recibo mínimo conservado impide repetir efecto al retirar resultado.
- [ ] Cursor/snapshot/resultado vencidos requieren recuperación explícita.

**Comprobación:** Avanzar reloj y reintentar misma operación tras purga de resultado. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/sync/application/; src/api/sync/repository/; scripts/; tests/sync/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** No purgar historia/auditoría en esta etapa; fechas del cliente no deciden vigencia.

**Evidencia:** pendiente.

### T31: Avisar cambios por SSE

**Estado:** Todo. **Propietario:** sync. **Tamaño previsto:** M.

**Entrada/dependencias:** T30 comprobada y C10 aceptado.

**Aceptación:**

- [ ] SSE autentica cada conexión y revalida acceso sin sesión SQL abierta por cliente.
- [ ] LISTEN/NOTIFY funciona entre procesos y el journal permite recuperar pérdidas.
- [ ] Señales no contienen datos personales y consumidores lentos no acumulan colas.

**Comprobación:** Dos procesos, caída del listener y revocación con stream abierto. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** src/api/sync/application/; src/api/sync/infrastructure/; src/core/db/; src/application.py; tests/sync/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Aviso tras commit; no sustituye páginas ni avanza cursor aplicado.

**Evidencia:** pendiente.

### T32: Probar colaboración concurrente

**Estado:** Todo. **Propietario:** integración API. **Tamaño previsto:** M.

**Entrada/dependencias:** T31 comprobada.

**Aceptación:**

- [ ] Clientes independientes prueban reservas, versiones, duplicados y revocaciones.
- [ ] Dos procesos cumplen recuperación y objetivo local SSE con diez conexiones.
- [ ] Pruebas PostgreSQL y fallos controlados conservan estado final e historia.

**Comprobación:** Ejecutar matriz contractual con conexiones independientes. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** tests/integration/; test-support/; docs/operations/development.md. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Solo API; no se presenta como integración Rust/Hub ni producción.

**Evidencia:** pendiente.

### T33: Entregar el contrato y su evidencia

**Estado:** Todo. **Propietario:** contratos e integración API. **Tamaño previsto:** M.

**Entrada/dependencias:** T32 comprobada.

**Aceptación:**

- [ ] OpenAPI/JSON Schema generados coinciden con rutas, registro de acciones y permisos.
- [ ] Guía para Rust explica auth, lotes, conflicto, SSE, cursor y recuperación.
- [ ] Instalación/migraciones/pruebas/build reproducibles y faltantes externos constan.

**Comprobación:** Consumir ejemplos desde cliente de prueba y contrastar catálogo completo. Pruebas enfocadas del componente y `uv run --locked python -m unittest discover -s tests -v`; `uv build` al cambiar composición/paquete y al cerrar el checkpoint. Los módulos enfocados y comandos de integración aún no existen: definirlos y comprobarlos en T05/T06 antes de citarlos como disponibles.

**Archivos previstos:** docs/api-v1.md; docs/operations/development.md; contracts/; plan.md; todo.md. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Artefactos generados con origen/versión; no modifica consumidor ni habilita producción.

**Evidencia:** pendiente.

## Corrección aprobada el 2026-10-26

El usuario pidió implementar el plan de corrección. Se ejecuta antes de retomar T09 y T07. T08 conserva evidencia histórica; no acredita el código tras su traslado. La referencia histórica a una tarea preparatoria T34 retirada se conserva y no acredita estas tareas. Cada tarea se divide por recorridos pequeños antes de editar si supera cinco archivos de producto; no se añaden tareas paralelas.

T34.1 corrige reglas y arquitectura; T34.2 registra plan, tareas e índice. T35.1 corrige el contrato HTTP; T35.2 alinea contratos y decisiones; T35.3 actualiza referencias vigentes. T36.1 mueve esquemas de error y adapta serialización; T36.2 añade soporte mínimo de transacción; T36.3 comprueba el conjunto y registra límites. Son pasos de la misma tarea, no tareas activas a la vez.

### T34: Corregir reglas y registrar la ampliación

**Estado:** Done. **Propietario:** Arquitectura. **Tamaño previsto:** M.

**Entrada/dependencias:** Aprobación del usuario del 2026-10-26; estado actual de Git y referencia api/users.

**Aceptación:**

- [x] Reglas, plan y lista de tareas concuerdan con la estructura del usuario.
- [x] T34–T45 y C12–C15 conservan IDs previos, historia y revisiones sin aceptación implícita.
- [x] Solo documentación: conserva código, dependencias y modelo físico.

**Comprobación:** Control documental de enlaces, IDs, reglas y contrato; comparación de huellas de código/configuración. No acredita comportamiento ejecutable.

**Archivos previstos:** AGENTS.md, docs/architecture.md, tasks/README.md, plan.md y todo.md.

**Transacción, datos y consumidores:** No cambia transacciones ni datos. Fija límites de componentes y el contrato que usarán los consumidores.

**Evidencia:** Control Node de IDs: 45 tareas y 15 checkpoints únicos, todas las tareas de todo.md presentes en plan.md. Las 68 huellas SHA-256 de código, pruebas, migraciones, manifiesto, lockfile y .env.example coinciden con el inicio de C12. Reglas de carpetas, separación de componentes, esquema base, paginación y scripts registradas sin aceptar checkpoints.

### T35: Corregir el contrato público

**Estado:** Done. **Propietario:** Contrato. **Tamaño previsto:** M.

**Entrada/dependencias:** T34 comprobada.

**Aceptación:**

- [x] JSON público camelCase; esquemas de domain heredan de la base del proyecto.
- [x] Listas y snapshot usan page/shows, LIMIT/OFFSET e items/total; sin cursores de página.
- [x] El avance incremental conserva alcance, recuperación y grupos completos.

**Comprobación:** Control documental de enlaces, IDs, reglas y contrato; comparación de huellas de código/configuración. No acredita comportamiento ejecutable.

**Archivos previstos:** docs/api-v1.md, docs/contracts.md, docs/decisions.md; referencias vigentes de especificación y acceso.

**Transacción, datos y consumidores:** Cambia el diseño HTTP, no el esquema físico ni la implementación pendiente. No modifica consumidores.

**Evidencia:** Revisión de diseño 1.1: 47 rutas y 42 acciones únicas conservadas; ejemplo JSON válido con claves camelCase. Listas y SnapshotPage usan PaginatedResponse e items/total, page/shows y límites existentes; ChangePage/baseCursor conservan el avance incremental, alcance y recuperación. Contratos, D10, acceso, especificación y README enlazan el acuerdo vigente y distinguen diseño de implementación pendiente. Las 68 huellas protegidas siguen iguales tras T35; sin cambios físicos ni ejecución de producto por esta tarea.

### T36: Preparar errores comunes y transacciones

**Estado:** Done. **Propietario:** Soporte común. **Tamaño previsto:** M.

**Entrada/dependencias:** T35 comprobada.

**Aceptación:**

- [x] Errores comunes heredan de la base; JSON usa alias y no revela entradas, SQL ni secretos.
- [x] Transacción reutiliza la sesión recibida y confirma o revierte una sola vez, sin otra fábrica.
- [x] Pruebas de errores y coordinación pasan; se conserva la fábrica y el arranque del usuario.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** src/core/schema, src/api/errors.py, src/core/db y pruebas enfocadas.

**Transacción, datos y consumidores:** Prepara la coordinación atómica; no migra todavía casos ni endpoints de access. No ejecuta SQL de producto.

**Evidencia:** 25 pruebas correctas mediante `.venv/Scripts/python.exe -m unittest discover -s tests -v` (21.537 s), fuera del sandbox de Windows. Cuatro pruebas nuevas cubren herencia/alias de errores, PaginatedResponse existente, HTTP por ASGI con redacción/correlación/cabeceras y scope real de SQLAlchemy sin conexión (commit, rollback, cancelación, rechazo de begin anidado y reutilización de sesión). Se adaptan seis fallos previos de pruebas de fundación al código actual: URI requerida al importar y fábrica importada en deps; no se restaura código del usuario. `uv build --offline` construye sdist y wheel sin instalar dependencias. Se conserva la fábrica, get_db/session, app, esquema base, DAO y migraciones por huella. No se prueban aquí escrituras ni concurrencia PostgreSQL; se repiten al corregir credenciales/cuentas en C13/C14. No se iniciaron servicios ni servidor API; no se ejecutó el test HTTP separado del wheel.

### T37: Colocar tipos y modelos de authorization

**Estado:** Done. **Propietario:** Authorization. **Tamaño previsto:** M.

**Entrada/dependencias:** T36 comprobada y C12 aceptado.

**Aceptación:**

- [x] Esquemas, objetos de valor y errores viven en domain y usan la base cuando son esquemas.
- [x] Identidad, dispositivos globales y tokens conservan sus modelos físicos.
- [x] Imports y pruebas enfocadas funcionan sin duplicar modelos ni exponer secretos.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** src/api/authorization/domain, repository y pruebas de credenciales.

**Transacción, datos y consumidores:** No cambia tablas. Mantiene la pareja exacta issuer/subject y credenciales sin normalizarlas.

**Evidencia:** Cuatro pruebas de esquemas correctas: herencia de la base, alias camelCase, rechazo de identidad inyectada/bool/nombre vacío, proyección explícita y UTC, secreto fuera de repr, identidad/configuración externa sin recorte. Importación con URI ficticia sin conexión: un único mapeo por tabla; app_users 8 columnas, devices 10 y device_tokens 7, conservadas. Los imports de modelos desde access son transitorios para el trabajo de cuenta pendiente de C14; no se duplican clases SQLAlchemy ni se cambia DDL. La adaptación de rutas y el retiro de los esquemas anteriores se completa en T39.

### T38: Derivar DAOs de authorization

**Estado:** Done. **Propietario:** Authorization. **Tamaño previsto:** M.

**Entrada/dependencias:** T37 comprobada.

**Aceptación:**

- [x] Todos los DAOs derivan de la base existente; sus consultas son métodos.
- [x] Bloqueos y relecturas preservan carreras de rotación y revocación.
- [x] Operaciones coordinadas usan la misma sesión y commit=False.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** src/api/authorization/repository y pruebas de persistencia de acceso.

**Transacción, datos y consumidores:** Conserva el límite atómico y el orden de bloqueos; no cambia reglas de acceso.

**Evidencia:** AppUserDAO, DeviceDAO y DeviceTokenDAO derivan del DAO existente sin modificarlo. Probe .tmp/c13-dao-check.py correcto contra PostgreSQL real aislado, migración de credenciales 20261025_01: identidad exacta con espacios sin duplicación, pertenencia del dispositivo, creación atómica y rollback de revocación con commit=False. La base aleatoria se elimina al terminar. El sandbox no mostraba el proceso existente; fuera de él se comprobó PID 9400, ruta y clúster de prueba activos. No se movió su marcador ni se tocó el servicio personal. La carrera HTTP se repite al cerrar T39.

### T39: Corregir casos y endpoints de authorization

**Estado:** Done. **Propietario:** Authorization. **Tamaño previsto:** M.

**Entrada/dependencias:** T38 comprobada.

**Aceptación:**

- [x] Casos de uso sin acceso directo a SQLAlchemy; endpoints usan match con Ok/Err y Depends(get_db).
- [x] Cuatro rutas de credenciales conservan comportamiento y eliminan Request de sus parámetros.
- [x] OIDC y generación de credenciales usan core/services; integración real de credenciales pasa.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** src/api/authorization/application e infrastructure, core/services, composición y pruebas.

**Transacción, datos y consumidores:** Proveedor fuera de la transacción; credencial y revocación se confirman juntas. No añade rutas.

**Evidencia:** 36 pruebas unittest correctas (27.443 s), incluidas cinco de estructura sin excepciones dentro de authorization: casos sin acceso directo a sesión, infrastructure solo endpoints/configuración y sin Request, DAOs derivados, dominio sin proveedores/SQL/BaseModel directo de Pydantic e imports sin repositorios ajenos. HTTP/ASGI y OpenAPI comprueban las cuatro rutas y campos camelCase; issuer/subject y secretos no se recortan, y subject vacío solo con espacios se rechaza. Integración real test-support/access/check.py correcta dos veces con Keycloak 26.8.1 y PostgreSQL 18.3, migración de credenciales 20261025_01 aislada del trabajo parcial de cuentas: canje OIDC S256, solo huella guardada, un único éxito de dos rotaciones, credencial anterior inválida, aislamiento de usuarios/instalaciones, revocación terminal y carrera revocar/rotar. Fallos CHECK reales revierten alta y rotación completas. Se eliminan las bases aleatorias. uv build --offline correcto. Se retiran el endpoint, caso y adaptador OIDC anteriores de access; sus modelos/imports restantes sostienen solo la cuenta parcial hasta T40–T45. No se cambian fábrica, DAO base, esquema base, migraciones ni dependencias. C13 requiere aceptación del usuario.

### T40: Separar tipos y modelos de accounts

**Estado:** Done. **Propietario:** Accounts. **Tamaño previsto:** M.

**Entrada/dependencias:** T39 comprobada y C13 aceptado.

**Aceptación:**

- [x] Cuenta, pertenencias, profesional y autorización por cuenta quedan separados de authorization.
- [x] Esquemas usan la base, alias y campos permitidos; domain no accede a proveedores o SQL.
- [x] Modelos conservan tablas y claves sin nuevos cambios físicos.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** src/api/accounts/domain, repository y pruebas enfocadas.

**Transacción, datos y consumidores:** No cambia datos ni añade alta pública; conserva el alcance independiente.

**Evidencia:** Cuatro pruebas de esquemas correctas: base/alias, identidad externa exacta, país/entradas extra/nombres vacíos, proyección UTC y page/shows. Comparación de columnas de los cinco modelos frente al inicio: idénticas. Modelos trasladados sin duplicar mapeos; imports de access transitorios hasta T42. El Python local no incluye tzdata y TZPATH está vacío: ZoneInfo no reconoce ni America/Caracas; se elimina esa dependencia implícita. La validación de zona reconocida usará pg_timezone_names en AccountDAO y el caso de alta, junto al CHECK existente, sin instalar dependencias ni cambiar DDL.

### T41: Trasladar persistencia de accounts a DAOs

**Estado:** Done. **Propietario:** Accounts. **Tamaño previsto:** M.

**Entrada/dependencias:** T40 comprobada.

**Aceptación:**

- [x] Consultas y escrituras son métodos de DAOs derivados.
- [x] Autorización filtra antes de contar o paginar y protege cuentas ajenas.
- [x] Alta coordinada comparte sesión y evita commits parciales.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** src/api/accounts/repository y pruebas de persistencia.

**Transacción, datos y consumidores:** Mantiene alta atómica y referencias de usuario/profesional/cuenta; no cambia DDL.

**Evidencia:** Probe .tmp/c14-dao-check.py correcto contra PostgreSQL real aislado, aplicando la revisión de cuentas 20261025_02 existente sin editarla. Cinco DAOs derivados del DAO actual: cuenta, pertenencia, profesional, vínculo y acceso de dispositivo. Commit conjunto de cuenta/pertenencia/profesional/vínculo/head, filtros de ámbito antes de contar/paginar, propietario visible y usuario ajeno sin filas ni referencias. Catálogo PostgreSQL reconoce America/Caracas y rechaza Fixture/Unknown. La base aleatoria se elimina al terminar. El caso completo y rollback inyectado se prueban en T42.

### T42: Corregir casos de accounts y soporte de sync

**Estado:** Done. **Propietario:** Accounts y sync. **Tamaño previsto:** M.

**Entrada/dependencias:** T41 comprobada.

**Aceptación:**

- [x] Casos aplican reglas y consumen casos/tipos públicos de otros componentes, nunca sus repositorios.
- [x] El estado técnico de sync usa modelo y DAO propios derivados de la base.
- [x] Alta y rollback conservan todas sus partes y revalidan el acceso vigente.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** src/api/accounts/application, src/api/sync y pruebas de alta.

**Transacción, datos y consumidores:** Un único límite de transacción sin llamadas externas; no implementa T07 ni descarga incremental.

**Evidencia:** 50 pruebas unittest correctas; los cinco controles de estructura se aplican a authorization, accounts y sync sin excepciones por componente. test-support/accounts/check.py correcto con Keycloak y PostgreSQL reales: no hay cuenta al autenticar, el rol operativo no puede dar altas, zona desconocida se rechaza antes de escribir, alta de seis partes coordinadas, duplicado, aislamiento, dispositivo no registrado/revocado y cuenta inactiva, MeResponse y listados propios con items/total y LIMIT/OFFSET. Fallo CHECK real del head revierte usuario/cuenta/pertenencia/profesional/vínculo/head y permite reintentar; dos altas concurrentes del mismo propietario producen una sola cuenta. Head ORM retenido en la sesión se refresca tras un cambio de época desde otra conexión. test-support/persistence/check.py correcto con el head existente 20261025_02 y nueve tablas: upgrade/downgrade, fallo de revisión sin DDL parcial, DDL denegado al rol operativo y coordinación/rollback real. Build offline correcto. Se retiran los módulos de access sin consumidores y el antiguo heads.py; CLI solo adapta imports/llamada/resultado hasta T44. No hay endpoints nuevos ni cambios de migraciones o dependencias. Las pertenencias y registros de dispositivo de integración son fixtures, no operaciones de negocio implementadas.

### T43: Sustituir cursores de página por LIMIT/OFFSET

**Estado:** Done. **Propietario:** Listados. **Tamaño previsto:** M.

**Entrada/dependencias:** T42 comprobada y C14 aceptado.

**Aceptación:**

- [x] Listas usan page desde 1, shows 100 por defecto y máximo 500; items/total.
- [x] DAO aplica filtros, orden estable, LIMIT/OFFSET y conteo autorizado.
- [x] Se eliminan módulos y configuración de cursores de página sin alterar el avance incremental.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** DAOs y esquemas de listados, src/core/cursors.py, src/settings/cursor_settings.py y pruebas.

**Transacción, datos y consumidores:** No implementa snapshot o sync pendientes. Su contrato se corrige en T35; no crea permisos por paginar.

**Evidencia:** Se verifican huellas antes de retirar core/cursors.py y settings/cursor_settings.py, sin consumidores. Búsqueda en src/tests/test-support/.env.example/manifiesto sin imports ni configuración CURSOR_. Cuatro pruebas de esquemas correctas después de la retirada: PageQuery acepta page/shows y rechaza cursor/limit; conserva valores iniciales y límites. Las pruebas PostgreSQL de C14 ya comprobaron filtros, orden, páginas sucesivas/vacías y total autorizado en cuentas y dispositivos. No se modifica el contrato ni código de avance incremental; snapshot sigue pendiente de implementación, con contrato LIMIT/OFFSET.

### T44: Sustituir CLI por script pequeño de alta

**Estado:** Done. **Propietario:** Scripts. **Tamaño previsto:** M.

**Entrada/dependencias:** T43 comprobada.

**Aceptación:**

- [x] scripts/create_practice.py lee JSON, valida y llama al caso de uso; se retira src/cli.py.
- [x] Conexión administrativa separada; sin sistema de comandos ni dependencia de arranque.
- [x] Entradas inválidas, falta de configuración y fallos de base tienen resultado claro y sin secretos.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** scripts/create_practice.py, src/cli.py, pruebas y guía de uso.

**Transacción, datos y consumidores:** Conserva el alta atómica; no añade workflows ni seeders generales.

**Evidencia:** Cinco pruebas unitarias de script correctas (11.194 s): ayuda sin base/OIDC, archivos ausentes/JSON inválido/UTF-8 inválido, URI administrativa obligatoria aunque exista URI operativa, URL/puerto inválidos sin secretos e issuer exacto antes de conectar. Probe de cuentas real correcto con subprocess del script: alta y JSON camelCase, duplicado, rol operativo denegado, zona inválida, contraseña errónea y conexión no disponible sin traceback/credenciales. El script toma BOOTSTRAP_DATABASE_URI explícita y selecciona esa URI solo en su proceso antes de cargar la fábrica existente; no crea otra fábrica ni modifica archivos o el proceso API. La prueba deja una URI operativa falsa en el proceso hijo y aun así crea el alta con la administrativa; el entorno del padre se conserva. Se elimina la base ficticia. src/cli.py se retira tras comparar su huella. No hay subcomandos ni seeders.

### T45: Cerrar corrección, pruebas y documentación

**Estado:** Done. **Propietario:** Verificación. **Tamaño previsto:** M.

**Entrada/dependencias:** T44 comprobada.

**Aceptación:**

- [x] No quedan access, cursores de página, CLI retirada ni imports transitorios de compatibilidad.
- [x] Controles de estructura pasan sin excepciones que oculten infracciones.
- [x] Suite, integraciones reales pertinentes, build y revisión documental registran evidencia y límites.

**Comprobación:** Pruebas enfocadas y `uv run --locked python -m unittest discover -s tests -v`. Build al cambiar composición o cerrar el checkpoint. PostgreSQL/Keycloak reales solo para los recorridos que esta tarea modifica; no exigir Docker ni el test HTTP separado del wheel.

**Archivos previstos:** Pruebas de estructura/comportamiento, soporte de pruebas, documentación y restos retirados.

**Transacción, datos y consumidores:** No da por terminada T09 ni acepta C15/C03; no despliega, no modifica consumidores ni el esquema.

**Evidencia:** 63 pruebas unittest correctas (33.838 s), con 20 controles de estructura en users/authorization/accounts/sync y tres controles generales de esquemas, paginación y módulos retirados. Los archivos de esquemas se cargan sin activar los imports antiguos de users; no se cambia ni acredita la ejecución de ese componente de referencia. Se permite su alias de tipo de parámetros en infrastructure, sin permitir helpers ni clases. Integraciones reales correctas: acceso con Keycloak/PostgreSQL, cuentas con alta/lecturas/rollback/concurrencia y subprocess administrativo, y persistencia con upgrade/downgrade, fallo de revisión sin DDL parcial, permisos y dos escritores. Solo bases ficticias verificadas y eliminadas; servicios previos conservados. uv build --offline correcto: sdist y wheel sin módulos retirados ni carpetas privadas; no se ejecuta la prueba HTTP separada del wheel. git diff --check correcto. Huellas: de 80 archivos protegidos, 74 iguales; cambian solo dos pruebas de estructura y un comentario de .env.example, y se retiran los tres módulos previstos. Fábrica, dependencias de sesión, app, DAO base, esquema base, migraciones, manifiesto y lockfile conservan su huella. Revisión documental: 45 tareas, 15 checkpoints, 15 documentos y 86 enlaces locales; seis destinos previos ausentes, cuatro referencias de procedencia del esquema al escritorio y dos de la copia histórica, sin copiar ni modificar otro repositorio. No se añaden endpoints ni se declara implementado snapshot/avance incremental. C15 requiere aceptación del usuario.

## Checkpoints

### C01: Contratos, modelos y decisiones

- [x] T01–T03 comprobadas y evidencia registrada.
- [x] Revisión documental completa; código y dependencias sin cambios en ese bloque.
- [x] Usuario: «Válido, puedes continuar con el objetivo, por favor».

### C02: Base ejecutable y entorno

- [x] T04–T06 comprobadas y evidencia registrada.
- [x] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [x] Usuario: «Por favor, continua con la meta.» el 2026-10-25; después eligió T08 → T09 → T07. No acepta C03.

### C03: Identidad y aceptación técnica

- [x] T07–T09 comprobadas y evidencia registrada.
- [x] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [x] Usuario acepta el 2026-10-26: «Continua, por favor». Habilita T10 → T11 → T12; C04 sigue pendiente.

### C04: Permisos y dos usuarios

- [x] T10–T12 comprobadas y evidencia registrada.
- [x] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [x] Usuario acepta el 2026-10-26: «Aprobado, podemos continuar». Habilita T13 → T14 → T15; C05 conserva su revisión.

### C05: Pacientes y contactos

- [x] T13–T15 comprobadas y evidencia registrada.
- [x] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [ ] Revisión y aceptación expresa del usuario.

### C06: Catálogo y horario habitual

- [ ] T16–T18 comprobadas y evidencia registrada.
- [ ] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [ ] Revisión y aceptación expresa del usuario.

### C07: Disponibilidad protegida

- [ ] T19–T21 comprobadas y evidencia registrada.
- [ ] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [ ] Revisión y aceptación expresa del usuario.

### C08: Creación, confirmación y reprogramación

- [ ] T22–T24 comprobadas y evidencia registrada.
- [ ] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [ ] Revisión y aceptación expresa del usuario.

### C09: Ciclo completo de citas

- [ ] T25–T27 comprobadas y evidencia registrada.
- [ ] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [ ] Revisión y aceptación expresa del usuario.

### C10: Descarga y recuperación

- [ ] T28–T30 comprobadas y evidencia registrada.
- [ ] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [ ] Revisión y aceptación expresa del usuario.

### C11: Colaboración y entrega de API

- [ ] T31–T33 comprobadas y evidencia registrada.
- [ ] Pruebas aplicables y recorrido del bloque comprobados; límites externos identificados.
- [ ] Revisión y aceptación expresa del usuario.

### C12: Reglas, contrato y soporte

- [x] T34–T36 comprobadas; fuentes y pruebas del soporte común registradas.
- [x] Fábrica, app de módulo, inyección y comando Uvicorn del usuario conservados.
- [x] Usuario: «Vale, me parece bien. Puedes continuar con la implementación del plan», tras confirmar transacción en el caso de uso y DAOs con commit=False. C13 conserva su revisión.

### C13: Recorrido de credenciales

- [x] T37–T39 comprobadas; endpoint → caso de uso → DAO revisable.
- [x] Emisión, rotación y revocación comprobadas con PostgreSQL/Keycloak reales.
- [x] Usuario: «Por favor, continúa». Habilita T40–T42, con revisión pendiente de C14.

### C14: Componentes y alta atómica

- [x] T40–T42 comprobadas; separación de cuentas, identidad y sync verificada.
- [x] Alta y rollback sin SQL en aplicación ni repositorios ajenos.
- [x] Usuario: «Todo bien». Habilita T43–T45; C15 conserva su revisión pendiente.

### C15: Corrección completa

- [x] T43–T45 comprobadas; sin infracciones ocultas ni módulos transitorios.
- [x] Paginación, scripts, contrato, pruebas e integraciones documentados.
- [x] Usuario revisó y aceptó el 2026-10-26: «Sí, continúa con el desarrollo. Por favor». Permite retomar T09 y después T07, sin aceptar C03.

## Registro de comprobaciones

### T13 → T14 → T15 · 2026-10-26 · C05 para revisión

- El usuario acepta C04 con «Aprobado, podemos continuar». Se trabaja una tarea a la vez, sin delegación y sin avanzar a T16.
- Se añaden pacientes/contactos y completitud mediante la aceptación vigente. No se habilita verificación, identidad global arbitraria ni rutas de citas; la regla por fecha queda comprobada como caso compartido que T22 debe conectar.
- Suite final: 91 pruebas correctas; seis probes reales, migraciones y build correctos. Evidencia y límites en T13–T15 y la guía de desarrollo. C05 requiere revisión expresa del usuario.

### T10 → T11 → T12 · 2026-10-26 · C04 para revisión

- El usuario acepta C03 con «Continua, por favor». Se trabaja una tarea a la vez, sin delegación y sin avanzar a T13.
- Invitaciones/pertenencias y gestión de cuenta/perfil/dispositivos reutilizan la aceptación de T07. Auditoría de efectos/controles, consulta por propietario y mantenimiento limitado quedan comprobados. No se crean sesiones, renovación, sistema de comandos ni funciones de pacientes o agenda.
- Suite final: 76 pruebas correctas. Cinco probes reales, migraciones, build/inspección del paquete y revisión de archivos correctos. Evidencia y límites detallados en T10–T12 y guía de desarrollo. C04 requiere revisión expresa del usuario.

### T09 → T07 · 2026-10-26 · C03 para revisión

- C15 aceptado por el usuario al pedir continuar con el desarrollo. Se ejecutan T09 y T07 en secuencia, sin delegación ni avance a T10.
- T09 reutiliza alta y lecturas existentes; añade seis rutas HTTP propias y su prueba de aislamiento. T07 añade lote/resultado, registro de instalación propia y persistencia técnica atómica. Las acciones posteriores siguen sin implementar.
- 71 pruebas correctas, cuatro probes reales correctos, build e inspección del paquete correctos. La evidencia completa y sus límites figuran en T09/T07 y la guía de desarrollo. C03 requiere aceptación expresa.

### Corrección T43–T45 · 2026-10-26 · C15 para revisión

- El usuario acepta C14 con «Todo bien». Se ejecutan T43, T44 y T45 en secuencia y se detiene el trabajo en C15; T09 y T07 siguen pendientes.
- Se retiran los módulos de cursores de página y la CLI tras comprobar sus huellas. Se conserva el avance incremental de sync como contrato separado. El snapshot sigue pendiente; su contrato usa page/shows.
- scripts/create_practice.py conserva un único flujo: JSON validado, URI administrativa explícita, llamada al caso de alta y salida breve. Pruebas reales acreditan alta, duplicado, rechazo al rol operativo y fallos seguros, sin otro sistema de sesiones.
- Se amplían las pruebas de estructura a users y a todos los esquemas de datos. Suite completa de 63 pruebas, integraciones reales de acceso/cuentas/persistencia, build offline e inspección del paquete correctos. La evidencia completa y los límites figuran en T45. No hay nuevas dependencias, cambios físicos ni funciones de negocio.

### Corrección T40–T42 · 2026-10-26 · C14 para revisión

- El usuario acepta C13 con «Por favor, continúa». T40, T41 y T42 se ejecutan en secuencia y se detienen en C14. No se inicia T43, no se marca T09 terminada y C03 conserva su revisión pendiente.
- accounts posee cinco modelos y DAOs derivados; domain usa la base y las proyecciones permitidas. application coordina transaction(db), autorización vigente y alta completa mediante casos públicos de authorization y sync; no importa sus repositorios. Identidad y dispositivos globales se consultan en authorization, y sync posee su modelo AccountSyncHead, DAO y casos públicos sin abrir otra transacción.
- Los cinco modelos de cuenta conservan exactamente columnas/definiciones; el modelo del head refleja la tabla existente y sus bigint. No se cambia ninguna migración ni dependencia. Aplicar/revertir revisiones ocurre solo en bases aleatorias del clúster de pruebas validado, no en la base del usuario.
- ZoneInfo falló con America/Caracas por ausencia de tzdata y TZPATH vacío en Windows. AccountDAO valida pg_timezone_names, la misma fuente del CHECK vigente; el caso devuelve UnknownTimeZone antes de crear identidad. Se conservan país ISO, alias, valores externos exactos y proyecciones UTC, sin añadir un paquete.
- Listas trasladadas usan page/shows, LIMIT/OFFSET e items/total desde ahora para cumplir D10; T43 conserva la retirada de core/cursors.py y cursor_settings.py y su comprobación final. No se añaden endpoints ni código de snapshot o descarga incremental.
- test-support/accounts/check.py: Keycloak/PostgreSQL reales, alta controlada, scopes, dos usuarios y cuentas, permisos de dispositivo y cuenta inactiva, paginación, identidad exacta, rechazo de rol operativo, duplicado concurrente, fallo CHECK después de crear las partes y rollback completo. Las membresías/autorizaciones se preparan como fixtures explícitos; no acreditan invitaciones ni RegisterAccountDevice. Las bases se eliminan al terminar y se reutilizan los servicios de prueba que ya estaban activos.
- 50 pruebas correctas, incluidos 15 controles de estructura en los tres componentes. Integración de persistencia correcta con la revisión ya existente 20261025_02. Build offline correcto. Se actualizan los imports de la CLI para mantenerlos válidos; su sustitución y pruebas específicas siguen en T44. Se retira código de access y heads.py ya sin consumidores; T45 verificará la ausencia de restos.
- Cierre final: 50 pruebas correctas en 24.032 s tras el ajuste de refresco, integración de cuentas repetida con ese caso y git diff --check correcto. De 77 archivos protegidos, 64 conservan su huella; seis cambian dentro del alcance y siete módulos antiguos se retiran. Fábrica, dependencia de sesiones, DAO base, esquema base, app, migraciones, manifiesto y lockfile conservan su huella. Revisión documental: 45 tareas/15 checkpoints, 14 documentos y 74 enlaces locales; solo los dos destinos históricos ausentes de la copia del escritorio ya registrados. Sin imports de access/heads ni consumidores de los helpers antiguos de cursores en el código revisado.

### Corrección T37–T39 · 2026-10-26 · C13 para revisión

- El usuario acepta C12 al pedir continuar tras confirmar que transaction(db) delimita el caso de uso; los DAOs comparten sesión y commit=False. Se ejecutan T37, T38 y T39 en secuencia; detenerse en C13 sin iniciar T40.
- authorization tiene domain (esquemas base, identidad/actor y errores), repository (modelos existentes y tres DAOs derivados), application (casos con transaction, Ok/Err y sin consultas) e infrastructure (cuatro endpoints, sin helpers, esquemas ni Request). Proveedor OIDC y generación/lectura de credenciales pasan a core/services sin importar componentes del API.
- Se activa el control de estructura para authorization completo, sin excepciones internas. access conserva solo la cuenta parcial y los imports necesarios para trasladarla en C14; no es la fuente de las rutas de credenciales. La retirada completa de access, cursores de página y CLI conserva las tareas y checkpoints aprobados.
- PostgreSQL y Keycloak de pruebas ya estaban activos. El sandbox ocultaba el PID 9400; al consultar fuera se confirmó la ruta del clúster de pruebas y su estado. No se movió el marcador ni se detuvo/inició otro servicio. Los intentos de arranque no cambiaron la configuración; el log nuevo de diagnóstico queda en .tmp. Se reutilizan los servicios existentes y siguen activos como al inicio.
- El probe de DAO y el de HTTP crean bases aleatorias distintas con guardia de data_directory y las eliminan al terminar. Aplican solo la revisión ya comprobada de credenciales en esas bases de prueba; no se modifica ni aplica la revisión parcial de cuentas al entorno del usuario. Las carreras y rollback usan PostgreSQL real, no SQLite ni solo mocks.
- 36 pruebas correctas, build offline correcto y revisión final de huellas/archivos. API HTTP se ejecuta mediante ASGITransport, sin Uvicorn ni prueba HTTP separada de wheel. No se instala, actualiza o despliega nada; no se modifica otro repositorio. Fuentes y límites en docs/sources.md y docs/operations/development.md.

### Corrección T34–T36 · 2026-10-26 · C12 para revisión

- El usuario aprobó implementar la corrección dentro del plan vigente. Se conservan IDs y evidencia de T01–T33; T09 pasa a Todo con trabajo parcial conservado, pendiente de C15. Se añaden T34–T45 y C12–C15. C03 y C12–C15 no aceptados. Detenerse aquí antes de T37.
- T34 y T35 solo modificaron documentación: 68 huellas protegidas sin cambios en ambos cierres. Catálogo 1.1 conserva 47 rutas y 42 acciones únicas; ejemplo JSON con claves camelCase. El contrato distingue LIMIT/OFFSET para listas/snapshot de avance incremental de sync.
- T36 cambia cinco archivos del conjunto protegido: errors.py, exportaciones de core/db y core/schema, esquemas HTTP y pruebas de fundación. Otros 63 conservan su huella, entre ellos session.py, deps.py, application.py, base.py, DAO, modelos y migraciones, pyproject.toml y uv.lock. Añade transaction.py y cuatro pruebas de soporte. El probe de acceso cambia solo el nombre correlationId esperado; no se ejecuta como integración en este bloque.
- Antes de editar código: sandbox con errores de permisos en temporales/procesos; repetición fuera del sandbox ejecutó 21 pruebas con seis fallos previos de fundación. Después de adaptar las pruebas a la fábrica del usuario y añadir soporte: 25 correctas. No se atribuyen esos seis fallos a la corrección ni se cambia producción para ocultarlos.
- Build offline correcto. git diff --check correcto; revisión adicional de archivos no seguidos, bloques Markdown y UTF-8. En 13 documentos se inspeccionan 73 referencias locales: dos destinos históricos ausentes a nightingale-desktop-docs/README.md, ya documentados como copia trasladada; no se restauran ni modifican otros repositorios.
- Fuentes oficiales y versiones en docs/sources.md. Sin dependencias, migraciones, servicios nuevos, prueba HTTP del wheel ni despliegue. La separación de componentes, retirada de Request en endpoints, cursores de página y CLI se ejecutará en los siguientes bloques aprobados tras revisión, no se declara hecha en C12.

### Bloque T01–T03 · 2026-10-24

- Usuario aprobó ejecutar el plan sucesor; C01 permanece sin aceptar. T01, T02 y T03 se ejecutaron en secuencia, una activa a la vez.
- Node.js 24.18.0/biblioteca estándar: 33 tareas y 11 checkpoints; 47 rutas y 42 acciones únicas; ejemplo JSON válido; tablas Markdown y bloques de código coherentes.
- Esquema 1.0: 27 tablas, 300 columnas, 53 FK; columnas/tipos/destinos PK/UQ contrastados. Los 189 atributos de los 17 modelos dibujados del núcleo coinciden con el diccionario. La captura conserva zona y límites UTC para no reinterpretar su ventana tras cambiar la cuenta. Diagrama técnico revisado como texto; sin render nuevo.
- 18 Markdown y 99 referencias locales: 93 destinos existentes y seis ausencias históricas, sin nuevo destino ausente. Cuatro rutas del esquema pertenecen al escritorio y se conservan; dos referencias antiguas apuntan a la copia ya trasladada, en decisiones/fuentes históricas. No se afirmó comprobar esos archivos fuera de su contexto.
- Huellas SHA-256 de 49 archivos de src/tests, pyproject.toml, uv.lock, .python-version y .env.example: sin cambios frente al inicio del bloque. No se modificó otro repositorio.
- git diff --check correcto para cambios seguidos por Git; los archivos no seguidos también se revisaron con controles de Markdown/diccionario, que Git no cubre por sí solo.
- Revisión de recorridos: duplicado rechazado no se convierte en aceptación; token no vence y no se revoca por logout OIDC; catálogo privado no llega a asistentes; invitación exige destinatario; captura y cursor conservan frontera; recibo mínimo evita repetir al vencer resultado. Es revisión de diseño, no prueba del producto.
- Se corrigió y comprobó UTF-8 en textos nuevos; no se conservaron sustituciones de tildes causadas por el paso de texto a Node desde PowerShell.

No se ejecutaron pruebas de producto, build, servidores, instalación, SQL, migraciones ni integración de consumidores. Las dependencias y comandos futuros siguen sin ejecución. Código de proceso actual se conciliará en T04; las pruebas de T03 histórico no acreditan el estado actual. C01 listo para revisión; T04 y todos los checkpoints permanecen pendientes.

### Reversión de la continuación de código

El usuario pidió detener y volver al código anterior porque la continuación sustituyó cambios de estilo suyos. Se retiran los cambios de T04 y la tarea preparatoria T34, sin marcarla terminada. T04 queda Todo. C01 sigue aceptado y la instrucción posterior de no exigir Docker se conserva. No se retoma desarrollo por esta reversión.

Se verifican las huellas SHA-256 frente al estado previo: seis archivos restaurados y los 49 archivos protegidos de código, pruebas y configuración coincidentes. Se retira solo el probe temporal creado en esa continuación; no se borran carpetas ni archivos ajenos. No se ejecutan pruebas de producto o imports que cambien ese estado.

### Reanudación con el estilo del usuario

El usuario pide continuar y respetar su estilo: app de módulo, ajustes compartidos, motor/fábrica de sesiones y sus exportaciones existentes. T04 cambia solo cinco archivos de código/pruebas, sin create_app/create_db_engine ni otra estructura de estado. Se corrigen imports de utilidades que no existen y se adaptan las pruebas al app actual, con entornos de prueba separados de .env local. C02 sigue pendiente.

Las 12 pruebas actuales pasan. uv build --offline produce los dos artefactos. La comprobación HTTP separada del wheel se omite por instrucción del usuario; no se vuelve a pedir permiso para ella. No se da por ejecutada ni se convierte en un bloqueo nuevo. La prueba del punto de entrada comprueba el destino del manifiesto y su llamada a Uvicorn; no acredita ejecutar el comando desde un wheel instalado en otro entorno.

### Bloque T04–T06 · C02 preparado para revisión

- Se conservan 41 de las 49 huellas de código/configuración del inicio. Ocho archivos existentes cambian: aplicación, salud, ajustes DB, imports de utilidades, pruebas, manifiesto, lockfile y el arreglo concreto del hook SQLAlchemy. DAO, dependencia y exportaciones de core.db conservan sus huellas; no se restaura el diseño retirado.
- 12 pruebas actuales correctas con el comando bloqueado del plan. Flujo OIDC real comprobado con Keycloak 26.8.1 y tres sujetos ficticios. PostgreSQL 18.3 acredita aislamiento de perfiles, migraciones, permisos, rollback y dos escritores sobre una fila ficticia; no acredita aún aceptación de negocio ni colaboración de consumidores.
- Solo Alembic y Mako se añaden a dependencias. SQL offline, build offline y git diff --check correctos. No se ejecuta la prueba HTTP separada del wheel que el usuario pidió omitir.
- Los procesos temporales de Keycloak y ambos clústeres PostgreSQL se detienen. Las descargas, certificados, roles y catálogos ficticios quedan en .tmp ignorado; las bases aleatorias de cada comprobación se eliminan. No se cambia el servicio personal ni otro repositorio; sin Docker, commits o despliegue.
- C02 queda para revisión expresa del usuario. T07 no se inicia y no se marca aceptado este checkpoint.
