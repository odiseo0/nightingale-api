# Planes y tareas

## Revisión general de código

- [P-20261118-01-project-code-review](P-20261118-01-project-code-review/plan.md), **Closed**, con [revisión inicial](P-20261118-01-project-code-review/review.md) y [lista de control](P-20261118-01-project-code-review/todo.md). El usuario lo cerró el 2026-11-22 y decidió no continuarlo. Conserva el código, las tareas `Done`, las comprobaciones y la evidencia ya registrados. Las tareas pendientes no se ejecutarán dentro de este plan y los checkpoints sin revisión, incluidos C07, C08 y C09, no quedan aceptados.

## Planes de componentes nuevos

- [P-20261122-01-vademecum-read-api](P-20261122-01-vademecum-read-api/plan.md), **Completed**, con [lista de control](P-20261122-01-vademecum-read-api/todo.md). T01–T12 Done y C01–C05 aceptados el 2026-11-22. La revisión corrigió registros con `/`; pasaron 40 pruebas focales, probes PostgreSQL/Keycloak, contratos, build y diff. La suite conserva el error ajeno documentado de `UsersStructureTests`; consumidores, revisión profesional y producción siguen fuera.
- [P-20261117-01-authorization-policies](P-20261117-01-authorization-policies/plan.md), **Completed**, con [lista de control](P-20261117-01-authorization-policies/todo.md). T01–T17 Done y C06 aceptado el 2026-11-18. El usuario autorizó pasar C01, aceptó C02/C03 y autorizó continuar hasta C06 sin aceptar por anticipado C04/C05. Pasaron 259 pruebas, los trece probes locales, los contratos y el build.
- [P-20261117-02-account-subscriptions](P-20261117-02-account-subscriptions/plan.md), **Approved**, con [lista de control](P-20261117-02-account-subscriptions/todo.md). Implementa planes, asientos, USD/BCV, evidencias y verificación manual. Depende de C06 del plan de autorización; las decisiones `SU-Oxx` se cierran en T01–T04 y ninguna tarea/checkpoint está ejecutado/aceptado.
- [P-20261117-03-patient-billing](P-20261117-03-patient-billing/plan.md), **Approved**, con [lista de control](P-20261117-03-patient-billing/todo.md). Implementa precios, cargos, reportes del paciente, revisión, saldos, comprobantes y analítica. Depende de C10 de suscripciones; las decisiones `BI-Oxx` se cierran en T01–T04 y ninguna tarea/checkpoint está ejecutado/aceptado.
- [P-20261117-04-clinical-documents](P-20261117-04-clinical-documents/plan.md), **Approved**, con [lista de control](P-20261117-04-clinical-documents/todo.md). Implementa récipes/órdenes, emisión profesional, PDF, historia, paciente y QR como bloque acotado de Etapa 3. Depende de C10 de facturación; las decisiones `CD-Oxx` se cierran en T01–T04 y ninguna tarea/checkpoint está ejecutado/aceptado.
- [P-20261117-05-clinical-stage-3](P-20261117-05-clinical-stage-3/plan.md), **Completed**, con [lista de control](P-20261117-05-clinical-stage-3/todo.md). Cubre el resto de Etapa 3 sin prescripción/récipes. T01–T36 Done y C01–C12 aceptados el 2026-11-17/18, incluida la verificación conjunta de críticos en P-20261118-01/C16. Medicación declarada, planes de cuidados, informes/resultados con adjuntos, plantillas + odontología y analítica/crecimiento OMS comprobados con suite, probes PostgreSQL reales y contratos exportados; consumidores y producción siguen fuera.

## Planes vigentes y antecedentes

Plan de etapa 2 clínica: [P-20261116-02-clinical-routine](P-20261116-02-clinical-routine/plan.md), **Completed**, con [lista de control](P-20261116-02-clinical-routine/todo.md). T01–T27 están Done. C01–C09 están aceptados; el usuario aceptó C09 el 2026-11-17. Etapa 2 publica `api-v1.3`; no se inicia Etapa 3. Los cierres anteriores se conservan sin atribuirles nuevas aceptaciones.

El 2026-11-16 el usuario aprobó todas las revisiones pendientes de trabajo ya completado: C08 de P-20261116-01-clinical-review-refactor, C06 de P-20261115-02-patient-clinical-data, C11 de P-20261024-01-desktop-shared-api y C01 de los dos encargos documentales. Esos cinco planes quedan **Completed**. Esto no acepta por anticipado tareas o checkpoints futuros de etapa 2.

