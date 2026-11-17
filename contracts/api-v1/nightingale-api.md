# Nightingale API: especificación y guía para el escritorio

**Corte:** 2026-11-16. **Contrato remoto:** `1`. **Revisión de modelos:** `api-v1.3`. **Aplicación API:** `0.1.0`.

Esta es la referencia portable para el repositorio `nightingale`. Explica qué ofrece Nightingale API, cómo consumirla y qué debe resolver el escritorio. Los JSON adjacentes fijan las formas ejecutables; esta guía no los sustituye ni crea otra definición editable. Todos los ejemplos son ficticios.

## 1. Paquete del contrato

Conservar juntos estos archivos:

| Archivo | Contenido y uso |
|---|---|
| [openapi.json](openapi.json) | OpenAPI 3.1: 78 rutas y 127 esquemas HTTP reales. |
| [public-models.schema.json](public-models.schema.json) | Los mismos modelos públicos en `$defs`, con referencias locales. |
| [accepted-operations.schema.json](accepted-operations.schema.json) | Envoltorio y payloads de las 66 acciones aceptadas por lote. |
| [sse.schema.json](sse.schema.json) | Eventos `changes_available`, `heartbeat` y `access_revoked`. |
| [capabilities.json](capabilities.json) | Revisión, acciones, acciones online, límites y modelos de payload. |
| [manifest.json](manifest.json) | Origen, HEAD, huella de fuentes y SHA-256 de los cinco JSON anteriores. |
| [examples.json](../examples.json) | Solicitudes ficticias comprobadas contra los modelos y servicios de prueba. |
| `nightingale-api.md` | Esta especificación y guía de consumo. |

El origen editable está en `nightingale-api`: `src.application:app` y los esquemas Pydantic de `src/api/*/domain`. El generador es `scripts/export_contracts.py`. No editar los JSON en el escritorio ni regenerar solo una parte del paquete.

`sourceHead` identifica el commit de referencia. `sourceSha256` cubre también los cambios locales de las fuentes incluidas por el exportador. Fijar una revisión o huella al implementar el consumidor.

OpenAPI describe HTTP. `accepted-operations.schema.json` distingue el payload de cada acción dentro del mismo endpoint de lotes. JSON Schema no expresa todas las reglas de negocio ni concede permisos.

## 2. Propósito, arquitectura y límites

Nightingale API autoriza y acepta el estado compartido. Usa Python, FastAPI y PostgreSQL operativo privado. No ofrece SQL, acceso libre a tablas ni guardado ciego de objetos.

| Proyecto | Responsabilidad |
|---|---|
| Escritorio `nightingale` | React/Tauri para interfaz; Rust para casos de uso y acceso remoto; SQLite para datos locales, Outbox e intenciones pendientes. El trabajo local permitido no necesita red. |
| `nightingale-api` | Autenticación de servidor, autorización vigente, aceptación transaccional, historial, auditoría, resultados, capturas, delta y avisos. |
| Patient Hub | Interfaz web en otro repositorio. API poseerá todas sus funciones de servidor; no hay backend, almacén ni credenciales SQL propios del Hub. |

El contrato actual sirve al escritorio y al personal autorizado. No contiene micrositios públicos ni acciones del paciente. Esas funciones futuras no se deducen de las rutas internas de cuentas, servicios o citas.

### Estado y evidencia del servidor

Las etapas clínicas 1 y 2 están implementadas para revisión C09. T01–T27 están Done y C01–C08 fueron aceptados; C09 espera decisión del usuario. El cierre registrado documenta 198 pruebas y 25 probes correctos con datos ficticios, PostgreSQL Test y Keycloak Test.

Esa evidencia pertenece al servidor. No acredita integración completa con Rust/SQLite, Patient Hub, datos reales, saturación, despliegue o producción. El analizador conserva 15 errores históricos documentados. No se inicia Etapa 3 por publicar este paquete.

Quedan fuera de esta revisión: medicación y prescripción, planes de cuidados, laboratorio y adjuntos, plantillas clínicas, especialidades, IMC y curvas OMS, analítica clínica, gestión pública del Hub, mensajes, lista de espera y operación con datos reales.

## 3. Recorrido rápido del consumidor

Un consumidor nuevo sigue este orden:

1. Configurar la URL base de API por entorno. Release exige HTTPS; HTTP solo se admite para desarrollo/prueba local configurado.
2. Leer `GET /v1/auth/config` y `GET /v1/capabilities`.
3. Autenticar al usuario con OIDC Authorization Code + PKCE S256 en navegador externo.
4. Canjear el access token OIDC en `POST /v1/auth/device-tokens` y guardar el token opaco devuelto en almacenamiento seguro.
5. Consultar `GET /v1/me` y `GET /v1/accounts`; elegir una cuenta visible.
6. Consultar `GET /v1/accounts/{account_id}/access`. Si exige registro, enviar `RegisterAccountDevice` para el dispositivo autenticado.
7. Crear una captura con `POST A/sync/snapshots`, descargar todos sus elementos e instalar vista y `baseCursor` juntos en SQLite.
8. Continuar con `GET A/sync/changes?cursor=...`; aplicar cada página y `nextCursor` juntos.
9. Enviar escrituras mediante `POST A/sync/operations`, conservando `operationId` y contenido hasta conocer el resultado.
10. Usar `GET A/sync/events` solo como aviso. La recuperación persistente siempre usa captura, journal y cursor aplicado.

`A` significa `/v1/accounts/{account_id}` en toda esta guía.

## 4. Identidad, dispositivo y autorización

### 4.1 Emisión y uso de credenciales

`GET /v1/auth/config` devuelve `issuer`, `publicClientId`, `audience`, `authorizationFlow=authorization_code` y `pkceMethod=S256`. No contiene secreto de cliente.

Enviar a `POST /v1/auth/device-tokens` el access token OIDC destinado a API como Bearer y este cuerpo:

