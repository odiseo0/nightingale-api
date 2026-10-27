# Servicios locales de prueba

Solo datos ficticios. Estos comandos no usan Docker, no registran servicios de Windows y no acceden al PostgreSQL personal. Los datos y descargas viven en `.tmp/test-services/`, que Git ignora. No borres una carpeta de datos mientras su proceso siga activo.

## Descarga, snapshot y retención · C10

Con los servicios Test existentes, desde la raíz:

```powershell
.\.venv\Scripts\python.exe test-support/downloads/check.py
.\.venv\Scripts\python.exe test-support/retention/check.py
```

Ambos reutilizan la preparación de sync, comprueban la ruta del clúster, aplican head 20261027_06 en bases aleatorias y las eliminan al terminar. Head actual: 27 tablas y btree_gist. Descarga prueba grupos completos, audiencia, firma/alcance, retiradas, escritor concurrente y captura/base coherentes; snapshot prueba inmutabilidad, páginas, zona, época, vencimiento y rollback. Retención prepara resultados ficticios con reloj controlado, comprueba lotes de 500 resultados/100 grupos, frontera-1, recibo mínimo y recuperación sin repetir efectos. La clave HMAC de cada probe existe solo en su proceso.

C10 ejecutó estos dos probes y los nueve existentes en secuencia. No inicia ni detiene servicios. Las conexiones separadas y ASGI no acreditan dos procesos de API, SSE o consumidores; eso sigue en T31–T33. No se ejecuta HTTP separado del wheel. Evidencia y límites en [T30/C10](../tasks/P-20261024-01-desktop-shared-api/todo.md#t30-recuperar-tras-vencimiento).

## PostgreSQL

Herramientas locales comprobadas: PostgreSQL **18.3**, en `C:\Program Files\PostgreSQL\18\bin`. La referencia 18.6 del plan no describe la versión instalada. El soporte usa la familia 18 y no actualiza la instalación del usuario.

Desde la raíz, abre el perfil que necesites:

```powershell
.\test-support\postgres.ps1 -Action Start -Mode Test
.\test-support\postgres.ps1 -Action Stop -Mode Test
```

`-Mode Development` usa otra carpeta y otro puerto. `-PostgresBin` permite indicar la ruta de herramientas de PostgreSQL 18. Cada inicio nuevo crea su propio clúster si falta. Si ya existe un marcador de proceso, el comando se detiene; no intenta reutilizar ni detener otro clúster.

| Perfil | Puerto, solo 127.0.0.1 | Carpeta |
|---|---|---|
| Test | 55433 | .tmp/test-services/postgres-test/data |
| Development | 55432 | .tmp/test-services/postgres-development/data |

Usuario inicial: `nightingale_fixture`; base inicial: `postgres`; contraseña ficticia pública: `Fixture-postgres-only-2026!`. Sirve para preparar el entorno aislado. **No es el usuario operativo de API**: T06 separará la identidad de migraciones y la de ejecución antes de añadir persistencia de producto.

Comprobación sin usar archivos de inicio de psql:

```powershell
$env:PGPASSWORD = 'Fixture-postgres-only-2026!'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -X -w -h 127.0.0.1 -p 55433 `
    -U nightingale_fixture -d postgres -v ON_ERROR_STOP=1 `
    -c "SELECT current_setting('server_version'), current_user, inet_server_addr(), inet_server_port();"
Remove-Item Env:PGPASSWORD
```

No se consulta ni se migra ninguna base de 5432. Los perfiles persisten al detenerlos; no son una limpieza automática de datos entre pruebas.

## Keycloak

Proveedor fijado: **26.8.1**, distribución ZIP oficial. Java local comprobado: Corretto **21.0.6**. El modo de desarrollo y las claves ficticias pertenecen solo a loopback. Usa HTTPS local: Keycloak marca sus cookies Secure y HTTPX no las envía por HTTP. No trasladar este realm a un servidor público.

Descarga en la carpeta temporal y compara la suma oficial antes de extraer:

```powershell
$release = 'https://github.com/keycloak/keycloak/releases/download/26.8.1'
$archive = Join-Path $PWD '.tmp/test-services/keycloak-26.8.1.zip'
New-Item -ItemType Directory -Force (Split-Path $archive) | Out-Null
Invoke-WebRequest "$release/keycloak-26.8.1.zip" -OutFile $archive
$checksum = (Invoke-WebRequest "$release/keycloak-26.8.1.zip.sha1").Content.Trim().Split(' ')[0]
if ((Get-FileHash $archive -Algorithm SHA1).Hash -ne $checksum) { throw 'Keycloak checksum mismatch' }
Expand-Archive -LiteralPath $archive -DestinationPath '.tmp/test-services/keycloak-test'
$keycloak = Join-Path $PWD '.tmp/test-services/keycloak-test/keycloak-26.8.1'
New-Item -ItemType Directory -Force "$keycloak/data/import" | Out-Null
Copy-Item -LiteralPath 'test-support/oidc/realm.json' -Destination "$keycloak/data/import/nightingale-test-realm.json"
$keytool = 'C:\Program Files\Amazon Corretto\jdk21.0.6_7\bin\keytool.exe'
& $keytool -genkeypair -alias fixture -keyalg RSA -keysize 2048 -validity 30 `
    -dname 'CN=localhost' -ext 'SAN=ip:127.0.0.1,dns:localhost' `
    -keystore "$keycloak/conf/fixture.p12" -storetype PKCS12 `
    -storepass 'Fixture-only-2026!' -keypass 'Fixture-only-2026!' -noprompt
& $keytool -exportcert -rfc -alias fixture -keystore "$keycloak/conf/fixture.p12" `
    -storepass 'Fixture-only-2026!' -file "$keycloak/conf/fixture.pem"
$env:KC_HTTPS_KEY_STORE_PASSWORD = 'Fixture-only-2026!'
& "$keycloak/bin/kc.bat" start-dev --http-host=127.0.0.1 --http-enabled=false `
    --https-port=18443 --https-key-store-file="$keycloak/conf/fixture.p12" --import-realm
```

El último comando ocupa la terminal. Ctrl+C detiene ese proceso. En esta versión start-dev también abrió HTTP en 8080 pese a http-enabled=false; el host quedó en loopback. La comprobación usa solo HTTPS 18443. No se presenta start-dev como una configuración de producción.

El certificado dura 30 días; genera otro al vencer, con el proveedor detenido y una ruta nueva, y actualiza el PEM del cliente. No instales su confianza en Windows: el script carga solo ese PEM en su contexto TLS. No desactives la validación de certificados.

Para desarrollo, extrae otra copia en `keycloak-development` y usa 18444, con su propio certificado; no compartas la carpeta de datos del proveedor entre procesos. El script comprueba solo el perfil Test, cuyo emisor es `https://127.0.0.1:18443/realms/nightingale-test`. Ningún cliente de escritorio real tiene que usar el puerto de retorno de esta prueba.

El realm contiene tres sujetos ficticios: `fixture-owner`, `fixture-assistant` y `fixture-outsider`. La clave pública de prueba está en realm.json. Esos nombres no conceden roles en la API: los permisos pertenecen a PostgreSQL y a los casos posteriores de acceso.

El cliente público `nightingale-desktop-test` exige Authorization Code con PKCE S256, sin secreto. Solo admite el retorno `http://127.0.0.1:18765/callback`; desactiva implicit y password grants. El access token incluye audiencia `nightingale-api`; el ID token no sustituye esa credencial. El proveedor conserva sus sesiones OIDC; esto no añade sesiones ni renovación a nuestra API.

Con el proveedor de prueba activo:

```powershell
.\.venv\Scripts\python.exe test-support/oidc/check.py
```

La comprobación usa HTTPX del entorno existente. Recorre login y canje S256 para los tres sujetos; contrasta emisor/audiencia y rechaza código repetido, verifier incorrecto, ausencia de PKCE y password grant. No inicia un navegador ni necesita un listener de retorno: captura la redirección sin seguirla. No imprime ni guarda tokens. La lectura de claims de ese probe **no valida firmas**; el adaptador de producto sí las valida y se comprueba mediante los probes de acceso y cuentas.

## Migraciones y transacciones

Alembic **1.20.1** registra la historia del esquema; incorpora Mako **1.4.3** como dependencia propia. uv.lock conserva las demás versiones. El motor de migraciones es local al comando y usa `ALEMBIC_DATABASE_URI`; nunca toma la identidad operativa del motor compartido de la API.

La revisión `20261024_01` crea el espacio `nightingale`, limita el acceso a `public` y concede solo uso del espacio al grupo SQL `nightingale_runtime`. La identidad de migraciones posee el esquema y `public.alembic_version`. La identidad de API pertenece al grupo de ejecución y no puede crear tablas, asumir el rol de migraciones ni cambiar su historia. Cada futura migración concederá los permisos de tabla que necesite su caso; no hay permiso de escritura general sobre tablas futuras.

Las tablas de identidad/cuenta y sus modelos se añaden con sus casos T08/T09. Esta base no crea las 27 tablas por adelantado ni importa todos los modelos en Alembic. No hay autogeneración ni plantilla vacía de revisiones; las revisiones actuales se escriben y revisan como Python/SQL. Para generar solo SQL, sin conectar:

```powershell
uv run --locked alembic upgrade head --sql
```

Para una base aislada que ya tenga sus roles preparados, `ALEMBIC_DATABASE_URI` debe indicar su identidad de migraciones. No guardes la URI en alembic.ini ni reutilices para ella `SQLALCHEMY_DATABASE_URI`, que pertenece a la API. Aplicar la revisión requiere que exista el grupo `nightingale_runtime`; la preparación administrativa queda fuera del arranque HTTP.

Con el perfil PostgreSQL Test activo:

```powershell
.\.venv\Scripts\python.exe test-support/persistence/check.py
```

El script comprueba la ruta real del clúster antes de crear nada. Prepara tres roles ficticios sin privilegios de administración: `nightingale_runtime` sin login, `nightingale_migrator` y `nightingale_app` con login. Usa claves públicas de prueba; nunca las traslada a desarrollo real. Crea una base con nombre aleatorio `nightingale_test_...`, prueba y la elimina al terminar. Las carpetas temporales de la revisión fallida permanecen dentro de .tmp y se limpian al salir. Los roles ficticios permanecen en el clúster de prueba.

La comprobación cubre upgrade/downgrade/upgrade desde vacío; fallo real a mitad de otra revisión con rollback de DDL y versión; permisos SQL de ejecución; rollback de dos escrituras; dos sesiones independientes sobre la misma fila y bloqueo observado mediante pg_blocking_pids antes de liberar al primer escritor. Usa la fábrica de sesiones del usuario y comprueba también preparación contra PostgreSQL real, zona y codec de fecha.

La única corrección de T06 en `core/db/session.py` cambia await_ por run_async, método público compatible con SQLAlchemy 2.1.6. El fallo AttributeError apareció al abrir la primera conexión real. Se conservaron motor, fábrica, zona y codec. C12 añadió la exportación de transaction; las correcciones posteriores conservan la fábrica y deps.py.

El DAO existente conserva commit=True por defecto. Los casos de aplicación delimitan `async with transaction(db)` y llaman al DAO con `commit=False`; el soporte de core/db usa begin sobre esa misma sesión. La prueba provoca un fallo después de un create y comprueba que no queda su fila. No se modifica el DAO base ni se habilitan las rutas heredadas de users.

Esto prueba la base técnica con filas ficticias. No demuestra todavía autorización, coordinación de permisos de varias cuentas, orden confirmado del Change Log, idempotencia ni dos procesos de API: corresponden a los casos siguientes y a T32. Los comandos de migración se ejecutan desde este repositorio; no se acredita distribuir ni ejecutar migraciones desde un wheel instalado.

## Citas y cierre C09 · 2026-10-27

El head histórico de C09 fue 20261027_04: 25 tablas y btree_gist en el esquema dedicado. El probe de persistencia ahora aplica, revierte y reaplica el head actual indicado en C10; no usa una base personal ni instala una extensión fuera de la base ficticia. Los ocho probes del bloque siguiente siguen disponibles y C09 añadió:

```powershell
.\.venv\Scripts\python.exe test-support/appointments/check.py
```

Comprueba creación con documento declarado, menor con responsable, versión/duplicado, confirmación, reprogramación, cancelación, asistencia y ausencia con reloj controlado. Prueba ocupación global con citas reales, espera y exclusión entre dos cuentas, carrera reserva/bloqueo, cambios de agenda incompatibles y rollback entre cita/historia. Intenta huecos, historia futura, cambio de snapshots y reescritura/borrado SQL. La segunda cuenta clinic es solo fixture; sus rutas HTTP siguen fuera de alcance. No se guardan tokens ni datos reales.

Los nueve probes se ejecutaron en orden con PostgreSQL Test y Keycloak Test existentes. Cada uno valida el clúster y elimina su base aleatoria. Suite/build/analizador y límites en [T27/C09](../tasks/P-20261024-01-desktop-shared-api/todo.md#t27-proteger-historia-funcional). No hay HTTP separado del wheel. T32 conserva pruebas de dos procesos/SSE y consumidores.

## Registro histórico de acceso, cuentas, equipo, pacientes, servicios y agenda para C06

Con PostgreSQL Test y Keycloak Test ya activos:

```powershell
.\.venv\Scripts\python.exe test-support/access/check.py
.\.venv\Scripts\python.exe test-support/accounts/check.py
.\.venv\Scripts\python.exe test-support/sync/check.py
.\.venv\Scripts\python.exe test-support/team/check.py
.\.venv\Scripts\python.exe test-support/patients/check.py
.\.venv\Scripts\python.exe test-support/services/check.py
.\.venv\Scripts\python.exe test-support/schedule/check.py
.\.venv\Scripts\python.exe test-support/persistence/check.py
```

Los ocho probes aplican el head 20261026_08 en bases aleatorias distintas: 21 tablas, incluidas las cinco de pacientes/contactos y las tres de catálogo/ofertas/reglas. Acceso comprueba credenciales y auditoría; cuentas prueba alta/lecturas/script; sync conserva idempotencia/rollback; equipo prueba invitaciones, pertenencias y dispositivos; pacientes prueba sus recorridos y completitud. Todos validan el clúster y eliminan solo su base. Persistencia comprueba upgrade/downgrade/reaplicación y fallo de revisión sin DDL parcial.

Cuentas comprueba alta administrativa atómica, rechazo al rol operativo, duplicado concurrente, rollback real tras fallo CHECK en el head, aislamiento por pertenencia, cuenta inactiva, dispositivos no registrados/revocados y paginación con total autorizado. También retiene un head en una sesión mientras otra conexión cambia la época y comprueba su refresco. Ejecuta el script de alta en un proceso hijo: éxito, duplicado, rol operativo denegado, zona inválida y fallos de conexión sin secretos. Usa OIDC real para identificar a los actores; no guarda ni imprime tokens. Las pertenencias y autorizaciones de dispositivo se preparan como fixtures SQL explícitos; no acreditan las futuras operaciones de invitación/registro.

Sync comprueba autorización vigente, versiones, huella canónica y rechazo seguro, recibos por actor/cuenta, duplicado concurrente, respuesta perdida tras commit en ASGI, rollback inmediato/diferido y reintento. Comprueba lotes con fallo temporal, dependencia temporal e independiente; espera un bloqueo PostgreSQL real antes de releer la revocación. Prepara un recibo ficticio antiguo para probar 410 y conservación de clave/huella tras purgar detalles; no cambia el reloj del servicio. Sus pertenencias son fixtures. Equipo usa la aceptación real de invitación y comprueba que no registra una instalación por deducción; también prueba la consulta de auditoría y su correlación, el fallo de auditoría que revierte una rotación y el mantenimiento administrativo repetible.

La zona se contrasta con pg_timezone_names en el DAO antes de escribir; coincide con la restricción del esquema. No requiere instalar tzdata en Python. La migración nueva se aplica solo en bases ficticias; no se aplica nada en una base personal. Los scripts no inician ni detienen servicios por su cuenta.

Pacientes comprueba borradores/documentos, versiones y búsqueda por cuenta, contactos compartidos, FK de cuenta, conservación de constancias y completitud con documentos declarados. Dos conexiones reales intentan retirar los dos teléfonos responsables: solo una confirma. El caso compartido de elegibilidad se prueba en la fecha local de una futura cita, sin afirmar que las rutas de citas estén implementadas. El head de C05 tenía 18 tablas; las tres migraciones de C06 lo llevan a 20261026_08 con 21.

Servicios comprueba catálogo privado, propiedad, duraciones estrictas, versiones/duplicados concurrentes, ofertas, FK de propietario y ajuste nulo. Una segunda cuenta clinic existe solo como fixture SQL: demuestra oferta independiente y proyección sin habilitar su gestión HTTP. Un fallo diferido de su grupo revierte el cambio de catálogo y los recibos/grupos de ambas cuentas. La consulta de resultado y su duplicado vuelven a validar vínculo y cuenta.

Agenda comprueba jornada partida, unión de tramos, fin 1440, vigencia, fecha local en Caracas, paginación, NULLS NOT DISTINCT y dos creaciones concurrentes del mismo intervalo abierto. Observa con pg_blocking_pids que la operación espera al profesional antes de editar. Prueba un cambio incompatible con intervalos requeridos ficticios, sin tabla de reservas. T22/T32 conservan aportar ocupación real y probar su carrera; T21 conserva disponibilidad completa y resolución de horas locales ambiguas.

## Alta administrativa

El mantenimiento reutiliza `scripts/purge_expired_results.py`, sin subcomandos. Exige `MAINTENANCE_DATABASE_URI` administrativa explícita y no toma la URI de ejecución como sustituto. Cada ejecución retira hasta 500 resultados completos, 100 grupos consecutivos de una cuenta con al menos 90 días y 100 capturas vencidas. Conserva recibos mínimos, historia funcional y auditoría; avanza la frontera junto al borrado de grupos. Devuelve purgedResults para conservar la salida anterior; ese número solo cuenta resultados, no grupos ni capturas. Se puede repetir para procesar los lotes restantes. Debe ejecutarse con este repositorio en PYTHONPATH, igual que el alta. No lo ejecuta el servidor ni un proceso periódico de esta entrega.

Desde la raíz, prepara un JSON local con el esquema BootstrapPracticeInput de accounts. Ejemplo solo con datos ficticios:

```json
{
  "ownerIssuer": "https://identity.example.test/realms/nightingale",
  "ownerSubject": "fixture-owner",
  "ownerName": "Persona de prueba",
  "professionalName": "Profesional de prueba",
  "displayName": "Consulta de prueba",
  "timeZone": "America/Caracas",
  "locationName": "Sede de prueba",
  "locationAddress": "Dirección ficticia",
  "locationCountry": "VE",
  "locationState": "Lara",
  "locationCity": "Barquisimeto"
}
```

El operador debe obtener issuer/subject de una fuente de identidad de confianza y conservarlos exactos. Configura OIDC_ISSUER con el mismo emisor. Proporciona BOOTSTRAP_DATABASE_URI en el entorno del proceso, con el rol administrativo y el controlador postgresql+asyncpg; no usa la conexión operativa como alternativa. No guardes esa credencial en el JSON ni en archivos versionados. Ejecuta:

```powershell
uv run --locked python -m scripts.create_practice --file .tmp/practice.json
```

El script valida la entrada y llama a bootstrap_practice. Usa la fábrica existente con la conexión administrativa solo dentro de su proceso; no cambia el servidor ni sus archivos. Devuelve código 0 y JSON camelCase con identificadores, o código 2 y un error breve en stderr. Si no puede confirmar el resultado, consulta el estado antes de repetir. No ejecuta migraciones, no emite credenciales y no forma parte del arranque del API.

## Fuentes

- [PostgreSQL 18: initdb](https://www.postgresql.org/docs/18/app-initdb.html) y [pg_ctl](https://www.postgresql.org/docs/18/app-pg-ctl.html).
- [Descarga Keycloak](https://www.keycloak.org/downloads), [importación de realm](https://www.keycloak.org/server/importExport#_importing_a_realm_during_startup) y [clientes OIDC/PKCE](https://www.keycloak.org/docs/latest/server_admin/index.html#_oidc_clients).
- [TLS de Keycloak](https://www.keycloak.org/server/enabletls) y [keytool de Java 21](https://docs.oracle.com/en/java/javase/21/docs/specs/man/keytool.html).
- [HTTPX: redirecciones](https://www.python-httpx.org/quickstart/#redirection-and-history), [variables de entorno](https://www.python-httpx.org/environment_variables/) y [contexto TLS](https://www.python-httpx.org/advanced/ssl/#configuring-client-instances), para HTTPX 0.28.1 ya resuelto en el entorno.
- [Alembic 1.20.1: uso async](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic) y [tabla de versiones](https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.environment.EnvironmentContext.configure.params.version_table_schema).
- [SQLAlchemy 2.1: run_async en eventos](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html#using-awaitable-only-driver-methods-in-connection-pool-and-other-events) y [transacciones/savepoints](https://docs.sqlalchemy.org/en/21/orm/session_transaction.html#using-savepoint).
- [PostgreSQL 18: esquema](https://www.postgresql.org/docs/18/sql-createschema.html) y [pg_blocking_pids](https://www.postgresql.org/docs/18/functions-info.html#FUNCTIONS-INFO-SESSION); [Python 3.15: TaskGroup](https://docs.python.org/3.15/library/asyncio-task.html#task-groups).

La evidencia ejecutada y los límites vigentes se registran en [T05](../tasks/P-20261024-01-desktop-shared-api/todo.md), sin dar estos comandos por comprobados solo por escribirlos.
