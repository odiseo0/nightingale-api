# P-20261117-05-clinical-stage-3: funciones clínicas completas sin prescripción

**Estado:** Completed. **Creado:** 2026-11-17. **Actualizado:** 2026-11-18. **Lista de tareas:** [todo.md](todo.md).

## 1. Contexto y resultado

El usuario pidió un plan para el resto de Etapa 3, dejando prescripción/récipes fuera porque ya tienen su propio plan aprobado. Este plan cubre cinco bloques de [patient-clinical-record.md](../../docs/patient-clinical-record.md):

1. Medicación declarada.
2. Tratamiento y planes de cuidados.
3. Informes y resultados de laboratorio/diagnóstico.
4. Plantillas y una primera función por especialidad.
5. Analítica histórica individual y crecimiento pediátrico OMS.

El resultado debe ser un conjunto de recorridos completos y revisables, con aislamiento cuenta/paciente, versiones, historia, permisos, sincronización y recuperación. Cada bloque termina en un checkpoint antes de continuar.

No se modifica ni sustituye [P-20261117-04-clinical-documents](../P-20261117-04-clinical-documents/plan.md). Prescripción, récipes, emisión, firma, PDF de esos documentos, QR y acceso del paciente a ellos permanecen fuera de este plan.

### 1.1 Línea base y trazabilidad registradas en T01 (2026-11-17)

**Línea base:** C09 de Etapa 2 fue aceptado el 2026-11-17 y [P-20261116-02-clinical-routine](../P-20261116-02-clinical-routine/plan.md) está Completed (publica `api-v1.3`): paciente/nacimiento/sexo, condiciones/alergias, atenciones/notas, mediciones (cinco iniciales), vacunas/antecedentes, timeline, permisos por sección, descarga y sync están comprobados hasta C09. Autorización (P-20261117-01) sigue In progress (T01 Done; T02 espera decisión AU-32; T03 Todo): sus resultados aún no se consumen; las tareas de este plan que los necesiten (p. ej. matriz de permisos en T31) esperan su cierre. Las demás decisiones pendientes de Etapa 3 se cierran en T02/T03 antes del diseño dependiente. Esta línea base no declara implementada ninguna función de Etapa 3 ni de prescripción.

**Trazabilidad bloque → caso/requisito → fase/tareas:**

| Bloque | Casos y requisitos | Acuerdos | Fase y tareas | Decisiones |
|---|---|---|---|---|
| Medicación declarada | E15; R13 | A12 | Fase 4 · T10–T12 → C04 | O09 (solo declarada) en T02 |
| Tratamiento y planes de cuidados | E17; R15 | A11 | Fase 5 · T13–T15 → C05 | O10 en T02 |
| Informes y resultados | E18; R16 | — | Fase 6 · T16–T18 → C06 | O12 en T02 |
| Plantillas versionadas | E19; R17 | A13 | Fase 7 · T19–T21 → C07 | O13 en T03 |
| Primera especialidad | recorrido elegido en T03; R17 | A13 | Fase 8 · T22–T24 → C08 | O13 en T03 |
| Series históricas y analítica individual | E03, E09; R03, R18 | A14 | Fase 9 · T25–T27 → C09 | O11 en T03 |
| Crecimiento pediátrico OMS | E20, E21; R18 | A14 | Fase 10 · T28–T30 → C10 | O11 en T03 |
| Reglas comunes (entrada, tiempo, cambios, acceso, sync) | E22, E23, E24; R19–R25 | A04, A08–A10 | Fases 11–12 · T31–T36 → C11–C12 | aplicación transversal |

**Fuera del plan:** prescripción/récipes, E16 y R14 pertenecen a [P-20261117-04-clinical-documents](../P-20261117-04-clinical-documents/plan.md), que este plan no ejecuta ni modifica. Toxicidad, recomendaciones automáticas, expediente global, conformidad FHIR e integración externa quedan excluidas según §3.6.

## 2. Precondiciones y límites

