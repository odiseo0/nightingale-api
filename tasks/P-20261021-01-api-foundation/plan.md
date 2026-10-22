# P-20261021-01-api-foundation

**Estado:** In progress. **Fecha:** 2026-10-21. **Trabajo actual:** T04, acuerdo de acceso. **C03:** habilitado por el usuario tras corregir las anotaciones.

El 2026-10-21 el usuario indicó que ya había instalado dependencias y añadió código base; autorizó comenzar la fundación. Esa instrucción habilita T03 con su selección de herramientas y sustituye la espera documental de C01/C02 para este alcance. La base PostgreSQL de prueba de O08 sigue pendiente y debe definirse antes de T07. No se extiende esta autorización a esquema, negocio o despliegue.

Después pidió cambiar las anotaciones de `@asynccontextmanager` a `AsyncGenerator` y autorizó continuar. La corrección y sus comprobaciones permiten iniciar T04. Confirmó OIDC externo y permisos vigentes al aceptar; el resto se distingue como propuesta en [diseño de acceso](../../docs/access-design.md).

## Objetivo y límites

Preparar una base de desarrollo para Nightingale API conforme a [la especificación](../../docs/nightingale-api.md). La base de proceso T03 ya permite iniciar el acuerdo documental T04. Las decisiones de negocio y seguridad pendientes conservan sus puntos de revisión.

No incluye código del escritorio/Hub, datos reales, historias clínicas, pagos, varias sedes, SQL desde consumidores ni despliegue actual. Las pruebas de consumidor reales se coordinan después en sus repositorios; no se cambian desde esta tarea. Los pasos posteriores no se ejecutan solo por figurar en el plan.

## Dependencias y controles comunes

- Seguir [arquitectura](../../docs/architecture.md), [contratos](../../docs/contracts.md), [decisiones](../../docs/decisions.md) y requisitos Q01–Q16 de [calidad](../../docs/quality.md).
- Las dependencias `Txx` indican trabajo comprobado; además debe estar aceptado el checkpoint anterior. Oxx son decisiones abiertas que debe cerrar el propietario indicado en el registro.
- C01/C02 quedan habilitados para la base de proceso por la instrucción posterior del usuario descrita arriba. Cada checkpoint posterior requiere revisión expresa antes de continuar.
- Cada tarea usa datos ficticios, cambia solo su alcance y registra comandos/versiones/resultados reales. T02 define los comandos; no se presentan comandos imaginados como controles ya disponibles.
- Probar persistencia y concurrencia con PostgreSQL real aislado; no SQLite. Un resultado local no acredita CI, consumidores reales ni operación en cloud.
- No crear archivos de todos los componentes por anticipación. Definir el contrato necesario y construir el recorrido mínimo de la tarea. Si el tamaño impide una revisión concreta, dividir antes de ejecutar.

## Tareas y criterios de aceptación

