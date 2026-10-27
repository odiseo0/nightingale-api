# Desarrollo de la base de proceso

## T55–T57 comprobadas para revisión C06 · 2026-10-26

Las lecturas HTTP de catálogo, ofertas y reglas devuelven dicts con campos explícitos y response_model en sus rutas. Recibos y journal conservan validación y serialización antes del commit; una proyección inválida en la segunda cuenta revierte toda la operación y permite reintentar. Los modelos de propuesta, intervalos y referencia interna se conservan.

112 pruebas correctas en 52.924 s, ocho probes PostgreSQL/Keycloak reales, migraciones up/down/reaplicación, build offline e inspección del paquete correctos. OpenAPI completo y 72 esquemas JSON conservados; 48 huellas previas siguen iguales. Wheel de 152 entradas y 97 fuentes idénticas al árbol actual, sin archivos privados. Servicios existentes conservados.

El analizador de Zed mantiene 16 errores documentados, seis por el soporte de sentinel y diez de código previo; no se afirma una comprobación estática global correcta. El [cierre T57](../../tasks/P-20261024-01-desktop-shared-api/todo.md#t57-cerrar-la-corrección-y-ajustar-la-evidencia-de-c06) conserva evidencia, fuentes y límites. Las reservas reales siguen pendientes de T22/T32. C06 espera aceptación expresa; T19 no se inicia. Los apartados siguientes conservan evidencia histórica.

## T52–T54 para revisión C18 · 2026-10-26

Cada operación valida una vez su payload y usa el mismo modelo para la huella y el caso. Se retiran los seis normalizadores; las validaciones que combinan estado guardado y patch se conservan. Las 48 huellas previas siguen iguales. PostgreSQL comprueba una validación por petición real, recibo con huella previa, duplicado con defaults equivalentes, conflicto al cambiar contenido y ausencia de payload en el recibo.

112 pruebas, ocho probes reales, 72 esquemas JSON, build offline y wheel de 152 entradas comprobados. El analizador mantiene 16 errores: seis se relacionan con el soporte de sentinel y diez con código previo; no se ocultan ni se declara un cierre estático global. El [registro de C18](../../tasks/P-20261024-01-desktop-shared-api/todo.md#t52--t53--t54--2026-10-26--c18-para-revisión) detalla cambios, fuentes y límites. Registro histórico: C18 recibió después aceptación expresa; T55–T57 continúan hasta revisión C06. C06 sigue sin aceptar y T19 no se inicia. Los registros siguientes conservan sus resultados históricos.

## T49–T51 para revisión C17 · 2026-10-26

Tras la autorización de continuar en C16, se completan firmas de validadores/serializadores de pacientes, servicios y agenda, y de los DAOs/casos de acceso afectados. Se conservan 72 esquemas JSON, formatos de fecha, null y ausencia. Filas y pares de ORM usan los tipos variádicos de SQLAlchemy 2.1.6; se mantienen consultas, locks, transacciones y permisos.

110 pruebas correctas, ocho probes reales correctos y build offline con wheel de 152 entradas revisado. basedpyright conserva 28 errores globales y no señala ninguno de los doce archivos de producto de este bloque; los alias de sentinel siguen sin soporte. El [registro de C17](../../tasks/P-20261024-01-desktop-shared-api/todo.md#t49--t50--t51--2026-10-26--c17-para-revisión) distingue evidencia y límites. C17 y C06 siguen sin aceptar; detenerse antes de T52/T19. Los registros siguientes conservan sus resultados históricos.

## T46–T48 para revisión C16 · 2026-10-26

El usuario aprueba la corrección de C06 y pide conservar sentinel de Python 3.15 tras comprobar el límite de basedpyright 1.40.2 de Zed. Empty/Undefined son valores únicos con alias de tipo coherentes; el DAO admite claves int/UUID. Invitaciones comprueban error, tipo de estado y resultado original antes de responder; un duplicado rechazado conserva su rechazo. Los validadores y serializadores compartidos declaran tipos, con fechas, null, ausencia y esquemas JSON conservados. Evidencia, comando del analizador y fuentes en [T46–T48/C16](../../tasks/P-20261024-01-desktop-shared-api/todo.md#t46--t47--t48--2026-10-26--c16-para-revisión-con-límite-estático).

Comprobación nueva: 110 pruebas correctas, ocho probes PostgreSQL/Keycloak correctos, seis esquemas JSON contrastados, build offline y wheel de 152 entradas revisado. El análisis estático conserva 40 errores, incluidos dos en los alias de sentinel por falta de soporte; no se ocultan ni se declara un cierre estático correcto. Sin herramientas nuevas, cambios SQL, consumidores, commits ni despliegue. C16 y C06 siguen sin aceptar; detenerse antes de T49/T19. Los apartados siguientes conservan evidencia histórica de sus bloques.

**Registro previo de C06, 2026-10-26:** C05 aceptado por el usuario al pedir un prompt para continuar en otra sesión. T16–T18 comprobadas; C06 sin aceptar ni habilitar T19.

## T16–T18 para revisión C06

services añade catálogo privado, ofertas por cuenta y resolución de duración. Solo el profesional propietario escribe; miembros leen únicamente las ofertas de su cuenta. Un ajuste nulo toma la base vigente; otro valor entre 1 y 1440 conserva su valor. Inactivar catálogo no cambia estados de ofertas; inactivar una oferta no altera otra. El journal conserva catálogo para owner y proyecciones de ofertas para members, con ambas versiones. Los controles de cuenta se bloquean en orden tras el profesional; un fallo en la segunda proyección revierte todo, incluido recibo y auditoría. Duplicados y consulta del resultado revalidan también el vínculo profesional vigente.

schedule añade las tres operaciones y dos lecturas de reglas semanales. Respeta día ISO, minutos, fechas de vigencia incluidas y fin 1440. Une solapados y contiguos sin borrar el corte de jornada partida. La UQ con NULLS NOT DISTINCT impide duplicar una regla abierta, incluso con SQL directo. Un caso compartido usa la fecha local y la zona de cuenta; el cambio de fecha de Caracas a las 04:00 UTC queda comprobado. No calcula aún huecos libres ni extremos UTC de una recurrencia: T21 debe añadir excepciones, bloqueos, ocupación y resolución explícita de horas ambiguas o inexistentes.

La prueba de cambio incompatible pasa intervalos requeridos ficticios al caso de reglas bajo el bloqueo del profesional. Rechaza antes de escribir y conserva las filas. No hay reservas reales ni tablas de citas: T22 debe aportar esos intervalos desde ocupación vigente y conectar booking_patient/booking_service; T32 debe probar la carrera. La segunda cuenta del profesional es solo una fixture SQL de tipo clinic para comprobar FK, ajuste independiente y proyección. El API sigue limitado a consultas independientes; no se habilita gestión de clínicas.

Comprobaciones: 108 pruebas unittest correctas en 51.714 s, incluidos controles de estructura de los dos componentes, sin excepciones nuevas. Ocho probes reales correctos: acceso, cuentas, sync, equipo, pacientes, servicios, agenda y persistencia. Servicios y agenda se repitieron tras la revisión final. PostgreSQL aplica/revierte/reaplica el head 20261026_08 con 21 tablas y comprueba rollback de una revisión fallida. Build offline correcto. La prueba HTTP separada del wheel se omite, según la instrucción del usuario. No se añaden dependencias, commits, despliegues, consumidores ni cambios a otros repositorios. Las versiones y fuentes oficiales están en [sources.md](../sources.md#fuentes-técnicas-de-t16t18--2026-10-26).

La suite inicial tenía 91 pruebas correctas. El aislamiento de Windows impidió a uv guardar su caché: repetir fuera permitió usar el entorno existente. Un fallo de importación de T16 señaló una ubicación incorrecta de repository; se movieron esos dos archivos a su carpeta y se repitieron las comprobaciones. Las ofertas usan el método del DAO derivado para su clave compuesta; no se modifica el DAO base.

## Estado comprobado y aceptado en C05

patients contiene fichas borrador, documentos declarados opcionales, contactos reutilizables y vínculos por cuenta. RegisterPatient crea una identidad nueva y su ficha; nunca adjunta una identidad global arbitraria ni fusiona coincidencias declaradas. Edición, actividad, completitud y alta posterior de documento usan la aceptación existente, versiones, recibos, auditoría y grupos atómicos. Las siete lecturas aplican permisos vigentes y paginación autorizada en DAO; q busca texto literal de nombre/documento dentro de cuenta. Los vínculos muestran nombres/teléfonos actuales en GET; resultados y journal conservan solo el estado propio del vínculo.

phonenumbers 9.0.41 es la única dependencia nueva prevista por el contrato. Valida prefijo, estructura y longitud posible, normaliza la parte nacional y conserva ceros significativos. No prueba existencia ni titularidad. Los documentos conservan prefijos, ceros y puntuación; su normalización por país y la verificación siguen fuera del alcance. Las demás versiones no cambian.

SetPatientCompletion acepta own_document con documento declarado o verificado y teléfono propio o responsable vigente. minor_without_document requiere nacimiento, menos de 18 en el día local y responsable vigente con teléfono. No exige inspección física. booking_patient vuelve a comprobar actividad, completitud, edad y contacto en el instante propuesto de cita; sus pruebas usan la zona America/Caracas, el límite de 18 años y fin exclusivo de vigencia. El cálculo administrativo por mes/día trata el cumpleaños del 29 de febrero como alcanzado el 1 de marzo en un año no bisiesto; no acredita edad legal. No existe todavía una ruta de cita que invoque ese caso: T22 debe conectarlo y probarlo junto con las demás reglas de reserva.

Retirar requisitos exige otra base válida o pasar antes explícitamente a draft. El caso comprueba la propuesta antes de escribir y devuelve COMPLETENESS_CONFLICT sin efecto parcial. La migración 20261026_05 comprueba el estado final al commit en fichas/documentos/contactos/vínculos, con bloqueos de control de cuenta e identidad, también para borradores y escrituras SQL concurrentes. Una prueba con dos conexiones retira cada uno de los dos teléfonos responsables: confirma uno, rechaza el otro y conserva una ficha válida. Se comprueba también el rechazo diferido al invalidar el único documento. El paso del tiempo no actualiza filas por sí solo: reservar revalida edad y vigencia, aunque una ficha conserve complete desde antes.

Suite final: 91 pruebas correctas (63.974 s), incluidos 30 controles de estructura y tres generales, sin excepciones nuevas. Seis probes reales correctos: acceso, cuentas, sync, equipo, pacientes y persistencia. Prueban aislamiento, versiones, duplicados concurrentes, rollback inmediato/diferido, respuesta perdida en ASGI, contactos compartidos, FK de cuenta, conservación de constancias y completitud concurrente. Una constancia verificada es una fixture administrativa; la API no ofrece verificar. Migraciones hasta 20261026_05 aplicadas/revertidas/reaplicadas con 18 tablas en bases ficticias que se eliminan. Build offline correcto; no se ejecuta la prueba HTTP separada del wheel.

Cierre de archivos: 54 Python nuevos/cambiados analizados con AST, 14 Markdown revisados y 68 enlaces locales, sin destino nuevo ausente. Se conservan cinco destinos históricos ausentes. Wheel de 130 entradas con casos/rutas de pacientes y sin archivos privados; fábrica, dependencia de sesión, DAO base, esquema base y script de alta sin cambios. git diff --check correcto. PostgreSQL y Keycloak conservan los PID 9400 y 32092 del inicio.

Servicios, agenda/citas, snapshot, descarga, SSE, consumidores Rust/Hub y operación siguen pendientes. No se aplica SQL a una base personal ni se modifica otro repositorio; no hay commits o despliegues. Se conservan los servicios de prueba ya activos. La integración con reservas reales y cambios de zona/horario conserva sus tareas; no se acredita por probar la regla aislada de pacientes.

## Registro de C04

T10 añade invitaciones dirigidas de 72 horas y listas con estado vencido derivado, sin cambiar la fila por leerla. Solo propietario crea/revoca invitaciones o cambia asistentes. El destinatario acepta con su identidad autenticada; pertenencia, invitación, recibo, auditoría, época y grupo completo se confirman juntos. La aceptación no registra un dispositivo. Una aceptación inicial rechazada no crea pertenencia ni recibo de éxito para satisfacer la FK. Se comprueban duplicado concurrente, vencimiento, destinatario ajeno, revocación frente a aceptación, rollback y respuesta perdida tras commit en ASGI.

T11 añade cambios tipados de datos/política/estado de cuenta y perfil profesional, así como revocación/restauración por cuenta. El propietario puede recuperar su cuenta inactiva desde una instalación habilitada; no puede autorrestaurar una instalación revocada ni restaurar una instalación globalmente revocada. Los usuarios afectados se bloquean por ID antes del control de cuenta; profesional antes del control al editar cuenta/perfil. La prueba usa el mismo dispositivo en dos cuentas y verifica su aislamiento y la carrera de restauración local/revocación global. Equipo, dispositivos y profesionales usan proyecciones explícitas, total autorizado y LIMIT/OFFSET en DAO.

T12 añade consulta de auditoría por propietario, filtros de fecha/acción/tipo/objeto, orden (occurredAt,id), paginación y correlación. Alta administrativa y controles de emisión/rotación/revocación guardan evidencia en su transacción; un fallo CHECK del hecho técnico revierte la rotación. Las denegaciones HTTP 401/403/404 guardan solo identidad validada, ámbito conocido y correlación, sin cuerpo, ruta libre ni secreto. Si el almacén falla al registrar una denegación, conserva el rechazo original; no se acredita persistencia de ese hecho durante una caída de base. Las lecturas correctas no generan copias de datos en auditoría.

scripts/purge_expired_results.py exige MAINTENANCE_DATABASE_URI explícita y privilegio UPDATE. Usa la fábrica existente solo en su proceso; no cambia la configuración de API. Retira result_json de recibos vencidos y asigna purged_at con reloj del servidor. Conserva claves, huellas, estados/versiones, journal y auditoría. La prueba ejecuta el script con rol operativo (denegado), rol administrativo (un resultado) y repetición (cero); luego comprueba 410 y conflicto de contenido bajo la misma clave. No se implementa purga de snapshots aún inexistentes.

Suite de 76 pruebas correcta (48.992 s), incluidos 25 controles de estructura y tres generales; cinco probes reales de acceso, cuentas, sync, equipo y persistencia correctos. La revisión 20261026_02 aplica/revierte/reaplica el head de 13 tablas en base ficticia. Cada probe verifica el clúster y elimina solo su base aleatoria. Build offline e inspección de 117 entradas del wheel correctos. Los servicios previos se conservan. Sin dependencias nuevas, cambios a fábrica/DAO base/esquema base, commits ni despliegues. No se ejecuta la prueba HTTP separada del wheel.

No existen tablas ni funciones de pacientes, agenda o citas en este punto. Por ello no se acredita compatibilidad de cambios de zona/horario con reservas reales; sus tareas deben conectar y probar esa regla antes de habilitarla. No hay consumidor Rust/Hub, caída TCP real, snapshot, descarga incremental, SSE ni operación en producción. Las pruebas de caducidad preparan fixtures antiguas sustituyendo el reloj del DAO; no cambian el reloj de PostgreSQL ni esperan 72 horas/90 días.

## Registro de C03

T09 conecta seis lecturas: identidad propia, cuentas visibles, detalle de cuenta, acceso vigente, perfil profesional propio y dispositivos propios. Reutiliza los casos y DAOs existentes; no añade alta pública. El probe de cuentas contrasta HTTP, SQL y script con tres sujetos y dos cuentas, páginas sucesivas/vacías, proyecciones explícitas, errores 401/403/404/422 y revocaciones. Autenticarse sigue sin crear permisos.

T07 conecta POST /v1/accounts/{account_id}/sync/operations y GET de su resultado. RegisterAccountDevice es el único efecto inicial; las demás acciones siguen en sus tareas y producen UNSUPPORTED_OPERATION. accounts registra solo la instalación propia. sync coordina autorización vigente, control de cuenta, versión, dependencias y huella canónica; audit escribe el hecho técnico mediante su caso de uso. Todos usan la misma sesión y transaction(db), con commit=False. No hay acceso directo a sesiones en application ni repositorios ajenos.

La revisión 20261026_01 añade operation_receipts, change_log y audit_events, sus FK, restricciones, índices y controles diferidos. La aceptación conserva efecto, época, posición, grupo completo, recibo y auditoría juntos. La identidad de ejecución puede insertar/leer esos registros, pero no modificarlos ni borrarlos. Recibos mínimos no se eliminan; el resultado vence tras 90 días y devuelve 410, incluso tras retirar sus detalles. No hay tarea automática de purga ni descarga de journal en esta entrega.

71 pruebas unittest correctas (33.383 s), incluidos 25 controles de estructura para users, authorization, accounts, sync y audit, y tres controles generales. Los probes de acceso, cuentas, sync y persistencia pasan con PostgreSQL 18.3/Keycloak 26.8.1 reales. La prueba de sync verifica duplicado concurrente, conflicto de contenido, claves aisladas por actor/cuenta, rollback inmediato y diferido, reintento, independencia de lotes y permiso releído tras esperar un bloqueo real (pg_blocking_pids). Simula la pérdida de respuesta en ASGI después del commit; no acredita una caída de red TCP. Para caducidad prepara un recibo ficticio antiguo mediante el reloj sustituido del DAO; no espera 90 días ni cambia el reloj de PostgreSQL.

Los servicios locales ya estaban activos y se conservaron. Cada probe valida el clúster, crea una base aleatoria y elimina solo esa base. Sin nuevas dependencias, cambios a la fábrica, DAO base o esquema base. La construcción de sdist/wheel pasa; se omite la prueba HTTP separada del wheel por petición del usuario. No hay consumidor Rust/Hub, SSE, snapshot, descarga incremental, operación en producción ni datos reales. La consulta pública de auditoría permanece en T12.

## Registro de C15

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