- Este documento es solo planificación. No cambia código, contratos, migraciones, pruebas ni estados del trabajo actual de Autorización.
- **Inicio anticipado autorizado el 2026-11-17:** el usuario decidió expresamente comenzar la ejecución sin esperar el cierre Completed de Autorización (P-20261117-01), que sigue In progress. Esta autorización, registrada en [D19](../docs/decisions.md), sustituye solo la espera previa de este plan: no modifica el plan de Autorización, no interrumpe su trabajo y no habilita ediciones paralelas sobre sus archivos. Las tareas que consuman el resultado final de Autorización esperan su cierre; el trabajo independiente de Etapa 3 avanza en orden secuencial.
- Antes de T01 de ejecución, C09 de Etapa 2 debe estar aceptado y su plan Completed. Etapas 1 y 2 se consideran dependencias disponibles solo según su evidencia aceptada.
- No se exige completar Suscripciones, Facturación o Documentos clínicos para este plan. Si almacenamiento/concesiones existen al ejecutar, se reutilizan; si no, la tarea afectada propone el mínimo sin iniciar esos otros planes.
- Trabajo secuencial, sin delegación ni tareas paralelas. Solo el usuario aprueba el plan y acepta checkpoints.
- No se modifica Rust/Hub ni se abre portal clínico general para pacientes. Toda integración con consumidores requiere prueba específica en su repositorio.

## 3. Alcance funcional

### 3.1 Medicación declarada

Registrar lo que el paciente informa tomar o haber tomado, incluso sin receta propia. Conservar fuente, periodo, precisión, datos incompletos, revisión y correcciones. No inferir consumo, adherencia, prescripción, dispensación o administración. Caso E15.

### 3.2 Tratamiento y planes de cuidados

Representar intervenciones, objetivos, acciones, responsables, periodos y revisiones. Permitir planes preventivos sin condición obligatoria. Separar actividad realizada de resultado del objetivo y conservar sustitución/cierre/suspensión según O10. Caso E17.

### 3.3 Informes y resultados

Separar informe original, archivo privado y resultados estructurados. Conservar fuente, fechas de muestra/emisión/carga, unidades, referencia del informe, preliminar/final y corrección. Subir PDF no prueba extracción/verdad ni integración externa. Caso E18.

### 3.4 Plantillas y especialidad

Definir plantillas versionadas que ordenan captura sin rellenar hechos normales. La primera especialidad y el posible módulo, como odontograma, se eligen en T03; no se crea un editor libre ni un almacén JSON clínico genérico. Caso E19.

### 3.5 Analítica individual y crecimiento

Consultar series de datos válidos, tendencias y referencias OMS aplicables por edad/indicador/método. Recalcular o invalidar derivados cuando cambian entradas/nacimiento. No diagnosticar ni extrapolar fuera de rango. Casos E03, E09, E20 y E21.

### 3.6 Exclusiones permanentes del plan

- Prescripción/récipes y su plan existente.
- Toxicidad.
- Recomendaciones automáticas de medicamentos, interacciones o dosis.
- Expediente global compartido entre cuentas.
- Intercambio FHIR completo o conformidad no comprobada.
- Integración con farmacias/laboratorios sin alcance propio.
- Analítica poblacional o financiera.
- Todas las especialidades a la vez.
- Datos reales, producción, copias/restauración o despliegue sin su propia operación aprobada.

## 4. Fuentes de verdad

- [Registro clínico y seguimiento](../../docs/patient-clinical-record.md): A01–A15, R13–R25, casos E03/E09/E15/E17–E21 y pendientes O09–O13.
- [D12/D13](../../docs/decisions.md) y fuentes únicas [database-schema.md](../../docs/database-schema.md), [api-v1.md](../../docs/api-v1.md), [architecture.md](../../docs/architecture.md), [access-design.md](../../docs/access-design.md) y [quality.md](../../docs/quality.md).
- Datos de Etapa 1/2: paciente/nacimiento/sexo, condiciones/alergias, atenciones/notas, mediciones/unidades, vacunas/antecedentes, timeline, permisos y sync.
- FHIR R5 `MedicationStatement`, `CarePlan`, `Goal`, `DiagnosticReport` y `Observation` como referencias conceptuales, sin adoptar todos sus recursos/rutas.
- Referencias OMS W01–W06 enlazadas en la especificación; datasets, métodos, versiones y licencias se comprobarán antes de uso.
- Planes aprobados existentes solo como referencias de arquitectura, nunca como trabajo que este plan ejecuta o modifica.