| ID | Trabajo / propietario | Depende de | Aceptación y comprobaciones |
|---|---|---|---|
| T01 | Documentación y propuesta / documentación | Especificación del usuario y fuentes disponibles | Guía, arquitectura, propiedad, calidad, decisiones y plan legibles; enlaces/IDs coherentes; fuente técnica preservada; evidencia documental en `docs/sources.md` |
| T02 | Herramientas, versiones y entorno de prueba / composición y operación | T01 + C01 | Comparar candidatos, seleccionar versiones estables compatibles, un gestor/lockfile y PostgreSQL de prueba; páginas oficiales por versión, comandos previstos y permisos mínimos. Resolver O08 para pruebas. Solo documentación, sin instalar |
| T03 | Base mínima de proceso y controles / composición, settings, core | T02 + C02 | Manifiesto/lockfile aprobados, arranque/cierre y configuración validada; salud de proceso/preparación sin datos de producto, pruebas/controles desde entorno limpio. No crear aún tablas de negocio. Documentar comandos reales |
| T04 | Acuerdo de acceso y revocación / access + Hub | T03 + C03; O01, O02 | Definir identidad, membresía, dispositivo, servicio, concesión por objeto, sesiones, renovación/revocación y orden frente a commit. Matriz de amenazas y resultados para pendientes con hora manipulada; revisión del usuario antes de código de acceso |
| T05 | Contrato de aceptación/descarga y evolución / sync | T04; O03, parte sync de O10 | Fuente contractual elegida, operaciones/errores/lotes, claves/resultados, cursor/snapshot y compatibilidad. Razonar carreras con commits invertidos y expiración, justificar retención con ventana de soporte. Diseño, sin migraciones |
| T06 | Reglas administrativas y transiciones / patients, services, schedule, appointments + Hub | T04; O04 | Campos mínimos, intervalos UTC/zona, duración, validación cruzada y restricciones; acciones permitidas y salidas de solicitudes del Hub. Diseñar carreras agenda/cita y actividad de referencias. No deducir transiciones abiertas |
| T07 | Persistencia y límite atómico / repository, core, sync, audit | T05, T06 + C04 | Implementar la base técnica y migraciones aprobadas, identidades SQL separadas y coordinación sin commit parcial. Preparar registros de aceptación/cambios/trabajo. Pruebas de migración y fallo integral en PostgreSQL; verificar esquema no público |
| T08 | Acceso remoto y aislamiento / access | T07 | Aplicar el acuerdo de T04 a entradas/repositorios y prueba por objeto. Dos cuentas, servicio Hub limitado, revocación concurrente y consulta de resultados protegida; sin acceso abierto temporal para avanzar |
| T09 | Pacientes mínimos / patients | T08 + C05, T06 | Alta/cambio de contacto/inactividad con versión, autorización y baja sincronizable; errores sin datos ajenos. Dominio, persistencia y HTTP; no incluir notas clínicas |
| T10 | Catálogo de servicios / services | T09, T06 | Catálogo limitado por cuenta, duración según acuerdo, versiones y actividad. Probar referencias ajenas y cambios frente a citas según T06 |
| T11 | Agenda / schedule | T10, T06 | Horarios/excepciones/bloqueos con zona y versiones; lectura acotada. Probar límites de intervalos y coordinación con reservas/bloqueos concurrentes, sin otra tabla autoritativa de disponibilidad |
| T12 | Aceptación de citas / appointments, sync, audit | T11 + C06, T05 | Crear, confirmar, cancelar, reprogramar, atender y marcar ausencia conforme a transiciones aprobadas. Efecto/versión/historial/auditoría/resultado/cambios/trabajo atómicos. Probar reserva concurrente, estado manipulado, fallo y duplicado; los canales externos aún pueden ser sustitutos |
| T13 | Descarga incremental y recuperación / sync | T12, T05 | Páginas y snapshot vinculados con bajas y expiración; ámbitos/versiones y contratos de consumidores. Demostrar ausencia de omisiones con commits invertidos, reconstrucción y cambios de permisos |
| T14 | Pruebas conjuntas de aceptación/sync / propietarios T08–T13 | T13 | Ejecutar Q01–Q08 con conexiones independientes: payload manipulado, clave concurrente y contenido distinto, respuesta perdida tras commit, pendientes tras revocación, lotes y páginas. Guardar estado final y límites de evidencia; no suplir con mocks SQL |
| T15 | Adaptador interno del Hub y conciliación / appointments + access | T14 + C07; T04, T06 | Consultas mínimas/acciones con concesión verificable, misma aceptación y resultado recuperable; no construir Hub aquí. Probar cancelación/reprogramación simultáneas, versión antigua, concesión ajena/revocada y fallo parcial. La prueba contra Hub real queda pendiente si no está disponible |
| T16 | Trabajo duradero y recuperación / communications, core | T15 + C08; O07 | Seleccionar transporte y política de reclamación/reintentos con revisión antes de implementarlos. Persistencia tras commit, reclamación acotada y recuperación de trabajo interrumpido; probar caída entre commit/publicación y competencia de workers |
| T17 | Recordatorios y entregas / communications | T16; O06 | Aprobar política/proveedor antes del adaptador real. Programar/inutilizar trabajos por versión; obtener accesos del Hub sin poseerlos. Probar duplicados, cancelación, timeout recibido por proveedor y conciliación/revisión; registrar estados de entrega sin prometer envío único sin respaldo externo |
| T18 | Webhooks y n8n / communications | T17; O07 | Contrato autenticado limitado, firma/duplicados/orden y resultado de trabajos; n8n sin SQL operativo. Probar reenvío, manipulación, aislamiento y caída/reinicio. Dividir recepción y adaptador n8n si requieren revisiones separadas |
| T19 | Acuerdo de lista de espera / waitlist + producto | T18 + C09; O05 | Cerrar prioridad, compatibilidad, oferta, vencimiento, respuesta y papel del personal. Identificar dueño del recorrido del paciente sin ampliar Hub por deducción. Revisión expresa antes de T20 |
| T20 | Lista de espera / waitlist + appointments | T19 + C10 | Entradas/ofertas según acuerdo, baja/retiro/vencimiento, asignación por aceptación de Citas sin escribir sus tablas. Probar dos aceptaciones, horario ocupado y oferta antigua; una respuesta no garantiza reserva |
| T21 | Indicadores básicos / analytics | T20; O11 | Definir fórmulas y frecuencia antes de implementar proyecciones en PostgreSQL separado; consumo/avance repetible y alcance por cuenta. Repetir lote sin doble conteo y recuperar caída ETL; sin informe costoso sobre operativo |
| T22 | Operación y restauración / operación, todos los adaptadores | T21; O08–O10 | Proponer y revisar límites/umbrales, disponibilidad, retenciones, red/secretos, copias y RPO/RTO. Verificar salud, carga, recuperación y restauración en entorno aislado autorizado. No desplegar producción por esta tarea; registrar lo no disponible |
| T23 | Integración y aceptación de versión / API + consumidores | T22 + C11 | Matriz contractual, cambios de esquema compatibles, casos conjuntos de Q01–Q16 y recorrido con Hub/escritorio cuando estén disponibles. Separar evidencia de API de pruebas externas faltantes; preparación de publicación para revisión, sin desplegar por defecto |

