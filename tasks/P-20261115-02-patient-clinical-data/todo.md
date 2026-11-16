# Estado y evidencia: P-20261115-02-patient-clinical-data

**Estado del plan:** In progress. **Fecha:** 2026-11-15. **Plan:** [plan.md](plan.md).

El usuario solicitó primero guardar el plan y esta lista tras la planificación conversada. Después aprobó el plan y autorizó T01 → T02 → T03, en secuencia y sin delegación, hasta C01. No autorizó T04, aceptación de checkpoints ni inicio de etapa 2. Esta autorización no acepta C11 del núcleo ni revisiones de los encargos documentales anteriores. La creación inicial de estos documentos no completó T01; su alcance incluye integrar las decisiones en las fuentes indicadas en el plan.

## Tareas

| ID | Tarea | Dependencia para iniciar | Estado | Evidencia |
|---|---|---|---|---|
| T01 | Registrar acuerdos y preparar ejecución | Aprobación del plan | Done | Autorización y concreciones integradas; comprobación documental correcta |
| T02 | Definir datos y contratos | T01 | Done | Diseño físico/HTTP, permisos y referencias comprobados documentalmente |
| T03 | Registrar línea base y casos | T02 | Done | Línea base real, fallos previos/nuevos separados y casos ficticios preparados |
| T04 | Preparar permisos y filtrado cerrado | T03 y C01 aceptado | Done | 10 pruebas enfocadas y 48 controles de estructura correctos; filtrado antes de proyecciones |
| T05 | Configurar acceso por asistente | T04 | Done | Acción y lecturas conectadas; pruebas unitarias/estructura y contratos en memoria correctos |
| T06 | Comprobar permisos y revocación | T05 | Done | Probe clínico y persistencia PostgreSQL correctos; carreras, rollback y revocación comprobados |
| T07 | Persistir perfil e historia | T06 y C02 aceptado | Done | SQL offline y 53 controles de estructura correctos; tablas/DAOs listos para casos |
| T08 | Registrar y consultar perfil | T07 | Done | Acción/lecturas conectadas; contrato en memoria y 53 controles correctos |
| T09 | Comprobar perfil y nacimiento | T08 | Done | Probe integral y persistencia correctos; aislamiento, edad, rollback e historia comprobados |
| T10 | Persistir condiciones y revisiones | T09 y C03 aceptado | Done | Fechas parciales, tablas/DAOs y 53 controles correctos |
| T11 | Registrar y consultar condiciones | T10 | Done | Cuatro acciones y cinco lecturas; 55 rutas/91 esquemas y estructura correctos |
| T12 | Comprobar estados y carreras | T11 | Done | Probe integral correcto; estados, carrera alta/ausencia y rollback comprobados |
| T13 | Persistir alergias e intolerancias | T12 y C04 aceptado | Done | Tablas/DAOs, tipos y estructura correctos |
| T14 | Registrar y consultar alergias | T13 | Done | Acciones y cinco lecturas; 60 rutas/98 esquemas y estructura correctos |
| T15 | Comprobar alergias y aislamiento de secciones | T14 | Done | Probe integral correcto; tipos, secciones, carreras y rollback comprobados |
| T16 | Descargar estado clínico autorizado | T15 y C05 aceptado | Done | Captura/delta por sección, época, auditoría y rollback comprobados |
| T17 | Publicar contratos de revisión | T16 | Done | 60 rutas/98 esquemas/51 acciones generadas y ejemplos reales correctos |
| T18 | Comprobar y entregar etapa 1 | T17 | Done | Suite, todos los probes, analizador y build completos; C06 pendiente de revisión |

Los propietarios, entradas, datos/contratos, límites de transacción, efecto en sync/consumidores y criterios de cada tarea se mantienen en el plan. Esta es la única lista de ejecución de la etapa; no se duplica en la especificación.

## Checkpoints

