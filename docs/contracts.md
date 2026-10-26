# Contratos y propiedad

**Estado al 2026-10-26:** C04 aceptado; T13–T15 para revisión C05. El [contrato de diseño HTTP v1](api-v1.md), revisión 1.1, conserva camelCase y page/shows. patients posee identidad mínima, fichas/documentos y contactos/vínculos; accounts conserva permisos, sync coordina recibos/grupos y audit conserva hechos. Las aceptaciones no registran un dispositivo por deducción. Servicios, agenda/citas, clientes generados e integración de consumidores siguen pendientes.

## Una fuente por contrato

| Artefacto | Propietario de la fuente | Consumidores y forma de compartir |
|---|---|---|
| Operaciones, resultados, consulta de resultado, descarga y recuperación | Nightingale API | Escritorio Rust; artefacto versionado y pruebas contra esa versión |
| Consultas y acciones internas de citas para el Hub | Nightingale API; acuerdo revisado por Hub | Backend del Hub; misma fuente y ejemplos compartidos |
| Eventos, trabajo interno, webhooks recibidos y API interna de n8n | Nightingale API | Workers, adaptadores, n8n y ETL autorizados |
| Migraciones y esquema PostgreSQL operativo/analítico | Nightingale API | Procesos autorizados; no contrato SQL público |
| API pública del Hub, enlaces, sesiones, política del paciente y solicitudes | Patient Hub | Web del paciente y escritorio; API consume solo las capacidades necesarias |
| Comandos Tauri, SQLite, Outbox, aplicación de páginas y estados visibles | Escritorio | React y Rust; no son fuente de esquemas remotos |

Selección aprobada para v1: esquemas Pydantic de domain derivados del BaseModel del proyecto como origen de OpenAPI y JSON Schema, con tipos comunes en core/schema. La base conserva alias camelCase y los atributos Python siguen en snake_case. Los proveedores externos conservan sus nombres propios de protocolo. Hasta implementarlos, api-v1.md posee el diseño; después conserva explicación y ejemplos, no una segunda definición editable del esquema generado. El generado identifica origen/versión y las pruebas verifican correspondencia; no se editan ambos. Consumidores fijan una versión o huella. La base de datos no genera un contrato público por defecto.

Para el modelo de datos operativo cubierto, [database-schema.md](database-schema.md) es la única fuente de diseño por instrucción del usuario del 2026-10-24. Sus acuerdos sustituyen las reglas previas incompatibles de D07; las propuestas pendientes se distinguen en el propio esquema. El borrador lógico anterior queda retirado. La revisión 1.0 añade soporte físico de acceso/sync/auditoría en §9, sin convertirlo en contrato HTTP; el comportamiento y las proyecciones públicas viven en api-v1.md. Analítica, Hub y módulos excluidos conservan sus fuentes y tareas posteriores.

La precedencia depende del tema: SRS y decisiones funcionales confirmadas fijan requisitos del producto; API posee la aceptación remota y sus contratos; Hub posee su API pública, accesos y solicitudes; escritorio posee comandos, SQLite y operación local. Una decisión posterior confirmada identifica qué sustituye. La copia del escritorio ya trasladada es antecedente; las fuentes originales y sus versiones figuran en [sources.md](sources.md). Las propuestas no sustituyen acuerdos confirmados.

## Operaciones y resultados

Los criterios siguientes conservan su fundamento; en el ámbito de escritorio v1, sus elecciones están concretadas en api-v1.md y D09. Las referencias a T04/T05 históricas corresponden al plan sustituido; ejecutar las tareas del sucesor. Hub conserva sus acuerdos pendientes y queda fuera de la entrega.

El acuerdo previo a código debe fijar:

- Identidad estable de operación, contrato, cuenta, entidad, acción, versión esperada, payload mínimo y dependencia causal. Actor, dispositivo/servicio y cuenta proceden de identidad validada o se contrastan con ella. La hora del cliente no concede permisos.
- Espacio de claves idempotentes ligado a identidad y cuenta verificadas; comparación canónica del contenido. Dos peticiones simultáneas con igual clave producen un efecto; con distinto contenido producen conflicto, sin revelar datos de otra cuenta.
- Resultado por operación: aceptada, duplicada, conflicto, rechazada o fallo temporal; versión y datos permitidos. HTTP y código de error se acordarán sin exponer SQL ni trazas. Duplicada conserva el resultado original y no declara aceptación si aquel fue un rechazo.
- Alcance y retención del resultado, consulta tras respuesta perdida, rechazo por revocación y tratamiento de fallos antes/durante/después del commit. Una clave purgada no autoriza repetir un efecto antiguo: habrá ventana contractual y recuperación explícita.
- Límites de bytes, operaciones, páginas, tiempo y frecuencia; orden/dependencias del lote, errores parciales y compatibilidad. No procesar campos libres como asignaciones arbitrarias al modelo.

