# P-20261116-02-clinical-routine: Etapa 2, registro clínico habitual

**Estado:** In progress. **Creado:** 2026-11-16. **Actualizado:** 2026-11-16. **Lista de tareas:** [todo.md](todo.md).

## 1. Contexto y autoridad

La Etapa 2 implementará atención clínica, notas, mediciones, vacunas, antecedentes, historial integrado y última visita en Nightingale API. La referencia funcional principal es [patient-clinical-record.md](../../docs/patient-clinical-record.md), especialmente §§4.2, 5, 7, 9–12.

Este plan conserva las fuentes únicas: `database-schema.md` para el modelo físico, `api-v1.md` para transporte y comportamiento HTTP, `access-design.md` para permisos, `architecture.md` para propietarios y `quality.md` para comprobaciones. No mantiene una segunda definición editable de los esquemas generados.

El plan es nuevo y no sustituye los planes de Etapa 1. [P-20261116-01-clinical-review-refactor](../P-20261116-01-clinical-review-refactor/plan.md) y [P-20261115-02-patient-clinical-data](../P-20261115-02-patient-clinical-data/plan.md) quedaron Completed con C08 y C06 aceptados el 2026-11-16. La aprobación de este diseño no autoriza por sí sola implementar código de Etapa 2: la primera tarea ejecutable requiere autorización expresa.

## 2. Decisiones de producto acordadas para este plan

| Pendiente | Decisión del usuario | Consecuencia de diseño |
|---|---|---|
| O02 | **Sin ciclo de cierre de atención.** Registrar una atención afirma que ocurrió. Puede existir sin cita y una cita puede tener varias atenciones | No hay estados `planned`, `in_progress` o `completed`; no hay firma/cierre. Solo anulación por error conserva una marca terminal distinta del ciclo asistencial |
| O02 / última visita | Es la última vez que paciente y profesional se vieron | Se calcula desde `occurred_at` de la última atención válida de la cuenta/paciente; no depende de citas, notas, aceptación remota ni estado de cierre |
| O03 | Mantener `serviceId` obligatorio al reservar | Etapa 2 no cambia disponibilidad, duración ni snapshots de citas. Una atención sin cita admite el motivo en palabras del paciente |
| O06 | Aplicar versiones y correcciones sin cierre universal | Atenciones/notas se editan con versión esperada; mediciones, vacunas y antecedentes distinguen nueva entrada, corrección y anulación; motivo de corrección opcional |
| O07 | Cinco mediciones iniciales | Peso, presión arterial, temperatura, saturación de oxígeno y frecuencia cardíaca. Talla, perímetro cefálico, frecuencia respiratoria, IMC y curvas quedan fuera |
| O08 | Datos opcionales de vacunas y antecedentes narrativos tipados | No exigir producto, lote, vía u otros detalles desconocidos; antecedentes `personal`, `family` u `other` sin crear condiciones automáticamente |
| O14 | Secciones independientes | Añadir atenciones, notas, mediciones, vacunas y antecedentes a los permisos por asistente. Historial filtra por la sección de cada fuente |
| O15 | Descargar hechos para evolución | Atenciones válidas, versión actual de notas/antecedentes, todas las tomas válidas y vacunas vigentes; sin versiones anteriores ni adjuntos |

Estas decisiones cierran los pendientes de Etapa 2 indicados. O04 conserva las fechas parciales solo para los tipos que las admiten aquí. O11 y la analítica/crecimiento permanecen en Etapa 3. La operación con datos reales y las políticas de copias/restauración siguen pendientes.

## 3. Resultado, trazabilidad y límites

### 3.1 Casos de aceptación cubiertos

- **E06:** registrar motivo con palabras del paciente sin cambiar la reserva actual ni exigir una cita para la atención.
- **E07:** guardar una nota con autor/fecha sin crear diagnóstico, condición u otro efecto clínico.
- **E08/E09:** conservar dos pesajes y corregir 700 a 70 kg sin conservar 700 como punto vigente.
- **E10/E11:** conservar fecha del hecho, captura local y aceptación remota; una carga histórica no desplaza una toma más reciente.
- **E12:** conservar presión con un componente desconocido sin inventar cero ni mezclar tomas.
- **E13:** registrar vacuna antigua declarada con fuente y precisión, sin afirmar administración actual.
- **E14:** calcular última visita desde atención válida, con alcance de cuenta explícito.
- **E22/E23:** impedir sobrescritura, efecto duplicado y lectura/recuperación tras revocación.
- **E24:** conservar datos clínicos anteriores a la ventana de citas y no borrar historia funcional al vencer cursores o recibos.

### 3.2 Exclusiones

