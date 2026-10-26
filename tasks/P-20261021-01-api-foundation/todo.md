# Estado y evidencia

**Estado vigente del plan:** Superseded para ejecución desde el 2026-10-24 por [el plan sucesor](../P-20261024-01-desktop-shared-api/plan.md). Los estados y aceptaciones siguientes quedan como historia; los pendientes no pasan a Done. La ejecución y su evidencia nueva viven solo en [la lista del sucesor](../P-20261024-01-desktop-shared-api/todo.md).

## Registro histórico hasta la sustitución

**Plan:** [P-20261021-01-api-foundation](plan.md). **Estado:** In progress. **Último cierre:** T24 y C14 aceptados por el usuario el 2026-10-24. Se conserva el acuerdo parcial de T04 como siguiente tarea por retomar; no se inicia en esta entrega.

## Tareas

| ID | Estado | Evidencia / condición |
|---|---|---|
| T01 | Done | Comprobaciones documentales realizadas; evidencia histórica en `docs/sources.md` |
| T02 | Done | Alcance acotado a herramientas de proceso ya elegidas por el usuario, versiones/lockfile comprobados; entorno PostgreSQL O08 aplazado hasta antes de T07 |
| T03 | Done | Base y corrección de anotaciones comprobadas; el usuario autorizó continuar. Evidencia en `docs/operations/development.md` |
| T04 | Todo | Acuerdo parcial conservado: OIDC externo y permisos vigentes confirmados; O01/O02 aún parciales. Retomar tras el foco documental de T24 que pidió el usuario |
| T05 | Todo | Depende de T04; contrato, cursor, recuperación y compatibilidad |
| T06 | Todo | Depende de T04; reglas administrativas y estados |
| T07 | Todo | Espera C04; persistencia técnica |
| T08 | Todo | Depende de T07; autorización/aislamiento |
| T09 | Todo | Espera C05; pacientes |
| T10 | Todo | Depende de T09; servicios |
| T11 | Todo | Depende de T10; agenda |
| T12 | Todo | Espera C06; citas/aceptación |
| T13 | Todo | Depende de T12; descarga/recuperación |
| T14 | Todo | Depende de T13; fallos y concurrencia |
| T15 | Todo | Espera C07; adaptación al Hub |
| T16 | Todo | Espera C08; trabajo duradero |
| T17 | Todo | Depende de T16; recordatorios/entregas |
| T18 | Todo | Depende de T17; webhooks/n8n |
| T19 | Todo | Espera C09; acuerdo de lista de espera |
| T20 | Todo | Espera C10; lista de espera |
| T21 | Todo | Depende de T20; indicadores |
| T22 | Todo | Depende de T21; operación/restauración |
| T23 | Todo | Espera C11; integración/aceptación |
| T24 | Done | C14 aceptado al responder «Listo, todo bien». Esquema 0.9 como fuente única; propuestas 2/3 incorporadas, pendiente global aplazado y estructura comprobada. Sin SQL ni cambios de código |

## Revisión del usuario

- [x] C01 — el usuario autorizó comenzar la fundación el 2026-10-21.
- [x] C02 — habilitación para las herramientas de proceso añadidas por el usuario; PostgreSQL de prueba sigue en O08, sin aprobación de esquema.
- [x] C03 — el usuario pidió corregir AsyncIterator en contextos asíncronos y autorizó continuar; corrección y pruebas realizadas.
- [ ] C04 — acuerdos previos de acceso, sync y dominio.
- [ ] C05 — persistencia técnica y aislamiento.
- [ ] C06 — pacientes, servicios y agenda.
- [ ] C07 — citas, sync y pruebas concurrentes.
- [ ] C08 — contrato/adaptador del Hub.
- [ ] C09 — workers e integraciones.
- [ ] C10 — acuerdo de lista de espera.
- [ ] C11 — lista de espera, indicadores y operación.
- [ ] C12 — aceptación de versión y cierre.
- [x] C13 — el usuario aprobó la alineación y los criterios P05/P06 el 2026-10-23; podrá revisarlos al implementar. Conservación de rutas del escritorio por su instrucción. No sustituye C04.
- [x] C14 — el usuario acepta la revisión y las propuestas 2/3 al responder «Listo, todo bien» el 2026-10-24. Incorporadas al esquema 0.9; no cierra T04–T06 ni habilita migraciones.

