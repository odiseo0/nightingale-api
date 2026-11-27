# Registro de decisiones

**Fecha:** 2026-10-21. Confirmada significa acordada en el encargo o fuente vigente; propuesta requiere revisión; pendiente no autoriza una elección por defecto. Ningún estado acredita implementación.

## Confirmadas

### D01 · Tres proyectos y API transaccional

**Contexto:** el escritorio puede modificarse y operar sin red. **Decisión:** conserva casos de uso Rust/SQLite y envía operaciones completas; API autoriza y acepta el estado compartido en PostgreSQL privado. Repositorios separados. **Actualización del 2026-11-14, D11:** Patient Hub contiene la interfaz web; Nightingale API tendrá todas sus funciones de servidor.

**Antecedente sustituido por D11:** D01 asignaba al Hub web, API, enlaces, reglas, solicitudes y almacenamiento propios, con llamadas entre su backend y API. Ese reparto ya no rige; se conserva aquí como historia.

**Sustituye:** propuestas históricas de sincronización SQL directa y de un solo proyecto cloud. **Consecuencia:** ni escritorio ni Hub reciben credenciales SQL; API debe validar aun si el cliente afirma haberlo hecho. No convierte el guardado local en dependiente de la red. Fuente: encargo y especificación §§1–5; ADR del escritorio del 2026-10-21 identificado en [fuentes](sources.md).

### D02 · Propiedad y aceptación

API posee contratos remotos, migraciones operativas, idempotencia, Change Log, historial/auditoría y trabajo persistente. Acepta cada operación en su límite atómico y responde tras commit; los contratos no exponen el esquema SQL. Fuente: especificación §§2–4 y 8. Consecuencia: los adaptadores del Hub y los workers no crean otra vía de escritura de citas.

### D03 · Apoyo posterior al commit

Recordatorios, entregas/webhooks, n8n y analítica son módulos/workers de API. Persisten intención duradera, ejecutan fuera de la transacción de sync y usan permisos propios. Analítica tiene PostgreSQL separado. n8n es una herramienta externa sin SQL operativo. Fuente: especificación §6.

### D04 · Organización y alcance

Python/FastAPI/PostgreSQL y arquitectura hexagonal práctica por componentes según `src/application.py`, `api/`, `core/`, `settings/`. Sin una clase o puerto obligatorio por acción. Primera versión y exclusiones: [README](../README.md). Fuente: encargo y especificación; Free-Win Orders solo aporta organización.

### D05 · Trabajo revisable

La entrega inicial T01 solo documentó. El usuario autorizó T03 después y, tras pedir la corrección de anotaciones, autorizó continuar con T04. Plan y checkpoints conservan la revisión antes del trabajo que habilitan. La especificación copiada a `docs/nightingale-api.md` es la fuente de alcance de este proyecto. Al cerrar T01 no se cambió la copia del escritorio.

**Ampliación del 2026-10-23:** el usuario añadió la documentación del escritorio aquí y autorizó resolver sus diferencias. Se alinean las copias locales con los acuerdos confirmados y se sustituye el cuerpo duplicado de la especificación API por una referencia. Su [índice](nightingale-desktop-docs/README.md) identifica origen y versiones. No se modifica el repositorio original del escritorio.

**Revisión del usuario del 2026-10-23:** aprueba C13 y los criterios P05/P06, con derecho a cambiarlos antes o durante su implementación. Se conservan sus identificadores para mantener las referencias. La aprobación no cierra los detalles restantes de O04/O05 ni habilita código. El usuario trasladará los documentos del escritorio a su repositorio: conservar sus rutas originales y evitar dependencias relativas hacia archivos exclusivos de API.

**Nuevo foco del 2026-10-23:** el usuario confirmó el traslado y pidió trabajar en el diseño de la base de datos. Se abre T24 para un diseño lógico documental inicial, sin crear tablas ni cambiar modelos Python. Se leen Plan Maestro, SRS y arquitectura desde su repositorio original; no se copian ni modifican sus rutas. T04 conserva su acuerdo parcial para retomarlo, sin trabajo paralelo ni cierre de seguridad por anticipación.

### D06 · Identidad externa y permisos vigentes

**Confirmada por el usuario el 2026-10-21:** proveedor externo OIDC para el personal; Nightingale API conserva permisos y dispositivos. Al aceptar una operación pendiente se aplican los permisos vigentes. Si falta permiso, se rechaza sin efecto y el escritorio conserva la intención para revisión. No se deduce autorización de la fecha local.

Proveedor, dispositivo y acceso del escritorio se concretan después en D09 y [diseño de acceso](access-design.md). D11 fija el alcance y el propietario de servidor del Hub; su acceso limitado a citas sigue pendiente de diseño. Las alternativas previas de sesiones quedan como antecedente. Ninguna decisión acredita implementación ni permite eludir permisos vigentes.

### D07 · Bases del modelo de datos

**Antecedente sustituido en parte por D08 el 2026-10-24.** La lista siguiente registra las respuestas iniciales; no se usa para imponer una sola cuenta por profesional ni documento propio obligatorio para todo paciente. El esquema vigente define las reglas aplicables.

**Confirmadas por el usuario el 2026-10-23**, al responder las preguntas del diseño:

- La primera versión impide solapamientos del tiempo del profesional, sin añadir consultorios o equipos como recursos de reserva.
- Un profesional tiene una sola cuenta profesional. Se conserva el alcance inicial de un profesional y sus asistentes por cuenta; no se habilitan cuentas de varios médicos.
- La duración se determina por servicio y permite ajuste al crear la cita. Límites, precisión, permisos y ajuste en reprogramaciones siguen pendientes.
- Para registrar una cita, el paciente debe tener nombre, teléfono y documento. Formato, tipos de documento y reglas de duplicados siguen pendientes; obligatoriedad no implica unicidad global.

Estos acuerdos concretaron parte de O04 para el diseño inicial. No definían el esquema físico ni el mecanismo SQL de integridad. El borrador lógico 0.1 queda retirado por instrucción del usuario; D08 fija la fuente vigente.

### D08 · Fuente única del modelo de datos

**Confirmada por el usuario el 2026-10-24:** usar [database-schema.md](database-schema.md) como única fuente para pensar el modelo y el esquema de base de datos. No volver a usar el borrador lógico anterior. Las decisiones de cuentas, profesionales, pacientes y servicios que el esquema revisa sustituyen las reglas anteriores incompatibles, incluidas las de D07. Se conserva D07 como antecedente.

El usuario aplaza la solución de correcciones de identidad global y permite avanzar en las partes independientes. Confirma que las correcciones administrativas pueden quedar en la historia de la cita y pide contemplar la hora de médico y paciente en telemedicina. Después acepta la revisión y las propuestas 2 y 3 al responder «Listo, todo bien»: conservar fecha y autor de verificación y usar minutos desde medianoche para horarios de Agenda. La revisión 0.9 del esquema las incorpora y registra su alcance en §8.10. C14 queda aceptado y T24 cierra la revisión documental. Seguridad y sincronización mantienen sus fuentes y checkpoints; no se inicia código ni migraciones.

### D09 · Primera etapa de API compartida para escritorio

**Confirmada el 2026-10-24:** el usuario eligió núcleo compartido, aviso inmediato, plan sucesor, Keycloak de desarrollo, consultas independientes, Docker Compose, operaciones tipadas con lecturas por recurso, solo API, roles fijos, alta controlada y ventana de 90 días. Sustituyó la propuesta de sesiones por un token sin vencimiento y aceptó límites de duración, margen de ausencia y criterio administrativo de menor. Después pidió «Por favor, implementa este plan».