No incluye medicación declarada, prescripción, tratamiento/planes, laboratorio, archivos, plantillas, especialidades, IMC, curvas OMS, analítica, recomendaciones de vacunas, calendarios, alertas, extracción automática, Portal/Hub, cambios en Rust ni operación con datos reales. Una nota o medición nunca crea una condición o diagnóstico por deducción.

## 4. Arquitectura y propiedad

| Componente | Responsabilidad |
|---|---|
| `encounters` | Atenciones reales, participantes limitados al ámbito actual, vínculo opcional con cita y última visita |
| `clinical_records` | Notas, mediciones, vacunas, antecedentes, historias y proyección de timeline; reutiliza acceso/auditoría y patrones de Etapa 1 |
| `accounts` | Nuevas secciones de permisos, valores iniciales, contexto y configuración por propietario |
| `patients` | Ficha, nacimiento, referencias cuenta/paciente y datos administrativos necesarios |
| `appointments` | Conserva reserva e historia; expone solo casos/tipos necesarios para validar el vínculo. No recibe contenido clínico |
| `sync` | Aceptación, alcance de recibos, journal, capturas, delta, cursores y recuperación |
| `audit` | Evidencia de escrituras y lecturas sin contenido clínico |

No se crea una capa nueva ni un bus genérico. Se reutilizan `access_cases.py`, `entries_cases.py`, DAO base, transacciones y guardas de identidad. Las reglas específicas de cada tipo permanecen en su dominio. No se importan repositorios ajenos entre componentes.

## 5. Diseño físico propuesto para revisión C01

Se proponen **once tablas nuevas**: estado actual e historia para atenciones, notas, mediciones, vacunas y antecedentes, más una proyección de timeline. No se crean filas clínicas vacías durante las migraciones.

### 5.1 Reglas comunes

- UUIDv7 para entidades nuevas; `account_id`/`patient_id` y FK compuestas a `account_patients` en todas las filas funcionales.
- Cuenta, paciente e ID son estables; aplicar la guarda de identidad existente a todas las tablas actuales. No reasignar registros entre pacientes.
- `record_status` usa `valid` o `entered-in-error` solo para distinguir uso ordinario de anulación por error. No representa cierre ni evolución clínica.
- Versiones desde 1, consecutivas por registro, igualdad entre estado actual e historia y control optimista. Anulación es terminal; una nueva afirmación usa otro ID.
- Historias append-only con contenido resultante, acción `created`/`updated`/`invalidated`, actor, operación e instante. El rol operativo recibe SELECT/INSERT, no UPDATE/DELETE/TRUNCATE.
- Efecto, historia, timeline cuando aplique, auditoría, recibo y grupo de sync comparten transacción. Proyecciones se validan antes del commit.
- Texto presente no vacío tras quitar espacios; ausencia conserva en patch, null solo en campos anulables y `NO_CHANGES` no crea versión.
- Autor procede del contexto autenticado. Fuente declarada no prueba veracidad ni autorización. No se aceptan actor, cuenta o instante técnico como autoridad del cliente.
- Fechas/horas finitas. Instantáneos usan offset explícito y se serializan UTC con Z. Fechas históricas parciales conservan `YYYY`, `YYYY-MM` o `YYYY-MM-DD` solo donde se indica.
- `captured_at_local` conserva la marca reportada por el dispositivo; `created_at`/`updated_at` conservan aceptación del servidor. Ninguno prueba permisos anteriores ni orden de commit.

### 5.2 `clinical_encounters` y `clinical_encounter_histories`

Una fila actual representa una atención que ocurrió; no existe una atención planificada por deducción de una cita.

| Grupo | Campos propuestos |
|---|---|
| Identidad y ámbito | `id`, `account_id`, `patient_id`, `appointment_id?`, `attending_professional_id`, `assistant_user_id?` |
| Tiempo | `occurred_at`, `ended_at?`, `captured_at_local?`, `created_at`, `updated_at` |
| Contenido | `reason?`, `reason_source_type=unknown`, `history_present_illness?`, `findings?`, `assessment?`, `indications?` |
| Cambios | `record_status=valid`, `correction_reason?`, `version`, `created_by_user_id`, `updated_by_user_id` |

Reglas:

- FK `(account_id,patient_id)` a ficha; `(account_id,attending_professional_id)` a `account_professionals`; asistente opcional a `account_memberships`.
- Para preservar paciente/cita, añadir UQ técnica `(account_id,id,patient_id)` a `appointments` y usar FK `(account_id,appointment_id,patient_id)` desde la atención. No hay UQ por cita: admite varias atenciones.
- `ended_at` no precede a `occurred_at`. No se exige contenido clínico para conservar que la visita ocurrió. No se escribe en `appointment_histories`.
- Completar, cancelar o marcar ausencia en una cita no crea una atención. Editar ficha o añadir nota tampoco cambia última visita.
- Correcciones pueden cambiar contenido y tiempo con nueva versión. Un vínculo erróneo de paciente/cita/profesional se resuelve por anulación y nuevo registro, no por reasignación silenciosa.

