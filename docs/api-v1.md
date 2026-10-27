# Contrato de diseño HTTP v1 para escritorio

**Versión de diseño:** 1.1. **Fecha:** 2026-10-27. **Estado:** C06 aceptado; T19–T27 comprobadas en el [plan aprobado](../tasks/P-20261024-01-desktop-shared-api/plan.md). C09 listo para revisión, sin marcar aceptación de C07–C09. Agenda y ciclo de citas operativos en pruebas aisladas, con ocupación global e historia inmutable. Snapshot, descarga y SSE siguen pendientes; no se acredita integración con el escritorio ni operación en producción.

Esta es la única fuente editable del diseño de transporte de esta etapa. [contracts.md](contracts.md) fija propiedad y principios; [database-schema.md](database-schema.md) posee columnas, tipos y restricciones físicas, sin duplicarlos aquí. Los esquemas Pydantic de domain heredan del BaseModel del proyecto y producirán OpenAPI/JSON Schema; un generado identificará origen y versión y nunca se editará a mano. Los casos de uso no dependen de FastAPI ni acceden directamente a SQLAlchemy.

## 1. Alcance y autenticación

Solo consultas independientes, un profesional y asistentes. Sin modificación de Rust, Hub, clínicas, comunicaciones, espera, analítica, datos reales o producción. No se exponen CRUD global de usuarios, contraseñas, concesiones Hub, búsqueda/fusión/corrección global de pacientes, verificación de identidad/representación o reapertura/cambio de referencias de citas.

Keycloak de desarrollo autentica mediante navegador externo, Authorization Code y PKCE S256. El token OIDC solo se acepta en POST /v1/auth/device-tokens; comprobar firma RS256 con JWKS de URL configurada, issuer, audiencia, exp/nbf y azp del cliente público permitido. No aceptar ID token, algoritmos del cliente ni URL de claves del JWT. El proveedor y JWKS se consultan fuera de transacciones; HTTPX asíncrono, caché de claves 5 minutos, recarga única ante kid desconocido; sin clave válida por fallo de red: 503, sin permitir por error. En producción todo externo exige TLS; HTTP se permite solo en el entorno local de desarrollo/prueba y direcciones configuradas.

La pareja OIDC exacta iss/sub identifica al usuario. Primer canje puede crear app_user sin permisos; no crea consulta, pertenencia o profesional. El token API se presenta como Authorization: Bearer ngt_<token_id>.<secret>. tokenId es UUIDv7; secret son 32 bytes aleatorios en base64url sin relleno. Guardar solo SHA-256 de los bytes secretos, comparar de forma segura; nunca devolver huella en respuestas. Token sin expiresAt, ligado a una sola persona y dispositivo. Validar token, dispositivo, usuario, pertenencia, cuenta y autorización por objeto/acción desde estado actual.

Cerrar sesión o desactivar en Keycloak no revoca automáticamente el token API. Revocación efectiva ocurre al commit de API. Recuperar una credencial perdida exige volver a OIDC, crear otro dispositivo y revocar el anterior; no recuperar secretos del servidor. La instalación conserva el token solo en almacenamiento seguro de Rust, fuera de este alcance.

## 2. Reglas de transporte

- JSON público y filtros compuestos en camelCase; atributos Python y nombres SQL en snake_case. Los parámetros de ruta conservan sus nombres internos. Estados, acciones, códigos de error, claims OIDC y valores de protocolos externos conservan su forma exacta. No alterar credenciales ni issuer/subject al validar. Los ejemplos de JSON describen campos públicos, no columnas SQL.
- Prefijo /v1; identificadores UUIDv7 en forma textual canónica. Versiones enteras positivas; expectedVersion=0 solo creación. Nombres de acciones sensibles a mayúsculas.
- Tiempos RFC 3339 con offset explícito y finitos; respuestas de instantes en UTC con Z. Fechas YYYY-MM-DD, zonas IANA reconocidas. No aceptar fecha naive, infinito ni booleano como número. Los extremos de citas tienen segundos/fracción cero y duración entera 1–1440 minutos.
- Campos desconocidos rechazados. Objeto vacío permitido solo en acciones que lo indiquen. Patch: al menos un campo, ausencia conserva valor, nulo solo si el dato admite nulo. No aplicar diccionarios libres al ORM. Cambio sin diferencia devuelve NO_CHANGES y no añade versión funcional.
- Texto presente no vacío tras quitar espacios exteriores; documento conserva prefijos, ceros, mayúsculas internas y puntuación mientras no exista regla nacional aprobada. No verificar titularidad por texto.
- Teléfono con pareja phoneCode/phone ambos presentes o ambos nulos. pycountry valida país ISO asignado; phonenumbers normaliza estructura internacional y longitud posible, preserva ceros significativos; no prueba existencia/propiedad. Código ISO no deriva de prefijo telefónico.
- Lote 1–100 operaciones, cuerpo máximo 1 MiB y cada operación 64 KiB UTF-8. Superar límites rechaza antes de efectos. Lista normal 100/máximo 500; páginas de cambios 100/máximo 500 grupos completos. Página de snapshot 100/máximo 500 elementos; un grupo no se corta aunque contenga varias entidades.
- Correlación UUIDv7 generada en servidor y devuelta en cabecera X-Correlation-ID y errores; no equivale a autorización. Respuestas personales/credenciales: Cache-Control: no-store. No secretos en URL, logs, errores ni métricas.
- Listados y elementos del snapshot: page entero desde 1 (por defecto 1), shows entero de 1 a 500 (por defecto 100); OFFSET=(page-1)*shows y LIMIT=shows en DAO. Respuesta PaginatedResponse con items y total autorizado, sin cursor, firma ni configuración de páginas. Filtros y autorización se aplican antes del conteo y de la paginación. Una página posterior al final devuelve items vacío y el total. Parámetros desconocidos o inconsistentes: 422.
- La posición de avance incremental de sync conserva su contrato de alcance, ventana, época de acceso y recuperación. No es un cursor de página ni se sustituye por OFFSET. El soporte de cursores de listados no se reutiliza para implementarla.
- Listados con orden estable y estado por defecto sin filtrar para no ocultar inactivos/borradores; q opcional, búsqueda literal limitada a cuenta (no directorio global). Rango de instantes [from,until), from < until. Fechas de vigencia mantienen la convención del esquema.
- Solo API. Esta guía indica cómo consumirá Rust el contrato, no acredita integración del escritorio.

