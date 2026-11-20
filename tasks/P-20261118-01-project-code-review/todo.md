# Tareas · P-20261118-01

**Plan:** [plan.md](plan.md). **Estado del plan:** In progress. **Actualizado:** 2026-11-20.

Los bloques se ejecutan en el orden en que aparecen. Cada bloque posterior depende del checkpoint anterior. Dentro del bloque, cada tarea depende de la anterior. C13 a C16 se incorporan después de C02 para resolver los críticos antes de retomar C03. C17 a C19 incorporan la tercera revisión después de C06. C20 a C22 incorporan la cuarta revisión después de C09. La quinta añade C23 después de C19 y C24 a C27 después de C22. T01 registra la revisión inicial. C01 sigue pendiente.

Comandos comunes desde la raíz del proyecto.

- Suite `./.venv/Scripts/python.exe -m unittest discover -s tests -v`.
- Probes `./.venv/Scripts/python.exe test-support/<nombre>/check.py`. Ver [servicios de prueba](../../test-support/README.md) para iniciar PostgreSQL Test y Keycloak de prueba cuando corresponda.
- Contratos `./.venv/Scripts/python.exe -m scripts.export_contracts --check`.
- Build `uv build --offline`.

## Etapa 1 · Revisión y corrección por gravedad

### C01 · Revisión por gravedad

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T01 · Inventario y rastreo inicial | Done · API | Inventariar fuentes y rastrear los puntos de entrada y cláusulas de persistencia de los hallazgos listados. | Publicar hallazgos con impacto, evidencia y caso de verificación. | AST, build y exportación temporal. Ver [review.md](review.md). |
| T02 · Completar revisión de acceso y sync | Done · authorization, accounts, sync, audit | Completar la lectura por archivo de credenciales, permisos de objeto, recibos, carreras, diario, captura, retención y SSE. Ver el rastreo ya registrado. | Registrar cobertura por archivo y sustentar cada crítico con alcance y efecto. | Suite y probes `access`, `sync`, `downloads`, `retention`, `events`. |
| T03 · Completar revisión de flujos y datos | Done · agenda, citas, pacientes y componentes clínicos | Completar la lectura por archivo desde HTTP hasta SQL y soporte de operación. CR-01 a CR-05 ya tienen evidencia en el informe. | Cerrar cobertura manual y vincular cada crítico confirmado con tareas. | Suite y probes `persistence`, `appointments`, `patients`, `clinical_history`, `diagnostic_results`, `specialty_templates`, `clinical_analytics`. |

- [x] Matriz de cobertura y hallazgos con prueba propuesta. Relación con C12 clínico decidida: repetir sus comprobaciones afectadas antes de aceptarlo.
- [x] Revisión del usuario. **C01 aceptado el 2026-11-18.**

### C02 · Integridad y alcance de adjuntos

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T04 · Validar la ficha en lecturas de adjuntos | Done · diagnostic_results | Pasar cuenta y ficha al caso de uso y comprobar el vínculo antes de auditar y cargar. CR-01. | Las lecturas devuelven el adjunto solo para la ficha autorizada. | Probe `diagnostic_results` y `clinical_permissions`. |
| T05 · Validar el vínculo al guardar el informe | Done · diagnostic_results | Compartir la comprobación de ficha y estado entre alta y cambios. CR-01. | Un vínculo inválido rechaza la operación sin efecto ni cambio de versión. | Probe `diagnostic_results`; alta, edición y retiro. |
| T06 · Proteger el vínculo en PostgreSQL | Done · diagnostic_results | Comprobar datos previos y añadir FK compuesta con migración nueva. CR-01. | PostgreSQL conserva cuenta y ficha al insertar y actualizar, con prueba desde una revisión previa. | Probe `persistence` y prueba SQL con dos fichas. |

- [x] Pruebas focales y matriz común registradas. Integridad y escrituras comprobadas con PostgreSQL aislado.
- [x] Revisión del usuario. **C02 aceptado el 2026-11-18.**

### C13 · Corrección clínica de informes

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T33 · Resolver el contrato de corrección | Done · diagnostic_results, contratos | Acordar cómo expresa el cliente el nuevo conjunto y qué respuesta recibe un cliente que solo envía el motivo. Precisar cómo identificar resultados para el reintento. CR-02. | Contrato aprobado con regla de vigencia, de transición y de compatibilidad. | Comparar límites de `CorrectDiagnosticReport` y esquema exportado con E18. |
| T34 · Sustituir el conjunto vigente de resultados | Done · diagnostic_results | Versionar el informe, anular resultados anteriores y guardar los corregidos con sus historias bajo la aceptación existente. CR-02, depende de T33. | La lectura devuelve solo el nuevo conjunto. Historia, auditoría, recibo y grupo se confirman juntos. | Probe `diagnostic_results`, con nuevo conjunto, rollback forzado y reintento. |
| T35 · Verificar informes corregidos anteriormente | Done · diagnostic_results | Identificar versiones anteriores afectadas y la evidencia disponible. Registrar reparación verificable o estado pendiente de revisión clínica. CR-02. | El plan de datos preserva historia y evita inferir resultados que nunca se guardaron. | Fixture con corrección previa incompleta y con resultados recuperables. |

- [x] E18 distingue informe corregido y corrección de un resultado. Lectura, captura, delta y compatibilidad comprobadas.
- [x] Revisión del usuario. **C13 aceptado el 2026-11-18.**

### C14 · Transiciones de especialidad

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T36 · Anular el registro con una versión nueva | Done · specialties | Crear una versión de anulación con historia y valores preservados. CR-03. | Tras el commit se retira de la lista vigente, se emite la anulación en sync y la historia conserva ambas versiones. | Probe `specialty_templates`, con versión anterior, reintento y rollback. |
| T37 · Retirar la plantilla con una versión nueva | Done · specialties | Avanzar versión al retirar y conservar las definiciones que usan los registros ya capturados. CR-03. | El retiro impide nuevas capturas y los registros previos aún se leen con su versión de plantilla. | Probe `specialty_templates`, con plantilla activa y retiro. |

- [x] Las transiciones confirman con el rol de ejecución en PostgreSQL Test y conservan las proyecciones de historia y sync.
- [x] Revisión del usuario. **C14 aceptado el 2026-11-18.**

### C15 · Conservación y tipos en especialidad

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T38 · Conservar los valores omitidos en un patch | Done · specialties | Construir el estado resultante desde la versión actual y los campos enviados. Proyectar los valores de cada versión histórica. CR-04. | Cambiar solo fecha o motivo conserva valores opcionales y obligatorios. La historia muestra los valores de cada versión. | Probe `specialty_templates`, con fecha, motivo, campo ausente y null según contrato. |
| T39 · Validar cada valor según la plantilla aplicada | Done · specialties | Leer una vez la versión asociada y validar claves, campos obligatorios y `field_kind` en alta y edición. CR-05 y RF-10. | Rechaza tipos que no corresponden sin nueva versión ni cambio en sync. Versiones anteriores con tipos correctos se leen igual. | Probe `specialty_templates` para los cuatro tipos, edición e historial. |
| T40 · Revisar datos anteriores de especialidad | Done · specialties | Inventariar estados vaciados y valores incompatibles. Distinguir correcciones verificables de casos que necesitan decisión clínica. CR-04 y CR-05. | La historia original queda disponible y toda reparación conserva autor, motivo y versión. | Fixture con valores históricos recuperables y sin evidencia suficiente. |

- [x] HTTP, historia, captura y delta preservan el significado de la plantilla y de cada versión del registro.
- [x] Revisión del usuario. **C15 aceptado el 2026-11-18.**

### C16 · Cierre de críticos

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T41 · Verificar el cierre conjunto | Done · diagnostic_results, specialties, sync | Volver a comprobar CR-01 a CR-05 con datos ficticios y registrar el efecto sobre consumidores. | Pruebas focales, suite, build y contratos quedan comprobados. Los datos previos tienen evidencia o estado pendiente explícito. | Probes `diagnostic_results`, `specialty_templates`, `persistence`, `sync`, `downloads`; matriz común. |

- [x] Evidencia de CR-01 a CR-05 completa; el usuario aceptó el cierre clínico C12 tras repetir las comprobaciones afectadas.
- [x] Revisión del usuario. **C16 aceptado el 2026-11-18.**

### C03 · Historial y entrega del adjunto

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T07 · Conservar el vínculo por versión | Done · diagnostic_results | Corregir la proyección de historial y definir el significado de `reportId` en carga y lectura según el contrato. ME-04. | Las versiones guardan su vínculo real; la evidencia distingue lo recuperable de los huecos históricos. | Suite `test_diagnostic_results.py` y probe `diagnostic_results`. |
| T08 · Recuperar adjuntos tras fallos | Done · diagnostic_results, core/services | Definir registro y bytes ante rollback, reintento y cambio de almacén. Separar metadatos y contenido. ME-06 y MN-01. | Reintento y descarga preservan huella y archivo correcto. Un nombre Unicode no rompe la respuesta. | Probe `diagnostic_results` y pruebas de los almacenes configurados. |

- [x] Pruebas focales y matriz común registradas. Adjuntos y recuperación comprobados con PostgreSQL aislado.
- [x] Revisión del usuario. **C03 aceptado el 2026-11-18.**

