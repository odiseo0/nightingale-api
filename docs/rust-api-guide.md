# Consumo de API v1 desde Rust

Revisión: api-v1.3, 2026-11-16. Esta guía describe el servidor de este repositorio. No implementa ni acredita el cliente Rust, SQLite, Outbox o Hub.

## Fuente y arranque

Fija una versión o huella de [los contratos generados](../contracts/README.md). OpenAPI describe HTTP; `accepted-operations.schema.json` añade los payloads válidos del catálogo real por lote, sin recuento fijo. Los modelos Pydantic y los casos de uso siguen siendo la fuente. JSON Schema no expresa todas las reglas de negocio ni concede permisos.

Con Python 3.15.1 o posterior compatible, usa las dependencias de `uv.lock`. El servidor conserva su app de módulo:

```powershell
uv sync --locked
uv run --locked uvicorn src.application:app --host 127.0.0.1 --port 8000
```

Antes de arrancar, proporciona la conexión operativa y la configuración OIDC en el entorno seguro del proceso. `API_SYNC_SIGNING_KEY` debe ser secreta, tener al menos 32 caracteres y ser igual en cada proceso. No guardarla en ejemplos, contratos o registros. El servidor no migra ni crea cuentas al arrancar. El operador aplica las migraciones y usa el alta controlada de [desarrollo](operations/development.md); el escritorio no recibe credenciales SQL.

`GET /health/live` comprueba vida; `/health/ready` exige base y listener disponibles. Al perder el listener, preparación devuelve 503 mientras las rutas de datos siguen disponibles. OpenAPI y las páginas de documentación HTTP se exponen solo en desarrollo/prueba. La exportación offline funciona sin conexión a la base.

## Identidad, dispositivo y cuenta

1. Lee `GET /v1/auth/config` y usa OIDC Authorization Code con PKCE S256 en un navegador externo. La API comprueba emisor, audiencia y firma. El ID token no sustituye al access token OIDC destinado a API.
2. Envía ese access token en Authorization Bearer a `POST /v1/auth/device-tokens`, con el cuerpo `deviceRegistration` de [examples.json](../contracts/examples.json). API devuelve el token opaco de dispositivo y su ID. Rust debe conservarlo de forma segura; esta guía no prueba ese almacenamiento.
3. Usa ese token opaco en las peticiones siguientes. `GET /v1/me` y `/v1/accounts` permiten descubrir las cuentas propias. `GET /v1/accounts/{account_id}/access` informa estado, acciones y permissionEpoch antes de registrar la instalación.
4. Sustituye `{{deviceId}}` en el ejemplo `registerAccountDevice` y envíalo como operación. Una identidad global no crea pertenencia ni acceso a pacientes por sí sola. Aceptar una invitación usa su ruta propia, con operationId, y tampoco registra la instalación por deducción.

El token API no vence por tiempo; API puede revocarlo. Cerrar sesión en Keycloak no lo revoca por sí solo. La revocación global de dispositivo y la revocación en una sola cuenta tienen alcances distintos. Una instalación revocada no se restaura a sí misma.

`GET /v1/capabilities` publica las acciones y límites implementados. `operationCatalog` se deriva del catálogo real por lote; `onlineOnlyActions` incluye también AcceptInvitation, que usa su ruta dirigida. Conserva esas acciones administrativas como flujos con conexión; no las conviertas en intenciones offline por inferencia. API reautoriza siempre con el estado vigente al recibir cada petición.

## Escrituras, lotes y resultados

Envía `POST /v1/accounts/{account_id}/sync/operations` con `{operations:[...]}`. Los objetos de `examples.json` se colocan dentro de esa lista. El ejemplo crea una ficha draft; no crea una ficha completa ni habilita una reserva sin sus requisitos.

- Usa UUIDv7 para operación y entidades nuevas. Conserva operationId y contenido al reintentar; no generes otro ID para resolver una respuesta perdida.
- Crea con expectedVersion=0; cambia con la versión remota conocida. No envíes actor/dispositivo como autoridad en el payload.
- Máximo 100 operaciones, 1 MiB por cuerpo y 64 KiB por operación. dependsOn admite hasta ocho IDs del mismo actor/cuenta, ya aceptados o anteriores en el lote. Una operación tiene su propia transacción; el lote no confirma todo como una sola unidad.
- Conserva ausencia frente a null. Un patch no borra un campo solo porque falte; un null solo vale donde su modelo lo permita. API valida el payload una vez y usa ese modelo para huella y ejecución. Un payload inválido conserva el JSON recibido para su rechazo, sin guardar el cuerpo personal.

