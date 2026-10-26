# Desarrollo de la base de proceso

**Lectura vigente al 2026-10-26:** C01/C02/C12/C13/C14 aceptados. La corrección T34–T45 queda para revisión en C15. C03 y C15 no están aceptados; T09 no está terminada. Las rutas HTTP siguen siendo las cuatro de credenciales.

## Estado actual en C15

Se retiran src/core/cursors.py, src/settings/cursor_settings.py y src/cli.py. No quedan módulos fuente de access ni imports de compatibilidad. Las listas propias de cuentas y dispositivos usan page/shows e items/total con LIMIT/OFFSET en DAO. Snapshot conserva ese contrato pero aún no tiene código; el avance incremental de sync sigue separado y pendiente de implementar.

scripts/create_practice.py lee un JSON, valida el esquema de accounts y llama al alta. Exige BOOTSTRAP_DATABASE_URI administrativa explícita y coincidencia exacta con OIDC_ISSUER. Selecciona esa URI solo en su proceso, antes de cargar la fábrica existente; no crea otra fábrica ni altera la configuración del API. Salida camelCase con identificadores o error breve sin datos privados. No hay subcomandos, seeders ni conexión al arranque del servidor. [Uso local](../../test-support/README.md#alta-administrativa).

La suite pasa 63 pruebas, con controles de estructura para users, authorization, accounts y sync. Comprueba casos sin acceso directo a sesiones, endpoints sin helpers/esquemas/Request, DAOs derivados, dominio sin proveedores ni SQL, esquemas de la base, imports entre componentes y ausencia de módulos retirados. La comprobación de esquemas carga cada archivo sin activar el __init__ del componente: no acredita las exportaciones antiguas ni ejecución de users, que se conserva como referencia de estilo.

Keycloak/PostgreSQL reales comprueban credenciales, cuentas, paginación autorizada, rollback, carreras y persistencia. El probe de cuentas incluye el script en un proceso aparte: alta, duplicado, rol operativo denegado, zona inválida y fallos de conexión seguros. Solo crea y elimina bases ficticias; conserva los servicios previos. El detalle de comprobaciones y build está en T45. Sin dependencias, migraciones, cambios a la fábrica, DAO base, esquema base ni rutas nuevas. Se omite la prueba HTTP separada del wheel. C15 habilitará retomar T09 y después T07 solo cuando el usuario lo acepte.

## Registro de C14

accounts posee esquemas derivados de la base, cinco modelos existentes y cinco DAOs derivados. Los casos usan transaction(db) y llaman a los casos públicos de authorization para identidad y a los de sync para su control técnico, con la misma sesión. No hay consultas, flush, commits directos ni imports de repositorios ajenos en application. sync posee AccountSyncHead y su DAO; el caso de alta crea ese registro en la misma transacción que las otras partes.

El alta exige la conexión administrativa; el rol de ejecución no puede crear la consulta desde ese caso. Antes de crear identidad se comprueba la zona en pg_timezone_names. El catálogo coincide con la restricción existente; Python no tiene tzdata en este Windows y no se añade una dependencia para repetir esa validación. Los valores issuer/subject se conservan exactos, y el país sigue validado con pycountry existente.

Las lecturas propias de cuentas y dispositivos usan page/shows, LIMIT/OFFSET en DAO e items/total. El resumen de usuario solo incluye su identidad y sus pertenencias visibles. El contexto de cuenta comprueba identidad, pertenencia, actividad y autorización de dispositivo; el estado de acceso puede consultarse antes de registrar la instalación y devuelve acciones vacías mientras T07 siga pendiente. El head se refresca al leer para no reutilizar una época anterior retenida en la sesión.

Comprobación: 50 pruebas correctas, incluidos 15 controles de estructura para authorization/accounts/sync; integración real de cuentas con Keycloak/PostgreSQL; persistencia con la revisión ya existente 20261025_02; build offline correcto. El alta concurrente produce una cuenta y un rechazo de duplicado. Un CHECK inválido del head revierte usuario, cuenta, pertenencia, profesional, vínculo y head; el reintento posterior funciona. Pruebas de cuenta inactiva, ámbito ajeno, dispositivo no registrado/revocado y época actual pasan. Las pertenencias y registros de dispositivos se preparan como fixtures; no acreditan invitaciones ni RegisterAccountDevice.

Se retiran los módulos de access que ya no tienen consumidores y las funciones sueltas de repository/heads.py. La CLI adapta imports, entrada y salida al caso corregido para seguir válida; T44 la sustituirá por scripts/create_practice.py. Los helpers antiguos de cursores permanecen sin consumidores hasta T43. No se añaden endpoints, migraciones, dependencias, tablas de producto ni código de sync incremental. Se conserva la fábrica, el DAO base y el esquema base del usuario. Las integraciones crean/eliminan solo bases aleatorias del clúster de pruebas; los servicios previos siguen activos.

## Registro de C13

El recorrido es endpoint → caso de uso → DAO. En authorization, infrastructure contiene solo las cuatro rutas y su configuración; domain contiene los esquemas derivados de la base y los tipos/errores propios. Los casos de application delimitan transaction(db), llaman a los DAOs y devuelven Ok/Err. SQLAlchemy aparece allí solo como anotación de AsyncSession bajo TYPE_CHECKING. No hay consultas, flush ni commits directos en los casos.

AppUserDAO, DeviceDAO y DeviceTokenDAO heredan del DAO existente. Los métodos específicos conservan identidad exacta, bloqueo y relectura después de esperas. Los casos usan commit=False en cada escritura; la misma transacción cubre revocación de credencial, reemplazo y enlace al sucesor. El bloqueo de usuario conserva el orden anterior y serializa sus peticiones; no se amplía concurrencia sin probar primero sus carreras.

OIDC y generación/lectura de tokens viven en core/services. El proveedor se consulta antes de abrir la transacción y no importa componentes del API. Las rutas usan Depends(get_db), esquemas de domain, resultados Ok/Err y HTTPException; el manejo común añade correlación y cabeceras sin Request en los endpoints. OpenAPI y las respuestas de credenciales usan camelCase. Se conserva el secreto y la pareja issuer/subject sin recortes; subject vacío solo con espacios se rechaza.

Comprobación: 36 pruebas unitarias correctas, incluidas cinco de estructura aplicadas a authorization sin excepciones, y build offline correcto. El probe de acceso pasa con Keycloak 26.8.1 y PostgreSQL 18.3 reales: hash, aislamiento, carreras de rotación/revocación y rollback de dos fallos CHECK. Las bases ficticias son nuevas, guardan data_directory y se eliminan al terminar; se aplica solo la revisión de credenciales 20261025_01, sin tocar el trabajo parcial de cuentas. HTTP usa ASGITransport sin servidor ni test separado de wheel.

La fábrica de sesiones, get_db/session, DAO base, esquema base, migraciones y dependencias conservan sus huellas. access mantiene solo código parcial de cuentas y los imports necesarios para trasladarlo en C14; ya no contiene las rutas, el caso ni el adaptador OIDC de credenciales. La retirada completa, los cursores de página y el script conservan sus tareas y revisiones posteriores. Se reutilizaron los servicios de prueba previos, que siguen activos; no se inició ni detuvo el servicio personal.

## Registro de C12

Se conserva src.application:app, la fábrica de sesiones, get_db/session y el arranque directo, sin main/lifespan de base de datos ni comando propio del paquete:

```powershell
uv run --locked uvicorn src.application:app --host 127.0.0.1 --port 8000
```

El motor actual exige una URI al importar la app, aunque no abre conexión por importar o iniciar. Las pruebas se adaptan a esa configuración y al lugar donde get_db importa su fábrica, sin restaurar la importación diferida retirada por el usuario.

Los errores comunes viven en core/schema/http.py y heredan del BaseModel del proyecto. JSONResponse serializa sus alias explícitos: correlationId coincide con X-Correlation-ID. El manejo común conserva WWW-Authenticate, Retry-After y Allow, y no devuelve input, SQL, trazas ni nombres de campos desconocidos. Las respuestas de éxito de credenciales aún se adaptarán en T37–T39; no se presentan como contrato 1.1 completo.

La función transaction(db) de core/db delimita una transacción en la sesión recibida, sin crear o cerrar otra sesión. Los DAOs coordinados deben usar commit=False. SQLAlchemy confirma al salir sin error y revierte ante excepción o cancelación; rechaza abrir otro begin sobre una sesión ya en transacción. Los casos de access actuales aún no usan este soporte: se adaptan después de C12.

Comprobación local: 25 pruebas unittest correctas con el Python de .venv, fuera del sandbox de Windows. Incluyen HTTP por ASGI sin servidor y transacciones sobre una sesión SQLAlchemy real sin conexión. Esto no acredita escrituras, integridad o concurrencia PostgreSQL; esas integraciones se vuelven a ejecutar al corregir los componentes en C13/C14. No se iniciaron servicios, ejecutaron migraciones ni instalaron dependencias en C12. La evidencia de build y del cierre figura en todo.md.

## Registro de T04–T06 (2026-10-24)

Las descripciones siguientes de main, lifespan e importación diferida son evidencia del código de aquella fecha. El usuario las sustituyó después por inyección de dependencias, Uvicorn directo y su fábrica actual; no restaurarlas para satisfacer pruebas.

`src.application:app` conserva la ruta de bienvenida y CORS existentes. Añade `/health/live` y `/health/ready`; `main()` inicia esa misma app mediante Uvicorn. El ciclo de vida libera el motor al cerrar, sin abrir conexiones SQL durante el import ni el arranque. Sin configuración de base no se importa el motor y preparación responde 503. Con configuración válida, preparación ejecuta `SELECT 1` con límite de tiempo y devuelve 200 o un 503 sin detalles internos. Esto aún no comprueba versión de esquema ni permisos de negocio.

Los ajustes conservan cadenas simples; contraseña y URI se omiten en repr y las validaciones ocultan los datos de entrada. Se valida configuración parcial, controlador, puerto y valores del pool. URL.create conserva contraseñas con caracteres especiales. Se retiran solo cinco imports de utilidades que apuntaban a nombres inexistentes. `core/db/session.py`, `deps.py` y `__init__.py` conservan sus huellas previas: fábrica compartida, exportaciones, zona America/Caracas y codec propios.

Comprobación actual: `./.venv/Scripts/python.exe -m unittest discover -s tests -v`, 12 pruebas correctas; `uv build --offline`, sdist y wheel construidos. La prueba de entrada contrasta pyproject.toml y comprueba que main llama a Uvicorn con src.application:app. El usuario pidió omitir la prueba HTTP separada del wheel y su solicitud de permiso; no se da por ejecutada. Las consultas y fallos de base usan sustitutos: no acreditan PostgreSQL real. No se instalaron dependencias ni se cambió uv.lock.

T05 comprobó servicios aislados sin Docker: PostgreSQL 18.3 en dos clústeres distintos y Keycloak 26.8.1 sobre Java 21.0.6. El flujo real S256 de tres usuarios ficticios pasó, con HTTPS local y certificado validado. Versiones, comandos y límites en el soporte local. No se atribuyen resultados a PostgreSQL 18.6 por figurar en la planificación.

En T06, la primera conexión real detectó await_ ausente en SQLAlchemy 2.1.6. Se corrigió solo esa llamada a run_async para instalar el codec existente; no se sustituyó el motor ni la fábrica. La huella conservada en T04 corresponde al momento de aquella comprobación, antes de este arreglo concreto.

Cierre C02: 12 pruebas unitarias y comprobación PostgreSQL correctas mediante uv run --locked; upgrade/downgrade/upgrade, fallo de revisión sin DDL/versión parcial, rol operativo sin DDL, rollback de un create del DAO con commit=False y dos escritores con espera observada. El check incluye preparación real y fecha con zona. uv build --offline correcto. Keycloak y ambos clústeres locales detenidos; no queda una base aleatoria de las comprobaciones. Todo esto acredita la base técnica, no autorización ni sync de producto.

## Registro histórico de T03

El resto de esta página conserva evidencia del 2026-10-21. Las descripciones de SecretStr, fábricas por aplicación, UTC y exportaciones retiradas pertenecen a aquel código; no describen el estado actual. Para continuar usa el estado de T04 de arriba y la tarea vigente.

**Fecha:** 2026-10-21. **Alcance comprobado:** T03. El usuario autorizó continuar tras corregir anotaciones. No hay tablas ni casos de negocio. El acuerdo de acceso T04 sigue en curso.

## Entorno y comandos

Python 3.15.1 y uv 0.13.4 en Windows. `.python-version` elige la familia 3.15; `requires-python` exige al menos 3.15.1. `uv.lock` fija las dependencias. No se acredita todavía otra plataforma ni CI.

Desde la raíz:

```powershell
uv sync --locked
uv run --locked nightingale-api
```

El comando inicia Uvicorn en `127.0.0.1:8000`. Para recarga durante desarrollo:

```powershell
uv run --locked uvicorn src.application:app --host 127.0.0.1 --reload
```

Controles:

```powershell
uv run --locked python -m unittest discover -s tests -v
uv build
git diff --check
```

Si PowerShell no encuentra `uv`, reinicia la terminal tras su instalación o usa `& "$env:USERPROFILE\.local\bin\uv.exe"`. En esta sesión se usó esa ruta. La caché y los temporales del aislamiento de Windows daban errores de permisos; para los controles se usó:

```powershell
New-Item -ItemType Directory -Force .uv-cache, .tmp | Out-Null
$env:UV_CACHE_DIR = Join-Path $PWD '.uv-cache'
$env:TMP = Join-Path $PWD '.tmp'
$env:TEMP = $env:TMP
```

Estas carpetas no se versionan. No hace falta cambiar el producto por ese límite del entorno.

## Configuración y salud

Puedes copiar `.env.example` a `.env`, sin versionar secretos. Las variables del proceso prevalecen sobre `.env`; después se usan los valores por defecto. `API_ENVIRONMENT` acepta `development`, `test` o `production`; el resto de la preparación de producción sigue pendiente.

Para PostgreSQL usa `SQLALCHEMY_DATABASE_URI` con el controlador `postgresql+asyncpg`, o `DB_HOST`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD` y `DB_PORT` (5432 por defecto). La URI prevalece sobre los campos separados. Contraseñas y URI usan `SecretStr`; se ocultan también los datos de entrada en errores de validación. La URL creada desde campos separados conserva caracteres especiales de la contraseña.

Sin conexión configurada, el proceso arranca sin motor ni sesiones y devuelve 503 en preparación. Una configuración parcial o inválida impide el arranque. Con URL válida, lifespan crea el motor y su fábrica de sesiones y libera el motor al cerrar. La creación no abre conexiones por sí sola. No se crean tablas ni se prueban credenciales al arrancar. Se usa UTC en las conexiones, sin un codec de fecha propio.

| Ruta | Qué prueba | Resultado |
|---|---|---|
| `GET /health/live` | El proceso responde | 200 |
| `GET /health/ready` | PostgreSQL configurado y capaz de ejecutar `SELECT 1` | 200; 503 si falta configuración o falla la consulta |

Preparación no acredita versión de esquema, permisos de negocio ni aislamiento. El tiempo de espera usa `pool_timeout`, que también acota la adquisición de conexión. Los valores del pool conservan los del código base (`pool_size=5`, `pool_timeout=30`, `pool_recycle=1800`, `pool_overflow=10`), ahora con validación. Son valores técnicos provisionales, no objetivos de rendimiento ni capacidad aprobados. No se habilita caché, storage, CORS ni reglas de producción de otro proyecto.

## Decisiones de biblioteca y fuentes oficiales

| Decisión | Versión detectada | Fuente usada |
|---|---|---|
| Recursos por lifespan y pruebas con contexto TestClient | FastAPI 0.159.1, Starlette 1.9.0 | [Lifespan](https://fastapi.tiangolo.com/advanced/events/#lifespan), [prueba de eventos](https://fastapi.tiangolo.com/advanced/testing-events/), [versión 0.159.1](https://fastapi.tiangolo.com/release-notes/#01591) |
| Motor async, sesión por uso y `await engine.dispose()`; extra asyncio obligatorio | SQLAlchemy 2.1.6, asyncpg 0.32.0, greenlet 3.5.6 | [API asíncrona 2.1](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html), [URL.create](https://docs.sqlalchemy.org/en/21/core/engines.html#sqlalchemy.engine.URL.create) |
| Validación al iniciar y prioridad entorno sobre dotenv | Pydantic 2.14.1, pydantic-settings 2.16.1 | [Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support) |
| Empaquetar `src` para que coincida con los imports y el comando instalado | uv/uv_build 0.13.4 | [Módulos](https://docs.astral.sh/uv/concepts/build-backend/#modules) |
| Arranque local mediante import string | Uvicorn 0.54.0 | [Arranque programático](https://uvicorn.dev/deployment/#running-programmatically), [configuración](https://uvicorn.dev/settings/#application) |

Se usaron las guías oficiales actuales para FastAPI/Pydantic/uv/Uvicorn y la guía 2.1 para SQLAlchemy; sus APIs se contrastaron con las versiones instaladas y pruebas. No se añadieron pytest, Ruff, caché o un proveedor de identidad. HTTPX 0.28.1 ya venía en el entorno y sirve al TestClient; unittest pertenece a Python.

## Evidencia y límites

- Instalación bloqueada/offline comprobada tras incorporar el extra asyncio; wheel y sdist construidos e inspeccionados. No contienen secretos, entorno virtual, caché ni temporales. Se verificó el punto de entrada `nightingale-api = src.application:main`.
- 10 pruebas de proceso/configuración correctas: prioridad de entorno, datos inválidos, secretos, salud, fallos y liberación de recursos. Los fallos de conexión usan sustitutos; no acreditan PostgreSQL real, integridad ni concurrencia.
- Prueba HTTP real con Uvicorn en un puerto local libre: vida 200, preparación 503 sin base. Se detuvo el proceso temporal. Las pruebas con sockets necesitaron salir del aislamiento de Windows porque este se bloqueaba antes de ejecutar la API.
- No se ha probado PostgreSQL real; su versión, entorno aislado e identidades de prueba siguen en O08 antes de T07. No hay migraciones, workers, negocio ni despliegue.
- El código base del usuario de DAO/modelos, utilidades, caché y storage no forma parte del arranque validado. Conserva referencias heredadas y requiere revisión antes de usarlo; esta tarea no lo da por aprobado. Los paquetes `core.db` y `settings` ya no importan sus adaptadores y configuración de forma global. No hay consumidores actuales de los antiguos exports; importar capacidades concretas desde sus módulos.

Se corrigieron las anotaciones de `lifespan` y `session` a `AsyncGenerator`, manteniendo AsyncIterator en la dependencia sin decorador. Se comprobaron los dos usos decorados mediante AST y pasaron las mismas 10 pruebas. No hay CLI de basedpyright instalada y no se acredita su ejecución. Python 3.15 documenta el requisito de función generadora asíncrona para [asynccontextmanager](https://docs.python.org/3.15/library/contextlib.html#contextlib.asynccontextmanager).

Trabajo actual: [T04, identidad/revocación y alcance del Hub](../access-design.md). OIDC y permisos vigentes al aceptar están confirmados; las demás decisiones no se infieren de la autorización para continuar.