La ejecución vive en [P-20261024-01-desktop-shared-api](../tasks/P-20261024-01-desktop-shared-api/plan.md); el plan anterior conserva evidencia y pasa a Superseded, sin dar por hechas sus tareas pendientes. T01–T03 documentan este bloque. C01 aún requiere revisión; la aprobación no habilita saltar checkpoints ni desplegar.

- Keycloak identifica al emitir un token opaco por usuario/dispositivo, sin vencimiento y revocable en API. No hay ciclo de sesiones/renovación API ni promesa de revocación automática por logout OIDC. La API guarda solo huella y comprueba acceso actual por petición. Esto sustituye las propuestas de sesiones limitadas de la especificación 0.2 para esta etapa.
- Alta de consulta controlada, propietario y asistentes con permisos fijos; invitación dirigida a identidad concreta, sin correo automático. La cuenta independiente mantiene un solo profesional; el esquema conserva capacidad relacional de clínicas y exclusión global por profesional sin exponer su gestión.
- Todas las escrituras de negocio van por operaciones tipadas, una transacción por operación y resultado propio. Pydantic del adaptador será fuente de OpenAPI/JSON Schema; las reglas de dominio no importan esos DTO. El [contrato v1](api-v1.md) contiene el diseño HTTP previo a código y [database-schema.md](database-schema.md) la única fuente del modelo físico ampliado.
- Cursor con contador transaccional por cuenta, grupos completos y snapshot coherente; retención mínima 90 días de cambios/resultados. Recibo mínimo conservado impide repetir efectos después del vencimiento. SSE avisa mediante LISTEN/NOTIFY entre procesos; páginas/journal siguen siendo la recuperación persistente. No confundir señal con aplicación de datos en Rust.
- Duración 1–1440 minutos, precisión de un minuto, ajustable al crear; reprogramar conserva duración efectiva e invalida confirmación. Ausencia manual desde inicio más margen de cuenta, inicialmente 15 minutos (0–1440). Menor sin documento: menos de 18 en fecha de cita y contacto responsable vigente; no prueba legal ni acceso al Hub.
- La etapa solo cambia API y usa datos ficticios. Hub, mensajes, espera, analítica, producción, corrección/fusión global y verificación de identidad/representación siguen fuera. No cierra O02/O05–O07/O11 ni los recorridos excluidos de O04.

Fuentes de organización: Plan Maestro 0.3, DAT 0.3 y SRS 0.5 con revisión del 2026-10-23, en el repositorio original del escritorio. La instrucción de esta etapa no modifica ese repositorio. Las reglas de rutas, modelos y pruebas del plan aprobado se traducen a documentos para revisar en C01; no son evidencia de implementación.

### P05 · Solicitud de reprogramación separada

**Estado:** criterio aprobado por el usuario el 2026-10-23; revisable antes o durante la implementación si el usuario lo cambia. Se conserva el ID de la propuesta. No implementado; O04 sigue abierto para los detalles restantes.

La solicitud forma parte del alcance futuro del Hub; D11 asigna su servidor a Nightingale API. Referencia una cita y su versión. Pedir un cambio no altera el estado, horario ni confirmación de la cita ni reserva otro horario. `reschedule_requested` no forma parte del estado de negocio de Citas; el escritorio muestra la solicitud como información separada. La reserva original sigue vigente hasta una operación autorizada que la cambie o cancele. Este criterio sustituye la propuesta de incluir la solicitud como estado de cita en DAT §11; no fija todavía el ciclo completo de la solicitud.

**Antecedente de diseño sustituido por D11:** la tabla y la conciliación entre almacenes siguientes describen la propuesta del 2026-10-23, cuando el Hub tenía backend propio. No fijan la propiedad actual ni obligan a crear dos servidores. Se conserva la separación entre pedir y aplicar el cambio; las formas y el ciclo siguen pendientes.

| Recorrido propuesto | Efecto en la solicitud / cita |
|---|---|
| Paciente pide cambio | Hub registra una solicitud pendiente; cita y confirmación permanecen |
| Personal rechaza o paciente retira | Hub registra motivo permitido y resultado; la cita permanece |
| Personal selecciona otro horario | Rust guarda intención local; la solicitud sigue pendiente de resultado remoto |
| API acepta la reprogramación | API cambia horario e invalida confirmación en una transacción; Hub resuelve la solicitud contra esa operación y versión aceptadas |
| API rechaza, encuentra conflicto o no se conoce el resultado | No resolver la solicitud como completada; conservar intención. Solo si el resultado es desconocido, consultar la misma operación antes de repetir. Un fallo no confirma el nuevo horario |
| Cita cambia por otra vía o termina | Hub revalida la versión y registra si la solicitud ya no aplica; no cambia la nueva cita usando una versión antigua |

Si falla el aviso al Hub después de la aceptación, conservar la conciliación pendiente y recuperar el mismo resultado; no ejecutar otra reprogramación para compensar. Rechazo y retirada concurrentes con una reprogramación necesitan un orden acordado y evidencia del resultado; no se promete atomicidad entre almacenes.

Antes de cerrar O04: definir identificadores y transiciones de solicitud, duplicados, orden entre retirada/rechazo/resolución, vencimiento si se necesita, y recuperación de avisos. La separación ya está aprobada; los recorridos de detalle de la tabla requieren cierre de diseño. No se eligen duraciones ni se crea un endpoint por este acuerdo.

Comprobaciones futuras del acuerdo: petición sobre cita confirmada conserva confirmación; rechazo/retirada conserva horario; conflicto de reserva no resuelve la solicitud; caída tras commit deja confirmación invalidada y conciliación recuperable; resolución antigua no sobrescribe una versión nueva. Son criterios, no pruebas ejecutadas.

### P06 · Ofertas con asignación por el personal

**Estado:** criterio aprobado por el usuario el 2026-10-23; revisable antes o durante la implementación si el usuario lo cambia. Se conserva el ID de la propuesta. No implementado; O05 sigue abierto para los detalles restantes. No habilita al paciente a crear o reservar citas desde el Hub.

Una oferta presenta un intervalo concreto y un vencimiento; no reserva ese intervalo. La respuesta del paciente expresa interés o rechazo. Solo el profesional o asistente autorizado pide a API asignar el horario, y API comprueba vigencia de oferta, permisos, disponibilidad y versiones con la reserva. La respuesta de interés no se muestra como cita confirmada.

Como recorrido mínimo propuesto, el personal recibe la respuesta por el canal de comunicación que se apruebe, verifica al paciente y registra el interés mediante una operación autorizada. No se añade ahora una acción pública al Hub ni se supone que WhatsApp tenga una respuesta automática implementada. Cualquier recorrido digital directo del paciente necesita su contrato de acceso y una decisión expresa de alcance.

| Situación propuesta | Resultado |
|---|---|
| Paciente responde con interés | Registrar interés verificable; informar que la asignación sigue pendiente del personal |
| Personal conectado pide asignación | API acepta una reserva válida o devuelve conflicto; oferta y resultado no permiten asignar dos veces el mismo horario |
| Escritorios apagados o personal sin conexión | Cloud puede enviar y conservar ofertas conforme a la política aprobada; no adjudica una cita por la sola respuesta. Una intención local no acredita recepción remota ni detiene el vencimiento |
| Oferta vencida, retirada o intervalo ocupado | No asignar por esa oferta; personal revisa otra alternativa. La siguiente oferta depende de la prioridad aún por acordar |
| Se pierde la respuesta del API al asignar | Consultar o reintentar la misma operación; no crear otra reserva para averiguar el resultado |

Antes de cerrar O05: fijar canal y prueba de respuesta, prioridad, compatibilidad, vencimiento, ofertas simultáneas, notificación al personal y tratamiento de respuestas tardías. La asignación por personal ya está aprobada; los recorridos de detalle de la tabla requieren cierre de diseño. No se fijan tiempos ni se amplía el Hub por deducción.

