# Estado y evidencia: P-20261024-01-desktop-shared-api

**Plan:** [plan.md](plan.md). **Estado:** In progress. **Actualizado:** 2026-10-26.

El usuario aprobó el plan al pedir «Por favor, implementa este plan». El usuario aceptó después C01 al decir «Válido, puedes continuar con el objetivo, por favor». Tras revertir la primera continuación, autorizó retomar el trabajo con su estilo de código. C01 conserva su aceptación. Una tarea a la vez, sin delegación. Los estados se registran solo tras comprobar.

**Ampliación aprobada, 2026-10-26:** el usuario indica «Acepto el plan, puedes continuar con las correcciones». Tras C16 pide continuar; T49–T51 comprobadas, sin delegación, para revisión C17 antes de T52. C17/C18 recibieron aceptación expresa. T46–T57 comprobadas para revisión C06; C06 sigue sin aceptar y T19 no se inicia. Los registros anteriores conservan su evidencia histórica.

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
| T16 | Done | Catálogo privado, propiedad, versiones y rollback comprobados; revisión en C06 pendiente |
| T17 | Done | Ofertas, duración y proyección entre cuentas comprobadas; revisión en C06 pendiente |
| T18 | Done | Reglas, unión local, unicidad y coordinación comprobadas; revisión en C06 pendiente |
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
| T46 | Done | sentinel por decisión del usuario; ejecución comprobada y límite estático registrado |
| T47 | Done | Guardas de resultado original e invitación; probes sync/equipo correctos |
| T48 | Done | Firmas y esquemas conservados; C16 aceptado con límite estático |
| T49 | Done | Validadores tipados; 17 pruebas y 72 esquemas conservados |
| T50 | Done | Tipos de acceso/cuentas y guardas comprobados con tres probes |
| T51 | Done | DAOs operativos tipados; C17 para revisión |
| T52 | Done | Selección única y 48 huellas previas conservadas |
| T53 | Done | Pacientes/contactos consumen el modelo ya validado |
| T54 | Done | Seis normalizadores retirados; C18 aceptado |
| T55 | Done | Separar proyección de ofertas y serialización; tras C18 |
| T56 | Done | Simplificar lecturas HTTP de C06; tras C18 |
| T57 | Done | Cierre comprobado; C06 para revisión |

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

**Estado:** Done. **Propietario:** services. **Tamaño previsto:** M. Done indica comprobación técnica, no aceptación del usuario; C06 sigue pendiente.

**Entrada/dependencias:** T15 comprobada y C05 aceptado.

**Aceptación:**

- [x] Solo el profesional propietario crea o modifica su catálogo.
- [x] Duración entera 1–1440 y estados tienen reglas explícitas.
- [x] Cambios no recalculan citas ni permiten editar catálogo ajeno. No hay aún citas persistidas; la integración de sus snapshots conserva T22–T27.

**Comprobación:** `uv run --locked python test-support/services/check.py`, `uv run --locked python -m unittest discover -s tests -v` y `uv build --offline`. Propiedad, versión, búsqueda literal, proyección privada y rollback real.

**Archivos previstos:** src/api/services/domain/; src/api/services/application/; src/api/services/repository/; src/api/services/infrastructure/; tests/services/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Catálogo global del profesional; cambios se proyectan en cuentas afectadas sin filtrar catálogo privado.

**Evidencia (2026-10-26):** CreateService/UpdateService/SetServiceStatus y GET /v1/me/services con esquemas de domain, DAO derivado y migración 20261026_06. Profesional antes de controles de cuenta ordenados; catálogo solo para owner. El probe `uv run --locked python test-support/services/check.py` pasó con PostgreSQL/Keycloak reales: propiedad, duración estricta, versiones y duplicados concurrentes, búsqueda literal, paginación, denegación a asistente, cuenta inactiva y rollback diferido de efecto/recibo/auditoría/grupo. SQL rechaza transferencia, versión fija y duración cero. Suite: 99 pruebas correctas en 44.480 s; build offline correcto. Un primer intento detectó una ubicación incorrecta de repository; se corrigió y se repitieron integración y suite. No existen tablas/rutas de citas; T22–T27 conservan sus pruebas reales. El usuario autorizó T16 → T17 → T18 antes de revisión C06; este registro no acepta C06.

**Desglose de ejecución (2026-10-26):** T16.1 define esquemas/modelo y migración del catálogo; T16.2 conecta propiedad, coordinación y aceptación; T16.3 añade lectura, controles de estructura y pruebas PostgreSQL/HTTP. Cada parte conserva este ID y se ejecuta en secuencia, sin delegación. No crea ofertas, agenda ni citas por anticipado. El alcance requiere más de cinco archivos para respetar los límites de cada componente.

### T17: Gestionar ofertas por cuenta

**Estado:** Done. **Propietario:** services. **Tamaño previsto:** M. Comprobación técnica; C06 sigue sin aceptación.

**Entrada/dependencias:** T16 comprobada.

**Aceptación:**

- [x] Oferta comprueba cuenta, profesional y propiedad del servicio.
- [x] Ajuste nulo usa la base vigente y ajuste positivo válido conserva su valor en la referencia interna comprobada.
- [ ] Conservar la duración elegida en el snapshot de una cita real: pendiente de T22.
- [x] Inactivar una oferta conserva las otras ofertas y sus filas independientes.
- [ ] Probar que la inactividad no cancela citas previas con reservas reales: pendiente de T22–T27/T32.

**Comprobación:** `uv run --locked python test-support/services/check.py`, suite completa y build offline. Segunda oferta mediante fixture relacional explícita; rechazo de servicio ajeno y rollback de ambas proyecciones. La evidencia distingue ese control de gestión HTTP de clínicas y de una reserva real.

**Archivos previstos:** src/api/services/domain/; src/api/services/application/; src/api/services/repository/; src/api/services/infrastructure/; tests/services/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** Transacción de servicio/oferta/versiones/cambios; sin escritura directa de citas.

**Evidencia (2026-10-26):** OfferService/UpdateServiceOffer/SetServiceOfferStatus y GET de ofertas por cuenta, con FK compuestas, estados y versiones independientes. El catálogo se proyecta solo al propietario; las ofertas publican nombre/base/ajuste/duración efectiva y ambas versiones a members. Cambiar catálogo no aumenta la versión propia de oferta: serviceVersion identifica ese cambio. Una fixture clinic permite comprobar segunda oferta sin habilitar gestión HTTP de clínicas. El probe de servicios pasó: nulo usa la base nueva, ajuste 45 se conserva, inactivar una oferta no altera la otra, FK rechaza servicio ajeno y fallo diferido en la segunda cuenta revierte catálogo/recibo/auditoría/ambos grupos. booking_service resuelve actividad de cuenta, usuario, pertenencia, profesional, vínculo, servicio y oferta; T22 debe usarlo y conservar el snapshot en una cita real. No se afirma esa reserva ahora. Suite completa: 100 pruebas correctas en 53.106 s; build offline correcto. El DAO derivado usa add para la clave compuesta; el DAO base permanece intacto.