```json
{
  "deviceName": "Equipo ficticio",
  "clientVersion": "0.0.0-fixture",
  "localSchemaVersion": 1
}
```

La API valida firma RS256 con su JWKS configurado, issuer, audience, `exp`/`nbf` y `azp`. No acepta un ID token ni una URL de claves proporcionada por el JWT.

La respuesta 201 contiene `accessToken`, `tokenId`, `deviceId`, `userId` e `issuedAt`. El token tiene la forma `ngt_<tokenId>.<secret>`, no vence por tiempo y se guarda solo como huella en el servidor. El secreto se entrega una vez. El consumidor no necesita interpretarlo.

Usar después:

```http
Authorization: Bearer <accessToken>
```

Cerrar sesión o desactivar al usuario en Keycloak no revoca por sí solo el token API. La revocación eficaz ocurre en API. Si se pierde la credencial, autenticar de nuevo, crear otra instalación y revocar la anterior; no existe recuperación del secreto guardado.

### 4.2 Cuenta e instalación

Autenticarse puede crear la identidad global, pero no crea consulta, pertenencia, profesional ni permisos. El alta administrativa de una consulta pertenece al operador de API.

`GET A/access` devuelve rol, estado, `permissionEpoch`, `allowedActions` y `clinicalPermissions`. Funciona antes de registrar la instalación. Si el estado es `registration_required`, enviar por lote:

```json
{
  "operationId": "019a1234-0000-7000-8000-000000000010",
  "contractVersion": 1,
  "action": "RegisterAccountDevice",
  "entityKey": "<deviceId autenticado>",
  "expectedVersion": 0,
  "payload": {}
}
```

Solo el propio dispositivo puede hacer ese registro inicial. Emitir token o aceptar invitación no registra la instalación por deducción.

Una invitación se dirige a un `userId` ya identificado, dura 72 horas y se acepta en `POST /v1/me/invitations/{invitation_id}/accept` con `{operationId}`. No hay directorio global ni correo automático.

### 4.3 Reglas de acceso

- El rol `owner` se deriva de la propiedad de la cuenta; los demás miembros activos son `assistant`.
- Toda ruta privada revalida token, usuario, dispositivo, cuenta, pertenencia, objeto y acción.
- Conocer un UUID no concede acceso. Un objeto ajeno o inexistente produce la misma ausencia.
- Los permisos vigentes se aplican también a duplicados, resultados anteriores, capturas, delta y SSE.
- Una operación offline se evalúa con los permisos al aceptarla, no con la fecha del cliente.
- Una revocación no promete borrar datos ya descargados ni intenciones locales. El escritorio conserva esas intenciones para revisión autorizada.
- La revocación global de dispositivo y la revocación de su acceso en una cuenta son efectos distintos. Una instalación revocada no se restaura a sí misma.

`allowedActions` ayuda a presentar las acciones disponibles, pero no sustituye la autorización del servidor. Las acciones online se obtienen de `capabilities.json`; no se registran como trabajo offline.

## 5. Reglas de transporte

| Regla | Contrato |
|---|---|
| JSON | camelCase; Python y SQL conservan snake_case fuera del contrato. Acciones, estados y códigos respetan mayúsculas y guiones exactos. |
| IDs | UUIDv7 textual canónico. Las nuevas entidades offline reciben UUID del cliente; el registro de dispositivo lo genera el servidor. |
| Instantes | RFC 3339 con offset explícito; respuestas en UTC con `Z`. No se admiten valores naive o infinitos. |
| Fechas y zonas | `YYYY-MM-DD`; zonas IANA reconocidas. No deducir zona de documento o teléfono. |
| Campos desconocidos | Se rechazan. No aplicar diccionarios libres al modelo remoto. |
| Patch | Al menos un campo; ausencia conserva; null solo borra valores anulables. Sin diferencia: `NO_CHANGES`, sin nueva versión. |
| Texto | Un valor presente no puede quedar vacío tras retirar espacios exteriores. |
| Teléfono | `phoneCode` y `phone`, ambos presentes o ambos nulos. La validación no prueba existencia ni titularidad. |
| Listas | `page` desde 1; `shows=100` por defecto, máximo 500; respuesta `{items,total}`. |
| Lote | 1–100 operaciones; cuerpo máximo 1 MiB; cada operación máximo 64 KiB UTF-8. |
| Correlación | El servidor genera UUIDv7 y lo devuelve en `X-Correlation-ID` y en errores/resultados. No concede acceso. |

Las listas corrientes no garantizan una vista única entre páginas si hay escrituras concurrentes. Para una reconstrucción coherente se usa captura más delta. Los filtros y la autorización se aplican antes de contar y paginar.

La posición incremental de sincronización no es un cursor de página y nunca se sustituye por OFFSET.

## 6. Catálogo HTTP

Salvo salud, capacidades, configuración OIDC y emisión, las rutas exigen token de dispositivo. Las rutas bajo `A` también exigen instalación habilitada, salvo `A/access`, el registro inicial y las excepciones administrativas documentadas.

### 6.1 Salud, identidad y cuentas

