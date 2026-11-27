# T04 · Identidad, permisos y alcance del Hub

**Revisión documental del 2026-11-14:** [D11](decisions.md#d11--interfaz-del-hub-y-servidor-en-nightingale-api) fija la interfaz web en Patient Hub y todas sus funciones de servidor en Nightingale API. Sustituye la propuesta entre dos servidores conservada al final. El acceso del personal no cambia; los accesos del futuro Hub aún no están implementados.

**Estado al 2026-10-26:** C05 aceptado; T16–T18 comprobadas para revisión C06, sin aceptar. El [contrato v1](api-v1.md) conserva Keycloak para emitir token opaco sin vencimiento, revocable en API y sin sesiones/renovación propias. Miembros activos con instalación habilitada gestionan pacientes/contactos y reglas semanales de su cuenta. Solo profesional propietario modifica catálogo/ofertas; miembros leen solo ofertas de su cuenta. Resultados de servicios vuelven a comprobar el vínculo profesional vigente. Solo propietario consulta auditoría. No se registra instalación al aceptar invitación ni se restaura desde el dispositivo revocado. Hub y consumidores siguen pendientes.

## Acuerdo vigente de la primera etapa

Alta de consulta mediante un script pequeño en scripts/create_practice.py con issuer/subject exactos del propietario y conexión administrativa separada; [uso local](../test-support/README.md#alta-administrativa). No hay sistema de comandos ni dependencia de arranque del servidor. authorization posee identidad, credenciales y dispositivos globales; accounts posee cuenta, pertenencias, perfil profesional y autorizaciones por cuenta. Autenticarse por OIDC puede registrar identidad sin conceder cuenta. Rol propietario derivado de propiedad; resto del equipo activo, asistentes. Solo propietario invita y gestiona pertenencias, políticas y acceso de dispositivos en su cuenta. Una invitación tiene destinatario autenticado concreto, dura 72 horas y se consume una vez, sin correo automático.

API valida el access token OIDC únicamente al emitir credencial; no ID token ni contraseñas. Guarda huella de secreto aleatorio de 256 bits y lo entrega una sola vez. Las entradas privadas del personal exigen token API vigente, usuario/dispositivo activos, pertenencia y autorización de cuenta/objeto/acción. Revocar instalación propia afecta sus tokens globales; propietario de una cuenta solo puede revocar acceso de esa instalación en su ámbito. Cambiar reloj o campos del cliente no modifica esa autoridad.

El token no vence. Logout o desactivación en Keycloak no revocan por sí solos un token ya emitido; la operación administrativa de API debe revocarlo o desactivar la identidad. No se implementan introspección por petición, sesiones API, renovación ni logout distribuido. Una credencial perdida exige nueva autenticación y revocación del dispositivo anterior, sin recuperar secretos guardados.

Aceptación y revocación se coordinan en PostgreSQL con el orden y relecturas de api-v1.md. Si revocación confirma primero no hay efecto posterior con acceso viejo; aceptación válida anterior conserva su hecho. La intención rechazada sigue en escritorio y una persona con permiso puede revisarla y crear una operación nueva con actor real, nunca reenviar como otra persona. Lecturas y resultados previos también se reautorizan; SSE revisa acceso al emitir y en heartbeat, sin transacción larga por conexión.

La definición física está solo en database-schema.md. El historial de T04 se conserva abajo; sus alternativas de sesiones/proveedor quedan sustituidas en este ámbito. D11 resuelve el alcance y la propiedad del servidor del Hub; O02 conserva el mecanismo de acceso limitado a citas pendiente de diseño.

## Permisos clínicos de etapa 1 · implementación para revisión C07

El plan [P-20261115-02-patient-clinical-data](../tasks/P-20261115-02-patient-clinical-data/plan.md) añade tres niveles independientes por pertenencia: perfil clínico, condiciones y alergias/intolerancias. Cada nivel vale `none`, `read` o `read_write`; asistentes existentes/nuevos empiezan con `read_write`. El propietario conserva acceso completo y solo él configura asistentes, online y con versión de pertenencia. Estos niveles no crean roles globales ni cambian los permisos administrativos sobre nacimiento.

`none` excluye estado, resúmenes, historias, resultados y descargas; `read` permite consultas; `read_write` permite acciones y recuperar resultados de escritura. API vuelve a autorizar antes de duplicados, resultados, listas, detalles, historias y capturas. Cambiar niveles incrementa pertenencia y época en la misma aceptación, invalida capturas/cursores y provoca cierre del SSE anterior. Desactivar/reactivar conserva la configuración.

La captura clínica es opcional y registra las secciones permitidas. Sus proyecciones usan audiencias cerradas por sección, filtradas antes de construir la respuesta; no incluyen historias. Las lecturas clínicas correctas dejan evidencia sin nombres clínicos, sustancias, reacciones, filtros, cuerpos o cursores; un fallo al persistirla impide entregar datos. No se promete borrado de copias locales ya descargadas.

Cada recibo clínico conserva `clinical_section`. Duplicados y GET exigen `read_write` vigente en esa sección antes de leer o validar el resultado; `read`/`none` no reciben cuerpos, `originalResult` ni conflictos informativos. Las revisiones compartidas usan su sección real. Los recibos históricos ambiguos permanecen sin alcance y fallan cerrados. Las lecturas de resultados, capturas y deltas clínicos registran evidencia en la misma transacción. La migración 20261116_03 impide reasignar cuenta, ID o paciente de las filas clínicas actuales.

## Operador de Nightingale · decidido en D23 (2026-11-26)

El operador de plataforma para revisión de suscripciones se autentica en Keycloak con identidad separada del personal y recibe de API una credencial opaca sin vencimiento, revocable en API, siguiendo el patrón de dispositivos del personal. No tiene pertenencia, rol de cuenta ni acceso clínico; sus acciones de plataforma son separadas del RBAC de cuentas. Alta, recuperación y revocación son un componente de la propia API gestionado por operadores con la acción separada; el alta inicial usa el flujo administrativo de despliegue y la recuperación revoca la credencial anterior y emite una nueva. Canal: rutas de operador en la misma aplicación FastAPI. Detalle en [D23](decisions.md#d23--operador-de-nightingale-identidad-ciclo-de-vida-y-canal-t03).

## Suscripciones de cuenta · diseño para C03 (2026-11-26)

El componente `subscriptions` añade dos ámbitos de acceso separados (D21–D24, diseño HTTP en [api-v1.md](api-v1.md) §14):

- **Cuenta:** todas las acciones de suscripción (consulta, cotización, reporte, evidencia, cambio de plan, cancelación) son del propietario con dispositivo registrado activo. El asistente no recibe permiso de suscripción por defecto. Presentar un reporte no activa ni extiende; la autorización precede a la existencia del objeto y un reporte o evidencia ajeno devuelve 404.
- **Operador:** identidad Keycloak separada del personal con credencial opaca revocable en API y acciones de plataforma `review`, `catalog`, `rates` y `operators`. No tiene pertenencia ni rol de cuenta, no abre rutas clínicas ni rutas bajo `A`, y un token del personal no abre las rutas de operador. Alta inicial por flujo administrativo de despliegue; el resto del ciclo de vida se gestiona por API con la acción `operators`.

La indisponibilidad comercial (gracia vencida, suspensión) se distingue de la credencial inválida: la lectura y la renovación permanecen disponibles y nada revoca identidades ni borra datos (D24).

## Acceso futuro del Hub acordado por D11

| Recorrido | Regla vigente de alcance | Diseño pendiente |
|---|---|---|
| Lectura del micrositio | Pública, sin cuenta de paciente, inicio de sesión ni permisos del personal. Solo información destinada a publicación mediante endpoints públicos de API | Proyecciones y formas HTTP de las plantillas de médico independiente y clínica/centro |
| Gestión de una cita existente | Acceso limitado verificado por API para esa cita, acción e información necesaria, sin credenciales del personal | Mecanismo y ciclo del enlace/acceso, vigencia, revocación, proyecciones, formas HTTP y recuperación del resultado |

La lectura pública no abre rutas internas ni publica fichas de pacientes, listados de citas, notas internas u otros datos privados. Las plantillas no son un editor libre ni permiten gestión de pacientes. Publicar clínicas no habilita toda su gestión interna, varias sedes o cambios generales del escritorio.

El acceso a la cita permitirá consultar información permitida, confirmar asistencia, cancelar según las reglas, solicitar reprogramación y consultar resultado. No permitirá crear o reservar citas, explorar disponibilidad para elegir otro horario ni marcar ausencias; el personal conserva ese registro. La solicitud conserva estado, horario y confirmación y no reserva otro intervalo. El personal decide el cambio y API lo aplica con las reglas comunes. Las rutas actuales del personal no conceden estas capacidades al paciente.

API tendrá la lógica de enlaces, acceso, reglas y solicitudes que el Hub necesite. No se eligen cuentas de paciente, sesiones ni un segundo servidor como solución. Un identificador declarado de cuenta, cita, actor o resultado no prueba acceso. Quedan por diseñar el tratamiento de revocación y versión antigua frente a una acción en curso y la consulta de resultados tras respuesta perdida.

## Antecedente T04 sustituido en los puntos indicados

Las secciones siguientes conservan la propuesta inicial y sus pruebas futuras. D09/D10 sustituyen las alternativas del personal; D11 sustituye la propiedad y autorización entre servidores del Hub. No son otra lista vigente de tareas o requisitos de implementación.

## Identidad del personal

El proveedor prueba quién inició sesión; Nightingale API decide qué puede hacer en cada cuenta. La clave externa propuesta es la pareja emisor/sujeto (`iss`, `sub`), vinculada a un usuario interno. El correo no concede pertenencia ni sirve para enlazar cuentas automáticamente. Autenticarse no crea una cuenta profesional ni otorga acceso a una existente.

El escritorio será un cliente público: navegador externo, Authorization Code y PKCE S256, sin secreto de cliente distribuido. Rust mantiene el retorno de autenticación y los secretos locales; esos cambios pertenecen al escritorio. API recibe un access token destinado a su audiencia; no acepta un ID token como credencial de operaciones. Las reglas de validación dependen del formato y del proveedor aprobado. [RFC 8252](https://www.rfc-editor.org/rfc/rfc8252) y [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700) sustentan el flujo nativo y la protección de tokens; no eligen un proveedor.

Para un access token JWT se verifican firma, algoritmos permitidos, emisor, audiencia, vigencia y propósito antes de consultar permisos locales. No se toma una URL de claves aportada por el cliente. Para tokens opacos, evaluar introspección autenticada. Las claves, su rotación, renovación y fallos requieren el contrato del proveedor. La validación del ID token del inicio de sesión corresponde al cliente OIDC; no sustituye la validación del access token de API. Referencias: [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation), [perfil de access tokens JWT](https://www.rfc-editor.org/rfc/rfc9068) e [introspección](https://www.rfc-editor.org/rfc/rfc7662).

## Propiedad y altas

| Propietario | Información y autoridad |
|---|---|
| Proveedor OIDC | Autenticación del personal, credenciales del proveedor, factores y tokens según su contrato |
| API / `authorization` | Usuario interno y vínculo externo, credenciales y dispositivos globales |
| API / `accounts` | Cuentas, pertenencias, perfil profesional, permisos y autorización de dispositivos por cuenta |
| Escritorio | Sesión/secretos locales en almacenamiento seguro, copia de permisos e intenciones pendientes; no puede modificar permisos sin conexión |
| Hub | Identidad y acceso del paciente, enlaces, reglas propias y solicitudes; no usa la sesión del profesional como identidad del paciente |

Propuesta: el primer acceso administrativo se habilita mediante un procedimiento online controlado. Un usuario autorizado invita a asistentes y concede permisos limitados a su cuenta. No habrá un alta pública que permita elegir cuenta, rol o pertenencia. Antes de T08 deben acordarse el alta inicial, la prueba de aceptación de invitación y la recuperación de la cuenta; no se crea una ruta administrativa abierta para pruebas.

Un dispositivo necesita un registro autorizado y una credencial o sesión ligada a ese registro. Un `device_id` enviado por el cliente no prueba esa relación. El protocolo concreto de vínculo y renovación queda abierto hasta elegir proveedor; debe impedir reutilizar el registro de otro usuario o dispositivo. No se promete atestación del equipo ni resistencia a un equipo intervenido.

## Política remota ante revocación

**Confirmada por el usuario el 2026-10-21:** aplicar los permisos vigentes al aceptar la operación. No conceder autorización retroactiva solo porque el equipo afirma que guardó el cambio antes. Si ya no existe permiso, rechazar sin aplicar el efecto y conservar la intención en el escritorio para revisión. Propuesta de tratamiento posterior: una persona aún autorizada podrá crear una operación nueva tras revisar la intención; no se restaura la antigua credencial ni se reenvía el cambio con un actor falso.

La API coordina la comprobación local de acceso y la escritura. Propuesta de orden:

1. La aceptación y la revocación de usuario/pertenencia/dispositivo comparten una referencia de autorización versionada y un mecanismo de coordinación en PostgreSQL.
2. Si revocación se confirma primero, la operación no puede aplicar efectos usando la versión anterior. Si aceptación obtiene el orden válido primero y confirma, una revocación posterior no borra ese hecho.
3. Un fallo no publica revocación o aceptación como completada antes de su commit. T07/T08 deben demostrar la carrera con conexiones distintas y orden de bloqueos definido.

Los tiempos del servidor y las versiones aportan evidencia; la hora del cliente no decide el orden. La revocación local de API puede impedir operaciones aunque el access token del proveedor siga vigente. En cambio, cerrar sesión en el proveedor no garantiza revocación inmediata en API: elegir entre introspección, notificación fiable y vigencia limitada, con demora acordada. No se promete equivalencia entre logout, revocación de sesión, dispositivo y pertenencia.

El escritorio conserva los últimos permisos válidos sin red. API no puede revocar de inmediato esa copia ni retirar datos ya descifrados. Al reconectar, devuelve el rechazo o la necesidad de revisión, sin ordenar un borrado silencioso de intenciones. También reautoriza consultas de resultados idempotentes y páginas; conocer un ID anterior no permite recuperar datos tras revocación.

## Antecedente sustituido: autorización entre servidores

**Sustituido por D11 el 2026-11-14.** La comparación siguiente suponía backend y almacenamiento propios del Hub. No exige identidad de servicio, concesión entre servidores ni consulta a otro backend para el diseño actual. La necesidad de limitar cada acceso a cita/acción permanece; el mecanismo concreto no está elegido.

Una credencial de servicio prueba que llama el backend del Hub, no que pueda operar cualquier cita. Comparación:

| Opción | Ventaja | Riesgo y coste |
|---|---|---|
| A. Concesión limitada registrada por API y comprobada con la operación | API puede comprobar y revocar su alcance dentro de la aceptación local | Exige emitir/vincular la concesión con la cita y conciliar su ciclo con los accesos del Hub |
| B. Consultar autorización al Hub en cada acción | Hub responde por el estado de su acceso y política | Añade dependencia de red y un intervalo entre consulta y commit; no demuestra revocación atómica entre servicios |
| C. Afirmación firmada del Hub sin estado de revocación en API | Evita una consulta por acción | Una firma prueba origen e integridad, no vigencia de permisos; necesita un límite de exposición y otro mecanismo de revocación |

**Propuesta para revisión:** A. Personal autorizado habilita el acceso a una cita mediante un caso de API que registra una concesión ligada a cuenta, cita, servicio destinatario y acciones. El Hub no puede crear concesiones para objetos arbitrarios solo con su identidad técnica. Su backend conserva la referencia necesaria y valida además su propio acceso del paciente. API exige identidad de servicio más concesión vigente; no acepta el actor o `practice_id` como prueba.

La concesión no es el enlace del paciente. API conserva el límite de autorización remota; Hub conserva el secreto del enlace, sus sesiones, reglas de cancelación y solicitudes. Se acuerdan identificación de actor, versión/época de la cita, vencimiento y revocación de la concesión; no se fija un formato firmado o duración antes de revisarlo. Los secretos de servicio no llegan al navegador.

Hub debe revocar su acceso local y comunicar a API la invalidación de la concesión. Si esa comunicación falla, mantiene el resultado remoto pendiente y reintenta por una identidad estable. La revocación compartida surte efecto cuando API la confirma. Una acción ya en curso puede tener un orden anterior; no hay revocación distribuida instantánea. La política de este intervalo necesita revisión. Reprogramar invalida la confirmación anterior y debe acordarse cómo afecta a la concesión y al enlace en T06/T15.

No se amplían las acciones del paciente: consultar su cita, confirmar, cancelar si Hub lo permite y solicitar cambio en Hub. Pedir cambio no modifica ni reserva horario. Las llamadas de proveedor o introspección ocurren fuera de las transacciones PostgreSQL; el alcance local se revalida con la escritura.

## Matriz histórica de amenazas y pruebas propuestas

Los casos de alcance ajeno, revocación, versión antigua y respuesta perdida siguen siendo criterios para el futuro contrato; la concesión de servicio era el mecanismo propuesto, ahora sustituido. Las referencias Txx pertenecen al plan anterior.

| Entrada o carrera | Resultado exigido / propuesta a comprobar | Tarea |
|---|---|---|
| Token con otro emisor/audiencia, firma inválida o ID token usado como access token | Rechazo antes de leer datos operativos | T08 |
| Mismo correo con otro sujeto OIDC | No enlazar automáticamente ni heredar permisos | T08 |
| Actor cambia cuenta, rol, dispositivo o referencia de objeto en el payload | Usar contexto comprobado y rechazar cruce de cuenta/dispositivo | T08, T14 |
| Permisos revocados, reloj atrasado y operación pendiente | Aplicar la política confirmada: no aplicar; conservar intención para revisión | T08, T14, T23 |
| Aceptación y revocación simultáneas | Un orden verificable; sin éxito anterior al commit ni autorización anterior reutilizada | T08, T14 |
| Hub autenticado sin concesión, con otra cita o más acciones | Rechazar sin filtrar existencia ni resultado previo | T15 |
| Concesión revocada o cita reprogramada frente a una acción Hub antigua | Revalidar alcance/versión; no sobrescribir el estado nuevo | T15 |
| Respuesta de aceptación/revocación perdida | Recuperar resultado autorizado con la misma identidad; no repetir efecto | T14, T15 |
| Proveedor OIDC, claves o canal de revocación no disponibles | Fallo controlado según política aprobada; no permitir por error ni confundir indisponibilidad con rechazo definitivo | T08, T23 |

## Condiciones históricas antes de cerrar T04

- Precisar el recorrido de revisión y nueva operación bajo la política de permisos vigentes ya confirmada.
- Aprobar o cambiar la opción del Hub y su comportamiento durante una revocación pendiente.
- Seleccionar proveedor OIDC y su contrato de access tokens, renovación, logout/revocación y disponibilidad; no hace falta contratarlo durante esta etapa.
- Precisar alta administrativa/invitaciones, vínculo dispositivo/sesión, recuperación y matriz mínima de permisos. Duraciones y límites requieren una decisión explícita antes de implementar acceso.

En aquel cierre T04 seguía en curso: OIDC y permisos vigentes estaban confirmados, O01/O02 abiertos y aún no había pruebas de seguridad ejecutadas. Es un registro histórico; el contrato del personal y su evidencia actual se consultan arriba y en el plan de escritorio. D11 sustituye las condiciones ligadas al segundo servidor del Hub. [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) respalda comprobar cada solicitud y denegar por defecto; no sustituye estas decisiones.

## Permisos clínicos de etapa 2 · contrato implementado

Diseño de [P-20261116-02-clinical-routine](../tasks/P-20261116-02-clinical-routine/plan.md), Completed, con C01–C09 aceptados. Conserva las reglas vigentes de identidad, dispositivo y autorización por objeto.

`ClinicalSection` y `ClinicalPermissions` añaden `encounters`,`notes`,`measurements`,`immunizations`,`antecedents`; `account_memberships` conserva un nivel independiente para cada una. Propietario conserva acceso completo; asistentes existentes/nuevos empiezan con `read_write` y solo propietario reduce niveles online. `SetMemberClinicalPermissions` acepta las ocho secciones; un cliente anterior que omita las nuevas conserva su default `read_write`.

- `none` excluye lecturas, historias, resúmenes, última visita, resultados y descargas de esa sección.
- `read` permite lecturas/historias y excluye escrituras, duplicados de escritura y reintentos.
- `read_write` permite lecturas, acciones y recuperación de resultados de esa sección.

Cada recibo conserva su `clinical_section`; autorización precede a duplicados, validación de resultados, conteos y proyecciones. Los conjuntos cerrados de capturas, cursores y audiencias añaden las cinco secciones. Cambiar niveles incrementa pertenencia/época, invalida capturas/cursores y cierra SSE. Una cuenta, paciente o registro ajeno devuelve la misma ausencia que uno inexistente, también en errores y totales.

`last-visit` exige lectura de `encounters`. `clinical-history` no usa permiso global: filtra `source_section` antes de contar/paginar y cada detalle vuelve a autorizar su fuente. La captura con `includeClinical=true` solo incluye secciones legibles; los hechos nuevos no heredan permiso de citas, perfil u otra sección. Grupos invisibles permiten avanzar sin cuerpos.

Escrituras y lecturas clínicas conservan auditoría sin motivos, texto, valores, nombres, filtros, cuerpos o cursores. Si la evidencia falla, no se entregan datos. Revocar permisos no promete borrar copias ya descargadas.

## Correspondencia para normalizar autorización · T03 · 2026-11-17

Fuente única de la correspondencia de P-20261117-01-authorization-policies. **Estado implementado para C06:** T04–T06 implementan OperationPolicy/operation_policies, published_actions en get_access y owner_only en la guarda administrativa. T07–T09 obtienen del catálogo sección/nivel clínicos, secciones legibles y referencias de reglas de objeto. Services/schedule conservan consultas, propiedad y proyecciones. Los descriptores distinguen own_professional (perfil), own_catalog, own_offer y block; la coordinación y la lectura de resultados usan esas referencias sin cambiar sus bloqueos. T01/T02 conservan la caracterización. T10–T12 usan projection_audiences/projection_allowed para captura y delta, sync_scope_matches para captura/cursor/SSE y changes_scope para invalidación atómica. No es otro contrato HTTP.

La fuente ejecutable única es `src/api/accounts/domain/policies.py`; esta tabla explica su correspondencia. Cada nombre de la tabla tiene un descriptor: rol base miembro/propietario, sección y nivel cuando aplique, referencia de regla de objeto y posiciones de publicación. Todas las operaciones privadas mantienen identidad y contexto vigentes. Las reglas del objeto permanecen en su componente; un descriptor no ejecuta SQL ni concede acceso por conocer un ID.

| Acciones exactas | Rol base y nivel | Regla de objeto |
|---|---|---|
| RegisterAccountDevice | miembro; excepción sin registro previo, cuenta activa | instalación autenticada propia; no autorrestauración |
| RegisterPatient, UpdatePatientProfile, SetPatientProfileStatus, SetPatientCompletion, AddPatientIdentifier | miembro | ficha/identificador de la cuenta; patients conserva relaciones y reglas |
| CreateContactPerson, UpdateContactPerson, SetContactPersonStatus, CreatePatientContactRelationship, UpdatePatientContactRelationship, SetPatientContactRelationshipStatus | miembro | contacto y ficha de la misma cuenta |
| CreateScheduleRule, UpdateScheduleRule, SetScheduleRuleStatus, CreateScheduleException, UpdateScheduleException, SetScheduleExceptionStatus | miembro | profesional vinculado a cuenta; schedule conserva disponibilidad |
| CreateScheduleBlock, UpdateScheduleBlock, SetScheduleBlockStatus | miembro | schedule comprueba bloqueo global del profesional propio |
| CreateAppointment, ConfirmAppointment, RescheduleAppointment, CancelAppointment, CompleteAppointment, MarkAppointmentNoShow | miembro | ficha, profesional, servicio y reserva del ámbito; appointments conserva transiciones |
| SetPatientSexAtBirth | miembro; profile/read_write | ficha clínica de cuenta |
| CreatePatientCondition, UpdatePatientCondition, InvalidatePatientCondition | miembro; conditions/read_write | registro/ficha de cuenta |
| SetPatientClinicalSectionReview | miembro; sección validada conditions o allergies, read_write | revisión de ficha; nunca deducir sección desde resultado |
| CreatePatientAllergyIntolerance, UpdatePatientAllergyIntolerance, InvalidatePatientAllergyIntolerance | miembro; allergies/read_write | registro/ficha de cuenta |
| CreatePatientEncounter, UpdatePatientEncounter, InvalidatePatientEncounter | miembro; encounters/read_write | atención, ficha, cita opcional y participantes del ámbito |
| CreatePatientNote, UpdatePatientNote, InvalidatePatientNote | miembro; notes/read_write | nota/ficha y atención opcional del ámbito |
| RecordPatientMeasurement, CorrectPatientMeasurement, InvalidatePatientMeasurement | miembro; measurements/read_write | toma/ficha y atención opcional del ámbito |
| RecordPatientImmunization, UpdatePatientImmunization, InvalidatePatientImmunization | miembro; immunizations/read_write | vacuna/ficha; administered_here exige atención válida |
| CreatePatientAntecedent, UpdatePatientAntecedent, InvalidatePatientAntecedent | miembro; antecedents/read_write | antecedente/ficha y atención opcional del ámbito |
| DeclarePatientMedication, UpdatePatientDeclaredMedication, ReviewPatientDeclaredMedication, InvalidatePatientDeclaredMedication | miembro; declared_medications/read_write | medicación declarada/ficha y atención opcional del ámbito; extensión concurrente D19 |
| CreateInvitation, RevokeInvitation, SetMembershipStatus, SetMemberClinicalPermissions | propietario | destinatario/pertenencia de la cuenta; no configurar propietario |
| UpdateAccountDetails, UpdateAccountPolicy, SetAccountStatus | propietario | cuenta; solo SetAccountStatus admite reactivación con instalación activa |
| RevokeAccountDevice, RestoreAccountDevice | propietario | instalación en cuenta; no revivir credenciales globales |
| UpdateProfessionalProfile | propietario | perfil profesional propio |
| CreateService, UpdateService, SetServiceStatus, OfferService, UpdateServiceOffer, SetServiceOfferStatus | propietario | services comprueba profesional propio; oferta limitada a cuenta |
| AcceptInvitation (ruta propia, fuera del catálogo publicado) | destinatario autenticado | invitación pendiente/vigente; accounts conserva aceptación y excepciones |

### Compatibilidad de descubrimiento y ejecución

- Con cuenta activa e instalación pendiente se publica solo RegisterAccountDevice. Revocada no publica acciones. Con instalación activa se publica registro, acciones comunes, clínica escribible y administración del propietario, en ese orden.
- El orden dentro de cada grupo es el de la tabla y sus nombres. Clínica sigue profile, conditions, allergies, encounters, notes, measurements, immunizations, antecedents. SetPatientClinicalSectionReview aparece tras las tres acciones de condiciones y tras las tres de alergias cuando cada sección permite escritura: se conservan ambas posiciones, sin deduplicar.
- Asistente en cuenta inactiva recibe denegación. Propietario con dispositivo de cuenta activo solo publica SetAccountStatus; con dispositivo pendiente/revocado no publica acciones. Publicar registro con instalación ya activa no promete que volver a registrarla aplique un efecto.
- allowedActions no prueba alcance del objeto. Descriptores desconocidos se deniegan en la evaluación pura; el transporte de acciones desconocidas conserva su rechazo UNSUPPORTED_OPERATION y su recibo según api-v1, sin convertirlo en permiso de negocio.
- Lectura clínica exige read o read_write; ejecución, duplicado y GET de escritura exigen read_write vigente. Owner no omite ámbito, relaciones, versiones ni estados.
- AU-32: la caracterización detectó GET 200 para una revisión histórica con clinical_section nula. El usuario autorizó corregirlo el 2026-11-17: GET ahora deniega antes de leer el resultado para cualquier acción clínica conocida sin sección. El reintento ya denegaba. Es una corrección autorizada de esta línea base; no se adivina la sección ni se migra el recibo.

### Entidades y audiencias implementadas

| Entidades exactas | Audiencia | Sección |
|---|---|---|
| account, professional, patient_profile, patient_identifier, contact_person, patient_contact, service_offer, schedule_rule, schedule_exception, schedule_block, appointment, appointment_history | members | ninguna; proyecciones limitadas por cuenta/objeto y ventana cuando aplica |
| account_device, membership, invitation, service | owner | ninguna; captura de propietario y filtro de delta |
| patient_clinical_profile | clinical_profile | profile |
| patient_condition | clinical_conditions | conditions |
| patient_allergy_intolerance | clinical_allergies | allergies |
| patient_clinical_section_review | clinical_conditions o clinical_allergies según sección validada | conditions o allergies |
| clinical_encounter | clinical_encounters | encounters |
| patient_note | clinical_notes | notes |
| patient_measurement | clinical_measurements | measurements |
| patient_immunization | clinical_immunizations | immunizations |
| patient_antecedent | clinical_antecedents | antecedents |
| declared_medication | clinical_declared_medications | declared_medications |

La tabla cubre las 26 proyecciones actuales: 25 de la línea base y una añadida por el desarrollo concurrente de Etapa 3 (D19). El journal no incluye historias clínicas ni timeline adicional; appointment_history es la proyección derivada autorizada de citas. Una captura no incluye clínica sin opt-in y materializa solo secciones legibles. Los filtros preceden al total; grupos invisibles avanzan sin cuerpo. Audiencia general del cursor owner/members y secciones clínicas son controles distintos. Cambiar época invalida alcance y cierra SSE anterior. La evaluación clínica, las secciones legibles y entidad→audiencia usan el catálogo. Una misma regla decide las proyecciones de captura/delta antes de contar o entregar; rol, sección y época se comparan también al reautorizar SSE. La propiedad y las consultas siguen en cada componente.

## Permisos clínicos de etapa 3 · decisión T03 (2026-11-17)

Decisión de [P-20261117-05-clinical-stage-3](../tasks/P-20261117-05-clinical-stage-3/plan.md), pendiente de diseño e implementación en T04–T09. No altera las secciones vigentes ni el trabajo en curso de Autorización.

Los bloques nuevos añaden secciones independientes por pertenencia con los mismos niveles `none`,`read`,`read_write`: medicación declarada (`declared_medications`), tratamiento y planes de cuidados (`care_plans`), informes y resultados (`diagnostic_reports`), plantillas y especialidad (`specialty_templates`) y analítica clínica (`clinical_analytics`). Propietario conserva acceso completo; asistentes existentes y nuevos empiezan con `read_write` y solo el propietario reduce niveles online, con la misma semántica de Etapas 1/2: `none` excluye lecturas, historias, totales, resultados, adjuntos, capturas y derivados; `read` permite consultas; `read_write` permite acciones y recuperación de resultados. Los adjuntos exigen además autorización vigente en `diagnostic_reports` antes de cada descarga. Cuando Autorización (P-20261117-01) esté Completed, su matriz de políticas sustituirá esta configuración sin cambiar el contrato de Etapa 3 por deducción.

Compatibilidad de `SetMemberClinicalPermissions`: la API calcula la huella del formato de ocho secciones si medicación declarada, cuidados, informes y especialidades conservan `read_write`. Si alguna de esas cuatro secciones tiene nivel `read` o `none`, incluye las doce secciones en la huella. La validación, la ejecución y las respuestas usan los doce niveles vigentes. Los recibos ya guardados conservan su huella.


## Acceso al vademecum global · diseño C01

Diseño de [P-20261122-01-vademecum-read-api](../tasks/P-20261122-01-vademecum-read-api/plan.md), pendiente de implementación y revisión. El componente reutiliza `get_account_context(..., require_device=True)` dentro de la transacción de lectura y exige además `context.account.status == "active"`. No usa la excepción administrativa que permite al propietario consultar una cuenta inactiva.

| Condición actual | Resultado antes de leer el catálogo |
|---|---|
| Token ausente, inválido o revocado; usuario/dispositivo global inactivo | 401 según la autenticación vigente |
| Cuenta no visible, outsider o pertenencia inactiva | 404, sin revelar su existencia |
| Dispositivo de cuenta ausente, pendiente o revocado | 403 `PERMISSION_DENIED` |
| Cuenta inactiva, incluso para su propietario | 403 `PERMISSION_DENIED` |
| Owner o assistant con todos los estados activos | Lectura permitida del release global activo |

El contenido no es una proyección por cuenta, paciente o sección clínica. No modifica `ClinicalPermissions`, `allowedActions`, políticas RBAC/ABAC, auditoría, snapshots, cursores, Change Log ni sincronización. Conocer un registro sanitario o ID de monografía no concede acceso. El release ausente se evalúa solo después de esta autorización y devuelve 503; los objetos ausentes devuelven 404.

## Facturación de pacientes · diseño para C03 (2026-11-27)

El componente `billing` añade tres ámbitos de acceso separados (D25–D28, diseño HTTP en [api-v1.md](api-v1.md) §15):

- **Personal:** las rutas bajo `A/billing` exigen las acciones financieras agrupadas `billing_read`, `billing_charges` y `billing_review` (D27). El propietario las tiene todas; los asistentes nuevos y existentes no reciben ninguna por defecto y el propietario las concede explícitamente. Ningún permiso clínico abre finanzas ni una acción financiera abre contenido clínico; la autorización precede a la existencia del objeto y lo ajeno devuelve 404 uniforme.
- **Paciente:** las rutas bajo `/v1/patient/billing` usan el secreto opaco de una concesión `patient_billing_grants`, sin cuenta de paciente ni token de dispositivo. La concesión es por objeto concreto (cita o cargo) y acción (`read_charge`, `submit_report`, `read_result`, `read_receipt`); solo se persiste la huella del secreto. Vigencia ligada a la cita con máximo 30 días tras atención/cierre; cancelar la cita revoca, reprogramar mantiene (D28). Enlace vencido, revocado, ajeno o sin la acción devuelve 404 `NOT_FOUND` sin revelar existencia; conocer el UUID no autoriza.
- **Precios:** la escritura de precios base/oferta sigue con el permiso propio de catálogo/oferta, no con las acciones de facturación.

Las capturas y comprobantes se descargan solo con reautorización por petición; nunca aparecen en journal, snapshots, deltas, SSE, logs ni auditoría. La observación interna de la revisión no se proyecta al paciente.
