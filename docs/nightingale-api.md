# Especificación técnica breve: Nightingale API

**Versión:** 0.1
**Fecha:** 2026-10-21
**Estado:** Arquitectura acordada; proyecto separado aún no implementado aquí.
**Decisión:** [Tres proyectos y API transaccional](decisions.md#d01--tres-proyectos-y-api-transaccional).

## 1. Propósito y tecnología

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

Una operación expresa una intención completa, por ejemplo `CreateAppointment`, `RescheduleAppointment` o `UpdatePatientContact`. Sus nombres son ejemplos, no rutas HTTP finales.

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

Ofrece páginas de cambios autorizados, versiones, eliminaciones lógicas y cursor. El orden debe impedir omitir cambios por confirmar transacciones en distinto orden; no basta ordenar por la fecha del cliente o por una secuencia asignada antes del commit. El mecanismo exacto se define antes de programar sincronización.

Define arranque desde snapshot, retención, caducidad del cursor y recuperación. Rust aplica datos y cursor juntos en SQLite, conserva intenciones locales y presenta conflictos. Una caída de API deja operaciones locales pendientes; no elimina ni revierte silenciosamente el trabajo guardado.

## 5. Integración con Patient Hub

El Hub tiene su API y su autenticación del paciente. Su backend consulta y envía acciones a Nightingale API por HTTPS autenticado, con actor, cita, cuenta, alcance y versión verificables. API no acepta esos campos solo por recibirlos de un servicio autenticado.

Confirmar, cancelar o aplicar una reprogramación respeta las mismas versiones y restricciones que una operación nativa. El contrato coordina la invalidación de confirmaciones antiguas. El Hub registra sus solicitudes; pedir otro horario no lo reserva. No hay una transacción distribuida con el almacenamiento privado del Hub: deben definirse reintentos y reconciliación de resultados.

## 6. Workers y rendimiento

La aceptación persiste trabajos o eventos dentro de una estrategia duradera; los workers los procesan después del commit. Una caída entre guardado y publicación no puede perder el trabajo. Los mensajes, webhooks y ETL necesitan deduplicación, reintentos y estados consultables.

Un timeout de un proveedor puede dejar el resultado desconocido. El contrato debe resolverlo mediante idempotencia del proveedor o reconciliación antes de repetir el envío; una clave local por sí sola no garantiza un único mensaje externo.

n8n obtiene trabajo y registra resultados mediante API interna autenticada. No escribe en tablas operativas ni decide reservas. Los módulos usan permisos y límites propios; el acceso de workers a citas no permite saltar las reglas transaccionales. La analítica utiliza un PostgreSQL separado del flujo operativo.

Las transacciones son breves, con consultas acotadas e índices adecuados. No incluyen llamadas a proveedores o al Hub. Se miden respuesta de API, duración de transacciones, espera por bloqueos, demora de sincronización y antigüedad de trabajos; los umbrales quedan pendientes. Una API de alto nivel no garantiza por sí sola tiempos bajos.

## 7. Seguridad y límites

- HTTPS y validación de certificados; PostgreSQL operativo en red privada, con identidades separadas para ejecución, workers y migración.
- Permisos mínimos, aislamiento por cuenta y autorización por operación y objeto. Pruebas con cuentas distintas y entradas manipuladas.
- Sesiones remotas limitadas y revocables; proveedor y duraciones por definir. Si se usa OAuth para el escritorio, navegador externo y PKCE conforme a RFC 8252, con protección de renovación según RFC 9700.
- Sin credenciales SQL en el escritorio, navegador o Hub; secretos de servicios fuera del código y de los registros.
- No confiar en validaciones Rust, relojes locales ni un `practice_id` declarado. No prometer que una API impida el uso indebido de una sesión válida en un equipo intervenido.
- Conservar operaciones dudosas ante revocación para rechazo o revisión. Definir la política temporal antes de implementar identidad/sincronización.

## 8. Contratos, comprobaciones y pendientes

El repositorio de API posee la fuente OpenAPI y los contratos de eventos/operaciones, con compatibilidad entre versiones y consumidores Rust y Hub. Las migraciones no dependen de que todos los escritorios se actualicen a la vez. El esquema operativo no es un contrato SQL público.

Comprobaciones futuras mínimas: aislamiento entre cuentas, transición inválida enviada sin Rust, dos reservas concurrentes, duplicado y contenido distinto, respuesta perdida tras commit, revocación con pendientes, cancelación del Hub frente a versión antigua, paginación sin omisiones y caída de workers sin perder trabajos. No se han ejecutado: aún no existe este servicio en el repositorio.

Pendientes: identidad concreta, contratos HTTP finales, cursores y retención, política de revocación, despliegue/proveedor, cola, límites de lotes, objetivos de rendimiento, copias, restauración y RPO/RTO. No incluye historia clínica ni lógica de presentación del escritorio o del Hub.

## Referencias

- [Arquitectura de API](architecture.md), [propiedad de contratos y acuerdo con el Hub](contracts.md) y [fuentes del escritorio: plan maestro, arquitectura y especificación del Hub](sources.md#fuentes-del-escritorio).
- [OWASP REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html), [PostgreSQL 18: transacciones](https://www.postgresql.org/docs/18/tutorial-transactions.html), [RFC 8252](https://www.rfc-editor.org/rfc/rfc8252.html) y [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html).

Esta es la fuente de alcance de Nightingale API, copiada por el usuario a este repositorio el 2026-10-21. La copia anterior del escritorio queda como referencia de procedencia; su propietario deberá sustituirla por un enlace, sin mantener dos especificaciones editables independientes. Ese cambio externo queda fuera de esta entrega.