| Método | Ruta | Uso |
|---|---|---|
| GET | `/health/live` | Vida del proceso; público. |
| GET | `/health/ready` | Base, esquema y listener; 200 o 503 sin detalles internos. |
| GET | `/v1/capabilities` | Revisión, catálogo y límites; público. |
| GET | `/v1/auth/config` | Configuración pública OIDC. |
| POST | `/v1/auth/device-tokens` | Emitir token opaco; 201. |
| GET | `/v1/me` | Identidad propia y cuentas visibles. |
| GET | `/v1/me/devices` | Dispositivos propios, incluidos revocados. |
| POST | `/v1/me/devices/{device_id}/rotate-token` | Rotar el token del dispositivo autenticado; `{}`; 201. |
| POST | `/v1/me/devices/{device_id}/revoke` | Revocar un dispositivo propio; 204. |
| GET | `/v1/me/invitations` | Invitaciones dirigidas al usuario. |
| POST | `/v1/me/invitations/{invitation_id}/accept` | Aceptar como destinatario. |
| GET | `/v1/accounts` | Cuentas propias, incluidas inactivas. |
| GET | `A` | Detalle de la cuenta. |
| GET | `A/access` | Acceso, acciones, época y permisos clínicos propios. |
| GET | `A/members` | Equipo; propietario. |
| GET | `A/members/{user_id}/clinical-permissions` | Permisos clínicos del asistente; propietario. |
| GET | `A/invitations` | Invitaciones de la cuenta; propietario. |
| GET | `A/devices` | Autorizaciones de instalaciones en la cuenta; propietario. |
| GET | `A/audit-events` | Auditoría técnica; propietario. |
| GET | `A/professionals` | Profesionales visibles en la cuenta. |
| GET | `/v1/me/professional` | Perfil profesional propio. |
| GET | `/v1/me/services` | Catálogo privado del profesional propio. |

### 6.2 Pacientes, contactos y servicios

| Método | Ruta | Uso y filtros |
|---|---|---|
| GET | `A/patients` | Fichas de la cuenta; `q`, `status`, `completionStatus`. |
| GET | `A/patients/{patient_id}` | Una ficha de la cuenta. |
| GET | `A/patients/{patient_id}/identifiers` | Documentos vinculados a esa ficha. |
| GET | `A/patients/{patient_id}/birth-date-changes` | Cambios de nacimiento desde la entrega clínica. |
| GET | `A/patients/{patient_id}/contacts` | Vínculos de la ficha; `status`. |
| GET | `A/contacts` | Contactos de la cuenta; `q`, `status`. |
| GET | `A/contacts/{contact_id}` | Contacto de la cuenta. |
| GET | `A/contacts/{contact_id}/patients` | Vínculos de ese contacto; `status`. |
| GET | `A/services` | Ofertas visibles; `professionalId`, `q`, `status`. |

No existe búsqueda o fusión global de pacientes ni una acción pública para verificar documentos o representación.

### 6.3 Agenda, disponibilidad y citas

| Método | Ruta | Uso y filtros |
|---|---|---|
| GET | `A/schedule/rules` | Reglas; profesional, día, estado y vigencia. |
| GET | `A/schedule/rules/{rule_id}` | Regla visible. |
| GET | `A/schedule/exceptions` | Excepciones; profesional, estado y rango local acotado. |
| GET | `A/schedule/exceptions/{exception_id}` | Excepción visible. |
| GET | `A/schedule/blocks` | Bloqueos; profesional, estado y rango UTC acotado. |
| GET | `A/schedule/blocks/{block_id}` | Bloqueo visible; el motivo global se oculta al asistente. |
| GET | `A/availability` | Requiere profesional, servicio y `[from,until)`; duración opcional; máximo 31 días. |
| GET | `A/appointments` | Requiere `[from,until)`; máximo 366 días; filtros por profesional, servicio, paciente y estado. |
| GET | `A/appointments/{appointment_id}` | Cita visible, incluso fuera de la ventana descargada. |
| GET | `A/appointments/{appointment_id}/history` | Historia por versión; `afterVersion`, `page`, `shows`. |

Consultar disponibilidad no reserva. Las citas se seleccionan por intersección de intervalos, no solo por su inicio.

### 6.4 Registro clínico

Todas las rutas siguientes cuelgan de `A/patients/{patient_id}` y exigen el permiso de su sección.

| Recurso | Rutas GET | Filtros y resultado |
|---|---|---|
| Perfil | `/clinical-profile`; `/clinical-profile/history` | Sexo al nacer, nacimiento y edad calculada; perfil ausente devuelve versión 0 sin escribir. |
| Condiciones | `/conditions`; `/conditions/{condition_id}`; `/conditions/{condition_id}/history` | Estados clínico/verificación; inclusión explícita de anulados. |
| Alergias | `/allergy-intolerances`; `/allergy-intolerances/{allergy_id}`; `/allergy-intolerances/{allergy_id}/history` | Tipo, sustancia, reacción, estados y fechas conocidas. |
| Revisiones | `/clinical-sections/conditions`; `/clinical-sections/conditions/history`; `/clinical-sections/allergies`; `/clinical-sections/allergies/history` | Estado de información y revisión por sección. |
| Atenciones | `/encounters`; `/encounters/{encounter_id}`; `/encounters/{encounter_id}/history` | Atención realizada, contenido, vínculos y versiones. |
| Última visita | `/last-visit` | Última atención válida de la cuenta/paciente; nulos si no existe. |
| Notas | `/notes`; `/notes/{note_id}`; `/notes/{note_id}/history` | Nota independiente o vinculada; filtro `encounterId`. |
| Mediciones | `/measurements`; `/measurements/{measurement_id}`; `/measurements/{measurement_id}/history` | Serie por tipo, fecha del hecho y validez. |
| Resumen de mediciones | `/measurements/summary` | Última toma válida por tipo. |
| Vacunas | `/immunizations`; `/immunizations/{immunization_id}`; `/immunizations/{immunization_id}/history` | Administrada aquí, declarada o desconocida; fecha con precisión. |
| Antecedentes | `/antecedents`; `/antecedents/{antecedent_id}`; `/antecedents/{antecedent_id}/history` | Relato `personal`, `family` u `other`. |
| Historial integrado | `/clinical-history` | Referencias sin contenido; filtros por fuente antes de total/página. |

Las historias usan versión ascendente y `afterVersion`. Las listas clínicas excluyen `entered-in-error` salvo filtro explícito. Cada detalle vuelve a autorizar su fuente.

### 6.5 Operaciones y sincronización

