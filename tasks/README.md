# Planes y tareas

Plan sucesor activo: [P-20261116-01-clinical-review-refactor](P-20261116-01-clinical-review-refactor/plan.md), **In progress**, con [lista de control](P-20261116-01-clinical-review-refactor/todo.md). Corrige alcance de resultados, estados, historial, descarga, auditoría, integridad, contratos y simplificación. T01–T20 están comprobadas y C01–C07 aceptados; C08 espera revisión del usuario. El usuario aceptó el diseño actual y revisó la meta inicial de 950 líneas en C06.

Plan de etapa 1 clínica: [P-20261115-02-patient-clinical-data](P-20261115-02-patient-clinical-data/plan.md), **In progress**, con [lista de control](P-20261115-02-patient-clinical-data/todo.md). Su ejecución quedó detenida en C06 mientras se completa el sucesor; no inicia nuevas tareas ni se marca aceptado. La etapa 2 no se inicia.

Encargo documental activo del 2026-11-15: [P-20261115-01-clinical-spec](P-20261115-01-clinical-spec/plan.md), con [lista y evidencia](P-20261115-01-clinical-spec/todo.md). Produce la [especificación clínica](../docs/patient-clinical-record.md) que servirá de referencia para los planes de datos, registro habitual y funciones completas. [D12](../docs/decisions.md#d12--registro-clínico-y-seguimiento-del-paciente) registra el alcance. Solo documentación, en secuencia y sin delegación; no inicia implementación ni acepta checkpoints previos.

Encargo documental del 2026-11-14: [P-20261114-01-patient-hub-docs](P-20261114-01-patient-hub-docs/plan.md), con [lista y evidencia](P-20261114-01-patient-hub-docs/todo.md). Solo alinea el alcance futuro del Hub con [D11](../docs/decisions.md#d11--interfaz-del-hub-y-servidor-en-nightingale-api); no autoriza código ni acepta checkpoints del núcleo. Trabajo secuencial, sin delegación; C01 de este encargo conserva su revisión pendiente.

Plan actual: [P-20261024-01-desktop-shared-api](P-20261024-01-desktop-shared-api/plan.md), **In progress**. Su [lista de control](P-20261024-01-desktop-shared-api/todo.md) conserva estados, evidencia y revisiones. C01–C06, C09/C10 y C12–C18 aceptados. T31–T33 comprobadas; trabajo detenido en C11 para revisión y aceptación expresa. C07/C08 conservaron autorización de paso sin aceptaciones separadas. Se conservan los 16 diagnósticos estáticos previos; no se declara análisis global correcto ni se cierra el plan.

El [plan anterior](P-20261021-01-api-foundation/plan.md) queda **Superseded** para ejecución. Conserva T24/C14 y toda la evidencia previa; sus tareas pendientes no se marcan terminadas. La tabla de sucesión del plan nuevo asigna el núcleo y conserva Hub, comunicaciones, espera, analítica y producción para etapas posteriores. El esquema sigue en [database-schema.md](../docs/database-schema.md); el borrador lógico permanece retirado.

Antecedente del 2026-10-23: el usuario aceptó C13 y P05/P06, revisables al implementar. Sus rutas e historia se conservan. La aprobación del sucesor no cierra los detalles del Hub o lista de espera ni acepta checkpoints pendientes del plan anterior.

D11 sustituye el servidor y almacén propios del Hub y la autorización propuesta entre dos servidores. API tendrá todas sus funciones de servidor y Hub su interfaz web, con lectura pública de micrositios y acceso limitado a citas. El contrato y la implementación del Hub siguen pendientes; su presentación pública de clínicas no cambia el alcance interno del plan de escritorio.

## Convenciones

- Plan: `P-YYYYMMDD-NN-short-slug`, con fecha local y número libre para ese día. Conservar el ID tras aprobarlo.
- Cada plan tiene `plan.md` (objetivo, tareas, dependencias, aceptación y controles) y `todo.md` (estado y evidencia). No mantener una segunda lista de ejecución en otro documento.
- Tareas `T01`, `T02`…; checkpoints `C01`, `C02`… dentro del plan. Al citar desde otro plan, incluir su ID completo.
- Planes: `Draft`, `Approved`, `In progress`, `Blocked`, `Completed`, `Superseded`. Tareas: `Todo`, `In progress`, `Blocked`, `Done`. Solo el usuario aprueba plan y checkpoints.
- Conservar planes cerrados y sustituidos. No renumerar tareas aprobadas; añadir nuevos IDs y explicar el cambio.

Cada tarea identifica propietario de componente, contrato/datos afectados, límites de transacción, efecto en sync y consumidores, dependencias, comprobación y evidencia. Si no afecta a uno, indicarlo. Una tarea debe permitir una revisión concreta; dividirla antes de ejecutar si crece.

Trabajar una tarea a la vez. Definir contratos y propietario de integración antes de proponer trabajo paralelo. Conservar trabajo ajeno. Registrar fallos y límites sin convertirlos en éxitos. Al llegar al checkpoint, detenerse hasta revisión; aprobar el plan no equivale a aceptar los checkpoints posteriores. Una decisión pendiente bloquea solo las tareas que la necesitan.
