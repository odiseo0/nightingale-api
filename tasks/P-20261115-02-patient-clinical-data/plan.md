# P-20261115-02-patient-clinical-data: etapa 1 de datos clínicos de referencia

**Estado:** In progress. **Fecha:** 2026-11-15. **Lista de ejecución y evidencia:** [todo.md](todo.md).

El usuario solicitó primero guardar el plan presentado y su lista de tareas. El 2026-11-15 aprobó el plan y autorizó ejecutar T01 → T02 → T03, una tarea a la vez y sin delegación, hasta presentar C01 para revisión. Después aceptó C01 y autorizó T04 → T05 → T06 hasta C02, en la misma forma. Posteriormente aceptó C02 y autorizó T07 → T08 → T09 hasta C03. Después aceptó C03 y autorizó T10 → T11 → T12 hasta C04. Posteriormente aceptó C04 y autorizó T13 → T14 → T15 hasta C05. Después aceptó C05 y autorizó T16 → T17 → T18 hasta C06. C06 permanece sin aceptar y la etapa 2 no se inicia. C11 del núcleo y los checkpoints de los encargos documentales anteriores conservan su estado.

## 1. Objetivo y decisiones de alcance

Implementar en Nightingale API el registro de sexo al nacer, condiciones, alergias e intolerancias por cuenta/paciente, con permisos por asistente, historial de cambios y descarga del estado actual.

El plan parte de la [especificación clínica](../../docs/patient-clinical-record.md), de la documentación vigente y de la lectura del código de pacientes, cuentas, operaciones, capturas y descarga incremental. La especificación conserva los objetivos de las tres etapas; este plan concreta la primera. Sus fuentes de datos y transporte siguen en [database-schema.md](../../docs/database-schema.md) y [api-v1.md](../../docs/api-v1.md).

### 1.1 Decisiones tomadas para esta etapa

El usuario eligió las opciones siguientes durante la planificación del 2026-11-15:

| Tema | Decisión |
|---|---|
| Sexo | Sexo al nacer, opcional y con fuente registrada. |
| Nacimiento | Conservar la fecha completa opcional existente. No añadir nacimiento parcial. |
| Edad | Calcularla desde nacimiento; no guardarla como otro dato editable. |
| Condiciones y sustancias | Nombres en texto libre. Sin catálogo médico externo en esta etapa. |
| Alergias | Incluir alergias, intolerancias y tipo aún no determinado. |
| Fechas clínicas históricas | Admitir fecha completa, mes/año o año, siempre opcionales. |
| Permisos | Por asistente y por sección: perfil clínico, condiciones y alergias/intolerancias. |
| Acceso inicial del asistente | Lectura y escritura en las tres secciones. El propietario puede reducirlo. |
| Descarga | Estado actual de los registros, incluidos sus estados. Las versiones anteriores se consultan aparte con conexión. |
| Ámbito | Cada cuenta conserva sus registros. Compartir identidad de paciente no comparte información clínica. |

Los nombres técnicos, estados, estructura y comprobaciones de los apartados siguientes desarrollan esas decisiones y forman el diseño incluido en el plan aprobado. El usuario aprobó ese conjunto para iniciar T01–T03; C01 conserva la revisión del diseño físico y contractual antes de código.

### 1.2 Entrega y límites

Entrega: API, persistencia, migraciones, contratos, documentación y pruebas de servidor. El escritorio recibirá el contrato necesario para una integración posterior; este plan no cambia otro repositorio.

Quedan fuera consultas clínicas, notas, mediciones, vacunas, medicación, prescripciones, planes de cuidados, laboratorio, plantillas, analítica y Toxicidad. Tampoco cambia la relación actual entre cita y servicio.

Trabajo secuencial, sin delegación. Cada checkpoint requiere revisión del usuario. Este plan no acepta C11 de P-20261024-01-desktop-shared-api ni los checkpoints de P-20261114-01-patient-hub-docs o P-20261115-01-clinical-spec.

### 1.3 Trazabilidad a la especificación

| Parte de la especificación clínica | Cobertura de este plan |
|---|---|
| A02, A04, A06–A10 | Decisión médica, ámbito por cuenta, etapa 1, datos calculados, entrada breve, correcciones y permisos |
| R01, R03–R06 | Aislamiento, nacimiento/sexo, condiciones, alergias y estado de información |
| R19–R25 | Fecha/fuente, correcciones, historial, acceso, aceptación y descarga |
| E01–E05, E22–E24 | Casos de cuenta, alta, edad, condiciones, alergias, concurrencia, revocación y ventana de descarga |
| O01, O04–O06, O14–O15 | Se concretan para esta etapa mediante las decisiones y reglas de este plan; las partes de otras etapas conservan su alcance |