accepted confirma el efecto después del commit. duplicate conserva el resultado original, incluso si era un rechazo. conflict exige revisión: VERSION_CONFLICT no permite sobrescribir la versión nueva; SLOT_UNAVAILABLE no reserva el horario; IDEMPOTENCY_CONFLICT indica que se reutilizó un ID con otro contenido. rejected conserva el rechazo definitivo. retryable_failure no fija un rechazo permanente: consulta o reintenta la misma intención.

Si no conoces el resultado, consulta `GET A/sync/operations/{operation_id}` o reintenta el mismo objeto. Una instalación nueva del mismo actor puede consultar un resultado si todavía tiene acceso a la cuenta y acción. Conocer el ID no evita una revocación. RESULT_EXPIRED impide recuperar el detalle, pero el recibo mínimo sigue evitando repetir el efecto. No sustituirlo por otra intención sin revisión del estado remoto.

## Captura y descarga incremental

1. Crea una captura con `POST A/sync/snapshots`, usando `snapshotRequest` o `{}`. Las fechas son locales: por defecto hoy-30 hasta hoy+181 exclusivo; máximo 366 días. API devuelve snapshotId, window, baseCursor, expiresAt e itemCount.
2. Lee `GET A/sync/snapshots/{snapshot_id}/items?page=1&shows=100` y las páginas siguientes. page empieza en 1, shows tiene máximo 500; la respuesta contiene items/total. La captura materializada conserva los mismos elementos y orden durante 15 minutos, sujeto a permisos vigentes.
3. Solo al completar la captura, instala la vista remota y su baseCursor juntos en la transacción SQLite del consumidor. Conserva por separado sus intenciones pendientes. Este paso es una obligación del consumidor; no lo ejecuta API.
4. Descarga `GET A/sync/changes?cursor=<cursor_aplicado>`. Aplica cada página y nextCursor juntos en SQLite. Continúa si hasMore es true, incluso si groups está vacío: API puede haber avanzado sobre grupos de audiencia oculta o fuera de ventana.
5. Libera el derivado con DELETE de la captura cuando ya no haga falta. Ese DELETE no borra negocio, recibos ni intenciones locales.

La descarga examina hasta 100 grupos completos por petición; no admite page/shows. Un grupo comparte groupId y operationId y puede contener varias entidades. No lo dividas al aplicar efectos. Las versiones de entidad no son la posición incremental.

appointment_history acompaña a appointment y solo contiene historia hasta la versión descargada. Si una cita sale de ventana, API retira cita e historia con changeKind=remove. Esa retirada cambia la vista local; no borra la historia funcional del servidor. Ventana, zona y límites UTC quedan fijos en captura/cursor aunque se edite la zona de la cuenta. Cambiar ventana exige otra captura explícita.

Las listas GET corrientes también usan page/shows, pero no ofrecen una vista única entre peticiones concurrentes. Usa captura más incremental para reconstruir una vista coherente.

## Datos clínicos opcionales

La captura acepta `includeClinical=false` por defecto. Con `true`, incluye solo secciones legibles de las Etapas 1 y 2: perfil, condiciones, alergias/intolerancias y sus revisiones, atenciones, notas, mediciones, vacunas y antecedentes. Incluye el estado clínico elegido para evolución y todas las tomas válidas, pero no historias de versiones, timeline ni adjuntos. `SnapshotResponse.clinicalSections` y el cursor conservan ese alcance. Los hechos clínicos no se limitan por la ventana de citas.

Las ocho secciones tienen permisos `none`, `read` o `read_write`; el propietario configura asistentes online con `SetMemberClinicalPermissions`. Cambiar permisos incrementa la época y exige otra captura. No hay borrado remoto garantizado de copias ya descargadas. Resultados de escritura clínica exigen `read_write` vigente. Las historias se consultan aparte con conexión. Un consumidor sin modelos y proyectores clínicos debe conservar `includeClinical=false`.

Los contratos clínicos incluyen perfil, condiciones/alergias, atenciones, notas, mediciones, vacunas y antecedentes, con corrección y anulación por tipo. Fechas históricas: `YYYY`, `YYYY-MM` o `YYYY-MM-DD` donde el modelo las admita, sin completar días ficticios. Perfil ausente devuelve versión 0 sin escribir. La edad y última visita se calculan desde nacimiento y atenciones válidas. La [referencia portable completa](../contracts/api-v1/nightingale-api.md) detalla rutas, acciones, modelos y límites.

## SSE como aviso

Abre `GET A/sync/events?cursor=<cursor_aplicado>` con el token de dispositivo. Un cliente Rust debe poder enviar Authorization y leer el formato SSE; no se escoge aquí una biblioteca de consumidor.

- changes_available contiene accountId y un cursor de referencia. Ese cursor conserva la posición que se dio al abrir el stream; no reconoce datos como aplicados. Descarga con el cursor aplicado que Rust conserve en ese momento.
- heartbeat contiene serverTime cada 15 segundos. API revalida acceso al emitir y en ese plazo, sin mantener una sesión SQL por stream.
- access_revoked no contiene data y cierra el stream. Last-Event-ID es solo una referencia; API no lo acepta como prueba de aplicación ni lo usa para saltar cambios.

