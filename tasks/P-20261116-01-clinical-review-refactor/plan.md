# P-20261116-01-clinical-review-refactor: corrección y simplificación de Clinical Records Etapa 1

**Estado:** Completed. **Creado:** 2026-11-16. **Actualizado:** 2026-11-16. **Lista de tareas:** [todo.md](todo.md).

## Contexto

La revisión de `d548ae3...HEAD` encontró ocho desviaciones de la especificación, cuatro de estándares y dos bloqueos previos de verificación. El usuario pidió corregir todas las observaciones y refactorizar para reducir código duplicado, simplificar el despacho y hacer explícitas las conexiones entre componentes.

El resultado debe ser una Etapa 1 con autorización uniforme, estados clínicos coherentes, descargas completas y auditables, integridad física, contratos reproducibles y código sustancialmente más pequeño y legible.

El usuario eligió un plan sucesor. [P-20261115-02-patient-clinical-data](../P-20261115-02-patient-clinical-data/plan.md) permanece **In progress**, detenido en C06 y sin nuevas tareas. Este solapamiento queda expresamente autorizado. Al terminar este plan, el usuario volverá a C06 del plan anterior para revisarlo y, si corresponde, aceptarlo. Este plan no cierra ni acepta el anterior ni inicia la Etapa 2.

## Enfoque aprobado

Trabajar en secuencia y sin delegación: primero restaurar una base ejecutable, después corregir comportamiento, después refactorizar con las mismas pruebas y, al final, actualizar contratos y documentación. Cada tarea debe dejar el árbol funcional y terminar en un checkpoint para revisión del usuario.

Aplicar las skills locales de esta forma:

- `minimal-code`: recorrer cada flujo, corregir una sola causa compartida, reutilizar patrones existentes, preferir eliminación y no añadir dependencias ni capas arquitectónicas.
- `planning-task-breakdown`: conservar este ID, tareas pequeñas, dependencias, evidencia y checkpoints en este archivo y `todo.md`.
- `docs-first-framework-code`: antes de cambiar APIs de frameworks, contrastar las versiones fijadas y las fuentes oficiales ya identificadas: Pydantic 2.14.1, SQLAlchemy 2.1.6, Alembic 1.20.1, FastAPI 0.159.1 y PostgreSQL 18. No instalar ni actualizar paquetes.
- `code-review`: al cerrar, revisar el diff completo contra `f733271` en los ejes de especificación y estándares, sin delegar porque el trabajo aprobado es secuencial.

### Decisiones de diseño

- **Una política clínica para resultados:** una función tipada determina la sección de cada acción y exige `read_write` antes de leer recibos, devolver duplicados o recuperar resultados. Persistir `clinical_section` en `operation_receipts`; no separar la acción HTTP ni cambiar el contrato público.
- **Migración fail-closed:** rellenar secciones conocidas de recibos existentes. Para `SetPatientClinicalSectionReview`, usar `result_json.state.section` cuando exista. Un recibo histórico cuya sección no pueda determinarse queda sin alcance recuperable; no se adivina ni se concede acceso por defecto.
- **Una implementación de revisiones:** una sola lógica decide transiciones de `has_entries` y `unknown` a partir de la pertinencia anterior y posterior. Editar un registro que ya no era pertinente no crea una revisión ni altera `none_known`.
- **Simplificación dentro de la arquitectura actual:** como máximo, un módulo `access_cases.py` para acceso/auditoría y otro `entries_cases.py` para flujos compartidos de entradas y revisiones. Las diferencias clínicas permanecen en `conditions_cases.py` y `allergies_cases.py`. No crear una capa nueva, un bus de comandos, interfaces por acción ni modelos ORM genéricos anticipados.
- **Tipos explícitos:** usar uniones, `TypeVar`, callbacks y, solo donde ahorre duplicación real, un `Protocol` estructural para DAOs existentes. No usar `Any`, `cast` ni supresiones para hacer pasar el diseño.
- **Despacho explícito:** sustituir la cascada de `operations_cases.py` por una tabla pequeña y tipada que reutilice los catálogos de esquemas y casos existentes. Mantener bloqueos, orden de autorización y firmas; no crear otro sistema de comandos.
- **Integridad mínima:** declarar `ChangeLog.__tablename__ = "change_log"` para coincidir con la fuente física y evitar una migración de datos. Añadir una guarda SQL compartida que impida cambiar cuenta, ID o paciente de los registros clínicos actuales.
- **Reducción medible:** `src/api/clinical_records/application/` tiene 1.729 líneas. Objetivo: **950 o menos**, una reducción mínima del 45 % contando también los módulos nuevos. No comprimir sentencias, acortar nombres, eliminar validaciones ni sacrificar claridad para alcanzar la cifra. Si el objetivo exige una solución menos clara, detenerse en C06 para que el usuario decida; no reducir el alcance en silencio.

