# Planes y tareas

Plan actual: [P-20261021-01-api-foundation](P-20261021-01-api-foundation/plan.md), estado **In progress**, tarea T04 en curso. Su [lista de control](P-20261021-01-api-foundation/todo.md) separa comprobación de revisión del usuario.

## Convenciones

- Plan: `P-YYYYMMDD-NN-short-slug`, con fecha local y número libre para ese día. Conservar el ID tras aprobarlo.
- Cada plan tiene `plan.md` (objetivo, tareas, dependencias, aceptación y controles) y `todo.md` (estado y evidencia). No mantener una segunda lista de ejecución en otro documento.
- Tareas `T01`, `T02`…; checkpoints `C01`, `C02`… dentro del plan. Al citar desde otro plan, incluir su ID completo.
- Planes: `Draft`, `Approved`, `In progress`, `Blocked`, `Completed`, `Superseded`. Tareas: `Todo`, `In progress`, `Blocked`, `Done`. Solo el usuario aprueba plan y checkpoints.
- Conservar planes cerrados y sustituidos. No renumerar tareas aprobadas; añadir nuevos IDs y explicar el cambio.

Cada tarea identifica propietario de componente, contrato/datos afectados, límites de transacción, efecto en sync y consumidores, dependencias, comprobación y evidencia. Si no afecta a uno, indicarlo. Una tarea debe permitir una revisión concreta; dividirla antes de ejecutar si crece.

Trabajar una tarea a la vez. Definir contratos y propietario de integración antes de proponer trabajo paralelo. Conservar trabajo ajeno. Registrar fallos y límites sin convertirlos en éxitos. Al llegar al checkpoint, detenerse hasta revisión; aprobar el plan no equivale a aceptar los checkpoints posteriores. Una decisión pendiente bloquea solo las tareas que la necesitan.