La autorización se comprueba también para consultas, duplicados, exportaciones y errores. El consumidor no puede obtener un resultado revocado por conocer su identificador. El error permitido y el procedimiento de revisión deben conservar la intención local sin revelar el dato remoto.

## Paginación, avance incremental y snapshot

Las listas y elementos del snapshot usan page desde 1 y shows 100 por defecto, máximo 500; DAO aplica LIMIT/OFFSET, autorización y filtros antes de paginar y contar. Reutilizar PaginatedResponse con items/total. No hay cursores de página, firmas ni configuración de paginación. Las listas corrientes pueden variar entre peticiones; una captura materializada conserva su conjunto y orden mientras siga vigente y autorizado.

El avance incremental mantiene orden confirmado, frontera compartida con snapshot, continuidad, bajas, ámbito por cuenta/permisos y recuperación ante posición inválida o vencida. No se expresa mediante OFFSET ni la hora del equipo. Su cursor representa solo la posición del último cambio aplicado, con versión, alcance y vigencia verificables; no se comparte con listados. T28–T30 deben demostrar estas garantías.

Si cambia la autorización, API impide nuevas lecturas fuera de alcance y exige la recuperación definida. El protocolo podrá ordenar retirar datos locales, pero no prueba que un equipo intervenido los haya borrado. Retenciones de cambios, bajas y resultados deben cubrir la ventana de escritorios soportados o forzar recuperación segura. El arranque conserva la intención pendiente en el escritorio; no la sobrescribe con el snapshot.

## Hub

La identidad técnica acredita al backend del Hub, pero no su derecho sobre una cita. T04 debe definir cómo API verifica cuenta, cita, acciones, versión, vencimiento y revocación de cada concesión sin apropiarse de enlaces o reglas del Hub. Comparar una concesión limitada verificable con una consulta autenticada de autorización; documentar confianza, rotación, reuso y fallos de ambas opciones. No aceptar un `practice_id` o un encabezado de actor como prueba.

El acuerdo distinguirá confirmar/cancelar una cita de solicitar un cambio en el almacén del Hub. Definirá versiones, invalidación de confirmación al reprogramar, rechazo/retirada de solicitudes y conciliación de fallos parciales. Un éxito remoto con respuesta perdida se recupera por la misma operación. No se compensa cambiando otra vez la cita sin un caso de uso autorizado.

La reprogramación aceptada cambia el intervalo e invalida la confirmación anterior dentro de una sola transacción de API. Un aviso posterior al Hub concilia accesos y solicitudes; no decide la validez de la confirmación compartida. Su fallo no deshace la cita ni permite repetir su efecto con otra identidad.

Este contrato no permite al paciente crear citas, listar disponibilidad general ni elegir o reservar otro horario. El recorrido de ofertas de lista de espera requiere una decisión previa y no amplía por sí solo estas acciones.

[P05](decisions.md#p05--solicitud-de-reprogramación-separada) confirma la solicitud separada del estado de cita; pedir un cambio conserva estado, horario y confirmación. [P06](decisions.md#p06--ofertas-con-asignación-por-el-personal) confirma que la respuesta a una oferta expresa interés y que el personal autoriza la reserva. El usuario aprobó ambos criterios el 2026-10-23 y puede revisarlos antes o durante la implementación. Los ciclos, canales y formatos exactos siguen pendientes en O04/O05; no se añaden capacidades públicas al Hub.

## Trabajo y compatibilidad

Los eventos describen hechos aceptados; llevan identidad, tipo/versión, cuenta, entidad/versión, correlación, causa y tiempo del servidor cuando corresponda. Los mensajes de trabajo usan identificadores y datos mínimos. El acuerdo define duplicados, orden necesario, firma/autenticación de webhooks, reintentos, resultado desconocido y consulta al proveedor. Cada proyección puede reconstruirse o tiene un procedimiento de recuperación documentado.

Versiones de contrato, aplicación y esquema son distintas. Cambios opcionales requieren comprobar consumidores; eliminar campos, cambiar significado o ampliar enumeraciones sin un tratamiento seguro exige compatibilidad explícita. T05 fijará ventana de soporte, matriz API/escritorio/Hub y aviso de retirada. Migraciones y despliegues mantienen operativos los consumidores soportados; no exigen que todos actualicen a la vez.