## 3. Catálogo de rutas

A equivale exactamente a /v1/accounts/{account_id}. Parámetros de ruta y filtro no conceden acceso. Salvo rutas públicas y emisión OIDC, todas requieren token de dispositivo. Las rutas bajo A requieren además dispositivo registrado activo en la cuenta, salvo GET A/access, RegisterAccountDevice y las excepciones administrativas limitadas de reactivación/restauración. Sin registro se permite descubrir las cuentas en GET /v1/accounts y registrar la instalación; nunca descargar pacientes. Rotación propia exige el dispositivo del token actual; revocación global propia puede dirigirse a otro dispositivo propio.

| Método | Ruta | Acceso | Modelo de respuesta | Entrada / comportamiento |
|---|---|---|---|---|
| GET | `/health/live` | público | LiveResponse | vida del proceso |
| GET | `/health/ready` | público | ReadyResponse | 200 preparado; 503 con dependencia esencial no lista, sin detalles de conexión |
| GET | `/v1/capabilities` | público | CapabilitiesResponse | versión 1, acciones y límites; sin información de cuentas |
| GET | `/v1/auth/config` | público | AuthConfigResponse | issuer, publicClientId, audience; nunca secreto |
| POST | `/v1/auth/device-tokens` | OIDC | DeviceTokenIssued | DeviceRegistrationRequest; 201; solo acepta access token OIDC destinado a API |
| GET | `/v1/me` | token | MeResponse | identidad propia y resumen de cuentas; no registra permisos |
| GET | `/v1/me/devices` | token | PaginatedResponse<DeviceResponse> | dispositivos del mismo usuario, incluidos revocados |
| POST | `/v1/me/devices/{device_id}/rotate-token` | token propio | DeviceTokenIssued | TokenRotationRequest; 201; exige que el token presentado pertenezca al dispositivo indicado |
| POST | `/v1/me/devices/{device_id}/revoke` | token propio | sin cuerpo | 204; el usuario puede revocar cualquiera de sus dispositivos; preserva referencias |
| GET | `/v1/me/invitations` | token | PaginatedResponse<InvitationResponse> | solo invitaciones dirigidas al usuario; filtro status |
| POST | `/v1/me/invitations/{invitation_id}/accept` | token destinatario | InvitationAcceptanceResult | InvitationAcceptRequest; 200; idempotencia con operationId |
| GET | `/v1/accounts` | token | PaginatedResponse<AccountSummary> | cuentas del usuario, incluidas inactivas para administrar su reactivación |
| GET | `A` | miembro activo | AccountResponse | propietario conserva acceso administrativo mínimo para reactivar cuenta inactiva |
| GET | `A/access` | miembro | AccessResponse | rol, acciones efectivas, estado y permissionEpoch; funciona antes de registrar instalación en la cuenta |
| GET | `A/members` | propietario | PaginatedResponse<MemberResponse> | userId, displayName, rol derivado y estado; sin claims OIDC |
| GET | `A/invitations` | propietario | PaginatedResponse<InvitationResponse> | filtro status; destinatario solo por userId |
| GET | `A/devices` | propietario | PaginatedResponse<AccountDeviceResponse> | solo autorizaciones de la cuenta, sin otras cuentas ni tokens |
| GET | `A/audit-events` | propietario | PaginatedResponse<AuditEventResponse> | from, until, action, objectType, objectId; orden (occurredAt,id) |
| GET | `A/professionals` | miembro | PaginatedResponse<ProfessionalResponse> | profesional visible de la consulta; filtro status |
| GET | `/v1/me/professional` | profesional propio | ProfessionalResponse | 404 si no existe perfil propio |
| GET | `/v1/me/services` | profesional propio | PaginatedResponse<ServiceResponse> | catálogo propio, ofrecido o no; q y status |
| GET | `A/services` | miembro | PaginatedResponse<ServiceOfferResponse> | ofertas visibles; professionalId, status y q; no catálogo privado completo |
| GET | `A/patients` | miembro | PaginatedResponse<PatientProfileResponse> | q, status, completionStatus; búsqueda por nombre o documento registrado de sus fichas |
| GET | `A/patients/{patient_id}` | miembro | PatientProfileResponse | solo ficha de esta cuenta |
| GET | `A/patients/{patient_id}/identifiers` | miembro | PaginatedResponse<PatientIdentifierResponse> | documentos de identidad vinculada a esa ficha; sin búsqueda global ni verificador de otra cuenta |
| GET | `A/patients/{patient_id}/contacts` | miembro | PaginatedResponse<PatientContactResponse> | vínculos de esta ficha; status |
| GET | `A/contacts` | miembro | PaginatedResponse<ContactResponse> | q y status; sin buscar contactos globales |
| GET | `A/contacts/{contact_id}` | miembro | ContactResponse | contacto de la misma cuenta |
| GET | `A/contacts/{contact_id}/patients` | miembro | PaginatedResponse<PatientContactResponse> | vínculos y resumen mínimo de fichas de esta cuenta; status |
| GET | `A/schedule/rules` | miembro | PaginatedResponse<ScheduleRuleResponse> | professionalId, isoWeekday, status, fromDate, untilDate |
| GET | `A/schedule/rules/{rule_id}` | miembro | ScheduleRuleResponse | solo regla visible |
| GET | `A/schedule/exceptions` | miembro | PaginatedResponse<ScheduleExceptionResponse> | professionalId, status y rango local de fechas |
| GET | `A/schedule/exceptions/{exception_id}` | miembro | ScheduleExceptionResponse | solo excepción visible |
| GET | `A/schedule/blocks` | miembro | PaginatedResponse<ScheduleBlockResponse> | professionalId, status y rango UTC; bloqueo global ajeno a gestión se proyecta solo como intervalo |
| GET | `A/schedule/blocks/{block_id}` | miembro | ScheduleBlockResponse | sin motivo global para asistente; 404 si no corresponde al ámbito |
| GET | `A/availability` | miembro | AvailabilityResponse | professionalId, serviceId, from, until y durationMinutes opcional; máximo 31 días |
| GET | `A/appointments` | miembro | PaginatedResponse<AppointmentResponse> | from y until requeridos; professionalId, serviceId, patientId, status; máximo 366 días |
| GET | `A/appointments/{appointment_id}` | miembro | AppointmentResponse | permite consulta histórica fuera de ventana descargada |
| GET | `A/appointments/{appointment_id}/history` | miembro | PaginatedResponse<AppointmentHistoryResponse> | orden version ascendente; afterVersion opcional; page/shows |
| POST | `A/sync/operations` | miembro | OperationBatchResult | OperationBatch; 200 con resultado por operación; excepciones de registro/reactivación definidas abajo |
| GET | `A/sync/operations/{operation_id}` | actor original | OperationResult | mismo usuario, cuenta y permiso vigente sobre resultado; nuevo dispositivo propio autorizado puede recuperarlo |
| GET | `A/sync/changes` | miembro | ChangePage | posición incremental obligatoria desde snapshot o última descarga; cursor de sync, nunca OFFSET |
| POST | `A/sync/snapshots` | miembro | SnapshotResponse | SnapshotRequest; 201; materialización síncrona, sin trabajo en memoria pendiente |
| GET | `A/sync/snapshots/{snapshot_id}` | creador | SnapshotResponse | misma cuenta, usuario, dispositivo, ventana y época; 410 vencido o alcance cambiado |
| GET | `A/sync/snapshots/{snapshot_id}/items` | creador | SnapshotPage | page/shows; orden materializado estable; items/total autorizado |
| DELETE | `A/sync/snapshots/{snapshot_id}` | creador | sin cuerpo | 204; libera derivado temporal; no borra negocio ni recibos |
| GET | `A/sync/events` | miembro | text/event-stream | SSE de avisos; Last-Event-ID es una pista, nunca cursor aplicado |