## Cambios clave y trazabilidad

| Observaciones | Corrección | Tareas |
|---|---|---|
| Duplicados tras revocación y revisión de alergias autorizada como condiciones | Alcance persistido, política común antes de recibos y pruebas de ambas direcciones de permisos | T04–T06 |
| Creación directa como `entered-in-error` | Rechazo en validadores de creación de condiciones y alergias | T07 |
| `none_known` perdido al editar registros refutados | Transición derivada solo al ganar o perder pertinencia | T08 |
| Historial de nacimiento sin `afterVersion` y orden incorrecto | `ClinicalHistoryQuery`, filtro y orden por `patient_version` | T09 |
| Captura clínica sin ficha de paciente inactivo/completo | Reunir referencias de citas y de todas las proyecciones clínicas antes de materializar pacientes | T10 |
| Delta/resultados sin auditoría de lectura | Evidencia sin contenido clínico y rollback si falla | T05 y T11 |
| Reasignación SQL de paciente | Guarda de identidad actual en perfil, condiciones y alergias | T12 |
| Código duplicado, cascadas y tipos incompletos | Helpers compartidos, despacho tabular, DAO común donde sea idéntico y anotaciones completas | T13–T16 |
| Metadatos de contratos antiguos y manifiesto sin HEAD | Añadir origen/HEAD/huella al manifiesto y regenerar artefactos | T17 |
| Documentación contradictoria o vacía | Actualizar estados, tablas y evidencia sin aceptar checkpoints por cuenta del agente | T18–T19 |
| `change_logs` inexistente y dos errores de agenda | Restaurar el nombre físico y devolver `ValueError` en validación | T02–T03 |

## Secuencia de tareas y checkpoints

### Fase 1 · Base verificable

**T01 · Registrar plan y línea base** — Documentación. Crear plan/todo del sucesor, enlazar el plan anterior pausado y registrar alcance, 1.729 líneas, fallos y métricas iniciales. Aceptación: trazabilidad completa y estados sin aceptaciones automáticas. Comprobación: enlaces, diff documental y comandos reproducibles.

**T02 · Restaurar aceptación transaccional** — `sync`. Declarar el nombre físico `change_log` en `src/api/sync/repository/models.py` y añadir una regresión de correspondencia ORM/esquema. Aceptación: alta de dispositivo, recibo, auditoría y journal vuelven a confirmarse juntos. Comprobación: `test-support/sync/check.py` y estructura.

**T03 · Corregir validación de duración** — `schedule`. Cambiar el `TypeError` de `integer_duration` por el error de validación documentado, sin tocar reglas de disponibilidad. Aceptación: `true` y `1.5` producen `ValidationError`/422. Comprobación: pruebas enfocadas de agenda y suite completa.

**C01 · Base ejecutable** — Suite sin los dos errores de agenda, probe real de sync correcto y revisión del usuario. No avanzar con base rota.

### Fase 2 · Autorización de resultados

**T04 · Persistir alcance y definir política común** — `sync`, `accounts`, `clinical_records`. Añadir migración/columna `clinical_section`, modelo y función tipada de autorización. Aceptación: acciones nuevas guardan su sección; recibos antiguos conocidos se migran y los ambiguos fallan cerrados. Comprobación: migración reversible y pruebas de matriz acción/sección/nivel.

**T05 · Aplicar política a duplicados y resultados** — `sync`. Usar la política antes de consultar/devolver recibos en lote y GET; auditar recuperaciones clínicas correctas sin contenido sensible. Aceptación: `read`/`none` no devuelve estados ni conflictos informativos de escritura y una lectura sin evidencia falla sin entregar datos. Comprobación: pruebas unitarias de duplicado, GET, sección compartida y rollback.

**T06 · Probar revocación y secciones independientes** — Calidad de acceso. Ampliar `test_clinical_permissions.py` y `test-support/clinical_permissions/check.py` para reintento por lote, GET y `SetPatientClinicalSectionReview` en ambas secciones. Aceptación: permisos cruzados, carrera de revocación y nuevo dispositivo se comportan igual en ambas rutas. Comprobación: PostgreSQL/Keycloak reales y carrera observada.

**C02 · Resultados autorizados** — Casos E22/E23 corregidos, pruebas de permisos y migración correctas; revisión del usuario.

### Fase 3 · Reglas clínicas e historial

