# Contratos y propiedad

**Estado:** criterios de diseño para revisión; aún no hay rutas, esquemas ejecutables ni clientes generados. Complementa los límites de [la especificación](nightingale-api.md), sin fijar su formato final.

## Una fuente por contrato

| Artefacto | Propietario de la fuente | Consumidores y forma de compartir |
|---|---|---|
| Operaciones, resultados, consulta de resultado, descarga y recuperación | Nightingale API | Escritorio Rust; artefacto versionado y pruebas contra esa versión |
| Consultas y acciones internas de citas para el Hub | Nightingale API; acuerdo revisado por Hub | Backend del Hub; misma fuente y ejemplos compartidos |
| Eventos, trabajo interno, webhooks recibidos y API interna de n8n | Nightingale API | Workers, adaptadores, n8n y ETL autorizados |
| Migraciones y esquema PostgreSQL operativo/analítico | Nightingale API | Procesos autorizados; no contrato SQL público |
| API pública del Hub, enlaces, sesiones, política del paciente y solicitudes | Patient Hub | Web del paciente y escritorio; API consume solo las capacidades necesarias |
| Comandos Tauri, SQLite, Outbox, aplicación de páginas y estados visibles | Escritorio | React y Rust; no son fuente de esquemas remotos |

Se propone OpenAPI para HTTP y JSON Schema para mensajes, con tipos comunes referenciados desde una sola fuente. T05 decidirá si HTTP se define primero en esquema o en modelos del adaptador. El archivo generado se identifica como tal y CI verifica su correspondencia; no se editan ambos. Los consumidores fijan una versión o huella del artefacto. El esquema de base de datos nunca genera un contrato público por defecto.

## Operaciones y resultados

El acuerdo previo a código debe fijar:

- Identidad estable de operación, contrato, cuenta, entidad, acción, versión esperada, payload mínimo y dependencia causal. Actor, dispositivo/servicio y cuenta proceden de identidad validada o se contrastan con ella. La hora del cliente no concede permisos.
- Espacio de claves idempotentes ligado a identidad y cuenta verificadas; comparación canónica del contenido. Dos peticiones simultáneas con igual clave producen un efecto; con distinto contenido producen conflicto, sin revelar datos de otra cuenta.
- Resultado por operación: aceptada, duplicada, conflicto, rechazada o fallo temporal; versión y datos permitidos. HTTP y código de error se acordarán sin exponer SQL ni trazas. Duplicada conserva el resultado original y no declara aceptación si aquel fue un rechazo.
- Alcance y retención del resultado, consulta tras respuesta perdida, rechazo por revocación y tratamiento de fallos antes/durante/después del commit. Una clave purgada no autoriza repetir un efecto antiguo: habrá ventana contractual y recuperación explícita.
- Límites de bytes, operaciones, páginas, tiempo y frecuencia; orden/dependencias del lote, errores parciales y compatibilidad. No procesar campos libres como asignaciones arbitrarias al modelo.

La autorización se comprueba también para consultas, duplicados, exportaciones y errores. El consumidor no puede obtener un resultado revocado por conocer su identificador. El error permitido y el procedimiento de revisión deben conservar la intención local sin revelar el dato remoto.

## Cursor y snapshot

T05 debe demostrar: orden confirmado, frontera de snapshot, continuidad a incremental, cambios concurrentes, bajas lógicas, ámbito por cuenta/permisos y tratamiento de cursor manipulado, vencido o de otra cuenta. La paginación usa un orden estable; no deriva el cursor de la hora del equipo ni salta transacciones aún sin confirmar.

Cursor y snapshot tendrán versión, alcance y vigencia verificables. Si cambia la autorización, API debe impedir nuevas lecturas fuera de alcance y definir si exige recuperación. El protocolo podrá ordenar retirar datos locales, pero no prueba que un equipo intervenido los haya borrado. Retenciones de cambios, bajas y resultados deben cubrir la ventana de escritorios soportados o forzar recuperación segura. El arranque conserva la intención pendiente en el escritorio; no la sobrescribe con el snapshot.

## Hub

La identidad técnica acredita al backend del Hub, pero no su derecho sobre una cita. T04 debe definir cómo API verifica cuenta, cita, acciones, versión, vencimiento y revocación de cada concesión sin apropiarse de enlaces o reglas del Hub. Comparar una concesión limitada verificable con una consulta autenticada de autorización; documentar confianza, rotación, reuso y fallos de ambas opciones. No aceptar un `practice_id` o un encabezado de actor como prueba.

El acuerdo distinguirá confirmar/cancelar una cita de solicitar un cambio en el almacén del Hub. Definirá versiones, invalidación de confirmación al reprogramar, rechazo/retirada de solicitudes y conciliación de fallos parciales. Un éxito remoto con respuesta perdida se recupera por la misma operación. No se compensa cambiando otra vez la cita sin un caso de uso autorizado.

Este contrato no permite al paciente crear citas, listar disponibilidad general ni elegir o reservar otro horario. El recorrido de ofertas de lista de espera requiere una decisión previa y no amplía por sí solo estas acciones.

## Trabajo y compatibilidad

Los eventos describen hechos aceptados; llevan identidad, tipo/versión, cuenta, entidad/versión, correlación, causa y tiempo del servidor cuando corresponda. Los mensajes de trabajo usan identificadores y datos mínimos. El acuerdo define duplicados, orden necesario, firma/autenticación de webhooks, reintentos, resultado desconocido y consulta al proveedor. Cada proyección puede reconstruirse o tiene un procedimiento de recuperación documentado.

Versiones de contrato, aplicación y esquema son distintas. Cambios opcionales requieren comprobar consumidores; eliminar campos, cambiar significado o ampliar enumeraciones sin un tratamiento seguro exige compatibilidad explícita. T05 fijará ventana de soporte, matriz API/escritorio/Hub y aviso de retirada. Migraciones y despliegues mantienen operativos los consumidores soportados; no exigen que todos actualicen a la vez.
