# Contratos y propiedad

**Estado al 2026-11-16:** C09/C10 aceptados; C11 del núcleo sigue pendiente. El [contrato HTTP v1](api-v1.md), revisión 1.2, conserva camelCase y page/shows. La corrección clínica está implementada hasta T19 para revisión C07: 60 rutas, 98 esquemas y 51 acciones generadas. El manifiesto incluye origen, `sourceHead`, `sourceSha256` y huellas de archivos; dos generaciones y `--check` producen los mismos artefactos. Consumidores y producción siguen pendientes. [OpenAPI/JSON Schema](../contracts/README.md) se generan desde la app/modelos reales. Los ejemplos de la [guía Rust](rust-api-guide.md) se comprueban contra PostgreSQL/Keycloak aislados. C11 no está aceptado.

## Una fuente por contrato

| Artefacto | Propietario de la fuente | Consumidores y forma de compartir |
|---|---|---|
| Operaciones, resultados, consulta de resultado, descarga y recuperación | Nightingale API | Escritorio Rust; artefacto versionado y pruebas contra esa versión |
| Futuras lecturas públicas de micrositios y acciones limitadas de citas del Hub | Nightingale API; diseño pendiente bajo D11 | Interfaz web del Hub; sin backend propio ni credenciales del personal para el paciente |
| Eventos, trabajo interno, webhooks recibidos y API interna de n8n | Nightingale API | Workers, adaptadores, n8n y ETL autorizados |
| Migraciones y esquema PostgreSQL operativo/analítico | Nightingale API | Procesos autorizados; no contrato SQL público |
| Interfaz web del Hub y plantillas de micrositios | Patient Hub, en su propio repositorio | Visitantes y pacientes; consume contratos de API. API poseerá accesos, reglas y solicitudes; no se acuerdan sesiones ni cuentas de paciente |
| Comandos Tauri, SQLite, Outbox, aplicación de páginas y estados visibles | Escritorio | React y Rust; no son fuente de esquemas remotos |

Selección aprobada para v1: esquemas Pydantic de domain derivados del BaseModel del proyecto como origen de OpenAPI y JSON Schema, con tipos comunes en core/schema. La base conserva alias camelCase y los atributos Python siguen en snake_case. Los proveedores externos conservan sus nombres propios de protocolo. Hasta implementarlos, api-v1.md posee el diseño; después conserva explicación y ejemplos, no una segunda definición editable del esquema generado. El generado identifica origen/versión y las pruebas verifican correspondencia; no se editan ambos. Consumidores fijan una versión o huella. La base de datos no genera un contrato público por defecto.

Para el modelo de datos operativo cubierto, [database-schema.md](database-schema.md) es la única fuente de diseño por instrucción del usuario del 2026-10-24. Sus acuerdos sustituyen las reglas previas incompatibles de D07; las propuestas pendientes se distinguen en el propio esquema. El borrador lógico anterior queda retirado. La revisión 1.0 añade soporte físico de acceso/sync/auditoría en §9, sin convertirlo en contrato HTTP; el comportamiento y las proyecciones públicas viven en api-v1.md. Analítica, Hub y módulos excluidos conservan sus fuentes y tareas posteriores.