**T07 · Impedir altas ya anuladas** — Dominio clínico. Rechazar `entered-in-error` en los dos payloads de creación; conservarlo en respuestas e invalidaciones. Aceptación: creación rechazada y anulación existente sin cambios. Comprobación: pruebas de esquema y operaciones reales para ambos tipos.

**T08 · Corregir transiciones de revisión** — Aplicación clínica. Calcular pertinencia antes/después y derivar solo al ganar el primer registro o perder el último. Aceptación: editar refutados conserva `none_known`; altas pertinentes y retirada del último mantienen historia y grupo coherentes. Comprobación: probes de condiciones/alergias y carrera alta/ausencia.

**T09 · Completar historial de nacimiento** — `patients`. Admitir `afterVersion`, filtrar y ordenar por `patient_version`. Aceptación: huecos administrativos permitidos, orden ascendente y filtros antes de contar/paginar. Comprobación: pruebas con cambios de nacimiento intercalados con otras ediciones.

**C03 · Reglas e historial coherentes** — Casos de creación, refutación, anulación y nacimiento correctos; revisión del usuario.

### Fase 4 · Descarga, auditoría e integridad

**T10 · Incluir referencias clínicas requeridas** — `sync` y `patients`. Reunir pacientes de citas y proyecciones clínicas antes de llamar a `snapshot_patients`. Aceptación: paciente inactivo/completo sin citas conserva ficha y datos clínicos vinculados; captura sin clínica no cambia. Comprobación: captura, páginas y total en `clinical_downloads`.

**T11 · Auditar delta clínico** — `sync`. Registrar lecturas de cambios con alcance clínico usando solo actor, dispositivo, cuenta, acción y correlación. Aceptación: lectura correcta deja evidencia; fallo de auditoría revierte y no entrega grupos. Comprobación: delta con/sin clínica, grupos invisibles y rollback real.

**T12 · Impedir reasignación de identidad clínica** — Migraciones. Añadir guarda SQL compartida para cuenta/ID/paciente en tablas actuales y probarla con el rol operativo. Aceptación: actualizaciones clínicas normales pasan; reasignación directa falla sin efecto; migración reversible. Comprobación: PostgreSQL real para perfil, condición y alergia.

**C04 · Descarga e integridad completas** — E01/E24, auditoría y guardas SQL correctos; revisión del usuario.

### Fase 5 · Refactorización y reducción

**T13 · Unificar acceso y lecturas clínicas** — `clinical_records`. Extraer acceso/auditoría a `access_cases.py` y reutilizar lecturas/paginación en perfil, condiciones y alergias. Aceptación: eliminar helpers paralelos, conservar respuestas y mantener tipos sin `Any`/`cast`. Comprobación: pruebas de lecturas, historia, permisos y contratos en memoria.

**T14 · Unificar revisiones de sección** — `clinical_records`. Concentrar en `entries_cases.py` la lectura, historia, confirmación y derivación de revisiones de condiciones/alergias. Aceptación: una sola implementación conserva las reglas corregidas y las audiencias. Comprobación: estados, versiones, carreras y sincronización de ambas secciones.

**C05 · Lecturas y revisiones simplificadas** — Comportamiento idéntico al de C04, duplicación retirada y revisión del usuario.

**T15 · Unificar escrituras y simplificar despacho** — `clinical_records` y `sync`. Reutilizar un flujo tipado para alta/edición/anulación y sustituir la cascada por despacho tabular basado en catálogos existentes. Aceptación: mismos efectos/versiones/grupos, menos ramas y conexiones explícitas. Comprobación: operaciones, idempotencia, rollback y huellas previas.

**T16 · Reducir DAO y cerrar calidad estructural** — Repositorio y aplicación clínica. Unificar solo métodos DAO idénticos, completar anotaciones y retirar código muerto detectado por referencias. Aceptación: `application/` ≤950 líneas y controles de estructura sin excepciones; ninguna compactación artificial. Comprobación: `wc -l`, estructura, basedpyright comparado y suite clínica.

**C06 · Refactorización comprobada** — Objetivo de líneas, legibilidad y comportamiento verificados; revisión del usuario antes de publicar contratos.

### Fase 6 · Contratos, documentación y cierre

**T17 · Hacer contratos reproducibles** — `scripts/export_contracts.py`, `contracts/README.md` y generados. Incluir `sourceHead`/`sourceSha256` en el manifiesto, conservar metadatos coherentes y regenerar desde la app real. Aceptación: dos generaciones iguales y `--check` correcto; ejemplos y referencias válidos. Comprobación: exportador y `test-support/contracts/check.py`.