### C04 · Proyección analítica

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T09 · Comprobar el rol y la base analítica | Done · analytics | Acordar topología con el esquema vigente y conceder permisos mínimos al rol correspondiente. ME-03. | El rol de ejecución puede hacer su trabajo en la base acordada y se conserva la separación de acceso. | Probes `persistence` y `clinical_analytics` con rol limitado. |
| T10 · Retirar proyecciones invalidadas | Done · analytics, clinical_records | Procesar corrección e invalidación desde la fuente permitida. ME-01. | Se elimina el punto invalidado y el cursor se confirma con el efecto. | Probe `clinical_analytics`; invalidación, rollback y reintento. |
| T11 · Recuperar ETL tras retención | Done · analytics, sync | Reclamar el cursor por cuenta y definir origen completo para reconstrucción. ME-02. | Dos ejecuciones convergen y la reconstrucción recupera los puntos vigentes tras la poda. | Probe `clinical_analytics` con dos conexiones y retención. |

Despiece de T11 por recorrido: `etl_cases.py` coordina; `analytics/repository/dao.py` reclama; `clinical_records/domain/measurements.py` y `application/measurements_cases.py` exponen la fuente vigente; `clinical_records/repository/dao.py` la consulta; `clinical_analytics/check.py` prueba poda y dos conexiones.

- [x] Pruebas focales y matriz común registradas. ETL y concurrencia comprobados con PostgreSQL aislado.
- [x] Revisión del usuario. **C04 aceptado el 2026-11-18.**

### C05 · Límites HTTP e historia clínica

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T12 · Aplicar el límite antes de analizar JSON | Done · sync, HTTP común | Conservar topes de cuerpo y operación, respuesta 413 y correlación. ME-05. | Medir recepción acotada en las peticiones grandes y comprobar cero efectos. | Suite `test_operations.py` y probe `sync`. |
| T13 · Paginar resultados del informe | Done · diagnostic_results | Filtrar y contar en SQL con orden estable y parámetros de página del proyecto. ME-07. | Listas de varias páginas conservan el total filtrado y orden; se verifica el contrato publicado. | Probe `diagnostic_results` y exportador. |
| T14 · Completar proyección de historia clínica | Done · clinical_records y componentes propietarios | Añadir un recorrido por propietario según el diseño y acordar recuperación de entradas previas. ME-08. Separar informes y especialidades si superan cinco archivos. | La entrada refleja cada versión y aparece solo con permiso de la sección al leer historia. | Probes `clinical_history`, `diagnostic_results`, `specialty_templates` y `specialties`. |

- [x] Pruebas focales y matriz común registradas. Límite HTTP, paginación e historia comprobados con PostgreSQL aislado.
- [x] Revisión del usuario. **C05 aceptado el 2026-11-18.**

### C06 · Captura clínica y trazabilidad de contratos

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T15 · Reunir las fichas que requiere la captura clínica | Done · sync, patients | Incluir las referencias de las proyecciones de etapa 3 y conservar el filtro por cuenta y sección. ME-09. | La captura incluye la ficha inactiva cuando una proyección autorizada la necesita. | Probes `downloads`, `medications`, `care_plans` y `diagnostic_results`. |
| T16 · Hacer reproducible la verificación de contratos | Done · scripts, sync/contratos | Definir marca verificable y comprobar archivos publicados ante cambios de código y ante commits ajenos al contrato. MN-02. | Dos exportaciones reproducibles y `--check` detectan cambios reales de fuentes o contenido. | `python -m scripts.export_contracts --check` y probe `contracts`. |

- [x] Pruebas focales y matriz común registradas. Captura clínica y contratos comprobados con servicios aislados.
- [x] Revisión del usuario. **C06 aceptado el 2026-11-18.**

### C17 · Errores de lote, filtros y paginación

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T42 · Validar la forma de la clave por acción | Done · sync | Resolver dónde validar la relación entre acción y tipo de clave. Cerrar el camino que termina en `assert_never`. ME-10. | El cliente recibe la validación contractual. Para un rechazo por operación conserva los resultados del lote y el tratamiento de las independientes. | `test_operations.py` y probe `sync`; clave de forma incorrecta, resultado anterior y acción posterior. |
| T43 · Aplicar filtros de objetivos y acciones | Done · care_plans | Usar `goalKind`, `evaluationStatus` y `completionStatus` en el DAO de su recurso, con consulta tipada. Retirar el callback de SQL de aplicación. ME-11 y RF-09. | Filtros solos y combinados producen `items` y `total` del mismo conjunto antes de paginar. | Probe `care_plans` con estados mixtos y más de una página. |
| T44 · Alinear los parámetros de series con su respuesta | Done · analytics | Resolver si el contrato pide serie completa acotada o paginación y hacer que la consulta cumpla la forma acordada. ME-12. | Los parámetros publicados tienen el efecto definido y las series grandes tienen un límite comprobado. | `test_clinical_series.py`, probe `clinical_analytics` y comparación del contrato. |

- [x] Las entradas, resultados y errores concuerdan con lo que publica la API.
- [x] Revisión del usuario. **C17 aceptado el 2026-11-18.**

### C18 · Versiones de plantilla y conexiones de adjuntos

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T45 · Incluir las versiones de plantilla que necesita la captura | Done · specialties, sync | Definir las claves por versión y usar las referencias de los registros autorizados para preparar una captura que se pueda interpretar desde vacío. ME-13. Depende del retiro de plantillas de T37. | Un mismo snapshot permite recuperar la definición de cada registro vigente, incluso tras editar o retirar su plantilla. | Probes `specialty_templates` y `downloads`; arranque con registros de dos versiones. |
| T46 · Cerrar o reutilizar el cliente HTTP de S3 | Done · core/services | Dar al cliente un dueño y un límite de vida explícitos en la carga y la descarga. ME-14. Coordinar con T08. | Se comprueba cierre en éxito y en fallo, o uso de un cliente con cierre al apagar el servicio. | Almacén de prueba y comprobación de conexiones en llamadas repetidas. |

- [x] Captura y adjuntos funcionan con las referencias y los recursos que requieren. La captura incluye versiones retiradas necesarias; los dobles comprueban el cierre HTTP de S3 en éxito y error.
- [x] Revisión del usuario. **C18 aceptado el 2026-11-18.**

### C19 · Cálculo, datos opcionales y trazas

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T47 · Cubrir lambda cero en LMS | Done · analytics | Corregir el logaritmo en la rama lambda cero. MN-04. | Una fila ficticia con lambda cero produce el resultado de prueba y las referencias actuales conservan sus salidas. | `test_who_growth.py` con el caso faltante. |
| T48 · Resolver la nota de evaluación | Done · care_plans, contratos | Acordar si la nota se conserva y dónde se lee. Si se retira del payload, acordar cómo responde la API a consumidores actuales. MN-05. | Una nota enviada se conserva según contrato o recibe un rechazo explícito. | Probe `care_plans`, con evaluación con nota y sin nota. |
| T49 · Usar la misma correlación en lectura y auditoría | Done · clinical_records, API | Propagar el identificador de la petición a la auditoría de la lectura. MN-06. | El valor de `X-Correlation-ID` permite localizar el evento de la misma lectura sin registrar contenido clínico. | Probe `clinical_history` y comprobación de auditoría por correlación. |
| T71 · Leer todas las secciones guardadas | Done · accounts | Proyectar las doce secciones desde la membresía sin sustituirlas por defaults. ME-15. Añadida por decisión del usuario en C01. | Cada nivel guardado aparece igual en la respuesta; la autorización ejecutada no cambia. | Caso focal de `accounts` con las doce secciones y tres niveles; comparar HTTP con la fila. |

**Desglose de T48 tras la decisión del usuario:** conservar `note` como `evaluationNote`. Dominio: proyectar el campo en respuesta e historia. Persistencia: añadir columnas nulas a estado/historia en una migración nueva y actualizar el modelo físico. Aplicación: guardar el valor validado en la evaluación. Contrato: documentar entrada y lectura. Probe: evaluar con y sin nota y comprobar respuesta, historia, captura y PostgreSQL.

- [x] Los cuatro casos tienen prueba focal y el contrato refleja la decisión sobre la nota.
- [x] Revisión del usuario. **C19 aceptado el 2026-11-18.**

### C23 · Huella de los cambios parciales

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T69 · Distinguir ausencia y null en la huella | Done · sync, clinical_records | Sustituir la decisión por prefijo por la semántica de cada acción, a partir del payload ya validado. Inventariar acciones parciales. Acordar el tratamiento de recibos antiguos con huella ambigua antes de escribir el cambio. RG-10. | La misma clave y el mismo cambio recuperan el recibo. Omitir un valor y borrarlo cuentan como payloads distintos cuando la escritura los distingue. Un recibo de cualquier versión impide repetir el efecto. Los defaults equivalentes conservan su comportamiento. | Vectores de `test_operations.py` y probe `sync` con recibos de ambas versiones, método presente, omitido y nulo, y reintentos concurrentes en PostgreSQL. |

- [x] Registrar la decisión sobre recibos antiguos y los resultados con omisión, null y concurrencia. Se conserva la recuperación antigua sin repetir efectos; las huellas nuevas distinguen las variantes.
- [x] Revisión del usuario. **C23 aceptado el 2026-11-18.**

## Etapa 2 · Relaciones, reutilización y reglas comunes

### C07 · Relaciones y persistencia común

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T17 · Modelar una relación de contactos | Done · patients | Probar relaciones tipadas sobre FK existentes para ficha, vínculo y contacto. Conservar datos del vínculo. | Las lecturas conservan alcance, orden y cardinalidad. Medir consultas y comprobar que no aparece carga implícita. | Probes `patients` y `persistence`; recuento SQL del recorrido. |
| T18 · Modelar el vínculo informe-adjunto | Done · diagnostic_results | Usar como piloto la relación compuesta validada en T06. Adoptar carga explícita donde reduzca consultas. | La relación usa las mismas claves y el DAO conserva filtros, paginación y bloqueos necesarios. | Probe `diagnostic_results` y comparación de consultas. |
| T19 · Reducir DAOs de historia y vínculo | Done · todos los componentes | Reutilizar `get_by` y `get_multi` en todas las lecturas por ámbito y páginas de historia. Retirar subclases vacías y todas las variantes `scoped`, incluidas las de especialidad; el usuario amplió el alcance tras revisar el piloto. RF-03. | Mismos filtros, orden, bloqueos y tipos de retorno sin llamadas `scoped` ni páginas de historia duplicadas. | Probes de cada componente, persistencia y suite completa. |