| Método | Ruta | Uso |
|---|---|---|
| POST | `A/sync/operations` | Lote de operaciones; 200 con resultado individual. |
| GET | `A/sync/operations/{operation_id}` | Resultado del actor original con permiso vigente. |
| POST | `A/sync/snapshots` | Materializar captura; 201. |
| GET | `A/sync/snapshots/{snapshot_id}` | Metadatos de una captura propia y autorizada. |
| GET | `A/sync/snapshots/{snapshot_id}/items` | Elementos inmutables con `page`/`shows`. |
| DELETE | `A/sync/snapshots/{snapshot_id}` | Liberar derivado temporal; no borra negocio ni recibos. |
| GET | `A/sync/changes` | Grupos completos desde el cursor aplicado. |
| GET | `A/sync/events` | SSE de avisos desde el cursor aplicado. |

`/openapi.json`, `/docs` y `/redoc` solo se habilitan en desarrollo/prueba. La URL base y el entorno se configuran fuera de este paquete.

## 7. Escrituras por operaciones

### 7.1 Envoltorio

Todas las escrituras de negocio de una cuenta usan `POST A/sync/operations` con esta forma:

```json
{
  "operations": [
    {
      "operationId": "019a1234-0000-7000-8000-000000000012",
      "contractVersion": 1,
      "action": "RegisterPatient",
      "entityKey": "019a1234-0000-7000-8000-000000000013",
      "expectedVersion": 0,
      "payload": {
        "fullName": "Paciente ficticio",
        "birthDate": "2000-02-29"
      },
      "dependsOn": []
    }
  ]
}
```

El ejemplo crea una identidad nueva y una ficha `draft`; no la deja completa ni habilita una cita.

- `entityKey` es UUIDv7 o la clave compuesta documentada.
- `accountId`, actor y dispositivo proceden de la ruta y del contexto autenticado.
- Crear usa `expectedVersion=0`; modificar usa la versión actual positiva.
- `dependsOn` admite hasta ocho IDs del mismo actor/cuenta, ya aceptados o anteriores en el lote.
- Una operación tiene su propia transacción. No hay commit global del lote.
- `occurredAtLocal` es evidencia reportada; no concede permisos ni prueba orden de commit.

Validar el payload exacto contra `accepted-operations.schema.json`. La huella idempotente incluye los campos semánticos normalizados, no el token ni la correlación.

### 7.2 Catálogo de acciones

| Área | Acciones | Clave y regla principal |
|---|---|---|
| Cuenta | `UpdateAccountDetails`, `UpdateAccountPolicy`, `SetAccountStatus` | UUID de cuenta; propietario y online. |
| Invitaciones | `CreateInvitation`, `RevokeInvitation` | UUID de invitación; propietario y online. |
| Equipo | `SetMembershipStatus`, `SetMemberClinicalPermissions` | UUID del asistente; propietario y online; versión de pertenencia. |
| Dispositivo en cuenta | `RegisterAccountDevice`, `RevokeAccountDevice`, `RestoreAccountDevice` | UUID de dispositivo; registro propio; revocación/restauración por propietario. |
| Profesional | `UpdateProfessionalProfile` | UUID del profesional propio; `publicName`. |
| Pacientes | `RegisterPatient`, `UpdatePatientProfile`, `SetPatientCompletion`, `SetPatientProfileStatus` | UUID de paciente; identidad y completitud no se cambian por deducción. |
| Documentos | `AddPatientIdentifier` | UUID de documento nuevo; ficha ya vinculada. |
| Contactos | `CreateContactPerson`, `UpdateContactPerson`, `SetContactPersonStatus` | UUID de contacto; datos administrativos o estado. |
| Vínculos | `CreatePatientContactRelationship`, `UpdatePatientContactRelationship`, `SetPatientContactRelationshipStatus` | `{patientId,contactPersonId}`; extremos estables. |
| Catálogo | `CreateService`, `UpdateService`, `SetServiceStatus` | UUID de servicio; profesional propietario. |
| Ofertas | `OfferService`, `UpdateServiceOffer`, `SetServiceOfferStatus` | `{professionalId,serviceId}`; profesional propietario. |
| Reglas semanales | `CreateScheduleRule`, `UpdateScheduleRule`, `SetScheduleRuleStatus` | UUID de regla; minutos locales y vigencia. |
| Excepciones | `CreateScheduleException`, `UpdateScheduleException`, `SetScheduleExceptionStatus` | UUID de excepción; cierre o reemplazo de una fecha. |
| Bloqueos | `CreateScheduleBlock`, `UpdateScheduleBlock`, `SetScheduleBlockStatus` | UUID de bloqueo; alcance global solo profesional propio. |
| Citas | `CreateAppointment`, `ConfirmAppointment`, `RescheduleAppointment`, `CancelAppointment`, `CompleteAppointment`, `MarkAppointmentNoShow` | UUID de cita; estados y disponibilidad del servidor. |
| Perfil clínico | `SetPatientSexAtBirth` | UUID de paciente; versión de perfil, inicial 0; permiso `clinicalProfile`. |
| Condiciones | `CreatePatientCondition`, `UpdatePatientCondition`, `InvalidatePatientCondition` | UUID de condición; historial y anulación terminal. |
| Alergias | `CreatePatientAllergyIntolerance`, `UpdatePatientAllergyIntolerance`, `InvalidatePatientAllergyIntolerance` | UUID de alergia; historial y anulación terminal. |
| Revisión clínica | `SetPatientClinicalSectionReview` | UUID de paciente; `section=conditions|allergies`; versión de revisión. |
| Atenciones | `CreatePatientEncounter`, `UpdatePatientEncounter`, `InvalidatePatientEncounter` | UUID de atención; sin ciclo de cierre. |
| Notas | `CreatePatientNote`, `UpdatePatientNote`, `InvalidatePatientNote` | UUID de nota; cuerpo obligatorio al crear. |
| Mediciones | `RecordPatientMeasurement`, `CorrectPatientMeasurement`, `InvalidatePatientMeasurement` | UUID de toma; nueva toma y corrección son acciones distintas. |
| Vacunas | `RecordPatientImmunization`, `UpdatePatientImmunization`, `InvalidatePatientImmunization` | UUID de vacuna; fuente y precisión conservadas. |
| Antecedentes | `CreatePatientAntecedent`, `UpdatePatientAntecedent`, `InvalidatePatientAntecedent` | UUID de antecedente; relato sin efectos automáticos. |