## Registro de comprobaciones

- 2026-10-21: inspección inicial sin `.git`, código ni manifiestos; el usuario añadió `docs/nightingale-api.md` como fuente de alcance.
- 2026-10-21: lectura de fuentes actuales del escritorio y copia local de Free-Win Orders; véase [procedencia](../../docs/sources.md).
- 2026-10-21: inventario de 11 Markdown sin archivos de producto; 39 enlaces locales y 3 anclas correctos; 23 tareas/12 checkpoints coherentes; §§1–8 de la especificación preservadas. Sin incidencias en esos controles. Diagrama revisado como texto, sin renderizar.
- Al cerrar T01 no se habían ejecutado instalación ni pruebas de producto. Esa nota es histórica; la continuación actual se detalla abajo.

### Continuación T02/T03 · 2026-10-21

- El usuario creó Git, instaló dependencias y añadió código base; autorizó iniciar la fundación. Se conservó su selección de versiones.
- Se añadió el extra asyncio de SQLAlchemy: faltaba greenlet y el import asíncrono fallaba. `uv` actualizó manifiesto/lockfile e instaló greenlet 3.5.6 sin actualizar las otras dependencias.
- `uv sync --locked --offline`: correcto; construcción de wheel/sdist correcta. Se inspeccionaron ambos artefactos: contienen `src.application`, no contienen `.env`, `.venv`, caché ni temporales. El comando instalado apunta a `src.application:main`.
- 10 pruebas unittest correctas. La ejecución aislada se bloqueó en el socket interno de asyncio de Windows; las mismas pruebas pasaron fuera del aislamiento, sin cambiar el producto para eludir ese fallo.
- HTTP local real: `/health/live` respondió 200 y `/health/ready` 503 con base no configurada. El proceso temporal se detuvo.
- Sin tablas, migraciones, credenciales reales, workers, CI, integración de consumidores ni despliegue. No se ha comprobado PostgreSQL real. C03 no se marca aceptado por estas pruebas.

### Corrección de T03 e inicio de T04 · 2026-10-21

- `lifespan` y `session`, ambas con `@asynccontextmanager`, usan `AsyncGenerator` en vez de `AsyncIterator`. Se conserva AsyncIterator en la dependencia sin decorador. No se cambió el comportamiento.
- Las 10 pruebas existentes pasaron. Comprobación AST: los dos contextos decorados usan AsyncGenerator. No hay CLI de basedpyright en este entorno; no se afirma una ejecución de ese analizador.
- El usuario autorizó continuar y eligió proveedor externo OIDC, con permisos y dispositivos en API. Confirmó permisos vigentes al aceptar y conservación de intenciones rechazadas para revisión.
- Propuesta de seguridad creada en `docs/access-design.md`; concesiones del Hub, proveedor, sesiones y vínculo de dispositivo aún requieren cierre. T04 no se marca Done ni se implementa acceso.

### Alineación documental dentro de T04 · 2026-10-23

El usuario autorizó resolver las diferencias con la documentación del escritorio añadida aquí. Se ejecutaron en secuencia los cuatro pasos de la ampliación de T04; C13 conserva la revisión entre la alineación y la adopción de acuerdos funcionales.