**Ampliación de T19 aprobada por el usuario:** migrar absolutamente todos los componentes, no solo cuidados e informes. Grupos: (1) cuentas, pacientes y medicación; (2) registros clínicos y encuentros; (3) especialidades y odontología; (4) historias restantes. Las páginas ordinarias con filtros de dominio no se sustituyen; solo las historias que `get_multi` puede expresar con los mismos efectos.

- [x] Pruebas focales y matriz común registradas. Relaciones, lecturas por ámbito y todas las historias comprobadas con PostgreSQL aislado y datos ficticios.
- [ ] Revisión del usuario.

### C08 · Reloj y sellos de base

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T20 · Reutilizar `datetime_now()` para consultar la hora | Done · core/utils y consumidores | Sustituir las consultas SQL de reloj por la función existente y retirar llamadas redundantes donde el mixin genera los sellos. Distinguir hora de negocio, caducidad y hora del hecho. | Cada recorrido conserva el instante y el orden de bloqueos que exige su contrato, sin consultar el reloj a PostgreSQL. | Suite de operaciones, autorización y pruebas de caducidad. |
| T21 · Probar sellos de creación y modificación | Done · core/db y un componente piloto | Heredar `Date` con `insert_default` y `onupdate` basados en `datetime_now()`. Conservar nombres físicos, valores explícitos y defaults de alta. | Altas con ORM, DAO Core y SQL directo, y modificaciones ORM/Core verifican zona, precisión, orden y sellos, incluido rollback. | Probe `persistence`; comparar API, fila, historia, recibo y journal. |
| T22 · Extender solo los sellos compatibles | Done · propietarios de tablas | Registrar por tabla qué campos son sellos y cuáles son instantes compartidos o de negocio. Migrar cada grupo compatible en un cambio pequeño. | El inventario refleja reglas aplicadas, excepciones justificadas y datos previos conservados. | Migración desde la revisión previa y pruebas por propietario. |

**Decisión del usuario, 2026-11-20:** enfocar C08, consultar la hora con `datetime_now()` y heredar los sellos mediante el mixin `Date` de `core/db/model.py`, sin repetirlos en cada modelo. Esta instrucción sustituye el enfoque previo de triggers y no registra aceptación de C07 ni de C08.

**Inventario T22:** 52 modelos con ambos campos heredan `Date`: 41 filas vigentes y las 11 historias `care_plan_histories`, `care_plan_goal_histories`, `care_plan_action_histories`, `care_plan_review_histories`, `dental_finding_histories`, `dental_treatment_histories`, `diagnostic_report_histories`, `diagnostic_report_result_histories`, `report_attachment_histories`, `specialty_record_histories` y `specialty_template_histories`. `DeviceToken` y `SyncSnapshot` heredan `CreatedDate`; `AnalyticEtlState` hereda `UpdatedDate`. Total: 55 modelos sin declaraciones locales de sellos. Las historias que solo tienen `changed_at` no reciben el mixin. `STAMP_TABLES` y `CREATED_ONLY_TABLES` en `20261120_01_row_timestamps.py` agregan 85 defaults físicos de alta a filas vigentes y recursos de un sello, sin reescribir datos. Las historias con sellos explícitos no reciben defaults físicos nuevos. `accepted_at`, `completed_at`, `occurred_at`, `changed_at`, `measured_at`, `expires_at`, `revoked_at`, fechas clínicas e intervalos conservan sus reglas. No quedan triggers ni funciones de reloj nuevos.

- [x] Pruebas focales y matriz común registradas. Reloj, sellos, retención, sincronización y propietarios comprobados con PostgreSQL aislado y datos ficticios.
- [ ] Revisión del usuario.

### C09 · Constantes y límites de componentes

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T23 · Unificar los límites publicados del protocolo | Todo · core, sync, HTTP | Compartir en `src/core/constants.py` los topes de cuerpo, operación, lote y página entre capacidades y validación. RG-01. | Los topes anunciados y los aplicados coinciden. Se conservan defaults, esquemas y estados HTTP. | Capacidades, exportador y peticiones con tamaño exacto, una unidad menos y una más. |
| T24 · Trasladar consultas al dueño de los datos | Todo · analytics, clinical_records, specialties | Mover SQL de aplicación al DAO dueño y exponer resultados tipados entre componentes. Empezar por odontología y retirar el envoltorio que solo desempaqueta el payload. RF-10. Aplicar el control estructural a cada componente al terminar su tarea. | La capa de aplicación queda sin SQL directo ni imports de repositorios ajenos en los recorridos modificados. | Controles de estructura, probes `specialties` y `clinical_analytics`. |

- [ ] Pruebas focales y matriz común registradas. Si toca datos o transacciones, prueba con PostgreSQL aislado.
- [ ] Revisión del usuario.

### C20 · Trabajo repetido en políticas y consultas

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T50 · Preparar una vez el catálogo de permisos | Todo · accounts, sync | Compartir los descriptores inmutables y sus tablas derivadas entre descubrimiento y proyecciones. RF-01. | El número de construcciones deja de crecer con las acciones o las filas. Los permisos siguen evaluándose con el contexto vigente y las posiciones públicas conservan orden y duplicados. | `test_authorization_policies.py`, `test_downloads.py` y recuento con 500 proyecciones. |
| T51 · Omitir el conteo en lecturas que solo necesitan filas | Todo · core/db, sync y dueños | Separar el camino que ejecuta `COUNT` y nombrar el argumento de desplazamiento interno. Migrar primero una captura y extender por componente. RF-04. | Las capturas migradas conservan contenido y límites de transacción con menos consultas. Las listas paginadas conservan `items` y `total`. | Probes `downloads` y `persistence` con recuento de sentencias. |
| T52 · Reutilizar las consultas de captura y revisiones iguales | Todo · propietarios de DAOs | Aprovechar T51 y el soporte existente para `valid_snapshot`. Compartir `revise` donde la clave, versión, sello y requisito de bloqueo coincidan. RF-03. | Hay menos copias con los mismos filtros y versiones. Las reglas por objeto siguen en su DAO. | Probes del componente piloto y pruebas de persistencia antes de extender. |

- [ ] Registrar recuentos antes y después de catálogos y consultas. Validar el mismo contrato y ámbito de cada lectura.
- [ ] Revisión del usuario.

### C21 · Retiro de código sin recorrido activo

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T53 · Reducir la superficie del DAO y del modelo base | Todo · core/db | Retirar operaciones masivas, selección de estrategias por cadena, acceso asíncrono de atributos propio y sesión por tarea cuando se confirme la ausencia de consumidor. RF-05. | Se conservan consultas y escrituras activas, claves, opciones de ejecución y bloqueos. El paquete se importa y construye. | Búsqueda de referencias, pruebas de estructura y probe `persistence`. |
| T54 · Retirar utilidades que carecen de llamadas | Todo · core/utils, core/constants | Confirmar el uso de utilidades y filtros. Comprobar `REQUEST_TIMEOUT_SECONDS` y `DELAY_BETWEEN_REQUESTS_SECONDS` en los puntos de entrada del paquete antes de retirar sus reexportaciones y definiciones. RF-06 y quinta revisión. | Las piezas retiradas carecen de consumidor comprobado. Se conservan los sentinels y el orden que usa la referencia `api/users`. | Búsqueda de referencias, `test_common_support.py` y suite. |
| T55 · Resolver el alcance de la caché desconectada | Todo · core/services, settings | Verificar si el paquete publicado o los flujos de operación requieren los adaptadores y su configuración. Retirar por grupos o registrar el consumidor concreto que lo conserva. RF-06. | El arranque y el paquete conservan las capacidades soportadas. La decisión queda respaldada por referencias. | Pruebas de arranque, contenido del wheel y build. |

- [ ] Documentar para cada retiro los puntos de entrada comprobados y las capacidades con uso que se conservaron.
- [ ] Revisión del usuario.

### C22 · Rutas, sesiones y descarga

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T56 · Reutilizar la obtención de credenciales y los errores comunes | Todo · API, authorization | Probar la dependencia y el mapeo común de 401/403/404 en dos routers. Extender por router si desaparece duplicación. RF-07. | Mismos esquemas OpenAPI, credenciales aceptadas, códigos, cabeceras y auditoría que en las rutas anteriores. | Exportador y probes `access` y de los routers del piloto. |
| T57 · Quitar el segundo cierre de sesión | Todo · core/db | Dejar que el contexto de sesión cierre la dependencia HTTP. RF-08. | Una sesión por petición con un cierre al salir, en éxito, error y cancelación. | `test_foundation.py` y comprobación focal del cierre. |
| T58 · Probar la política de descarga que ejecuta la API | Todo · sync, accounts | Mover los casos de prueba del alias de compatibilidad a `projection_allowed` y retirar el alias si carece de consumidores. RF-06. | Se conserva la cobertura de entidades, audiencias, rol y sección en la función activa. | `test_downloads.py`, `test_clinical_permissions.py` y probe `downloads`. |

- [ ] Comprobar el contrato de las rutas, la auditoría y el manejo de sesiones y permisos.
- [ ] Revisión del usuario.