## 5. Decisiones de arquitectura

- **Propietarios por recorrido:** `medications`, `care_plans`, `diagnostic_results`, `specialties` y `analytics` son nombres lógicos propuestos que T02–T09 confirmarán; `patients` y `core` no se convierten en contenedores generales.
- **Datos tipados:** no JSON clínico libre ni tablas vacías anticipadas. Cada especialidad decide sus campos e integridad.
- **Fuente y estado:** medicación declarada no es prescripción; informe original no es resultado estructurado; actividad no es objetivo cumplido; referencia OMS no es diagnóstico.
- **Operaciones existentes:** escrituras con identidad, versión esperada, idempotencia, efecto/historia/auditoría/recibo/grupo en una transacción.
- **Archivos privados:** bytes fuera de journal/logs; descarga reautorizada y sin red dentro de la transacción.
- **Derivados reconstruibles:** series, indicadores y curvas identifican entradas/versiones/referencia. Un cambio de nacimiento o corrección recalcula/invalida de forma explícita.
- **Analítica separada:** PostgreSQL analítico y avance ETL cuando el volumen/consulta lo justifique; sin cargar aceptación operativa.
- **Sin nuevo motor de permisos:** se consume el resultado final de Autorización una vez Completed; este plan no modifica ese plan ni su trabajo en curso.

## 6. Orden de dependencias

```text
Etapa 2 C09 aceptada + Autorización Completed
  → límites y decisiones O09–O13
  → diseño físico y contratos por bloque
  → medicación declarada completa
  → tratamiento/planes completo
  → informes/resultados completo
  → plantillas versionadas y primera especialidad
  → series históricas/ETL
  → referencias OMS y crecimiento pediátrico
  → integración, carreras, contratos y cierre
```

Cada bloque deja un recorrido funcional antes de comenzar el siguiente. No se crean todas las capas de dominio/persistencia de forma anticipada sin conectar su caso real.

## 7. Fases, tareas y checkpoints

### Fase 1 · Alcance y decisiones abiertas

- [x] **T01:** Registrar línea base, límites y correspondencia de casos/requisitos.
- [x] **T02:** Cerrar medicación declarada, ciclo de cuidados e informes/resultados.
- [x] **T03:** Cerrar analítica OMS, primera especialidad, permisos, archivos y offline.

#### C01 · Alcance de Etapa 3 decidido

- [x] O09–O13 tienen decisiones propias sin reabrir prescripción.
- [x] Casos E15/E17/E18/E19/E20/E21 y dependencias están trazados.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-17.**

### Fase 2 · Diseño físico por bloques

- [x] **T04:** Diseñar físicamente medicación declarada y planes de cuidados.
- [x] **T05:** Diseñar físicamente informes, resultados y adjuntos.
- [x] **T06:** Diseñar físicamente plantillas/especialidad y analítica/derivados.

#### C02 · Integridad física revisable

- [x] Tablas propuestas conservan ámbito, versiones, historia, relaciones y conservación.
- [x] Archivos, derivados y referencias OMS tienen índices/restricciones sin JSON genérico.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-17.**

### Fase 3 · Contratos, acceso y recuperación

- [x] **T07:** Diseñar contratos de medicación y planes de cuidados.
- [x] **T08:** Diseñar contratos de informes, plantillas y especialidad.
- [x] **T09:** Diseñar contratos de analítica, acceso, sync, auditoría y recuperación común.

#### C03 · Contratos completos antes de implementación