- [x] C01 — Diseño y contrato: aceptado por el usuario el 2026-11-15; autoriza T04 → T05 → T06 hasta C02.
- [x] C02 — Permisos clínicos: aceptado por el usuario el 2026-11-15; autoriza T07 → T08 → T09 hasta C03.
- [x] C03 — Perfil y nacimiento: aceptado por el usuario el 2026-11-15; autoriza T10 → T11 → T12 hasta C04.
- [x] C04 — Condiciones: aceptado por el usuario el 2026-11-16; autoriza T13 → T14 → T15 hasta C05.
- [x] C05 — Alergias e intolerancias: aceptado por el usuario el 2026-11-16; autoriza T16 → T17 → T18 hasta C06.
- [ ] C06 — Etapa 1 completa: después de T18; detenerse sin iniciar etapa 2.

Solo el usuario acepta estos checkpoints. Se conservan sin cambios las revisiones pendientes de otros planes.

## Registro de ejecución

### T01 · Registrar acuerdos y preparar ejecución

El usuario aprobó el plan y autorizó T01 → T02 → T03, en secuencia y sin delegación, hasta C01. Se actualizaron plan.md, todo.md, tasks/README.md, docs/patient-clinical-record.md, docs/decisions.md y docs/nightingale-api.md. La especificación 0.2 registra las decisiones de etapa 1 y resuelve O01, O04–O06 y O14 solo para esa etapa, más la parte funcional de O15. Las etapas 2/3, operación con datos reales y revisiones anteriores conservan sus pendientes.

Comprobación documental con Python de biblioteca estándar: seis archivos revisados, enlaces nuevos presentes, formato y estados correctos, seis checkpoints sin aceptar. La primera ejecución detectó dos destinos ausentes ya conocidos (`nightingale-desktop-docs/README.md` y `contracts/README.md`); se repitió distinguiendo esos destinos previos y no apareció uno nuevo. `git diff --check` correcto. No se añadió código de producto, migraciones o generados ni se ejecutaron pruebas de producto. C01 permanece sin aceptar.

### T02 · Definir datos y contratos

Se actualizaron docs/database-schema.md §10, docs/api-v1.md §10, docs/access-design.md, docs/architecture.md, docs/contracts.md, docs/quality.md y docs/sources.md. El diseño contiene nueve tablas nuevas, cuatro columnas añadidas a tablas existentes, 37 tablas/420 columnas/81 FK como objetivo documental, nueve acciones y doce rutas clínicas nuevas. Define versiones/historias, fechas parciales, revisión de listas, aislamiento, permisos por sección, captura opcional del estado actual y auditoría sin contenido clínico. No se crearon migraciones, modelos, esquemas Pydantic o artefactos generados.

Referencias oficiales consultadas y enlazadas en docs/sources.md: PostgreSQL 18 constraints/constraint triggers, SQLAlchemy 2.1 transactions, Pydantic 2.14.1 validators, FastAPI response models y FHIR R5 Patient/Condition/AllergyIntolerance/date/List Empty Reasons. Versiones resueltas verificadas en manifiesto/lockfile: FastAPI 0.159.1, Pydantic 2.14.1, SQLAlchemy 2.1.6, Alembic 1.20.1 y asyncpg 0.32.0. Sin instalaciones o actualizaciones.

Comprobación cruzada con Python: nueve tablas, F57–F81, nueve acciones y doce rutas únicas; enlaces nuevos presentes y `git diff --check` correcto. Las primeras versiones del script exigieron recuentos o ausencia de espacios en todo el documento y fallaron por su propia cobertura/formato, no por pruebas de producto; se corrigieron el alcance del script y una numeración FK detectada durante la revisión. El resultado final es documental, no evidencia SQL o HTTP.

### T03 · Línea base y casos ficticios

Comandos ejecutados desde la raíz con el código actual y Python 3.15.1 del entorno existente. Versiones verificadas por importación: FastAPI 0.159.1, Pydantic 2.14.1, SQLAlchemy 2.1.6, Alembic 1.20.1 y asyncpg 0.32.0. Sin instalaciones, Docker, base personal, código de producto, migraciones nuevas o artefactos generados.