`AcceptInvitation` figura como acción online en capacidades, pero usa su ruta dirigida y no una de las 66 acciones del lote.

### 7.3 Resultados e idempotencia

La respuesta contiene `results` y `correlationId`. Cada `OperationResult` incluye `operationId`, `status`, `entityVersion`, `state`, `error` y, en duplicados, `originalResult`.

| Estado | Interpretación y acción del escritorio |
|---|---|
| `accepted` | Efecto y resultado confirmados tras commit. Conservar recibo local; no equivale a haber descargado el delta. |
| `duplicate` | Recupera el resultado original, incluso si fue rechazo o conflicto. No aplica otro efecto. |
| `conflict` | Revisar versión, disponibilidad o identidad de operación. No sobrescribir el estado remoto. |
| `rejected` | Rechazo definitivo. Conservar intención para corrección o revisión. |
| `retryable_failure` | Fallo temporal sin efecto confirmado. Consultar o reintentar la misma intención. |

La clave es `(accountId, actorUserId, operationId)`. Reintentar conserva ID y contenido semántico, incluso desde otra instalación autorizada del mismo actor. Cambiar acción, payload, versión esperada, dependencias o tiempo local con el mismo ID produce `IDEMPOTENCY_CONFLICT`.

Ante timeout, caída o respuesta perdida, consultar `GET A/sync/operations/{operation_id}` o repetir exactamente la misma operación. Nunca crear otro ID para averiguar si ocurrió el efecto.

El resultado completo se conserva al menos 90 días. Después queda un recibo mínimo que impide repetir el efecto. `RESULT_EXPIRED` exige revisar el estado actual antes de crear una nueva intención.

Un HTTP 200 del lote no significa que todas las operaciones fueran aceptadas. Revisar cada resultado. Si la petición falla después de confirmaciones parciales, recuperar cada resultado conocido con acceso válido.

## 8. Modelo funcional que consume el escritorio

### 8.1 Cuenta, paciente y contactos

La identidad global de una persona no es su ficha ni concede acceso entre cuentas. Cada cuenta conserva sus propios datos administrativos y clínicos.

Una ficha tiene dos estados independientes:

- `completionStatus`: `draft` permite datos incompletos; `complete` exige una base válida.
- `status`: `active` o `inactive`; inactivar no borra ni cancela citas.

Para `own_document` se exige nombre, documento propio `declared` o `verified`, y teléfono propio o responsable vigente con teléfono. No se exige inspección física del documento.

Para `minor_without_document` se exige nombre, nacimiento y contacto responsable vigente con teléfono. Al citar, el paciente debe ser menor de 18 en la fecha local de la cita. Es una regla administrativa, no prueba legal ni acceso al Hub. Para un nacimiento el 29 de febrero, el cumpleaños administrativo en año no bisiesto es el 1 de marzo.

Nombre, teléfono o documento declarado coincidentes no fusionan personas. El documento de un adulto contacto no identifica al menor. Añadir después un documento conserva la identidad y las citas del paciente.

Si una edición de contacto o vínculo deja una ficha completa sin requisitos, API devuelve `COMPLETENESS_CONFLICT`. El cliente primero cambia expresamente las fichas afectadas a `draft` o establece otra base válida.

### 8.2 Servicios, agenda y disponibilidad

El profesional posee un catálogo. Una oferta vincula un servicio propio con una cuenta y puede definir `durationMinutesOverride`; si es nulo usa la duración base. Ambas duraciones son enteros de 1–1440 minutos.

`ServiceOfferResponse` conserva `version` de la oferta y `serviceVersion` del catálogo. Una actualización del catálogo puede cambiar la proyección sin incrementar la versión propia de la oferta.

Las reglas semanales y excepciones usan minutos desde medianoche: inicio 0–1439 y fin exclusivo 1–1440. Una excepción `closed` cierra el día; `replacement` sustituye el horario habitual. Un bloqueo con `accountId` nulo afecta toda la actividad del profesional; con cuenta, solo ese ámbito.

La disponibilidad une reglas, aplica excepciones y resta bloqueos y ocupación real del profesional en todas sus cuentas. No revela pacientes ni motivos ajenos. Cambios de agenda o zona que hacen incompatible una cita vigente se rechazan; no mueven ni cancelan citas automáticamente.

### 8.3 Citas e historia

| Acción | Transición y efecto |
|---|---|
| `CreateAppointment` | Crea `scheduled`, versión 1 e historia inicial. Exige ficha completa y referencias operativas. |
| `ConfirmAppointment` | `scheduled` a `confirmed`; conserva intervalo y registra confirmación del servidor. |
| `RescheduleAppointment` | `scheduled`/`confirmed` a `scheduled`; conserva duración real y referencias; invalida confirmación. |
| `CancelAppointment` | A `cancelled`; conserva historia e intervalo y libera ocupación. |
| `CompleteAppointment` | A `completed`; exige haber alcanzado el inicio. No crea una atención clínica. |
| `MarkAppointmentNoShow` | A `no_show`; acción manual tras inicio más margen vigente de cuenta. |

`cancelled`, `completed` y `no_show` son terminales. El margen inicial de ausencia es 15 minutos y admite 0–1440.

La ocupación se protege por profesional entre cuentas. `scheduled`, `confirmed`, `completed` y `no_show` ocupan; `cancelled` libera. Los intervalos incluyen inicio y excluyen fin, por lo que dos citas contiguas no se solapan.

Cada versión conserva los datos acordados del servicio, profesional, duración de referencia, lugar y zona. Editar sus fuentes no reescribe citas anteriores. Reprogramar conserva esos datos y la duración efectiva.