- [x] Todas las acciones tienen actor/objeto/versión/resultado/permiso y proyección.
- [x] Sync, adjuntos, derivados y consumidores conservan compatibilidad y límites.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-17.**

### Fase 4 · Medicación declarada

- [x] **T10:** Implementar dominio de medicación declarada y su revisión/corrección.
- [x] **T11:** Implementar persistencia y migración de medicación declarada.
- [x] **T12:** Implementar operaciones/lecturas/historia/sync y probe del recorrido E15.

#### C04 · Medicación declarada funcional

- [ ] Medicamento de otro médico conserva fuente/incertidumbre sin receta propia.
- [ ] Versiones, permisos, aislamiento y respuesta perdida pasan pruebas reales.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 5 · Tratamiento y planes de cuidados

- [x] **T13:** Implementar dominio de tratamientos, planes, objetivos, acciones y revisiones.
- [x] **T14:** Implementar persistencia/migración y relaciones con problemas/mediciones.
- [x] **T15:** Implementar operaciones/seguimiento/historia/sync y probe E17.

#### C05 · Seguimiento de cuidados funcional

- [x] Actividad hecha no equivale a objetivo logrado y versiones/cierres conservan historia.
- [x] Relaciones por cuenta/paciente y concurrencia pasan PostgreSQL real.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-17.**

### Fase 6 · Informes y resultados

- [x] **T16:** Implementar dominio de informes, resultados, unidades y correcciones.
- [x] **T17:** Implementar persistencia/migración y referencias privadas a adjuntos.
- [x] **T18:** Implementar carga/consulta/resultados/corrección/sync y probe E18.

#### C06 · Informes originales y datos estructurados funcionales

- [x] Informe corregido conserva original/resultados vigentes sin puntos duplicados.
- [x] Adjuntos requieren autorización y no acreditan extracción o integración externa.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-17.**

### Fase 7 · Plantillas versionadas

- [x] **T19:** Implementar dominio de plantillas, campos tipados y versiones.
- [x] **T20:** Implementar persistencia/migración y compatibilidad histórica.
- [x] **T21:** Implementar aplicación de plantillas, lecturas/sync y probe E19.

#### C07 · Plantillas sin invención de hechos

- [x] Cambiar plantilla conserva significado/versión de registros anteriores.
- [x] Ningún valor normal/diagnóstico/respuesta se genera por defecto.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-18.**

### Fase 8 · Primera función por especialidad

- [x] **T22:** Diseñar el recorrido y diccionario de la especialidad elegida en T03.
- [x] **T23:** Implementar persistencia e integridad específica de esa especialidad.
- [x] **T24:** Implementar operaciones/lecturas/historia/sync y probe del recorrido especializado.

#### C08 · Especialidad inicial funcional y delimitada

- [x] El recorrido elegido funciona de extremo a extremo sin afirmar otras especialidades.
- [x] Reglas propias, permisos, versiones y aislamiento pasan pruebas reales.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-18.**

### Fase 9 · Series históricas y analítica individual

- [x] **T25:** Implementar selección de series válidas, edad en el hecho e invalidación de derivados.
- [x] **T26:** Implementar almacén analítico, ETL incremental y proyecciones versionadas.
- [x] **T27:** Implementar consultas de evolución/tendencias y probe con correcciones E03/E09.

#### C09 · Evolución individual coherente

- [x] Series usan solo datos válidos y no sustituyen recencia por orden de carga.
- [x] Correcciones/reintentos/ETL no duplican puntos y conservan entradas/versiones.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-18.**

### Fase 10 · Referencias OMS y crecimiento pediátrico

- [x] **T28:** Verificar fuentes/datasets/métodos/versiones/licencias OMS y preparar fixtures.
- [x] **T29:** Implementar cálculo de indicadores y selección por edad/sexo/método/rango.
- [x] **T30:** Integrar curvas/referencias al contrato individual y probar E20/E21.

#### C10 · Crecimiento pediátrico limitado y comprobado

- [x] No se aplica referencia fuera de rango ni se diagnostica; límites quedan visibles.
- [x] Cambio de nacimiento/entrada recalcula o invalida con versiones identificables.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-18.**