La historia conserva todo el contenido resultante y los metadatos de la operación. La última visita se consulta directamente de atenciones válidas, no de una columna editable ni de la historia de citas.

### 5.3 `patient_notes` y `patient_note_histories`

| Grupo | Campos propuestos |
|---|---|
| Identidad y contexto | `id`, `account_id`, `patient_id`, `encounter_id?` |
| Contenido y tiempo | `body`, `captured_at_local?`, `created_at`, `updated_at` |
| Cambios | `record_status`, `correction_reason?`, `version`, `created_by_user_id`, `updated_by_user_id` |

`body` es obligatorio. La FK `(account_id,encounter_id,patient_id)` impide vincular una nota con una atención de otro paciente. Una nota puede existir sin atención. No hay cierre, firma ni motivo obligatorio. La corrección conserva versiones y no cambia la última visita.

### 5.4 `patient_measurements` y `patient_measurement_histories`

| Grupo | Campos propuestos |
|---|---|
| Identidad y contexto | `id`, `account_id`, `patient_id`, `encounter_id?`, `kind` |
| Toma | `measured_at`, `captured_at_local?`, `created_at`, `updated_at`, `method?`, `body_site?` |
| Valores | `value?`, `systolic_value?`, `diastolic_value?`, `unit` |
| Cambios | `record_status`, `correction_reason?`, `version`, `created_by_user_id`, `updated_by_user_id` |

Tipos iniciales y forma cerrada:

| `kind` | Valor y unidad | Rango técnico de captura propuesto |
|---|---|---|
| `weight` | `value`, `kg` | 0,01–1000; admite el error ficticio 700 de E09 |
| `temperature` | `value`, `Cel` | 20–45 |
| `oxygen_saturation` | `value`, `%` | 0–100 |
| `heart_rate` | `value`, `/min` | 1–300 |
| `blood_pressure` | `systolic_value` y/o `diastolic_value`, `mm[Hg]` | 20–300 por componente presente |

Los rangos son límites de captura para revisión, no umbrales clínicos ni alertas. No se descartan valores por ser extremos dentro de ellos. Valores `numeric`/Decimal, sin NaN/infinito ni pérdida por formato regional. No se admiten unidades alternativas en esta entrega.

Para presión, al menos un componente es obligatorio y el otro puede ser nulo; `value` debe ser nulo. Para los demás tipos, `value` es obligatorio y ambos componentes deben ser nulos. Tipo, paciente y unidad no cambian por corrección. Cada toma nueva recibe otro ID.

La lectura histórica ordena por `(measured_at,id)` sin usar orden de carga. El resumen calcula el último valor por tipo solo con tomas válidas. La edad en una toma se deriva de nacimiento en la fecha local de `measured_at`, conserva en la respuesta `ageYears`, `ageAsOf` y la versión de ficha usada; no se persiste como otro dato. Si falta nacimiento, `ageYears` es nulo. No se calcula IMC ni percentil.

### 5.5 `patient_immunizations` y `patient_immunization_histories`

| Grupo | Campos propuestos |
|---|---|
| Identidad y contexto | `id`, `account_id`, `patient_id`, `encounter_id?` |
| Vacuna y fecha | `vaccine_name`, `occurrence_date` como fecha clínica parcial, `record_kind=unknown` |
| Fuente | `source_type=unknown`, `captured_at_local?` |
| Detalles opcionales | `product_name?`, `dose_description?`, `lot_number?`, `route?`, `body_site?`, `location_text?`, `administrator_name?` |
| Cambios | `record_status`, `correction_reason?`, autores, `version`, `created_at`, `updated_at` |

`record_kind` admite `administered_here`, `reported` o `unknown`. `administered_here` exige una atención válida de la misma ficha; una declaración externa no la usa. El autor autenticado se conserva aparte de `administrator_name`, que es texto declarado cuando proceda. No hay catálogo externo obligatorio, evaluación de esquema, recomendación o aviso.

### 5.6 `patient_antecedents` y `patient_antecedent_histories`

| Grupo | Campos propuestos |
|---|---|
| Identidad y contexto | `id`, `account_id`, `patient_id`, `encounter_id?`, `category` |
| Relato | `content`, `related_person_description?`, `occurrence_date?`, `source_type=unknown` |
| Cambios | `record_status`, `correction_reason?`, autores, `version`, `created_at`, `updated_at`, `captured_at_local?` |

`category` admite `personal`, `family` y `other`. `family` exige `related_person_description` para identificar en palabras a la persona relacionada; no atribuye su condición al paciente ni crea una condición. El relato permanece en texto, sin codificación o análisis automático. Fecha y fuente conservan incertidumbre.