La historia funcional de citas es append-only y distinta de la auditoría técnica, del Change Log y del historial clínico.

## 9. Registro clínico

### 9.1 Permisos por sección

`ClinicalPermissions` contiene ocho niveles independientes:

- `clinicalProfile`
- `conditions`
- `allergies`
- `encounters`
- `notes`
- `measurements`
- `immunizations`
- `antecedents`

Cada nivel vale `none`, `read` o `read_write`. El propietario tiene acceso completo. Asistentes existentes y nuevos empiezan con `read_write`; solo el propietario cambia esa configuración online mediante `SetMemberClinicalPermissions`.

- `none`: sin lecturas, historias, resultados, resúmenes ni descarga de esa sección.
- `read`: lecturas e historias; no escrituras, duplicados de escritura ni recuperación de sus resultados.
- `read_write`: lectura, acciones y recuperación autorizada de resultados.

Los clientes anteriores que omitan las cinco secciones de Etapa 2 reciben el default `read_write` documentado antes de huella y ejecución.

Cambiar niveles incrementa la versión de pertenencia y `permissionEpoch`, invalida capturas/cursores y cierra el SSE del alcance anterior. El historial integrado no tiene un permiso global: filtra cada fuente antes de contar y paginar.

### 9.2 Datos de referencia de Etapa 1

El perfil registra `sexAtBirth` opcional con fuente. No se infiere de nombre, documento o género. La edad se calcula desde el nacimiento; no se guarda como un dato editable.

Condiciones y alergias usan texto libre, fuente, estado clínico y estado de verificación separados. Las fechas históricas aceptan `YYYY`, `YYYY-MM` o `YYYY-MM-DD` y conservan su precisión. No se completa un día ficticio.

Una lista vacía no significa «sin condiciones» o «sin alergias». Las revisiones distinguen `not_recorded`, `not_asked`, `unknown`, `none_known` y `has_entries`. Crear el primer registro pertinente deriva `has_entries`; retirar el último deriva `unknown`.

`refuted` no es lo mismo que `entered-in-error`. La anulación por error es terminal y conserva la historia.

### 9.3 Atenciones, notas y antecedentes

Registrar una atención afirma que ocurrió. No existen estados de planificación, firma o cierre. Puede existir sin cita y una cita admite varias atenciones. Cancelar, completar o marcar ausencia en una cita no crea una atención.

La atención conserva profesional, asistente opcional, `occurredAt`, `endedAt`, captura local y contenido clínico opcional. `serviceId` sigue siendo obligatorio al reservar una cita, pero una atención sin cita puede conservar el motivo en palabras del paciente.

La última visita es el `occurredAt` de la última atención válida de esa cuenta/paciente. No depende de citas, notas, aceptación remota ni cierre.

Una nota puede existir sin atención. Su texto no crea diagnóstico, condición, tratamiento ni última visita. Las ediciones usan versión esperada y conservan historia sin exigir motivo.

Los antecedentes `personal`, `family` y `other` conservan relato, fuente y fecha conocida. `family` exige `relatedPersonDescription`; no atribuye esa historia como condición del paciente ni ejecuta codificación automática.

### 9.4 Mediciones

Cada toma nueva recibe otro ID. Una corrección conserva el mismo ID y añade una versión; el valor anterior queda en historia, no como otro punto vigente. La serie se ordena por `measuredAt`, no por fecha de carga.

| `kind` | Forma | Unidad fija | Rango técnico de captura |
|---|---|---|---|
| `weight` | `value` | `kg` | 0,01–1000 |
| `temperature` | `value` | `Cel` | 20–45 |
| `oxygen_saturation` | `value` | `%` | 0–100 |
| `heart_rate` | `value` | `/min` | 1–300 |
| `blood_pressure` | `systolicValue` y/o `diastolicValue` | `mm[Hg]` | 20–300 por componente presente |

Los rangos no son umbrales clínicos ni alertas. Para presión, al menos un componente es obligatorio y el otro puede ser nulo; `value` debe ser nulo. Para los demás tipos, `value` es obligatorio y ambos componentes deben ser nulos. No se inventa cero ni se admiten unidades alternativas.

`PatientMeasurementResponse` deriva `ageYears`, `ageAsOf` y `patientVersion` desde el nacimiento en la fecha local de la toma. Si falta nacimiento, la edad es nula. No se calcula IMC ni percentil.

Ejemplo de nueva toma:

```json
{
  "operationId": "019a1234-0000-7000-8000-000000000020",
  "contractVersion": 1,
  "action": "RecordPatientMeasurement",
  "entityKey": "019a1234-0000-7000-8000-000000000021",
  "expectedVersion": 0,
  "payload": {
    "patientId": "019a1234-0000-7000-8000-000000000013",
    "kind": "weight",
    "measuredAt": "2026-11-16T10:00:00-04:00",
    "value": 70,
    "unit": "kg"
  }
}
```

Corregir esa toma usa `CorrectPatientMeasurement`, el mismo `entityKey`, su versión actual y solo los campos que cambian.

### 9.5 Vacunas

Una vacuna conserva nombre, fecha parcial, fuente y `recordKind=administered_here|reported|unknown`. `administered_here` exige una atención válida de la misma ficha. Una declaración histórica no prueba administración actual.

Producto, dosis, lote, vía, sitio, lugar y administrador son opcionales. No existe catálogo externo obligatorio, recomendación, calendario, aviso ni creación automática de alergias.

### 9.6 Historial integrado y auditoría

`GET .../clinical-history` devuelve referencias, tiempos, precisión, versión y estado. No devuelve cuerpo, nombre, sustancia ni valores. El detalle se obtiene por la ruta de la fuente y vuelve a autorizar.

La proyección `patient_clinical_timeline` es interna y reconstruible; no se descarga como otra entidad ni es una fuente editable.