T01 registrará estas concreciones en la especificación sin borrar la historia de descubrimiento. Los Oxx anteriores pertenecen a patient-clinical-record.md, no al registro histórico de decisions.md.

## 2. Diseño de datos, permisos e interfaces

### 2.1 Propiedad y estructura

Añadir el componente `clinical_records` para los nuevos datos clínicos. `patients` conserva identidad, ficha administrativa y nacimiento; `accounts` conserva permisos; `sync` conserva aceptación, recibos y descarga; `audit` conserva evidencia de acceso y operaciones.

El componente tendrá las capas actuales del proyecto: esquemas y reglas en dominio, casos con Ok/Err, endpoints sin helpers y modelos/DAOs derivados de la base. Los componentes consumirán casos de uso y tipos ajenos, sin importar sus repositorios.

El diseño físico se incorporará únicamente a database-schema.md. El contrato de transporte se ampliará en su fuente actual. No se añadirá lógica de producto a core ni una segunda fábrica de sesiones.

### 2.2 Datos y tablas

| Datos | Persistencia y reglas |
|---|---|
| Perfil clínico | `patient_clinical_profiles`, con clave cuenta/paciente. Sexo al nacer, fuente, versión y marcas de registro. |
| Condiciones | `patient_conditions`, con UUIDv7, cuenta/paciente, nombre, estado clínico, certeza, fechas conocidas y fuente. |
| Alergias e intolerancias | `patient_allergy_intolerances`, con UUIDv7, cuenta/paciente, sustancia, tipo, reacción descrita, estados, fechas conocidas y fuente. |
| Estado de información de cada lista | `patient_clinical_section_reviews`, con clave cuenta/paciente/sección. Distingue información no registrada, no preguntada, desconocida, ausencia conocida y presencia de registros. |
| Versiones clínicas | Una tabla de historial por cada una de las cuatro tablas anteriores, con su estado tipado, versión, autor, instante y operación de origen. |
| Cambios de nacimiento | `patient_birth_date_changes`, propiedad de patients: valor anterior, nuevo valor, versión resultante de la ficha, autor, instante y operación. |

Son nueve tablas nuevas. Las columnas y restricciones se documentarán antes de implementar cada bloque.

Reglas comunes:

- Referencias compuestas que comprueben cuenta y paciente; ninguna reasignación de registros entre pacientes o cuentas.
- Versiones positivas y control optimista. Los historiales clínicos empiezan en 1, avanzan sin huecos y coinciden con el estado actual.
- Historial inmutable: el rol operativo no puede actualizarlo ni borrarlo.
- Datos actuales y su historia se confirman en la misma transacción.
- Índices por cuenta/paciente/identificador; historiales por registro/versión. No añadir índices globales de nombres ni unicidad por texto.
- No crear registros clínicos vacíos para todos los pacientes durante la migración.
- Una lectura sin perfil clínico devuelve valores sin registrar y versión 0, sin escribir en la base.
- El nacimiento continúa en la ficha administrativa. Su historial empieza con los cambios realizados desde esta entrega; no se inventan autores ni fechas anteriores.

La continuidad de versiones clínicas no impone continuidad a patient_birth_date_changes: otras ediciones administrativas pueden incrementar la versión de la ficha sin cambiar nacimiento.

