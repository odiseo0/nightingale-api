# P-20261024-01-desktop-shared-api: API compartida para escritorio

**Checkpoint actual:** C14 aceptado por el usuario al decir «Todo bien». T43–T45 comprobadas; detenido en C15 para revisión. C15 y C03 no están aceptados. C02 conserva su aceptación y T08 su evidencia histórica; T09 se retoma después de C15.

**Estado:** In progress. **Creado:** 2026-10-24. **Actualizado:** 2026-10-26. **Lista:** [todo.md](todo.md).

**Aprobación:** el usuario pidió «Por favor, implementa este plan» y después aceptó C01. No se aceptan por ello checkpoints posteriores. El usuario indicó además «No hay Docker, no te preocupes por Docker. No lo necesitamos ahora»: no exigir Docker. Después pidió revertir esa continuación y luego autorizó reanudar respetando el estilo implementado por él. No repetir la reescritura retirada.

## Resultado y límites

API funcional para un profesional y sus asistentes desde varios dispositivos. Solo este repositorio. Alta controlada; roles fijos; operaciones tipadas y lecturas por recurso; token opaco por usuario/dispositivo sin vencimiento y revocable; avisos inmediatos por SSE; PostgreSQL y Keycloak locales, sin exigir Docker. Ventana de sync de 90 días y recuperación por snapshot.

No incluye escritorio, Hub, clínicas, varias sedes, transferencia de cuentas, roles personalizados, comunicaciones, espera, analítica, producción ni datos reales. Tampoco fusión/corrección global de identidad, verificación documental/representación o corrección de referencias y reapertura de citas terminales. No crear rutas simuladas para lo excluido.

## Fuentes y contratos

- [Especificación API](../../docs/nightingale-api.md), [decisiones](../../docs/decisions.md) y [arquitectura](../../docs/architecture.md).
- [Contrato HTTP v1](../../docs/api-v1.md): única fuente del diseño de transporte, rutas, modelos públicos, operaciones y resultados. Al implementar, los esquemas Pydantic de domain, derivados de la base del proyecto, generarán OpenAPI/JSON Schema; no editar artefactos generados.
- [Esquema](../../docs/database-schema.md): única fuente del modelo físico; no mantener otro diccionario en este plan.
- Plan Maestro 0.3, DAT 0.3 y SRS 0.5, leídos desde el repositorio original Nightingale, con revisión del 2026-10-23. Se conservan sus rutas y no se modifica ese repositorio.
- Skills locales: planning-task-breakdown para formato de tareas; fastapi y docs-first-framework-code al usar APIs; minimal-code al implementar. La estructura de api/users y las instrucciones del usuario fijan el estilo. No usar textos anteriores de arquitectura para omitir esas reglas.

## Decisiones de implementación

**Instrucción posterior de estilo (2026-10-25):** partir de la app de módulo, ajustes compartidos y fábrica de sesiones existentes. Añadir capacidades con funciones simples y conservar nombres/exportaciones válidas. El usuario descartó lifespan para la base: las rutas usan Depends(get_db), como api/users/infrastructure, y Uvicorn arranca directamente. No restaurar main/lifespan ni otra fábrica de aplicación. get_db/session usan la misma fábrica del usuario. El motor actual exige URI al importar, sin abrir conexión; adaptar las pruebas a ese código, no restaurar la importación diferida retirada.

**Corrección aprobada (2026-10-26):** domain contiene esquemas derivados del BaseModel del proyecto, objetos de valor, tipos y errores; infrastructure solo endpoints y su configuración; application casos de uso sin acceso directo a SQLAlchemy; repository modelos y DAOs derivados de la base. Separar authorization de accounts; consumir casos de uso y tipos de dominio entre componentes, no sus repositorios. Proveedores y credenciales usan soporte concreto de core/services. Aplicación coordina la misma sesión mediante una función pequeña de transacción en core/db; DAOs con commit=False. No crear otra fábrica ni una capa de clases de coordinación.

JSON público camelCase y Python snake_case. Listas y páginas de snapshot usan page desde 1, shows 100 por defecto y máximo 500, LIMIT/OFFSET en DAO, respuesta items/total y orden estable. El avance incremental de sync conserva su posición, alcance y recuperación; no se convierte en OFFSET. Eliminar módulos y configuración de cursores de página en T43. Sustituir la CLI por scripts/create_practice.py en T44, sin un sistema de comandos ni seeders generales. No añadir funciones, dependencias ni cambios físicos en esta corrección. Ninguna fecha, identidad o versión de permiso enviada por cliente concede acceso.

Los modelos y permisos están en sus fuentes citadas. Citas usan 1–1440 minutos con precisión de minuto; reprogramar conserva duración y anula confirmación. Ausencia manual tras inicio más margen de cuenta (15 por defecto). Menor sin documento: menos de 18 en la fecha local de la cita y responsable vigente. Esto no prueba representación legal.