Plan sucesor de corrección: [P-20261116-01-clinical-review-refactor](P-20261116-01-clinical-review-refactor/plan.md), **Completed**, con [lista y evidencia](P-20261116-01-clinical-review-refactor/todo.md). T01–T20 y C01–C08 están comprobados/aceptados; conserva sus límites de consumidores, operación y producción.

Plan de etapa 1 clínica: [P-20261115-02-patient-clinical-data](P-20261115-02-patient-clinical-data/plan.md), **Completed**, con [lista de control](P-20261115-02-patient-clinical-data/todo.md). T01–T18 y C01–C06 están comprobados/aceptados; el refactor sucesor conserva las correcciones posteriores.

Encargo documental de especificación clínica: [P-20261115-01-clinical-spec](P-20261115-01-clinical-spec/plan.md), **Completed**, con [lista y evidencia](P-20261115-01-clinical-spec/todo.md). C01 fue aceptado el 2026-11-16. Produce la [especificación clínica](../docs/patient-clinical-record.md) bajo [D12](../docs/decisions.md#d12--registro-clínico-y-seguimiento-del-paciente).

Encargo documental del Hub: [P-20261114-01-patient-hub-docs](P-20261114-01-patient-hub-docs/plan.md), **Completed**, con [lista y evidencia](P-20261114-01-patient-hub-docs/todo.md). C01 fue aceptado el 2026-11-16. Alinea el alcance futuro del Hub con [D11](../docs/decisions.md#d11--interfaz-del-hub-y-servidor-en-nightingale-api); no acredita implementación del Hub.

Plan del núcleo compartido: [P-20261024-01-desktop-shared-api](P-20261024-01-desktop-shared-api/plan.md), **Completed**. Su [lista de control](P-20261024-01-desktop-shared-api/todo.md) conserva estados y evidencia. C11 fue aceptado el 2026-11-16. C07/C08 conservaron autorización de paso sin aceptaciones separadas. Se conservan los diagnósticos estáticos y límites externos documentados; el cierre no acredita consumidores o producción.

El [plan anterior](P-20261021-01-api-foundation/plan.md) queda **Superseded** para ejecución. Conserva T24/C14 y toda la evidencia previa; sus tareas pendientes no se marcan terminadas. La tabla de sucesión del plan nuevo asigna el núcleo y conserva Hub, comunicaciones, espera, analítica y producción para etapas posteriores. El esquema sigue en [database-schema.md](../docs/database-schema.md); el borrador lógico permanece retirado.

Antecedente del 2026-10-23: el usuario aceptó C13 y P05/P06, revisables al implementar. Sus rutas e historia se conservan. La aprobación del sucesor no cierra los detalles del Hub o lista de espera ni acepta checkpoints pendientes del plan anterior.

D11 sustituye el servidor y almacén propios del Hub y la autorización propuesta entre dos servidores. API tendrá todas sus funciones de servidor y Hub su interfaz web, con lectura pública de micrositios y acceso limitado a citas. El contrato y la implementación del Hub siguen pendientes; su presentación pública de clínicas no cambia el alcance interno del plan de escritorio.

## Convenciones

- Plan: `P-YYYYMMDD-NN-short-slug`, con fecha local y número libre para ese día. Conservar el ID tras aprobarlo.
- Cada plan tiene `plan.md` (objetivo, tareas, dependencias, aceptación y controles) y `todo.md` (estado y evidencia). No mantener una segunda lista de ejecución en otro documento.
- Tareas `T01`, `T02`…; checkpoints `C01`, `C02`… dentro del plan. Al citar desde otro plan, incluir su ID completo.
- Planes: `Draft`, `Approved`, `In progress`, `Blocked`, `Completed`, `Closed`, `Superseded`. `Closed` registra un cierre anticipado y conserva el trabajo realizado sin completar tareas ni aceptar checkpoints pendientes. Tareas: `Todo`, `In progress`, `Blocked`, `Done`. Solo el usuario aprueba plan y checkpoints.
- Conservar planes cerrados y sustituidos. No renumerar tareas aprobadas; añadir nuevos IDs y explicar el cambio.

Cada tarea identifica propietario de componente, contrato/datos afectados, límites de transacción, efecto en sync y consumidores, dependencias, comprobación y evidencia. Si no afecta a uno, indicarlo. Una tarea debe permitir una revisión concreta; dividirla antes de ejecutar si crece.

Trabajar una tarea a la vez. Definir contratos y propietario de integración antes de proponer trabajo paralelo. Conservar trabajo ajeno. Registrar fallos y límites sin convertirlos en éxitos. Al llegar al checkpoint, detenerse hasta revisión; aprobar el plan no equivale a aceptar los checkpoints posteriores. Una decisión pendiente bloquea solo las tareas que la necesitan.