| Comprobación | Resultado real y clasificación |
|---|---|
| `./.venv/Scripts/python.exe -m unittest discover -s tests -v` | 144 pruebas en 74.372 s: 142 correctas y dos errores en `AvailabilityQuery.integer_duration` para `true` y `1.5`. Lanza `TypeError` en src/api/schedule/domain/schedule.py:383. **Fallo previo vigente**, ya documentado en el núcleo; no hubo cambios de código en este bloque. Los controles de estructura incluidos terminaron correctos. |
| `node C:/Users/Pedro/AppData/Local/Zed/languages/basedpyright/node_modules/basedpyright/index.js --pythonpath .venv/Scripts/python.exe --pythonversion 3.15 src --outputjson` | basedpyright 1.40.2: 125 archivos, **16 errores previos**, cero warnings, 11.475 s. Incluye límite de sentinel, código anterior y valkey ausente. No se añadieron supresiones ni dependencias; no es un análisis global correcto. |
| `./.venv/Scripts/python.exe -m alembic heads` e `history` | Una cadena con head `20261028_01`, desde `20261024_01`. |
| `./.venv/Scripts/python.exe -m alembic upgrade head --sql` | SQL offline generado correctamente, sin conexión ni archivo de salida conservado. |
| `./.venv/Scripts/python.exe test-support/persistence/check.py` | PostgreSQL Test 18.3 iniciado solo para la prueba. `check_migrations` completó upgrade/downgrade/reaplicación y fallo de revisión antes del fallo posterior. Después, `check_transactions` falló al comparar `ready(db)` con un dict antiguo: la función actual devuelve `ReadyResponse` con `notifications`. **Fallo previo del probe desactualizado tras SSE**, no una nueva restricción clínica. La base aleatoria se eliminó en `finally`; PostgreSQL Test se detuvo al terminar. No acredita la fase de transacciones posterior. |
| `./.venv/Scripts/python.exe -m scripts.export_contracts --check` | Primer fallo **nuevo de este bloque**: el exportador leyó las doce rutas futuras de §10 como actuales. Se marcaron `GET futuro`, sin cambiar su contrato. El segundo intento llegó hasta los artefactos y falló porque `contracts/api-v1/openapi.json` no existe, **límite previo del árbol**. No se regeneró. |
| Construcción de `scripts.export_contracts.documents()` en memoria | Correcta tras el ajuste: 46 rutas, 70 esquemas HTTP; rutas y acciones coinciden con el contrato actual. Cinco documentos construidos sin escribirlos. No acredita correspondencia con artefactos ausentes ni integración HTTP. |
| `git diff --check` | Correcto; solo advertencias de conversión LF/CRLF de Git en archivos previos. |

Las pruebas no usaron Keycloak porque el alcance de línea base no exigía un nuevo flujo OIDC. No se ejecutaron build, probes clínicos o consumidores: no existe implementación clínica y esas comprobaciones pertenecen a tareas posteriores. El probe de persistencia no se modificó para ocultar su fallo.

#### Casos ficticios preparados para T04–T18

Todos los nombres, sustancias y marcadores son inventados y no representan recomendaciones clínicas. `CND-A`, `ALG-A`, `MRK-SECRET` sirven para detectar filtraciones en errores, logs y auditoría; no deben aparecer allí.