Las lecturas y escrituras clínicas dejan auditoría sin motivos, texto, valores, nombres, filtros, cuerpos ni cursores. Si la evidencia no puede persistir, API no entrega los datos.

## 10. Proyecciones de sincronización

Cada `SyncItem` o `SyncChange` identifica `entityType`, `entityKey`, `entityVersion`, `changeKind` y `state`. El tipo selecciona el modelo de estado; no inferirlo por campos opcionales.

| `entityType` | Clave pública | Modelo de `state` |
|---|---|---|
| `account` | UUID de cuenta | `AccountResponse` |
| `account_device` | UUID de dispositivo | `AccountDeviceResponse` |
| `membership` | UUID de usuario | `MemberResponse` |
| `invitation` | UUID de invitación | `InvitationResponse` |
| `professional` | UUID de profesional | `ProfessionalResponse` |
| `patient_profile` | UUID de paciente | `PatientProfileResponse` |
| `patient_identifier` | UUID de documento | `PatientIdentifierResponse` |
| `contact_person` | UUID de contacto | `ContactResponse` |
| `patient_contact` | `{patientId,contactPersonId}` | `RelationshipResponse` |
| `service` | UUID de servicio | `ServiceResponse` |
| `service_offer` | `{professionalId,serviceId}` | `ServiceOfferResponse` |
| `schedule_rule` | UUID de regla | `ScheduleRuleResponse` |
| `schedule_exception` | UUID de excepción | `ScheduleExceptionResponse` |
| `schedule_block` | UUID de bloqueo | `ScheduleBlockResponse` |
| `appointment` | UUID de cita | `AppointmentResponse` |
| `appointment_history` | UUID de cita | `AppointmentHistoryProjection` |
| `patient_clinical_profile` | UUID de paciente | `ClinicalProfileResponse` |
| `patient_condition` | UUID de condición | `PatientConditionResponse` |
| `patient_clinical_section_review` | `{patientId,section}` | `ClinicalSectionReviewResponse` |
| `patient_allergy_intolerance` | UUID de alergia | `PatientAllergyIntoleranceResponse` |
| `clinical_encounter` | UUID de atención | `PatientEncounterResponse` |
| `patient_note` | UUID de nota | `PatientNoteResponse` |
| `patient_measurement` | UUID de toma | `PatientMeasurementResponse` |
| `patient_immunization` | UUID de vacuna | `PatientImmunizationResponse` |
| `patient_antecedent` | UUID de antecedente | `PatientAntecedentResponse` |

La cuenta de la ruta forma parte del ámbito aunque la clave no la repita. Las claves locales deben conservar ese ámbito.

`appointment_history.state.items` contiene las entradas hasta la versión proyectada. `patient_contact` sincroniza el vínculo; los GET `PatientContactResponse` añaden nombres y teléfonos actuales que no forman parte del estado persistido del vínculo.

## 11. Captura, delta y SSE

### 11.1 Captura inicial

`SnapshotRequest` admite:

```json
{
  "appointmentsFrom": "2026-10-17",
  "appointmentsUntil": "2027-04-16",
  "includeClinical": false
}
```

Todos los campos son opcionales como objeto, pero una fecha presente no puede ser nula. La ventana por defecto va de hoy local menos 30 días hasta hoy más 181, con fin exclusivo. Máximo 366 días. `includeClinical` es booleano y por defecto `false`.

Procedimiento:

1. Enviar `POST A/sync/snapshots` con `{}` o la selección anterior.
2. Conservar `snapshotId`, `window`, `baseCursor`, `expiresAt`, `itemCount` y `clinicalSections`.
3. Descargar `A/sync/snapshots/{snapshot_id}/items?page=1&shows=100` y todas las páginas.
4. Solo al completar, instalar la vista remota y `baseCursor` en una transacción SQLite, conservando Outbox e intenciones.
5. Liberar la captura con DELETE cuando ya no sea necesaria.

API materializa datos y posición bajo REPEATABLE READ. La captura dura 15 minutos, conserva conjunto y orden, y no mantiene una transacción SQL entre peticiones. Cada página revalida creador, dispositivo, alcance y época.

La captura administrativa incluye datos operativos y referencias necesarias de la cuenta, agenda y citas de la ventana con su historia. No copia datos de otras cuentas.

Con `includeClinical=true`, añade solo las secciones legibles y registra el conjunto en `clinicalSections`. Incluye datos de Etapas 1 y 2: atenciones válidas, versiones actuales válidas de notas/antecedentes, todas las tomas válidas, vacunas válidas y datos de referencia clínica. No incluye historias de versiones, timeline ni adjuntos. Los hechos clínicos no se filtran por la ventana de citas.

**Un consumidor sin modelos y proyectores clínicos debe mantener `includeClinical=false`.** Publicar el esquema no implementa esa parte del escritorio.

### 11.2 Descarga incremental

Usar `GET A/sync/changes?cursor=<cursor_aplicado>`. La respuesta contiene `groups`, `nextCursor` y `hasMore`.

- API examina hasta 100 grupos completos por petición; no admite `page`/`shows`.
- Aplicar los cambios y guardar `nextCursor` en la misma transacción SQLite.
- No dividir un grupo: comparte operación y puede contener varias entidades.
- Continuar mientras `hasMore=true`, incluso si `groups` está vacío. API puede avanzar sobre grupos invisibles sin entregar contenido.
- Si falla la escritura local, conservar el cursor anterior y repetir la descarga.
- `upsert` instala estado; `remove` retira la entidad de la vista, sin borrar su historia funcional en API.

Una corrección clínica publica su versión actual. Una anulación publica `entered-in-error`; una captura posterior ya no incluye esa entrada. La retención técnica no borra hechos ni historias clínicas.

El cursor HMAC se liga a contrato, cuenta, usuario, dispositivo, audiencia, secciones clínicas, época y ventana. Tiene un plazo de hasta 90 días, pero la frontera de retención puede exigir recuperación antes. Cambiar permisos o ventana exige otra captura.