GET /openapi.json y GET /docs se habilitarán solo en desarrollo/prueba al existir el contrato generado, sin añadir acciones de negocio. No se presenta su estado actual como contrato v1.

## 4. Modelos públicos

### 4.1 Acceso y controles

| Modelo | Campos permitidos / forma |
|---|---|
| DeviceRegistrationRequest | deviceName, clientVersion, localSchemaVersion; no userId/deviceId/rol elegidos por el cliente. |
| TokenRotationRequest | Objeto vacío. Nuevo secreto una vez; anterior revocado en la misma transacción. |
| DeviceTokenIssued | tokenType=Bearer, accessToken, tokenId, deviceId, userId, issuedAt; sin fecha de vencimiento. Nunca se guarda accessToken en recibos o auditoría. |
| InvitationAcceptRequest | operationId; identidad destinataria procede de token. |
| InvitationAcceptanceResult | operationId,status accepted/duplicate,invitationId,accountId,membershipVersion; respuesta perdida recuperable bajo misma identidad sin nueva pertenencia. Rechazo definitivo: 409 con ApiError; no crear pertenencia para guardar un rechazo inicial. |
| AuthConfigResponse | issuer,publicClientId,audience,authorizationFlow=authorization_code,pkceMethod=S256. Sin clientSecret. |
| CapabilitiesResponse | contractVersion=1,modelRevision,operationCatalog,onlineOnlyActions,maxBatchOperations,maxBodyBytes,maxOperationBytes,maxPageSize,syncRetentionDays=90,snapshotTtlSeconds=900,recoveryRequiredCodes,defaultAppointmentWindow. Solo capacidades implementadas al publicar versión. |
| MeResponse | userId,displayName,status,oidcIssuer,oidcSubject propios y resumen de pertenencias; nunca token o credenciales. |
| AccessResponse | accountId,userId,deviceId,role owner/assistant,status,permissionEpoch,allowedActions; origen remoto, no editable offline. |
| LiveResponse / ReadyResponse | status; ready incorpora estado general de database/schema/listener, sin URI ni mensajes internos. |
| PaginatedResponse<T> | items y total (entero no negativo); esquema común existente. No incluye nextCursor ni hasMore. SnapshotPage usa la misma forma con SyncItem. |

Los demás Response proyectan los campos administrativos del diccionario con su clave y versión. AccountSummary solo id,displayName,status y rol propio. MemberResponse no expone issuer/sub o tokens. ProfessionalResponse no expone credenciales. ServiceOfferResponse incluye clave compuesta, nombre de servicio, base, override, duración efectiva y versiones de servicio/oferta. PatientProfileResponse no incluye otras fichas; documentos/contactos se obtienen por sus rutas. PatientIdentifierResponse oculta verifiedByUserId global de otra cuenta; solo estado/instante si permitido. AccountDeviceResponse solo identificador, nombre, actividad/versión reportada y estado de autorización de esta cuenta, sin otras pertenencias.