El servidor sugiere reconectar tras 3000 ms. Al reconectar, da el cursor aplicado más reciente; si el proceso o la señal falla, journal y heartbeat permiten recuperar. Máximo dos conexiones por dispositivo/cuenta entre todos los procesos. Tras una caída, un registro puede ocupar el cupo hasta 45 segundos; no crees otro dispositivo para eludir 429. La cola de aviso tiene capacidad uno y un envío que excede tres segundos desconecta al cliente lento. Vuelve a descargar por cursor.

El probe local de T32 midió 20 commits/200 avisos con diez streams y dos procesos. P95: 120.1 ms desde callback posterior al commit; cota superior que incluye commit: 122.5 ms. Es una muestra local, sin saturación, consumidores Rust/Hub ni garantía de producción. Configuración y límites en [desarrollo](operations/development.md).

## Recuperación y errores

| Respuesta | Acción del consumidor |
|---|---|
| 401 | Revisar token/dispositivo; volver al flujo de acceso si corresponde. No repetir una operación con otro ID por este error. |
| 403/404 | Detener el acceso afectado; no deducir existencia de objetos ajenos. Conservar intención para revisión autorizada. |
| 410 CURSOR_EXPIRED | Crear otra captura; reconstruir la vista remota conservando Outbox e intenciones. Incluye firma, ámbito, época, plazo o frontera de retención inválidos. |
| 410 SNAPSHOT_EXPIRED/SNAPSHOT_SCOPE_CHANGED | Abandonar ese derivado y solicitar otra captura con permisos actuales. |
| 410 RESULT_EXPIRED | Consultar el estado actual y revisar la intención; el recibo mínimo sigue impidiendo repetirla. |
| 422 | Corregir entrada según modelo/código. No alterar el contenido de una operación ya identificada para reintentarla con el mismo ID. |
| 429 CONNECTION_LIMIT | Cerrar un stream sobrante o esperar su liberación/vencimiento; conservar cursor aplicado. |
| 503 | Reintentar con la misma identidad cuando se recupere la dependencia; una respuesta perdida puede seguir a un commit correcto. |

Los grupos y resultados completos se conservan al menos 90 días. Un cursor en frontera-1 aún puede seguir; uno anterior requiere captura. Una captura ausente, ajena o ya liberada devuelve el mismo 404; una captura propia aún existente distingue vencimiento y cambio de época con 410. Ninguna recuperación remota borra las intenciones del escritorio por sí sola.

Prueba reproducible de los ejemplos: `.venv/Scripts/python.exe test-support/contracts/check.py`, con servicios Test existentes y datos ficticios. Usa PostgreSQL/Keycloak reales y cliente ASGI para esos ejemplos; las pruebas separadas de SSE/colaboración sí usan dos procesos Uvicorn. No se ejecuta HTTP separado del wheel ni se acredita todavía un consumidor externo.


## Vademecum en línea

El catálogo global de productos vigentes y monografías se consulta solo con conexión, con el token de dispositivo y una cuenta donde el profesional o asistente, la pertenencia, la cuenta y la instalación estén activos. `A` significa `/v1/accounts/{account_id}`.

- `GET A/vademecum/products?q=...&monographId=...&page=1&shows=100` busca por nombre, registro, texto/ID de ingrediente, alias y ATC de monografías vinculadas. `monographId` es opcional.
- `GET A/vademecum/products/{registration_number}` devuelve el producto y sus vínculos del release activo.
- `GET A/vademecum/monographs?q=...&page=1&shows=100` busca nombre, alias y ATC.
- `GET A/vademecum/monographs/{monograph_id}` devuelve el documento completo.

Cada respuesta incluye `catalog` con `schemaVersion`, `registryCutoffDate`, `medicalNotice` y `sourceSha256`. La interfaz debe mostrar el aviso y conservar `review`, fuentes, procedencia, `ingredientLinkStatus` e `ingredientResolution`; un vínculo inferido o revisión pendiente no es aprobación clínica. Las especialidades extranjeras de referencia no son registros venezolanos.

Los listados devuelven `items`/`total`; `shows` llega a 500. Una página posterior al final está vacía y conserva el total. 404 significa objeto ausente después de autorización; 503 indica catálogo sin release activo o dependencia no disponible. 401/403 exigen revisar el acceso vigente.

Estas lecturas no participan en capturas, Change Log, Outbox ni almacenamiento offline. No las conviertas en medicación declarada o prescripción de un paciente. No hay endpoints de escritura/revisión ni contenido histórico/suplementario. La referencia ejecutable está en los JSON generados; esta guía no acredita un consumidor Rust implementado.
