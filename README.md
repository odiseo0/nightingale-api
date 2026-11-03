# Nightingale API

API de autorización, aceptación del estado compartido y sincronización de Nightingale. Python y FastAPI; PostgreSQL operativo privado. Este repositorio también tendrá los módulos y workers de recordatorios, entregas, integración con n8n e indicadores básicos.

El escritorio guarda su trabajo con Rust/SQLite sin esperar a esta API. Patient Hub tiene su web, backend y datos propios; usa esta API para consultar y cambiar citas autorizadas. Ninguno recibe acceso SQL al PostgreSQL operativo.

## Documentos

| Documento | Función |
|---|---|
| [Especificación](docs/nightingale-api.md) | Fuente del alcance y los límites confirmados |
| [Reglas de trabajo](AGENTS.md) | Guía común para colaboradores y agentes |
| [Desarrollo y evidencia](docs/operations/development.md) | Corrección actual y registros de comprobaciones previas |
| [Soporte local de pruebas](test-support/README.md) | PostgreSQL y Keycloak sin Docker; OIDC, migraciones y transacciones con datos ficticios |
| [Arquitectura](docs/architecture.md) | Componentes, datos, dependencias y flujos propuestos |
| [Contratos](docs/contracts.md) | Propiedad, criterios de diseño y acuerdos por cerrar |
| [Contrato de diseño HTTP v1](docs/api-v1.md) | Rutas, operaciones, modelos públicos, permisos y recuperación de esta etapa |
| [Artefactos de contrato](contracts/README.md) | OpenAPI/JSON Schema generados desde código, origen y huellas |
| [Referencia para el escritorio](contracts/api-v1/nightingale-api.md) | Documento portable para nightingale: estado, decisiones, datos, endpoints y flujos, junto a los contratos |
| [Guía para Rust](docs/rust-api-guide.md) | Acceso, lotes, conflictos, SSE, cursores y recuperación; consumidor pendiente |
| [Esquema físico de diseño](docs/database-schema.md) | Única fuente del modelo; implementación parcial en migraciones y pruebas aisladas |
| [Calidad y pruebas](docs/quality.md) | Requisitos verificables y pruebas futuras |
| [Decisiones](docs/decisions.md) | Qué está confirmado, propuesto o pendiente |
| [Diseño de acceso](docs/access-design.md) | OIDC de emisión y token API sin vencimiento/revocable; Hub posterior aún en revisión |
| [Fuentes y revisión](docs/sources.md) | Referencias, diferencias y comprobaciones documentales |
| [Plan sucesor aprobado](tasks/P-20261024-01-desktop-shared-api/plan.md) | Tareas, dependencias y checkpoints de API para escritorio |


## Entorno local de desarrollo

Sin Docker; todos los servicios quedan en loopback y las claves son ficticias públicas de prueba. Secuencia comprobada en Windows 11 con PowerShell; las variantes de Linux son los comandos equivalentes sobre la instalación local de cada herramienta (psql y pg_ctl suelen estar ya en el PATH del paquete del sistema; keytool viene con el JDK).

Requisitos: `uv`, Python 3.15, PostgreSQL 18 y Java 21. La copia local de Keycloak 26.8.1 vive en `.tmp/test-services/keycloak-test`; si falta, sigue la descarga y el certificado de [test-support/README.md](test-support/README.md).

### 1. Dependencias

```powershell
uv sync --locked
```

`uv run` usa `.venv` sin activarlo. `--locked` conserva las versiones de `uv.lock`.

### 2. Base de datos: elige una opción

**Opción A — clúster aislado del proyecto (Windows).** El script mantiene este perfil separado del servicio habitual de PostgreSQL en 5432; los datos permanecen al detenerlo:

```powershell
.\test-support\postgres.ps1 -Action Start -Mode Development
```

Queda en `127.0.0.1:55432`, usuario inicial `nightingale_fixture`. En Linux no hay equivalente del script: usa la opción B o crea tu propio clúster con `initdb`/`pg_ctl` de PostgreSQL 18.

**Opción B — servicio PostgreSQL propio ya abierto.** Usa tu servicio habitual (el de Windows en 5432, o el servicio del sistema en Linux) en vez del clúster aislado. No ejecutes `postgres.ps1` ni uses `.tmp`. Conéctate con un rol administrativo del servicio (en Windows, el superusuario del instalador; en Linux, normalmente `sudo -u postgres psql`) y ejecuta el mismo bloque de preparación del paso 3, adaptando nombres de base, puerto y claves a tu servicio. Ten en cuenta:

- Los roles son del clúster, no de la base. Si `already exists` aparece, reutilízalos; no borres nada.
- Las claves públicas de prueba solo sirven en loopback. En un servicio compartido elige claves propias.
- Refleja los cambios en las URIs de los pasos 4 y 5. El controlador es siempre `postgresql+asyncpg`.

### 3. Preparar roles y base (una vez)

Con la opción A (PowerShell):

```powershell
$env:PGPASSWORD = 'Fixture-postgres-only-2026!'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' `
    -X -w -h 127.0.0.1 -p 55432 `
    -U nightingale_fixture -d postgres
```

Con la opción B en Linux:

```bash
sudo -u postgres psql -X -d postgres
```

Dentro de psql, el mismo bloque (ajusta `-p 55432` a tu puerto en la opción B):

