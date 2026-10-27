# Especificación técnica breve: Nightingale API

**Versión:** 0.4
**Fecha:** 2026-10-27
**Estado:** C01–C06 y C12–C18 aceptados. T19–T27 comprobadas; C09 listo para revisión, sin marcar aceptación de C07–C09. Agenda, disponibilidad con ocupación real y ciclo de citas probado con PostgreSQL/Keycloak aislados. Se conservan credenciales, equipo, auditoría, pacientes/contactos y alta administrativa. Snapshot, descarga, SSE y consumidores siguen pendientes; T32 conserva pruebas conjuntas de procesos y avisos.
**Decisión:** [Tres proyectos y API transaccional](decisions.md#d01--tres-proyectos-y-api-transaccional).

## 1. Propósito y tecnología

La primera etapa aprobada está en [P-20261024-01-desktop-shared-api](../tasks/P-20261024-01-desktop-shared-api/plan.md). [api-v1.md](api-v1.md) fija su diseño de rutas/operaciones/modelos públicos; [database-schema.md](database-schema.md) conserva la única fuente física, ampliada en 1.0 para revisar en C01. Los apartados generales de Hub, comunicaciones y analítica describen el producto posterior, no trabajo autorizado de esta entrega.

La corrección aprobada conserva arquitectura hexagonal por componentes con api/users como estilo: infrastructure solo endpoints; application casos de uso sin acceso directo a SQLAlchemy; repository modelos y DAOs derivados; domain esquemas de la base del proyecto, valores y errores. JSON camelCase, listas y snapshot con page/shows, LIMIT/OFFSET e items/total. No hay cursores de página; sí posición de avance incremental de sync. authorization y accounts tienen propietarios separados. Los workflows de alta son scripts pequeños, sin sistema CLI. App de módulo, fábrica existente, inyección de dependencias y Uvicorn directo; sin lifespan para base de datos.

Nightingale API es el límite remoto de seguridad y aceptación del estado compartido. Usa Python y FastAPI en su propio repositorio. El escritorio ejecuta sus casos de uso con Rust/SQLite; la API no es necesaria para consultar o guardar datos locales permitidos.

La API recibe operaciones de alto nivel y entrega cambios incrementales. No ofrece SQL, acceso libre a tablas ni un guardado ciego de objetos enviados por el cliente.

## 2. Responsabilidades y datos

- Autenticar personas, dispositivos y servicios; comprobar cuenta, pertenencia, alcance y revocaciones según la política de acceso.
- Aceptar operaciones sobre pacientes, servicios, agenda y citas, con versiones, transiciones e integridad compartida.
- Conservar en PostgreSQL operativo entidades aceptadas, historial, auditoría, operaciones y resultados idempotentes, Change Log y trabajos persistentes.
- Atender al backend del Patient Hub con consultas limitadas y acciones sobre la cita autorizada. La API aplica reglas comunes; el Hub posee enlaces y política del paciente.
- Poseer migraciones del esquema operativo y sus contratos de lectura/escritura. Ningún escritorio ni Hub migra o escribe directamente ese esquema.
- Incluir módulos y workers para recordatorios, entregas/webhooks, integración con n8n y analítica. No son proyectos adicionales ni parte de la transacción de sincronización.

## 3. Contrato de operaciones

Una operación expresa una intención completa, como `CreateAppointment`, `RescheduleAppointment` o `UpdatePatientProfile`. El catálogo v1 aprobado identifica sus acciones y una entrada común de operaciones; no son CRUD libre ni rutas de escritura independientes por tabla.

Incluye identificador único, versión contractual, entidad, acción, versión esperada y datos mínimos. Registra actor, dispositivo o servicio, cuenta y correlación; la API obtiene o verifica esos datos contra la identidad autenticada. La fecha local y la versión de permisos son evidencia de revisión, no prueba suficiente de autorización.

Para cada operación:

1. Autenticar y autorizar la entrada. Consultar el resultado previo solo dentro de un alcance todavía permitido.
2. Detectar duplicados; rechazar un mismo identificador con contenido distinto.
3. Revalidar permisos, estado compartido y versión en coordinación con la escritura; una consulta previa aislada no evita carreras.
4. Aplicar efecto, versión, historial, auditoría, resultado idempotente y Change Log en una transacción PostgreSQL protegida por restricciones.
5. Responder después del commit con resultado y versión. Ante una respuesta perdida, el reintento recupera el resultado sin repetir el efecto.

Los resultados distinguen aceptada, duplicada, conflicto, rechazada y fallo temporal. Los errores no exponen SQL, secretos o trazas. Un identificador o resultado anterior no permite eludir una revocación.

Los lotes tienen límites y resultado por operación. Una operación fallida no cancela otras independientes; las dependencias causales deben ordenarse o declararse. No hay una transacción global obligatoria del lote.

## 4. Descarga y recuperación

Ofrece páginas de cambios autorizados, versiones, eliminaciones lógicas y cursor. El orden debe impedir omitir cambios por confirmar transacciones en distinto orden; no basta ordenar por la fecha del cliente o por una secuencia asignada antes del commit. D09 selecciona contador transaccional por cuenta y grupos completos, con snapshot materializado coherente, cursor firmado y retención mínima de 90 días. La recuperación conserva recibos mínimos para impedir repetir efectos al vencer resultados. Las garantías siguen pendientes de prueba PostgreSQL.

Define arranque desde snapshot, retención, caducidad del cursor y recuperación. Rust aplica datos y cursor juntos en SQLite, conserva intenciones locales y presenta conflictos. Una caída de API deja operaciones locales pendientes; no elimina ni revierte silenciosamente el trabajo guardado.

## 5. Integración con Patient Hub

El Hub tiene su API y su autenticación del paciente. Su backend consulta y envía acciones a Nightingale API por HTTPS autenticado, con actor, cita, cuenta, alcance y versión verificables. API no acepta esos campos solo por recibirlos de un servicio autenticado.

Confirmar, cancelar o aplicar una reprogramación respeta las mismas versiones y restricciones que una operación nativa. API cambia el intervalo e invalida la confirmación anterior en la misma transacción PostgreSQL; no espera un aviso posterior del escritorio al Hub. El Hub concilia después sus accesos y solicitudes con la versión aceptada. El Hub registra sus solicitudes; pedir otro horario no lo reserva. No hay una transacción distribuida con el almacenamiento privado del Hub: deben definirse reintentos y reconciliación de resultados.

## 6. Workers y rendimiento

La aceptación persiste trabajos o eventos dentro de una estrategia duradera; los workers los procesan después del commit. Una caída entre guardado y publicación no puede perder el trabajo. Los mensajes, webhooks y ETL necesitan deduplicación, reintentos y estados consultables.

Un timeout de un proveedor puede dejar el resultado desconocido. El contrato debe resolverlo mediante idempotencia del proveedor o reconciliación antes de repetir el envío; una clave local por sí sola no garantiza un único mensaje externo.

n8n obtiene trabajo y registra resultados mediante API interna autenticada. No escribe en tablas operativas ni decide reservas. Los módulos usan permisos y límites propios; el acceso de workers a citas no permite saltar las reglas transaccionales. La analítica utiliza un PostgreSQL separado del flujo operativo.

Las transacciones son breves, con consultas acotadas e índices adecuados. No incluyen llamadas a proveedores o al Hub. Se miden respuesta de API, duración de transacciones, espera por bloqueos, demora de sincronización y antigüedad de trabajos; los umbrales quedan pendientes. Una API de alto nivel no garantiza por sí sola tiempos bajos.

## 7. Seguridad y límites

- HTTPS y validación de certificados; PostgreSQL operativo en red privada, con identidades separadas para ejecución, workers y migración.
- Permisos mínimos, aislamiento por cuenta y autorización por operación y objeto. Pruebas con cuentas distintas y entradas manipuladas.
- OIDC externo para el personal, con permisos y dispositivos en API, según D06/D09. Keycloak en desarrollo con navegador externo y PKCE S256 identifica al emitir token opaco de dispositivo sin vencimiento y revocable en API. No se añaden sesiones/renovación API ni revocación automática por logout OIDC. D09 sustituye la propuesta previa de sesiones limitadas para esta etapa; formato y control vigentes en api-v1.md.
- Sin credenciales SQL en el escritorio, navegador o Hub; secretos de servicios fuera del código y de los registros.
- No confiar en validaciones Rust, relojes locales ni un `practice_id` declarado. No prometer que una API impida el uso indebido de una sesión válida en un equipo intervenido.
- Aplicar permisos vigentes al aceptar operaciones pendientes. Si falta permiso, rechazar sin efecto y conservar la intención local para revisión; la fecha del cliente no concede autorización anterior. Contrato v1 define coordinación de revocación/aceptación y revisión con nueva intención por persona autorizada; su prueba sigue pendiente, sin ampliar el acceso del Hub.

## 8. Contratos, comprobaciones y pendientes

El repositorio de API posee la fuente OpenAPI y los contratos de eventos/operaciones, con compatibilidad entre versiones y consumidores Rust y Hub. Las migraciones no dependen de que todos los escritorios se actualicen a la vez. El esquema operativo no es un contrato SQL público.

T19–T27 comprueban aislamiento, transiciones inválidas sin Rust, reservas concurrentes, duplicados, revocación vigente, rollback y conservación de historia con PostgreSQL real. El soporte de sync conserva su prueba de respuesta perdida tras commit. La [lista de control](../tasks/P-20261024-01-desktop-shared-api/todo.md) registra comandos, resultados y límites. Descarga sin omisiones, snapshot, SSE entre procesos y consumidores conservan T28–T33. Hub y workers siguen fuera de esta etapa.

Pendientes de producto fuera de esta etapa: autorización del Hub, despliegue/proveedor, cola, política de comunicaciones/espera, objetivos de producción, copias, restauración y RPO/RTO, verificación y corrección global de identidad. D09 concreta identidad, dispositivo, operaciones, cursores, lotes y ventana de recuperación para el escritorio; no demuestra implementación. El objetivo local de avisos no sustituye un SLO de producción. No incluye historia clínica ni lógica de presentación del escritorio o del Hub.

## Referencias

- [Arquitectura de API](architecture.md), [propiedad de contratos y acuerdo con el Hub](contracts.md) y [fuentes del escritorio: plan maestro, arquitectura y especificación del Hub](sources.md#fuentes-del-escritorio).
- [OWASP REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html), [PostgreSQL 18: transacciones](https://www.postgresql.org/docs/18/tutorial-transactions.html), [RFC 8252](https://www.rfc-editor.org/rfc/rfc8252.html) y [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html).

Esta es la fuente de alcance de Nightingale API, trasladada por el usuario a este repositorio el 2026-10-21. La versión 0.2 alinea identidad y revocación con D06 y aclara la invalidación atómica de confirmación; no implementa funciones. La referencia en `nightingale-desktop-docs/specifications/` identifica esta fuente por repositorio y documento, sin depender de una ruta relativa entre proyectos. El usuario trasladará la documentación revisada al repositorio original del escritorio; esta entrega no realiza ese traslado.
