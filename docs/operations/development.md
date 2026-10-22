# Desarrollo de la base de proceso

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