- Alineados los textos vigentes de API y de las copias de escritorio con D06. Se distinguen OIDC/permisos vigentes confirmados de proveedor, sesiones, vínculo de dispositivos, orden concurrente y revisión aún pendientes.
- Reprogramación: el cambio de horario y la invalidación de confirmación comparten transacción de API; Hub concilia después accesos/solicitudes. Recordatorios: se distingue trabajo duplicado de envío con resultado desconocido y se exige conciliación/deduplicación del proveedor o revisión antes de reenviar.
- La especificación API es ahora 0.2; su copia se sustituye por una referencia. El índice de `docs/nightingale-desktop-docs/` declara origen, versiones y ajustes locales. Se corrigieron los dos enlaces a planes del escritorio no incluidos, sin copiar esos planes ni editar otro repositorio.
- P05/P06 están redactadas en `docs/decisions.md` con recorridos, fallos y decisiones que faltan. Permanecen como propuestas; no se eliminó `reschedule_requested` del diagrama de origen ni se habilitaron nuevas acciones del Hub. O04/O05 siguen abiertos.

Comprobaciones ejecutadas con Python de `.venv`, biblioteca estándar y comandos Git:

- Lectura de los cambios frente a una copia tomada antes de editar, incluida la documentación aún no seguida por Git. Revisión de recorridos: caída después de reprogramar conserva confirmación invalidada; resultado desconocido externo no autoriza reenvío; solicitudes/ofertas no se presentan como acuerdos aprobados. Es revisión de texto, sin ejecución del producto ni render de Mermaid.
- Validador puntual de Markdown: 23 archivos, 116 enlaces locales y 16 anclas; ningún destino o ancla ausente y bloques de código cerrados. No se comprobó disponibilidad de enlaces web.
- SHA-256 de 48 archivos de código, pruebas, manifiesto, lockfile y `AGENTS.md`: sin cambios respecto al inicio. ADR histórico de SQL directo y especificación inicial del Hub sin cambios. El contenido previo de `docs/sources.md` se conserva íntegro como prefijo, incluida la supresión previa del usuario.
- `git diff --check`: correcto. Para las copias todavía no seguidas por Git, revisión por comparación con la copia inicial; el control de Git por sí solo no las cubre.

Sin tablas, migraciones, pruebas de producto, consumidores reales ni despliegue. T04 sigue en curso; C13 no está aceptado y P05/P06 no cierran O04/O05. Antes de adoptarlas, el usuario revisa este resultado conforme a `AGENTS.md` y al acuerdo de dos pasos.

### Aceptación de C13 y conservación de rutas · 2026-10-23

El usuario aprobó la alineación y los criterios P05/P06, reservándose cambiarlos al implementar. También indicó que trasladará los documentos del escritorio a su repositorio original y pidió no cambiar rutas. Esta instrucción sustituye la adaptación previa de los enlaces del escritorio al árbol de API; no autoriza mover archivos ni editar el otro repositorio desde aquí.

- C13 se registra aceptado por instrucción expresa del usuario. P05/P06 pasan a criterios confirmados y revisables; O04/O05 conservan sus detalles pendientes y T04 sigue en curso. No se cambia el estado de T05/T06/T19 ni se acepta C04.
- SRS, plan maestro y arquitectura técnica aplican los dos criterios: solicitud separada del estado de cita e interés por oferta separado de asignación por personal. El diagrama de Citas deja de usar `reschedule_requested`; el ciclo propio de solicitud sigue pendiente. Se conserva la opción de revisión por el usuario antes o durante la implementación.
- Se restauran los destinos originales de los enlaces y se eliminan los añadidos que dependían de archivos exclusivos de API. La referencia de especificación identifica repositorio, documento y versión sin suponer una ruta entre repositorios. No se mueve ni renombra ningún archivo.

Comprobaciones después del ajuste:

- Los nueve archivos Markdown originales del escritorio conservan exactamente el mismo conjunto de destinos de enlace que la copia aportada por el usuario antes de la alineación. Sin destinos nuevos ni sustituidos; ADR de la base restaurado al texto original. ADR histórico de SQL directo y especificación del Hub sin cambios.
- 23 Markdown revisados; 95 enlaces locales y 5 anclas resueltas. Solo faltan los dos planes originales del escritorio, conservados por instrucción del usuario; no se comprueban ni se crean sus archivos aquí. Ningún enlace del escritorio depende de documentos propios de API situados fuera de su árbol.
- 48 archivos protegidos de código, pruebas, manifiesto, lockfile y `AGENTS.md` sin cambios según SHA-256. Contenido previo del usuario en `docs/sources.md` conservado. Comparación con la copia anterior para los documentos todavía no seguidos por Git; bloques Markdown cerrados y `git diff --check` correcto.
- Plan/lista coherentes: 23 tareas y 13 checkpoints; solo C01, C02, C03 y C13 figuran aceptados. El traslado al repositorio original lo hará el usuario; no se presenta como ejecutado.

Sin pruebas de producto, migraciones, instalación, implementación ni despliegue. La revisión de Mermaid sigue limitada al texto; no se afirma un render del diagrama.

### T24 · Primer diseño lógico de datos · 2026-10-23

El usuario confirmó el traslado de los documentos del escritorio y pidió priorizar el diseño de la base de datos. Se conserva el plan y sus IDs: T24 es la única tarea activa; T04 vuelve a Todo para retomarlo con su acuerdo parcial intacto. C14 queda pendiente de revisión, sin habilitar T07 ni cerrar T04–T06.

Entradas comprobadas por lectura: documentación actual de API, modelo de usuarios y soporte de persistencia; Plan Maestro 0.3, arquitectura técnica 0.3 y SRS 0.5 en `C:/Users/Pedro/Documents/GitHub/nightingale/docs/`, con revisión del 2026-10-23. Se comprobó que el Plan Maestro está en la ubicación original. No se modificó ese repositorio ni se cambiaron rutas.

D07 registra las respuestas expresas del usuario: solo tiempo del profesional como recurso de reserva; duración por servicio ajustable al crear; nombre, teléfono y documento obligatorios; una cuenta por profesional.

Salida: `docs/data-model.md` 0.1 Draft con relaciones del núcleo, campos propuestos, propietarios, reglas y casos ficticios. Propone vincular la cuenta a un usuario profesional sin una tabla anticipada de perfiles; ese vínculo concreto sigue para revisión. Distingue persistencia operativa de SQLite, Hub y analítica, y reserva el diseño físico de seguridad/sync para sus acuerdos. No presenta el modelo actual de usuarios con contraseña/rol global como diseño final.

Comprobaciones ejecutadas con Python de `.venv`, biblioteca estándar y Git:

- Seis enlaces locales del nuevo documento y una ancla resueltos; bloque Mermaid cerrado y sin espacios sobrantes. La revisión del diagrama es textual, sin renderizador. No se adaptan enlaces anteriores a las copias retiradas por el usuario.
- Plan y lista coinciden: 24 tareas, 14 checkpoints; solo T24 en curso; C14 sin aceptar. C01/C02/C03/C13 conservan la aceptación previa, sin nuevos checkpoints aceptados por las comprobaciones.
- 48 archivos de código, pruebas, manifiesto, lockfile y `AGENTS.md` conservan sus SHA-256 respecto al inicio del diseño. `git diff --check` correcto; control de espacios separado sobre el nuevo documento aún no seguido por Git.
- Revisión manual del caso ficticio: servicio de 30 minutos con cita de 45 y cambio posterior a 20 conserva el intervalo de 45. Una solicitud del Hub no cambia la cita y una oferta no reserva sin personal. Son comprobaciones del texto, no pruebas de ejecución.

Pendientes antes del esquema físico: vínculo del profesional y permisos, formato/tipo y duplicados de documento, reglas de teléfono, límites y precisión de duración, historia del servicio y carreras entre cita/agenda/permisos; además de las decisiones técnicas de T05. No se ejecutó SQL ni se crearon tablas, migraciones, modelos, pruebas de producto o despliegues.

### T24 · Fuente única y preparación del esquema · 2026-10-24