### Fase 11 · Integración, seguridad y concurrencia

- [x] **T31:** Completar permisos, timeline, capturas/deltas y recuperación entre bloques.
- [x] **T32:** Completar migraciones, carreras, idempotencia y aislamiento PostgreSQL.
- [x] **T33:** Probar correcciones, cambios de nacimiento/entradas y ausencia de efectos clínicos indebidos.

#### C11 · Integración clínica comprobada localmente

- [x] Ninguna cuenta/permiso/resultado/página/adjunto filtra datos ajenos.
- [x] Carreras, rollback, respuesta perdida y recuperación no repiten efectos ni pierden historia.
- [x] Revisión y aceptación expresa del usuario. **Aceptado el 2026-11-18.**

### Fase 12 · Contratos y cierre

- [x] **T34:** Generar/verificar contratos, ejemplos y documentación de cada bloque.
- [x] **T35:** Ejecutar suite, probes, migraciones, analítica y build del entregable.
- [x] **T36:** Registrar evidencia, límites y revisión documental final.

#### C12 · Resto de Etapa 3 listo para revisión final

- [x] Todos los comandos pertinentes y recorridos ficticios pasan, incluida la verificación conjunta de CR-01 a CR-05.
- [x] Documentación distingue servidor, consumidores, jurídico/operación y producción.
- [x] Revisión y aceptación expresa del usuario. **C12 aceptado el 2026-11-18.**

## 8. Riesgos y mitigación

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Trabajo paralelo pisa Autorización | Alto | Plan Draft, precondición Completed y ninguna edición de su plan/tareas |
| Medicación declarada se confunde con consumo/prescripción | Alto | Modelo/fuente propios y prueba E15 sin efectos derivados |
| Actividad completada se confunde con objetivo cumplido | Alto | Estados/resultados separados y prueba E17 |
| Informe corregido duplica resultados | Alto | Relación original/corrección, vigencia y prueba E18 |
| Plantilla/especialidad inventa datos clínicos | Alto | Campos tipados, sin defaults clínicos y prueba E19 |
| Referencia OMS se aplica fuera de ámbito | Alto | T28 verifica fuente/método/rango/licencia; T29/T30 prueban rechazo |
| Cambio de nacimiento deja derivados obsoletos | Alto | Entradas/versiones y recálculo/invalidación E21 |
| Adjuntos/derivados filtran datos | Alto | Audiencias/permiso por fuente y descarga reautorizada |
| ETL/corrección duplica series | Alto | Cursor durable, idempotencia y proyección reconstruible |
| El plan crece a todas las especialidades | Medio | Una elegida en T03 y límite explícito de C08 |

## 9. Preguntas abiertas durante la planificación

**Actualización 2026-11-17 (T01–T03 ejecutadas):** las preguntas siguientes quedaron cerradas para el alcance de este plan y se registran en [§4.3.1 de la especificación clínica](../docs/patient-clinical-record.md): primera especialidad odontología con odontograma; indicadores OMS iniciales peso/edad, talla o longitud/edad, peso/talla o longitud e IMC/edad; permisos por secciones `none/read/read_write`; adjuntos en S3 privado sin instalar dependencias.

- O09 se resolvió solo para medicación declarada; prescripción permanece en su plan existente.
- O10/O12 se asignaron a T02; O11/O13 a T03.
- Permisos/defaults por bloque, retención/copias, offline y almacenamiento se cerraron en T03 (S3 privado para adjuntos).
- Ninguna referencia OMS, biblioteca o dataset de cálculo queda elegido por adelantado: su verificación sigue en T28.

## 10. Evidencia y límites

Cada tarea registra comandos y resultados reales en `todo.md`. Integridad/concurrencia requiere PostgreSQL Test aislado; analítica pesada usa su almacén separado. Datos ficticios únicamente. No se acredita diagnóstico, validez clínica/jurídica, integración externa, Rust/Hub, datos reales o producción sin pruebas específicas posteriores.