### C24 · Paginación, duraciones y revisión del modelo

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T59 · Calcular el desplazamiento desde la página | Todo · core/schema, dueños de DAOs | Reusar el cálculo con los datos validados de `PageQuery`. Coordinar el argumento interno con T51. Migrar por componente. RG-01. | Misma forma pública y mismos límites, totales y filas con páginas fuera y dentro del rango. | Pruebas de límites y probe de listados con páginas 1 y 2, filtros y una página vacía. |
| T60 · Nombrar duraciones y límites de sincronización | Todo · sync, core | Dar una fuente a cada duración y al tamaño validado de cursor. Documentar unidades y qué reglas de retención requieren equivalencia en SQL. Conservar las migraciones publicadas. RG-02. | Emisión y validación coinciden en cada plazo. Capacidades sigue publicando los mismos valores. Alta y renovación de cupos SSE conservan su duración. | Probes `retention`, `downloads` y `events` con vencimientos en ambos lados del límite y SQL vigente. |
| T61 · Compartir la revisión vigente del modelo | Todo · sync, contratos | Usar una fuente para capacidades, capturas nuevas, manifiesto y artefactos. Coordinar con T16. RG-03. | Las salidas coinciden en revisión e identificadores previstos. Una captura previa conserva la revisión que guardó. | Exportador, comparación de esquemas y probe `downloads` con una captura previa y otra nueva. |

- [ ] Comparar límites, tiempos y revisión de modelo entre esquema, ejecución y lo que publica la API.
- [ ] Revisión del usuario.

### C25 · Ventana y formatos comunes

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T62 · Derivar el fin exclusivo de la ventana | Todo · sync | Reusar los valores de la ventana por defecto y calcular el fin exclusivo desde el último día incluido. RG-04. | La ventana incluye hoy más 180 días. El máximo sigue siendo 366 días. | Captura con citas en los dos límites, parámetros explícitos y un día fuera del máximo. |
| T63 · Compartir la conversión pública a UTC | Todo · core/schema y dueños de proyecciones | Usar un formateador tipado para instantes con zona que salen con `Z`. Migrar por componente tras comparar JSON. RG-05. | Se conservan formato `date-time`, offset convertido, fracciones, null, huellas y salidas que consumen clientes. | Vectores de JSON, pruebas de recibos y probe `events` por cada tipo migrado. |
| T64 · Reusar las comprobaciones de formato de fecha | Todo · core/schema, patients, schedule, sync | Extraer las comprobaciones comunes que ya coinciden. Retirar la llamada de un esquema de captura a otro de agenda. RG-06. | Se conservan mensajes, campos opcionales y formas admitidas en cada ruta. | Casos de fecha válida, fecha con hora, objeto `datetime`, valor nulo, fecha omitida e instante con zona. |

- [ ] Comparar entradas, salidas y esquemas con los casos de prueba previos.
- [ ] Revisión del usuario.

### C26 · Tipos y cálculos clínicos

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T65 · Compartir precisión y límites de fechas parciales | Todo · clinical_records, medications, care_plans | Definir por recurso cómo ordenar rangos inciertos. Reusar el cálculo de precisión y límites de calendario en el dominio. RG-07. | Rango de precisión mixta sigue la regla acordada. Diciembre de 9999 se calcula dentro del rango de fechas admitido. | Pruebas de rangos parciales, año bisiesto, fin de año, precisión distinta y orden inverso. |
| T66 · Reusar la aritmética de edad | Todo · patients, clinical_records, analytics | Compartir el cálculo de años y meses completos tras fijar la referencia de cada caso. RG-08. | Se preservan las referencias, la regla del cumpleaños y el trato acordado de fechas anteriores al nacimiento. | Paciente nacido el 29 de febrero, día previo y fecha de nacimiento corregida. Comparar perfil y crecimiento. |
| T67 · Compartir el tipo de medición | Todo · clinical_records, care_plans, analytics | Usar el tipo del dominio de mediciones en cuidados y analítica. RG-09. | Los cinco valores válidos, esquemas y filtros conservan su contrato. | Validadores de cuidados y series, exportador y comparación de tipos en sus esquemas. |

- [ ] Verificar cada regla clínica con los casos de su dominio.
- [ ] Revisión del usuario.

### C27 · Guardas, códigos y soporte de pruebas

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T68 · Reusar guardas de patch y códigos comunes | Todo · core/schema y dueños de operaciones | Inventariar guardas idénticas y los emisores y lectores de códigos públicos comunes. Adoptar los casos que compartan significado, con tipos y sin volver a validar el payload. RG-12. | Se conservan códigos textuales, mensajes, ubicación, semántica de null y etapas de validación. | Casos de patch vacío, campo ausente, null permitido, null inválido y conflicto de versión. |
| T70 · Compartir la envoltura de operaciones en probes | Todo · test-support | Probar en informes y cuidados una forma común de armar y enviar operaciones. Extender donde elimine copias sin ocultar las expectativas. RG-13. | La prueba permite ver clave, versión, actor y resultado esperado. Sus límites contractuales se comprueban con valores independientes del código que valida. | Probes `diagnostic_results` y `care_plans` con los mismos casos y resultados antes y después. |

- [ ] Comparar las pruebas de errores y los resultados de los dos probes piloto.
- [ ] Revisión del usuario.

## Etapa 3 · Legibilidad y funciones de hasta 70 líneas

### C10 · Aceptación y sincronización legibles

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T25 · Dividir la preparación de operaciones | Todo · sync | Aislar normalización, reutilizar el cálculo de huella de T69 y quitar la condición de permisos legados repetida. Agrupar las guardas de entrada y distinguir cuenta solicitada de cuenta autorizada. MN-03 y RG-11. | Se conserva el orden de validación y autorización, sin validar dos veces el payload. Los vectores legados conservan su huella. | Vectores y suite `test_operations.py`; probe `sync` con invitación y cuenta explícita. |
| T26 · Dividir el despacho de efectos | Todo · sync y propietarios | Reducir la duplicación entre clasificación de entidad, filtro previo y handlers. Reusar los catálogos existentes y funciones de los dueños. RF-02. | Cada acción produce el mismo efecto, errores y respuesta canónica, con los mismos bloqueos. | Suite de operaciones, políticas y probe `contracts`. |
| T27 · Dividir el registro de la aceptación | Todo · sync, audit | Aislar recibo y registro de cambios dentro de `transaction(db)` y reducir recuperación y descarga en pasos propios. Reusar sección y clave canónica ya calculadas y nombrar el instante que comparten los registros. RG-11. | Cada función modificada tiene hasta 70 líneas. Fallo, reintento y concurrencia conservan atomicidad y visibilidad. | Probes `sync`, `downloads`, `events`, `persistence`; comparar clave, sección e instante. |

- [ ] Pruebas focales y matriz común registradas. Si toca datos o transacciones, prueba con PostgreSQL aislado.
- [ ] Revisión del usuario.

### C11 · Casos de uso por dominio

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T28 · Simplificar agenda, citas y servicios | Todo · appointments, schedule, services | Dividir primero transiciones de cita y después agenda/servicios por archivo o pareja de archivos. | Cada función modificada tiene hasta 70 líneas y los cambios de horario conservan sus efectos y bloqueos. | Probes `appointments`, `schedule`, `services`. |
| T29 · Simplificar cuenta, paciente e identidad | Todo · accounts, patients, authorization | Separar altas, cambios, invitaciones, lecturas y credenciales por recorrido, con tipos explícitos. | Cada función modificada tiene hasta 70 líneas, con mismo acceso y efectos. | Probes `accounts`, `access`, `patients`, `team`. |
| T30 · Simplificar casos clínicos largos | Todo · propietarios clínicos | Dividir por componente, eliminar proyecciones identidad y compartir mapeos repetidos de informes. Simplificar el desempaquetado y la auditoría de cuidados. RF-09 y RF-10. | Cada función modificada tiene hasta 70 líneas. Se conserva la versión, auditoría, permisos y selección de datos. | Probes de cada componente clínico modificado. |

- [ ] Pruebas focales y matriz común registradas. Si toca datos o transacciones, prueba con PostgreSQL aislado.
- [ ] Revisión del usuario.

### C12 · Límite de longitud y verificación final

| Tarea | Estado y dueño | Cambio | Aceptación | Prueba focal |
|---|---|---|---|---|
| T31 · Simplificar las funciones largas restantes | Todo · sync, core, analytics y pruebas | Cerrar lista AST en `src`, `scripts`, `tests` y `test-support`. Dividir por grupo de hasta cinco archivos y revisar complejidad antes y después. Conservar las migraciones publicadas. | Cero funciones de más de 70 líneas en el alcance activo; el control se aplica también a migraciones nuevas. | Inventario AST y suite por cada módulo modificado. |
| T32 · Verificar la entrega completa | Todo · API | Correr la matriz integral, comparar contratos y registrar mediciones y riesgos pendientes. | Suite, build, contratos y probes clave pasan en entorno aislado. Cada incidencia conserva evidencia y estado. | Suite, build sin red, exportador, persistencia, acceso, sync, agenda, clínicos y analítica. |

- [ ] Pruebas focales y matriz común registradas. Si toca datos o transacciones, prueba con PostgreSQL aislado.
- [ ] Revisión del usuario.

## Evidencia de C08 · Reloj y sellos heredados

**Diseño aplicado.** `CreatedDate`, `UpdatedDate` y `Date` en `core/db/model.py` mapean `date_added`/`date_updated` a `created_at`/`updated_at`. Cincuenta y dos modelos con ambos sellos usan `Date`; dos usan `CreatedDate` y ETL usa `UpdatedDate`. No hay declaraciones locales de estos campos. Las propiedades de compatibilidad permiten que Pydantic siga validando `created_at`/`updated_at` sin cambiar el JSON.