Comprobaciones futuras del acuerdo: dos personas interesadas no obtienen dos reservas incompatibles; interés sin personal no crea cita; oferta vencida o intervalo ocupado no se asigna; respuesta perdida recupera el resultado original; conocer una oferta no concede acceso a otra cuenta. Son criterios, no pruebas ejecutadas.

### D10 · Corrección de arquitectura y estilo

**Confirmada el 2026-10-26:** el usuario aprobó implementar T34–T45 dentro del plan vigente. Sustituye la distribución previa incompatible de D04/D09 y arquitectura, sin borrar su historia ni cambiar el modelo físico.

- Referencia de estilo: api/authorization. infrastructure solo endpoints/configuración; application casos de uso sin acceso directo a SQLAlchemy; repository modelos y DAOs derivados; domain esquemas, objetos de valor, tipos y errores.
- authorization posee identidad, credenciales y dispositivos globales; accounts cuenta, pertenencias, perfil profesional y autorizaciones por cuenta. Entre componentes, casos de uso y tipos de dominio, no repositorios ajenos.
- Todos los esquemas de datos heredan de la base del proyecto. JSON camelCase y Python snake_case; conservar nombres de protocolos externos y valores exactos de identidad/credenciales.
- Listas y páginas de snapshot usan page/shows, LIMIT/OFFSET e items/total. Eliminar cursores de página y su configuración. Conservar el avance incremental de sincronización y sus garantías, nunca sustituirlo por OFFSET.
- App de módulo, Depends(get_db), fábrica existente y Uvicorn directo; sin lifespan para base de datos. Soporte mínimo de transacción con la sesión recibida; DAOs coordinados con commit=False.
- Scripts pequeños en scripts/, empezando por create_practice.py, en lugar de CLI con subcomandos. No añadir funciones de negocio, dependencias, cambios físicos o despliegues en la corrección.

T34–T36 se detienen en C12; T37–T39 en C13; T40–T42 en C14; T43–T45 en C15. Solo la aceptación de C15 permite retomar T09 y T07. La aprobación no acepta esos checkpoints ni C03. T08 conserva la evidencia histórica y requiere nuevas pruebas tras el traslado.

### D11 · Interfaz del Hub y servidor en Nightingale API

**Confirmada por el usuario el 2026-11-14.** Motivo: reunir en Nightingale API todas las funciones de servidor del Hub. El encargo autoriza solo documentación; no acredita ni autoriza implementar estas funciones.

- Nightingale sigue como escritorio. Patient Hub tendrá repositorio propio para su interfaz web. Nightingale API tendrá todo el servidor que necesite el Hub. El Hub no tendrá backend/API ni almacén privado propios, ni acceso directo a PostgreSQL.
- La primera versión del Hub incluirá micrositios con plantillas definidas para médico independiente (profesional, servicios, ubicación y contacto) y clínica o centro médico (centro, catálogo de servicios, profesionales y ubicación). Sin editor libre ni gestión de pacientes en el Hub. Esto no habilita toda la gestión interna de clínicas, varias sedes o cambios generales del escritorio.
- La lectura del micrositio será pública, sin cuentas de paciente, inicio de sesión o permisos del personal. API ofrecerá endpoints públicos con información destinada a publicación. Las rutas internas actuales conservan su acceso; no se publicarán fichas de pacientes, listados de citas, notas internas ni otros datos privados.
- El paciente podrá consultar la información permitida de una cita existente, confirmar asistencia, cancelar según las reglas, solicitar reprogramación y consultar el resultado. API verificará accesos limitados a esa cita, acción e información necesaria, sin exigir credenciales del personal. Esa información privada no forma parte del micrositio público.
- El paciente no creará ni reservará citas, no explorará disponibilidad para elegir otro horario y no marcará ausencias. El personal conserva el registro de ausencias. Pedir reprogramación conserva estado, horario y confirmación y no reserva otro intervalo. El personal decide el cambio; API aplica la reprogramación con las reglas comunes, incluida la invalidación de confirmación.

**Sustituye:** el reparto anterior de D01 y de las fuentes históricas que asignaba servidor, API pública, almacenamiento, enlaces y solicitudes al Hub; la propuesta entre dos servidores de T04/O02 en access-design.md y contracts.md; y la propiedad/conciliación entre almacenes de los recorridos propuestos en P05. Conserva el criterio funcional de P05. D09 sigue delimitando la implementación actual para escritorio; su exclusión de Hub y clínicas no impide documentar este alcance futuro. P06 no añade reservas ni exploración de horarios por el paciente.

**Pendientes reales:** mecanismo y ciclo del enlace/acceso limitado, vigencia y revocación, proyecciones de publicación y de cita, rutas y formas HTTP, ciclo de solicitud y consulta de resultados. No se deducen cuentas de paciente, sesiones, tablas, campos o un segundo servidor. O02/O04 conservan estos detalles; ya no queda pendiente decidir qué proyecto posee el servidor. El [contrato actual](api-v1.md) no incluye endpoints de micrositio ni acciones del paciente.