**T18 · Actualizar fuentes de comportamiento y datos** — `docs/api-v1.md`, `database-schema.md`, `access-design.md`, `architecture.md` y `contracts.md`. Completar tablas vacías y reflejar alcance de recibos, auditoría, integridad y simplificación. Aceptación: una sola fuente por contrato y correspondencia exacta con el código. Comprobación: enlaces, rutas/acciones, FK y revisión de diff.

**T19 · Actualizar especificación y evidencia de ejecución** — `patient-clinical-record.md`, `tasks/README.md` y los archivos de los dos planes. Retirar estados antiguos y registrar el plan sucesor, las comprobaciones y los límites. Aceptación: C06 del plan anterior sigue pendiente y ninguna aceptación se atribuye al agente. Comprobación: estados, enlaces y consistencia entre plan/todo.

**C07 · Contratos y documentación revisados** — Exportación reproducible, fuentes coherentes y revisión del usuario.

**T20 · Ejecutar cierre integral** — Calidad y evidencia. Ejecutar suite, todos los probes, migraciones, contratos, build, analizador, medida de líneas y revisión final `f733271...HEAD`. Aceptación: resultados reales registrados y límites separados de lo comprobado. Comprobación: matriz completa y `git diff --check`.

**C08 · Corrección y refactorización listas para revisión** — El usuario revisa este plan sucesor. Después vuelve a C06 de `P-20261115-02-patient-clinical-data`; ninguno se marca aceptado automáticamente.

## Verificación

Comandos estándar, desde la raíz y con datos ficticios:

```bash
./.venv/Scripts/python.exe -m unittest discover -s tests -v
./.venv/Scripts/python.exe -m scripts.export_contracts --check
UV_CACHE_DIR=.uv-cache uv build --offline --out-dir .tmp/clinical-review/build
node C:/Users/Pedro/AppData/Local/Zed/languages/basedpyright/node_modules/basedpyright/index.js --pythonpath .venv/Scripts/python.exe --pythonversion 3.15 src --outputjson
wc -l src/api/clinical_records/application/*.py
git diff --check
```

Ejecutar con PostgreSQL Test y Keycloak Test los probes `access`, `accounts`, `sync`, `team`, `patients`, `services`, `schedule`, `appointments`, `persistence`, `downloads`, `retention`, `events`, `collaboration`, `clinical_permissions`, `clinical_profile`, `conditions`, `allergies`, `clinical_downloads` y `contracts`, mediante sus comandos documentados en `test-support/README.md`.

Los recorridos obligatorios incluyen: reintento idempotente después de cada cambio de permiso; revisión de alergias con condiciones=`none` y el caso inverso; alta directa como `entered-in-error`; edición de un refutado tras `none_known`; paciente inactivo/completo sin citas; delta sin auditoría disponible; reasignación SQL; historial de nacimiento con versiones no consecutivas; y comparación de huellas/respuestas antes y después de la refactorización.

El análisis estático debe comparar archivo, regla y mensaje con la línea base real. Los diagnósticos históricos ajenos —incluidos sentinels no soportados y `users`/Valkey heredados— no se ocultarán ni se convertirán en un objetivo artificial de “cero global”; los archivos tocados no pueden introducir diagnósticos nuevos. Su limpieza independiente no forma parte de las doce observaciones corregidas aquí.

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| La tabla de despacho o los helpers cambian comportamiento | Alto | Corregir primero, caracterizar huellas y ejecutar todos los probes después de cada bloque |
| Recibos antiguos sin sección recuperable | Alto | Backfill conocido y denegación cerrada de casos ambiguos; prueba de migración con datos ficticios |
| Los tipos genéricos fuerzan `Any` o supresiones | Medio | Usar uniones/callbacks/`Protocol` mínimo y basedpyright sin relajar configuración |
| La meta de líneas degrada legibilidad | Medio | Medir módulos nuevos, prohibir compactación y detenerse en C06 si el diseño claro no basta |
| Servicios o fallos históricos impiden pruebas | Alto | Corregir T02/T03 primero; no usar aliases, SQLite ni bases personales como sustitutos |

## Supuestos y límites

- Se incluyen los bloqueos `change_log` y agenda porque impiden comprobar la entrega; no se amplía la refactorización a módulos históricos no relacionados.
- No se cambian rutas, nombres de acciones, `contractVersion=1`, `modelRevision=api-v1.2` ni reglas clínicas salvo las correcciones listadas.
- No hay dependencias nuevas, commits, despliegues, cambios en Rust/Hub ni datos reales. No se inicia Etapa 2.
- La reducción de líneas es un requisito de diseño y medición, nunca una razón para borrar validaciones, historia, auditoría, errores o pruebas.
- Los checkpoints solo se aceptan por el usuario. La aprobación de este plan autorizó T01; cada checkpoint detiene el trabajo hasta nueva autorización.