### 5.7 `patient_clinical_timeline`

Proyección actual y reconstruible para el historial integrado; no es una segunda fuente editable ni contiene cuerpos clínicos.

Campos: `account_id`, `patient_id`, `entry_type`, `entry_id`, `source_section`, `occurred_at?`, `occurrence_date?`, `date_precision?`, `sort_key`, `accepted_at`, `entity_version`, `record_status`.

- PK `(account_id,patient_id,entry_type,entry_id)`; índice para historial `(account_id,patient_id,record_status,sort_key,entry_type,entry_id)` y otro por `source_section` cuando lo exija la consulta.
- Solo conserva referencias, fechas, versión y alcance. No guarda nombres, notas, sustancias ni valores.
- `sort_key` es técnico y permite orden estable sin completar una fecha parcial ni afirmar precisión desconocida. La respuesta conserva el valor original y `date_precision`.
- La escritura de cada fuente actualiza timeline en la misma aceptación. La proyección puede reconstruirse desde estados actuales; su pérdida no borra historia funcional.
- La migración de integración rellena condiciones/alergias existentes. Condiciones/alergias usan inicio conocido cuando existe y, en otro caso, la marca de la versión actual como tiempo de referencia, sin presentarlo como inicio clínico.
- Timeline no se descarga como entidad adicional: el escritorio puede derivarlo de los hechos sincronizados.

## 6. Contrato HTTP y operaciones propuestos

### 6.1 Escrituras

Se mantienen los lotes existentes y se añaden quince acciones:

| Área | Acciones |
|---|---|
| Atención | `CreatePatientEncounter`, `UpdatePatientEncounter`, `InvalidatePatientEncounter` |
| Notas | `CreatePatientNote`, `UpdatePatientNote`, `InvalidatePatientNote` |
| Mediciones | `RecordPatientMeasurement`, `CorrectPatientMeasurement`, `InvalidatePatientMeasurement` |
| Vacunas | `RecordPatientImmunization`, `UpdatePatientImmunization`, `InvalidatePatientImmunization` |
| Antecedentes | `CreatePatientAntecedent`, `UpdatePatientAntecedent`, `InvalidatePatientAntecedent` |

Todas usan UUID nuevo para crear, `expectedVersion=0`, control optimista para cambios, idempotencia y alcance persistido en el recibo. `SetMemberClinicalPermissions` conserva su acción y acepta las nuevas secciones; sus valores omitidos por un cliente anterior conservan el default `read_write` documentado.

Para atenciones y mediciones, el momento del hecho se resuelve en este orden: valor explícito del payload, `occurredAtLocal` de la envoltura como dato reportado, o reloj del servidor. Se conserva también la aceptación remota. Un instante futuro respecto del servidor se rechaza sin ajustarlo silenciosamente; un reloj desajustado no concede permisos. Vacunas/antecedentes usan fecha clínica parcial y no reciben una hora ficticia.

### 6.2 Lecturas

Todas bajo `/v1/accounts/{account_id}/patients/{patient_id}`, con token, dispositivo y permiso de sección:

- Atenciones: lista, detalle e historia; `GET .../last-visit` devuelve `encounterId`, `occurredAt` y `scope=account`, o nulos si no hay atención válida.
- Notas: lista, detalle e historia.
- Mediciones: lista con filtros por tipo/rango/estado, detalle, historia y resumen de últimos valores por tipo.
- Vacunas: lista, detalle e historia.
- Antecedentes: lista con categoría/estado, detalle e historia.
- `GET .../clinical-history`: página integrada de referencias actuales, fechas con precisión, tipo, versión y estado, filtrada por secciones permitidas antes de contar/paginar. Cada referencia permite consultar el detalle por su ruta autorizada.

Listas usan `page`/`shows`, `items`/`total`, filtros antes del conteo, orden estable y ausencia frente a null. Anulados no aparecen en vistas ordinarias salvo filtro explícito. Historias usan versión ascendente y `afterVersion`.

### 6.3 Compatibilidad

- `contractVersion=1`; publicar `modelRevision=api-v1.3` al cerrar Etapa 2.
- `includeClinical=false` conserva capturas sin clínica. Con `true`, incluye todas las secciones legibles de Etapas 1 y 2.
- Los contratos y ejemplos se generan desde la app real; no se editan manualmente. Los recuentos se calculan del catálogo, sin cifras fijas antiguas.

## 7. Permisos, auditoría y sincronización

### 7.1 Permisos

Añadir a `ClinicalSection`, `ClinicalPermissions` y `account_memberships` las secciones `encounters`, `notes`, `measurements`, `immunizations` y `antecedents`, cada una con `none`, `read` o `read_write`.