Las FK y los controles entre filas seguirán las garantías de [PostgreSQL 18](https://www.postgresql.org/docs/18/ddl-constraints.html). La aplicación coordinará la sesión existente, según el patrón de [transacciones de SQLAlchemy 2.1](https://docs.sqlalchemy.org/en/21/orm/session_transaction.html).

### 2.3 Perfil clínico y nacimiento

`sexAtBirth` admite `male`, `female`, `other`, `unknown` o `null`.

- null: no registrado.
- unknown: se registra que se desconoce.
- other: otra clasificación declarada; no permite deducir características clínicas.
- No se obtiene del nombre, documento o género administrativo.
- Cambiarlo conserva versión y fuente anteriores.

El significado del campo será explícito. FHIR distingue sexo al nacer, datos administrativos y parámetros para uso clínico; este campo no sustituye a los demás. [FHIR Patient](https://hl7.org/fhir/R5/patient.html).

La lectura del perfil clínico incluirá nacimiento, versión de la ficha administrativa, edad en años completos y fecha local usada para calcularla. Si falta nacimiento, la edad será nula. Se conserva el criterio actual del cumpleaños del 29 de febrero.

El nacimiento mantiene sus permisos administrativos actuales. El nuevo permiso de perfil clínico controla el sexo al nacer y su historial; no retira por deducción el acceso administrativo a nacimiento.

### 2.4 Condiciones

Datos de entrada:

- patientId al crear; la referencia queda estable.
- name, obligatorio y no vacío.
- clinicalStatus, por defecto active.
- verificationStatus, por defecto unconfirmed.
- onsetDate y abatementDate, opcionales y con precisión variable.
- sourceType, por defecto unknown.
- correctionReason, opcional en cambios.

Estados clínicos: `active`, `recurrence`, `relapse`, `inactive`, `remission`, `resolved`, `unknown`.

Certeza: `unconfirmed`, `provisional`, `differential`, `confirmed`, `refuted`, `entered-in-error`. Se conservan las distinciones documentadas en [estado clínico](https://hl7.org/fhir/R5/valueset-condition-clinical.html) y [verificación](https://hl7.org/fhir/R5/valueset-condition-ver-status.html).

Reglas:

- Crear o editar constituye una acción expresa de quien registra; no se extraen condiciones de textos ni otros datos.
- La lista de condiciones activas incluye active, recurrence y relapse, excluyendo registros descartados o introducidos por error.
- Resolver y corregir tienen efectos distintos.
- entered-in-error se establece mediante una acción de anulación y es terminal. Una nueva afirmación requiere otro registro.
- Los demás cambios de estado conservan historia. La certeza puede revisarse sin borrar lo anterior.
- Dos registros con igual nombre no se fusionan ni se rechazan por esa coincidencia.
- La descripción y la fuente no prueban por sí solas un diagnóstico.

### 2.5 Alergias e intolerancias

Datos de entrada:

- patientId al crear.
- substance, obligatoria y no vacía.
- type: allergy, intolerance o unknown; por defecto unknown.
- reactionDescription, opcional.
- clinicalStatus: active, inactive o resolved; por defecto active.
- verificationStatus: unconfirmed, presumed, confirmed, refuted, entered-in-error; por defecto unconfirmed.
- onsetDate, lastOccurrenceDate y sourceType, opcionales. sourceType usa el valor inicial unknown de §2.7.
- correctionReason, opcional en cambios.

La reacción será una descripción en esta etapa. No se añade todavía un sistema de episodios de reacción, recomendaciones farmacológicas o clasificación automática de gravedad.

Una anulación por error conserva la información anterior y excluye el registro de los resúmenes vigentes. No se reactiva. Las demás revisiones mantienen historia. [FHIR AllergyIntolerance](https://hl7.org/fhir/R5/allergyintolerance.html), [estados de verificación](https://hl7.org/fhir/R5/valueset-allergyintolerance-verification.html).

### 2.6 Información desconocida y revisión de listas

Condiciones y alergias tendrán un estado de información propio:

- not_recorded: valor inicial sin una revisión registrada.
- not_asked: se registra que no se preguntó.
- unknown: no se conoce la información.
- none_known: una persona registra ausencia conocida.
- has_entries: existen registros pertinentes.

has_entries se deriva de condiciones o alergias no descartadas ni introducidas por error, incluso si están resueltas. El número de registros activos se mostrará aparte.

Al añadir un registro pertinente, el estado pasa a has_entries. Al retirar el último por descarte o error, pasa a unknown; nunca a none_known de forma automática.

La acción de revisión:

- Permite registrar not_asked, unknown o none_known cuando no hay registros pertinentes.
- Permite confirmar una revisión de has_entries cuando sí los hay.
- Obtiene autor e instante del servidor.
- Conserva historia.
- Rechaza contradicciones con los registros existentes.

Una lista vacía no acredita ausencia clínica. [FHIR List Empty Reasons](https://hl7.org/fhir/R5/valueset-list-empty-reason.html).

### 2.7 Fechas, fuente y correcciones

Las fechas históricas usarán cadenas YYYY, YYYY-MM o YYYY-MM-DD, o null. La precisión se conserva en la representación guardada; no se completa un día ficticio. Esta forma sigue la referencia de [fecha de FHIR](https://hl7.org/fhir/R5/datatypes.html#date).

- Validar fechas de calendario, incluidos años bisiestos.
- Rechazar un inicio completamente posterior al día local actual.
- Rechazar un fin inequívocamente anterior al inicio.
- Si las fechas parciales no permiten determinar el orden, conservar esa precisión sin afirmar un orden exacto.
- No usar la fecha de registro como inicio de una enfermedad o de una reacción.
- Autor, versión e instante de aceptación proceden del servidor.
- Ausencia en un patch conserva; null borra solo los campos que lo permiten.
- Un cambio sin diferencias devuelve NO_CHANGES y no crea otra versión.

sourceType admite `patient`, `related_person`, `professional`, `external_document`, `unknown`; su valor inicial es unknown. Es información sobre el origen, no una identidad autenticada adicional. El autor real siempre se conserva.

Cada edición crea una revisión. La anulación es una acción distinta. No se exige un motivo en toda edición ni un trámite universal de firma.

### 2.8 Permisos

Añadir a cada pertenencia tres niveles independientes: perfil clínico, condiciones y alergias. Cada uno admite `none`, `read` o `read_write`.

- Propietario: acceso efectivo completo; esta operación no permite retirárselo.
- Asistentes existentes y nuevos: read_write inicial en las tres secciones.
- Solo el propietario configura los permisos de asistentes de su cuenta.
- El cambio usa la versión de la pertenencia y conserva sus demás datos.
- Cambiar permisos incrementa la versión de pertenencia y la época de acceso en la misma aceptación.
- Desactivar o reactivar una pertenencia conserva su configuración clínica.
- Sin lectura: no se entregan datos, resúmenes, versiones ni resultados clínicos de esa sección.
- Solo lectura: permite consultar; rechaza nuevas escrituras y reintentos de escritura.
- Recuperar un resultado de escritura exige seguir autorizado para esa acción. El estado vigente sigue consultable con permiso de lectura.

El control se aplica antes de devolver duplicados o resultados. La escritura y la revocación siguen el orden de bloqueos del proyecto, con relectura tras esperas. [Bloqueos de PostgreSQL](https://www.postgresql.org/docs/18/explicit-locking.html).

### 2.9 Contrato HTTP y operaciones

Se mantienen las escrituras en el lote de operaciones. Se añaden nueve acciones:

| Acción | Clave | Entrada principal |
|---|---|---|
| SetMemberClinicalPermissions | Usuario destinatario | Los tres niveles; solo con conexión y propietario. |
| SetPatientSexAtBirth | Paciente | Valor y fuente. Versión 0 para primer registro. |
| CreatePatientCondition | UUID nuevo | Paciente y datos de condición. |
| UpdatePatientCondition | Condición | Patch con versión actual. |
| InvalidatePatientCondition | Condición | Motivo opcional. |
| CreatePatientAllergyIntolerance | UUID nuevo | Paciente y datos de alergia/intolerancia. |
| UpdatePatientAllergyIntolerance | Registro | Patch con versión actual. |
| InvalidatePatientAllergyIntolerance | Registro | Motivo opcional. |
| SetPatientClinicalSectionReview | Paciente | Sección, estado de información y fuente; versión de esa revisión. |

No se incluyen actor, cuenta o instante técnico como autoridad aportada por el cliente.

Lecturas nuevas, bajo la cuenta:

- Acceso clínico efectivo propio y acceso configurado de un miembro, este último solo para el propietario.
- Perfil clínico del paciente y su historial.
- Condiciones: lista, detalle e historial de un registro.
- Alergias/intolerancias: lista, detalle e historial.
- Revisión actual de cada sección e historial.
- Historial de cambios de nacimiento, bajo los permisos administrativos existentes.

Las rutas clínicas quedarán bajo patients/{patient_id}; los permisos, bajo cuentas/miembros. Todas las listas usarán page/shows, items/total, filtros anteriores al conteo y orden estable. Historial por versión ascendente; listas por identificador.

Las listas ordinarias incluyen estados vigentes, resueltos y descartados; los introducidos por error se incluyen solo mediante filtro explícito. La descarga conserva la última versión de todos ellos para poder reconstruir el estado.

Cada ruta declarará respuesta y retorno reales con proyecciones explícitas. Se mantienen los errores comunes: 401, 403, 404, 422, 503, conflictos por versión y resultados por operación. Un identificador ajeno devuelve la misma ausencia que uno inexistente. [Modelos de respuesta de FastAPI](https://fastapi.tiangolo.com/tutorial/response-model/).

## 3. Secuencia de tareas y checkpoints

Cada tarea depende de la anterior. Las migraciones forman una cadena desde el head actual, sin modificar revisiones previas. Cada bloque implementa y comprueba sus propias tablas y controles; no se crean archivos o tablas vacíos para entregas posteriores.

### 3.1 Diseño y contrato

| Tarea | Propietario, entradas y trabajo | Aceptación y comprobación |
|---|---|---|
| T01 · Registrar acuerdos y preparar ejecución | Documentación. Entrada: este plan y la especificación clínica; sin dependencia. Registrar las decisiones de planificación y su trazabilidad. Preparar plan y lista de control. | Alcance, exclusiones, tareas y checkpoints completos; integrar acuerdos en sus fuentes sin aceptar revisiones previas. |
| T02 · Definir datos y contratos | Documentación de datos y contratos. Entrada: T01. Incorporar el diseño físico, acciones, lecturas, permisos y descarga en sus fuentes únicas. | Relaciones, estados, versiones y nulabilidad coherentes; catálogos de acciones y rutas sin duplicados. |
| T03 · Registrar línea base y casos | Calidad. Entrada: T02. Registrar estado inicial de suite, estructura, analizador, migraciones y contratos disponibles. Preparar casos ficticios y fuentes por versión. | Evidencia real y fallos previos separados; revisión de enlaces y diff. |

T01–T03 no cambian transacciones ni sincronización ejecutables. Su efecto en consumidores se limita a definir y revisar el contrato futuro. Crear estos dos archivos por encargo del usuario no completa por sí solo T01, que también exige registrar las concreciones en las fuentes.

C01 — Diseño y contrato. Revisar antes de añadir código.

### 3.2 Permisos clínicos

| Tarea | Propietario, entradas y trabajo | Aceptación y comprobación |
|---|---|---|
| T04 · Preparar permisos y filtrado cerrado | accounts y sync. Entrada: T03 y C01 aceptado. Añadir niveles clínicos al dominio y preparar filtrado cerrado de audiencias: todo dato nuevo queda excluido de consumidores que no soliciten clínica. | Audiencias no permitidas se filtran antes de interpretar sus proyecciones; controles de estructura activos. |
| T05 · Configurar acceso por asistente | accounts. Entrada: T04. Migrar permisos en pertenencias; implementar consulta propia, consulta del propietario y acción de configuración. Inicialización de invitados y asistentes existentes. | Versión, auditoría, recibo, época y cambios atómicos; propietario conserva acceso; sin alterar roles globales. |
| T06 · Comprobar permisos y revocación | Calidad de acceso. Entrada: T05. Probar permisos por sección y concurrencia de configuración con operaciones/lecturas. | Sin filtraciones por errores o resultados; aplicación/reversión/reaplicación de migración en PostgreSQL aislado. |

Datos afectados: pertenencias y contexto de autorización. T05 utiliza la aceptación existente y confirma permiso, versión, época, recibo, auditoría y journal juntos. T04 no amplía la descarga de datos; la preparación evita que lectores anteriores reciban las proyecciones clínicas al incorporarlas. Consumidores: contrato de acceso y acciones efectivas; sin cambios al escritorio.

C02 — Permisos clínicos. Revisar antes de habilitar datos clínicos.

### 3.3 Perfil y nacimiento

| Tarea | Propietario, entradas y trabajo | Aceptación y comprobación |
|---|---|---|
| T07 · Persistir perfil e historia | clinical_records y patients. Entrada: T06 y C02 aceptado. Implementar perfil clínico, historial de sexo y registro de cambios de nacimiento. | Reutiliza nacimiento; datos actuales/historia coherentes; sin historial anterior inventado. |
| T08 · Registrar y consultar perfil | clinical_records, patients y sync. Entrada: T07. Conectar acción de sexo, lecturas, edad calculada y resultados tipados. Registrar cambios de nacimiento en operaciones existentes. | No cambia completitud ni requisitos de cita. Perfil no registrado se lee sin escritura; duplicados no añaden historia. |
| T09 · Comprobar perfil y nacimiento | Calidad de perfil. Entrada: T08. Probar aislamiento, ausencia/null, edad, bisiestos, correcciones, versiones y rollback. | Controles de estructura sin excepciones; historia protegida y pruebas PostgreSQL correctas. |

Datos afectados: perfil clínico e historiales, además de trazabilidad de nacimiento en patients. Las escrituras conservan historia en la misma aceptación que efecto, recibo y cambios. No publican el sexo al nacer como campo administrativo para todos los miembros. Consumidores: nuevas lecturas y acción; descarga clínica aún pendiente de T16.

C03 — Perfil y nacimiento. Revisar antes de condiciones.

### 3.4 Condiciones

| Tarea | Propietario, entradas y trabajo | Aceptación y comprobación |
|---|---|---|
| T10 · Persistir condiciones y revisiones | clinical_records. Entrada: T09 y C03 aceptado. Implementar fechas parciales, condiciones, revisiones de sección y sus historiales. | Restricciones, referencias y fechas válidas; sin identidad o cuenta mutable. |
| T11 · Registrar y consultar condiciones | clinical_records y sync. Entrada: T10. Conectar altas, cambios, anulación, revisión de lista y lecturas. | Estados y certeza independientes; coherencia automática de lista; resultados y journal tipados antes del commit. |
| T12 · Comprobar estados y carreras | Calidad de condiciones. Entrada: T11. Probar estados, correcciones, datos desconocidos y carreras entre alta y revisión de ausencia. | Ningún estado contradictorio persiste; versión antigua y respuesta perdida no repiten efectos. |

Datos afectados: condiciones, revisión de la sección y sus historiales. Una escritura que cambie también el estado de información conserva ambos efectos en una aceptación y grupo completo. La revisión de ausencia y el alta concurrente comparten coordinación de cuenta. Consumidores: nuevas acciones y lecturas; sin descarga de historia completa.

C04 — Condiciones. Revisar antes de alergias.

### 3.5 Alergias e intolerancias

| Tarea | Propietario, entradas y trabajo | Aceptación y comprobación |
|---|---|---|
| T13 · Persistir alergias e intolerancias | clinical_records. Entrada: T12 y C04 aceptado. Implementar registros e historial usando revisión de sección y fechas ya disponibles. | Sustancia obligatoria, tipo y estados válidos; sin convertir toda reacción en alergia. |
| T14 · Registrar y consultar alergias | clinical_records y sync. Entrada: T13. Conectar acciones, lecturas, filtros, anulación y revisión de información. | Misma aceptación transaccional; ninguna lista vacía establece ausencia conocida. |
| T15 · Comprobar alergias y aislamiento de secciones | Calidad de alergias. Entrada: T14. Probar intolerancia, tipo desconocido, fuente, fechas parciales, errores y permisos independientes. | Alergias y condiciones no comparten permiso ni revisión por accidente; migraciones reversibles en pruebas. |

Datos afectados: alergias/intolerancias, revisión de su sección e historiales. Reutiliza la coordinación probada para condiciones, conservando efectos y estado de información juntos. Consumidores: lecturas y acciones propias; no incorpora reglas de medicación ni extracción automática.

C05 — Alergias e intolerancias. Revisar antes de descarga y cierre.

### 3.6 Descarga, contratos y cierre

| Tarea | Propietario, entradas y trabajo | Aceptación y comprobación |
|---|---|---|
| T16 · Descargar estado clínico autorizado | sync, con casos de los propietarios. Entrada: T15 y C05 aceptado. Incorporar captura opcional, delta autorizado y recuperación al cambiar permisos. Revisar SSE. | Captura coherente, grupos completos, filtros por sección y ausencia de historias completas en descarga. |
| T17 · Publicar contratos de revisión | Contratos y calidad. Entrada: T16. Actualizar capacidades, revisión de modelo, exportador y ejemplos; validar correspondencia con rutas/acciones reales. | Contratos reproducibles, sin recuentos fijos antiguos. Exportación a destino temporal explícito. |
| T18 · Comprobar y entregar etapa 1 | Calidad y documentación. Entrada: T17. Ejecutar pruebas pertinentes completas, probes reales, build y revisión final de fuentes/evidencia. | Sin nuevas infracciones de estructura o avisos ocultados; límites y resultados registrados; entrega de API. |

Datos afectados: proyecciones, ámbito de captura/cursor y capacidades. T16 materializa captura y base coherentes en la transacción existente; no mantiene sesiones entre páginas. No altera retención funcional clínica. Consumidores: contratos y ejemplos para integración posterior; no se declara escritorio implementado. T17/T18 no añaden operaciones de negocio fuera de lo aprobado.

C06 — Etapa 1 completa. Entregar evidencia y detenerse para revisión. No iniciar etapa 2.

## 4. Sincronización, seguridad y pruebas

### 4.1 Descarga y compatibilidad

Añadir includeClinical, opcional y falso por defecto, a la creación de captura.

- Una captura clínica incluye las secciones que el usuario puede leer y registra ese conjunto en la captura y el cursor firmado.
- Los cursores anteriores equivalen a una captura sin clínica.
- Las respuestas anteriores conservan su forma cuando no se solicita clínica.
- El conjunto descargado incluye los últimos estados de perfil, condiciones, alergias y revisiones. No incluye las tablas de historial.
- Se incluyen las referencias administrativas necesarias para interpretar esos registros.
- Las condiciones y alergias no se filtran por la ventana temporal de citas.
- La descarga incremental usa el mismo alcance y filtra antes de construir la respuesta. Puede avanzar por grupos invisibles sin entregar sus cuerpos.
- Cada cambio de permisos invalida capturas y cursores mediante la época de acceso. SSE vuelve a comprobarla y cierra el stream anterior conforme al mecanismo actual.
- Un cliente solicita otra captura con los permisos nuevos. Esto no promete borrado remoto de datos ya descargados.
- Se mantiene contractVersion=1 y se publica modelRevision=api-v1.2 al cerrar la etapa. La ampliación clínica requiere solicitud explícita.
- No se habilita el consumo clínico mientras queden procesos API con el código anterior.

Los historiales se conservan sin purga automática durante esta etapa. La retención de recibos y journal no borra historia funcional. La operación con datos reales y su política de conservación requieren una entrega operativa posterior.

### 4.2 Auditoría

Conservar la auditoría transaccional de escrituras y añadir evidencia de lecturas clínicas correctas, incluidas capturas y páginas clínicas: actor, dispositivo, cuenta, objeto/sección, acción, resultado, correlación e instante.

No registrar nombres clínicos, sustancias, reacciones, filtros de búsqueda, cuerpos ni cursores. Una lectura clínica no devuelve datos si falla la persistencia de su evidencia; devuelve el error temporal común. SSE continúa como aviso, sin duplicar auditoría por cada heartbeat.

### 4.3 Matriz de pruebas

| Área | Casos obligatorios |
|---|---|
| Dominio | Sexo opcional/desconocido; texto vacío; estados; fecha completa/parcial; bisiestos; fechas imposibles; ausencia frente a null; patch vacío; cambios sin diferencias. |
| Edad | Nacimiento vacío, fecha futura, cumpleaños y 29 de febrero; misma regla administrativa ya vigente. |
| Historial | Creación, edición y anulación; continuidad e igualdad con estado actual; rechazo de modificación/borrado; cambios de nacimiento sin reconstrucción ficticia. |
| Información de listas | Vacía inicial, no preguntado, desconocido, ausencia conocida, alta posterior y retirada del último registro pertinente. |
| Permisos | Propietario; asistente con lectura/escritura, lectura y sin acceso, combinados entre las tres secciones; miembro inactivo, cuenta inactiva y dispositivo revocado. |
| Aislamiento | Paciente o registro de otra cuenta; referencias manipuladas; búsqueda, total, detalle, historia, resultado, error y descarga. |
| Idempotencia | Duplicado concurrente, contenido distinto, respuesta perdida, resultado vencido y nueva instalación del mismo actor. |
| Concurrencia real | Dos cambios de versión; cambio frente a anulación; alta frente a sin elementos conocidos; revocación frente a aceptación, lectura y resultado previo. |
| Atomicidad | Fallos antes del commit y en restricciones diferidas; sin efecto, historia, recibo o journal parciales. |
| Sincronización | Captura anterior y clínica; subconjunto de permisos; datos anteriores a ventana de citas; grupos invisibles; corrección/anulación; cambio de época y SSE abierto. |
| Compatibilidad | Envolturas y huellas anteriores conservadas; captura sin clínica sin entidades nuevas; modelos y ejemplos generados contra código real. |
| Privacidad | Marcadores ficticios que permitan detectar datos clínicos o secretos en errores, logs y auditoría. |

Activar controles de estructura para el componente nuevo y mantener los de los componentes afectados. Tomar una línea base real del analizador; no convertir los 16 diagnósticos históricos documentados en un resultado correcto ni añadir supresiones para ocultar avisos.

Los probes usarán PostgreSQL Test aislado y bases aleatorias. Keycloak se usará donde corresponda al flujo de acceso. No se ejecutarán contra la base personal ni se exigirá Docker.

## 5. Migraciones, validación y entrega

### 5.1 Migraciones

- Partir de 20261028_01 y añadir revisiones secuenciales por bloque.
- Conservar las columnas y datos anteriores.
- Inicializar los permisos de asistentes en lectura/escritura, según lo acordado.
- Mantener los datos clínicos ausentes como no registrados.
- Probar actualización desde el head anterior con datos ficticios, instalación desde vacío, reversión/reaplicación y fallo sin DDL parcial.
- La reversión que retire tablas clínicas se usa en bases de prueba. No se plantea como recuperación de una base real ya utilizada; para ese caso se prepara una corrección hacia delante o restauración comprobada.
- Conservar la identidad SQL operativa sin permisos de migración.

Se mantiene Alembic 1.20.1 y el patrón actual de migraciones explícitas. [Referencia de operaciones de Alembic](https://alembic.sqlalchemy.org/en/latest/ops.html).

### 5.2 Herramientas y comprobaciones

No añadir ni actualizar dependencias. Conservar las versiones resueltas del manifiesto y lockfile: FastAPI 0.159.1, Pydantic 2.14.1, SQLAlchemy 2.1.6, Alembic 1.20.1 y asyncpg 0.32.0.

Las fechas parciales usan biblioteca estándar y validadores del proyecto. Las guías oficiales actuales de FastAPI/Pydantic se contrastarán con las versiones instaladas en las pruebas; no se presentarán como documentación de un tag que no se haya consultado.

En cada bloque se ejecutan sus pruebas pertinentes. Al cierre:

- Suite unittest completa y controles de estructura.
- Probes de acceso, pacientes, permisos clínicos, datos clínicos, persistencia, descarga y retención.
- Probes SSE/colaboración pertinentes a los cambios de época y cursores.
- Exportación reproducible de contratos y validación de ejemplos.
- Build offline e inspección del paquete.
- Análisis estático comparado con la línea base.
- Revisión documental y git diff --check.

El exportador actual tiene destino y cifras fijas. Se añadirá un destino explícito para generar la evidencia en .tmp, se actualizarán sus revisiones y se obtendrán las cifras del catálogo real. Esto evita reconstruir copias retiradas para satisfacer pruebas antiguas.

### 5.3 Cierre documental

Actualizar la especificación clínica con las decisiones cerradas aquí, el registro de decisiones, las fuentes de esquema/contratos y el índice de tareas. La lista de control conserva evidencia por tarea y checkpoints sin aceptar hasta revisión del usuario.

La entrega final indicará qué funciones de servidor quedaron comprobadas, qué contratos puede consumir el escritorio y qué falta verificar en ese consumidor. No incluirá commits, despliegues ni cambios en otros repositorios.

### 5.4 Fuentes consultadas durante la planificación

Fuentes locales: [especificación API](../../docs/nightingale-api.md), [D12](../../docs/decisions.md#d12--registro-clínico-y-seguimiento-del-paciente), [arquitectura](../../docs/architecture.md), [contratos](../../docs/contracts.md), [acceso](../../docs/access-design.md), [calidad](../../docs/quality.md) y [soporte de pruebas](../../test-support/README.md). Se revisaron además manifiesto, lockfile y los componentes actuales de pacientes, cuentas, sync y auditoría, sus pruebas, migraciones y exportador.

Las referencias oficiales FHIR y de persistencia aparecen junto a la decisión que sustentan. Se consultaron el 2026-11-15. Para las validaciones se consultaron también [Pydantic: validators](https://docs.pydantic.dev/latest/concepts/validators/), [Python 3.15: date](https://docs.python.org/3.15/library/datetime.html#date-objects) y [calendar.monthrange](https://docs.python.org/3.15/library/calendar.html#calendar.monthrange). Son referencias de implementación, no autorización para actualizar herramientas ni evidencia de pruebas ejecutadas.

El encargo de guardar este plan solo crea documentación. Las futuras comprobaciones de producto se ejecutarán y registrarán en sus tareas; no constan realizadas por escribir el plan.
