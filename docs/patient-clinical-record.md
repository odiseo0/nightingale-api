# Registro clínico y seguimiento del paciente

**Versión:** 0.4. **Fecha:** 2026-11-16.
**Estado:** especificación funcional vigente. Etapas 1 y 2 están implementadas para revisión C09, con atenciones, notas, mediciones, vacunas, antecedentes, permisos, timeline, historial y descarga comprobados hasta C08. C09 espera revisión del usuario.
**Decisión de alcance:** [D12](decisions.md#d12--registro-clínico-y-seguimiento-del-paciente).
**Entrega documental:** [P-20261115-01-clinical-spec](../tasks/P-20261115-01-clinical-spec/plan.md), con [evidencia](../tasks/P-20261115-01-clinical-spec/todo.md).

Lectura: [decisiones](#3-decisiones-del-descubrimiento), [etapas](#4-etapas-y-dependencias), [encaje](#5-modelo-conceptual-y-encaje-con-el-proyecto), [datos de referencia](#6-datos-de-referencia-etapa-1), [registro habitual](#7-registro-clínico-habitual-etapa-2), [funciones completas](#8-funciones-completas-etapa-3), [reglas comunes](#9-reglas-comunes-de-entrada-tiempo-y-cambios), [integración](#10-acceso-sincronización-e-integración), [aceptación](#11-casos-de-aceptación-y-trazabilidad-para-los-planes), [pendientes](#12-decisiones-abiertas-y-preparación-de-los-planes) y [referencias](#13-referencias-y-uso-en-esta-especificación).

## 1. Propósito y autoridad

Nightingale ampliará sus funciones para que el profesional médico registre la atención, consulte la historia de cada paciente y siga su evolución. El paciente es la persona que recibe atención; tener ficha no exige convertirlo en usuario del sistema ni en cliente de una cuenta comercial.

Esta especificación es la referencia funcional principal para los planes de las tres etapas clínicas. Explica qué se busca, los acuerdos tomados, los datos necesarios y los casos que cada entrega debe resolver. Los planes concretarán tareas, dependencias y comprobaciones sin mantener otra definición del mismo alcance.

La [especificación de API](nightingale-api.md) conserva el alcance general. [database-schema.md](database-schema.md) conserva la única fuente del modelo físico: cuando se aprueben tablas, columnas y restricciones clínicas, se definirán allí. [api-v1.md](api-v1.md) conserva el contrato HTTP actual; esta especificación no añade rutas ni acciones disponibles. [contracts.md](contracts.md) fija la propiedad de los contratos y [architecture.md](architecture.md), las reglas de implementación.

Las exclusiones clínicas de la primera entrega delimitan esa entrega. Este acuerdo amplía el producto futuro y no cambia por sí solo el código, las migraciones, los permisos actuales o los contratos publicados. Tampoco acepta C11 del núcleo ni los checkpoints pendientes del Hub.

### 1.1 Cómo leer el estado de cada regla

| Marca | Autoridad |
|---|---|
| Acuerdo Axx | Decisión expresada o aceptada por el usuario durante el descubrimiento del 2026-11-15. El detalle figura en §3 |
| Propuesta de diseño | Desarrollo concreto para cumplir los acuerdos; no se atribuye al usuario como decisión ya aceptada |
| Pendiente Oxx | Elección que todavía necesita resolución antes de implementar la función afectada; no bloquea trabajo independiente |
| Referencia Fxx / Wxx | Fuente externa que aclara conceptos, unidades o métodos. No aprueba decisiones del producto |

Los requisitos Rxx organizan el diseño propuesto para revisión. Su base funcional procede de los acuerdos citados; los nombres de estados, datos mínimos y pruebas desarrollan esa base y no equivalen a un contrato físico o HTTP aprobado. Los ejemplos son ficticios y no indican tratamientos recomendados.

### 1.2 Uso de FHIR y de la OMS

HL7 FHIR R5, versión 5.0.0, aporta referencias para distinguir conceptos clínicos y usar unidades conocidas. La finalidad es cubrir el trabajo del profesional. Consultar FHIR no añade un compromiso de implementar todos sus recursos, rutas, cardinalidades o mecanismos de intercambio. Una correspondencia conceptual no acredita conformidad FHIR.

Las referencias de la OMS permiten diseñar después la comparación del crecimiento pediátrico. Cada cálculo debe usar el indicador, población, edad y método aplicables. Las referencias y su uso concreto figuran en §§8.6 y 13. No se seleccionan aquí bibliotecas, dependencias ni servicios externos.

## 2. Objetivos, usuarios y límites

El profesional y su asistente deben poder añadir información de forma breve, recuperar lo que ya se conoce, registrar una nueva toma sin perder las anteriores y corregir errores con trazabilidad. El sistema completa los datos técnicos que puede conocer: autor autenticado, momento de registro y unidad habitual.

El profesional toma las decisiones clínicas. Una nota no genera por sí sola una enfermedad, condición, diagnóstico o tratamiento. El sistema registra sus decisiones y facilita consultar datos y evolución. La comparación con referencias tampoco crea un diagnóstico por sí sola.

El alcance futuro incluye datos de referencia, atención clínica, notas, mediciones, vacunas, antecedentes e historia, condiciones/alergias, medicación declarada, prescripción, tratamiento, planes y seguimiento, informes/resultados, funciones por especialidad y analítica individual.

Toxicidad queda excluida por decisión expresa. La mención inicial se refería a efectos tóxicos, no a hábitos o consumo de sustancias. No se añade un módulo de toxicidad ni se transforma esa exclusión en una decisión sobre todas las futuras funciones de seguridad de medicamentos.

Esta entrega solo especifica. No desarrolla funciones, importa datos reales, cambia otros repositorios, abre acceso clínico en Hub ni inicia trabajo en las tres etapas. El diseño de recomendaciones automáticas de medicamentos, interacciones y dosis requiere un alcance propio; registrar datos para el médico no confirma esa función.

## 3. Decisiones del descubrimiento

| ID | Acuerdo del 2026-11-15 | Efecto para los planes |
|---|---|---|
| A01 | Ampliar Nightingale para cubrir cada vez más funciones del profesional médico | La primera versión es la base de evolución; sus exclusiones no son una prohibición permanente |
| A02 | El médico decide; el sistema registra | No derivar condiciones o enfermedades de una nota |
| A03 | Cita, paciente y atención tienen funciones distintas | Conservar la cita como compromiso; registrar atención y datos clínicos mediante relaciones propias |
| A04 | Mantener el registro clínico por cuenta/paciente | Compartir identidad no comparte historia entre cuentas; aceptar diferencias de información entre consultas |
| A05 | El paciente puede expresar su motivo sin conocer servicio ni especialidad | El recorrido debe aceptar la necesidad en sus palabras; revisar el requisito actual de servicio según §5.3 |
| A06 | Organizar el trabajo en tres etapas | Datos de referencia; registro habitual; funciones completas. El orden no implica que las funciones de la segunda etapa sean técnicamente triviales |
| A07 | Edad y última visita se calculan | No añadir campos manuales que compitan con nacimiento o atención realizada |
| A08 | Completar fechas, horas y unidades con la mayor automatización posible | Usar el momento de entrada por defecto; no exigir escribir fecha/hora exactas en cada registro; usar unidades basadas en FHIR |
| A09 | Conservar tomas sucesivas y distinguirlas de correcciones | La evolución utiliza mediciones válidas; la trazabilidad conserva el error corregido |
| A10 | Médico y asistente son los usuarios principales; el acceso se ajustará en configuración | Diseñar permisos por cuenta y acción. La matriz clínica detallada queda pendiente |
| A11 | Plan/careplan es una función completa | Incluir objetivos, acciones, tratamiento y revisiones; seguimiento de resultados |
| A12 | Medicación declarada y prescripción son funciones distintas | Saber qué toma el paciente además de lo que se le prescribe; no inferir consumo de una receta |
| A13 | Incluir funciones por especialidad en la tercera etapa | Las plantillas y módulos, como odontología, requieren sus propios casos y datos |
| A14 | Analítica histórica individual en la tercera etapa | Incluir crecimiento pediátrico y comparación con referencias OMS; preparar los datos desde las etapas previas |
| A15 | Excluir Toxicidad | No asignarle tablas, tareas ni criterios de entrega |

El usuario aceptó la separación por cuenta pese a la posible repetición de datos. No acordó intercambio automático entre médicos, un expediente global compartido ni fusionar información de cuentas distintas. Dentro de una cuenta se deben reutilizar las referencias a una condición, alergia o plan en vez de copiar una ficha completa por visita.

El usuario entendió y destacó la necesidad de distinguir nueva medición y corrección. No aprobó un proceso universal de firma o cierre obligatorio para toda nota. Los ciclos de emisión de prescripciones y cierre de atención siguen pendientes por función.

## 4. Etapas y dependencias

### 4.1 Etapa 1: datos de referencia del paciente

Base A04, A06–A08 y A10. Incluye nacimiento ya existente, el dato de sexo una vez definido su significado, condiciones y alergias con sus estados, fuente y cambios. Los datos clínicos iniciales son opcionales para el alta administrativa: no convertirlos en requisitos nuevos de completitud o reserva por deducción.

Condiciones y alergias pueden cambiar. Deben permitir añadir, revisar y corregir información conservando su contexto. La etapa establece cómo representar dato desconocido, no preguntado y ausencia conocida, además de la base de permisos y trazabilidad. La medicación declarada completa queda en la etapa 3, sin adelantar una función incompleta aquí.

Resultado esperado: consultar y actualizar la información de referencia autorizada sin exigir otra cita, sin cruzar cuentas y sin perder cambios anteriores. Criterios en §11.

#### 4.1.1 Concreciones aprobadas para la etapa 1

El usuario aprobó [P-20261115-02-patient-clinical-data](../tasks/P-20261115-02-patient-clinical-data/plan.md) el 2026-11-15. Estas decisiones cierran para esta etapa los pendientes indicados; el diseño físico y HTTP se revisa en C01 y no se considera implementado.

| Decisión | Regla aprobada |
|---|---|
| Sexo | `sexAtBirth`: opcional; registra sexo al nacer y fuente. No se infiere de otros datos ni sustituye el género administrativo. |
| Nacimiento y edad | Conservar la fecha completa opcional de `account_patients.birth_date`; no añadir nacimiento parcial. La edad se calcula, no se edita. |
| Condiciones y sustancias | Nombres en texto libre, sin catálogo médico externo en esta etapa. El médico decide qué registra; el sistema no lo deriva. |
| Alergias e intolerancias | Admitir ambos tipos y tipo desconocido. |
| Fechas históricas | Opcionales; admitir `YYYY`, `YYYY-MM` o `YYYY-MM-DD` y conservar su precisión. Esto no cambia nacimiento. |
| Permisos | Tres secciones independientes: perfil clínico, condiciones y alergias/intolerancias. Propietario con acceso completo; asistentes existentes y nuevos con lectura/escritura inicial que el propietario puede reducir. |
| Descarga e historia | Descargar el estado actual de los registros y sus estados; consultar versiones anteriores aparte con conexión. |
| Ámbito | Aislamiento por cuenta/paciente; compartir identidad no comparte datos clínicos. |

Los estados, acciones, columnas, restricciones, rutas y reglas transaccionales se concretan en las fuentes únicas enlazadas en §10.4. La aprobación del plan no equivale a aceptar ese diseño detallado en C01. O01, O05 y O14 quedan resueltos para etapa 1; O04 y O06 solo en su parte de etapa 1. O15 queda resuelto para descarga e historia funcional de esta etapa, pero conserva la política operativa y de datos reales pendiente.

### 4.2 Etapa 2: registro clínico habitual

Base A03, A05–A10. Incluye atención clínica, motivo, historia del problema actual, notas sobre el paciente, mediciones, registro de vacunas recibidas, antecedentes y consulta del historial disponible. La última visita se obtiene de atención realizada según una definición aún por cerrar.

La consulta clínica aporta el contexto común para la información que pertenece a una atención. Los registros que no dependen de una consulta deben poder existir sin inventar una cita: por ejemplo, una vacuna histórica o una nota posterior. El plan concretará esos vínculos y la secuencia de entrega.

Vacunas en esta etapa significa registrar y consultar dosis recibidas o declaradas. Calendarios automáticos, recomendación de dosis y avisos son funciones adicionales cuyo alcance no está decidido. La vista del historial reúne los datos ya implementados; no debe simular funciones de etapas posteriores.

Resultado esperado: trabajar desde la ficha y las consultas con entrada breve, historia de mediciones y correcciones claras, dejando datos aptos para análisis posterior.

#### 4.2.1 Concreciones aprobadas para la etapa 2

El usuario aprobó [P-20261116-02-clinical-routine](../tasks/P-20261116-02-clinical-routine/plan.md) el 2026-11-16 y autorizó integrar sus decisiones antes de revisar C01. Estas reglas no acreditan implementación ni habilitan T04.

| Decisión | Regla aprobada |
|---|---|
| O02 | Registrar una atención afirma que ocurrió, sin ciclo de planificación, firma o cierre. Puede existir sin cita y una cita puede tener varias atenciones. Solo la anulación por error usa una marca terminal distinta del ciclo asistencial. |
| O02 / última visita | Es la última vez que paciente y profesional se vieron. Se calcula desde `occurredAt` de la última atención válida de la cuenta/paciente; no depende de citas, notas, aceptación remota ni cierre. |
| O03 | `serviceId` sigue obligatorio al reservar. Etapa 2 no cambia disponibilidad, duración ni snapshots de citas; una atención sin cita admite el motivo en palabras del paciente. |
| O06 | Atenciones y notas se editan con versión esperada, sin cierre universal. Mediciones, vacunas y antecedentes distinguen nueva entrada, corrección y anulación; el motivo de corrección es opcional. |
| O07 | Las cinco mediciones iniciales son peso, presión arterial, temperatura, saturación de oxígeno y frecuencia cardíaca. Talla, perímetro cefálico, frecuencia respiratoria, IMC y curvas quedan fuera. |
| O08 | Los detalles de vacunas son opcionales cuando no se conocen. Antecedentes narrativos tipados como `personal`, `family` u `other` no crean condiciones automáticamente. |
| O14 | Atenciones, notas, mediciones, vacunas y antecedentes tienen permisos independientes por asistente. El historial filtra cada elemento por la sección de su fuente. |
| O15 | La descarga para evolución incluye atenciones válidas, versión actual válida de notas/antecedentes, todas las tomas válidas y vacunas vigentes; excluye versiones anteriores y adjuntos. |

El diseño físico, HTTP, acceso y sincronización se incorpora a las fuentes únicas para C01. O04 conserva fechas parciales solo donde el diseño las admite; O11 y la analítica/crecimiento siguen en etapa 3. Las políticas de copias, restauración y operación con datos reales permanecen pendientes.

### 4.3 Etapa 3: funciones clínicas completas

Base A11–A14. Incluye los siguientes bloques funcionales, cuyo orden interno debe decidir un plan por dependencias y uso:

| Bloque | Resultado que debe diseñarse |
|---|---|
| Medicación declarada | Registrar y revisar lo que el paciente toma o tomó, incluso si otro profesional lo indicó |
| Prescripción | Preparar y emitir indicaciones de medicamentos con su ciclo de cambios y anulación |
| Tratamiento y plan de cuidados | Relacionar problemas, intervenciones, objetivos, acciones y seguimiento |
| Laboratorio e informes | Conservar documentos y resultados fechados, con fuente, unidades y revisiones |
| Plantillas y funciones por especialidad | Apoyar recorridos concretos; el ejemplo de odontología puede requerir un módulo propio |
| Analítica histórica individual | Consultar tendencias y comparar crecimiento pediátrico con referencias OMS aplicables |

La tercera etapa no debe convertirse en una única tarea ni en un requisito de terminar todos los bloques a la vez. Cada bloque tendrá un plan revisable. Un bloque puede depender de otro: el seguimiento de una meta medible usa mediciones; la analítica pediátrica exige datos aptos; la prescripción necesita sus permisos y datos propios.

## 5. Modelo conceptual y encaje con el proyecto

### 5.1 Identidad, ficha, cita y atención

| Concepto | Responsabilidad | Relación prevista |
|---|---|---|
| Identidad interna de paciente | Identificador estable; no concede acceso ni exige cuenta de usuario | `patients` conserva su función actual |
| Ficha del paciente en una cuenta | Información administrativa y acceso al registro clínico de esa cuenta | La pareja actual de `account_patients` fija el ámbito |
| Cita | Compromiso programado, intervalo, paciente y participantes | Conserva sus reglas de reserva y su historial de cambios |
| Atención o consulta clínica | Lo ocurrido durante una atención: motivo, hallazgos, valoración e indicaciones | Pertenece al paciente/cuenta y a quien atiende; puede referirse a una cita |
| Registro que continúa entre consultas | Condición, alergia, medicación o plan | Se referencia desde consultas sin recrearlo por visita |
| Hecho fechado | Medición, vacuna, resultado o revisión | Conserva su fecha y fuente; puede referirse a atención, problema o plan |

La cardinalidad está resuelta por §4.2.1: una atención no exige cita y una cita admite varias atenciones. No existe una atención planificada por deducción de una cita; una ausencia o cancelación no acredita atención realizada.

Las notas y diagnósticos no se guardan en `appointment_histories`. Esa tabla conserva la historia funcional de la cita según el esquema actual. El historial clínico y la auditoría técnica también tienen fines distintos.

FHIR [Encounter](https://hl7.org/fhir/R5/encounter.html) distingue la actividad de atención de la actividad prevista en una cita [F02]. Se usa como referencia para esta separación, sin adoptar su ciclo hospitalario completo.

### 5.2 Ámbito por cuenta

R01 · Base A04. Cada registro clínico debe identificar la ficha autorizada dentro de su cuenta. La relación debe impedir cruzar cuentas también en el diseño físico. Una referencia global de paciente, profesional o documento nunca basta para leer historia ajena.

Dos cuentas pueden registrar hechos semejantes sobre una persona. Cada cuenta conserva su fuente, fecha y responsabilidad; una edición no debe propagar cambios por compartir identidad. Un futuro intercambio requerirá un contrato propio, sin crear ahora un almacén global clínico.

Dentro de la cuenta, varias consultas pueden relacionarse con la misma condición o plan. Las vistas de resumen se obtienen de los registros vigentes y su historia; no se editan como otra copia que pueda discrepar.

### 5.3 Motivo y servicio

R02 · Base A05. El paciente puede decir «me salió un moretón en el cuello y quiero revisarlo» sin identificar un diagnóstico, servicio o especialidad. El personal puede registrar ese motivo y después organizar la atención y duración.

El contrato actual exige `serviceId` al crear cita y conserva referencias de nombre/duración. O03 conserva esa obligación y no cambia disponibilidad, validación, duración o snapshots. El motivo en palabras del paciente pertenece a una atención sin cita; no se convierte en una reserva incompleta ni autoriza autorreserva del Hub.

La razón breve usada para coordinar puede necesitar una proyección distinta del relato clínico completo. Conservar origen y autor de cada entrada; una clasificación posterior no debe reemplazar silenciosamente las palabras registradas. No se autoriza por este acuerdo una nueva ruta de autorreserva del paciente en el Hub.

## 6. Datos de referencia: etapa 1

### 6.1 Nacimiento, edad y sexo

R03 · Base A07–A08. Reutilizar la fecha de nacimiento de la ficha por cuenta. Calcular la edad para el momento pertinente: hoy en el resumen y fecha de atención o medición en la historia. Corregir nacimiento no debe reescribir hechos clínicos; los derivados que dependan de él deben poder recalcularse e identificar qué versión de datos usaron.

Si falta nacimiento o su precisión no permite un cálculo, mostrar esa limitación. No inventar un día o mes ni convertir una edad declarada en una fecha exacta. Para etapa 1 se conserva la fecha completa opcional existente y no se añade nacimiento parcial, conforme a §4.1.1. Las fechas históricas de condiciones y alergias sí admiten precisión variable.

El usuario pidió sexo como dato del paciente. Para etapa 1 se registra sexo al nacer, opcional y con fuente, conforme a §4.1.1. No inferirlo del nombre, documento ni género administrativo. FHIR [Patient, §8.1.9](https://hl7.org/fhir/R5/patient.html) distingue usos administrativos y clínicos [F01]. Esa referencia ayuda a formular la decisión; no impone un catálogo nuevo al producto.

Para las curvas pediátricas se debe definir el dato que permite elegir una referencia aplicable y qué hacer si falta. No usar el campo sexo sin haber fijado su significado para ese cálculo.

### 6.2 Condiciones, diagnósticos y enfermedad

R04 · Base A02 y A06. Propuesta de diseño: mantener un conjunto de problemas o condiciones del paciente y relacionar con ellos los diagnósticos que el profesional registra durante una atención. La palabra enfermedad de la lista inicial queda cubierta por ese análisis; no justifica otra lista paralela con el mismo contenido.

Cada registro debe poder expresar su descripción, fuente, fechas conocidas de inicio/fin y responsable de registro. Separar dos aspectos: si el problema sigue vigente y qué certeza tiene la afirmación. Los conjuntos exactos de estados, su transición y la codificación médica se decidirán en O05. No copiar enumeraciones de FHIR sin revisar los casos propios.

El resumen de condiciones activas se obtiene de esos registros. Resolver una condición conserva lo sucedido; corregir una atribución errónea no equivale a que el paciente se recuperó. Un problema pasado puede seguir siendo pertinente como antecedente. Una recurrencia necesita mantener la relación con lo anterior sin borrar episodios.

Ejemplo ficticio: el paciente comunica un diagnóstico previo. El profesional registra esa información y su fuente; después puede revisarla. El sistema no convierte el texto de una nota o un valor de laboratorio en otra condición. FHIR [Condition](https://hl7.org/fhir/R5/condition.html) separa estado clínico y verificación y contempla problemas y diagnósticos [F03].

### 6.3 Alergias e intolerancias

R05 · Base A06 y A08. Registrar alergias como información consultable por separado, con sustancia o producto descrito, reacción conocida, fuente y estado de revisión. Fechas, gravedad y otros detalles solo cuando se conozcan y el diseño los contemple; no exigir datos que el paciente no pueda aportar para guardar una declaración.

Propuesta: distinguir una alergia declarada de una revisada por el profesional y conservar correcciones. La reacción ocurrida y el riesgo de otra reacción pueden necesitar datos distintos. FHIR [AllergyIntolerance](https://hl7.org/fhir/R5/allergyintolerance.html) aporta esa referencia [F04]. La inclusión detallada de intolerancias y sus estados queda en O05; no tratar todo efecto adverso como alergia.

Mostrar alergias y condiciones en el contexto del paciente puede ayudar al profesional a decidir. No atribuir al sistema un control de interacciones o contraindicaciones que aún no existe.

### 6.4 Ausencia, desconocimiento y revisión

R06 · Propuesta que desarrolla A08 y el registro de información opcional. Debemos distinguir al menos los significados siguientes, aunque sus códigos y presentación queden por diseñar:

| Situación | Significado que conserva el sistema |
|---|---|
| Sin información registrada | El sistema aún no tiene datos; no afirma ausencia clínica |
| No preguntado | No se realizó esa consulta al paciente |
| Desconocido o no disponible | No se puede establecer la información con lo disponible |
| Sin elementos conocidos tras revisión | Una persona lo indicó o revisó; conservar fuente y momento |
| Con registros | Hay elementos concretos que consultar, con su propio estado |

Una lista vacía nunca establece por defecto «sin alergias». Al añadir una alergia después de una revisión previa, el resumen vigente debe seguir siendo coherente y conservar la revisión anterior en su contexto. El contrato concreto evitará combinaciones contradictorias. FHIR [List Empty Reasons](https://hl7.org/fhir/R5/valueset-list-empty-reason.html) distingue ausencia conocida, no preguntado y falta de información [F05].

## 7. Registro clínico habitual: etapa 2

### 7.1 Atención y relato del problema actual

R07 · Base A03 y A05. Propuesta de contenido de una atención: paciente/cuenta, profesional, participantes permitidos, momento o intervalo de atención, motivo, historia del problema actual, hallazgos, valoración e indicaciones, según las funciones disponibles. Los campos clínicos no deben imponerse todos como obligatorios para guardar.

La historia del problema actual —History of Present Illness— describe cuándo comenzó lo que motiva la atención, cómo cambió y el contexto que el profesional considera pertinente. Es distinta de los antecedentes generales y del motivo breve de contacto. Se puede iniciar con texto; una estructura posterior debe partir del uso y conservar lo registrado.

La fecha de cita y la de atención pueden diferir. El cierre administrativo de una cita no finaliza por deducción una nota ni crea toda una consulta clínica. O02/O06 fijan que registrar la atención afirma que ocurrió, sin ciclo de cierre; las correcciones usan versiones y la anulación por error es terminal.

### 7.2 Notas sobre el paciente

R08 · Base A02–A03 y A09. Son notas que el médico o asistente autorizado escribe sobre el paciente. No se presupone que las escribe el paciente ni que son mensajes de un chat. Pueden vincularse con una atención; las observaciones que no pertenezcan a una deben poder guardarse desde la ficha.

Guardar contenido, autor, momento de registro y cambios. Evitar una sola columna cuyo contenido nuevo destruya todo lo anterior. El médico debe poder leer, editar y guardar sin copiar versiones ni rellenar siempre un motivo de corrección. La interfaz puede mostrar el historial cuando se necesite; el mecanismo exacto se resolverá en O06.

Ejemplo ficticio: durante una revisión dermatológica el profesional observa algo en el ojo y lo anota. El sistema conserva observación y contexto. Registrar una condición, una derivación o un seguimiento será una acción del profesional; escribir la nota no ejecuta esas decisiones.

### 7.3 Mediciones y signos vitales

R09 · Base A08–A09 y A14. Cada toma conserva qué se midió, su valor y unidad, fecha del hecho, fecha de registro, autor y estado de validez. El contexto necesario puede incluir método o lugar de medición cuando afecte a su interpretación. El plan elegirá los datos mínimos por tipo; no se crea un formulario universal con todos los campos posibles.

O07 fija como alcance inicial peso, presión arterial, temperatura, saturación de oxígeno y frecuencia cardíaca, con unidades fijas. Talla/longitud, perímetro cefálico, frecuencia respiratoria, IMC y curvas quedan fuera de etapa 2. Las demás filas de la tabla son referencias futuras, no mediciones aprobadas para esta entrega.

Selección propuesta de unidades iniciales a partir de FHIR [Vital Signs](https://hl7.org/fhir/R5/observation-vitalsigns.html) [F07]:

| Medición | Presentación | Código UCUM | Código LOINC de referencia |
|---|---|---|---|
| Peso | kg | `kg` | `29463-7` |
| Talla o longitud, según método | cm | `cm` | `8302-2`; revisar detalle de longitud |
| Temperatura | °C | `Cel` | `8310-5` |
| Presión arterial sistólica | mmHg | `mm[Hg]` | `8480-6` |
| Presión arterial diastólica | mmHg | `mm[Hg]` | `8462-4` |
| Frecuencia cardíaca | latidos/min | `/min` | `8867-4` |
| Saturación de oxígeno | % | `%` | `2708-6`; conservar método cuando proceda |
| Perímetro cefálico | cm | `cm` | `9843-4` |
| Frecuencia respiratoria | respiraciones/min | `/min` | `9279-1` |
| IMC calculado | kg/m² | `kg/m2` | `39156-5` |

La tabla fija una referencia para el diseño: no declara exportación FHIR ni un catálogo médico ya instalado. El código para presión agrupada es `85354-9`; sus dos componentes deben conservar la relación de una misma toma. Si falta uno, reflejarlo sin inventar un cero. La frecuencia cardíaca y la saturación son datos distintos aunque procedan del mismo dispositivo.

La unidad visible viene elegida. Si se admiten unidades alternativas, conservar el valor/unidad recibidos y una conversión definida para cálculos, sin pérdidas silenciosas ni cambios por formato regional. Validar tipo, unidad y límites de captura; los umbrales clínicos o avisos requieren fuente y revisión propia. No eliminar de forma automática un valor solo por ser extremo.

IMC es un derivado: necesita peso y talla adecuados para el mismo cálculo. No mezclar sin regla una talla antigua con un peso nuevo. Las reglas de asociación y precisión corresponden a O07/O11. FHIR [Observation](https://hl7.org/fhir/R5/observation.html) sirve de referencia para hechos medidos [F06].

### 7.4 Vacunas

R10 · Base A06 y A08. Registrar la vacuna recibida o comunicada como antecedente, su fecha con la precisión disponible y la fuente. Según el caso, el plan puede incluir producto, dosis, lote, vía, lugar o profesional que la administró; no exigirlos para toda entrada histórica desconocida.

Distinguir lo administrado en la propia atención de lo que el paciente o un documento informa. Una fecha de carga actual no debe presentarse como fecha de vacunación histórica. La corrección conserva el dato anterior y actualiza la vista vigente.

FHIR [Immunization](https://hl7.org/fhir/R5/immunization.html) contempla vacunación actual e histórica [F08]. Una recomendación de vacuna no acredita administración. Calendarios, evaluación de esquema y avisos quedan pendientes de alcance, no implícitos en este registro.

### 7.5 Antecedentes e historial médico

R11 · Base A06. El historial es una vista de la información disponible: atenciones, notas, condiciones, alergias, mediciones y vacunas; después añadirá medicación, planes y resultados. Debe permitir seguir fechas y consultar el detalle permitido de cada hecho sin duplicarlo como otro texto editable global.

Los antecedentes narrados también son información registrable. El plan debe decidir cómo recoger antecedentes personales, familiares y otros pertinentes sin atribuir al paciente la enfermedad de un familiar. Su alcance y estructura están en O08. La presencia de un relato histórico no obliga a codificar cada frase ni crea condiciones por análisis automático.

Las vistas deben distinguir información vigente, pasada, corregida y anulada, con filtros claros. Un registro corregido puede consultarse en trazabilidad; no debe mostrarse como otra medición válida en una curva.

### 7.6 Última visita

R12 · Base A07 y O02. Calcularla desde `occurredAt` de la última atención válida de la cuenta/paciente. El resumen identifica `scope=account` y permite acceder a la atención autorizada. No depende de cita, nota, fecha de aceptación remota ni cierre.

Una cita futura, cancelada, ausente o una ficha recién editada no acreditan visita. Una nota fuera de consulta no cambia el dato. Anular la última atención obliga a recalcular desde las demás atenciones válidas.

## 8. Funciones completas: etapa 3

### 8.1 Medicación declarada

R13 · Base A12. Registrar qué medicamento comunica el paciente que usa o usó, su fuente, periodo conocido y detalles disponibles. Permitir información incompleta identificada como tal: no inventar dosis, frecuencia, fecha de inicio o prescriptor para completar un formulario.

Propuesta de diseño: revisión de la lista con el profesional, cambios de uso y corrección de errores con historia. Registrar lo declarado conserva su origen aunque después el profesional lo revise. La toma real, la entrega por farmacia y la indicación son hechos distintos; el alcance inicial no incluye controlar dispensación o cada administración.

FHIR [MedicationStatement](https://hl7.org/fhir/R5/medicationstatement.html) distingue el relato de uso de las órdenes y administraciones [F09]. La medicación que otro profesional indicó puede ser relevante aunque no exista una receta propia en Nightingale.

### 8.2 Prescripción

R14 · Base A12. Función completa para preparar indicaciones de medicamentos y conservar lo que se emitió. El plan debe fijar identificación de producto o principio activo, forma/concentración cuando proceda, dosis, unidad, vía, frecuencia, duración, cantidad e instrucciones, con las reglas de obligatoriedad de cada caso.

Hay que distinguir preparación, emisión, sustitución y anulación. Los estados exactos, quién puede emitir y la representación del documento se resolverán en O09. Una corrección posterior debe conservar el contenido emitido y permitir conocer cuál lo sustituye. Editar un catálogo no debe alterar una receta previa.

FHIR [MedicationRequest](https://hl7.org/fhir/R5/medicationrequest.html) aporta la referencia de orden e instrucciones de medicamentos [F10]. Emitir no prueba que el paciente lo recibió o lo tomó. El plan resolverá si una receta permite preparar una entrada vinculada de medicación declarada, sin afirmarla como consumo por defecto.

Esta especificación no elige un catálogo farmacológico, firma electrónica, proveedor de recetas ni normativa territorial. Esos requisitos se comprobarán al fijar su alcance; la documentación actual no acredita validez de una receta para cualquier país.

### 8.3 Tratamiento y plan de cuidados

R15 · Base A11. El tratamiento expresa intervenciones e indicaciones para atender un problema. Puede incluir medicamentos, procedimientos y otras medidas. El plan organiza el cuidado en el tiempo y puede reunir varios tratamientos, actividades, pruebas, controles y objetivos.

Propuesta de contenido del plan: paciente/cuenta, autor y participantes, finalidad, problemas relacionados, periodo previsto, objetivos, acciones, responsables, estado y revisiones. No todos los planes requieren una condición concreta; puede existir un plan preventivo. El plan de desarrollo decidirá si tratamiento requiere entidad propia o relaciones con otras indicaciones, evitando dos listas con información repetida.

Cada objetivo debe expresar qué se busca y cómo se revisará. Si es medible, conservar referencia inicial cuando exista, resultado esperado, unidad, plazo y mediciones relacionadas. Los objetivos narrativos deben poder evaluarse mediante revisión profesional; no forzar un número inventado.

Ejemplo de uso sin recomendación clínica: el profesional acuerda una actividad con el paciente, fija cuándo la revisará y registra después lo que este comunica y las mediciones disponibles. El sistema muestra cambios y revisiones; marcar la actividad como hecha no demuestra por sí solo que se logró el objetivo.

La evolución conserva las versiones del plan y las revisiones fechadas. Una nueva indicación puede sustituir otra sin borrarla; cerrar, suspender o cancelar necesita transiciones acordadas en O10. Cumplimiento de una actividad y resultado del objetivo son datos distintos.

FHIR [CarePlan](https://hl7.org/fhir/R5/careplan.html) describe la organización de cuidados [F11]; [Goal](https://hl7.org/fhir/R5/goal.html) distingue el resultado que se busca y su evaluación [F12]. Se usan para revisar los conceptos y relaciones; el modelo de Nightingale responderá a sus casos de uso.

### 8.4 Laboratorio e informes

R16 · Base de alcance inicial y A06. Separar el informe original de los resultados con estructura. El informe tiene fuente, paciente/cuenta, fechas pertinentes, estado y contenido o archivo. Cada resultado identifica qué se midió, su valor —numérico o de otro tipo permitido—, unidad cuando corresponda y contexto de interpretación.

Distinguir fecha de muestra o estudio, emisión y carga cuando se conozcan. Los intervalos de referencia deben proceder del informe o de una fuente identificada; no aplicar uno universal por nombre de prueba. Conservar resultado preliminar, final y corrección con sus relaciones según O12.

Un PDF permite consultar lo recibido; los valores estructurados permiten comparar. Subirlo no acredita que sus datos se hayan extraído o comprobado. Si se plantea extracción automática, deberá tener alcance, revisión y pruebas propios; esta especificación no la da por acordada.

Los adjuntos necesitan almacenamiento privado y autorización de lectura/descarga por cuenta. El plan debe resolver carga fallida, archivo sin vínculo, límites, retención y recuperación, sin llamadas de red dentro de la aceptación transaccional. No exponer archivos por conocer una URL o por el acceso público del micrositio.

FHIR [DiagnosticReport](https://hl7.org/fhir/R5/diagnosticreport.html) relaciona informe y resultados [F13]; [Observation](https://hl7.org/fhir/R5/observation.html) aporta la referencia para resultados individuales [F06]. Registrar resultados no confirma una integración con laboratorios externos.

### 8.5 Plantillas y funciones por especialidad

R17 · Base A13. Una plantilla ordena el registro para un uso clínico concreto. Puede sugerir secciones y campos; no debe rellenar hallazgos normales, diagnósticos o respuestas que el profesional no registró. Reducir escritura repetida no permite inventar hechos.

Propuesta de diseño: identificar plantilla y versión; conservar el significado de los registros creados con versiones anteriores. Cambiar una plantilla no debe borrar campos históricos ni reinterpretar sus valores. Las partes comunes se relacionan con notas, condiciones y mediciones ya disponibles.

Un odontograma es el ejemplo de una función que puede superar una plantilla: puede necesitar identificación de pieza y superficie, hallazgos, actuaciones y evolución. Su sistema de numeración y casos se definirán en un plan propio. El ejemplo no aprueba ya su diccionario, implantes, dentición u otros detalles.

O13 debe decidir primeras especialidades, plantillas definidas o editables, quién las configura, tipos de campo y límites. No se deduce un editor libre ni un almacén genérico de JSON clínico. El número de tablas no decide por sí solo la división de funciones; la decide el recorrido y su integridad.

### 8.6 Analítica histórica individual y crecimiento pediátrico

R18 · Base A14. Consultar evolución del paciente mediante series de mediciones válidas y, donde proceda, comparación con referencias. Esta analítica pertenece a la etapa 3 y es distinta de los indicadores generales de actividad de la consulta o de la analítica poblacional prevista en otros documentos.

El seguimiento pediátrico debe poder representar mediciones del niño junto a curvas de referencia aplicables. La OMS publica [patrones de crecimiento infantil](https://www.who.int/tools/child-growth-standards/) [W01] y una [referencia para 5–19 años](https://www.who.int/tools/growth-reference-data-for-5to19-years/) [W03]. Sus indicadores tienen límites propios; O11 elegirá los indicadores de la primera entrega y el método de cálculo.

| Referencia | Ámbito que documenta la fuente | Uso previsto para el diseño |
|---|---|---|
| Patrones OMS de 2006 | 0–60 meses; indicadores como peso/edad, longitud o talla/edad, peso/longitud o talla e IMC/edad | Elegir curva según indicador, datos y edad; revisar método de longitud/talla [W01–W02] |
| Referencia OMS de 2007 | 61–228 meses; talla/edad e IMC/edad dentro del ámbito 5–19 años | Seguir edades posteriores con la referencia adecuada [W03–W04] |
| Peso/edad de la referencia 2007 | Su ámbito publicado es 5–10 años | No extender esta curva a todas las edades de 5–19 [W05] |

Requisitos de diseño para la función:

1. Calcular la edad en la fecha de cada medición, con la precisión y método exigidos por la fuente. No usar la edad de hoy para puntos pasados ni inventar fecha cuando falta.
2. Elegir la curva solo cuando se conocen los datos que necesita. Identificar referencia y versión; no deducir de forma silenciosa un dato clínico o demográfico faltante.
3. Usar mediciones válidas, unidades compatibles y el método de toma cuando influya. No interpolar ni sustituir datos ausentes sin una regla aprobada.
4. Mostrar valor original, fecha y referencia utilizada. Percentil y puntuación z son derivados identificables, no sustitutos de la medición.
5. Corregir una medición, nacimiento u otro dato de entrada debe invalidar o recalcular los resultados derivados afectados. Conservar qué entradas/versiones y método produjeron un cálculo cuando se guarde.
6. Excluir del cálculo ordinario el valor registrado por error, manteniéndolo accesible en trazabilidad. No ocultar valores extremos válidos solo por separarse de la referencia.
7. Si el dato no permite comparar, mostrar la medición y explicar qué falta. No producir un valor inventado ni aplicar una curva fuera de rango.
8. Contrastar los cálculos con casos de referencia oficiales y límites de edad; probar correcciones y versiones. La apariencia de una gráfica no acredita exactitud numérica.

Propuesta: acompañar la serie con percentiles o puntuaciones z cuando el indicador los soporte, sin imponer ambos en toda vista. La interpretación y las decisiones corresponden al profesional. Umbrales de aviso, prematuridad/edad corregida, límites exactos de cambio de referencia, redondeo, precisión y actualización de métodos quedan en O11. No se fijan aquí fórmulas ni recomendaciones clínicas.

La OMS ofrece [herramientas de cálculo y documentación](https://www.who.int/tools/child-growth-standards/software) [W06]. Revisarlas no elige una biblioteca ni autoriza enviar datos del paciente a otro servicio. La selección técnica se justificará con las versiones disponibles al implementar.

## 9. Reglas comunes de entrada, tiempo y cambios

### 9.1 Entrada breve y fechas automáticas

R19 · Base A08. La entrada habitual debe pedir el dato clínico y completar el momento actual, autor autenticado y unidad inicial. Esos datos técnicos no obligan al médico a escribir fecha/hora exactas, su nombre o códigos de unidad en cada acción.

Propuesta para el modelo de tiempo:

| Tiempo | Uso | Entrada habitual |
|---|---|---|
| Momento del hecho | Cuándo se tomó la medida, ocurrió la atención o se recibió una vacuna | Momento actual por defecto; el usuario puede indicar que ocurrió antes |
| Momento de registro | Cuándo se añadió el dato en el sistema de origen | Automático; conservar el origen de la marca |
| Momento de aceptación remota | Cuándo API confirmó la operación | Reloj del servidor; no sustituye al momento del hecho |

Si el dato histórico solo se conoce por día, mes, año o intervalo, el diseño debe conservar esa precisión en los tipos que lo admitan. No completar con el primer día del mes y presentarlo como exacto. Cada función decidirá si admite fecha parcial; un cálculo que exige precisión mayor deberá mostrar esa limitación. El valor por defecto y el origen de una fecha también deben distinguirse de una fecha histórica aportada expresamente.

En operación sin red, conservar la marca de captura del dispositivo y la posterior aceptación del servidor. La hora del equipo es un dato reportado que API valida; nunca acredita permisos anteriores ni orden de commit. El contrato debe definir cómo resolver relojes desajustados, fechas futuras y zonas sin perder la intención local. Las fechas clínicas no heredan la precisión de minuto de las reservas por deducción.

### 9.2 Nueva toma, corrección y anulación

R20 · Base A09. El caso de uso debe expresar qué acción realiza la persona; no resolverlo mediante sustitución ciega del último valor.

| Acción | Ejemplo ficticio | Efecto esperado |
|---|---|---|
| Nueva toma | Peso de 70 kg y, una semana después, 69 kg | Dos hechos válidos; el más reciente según fecha del hecho alimenta el resumen |
| Corrección | Se escribió 700 kg y se corrige a 70 kg | Un hecho con contenido corregido e historia; 700 no aparece como otro punto válido |
| Anulación por error | La toma correspondía a otro paciente | Retirar del uso clínico ordinario con constancia; resolver atribución según regla aprobada, sin moverla silenciosamente a otra ficha |
| Cambio clínico | El profesional da por resuelta una condición | Nueva información sobre su evolución; no equivale a borrar un error de captura |

Conservar autor, momento y valores anteriores de la corrección. Un motivo puede ser útil en casos concretos; no se aprueba pedirlo siempre para toda edición. El detalle del historial y cuándo exigir motivo se resolverá por tipo en O06. La vista vigente y las gráficas deben consultar solo versiones válidas, sin perder la trazabilidad.

Una medición histórica cargada hoy no es necesariamente la más reciente del paciente. Si empatan fechas o la precisión no permite ordenarlas, el plan debe definir presentación y desempate sin afirmar un orden clínico que no conoce.

### 9.3 Guardado y finalización

R21 · Base A08–A09. Guardar una nota puede conservar versiones de forma automática. No se exige al médico archivar manualmente cada versión ni completar un trámite de firma/cierre en cada entrada.

La atención clínica, la receta emitida y el informe pueden necesitar ciclos distintos. Cada plan debe definir cuáles permiten edición, cuáles requieren sustitución o adenda y cómo se consulta el original. O06/O09/O12 mantienen esos detalles abiertos; no trasladar las reglas terminales de una cita a toda información clínica.

### 9.4 Fuente, autor y registros relacionados

R22 · Propuesta que desarrolla A02, A04 y A08. Conservar quién informó y quién registró cuando son personas distintas: paciente, responsable, profesional o documento externo. API obtiene el autor de su contexto autenticado. La fuente declarada es información del registro, no una credencial ni prueba automática de veracidad.

Cuando una vista muestra un resumen o una nota referencia una condición, debe poder consultarse el registro de origen permitido. Reutilizar relaciones dentro de la cuenta y conservar valores emitidos o históricos cuando su función lo requiera. No actualizar recetas, notas previas o informes emitidos al editar después un nombre de catálogo.

## 10. Acceso, sincronización e integración

### 10.1 Permisos configurables por cuenta

R23 · Base A10 y O14. El médico y su asistente son los usuarios principales. Además de las secciones de etapa 1, atenciones, notas, mediciones, vacunas y antecedentes tienen niveles independientes por asistente, sin crear un sistema general de roles. El historial integrado filtra cada fuente por su permiso antes de contar o paginar.

La matriz que deberá resolver el plan distingue lectura, alta, corrección/anulación, revisión clínica y acciones de emisión o cierre que la función requiera. Debe definir quién cambia esa configuración y sus valores iniciales. Las acciones concretas se diseñan por función: por ejemplo, registrar una medición y emitir una receta pueden necesitar permisos distintos.

API verifica cuenta, ficha y acción con los permisos vigentes. El acceso administrativo a una cuenta no decide por sí solo toda la nueva matriz clínica; tampoco el permiso para gestionar citas debe ampliar el acceso al añadir campos a una respuesta existente. Ajustes de permiso deben afectar a lecturas, resultados previos, búsquedas, adjuntos, derivados y sincronización.

El micrositio público del Hub continúa limitado a publicación; sus acciones limitadas sobre una cita no conceden acceso a notas, condiciones o historia clínica. No se incorpora aquí un portal de historia para pacientes ni cuentas de paciente.

### 10.2 Escrituras y conflictos

R24 · Desarrollo de A04, A09 y las reglas transaccionales existentes. Reutilizar el mecanismo de operaciones tipadas, versión esperada, idempotencia y resultados autorizados para las nuevas acciones. No ofrecer escritura libre de todas las columnas ni una nueva vía que eluda la aceptación.

Cada operación debe conservar su efecto y versiones, historia requerida, resultado recuperable, auditoría y cambios de sincronización juntos. Una respuesta perdida se consulta o reintenta con la misma identidad, sin crear otra toma o receta para averiguar qué ocurrió. Las restricciones y carreras se probarán en PostgreSQL real aislado.

Dos mediciones independientes son dos hechos; dos ediciones del mismo registro pueden entrar en conflicto. Una versión antigua no sobrescribe la nueva. El plan debe mostrar cómo revisar esa intención sin fusionar texto clínico de forma automática. Los rechazos y la revocación de permisos conservan la intención local según las reglas actuales del consumidor.

### 10.3 Descarga, datos locales y derivados

R25 · Propuesta que desarrolla A04, A10 y A14. Definir proyecciones clínicas autorizadas y un alcance explícito de descarga. La audiencia actual owner/members y la ventana de citas no bastan por deducción para los nuevos permisos y datos.

Una alergia o condición vigente no desaparece porque su fecha de registro quede fuera de la ventana de citas. O15 fija para etapa 2 la descarga de atenciones válidas, versión actual válida de notas/antecedentes, todas las tomas válidas y vacunas vigentes, sin historias de versiones ni adjuntos. Ningún hecho se filtra por la ventana de citas; se aplican los mismos permisos en captura y delta.

La retención técnica actual de cambios/resultados de 90 días no fija la vida de la historia clínica. O15 debe resolver retención y recuperación por clase de dato y sus copias. Vencer un cursor o retirar un resultado técnico no borra una medición, una nota o una receta funcional.

Los derivados, como última visita, valores más recientes y curvas, deben depender de los registros válidos y de versiones identificables. La interfaz debe distinguir datos locales pendientes de aceptación cuando eso afecte a la lectura. La aplicación atómica de datos y posición de sincronización en SQLite sigue siendo responsabilidad del escritorio; este documento no acredita ese consumidor.

### 10.4 Propiedad de fuentes y cambios que necesitarán los planes

| Área | Fuente actual | Trabajo futuro que debe concretarse |
|---|---|---|
| Datos físicos | [database-schema.md](database-schema.md) | Nuevas relaciones clínicas por cuenta, referencias, estados, versiones, historia, índices y conservación |
| Comportamiento y contratos remotos | [api-v1.md](api-v1.md) y [contracts.md](contracts.md) | Acciones tipadas, respuestas/proyecciones clínicas y compatibilidad con consumidores |
| Organización de componentes | [architecture.md](architecture.md) | Propietarios concretos de cada capacidad y dependencias; evitar convertir patients o core en un contenedor de todo |
| Acceso | [access-design.md](access-design.md) | Configuración clínica y autorización por acción, incluidas lecturas y descargas |
| Calidad | [quality.md](quality.md) | Casos clínicos, errores/correcciones, datos faltantes y exactitud de derivados |
| Escritorio | Repositorio Nightingale, fuera de este encargo | Registro local, UI, conflictos y sincronización del nuevo contrato mediante una tarea autorizada en ese repositorio |
| Hub | D11 y su futuro contrato limitado | Conservar límites de publicación y cita; no añadir acceso clínico por deducción |

No se define aquí otro diccionario SQL ni una segunda lista de rutas. Los nombres de futuros componentes, tablas y acciones quedan para sus planes y fuentes. Al ampliar un contrato, deben conservarse ausencia frente a null, validación única y tipos explícitos, camelCase público y paginación existente, sin romper recuperación incremental.

## 11. Casos de aceptación y trazabilidad para los planes

Estos casos son comprobaciones futuras. Ninguno consta ejecutado por escribir esta especificación. Los planes deberán transformarlos en tareas pequeñas con evidencia de dominio, persistencia, HTTP y consumidores según corresponda.

| Caso | Etapa / requisitos | Resultado esperado |
|---|---|---|
| E01 · Misma identidad en dos cuentas | 1; R01/R23 | Una cuenta no ve ni cambia la historia clínica de la otra, tampoco por búsqueda, error o resultado previo |
| E02 · Alta administrativa sin datos clínicos | 1; R03–R06 | Permite los flujos administrativos actuales; no inventa sexo, condiciones o ausencia de alergias |
| E03 · Edad en una medición antigua | 1 y 3; R03/R18 | Usa nacimiento y fecha del hecho; dato insuficiente produce límite explícito |
| E04 · Añadir y resolver una condición | 1; R04 | El resumen cambia y conserva la evolución; corrección por error tiene un significado distinto |
| E05 · Lista de alergias vacía | 1; R05–R06 | No afirma «sin alergias»; distingue una revisión posterior y su fuente |
| E06 · Revisión sin conocer el servicio | 2; R02/R07 | Permite registrar motivo con palabras del paciente; el recorrido de reserva sigue la decisión de O03 |
| E07 · Nota del dermatólogo | 2; R08 | Guarda observación con autor/fecha; no crea un diagnóstico ni otro efecto clínico automático |
| E08 · Dos pesajes válidos | 2; R09/R20 | Conserva ambos; la toma más reciente alimenta el resumen sin borrar la anterior |
| E09 · Corrección de 700 a 70 kg | 2 y 3; R09/R18/R20 | La serie usa 70; conserva versión anterior y autor; recalcula derivados afectados |
| E10 · Dato histórico añadido hoy | 2; R19–R20 | Conserva fecha del hecho y de registro; no reemplaza un dato más reciente solo por orden de carga |
| E11 · Trabajo sin conexión | 2; R19/R24–R25 | Conserva captura e intención; aceptación remota no cambia silenciosamente la fecha clínica |
| E12 · Presión con un componente desconocido | 2; R09 | No inventa un cero ni mezcla componentes de tomas distintas |
| E13 · Vacuna antigua comunicada | 2; R10 | Conserva fuente y precisión; no afirma una administración actual |
| E14 · Última visita | 2; R12 | Atiende al alcance y estado acordados; cita futura, ausencia o edición de ficha no cuentan |
| E15 · Medicamento indicado por otro médico | 3; R13 | Puede constar como uso declarado sin receta propia; conserva incertidumbre de los datos |
| E16 · Receta nueva o sustituida | 3; R14 | Conserva lo emitido y su relación con la sustitución; no prueba consumo |
| E17 · Seguimiento de plan | 3; R15 | Conserva objetivos, acciones y revisiones; completar actividad no equivale a lograr objetivo |
| E18 · Informe corregido | 3; R16 | Distingue original, corrección y resultados vigentes; no duplica puntos válidos |
| E19 · Cambio de plantilla | 3; R17 | Registros previos mantienen significado y versión; no genera hechos normales por defecto |
| E20 · Curva fuera de rango | 3; R18 | No aplica la referencia; explica el límite y conserva la medición |
| E21 · Cambio de nacimiento o entrada de cálculo | 3; R03/R18 | Invalida o recalcula derivados con entradas/versiones identificables |
| E22 · Dos ediciones y respuesta perdida | Todas; R20/R24 | Sin sobrescritura de versión ni repetición del efecto; resultado autorizado recuperable |
| E23 · Permiso clínico retirado | Todas; R23–R25 | Impide lecturas/acciones remotas y recuperación de resultados fuera de alcance; no filtra por sync |
| E24 · Alergia anterior a ventana de citas | 1–3; R25 | Sigue disponible en el resumen autorizado; retención de sync no borra historia funcional |

Para una etapa revisable, el plan debe indicar qué casos entrega, cuáles dependen de otra y qué evidencia falta. La aceptación de una etapa no acepta las siguientes ni acredita todas las especialidades.

## 12. Decisiones abiertas y preparación de los planes

Los identificadores Oxx siguientes pertenecen solo a esta especificación. Al citarlos fuera de ella, usar «patient-clinical-record Oxx» para distinguirlos de los pendientes históricos de decisions.md.

| ID | Decisión necesaria | Antes de |
|---|---|---|
| O01 | **Resuelto para etapa 1:** sexo al nacer opcional, con valores y fuente definidos en el plan. La elección de curvas pediátricas conserva sus reglas para etapa 3 | Campo aprobado; revisión de curvas en etapa 3 |
| O02 | **Resuelto para etapa 2:** atención real sin ciclo de cierre, sin cita obligatoria, varias por cita y última visita desde atenciones válidas de la cuenta/paciente | Revisión del diseño en C01 |
| O03 | **Resuelto para etapa 2:** `serviceId` obligatorio al reservar; motivo de atención sin cita no cambia disponibilidad, duración ni snapshots | Revisión del diseño en C01 |
| O04 | **Resuelto para etapa 1:** nacimiento completo opcional existente; fechas históricas opcionales completas o parciales y sus reglas. Otros tipos y etapas conservan su precisión por decidir | Payload y modelo de los datos afectados |
| O05 | **Resuelto para etapa 1:** estados/transiciones, texto libre, intolerancias, tipo desconocido y revisiones de información definidos en el plan | Revisión del diseño en C01 |
| O06 | **Resuelto para etapas 1 y 2:** versiones, correcciones, anulación terminal, motivos opcionales e historial aparte; atenciones/notas editables sin cierre y nueva toma distinta de corrección | Revisión del diseño en C01 |
| O07 | **Resuelto para etapa 2:** cinco mediciones con unidades fijas y límites de captura definidos en las fuentes técnicas. Talla, peso/talla, IMC y curvas quedan para etapa 3 | Revisión del diseño en C01 |
| O08 | **Resuelto para etapa 2:** detalles opcionales de vacunas y antecedentes narrativos `personal`,`family`,`other` sin efectos automáticos | Revisión del diseño en C01 |
| O09 | Catálogo farmacológico, datos/ciclo de receta, permisos de emisión y requisitos del ámbito de uso | Prescripción y medicación de etapa 3 |
| O10 | Objetivos, acciones, estados/revisiones y relación entre tratamiento, plan y otras indicaciones | Planes de cuidados |
| O11 | Indicadores OMS iniciales, métodos y versiones, precisión, rangos, límites, prematuridad, pruebas numéricas y avisos si se desean | Analítica de etapa 3 |
| O12 | Entrada de informes/resultados, correcciones, adjuntos, límites y posible integración externa | Laboratorio |
| O13 | Primeras especialidades, plantillas definidas o configurables y alcance del ejemplo odontológico | Plantillas y módulos por especialidad |
| O14 | **Resuelto para etapas 1 y 2:** permisos por asistente/sección, lectura/escritura inicial, configuración por propietario y aplicación a resultados, descargas, dispositivos e historial por fuente | Revisión del diseño en C01 |
| O15 | **Resuelto para etapas 1 y 2:** descarga opcional de hechos vigentes/válidos, todas las tomas para evolución, historial aparte y conservación funcional. Copias, recuperación, datos reales y operación conservan su política pendiente | Revisión del diseño en C01 y antes de operación con datos reales |

Los planes de desarrollo deben partir de esta especificación revisada y de las fuentes actuales de datos/contratos. Para cada entrega deben:

1. Citar acuerdos Axx y requisitos Rxx que cubren; resolver los Oxx que afecten al trabajo.
2. Recorrer casos reales con datos ficticios y elegir el cambio mínimo que permite completarlos.
3. Identificar propietario de componente, entradas, dependencias, datos/contratos y consumidores afectados.
4. Definir aceptación transaccional, historia, permisos, sincronización y recuperación, con límites concretos.
5. Añadir el diseño físico solo a database-schema.md y los contratos a su fuente correspondiente.
6. Separar evidencia del servidor, integración del escritorio y operación. Para concurrencia/integridad, usar PostgreSQL real aislado.
7. Entregar checkpoints concretos al usuario; no marcar aceptación por pasar pruebas ni iniciar otras etapas por deducción.

La secuencia de etapas fija el orden funcional general. Cada plan determinará los prerrequisitos ya disponibles y la porción completa que puede entregar; no creará tablas vacías ni abstraerá todas las especialidades por anticipación. No hay autorización de trabajo paralelo ni de cambios en otros repositorios.

## 13. Referencias y uso en esta especificación

Fuentes oficiales consultadas el **2026-11-15**. Las páginas FHIR enlazan la versión R5, 5.0.0; el alcance de Nightingale procede de §3. La documentación de recursos tiene distintos grados de madurez y no convierte todas sus opciones en requisitos del producto.

### 13.1 HL7 FHIR R5

| ID | Fuente oficial | Uso y límite |
|---|---|---|
| F01 | [Patient](https://hl7.org/fhir/R5/patient.html), en particular Patient Gender and Sex | Distinguir propósitos de los datos de sexo/género; no imponer significado al campo pendiente |
| F02 | [Encounter](https://hl7.org/fhir/R5/encounter.html) | Diferencia entre atención realizada y cita prevista; no adoptar hospitalización completa |
| F03 | [Condition](https://hl7.org/fhir/R5/condition.html) | Problemas/diagnósticos, estado clínico y grado de verificación; no derivarlos de notas |
| F04 | [AllergyIntolerance](https://hl7.org/fhir/R5/allergyintolerance.html) | Registro de riesgo de reacción y antecedentes de reacción; no equiparar todo efecto adverso con alergia |
| F05 | [List Empty Reasons](https://hl7.org/fhir/R5/valueset-list-empty-reason.html) | Diferenciar ausencia conocida, no preguntado y dato no disponible; catálogo informativo de referencia |
| F06 | [Observation](https://hl7.org/fhir/R5/observation.html) | Mediciones y resultados; no usarlo como almacén genérico de todo dato clínico |
| F07 | [Observation Vital Signs](https://hl7.org/fhir/R5/observation-vitalsigns.html) | Unidades UCUM y códigos de referencia; relación de componentes de presión arterial |
| F08 | [Immunization](https://hl7.org/fhir/R5/immunization.html) | Vacunación administrada o comunicada, actual e histórica; no implica recomendación automática |
| F09 | [MedicationStatement](https://hl7.org/fhir/R5/medicationstatement.html) | Uso de medicación comunicado o documentado, distinto de prescribir |
| F10 | [MedicationRequest](https://hl7.org/fhir/R5/medicationrequest.html) | Orden e instrucciones de medicamentos; no acredita entrega ni consumo |
| F11 | [CarePlan](https://hl7.org/fhir/R5/careplan.html) | Organización de cuidados, actividades y participantes |
| F12 | [Goal](https://hl7.org/fhir/R5/goal.html) | Objetivos y evaluación; distinguir acción y resultado |
| F13 | [DiagnosticReport](https://hl7.org/fhir/R5/diagnosticreport.html) | Informe, contexto y resultados individuales; original y datos estructurados |

### 13.2 Organización Mundial de la Salud

| ID | Fuente oficial | Uso y límite |
|---|---|---|
| W01 | [Child Growth Standards](https://www.who.int/tools/child-growth-standards/) | Patrones de crecimiento infantil y curvas hasta 60 meses |
| W02 | [Child Growth Standards: indicadores](https://www.who.int/tools/child-growth-standards/standards) | Identificar indicadores y documentación; no aprobar todos para la primera entrega |
| W03 | [Growth reference data for 5–19 years](https://www.who.int/tools/growth-reference-data-for-5to19-years/) | Referencia 2007, ámbito 61–228 meses y relación con patrones 2006 |
| W04 | [Indicadores de 5–19 años](https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/) | Talla/edad e IMC/edad; rango propio de peso/edad |
| W05 | [Weight-for-age, 5–10 years](https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/weight-for-age-5to10-years) | Límite de esta referencia; no extrapolar a adolescentes mayores |
| W06 | [WHO Anthro y otras herramientas](https://www.who.int/tools/child-growth-standards/software) | Documentación y cálculo de referencia; no seleccionar proveedor o biblioteca ni remitir datos clínicos |

Estas páginas sustentan las distinciones indicadas. No se han validado fórmulas, tablas numéricas, licencias de distribución de datasets ni implementaciones de cálculo durante este encargo. Antes de incorporar datos o código de terceros, el plan comprobará versión, método y condiciones de uso de la fuente exacta.

### 13.3 Fuentes locales y precedencia

- [Especificación API](nightingale-api.md): alcance general y evidencia histórica del núcleo.
- [Decisiones](decisions.md): D08 conserva fuente única del esquema; D09 delimita el núcleo; D10 fija arquitectura; D11 delimita Hub; D12 registra esta ampliación.
- [Esquema físico](database-schema.md): identidad mínima, ficha por cuenta, nacimiento, reservas e historia funcional de citas.
- [Contrato v1](api-v1.md): servicio actualmente requerido, acceso del personal, operaciones y recuperación; no incluye estas funciones clínicas.
- [Contratos](contracts.md), [arquitectura](architecture.md), [acceso](access-design.md) y [calidad](quality.md): reglas transversales que los planes deben conservar o revisar de forma explícita cuando el alcance las cambie.

Los acuerdos de §3 concretan la ampliación futura. Las propuestas y pendientes de este documento no borran decisiones previas ni aceptan checkpoints. Cualquier cambio posterior debe identificar qué regla sustituye y actualizar esta fuente y los planes afectados.

## 14. Revisión y evidencia

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1 | 2026-11-15 | Especificación de descubrimiento: acuerdos, tres etapas, funciones y datos, reglas comunes, integración, casos de aceptación, pendientes y fuentes oficiales |
| 0.2 | 2026-11-15 | Aprobación del plan de etapa 1 y concreción de O01, O04–O06, O14 y la parte funcional de O15; pendientes de otras etapas y operación conservados |
| 0.3 | 2026-11-16 | Corrección de alcance de resultados, estados, historial, descarga, auditoría e integridad; C01–C06 del sucesor aceptados, C07 pendiente |
| 0.4 | 2026-11-16 | Decisiones O02/O03/O06/O07/O08/O14/O15 para etapa 2; diseño pendiente de C01, sin implementación |

La comprobación de esta entrega vive en [la lista documental](../tasks/P-20261115-01-clinical-spec/todo.md). Escribir y revisar el documento no prueba la API, el escritorio, PostgreSQL, exactitud clínica, métodos de crecimiento ni producción. La aceptación de la especificación y los futuros planes corresponde al usuario.