Toda escritura compartida usa el mismo caso de aceptación, con versiones, recibo, auditoría, historia cuando proceda y Change Log atómicos. Acceso se comprueba también en lecturas, errores, resultados, páginas y SSE. Cambios se ordenan mediante contador transaccional por cuenta y grupos indivisibles. Snapshot materializado conserva frontera con incremental; páginas no mantienen una transacción abierta entre peticiones. SSE solo avisa; no sustituye los datos persistidos.

## Sucesión

Sustituye la ejecución pendiente del [plan anterior](../P-20261021-01-api-foundation/plan.md), no sus aceptaciones. T01–T03/T24 y C01–C03/C13/C14 anteriores conservan su historia. Sus T04–T14 pasan a los recorridos de este plan según la tabla siguiente; no se marcan Done. Hub T15, workers T16–T18, espera T19–T20, analítica T21 y operación/integración externas T22–T23 quedan fuera y se conservan como pendientes de planes posteriores. La revisión parcial de O02 y detalles de O04/O05 no se cierran.

| Origen pendiente | Destino |
|---|---|
| T04 acceso | T02–T03, T08–T12 y pruebas de T32; Hub excluido |
| T05 contrato y sync | T02–T03, T07, T28–T31 |
| T06 reglas | T02–T03 y T13–T27; solicitudes Hub excluidas |
| T07–T08 base técnica y acceso | T04–T12 |
| T09 pacientes | T13–T15 |
| T10 servicios | T16–T17 |
| T11 agenda | T18–T21 |
| T12 citas | T22–T27 |
| T13 descarga | T28–T30 |
| T14 pruebas conjuntas | T32–T33 |

## Orden de tareas

Dependencia secuencial según este orden: cada tarea requiere la anterior comprobada; tras cada grupo de tres se detiene hasta aceptación del checkpoint. El 2026-10-25 el usuario cambió el bloque C03 a T08 → T09 → T07 para disponer de identidad, pertenencia y dispositivos reales antes de aceptar operaciones. No se renumeran IDs. Los registros completos, entradas, archivos, aceptación y controles viven en todo.md. No hay trabajo paralelo aprobado.

La corrección del 2026-10-26 interrumpe T09: T34–T36 → C12 → T37–T39 → C13 → T40–T42 → C14 → T43–T45 → C15 → retomar T09 → T07 → C03. Cada checkpoint requiere revisión del usuario. La referencia histórica a una tarea preparatoria T34 retirada no se borra ni acredita esta tarea nueva aprobada expresamente.

- [x] T34: Corregir reglas y registrar la ampliación.
- [x] T35: Corregir el contrato público.
- [x] T36: Preparar errores comunes y soporte de transacciones.

**C12: Reglas, contrato y soporte.** Detenerse para revisión antes de reorganizar componentes.

- [x] T37: Colocar esquemas, valores y modelos de authorization.
- [x] T38: Derivar los DAOs de authorization.
- [x] T39: Corregir casos de uso y endpoints de authorization.

**C13: Recorrido de credenciales.** Detenerse para revisión.

- [x] T40: Separar esquemas y modelos de accounts.
- [x] T41: Trasladar persistencia de accounts a DAOs.
- [x] T42: Corregir casos de accounts y acceso técnico de sync.

**C14: Componentes y alta atómica.** Detenerse para revisión.

- [x] T43: Sustituir los cursores de página por LIMIT/OFFSET.
- [x] T44: Sustituir CLI por el script pequeño de alta.
- [x] T45: Cerrar corrección, pruebas y documentación.

**C15: Corrección completa.** Detenerse para revisión; su aceptación habilita retomar T09 y después T07. No acepta C03.

- [x] T01: Documentar el plan sucesor.
- [x] T02: Fijar el contrato HTTP v1.
- [x] T03: Ampliar el esquema de diseño.

**C01: Contratos, modelos y decisiones.** Detenerse para revisión.

- [x] T04: Recuperar la base de proceso.
- [x] T05: Preparar el entorno aislado.
- [x] T06: Preparar migraciones y coordinación.

**C02: Base ejecutable y entorno.** Detenerse para revisión.

- [x] T08: Emitir credenciales de dispositivo.
- [ ] T09: Habilitar una consulta independiente.
- [ ] T07: Aceptar operaciones con idempotencia.

**C03: Identidad y aceptación técnica.** Detenerse para revisión.

- [ ] T10: Gestionar invitaciones.
- [ ] T11: Gestionar cuenta y dispositivos autorizados.
- [ ] T12: Registrar y consultar auditoría.

**C04: Permisos y dos usuarios.** Detenerse para revisión.

- [ ] T13: Registrar fichas borrador.
- [ ] T14: Gestionar contactos y vínculos.
- [ ] T15: Completar fichas y añadir documentos declarados.

**C05: Pacientes y contactos.** Detenerse para revisión.