T07 crea solo la base técnica aprobada; cada componente añade sus migraciones al existir su caso de uso. Los contratos y las restricciones compartidas quedan definidos antes, sin crear un modelo global editable desde todos los componentes. T12/T14 deben repetir las carreras de cambios de agenda con citas reales; T11 por sí sola no acredita ese recorrido.

## Checkpoints

| ID | Revisar al terminar | Habilita tras aprobación |
|---|---|---|
| C01 | T01: alcance, arquitectura, propiedad, pendientes, calidad y secuencia | T02 documental; sin implementación |
| C02 | T02: herramientas/versiones, entorno aislado y comandos propuestos | T03: primera instalación y base de proceso |
| C03 | T03: base reproducible y evidencia de recursos/configuración | T04–T06: acuerdos previos, sin dominio persistido |
| C04 | T04–T06: seguridad, sync, estados y restricciones, pendientes necesarios cerrados | T07–T08: persistencia técnica y acceso |
| C05 | T07–T08: migraciones, atomicidad y aislamiento | T09–T11: datos mínimos, catálogo y agenda |
| C06 | T09–T11: referencias y reglas de agenda | T12–T14: citas y sync completas |
| C07 | T12–T14: evidencia concurrente, idempotencia y recuperación | T15: adaptación al Hub |
| C08 | T15: alcance del servicio y conciliación | T16–T18: workers e integraciones, con sus decisiones previas |
| C09 | T16–T18: trabajo recuperable y entrega/resultado desconocido | T19: acuerdo de lista de espera |
| C10 | T19: alcance de ofertas y papel del paciente/personal | T20–T22: lista de espera, indicadores y preparación operativa |
| C11 | T20–T22: datos, indicadores, restauración y objetivos aprobados | T23: integración para aceptación de versión |
| C12 | T23: evidencia disponible y faltantes externos identificados | Solo cierre del plan si se cumplen los criterios; despliegue requiere alcance propio |

## Riesgos y cierre

El orden del cursor puede limitar concurrencia; medirlo antes de comprometer un objetivo. Una identidad Hub sin prueba por objeto abre acceso excesivo. Retención corta puede romper reintentos o recuperación. Un resultado desconocido del proveedor exige conciliación. Los acuerdos pendientes se resuelven en sus tareas antes de implementar; no se ocultan en valores por defecto.

El plan termina cuando los controles aplicables pasan y el usuario acepta C12. Si faltan consumidores, proveedor o entorno, el hito afectado queda pendiente; no se declara completado por usar sustitutos. No se implementa acceso mientras T04/O01/O02 sigan abiertos.