**Fuentes y alcance:** encargo de revisión documental del 2026-11-14 y [especificación §5](nightingale-api.md#5-integración-con-patient-hub). [Plan documental](../tasks/P-20261114-01-patient-hub-docs/plan.md). La reunión de documentos en `patient-hub-docs/` con `Master-Plan.md` queda para otra sesión en el repositorio del escritorio; aquí no se crea ni se modifica ese repositorio.

### D12 · Registro clínico y seguimiento del paciente

**Alcance acordado por el usuario el 2026-11-15.** Tras el descubrimiento, el usuario solicita una especificación detallada como referencia principal de los planes de tres etapas. La fuente funcional es [patient-clinical-record.md](patient-clinical-record.md), con acuerdos A01–A15, propuestas de requisitos y pendientes identificados. La redacción completa espera revisión; no se atribuye aceptación de sus detalles nuevos.

El producto ampliará datos de referencia, registro habitual y funciones completas del profesional. El médico decide y el sistema registra. La información clínica mantiene ámbito cuenta/paciente; la cita conserva su función de compromiso. Se automatizan fecha/autor/unidad en la entrada habitual y se distinguen tomas nuevas y correcciones. Edad y última visita se calculan. Médico y asistente son los usuarios principales, con acceso configurable cuyo detalle debe diseñarse.

La tercera etapa incluye planes de cuidados, medicación declarada y prescripción diferenciadas, informes/resultados, funciones por especialidad y analítica histórica individual, con crecimiento pediátrico y comparación con referencias OMS. Toxicidad queda fuera. FHIR R5 aporta referencias conceptuales y de unidades; no se acuerda implementar todo el estándar.

**Efecto sobre acuerdos previos:** amplía el alcance futuro respecto de las exclusiones clínicas de D09 y de la especificación, sin cambiar aquella entrega, su contrato o sus checkpoints. D08 conserva database-schema.md como fuente física; D10 mantiene arquitectura y D11 los límites del Hub. El recorrido de motivo sin conocer servicio queda acordado; su traducción a la obligación actual de serviceId sigue pendiente, no se cambia la FK por deducción.

**Autorización y límites iniciales:** el encargo documental [P-20261115-01-clinical-spec](../tasks/P-20261115-01-clinical-spec/plan.md) no inició código, migraciones ni cambios en escritorio/Hub. C11 del núcleo y C01 documental del Hub conservan su revisión pendiente. Los Oxx de la especificación clínica tienen ámbito propio y no renumeran los pendientes históricos de este registro.

**Ejecución aprobada de etapa 1 el 2026-11-15:** el usuario aprobó [P-20261115-02-patient-clinical-data](../tasks/P-20261115-02-patient-clinical-data/plan.md) y autorizó T01 → T02 → T03, una tarea a la vez y sin delegación, hasta presentar C01. Aprueba las decisiones de producto de §1.1 del plan: sexo al nacer opcional; nacimiento completo opcional existente; edad calculada; texto libre para condiciones y sustancias; alergias, intolerancias y tipo desconocido; fechas clínicas históricas opcionales con precisión variable; permisos por asistente/sección con lectura/escritura inicial; descarga del estado actual e historial aparte; aislamiento por cuenta/paciente. El diseño físico y HTTP se incorpora a sus fuentes únicas para revisión C01. No se acepta C01, no se habilita T04 y no cambian los límites de C11 o de los encargos documentales anteriores.

### D13 · Registro clínico habitual de etapa 2

**Confirmada por el usuario el 2026-11-16** al aprobar [P-20261116-02-clinical-routine](../tasks/P-20261116-02-clinical-routine/plan.md) y autorizar T01–T03. Integra O02/O03/O06/O07/O08/O14/O15 de [patient-clinical-record.md](patient-clinical-record.md); no acepta C01 ni autoriza T04.

- Una atención registrada afirma que ocurrió, sin estados de planificación, firma o cierre. Puede existir sin cita; una cita admite varias atenciones. La anulación por error es terminal y no representa evolución clínica.
- Última visita es el `occurredAt` de la última atención válida de la cuenta/paciente. No depende de citas, notas, aceptación remota ni cierre.
- `serviceId` continúa obligatorio al reservar. Etapa 2 no cambia disponibilidad, duración o snapshots; una atención sin cita conserva el motivo en palabras del paciente.
- Atenciones/notas se editan con versión esperada. Nueva entrada, corrección y anulación se distinguen para mediciones, vacunas y antecedentes; el motivo de corrección es opcional.
- Las mediciones iniciales son peso, presión arterial, temperatura, saturación de oxígeno y frecuencia cardíaca. Talla, perímetro cefálico, frecuencia respiratoria, IMC y curvas quedan fuera.
- Los detalles de vacunas no conocidos son opcionales. Antecedentes narrativos `personal`, `family` u `other` no crean condiciones automáticamente.
- Las cinco nuevas clases de datos tienen permisos por sección; el historial filtra cada fuente antes de contar/paginar.
- La descarga incluye atenciones válidas, versión actual válida de notas/antecedentes, todas las tomas válidas y vacunas vigentes, sin versiones anteriores ni adjuntos.

D08 conserva la fuente física y D10 la arquitectura. El diseño detallado se revisa en C01. Las políticas de copias, restauración, datos reales y producción no quedan resueltas; Etapa 1 conserva sus aceptaciones y límites.

### D14 · Especificación separada de autorización RBAC/ABAC

**Alcance acordado por el usuario el 2026-11-17.** Antes de planificar el desarrollo de los nuevos componentes, cada uno tendrá una especificación propia y detallada. El usuario eligió comenzar por autorización y confirmó que quiere estandarizar de forma deliberada los permisos actuales mediante roles y atributos, en vez de mantenerlos solo como una consecuencia del desarrollo.

La fuente funcional aprobada es [authorization-rbac-abac.md](authorization-rbac-abac.md). Distingue comportamiento vigente, dirección acordada, propuestas de destino y pendientes. Conserva `owner`/`assistant`, la condición profesional como relación, los niveles clínicos por sección, la autoridad de API y la separación D10 entre `authorization` y `accounts`. No traslada permisos de negocio a Keycloak ni introduce un motor externo, roles nuevos, rutas, tablas o dependencias por esta decisión.

La suscripción y sus asientos son condiciones comerciales separadas del permiso personal. El futuro paciente, el operador de Nightingale y los servicios tampoco heredan roles del personal. Sus concesiones concretas pertenecen a las especificaciones correspondientes.

El usuario aprobó la especificación completa el 2026-11-17, incluidas sus propuestas de destino; los `AU-Oxx` permanecen abiertos para las decisiones que expresamente remiten a otros componentes. Esta entrega es documental y no forma un plan de desarrollo: no autoriza código o migraciones, no cambia C09 de Etapa 2 y no acredita implementación nueva. Las especificaciones de suscripciones, facturación y documentos se elaboran por separado.

### D15 · Especificación de suscripciones con verificación manual

**Alcance acordado por el usuario el 2026-11-17.** El siguiente componente especificado es `subscriptions`. La fuente funcional aprobada es [account-subscriptions.md](account-subscriptions.md), separada de autorización y de la futura facturación de pacientes.

El ámbito inicial es Venezuela. Los planes se expresan en USD y se calcula su equivalente a tasa BCV del día; no se utiliza Stripe ni otra plataforma de Billing. El cliente paga fuera del sistema y presenta una captura con los últimos cuatro dígitos de referencia o datos manuales. Un operador de Nightingale revisa y aprueba/rechaza: reportar no activa ni extiende por sí solo. Las periodicidades acordadas son 30 días o un año.

Los planes comerciales son médico independiente, consultorio pequeño y centro médico. Todos conceden las mismas capacidades sin límites comerciales salvo asientos; no se crea una matriz de entitlements por función. Plan, suscripción, pertenencia y dispositivo son conceptos distintos. El plan de centro médico no acredita gestión interna de clínicas ya implementada.

La especificación conserva historia de precios/tasas/periodos, separa datos declarados y verificados, exige aprobación idempotente, protege capturas como documentos privados y coordina asientos concurrentes. Precios, límites, regla anual, fecha exacta de tasa BCV, gracia, suspensión y demás `SU-Oxx` permanecen pendientes; no se inventan valores por esta decisión.

El usuario aprobó la especificación completa el 2026-11-17, incluidas sus propuestas de destino; los `SU-Oxx` permanecen abiertos para las decisiones expresamente pendientes. La entrega es documental: no autoriza código, migraciones, almacenamiento de archivos, operador, rutas o enforcement comercial y no acredita funciones implementadas.

### D16 · Especificación de facturación administrativa de pacientes

**Alcance acordado por el usuario el 2026-11-17.** El siguiente componente especificado es `billing`, con fuente funcional aprobada en [patient-billing.md](patient-billing.md). Registra precios de consultas, cargos, documentos y pagos aprobados, y entrega analítica financiera. No procesa ni mueve dinero, no integra una pasarela y no emite factura fiscal por esta decisión.

El paciente realiza el pago fuera del sistema y presenta un reporte con captura. La asistente autorizada revisa, anota datos verificados y aprueba o rechaza. Un reporte pendiente no reduce saldo ni cuenta como cobrado; una aprobación crea un efecto administrativo único. Datos declarados/verificados, evidencia, cargo, pago y comprobante son conceptos separados.

**Ampliación del acceso futuro del paciente:** D11 se amplía para que el enlace de una cita pueda autorizar también consultar un cargo relacionado, presentar el reporte, consultar su resultado y obtener un comprobante permitido. Sigue sin crear una cuenta general de paciente ni abrir rutas del personal o el micrositio público. El mecanismo, vigencia, revocación y proyecciones concretas permanecen pendientes en `BI-O09`; conocer identificadores no concede acceso.

Los permisos financieros son independientes de los clínicos y de las suscripciones. El componente conserva instantáneas de precios, moneda exacta, historia, idempotencia, concurrencia de saldo y almacenamiento privado. Monedas/BCV para pacientes, permisos iniciales, pagos parciales/excedentes, archivos y demás `BI-Oxx` no se fijan por esta decisión.

El usuario aprobó la especificación completa el 2026-11-17, incluidas sus propuestas de destino; los `BI-Oxx` permanecen abiertos para las decisiones expresamente pendientes. La entrega es documental: no autoriza código, migraciones, almacenamiento, rutas del Hub o analítica nueva y no acredita funciones implementadas.

### D17 · Especificación de récipes y órdenes de diagnóstico

**Alcance acordado por el usuario el 2026-11-17.** El siguiente componente especificado es `clinical_documents`, con fuente funcional aprobada en [clinical-documents.md](clinical-documents.md). Comprende récipes con copia para farmacia/paciente y órdenes de diagnóstico con motivo, exámenes e indicaciones, siguiendo el estilo de las imágenes aportadas.

El médico emite el documento y firma a mano después de imprimir. No se añade firma digital, certificado, envío a farmacias/laboratorios, recomendación clínica o seguimiento de cumplimiento. API conserva datos, instantáneas, historia, sustitución/anulación y PDF privado. Emitir no acredita consumo, dispensación, realización de exámenes o firma física.

El documento creado desde una cita queda vinculado automáticamente, sin copiar contenido a `appointment_histories` ni cambiar cita, atención o última visita. **D11/D16 se amplían** para que el enlace privado pueda autorizar lectura/descarga de documentos clínicos emitidos relacionados con la cita. No crea cuenta general de paciente, acceso a toda la historia ni publicación en el micrositio. Concesión, vigencia, revocación y herencia a sustitutos quedan en `CD-O10`.

El QR se propone para verificación mínima de número/fecha/estado, separado del enlace privado y sin paciente, medicamentos, diagnóstico o exámenes. La emisión exige profesional activo y permiso específico; ser propietario o asistente no basta. Numeración, datos mínimos, permisos iniciales, emisión online/offline, plantilla, requisitos jurídicos y demás `CD-Oxx` permanecen pendientes.

El usuario aprobó la especificación completa el 2026-11-17, incluidas sus propuestas de destino; los `CD-Oxx` permanecen abiertos para las decisiones expresamente pendientes. Con esta aprobación, las cuatro especificaciones nuevas son referencias funcionales aprobadas. La entrega es documental: no autoriza código, migraciones, PDF, almacenamiento, rutas del Hub o verificación pública y no acredita funciones implementadas.

### D18 · Planes separados para implementar los cuatro componentes

**Alcance acordado por el usuario el 2026-11-17.** El usuario pidió un plan de implementación dedicado a cada especificación aprobada, redactados en secuencia sin detenerse entre ellos para aprobar cada borrador. Se aplicó `planning-task-breakdown` y se conservó `docs-first-framework-code` para las futuras decisiones de bibliotecas/plataforma. No se delegó ni se implementó código.

Los planes son [P-20261117-01-authorization-policies](../tasks/P-20261117-01-authorization-policies/plan.md), [P-20261117-02-account-subscriptions](../tasks/P-20261117-02-account-subscriptions/plan.md), [P-20261117-03-patient-billing](../tasks/P-20261117-03-patient-billing/plan.md) y [P-20261117-04-clinical-documents](../tasks/P-20261117-04-clinical-documents/plan.md). Contienen 103 tareas y 36 checkpoints en total, con propietarios, dependencias, datos/contratos/transacciones/consumidores, archivos previstos, comprobaciones y evidencia pendiente.

El orden de ejecución es autorización → suscripciones → facturación → documentos clínicos. Autorización requiere antes el cierre aceptado de C09 de Etapa 2; cada plan posterior depende del checkpoint final aceptado del anterior. Las decisiones `SU-Oxx`, `BI-Oxx` y `CD-Oxx` se resuelven en tareas iniciales antes del trabajo dependiente, sin valores supuestos. Almacenamiento, comprobantes y PDF exigen fuentes oficiales/versiones antes de elegir herramientas.

El usuario aprobó los cuatro planes el 2026-11-17. Quedan **Approved** y todas sus tareas Todo; ningún checkpoint está aceptado. La aprobación no habilita trabajo paralelo ni elimina las precondiciones y el orden de ejecución, y no cambia por sí sola el plan activo de Etapa 2. Solo el usuario acepta los checkpoints durante la ejecución.

### D19 · Plan del resto de Etapa 3 sin prescripción

**Alcance acordado por el usuario el 2026-11-17.** El usuario pidió dejar prescripción/récipes en su plan existente y planificar los demás bloques de Etapa 3, sin afectar el trabajo actual de Autorización. La nueva fuente de ejecución propuesta es [P-20261117-05-clinical-stage-3](../tasks/P-20261117-05-clinical-stage-3/plan.md), con [lista de tareas](../tasks/P-20261117-05-clinical-stage-3/todo.md).

El plan cubre medicación declarada, tratamiento/planes de cuidados, informes/resultados, plantillas/primera especialidad y analítica histórica individual con referencias OMS. Contiene 36 tareas y 12 checkpoints. No modifica ni sustituye P-20261117-04 y no ejecuta prescripción, emisión, PDF, QR o acceso del paciente a esos documentos.

La planificación usa las reglas de `planning-task-breakdown`; datasets, bibliotecas, almacenamiento y métodos OMS requieren fuentes oficiales/versiones según `docs-first-framework-code`. El usuario aprobó el plan el 2026-11-17: queda **Approved**, con todas las tareas Todo y ningún checkpoint aceptado. No se inicia mientras Autorización esté In progress y no se modifican sus tareas, archivos o estados. No hay trabajo paralelo ni cambios en Rust/Hub.

**Inicio anticipado autorizado el 2026-11-17.** El usuario decidió expresamente comenzar la ejecución de P-20261117-05 ese mismo día, sin esperar el cierre Completed de Autorización (P-20261117-01), que sigue In progress. Esta autorización sustituye solo la precondición de espera de este plan: no modifica el plan de Autorización ni interrumpe su trabajo, no habilita ediciones paralelas sobre sus archivos y no acepta ningún checkpoint de Etapa 3 por adelantado. Las tareas de Etapa 3 que consuman el resultado final de Autorización esperan su cierre; el resto avanza por fases con revisión de checkpoints por el usuario.

**Decisiones de producto cerradas para Etapa 3 el 2026-11-17 (T02/T03):** la primera especialidad es odontología con odontograma; los indicadores OMS iniciales son peso/edad, talla o longitud/edad, peso/talla o longitud e IMC/edad (patrones 2006 y referencia 2007); los permisos de los nuevos bloques reusan las secciones `none/read/read_write` por pertenencia de Etapas 1/2; los adjuntos privados usan almacenamiento de objetos S3 con adaptador mínimo sin instalar dependencias. El detalle figura en [§4.3.1 de la especificación clínica](patient-clinical-record.md) y cierra O09–O13 para el alcance de este plan.

### D20 · Vademecum venezolano global de solo lectura

**Confirmada por el usuario el 2026-11-22** al aprobar [P-20261122-01-vademecum-read-api](../tasks/P-20261122-01-vademecum-read-api/plan.md). La decisión fija alcance y arquitectura; no declara implementación, revisión profesional, integración con el escritorio ni despliegue.

- La fuente autoritativa de importación es [vademecum_venezuela_2026-11-03.json](../vademecum/vademecum_venezuela_2026-11-03.json), con monografías conformes a [monograph.schema.json](../vademecum/monograph.schema.json). Comprende los productos vigentes y las monografías de esa fuente, incluidos productos sin vínculo y monografías sin productos. Las copias individuales de apoyo y `data.js` no son fuentes de importación.
- `src/api/vademecum` será un componente global dentro de la aplicación FastAPI existente, con domain/application/repository/infrastructure y persistencia PostgreSQL. No será otra aplicación ni parte de la medicación declarada por pacientes. Las rutas llevan `account_id` para reutilizar el contexto de acceso, sin duplicar el catálogo por cuenta.
- Solo el propietario profesional y los asistentes con usuario, pertenencia, cuenta y dispositivo activos pueden consultar el catálogo en línea. No se añade acceso público/paciente, permiso clínico nuevo, escrituras HTTP, flujo de revisión, sincronización ni almacenamiento offline.
- Las lecturas incluyen productos vigentes, monografías completas, búsqueda acotada por nombre, alias, registro, ingrediente e identificador canónico y ATC. Excluyen productos históricos, dataset suplementario, administración cruda de la fuente y búsqueda en todo el texto clínico.
- El contenido pendiente se publica con aviso visible, estado de revisión, fuentes, procedencia, corte del registro, huella de fuente y calidad del vínculo/resolución. Las referencias extranjeras no se presentan como registros venezolanos.
- Cada importación administrativa valida todo el archivo y crea un release por huella SHA-256; guarda su contenido y lo activa en una sola transacción. Solo un release está activo, repetir la huella no cambia datos y los releases anteriores se conservan. La identidad administrativa es separada y el rol runtime recibe solo SELECT sobre las tablas del componente.

### D21 · Planes, precios y asientos de suscripciones (T01)

**Decidido por el usuario el 2026-11-26** durante la ejecución de T01 de [P-20261117-02-account-subscriptions](../tasks/P-20261117-02-account-subscriptions/plan.md). Cierra `SU-O02`, `SU-O05` y `SU-O08` de [account-subscriptions.md](account-subscriptions.md); no autoriza por sí solo código, migraciones ni contratos.

- **Precios USD (`SU-O05`):** médico independiente USD 18 por 30 días y USD 100 por año; consultorio pequeño USD 24 y USD 240; centro médico USD 75 y USD 500. Son los precios iniciales del catálogo; un cambio posterior crea una versión nueva del plan conforme a §7.3.
- **Cómputo de asientos (`SU-O02`):** se confirma la regla de §8.1. Cuenta cada pertenencia humana activa y única por cuenta, incluido el propietario; un usuario con varias relaciones profesionales en la misma cuenta consume un solo asiento. Invitaciones pendientes, pertenencias inactivas, dispositivos, pacientes/contactos y el operador de Nightingale no consumen asiento.
- **Límites numéricos (`SU-O02`):** independiente 2 asientos, consultorio pequeño 5, centro médico 20.
- **Exceso de asientos (`SU-O08`):** se confirma §8.4. Una reducción de plan o corrección que deje a la cuenta por encima del límite no desactiva personas automáticamente; conserva acceso e historia, impide nuevas incorporaciones y reactivaciones hasta volver al límite y señala la situación al propietario.

### D22 · Tasa BCV, monedas y periodos de suscripciones (T02)

**Decidido por el usuario el 2026-11-26** durante la ejecución de T02 de [P-20261117-02-account-subscriptions](../tasks/P-20261117-02-account-subscriptions/plan.md). Cierra `SU-O03`, `SU-O04` y `SU-O06` de [account-subscriptions.md](account-subscriptions.md); no autoriza por sí solo código, migraciones ni integración BCV automática.

- **Fecha de la tasa (`SU-O03`):** se aplica la tasa BCV de la fecha del pago declarada y verificada por el operador. Si ese día no hay publicación, se usa la tasa publicada más reciente anterior. Si la fecha del pago no es verificable, el operador no aprueba con una tasa elegida por el cliente y registra su decisión conforme a la política administrativa.
- **Monedas de pago admitidas (`SU-O03`):** VES y USD. La aprobación conserva importe y moneda efectivamente verificados junto a la tasa, fecha y fuente aplicadas.
- **Periodicidad anual (`SU-O04`):** un año es el año civil en `America/Caracas`: el periodo termina en la misma fecha civil del año siguiente. Un inicio el 29 de febrero termina el 28 de febrero del año siguiente.
- **Inicio de periodos (`SU-O06`):** se confirma la propuesta de §11. El periodo inicial comienza en el instante de aprobación del operador. La renovación anticipada comienza en el `endsAt` del último periodo aprobado, sin perder días. La renovación tardía comienza en el instante de aprobación del servidor, sin retroactividad por fechas declaradas salvo corrección administrativa justificada.

### D23 · Operador de Nightingale: identidad, ciclo de vida y canal (T03)

**Decidido por el usuario el 2026-11-26** durante la ejecución de T03 de [P-20261117-02-account-subscriptions](../tasks/P-20261117-02-account-subscriptions/plan.md). Cierra `SU-O01` y `SU-O12` de [account-subscriptions.md](account-subscriptions.md); no autoriza por sí solo código, migraciones ni contratos.

- **Autenticación (`SU-O01`):** el operador se autentica en Keycloak con una identidad separada del personal de cuentas. API lo reconoce como operador de plataforma y emite una credencial opaca sin vencimiento, revocable en API, siguiendo el patrón vigente de dispositivos. No recibe pertenencia, rol de cuenta ni acceso clínico. La revocación en API es la que retira el acceso; logout o desactivación en Keycloak no revocan por sí solos una credencial ya emitida.
- **Ciclo de vida (`SU-O01`):** el alta, la recuperación y la revocación de operadores son un componente de la propia API, gestionable por el usuario, no solo un script. Un operador con la acción separada de gestión de operadores puede dar de alta, revocar y recuperar a otros operadores. La recuperación revoca la credencial anterior y emite una nueva; no se recuperan secretos guardados. El alta del primer operador usa el flujo administrativo de despliegue.
- **Canal (`SU-O12`):** rutas de operador dentro de la misma aplicación FastAPI, protegidas por acciones de plataforma separadas del RBAC de cuentas. No se deduce un módulo del Hub ni una interfaz nueva en esta etapa.

### D24 · Gracia, evidencias y excepciones de pago en suscripciones (T04)

**Decidido por el usuario el 2026-11-26** durante la ejecución de T04 de [P-20261117-02-account-subscriptions](../tasks/P-20261117-02-account-subscriptions/plan.md). Cierra `SU-O07` y `SU-O09`–`SU-O11` de [account-subscriptions.md](account-subscriptions.md); no autoriza por sí solo código, migraciones ni almacenamiento.

- **Gracia y suspensión (`SU-O07`):** 7 días de gracia con servicio normal tras el fin del periodo. Después, suspensión: se bloquean las escrituras operativas, se conserva la lectura/exportación de datos y permanecen siempre disponibles la renovación y la consulta del estado comercial. Offline: el servidor comunica el fin de gracia en la proyección; el reloj local no extiende vigencia ni concede días. Nada de esto borra datos ni revoca identidades.
- **Capturas (`SU-O09`):** formatos admitidos JPG, PNG y PDF; máximo 5 MB por archivo; una captura por reporte. La evidencia y los reportes se conservan mientras la cuenta exista; no se borran al rechazar ni al vencer la suscripción. La eliminación solo ocurre por un proceso administrativo trazado. Copias de seguridad y restauración siguen la política general de operación antes de datos reales.
- **Pagos atípicos (`SU-O10`):** solo se aprueba como periodo completo un reporte cuyo importe verificado cubre el importe debido. Pagos parciales o excedentes no se aprueban: el operador los rechaza con motivo y el cliente presenta un reporte corregido. Varios periodos requieren un reporte por periodo. Las coincidencias de referencia parcial generan advertencia al operador, nunca rechazo ni borrado automático.
- **Cambio de plan (`SU-O11`):** sin prorrateo. El nuevo plan y su precio aplican al siguiente periodo aprobado; el tiempo pagado del plan anterior se conserva completo. Un plan inferior exige cumplir el límite de asientos o la política de exceso de D21.

### D25 · Monedas, precios y vínculos de cargos de pacientes (T01)

**Decidido por el usuario el 2026-11-27** durante la ejecución de T01 de [P-20261117-03-patient-billing](../tasks/P-20261117-03-patient-billing/plan.md). Cierra `BI-O01`–`BI-O03` de [patient-billing.md](patient-billing.md); no autoriza por sí solo código, migraciones ni contratos.

- **Monedas (`BI-O01`):** precios de catálogo y cargos de pacientes admiten USD y VES. Cada precio/cargo declara una sola moneda ISO 4217; nunca se suman ni restan monedas distintas ni se revaloriza historia.
- **Conversión USD/VES (`BI-O01`):** se admiten cargos USD pagados en VES. La conversión es explícita y previa a aplicar el pago, con la tasa BCV de la fecha del pago declarada y verificada por quien revisa (misma regla de fecha/fuente de D22, con configuración e historia propias de facturación). El pago conserva importe USD, tasa, fecha/fuente, equivalente VES y redondeo; nada se revaloriza después.
- **Precisión y redondeo (`BI-O01`):** importes con decimal exacto (nunca punto flotante binario), dos decimales; el redondeo de la conversión VES es half-up a dos decimales y queda registrado junto a la tasa. Nulo significa «sin precio definido»; cero es un precio válido (servicio gratuito) y no equivale a nulo.
- **Precio base/oferta (`BI-O02`):** se confirma la resolución base/oferta: el precio de la oferta de la cuenta sustituye al precio base del profesional cuando existe. El paciente puede ver una estimación no vinculante antes de que exista cargo; la estimación no crea obligación ni reserva precio. El cargo emitido copia descripción, importe, moneda, tasa y origen en instantánea; cambios posteriores del catálogo no alteran cargos.
- **Vínculos y ajustes (`BI-O03`):** se permiten cargos sin cita/atención (cargo libre) y ajustes manuales del importe, ambos solo con el permiso financiero correspondiente y registrados en la historia del cargo. Nunca hay cargo automático por crear, completar o cancelar citas o atenciones.

### D26 · Reportes de pago, parciales/excedentes y pagos directos (T02)

**Decidido por el usuario el 2026-11-27** durante la ejecución de T02 de [P-20261117-03-patient-billing](../tasks/P-20261117-03-patient-billing/plan.md). Cierra `BI-O04`, `BI-O06` y `BI-O07` de [patient-billing.md](patient-billing.md); no autoriza por sí solo código, migraciones ni contratos.

- **Datos del reporte (`BI-O04`):** obligatorios: cargo, fecha del pago, importe y moneda, método declarado y captura válida. La referencia es opcional y siempre parcial (por ejemplo, últimos dígitos); la nota breve es opcional. Nunca se solicitan números bancarios completos.
- **Parciales y excedentes (`BI-O06`):** se admiten varios pagos aprobados sobre un cargo mientras la suma de pagos vigentes no supere el total. Un pago que excede el saldo no se aprueba: la asistente lo rechaza con motivo y el paciente presenta un reporte corregido. Un pago se aplica a un solo cargo; no genera crédito ni se aplica a otros cargos automáticamente. Dos aprobaciones simultáneas no pueden exceder el total (coordinación de saldo en PostgreSQL).
- **Pagos directos (`BI-O07`):** se incluye el origen `staff_entry` para efectivo u otros pagos recibidos por la consulta, con permiso propio y evidencia propia; nunca se simula un reporte del paciente. Comparte las mismas reglas de moneda, saldo y efecto único, y su origen queda distinguible en lecturas y analítica.

### D27 · Permisos financieros iniciales y correcciones (T03)

**Decidido por el usuario el 2026-11-27** durante la ejecución de T03 de [P-20261117-03-patient-billing](../tasks/P-20261117-03-patient-billing/plan.md). Cierra `BI-O05` y `BI-O08` de [patient-billing.md](patient-billing.md); no autoriza por sí solo código, migraciones ni contratos.

- **Valores iniciales (`BI-O05`):** asistentes nuevos y existentes no reciben ninguna acción financiera por defecto; el propietario concede cada acción explícitamente. El propietario conserva acceso financiero completo en su cuenta. Ningún permiso clínico concede acciones financieras ni viceversa.
- **Granularidad (`BI-O05`):** el catálogo agrupa la autorización financiera de pacientes en tres acciones: `billing_read` (consultar cargos/saldos, reportes/evidencias en lectura y analítica autorizada), `billing_charges` (crear/editar borradores, emitir y cancelar cargos, ajustes manuales de D25) y `billing_review` (revisar reportes, aprobar/rechazar, registrar `staff_entry` y anular pagos/corregir). Modificar precios sigue con el permiso propio de catálogo/oferta. Estas acciones sustituyen la tabla granular de §15.1.
- **Corrección con pagos (`BI-O08`):** un cargo con pagos vigentes no puede cancelarse; primero se anulan los pagos con la acción de corrección, motivo, actor e instante, conservando reporte, evidencia, comprobante e historia. Anular un pago lo excluye del saldo vigente y no afirma devolución de fondos; no existe reembolso real ni constancia de devolución en esta etapa. Los comprobantes emitidos conservan su instantánea y muestran el estado posterior.

### D28 · Concesión del paciente, offline, archivos y primer panel (T04)

**Decidido por el usuario el 2026-11-27** durante la ejecución de T04 de [P-20261117-03-patient-billing](../tasks/P-20261117-03-patient-billing/plan.md). Cierra `BI-O09`–`BI-O12` de [patient-billing.md](patient-billing.md); no autoriza por sí solo código, migraciones ni contratos.

- **Concesión (`BI-O09`):** la concesión del enlace vive mientras la cita esté activa y hasta 30 días después de la atención o el cierre de la cita; el personal puede revocarla en cualquier momento. Cancelar la cita revoca la concesión (un reporte ya presentado conserva su historia y su revisión); reprogramar la cita la mantiene. El secreto del enlace se almacena con huella, nunca en claro, y conocer el UUID no concede nada.
- **Offline (`BI-O10`):** solo los borradores de cargo pueden prepararse offline, como operaciones tipadas que API revalida al sincronizar (precio, objeto, permiso y versión vigentes; un rechazo conserva la intención local). Reportes del paciente, carga/descarga de evidencia, aprobación/rechazo, anulaciones, pagos directos `staff_entry` y cambios de permisos son online. La copia local nunca prueba saldo ni permiso vigente.
- **Archivos (`BI-O11`):** misma política de capturas de D24: JPG, PNG y PDF; máximo 5 MB por archivo; una captura por reporte. Los comprobantes son PDF generado por API. Capturas, comprobantes y reportes se conservan mientras la cuenta exista; no se borran al rechazar, vencer o cancelar. La eliminación solo ocurre por un proceso administrativo trazado. Copias de seguridad y restauración siguen la política general de operación antes de datos reales.
- **Primer panel (`BI-O12`):** los siete indicadores de §19.1 (total cargado, total cobrado, saldo pendiente, pendiente de revisión, pagos parciales, cargos pagados, anulaciones). Fechas: cargado y saldo por fecha de emisión del cargo; cobrado por fecha de aprobación, declarada así en el contrato. Totales siempre separados por moneda, sin revalorizar VES histórico; pendientes no cuentan como cobrado y anulados no suman al vigente.

## Propuestas

| ID | Propuesta, motivo y alternativa | Consecuencia / revisión |
|---|---|---|
| P01 | Una aplicación modular con procesos HTTP y worker; componentes de [arquitectura](architecture.md). Evita dividir despliegues por capacidad antes de necesitarlo | Compartir casos de uso y recursos con permisos separados; revisar en C01 |
| P02 | Una unidad de trabajo pequeña coordina propietarios sin commits en repositorios. Alternativa: función explícita equivalente si resulta más simple | No filtrar SQL al dominio/aplicación; demostrar rollback integral; C01 y T07 |
| P03 | OpenAPI y JSON Schema con una fuente por tipo. Alternativas de fuente: esquema primero o modelos del adaptador que generan artefactos | Elegir origen, generación y compatibilidad en T05 antes del contrato ejecutable |
| P04 | Trabajo duradero en PostgreSQL y publicación tras commit; un broker puede servir de transporte | Un broker no sustituye la evidencia persistente. Comparar sondeo y publicación en T16; no escoger cola ahora |

P05/P06 conservan sus IDs de origen, pero sus criterios ya figuran entre las decisiones confirmadas. Los detalles no aprobados se distinguen en sus apartados y en O04/O05.

## Herramientas: propuesta inicial y selección actual

La propuesta inicial no fijaba versiones. Después, el usuario añadió Python, `uv` y las dependencias del manifiesto y autorizó iniciar la fundación. Se conservó esa selección y se añadió el extra `sqlalchemy[asyncio]` que exige su API asíncrona. Versiones comprobadas y fuentes por API: [guía de desarrollo](operations/development.md). La tabla siguiente conserva la comparación inicial; no ordena instalar alternativas.

| Necesidad | Candidato y razón | Alternativa / condición de elección |
|---|---|---|
| Entorno y dependencias reproducibles | `uv`, por gestión de entorno y [lockfile verificable](https://docs.astral.sh/uv/concepts/projects/sync/) | `venv`/pip con estrategia de bloqueo explícita; elegir un solo gestor en T02 |
| Persistencia y migraciones | SQLAlchemy, por consultas y [control de transacciones](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), con Alembic para [migraciones versionadas](https://alembic.sqlalchemy.org/en/latest/) | Psycopg con SQL explícito y migraciones controladas; comparar coste y claridad antes de elegir. No mantener dos vías de persistencia para el mismo caso; SQLAlchemy sí necesita un controlador |
| Controlador PostgreSQL | Psycopg si satisface el modo de I/O y las versiones elegidas | Comparar con el controlador compatible requerido; su [gestión de transacciones](https://www.psycopg.org/psycopg3/docs/basic/transactions.html) exige límites explícitos |
| Configuración | Validación de entorno al iniciar; evaluar `pydantic-settings` si reduce código real | Biblioteca estándar con validación concreta. No convertir configuración ni DTO en dominio |
| Pruebas y revisión estática | Evaluar pytest y Ruff; HTTPX solo si hace falta al cliente de prueba | Biblioteca estándar donde baste; T02 debe justificar cada herramienta, versiones y comandos |
| Servicio HTTP | Evaluar Uvicorn como servidor ASGI de FastAPI | Modo y número de procesos según entorno y medidas, sin copiar Docker/Compose ni elegir cloud |

**Selección para T03:** Python 3.15.1, uv/uv_build 0.13.4, FastAPI 0.159.1, Pydantic 2.14.1, pydantic-settings 2.16.1, SQLAlchemy 2.1.6, asyncpg 0.32.0 y Uvicorn 0.54.0. `uv.lock` fija las dependencias; greenlet 3.5.6 llegó mediante el extra asyncio. Se usa unittest y el cliente HTTPX ya instalado, sin añadir pytest o Ruff. PostgreSQL de prueba, migraciones/Alembic y despliegue siguen pendientes. No se interpreta “PostgreSQL 18” en una referencia como versión elegida.

## Pendientes y condición para resolverlos

**Lectura vigente tras D11:** D11 fija el servidor y el alcance futuro del Hub; quedan su diseño de acceso y contratos, sin implementar. O04 conserva el ciclo de solicitud separado de Citas. Las pruebas del escritorio y sus límites figuran en el plan vigente, no se deducen de una decisión.

**Lectura histórica tras D09:** O01 se concreta para el escritorio de esta etapa en el contrato v1 (queda su prueba, no una elección de sesiones). O03 y la parte sync de O10 tienen diseño acotado de contador/snapshot/90 días y compatibilidad v1, aún sin comprobación de producto. O08 tiene selección local aprobada, no entorno ejecutado ni despliegue. O09 incorpora el objetivo local de avisos, no un SLO de producción. O04 fija duración, margen y criterio administrativo; globales y Hub siguen aplazados. La tabla siguiente conserva la trazabilidad del plan anterior; sus Txx no son la lista vigente de ejecución.

| ID | Decisión y evidencia necesaria | Propietario de decisión / antes de |
|---|---|---|
| O01 | Parcialmente resuelta por D06: OIDC externo, permisos/dispositivos en API y permisos vigentes al aceptar. Faltan proveedor, sesiones, alta/vínculo de dispositivo, roles, orden de revocación y recorrido de revisión | Usuario y responsable de seguridad/API; T04, antes de T08 |
| O02 | D11 resuelve servidor y lectura pública. Falta diseñar en API el acceso limitado a una cita, enlace, vigencia/revocación y consulta de resultados, sin credenciales del personal ni autorización entre dos backends | API y web Hub con revisión del usuario; antes de implementar el contrato futuro. T04/T15 solo como antecedentes |
| O03 | Orden confirmado, snapshot/cursor, expiración, bajas, retención de idempotencia y ventana de compatibilidad | API + consumidores; prueba razonada de carreras y recuperación en T05, antes de T07/T13 |
| O04 | D08 fija el esquema como fuente del modelo; sus §§8.3 y 8.9 distinguen acuerdos, propuestas y pendientes. La corrección de identidad global queda aplazada sin bloquear trabajo independiente. T06 concreta las reglas restantes de su alcance y el ciclo de solicitud separado según P05 | Usuario/producto, API + Hub; revisión T24 y cierre de lo necesario en T06, antes de la función afectada en T09–T12/T15 |
| O05 | Lista de espera: prioridad, oferta/expiración, canal y prueba de respuesta y tratamiento de casos tardíos. P06 confirma interés separado y asignación por personal; quedan sus detalles | Usuario/producto y propietarios; T19 antes de T20. Mantener límite actual del Hub |
| O06 | Política y proveedor oficial de WhatsApp, datos permitidos, cancelación de trabajos y conciliación de resultado desconocido | Usuario/producto y comunicaciones; evidencia del proveedor en T17 antes de envíos reales |
| O07 | Cola, reclamación y recuperación de workers; reintentos, límite, revisión manual y autenticación de n8n | API/operación; diseño y fallos controlados en T16/T18, antes de activar integración |
| O08 | Entornos de desarrollo/prueba, versión de PostgreSQL, proveedor cloud, red, secretos y despliegue | Usuario/operación; T02 para entorno de prueba, T22 para despliegue. No heredar las decisiones cloud históricas del escritorio |
| O09 | Límites, carga representativa, latencia, disponibilidad y demora admisible; alertas y umbrales | Usuario/producto/operación; medición y presupuesto en T22, antes de aceptar producción |
| O10 | Retención por clase (cambios, resultados, auditoría, datos, trabajos, copias), acceso y eliminación; RPO/RTO y restauración | Usuario/producto/operación; T05 para sync, T22 antes de datos reales/producción |
| O11 | Definición de indicadores, datos mínimos, ventana y frecuencia ETL; límites de uso analítico | Usuario/producto + API; T21 antes de fijar proyecciones |

Los pendientes no impiden revisar esta propuesta. Sí impiden implementar la parte que dependa de ellos. Para cambiar una decisión, registrar fecha, motivo, alcance, alternativa, consecuencia y qué ID sustituye; conservar la anterior como historial.
