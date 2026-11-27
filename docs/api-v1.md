# Contrato de diseño HTTP v1 para escritorio

**Versión de diseño:** 1.3. **Fecha:** 2026-11-22. **Estado:** vademecum implementado para revisión C05. Los contratos generados contienen 117 rutas, 205 esquemas y 104 acciones por lote, con origen, HEAD y huellas reproducibles. `contractVersion=1` y `modelRevision=api-v1.3`. Consumidores y producción conservan sus límites.

Este documento conserva explicación de transporte, permisos y recuperación. [contracts.md](contracts.md) fija propiedad y principios; [database-schema.md](database-schema.md) posee columnas, tipos y restricciones físicas. Los esquemas Pydantic de domain, derivados del BaseModel del proyecto, son la fuente de OpenAPI/JSON Schema exportados por scripts/export_contracts.py. Los generados identifican origen/versión/huella y no se editan a mano. La [guía Rust](rust-api-guide.md) explica su uso y enlaza ejemplos comprobados. Los casos de uso no dependen de FastAPI ni acceden directamente a SQLAlchemy.

## 1. Alcance y autenticación

Solo consultas independientes, un profesional y asistentes. Sin modificación de Rust, Hub, clínicas, comunicaciones, espera, analítica, datos reales o producción. No se exponen CRUD global de usuarios, contraseñas, concesiones Hub, búsqueda/fusión/corrección global de pacientes, verificación de identidad/representación o reapertura/cambio de referencias de citas.