- Propietario conserva acceso completo; asistentes existentes/nuevos empiezan con `read_write` y solo el propietario reduce niveles online.
- `none` excluye lecturas, historias, resultados, resúmenes y descargas; `read` permite lecturas y excluye escrituras/reintentos; `read_write` permite ambos.
- `clinical_section` de recibos y los conjuntos de capturas/cursores/audiencias amplían sus conjuntos cerrados. Cambiar permisos incrementa pertenencia y época, invalida capturas/cursores y cierra SSE anterior.
- Última visita exige lectura de `encounters`. El historial no obtiene un permiso global: cada elemento se filtra por `source_section` y los detalles vuelven a autorizar su fuente.
- Una cuenta/paciente o registro ajeno devuelve la misma ausencia que uno inexistente, también en totales, resultados y errores.

### 7.2 Auditoría

Escrituras conservan la auditoría transaccional actual. Lecturas de recursos, historias, última visita, historial integrado, resultados, capturas, páginas y deltas clínicos registran actor, dispositivo, cuenta, objeto/sección, acción, resultado, correlación e instante. No registran motivos, texto clínico, valores, nombres, filtros de búsqueda, cuerpos ni cursores. Si la evidencia falla, no se entregan datos y se devuelve el fallo temporal común.

### 7.3 Descarga y delta

Captura clínica incluye:

- Todo lo ya definido en Etapa 1, sin cambiar su contrato.
- Atenciones válidas actuales y sus vínculos.
- Versión actual válida de notas y antecedentes.
- Todas las tomas válidas para evolución, no solo la última.
- Vacunas válidas actuales.
- Referencias administrativas necesarias, incluidos pacientes inactivos/completos y profesionales necesarios.

No incluye historias de versiones, timeline derivado ni adjuntos. Una anulación incremental publica el nuevo estado `entered-in-error` para que el consumidor lo retire de la vista ordinaria; una captura posterior no incluye esa entrada inválida. Los datos no se filtran por ventana de citas por depender de una atención.

La retención técnica de 90 días no borra datos ni historias clínicas. Cambiar permisos exige otra captura. No se promete borrado remoto de copias ya descargadas ni aplicación atómica en SQLite sin probar el consumidor.

## 8. Secuencia de trabajo y checkpoints

Trabajo secuencial, sin delegación. T01–T03 son documentación/diseño. Cada tarea registra propietario, entradas, datos/contratos, transacción, sync/consumidores, pruebas y evidencia en `todo.md`. Ninguna tarea crea archivos vacíos para una fase posterior.

### Fase 1 · Decisiones, diseño y línea base

**T01 · Registrar decisiones de Etapa 2** — Documentación. Integrar O02/O03/O06/O07/O08/O14/O15 en especificación/decisiones y crear plan/todo. Aceptación: alcance, exclusiones y estado de Etapa 1 sin contradicciones. Comprobación: enlaces, estados y `git diff --check`.

**T02 · Definir datos, contratos y acceso** — Documentación física/HTTP/sync. Incorporar once tablas, quince acciones, lecturas, permisos, timeline y descarga a sus fuentes. Aceptación: FK, nulabilidad, versiones, tiempos, rutas y filtros coherentes. Comprobación: revisión cruzada de columnas/referencias/acciones/rutas.

**T03 · Registrar línea base y casos ficticios** — Calidad. Capturar suite, estructura, analizador, migraciones y contratos; preparar casos E06–E14/E22–E24 y marcadores de privacidad. Aceptación: fallos previos separados y comandos reales. Comprobación: ejecución de línea base y revisión documental.

**C01 · Diseño de Etapa 2** — Revisión y aceptación expresa del usuario antes de código.

### Fase 2 · Permisos y filtrado cerrado

**T04 · Preparar secciones y migraciones de alcance** — `accounts`/`sync`. Ampliar pertenencias, recibos, capturas, cursores y audiencias; filtrado cerrado antes de interpretar proyecciones. Aceptación: clientes sin nueva sección no reciben datos; migración reversible. Comprobación: pruebas unitarias y PostgreSQL real.

**T05 · Conectar configuración y resultados** — `accounts`/`sync`. Inicializar asistentes, consultar/configurar niveles, ampliar acciones permitidas y reautorizar resultados por sección. Aceptación: época/recibo/auditoría/grupo atómicos y compatibilidad de payloads anteriores. Comprobación: casos propietario/asistente, duplicado y revocación.

**T06 · Comprobar aislamiento de permisos** — Calidad de acceso. Probar todas las nuevas secciones en lecturas, acciones, resultados, capturas y carreras. Aceptación: ninguna filtración por error, total, duplicado o delta. Comprobación: PostgreSQL/Keycloak reales y cambio de época.