| ID | Datos / recorrido | Resultado que se comprobará |
|---|---|---|
| CL-01 | Paciente `Paciente Ficticio A`, sin perfil | Sexo/fuente nulos y versión 0; lectura sin insertar fila |
| CL-02 | Sexo `unknown`, fuente `patient`; después nulo | `unknown` no equivale a ausente; corrección conserva versiones |
| CL-03 | Nacimiento `2000-02-29`, consulta `2026-02-28` y `2026-03-01` | Edad calculada; cumpleaños el 1 de marzo en año no bisiesto |
| CL-04 | Nacimiento nulo | Edad nula; alta administrativa sin datos clínicos |
| CL-05 | Condición `CND-A`, inicio `2024-02-29`, fin `2024-03` | Fecha válida y precisión conservada; sin día inventado |
| CL-06 | Inicios `2023-02-29`, `2024-02-30`, año/mes/día futuros | Rechazo de calendario o futuro inequívoco |
| CL-07 | Inicio `2024`, fin `2024-03`; inicio `2024-05`, fin `2024` | Primer orden indeterminado permitido; segundo fin inequívocamente anterior rechazado |
| CL-08 | Dos condiciones `CND-A` con IDs distintos | No fusionar ni rechazar por texto repetido |
| CL-09 | Condición `active/unconfirmed`, luego `resolved/confirmed` | Estados independientes, historia y resumen correctos |
| CL-10 | Anular condición y reintentar actualización | `entered-in-error` terminal; contenido anterior consultable |
| CL-11 | Alergia `ALG-A`, tipo `unknown`, reacción nula | Se admite tipo desconocido y datos opcionales |
| CL-12 | Sustancia `Sustancia Ficticia B`, tipo `intolerance` | No se convierte en alergia ni se clasifica gravedad automáticamente |
| CL-13 | Lista inicial, luego `not_asked`, `unknown`, `none_known` | Lista vacía no prueba ausencia; revisión con fuente/autor/instante |
| CL-14 | `none_known` y alta concurrentes | Solo un orden coherente; nunca ausencia conocida con registros pertinentes |
| CL-15 | Retirar último registro por `refuted` y por error | Nueva revisión `unknown`, no `none_known` automática |
| CL-16 | Asistente perfil=`none`, condiciones=`read`, alergias=`read_write` | Secciones independientes en lecturas, acciones, resultados y captura |
| CL-17 | Cambio de permisos con resultado previo y SSE abierto | Nueva versión/época; resultado reautorizado; captura/cursor anteriores inválidos |
| CL-18 | Misma identidad en cuentas A/B y IDs cruzados | 404 indistinguible; sin conteos, historias, errores o proyecciones ajenas |
| CL-19 | Misma operación dos veces y con `CND-A` alterado | Un efecto; duplicado autorizado o conflicto de huella; respuesta perdida recuperable |
| CL-20 | Captura sin clínica y con `includeClinical=true` | La primera conserva forma anterior; la segunda solo secciones legibles, estado actual y sin historias |
| CL-21 | Alergia anterior a la ventana de citas | Presente en captura clínica autorizada |
| CL-22 | Fallo al escribir historia, revisión, recibo, auditoría o journal | Rollback completo, sin versión o dato parcial |
| CL-23 | Patch vacío, ausencia, null y cambio equivalente | Reglas conservadas; `NO_CHANGES` sin nueva versión |
| CL-24 | Textos `CND-A`, `ALG-A`, `MRK-SECRET` en datos ficticios | Ausentes de auditoría, errores y logs; solo IDs/correlación permitidos |

### T04 · Preparar permisos y filtrado cerrado

C01 quedó aceptado por el usuario y se autorizó T04 → T05 → T06. Se añadieron `ClinicalPermissions` y niveles por sección al contexto de cuentas, `includeClinical=false`, alcance en cursores/capturas y audiencias clínicas cerradas. `read_changes` filtra antes de `SyncChange.model_validate`; cursores y capturas vuelven a comprobar subconjunto autorizado y época. Las respuestas anteriores conservan `clinicalSections=[]` por defecto y no se añadieron proyecciones clínicas.

Archivos: dominio/modelos/casos de accounts y sync, tests/test_clinical_permissions.py. Resultado: 10 pruebas enfocadas y 48 controles de estructura correctos. La primera carga detectó un default mutable de dataclass, corregido con `default_factory`; no quedó como fallo pendiente. basedpyright en accounts/sync conserva solo los dos diagnósticos previos `Err[Never]` y `__tablename__`.

### T05 · Configurar acceso por asistente

La revisión `20261115_01` añade tres niveles a pertenencias con `read_write` inicial, `clinical_sections` a capturas y audiencias clínicas en journal. `SetMemberClinicalPermissions` reutiliza la aceptación existente: propietario online, asistente/versionados, `NO_CHANGES`, idempotencia, pertenencia/época/recibo/auditoría/grupo en una transacción. Se añadieron acceso propio con niveles efectivos, consulta del propietario y catálogo/capacidades. Desactivar/reactivar conserva niveles y el propietario no puede retirarse acceso.

Archivos: migración nueva, dominio/modelos/DAOs/casos/rutas de accounts y sync, docs/api-v1.md. Resultado: 11 pruebas enfocadas, seis de operaciones y 48 de estructura correctas; OpenAPI en memoria 47 rutas/74 esquemas y acción presente. No se regeneraron artefactos ausentes.