**Reloj.** Las consultas SQL de reloj se sustituyeron por `datetime_now()`. Servicios, ofertas, agenda, gestión administrativa y ETL dejaron de pedir hora para sellos: `insert_default` y `onupdate` los generan. Citas, clínica, invitaciones, caducidad, recibos, auditoría y journal conservan el reloj explícito que requieren sus reglas.

**SQLAlchemy 2.1.6.** Se comprobaron [mixins declarativos](https://docs.sqlalchemy.org/en/21/orm/declarative_mixins.html#mixing-in-columns), [defaults contextuales](https://docs.sqlalchemy.org/en/21/core/defaults.html#context-sensitive-default-functions) y [dataclasses](https://docs.sqlalchemy.org/en/21/orm/dataclasses.html#using-mixins-and-abstract-superclasses). No se conservó `default_factory`: convertir todos los modelos a dataclasses volvió obligatorios campos con `server_default` y rompió constructores existentes. `insert_default` aplica el comportamiento pedido al INSERT sin ese efecto. Los defaults contextuales reutilizan el otro sello para evitar `updated_at<created_at` en DAO Core.

**Persistencia.** `20261120_01_row_timestamps.py` agrega 85 defaults físicos `CURRENT_TIMESTAMP`, sin triggers ni reescritura de datos. `persistence` comprueba el inventario, alta ORM, alta DAO Core, alta SQL directa, `onupdate`, zona, microsegundos, valor explícito, rollback y migraciones up/down/reapply. Los UPDATE SQL directos no ejecutan `onupdate`; el alcance automático de modificación es ORM/Core.

**Correcciones durante la verificación.** Se separaron DTOs y entradas ORM en citas/agenda, se restauraron los nombres de DTO en el timeline y se ajustaron fixtures de `SimpleNamespace` y servicios. El probe de retención ahora hace avanzar por microsegundos su reloj controlado: un valor congelado no marca `updated_at` como modificado y activa `onupdate`. Las repeticiones posteriores pasaron.

**Comandos y resultados.**

- Matriz final de 30 probes con PostgreSQL/Keycloak Test y datos ficticios: `access`, `accounts`, `team`, `appointments`, `services`, `schedule`, `patients`, `sync`, `retention`, `downloads`, `events`, nueve propietarios clínicos, `care_plans`, `diagnostic_results`, `specialty_templates`, `specialties`, `clinical_history`, `clinical_permissions`, `clinical_downloads`, `clinical_analytics`, `collaboration` y `persistence` → **30/30 pasaron**.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **262/263 pruebas correctas**, 94,956 s. El único error es `UsersStructureTests`: `src/api/users/repository/dao.py` ya estaba eliminado antes de C08. No se restauró código retirado.
- `uv build --offline` → wheel y sdist correctos.
- `./.venv/Scripts/python.exe -m scripts.export_contracts --check` → conserva el fallo previo por `openapi.json` desactualizado; no se modificó la forma pública en C08.
- `git diff --check` → sin errores; solo avisos LF/CRLF. `basedpyright` no está instalado en `.venv`, por lo que no se añade una comprobación de tipos con esa herramienta.

**Límites y revisión.** No se acreditan consumidores Rust/Hub, datos reales ni producción. T20–T22 están Done; C08 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C07 · Relaciones y persistencia común

**T17.** `AccountPatient.contact_links`, `PatientContactRelationship.patient` y `.contact` usan relaciones tipadas con las FK compuestas existentes, `foreign()` y `viewonly=True`. Los DAOs las usan en los tres joins que ya existían. El recorrido de contactos conserva alcance, orden, estado y datos del vínculo. La captura SQL comprobó dos consultas —total y página— sin lecturas adicionales de contactos.

**T18.** `DiagnosticReport.attachment` usa `(account_id,attachment_id,patient_id)` y `viewonly=True`; `for_attachment` reutiliza esa relación en su join. No se añadió eager loading porque el caso solo necesita el ID del informe. El probe conserva metadatos, permisos e historias y capturó en el motor exactamente dos consultas, para adjunto e informe. La primera instrumentación con `AsyncSession.execute` no capturaba `scalar()`; se sustituyó por `before_cursor_execute` y se retiró el diagnóstico temporal.

**T19 corregido y ampliado por decisión del usuario.** Se descartó por completo el diseño inicial con `ScopedDAO` y `HistoryPageDAO`. Después se migraron todos los componentes y también las variantes detectadas durante la revisión: `_PlanScoped` y `get_scoped`. En los DAOs no quedan `scoped`, `lock_scoped`, `get_scoped`, `_Scoped`, `_PlanScoped`, `_HistoryPage` ni páginas de historia duplicadas; tampoco quedan llamadores antiguos en `test-support`. `AsyncScopedSession` es una pieza de sesión distinta, asignada a T53. Las lecturas usan directamente `DAO.get_by`; las historias y subrecursos de planes, `DAO.get_multi`. Los métodos existentes admiten `for_update` (incluido `read`), `after_version`, `after_version_field` e `include_total`; conservan `populate_existing`, bloqueos, orden, paginación y el número de consultas de captura. La variante de nacimiento usa `patient_version`. El adaptador clínico interno ahora se llama `read`; la consulta de profesional con joins se llama `for_account`. Se retiraron mixins y clases vacías y se actualizaron controles y dobles. Las páginas ordinarias con filtros de dominio y `AppointmentHistoryDAO.append` permanecen porque no son las consultas sustituidas.

**Fuentes oficiales para SQLAlchemy 2.1.6 (`uv.lock`).** [Relaciones tipadas y viewonly](https://docs.sqlalchemy.org/en/21/orm/basic_relationships.html), [primaryjoin y foreign](https://docs.sqlalchemy.org/en/21/orm/join_conditions.html#specifying-alternate-join-conditions), [before_cursor_execute](https://docs.sqlalchemy.org/en/21/core/events.html#sqlalchemy.events.ConnectionEvents.before_cursor_execute).

**Comandos y resultados.**

- `./.venv/Scripts/python.exe test-support/patients/check.py` → pasó con relaciones, paginación, dos consultas, alcance y carreras previas.
- `./.venv/Scripts/python.exe test-support/diagnostic_results/check.py` → pasó con relación compuesta, dos consultas, historias, captura, rollback y descarga.
- Cobertura global con PostgreSQL/Keycloak Test: `accounts`, `patients`, `medications`, `care_plans`, `diagnostic_results`; diez probes de perfil/condiciones/alergias/antecedentes/inmunizaciones/mediciones/notas/encuentros/historia clínica/analítica; `specialty_templates` y `specialties`; y una secuencia de 13 probes para citas e historias migradas. Todos pasaron. El probe final de `patients` comprobó también `patient_version`.
- Las búsquedas finales sobre `src`, `tests` y `test-support` no encontraron `scoped` ni páginas de historia duplicadas. Los dos llamadores directos del probe de citas también se migraron.
- La primera suite global detectó listas de clases retiradas en los controles de estructura de registros clínicos y encuentros. Se actualizaron los inventarios, sin restaurar código, y la repetición pasó.
- Tras la última corrección pasaron los probes `care_plans`, `accounts`, `access` y `sync`, con filtros, capturas, bloqueos, recibos y carreras. Contratos, build y `git diff --check` también pasaron.
- `./.venv/Scripts/python.exe test-support/persistence/check.py` → pasó con migraciones, rollback, DDL denegado y escritores coordinados.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **263 pruebas, OK**, 106,640 s antes de la última observación. Tras retirar `_PlanScoped`/`get_scoped` y actualizar sus dobles, las pruebas focales de cuentas y operaciones pasaron (**5 + 12**). La última suite completó 263 casos: 262 sin fallos y un error externo porque `src/api/users/repository/dao.py` fue eliminado fuera de esta tarea. No se restauró trabajo ajeno.
- `./.venv/Scripts/python.exe -m scripts.export_contracts` y `--check` → **113 rutas, 176 esquemas HTTP, 104 acciones; correcto**. No cambió la forma pública.
- `uv build --offline` y `git diff --check` → correctos.

**Límites.** No se acreditan consumidores Rust/Hub o producción. La suite completa conserva un error externo por la eliminación de `src/api/users`; las pruebas de esta corrección pasan. T17–T19 están Done; C07 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C23 · Huella de los cambios parciales

**Inventario y decisión.** Las acciones `Update…` ya calculan la huella con campos presentes y escriben un patch. La única excepción no cubierta por ese prefijo es `CorrectPatientMeasurement`. Su recibo antiguo no permite saber si un valor nulo estaba omitido o explícito. El usuario eligió recuperar el recibo cuando coincida la huella antigua, para ambas variantes ambiguas y sin repetir efectos. Los recibos nuevos distinguen las variantes. La regla quedó en `docs/api-v1.md`.

**Cambio.** `_operation_fingerprint` reutiliza el payload validado una vez y aplica `exclude_unset` a `Update…` y `CorrectPatientMeasurement`. Solo esta corrección calcula la huella antigua como respaldo tras encontrar un recibo con otra huella. Una coincidencia nueva o antigua recupera el resultado; el resto devuelve `IDEMPOTENCY_CONFLICT`. No cambió el esquema JSON ni la persistencia de recibos.

**Comprobaciones.**

- `./.venv/Scripts/python.exe -m unittest discover -s tests -p test_operations.py -v` → **12 pruebas, OK**. Los 48 vectores históricos conservan su huella. Los vectores nuevos producen tres huellas para método presente/omitido/nulo; con recibo nuevo los resultados son `duplicate`/`conflict`, y con recibo antiguo ambos son `duplicate`, sin llamar al efecto.
- `./.venv/Scripts/python.exe test-support/sync/check.py` → pasó con PostgreSQL/Keycloak Test. Comprobó corrección omitida, reintento idéntico con `originalResult`, variante nula en conflicto, borrado real con otra clave, reintento nulo y carrera `accepted`/`duplicate` con un recibo. Una aceptación real con el calculador antiguo generó el recibo histórico; sus reintentos omitido/nulo recuperaron el original. Estado final: versión 5, cinco historias y sin efectos repetidos.
- Durante la preparación del probe, el dispositivo inicial ya estaba revocado y una copia aislada de recibo aceptado violó la integridad de auditoría/journal. Se corrigió el fixture para usar la instalación activa y una aceptación real con huella antigua; no se relajó ninguna restricción.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **263 pruebas, OK**, 75,195 s.
- `./.venv/Scripts/python.exe -m scripts.export_contracts` y `--check` → **113 rutas, 176 esquemas HTTP, 104 acciones; correcto**. Cambió la procedencia de fuentes, no la forma pública.
- `uv build --offline` y `git diff --check` → correctos.

**Límites.** La compatibilidad antigua puede devolver el recibo anterior a la variante ambigua, según la decisión aceptada; nunca ejecuta otro efecto. No se acreditan consumidores Rust/Hub o producción. T69 está Done; C23 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C19 · Cálculo, datos opcionales y trazas

**T47.** La rama LMS con `lambda_=0` usa `Decimal.ln()` sobre `value/mu`. Un vector ficticio con razón 2 comprueba el resultado matemático; las seis pruebas previas de referencias activas siguen pasando.

**T48.** El usuario decidió conservar la nota. `EvaluateCarePlanGoal.note` se guarda como `evaluation_note` y se publica como `evaluationNote` en estado, historia y captura. La migración `20261118_05_goal_evaluation_note.py` añade columnas nulas y restricciones de texto no vacío a ambas tablas. Las filas anteriores quedan nulas: las notas ya descartadas no se pueden reconstruir. El probe comprueba evaluación con y sin nota, recibo, lectura, historia, captura y valores PostgreSQL.

**T49.** `CORRELATION_ID` es un `ContextVar` técnico en `core/constants.py`. El middleware lo establece con el UUID de `request.state` y lo restablece en `finally`; todas las lecturas que ya usan `record_clinical_read` comparten ese valor. Fuera de HTTP se conserva el UUID nuevo. El probe comparó `X-Correlation-ID` con un evento `ReadPatientClinicalHistory` en PostgreSQL, sin contenido clínico en la consulta.

**T71.** La lectura de permisos proyecta las doce columnas reales de la membresía. El probe alternó `none`,`read`,`read_write`, comparó el JSON HTTP con la fila y confirmó que un asistente sigue recibiendo 403 en esta consulta de propietario. La autorización de escritura no cambió.

**Comandos y resultados.**

- `./.venv/Scripts/python.exe -m unittest tests.test_who_growth -v` → **7 pruebas, OK**.
- `./.venv/Scripts/python.exe -m unittest tests.test_care_plans tests.test_care_plan_persistence -v` → **9 pruebas, OK**; `test-support/care_plans/check.py` → pasó.
- `test-support/clinical_history/check.py` → la primera aserción de correlación usó `object_key::text` sobre JSONB y no encontró el UUID por las comillas JSON; tras comparar con `to_jsonb(text)`, pasó el recorrido completo.
- `./.venv/Scripts/python.exe -m unittest tests.test_account_changes tests.test_clinical_permissions -v` → **13 pruebas, OK**; `test-support/accounts/check.py` → pasó.
- `test-support/persistence/check.py` → pasó con migraciones up/down/reapply, rollback, DDL denegado y escritores coordinados.
- `test-support/contracts/check.py` → primero detectó el `openapi.json` anterior sin `evaluationNote`. Tras `scripts.export_contracts`, el exportador y `--check` confirmaron **113 rutas, 176 esquemas HTTP, 104 acciones** y el probe HTTP pasó.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **261 pruebas, OK**, 70,650 s.
- `uv build --offline` y `git diff --check` → correctos.

**Límites.** No se recuperan notas históricas descartadas antes de esta corrección ni se acreditan consumidores Rust/Hub o producción. T47–T49 y T71 están Done; C19 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C18 · Versiones de plantilla y conexiones de adjuntos

**T45.** La captura reúne los pares `(templateId,templateVersion)` de los registros vigentes y consulta también el historial para incluir versiones retiradas requeridas. Cada plantilla usa la clave compuesta `{"templateId":...,"version":"..."}`; el constraint de PostgreSQL admite esa forma. La documentación de captura registra la clave y el probe comprueba una versión retirada 2 junto a una plantilla activa 1.

**T46.** `_import_s3` devuelve el cliente S3 y su cliente HTTP. `save` y `fetch` cierran este último en `finally`, sin cambiar las claves de almacenamiento ni el backend local. Los dobles comprueban una llamada a `aclose()` después de carga y descarga correctas y después de una carga fallida; el error ficticio se propaga.

**Comprobaciones.**

- Secuencia `specialty_templates && downloads && persistence`, cada uno con `./.venv/Scripts/python.exe test-support/<nombre>/check.py` → **3/3 pasaron** con PostgreSQL/Keycloak Test; cubrieron versiones activas/retiradas, captura, descarga y migración del constraint.
- `./.venv/Scripts/python.exe test-support/diagnostic_results/check.py` → la primera ejecución llegó al caso nuevo y falló por un `patch` local no importado en la prueba; tras corregirlo, pasó el recorrido completo y los tres cierres S3 con dobles.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **260 pruebas, OK**, 70,815 s.
- `./.venv/Scripts/python.exe -m scripts.export_contracts` y `--check` → **113 rutas, 176 esquemas HTTP, 104 acciones; correcto**.
- `uv build --offline` → wheel y sdist correctos.
- `git diff --check` → sin errores.

**Límites.** No se usó S3 real, no se midieron sockets y no se acreditan consumidores o producción. T45/T46 están Done; C18 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C17 · Errores de lote, filtros y paginación

**T42.** Un `AccountRuleError` de una operación se convierte en resultado `rejected` dentro del lote, sin perder resultados anteriores ni detener independientes. El probe usó una clave compuesta inválida entre dos operaciones y recibió las tres respuestas.

**T43.** El DAO de cuidados aplica `recordStatus`, `goalKind`, `evaluationStatus` y `completionStatus` antes de contar/paginar. Se retiró el callback SQL de aplicación. El probe cubrió estados mixtos, filtros combinados y dos páginas.

**T44.** El usuario eligió paginar puntos. La consulta filtra válidos, ordena por `(measuredAt,id)` y aplica `LIMIT/OFFSET`; `SeriesResponse` conserva `points` y añade `total`. El contrato y la documentación se actualizaron.

**Comprobaciones.**

- `test-support/sync/check.py` y `unittest discover -s tests -p test_operations.py -v` → pasaron, incluidas 10 pruebas focales.
- `test-support/care_plans/check.py` → pasó con filtros solos/combinados y páginas.
- `test_clinical_series.py` → **4 pruebas, OK**; `test-support/clinical_analytics/check.py` → pasó con páginas 1/2/3 y total.
- Exportador y `--check` → **113 rutas, 176 esquemas, 104 acciones; correcto**.
- Suite completa → **260 pruebas, OK**, 71,261 s; `uv build --offline` y `git diff --check` → correctos.

C17 queda pendiente de revisión y aceptación del usuario. Consumidores y producción no están acreditados.

## Evidencia de C06 · Captura clínica y trazabilidad de contratos

**T15.** La captura reconoce las referencias de medicación, cuidados, informes, adjuntos y especialidad. `ReportAttachmentResponse` añade `patientId` desde la fila para que esas referencias sean utilizables; la historia excluye el duplicado al construirse. Una ficha inactiva requerida por un adjunto queda incluida y el filtro por audiencia se conserva.

**T16.** `sourceHead` usa el último commit que toca `src`, `pyproject.toml`, `uv.lock` o el exportador; un commit ajeno no la cambia. `sourceSha256` conserva la huella del contenido actual. No se crearon commits para probarlo: el probe verificó la selección con una salida ficticia de Git y la misma huella de contenido.

**Comprobaciones.**

- Secuencia `downloads`, `medications`, `care_plans`, `diagnostic_results` → los tres primeros pasaron; el último detectó primero la falta de `patientId` en adjuntos y después el duplicado en su historia. Tras ambas correcciones pasó, incluida la ficha inactiva requerida.
- Dos exportaciones y `./.venv/Scripts/python.exe -m scripts.export_contracts --check` → **113 rutas, 176 esquemas, 104 acciones; reproducibles y correctos**.
- `./.venv/Scripts/python.exe test-support/contracts/check.py` → pasó con referencias locales, ejemplos, acceso, sync y la selección ficticia de `sourceHead`.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **260 pruebas, OK**, 77,174 s.
- `uv build --offline` y `git diff --check` → correctos.

**Límites.** No se creó un commit ajeno real; esa condición se comprobó mediante el doble documentado. Consumidores y producción quedan fuera. C06 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C05 · Límites HTTP e historia clínica

**T12.** Se adoptó `RequestBodyLimitMiddleware` de Starlette **1.9.0**, que usa `Content-Length` cuando es posible y siempre cuenta los bytes recibidos. Se retiró la dependencia tardía de las rutas y se conservó el tope de 64 KiB por operación. `correlate_request` mantiene `ApiError`, 413 y cabeceras. Fuente oficial: [Starlette RequestBodyLimitMiddleware](https://www.starlette.dev/middleware/#requestbodylimitmiddleware).

**T13.** La ruta de resultados acepta `page`, `shows` y `recordStatus`; el DAO filtra y cuenta antes de `LIMIT/OFFSET`, con orden por ID. La consulta completa de corrección/captura quedó separada. El contrato generado refleja los parámetros.

**T14.** Informes y registros de especialidad proyectan su versión actual al timeline en la aceptación. La migración `20261118_03` recupera el estado actual con las reglas de fecha del esquema; no reconstruye contenido clínico en el timeline.

**Comprobaciones.**

- `./.venv/Scripts/python.exe test-support/sync/check.py` y `python -m unittest discover -s tests -p test_operations.py -v` → pasaron; cuerpo grande y `Content-Length` subestimado reciben 413 con correlación y sin efectos. El primer intento mostró el límite fuera de correlación; se corrigió el orden del middleware y la repetición pasó.
- `./.venv/Scripts/python.exe test-support/diagnostic_results/check.py` → pasó con páginas 1/2/3, filtro de anulados y contrato comparado.
- Secuencia `clinical_history`, `diagnostic_results`, `specialty_templates` → **3/3 pasaron**, con versión actual, permiso por sección y recuperación de entradas desde la revisión previa.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **260 pruebas, OK**, 77,033 s.
- `./.venv/Scripts/python.exe -m scripts.export_contracts` y `--check` → **113 rutas, 176 esquemas, 104 acciones; correcto**.
- `uv build --offline` y `git diff --check` → correctos.

**Límites.** No se midió carga de producción ni se acreditan consumidores. C05 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C04 · Proyección analítica

**Cambios.** La migración `20261118_02` concede `USAGE` en el esquema `analytics` existente al rol de ejecución; se conserva la topología actual en el mismo PostgreSQL de prueba. ETL elimina puntos con `recordStatus=entered-in-error` y confirma el cursor con el efecto. Rebuild usa las mediciones vigentes expuestas por un caso de `clinical_records`, no el journal podado. ETL y rebuild comparten un bloqueo técnico global en esta etapa; antes de concurrencia de producción debe revisarse por cuenta.

**Comprobaciones.**

- `./.venv/Scripts/python.exe test-support/persistence/check.py` → migraciones, privilegios, rollback y escritores pasaron.
- `./.venv/Scripts/python.exe test-support/clinical_analytics/check.py` → pasó con el rol limitado, commits y observación desde otra conexión, invalidación sin punto, poda del journal y dos rebuilds concurrentes que conservaron el punto vigente. La primera preparación de poda falló por eventos diferidos pendientes al reactivar un trigger; el fixture los resolvió explícitamente y la repetición pasó.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **260 pruebas, OK**, 70,159 s.
- `./.venv/Scripts/python.exe -m scripts.export_contracts` y `--check` → **113 rutas, 176 esquemas, 104 acciones; correcto**. No cambió el contrato HTTP.
- `uv build --offline` → wheel y sdist correctos.
- `git diff --check` → sin errores.

**Límites.** No se acredita un almacén analítico separado ni concurrencia de producción. El bloqueo global es una decisión acotada para la implementación actual. C04 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C03 · Historial y entrega del adjunto

**Cambios T07.** La historia de informes conserva `attachmentId` por versión. `UploadReportAttachment.reportId` vincula el nuevo adjunto con un informe de la misma ficha, versiona ambos y registra sus historias/cambios en una aceptación. Lecturas y capturas proyectan `reportId` real. Las historias anteriores que no guardaron el vínculo no se reconstruyen por inferencia.

**Cambios T08.** Metadatos ya no cargan bytes. La descarga usa `storage_key`: conserva bucket S3 o ruta local registrada; las claves locales relativas antiguas siguen usando `STORAGE_ROOT`. Las altas locales nuevas guardan una ruta absoluta interna y escriben con reemplazo atómico. `Content-Disposition` usa `filename*` UTF-8 para Unicode y caracteres especiales.

**Comprobaciones.**

- `./.venv/Scripts/python.exe test-support/diagnostic_results/check.py` → pasó con vínculo en carga, historias antes/después de retirar, metadatos sin llamada a almacenamiento, captura con `reportId`, rollback de carga, reintento y descarga, cambio de `STORAGE_ROOT` y nombre Unicode.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **260 pruebas, OK**, 76,655 s.
- `./.venv/Scripts/python.exe -m scripts.export_contracts` y `--check` → **113 rutas, 176 esquemas, 104 acciones; correcto**. La forma de los modelos no cambió; se corrigió su contenido.
- `uv build --offline` → wheel y sdist correctos.
- `git diff --check` → sin errores.

**Límites.** Un rollback puede dejar bytes sin registro; no son accesibles y el reintento usa la misma clave. La limpieza de huérfanos no se añadió. S3 real no fue probado; el cierre del cliente S3 sigue en ME-14/T46. Consumidores y producción no están acreditados. C03 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C16 · Cierre conjunto de críticos

**Matriz verificada sin nuevos cambios de código.** CR-01 conserva cuenta/ficha en lectura, escritura y FK. CR-02 sustituye el conjunto completo y conserva historias. CR-03 versiona anulación/retiro. CR-04 conserva omisiones y proyecta historia. CR-05 valida los cuatro tipos. Todos conservan recibos, captura y delta en sus probes.

**Comandos y resultados.**

- Secuencia `diagnostic_results && specialty_templates && persistence && sync && downloads`, cada uno con `./.venv/Scripts/python.exe test-support/<nombre>/check.py` → **5/5 pasaron**, 60,646 s, con PostgreSQL/Keycloak Test, migraciones, rollback, carreras, captura y recuperación.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **260 pruebas, OK**, 79,250 s.
- `./.venv/Scripts/python.exe -m scripts.export_contracts --check` → **113 rutas, 176 esquemas, 104 acciones; correcto**.
- `uv build --offline` → wheel y sdist correctos.

**Datos y cierre clínico.** Las correcciones anteriores sin evidencia del conjunto o valor deseado permanecen para revisión clínica; no se repararon ni consultaron datos reales. Las comprobaciones afectadas de Etapa 3 se repitieron según la decisión de C01. C12 de `P-20261117-05-clinical-stage-3` fue revisado y aceptado por el usuario el 2026-11-18 después de esta pasada; sus límites se conservan.

**Límites.** No se acreditan consumidores Rust/Hub, S3 real, datos reales o producción. C16 queda pendiente de aceptación del usuario antes de retomar C03.

## Evidencia de C15 · Conservación y tipos en especialidad

**Cambios.** `UpdateSpecialtyRecord` construye el estado desde la versión actual cuando `values` está ausente; `values: null` conserva el efecto de proponer un conjunto vacío, que se rechaza si faltan obligatorios. La historia carga valores por versión. Una sola lectura de la plantilla valida claves, duplicados, obligatorios y `field_kind` en alta y edición.

**Datos anteriores.** El fixture reversible creó un valor incompatible y una versión sin valores. La consulta por versión de plantilla detectó el tipo incorrecto; la versión anterior conservó dos valores recuperables. El rollback retiró el fixture. No hay reparación automática: los casos reales requieren evidencia y revisión clínica; no se consultaron datos reales.

**Comprobaciones.**

- `./.venv/Scripts/python.exe test-support/specialty_templates/check.py` → pasó con omisión, `null`, historia por versión, cuatro tipos, alta/edición inválida sin nueva versión, captura y sync. La primera expectativa de vaciado con un obligatorio falló y se corrigió para exigir `VALIDATION_ERROR` y conservación; no se ocultó el caso.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **260 pruebas, OK**, 79,285 s.
- `./.venv/Scripts/python.exe -m scripts.export_contracts` y `--check` → **113 rutas, 176 esquemas, 104 acciones; correcto**. No cambió la forma pública.
- `uv build --offline` → wheel y sdist correctos.
- `git diff --check` → sin errores.

**Límites.** CR-04/CR-05 tienen corrección comprobada en datos ficticios. La recuperación de estados históricos no prueba el valor clínico deseado. Consumidores, datos reales y producción quedan fuera. C15 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C14 · Transiciones de especialidad

**Cambios.** `InvalidateSpecialtyRecord` incrementa la versión y copia los valores a esa versión antes de formar la historia. `RetireSpecialtyTemplate` incrementa la versión y conserva los campos de la versión anterior. Ambos usan la transacción y los DAOs existentes, sin migración ni cambio de esquema JSON.

**Comprobaciones con PostgreSQL Test y rol de ejecución.**

- `./.venv/Scripts/python.exe test-support/specialty_templates/check.py` → pasó tras las dos correcciones. Anulación: rollback forzado, reintento, duplicado, versiones 1/2/3, valores copiados, retiro de vigentes y cambio en sync. Retiro: rollback, reintento, duplicado, versiones 1/2/3 con campos 2/3/3, lectura de registros previos y rechazo 404 de nuevas capturas.
- La primera ejecución del retiro falló porque la aserción anterior esperaba la plantilla en una captura posterior al retiro. Se corrigió la prueba para comprobar el registro presente; la inclusión de versiones retiradas necesarias para interpretar capturas sigue asignada a ME-13/T45.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **260 pruebas, OK**, 71,501 s.
- `./.venv/Scripts/python.exe -m scripts.export_contracts` y `--check` → **113 rutas, 176 esquemas HTTP, 104 acciones; correcto**. Solo cambió la procedencia de fuentes en esta pasada.
- `uv build --offline` → wheel y sdist correctos.
- `git diff --check` → sin errores.

**Límites.** No se modificaron datos anteriores ni se acreditan consumidores o producción. T36/T37 están Done; C14 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C13 · Corrección clínica de informes

**Contrato decidido en T33.** El usuario aprobó que `CorrectDiagnosticReport` reciba `results` con el conjunto vigente completo. Cada elemento lleva `resultId` y campos tipados; IDs duplicados son inválidos. El payload anterior que solo contiene `correctionReason` recibe `VALIDATION_ERROR`, incluso cuando el conjunto requerido es vacío. La regla quedó en `docs/api-v1.md`, los modelos de dominio y los artefactos generados.

**Implementación T34.** La aceptación existente versiona el informe, actualiza resultados identificados, crea los nuevos y anula los omitidos. Cada efecto tiene historia y cambio en el mismo grupo/transacción. No se añadió otra transacción ni una segunda validación del payload. Los helpers nuevos tienen 34 y 65 líneas físicas.

**Datos anteriores T35.** Un fixture PostgreSQL representó una corrección anterior incompleta: el resultado original permanece recuperable en su historia, pero no existe evidencia del conjunto corregido que permita reconstruirlo. El candidato queda identificado para revisión clínica; no se infieren ni reescriben valores. No se consultaron datos reales y no se afirma que una instalación carezca de casos por esta prueba.

**Comprobaciones.**

- `./.venv/Scripts/python.exe -m unittest tests.test_diagnostic_results -v` → **5 pruebas, OK**; cubre payload antiguo, conjunto vacío, IDs y contenido tipado.
- `./.venv/Scripts/python.exe test-support/diagnostic_results/check.py` → pasó con payload antiguo rechazado, rollback forzado, reintento idéntico, duplicado, alta/actualización/anulación, lectura, captura y delta. El grupo de corrección contiene informe, resultado actualizado, nuevo y retirado.
- `./.venv/Scripts/python.exe test-support/downloads/check.py` → pasó con capturas coherentes, grupos completos y recuperación.
- `./.venv/Scripts/python.exe -m scripts.export_contracts` y `--check` → **113 rutas, 176 esquemas HTTP y 104 acciones; comprobación correcta**.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **260 pruebas, OK**, 67,365 s.
- `uv build --offline` → wheel y sdist correctos.
- `git diff --check` → sin errores.

**Límites.** E18 distingue corrección del informe y de un resultado. La compatibilidad antigua es un rechazo explícito, no una aceptación. Datos reales, consumidores Rust/Hub, S3 real y producción no están acreditados. C13 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C02 · Integridad y alcance de adjuntos

**Cambios.** `report_cases.py` valida la ficha antes de auditar/leer un adjunto y reutiliza una guarda de cuenta, ficha y estado en alta y edición. Las dos rutas pasan `patient_id`. La migración `20261118_01_report_attachment_scope.py` cuenta referencias ausentes/cruzadas y añade una FK compuesta `(account_id,attachment_id,patient_id)`; no repara ni reescribe datos por inferencia. El probe cubre dos fichas, adjunto inexistente o anulado, metadatos, contenido, alta, edición, retiro con `null` y SQL directo.

**Comprobaciones con datos ficticios.**

- `./.venv/Scripts/python.exe test-support/diagnostic_results/check.py` → pasó en T04, T05 y T06. En T06 comprobó rechazo SQL `23503`, downgrade a `20261117_07`, upgrade rechazado con un vínculo previo cruzado (`cross_scope=1`) y upgrade correcto tras retirar explícitamente ese vínculo del fixture.
- `./.venv/Scripts/python.exe test-support/clinical_permissions/check.py` → pasó, incluidas carreras de autorización, captura, recibos y revocación.
- `./.venv/Scripts/python.exe test-support/persistence/check.py` → pasó: migraciones up/down/reapply, rollback de revisión fallida, DDL denegado y dos escritores coordinados.
- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **259 pruebas, OK**, 77,534 s.
- `./.venv/Scripts/python.exe -m scripts.export_contracts --check` → falló en `openapi.json` por metadatos de origen. La regeneración temporal mostró diferencias solo en `sourceHead` y `sourceSha256`; al excluir esos campos de procedencia, los cinco documentos coinciden. No se editaron artefactos publicados ni se corrigió MN-02 en este bloque. Los archivos temporales se retiraron.
- `git diff --check` → sin errores.

**Límites y revisión.** La corrección conserva el contrato JSON y cambia a 404 la lectura con otra ficha. No acredita consumidores Rust/Hub, S3 real, datos reales o producción. T04–T06 están Done; C02 queda pendiente de revisión y aceptación del usuario.

## Evidencia de C01 · Revisión completada para decisión

**Cobertura manual actual.** Se recorrieron los archivos con implementación desde HTTP hasta SQL, incluidos dominio, aplicación, infraestructura, repositorio y captura. Los `__init__.py` vacíos quedaron inventariados como tales.

| Alcance | Cobertura por archivo | Comprobación |
|---|---|---|
| T02 · `authorization`, `accounts`, `sync`, `audit` | 41 archivos, 8.386 líneas; credenciales, permisos, recibos, carreras, journal, captura, retención y SSE | Probes `access`, `sync`, `downloads`, `retention`, `events` |
| T03 · agenda, servicios, citas, pacientes y once componentes clínicos/analíticos | 140 archivos: 115 con contenido y 25 iniciales vacíos; 21.730 líneas | Probes `persistence`, `appointments`, `patients`, `clinical_history`, `diagnostic_results`, `specialty_templates`, `clinical_analytics` |
| Persistencia y pruebas del bloque | 40 archivos de migraciones/soporte Alembic, 13 pruebas focales y 13 probes; 4.053, 1.515 y 3.649 líneas respectivamente | Suite completa y probes con PostgreSQL/Keycloak Test |

CR-01 a CR-05 se confirmaron de nuevo en el árbol actual. Conservan sus efectos y tareas: CR-01 → C02; CR-02 → C13; CR-03 → C14; CR-04/CR-05 → C15. La lectura añadió [ME-15](review.md#medianos-nuevos), una respuesta incorrecta de permisos que no altera la autorización ejecutada. Su prueba propuesta cubre las doce secciones y sus tres niveles contra la fila guardada.

**Comandos y resultados.**

- `./.venv/Scripts/python.exe -m unittest discover -s tests -v` → **259 pruebas, OK**, 68,187 s.
- Primera secuencia de probes → no ejecutó casos: PostgreSQL Test estaba detenido y `access` recibió `ConnectionRefusedError`. Se inició con `powershell.exe -NoProfile -File ./test-support/postgres.ps1 -Action Start -Mode Test`; el script confirmó `127.0.0.1:55433` y el perfil Test.
- Secuencia `access && sync && downloads && retention && events && persistence && appointments && patients && clinical_history && diagnostic_results && specialty_templates && clinical_analytics`, cada uno mediante `./.venv/Scripts/python.exe test-support/<nombre>/check.py` → **12/12 pasaron**, 134,328 s. Cubrieron migraciones, rollback, bloqueos, dos procesos SSE, recibos, captura, retención y los recorridos clínicos con datos ficticios; cada base aleatoria se eliminó al salir.
- Caso focal de ME-15 con el caso de uso real y dobles de acceso/persistencia → una fila con todas las secciones en `none` devolvió `notes`, `diagnosticReports` y `specialtyTemplates` como `read_write`. La prueba no usa PostgreSQL ni acredita el contrato HTTP completo; el código y el esquema sí muestran el origen del error.

**Decisiones aceptadas para C01.** El usuario aceptó C01 el 2026-11-18. Las correcciones compartidas repiten las comprobaciones clínicas afectadas antes de C12 de `P-20261117-05-clinical-stage-3`, que permanece sin cambios y sin aceptación. ME-15 se añadió como T71 en C19, sin adelantarla a los críticos.

**Límites.** Estas pruebas no corrigen los hallazgos, no acreditan consumidores Rust/Hub, S3 real, datos reales ni producción. Las reparaciones y sus contratos se verifican en sus bloques.

## Evidencia de T01

[Revisión inicial y línea base](review.md). La revisión se hizo sin diffs de Git. Solo se editaron archivos del plan e índice de tareas.

## Evidencia de la segunda revisión de críticos

Pasada estática de 351 archivos Python y comprobación manual de los recorridos de riesgo indicados en el [informe](review.md#cobertura-y-verificación-de-críticos). PostgreSQL Test y HTTP confirmaron CR-02 a CR-05 con datos ficticios. Pasaron 14 pruebas existentes de informes y especialidad. La lectura manual exhaustiva de T02/T03 se completó después y figura en la evidencia de C01. Las tareas de corrección siguen pendientes de ejecución.

## Evidencia de la tercera revisión

[Hallazgos medianos y menores](review.md#tercera-revisión--medianos-y-menores). Cinco comprobaciones focales con datos ficticios confirmaron el error en el endpoint de operaciones, los filtros omitidos, la paginación ignorada, la versión de plantilla ausente y el error latente de LMS. Pasaron 19 pruebas existentes de planes, series y crecimiento. Quedan pendientes las pruebas reales de S3, carga y datos en PostgreSQL para esta etapa.

## Evidencia de la cuarta revisión

[Hallazgos de simplificación y línea base](review.md#cuarta-revisión--código-que-se-puede-simplificar). Se comprobaron referencias de funciones y tipos, coincidencias sintácticas de cuerpos y conteos de llamadas al catálogo. Pasaron 21 pruebas de políticas, estructura de autorización, estructura general y descarga. Los recuentos de consultas en PostgreSQL y la validación de los refactores quedan en sus tareas.

## Evidencia de la quinta revisión

[Hallazgos de reutilización, variables y constantes](review.md#quinta-revisión--reutilización-variables-y-constantes). Inventario sintáctico de 351 archivos Python, con seguimiento manual de las familias documentadas. Los casos locales con datos ficticios confirmaron la huella de RG-10, las fechas parciales de RG-07 y la equivalencia entre día incluido y límite exclusivo de RG-04. Pasaron 38 pruebas de `unittest` en `test_patients.py`, `test_care_plans.py`, `test_declared_medications.py`, `test_clinical_series.py`, `test_downloads.py` y las clases `OperationSchemaTests` y `SyncModelTests` de `test_operations.py`. Las tareas añadidas quedan en Todo y las pruebas con servicios y consumidores quedan en su checkpoint.