### 11.3 SSE como aviso

Abrir `GET A/sync/events?cursor=<cursor_aplicado>` con Bearer. El cliente debe poder enviar esa cabecera y leer SSE.

| Evento | Datos y tratamiento |
|---|---|
| `changes_available` | `{accountId,cursor}`; despertar la descarga usando el último cursor aplicado local. El cursor del aviso no prueba aplicación ni salta al head. |
| `heartbeat` | `{serverTime}` cada 15 segundos; API revalida acceso. |
| `access_revoked` | Sin datos; cierra el stream. Detener el acceso afectado y conservar intenciones. |

`id` SSE y `Last-Event-ID` son referencias, no cursores aplicados. Reconectar con el cursor aplicado más reciente. El servidor sugiere 3000 ms.

Hay dos conexiones como máximo por dispositivo/cuenta entre procesos. Un lease puede ocupar el cupo hasta 45 segundos tras una caída. Un consumidor lento se desconecta y recupera por cursor. Si el listener falla, `/health/ready` degrada a 503; las rutas de datos y el journal siguen siendo la recuperación.

## 12. Errores y recuperación

`ApiError` tiene `{code,message,correlationId,details}`. Usar `code`; el mensaje no es una clave estable. Los errores no incluyen token, SQL, trazas ni datos personales de entrada.

| Respuesta o código | Acción del consumidor |
|---|---|
| 401 `AUTHENTICATION_REQUIRED` | Revisar token/dispositivo y volver al acceso si corresponde. No cambiar IDs de operaciones pendientes. |
| 403 `PERMISSION_DENIED` | Detener el acceso afectado; conservar intenciones para revisión. |
| 404 `NOT_FOUND` | Objeto inexistente o no visible. No deducir existencia ni autorizar otro ID de operación automáticamente. |
| `VERSION_CONFLICT` | Leer estado actual autorizado y revisar la intención. |
| `SLOT_UNAVAILABLE` | Revisar disponibilidad; no hubo reserva. |
| `IDEMPOTENCY_CONFLICT` | El mismo ID tiene contenido distinto; revisar el registro local. |
| `COMPLETENESS_CONFLICT` | Resolver ficha, documento o contacto con operaciones explícitas. |
| `INVALID_STATE_TRANSITION` / `NO_CHANGES` | Revisar estado y acción; no insistir para crear una versión. |
| `DEPENDENCY_FAILED` | Revisar la dependencia; las operaciones independientes conservan su propio resultado. |
| 410 `CURSOR_EXPIRED` | Nueva captura y reconstrucción conservando Outbox. |
| 410 `SNAPSHOT_EXPIRED` / `SNAPSHOT_SCOPE_CHANGED` | Descartar el derivado y capturar con alcance actual. |
| 410 `RESULT_EXPIRED` | Revisar estado actual; el recibo mínimo sigue impidiendo repetir el efecto. |
| 413 | Reducir cuerpo u operación antes de cualquier efecto. |
| 422 | Corregir estructura o parámetros. Un payload inválido dentro de un lote válido puede aparecer como rechazo individual con HTTP 200. |
| 429 `CONNECTION_LIMIT` | Cerrar streams sobrantes o esperar liberación; conservar cursor. |
| 503 / `retryable_failure` | Consultar o reintentar la misma identidad cuando se recupere la dependencia. |

Aceptar invitación puede usar HTTP 409 para su rechazo. Los conflictos del lote conservan HTTP 200 y resultado individual.

## 13. Obligaciones del escritorio

La guía no afirma que todo esto ya esté implementado en `nightingale`. El consumidor debe:

- Separar estado local, intención pendiente, recibo remoto y vista aceptada.
- No borrar trabajo local porque API rechace o porque falle la red.
- Conservar ID y contenido de cada operación hasta resolver su resultado.
- Guardar credenciales en el almacenamiento seguro del sistema, fuera de SQLite, IPC y logs.
- Respetar acciones online, permisos vigentes y cambios de época.
- Aplicar captura/base y página/cursor atómicamente en SQLite.
- Procesar grupos completos, duplicados, grupos vacíos con avance y retiradas de vista.
- Usar modelos tipados por `entityType`; no copiar el esquema PostgreSQL como diseño local.
- Mantener `includeClinical=false` hasta implementar todas las proyecciones clínicas seleccionadas.
- Mostrar conflictos para revisión; una corrección autorizada crea otra intención solo cuando corresponde.
- Probar reinicio con envío desconocido, dos dispositivos, revocación, cursor/captura vencidos, SSE caído y cita fuera de ventana.

## 14. Actualización del paquete

Desde `nightingale-api`, con su entorno existente:

```powershell
uv run --locked python -m scripts.export_contracts
uv run --locked python -m scripts.export_contracts --check
uv run --locked python test-support/contracts/check.py
```

Copiar completa la exportación y esta guía al escritorio. No editar los JSON importados para hacer pasar pruebas. Verificar en el consumidor los hashes del manifiesto, referencias JSON, rutas utilizadas, envoltorios, proyecciones y eventos.

Fuentes propietarias en `nightingale-api`:

- `docs/nightingale-api.md`: alcance general.
- `docs/patient-clinical-record.md`: alcance funcional clínico.
- `docs/decisions.md`: decisiones y pendientes.
- `docs/api-v1.md`: transporte, reglas HTTP, operaciones y recuperación.
- `docs/access-design.md`: identidad y permisos.
- `docs/database-schema.md`: única fuente del modelo físico; no es un contrato SQL para el escritorio.
- `src/application.py` y `src/api/*/domain`: origen de los artefactos generados.

La integración real del escritorio, su aplicación atómica en SQLite y cualquier despliegue requieren evidencia propia. Este paquete fija la referencia para realizar ese trabajo sin dejar al consumidor en una revisión anterior.