RelationshipResponse conserva el estado del vínculo para resultados/journal. PatientContactResponse añade a esa lectura patientFullName, contactFullName, phoneCode y phone vigentes de la misma cuenta; no copia documentos del contacto. Los nombres relacionados no se guardan como parte del estado sincronizado del vínculo. Las verificaciones preparadas por administración en pruebas solo acreditan conservación: no existe una acción pública para verificarlas.

Los modelos implementados de [servicios](../src/api/services/domain/services.py), [ofertas](../src/api/services/domain/offers.py) y [reglas semanales](../src/api/schedule/domain/schedule.py) son la fuente de sus esquemas generados. La oferta conserva su versión propia y serviceVersion: un cambio de catálogo actualiza la proyección y serviceVersion sin cambiar el ajuste, estado o versión propia de otra oferta. El resultado de catálogo es privado; el grupo de cada cuenta publica solo sus ofertas para members. El cálculo semanal devuelve tramos locales unidos, con fecha y zona de cuenta; no es disponibilidad completa ni reserva.

AppointmentResponse y AppointmentHistoryResponse conservan los snapshots y el actor funcional del diccionario; no incluyen intentos, tokens, SQL ni payload de otra operación. AvailabilityResponse contiene accountId,professionalId,serviceId,referenceDurationMinutes,requestedDurationMinutes y availableIntervals[{startsAt,endsAt}]; no reserva. AuditEventResponse contiene identificadores, acción/objeto, resultado, instante y correlación, sin cuerpos personales.

Los modelos de [agenda](../src/api/schedule/domain/schedule.py) y [citas](../src/api/appointments/domain/appointments.py) generan ahora sus respuestas y esquemas. Bloques globales muestran reasonCode nulo al asistente y en el journal de miembros; solo el profesional propio lo lee en GET/resultado. Disponibilidad resta ocupación real de todas las cuentas sin devolver sus datos, ajusta extremos a minutos y devuelve 422 ante extremos locales ambiguos/inexistentes. Consultar no reserva. Reprogramar conserva los nueve snapshots y la duración real, aunque cambien catálogo, dirección o zona vigentes.

### 4.2 Filtros y orden

Las consultas GET por recurso muestran la vista vigente de cada petición; no garantizan una única vista de toda una lista paginada mientras otros usuarios la editan. Inserciones o bajas entre páginas pueden desplazar resultados. Para una descarga completa coherente se usa snapshot y luego incremental; page/shows no expresan avance de sincronización.

Listas administrativas ordenan por id ascendente; relaciones por la clave compuesta del diccionario. Patients ordena por patientId, no por nombre mutable; q no cambia ese orden. Reglas/excepciones/bloqueos usan su id y repiten sus filtros en cada petición. Citas por (startsAt,id), historial por version, auditoría por (occurredAt,id). Todo orden termina en una clave única. Cambiar filtros inicia otra consulta desde page=1; no mantiene una vista anterior.

Disponibilidad exige professionalId,serviceId,from,until; durationMinutes opcional usa referencia de oferta, 1–1440. Rango máximo 31 días. Citas requieren from/until, máximo 366 días. Calendario por intersección de intervalos, no solo por inicio; no omitir cita que empieza antes y termina dentro del rango. Listados de excepciones/bloqueos requieren rango acotado a 366 días. No se ordena por fechas del cliente.

### 4.3 Matriz fija

| Capacidad | Propietario | Asistente |
|---|---|---|
| Leer datos operativos de su cuenta | Sí | Sí |
| Pacientes/contactos y citas | Sí | Sí |
| Horarios y bloqueos limitados a la consulta | Sí | Sí |
| Bloqueos globales del profesional propio | Sí | No |
| Catálogo propio, oferta y nombre profesional propio | Sí | No |
| Datos/políticas/actividad de cuenta, invitaciones y asistentes | Sí | No |
| Revocar/restaurar dispositivo dentro de cuenta | Sí | No |
| Auditoría técnica y listado del equipo | Sí | No |
| Dispositivos/tokens propios y aceptar invitación propia | Sí | Sí |

Rol owner se deriva de accounts.owner_user_id; el resto de pertenencias activas son assistant. No se persiste un rol global ni se permite cambiar propietario. Cada usuario puede tener cuentas distintas; conocer un UUID no extiende el alcance. La cuenta inactiva impide negocio; propietario global activo conserva solo lecturas mínimas y operaciones de reactivación. Un dispositivo revocado no puede restaurarse a sí mismo; otro dispositivo propietario autorizado o el operador administrativo realiza recuperación.

## 5. Operaciones y payloads

OperationBatch = {operations:[OperationEnvelope]}. OperationEnvelope = {operationId,contractVersion:1,action,entityKey,expectedVersion,payload,dependsOn?:[],occurredAtLocal?:null}. entityKey es UUID para clave simple de la tabla siguiente, u objeto con las columnas enumeradas para clave compuesta. accountId ya está fijado por la ruta y debe coincidir en cualquier referencia de payload.

Actor/dispositivo no se aceptan en payload. UUID de nuevas entidades procede del cliente para operación offline; el registro de dispositivo lo genera servidor. Para crear expectedVersion=0 y se obtiene versión 1. Cambiar requiere versión positiva actual. dependsOn tiene máximo ocho IDs del mismo actor/cuenta: ya aceptados o anteriores en el lote; dependencias futuras/ciclos/envoltura mal formada producen 422 antes de procesar. Dependencia inexistente o rechazada produce DEPENDENCY_FAILED para esa operación sin impedir independientes. Dependencia temporal pendiente produce retryable_failure sin fijar rechazo.