### T06 · Comprobar permisos y revocación

Se añadió test-support/clinical_permissions/check.py. Con PostgreSQL 18.3 y Keycloak Test reales, el probe pasó: niveles iniciales, acceso propio/de propietario, configuración independiente, duplicado/contenido distinto, versión antigua, propietario/no propietario, conservación al desactivar/reactivar, carrera entre dos configuraciones, rollback temporal y recuperación desde otra instalación tras revocación. Solo bases aleatorias eliminadas al salir y datos ficticios.

`test-support/persistence/check.py` pasó completo: head real `20261115_01` y 29 tablas, upgrade/downgrade/reaplicación, revisión fallida sin DDL parcial, permisos de ejecución, rollback y dos escritores coordinados. Se actualizó el soporte para leer head y distinguir base disponible de listener no iniciado, sin ocultar esos fallos previos.

Durante el bloque se corrigieron: subconsulta no admitida en CHECK (función SQL inmutable), validación del payload de la nueva acción y expectativas del probe para fallo temporal y revocación local 403. El certificado Test se renovó solo en `.tmp` con SAN para 127.0.0.1; no se desactivó TLS ni se instaló confianza. Servicios detenidos al terminar.

Cierre: suite de 149 pruebas en 60.391 s, 147 correctas y los dos errores previos de `integer_duration` en agenda; 48 controles de estructura correctos. basedpyright completo: 125 archivos, mismos 16 errores previos, cero warnings. `uv build --offline --out-dir .tmp/c02-clinical-permissions/build` correcto. `git diff --check` correcto. Sin nuevas dependencias, commits, despliegues, consumidores o datos clínicos. C02 espera revisión del usuario y T07 no se inició.

### T07 · Persistir perfil e historia

C02 quedó aceptado y se autorizó T07 → T08 → T09. La revisión `20261115_02` crea `patient_clinical_profiles`, `patient_clinical_profile_histories` y `patient_birth_date_changes`, con FK por cuenta/paciente/autor/recibo, control diferido de versión/contenido y triggers append-only. Se añadieron modelos y DAOs de `clinical_records` y `patients`, y controles de estructura para el componente nuevo. SQL offline y 53 controles de estructura correctos. PostgreSQL detectó un `CHECK` ausente, corregido antes de continuar.

### T08 · Registrar y consultar perfil

Se implementó `SetPatientSexAtBirth`: valor/fuente, versión 0 inicial, `NO_CHANGES`, duplicados, historia por cambio y audiencia `clinical_profile`. Las lecturas actuales/historias usan permisos vigentes y registran solo IDs, acción y correlación. Perfil ausente devuelve versión 0 sin insertar. Edad usa nacimiento, fecha local de cuenta y la regla existente del 29 de febrero. `UpdatePatientProfile` conserva cambios de nacimiento con autor, operación, instante y versión de ficha, sin inventar historia previa.

Se añadieron rutas de perfil/historia y nacimiento, catálogo y proyección de sync. `patients` expone casos de uso para evitar imports de repositorios ajenos. Nueve pruebas enfocadas y 53 controles de estructura correctos; OpenAPI en memoria 50 rutas/81 esquemas. Se corrigió además la inserción de historia con clave compuesta usando `add`, sin alterar el DAO base.

### T09 · Comprobar perfil y nacimiento

`test-support/clinical_profile/check.py` pasó con PostgreSQL 18.3 y Keycloak Test: perfil ausente sin escritura, edad, sexo desconocido/nulo, duplicados, versiones, paginación/filtro de historia, rollback, dos cambios concurrentes, cambios de nacimiento, revocación de permiso, aislamiento, historia inmutable y auditoría sin contenido clínico. Se probaron también acceso ajeno 404 y recuperación de resultado solo con permiso vigente.

La revisión se aplicó, revirtió y reaplicó en `test-support/persistence/check.py`, junto con fallo sin DDL parcial, permisos, rollback y dos escritores. Las FK historia→recibo son diferidas para conservar efecto y recibo en una aceptación. Bases aleatorias eliminadas y servicios detenidos al terminar.

