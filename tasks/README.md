# Planes y tareas

Plan actual: [P-20261024-01-desktop-shared-api](P-20261024-01-desktop-shared-api/plan.md), **In progress**. Su [lista de control](P-20261024-01-desktop-shared-api/todo.md) conserva estados, evidencia y revisiones. C01, C02, C12, C13 y C14 aceptados. T43–T45 comprobadas; detenido en C15 para revisión, sin aceptar. T09 queda pendiente de retomar después de C15; T07 y C03 no están aceptados. No saltar las revisiones pendientes.

El [plan anterior](P-20261021-01-api-foundation/plan.md) queda **Superseded** para ejecución. Conserva T24/C14 y toda la evidencia previa; sus tareas pendientes no se marcan terminadas. La tabla de sucesión del plan nuevo asigna el núcleo y conserva Hub, comunicaciones, espera, analítica y producción para etapas posteriores. El esquema sigue en [database-schema.md](../docs/database-schema.md); el borrador lógico permanece retirado.

Antecedente del 2026-10-23: el usuario aceptó C13 y P05/P06, revisables al implementar. Sus rutas e historia se conservan. La aprobación del sucesor no cierra los detalles del Hub o lista de espera ni acepta checkpoints pendientes del plan anterior.

## Convenciones

- Plan: `P-YYYYMMDD-NN-short-slug`, con fecha local y número libre para ese día. Conservar el ID tras aprobarlo.
- Cada plan tiene `plan.md` (objetivo, tareas, dependencias, aceptación y controles) y `todo.md` (estado y evidencia). No mantener una segunda lista de ejecución en otro documento.
- Tareas `T01`, `T02`…; checkpoints `C01`, `C02`… dentro del plan. Al citar desde otro plan, incluir su ID completo.
- Planes: `Draft`, `Approved`, `In progress`, `Blocked`, `Completed`, `Superseded`. Tareas: `Todo`, `In progress`, `Blocked`, `Done`. Solo el usuario aprueba plan y checkpoints.
- Conservar planes cerrados y sustituidos. No renumerar tareas aprobadas; añadir nuevos IDs y explicar el cambio.

Cada tarea identifica propietario de componente, contrato/datos afectados, límites de transacción, efecto en sync y consumidores, dependencias, comprobación y evidencia. Si no afecta a uno, indicarlo. Una tarea debe permitir una revisión concreta; dividirla antes de ejecutar si crece.

Trabajar una tarea a la vez. Definir contratos y propietario de integración antes de proponer trabajo paralelo. Conservar trabajo ajeno. Registrar fallos y límites sin convertirlos en éxitos. Al llegar al checkpoint, detenerse hasta revisión; aprobar el plan no equivale a aceptar los checkpoints posteriores. Una decisión pendiente bloquea solo las tareas que la necesitan.