| Acción | entityKey | Payload (solo estos campos) | Permiso | Resultado/regla |
|---|---|---|---|---|
| UpdateAccountDetails | accountId | Patch de displayName, timeZone, locationName, locationAddress, locationCountry, locationState y locationCity. | propietario; online | No cambia kind/ownerUserId; coordina profesional y rechaza agenda incompatible. |
| UpdateAccountPolicy | accountId | noShowGraceMinutes requerido, entero 0–1440. | propietario; online | Margen se revalida al marcar ausencia; no cambia citas/historia anteriores. |
| SetAccountStatus | accountId | status active / inactive. | propietario; online | Propietario activo puede reactivar aunque cuenta esté inactiva; no borra citas. |
| CreateInvitation | invitationId nuevo | inviteeUserId requerido; rol assistant implícito. | propietario; online | Destinatario ya identificado por OIDC; vence 72 h después del instante del servidor; no correo. |
| RevokeInvitation | invitationId | Objeto vacío. | propietario; online | Solo pending no vencida; aceptación/revocación coordinadas; conserva evidencia. |
| SetMembershipStatus | userId destinatario | status active / inactive. | propietario; online | Solo asistentes ya vinculados; no transfiere propiedad ni desactiva usuario global. |
| RegisterAccountDevice | deviceId autenticado | Objeto vacío. | miembro activo; online | expectedVersion=0; registra instalación propia. Tras revocación no permite autorrestauración. |
| RevokeAccountDevice | deviceId | Objeto vacío. | propietario; online | Revoca solo en esta cuenta; no credencial ni otras cuentas. |
| RestoreAccountDevice | deviceId | Objeto vacío. | propietario; online | Exige dispositivo/usuario globales activos y pertenencia activa; no revive token global revocado. |
| UpdateProfessionalProfile | professionalId | publicName requerido. | propietario profesional | Solo perfil ligado al actor; no cambia userId; no refresca snapshots de citas. |
| RegisterPatient | patientId nuevo | fullName?, birthDate?, phoneCode?, phone?, identificationBasis?; identifiers? como lista de {id,issuingCountry,documentType,documentNumber}. | miembro | Crea patients y account_patients draft; solo identidad nueva, nunca adjunta una identidad global arbitraria. |
| UpdatePatientProfile | patientId | Patch de fullName, birthDate, phoneCode, phone, identificationBasis. | miembro | No cambia cuenta/identidad/completitud en silencio; antes de quitar requisito volver explícitamente a draft. |
| SetPatientCompletion | patientId | completionStatus draft / complete. | miembro | Valida existencia y estado de documentos/contactos; no concede permiso para citar. |
| SetPatientProfileStatus | patientId | status active / inactive. | miembro | Solo ficha de la cuenta; no estado global ni cancelación automática de citas. |
| AddPatientIdentifier | identifierId nuevo | patientId, issuingCountry=VE, documentType national_id / passport, documentNumber. | miembro | Solo identidad ya vinculada a la ficha; estado declared; sin vincular/editar/inutilizar documentos de otras identidades. |
| CreateContactPerson | contactId nuevo | fullName; phoneCode?,phone?; issuingCountry?,documentType?,documentNumber?. | miembro | Conjunto documental opcional completo; parejas telefónicas completas; status active. |
| UpdateContactPerson | contactId | Patch de los datos administrativos anteriores. | miembro | No cambia cuenta/id; coordina todas las fichas que dependen del contacto; no deja falsas complete. |
| SetContactPersonStatus | contactId | status active / inactive. | miembro | Conserva vínculos y constancias; exige resolver completitud afectada. |
| CreatePatientContactRelationship | {patientId,contactPersonId} | relationshipKind mother / father / guardian / other; isResponsibleContact=false; validFrom; validUntil?. | miembro | Ambos de la cuenta; unverified y active; no acepta marcas de comprobación. |
| UpdatePatientContactRelationship | {patientId,contactPersonId} | Patch de relationshipKind,isResponsibleContact,validFrom,validUntil. | miembro | Extremos estables; conserva verificaciones si las hubiera; no nueva comprobación ni acceso. |
| SetPatientContactRelationshipStatus | {patientId,contactPersonId} | status active / inactive. | miembro | No borra constancia; reactivar exige vigencia/completitud actuales. |
| CreateService | serviceId nuevo | professionalId,name,defaultDurationMinutes. | propietario profesional | 1–1440 minutos; profesional ligado al actor; active y versión 1. |
| UpdateService | serviceId | Patch de name,defaultDurationMinutes. | propietario profesional | Propiedad estable; no altera citas; proyecta catálogo propio solo al propietario. |
| SetServiceStatus | serviceId | status active / inactive. | propietario profesional | Inactivar impide nuevas reservas; no cancela ni altera las aceptadas. |
| OfferService | {professionalId,serviceId} | durationMinutesOverride? (nulo por defecto). | propietario profesional | Crea relación con cuenta de ruta, propiedad común comprobada y status active. |
| UpdateServiceOffer | {professionalId,serviceId} | durationMinutesOverride requerido, nulo o entero 1–1440. | propietario profesional | Nulo vuelve a base para reservas futuras; no cambia snapshots. |
| SetServiceOfferStatus | {professionalId,serviceId} | status active / inactive. | propietario profesional | Solo oferta de esta cuenta; sin cancelar citas. |
| CreateScheduleRule | ruleId nuevo | professionalId,isoWeekday,localStartMinute,localEndMinute,validFrom,validUntil?. | miembro | Regla de cuenta; active; límites y UQ con NULLS NOT DISTINCT del esquema. |
| UpdateScheduleRule | ruleId | Patch de isoWeekday,localStartMinute,localEndMinute,validFrom,validUntil. | miembro | No cambia profesional/cuenta; rechaza incompatibilidad con cita vigente. |
| SetScheduleRuleStatus | ruleId | status active / inactive. | miembro | Conserva fila; valida disponibilidad después del cambio. |
| CreateScheduleException | exceptionId nuevo | professionalId,localDate,kind closed / replacement,localStartMinute?,localEndMinute?. | miembro | Una por fecha; closed sin extremos; replacement con ambos. |
| UpdateScheduleException | exceptionId | Patch de localDate,kind,localStartMinute,localEndMinute. | miembro | No cambia profesional/cuenta; patch completo resultante válido y UQ. |
| SetScheduleExceptionStatus | exceptionId | status active / inactive. | miembro | Volver a habitual debe conservar citas compatibles. |
| CreateScheduleBlock | blockId nuevo | professionalId,accountId (cuenta de ruta o nulo),startsAt,endsAt,reasonCode. | miembro; global solo profesional propio | reasonCode vacation/administrative/unavailable; sin motivo libre o clínico; intervalo finito. |
| UpdateScheduleBlock | blockId | Patch de startsAt,endsAt,reasonCode. | miembro; global solo profesional propio | Cuenta/profesional/alcance estables; no transforma un bloqueo limitado en global. |
| SetScheduleBlockStatus | blockId | status active / inactive. | miembro; global solo profesional propio | Coordina por profesional; no cancela reservas. |
| CreateAppointment | appointmentId nuevo | patientId,professionalId,serviceId,responsibleContactId?,startsAt,endsAt. | miembro | 1–1440 minutos enteros; ficha complete; snapshots/estado/actor se obtienen en servidor. |
| ConfirmAppointment | appointmentId | Objeto vacío. | miembro | scheduled a confirmed; instante del servidor; versión esperada. |
| RescheduleAppointment | appointmentId | startsAt,endsAt. | miembro | scheduled/confirmed a scheduled; conserva duración efectiva y referencias/snapshots; confirmedAt nulo. |
| CancelAppointment | appointmentId | changeReason? administrativo. | miembro | scheduled/confirmed a cancelled; conserva intervalo e historia y libera ocupación. |
| CompleteAppointment | appointmentId | changeReason? administrativo. | miembro | scheduled/confirmed a completed; ahora >= startsAt; conserva intervalo. |
| MarkAppointmentNoShow | appointmentId | changeReason? administrativo. | miembro | scheduled/confirmed a no_show; ahora >= startsAt + margen vigente; acción manual. |