Cierre: 158 pruebas en 50.802 s, 156 correctas y los dos errores previos de agenda. Analizador completo: mismos 16 diagnósticos previos, cero warnings. `uv build --offline --out-dir .tmp/c03-clinical-profile/build` correcto. Sin nuevas dependencias, consumidores, commits o despliegues. C03 espera revisión; T10 no se inició.

### T10 · Persistir condiciones y revisiones

C03 quedó aceptado y se autorizó T10 → T11 → T12. La revisión `20261115_03` crea condiciones, historias y revisión de sección con control diferido de estado/contenido y coherencia entre registros pertinentes y `has_entries`. Se aplicaron `minimal-code`, `fastapi` y `docs-first-framework-code`: fechas parciales con biblioteca estándar, sin dependencias. Cuatro pruebas de dominio, 53 controles de estructura y SQL offline correctos.

### T11 · Registrar y consultar condiciones

Se conectaron `CreatePatientCondition`, `UpdatePatientCondition`, `InvalidatePatientCondition` y `SetPatientClinicalSectionReview`, con listas/detalle/historia de condiciones y revisión actual/historia. Las fechas validan calendario, futuro y orden determinable; `refuted` y anulación tienen efectos distintos y esta última es terminal. La coordinación por ficha conserva efecto, revisión derivada, historias, recibo, auditoría y journal juntos. Los resultados y lecturas reautorizan condiciones por separado.

Ocho pruebas enfocadas y 53 controles correctos; OpenAPI en memoria 55 rutas/91 esquemas. Se corrigieron proyecciones explícitas `id` → `conditionId` y la referencia del paciente al derivar revisión, sin ocultar el fallo inicial.

### T12 · Comprobar estados y carreras

`test-support/conditions/check.py` pasó con PostgreSQL 18.3 y Keycloak Test: estados iniciales, ausencia conocida, fechas completas/parciales/bisiestas/futuras, texto libre repetido, resolución/refutación, anulación terminal, filtros, historia, duplicados, rollback, permisos independientes y carrera entre alta y ausencia conocida. Solo persiste un orden coherente, sin `none_known` con registros pertinentes. Historias inmutables por permisos y triggers.

La migración se aplicó, revirtió y reaplicó en `test-support/persistence/check.py`, con revisión fallida sin DDL parcial, permisos, rollback y dos escritores. Bases aleatorias eliminadas y servicios detenidos. Cierre: 162 pruebas en 66.288 s, 160 correctas y los dos errores previos de agenda. basedpyright: 134 archivos, mismos 16 errores, cero warnings. `uv build --offline --out-dir .tmp/c04-conditions/build` correcto. Sin dependencias, commits o despliegues. C04 espera revisión y T13 no se inició.

### T13 · Persistir alergias e intolerancias

C04 quedó aceptado y se autorizó T13 → T14 → T15. La revisión `20261115_04` crea registros e historias de alergias/intolerancias, con tipo `allergy`, `intolerance` o `unknown`, estados, fechas parciales, fuente y control diferido. Se reutilizan revisión de sección, guarda append-only y aceptación existente. Tres pruebas de dominio, 53 controles de estructura y SQL offline correctos.

### T14 · Registrar y consultar alergias

Se conectaron altas, edición, anulación y revisión de alergias, con lista/detalle/historia y filtros por estado, verificación y tipo. La acción compartida de revisión selecciona condiciones o alergias por `payload.section`. Cada operación conserva registro, revisión derivada, historias, recibo, auditoría y journal juntos. Siete pruebas enfocadas y 53 controles correctos; OpenAPI en memoria 60 rutas/98 esquemas.

### T15 · Comprobar alergias y aislamiento de secciones

`test-support/allergies/check.py` pasó con PostgreSQL 18.3 y Keycloak Test: alergia, intolerancia y tipo desconocido; fechas parciales/bisiestas/futuras; estados, refutación y anulación terminal; filtros, duplicados, rollback, carrera alta/ausencia conocida, permisos independientes y acceso ajeno. Condiciones sigue legible con alergias=`none`. Historia inmutable comprobada.