**Desglose de ejecución (2026-10-26):** T17.1 añade modelo/esquemas/migración; T17.2 conecta operaciones, lectura y proyección; T17.3 comprueba propiedad, duración y dos ofertas aisladas. Sin gestión de clínicas ni citas. La segunda cuenta del mismo profesional usa solo una fixture relacional clinic: el esquema permite una única independent por propietario. Esa parte prueba DAO/FK/proyección, no gestión HTTP de clínicas.

### T18: Gestionar reglas semanales

**Estado:** Done. **Propietario:** schedule. **Tamaño previsto:** M. Comprobación técnica; C06 sigue sin aceptación y no acredita citas reales.

**Entrada/dependencias:** T17 comprobada.

**Aceptación:**

- [x] Minutos 0–1439/1–1440, día ISO y vigencia cumplen el diccionario.
- [x] Unión de tramos y unicidad de fin abierto no duplican disponibilidad. Se comprueban los intervalos semanales; la disponibilidad completa sigue en T21.
- [x] El cambio rechaza intervalos requeridos ficticios incompatibles sin escribir reglas, bajo bloqueo del profesional.
- [ ] Conservar citas reales y rechazar un cambio incompatible con ellas, incluida su carrera: pendiente de T22/T32.

**Comprobación:** `uv run --locked python test-support/schedule/check.py`, suite completa, probe de persistencia y build offline. Jornada partida, fin 1440, fecha local, vigencia incluida, UQ abierta, versiones y espera real del profesional.

**Archivos previstos:** src/api/schedule/domain/; src/api/schedule/application/; src/api/schedule/repository/; src/api/schedule/infrastructure/; tests/schedule/. Son ubicaciones, no orden de crear directorios vacíos. Si el recorrido excede cinco archivos o una revisión concreta, dividir antes de ejecutar sin renumerar IDs aprobados.

**Transacción, datos y consumidores:** No tabla de reservas duplicada; carrera se repetirá con Citas en T32.

**Evidencia (2026-10-26):** Tres acciones y dos lecturas de reglas, domain con BaseModel del proyecto, DAO derivado y migración 20261026_08. El probe real comprueba intervalos 08:00–13:00/14:00–24:00 tras unir solapados, fin de vigencia incluido y fecha de Caracas antes/después de las 04:00 UTC. Rechaza rangos inválidos, profesional ajeno, versión antigua, duplicado abierto por API y por SQL. Dos actores crean el mismo intervalo abierto: solo uno confirma. pg_blocking_pids prueba que la edición espera al profesional; al continuar lee el estado vigente. Un cambio incompatible con un intervalo requerido ficticio devuelve SLOT_UNAVAILABLE antes de escribir. Un fallo diferido revierte estado/recibo/auditoría/grupo; el reintento confirma. Se reautoriza al revocar el dispositivo. No se crean excepciones, bloqueos, disponibilidad completa ni citas: T21 resuelve esos intervalos completos y horas locales ambiguas; T22/T32 deben aportar ocupación real al control. Suite final: 108 pruebas correctas en 51.714 s; ocho probes reales, head de 21 tablas aplicado/revertido/reaplicado y build offline correctos. C06 para revisión, sin aceptar.

**Desglose de ejecución (2026-10-26):** T18.1 define reglas/modelo/migración; T18.2 conecta lecturas y aceptación bajo bloqueo del profesional; T18.3 comprueba límites, unión, unicidad abierta y rechazo de una propuesta incompatible con intervalos requeridos ficticios. No crea ocupación ni citas. T22/T32 deben alimentar el control con reservas reales y probar su carrera; los controles de T18 no acreditan esa integración.

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

## Corrección aprobada de C06

El usuario aprobó la ampliación; cada checkpoint conserva su aceptación por separado. Los archivos previstos delimitan cada cambio, no autorizan crear capas o archivos vacíos. Si aparece una sexta modificación de producto en una tarea, dividirla antes de ejecutarla y conservar los IDs. Los cambios de estado/evidencia del plan siguen cada comprobación. No delegar.

### T46: Corregir el tipo de ausencia tras comprobar el analizador

**Estado:** Done. **Propietario:** core técnico. **Tamaño:** M. **Dependencias:** ampliación aprobada; C06 sigue sin aceptar.

**Entrada:** definición actual de Empty/Undefined, retornos del DAO, consumidores y avisos del usuario. Localizar el analizador real, su intérprete, versión y configuración, sin asumir que Cursor Pyright sea basedpyright.

**Aceptación:**

- [x] Reproducir en un caso mínimo el aviso de EmptyType; comprobar soporte de sentinel de Python 3.15 y registrar el comando real y su salida.
- [x] Valor y anotación representan la misma ausencia; consultas presentes/ausentes conservadas. EmptyType/UndefinedType quedan como alias de tipo de sus sentinels; Undefined no tiene consumidores. La reducción estática con `is Empty` queda sin acreditar en basedpyright 1.40.2; el usuario pidió conservar sentinel tras recibir esa evidencia.
- [x] El DAO acepta UUID e int y conserva las guardas de sus consumidores, sin nuevos cast, Any o ignores. La comprobación estática de la ausencia mantiene el límite anterior.

**Archivos:** src/core/utils/utils.py; src/core/db/dao.py; tests/test_common_support.py; test-support/persistence/check.py para comprobar consultas presentes/ausentes en PostgreSQL real. Casos mínimos temporales en .tmp, sin persistir datos personales. Motor, fábrica y dependencia de sesión conservados.

**Comprobación:** basedpyright 1.40.2 instalado por Zed; ruta y comando reales en la evidencia. Pruebas enfocadas: `uv run --locked python -m unittest discover -s tests -p test_common_support.py -v`; suite completa y probe de persistencia al cambiar el DAO. Revisión de consulta ausente/presente; la reducción estática queda con el límite explícito del analizador.

**Transacción/consumidores:** soporte compartido; no cambia SQL, commits ni respuesta pública. Revisar todos los consumidores de la ausencia común. Si falta soporte real del analizador, pedir decisión antes de instalar/actualizar, sin elegir otro diseño en silencio.

**Evidencia parcial, 2026-10-26:** commit actual 233569c; cambios locales conservados. El usuario confirma que usa Zed. Se localiza su CLI en `C:\Users\Pedro\AppData\Local\Zed\languages\basedpyright\node_modules\basedpyright\index.js`, versión 1.40.2. Comando base: `node <ruta-CLI> --pythonpath .venv/Scripts/python.exe --pythonversion 3.15 src --outputjson`. Carga el pyproject.toml actual: basic, sin nuevas supresiones; Python del entorno 3.15.1, con sentinel disponible. El análisis inicial de 97 archivos registra 155 errores, 102 con EmptyType. No es un cierre estático correcto.