En CreateInvitation el destinatario comunica previamente su propio userId (GET /v1/me); no hay directorio global. El identificador de invitación sirve como código de un solo uso, pero solo su destinatario autenticado puede aceptarlo. La posesión del código no concede acceso. No se guarda un enlace personal o secreto de invitación innecesario. Destinatario inexistente produce NOT_FOUND sin revelar información personal.

SetAccountStatus, SetMembershipStatus y controles de dispositivo no otorgan autorización para saltar el control vigente: sus excepciones solo permiten al propietario activo restaurar ámbito administrativo desde una instalación válida. El primer RegisterAccountDevice exige token global válido, pertenencia y cuenta activas, clave igual al dispositivo autenticado; no acepta otro deviceId. El registro es la única operación de cuenta que puede ejecutarse sin una autorización de dispositivo previa, además de lecturas mínimas señaladas.

Cambios de contacto o vínculos que afectan varias fichas deben revisar todas bajo coordinación; si dejan una ficha complete sin base, rechazar COMPLETENESS_CONFLICT. El cliente primero cambia expresamente las fichas necesarias a draft con sus propias versiones y dependencias; no hay democión silenciosa de terceros.

Una ficha con minor_without_document se valida a la fecha local del inicio de la cita en zona de cuenta. Para nacido un 29 de febrero, el cumpleaños administrativo en año no bisiesto es el 1 de marzo (comparación de mes/día, sin guardar edad). Menos de 18 es criterio administrativo aprobado, no prueba legal. own_document admite documento declared o verified y teléfono propio o responsable con teléfono; documento invalidated no sirve. No exigir inspección física.

Confirmar ya confirmed bajo otra operationId devuelve INVALID_STATE_TRANSITION; repetir la misma operación devuelve duplicate. Estados terminales no se reabren. Cambiar catálogo o local no altera snapshots previos. Cambiar zona o agenda debe rechazar incompatibilidad con citas scheduled/confirmed sin recalificar terminales ni mover instantes.

## 6. Resultados, idempotencia y errores

OperationBatchResult = {results:[OperationResult],correlationId}. OperationResult = {operationId,status,entityVersion:null|int,state:null|proyección_permitida,error:null|ApiError,originalResult:null|resultado_original}. originalResult solo aparece en duplicate y no se anida recursivamente. La versión de estado actual de conflicto no se confunde con versión de resultado original. Posición de una escritura, si se muestra como dato de correlación, nunca es cursor aplicado.

Clave idempotente (accountId,actorUserId,operationId); el dispositivo del primer intento queda como evidencia, no impide recuperar resultado desde nueva instalación del mismo actor autorizada. Huella SHA-256 de JSON canónico UTF-8 con claves ordenadas, separación compacta, formatos tipados del envoltorio y payload y todos los campos semánticos. No incluir el token, correlación ni dispositivo de transporte. Cambiar payload, acción, versión esperada, dependencias o tiempo local de una misma operación es conflicto de contenido. Campos ausentes opcionales se normalizan a los valores documentados antes de la huella. Payload inválido se canoniza como JSON recibido para conservar su rechazo, sin aplicar coerciones silenciosas.