- [ ] T16: Gestionar catálogo propio.
- [ ] T17: Gestionar ofertas por cuenta.
- [ ] T18: Gestionar reglas semanales.

**C06: Catálogo y horario habitual.** Detenerse para revisión.

- [ ] T19: Gestionar excepciones diarias.
- [ ] T20: Gestionar bloqueos.
- [ ] T21: Consultar disponibilidad.

**C07: Disponibilidad protegida.** Detenerse para revisión.

- [ ] T22: Crear citas.
- [ ] T23: Confirmar citas.
- [ ] T24: Reprogramar citas.

**C08: Creación, confirmación y reprogramación.** Detenerse para revisión.

- [ ] T25: Cancelar citas.
- [ ] T26: Registrar resultado de asistencia.
- [ ] T27: Proteger historia funcional.

**C09: Ciclo completo de citas.** Detenerse para revisión.

- [ ] T28: Descargar cambios confirmados.
- [ ] T29: Materializar snapshot coherente.
- [ ] T30: Recuperar tras vencimiento.

**C10: Descarga y recuperación.** Detenerse para revisión.

- [ ] T31: Avisar cambios por SSE.
- [ ] T32: Probar colaboración concurrente.
- [ ] T33: Entregar el contrato y su evidencia.

**C11: Colaboración y entrega de API.** Detenerse para revisión.

## Herramientas y comprobaciones

Conservar Python 3.15.1, uv y versiones resueltas del proyecto salvo incompatibilidad demostrada. La referencia de planificación era PostgreSQL 18.6 y Keycloak 26.8.1. T05 usa PostgreSQL 18.3 ya instalado, sin actualizar el servicio personal: clústeres separados en .tmp y puertos 55432/55433. Keycloak 26.8.1 usa Java 21.0.6 y HTTPS local con certificado de prueba; su flujo S256 se comprobó con tres sujetos ficticios. No se exige Docker ni se despliega. Versiones, huellas, comandos y límites en test-support/README.md y todo.md.

T06 añadió Alembic 1.20.1 para migraciones y su dependencia Mako 1.4.3; las demás versiones resueltas se conservan. Dependencias previstas, aún no instaladas: PyJWT con crypto (validación OIDC), asgi-lifespan solo si hace falta (ciclo ASGI con HTTPX), pycountry (catálogo ISO), phonenumbers (normalización/longitud posible). Resolver versiones compatibles, fijarlas con uv y registrar páginas oficiales antes del uso. Mantener unittest; no añadir otro ejecutor por preferencia.

Comandos comprobados en C02: `uv sync --locked`, `uv run --locked python -m unittest discover -s tests -v` (12 correctas), `uv run --locked python test-support/persistence/check.py`, SQL de Alembic sin conexión y `uv build --offline`. El check OIDC se ejecutó con el Python del mismo entorno. git diff --check correcto. Servicios, fuentes y límites en test-support/README.md; sin PostgreSQL personal, consumidores reales, despliegue o prueba HTTP separada del wheel. No se añaden comandos de exportación todavía.

Cada implementación usa datos ficticios. Pruebas de concurrencia: PostgreSQL real, conexiones independientes y barreras; nunca SQLite como prueba de integridad. Ver matriz en el contrato v1. Separar evidencia documental, unitaria, integración OIDC/SQL, dos procesos de API y consumidor real aún no probado.

## Riesgos y cierre

| Riesgo | Control |
|---|---|
| Credencial API sin vencimiento copiada | Huella en servidor, revocación local vigente y comprobación por petición; no afirmar cierre externo automático |
| Orden precommit omite cambios | Contador transaccional por cuenta, grupos completos y prueba de commits invertidos |
| Revocación frente a aceptación | Orden de coordinación único, relectura tras espera y prueba con conexiones distintas |
| Snapshot o resultado vencido repite efecto | Cursor base coherente, 90 días de resultados y recibo mínimo conservado |
| SSE solo funciona en un proceso | LISTEN/NOTIFY por proceso más comprobación del journal al conectar/recuperar |
| Historia o citas divergen | FK/control diferido y prohibición de reescritura ordinaria |
| Código y evidencia histórica divergen | T04 antes de declarar proceso o pruebas válidos |

Cerrar solo tras C11 y C15 aceptados: catálogo funcional, dos usuarios/dispositivos, instalación y migración desde vacío, conflictos/recuperación/revocación comprobados, contrato generado y guía para Rust. Objetivo local de avisos: p95 menor de dos segundos con diez conexiones y dos procesos. No es aceptación de producción ni de integración del escritorio.

## Preguntas abiertas

Ninguna decisión funcional abierta para el alcance aprobado. Proveedor cloud, datos reales, política legal, corrección global, Hub y módulos posteriores quedan expresamente excluidos. La disponibilidad del entorno y versiones se verifica en sus tareas; un impedimento se registra sin sustituir herramientas o alcance en silencio.