Casos mínimos en `.tmp/c16-types`: `node <ruta-CLI> --project .tmp/c16-types/pyrightconfig.json --pythonpath .venv/Scripts/python.exe --outputjson`. El caso actual reproduce `Cannot access attribute "id" for class "EmptyType"`. `Empty = sentinel("Empty")` y `Row | Empty` producen `Variable not allowed in type expression` y no reducen la unión; ocurre también al activar funciones experimentales solo en la configuración temporal. El alias de tipo tampoco resuelve ese límite. Una alternativa temporal con Enum de un solo valor y `Empty: Final = EmptyType.EMPTY` sí reduce a Row tras `is Empty`, también al importar desde otro módulo; presente, ausente e identidad pasan en ejecución. Se pide decisión al usuario antes de elegir otro diseño o tocar soporte común. No se instala ni actualiza nada. T47/T48 siguen sin iniciar.

El usuario pide después conservar sentinel de Python 3.15, en lugar de Enum o actualizar herramientas. Se implementan ambos sentinels con sus alias de tipo; se amplían los tipos de claves del DAO a int/UUID y se retira el cast a int de create. Cinco pruebas enfocadas correctas y suite de 109 pruebas correcta (56.557 s). El probe de persistencia pasa con PostgreSQL real: añade consulta presente/ausente por get/get_by/get_for_update, clave UUID ausente, y conserva migraciones/rollback/concurrencia. No modifica el esquema de producto. El intento inicial de pruebas dentro del aislamiento tuvo dos errores de temporales/asyncio; fuera del aislamiento pasan, con el mismo entorno. UV_CACHE_DIR apunta a .uv-cache del repositorio por el fallo de permisos de la caché del sandbox; sin instalación ni actualización.

El análisis posterior devuelve 46 errores en 97 archivos, incluidos dos reportInvalidTypeForm en los alias de sentinel. La reducción desde 155 no acredita el estrechamiento: el analizador trata ese tipo como desconocido. Se conserva esa limitación por la decisión posterior del usuario y no se declara cierre estático correcto. PostgreSQL/Keycloak de pruebas conservan PID 9400/32092. T46 queda comprobada con ese límite explícito; C16 sigue sin aceptar.