**Aclaración documental del 2026-11-14:** [D11](decisions.md#d11--interfaz-del-hub-y-servidor-en-nightingale-api) acuerda el futuro Hub: interfaz web en su repositorio y todo su servidor en API. Este contrato actual no incluye endpoints públicos de micrositios ni acciones del paciente. Las lecturas públicas actuales de salud, capacidades y configuración OIDC no sirven como contrato de publicación de cuentas, profesionales o servicios. Las rutas internas y operaciones de citas conservan el acceso del personal.

El futuro micrositio tendrá plantillas para médico independiente y clínica/centro, sin cuentas de paciente, inicio de sesión o permisos del personal para leer información destinada a publicación. La gestión privada de una cita usará acceso limitado sin credenciales del personal: consulta permitida, confirmación, cancelación según reglas, solicitud de reprogramación y consulta de resultado. No permitirá crear o reservar citas, explorar disponibilidad para elegir otro horario ni marcar ausencias. Pedir reprogramación conserva estado, horario y confirmación, sin reservar otro intervalo; el personal decide y API aplica el cambio. La presentación pública de clínicas no amplía la gestión interna, las sedes o el escritorio de v1. Mecanismo del enlace, proyecciones y formas HTTP siguen pendientes en [la especificación §5](nightingale-api.md#5-integración-con-patient-hub); no se añaden a este catálogo ni a los artefactos generados.

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
| GET | `A/members/{user_id}/clinical-permissions` | propietario | MemberClinicalPermissionsResponse | niveles clínicos configurados y versión de pertenencia |
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
| GET | `A/patients/{patient_id}/encounters` | atenciones `read`/`read_write` | PaginatedResponse<PatientEncounterResponse> | filtros recordStatus/from/until; orden occurredAt,id |
| GET | `A/patients/{patient_id}/encounters/{encounter_id}` | atenciones `read`/`read_write` | PatientEncounterResponse | solo esa cuenta/ficha |
| GET | `A/patients/{patient_id}/encounters/{encounter_id}/history` | atenciones `read`/`read_write` | PaginatedResponse<PatientEncounterHistoryResponse> | versión ascendente, afterVersion |
| GET | `A/patients/{patient_id}/last-visit` | atenciones `read`/`read_write` | LastVisitResponse | última atención válida de cuenta/paciente |
| GET | `A/patients/{patient_id}/declared-medications` | medicación declarada `read`/`read_write` | PaginatedResponse<DeclaredMedicationResponse> | recordStatus, reviewStatus, sourceType; cuenta/ficha autorizadas |
| GET | `A/patients/{patient_id}/declared-medications/{medication_id}` | medicación declarada `read`/`read_write` | DeclaredMedicationResponse | solo esa cuenta/ficha |
| GET | `A/patients/{patient_id}/declared-medications/{medication_id}/history` | medicación declarada `read`/`read_write` | PaginatedResponse<DeclaredMedicationHistoryResponse> | afterVersion, versión ascendente |
| GET | `A/patients/{patient_id}/notes` | notas `read`/`read_write` | PaginatedResponse<PatientNoteResponse> | recordStatus/encounterId; orden createdAt,id |
| GET | `A/patients/{patient_id}/notes/{note_id}` | notas `read`/`read_write` | PatientNoteResponse | solo esa cuenta/ficha |
| GET | `A/patients/{patient_id}/notes/{note_id}/history` | notas `read`/`read_write` | PaginatedResponse<PatientNoteHistoryResponse> | versión ascendente, afterVersion |
| GET | `A/patients/{patient_id}/measurements` | mediciones `read`/`read_write` | PaginatedResponse<PatientMeasurementResponse> | kind/recordStatus/from/until; orden measuredAt,id |
| GET | `A/patients/{patient_id}/measurements/summary` | mediciones `read`/`read_write` | MeasurementSummaryResponse | última toma válida por tipo |
| GET | `A/patients/{patient_id}/measurements/{measurement_id}` | mediciones `read`/`read_write` | PatientMeasurementResponse | incluye edad derivada y versión de ficha |
| GET | `A/patients/{patient_id}/measurements/{measurement_id}/history` | mediciones `read`/`read_write` | PaginatedResponse<PatientMeasurementHistoryResponse> | versión ascendente, afterVersion |
| GET | `A/patients/{patient_id}/immunizations` | vacunas `read`/`read_write` | PaginatedResponse<PatientImmunizationResponse> | recordKind/recordStatus; orden occurrenceDate,id |
| GET | `A/patients/{patient_id}/immunizations/{immunization_id}` | vacunas `read`/`read_write` | PatientImmunizationResponse | fuente, precisión y detalles opcionales |
| GET | `A/patients/{patient_id}/immunizations/{immunization_id}/history` | vacunas `read`/`read_write` | PaginatedResponse<PatientImmunizationHistoryResponse> | versión ascendente, afterVersion |
| GET | `A/patients/{patient_id}/antecedents` | antecedentes `read`/`read_write` | PaginatedResponse<PatientAntecedentResponse> | category/recordStatus; orden createdAt,id |
| GET | `A/patients/{patient_id}/antecedents/{antecedent_id}` | antecedentes `read`/`read_write` | PatientAntecedentResponse | relato, fuente, fecha y persona relacionada |
| GET | `A/patients/{patient_id}/antecedents/{antecedent_id}/history` | antecedentes `read`/`read_write` | PaginatedResponse<PatientAntecedentHistoryResponse> | versión ascendente, afterVersion |
| GET | `A/patients/{patient_id}/clinical-history` | secciones legibles | PaginatedResponse<ClinicalHistoryEntry> | Referencias sin contenido; filtros por fuente antes de total/página |
| GET | `A/patients/{patient_id}/clinical-profile` | perfil `read`/`read_write` | ClinicalProfileResponse | versión 0 sin fila, sin escritura |
| GET | `A/patients/{patient_id}/clinical-profile/history` | perfil `read`/`read_write` | PaginatedResponse<ClinicalProfileHistoryResponse> | versión ascendente, afterVersion opcional |
| GET | `A/patients/{patient_id}/birth-date-changes` | miembro | PaginatedResponse<PatientBirthDateChangeResponse> | solo cambios desde esta entrega |
| GET | `A/patients/{patient_id}/conditions` | condiciones `read`/`read_write` | PaginatedResponse<PatientConditionResponse> | filtros y orden id |
| GET | `A/patients/{patient_id}/conditions/{condition_id}` | condiciones `read`/`read_write` | PatientConditionResponse | solo esa cuenta/ficha |
| GET | `A/patients/{patient_id}/conditions/{condition_id}/history` | condiciones `read`/`read_write` | PaginatedResponse<PatientConditionHistoryResponse> | versión ascendente |
| GET | `A/patients/{patient_id}/clinical-sections/conditions` | condiciones `read`/`read_write` | ClinicalSectionReviewResponse | revisión actual |
| GET | `A/patients/{patient_id}/clinical-sections/conditions/history` | condiciones `read`/`read_write` | PaginatedResponse<ClinicalSectionReviewHistoryResponse> | versión ascendente |
| GET | `A/patients/{patient_id}/allergy-intolerances` | alergias `read`/`read_write` | PaginatedResponse<PatientAllergyIntoleranceResponse> | filtros y orden id |
| GET | `A/patients/{patient_id}/allergy-intolerances/{allergy_id}` | alergias `read`/`read_write` | PatientAllergyIntoleranceResponse | solo esa cuenta/ficha |
| GET | `A/patients/{patient_id}/allergy-intolerances/{allergy_id}/history` | alergias `read`/`read_write` | PaginatedResponse<PatientAllergyIntoleranceHistoryResponse> | versión ascendente |
| GET | `A/patients/{patient_id}/clinical-sections/allergies` | alergias `read`/`read_write` | ClinicalSectionReviewResponse | revisión actual |
| GET | `A/patients/{patient_id}/clinical-sections/allergies/history` | alergias `read`/`read_write` | PaginatedResponse<ClinicalSectionReviewHistoryResponse> | versión ascendente |
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

GET /openapi.json, GET /docs y GET /redoc se habilitan solo en desarrollo/prueba. Producción no registra esas rutas. La ruta de bienvenida se conserva fuera del contrato público generado, sin acciones de negocio.

| GET | `A/patients/{patient_id}/declared-medications` | medicación declarada read | PaginatedResponse<DeclaredMedicationResponse> | filtros reviewStatus, sourceType, recordStatus; orden (createdAt,id) |
| GET | `A/patients/{patient_id}/declared-medications/{medication_id}` | medicación declarada read | DeclaredMedicationResponse | detalle; objeto ajeno = ausencia |
| GET | `A/patients/{patient_id}/declared-medications/{medication_id}/history` | medicación declarada read | PaginatedResponse<DeclaredMedicationHistoryResponse> | versiones con acción/actor/operación |
| GET | `A/patients/{patient_id}/care-plans` | planes read | PaginatedResponse<CarePlanResponse> | filtros planStatus, recordStatus |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}` | planes read | CarePlanResponse | detalle del plan |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/history` | planes read | PaginatedResponse<CarePlanHistoryResponse> | historia del plan |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/goals` | planes read | PaginatedResponse<CarePlanGoalResponse> | objetivos del plan |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/goals/{goal_id}` | planes read | CarePlanGoalResponse | detalle del objetivo |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/goals/{goal_id}/history` | planes read | PaginatedResponse<CarePlanGoalHistoryResponse> | historia del objetivo |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/actions` | planes read | PaginatedResponse<CarePlanActionResponse> | acciones del plan |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/actions/{action_id}` | planes read | CarePlanActionResponse | detalle de la acción |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/actions/{action_id}/history` | planes read | PaginatedResponse<CarePlanActionHistoryResponse> | historia de la acción |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/reviews` | planes read | PaginatedResponse<CarePlanReviewResponse> | revisiones del plan |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/reviews/{review_id}` | planes read | CarePlanReviewResponse | detalle de la revisión |
| GET | `A/patients/{patient_id}/care-plans/{plan_id}/reviews/{review_id}/history` | planes read | PaginatedResponse<CarePlanReviewHistoryResponse> | historia de la revisión |
| GET | `A/patients/{patient_id}/diagnostic-reports` | informes read | PaginatedResponse<DiagnosticReportResponse> | filtros reportKind, reportStatus, recordStatus, rango sampleDate |
| GET | `A/patients/{patient_id}/diagnostic-reports/{report_id}` | informes read | DiagnosticReportResponse | detalle del informe |
| GET | `A/patients/{patient_id}/diagnostic-reports/{report_id}/history` | informes read | PaginatedResponse<DiagnosticReportHistoryResponse> | historia del informe |
| GET | `A/patients/{patient_id}/diagnostic-reports/{report_id}/results` | informes read | PaginatedResponse<DiagnosticReportResultResponse> | resultados vigentes |
| GET | `A/patients/{patient_id}/report-attachments/{attachment_id}` | informes read | ReportAttachmentResponse | metadatos sin URL ni storageKey |
| GET | `A/patients/{patient_id}/report-attachments/{attachment_id}/content` | informes read | bytes | descarga reautorizada; bytes fuera de sync |
| GET | `A/specialty-templates` | especialidad read | PaginatedResponse<SpecialtyTemplateResponse> | plantillas de la cuenta |
| GET | `A/specialty-templates/{template_id}` | especialidad read | SpecialtyTemplateResponse | plantilla con campos de su versión |
| GET | `A/specialty-templates/{template_id}/history` | especialidad read | PaginatedResponse<SpecialtyTemplateHistoryResponse> | versiones de la plantilla |
| GET | `A/patients/{patient_id}/specialty-records` | especialidad read | PaginatedResponse<SpecialtyRecordResponse> | registros con versión de plantilla |
| GET | `A/patients/{patient_id}/specialty-records/{record_id}` | especialidad read | SpecialtyRecordResponse | detalle del registro |
| GET | `A/patients/{patient_id}/specialty-records/{record_id}/history` | especialidad read | PaginatedResponse<SpecialtyRecordHistoryResponse> | historia del registro |
| GET | `A/patients/{patient_id}/dental-findings` | especialidad read | PaginatedResponse<DentalFindingResponse> | filtros toothFdi, findingKind, findingStatus; orden (toothFdi,surface,id) |
| GET | `A/patients/{patient_id}/dental-findings/{finding_id}` | especialidad read | DentalFindingResponse | detalle del hallazgo |
| GET | `A/patients/{patient_id}/dental-findings/{finding_id}/history` | especialidad read | PaginatedResponse<DentalFindingHistoryResponse> | historia del hallazgo |
| GET | `A/patients/{patient_id}/dental-findings/{finding_id}/treatments` | especialidad read | PaginatedResponse<DentalTreatmentResponse> | actuaciones del hallazgo |
| GET | `A/patients/{patient_id}/dental-treatments/{treatment_id}` | especialidad read | DentalTreatmentResponse | detalle de la actuación |
| GET | `A/patients/{patient_id}/dental-treatments/{treatment_id}/history` | especialidad read | PaginatedResponse<DentalTreatmentHistoryResponse> | historia de la actuación |
| GET | `A/patients/{patient_id}/analytics/series` | mediciones read | SeriesResponse | solo válidos, orden por fecha del hecho; page/shows y total |
| GET | `A/patients/{patient_id}/analytics/growth` | mediciones read | GrowthResponse | z LMS o limitExplanation; sin diagnóstico |

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
| AccessResponse | accountId,userId,deviceId,role owner/assistant,status,permissionEpoch,allowedActions,clinicalPermissions; origen remoto, no editable offline. |
| MemberClinicalPermissionsResponse | userId,clinicalPermissions (modelo vigente),membershipVersion. |
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
| CreatePatientEncounter | encounterId nuevo | patientId, appointmentId?, attendingProfessionalId, assistantUserId?, occurredAt?, endedAt?, capturedAtLocal?, motivo/fuente y contenido clínico opcional. | atenciones read_write | Atención real sin cierre; varias por cita; vínculos de la misma ficha. |
| UpdatePatientEncounter | encounterId | Patch de tiempos/captura/contenido/fuente/correctionReason; versión actual. | atenciones read_write | No cambia ficha/cita/profesional; sin reasignación. |
| InvalidatePatientEncounter | encounterId | correctionReason opcional; versión actual. | atenciones read_write | Anulación terminal entered-in-error. |
| CreatePatientNote | noteId nuevo | patientId, encounterId?, body, capturedAtLocal?. | notas read_write | Nota independiente/vinculada; sin diagnóstico o última visita derivados. |
| UpdatePatientNote | noteId | Patch de body, capturedAtLocal, correctionReason; versión actual. | notas read_write | Ausencia conserva; NO_CHANGES sin versión. |
| InvalidatePatientNote | noteId | correctionReason opcional; versión actual. | notas read_write | Anulación terminal e historia conservada. |
| RecordPatientMeasurement | measurementId nuevo | patientId, encounterId?, kind, measuredAt?, capturedAtLocal?, method?, bodySite?, valores según tipo, unit fija. | mediciones read_write | Nueva toma con ID nuevo; cinco formas y rangos cerrados. |
| CorrectPatientMeasurement | measurementId | Patch de tiempos/captura/método/sitio/valores/correctionReason; versión actual. | mediciones read_write | No cambia tipo/unidad/ficha; conserva historia. |
| InvalidatePatientMeasurement | measurementId | correctionReason opcional; versión actual. | mediciones read_write | Anulación terminal fuera de serie vigente. |
| RecordPatientImmunization | immunizationId nuevo | patientId, encounterId?, vaccineName, occurrenceDate, recordKind, sourceType, captura y detalles opcionales. | vacunas read_write | administered_here exige atención válida; declaración no prueba administración. |
| UpdatePatientImmunization | immunizationId | Patch de vacuna/fecha/tipo/fuente/captura/detalles/correctionReason; versión actual. | vacunas read_write | Conserva historia; no cambia ficha/atención. |
| InvalidatePatientImmunization | immunizationId | correctionReason opcional; versión actual. | vacunas read_write | Anulación terminal. |
| CreatePatientAntecedent | antecedentId nuevo | patientId, encounterId?, category, content, relatedPersonDescription?, occurrenceDate?, sourceType, capturedAtLocal?. | antecedentes read_write | family exige persona relacionada; sin condición derivada. |
| UpdatePatientAntecedent | antecedentId | Patch de contenido/persona/fecha/fuente/captura/correctionReason; versión actual. | antecedentes read_write | Conserva contexto e historia; valida estado combinado. |
| InvalidatePatientAntecedent | antecedentId | correctionReason opcional; versión actual. | antecedentes read_write | Anulación terminal. |
| DeclarePatientMedication | medicationId nuevo | patientId, encounterId?, medicationName, sourceType, fechas parciales y detalles opcionales; ver §12.4. | declared_medications read_write | Fuente declarada; sin receta, consumo o adherencia derivados. |
| UpdatePatientDeclaredMedication | medicationId | Patch validado de datos declarados y correctionReason. | declared_medications read_write | Conserva ficha/atención e historia. |
| ReviewPatientDeclaredMedication | medicationId | Objeto vacío. | declared_medications read_write | Revisor autenticado; conserva fuente declarada. |
| InvalidatePatientDeclaredMedication | medicationId | correctionReason opcional. | declared_medications read_write | entered-in-error terminal, sin borrar historia. |
| CreateInvitation | invitationId nuevo | inviteeUserId requerido; rol assistant implícito. | propietario; online | Destinatario ya identificado por OIDC; vence 72 h después del instante del servidor; no correo. |
| RevokeInvitation | invitationId | Objeto vacío. | propietario; online | Solo pending no vencida; aceptación/revocación coordinadas; conserva evidencia. |
| SetMembershipStatus | userId destinatario | status active / inactive. | propietario; online | Solo asistentes ya vinculados; no transfiere propiedad ni desactiva usuario global. |
| SetMemberClinicalPermissions | userId destinatario | clinicalPermissions con las secciones implementadas del catálogo; cada nivel none/read/read_write. | propietario; online | Solo asistentes; versión/época/recibo/auditoría/journal juntos; conserva estado y demás datos de pertenencia. |
| RegisterAccountDevice | deviceId autenticado | Objeto vacío. | miembro activo; online | expectedVersion=0; registra instalación propia. Tras revocación no permite autorrestauración. |
| RevokeAccountDevice | deviceId | Objeto vacío. | propietario; online | Revoca solo en esta cuenta; no credencial ni otras cuentas. |
| RestoreAccountDevice | deviceId | Objeto vacío. | propietario; online | Exige dispositivo/usuario globales activos y pertenencia activa; no revive token global revocado. |
| UpdateProfessionalProfile | professionalId | publicName requerido. | propietario profesional | Solo perfil ligado al actor; no cambia userId; no refresca snapshots de citas. |
| RegisterPatient | patientId nuevo | fullName?, birthDate?, phoneCode?, phone?, identificationBasis?; identifiers? como lista de {id,issuingCountry,documentType,documentNumber}. | miembro | Crea patients y account_patients draft; solo identidad nueva, nunca adjunta una identidad global arbitraria. |
| UpdatePatientProfile | patientId | Patch de fullName, birthDate, phoneCode, phone, identificationBasis. | miembro | No cambia cuenta/identidad/completitud en silencio; antes de quitar requisito volver explícitamente a draft. |
| SetPatientSexAtBirth | patientId | sexAtBirth requerido y anulable, sourceType=unknown; versión de perfil, 0 inicial. | perfil read_write | Primera exige valor no nulo; posterior admite nulo. Conserva historia y calcula edad desde nacimiento. |
| CreatePatientCondition | conditionId nuevo | patientId, name, clinicalStatus=active, verificationStatus=unconfirmed, onsetDate?, abatementDate?, sourceType=unknown. | condiciones read_write | Crea versión 1 y deriva has_entries en la misma aceptación. |
| UpdatePatientCondition | conditionId | Patch de name, estados, fechas, fuente y correctionReason opcional; versión actual. | condiciones read_write | No cambia ficha ni permite entered-in-error; valida estado combinado. |
| InvalidatePatientCondition | conditionId | correctionReason opcional; versión actual. | condiciones read_write | Anulación terminal entered-in-error, sin reactivación. |
| SetPatientClinicalSectionReview | patientId | section=conditions, informationStatus, sourceType=unknown; versión de revisión, 0 inicial. | condiciones read_write | not_asked/unknown/none_known sin pertinentes o has_entries con pertinentes. |
| CreatePatientAllergyIntolerance | allergyId nuevo | patientId, substance, type=unknown, reactionDescription?, clinicalStatus=active, verificationStatus=unconfirmed, onsetDate?, lastOccurrenceDate?, sourceType=unknown. | alergias read_write | Crea versión 1 y deriva has_entries. |
| UpdatePatientAllergyIntolerance | allergyId | Patch de substance, type, reacción, estados, fechas, fuente y correctionReason; versión actual. | alergias read_write | No cambia ficha ni permite entered-in-error. |
| InvalidatePatientAllergyIntolerance | allergyId | correctionReason opcional; versión actual. | alergias read_write | Anulación terminal entered-in-error; conserva historia. |
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
| SetServicePrice | serviceId | amount (texto decimal ≥ 0; cero = gratuito),currency USD / VES. | propietario profesional | Precio base del catálogo propio; versión optimista (0 al crear); proyecta `service_price` al propietario; nunca reescribe cargos emitidos. |
| SetServiceOfferPrice | {professionalId,serviceId} | amount,currency. | propietario de la oferta | Ajuste de la oferta existente; sustituye al base en la resolución; proyecta `service_offer_price` a miembros. |
| RemoveServiceOfferPrice | {professionalId,serviceId} | {} | propietario de la oferta | Retira el ajuste y devuelve la resolución al precio base; 409 sin ajuste. |
| CreatePatientCharge | chargeId nuevo | patientId,appointmentId?,encounterId?,serviceId?,description?,amount?,currency?,adjustReason?. | billing_charges | Sin importe resuelve el precio vigente y congela instantánea; ajuste manual exige motivo; vínculos por cuenta/paciente; nunca automático desde citas/atenciones; preparable offline (D28). |
| UpdatePatientCharge | chargeId | Patch de description,amount,currency,adjustReason. | billing_charges | Solo `draft` (`CHARGE_NOT_DRAFT`); ajuste con motivo marca `manual`. |
| IssuePatientCharge | chargeId | {} | billing_charges | Emite con instantánea definitiva; visible para concesiones y proyección `billing`. |
| CancelPatientCharge | chargeId | reason. | billing_charges | 409 `CHARGE_HAS_ACTIVE_PAYMENTS` con pagos vigentes (D27); conserva historia y pagos. |
| SetMemberBillingPermissions | userId miembro | billingPermissions{billingRead,billingCharges,billingReview} none / granted. | propietario | Denegado por defecto (D27); versionado, auditado e invalida capturas del alcance. |
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

| DeclarePatientMedication | medicationId nuevo | patientId, encounterId?, medicationName, sourceType, periodo y detalles opcionales. | medicación declarada read_write | Sin receta propia ni efectos derivados; fuente obligatoria. |
| UpdatePatientDeclaredMedication | medicationId | Patch de nombre/fuente/periodo/detalles/correctionReason. | medicación declarada read_write | No cambia ficha/atención. |
| ReviewPatientDeclaredMedication | medicationId | sin contenido. | medicación declarada read_write | Marca revisado con revisor del contexto; conserva fuente. |
| InvalidatePatientDeclaredMedication | medicationId | correctionReason opcional. | medicación declarada read_write | Anulación terminal. |
| CreatePatientCarePlan | planId nuevo | patientId, encounterId?, conditionId?, title, purpose?, fechas opcionales. | planes read_write | Preventivo sin condición; vínculos de la ficha. |
| UpdatePatientCarePlan | planId | Patch de campos; planStatus con statusReason. | planes read_write | Transiciones con motivo; cerrado/cancelado terminal. |
| InvalidatePatientCarePlan | planId | correctionReason opcional. | planes read_write | Anulación terminal. |
| AddCarePlanGoal | goalId nuevo | planId, patientId, description, goalKind y meta/medición opcionales. | planes read_write | Medible exige referencia. |
| UpdateCarePlanGoal | goalId | Patch de descripción/referencia/meta/plazo. | planes read_write | No evalúa. |
| EvaluateCarePlanGoal | goalId | evaluationStatus achieved/not_achieved. | planes read_write | Evaluación separada del cumplimiento. |
| InvalidateCarePlanGoal | goalId | correctionReason opcional. | planes read_write | Anulación terminal. |
| AddCarePlanAction | actionId nuevo | planId, patientId, goalId?, description, responsable y plazo opcionales. | planes read_write | goalId del mismo plan. |
| UpdateCarePlanAction | actionId | Patch de descripción/responsable/plazo. | planes read_write | Actividad hecha no evalúa objetivo. |
| CompleteCarePlanAction | actionId | completionNote opcional. | planes read_write | Marca realizada con instante. |
| InvalidateCarePlanAction | actionId | correctionReason opcional. | planes read_write | Anulación terminal. |
| AddCarePlanReview | reviewId nuevo | planId, patientId, summary, findings? opcionales. | planes read_write | No crea hechos nuevos. |
| InvalidateCarePlanReview | reviewId | correctionReason opcional. | planes read_write | Anulación terminal. |
| CreateDiagnosticReport | reportId nuevo | patientId, encounterId?, sourceName, fechas parciales, reportKind, reportStatus, attachmentId? opcional. | informes read_write | Original separado de resultados. |
| UpdateDiagnosticReport | reportId | Patch de fuente/fechas/tipo/resumen/attachmentId. | informes read_write | No cambia ficha. |
| CorrectDiagnosticReport | reportId | correctionReason y results: conjunto vigente completo, con resultId y contenido tipado por elemento. | informes read_write | Versiona informe y resultados, crea los nuevos y anula los omitidos en una aceptación. El payload antiguo sin results recibe VALIDATION_ERROR. |
| AddDiagnosticReportResult | resultId nuevo | reportId, patientId, analyteName, valor tipado con unidad y referencia del informe. | informes read_write | Numérico exige unidad. |
| UpdateDiagnosticReportResult | resultId | Patch del contenido tipado. | informes read_write | Corrección sin duplicar vigentes. |
| InvalidateDiagnosticReportResult | resultId | correctionReason opcional. | informes read_write | Anula el punto vigente. |
| UploadReportAttachment | attachmentId nuevo | patientId, reportId?, fileName, contentType, byteSize, sha256, contentBase64. | informes read_write | Verifica huella; reportId vincula y versiona el informe de la misma ficha en la misma aceptación; lecturas devuelven el vínculo; bytes fuera de DB y de sync. |
| InvalidateReportAttachment | attachmentId | correctionReason opcional. | informes read_write | Retira el adjunto del uso ordinario. |
| CreateSpecialtyTemplate | templateId nuevo | name, specialty, fields tipados. | especialidad read_write | Versión 1; sin defaults clínicos. |
| UpdateSpecialtyTemplate | templateId | name?, changeNote, fields completos. | especialidad read_write | Publica versión nueva; anteriores inmutables. |
| RetireSpecialtyTemplate | templateId | sin contenido. | especialidad read_write | No borra versiones ni registros. |
| CaptureSpecialtyRecord | recordId nuevo | patientId, encounterId?, templateId, values tipados. | especialidad read_write | Versión de plantilla fija; campos ausentes no se generan. |
| UpdateSpecialtyRecord | recordId | values y recordedAt opcionales. | especialidad read_write | Conserva templateVersion aplicada. |
| InvalidateSpecialtyRecord | recordId | correctionReason opcional. | especialidad read_write | Anulación terminal. |
| RecordDentalFinding | findingId nuevo | patientId, encounterId?, toothFdi, surface?, findingKind, note? y fecha opcional. | especialidad read_write | FDI y superficies cerradas; duplicado vigente rechazado. |
| UpdateDentalFinding | findingId | Patch de pieza/superficie/tipo/nota. | especialidad read_write | Duplicado vigente rechazado. |
| ResolveDentalFinding | findingId | correctionReason opcional. | especialidad read_write | Resolver conserva historia y permite nuevo hallazgo. |
| InvalidateDentalFinding | findingId | correctionReason opcional. | especialidad read_write | Anulación terminal. |
| AddDentalTreatment | treatmentId nuevo | findingId, patientId, treatmentKind, note? y fecha opcional. | especialidad read_write | Vinculada al hallazgo de la ficha. |
| UpdateDentalTreatment | treatmentId | Patch de tipo/estado/fecha. | especialidad read_write | performed exige fecha. |
| InvalidateDentalTreatment | treatmentId | correctionReason opcional. | especialidad read_write | Anulación terminal. |

## 6. Resultados, idempotencia y errores

OperationBatchResult = {results:[OperationResult],correlationId}. OperationResult = {operationId,status,entityVersion:null|int,state:null|proyección_permitida,error:null|ApiError,originalResult:null|resultado_original}. originalResult solo aparece en duplicate y no se anida recursivamente. La versión de estado actual de conflicto no se confunde con versión de resultado original. Posición de una escritura, si se muestra como dato de correlación, nunca es cursor aplicado.

Clave idempotente (accountId,actorUserId,operationId); el dispositivo del primer intento queda como evidencia, no impide recuperar resultado desde nueva instalación del mismo actor autorizada. Huella SHA-256 de JSON canónico UTF-8 con claves ordenadas, separación compacta, formatos tipados del envoltorio y payload y todos los campos semánticos. No incluir el token, correlación ni dispositivo de transporte. Cambiar payload, acción, versión esperada, dependencias o tiempo local de una misma operación es conflicto de contenido. En altas y acciones completas, campos ausentes opcionales se normalizan a los valores documentados antes de la huella. En parches `Update…` y `CorrectPatientMeasurement`, la huella conserva los campos presentes: omisión y `null` difieren cuando la escritura les da efectos distintos. Un recibo anterior de `CorrectPatientMeasurement` cuya huella antigua coincida devuelve `duplicate` para cualquiera de las variantes ambiguas, sin repetir efectos; no es posible reconstruir el payload original. Payload inválido se canoniza como JSON recibido para conservar su rechazo, sin aplicar coerciones silenciosas.

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

La descarga examina hasta 100 grupos confirmados por petición, sin dividirlos; hasMore indica si quedan grupos aunque sean invisibles. El cursor HMAC queda ligado a contrato, cuenta, usuario, dispositivo, audiencia, época y ventana capturada. Vence a los 90 días de emisión; una descarga válida emite la siguiente posición con nuevo plazo, sin prolongar la retención del journal. Firma inválida, posición futura, alcance distinto o posición anterior a frontera-1 devuelven CURSOR_EXPIRED. La clave API_SYNC_SIGNING_KEY debe ser secreta, tener al menos 32 caracteres y ser igual en todos los procesos; sin configuración la descarga/captura devuelve 503.

Orden de aceptación: controles de usuario/credencial, profesionales, pacientes y cuentas, cada conjunto ordenado por identificador; luego filas de negocio/recibo. Releer tras esperas y reiniciar si cambia conjunto. Todo escritor que afecta una proyección de cuenta bloquea su account_sync_heads hasta commit; incremento transaccional por operación. Un cambio con varias entidades ocupa un grupo y no se corta al paginar. Para globales permitidos se coordinan las cuentas afectadas en el mismo orden, con bloqueo previo del profesional/paciente que estabiliza sus referencias. Estado aceptado y proyección/versiones se conservan juntos.

Audiencia de change_log: members para datos operativos visibles a ambos roles; owner para catálogo privado no ofrecido y equipo/auditoría administrativa si corresponde. Snapshots y páginas aplican la misma audiencia. Ofertar un servicio publica la proyección mínima para miembros, nunca acceso al resto del catálogo. La época de acceso cambia al cambiar pertenencias o autorizaciones, invalidando capturas/cursores de ámbito antiguo; respuesta permite recuperar desde nueva vista sin filtrar datos.

SnapshotRequest = {appointmentsFrom?:date,appointmentsUntil?:date,includeClinical=false}. Valores por defecto: hoy local menos 30 días y hoy más 181 días como límite exclusivo, incluyendo el día hoy+180. Ventana máxima 366 días. SnapshotResponse = {snapshotId,accountId,contractVersion,modelRevision,window,baseCursor,expiresAt,itemCount,clinicalSections=[]}. SnapshotPage = PaginatedResponse<SyncItem> = {items:[SyncItem],total}. SyncItem identifica entityType,entityKey,entityVersion y state tipado. El total y itemCount solo cuentan elementos permitidos de esa captura.

Capturar bajo REPEATABLE READ en una sola lectura/materialización, sin red dentro, datos y baseCursor de esa vista. No mantener transacción entre peticiones; almacenar temporal con vencimiento de 15 minutos. Cualquier cambio de acceso invalida la captura; solo creador/dispositivo autorizado la descarga. Sus elementos se ordenan por la posición materializada única; page/shows aplica LIMIT/OFFSET a ese conjunto inmutable. Repetir snapshot, page y shows devuelve los mismos elementos mientras siga vigente y autorizado. DELETE solo libera derivado temporal; no borra pendientes locales ni crea cambio de negocio.

SnapshotResponse.window incluye las fechas locales, timeZone y límites UTC startsAt/endsAt resueltos al crear. La captura y el cursor firmado conservan esos valores aunque después cambie la zona de la cuenta. No recalcular el alcance de una página o delta desde el estado nuevo de la cuenta; otra ventana requiere nueva captura explícita.

Contenido: datos administrativos operativos de cuenta; fichas activas y draft; contactos y vínculos pertinentes; servicios ofrecidos, reglas/excepciones/bloqueos de ventana; citas que intersectan ventana e historia de esas citas; referencias inactivas necesarias para interpretarlas. Propietario incluye catálogo propio no ofrecido y metadatos de equipo permitidos; asistente no. No copia historia de citas fuera de ventana ni datos de otras cuentas. Las consultas online de historia no cambian el cursor. Una proyección de ocupación global solo expresa indisponibilidad, sin cita/paciente/motivo ajeno.

La historia viaja como appointment_history, con la misma clave de cita y su versión, junto a la proyección appointment. Contiene las entradas hasta esa versión, leídas de historia funcional inmutable; no añade recibos ni reescribe grupos persistidos. Snapshot y delta aplican el mismo criterio. Al salir de ventana se retiran cita e historia del consumidor, sin borrar sus filas funcionales. Los límites UTC de fechas locales usan AT TIME ZONE de PostgreSQL, incluida su regla para medianoches ambiguas, y quedan fijos tras crear la captura.

Cambios fuera de ventana siguen avanzando posición autorizada; cuando una cita deja de pertenecer a la vista emitir remove (retirada de ventana, no borrado real). Cambiar ventana exige nueva captura, conservando Outbox/intentiones del consumidor. Solo el consumidor aplica página y cursor juntos en su SQLite; aquí no se implementa Rust.

Retener grupos completos y resultados completos al menos 90 días desde aceptación; conservar frontera de retención y recibo mínimo. Cursor anterior a la frontera obliga nuevo snapshot. No purgar historia funcional o auditoría en esta etapa. Mantenimiento elimina temporales/resultados vencidos en lotes pequeños, sin borrar el recibo que evita repetir efectos.

El mantenimiento administrativo existente procesa hasta 500 resultados, 100 grupos consecutivos de una cuenta y 100 capturas vencidas por ejecución. El rol operativo no retira resultados ni journal. El recibo mínimo conserva clave, huella, estado y versión; repetir la misma intención vencida devuelve RESULT_EXPIRED y cambiar su contenido conserva IDEMPOTENCY_CONFLICT. SNAPSHOT_EXPIRED y SNAPSHOT_SCOPE_CHANGED exigen otra captura explícita; ningún error permite repetir un efecto con otra identidad de operación.

Una captura ya liberada o retirada físicamente devuelve 404, igual que una captura ajena o un ID inexistente; no se conserva un registro adicional para revelar su existencia. Mientras exista y pertenezca al creador autorizado, el servidor distingue vencimiento y cambio de época con sus errores 410.

## 8. Canal de avisos

T31 implementa GET A/sync/events con query cursor obligatorio, validado igual que GET changes. No acepta page/shows ni sustituye ese cursor por Last-Event-ID. Los errores de entrada/acceso ocurren antes de abrir HTTP 200: 401/403/404, 410 CURSOR_EXPIRED, 422, 429 CONNECTION_LIMIT y 503 DEPENDENCY_UNAVAILABLE. La clave de firma es la misma de descarga/capturas.

changes_available entrega {accountId,cursor}. Ese cursor conserva la posición aplicada que dio el cliente, ventana y época; no salta al head que provocó el aviso. El id SSE contiene la posición observada solo como referencia. heartbeat entrega {serverTime}; access_revoked no contiene data y cierra el stream. El cliente conserva su cursor aplicado tras cada descarga y lo usa al volver a conectar.

El límite de dos conexiones rige entre procesos mediante registros con plazo de 45 segundos renovados al revalidar. No mantiene sesiones SQL por cliente. El listener usa una conexión dedicada por proceso; confirma LISTEN y despierta a los streams tras cada recuperación para releer el journal. Cada stream admite un aviso pendiente; al excederlo termina. Un envío de red que tarda más de tres segundos provoca desconexión. La preparación devuelve 503 mientras falta el listener; las rutas de datos siguen disponibles.

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


## 10. Diseño clínico de etapa 1 para revisión C01

Perfil, cambios de nacimiento, condiciones, alergias/intolerancias, permisos, resultados y descarga clínica están disponibles en el servidor para revisión C07. Los esquemas Pydantic de `clinical_records`, `accounts`, `patients` y `sync` son la fuente ejecutable; esta sección explica su comportamiento y no crea otra definición. Se conserva `contractVersion=1`; la publicación actual es `modelRevision=api-v1.3`.

### 10.1 Acceso clínico

Tres niveles independientes por pertenencia: `clinicalProfile`, `conditions`, `allergies`, cada uno `none`, `read` o `read_write`. El propietario tiene acceso efectivo completo y no puede retirárselo mediante esta operación. Asistentes existentes/nuevos empiezan con `read_write`; solo el propietario los configura, online y con la versión de pertenencia. Desactivar/reactivar no reinicia niveles.

- `none`: sin datos, resúmenes, historias, resultados o descargas de esa sección.
- `read`: consulta actual/historia y recuperación del estado vigente; no escrituras ni reintentos de escritura.
- `read_write`: lectura y acciones de esa sección.
- La recuperación de un resultado de escritura exige `read_write` vigente en su sección. Configurar permisos exige propietario vigente.
- Nacimiento conserva los permisos administrativos existentes; el nivel de perfil controla sexo al nacer y su historia. La autorización precede a duplicados, resultados, conteos y cuerpos. Un objeto de otra cuenta devuelve 404 como uno inexistente.

`AccessResponse` añade `clinicalPermissions` con los tres niveles efectivos propios. La configuración de otro asistente solo se consulta con la ruta de propietario. Cambiar niveles incrementa versión de pertenencia y `permissionEpoch`, invalida capturas/cursores y cierra SSE mediante la revalidación vigente.

### 10.2 Rutas nuevas

A equivale a `/v1/accounts/{account_id}` y todas exigen token, dispositivo y nivel aplicable. `section` admite `conditions` o `allergies`.

| Método | Ruta | Acceso | Modelo de respuesta / comportamiento |
|---|---|---|---|
| GET | `A/patients/{patient_id}/clinical-profile` | perfil `read`/`read_write` | `ClinicalProfileResponse`; versión 0 sin fila |
| GET | `A/patients/{patient_id}/clinical-profile/history` | perfil `read`/`read_write` | Historia ascendente con `afterVersion` |
| GET | `A/patients/{patient_id}/birth-date-changes` | miembro | Cambios por `patientVersion` ascendente y `afterVersion` |
| GET | `A/patients/{patient_id}/conditions` | condiciones `read`/`read_write` | Lista actual y filtros documentados |
| GET | `A/patients/{patient_id}/conditions/{condition_id}` | condiciones `read`/`read_write` | Detalle de la misma cuenta/ficha |
| GET | `A/patients/{patient_id}/conditions/{condition_id}/history` | condiciones `read`/`read_write` | Historia por versión |
| GET | `A/patients/{patient_id}/allergy-intolerances` | alergias `read`/`read_write` | Lista actual y filtros documentados |
| GET | `A/patients/{patient_id}/allergy-intolerances/{allergy_id}` | alergias `read`/`read_write` | Detalle de la misma cuenta/ficha |
| GET | `A/patients/{patient_id}/allergy-intolerances/{allergy_id}/history` | alergias `read`/`read_write` | Historia por versión |
| GET | `A/patients/{patient_id}/clinical-sections/conditions` | condiciones `read`/`read_write` | Revisión actual |
| GET | `A/patients/{patient_id}/clinical-sections/conditions/history` | condiciones `read`/`read_write` | Historia por versión |
| GET | `A/patients/{patient_id}/clinical-sections/allergies` | alergias `read`/`read_write` | Revisión actual |
| GET | `A/patients/{patient_id}/clinical-sections/allergies/history` | alergias `read`/`read_write` | Historia por versión |

Todas usan `page`/`shows`, `items`/`total`, autorización y filtros antes de contar/paginar. Historial acepta `afterVersion`. Condiciones filtra `clinicalStatus`, `verificationStatus` e `includeEnteredInError`; alergias añade `type`. Por defecto incluye estados vigentes, resueltos y refutados, pero excluye `entered-in-error`; un filtro explícito por ese estado o `includeEnteredInError=true` lo incluye. Las listas no tienen búsqueda global ni orden por texto clínico.

### 10.3 Modelos públicos

Campos comunes:

- Fechas clínicas `ClinicalDate`: cadena `YYYY`, `YYYY-MM`, `YYYY-MM-DD` o nulo en entradas que lo admitan. Conserva precisión y valida calendario/bisiestos. No se serializa como fecha completa ficticia.
- `ClinicalSourceType`: `patient`, `related_person`, `professional`, `external_document`, `unknown`; inicial `unknown`.
- Las respuestas actuales incluyen `createdAt`,`updatedAt`,`version`; historias incluyen contenido resultante, `action`,`actorUserId`,`operationId`,`changedAt`. No devuelven ORM, `accountId` redundante de ruta ni datos de otra cuenta.
- Los parches tienen al menos un campo, ausencia conserva y nulo borra solo campos anulables. Un cambio sin diferencia devuelve `NO_CHANGES` sin versión/historia.

| Modelo | Campos |
|---|---|
| `MemberClinicalPermissionsResponse` | `userId`, `clinicalPermissions{clinicalProfile,conditions,allergies}`, `membershipVersion` |
| `ClinicalProfileResponse` | `patientId`, `sexAtBirth`, `sourceType`, `version`, `birthDate`, `patientVersion`, `ageYears`, `ageAsOf`, `createdAt?`, `updatedAt?` |
| `PatientConditionResponse` | `conditionId`, `patientId`, `name`, `clinicalStatus`, `verificationStatus`, `onsetDate`, `abatementDate`, `sourceType`, `correctionReason`, `createdAt`, `updatedAt`, `version` |
| `PatientAllergyIntoleranceResponse` | `allergyId`, `patientId`, `substance`, `type`, `reactionDescription`, `clinicalStatus`, `verificationStatus`, `onsetDate`, `lastOccurrenceDate`, `sourceType`, `correctionReason`, `createdAt`, `updatedAt`, `version` |
| `ClinicalSectionReviewResponse` | `patientId`, `section`, `informationStatus`, `sourceType`, `reviewedByUserId?`, `reviewedAt?`, `activeCount`, `version`, `createdAt?`, `updatedAt?` |
| `PatientBirthDateChangeResponse` | `changeId`, `patientId`, `previousBirthDate`, `newBirthDate`, `patientVersion`, `actorUserId`, `operationId`, `changedAt` |

`sexAtBirth`: `male`,`female`,`other`,`unknown` o nulo. Perfil ausente devuelve sexo/fuente y marcas nulos, versión 0; no escribe. Edad usa años completos y `ageAsOf` fecha local del servidor en zona de cuenta; nacimiento ausente produce edad nula. Cumpleaños 29 de febrero se alcanza el 1 de marzo en año no bisiesto, como la regla administrativa vigente.

Estados de condición: clínico `active`,`recurrence`,`relapse`,`inactive`,`remission`,`resolved`,`unknown`; verificación `unconfirmed`,`provisional`,`differential`,`confirmed`,`refuted`,`entered-in-error`. Alergia: tipo `allergy`,`intolerance`,`unknown`; clínico `active`,`inactive`,`resolved`; verificación `unconfirmed`,`presumed`,`confirmed`,`refuted`,`entered-in-error`.

`informationStatus`: `not_recorded`,`not_asked`,`unknown`,`none_known`,`has_entries`. Pertinente significa no `refuted` ni `entered-in-error`, incluso resuelto. `activeCount` cuenta condiciones `active`,`recurrence`,`relapse` o alergias `active` dentro de pertinentes. Las listas de resumen no prueban diagnóstico, gravedad ni ausencia clínica.

### 10.4 Acciones por lote

Las acciones de etapa 1 ya figuran en §5; la descarga clínica completa se concretará en T16. Conservan envoltura, huella, `expectedVersion`, idempotencia, resultados y límites existentes. No aceptan actor, cuenta, autor o instante técnico del cliente. Los UUID nuevos proceden del cliente para trabajo offline.

| Acción | `entityKey` | Payload / versión | Permiso y regla |
|---|---|---|---|
| `SetPatientSexAtBirth` | `patientId` | `sexAtBirth`, `sourceType`; perfil versión actual o 0 | perfil `read_write`; primera exige valor no nulo |
| `CreatePatientCondition` | `conditionId` nuevo | `patientId`, nombre, estados, fechas y fuente | condiciones `read_write`; no admite `entered-in-error` inicial |
| `UpdatePatientCondition` | `conditionId` | Patch y versión actual | condiciones `read_write`; no anula por patch |
| `InvalidatePatientCondition` | `conditionId` | `correctionReason` y versión actual | condiciones `read_write`; anulación terminal |
| `CreatePatientAllergyIntolerance` | `allergyId` nuevo | `patientId`, sustancia, tipo, reacción, estados, fechas y fuente | alergias `read_write`; no admite `entered-in-error` inicial |
| `UpdatePatientAllergyIntolerance` | `allergyId` | Patch y versión actual | alergias `read_write`; no anula por patch |
| `InvalidatePatientAllergyIntolerance` | `allergyId` | `correctionReason` y versión actual | alergias `read_write`; anulación terminal |
| `SetPatientClinicalSectionReview` | `patientId` | `section`, `informationStatus`, fuente; revisión actual o 0 | `read_write` de la sección indicada |
| `SetMemberClinicalPermissions` | `userId` | Tres niveles y versión de pertenencia | propietario, online |

Crear el primer registro pertinente cambia revisión a `has_entries`; añadir más no crea otra revisión si ya tiene ese estado. Anular/refutar el último cambia a `unknown`. Confirmar `has_entries` sin diferencias devuelve `NO_CHANGES`; para dejar constancia de una nueva revisión se requiere un cambio de fuente u otro dato permitido, sin fabricar versiones repetidas. Altas, anulaciones y revisiones se coordinan por ficha para impedir ausencia conocida concurrente con un alta.

Una fecha de inicio completamente posterior al día local se rechaza. Un fin inequívocamente anterior al inicio se rechaza; si la precisión no decide el orden se conserva. La fecha de aceptación no sustituye fechas clínicas. `refuted` excluye del resumen vigente pero no es anulación por error; `entered-in-error` solo se asigna por la acción terminal.

### 10.5 Descarga, aceptación y auditoría

`SnapshotRequest` añade `includeClinical=false`. Cuando es verdadero, la captura materializa solo secciones legibles y registra `clinicalSections` subconjunto de `profile`,`conditions`,`allergies`; vacío conserva la forma y contenido anteriores. `SnapshotResponse` expone ese conjunto y el cursor firmado lo conserva. Cursores anteriores equivalen a `includeClinical=false`.

Nuevas proyecciones `patient_clinical_profile`, `patient_condition`, `patient_allergy_intolerance`, `patient_clinical_section_review`: último estado, incluidos resueltos, refutados y anulados; no tablas de historial. Ficha/nacimiento y demás referencias administrativas necesarias siguen las reglas existentes; también se reúnen pacientes referenciados por clínica aunque estén inactivos/completos y sin citas en la ventana. Condiciones/alergias no se filtran por ventana de citas. Audiencias cerradas `clinical_profile`,`clinical_conditions`,`clinical_allergies` se comprueban antes de validar/entregar proyecciones; un consumidor que no solicita clínica nunca las recibe. Los grupos invisibles permiten avanzar sin cuerpos.

Cambio de niveles o época exige otra captura; SSE cierra el alcance anterior. Esto no promete borrado remoto de datos ya descargados. No se habilita consumo clínico mientras procesos antiguos sigan activos.

Cada operación conserva efecto, historias/revisión derivada, auditoría, recibo y grupo en una transacción. El recibo clínico persiste `clinical_section`; duplicados y GET exigen `read_write` vigente en esa sección antes de entregar resultados o conflictos informativos. Lecturas clínicas correctas, recuperaciones de resultados, capturas, páginas y deltas con clínica registran actor, dispositivo, cuenta, paciente/objeto o sección, acción, resultado, correlación e instante. No registran nombres, sustancias, reacciones, filtros clínicos, cuerpos o cursores. Si falla esa evidencia, la lectura no entrega datos y devuelve el fallo temporal común; SSE no audita heartbeats.

Las fechas parciales usan biblioteca estándar y validadores del proyecto. Las rutas declaran `response_model` y retorno real; proyecciones se validan antes de commit. Fuentes oficiales: [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/), [Pydantic 2.14.1 validators](https://github.com/pydantic/pydantic/blob/v2.14.1/docs/concepts/validators.md), [PostgreSQL 18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html), [SQLAlchemy 2.1 transactions](https://docs.sqlalchemy.org/en/21/orm/session_transaction.html) y FHIR R5 enlazado en el plan.

## 11. Diseño clínico de etapa 2 para C01

Diseño futuro de [P-20261116-02-clinical-routine](../tasks/P-20261116-02-clinical-routine/plan.md), no implementado. Conserva `contractVersion=1`; `modelRevision=api-v1.3` se publicará solo al completar T26. Los modelos Pydantic reales seguirán siendo la fuente de los artefactos; esta sección fija comportamiento, nombres y campos sin editar generados.

### 11.1 Forma común

Todas las rutas nuevas están bajo `A/patients/{patient_id}`, exigen token, dispositivo y permiso de la sección. JSON camelCase, `page`/`shows`, `items`/`total`, autorización/filtros antes de contar/paginar y orden estable. Historias usan versión ascendente y `afterVersion`. Detalles/lecturas de objeto ajeno devuelven la misma ausencia que uno inexistente.

Respuestas actuales incluyen `patientId`, `recordStatus`, `correctionReason`, `createdAt`, `updatedAt`, `version` y su ID propio. No repiten `accountId`. Historias contienen el contenido resultante, `action`, `actorUserId`, `operationId`, `changedAt`. El actor procede del contexto; los instantes técnicos no se aceptan como autoridad del cliente.

Parches conservan campos ausentes, admiten null solo en campos anulables, exigen al menos un campo y devuelven `NO_CHANGES` sin crear versión. Crear usa UUID nuevo y `expectedVersion=0`; actualizar/corregir/anular usa la versión actual. `capturedAtLocal` es dato reportado. En atenciones/mediciones, el instante del hecho usa el campo explícito, luego `occurredAtLocal` de la envoltura o reloj del servidor. Un instante futuro se rechaza. Vacunas/antecedentes conservan `ClinicalDate` parcial sin hora ficticia.

### 11.2 Rutas y lecturas

| Recurso | Rutas GET bajo `A/patients/{patient_id}` | Acceso, filtros y orden |
|---|---|---|
| Atenciones | `/encounters`; `/encounters/{encounter_id}`; `/encounters/{encounter_id}/history`; `/last-visit` | `encounters`; lista `recordStatus`, rango `[from,until)`; orden `(occurredAt,id)`; última visita devuelve `encounterId`,`occurredAt`,`scope=account`, todos nulos salvo scope si no hay atención válida |
| Notas | `/notes`; `/notes/{note_id}`; `/notes/{note_id}/history` | `notes`; `recordStatus`, `encounterId`; orden `(createdAt,id)` |
| Mediciones | `/measurements`; `/measurements/{measurement_id}`; `/measurements/{measurement_id}/history`; `/measurements/summary` | `measurements`; `kind`,`recordStatus`, rango de `measuredAt`; orden `(measuredAt,id)`; resumen por tipo solo válidos |
| Vacunas | `/immunizations`; `/immunizations/{immunization_id}`; `/immunizations/{immunization_id}/history` | `immunizations`; `recordKind`,`recordStatus`; orden `(occurrenceDate,id)` |
| Antecedentes | `/antecedents`; `/antecedents/{antecedent_id}`; `/antecedents/{antecedent_id}/history` | `antecedents`; `category`,`recordStatus`; orden `(createdAt,id)` |
| Historial | `/clinical-history` | Permiso por fuente; `sections`,`entryTypes`,`recordStatus`,`from`,`until`; filtra secciones antes de total/página y ordena `(sortKey,entryType,entryId)` |

Las listas ordinarias excluyen `entered-in-error`; solo el filtro explícito lo incluye. `from`/`until` se aplica al tiempo clínico cuando existe y a la referencia documentada en otro caso, sin completar fechas parciales. El resumen de mediciones devuelve una entrada por cada tipo con toma válida; una toma corregida solo aporta su versión actual.

`ClinicalHistoryEntry` contiene `entryType`,`entryId`,`sourceSection`,`occurredAt`,`occurrenceDate`,`datePrecision`,`acceptedAt`,`entityVersion`,`recordStatus`; no contiene cuerpo, nombre, sustancia o valor. Cada referencia se resuelve por la ruta de su fuente y vuelve a autorizar. `LastVisitResponse` se limita a la referencia e instante, sin contenido de atención.

### 11.3 Modelos públicos

| Modelo | Campos específicos además de los comunes |
|---|---|
| `PatientEncounterResponse` | `encounterId`,`appointmentId`,`attendingProfessionalId`,`assistantUserId`,`occurredAt`,`endedAt`,`capturedAtLocal`,`reason`,`reasonSourceType`,`historyPresentIllness`,`findings`,`assessment`,`indications` |
| `PatientNoteResponse` | `noteId`,`encounterId`,`body`,`capturedAtLocal` |
| `PatientMeasurementResponse` | `measurementId`,`encounterId`,`kind`,`measuredAt`,`capturedAtLocal`,`method`,`bodySite`,`value`,`systolicValue`,`diastolicValue`,`unit`,`ageYears`,`ageAsOf`,`patientVersion` |
| `PatientImmunizationResponse` | `immunizationId`,`encounterId`,`vaccineName`,`occurrenceDate`,`recordKind`,`sourceType`,`capturedAtLocal`,`productName`,`doseDescription`,`lotNumber`,`route`,`bodySite`,`locationText`,`administratorName` |
| `PatientAntecedentResponse` | `antecedentId`,`encounterId`,`category`,`content`,`relatedPersonDescription`,`occurrenceDate`,`sourceType`,`capturedAtLocal` |
| `MeasurementSummaryResponse` | `patientId`,`items` de última toma por tipo; cada item es `PatientMeasurementResponse` |
| `LastVisitResponse` | `encounterId`,`occurredAt`,`scope=account` |
| `ClinicalHistoryEntry` | Referencias, tiempos, precisión, versión y estado indicados en §11.2 |

Los valores numéricos se serializan como números decimales JSON sin NaN/infinito ni formato regional. `blood_pressure` admite un componente nulo y `value` nulo; los demás tipos exigen `value` y componentes nulos. Unidad y tipo no se cambian por corrección. `ageYears`,`ageAsOf`,`patientVersion` se derivan del nacimiento en la fecha local de `measuredAt`; nacimiento ausente da edad nula y no se persiste el derivado.

`ClinicalPermissions` añade `encounters`,`notes`,`measurements`,`immunizations`,`antecedents`. `MemberClinicalPermissionsResponse` y `AccessResponse` los incluyen al publicar el contrato. Las respuestas de historia añaden el sufijo `HistoryResponse` al modelo actual correspondiente.

### 11.4 Quince acciones nuevas

Todas conservan envoltura, huella, idempotencia, permiso vigente, alcance persistido en recibo, auditoría y grupo. Los UUID nuevos proceden del cliente. No aceptan autor/cuenta/aceptación del payload.

| Acción | `entityKey` | Payload | Permiso / regla |
|---|---|---|---|
| `CreatePatientEncounter` | `encounterId` nuevo | `patientId`,`appointmentId?`,`attendingProfessionalId`,`assistantUserId?`,`occurredAt?`,`endedAt?`,`capturedAtLocal?`,`reason?`,`reasonSourceType=unknown`,`historyPresentIllness?`,`findings?`,`assessment?`,`indications?` | `encounters read_write`; sin cierre; varias por cita |
| `UpdatePatientEncounter` | `encounterId` | Patch de tiempos/captura/contenido/fuente/`correctionReason` | Igual; no cambia ficha/cita/profesional; anulación aparte |
| `InvalidatePatientEncounter` | `encounterId` | `correctionReason?` | Igual; `entered-in-error` terminal |
| `CreatePatientNote` | `noteId` nuevo | `patientId`,`encounterId?`,`body`,`capturedAtLocal?` | `notes read_write`; sin efecto clínico derivado |
| `UpdatePatientNote` | `noteId` | Patch de `body`,`capturedAtLocal`,`correctionReason` | Igual; no cambia ficha/atención |
| `InvalidatePatientNote` | `noteId` | `correctionReason?` | Igual; terminal |
| `RecordPatientMeasurement` | `measurementId` nuevo | `patientId`,`encounterId?`,`kind`,`measuredAt?`,`capturedAtLocal?`,`method?`,`bodySite?`,`value?`,`systolicValue?`,`diastolicValue?`,`unit` | `measurements read_write`; forma/unidad/rango cerrados |
| `CorrectPatientMeasurement` | `measurementId` | Patch de tiempo/captura/método/sitio/valores/`correctionReason` | Igual; no cambia ficha/tipo/unidad |
| `InvalidatePatientMeasurement` | `measurementId` | `correctionReason?` | Igual; terminal |
| `RecordPatientImmunization` | `immunizationId` nuevo | `patientId`,`encounterId?`,`vaccineName`,`occurrenceDate`,`recordKind=unknown`,`sourceType=unknown`,`capturedAtLocal?` y siete detalles opcionales de §11.3 | `immunizations read_write`; `administered_here` exige atención válida |
| `UpdatePatientImmunization` | `immunizationId` | Patch de vacuna/fecha/tipo/fuente/captura/detalles/`correctionReason` | Igual; no cambia ficha/atención |
| `InvalidatePatientImmunization` | `immunizationId` | `correctionReason?` | Igual; terminal |
| `CreatePatientAntecedent` | `antecedentId` nuevo | `patientId`,`encounterId?`,`category`,`content`,`relatedPersonDescription?`,`occurrenceDate?`,`sourceType=unknown`,`capturedAtLocal?` | `antecedents read_write`; `family` exige persona relacionada |
| `UpdatePatientAntecedent` | `antecedentId` | Patch de contenido/persona/fecha/fuente/captura/`correctionReason` | Igual; no cambia ficha/atención/categoría |
| `InvalidatePatientAntecedent` | `antecedentId` | `correctionReason?` | Igual; terminal |

`SetMemberClinicalPermissions` acepta las ocho secciones. En payloads anteriores, las cinco omitidas se normalizan a `read_write` antes de huella/ejecución. La configuración conserva versiones, época, recibo, auditoría y journal juntos.

### 11.5 Permisos, auditoría y transacción

Cada nivel es independiente: `none` excluye lecturas, historias, resúmenes, resultados y descarga; `read` permite lecturas y excluye escrituras/reintentos; `read_write` permite ambos. Última visita exige `encounters`. El historial no tiene permiso global: filtra por `source_section` antes de contar/paginar y cada detalle vuelve a autorizar. La autorización precede a duplicados y resultados.

Escrituras conservan efecto, historia, timeline, auditoría, recibo y grupo en una transacción. Lecturas de recursos, historias, última visita, historial, resultados, capturas, páginas y deltas clínicos registran actor, dispositivo, cuenta, objeto/sección, acción, resultado, correlación e instante. No guardan motivos, cuerpos, valores, nombres, filtros o cursores. Si falla la evidencia, no se entregan datos.

### 11.6 Captura, delta y compatibilidad

`includeClinical=false` conserva capturas sin clínica. Con `true`, incluye todas las secciones legibles de Etapas 1 y 2 y `clinicalSections` amplía su conjunto cerrado. Cursores/recibos/audiencias conservan ese alcance; cambiar permisos exige nueva captura y cierra SSE anterior.

La captura de Etapa 2 contiene atenciones válidas actuales y vínculos, versión actual válida de notas/antecedentes, todas las tomas válidas y vacunas válidas actuales. No incluye historias de versiones, timeline derivado ni adjuntos. Incluye referencias administrativas necesarias, incluso pacientes inactivos/completos y profesionales necesarios. Ningún hecho se filtra por ventana de citas.

El delta publica correcciones con la versión actual y anulaciones como `entered-in-error`; una captura posterior no incluye la entrada inválida. Los grupos invisibles permiten avanzar sin contenido. La retención de 90 días no borra hechos/historias. No se promete borrado de copias descargadas ni aplicación atómica en SQLite sin prueba del consumidor.

OpenAPI, esquemas, ejemplos y manifiesto se generan desde la app real con `modelRevision=api-v1.3`. Los recuentos proceden del catálogo real, no de cifras fijas. `contractVersion=1` se conserva.

## Compatibilidad de normalización de autorización · T03

La [correspondencia de acceso](access-design.md#correspondencia-para-normalizar-autorización--t03--2026-11-17) fija acciones/reglas/audiencias internas sin duplicar estos modelos HTTP. Se conservan role, allowedActions (incluido orden y las dos posiciones de SetPatientClinicalSectionReview), clinicalPermissions, permissionEpoch, defaults, rutas, estados y recuperación. contractVersion=1 y modelRevision=api-v1.3 no cambian. La excepción autorizada AU-32 deniega GET de un recibo clínico histórico sin sección antes de leer su resultado; no cambia el rechazo ya aplicado al reintento ni añade migración.

## 12. Diseño clínico de etapa 3 para C03

Diseño de [P-20261117-05-clinical-stage-3](../tasks/P-20261117-05-clinical-stage-3/plan.md), no implementado al redactarse. Conserva `contractVersion=1`; `modelRevision=api-v1.4` se publicará solo al completar la fase de contratos. Las reglas funcionales proceden de [patient-clinical-record.md §4.3.1](patient-clinical-record.md) y [database-schema.md §§12–14](database-schema.md). Prescripción/récipes, PDF de esos documentos, QR y su acceso del paciente permanecen en P-20261117-04 y no aparecen aquí.

### 12.1 Forma común

Conserva la forma de §11.1: rutas bajo `A/patients/{patient_id}`, token/dispositivo/permiso de sección, camelCase, `page`/`shows`, `items`/`total`, filtros antes de contar, orden estable, historias con `afterVersion`, objeto ajeno = ausencia. Fechas clínicas parciales usan `ClinicalDate` (`YYYY`,`YYYY-MM`,`YYYY-MM-DD`); `recordStatus`, `correctionReason`, `version`, envoltura, huella, idempotencia y `NO_CHANGES` se conservan. Parches: ausencia se conserva, null solo en anulables, al menos un campo.

Reglas propias: la revisión de medicación (`ReviewPatientDeclaredMedication`) y la evaluación de objetivo (`EvaluateCarePlanGoal`) son acciones propias, no parches; completar una acción (`CompleteCarePlanAction`) no evalúa objetivos. Corregir un informe (`CorrectDiagnosticReport`) es acción propia que versiona el informe y sustituye sus resultados vigentes en la misma aceptación. Las subcolecciones de plan (objetivos/acciones/revisiones) usan rutas anidadas y heredan el permiso `care_plans`.

### 12.2 Rutas y lecturas

| Recurso | Rutas GET bajo `A/patients/{patient_id}` | Acceso, filtros y orden |
|---|---|---|
| Medicación declarada | `/declared-medications`; `/declared-medications/{medication_id}`; `/declared-medications/{medication_id}/history` | `declared_medications`; `recordStatus`,`reviewStatus`,`sourceType`; orden `(createdAt,id)` |
| Planes de cuidados | `/care-plans`; `/care-plans/{plan_id}`; `/care-plans/{plan_id}/history`; `/care-plans/{plan_id}/goals`; `/care-plans/{plan_id}/goals/{goal_id}`; `/care-plans/{plan_id}/actions`; `/care-plans/{plan_id}/actions/{action_id}`; `/care-plans/{plan_id}/reviews`; `/care-plans/{plan_id}/reviews/{review_id}`; historia por cada subrecurso | `care_plans`; planes filtran `planStatus`,`recordStatus`; objetivos `goalKind`,`evaluationStatus`; acciones `completionStatus`; revisiones orden `(reviewedAt,id)`; subcolecciones orden `(createdAt,id)` |
| Informes | `/diagnostic-reports`; `/diagnostic-reports/{report_id}`; `/diagnostic-reports/{report_id}/history`; `/diagnostic-reports/{report_id}/results`; `/report-attachments/{attachment_id}`; `/report-attachments/{attachment_id}/content` | `diagnostic_reports`; informes filtran `reportKind`,`reportStatus`,`recordStatus`, rango de `sampleDate`; orden `(sampleDate,id)`; resultados usan `page`/`shows`, filtran `recordStatus` y ordenan por `id`; el contenido del adjunto exige `read` vigente y reautoriza antes de entregar bytes |
| Plantillas | `/specialty-templates`; `/specialty-templates/{template_id}`; `/specialty-records`; `/specialty-records/{record_id}`; `/specialty-records/{record_id}/history` | `specialty_templates`; plantillas filtran `specialty`,`templateStatus`; registros filtran `templateId`,`recordStatus`; orden `(createdAt,id)` |
| Analítica | `/analytics/series`; `/analytics/growth` | `measurements` para series de mediciones; `clinical_analytics` para proyecciones derivadas y crecimiento |

Las listas ordinarias excluyen `entered-in-error`; solo el filtro explícito lo incluye. Los resultados vigentes de un informe son los `recordStatus=valid` de su versión actual; las historias conservan versiones anteriores. La descarga de adjunto no usa URL firmada pública: la ruta reautoriza y sirve los bytes en la misma sesión autenticada.

### 12.3 Modelos públicos

| Modelo | Campos específicos además de los comunes |
|---|---|
| `DeclaredMedicationResponse` | `medicationId`,`encounterId`,`medicationName`,`sourceType`,`startDate`,`endDate`,`doseDescription`,`frequencyDescription`,`prescriberName`,`routeDescription`,`reviewStatus`,`reviewedAt`,`reviewedByUserId`,`capturedAtLocal` |
| `CarePlanResponse` | `planId`,`encounterId`,`conditionId`,`title`,`purpose`,`startDate`,`expectedEndDate`,`planStatus`,`statusReason`,`capturedAtLocal` |
| `CarePlanGoalResponse` | `goalId`,`planId`,`description`,`goalKind`,`measurementKind`,`referenceDescription`,`expectedResult`,`targetValue`,`unit`,`dueDate`,`evaluationStatus`,`evaluatedAt`,`evaluatedByUserId`,`evaluationNote` |
| `CarePlanActionResponse` | `actionId`,`planId`,`goalId`,`description`,`responsibleUserId`,`dueDate`,`completionStatus`,`completedAt`,`completionNote` |
| `CarePlanReviewResponse` | `reviewId`,`planId`,`reviewedAt`,`summary`,`findings`,`nextReviewDate` |
| `DiagnosticReportResponse` | `reportId`,`encounterId`,`sourceName`,`sourceType`,`sampleDate`,`issuedDate`,`reportKind`,`reportStatus`,`attachmentId`,`clinicalSummary`,`capturedAtLocal` |
| `DiagnosticReportResultResponse` | `resultId`,`reportId`,`analyteName`,`resultKind`,`value`,`textValue`,`unit`,`referenceLow`,`referenceHigh`,`referenceText` |
| `ReportAttachmentResponse` | `attachmentId`,`patientId`,`reportId?` en carga, `fileName`,`contentType`,`byteSize`,`sha256`,`uploadedAt` (sin `storageKey` ni URL) |
| `SpecialtyTemplateResponse` | `templateId`,`name`,`specialty`,`templateStatus`,`changeNote`,`version`,`fields` con `fieldKey`,`label`,`fieldKind`,`required`,`options`,`displayOrder` |
| `SpecialtyRecordResponse` | `recordId`,`encounterId`,`templateId`,`templateVersion`,`recordedAt`,`values` con `fieldKey` y el valor tipado aplicable |
| `SeriesPointResponse` | `measurementKind`,`measuredAt`,`value`,`systolicValue`,`diastolicValue`,`unit`,`sourceMeasurementId`,`sourceVersion` |
| `GrowthResponse` | `indicator`,`referenceCode`,`referenceVersion`,`ageDays`,`points` con medición, percentil/z cuando aplica y `limitExplanation` cuando la referencia no aplica |

`ClinicalPermissions` añade `declaredMedications`,`carePlans`,`diagnosticReports`,`specialtyTemplates`,`clinicalAnalytics`. `sourceType` de medicación admite `patient`,`caregiver`,`other_professional`,`document`. Ningún modelo incluye consumo, adherencia, diagnóstico, normalidad por defecto ni URL de adjunto.

### 12.4 Acciones nuevas

Todas conservan envoltura, huella, idempotencia, permiso vigente, recibo con `clinicalSection`, auditoría y grupo; los UUID nuevos proceden del cliente; no aceptan actor/cuenta/aceptación del payload.

**Medicación declarada** (`declared_medications read_write`):

| Acción | `entityKey` | Payload | Regla |
|---|---|---|---|
| `DeclarePatientMedication` | `medicationId` nuevo | `patientId`,`encounterId?`,`medicationName`,`sourceType`,`startDate?`,`endDate?`,`doseDescription?`,`frequencyDescription?`,`prescriberName?`,`routeDescription?`,`capturedAtLocal?` | Sin receta propia ni efecto derivado |
| `UpdatePatientDeclaredMedication` | `medicationId` | Patch de nombre/fuente/periodo/detalle/captura/`correctionReason` | No cambia ficha/atención |
| `ReviewPatientDeclaredMedication` | `medicationId` | — | Marca `reviewed` con revisor del contexto; conserva fuente |
| `InvalidatePatientDeclaredMedication` | `medicationId` | `correctionReason?` | `entered-in-error` terminal |

**Planes de cuidados** (`care_plans read_write`):

| Acción | `entityKey` | Payload | Regla |
|---|---|---|---|
| `CreatePatientCarePlan` | `planId` nuevo | `patientId`,`encounterId?`,`conditionId?`,`title`,`purpose?`,`startDate?`,`expectedEndDate?`,`capturedAtLocal?` | Condición nula = preventivo; debe ser de la misma ficha |
| `UpdatePatientCarePlan` | `planId` | Patch de título/finalidad/fechas/captura/`correctionReason`; `planStatus` con `statusReason` | Transiciones `active`⇄`suspended`, a `closed`/`cancelled`; terminal con historia |
| `AddCarePlanGoal` | `goalId` nuevo | `planId`,`description`,`goalKind`,`measurementKind?`,`referenceDescription?`,`expectedResult?`,`targetValue?`,`unit?`,`dueDate?` | Medible exige meta o unidad o medición |
| `UpdateCarePlanGoal` | `goalId` | Patch de descripción/referencia/meta/plazo/`correctionReason` | No evalúa |
| `EvaluateCarePlanGoal` | `goalId` | `evaluationStatus`,`note?` | `achieved`/`not_achieved` con evaluador del contexto; la nota se conserva como `evaluationNote` en el estado, la historia y la captura |
| `CompleteCarePlanAction` | `actionId` | `completedAt?`,`completionNote?` | Actividad hecha ≠ objetivo logrado |
| `AddCarePlanAction` / `UpdateCarePlanAction` / `InvalidateCarePlanAction` | `actionId` | Descripción/responsable/plazo/nota; patch; motivo | `goalId` debe pertenecer al mismo plan |
| `AddCarePlanReview` | `reviewId` nuevo | `planId`,`reviewedAt?`,`summary`,`findings?`,`nextReviewDate?` | Registra lo comunicado; no crea hechos |
| `InvalidateCarePlanReview` | `reviewId` | `correctionReason?` | Terminal |

**Informes y adjuntos** (`diagnostic_reports read_write` para escrituras; `read` para lecturas y descarga):

| Acción | `entityKey` | Payload | Regla |
|---|---|---|---|
| `CreateDiagnosticReport` | `reportId` nuevo | `patientId`,`encounterId?`,`sourceName`,`sourceType`,`sampleDate?`,`issuedDate?`,`reportKind`,`reportStatus`,`clinicalSummary?`,`capturedAtLocal?` | Fechas parciales conservan precisión |
| `UpdateDiagnosticReport` | `reportId` | Patch de fuente/fechas/tipo/resumen/captura/`correctionReason` | No cambia ficha |
| `CorrectDiagnosticReport` | `reportId` | `correctionReason` y `results` completos vigentes | Versiona el informe, anula resultados anteriores y crea los corregidos en una aceptación; historias conservan el original |
| `AddDiagnosticReportResult` / `UpdateDiagnosticReportResult` / `InvalidateDiagnosticReportResult` | `resultId` | Nombre/valor/unidad/referencia según tipo | Numérico exige unidad; referencia solo del informe |
| `UploadReportAttachment` | `attachmentId` nuevo | `patientId`,`reportId?`,`fileName`,`contentType`,bytes | Verifica tamaño/tipo y calcula huella; bytes fuera de la transacción; no acredita informe |
| `LinkReportAttachment` | `attachmentId` | `reportId` | Vincula adjunto de la misma ficha |
| `InvalidateReportAttachment` | `attachmentId` | `correctionReason?` | Retira el adjunto del uso ordinario |

**Plantillas y registros** (`specialty_templates read_write`; las plantillas las configura el propietario):

| Acción | `entityKey` | Payload | Regla |
|---|---|---|---|
| `CreateSpecialtyTemplate` | `templateId` nuevo | `name`,`specialty`,`fields` | Versión 1; campos tipados, sin defaults clínicos |
| `UpdateSpecialtyTemplate` | `templateId` | `name?`,`changeNote`,`fields` completos | Publica versión nueva; versiones anteriores inmutables |
| `RetireSpecialtyTemplate` | `templateId` | — | No borra versiones ni registros |
| `CaptureSpecialtyRecord` | `recordId` nuevo | `patientId`,`encounterId?`,`templateId`,`recordedAt?`,`values` | Versión de plantilla vigente queda fija; valores ausentes no se generan |
| `UpdateSpecialtyRecord` / `InvalidateSpecialtyRecord` | `recordId` | Patch de valores/`correctionReason`; motivo | Conserva `templateVersion` aplicada |

### 12.5 Analítica, acceso, sync, auditoría y recuperación

`GET /analytics/series` exige `measurements read` y devuelve solo tomas válidas ordenadas `(measuredAt,id)` con `sourceMeasurementId`/`sourceVersion`; correcciones sustituyen el punto vigente sin duplicar. `GET /analytics/growth` exige `clinical_analytics read`, calcula la edad en cada medición desde el nacimiento y selecciona la referencia OMS por indicador/sexo/edad/método; fuera de rango, dato insuficiente o referencia inaplicable devuelve la medición con `limitExplanation`, sin curva inventada ni diagnóstico. Cambio de nacimiento o corrección recalcula en la consulta: los derivados no se persisten como hechos.

Captura: `clinicalSections` amplía su conjunto con `declaredMedications`,`carePlans`,`diagnosticReports`,`specialtyTemplates`; `clinicalAnalytics` no se descarga, se consulta online. La captura incluye medicación declarada vigente, planes vigentes con objetivos/acciones/revisiones vigentes, informes vigentes con resultados vigentes y referencias de adjuntos sin bytes, y registros de especialidad vigentes con su versión de plantilla; cada plantilla requerida aparece con `entityKey={templateId,version}` para distinguir versiones, incluso si está retirada; sin historias de versiones. El delta publica correcciones con versión actual y anulaciones como `entered-in-error`; los adjuntos y sus bytes quedan fuera de sync y se recuperan por ruta reautorizada.

Auditoría y recibos conservan las reglas de §11.5 con las cinco secciones nuevas; la autorización precede a duplicados, resultados, adjuntos y derivados. La respuesta perdida se recupera con la misma clave idempotente; una revocación entre reintento y resultado deniega sin filtrar. `SetMemberClinicalPermissions` acepta las trece secciones; payloads anteriores normalizan las omitidas a `read_write`.

`modelRevision=api-v1.4` se publicará al completar T34 con artefactos generados desde la app real; `contractVersion=1` se conserva.

Integración concurrente del 2026-11-17: el árbol de desarrollo de Etapa 3 añade la sección declared_medications, cuatro acciones y tres lecturas anteriores. Se conservan los ocho permisos y las acciones previas. Los demás bloques del §12 continúan como diseño futuro; esta integración no publica api-v1.4 ni acredita toda Etapa 3.

### 12.7 Primera especialidad: odontograma

Diseño de T22/T24 para C08, no implementado al redactarse; el diccionario clínico está en [patient-clinical-record.md §4.3.2](patient-clinical-record.md). Misma forma común de §12.1 con sección `specialty_templates`.

| Recurso | Rutas GET bajo `A/patients/{patient_id}` | Acceso y orden |
|---|---|---|
| Hallazgos | `/dental-findings`; `/dental-findings/{finding_id}`; `/dental-findings/{finding_id}/history` | `specialty_templates`; filtros `findingKind`,`findingStatus`,`toothFdi`,`recordStatus`; orden `(toothFdi,surface,id)` |
| Actuaciones | `/dental-findings/{finding_id}/treatments`; `/dental-treatments/{treatment_id}`; `/dental-treatments/{treatment_id}/history` | Misma sección; orden `(createdAt,id)` |

Acciones (`specialty_templates read_write`): `RecordDentalFinding` (pieza FDI, superficie nula o cerrada, tipo, nota, fecha), `UpdateDentalFinding`, `ResolveDentalFinding`, `InvalidateDentalFinding`, `AddDentalTreatment` (vinculada al hallazgo), `UpdateDentalTreatment` (incluye `planned`→`performed`), `InvalidateDentalTreatment`. Modelos: `DentalFindingResponse` (`findingId`,`toothFdi`,`surface`,`findingKind`,`findingStatus`,`note`,`recordedDate`) y `DentalTreatmentResponse` (`treatmentId`,`findingId`,`treatmentKind`,`treatmentStatus`,`performedDate`,`note`). Pieza FDI inválida, superficie fuera del conjunto o hallazgo duplicado vigente se rechazan; objeto ajeno = ausencia.


## 13. Diseño del vademecum global para C01

Diseño de [P-20261122-01-vademecum-read-api](../tasks/P-20261122-01-vademecum-read-api/plan.md) y [D20](decisions.md#d20--vademecum-venezolano-global-de-solo-lectura), implementado para revisión C05. No cambia `contractVersion`, `modelRevision`, el catálogo de operaciones ni sync. El contenido procede solo de `vademecum/vademecum_venezuela_2026-11-03.json`; no incluye `historicalProducts`, `supplementaryIngredients` ni `data.js`.

### 13.1 Rutas, acceso y errores

`A` equivale a `/v1/accounts/{account_id}`. Las cuatro rutas exigen token API, usuario y pertenencia activos, cuenta activa y dispositivo registrado activo. Owner y assistant tienen el mismo acceso; no se consulta una sección clínica ni un paciente. La autorización precede a la existencia del release y de los objetos.

| Método | Ruta | Respuesta | Consulta y orden |
|---|---|---|---|
| GET | `A/vademecum/products` | `VademecumProductPage` | `q`, `monographId`, `page`, `shows`; `(name,registrationNumber)` |
| GET | `A/vademecum/products/{registration_number}` | `VademecumProductResponse` | Registro exacto dentro del release activo |
| GET | `A/vademecum/monographs` | `VademecumMonographPage` | `q`, `page`, `shows`; `(name,id)` |
| GET | `A/vademecum/monographs/{monograph_id}` | `VademecumMonographResponse` | ID textual exacto dentro del release activo |

Los listados usan `page` desde 1, `shows=100` por defecto y máximo 500, LIMIT/OFFSET y `items`/`total`. Una página posterior al final devuelve `items=[]` y el total filtrado. Parámetros desconocidos o inválidos producen 422. Sin release activo, cualquiera de las cuatro rutas devuelve 503 `DEPENDENCY_UNAVAILABLE`, no una colección vacía. Un registro o ID ausente devuelve 404 `NOT_FOUND` después de autorizar. Credencial inválida: 401; cuenta/dispositivo inactivo o no registrado: 403; cuenta no visible, outsider o pertenencia inactiva: 404 por la guarda vigente.

No existen rutas de escritura, importación, revisión, histórico, datos suplementarios ni acceso público/paciente. Estas lecturas no crean auditoría clínica ni entidades de sincronización.

### 13.2 Contexto y modelos públicos

Toda respuesta incluye `catalog: VademecumCatalogContext` con `schemaVersion`, `registryCutoffDate`, `medicalNotice` y `sourceSha256` del release activo. El aviso se muestra junto al contenido; la huella identifica la fuente importada y no prueba revisión clínica.

| Modelo | Campos y significado |
|---|---|
| `VademecumProduct` | `registrationNumber`, `name`, `activeIngredientText`, `approvedAt`, `validUntil`, `representative`, `manufacturer` nulo si falta, `monographIds`, `combinationMonographIds`, `canonicalIngredientIds`, `ingredientLinkStatus`, `ingredientResolution`, `productReference` opcional |
| `VademecumProductReference` | `scope`, `monographIds`, `sources`, `matchNote`; evidencia de referencia para ese producto, no una sustitución del estado de vínculo |
| `VademecumReferenceSource` | `title`, `url`; referencia externa conservada sin descargar ni comprobar su contenido en esta entrega |
| `VademecumProductPage` | `catalog`, `items[VademecumProduct]`, `total` |
| `VademecumProductResponse` | `catalog`, `product` |
| `VademecumMonographSummary` | `id`, `name`, `sismedAliases`, `atc{code,description}`, `review{status,date,reviewer}` |
| `VademecumMonographPage` | `catalog`, `items[VademecumMonographSummary]`, `total` |
| `VademecumMonographResponse` | `catalog`, `monograph` con el documento completo del esquema 1.0.0 |

El detalle de monografía conserva todas las secciones clínicas, formas, especialidades de referencia, poblaciones, seguridad, perfil farmacológico, grupo terapéutico, fuentes, procedencia y revisión definidos por `monograph.schema.json`. `referenceSpecialties` conserva país y no representa aprobación venezolana. `review.status=pending_local_review` y sus campos nulos permanecen visibles; no se convierten en revisión profesional aceptada.

`ingredientLinkStatus` admite exactamente `complete`, `unlinked`, `missing_ingredient`, `historical_complete`, `product_reference`, `inferred_complete`, `combination_only`, `historical_partial`, `inferred_partial`, `partial`. `ingredientResolution` admite `source_text`, `historical_product_match`, `unresolved`, `product_name_inference`, `product_reference`. Estos estados describen la calidad de la vinculación; no afirman que el contenido histórico o suplementario excluido esté disponible.

Mapeo fuente→público de producto: `ef`→`registrationNumber`; `nombre`→`name`; `principioActivo`→`activeIngredientText`; `fechaAprobado`→`approvedAt`; `fechaVigencia`→`validUntil`; `representante`→`representative`; `fabricante`→`manufacturer`; `productMonographReference`→`productReference`. Los demás campos públicos conservan su nombre y significado fuente. No se exponen `id`, `sortId`, `rifRepresentante`, `patrocinante`, `premium`, `oficios`, `fechaCancelado`, `supplementaryIngredientIds`, identificadores de usuarios/documentos de la fuente ni administración no seleccionada.

### 13.3 Búsqueda acotada

Python normaliza `q` y los textos persistidos con Unicode NFKD, elimina marcas diacríticas, pasa a minúsculas y pliega espacios. La coincidencia es una subcadena literal; `%`, `_` y el carácter de escape se escapan antes de SQL LIKE/ILIKE. No se añade texto completo, ranking, fuzzy search ni una extensión PostgreSQL.

- Productos: nombre, registro, `activeIngredientText`, IDs canónicos y, solo de monografías vinculadas al producto, nombre, alias y ATC.
- Monografías: nombre, `sismedAliases` y código ATC.
- `monographId` filtra productos por cualquier vínculo simple o de combinación del mismo release antes de contar y paginar.

Nunca se indexan ni consultan mecanismo, indicaciones, posología, seguridad, fuentes, procedencia u otro texto clínico para `q`.

## 14. Diseño de suscripciones de cuenta para C03

Diseño de [P-20261117-02-account-subscriptions](../tasks/P-20261117-02-account-subscriptions/plan.md) según [account-subscriptions.md](account-subscriptions.md) y las decisiones D21–D24. Pendiente de aceptación e implementación; no cambia `contractVersion` ni las rutas existentes. Física en [database-schema.md](database-schema.md) §§17–18.

### 14.1 Actores y acceso

Dos ámbitos separados que nunca se mezclan en una misma ruta:

- **Cuenta:** rutas bajo `A` con token de dispositivo y pertenencia activa. Todas las acciones de suscripción son del **propietario**; el asistente no recibe permiso de suscripción por defecto (§6.2 de la especificación). La autorización precede a la existencia del objeto: un reporte o evidencia de otra cuenta devuelve el mismo 404 `NOT_FOUND` que uno inexistente.
- **Operador:** rutas bajo `/v1/operator` con credencial de operador vigente (D23). La credencial no es un token de dispositivo de cuenta: no abre ninguna ruta bajo `A` ni ninguna ruta clínica, y un token de dispositivo del personal no abre las rutas de operador. Cada ruta exige su acción de plataforma: `review` (bandeja, detalle, evidencia, aprobación, rechazo), `catalog` (planes y versiones), `rates` (tasas BCV) u `operators` (gestión de operadores).

### 14.2 Rutas de la cuenta

Todas exigen propietario con dispositivo registrado activo. Las escrituras son online, con `operationId` UUIDv7 generado por el cliente para idempotencia y recuperación de respuesta perdida, igual que la aceptación de invitaciones; no pasan por el lote de operaciones de sync.

| Método | Ruta | Respuesta | Entrada / comportamiento |
|---|---|---|---|
| GET | `A/subscription` | `SubscriptionResponse` | plan y versión vigentes, estado, periodo actual, fin de gracia cuando aplique, asientos usados/límite, `subscriptionVersion` |
| POST | `A/subscription/quotes` | `QuoteResponse` | `QuoteRequest{operationId, planCode, periodicity}`; 201; conserva USD, tasa, fecha/fuente BCV y VES calculado (§9.2); no activa nada |
| POST | `A/subscription/reports` | `PaymentReportResponse` | `PaymentReportCreateRequest{operationId, planCode, periodicity, declaredPaidOn, declaredAmount, declaredCurrency, declaredMethod, declaredReferenceLast4?, declaredNote?, previousReportId?}`; 201; deja `pending`, sin activar ni extender |
| GET | `A/subscription/reports` | `PaginatedResponse<PaymentReportResponse>` | `page`, `shows`, filtro `status`; solo reportes de la cuenta |
| GET | `A/subscription/reports/{report_id}` | `PaymentReportDetailResponse` | declaración, estado, evidencia (metadatos) y, si fue revisado, resultado visible para la cuenta: decisión, periodo concedido o motivo seguro |
| POST | `A/subscription/reports/{report_id}/evidence` | `PaymentReportEvidenceResponse` | multipart; una captura por reporte (D24); JPG/PNG/PDF validado por firma real, máximo 5 MB; 409 `EVIDENCE_ALREADY_PRESENT` si ya existe; solo mientras el reporte está `pending` |
| GET | `A/subscription/reports/{report_id}/evidence` | archivo | descarga reautorizada del propietario; `Content-Disposition` con nombre generado; nunca URL pública |
| POST | `A/subscription/plan-changes` | `SubscriptionResponse` | `PlanChangeRequest{operationId, expectedVersion, planCode}`; aplica al siguiente periodo aprobado (D24); un plan inferior exige asientos dentro del límite o política de exceso D21 |
| POST | `A/subscription/cancellation` | `SubscriptionResponse` | `CancellationRequest{operationId, expectedVersion}`; conserva el tiempo pagado; no borra datos |

Presentar un reporte no cambia estado ni vigencia. El cliente no elige operador, resultado ni periodo. `accountId` de ruta se contrasta con la identidad autenticada en cada caso.

### 14.3 Rutas del operador

Prefijo `/v1/operator`, credencial de operador vigente. La emisión de credencial usa el access token OIDC de la identidad de operador registrada, siguiendo el patrón de `/v1/auth/device-tokens`; el alta inicial del primer operador es un flujo administrativo de despliegue fuera del servidor (D23).

| Método | Ruta | Acción | Respuesta | Entrada / comportamiento |
|---|---|---|---|---|
| POST | `/v1/operator/credentials` | identidad OIDC de operador | `OperatorTokenIssued` | 201; entrega el secreto una sola vez; solo huella persistida |
| GET | `/v1/operator/payment-reports` | `review` | `PaginatedResponse<OperatorPaymentReportResponse>` | `page`, `shows`, filtros `status`, `accountId`, `from`, `until`; orden `(createdAt, id)` |
| GET | `/v1/operator/payment-reports/{report_id}` | `review` | `OperatorPaymentReportDetailResponse` | declaración completa, metadatos de evidencia, historial de presentaciones vinculadas y advertencias de coincidencia de referencia parcial (nunca rechazo automático) |
| GET | `/v1/operator/payment-reports/{report_id}/evidence` | `review` | archivo | descarga reautorizada en cada petición |
| POST | `/v1/operator/payment-reports/{report_id}/approval` | `review` | `ApprovalResultResponse` | `ApprovalRequest{operationId, expectedVersion, verifiedPaidOn, verifiedAmount, verifiedCurrency, bcvRateId?}`; confirma revisión, estado, periodo, suscripción, recibo y auditoría en una transacción; 409 `REPORT_NOT_PENDING` si ya fue decidido |
| POST | `/v1/operator/payment-reports/{report_id}/rejection` | `review` | `PaymentReportResponse` | `RejectionRequest{operationId, expectedVersion, reason}`; motivo seguro sin datos bancarios completos; la suscripción conserva su estado anterior |
| GET | `/v1/operator/bcv-rates` | `rates` | `PaginatedResponse<BcvRateResponse>` | `page`, `shows`, rango `from`/`until` por `rateDate` |
| POST | `/v1/operator/bcv-rates` | `rates` | `BcvRateResponse` | `BcvRateCreateRequest{operationId, rateDate, rateVesPerUsd, source}`; 201; 409 `RATE_DATE_EXISTS` si la fecha ya tiene tasa |
| GET | `/v1/operator/plans` | `catalog` | `PaginatedResponse<OperatorPlanResponse>` | planes con sus versiones e historia |
| POST | `/v1/operator/plans/{code}/versions` | `catalog` | `OperatorPlanResponse` | `PlanVersionCreateRequest{operationId, expectedVersion, seatLimit, price30dUsd, priceYearUsd}`; crea la versión siguiente; las anteriores quedan intactas |
| POST | `/v1/operator/plans/{code}/retirement` | `catalog` | `OperatorPlanResponse` | `PlanRetirementRequest{operationId, expectedVersion}`; impide nuevas contrataciones, conserva historia |
| GET | `/v1/operator/operators` | `operators` | `PaginatedResponse<OperatorResponse>` | operadores con estado; sin huellas ni secretos |
| POST | `/v1/operator/operators` | `operators` | `OperatorResponse` | `OperatorCreateRequest{operationId, oidcIssuer, oidcSubject, displayName, actions}`; 201; `actions` es un subconjunto no vacío de `review`, `catalog`, `rates`, `operators`, `metrics` |
| GET | `/v1/operator/metrics/subscriptions` | `metrics` | `SubscriptionMetricsResponse` | indicadores administrativos acotados (§22 de la especificación): cuentas por plan/estado, vigencias próximas, pendientes con antigüedad, periodos por plan/periodicidad, importes verificados por moneda sin mezclar ni revalorizar, y cuentas sobre el límite de asientos |
| POST | `/v1/operator/operators/{operator_id}/revocation` | `operators` | `OperatorResponse` | revoca operador y sus credenciales en una transacción |
| POST | `/v1/operator/operators/{operator_id}/credential-recovery` | `operators` | `OperatorTokenIssued` | revoca credenciales anteriores y emite una nueva; nunca recupera secretos |

Un operador no puede aprobar con una tasa elegida por el cliente: `bcvRateId` referencia una tasa registrada, y la regla de selección (fecha del pago verificada, si no la más reciente anterior) se comprueba en el caso de uso (D22). Aprobar un reporte cuyo importe verificado no cubre el debido devuelve 422 `PAYMENT_MISMATCH`; el operador debe rechazar en su lugar (D24).

### 14.4 Modelos públicos

| Modelo | Campos |
|---|---|
| `SubscriptionResponse` | `plan{code, name}`, `planVersion{version, seatLimit, price30dUsd, priceYearUsd, currency}`, `status`, `currentPeriod{startsAt, endsAt, periodicity}` nulo si no hay, `graceEndsAt` nulo salvo gracia, `seats{used, limit}`, `subscriptionVersion`, `updatedAt` |
| `QuoteRequest` | `operationId`, `planCode` (`independent`, `smallPractice`, `medicalCenter`), `periodicity` (`days_30`, `year_1`) |
| `QuoteResponse` | `quoteId`, `planCode`, `planVersion`, `periodicity`, `amountUsd`, `bcvRate`, `bcvRateDate`, `bcvRateSource`, `amountVes`, `roundingRule`, `quotedAt` |
| `PaymentReportResponse` | `reportId`, `planCode`, `periodicity`, `status`, `declared{paidOn, amount, currency, method, referenceLast4?, note?}`, `evidence` metadatos o nulo, `previousReportId` nulo si no aplica, `createdAt`, `version` |
| `PaymentReportDetailResponse` | lo anterior más `review{decision, decidedAt, grantedPeriod{startsAt, endsAt}?, reason?}` nulo mientras `pending` |
| `PaymentReportEvidenceResponse` | `contentType`, `sizeBytes`, `sha256`, `uploadedAt`; nunca `storageKey` ni URL |
| `ApprovalRequest` | `operationId`, `expectedVersion`, `verifiedPaidOn`, `verifiedAmount`, `verifiedCurrency` (`VES`, `USD`), `bcvRateId` obligatorio si la moneda verificada es `VES` |
| `ApprovalResultResponse` | `reportId`, `decision`, `grantedPeriod{startsAt, endsAt, periodicity, sequence}`, `subscription{status, subscriptionVersion}`, `duplicate` para recuperación idempotente |
| `BcvRateResponse` | `rateId`, `rateDate`, `rateVesPerUsd`, `source`, `registeredAt` |
| `OperatorTokenIssued` | `operatorId`, `token` (una sola vez), `issuedAt`; `Cache-Control: no-store` |

Los importes viajan como texto decimal con dos fracciones (`"18.00"`), la tasa con hasta seis; nunca como número binario de punto flotante. `referenceLast4` es texto de exactamente cuatro dígitos y conserva ceros iniciales.

### 14.5 Errores específicos

Además de los códigos vigentes (401 credencial inválida, 403 sin permiso, 404 objeto ajeno o inexistente, 409 versión/duplicado, 422 validación):

| Código | HTTP | Significado |
|---|---|---|
| `SUBSCRIPTION_SUSPENDED` | 403 | escritura operativa bloqueada por suspensión comercial; la lectura y la renovación siguen disponibles (D24) |
| `SEAT_LIMIT_REACHED` | 409 | aceptación/reactivación/cambio superaría el límite de asientos |
| `PLAN_UNAVAILABLE` | 409 | plan retirado o no disponible para nuevas contrataciones |
| `REPORT_NOT_PENDING` | 409 | el reporte ya fue aprobado o rechazado |
| `EVIDENCE_ALREADY_PRESENT` | 409 | el reporte ya tiene su captura (una por reporte) |
| `PAYMENT_MISMATCH` | 422 | importe verificado insuficiente o excedente; corresponde rechazo |
| `RATE_DATE_EXISTS` | 409 | ya existe tasa para esa fecha |

La indisponibilidad comercial nunca se presenta como credencial inválida (§17.4 de la especificación). Un objeto de otra cuenta sigue devolviendo 404 antes de revelar cualquier situación comercial.

### 14.6 Proyección de sincronización

El snapshot/delta añade una proyección comercial mínima por audiencia (§18 de la especificación): la entidad `subscription` (audiencia `members`) lleva `planCode`, `status`, `currentPeriodEndsAt`, `graceEndsAt`, `subscriptionVersion` y `updatedAt`; la entidad `subscription_admin` (audiencia `owner`) añade `seats{used, limit}`. Reportes, tasas, motivos de revisión y evidencias no aparecen en snapshot, delta, SSE, journal, logs ni métricas. La versión comercial es independiente de `permissionEpoch` salvo que una política cambie el alcance de lectura. El reloj del cliente no extiende vigencia; la política offline aplica el fin de gracia comunicado por el servidor (D24).

El delta (`change_log`) solo registra los cambios comerciales causados por operaciones del personal con recibo (la primera presentación que crea la relación, acción `SubmitPaymentReport`). Las decisiones del operador no tienen dispositivo de miembro y por tanto no generan fila de delta: los consumidores recuperan aprobaciones y rechazos mediante la captura (snapshot), que siempre refleja el estado vigente.

## 15. Diseño de facturación de pacientes para C03

Diseño de [P-20261117-03-patient-billing](../tasks/P-20261117-03-patient-billing/plan.md) según [patient-billing.md](patient-billing.md) y las decisiones D25–D28. Pendiente de aceptación e implementación; no cambia `contractVersion` ni las rutas existentes. Física en [database-schema.md](database-schema.md) §§19–20.

### 15.1 Actores y acceso

Tres ámbitos separados que nunca se mezclan en una misma ruta:

- **Personal:** rutas bajo `A/billing` con token de dispositivo y pertenencia activa. Exigen las acciones financieras agrupadas de D27: `billing_read` (consultas y analítica), `billing_charges` (borradores, emisión, cancelación y ajustes) y `billing_review` (revisión, aprobación/rechazo, `staff_entry`, anulaciones y tasas). El propietario las tiene todas; los asistentes solo lo concedido explícitamente. Ningún permiso clínico abre estas rutas ni estas rutas abren contenido clínico. La autorización precede a la existencia del objeto: un cargo, reporte, pago o evidencia de otra cuenta devuelve el mismo 404 `NOT_FOUND` que uno inexistente.
- **Paciente:** rutas bajo `/v1/patient/billing` con el secreto opaco de una concesión `patient_billing_grants` (D28) en `Authorization: Bearer`. No hay cuenta de paciente ni token de dispositivo. API valida huella, vigencia, revocación y acción incluida (`read_charge`, `submit_report`, `read_result`, `read_receipt`); un enlace vencido, revocado o ajeno devuelve el mismo 404 `NOT_FOUND` sin revelar existencia. Conocer el UUID de la concesión no autoriza nada.
- **Precios:** la escritura de precios base/oferta usa el permiso propio de catálogo/oferta existente (D27), no las acciones de facturación.

### 15.2 Rutas del personal

Las escrituras son online, con `operationId` UUIDv7 generado por el cliente para idempotencia y recuperación de respuesta perdida, igual que §14.2; los borradores offline llegan como operaciones tipadas del lote de sync (D28) y se revalidan al aceptarse.

| Método | Ruta | Acción | Respuesta | Entrada / comportamiento |
|---|---|---|---|---|
| PUT | `A/services/{service_id}/price` | catálogo | `ServicePriceResponse` | `ServicePricePutRequest{operationId, expectedVersion, amount, currency}`; precio base del profesional propietario; `amount` texto decimal ≥ 0 (cero = gratuito) |
| PUT | `A/professional-services/{professional_id}/{service_id}/price` | oferta | `OfferPriceResponse` | `OfferPricePutRequest{operationId, expectedVersion, amount, currency}`; ajuste de la oferta; DELETE de la misma ruta retira el ajuste y vuelve al base |
| GET | `A/billing/price-resolution` | `billing_read` | `PriceResolutionResponse` | `serviceId` (+ oferta de la cuenta); devuelve `source` (`offer`, `base`) o 404 `PRICE_NOT_DEFINED` si no hay precio |
| GET | `A/billing/charges` | `billing_read` | `PaginatedResponse<ChargeResponse>` | `page`, `shows`, filtros `patientId`, `status`, `currency`, `from`, `until` por emisión |
| GET | `A/billing/charges/{charge_id}` | `billing_read` | `ChargeDetailResponse` | cargo, saldo, historia y pagos vigentes/anulados |
| GET | `A/billing/reports` | `billing_review` | `PaginatedResponse<PaymentReviewItemResponse>` | bandeja; `page`, `shows`, filtros `status`, `chargeId`, `patientId`, `from`, `until`; orden `(createdAt, id)` |
| GET | `A/billing/reports/{report_id}` | `billing_review` | `PaymentReviewDetailResponse` | declaración completa, metadatos de evidencia, cadena de presentaciones y advertencias de coincidencia de referencia parcial (nunca rechazo automático) |
| GET | `A/billing/reports/{report_id}/evidence` | `billing_review` | archivo | descarga reautorizada en cada petición; `Content-Disposition` con nombre generado |
| POST | `A/billing/reports/{report_id}/approval` | `billing_review` | `ApprovalResultResponse` | `BillingApprovalRequest{operationId, expectedVersion, verifiedPaidOn, verifiedAmount, verifiedCurrency, billingExchangeRateId?}`; confirma revisión, estado, pago, saldo bajo bloqueo del cargo, historia, recibo, auditoría y journal en una transacción; 409 `REPORT_NOT_PENDING`; 422 `PAYMENT_EXCEEDS_BALANCE` si excede el saldo (D26) |
| POST | `A/billing/reports/{report_id}/rejection` | `billing_review` | `PaymentReviewItemResponse` | `RejectionRequest{operationId, expectedVersion, reason}`; sin pago ni cambio de saldo; permite nueva presentación |
| POST | `A/billing/charges/{charge_id}/payments` | `billing_review` | `PaymentResponse` | `DirectPaymentRequest{operationId, expectedVersion, paidOn, amount, currency, method, referenceLast4?, evidenceNote}`; origen `staff_entry` distinguible; misma coordinación de saldo; 422 `PAYMENT_EXCEEDS_BALANCE` |
| POST | `A/billing/payments/{payment_id}/annulment` | `billing_review` | `PaymentResponse` | `PaymentAnnulmentRequest{operationId, expectedVersion, reason}`; el pago deja de sumar al vigente; no afirma devolución (D27) |
| GET | `A/billing/payments/{payment_id}/receipt` | `billing_read` | archivo | comprobante PDF no fiscal; descarga reautorizada |
| GET | `A/billing/exchange-rates` | `billing_review` | `PaginatedResponse<BillingRateResponse>` | `page`, `shows`, rango `from`/`until` por `rateDate` |
| POST | `A/billing/exchange-rates` | `billing_review` | `BillingRateResponse` | `BillingRateCreateRequest{operationId, rateDate, rateVesPerUsd, source}`; 201; 409 `RATE_DATE_EXISTS` |
| POST | `A/billing/grants` | `billing_review` | `GrantIssuedResponse` | `GrantCreateRequest{operationId, patientId, appointmentId?, chargeId?, actions}`; al menos un objeto; entrega el secreto una sola vez; vigencia según D28 |
| POST | `A/billing/grants/{grant_id}/revocation` | `billing_review` | `GrantResponse` | revoca de inmediato; el reporte ya presentado conserva su historia |
| GET | `A/billing/grants` | `billing_read` | `PaginatedResponse<GrantResponse>` | `page`, `shows`, filtros `patientId`, `chargeId`, `status`; sin huellas ni secretos |
| GET | `A/billing/metrics` | `billing_read` | `BillingMetricsResponse` | los siete indicadores de §19.1 de la especificación con fechas de D28; filtros `from`, `until`, `professionalId`, `serviceId`, `patientId`, `currency`; totales separados por moneda |

### 15.3 Rutas del paciente

Prefijo `/v1/patient/billing`, `Authorization: Bearer <secreto de concesión>`. La proyección es mínima (§9.3 de la especificación): sin notas internas, sin otros cargos, sin contenido clínico.

| Método | Ruta | Acción de concesión | Respuesta | Entrada / comportamiento |
|---|---|---|---|---|
| GET | `/v1/patient/billing/charge` | `read_charge` | `PatientChargeResponse` | descripción, importe, moneda, saldo, estado de revisión; solo el cargo de la concesión; estimación no vinculante disponible antes del cargo emitido (D25) cuando la concesión nace de una cita con servicio |
| POST | `/v1/patient/billing/reports` | `submit_report` | `PatientReportResponse` | multipart: campos declarados obligatorios de D26 (`paidOn`, `amount`, `currency`, `method`) más captura obligatoria (JPG/PNG/PDF, máx. 5 MB, firma real) en la misma operación; `operationId` para idempotencia; 201 deja `pending` sin cambiar saldo |
| GET | `/v1/patient/billing/reports` | `read_result` | `PaginatedResponse<PatientReportResponse>` | solo reportes presentados con esta concesión o sobre el mismo objeto |
| GET | `/v1/patient/billing/reports/{report_id}` | `read_result` | `PatientReportDetailResponse` | estado y resultado visible: aprobado con datos mínimos del pago o motivo seguro de rechazo; nunca observación interna |
| GET | `/v1/patient/billing/payments/{payment_id}/receipt` | `read_receipt` | archivo | comprobante no fiscal del pago aplicado a su cargo |

Presentar crea `pending` y nunca aprueba ni altera el saldo. Tras un rechazo, el paciente presenta de nuevo con `previousReportId`; un reporte aprobado no se reabre. La respuesta perdida se recupera repitiendo con el mismo `operationId` o consultando `read_result`.

### 15.4 Modelos públicos

| Modelo | Campos |
|---|---|
| `ChargeResponse` | `chargeId`, `patientId`, `appointmentId?`, `encounterId?`, `serviceId?`, `description`, `amount`, `currency`, `priceSource` (`offer`, `base`, `manual`), `status` (`draft`, `issued`, `cancelled`), `balance{paid, outstanding, state}` con `state` en `unpaid`, `partially_paid`, `paid`, `issuedAt?`, `cancelledAt?`, `createdAt`, `version` |
| `ChargeDetailResponse` | lo anterior más `history[]` (acción, actor, motivo, instante) y `payments[]` (pago, origen, estado) |
| `PriceResolutionResponse` | `serviceId`, `source`, `amount`, `currency`, `resolvedAt`; nunca reserva precio |
| `PaymentReviewItemResponse` | `reportId`, `chargeId`, `patientId`, `status`, `declared{paidOn, amount, currency, method, referenceLast4?, note?}`, `evidence` metadatos, `previousReportId?`, `createdAt`, `version` |
| `PaymentReviewDetailResponse` | lo anterior más `review{decision, reviewer, decidedAt, verified?, internalNote?, reason?}` nulo mientras `pending` |
| `ApprovalResultResponse` | `reportId`, `decision`, `payment{paymentId, amount, currency, status}`, `charge{chargeId, balance}`, `duplicate` para recuperación idempotente |
| `PaymentResponse` | `paymentId`, `chargeId`, `origin` (`patient_report`, `staff_entry`), `amount`, `currency`, `exchangeRate?`, `exchangeRateDate?`, `exchangeRateSource?`, `paidOn`, `method`, `referenceLast4?`, `status`, `registeredBy`, `createdAt`, `version` |
| `PatientChargeResponse` | `description`, `amount`, `currency`, `balance{outstanding, state}`, `issuedAt`, `reviewState` del último reporte propio |
| `PatientReportResponse` | `reportId`, `status`, `declared{paidOn, amount, currency, method}`, `createdAt` |
| `PatientReportDetailResponse` | lo anterior más `result{decision, decidedAt, payment{amount, currency, paidOn}?, reason?}` nulo mientras `pending` |
| `GrantCreateRequest` | `operationId`, `patientId`, `appointmentId?`, `chargeId?`, `actions` subconjunto no vacío de `read_charge`, `submit_report`, `read_result`, `read_receipt` |
| `GrantIssuedResponse` | `grantId`, `secret` (una sola vez), `actions`, `expiresAt`; `Cache-Control: no-store` |
| `GrantResponse` | `grantId`, `patientId`, `appointmentId?`, `chargeId?`, `actions`, `expiresAt`, `revokedAt?`, `status` (`active`, `expired`, `revoked`) |
| `BillingRateResponse` | `rateId`, `rateDate`, `rateVesPerUsd`, `source`, `registeredAt` |
| `BillingMetricsResponse` | `charged`, `collected`, `outstanding`, `pendingReview`, `partiallyPaid`, `paidCharges`, `annulments`; cada importe como lista por moneda `{currency, amount}`; `basis{chargedBy: issueDate, collectedBy: approvalDate}` (D28), `from`, `until` |

Los importes viajan como texto decimal con dos fracciones y las tasas con hasta seis; nunca punto flotante binario. Nulo significa «sin precio definido» y cero un precio gratuito válido (D25). La evidencia y los comprobantes nunca exponen `storageKey` ni URL.

### 15.5 Errores específicos

Además de los códigos vigentes (401, 403, 404 uniforme, 409 versión/duplicado, 422 validación):

| Código | HTTP | Significado |
|---|---|---|
| `PRICE_NOT_DEFINED` | 404 | el servicio no tiene precio base ni de oferta; distinto de precio cero |
| `CHARGE_NOT_DRAFT` | 409 | la edición exige estado `draft` |
| `CHARGE_NOT_ISSUED` | 409 | la operación exige un cargo emitido |
| `CHARGE_HAS_ACTIVE_PAYMENTS` | 409 | cancelación con pagos vigentes; anular primero (D27) |
| `PAYMENT_EXCEEDS_BALANCE` | 422 | el importe verificado excede el saldo; corresponde rechazo (D26) |
| `REPORT_NOT_PENDING` | 409 | el reporte ya fue aprobado o rechazado |
| `EVIDENCE_ALREADY_PRESENT` | 409 | el reporte ya tiene su captura |
| `RATE_DATE_EXISTS` | 409 | ya existe tasa para esa fecha en la cuenta |
| `GRANT_OBJECT_REQUIRED` | 422 | la concesión exige cita o cargo concreto |

Un enlace vencido, revocado, ajeno o con acción no concedida devuelve 404 `NOT_FOUND`, nunca un código que confirme la existencia del objeto (D28).

### 15.6 Idempotencia, transacciones y archivos

- Aprobación, pago directo y anulación confirman en una sola transacción: decisión/pago, saldo verificado bajo el bloqueo de la fila del cargo, historia, recibo de operación, auditoría y grupo del journal. Las lecturas de archivos y cualquier red ocurren fuera.
- La presentación del paciente confirma reporte, metadatos de evidencia, recibo y auditoría juntos; los bytes se escriben fuera de la transacción y un fallo posterior deja a lo sumo un archivo huérfano sin efecto.
- Una respuesta perdida se recupera con el mismo `operationId` sin duplicar reporte, captura, pago ni efecto; `duplicate: true` identifica la recuperación.
- Las descargas de evidencia y comprobante se reautorizan en cada petición; los bytes nunca viajan en snapshot, delta, SSE, journal, logs ni auditoría.

La proyección de sincronización, las audiencias financieras y la analítica se diseñan en T08 y se documentarán en la sección siguiente.

## 16. Diseño de sincronización y analítica de facturación para C03

Diseño de T08 de [P-20261117-03-patient-billing](../tasks/P-20261117-03-patient-billing/plan.md). Pendiente de aceptación e implementación; extiende §7–§8 sin cambiar las reglas existentes de snapshot/delta/SSE.

### 16.1 Audiencia financiera

Se añade la audiencia cerrada `billing`, separada de `members`, `owner` y las audiencias clínicas (§16.1 de la especificación). Solo los miembros con `billing_read` vigente reciben las proyecciones financieras en su alcance; la revisión completa (bandeja, declaración, evidencia) no se proyecta y sigue siendo consulta online con `billing_review`.

| Entidad | Audiencia | Campos proyectados |
|---|---|---|
| `billing_charge` | `billing` | `chargeId`, `patientId`, `appointmentId?`, `description`, `amount`, `currency`, `status`, `balance{paid, outstanding, state}`, `issuedAt?`, `chargeVersion`, `updatedAt` |
| `billing_payment` | `billing` | `paymentId`, `chargeId`, `patientId`, `origin` (`patient_report`, `staff_entry`), `amount`, `currency`, `status`, `paidOn`, `registeredBy`, `updatedAt` |

Borradores (`draft`) no se proyectan a ninguna audiencia: solo cargos emitidos o cancelados. Capturas, comprobantes, referencias bancarias, notas internas, tasas y secretos de concesión nunca aparecen en snapshot, delta, SSE, journal, logs ni métricas; los grupos invisibles permiten avanzar el cursor sin cuerpos (§16.2). Un cambio de permiso financiero invalida las capturas/cursores del alcance afectado igual que un cambio de permisos clínico.

### 16.2 Delta y recuperación

El `change_log` registra los cambios financieros causados por operaciones del lote con recibo: creación/edición/emisión/cancelación de cargos. **Decisión descubierta en la implementación (T24):** `change_log` exige un recibo de operación de un miembro con dispositivo (misma restricción documentada en §14.6), por lo que la aprobación, el rechazo, el `staff_entry` y la anulación —rutas HTTP con `operationId`, sin recibo de lote— **no generan fila de delta**: los consumidores los recuperan por la captura (snapshot), que siempre refleja cargos con saldo y pagos vigentes/anulados. Las presentaciones del paciente con concesión tampoco generan delta (sin dispositivo de miembro) y se recuperan por la bandeja online y el snapshot. Una aprobación con aviso perdido se recupera por snapshot sin duplicar el pago. Las concesiones y sus revocaciones no se proyectan: su gestión y validación son online.

### 16.3 Propiedad de integración

- `billing` posee cargos, reportes, pagos, comprobantes, tasas y concesiones. La concesión del paciente vive en `billing`; ningún otro componente la interpreta.
- `services` resuelve el precio efectivo mediante un caso de uso público; `billing` consume ese caso y congela la instantánea en el cargo. Ningún componente importa repositorios ajenos.
- `appointments`/`encounters` solo aportan validación de vínculo (misma cuenta/paciente) por casos/tipos públicos; crear/completar/cancelar citas o atenciones nunca genera cargos.
- La cancelación de una cita revoca sus concesiones ancladas dentro de la misma aceptación (D28), coordinada por el caso de uso de citas con el caso público de `billing`.

### 16.4 Analítica

El primer panel (D28) se sirve con `GET A/billing/metrics` (§15.2) sobre consultas acotadas de la base operativa: siete indicadores, filtros cerrados, totales por moneda sin revalorizar, cargado/saldo por fecha de emisión y cobrado por fecha de aprobación. Los indicadores no leen evidencias ni contenido clínico y exigen `billing_read`. La analítica histórica pesada pertenece al componente `analytics` y su PostgreSQL separado; si el volumen lo exige, `billing` emitirá hechos mínimos (cuenta, tipo de hecho, importe, moneda, fechas, referencias) hacia el cursor ETL existente, sin capturas ni datos bancarios. Ninguna necesidad de gráficos habilita consultas sin límite sobre la transacción operativa.