Se corrigieron durante la revisión: guarda append-only limitada a historia (no al estado actual) y selección del caso de revisión por sección. La migración se aplicó, revirtió y reaplicó con revisión fallida sin DDL parcial. Una ejecución de persistencia se interrumpió al detener PostgreSQL durante su ejecución; se repitió completa correctamente. Servicios detenidos al final.

Cierre: 165 pruebas en 86.457 s, 163 correctas y los dos errores previos de agenda. basedpyright: 138 archivos, mismos 16 errores, cero warnings. `uv build --offline --out-dir .tmp/c05-allergies/build` correcto. Sin dependencias, commits o despliegues. C05 espera revisión y T16 no se inició.

### T16 · Descargar estado clínico autorizado

C05 quedó aceptado y se autorizó T16 → T17 → T18. Se implementó `snapshot_clinical`: perfil, condiciones, alergias y revisiones actuales por sección, sin historias. Captura y delta respetan permisos, época y grupos invisibles; condiciones/alergias no usan ventana de citas. Capturas y páginas clínicas registran auditoría sin nombres, sustancias o cuerpos y fallan con 503 si no puede conservarse. Se amplió `entity_key` para `patientId`+`section` y se concedió `EXECUTE` mínimo sobre la función de alcance.

`test-support/clinical_downloads/check.py` pasó: captura anterior sin clínica, captura completa, subconjunto de permisos, delta posterior, cambio de época, auditoría y rollback. SSE conserva el mecanismo existente de revalidación/cierre por época.

### T17 · Publicar contratos de revisión

`scripts.export_contracts` ahora publica `modelRevision=api-v1.2`, acepta `--output` dentro del repositorio y calcula recuentos reales. Se generaron `contracts/api-v1/*` y `contracts/examples.json`, con origen/huellas en `contracts/README.md` y guía Rust actualizada. Resultado: 60 rutas, 98 esquemas y 51 acciones por lote. Generación, `--check` y destino temporal explícito correctos; ejemplos HTTP reales con PostgreSQL/Keycloak correctos. No se editaron generados a mano.

### T18 · Comprobar y entregar etapa 1

Suite completa: 165 pruebas en 89.697 s, 163 correctas y los dos errores previos de `integer_duration` en agenda. Controles de estructura completos. basedpyright: 139 archivos, mismos 16 diagnósticos previos y cero warnings. `uv build --offline --out-dir .tmp/c06-stage1/build` produjo wheel y sdist correctos. `git diff --check` correcto.

Probes correctos en secuencia: access, accounts, sync, team, patients, services, schedule, appointments, persistence, downloads, retention, events, collaboration, clinical_permissions, clinical_profile, conditions, allergies, clinical_downloads y contracts. Se ajustaron fixtures temporales del probe de citas por el paso de fecha y una espera acotada de limpieza SSE, sin cambiar reglas de producto. Migraciones y reversión completas hasta `20261116_01`. Bases aleatorias eliminadas y servicios detenidos.

Límites: no hay integración Rust/Hub, datos reales, operación, saturación o despliegue acreditados. Los contratos están disponibles para una integración posterior. C06 espera revisión del usuario y la etapa 2 no se inicia.

Al ejecutar cada tarea posterior, registrar archivos afectados, comandos, resultados reales, fallos, límites y efecto en datos, permisos y consumidores. Las pruebas propuestas no cuentan como evidencia ejecutada.

## Comprobación de la creación documental

Comprobado el 2026-11-15 con un script temporal de biblioteca estándar, sin añadirlo al repositorio:

- Plan y lista contienen las mismas 18 tareas, con nombres coincidentes y sin huecos o duplicados; todas en Todo.
- Los seis checkpoints coinciden y permanecen sin aceptar. Plan y lista mantienen Draft.
- Los dos archivos nuevos y tasks/README.md tienen 25 enlaces locales y tres anclas comprobados, sin destinos ausentes ni anclas rotas.
- Archivos nuevos sin espacios finales y con salto de línea final; git diff --check correcto.

Solo se crean plan.md y todo.md de esta carpeta y se añade su enlace al índice de tareas. Se conserva el trabajo previo. No se ejecutan pruebas de producto, build, migraciones ni servicios; las referencias externas proceden de la consulta realizada durante la planificación. Este registro documental no acredita T01–T18 ni aceptación del usuario.