Fuentes: [sentinel en Python 3.15](https://docs.python.org/3.15/builtins/functions.html#sentinel), [tipos de sentinels](https://typing.python.org/en/latest/spec/special-types.html#sentinels), [CLI de basedpyright](https://docs.basedpyright.com/latest/configuration/command-line/), [configuración](https://docs.basedpyright.com/latest/configuration/config-files/) y [Enum](https://docs.python.org/3.15/howto/enum.html). Se contrastan con la CLI instalada y los casos mínimos; no se atribuye soporte por leer la documentación.

### T47: Acotar los resultados opcionales de operaciones

**Estado:** Done. **Propietario:** sync y cuentas. **Tamaño:** M. **Dependencias:** T46 comprobada con el límite estático registrado.

**Aceptación:**

- [x] Los accesos a error.code y state dejan de depender de una relación entre campos que el tipo no expresa; comprobar campos/tipo concretos antes de usarlos y declarar el retorno específico de invitaciones.
- [x] Accepted, duplicate, conflict, rejected y retryable_failure conservan sus formas públicas y el resultado original; un estado interno inválido no produce AttributeError ni un éxito inventado.
- [x] Ningún diagnóstico objetivo se oculta con casts, ignores o configuración; evitar una jerarquía de clases por acción si basta una guarda y un tipo de retorno preciso.

**Archivos previstos:** src/api/sync/domain/operations.py; src/api/sync/application/operations_cases.py; src/api/accounts/application/invitations_cases.py; tests/test_operations.py.

**Comprobación:** analizador localizado en T46; `uv run --locked python -m unittest discover -s tests -p test_operations.py -v`; probes `test-support/sync/check.py` y `test-support/team/check.py` con `uv run --locked python`. Revisar aceptación, rechazo y repetición de invitación por HTTP. Ampliar pruebas solo para invariantes que los casos actuales no cubran.

**Transacción/consumidores:** conservar reautorización, recibos y rechazo inicial sin pertenencia; sin nuevas tablas ni commit parcial. JSON y semántica de estados estables.

**Evidencia:** cuatro pruebas enfocadas correctas (1.746 s). El nuevo caso comprueba aceptación, duplicado y los tres estados de fallo, incluidos originales rechazados y ocho resultados internos incompletos/incompatibles; estos últimos producen DAOError, sin AttributeError ni éxito. accept_invitation declara InvitationAcceptanceResult y sus errores; el efecto de cuentas y el estado de operation_result tienen tipos explícitos. Probes sync y equipo correctos con PostgreSQL/Keycloak reales: duplicados concurrentes, autorización vigente, aceptación/revocación, rechazo inicial, rollback y respuesta perdida en ASGI. El analizador baja de 46 a 44 errores y ya no señala los dos accesos opcionales de accept_invitation; no hay cambios de configuración ni supresiones. Conserva los límites de sentinel y otros recorridos pendientes. Sin cambios SQL, rutas, commits ni servicios nuevos.

### T48: Anotar los validadores compartidos

**Estado:** Done. **Propietario:** accounts, sync, audit y esquema técnico. **Tamaño:** M. **Dependencias:** T47 comprobada.

**Aceptación:**

- [x] Validadores y serializadores de los archivos afectados declaran sus entradas y salidas reales; model validators after devuelven Self.
- [x] Los validadores de campo de este bloque son after y usan el tipo real del campo o de sus campos atendidos; no hay before nuevos ni Any para suplir firmas.
- [x] Null, campos ausentes, credenciales exactas y serialización UTC conservan su conducta; ninguna nueva regla de producto aparece al añadir tipos.

**Archivos previstos:** src/api/accounts/domain/accounts.py; src/api/sync/domain/operations.py; src/api/audit/domain/audit.py; src/core/schema/http.py.

**Comprobación:** analizador de T46; pruebas existentes `test_account_changes.py`, `test_operations.py`, `test_audit.py` y `test_common_support.py`, mediante unittest discover con -p por archivo. Revisión manual de firmas frente al modo de cada validador. No escribir pruebas que solo repitan una anotación.

**Transacción/consumidores:** sin efecto transaccional; mismas entradas, errores y representación pública.

**Evidencia:** 14 pruebas enfocadas correctas (test_account_changes, test_operations, test_audit y test_common_support); sus casos vuelven a pasar en la suite final tras completar el ajuste de esquemas. Revisión AST de las doce firmas decoradas: entradas y salidas explícitas y Self en los dos model validators after. @classmethod explícito corrige la llamada compartida al validador de país. Se retiran tres declaraciones exactamente duplicadas de AuditQuery, sin cambiar campos ni reglas.

Los retornos de serializadores tipados alteraban el esquema generado al usar str sin formato. SerializedInstant conserva date-time en las tres salidas afectadas; las sobrecargas de serialize_instant precisan el retorno sin cambiar su cuerpo. unless-none mantiene acceptedAt nulo sin declarar expiresAt anulable. occurredAtLocal conserva su default nulo explícito en el esquema. Los seis esquemas JSON de validación/serialización de InvitationResponse, AuditEventResponse y OperationEnvelope coinciden con los de antes de T48 al ignorar solo el orden de alternativas de unión. No se añaden pruebas que repitan anotaciones.

Fuentes de Pydantic 2.14.1: [validadores](https://github.com/pydantic/pydantic/blob/v2.14.1/docs/concepts/validators.md), [WithJsonSchema](https://github.com/pydantic/pydantic/blob/v2.14.1/docs/concepts/json_schema.md#withjsonschema-annotation) y [serializadores](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.field_serializer), contrastados con el paquete instalado. Sin nuevas dependencias. El analizador no señala las firmas de los cuatro archivos de T48; el cierre global conserva los avisos detallados en C16.

### T49: Anotar validadores de pacientes, servicios y agenda

**Estado:** Done. **Propietario:** patients, services y schedule. **Tamaño:** M. **Dependencias:** C16 aceptado con el límite estático de sentinel conservado.

**Aceptación:**

- [x] Todos los validadores/serializadores de estos cuatro archivos tienen tipos explícitos, incluidos value y retorno; conservar Self donde corresponda.
- [x] Se conservan teléfono/documento, fecha frente a instante, patches, duración estricta, vigencia y estados.
- [x] El analizador no necesita excepciones para las llamadas compartidas a validadores ni para los valores devueltos.

**Archivos previstos:** src/api/patients/domain/patients.py; src/api/patients/domain/contacts.py; src/api/services/domain/services.py; src/api/schedule/domain/schedule.py.

**Comprobación:** analizador; `uv run --locked python -m unittest discover -s tests -p test_patients.py -v`, y equivalentes existentes para test_services.py/test_schedule.py. Revisar manualmente valor inválido, null explícito y ausencia. Sin nueva validación de negocio.

**Transacción/consumidores:** sin escrituras; contratos y datos conservados.

**Evidencia:** 17 pruebas enfocadas correctas (10 pacientes, 4 servicios, 3 agenda). Los 72 esquemas JSON de validación/serialización de los 36 modelos definidos en los cuatro archivos coinciden con el inicio, salvo orden de alternativas de unión. Entradas before object, salidas precisas, classmethod explícito y Self en after. Serializadores distinguen inicio requerido de extremos opcionales para conservar null y date-time; se reutiliza SerializedInstant de T48. La guarda del teléfono comprueba ambas partes tras el rechazo previo de parejas incompletas. Analizador: 35 errores en 97 archivos, sin errores en esos cuatro archivos; sin supresiones, dependencias ni reglas nuevas. Fuentes Pydantic 2.14.1 de T48 conservadas.

### T50: Tipar el acceso afectado de identidad y cuentas

**Estado:** Done. **Propietario:** authorization, accounts y audit. **Tamaño:** M. **Dependencias:** T49 comprobada.

**Aceptación:**

- [x] Parámetros y retornos de los métodos afectados expresan filas, ausencia, listas, estados y tiempo del servidor con tipos concretos. La ausencia conserva el límite de sentinel ya registrado.
- [x] Los nuevos casos own_professional, account_professional y catalog_accounts declaran contexto, identidad, IDs y Ok/Err sin importar repositorios ajenos.
- [x] Se mantienen permisos vigentes, orden de bloqueo, refresco tras espera y propiedad; ningún tipo justifica omitir una comprobación real.

**Archivos previstos:** src/api/authorization/repository/dao.py; src/api/accounts/repository/dao.py; src/api/accounts/application/management_cases.py; src/api/audit/repository/dao.py.

**Comprobación:** analizador; controles existentes `test_accounts_structure.py` y `test_authorization_structure.py`; probes de acceso/cuentas/equipo. Revisar manualmente las firmas frente a los resultados SQL y las guardas de los casos. Corregir consumidores solo si el cambio de tipo los exige; dividir antes si se exceden cinco archivos.

**Transacción/consumidores:** misma sesión y locks; sin cambios de permiso, SQL de producto o identidad externa.

**Evidencia:** 40 controles de estructura correctos y probes de acceso/cuentas/equipo correctos con PostgreSQL/Keycloak de prueba. Firmas completas en los DAOs afectados y en own_professional/account_professional/catalog_accounts; los casos consumen respuestas de dominio. Row de SQLAlchemy 2.1.6 usa parámetros variádicos (Row[Professional, str, str]), contrastados con el paquete instalado. Guardas previas al acceso en revise/rename y ante datos globales de dispositivo ausentes; sin consultas ni locks nuevos. Tiempos del servidor usan scalar_one sobre la misma consulta. Analizador: 31 errores globales, ninguno en los cuatro archivos de T50. Se mantienen sentinel y los avisos de bloques posteriores/código previo. Fuentes: [SELECT de ORM 2.1.6](https://docs.sqlalchemy.org/en/21/orm/queryguide/select.html#selecting-orm-entities) y [AsyncSession.execute](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncSession.execute). Sin dependencias nuevas.

### T51: Tipar los DAOs de datos operativos afectados

**Estado:** Done. **Propietario:** patients, services, schedule y sync. **Tamaño:** M. **Dependencias:** T50 comprobada.

**Aceptación:**

- [x] Los métodos afectados declaran AsyncSession, IDs, consultas, filas, valores de actualización, paginación y retornos, sin nuevos Any, casts o supresiones. Los retornos son filas concretas o mappings de object; sentinel conserva su límite estático previo.
- [x] Las claves compuestas y los pares oferta/servicio conservan su forma; ausencia usa el acuerdo comprobado de T46.
- [x] No cambia la responsabilidad de consultar/escribir en DAO ni commit=False en los casos coordinados.

**Archivos previstos:** src/api/patients/repository/dao.py; src/api/services/repository/dao.py; src/api/schedule/repository/dao.py; src/api/sync/repository/dao.py.

**Comprobación:** analizador; controles de estructura de test_accounts_structure.py; probes de pacientes/servicios/agenda/sync. Revisión manual del tipo inferido al recibir una fila y después de comprobar ausencia. No añadir otra base DAO ni interfaces vacías.

**Transacción/consumidores:** versiones, contadores, journal y aislamiento conservados. C17 requiere suite completa y build offline.

**Evidencia:** probes de pacientes/servicios/agenda/sync correctos con PostgreSQL/Keycloak reales, seguidos por persistencia aislada. Todos los métodos de los siete DAOs modificados entre T50/T51 tienen parámetros y retornos; las proyecciones conservan mappings de object y las uniones de ORM usan Row variádico de SQLAlchemy 2.1.6. Misma SQL, sesión, filtros, orden, LIMIT/OFFSET, locks, claves compuestas y commit=False. No se crean capas ni interfaces. Analizador final: 28 errores en 97 archivos, ninguno en los doce archivos de producto del bloque. El cierre completo se registra en C17; no se presenta el análisis global como correcto.

### T52: Unificar la validación de operaciones de cuentas

**Estado:** Done. **Propietario:** sync y accounts. **Tamaño:** M. **Dependencias:** C17 aceptado al pedir continuar con el resto de las correcciones.

**Aceptación:**

- [x] Seleccionar/validar una vez el payload de las acciones de cuenta e invitación; el caso reutiliza ese dato tipado. No crear un sistema de comandos ni otra capa de coordinación.
- [x] La huella coincide con la anterior para datos ficticios representativos: defaults, texto válido, ausencia/null de patch, fechas/IDs y aliases. Un payload inválido conserva su JSON recibido y un rechazo seguro.
- [x] Recibos previos y duplicados mantienen significado; ninguna credencial/correlación se incorpora a la huella ni se persiste el payload personal.

**Archivos previstos:** src/api/sync/domain/operations.py; src/api/sync/application/operations_cases.py; src/api/accounts/application/management_cases.py; src/api/accounts/application/invitations_cases.py; tests/test_operations.py.

**Comprobación:** analizador; test_operations.py; probes sync/equipo/cuentas. Fijar antes del cambio ejemplos ficticios con huellas esperadas y contrastar después. Revisar petición original, equivalente con defaults y petición distinta bajo la misma operationId.

**Transacción/consumidores:** validación estructural no sustituye autorización vigente; efecto, recibo, auditoría y journal siguen juntos. Migración gradual: los componentes no trasladados conservan su conducta hasta T53/T54; no dejar el mecanismo temporal en el cierre.

**Evidencia:** se fijan antes del cambio 48 huellas ficticias del recorrido anterior en tests/fixtures/operation_hashes.json, con origen/versiones. Todas coinciden con el recorrido nuevo de accept_operation. Seis pruebas de operaciones correctas, incluida selección única por modelo y reutilización real de la instancia en casos de cuenta/invitación. La primera fixture de esa prueba omitía owner_user_id; se completa sin cambiar producto para ella y la repetición pasa. Probes cuentas/equipo/sync correctos con PostgreSQL/Keycloak reales. El normalizador de cuentas se retira; los demás permanecen solo hasta T53/T54. Analizador: 22 errores globales, sin avisos en management_cases/invitations_cases. Sin cambios de configuración ni dependencias. Fuentes Pydantic 2.14.1: [modelos](https://github.com/pydantic/pydantic/blob/v2.14.1/docs/concepts/models.md) y [model_dump/exclude_unset](https://github.com/pydantic/pydantic/blob/v2.14.1/docs/concepts/serialization.md).

### T53: Reutilizar el payload validado de pacientes y contactos

**Estado:** Done. **Propietario:** patients y sync. **Tamaño:** M. **Dependencias:** T52 comprobada.

**Aceptación:**

- [x] Pacientes, documentos, contactos y vínculos reutilizan el payload ya validado; retirar sus normalizadores y la segunda lectura del original.
- [x] Se preservan defaults, texto documental exacto, parejas de teléfono, formatos de fecha/instante y campos presentes de patch al obtener la huella.
- [x] No cambia completitud, propiedad, restricciones diferidas, recepción de rechazos ni reautorización del duplicado.

**Archivos previstos:** src/api/patients/application/patients_cases.py; src/api/patients/application/contacts_cases.py; src/api/sync/application/operations_cases.py; tests/test_patients.py; tests/test_operations.py.

**Comprobación:** analizador; pruebas de pacientes/operaciones; probes pacientes/sync. Revisar el mismo payload válido antes/después y rechazos con valores inválidos distintos. Mantener separadas identidad declarada y verificación.

**Transacción/consumidores:** misma aceptación y claves/huellas; sin cambios de esquema ni reglas de reserva.

**Evidencia:** 16 pruebas enfocadas correctas (10 pacientes, 6 operaciones), con las 48 huellas previas conservadas y una selección por modelo. Probe pacientes correcto con PostgreSQL/Keycloak: documentos declarados, completitud diferida, contactos y carreras; incluye el probe sync. Se retiran ambos normalizadores y se pasan instancias validadas a los casos. Las validaciones restantes comprueban el estado guardado combinado con patches, no vuelven a leer el payload original. CONTACT_SCHEMAS pasa a su domain y sync lo consume como fuente única; se modifica también ese domain y sync/domain/operations.py, cinco archivos de producto en total. Sin nueva capa, esquema SQL ni reglas de verificación. Analizador ejecutado y resultado conservado en .tmp/c18-types/t53-static.json.

### T54: Reutilizar el payload validado de servicios y reglas

**Estado:** Done. **Propietario:** services, schedule y sync. **Tamaño:** M. **Dependencias:** T53 comprobada.

**Aceptación:**

- [x] Servicios, ofertas y reglas consumen una entrada tipada validada una vez; retirar sus normalizadores y la cadena completa de seis funciones en sync.
- [x] `{}` y override explícito null siguen siendo equivalentes para OfferService; UpdateServiceOffer requiere su campo, y ausencia/null de patches conserva su diferencia. No coaccionar booleanos a enteros.
- [x] Tipar los parámetros/retornos de los casos modificados y conservar las versiones, permisos, duración y rechazo de reglas incompatibles del alcance actual.

**Archivos previstos:** src/api/services/application/services_cases.py; src/api/services/application/offers_cases.py; src/api/schedule/application/schedule_cases.py; src/api/sync/application/operations_cases.py; tests/test_operations.py.

**Comprobación:** analizador; pruebas de operaciones/servicios/agenda; probes servicios/agenda/sync. Revisar huellas equivalentes/diferentes y buscar consumidores restantes de normalized_*; no retirar funciones antes de migrar su último consumidor.

**Transacción/consumidores:** no cambiar la coordinación del profesional ni los grupos por cuenta. C18 requiere suite completa, pruebas reales de rollback/idempotencia y build offline.

**Evidencia:** 13 pruebas enfocadas correctas (operaciones/servicios/agenda) y probes servicios/agenda/sync correctos. La selección de esquemas queda en sync/domain/operations.py; los casos reciben BaseModel validado o None y comprueban el tipo antes de usar sus campos. Los cinco archivos de producto son los tres casos, sync/application y sync/domain. No hay normalized_*payload ni model_validate(payload) en src; las comprobaciones de estados propuestos se conservan. El probe de agenda que llama al caso directamente entrega ahora ScheduleRuleStatusPayload, sin restaurar la validación retirada. Se amplía el probe de pacientes para observar una validación por petición y comprobar un recibo real con huella previa a T52, duplicado con defaults equivalentes y conflicto de contenido, sin guardar el payload. Fuentes Pydantic 2.14.1 de T52; cierre completo en C18.

### T55: Separar la proyección de ofertas de su serialización

**Estado:** Done. **Propietario:** services y sync. **Tamaño:** M por paso. **Dependencias:** C18 aceptado expresamente: «Acepto C18; continúa T55–T57».

**Desglose previo a código:** T55.1 traslada la proyección a un dict tipado y adapta todos sus consumidores de escritura (domain/offers.py, accounts/domain/accounts.py, offers_cases.py, services_cases.py y sync/application/operations_cases.py: cinco archivos de producto). Aceptación: salida interna revisable, validación/serialización antes del commit y rollback de una proyección inválida en la segunda cuenta; pruebas/probe servicios y operaciones. T55.2, tras comprobar T55.1, adapta read_offers y services_api.py para dict y response_model; prueba HTTP, esquema y total autorizado. Ambos reutilizan la misma sesión/recibo/journal y no añaden campos ni contratos. La división conserva T55 y el checkpoint final C06; se añade services_cases.py porque también consume offer_response. No se abre trabajo paralelo.

**Aceptación:**

- [x] La proyección de oferta usa un dict con tipos y campos explícitos cuando solo reúne datos de salida; no construye ServiceOfferResponse para devolverla de inmediato. Conservar un helper solo si sus consumidores lo justifican.
- [x] El HTTP declara response_model y un retorno que coincide con el valor real; recibo y journal validan/serializan esa proyección dentro de la transacción antes de confirmar, con la fuente de esquema existente.
- [x] Se conservan camelCase, UTC, UUID, campos permitidos, ambas versiones y audiencia privada/pública; un error de proyección revierte efecto/recibo/auditoría/grupos completos.

**Archivos previstos:** src/api/accounts/domain/accounts.py; src/api/sync/application/operations_cases.py; src/api/services/application/offers_cases.py; src/api/services/infrastructure/services_api.py; tests/test_services.py.

**Comprobación:** analizador; pruebas existentes de servicios/operaciones; probe servicios con rollback en la segunda cuenta y probe sync. Revisar respuesta GET, resultado guardado y proyección del journal del mismo dato ficticio. No devolver __dict__ ni un ORM completo para evitar el mapeo.

**Transacción/consumidores:** AccountEffect/AccountChange deben aceptar la representación explícita acordada, sin posponer el control al HTTP ni convertir core en soporte de negocio. Mantener Pydantic donde comprueba estado interno necesario.

**Evidencia (2026-10-26):** T55.1 y T55.2 comprobadas en orden. Cuatro pruebas de servicios y probe real servicios/sync correctos; una proyección inválida en la segunda cuenta devuelve retryable_failure y conserva los contadores, el nombre y la posibilidad de reintentar. HTTP usa dict y response_model; OpenAPI completo igual a la captura previa. Analizador: los mismos 16 avisos documentados en C18, ninguno nuevo en estos consumidores. El recibo y el journal conservan validación y JSON antes del commit.

### T56: Simplificar las lecturas HTTP restantes de C06

**Estado:** Done. **Propietario:** services y schedule. **Tamaño:** M. **Dependencias:** T55 comprobada.

**Aceptación:**

- [x] Las lecturas de catálogo/reglas devuelven dicts tipados con items/total y response_model en rutas; retirar construcciones de respuesta que solo repiten esos datos.
- [x] Se conservan los objetos que sí aplican reglas de dominio, como los intervalos y la propuesta semanal; no eliminar validación interna necesaria por analogía con la salida HTTP.
- [x] Los casos afectados declaran contexto, consultas y resultados reales; las rutas conservan solo endpoints/configuración, sin Request ni helpers de serialización.

**Archivos previstos:** src/api/services/application/services_cases.py; src/api/schedule/application/schedule_cases.py; src/api/services/infrastructure/services_api.py; src/api/schedule/infrastructure/schedule_api.py; tests/test_schedule.py.

**Comprobación:** analizador; pruebas de servicios/agenda y controles de estructura; ambos probes reales. Revisar JSON y OpenAPI generados, filtros, total autorizado, página vacía, estado inactivo y acceso ajeno. No ampliar esta tarea a reconstruir todas las respuestas antiguas de otros componentes.

**Transacción/consumidores:** conservar el límite de lectura y el filtrado; sin nuevos campos ni contratos de consumidor. Las escrituras mantienen el control interno probado en T55.

**Evidencia (2026-10-26):** Cuatro pruebas de servicios y tres de agenda correctas; ambos probes reales correctos. Catálogo, ofertas y lista/detalle de reglas devuelven dicts con campos explícitos; rutas con response_model. OpenAPI completo idéntico a la captura anterior a T55. Intervalos, propuesta y validación de escrituras conservados. Esquema SQL, migraciones, manifiesto y lock sin cambios. Analizador conserva los 16 avisos previos, sin avisos nuevos en estas lecturas.

### T57: Cerrar la corrección y ajustar la evidencia de C06

**Estado:** Done. **Propietario:** revisión y documentación. **Tamaño:** M. **Dependencias:** T56 comprobada.

**Aceptación:**

- [x] Diagnósticos objetivo corregidos en los consumidores afectados, salvo el límite de sentinel elegido por el usuario; salida real del analizador con 16 errores residuales detallados en el cierre. Sin nuevas supresiones ni reglas desactivadas. Imports/espacios y diff revisados frente al trabajo previo del usuario.
- [x] Suite completa, ocho probes reales, migraciones aisladas, build/inspección del paquete y git diff --check pasan; registrar por separado cualquier límite o fallo ajeno, sin presentarlo como comprobado.
- [x] El plan distingue intervalos ficticios de citas reales: las comprobaciones de protección/conservación con reservas quedan pendientes en T22/T32, y no como prueba cumplida en T17/T18. Entregar C06 sin aceptar ni iniciar T19.

**Archivos previstos:** AGENTS.md; docs/api-v1.md; docs/operations/development.md; este todo.md; plan.md. AGENTS documenta las reglas aprobadas de tipos y respuesta HTTP; no añade prohibiciones generales sobre esquemas con uso real.

**Comprobación:** comando real del analizador registrado en T46; `uv run --locked python -m unittest discover -s tests -v`; `uv run --locked python test-support/<componente>/check.py` para los ocho archivos que ya existen (access, accounts, sync, team, patients, services, schedule, persistence); `uv build --offline`; `git diff --check`. El marcador <componente> representa esos archivos existentes, no es un comando para copiar literalmente. No ejecutar la prueba HTTP separada del wheel.

**Transacción/consumidores:** pruebas de datos ficticios en PostgreSQL aislado; servicios existentes conservados. Sin cambios SQL, consumidor Rust/Hub, dependencia nueva, commit o despliegue. La revisión final incluye que la huella antigua sigue recuperando su recibo.

**Evidencia:** cierre T57 registrado al final de este documento. Los avisos estáticos pendientes se detallan por separado; no se afirma un análisis global sin errores.

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
- [x] Usuario acepta el 2026-10-26: «Aprobado, por favor escríbeme un prompt para continuar esto en otra sesión». Habilita T16 → T17 → T18 hasta revisión C06; en esta sesión solo se prepara el traspaso.

### C06: Catálogo y horario habitual

**Corrección comprobada:** T46–T57 verificadas y C16–C18 aceptados. C06 queda para revisión expresa; T19 no se inicia. Las pruebas con intervalos ficticios no acreditan reservas reales, pendientes de T22/T32.

- [x] T16–T18 comprobadas y evidencia registrada dentro del alcance actual; integración con reservas reales conserva T22/T32.
- [x] Pruebas aplicables y recorrido del bloque comprobados; límites de disponibilidad, citas y consumidores identificados.
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

### C16: Tipos base · aceptado con límite estático

- [ ] Reducción estática de sentinel pendiente de soporte de basedpyright 1.40.2. T46–T48 implementadas y analizadas sin supresiones nuevas; los accesos opcionales de accept_invitation están resueltos. El usuario pidió conservar sentinel tras recibir la evidencia del límite; esta decisión no acepta C16.
- [x] Pruebas enfocadas, suite completa, build offline y revisión del recorrido de ausencia/resultado/validadores. Evidencia nueva en el registro siguiente.
- [x] El usuario permite continuar el 2026-10-26: «Podemos continuar para terminar la revisión y corrección de código». C16 aceptado con el límite de sentinel registrado; habilita T49–T51, sin aceptar C17/C06.

### C17: Tipos de los recorridos · aceptado

- [x] T49–T51 comprobadas; entradas y filas tipadas. La ausencia conserva el sentinel elegido por el usuario y el límite del analizador registrado en C16.
- [x] Analizador ejecutado sin supresiones nuevas: 28 errores globales pendientes, ninguno en el bloque. Pruebas enfocadas, suite completa, ocho probes, build offline y revisión del paquete correctos; límites siguientes explícitos.
- [x] El usuario permite continuar con «Puedes continuar con el resto de las correcciones». Habilita T52–T54, sin aceptar C18 ni C06.

### C18: Validación e idempotencia · pendiente

- [x] T52–T54 comprobadas; no quedan normalizadores distribuidos ni segunda validación del payload original en esos recorridos.
- [x] Huellas previas/defaults/patch/rechazos, duplicados y rollback reales comprobados; 112 pruebas, ocho probes y build offline correctos. Analizador ejecutado con 16 avisos pendientes explícitos, no correcto globalmente; sin supresiones nuevas.
- [x] El usuario acepta: «Acepto C18; continúa T55–T57». C06 sigue pendiente y T19 no se habilita.

## Registro de comprobaciones

### T52 → T53 → T54 · 2026-10-26 · C18 para revisión

- El usuario permite continuar tras C17 con «Puedes continuar con el resto de las correcciones». Trabajo secuencial y sin delegación. C18 y C06 siguen sin aceptar; T55/T19 no se inician.
- Una selección de esquema y una validación por operación producen el modelo usado por huella y ejecución. Las 48 huellas capturadas antes de T52 coinciden, incluidas defaults, vacío/null de OfferService, patches, fechas, documentos, teléfonos, booleanos inválidos y JSON recibido de rechazos. Fixture con origen/versiones y solo datos ficticios. Las seis funciones de normalización se retiran sin consumidores pendientes.
- El probe PostgreSQL de pacientes acredita una validación por petición real, request_hash igual al valor anterior a T52, recuperación del recibo al añadir defaults equivalentes y conflicto al cambiar contenido. Los duplicados y conflictos no añaden efectos. El recibo conserva estado permitido, no payload de entrada. Se mantienen las validaciones de propuestas que combinan fila guardada y patch.
- Suite final: 112 pruebas correctas en 61.078 s. Ocho probes reales correctos (acceso, cuentas, sync, equipo, pacientes, servicios, agenda y persistencia), con migraciones aisladas hasta 20261026_08/21 tablas, rollback inmediato/diferido, carreras y respuesta perdida en ASGI. Las bases aleatorias se eliminan; PostgreSQL/Keycloak de prueba se conservan. Agenda sigue usando intervalos ficticios, sin citas reales; T22/T32 mantienen esa prueba.
- Build offline correcto, wheel de 152 entradas con los diez módulos modificados iguales a la fuente y sin fixtures, pruebas ni carpetas privadas. Los 72 esquemas JSON del bloque previo siguen iguales, salvo orden de alternativas de unión. Sin HTTP separado del wheel, dependencias, cambios SQL, commits, despliegues ni cambios en otros repositorios. git diff --check correcto; app, motor/fábrica, DAO base, base de esquemas, lockfile y sentinel conservados.
- basedpyright 1.40.2 analiza 97 archivos y devuelve 16 errores. Cuatro accesos en contactos siguen sin reducir Empty; dos avisos corresponden a los alias de sentinel sin soporte. Los otros diez están en resultado Err[Never] de accounts_cases, dos nombres de tabla, seis exportaciones previas de users y el módulo previo de caché. No quedan avisos sobre la selección del tipo de payload ni accesos a error.code opcional; no se ocultan los pendientes ni se declara un cierre estático global correcto.

### T49 → T50 → T51 · 2026-10-26 · C17 para revisión

- El usuario permite continuar tras C16 con «Podemos continuar para terminar la revisión y corrección de código». Trabajo secuencial y sin delegación. C17/C18 y C06 quedan sin aceptar; T52/T19 no se inician.
- T49: 17 pruebas enfocadas y 72 esquemas JSON de 36 modelos conservados (se ignora solo el orden de alternativas de unión). T50: 40 controles de estructura y probes de acceso/cuentas/equipo correctos. T51: pacientes/servicios/agenda/sync y persistencia correctos. Ocho probes de esta ejecución usan PostgreSQL/Keycloak reales y bases aleatorias aisladas eliminadas al salir; ningún dato real. Agenda sigue usando intervalos requeridos ficticios, sin citas; T22/T32 conservan su prueba real.
- Suite final: 110 pruebas correctas en 52.217 s. Build offline correcto; wheel de 152 entradas con los doce módulos modificados idénticos a la fuente y sin carpetas privadas ni pruebas. Sin HTTP separado del wheel.
- basedpyright 1.40.2 con Python 3.15.1 y la configuración existente: 97 archivos, 28 errores, ninguno en los doce archivos de producto modificados. Los pendientes están en selección/uso de payloads de cuentas/contactos (T52/T53), dos nombres de tabla, exportaciones previas de users, el módulo previo de caché y los dos alias de sentinel sin soporte. No se cambian diagnósticos, herramientas ni dependencias; no se atribuye la reducción a soporte nuevo de sentinel.
- Se conservan los imports y cambios previos del usuario, los demás archivos de producto, pruebas y scripts, manifiesto/lockfile, AGENTS, esquema SQL/migraciones, app, motor/fábrica, DAO base y los sentinels. git diff --check correcto. Servicios de prueba conservados con PID 9400/32092; sin commits, despliegues ni cambios en otros repositorios. Fuentes oficiales y versiones en T49/T50; revisión AST de las firmas de DAO sin omisiones.

### T46 → T47 → T48 · 2026-10-26 · C16 para revisión con límite estático

- Ampliación aprobada por el usuario; trabajo secuencial, sin delegación. Tras localizar basedpyright 1.40.2 de Zed y comprobar que no admite el sentinel en anotaciones, el usuario pide mantener la propuesta de Python 3.15. No se instala/actualiza el analizador ni se elige Enum. C16 y C06 siguen sin aceptar; T49/T19 no se inician.
- Suite final: 110 pruebas correctas en 61.041 s, incluidos controles de estructura sin excepciones nuevas. Ocho probes reales correctos después de T48: acceso, cuentas, sync, equipo, pacientes, servicios, agenda y persistencia. Migraciones hasta 20261026_08, 21 tablas, upgrade/downgrade/reaplicación y rollback de revisión fallida en bases aleatorias aisladas eliminadas al salir. El probe de agenda usa intervalos ficticios, sin citas reales; T22/T32 conservan esa prueba.
- Analizador: 97 archivos, 40 errores, sin avisos en las firmas de T48 ni en accept_invitation. Dos errores son reportInvalidTypeForm en EmptyType/UndefinedType por falta de soporte. El resto permanece en payloads/casos/DAOs de bloques posteriores y código previo (users, modelos y caché). No se declara correcto el análisis global ni se interpreta la reducción 155 → 40 como prueba del tipo de ausencia; parte de la reducción procede de Unknown. Configuración y lockfile sin cambios.
- Build offline correcto; wheel de 152 entradas, ocho módulos modificados idénticos a la fuente, sin datos privados, pruebas ni carpetas de herramientas. No se ejecuta HTTP separado del wheel. Se conservan esquema SQL, migraciones, motor, fábrica, dependencia de sesión, app y alta administrativa. git diff --check correcto. Servicios de prueba conservados; sin commits, despliegues, consumidores ni cambios en otros repositorios.

### T16 → T17 → T18 · 2026-10-26 · C06 para revisión

- El usuario autoriza expresamente este bloque tras C05. Se trabaja una tarea a la vez, sin delegación, commits ni despliegue. No se inicia T19.
- Catálogo privado y ofertas por cuenta comparten aceptación/recibo/auditoría/grupos. Bloqueo del profesional antes de controles de cuenta ordenados, proyecciones members limitadas a ofertas, y rollback de ambos destinos comprobados. Duplicados y consulta de resultado vuelven a validar vínculo profesional.
- Agenda conserva reglas, une tramos locales y exige UQ abierta también con SQL directo. El control de incompatibilidad usa intervalos requeridos ficticios; T22/T32 conservan integrarlo con reservas reales, sin crear tablas/rutas anticipadas. T21 conserva disponibilidad completa y resolución de horas ambiguas/inexistentes.
- Suite final: 108 pruebas correctas en 51.714 s. Ocho integraciones reales correctas: acceso, cuentas, sync, equipo, pacientes, servicios, agenda y persistencia; servicios/agenda repetidos tras la revisión. Migraciones hasta 20261026_08 con 21 tablas, aplicadas/revertidas/reaplicadas en bases aleatorias aisladas que se eliminan. Build offline y wheel de 152 entradas comprobados; sin carpetas privadas ni prueba HTTP separada del wheel.
- Revisión de 28 Python y 14 Markdown, 78 enlaces locales: cinco destinos históricos ausentes, sin nueva ausencia. Fábrica, dependencia de sesiones, DAO base, esquema base, alta administrativa, manifiesto y lockfile sin cambios. git diff --check correcto. PostgreSQL/Keycloak conservan los PID 9400/32092. C06 queda sin aceptar; no hay autorización para T19.

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


### T55 → T56 → T57 · 2026-10-26 · Corrección final para revisión C06

- T55.1/T55.2 comprobadas antes de T56. offer_response devuelve ServiceOfferProjection con campos explícitos; sus consumidores usan dicts. El resultado y cada proyección del journal validan y serializan antes del commit con sus esquemas existentes. El probe provoca una proyección incompleta en la segunda cuenta: retryable_failure, cero cambios en contadores y estado, reintento aceptado. Se conservan ambas versiones y audiencias.
- T56: catálogo, ofertas y lista/detalle de reglas devuelven dicts, con tipos reales y response_model en las rutas. Propuesta, intervalos, referencia interna de reserva y validaciones de escritura conservan sus modelos. OpenAPI completo idéntico a la captura previa a T55; 72 esquemas JSON iguales a la base de C17, salvo orden no significativo de uniones.
- T57: `uv run --locked --offline python -m unittest discover -s tests -v`: 112 pruebas correctas en 52.924 s. Ocho probes reales correctos en secuencia: access, accounts, sync, team, patients, services, schedule, persistence. PostgreSQL aislado: head 20261026_08 de 21 tablas, upgrade/downgrade/reaplicación, fallo de revisión sin DDL parcial, permisos y dos escritores coordinados. PostgreSQL PID 9400 y Keycloak PID 32092 conservados; solo bases ficticias verificadas y eliminadas por los probes.
- `uv build --offline --out-dir .tmp/c06-final/build` correcto: wheel 152 entradas, 97 fuentes Python idénticas al árbol actual; sdist 153 entradas. Sin secretos, temporales ni pruebas privadas. No se ejecutó la prueba HTTP separada del wheel. `git diff --check` correcto. Esquema SQL, migraciones, manifiesto, lock y versión Python conservan las huellas anteriores a T52. HEAD sigue en 233569c; sin commits ni despliegues.
- basedpyright 1.40.2 de Zed, Python 3.15, 97 archivos: 16 errores, cero avisos nuevos en los consumidores corregidos. Seis derivan del soporte de sentinel elegido por el usuario (dos alias y cuatro accesos en contacts_cases); diez son previos: Err[Never] en accounts_cases, dos declaraciones __tablename__, seis exports retirados de users y valkey.asyncio ausente en código heredado. No hay supresiones nuevas, casts/Any añadidos ni configuración relajada. No se restauran módulos retirados ni se instala Valkey. El cierre NO acredita un análisis estático global correcto.
- Se releen estándares y especificación por separado, sin delegar. El diff y las huellas conservan las revisiones previas ajenas a estas tareas. AGENTS registra tipos reales, validación única de payload y dicts/response_model con validación interna antes del commit. T17/T18 separan casillas comprobadas con datos ficticios de reservas reales pendientes en T22/T32.
- Fuente: FastAPI 0.159.1 resuelto; guía oficial actual [response_model y prioridad](https://fastapi.tiangolo.com/tutorial/response-model/#response_model-priority), contrastada con el paquete instalado y HTTP/OpenAPI reales. El enlace al archivo de documentación etiquetado 0.159.1 no estuvo disponible; no se presenta esa lectura como realizada. Sin dependencia nueva.
- Evidencia local no versionada: `.tmp/c06-final/` (suite, ocho probes, salida JSON del analizador, OpenAPI previo/posterior y paquetes). Las 48 huellas previas se verifican en la suite y el probe de pacientes recupera un recibo real con la huella anterior sin persistir payload. No se acredita consumidor Rust/Hub, reservas reales, disponibilidad completa, snapshot, descarga, SSE ni producción.
- C06 pendiente de revisión y aceptación expresa del usuario. T19 continúa Todo.
