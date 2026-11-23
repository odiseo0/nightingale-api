# Especificación técnica breve: Nightingale API

**Versión:** 0.8 (etapa 1 clínica implementada y comprobada para revisión C06).
**Fecha:** 2026-11-15
**Estado:** C01–C06, C09/C10 y C12–C18 aceptados. T31–T33 para revisión expresa C11: SSE y recuperación entre dos procesos, diez streams y contratos generados con ejemplos comprobados. C07/C08 conservan autorización de paso sin aceptaciones separadas. Consumidores Rust/Hub y producción siguen fuera; C11 no está aceptado.
**Decisiones:** [Tres proyectos y API transaccional](decisions.md#d01--tres-proyectos-y-api-transaccional), con el reparto del Hub sustituido por [D11](decisions.md#d11--interfaz-del-hub-y-servidor-en-nightingale-api).

## 1. Propósito y tecnología

La primera etapa aprobada está en [P-20261024-01-desktop-shared-api](../tasks/P-20261024-01-desktop-shared-api/plan.md). [api-v1.md](api-v1.md) fija su diseño de rutas/operaciones/modelos públicos; [database-schema.md](database-schema.md) conserva la única fuente física, ampliada en 1.0 para revisar en C01. Los apartados generales de Hub, comunicaciones y analítica describen el producto posterior, no trabajo autorizado de esta entrega.

La ampliación clínica acordada el 2026-11-15 se desarrolla en [Registro clínico y seguimiento del paciente](patient-clinical-record.md), referencia funcional para los planes de tres etapas bajo [D12](decisions.md#d12--registro-clínico-y-seguimiento-del-paciente). Comprende datos de referencia, registro habitual y funciones completas, incluida analítica individual con referencias OMS. El usuario aprobó [P-20261115-02-patient-clinical-data](../tasks/P-20261115-02-patient-clinical-data/plan.md) y autorizó T01–T03 hasta C01: acuerdos, diseño físico/contratos y línea base, sin código, migraciones o generados. T04–T06 añadieron permisos por asistente/sección y filtrado cerrado. T07–T09 añaden perfil clínico, sexo al nacer, historial y cambios de nacimiento para revisión C03. T10–T12 añaden condiciones y revisión de su sección para revisión C04. T13–T15 añadieron alergias/intolerancias. T16–T18 completan captura/delta clínica, contratos y verificación de etapa 1 para revisión C06. La etapa 2 no se inicia.

La corrección aprobada conserva arquitectura hexagonal por componentes con api/authorization como estilo: infrastructure solo endpoints; application casos de uso sin acceso directo a SQLAlchemy; repository modelos y DAOs derivados; domain esquemas de la base del proyecto, valores y errores. JSON camelCase, listas y snapshot con page/shows, LIMIT/OFFSET e items/total. No hay cursores de página; sí posición de avance incremental de sync. authorization y accounts tienen propietarios separados. Los workflows de alta son scripts pequeños, sin sistema CLI. App de módulo, fábrica existente, inyección de dependencias y Uvicorn directo; sin lifespan para base de datos.

Nightingale API es el límite remoto de seguridad y aceptación del estado compartido. Usa Python y FastAPI en su propio repositorio. El escritorio ejecuta sus casos de uso con Rust/SQLite; la API no es necesaria para consultar o guardar datos locales permitidos.

La API recibe operaciones de alto nivel y entrega cambios incrementales. No ofrece SQL, acceso libre a tablas ni un guardado ciego de objetos enviados por el cliente.

## 2. Responsabilidades y datos

- Autenticar personas, dispositivos y servicios; comprobar cuenta, pertenencia, alcance y revocaciones según la política de acceso.
- Aceptar operaciones sobre pacientes, servicios, agenda y citas, con versiones, transiciones e integridad compartida.
- Conservar en PostgreSQL operativo entidades aceptadas, historial, auditoría, operaciones y resultados idempotentes, Change Log y trabajos persistentes.
- Proveer en el futuro todas las funciones de servidor del Patient Hub: lectura pública del micrositio y gestión limitada de citas existentes. API poseerá sus contratos, accesos y solicitudes y aplicará las reglas comunes; el repositorio del Hub contendrá la interfaz web.
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

Ofrece páginas de cambios autorizados, versiones, retiradas de vista y cursor. El contador transaccional por cuenta y los grupos completos impiden omitir cambios por confirmar transacciones en distinto orden; no usa la fecha del cliente ni una secuencia precommit. T28–T30 prueban snapshot coherente, cursor firmado, retención mínima de 90 días y recibos mínimos que impiden repetir efectos al vencer resultados. La evidencia procede de PostgreSQL aislado; no acredita consumidores.

Define arranque desde snapshot, retención, caducidad del cursor y recuperación. Rust aplica datos y cursor juntos en SQLite, conserva intenciones locales y presenta conflictos. Una caída de API deja operaciones locales pendientes; no elimina ni revierte silenciosamente el trabajo guardado.

## 5. Integración con Patient Hub

**Alcance futuro acordado por D11, sin implementar.** Nightingale conserva el escritorio. Patient Hub tendrá repositorio propio para la interfaz web; Nightingale API tendrá todas las funciones de servidor que requiera. Este reparto sustituye la API, el backend y el almacén privado antes asignados al Hub. El Hub no accede directamente a PostgreSQL.

### Micrositio de lectura pública

La primera versión del Hub incluirá ambas presentaciones mediante plantillas definidas:

- Médico independiente: presentación del profesional, servicios, ubicación y datos de contacto.
- Clínica o centro médico: presentación del centro, catálogo de servicios, profesionales y ubicación.

No habrá editor libre de páginas ni gestión de pacientes dentro del Hub. La presentación pública de clínicas no autoriza toda su gestión interna, varias sedes ni cambios generales en el escritorio.

API ofrecerá endpoints públicos que entreguen solo información destinada a publicación. Leer el micrositio no exigirá cuenta de paciente, inicio de sesión ni permisos del personal. Las rutas internas actuales no pasan a ser públicas. No se publicarán fichas de pacientes, listados de citas, notas internas ni otros datos privados. Los datos actuales de cuentas, profesionales y servicios pueden servir de base, pero no prueban que exista una proyección pública.

### Gestión limitada de una cita existente

El paciente podrá consultar la información permitida de su cita, confirmar asistencia, cancelar conforme a las reglas, solicitar reprogramación y consultar el resultado de la acción. API verificará un acceso limitado a esa cita, acción e información necesaria, sin exigir credenciales del personal. No se confunde este acceso privado con la lectura pública del micrositio ni se diseña un sistema de cuentas de paciente para resolverla.

El paciente no creará ni reservará citas, no explorará disponibilidad para elegir o reservar otro horario y no marcará ausencias. El personal conserva el registro de ausencias según las reglas actuales. Solicitar reprogramación no altera estado, horario ni confirmación y no reserva otro intervalo. El personal decide el cambio; API aplica la reprogramación con las reglas comunes. El cambio de intervalo invalida la confirmación anterior en la misma transacción.

### Contrato actual y pendientes

[api-v1.md](api-v1.md) describe las funciones actuales para escritorio y personal autorizado; no incluye endpoints de micrositio ni acciones del paciente. Sus rutas y resultados no conceden acceso al paciente. Quedan pendientes el mecanismo exacto del enlace/acceso, su vigencia y revocación, las proyecciones permitidas, las formas HTTP y el ciclo de solicitudes y resultados. La autorización entre dos backends ya no es un requisito. No se fijan rutas, campos ni tablas para completar este acuerdo.

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

T19–T27 comprueban aislamiento, transiciones inválidas sin Rust, reservas concurrentes, duplicados, revocación vigente, rollback e historia. T28–T30 añaden descarga, snapshot y recuperación con PostgreSQL real. T31/T32 prueban SSE, reservas, duplicados, revocación con stream abierto y recuperación con dos procesos reales; p95 local 120.1 ms y cota superior que incluye commit 122.5 ms, con diez streams y 20 commits. T33 genera [contratos](../contracts/README.md) y comprueba los ejemplos de la [guía Rust](rust-api-guide.md). El soporte de sync conserva su prueba de respuesta perdida tras commit. La [lista de control](../tasks/P-20261024-01-desktop-shared-api/todo.md) registra comandos, resultados y límites. Estas pruebas no acreditan consumidores, saturación ni producción. Hub y workers siguen fuera.

Pendientes de producto fuera de esta etapa: diseño de acceso y contratos del Hub bajo D11, despliegue/proveedor, cola, política de comunicaciones/espera, objetivos de producción, copias, restauración y RPO/RTO, verificación y corrección global de identidad. D09 concreta identidad, dispositivo, operaciones, cursores, lotes y ventana de recuperación para el escritorio; no demuestra implementación. El objetivo local de avisos no sustituye un SLO de producción. No incluye historia clínica ni lógica de presentación del escritorio o del Hub.

## Referencias

- [Arquitectura de API](architecture.md), [propiedad de contratos y acuerdo con el Hub](contracts.md) y [fuentes del escritorio: plan maestro, arquitectura y especificación del Hub](sources.md#fuentes-del-escritorio).
- [OWASP REST Security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html), [PostgreSQL 18: transacciones](https://www.postgresql.org/docs/18/tutorial-transactions.html), [RFC 8252](https://www.rfc-editor.org/rfc/rfc8252.html) y [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html).

Esta es la fuente de alcance de Nightingale API, trasladada por el usuario a este repositorio el 2026-10-21. La versión 0.2 alinea identidad y revocación con D06 y aclara la invalidación atómica de confirmación; no implementa funciones. La referencia en `nightingale-desktop-docs/specifications/` identifica esta fuente por repositorio y documento, sin depender de una ruta relativa entre proyectos. El usuario trasladará la documentación revisada al repositorio original del escritorio; esta entrega no realiza ese traslado.

La revisión 0.5 del 2026-11-14 aplica D11 solo a documentación de API. La reunión futura en `patient-hub-docs/` con `Master-Plan.md` corresponde a otra sesión en el repositorio del escritorio.

La revisión 0.6 del 2026-11-15 enlaza la especificación clínica y D12. La exclusión de historia clínica de la entrega del núcleo se conserva; el producto futuro tiene el alcance ampliado y los pendientes que detalla esa fuente. No modifica HTTP, esquema físico ni evidencia de implementación.

La revisión 0.7 registra la aprobación del plan de etapa 1 clínica y la autorización limitada a T01–T03. No acepta C01, no habilita T04 y no acredita funciones clínicas implementadas.