**C02 · Permisos de Etapa 2** — Revisión del usuario antes de datos nuevos.

### Fase 3 · Atención y última visita

**T07 · Persistir atenciones y proyección inicial de timeline** — `encounters`/`clinical_records`. Implementar estado/historia, FK a cita/ficha/profesional, guardas y proyección de atenciones. Aceptación: atención sin cita, varias por cita, integridad y sin ciclo de cierre. Comprobación: migración, restricciones diferidas y SQL directo.

**T08 · Conectar atenciones y última visita** — Aplicación/infraestructura/sync. Implementar tres acciones, lista/detalle/historia y última visita por cuenta. Aceptación: autor, tiempo, versiones, resultado y auditoría correctos. Comprobación: recorridos HTTP y rollback.

**T09 · Comprobar atención y última visita** — Calidad. Probar citas canceladas/ausentes/futuras, notas sin atención, correcciones, anulación, empates y aislamiento. Aceptación: E06/E14 y ausencia de efectos automáticos en citas. Comprobación: PostgreSQL/Keycloak y carreras de edición.

**C03 · Atención clínica** — Revisión del usuario antes de notas.

### Fase 4 · Notas del paciente

**T10 · Persistir notas e historia** — `clinical_records`. Implementar cuerpo, autor, tiempo, vínculo opcional con atención, versiones y timeline. Aceptación: nota independiente o vinculada sin cruzar ficha. Comprobación: migración e inmutabilidad.

**T11 · Conectar notas** — Aplicación/infraestructura/sync. Implementar tres acciones y lecturas con auditoría. Aceptación: edición breve, `NO_CHANGES`, corrección y anulación sin cierre. Comprobación: HTTP, duplicados, respuesta perdida y rollback.

**T12 · Comprobar notas** — Calidad. Probar E07, permisos, aislamiento, texto sin diagnóstico automático y versión antigua. Aceptación: ningún efecto clínico derivado. Comprobación: PostgreSQL/Keycloak y privacidad de logs/auditoría.

**C04 · Notas** — Revisión del usuario antes de mediciones.

### Fase 5 · Mediciones y evolución

**T13 · Persistir mediciones e historia** — Dominio/`clinical_records`. Implementar cinco tipos, Decimal/UCUM, presión por componentes, tiempos, contexto y timeline. Aceptación: formas válidas, unidades fijas y sin valores inventados. Comprobación: dominio, migración y restricciones.

**T14 · Conectar tomas, correcciones y resúmenes** — Aplicación/infraestructura/sync. Implementar tres acciones, lista/detalle/historia, últimos valores y edad en la toma. Aceptación: nueva toma no sobrescribe; corrección conserva historia; reciente usa fecha del hecho. Comprobación: HTTP, duplicados, empates y rollback.

**T15 · Comprobar mediciones y trabajo offline** — Calidad. Probar E08–E12, 700→70, histórico cargado hoy, presión incompleta, captura/aceptación y revocación. Aceptación: serie válida y sin derivados de Etapa 3. Comprobación: PostgreSQL/Keycloak y carreras.

**C05 · Mediciones** — Revisión del usuario antes de vacunas.

### Fase 6 · Vacunas recibidas o declaradas

**T16 · Persistir vacunas e historia** — `clinical_records`. Implementar vacuna, fecha parcial, fuente, tipo de registro y detalles opcionales con timeline. Aceptación: administrada aquí frente a declarada, sin catálogo ni campos obligatorios desconocidos. Comprobación: migración, FK y calendario.

**T17 · Conectar vacunas** — Aplicación/infraestructura/sync. Implementar tres acciones y lecturas. Aceptación: `administered_here` exige atención válida; histórica conserva fecha/fuente y correcciones. Comprobación: HTTP, duplicados, respuesta perdida y rollback.

**T18 · Comprobar vacunas** — Calidad. Probar E13, precisión parcial, ausencia de recomendación/avisos, permisos y aislamiento. Aceptación: una declaración no prueba administración ni crea reacción/alergia. Comprobación: PostgreSQL/Keycloak y privacidad.

**C06 · Vacunas** — Revisión del usuario antes de antecedentes.

### Fase 7 · Antecedentes narrativos

**T19 · Persistir antecedentes e historia** — `clinical_records`. Implementar categorías, relato, persona relacionada, fecha/fuente y timeline. Aceptación: antecedente familiar no se atribuye al paciente ni crea condición. Comprobación: migración y reglas combinadas.

**T20 · Conectar antecedentes** — Aplicación/infraestructura/sync. Implementar tres acciones y lecturas con filtros. Aceptación: texto, fuente, corrección y anulación conservan contexto. Comprobación: HTTP, idempotencia y rollback.