El usuario fija `docs/database-schema.md` como única fuente del modelo y retira el borrador lógico anterior. D08 y las referencias vigentes de arquitectura, contratos, fuentes y plan reflejan esa instrucción. D07 conserva las respuestas iniciales como antecedente sustituido donde contradice el esquema; los registros del 2026-10-23 son históricos.

El esquema pasa de 0.7 a 0.8 por la revisión documental de §8.9: corrección de identidad global abierta y aplazada sin detener partes independientes; propuestas de conservar constancias de representación y usar minutos desde medianoche; correcciones administrativas en historia; mismo instante para médico y paciente en telemedicina. Las propuestas 2 y 3 no cuentan como aprobadas y no se cambian las columnas ni los diagramas. T24 y C14 conservan su estado para revisión; los checkpoints internos de la entrega del esquema no aceptan los de este plan.

Comprobaciones documentales con PowerShell y Git, frente a copia tomada antes de editar en `.tmp/schema-readiness-20261024/`:

- 17 tablas, 174 columnas y 30 FK conservadas. Todos los renglones de las tablas del documento y los cuatro bloques Mermaid son idénticos a la versión aportada; sin nuevo render ni ejecución SQL.
- 48 archivos de código, pruebas, manifiesto, lockfile e instrucciones conservan sus SHA-256. Se conservan las rutas existentes del esquema y no se modifica otro repositorio.
- Seis referencias locales nuevas resuelven su archivo; bloques Markdown cerrados. Las cuatro rutas del esquema ausentes en este repositorio se conservan por la instrucción previa del usuario; no se presentan como enlaces comprobados aquí.
- Plan y lista mantienen 24 tareas y 14 checkpoints; solo T24 en curso y C14 sin aceptar. `git diff --check` correcto; el esquema y el borrador retirado, aún no seguidos por Git, se compararon con sus copias iniciales.
- Se contrastó el intervalo de `time` de PostgreSQL 18 y el límite de `datetime.time` de Python 3.15 en sus páginas oficiales, enlazadas en §8.9. Python de `.venv` no pudo abrir su ejecutable base por acceso denegado; los controles se completaron con PowerShell, sin cambiar herramientas ni producto.

Sin SQL, migraciones, modelos, pruebas de producto ni despliegue. Los pendientes de acceso y sincronización conservan sus tareas; esta revisión no los cierra ni autoriza implementación por sí sola.

### Aceptación de C14 y cierre de T24 · 2026-10-24

El usuario responde «Listo, todo bien» a la revisión y las propuestas 2 y 3. Se registra C14 aceptado por esa respuesta, no por las comprobaciones. El esquema pasa a 0.9 e incorpora conservación inmutable de fecha/autor de verificación y extremos de horarios en minutos desde medianoche. La corrección de identidad global sigue abierta y aplazada.

Comprobaciones con Node.js 24.18.0, biblioteca estándar y Git, frente a la copia previa de `.tmp/schema-acceptance-20261024/`:

- 17 tablas, 174 columnas y 30 FK. Solo cambian los nombres y tipos de cuatro columnas de Agenda, según lo aprobado. Se ajustan sus límites, la UQ de reglas y el diagrama de detalle; los 174 atributos de los diagramas coinciden con el diccionario.
- Los destinos de todos los enlaces del esquema se mantienen. 48 archivos protegidos de código, pruebas, manifiesto, lockfile e instrucciones conservan sus SHA-256. No se modificó otro repositorio.
- Plan y lista conservan 24 tareas y 14 checkpoints; T24 queda Done, C14 aceptado y T04 Todo. No se inicia otra tarea ni se cierra C04.
- `git diff --check` y comparación de espacios del esquema con la copia previa, sin incidencias. Mermaid se revisó como texto; no se ejecutó otro render ni SQL, migraciones o pruebas de producto.

T24 cierra el alcance documental aceptado. La siguiente tarea del plan por retomar es T04, con sus acuerdos parciales conservados.