La precedencia depende del tema: SRS y decisiones funcionales confirmadas fijan requisitos del producto; API posee la aceptación remota y todos los contratos y funciones de servidor del Hub; Hub posee su interfaz web; escritorio posee comandos, SQLite y operación local. [D11](decisions.md#d11--interfaz-del-hub-y-servidor-en-nightingale-api) sustituye el reparto previo de API pública, accesos, reglas y solicitudes en un servidor del Hub. La copia del escritorio ya trasladada es antecedente; las fuentes originales y sus versiones figuran en [sources.md](sources.md). Las propuestas no sustituyen acuerdos confirmados.

## Operaciones y resultados

Los criterios siguientes conservan su fundamento; en el ámbito de escritorio v1, sus elecciones están concretadas en api-v1.md y D09. Las referencias a T04/T05 históricas corresponden al plan sustituido; ejecutar las tareas del sucesor. El alcance futuro del Hub está acordado por D11; su diseño e implementación quedan fuera del contrato actual.

El acuerdo previo a código debe fijar:

- Identidad estable de operación, contrato, cuenta, entidad, acción, versión esperada, payload mínimo y dependencia causal. Actor, dispositivo/servicio y cuenta proceden de identidad validada o se contrastan con ella. La hora del cliente no concede permisos.
- Espacio de claves idempotentes ligado a identidad y cuenta verificadas; comparación canónica del contenido. Dos peticiones simultáneas con igual clave producen un efecto; con distinto contenido producen conflicto, sin revelar datos de otra cuenta.
- Resultado por operación: aceptada, duplicada, conflicto, rechazada o fallo temporal; versión y datos permitidos. HTTP y código de error se acordarán sin exponer SQL ni trazas. Duplicada conserva el resultado original y no declara aceptación si aquel fue un rechazo.
- Alcance y retención del resultado, consulta tras respuesta perdida, rechazo por revocación y tratamiento de fallos antes/durante/después del commit. Una clave purgada no autoriza repetir un efecto antiguo: habrá ventana contractual y recuperación explícita.
- Límites de bytes, operaciones, páginas, tiempo y frecuencia; orden/dependencias del lote, errores parciales y compatibilidad. No procesar campos libres como asignaciones arbitrarias al modelo.

La autorización se comprueba también para consultas, duplicados, exportaciones y errores. El consumidor no puede obtener un resultado revocado por conocer su identificador. El error permitido y el procedimiento de revisión deben conservar la intención local sin revelar el dato remoto.

## Paginación, avance incremental y snapshot

Las listas y elementos del snapshot usan page desde 1 y shows 100 por defecto, máximo 500; DAO aplica LIMIT/OFFSET, autorización y filtros antes de paginar y contar. Reutilizar PaginatedResponse con items/total. No hay cursores de página, firmas ni configuración de paginación. Las listas corrientes pueden variar entre peticiones; una captura materializada conserva su conjunto y orden mientras siga vigente y autorizado.

El avance incremental mantiene orden confirmado, frontera compartida con snapshot, continuidad, retiradas, ámbito por cuenta/permisos y recuperación ante posición inválida o vencida. No se expresa mediante OFFSET ni la hora del equipo. Su cursor representa la posición que el consumidor debe aplicar junto a los datos, con versión, alcance y vigencia verificables; no se comparte con listados. T28–T30 prueban estas garantías del servidor con PostgreSQL aislado; la aplicación atómica en SQLite sigue pendiente del consumidor.

Si cambia la autorización, API impide nuevas lecturas fuera de alcance y exige la recuperación definida. El protocolo podrá ordenar retirar datos locales, pero no prueba que un equipo intervenido los haya borrado. Retenciones de cambios, bajas y resultados deben cubrir la ventana de escritorios soportados o forzar recuperación segura. El arranque conserva la intención pendiente en el escritorio; no la sobrescribe con el snapshot.

## Hub

**Contrato actual:** api-v1.md sirve al escritorio y al personal autorizado. No ofrece endpoints de micrositios ni acciones del paciente. Los modelos y rutas de cuentas, servicios y citas no son por ello un contrato público del Hub.

**Alcance futuro acordado por D11:** API tendrá todos los endpoints y funciones de servidor del Hub. Habrá dos accesos distintos:

| Uso futuro | Información y acciones permitidas | Acceso |
|---|---|---|
| Micrositio con plantillas para médico independiente o clínica/centro | Presentación, servicios, ubicación; contacto del profesional o profesionales del centro según plantilla. Solo información destinada a publicación | Lectura pública, sin cuenta de paciente, inicio de sesión ni permisos del personal |
| Gestión de una cita existente | Información permitida de esa cita; confirmar, cancelar según reglas, solicitar reprogramación y consultar resultado | Acceso limitado verificado por API para cita/acción e información necesaria, sin credenciales del personal |

La lectura pública no incluye fichas de pacientes, listados de citas, notas internas ni otra información privada; tampoco abre las rutas internas. No habrá editor libre ni gestión de pacientes en el Hub. Incluir clínicas en su presentación pública no habilita gestión interna completa, varias sedes o cambios generales del escritorio.

El paciente no crea ni reserva citas, no explora disponibilidad para elegir otro horario y no marca ausencias; el personal conserva ese registro. [P05](decisions.md#p05--solicitud-de-reprogramación-separada) conserva la solicitud separada del estado de cita: pedir cambio conserva estado, horario y confirmación y no reserva otro intervalo. El personal decide el cambio; API cambia el intervalo e invalida la confirmación anterior dentro de una transacción con las reglas comunes. [P06](decisions.md#p06--ofertas-con-asignación-por-el-personal) no amplía estas acciones del paciente.

**Diseño pendiente:** mecanismo de enlace y acceso limitado, vigencia/revocación, proyecciones de publicación y cita, formas HTTP y ciclo de solicitudes/resultados. La consulta de resultados requerirá el mismo alcance limitado; no bastará conocer un identificador de cita, cuenta, actor u operación. Se deberá resolver una respuesta perdida sin repetir el efecto. No se fijan aquí rutas, campos, tablas ni cuentas de paciente.

**Antecedente sustituido:** T04 comparaba concesión de servicio con consulta autenticada al backend del Hub, y separaba solicitudes en su almacén privado. D11 elimina ese segundo servidor y asigna estas funciones a API. La comparación histórica se conserva en [access-design.md](access-design.md#antecedente-sustituido-autorización-entre-servidores); no es un requisito vigente.

## Trabajo y compatibilidad

Los eventos describen hechos aceptados; llevan identidad, tipo/versión, cuenta, entidad/versión, correlación, causa y tiempo del servidor cuando corresponda. Los mensajes de trabajo usan identificadores y datos mínimos. El acuerdo define duplicados, orden necesario, firma/autenticación de webhooks, reintentos, resultado desconocido y consulta al proveedor. Cada proyección puede reconstruirse o tiene un procedimiento de recuperación documentado.

Versiones de contrato, aplicación y esquema son distintas. Cambios opcionales requieren comprobar consumidores; eliminar campos, cambiar significado o ampliar enumeraciones sin un tratamiento seguro exige compatibilidad explícita. T05 fijará ventana de soporte, matriz API/escritorio/Hub y aviso de retirada. Migraciones y despliegues mantienen operativos los consumidores soportados; no exigen que todos actualicen a la vez.