**T21 · Comprobar antecedentes** — Calidad. Probar personales/familiares/otros, incertidumbre, permisos y aislamiento. Aceptación: ninguna codificación o efecto automático. Comprobación: PostgreSQL/Keycloak y marcadores de privacidad.

**C07 · Antecedentes** — Revisión del usuario antes de integrar historial.

### Fase 8 · Historial integrado y descarga

**T22 · Integrar Etapa 1 en timeline** — `clinical_records`. Actualizar condiciones/alergias y rellenar sus referencias actuales sin copiar contenido ni reescribir historias. Aceptación: backfill idempotente, versión actual y reconstrucción coherente. Comprobación: migración desde head anterior y comparación con estados existentes.

**T23 · Conectar historial integrado** — Aplicación/infraestructura. Leer timeline con filtros de sección, tipo, fecha/estado y paginación antes del total. Aceptación: solo fuentes permitidas, precisión visible y referencias resolubles. Comprobación: historial parcial por permisos, empates y rollback de auditoría.

**T24 · Completar captura y delta de Etapa 2** — `sync` y propietarios. Materializar hechos elegidos, referencias y cambios de corrección/anulación sin historias. Aceptación: E11/E24, grupos completos y filtrado antes de proyección. Comprobación: captura anterior/actual, permisos parciales, cambio de época y rollback.

**T25 · Comprobar historial y sincronización** — Calidad. Probar integración de todos los tipos, aislamiento, datos antiguos, grupos invisibles, SSE y recuperación. Aceptación: ninguna omisión o fuga por total/cursor/resultado. Comprobación: PostgreSQL/Keycloak, dos procesos cuando cambie SSE y probes de descarga.

**C08 · Historial y descarga** — Revisión del usuario antes de publicar contratos.

### Fase 9 · Contratos, documentación y cierre

**T26 · Publicar api-v1.3 y actualizar fuentes** — Contratos/documentación. Generar app/modelos reales, ejemplos, manifiesto y guías; actualizar especificación/esquema/acceso/calidad/tareas. Aceptación: exportación reproducible y correspondencia con rutas/acciones. Comprobación: `--check`, ejemplos HTTP, enlaces y diff.

**T27 · Ejecutar cierre integral de Etapa 2** — Calidad/evidencia. Suite completa, probes, migraciones, contratos, build, analizador y revisión contra el HEAD anterior al plan. Aceptación: E06–E14/E22–E24 comprobados y límites separados. Comprobación: matriz completa y `git diff --check`.

**C09 · Etapa 2 lista para revisión** — El usuario acepta o rechaza. No inicia Etapa 3 ni acredita consumidor/producción.

## 9. Matriz de pruebas obligatoria

| Área | Casos mínimos |
|---|---|
| Atención | Sin cita; varias por cita; cita de otro paciente/cuenta; cita cancelada/ausente no crea atención; ausencia de cierre; corrección/anulación; empate de última visita |
| Notas | Independiente/vinculada; texto vacío; edición sin motivo; ninguna condición derivada; nota no cambia última visita |
| Mediciones | Dos pesos; corrección 700→70; toma histórica; unidad/tipo/rango; presión sin un componente; empate por fecha; edad ausente/bisiesta; nueva toma frente a edición concurrente |
| Vacunas | Administrada aquí/declarada/desconocida; fecha año/mes/día; datos opcionales ausentes; corrección; sin recomendación o efecto automático |
| Antecedentes | Categorías; persona relacionada requerida en familia; fuente/fecha incierta; ninguna atribución al paciente |
| Historial | Todos los tipos; precisión parcial; orden estable; detalle autorizado; corrección/anulación; backfill de Etapa 1; filtros por sección antes de total/página |
| Acceso | Propietario/asistente con niveles combinados; miembro/cuenta/dispositivo revocado; lecturas/resultados/duplicados/capturas/deltas; objeto ajeno indistinguible |
| Transacción | Efecto/historia/timeline/recibo/auditoría/grupo juntos; fallo inmediato/diferido; respuesta perdida; nuevo dispositivo autorizado; versión antigua |
| Sync | Captura sin clínica y con clínica; hechos históricos; corrección/anulación; grupos invisibles; época/cursor/SSE; retención sin borrado funcional |
| Privacidad | Marcadores ficticios ausentes de errores/logs/auditoría/cursores; timeline sin contenido clínico |

Dominio y aplicación usan pruebas sin red. Integridad, carreras, migraciones e idempotencia concurrente usan PostgreSQL Test 18.3 y Keycloak Test, con bases aleatorias eliminadas al terminar. SQLite no acredita esas reglas. No se declara integración Rust/Hub ni producción.

## 10. Comandos y evidencia

Desde la raíz:

```bash
./.venv/Scripts/python.exe -m unittest discover -s tests -v
./.venv/Scripts/python.exe -m scripts.export_contracts --check
UV_CACHE_DIR=.uv-cache uv build --offline --out-dir .tmp/clinical-stage2/build
node C:/Users/Pedro/AppData/Local/Zed/languages/basedpyright/node_modules/basedpyright/index.js --pythonpath .venv/Scripts/python.exe --pythonversion 3.15 src --outputjson
git diff --check
```

Los probes existentes se ejecutan desde `test-support/README.md`. Añadir probes específicos para atenciones, notas, mediciones, vacunas, antecedentes e historial, y ampliar permisos/descarga/persistencia/contratos. El cierre incluye todos los probes existentes, no solo los nuevos. La evidencia registra comandos, resultados, fallos, archivos y límites en `todo.md`; no acepta checkpoints automáticamente.

## 11. Referencias oficiales consultadas

Consultadas el 2026-11-16. FHIR R5 5.0.0 aporta conceptos, no conformidad ni obligación de copiar sus ciclos o cardinalidades.

- [FHIR Encounter](https://hl7.org/fhir/R5/encounter.html): atención real frente a cita planificada y vínculo entre ambas. El producto no adopta su ciclo de estados.
- [FHIR Observation](https://hl7.org/fhir/R5/observation.html): mediciones, contexto y distinción de otros conceptos clínicos.
- [FHIR Vital Signs](https://hl7.org/fhir/R5/observation-vitalsigns.html): valores numéricos, UCUM, códigos de referencia y presión con componentes que admiten dato ausente.
- [FHIR Immunization](https://hl7.org/fhir/R5/immunization.html): administración actual/histórica, fuente, atención y detalles opcionales.
- [FHIR FamilyMemberHistory](https://hl7.org/fhir/R5/familymemberhistory.html): historia de una persona relacionada, sin atribuir su condición al paciente. No se copia su modelo completo.
- [FHIR date](https://hl7.org/fhir/R5/datatypes.html#date): año/mes/día con precisión conservada.
- [Pydantic 2.14.1 validators](https://github.com/pydantic/pydantic/blob/v2.14.1/docs/concepts/validators.md), [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/), [SQLAlchemy 2.1 transactions](https://docs.sqlalchemy.org/en/21/orm/session_transaction.html), [Alembic 1.20.1 operations](https://alembic.sqlalchemy.org/en/latest/ops.html) y [PostgreSQL 18 constraints/triggers](https://www.postgresql.org/docs/18/sql-createtrigger.html): fuentes para las comprobaciones técnicas durante implementación.

No se seleccionan bibliotecas, catálogos médicos ni servicios externos nuevos. Antes de usar una API concreta se vuelve a contrastar la versión resuelta y la fuente oficial conforme a `docs-first-framework-code`.

## 12. Riesgos, supuestos y preguntas

| Riesgo | Mitigación |
|---|---|
| Mezclar cita y atención o reintroducir cierre | Revisión C01/C03; pruebas de ausencia de efectos automáticos y última visita directa de atenciones |
| Filtrar historial o resultados con un permiso global | Alcance por fuente antes de contar/validar/proyectar y pruebas cruzadas de todas las secciones |
| Perder precisión temporal o confundir carga con hecho | Campos separados para hecho/captura/aceptación y pruebas offline/históricas |
| Crear una proyección timeline inconsistente | Escritura en la misma transacción, backfill y procedimiento de reconstrucción comparado con estados actuales |
| Copiar demasiada historia a dispositivos | Descarga de hechos actuales/válidos sin versiones anteriores; historias online y permisos por sección |
| Expandir Etapa 2 a analítica o consumidores | Exclusiones explícitas y revisión en cada checkpoint |

**Supuestos:**

- El diseño exacto de columnas, restricciones, rutas y payloads se revisa en C01 antes de código.
- Las cinco mediciones no admiten unidades alternativas ni fechas parciales; atenciones/mediciones usan instantes exactos. Vacunas/antecedentes sí usan las fechas parciales indicadas.
- No se crea un modelo general de participantes: esta entrega conserva profesional responsable y asistente opcional de la cuenta, sin equipos/clínicas nuevos.
- La última visita usa el alcance cuenta/paciente. Un empate no afirma un orden clínico adicional; el identificador solo estabiliza el enlace devuelto.
- La captura offline no contiene historias de versiones ni adjuntos. La aplicación atómica en SQLite sigue siendo trabajo del escritorio.
- No hay dependencias, commits, despliegues, datos reales ni cambios en otros repositorios. Trabajo secuencial y sin delegación.
- Las revisiones pendientes de Etapa 1 y de planes anteriores no se aceptan por redactar o aprobar este plan.

**Preguntas abiertas:** ninguna para el alcance aprobado de esta planificación. Las decisiones operativas para datos reales y las funciones de Etapa 3 permanecen fuera.
