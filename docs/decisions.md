# Registro de decisiones

**Fecha:** 2026-10-21. Confirmada significa acordada en el encargo o fuente vigente; propuesta requiere revisión; pendiente no autoriza una elección por defecto. Ningún estado acredita implementación.

## Confirmadas

### D01 · Tres proyectos y API transaccional

**Contexto:** el escritorio puede modificarse y operar sin red. **Decisión:** conserva casos de uso Rust/SQLite y envía operaciones completas; API autoriza y acepta el estado compartido en PostgreSQL privado. Hub conserva su web, API, enlaces, reglas y solicitudes y usa API para citas. Repositorios separados.

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

Proveedor, dispositivo y acceso del escritorio se concretan después en D09 y [diseño de acceso](access-design.md); el Hub sigue abierto. Las alternativas previas de sesiones quedan como antecedente. Ninguna decisión acredita implementación ni permite eludir permisos vigentes.

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

La solicitud pertenece al Hub y referencia una cita y su versión. Pedir un cambio no altera el estado, horario ni confirmación de la cita. `reschedule_requested` no forma parte del estado de negocio de Citas; el escritorio muestra la solicitud como información separada. La reserva original sigue vigente hasta una operación autorizada que la cambie o cancele. Este criterio sustituye la propuesta de incluir la solicitud como estado de cita en DAT §11; no fija todavía el ciclo completo de la solicitud.

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

- Referencia de estilo: api/users. infrastructure solo endpoints/configuración; application casos de uso sin acceso directo a SQLAlchemy; repository modelos y DAOs derivados; domain esquemas, objetos de valor, tipos y errores.
- authorization posee identidad, credenciales y dispositivos globales; accounts cuenta, pertenencias, perfil profesional y autorizaciones por cuenta. Entre componentes, casos de uso y tipos de dominio, no repositorios ajenos.
- Todos los esquemas de datos heredan de la base del proyecto. JSON camelCase y Python snake_case; conservar nombres de protocolos externos y valores exactos de identidad/credenciales.
- Listas y páginas de snapshot usan page/shows, LIMIT/OFFSET e items/total. Eliminar cursores de página y su configuración. Conservar el avance incremental de sincronización y sus garantías, nunca sustituirlo por OFFSET.
- App de módulo, Depends(get_db), fábrica existente y Uvicorn directo; sin lifespan para base de datos. Soporte mínimo de transacción con la sesión recibida; DAOs coordinados con commit=False.
- Scripts pequeños en scripts/, empezando por create_practice.py, en lugar de CLI con subcomandos. No añadir funciones de negocio, dependencias, cambios físicos o despliegues en la corrección.

T34–T36 se detienen en C12; T37–T39 en C13; T40–T42 en C14; T43–T45 en C15. Solo la aceptación de C15 permite retomar T09 y T07. La aprobación no acepta esos checkpoints ni C03. T08 conserva la evidencia histórica y requiere nuevas pruebas tras el traslado.

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

**Lectura vigente tras D09:** O01 se concreta para el escritorio de esta etapa en el contrato v1 (queda su prueba, no una elección de sesiones). O03 y la parte sync de O10 tienen diseño acotado de contador/snapshot/90 días y compatibilidad v1, aún sin comprobación de producto. O08 tiene selección local aprobada, no entorno ejecutado ni despliegue. O09 incorpora el objetivo local de avisos, no un SLO de producción. O04 fija duración, margen y criterio administrativo; globales y Hub siguen aplazados. La tabla siguiente conserva la trazabilidad del plan anterior; sus Txx no son la lista vigente de ejecución.

| ID | Decisión y evidencia necesaria | Propietario de decisión / antes de |
|---|---|---|
| O01 | Parcialmente resuelta por D06: OIDC externo, permisos/dispositivos en API y permisos vigentes al aceptar. Faltan proveedor, sesiones, alta/vínculo de dispositivo, roles, orden de revocación y recorrido de revisión | Usuario y responsable de seguridad/API; T04, antes de T08 |
| O02 | Cómo API verifica el alcance del Hub y su revocación; confianza, concesiones, rotación y consulta de resultados | API + Hub con revisión del usuario; T04, antes de T15 |
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