Efecto, versiones, historia pertinente, auditoría, recibo y cambios se confirman juntos. Rechazo definitivo autorizado puede guardar solo recibo/auditoría, sin cambio de negocio. Fallo temporal revierte y permite reintentar la misma clave, sin reservarla definitivamente. Si se requiere rollback de una restricción, la coordinación conserva el resultado de rechazo en el límite acordado; nunca confirma parte del efecto. Un reintento reautoriza antes de consultar el recibo.

Resultado completo al menos 90 días. Después se retira state/error detallado y se conserva clave/huella/resultado mínimo; resultado vencido 410 RESULT_EXPIRED, nunca nueva ejecución. No decidir caducidad por fecha del UUID ni occurredAtLocal. La misma clave con otra huella sigue siendo IDEMPOTENCY_CONFLICT. Intención no enviada antes puede evaluarse de nuevo con permiso y versión actuales; el consumidor no crea otra identidad para repetir un efecto desconocido.

ApiError = {code,message,correlationId,details:[]}; details solo ubicaciones de campo/códigos seguros, no token, valor personal, SQL o traza. Error HTTP 422 usa esa forma, no incluye input personal. Mensaje humano no es clave contractual.

| HTTP / resultado | Código / condición |
|---|---|
| 200 / accepted | Efecto y resultado confirmados. |
| 200 / duplicate | Resultado original recuperado; un rechazo no se convierte en aceptación. |
| 200 / conflict | VERSION_CONFLICT, SLOT_UNAVAILABLE, IDEMPOTENCY_CONFLICT. |
| 200 / rejected | VALIDATION_ERROR, INVALID_STATE_TRANSITION, NO_CHANGES, COMPLETENESS_CONFLICT, DEPENDENCY_FAILED, UNSUPPORTED_OPERATION o regla de negocio. |
| 200 / retryable_failure | TEMPORARY_FAILURE, DEPENDENCY_UNAVAILABLE o dependencia temporal; sin efecto confirmado. |
| 401 | AUTHENTICATION_REQUIRED / credencial inválida o revocada. |
| 403 | PERMISSION_DENIED / dispositivo no habilitado o acción no permitida en ámbito conocido. |
| 404 | NOT_FOUND para objeto no visible o inexistente; no revela otra cuenta. |
| 409 | Rechazo de aceptación de invitación: INVALID_STATE_TRANSITION, NO_CHANGES o IDEMPOTENCY_CONFLICT. Los conflictos del lote conservan HTTP 200 y resultado por operación. |
| 410 | CURSOR_EXPIRED, SNAPSHOT_EXPIRED, SNAPSHOT_SCOPE_CHANGED, RESULT_EXPIRED; recuperación explícita. |
| 413 | REQUEST_TOO_LARGE, antes de efectos. |
| 422 | VALIDATION_ERROR estructural antes de procesar lote. |
| 429 | RATE_LIMITED con Retry-After; antes de procesar. |
| 503 | DEPENDENCY_UNAVAILABLE / TEMPORARY_FAILURE antes de aceptación o sin resultado conocido. |

Desconocer si hubo commit no permite declarar rechazo definitivo: consultar/reintentar la misma identidad. En esta etapa no hay proveedores externos de efectos de negocio.

## 7. Descarga y recuperación

ChangePage = {groups:[ChangeGroup],nextCursor,hasMore}. ChangeGroup = {groupId,operationId,changes:[{entityType,entityKey,entityVersion,changeKind:upsert|remove,state}],acceptedAt}. state es proyección autorizada, no fila SQL arbitraria. La posición interna del grupo no es secuencia asignada antes del commit. Filtrar audiencia no impide avanzar sobre grupos invisibles al usuario; no se devuelve su contenido.

Orden de aceptación: controles de usuario/credencial, profesionales, pacientes y cuentas, cada conjunto ordenado por identificador; luego filas de negocio/recibo. Releer tras esperas y reiniciar si cambia conjunto. Todo escritor que afecta una proyección de cuenta bloquea su account_sync_heads hasta commit; incremento transaccional por operación. Un cambio con varias entidades ocupa un grupo y no se corta al paginar. Para globales permitidos se coordinan las cuentas afectadas en el mismo orden, con bloqueo previo del profesional/paciente que estabiliza sus referencias. Estado aceptado y proyección/versiones se conservan juntos.

Audiencia de change_log: members para datos operativos visibles a ambos roles; owner para catálogo privado no ofrecido y equipo/auditoría administrativa si corresponde. Snapshots y páginas aplican la misma audiencia. Ofertar un servicio publica la proyección mínima para miembros, nunca acceso al resto del catálogo. La época de acceso cambia al cambiar pertenencias o autorizaciones, invalidando capturas/cursores de ámbito antiguo; respuesta permite recuperar desde nueva vista sin filtrar datos.

SnapshotRequest = {appointmentsFrom?:date,appointmentsUntil?:date}. Valores por defecto: hoy local menos 30 días y hoy más 181 días como límite exclusivo, incluyendo el día hoy+180. Ventana máxima 366 días. SnapshotResponse = {snapshotId,accountId,contractVersion,modelRevision,window,baseCursor,expiresAt,itemCount}. SnapshotPage = PaginatedResponse<SyncItem> = {items:[SyncItem],total}. SyncItem identifica entityType,entityKey,entityVersion y state tipado. El total y itemCount solo cuentan elementos permitidos de esa captura.

Capturar bajo REPEATABLE READ en una sola lectura/materialización, sin red dentro, datos y baseCursor de esa vista. No mantener transacción entre peticiones; almacenar temporal con vencimiento de 15 minutos. Cualquier cambio de acceso invalida la captura; solo creador/dispositivo autorizado la descarga. Sus elementos se ordenan por la posición materializada única; page/shows aplica LIMIT/OFFSET a ese conjunto inmutable. Repetir snapshot, page y shows devuelve los mismos elementos mientras siga vigente y autorizado. DELETE solo libera derivado temporal; no borra pendientes locales ni crea cambio de negocio.