```sql
\set ON_ERROR_STOP on

CREATE ROLE nightingale_runtime NOLOGIN;

CREATE ROLE nightingale_migrator
    LOGIN PASSWORD 'Fixture-migrator-2026!';

CREATE ROLE nightingale_app
    LOGIN PASSWORD 'Fixture-app-2026!'
    IN ROLE nightingale_runtime;

CREATE DATABASE nightingale_local OWNER nightingale_migrator;

REVOKE ALL ON DATABASE nightingale_local FROM PUBLIC;
GRANT CONNECT ON DATABASE nightingale_local TO nightingale_runtime;

ALTER DATABASE nightingale_local
    SET search_path = nightingale, public;
```

La separación sigue el uso de roles y propietario de PostgreSQL: `nightingale_migrator` crea el esquema y las tablas; `nightingale_app` solo ejecuta. Sal con `\q`. En PowerShell, limpia la variable: `Remove-Item Env:PGPASSWORD`.

### 4. Migraciones

La API no migra al arrancar; repite este paso cuando el proyecto añada revisiones:

```powershell
$env:ALEMBIC_DATABASE_URI = 'postgresql+asyncpg://nightingale_migrator:Fixture-migrator-2026!@127.0.0.1:55432/nightingale_local'

uv run --locked alembic upgrade head
uv run --locked alembic current

Remove-Item Env:ALEMBIC_DATABASE_URI
```

En Linux usa `export ALEMBIC_DATABASE_URI='...'`. `alembic current` debe mostrar `20261028_01 (head)` con el código actual.

### 5. Configurar `.env`

`.env.example` documenta las variables. Añade o ajusta estas en tu `.env`, una línea por variable:

```dotenv
API_ENVIRONMENT=development
SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://nightingale_app:Fixture-app-2026!@127.0.0.1:55432/nightingale_local
OIDC_ISSUER=https://127.0.0.1:18443/realms/nightingale-test
OIDC_JWKS_URI=https://127.0.0.1:18443/realms/nightingale-test/protocol/openid-connect/certs
OIDC_TLS_CA_FILE=.tmp/test-services/keycloak-test/keycloak-26.8.1/conf/fixture.pem
OIDC_PUBLIC_CLIENT_ID=nightingale-desktop-test
OIDC_AUDIENCE=nightingale-api
```

En la opción B, ajusta `SQLALCHEMY_DATABASE_URI` a tu host, puerto, base y claves. Genera la clave de firma de cursores y consérvala entre arranques:

```powershell
uv run --locked python -c "import secrets; print(secrets.token_hex(32))"
# API_SYNC_SIGNING_KEY=<resultado>
```

### 6. Keycloak

Deja esta terminal abierta. En Windows:

```powershell
$keycloak = (Resolve-Path '.tmp/test-services/keycloak-test/keycloak-26.8.1').Path
$env:KC_HTTPS_KEY_STORE_PASSWORD = 'Fixture-only-2026!'
& "$keycloak/bin/kc.bat" start-dev `
    --http-host=127.0.0.1 `
    --http-enabled=false `
    --https-port=18443 `
    --https-key-store-file="$keycloak/conf/fixture.p12" `
    --import-realm
```

En Linux es el mismo comando con `bin/kc.sh` (hazlo ejecutable con `chmod +x`); `keytool` y la renovación del certificado siguen [test-support/README.md](test-support/README.md). Ctrl+C detiene el proceso. Si la copia de `.tmp` no existe en tu máquina, descarga el ZIP oficial, verifica la suma y extrae con `unzip` en esa ruta.

### 7. API

En otra terminal, desde la raíz:

```powershell
uv run --locked uvicorn src.application:app `
    --host 127.0.0.1 `
    --port 8000 `
    --reload
```

`--reload` reinicia la API al cambiar el código. Deja la terminal abierta.

### 8. Comprobar el arranque

| Enlace | Qué debes ver |
|---|---|
| http://127.0.0.1:8000/ | Mensaje de bienvenida |
| http://127.0.0.1:8000/health/live | `"status": "alive"` |
| http://127.0.0.1:8000/health/ready | `"status": "ready"` |
| http://127.0.0.1:8000/docs | Lista de rutas |
| http://127.0.0.1:8000/v1/auth/config | Configuración pública de Keycloak |

En `ready`, el código actual también comprueba el canal de avisos de PostgreSQL; puede tardar unos segundos en quedar listo.

### 9. Cuenta de desarrollador y datos de prueba

El realm `nightingale-test` incluye tres sujetos ficticios, todos con la clave `Fixture-only-2026!`:

| Usuario | Uso |
|---|---|
| `fixture-owner` | Propietario de la consulta de prueba |
| `fixture-assistant` | Miembro de equipo con permisos limitados |
| `fixture-outsider` | Sin pertenencia; sirve para probar rechazos |

No son cuentas de administración de Keycloak, y tener un usuario allí no concede acceso a una cuenta de la API. No hay seeders que poblen pacientes en una base de desarrollo: los probes de `test-support/` crean bases temporales y las eliminan al terminar. Para datos persistentes, el flujo es:

1. Crear la consulta con [scripts/create_practice.py](scripts/create_practice.py), usando el subject real que Keycloak asigna al usuario (puede diferir de su nombre).
2. Obtener un token de dispositivo y registrar el dispositivo en la cuenta (`POST /v1/auth/device-tokens`).
3. Crear los pacientes mediante las operaciones de la API.

El alta administrativa detallada y su JSON de entrada están en [test-support/README.md](test-support/README.md).

### 10. Detener los servicios

Pulsa Ctrl+C en la terminal de la API y en la de Keycloak. Después, solo con la opción A:

```powershell
.\test-support\postgres.ps1 -Action Stop -Mode Development
```

En los próximos arranques solo inicia PostgreSQL, Keycloak y la API; la base, los roles y el `.env` quedan guardados.