SnapshotResponse.window incluye las fechas locales, timeZone y límites UTC startsAt/endsAt resueltos al crear. La captura y el cursor firmado conservan esos valores aunque después cambie la zona de la cuenta. No recalcular el alcance de una página o delta desde el estado nuevo de la cuenta; otra ventana requiere nueva captura explícita.

Contenido: datos administrativos operativos de cuenta; fichas activas y draft; contactos y vínculos pertinentes; servicios ofrecidos, reglas/excepciones/bloqueos de ventana; citas que intersectan ventana e historia de esas citas; referencias inactivas necesarias para interpretarlas. Propietario incluye catálogo propio no ofrecido y metadatos de equipo permitidos; asistente no. No copia historia de citas fuera de ventana ni datos de otras cuentas. Las consultas online de historia no cambian el cursor. Una proyección de ocupación global solo expresa indisponibilidad, sin cita/paciente/motivo ajeno.

Cambios fuera de ventana siguen avanzando posición autorizada; cuando una cita deja de pertenecer a la vista emitir remove (retirada de ventana, no borrado real). Cambiar ventana exige nueva captura, conservando Outbox/intentiones del consumidor. Solo el consumidor aplica página y cursor juntos en su SQLite; aquí no se implementa Rust.

Retener grupos completos y resultados completos al menos 90 días desde aceptación; conservar frontera de retención y recibo mínimo. Cursor anterior a la frontera obliga nuevo snapshot. No purgar historia funcional o auditoría en esta etapa. Mantenimiento elimina temporales/resultados vencidos en lotes pequeños, sin borrar el recibo que evita repetir efectos.

## 8. Canal de avisos

GET A/sync/events usa EventSourceResponse/ServerSentEvent de FastAPI instalado; no nueva biblioteca SSE. Emite changes_available con cursor de referencia para solicitar datos, access_revoked sin datos y heartbeat con tiempo del servidor. Heartbeat cada 15 s y revisión de posición/acceso. Reconexión sugerida 3 s; Last-Event-ID no prueba aplicación ni permite saltar descarga.

LISTEN/NOTIFY por proceso, conexión dedicada de escucha, payload mínimo de cuenta/posición sin pacientes. Primero confirmar LISTEN, después comprobar journal; al recuperar listener comparar de nuevo. NOTIFY se registra en la misma transacción y se entrega tras commit. Si se pierde la señal, posición persistida más reconexión/heartbeat recuperan. No es cola durable ni prueba de entrega externa única.

No mantener sesión SQL por conexión SSE. Revalidar al emitir y en heartbeat con transacción breve; revocación avisa/cierra, futuro intercambio rechaza. Máximo dos conexiones por dispositivo y cuenta; buffer de aviso agrupable por cuenta, capacidad uno para hint pendiente. Consumidor lento se desconecta y recupera por cursor; no bloquear aceptación por red del cliente. Listener perdido implica preparación degradada y recuperación, no pérdida del registro.

Objetivo local: p95 de commit a aviso menor de dos segundos con diez conexiones y dos procesos de API, sobre datos ficticios. Registrar configuración y medidas; no promesa de producción. API sirve páginas aunque el canal de avisos se recupere, pero preparación informa la degradación esencial conforme al plan.

## 9. Ejemplo ficticio y comprobación

Ejemplo de creación (el actor/dispositivo proceden del token, no del JSON):

```json
{"operations":[{"operationId":"019a1234-0000-7000-8000-000000000001","contractVersion":1,"action":"CreateAppointment","entityKey":"019a1234-0000-7000-8000-000000000002","expectedVersion":0,"payload":{"patientId":"019a1234-0000-7000-8000-000000000003","professionalId":"019a1234-0000-7000-8000-000000000004","serviceId":"019a1234-0000-7000-8000-000000000005","startsAt":"2026-10-26T13:00:00Z","endsAt":"2026-10-26T13:45:00Z"},"dependsOn":[]}]}
```

La API acepta solo si existen las referencias autorizadas, completas y operativas y el intervalo está libre. El ejemplo es de formato; no demuestra una ruta ni datos creados.

Matriz futura: OIDC emisor/audiencia/ID token; token/dispositivo/miembro revocados; invitación ajena/vencida/usada; lecturas/errores/resultados/páginas de otra cuenta; duplicado concurrente y cuerpo distinto; respuesta perdida; dependencia fallida y lote independiente; menor y cumpleaños 18; responsables compartidos y completitud; servicio ajeno y duración conservada; medianoche/zona ambigua; cita simultánea y cita frente a bloqueo; versión antigua y transición inválida; historia futura/hueco/reescritura; commits invertidos y grupos completos; snapshot concurrente y frontera; vencimiento 90 días; SSE dos procesos/caída/consumidor lento/revocación; secretos y PII ausentes de logs. Estas pruebas se ejecutan en las tareas del plan, no en C01.

Fuentes de API ya contrastadas durante planificación: [lifespan](https://fastapi.tiangolo.com/advanced/events/), [SSE](https://fastapi.tiangolo.com/tutorial/server-sent-events/), [HTTPX y lifespan en pruebas](https://fastapi.tiangolo.com/advanced/async-tests/), [SQLAlchemy 2.1 async](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html), [NOTIFY](https://www.postgresql.org/docs/18/sql-notify.html), [LISTEN](https://www.postgresql.org/docs/18/sql-listen.html), [Keycloak OIDC](https://www.keycloak.org/securing-apps/oidc-layers). Volver a comprobar versión y patrón antes de codear; no se instalan dependencias en este bloque.

