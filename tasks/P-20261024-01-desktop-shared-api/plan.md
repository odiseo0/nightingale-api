# P-20261024-01-desktop-shared-api: API compartida para escritorio

**Checkpoint actual:** C18 aceptado: «Acepto C18; continúa T55–T57». T46–T57 comprobadas para revisión C06, sin iniciar T19. Se conserva sentinel de Python 3.15 y su límite estático. Las pruebas con reservas reales conservan T22/T32.

**Estado:** In progress. **Creado:** 2026-10-24. **Actualizado:** 2026-10-26. **Lista:** [todo.md](todo.md).

**Corrección aprobada el 2026-10-26:** el usuario aprueba la ampliación T46–T57: «Acepto el plan, puedes continuar con las correcciones». Tras revisar T46–T48, pide continuar y permite T49–T51. Una tarea a la vez y sin delegación; detenerse en C17 antes de T52. C17/C18 y C06 conservan su revisión expresa. Se conservan los imports, espacios y demás revisiones del usuario.

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
- [x] T09: Habilitar una consulta independiente.
- [x] T07: Aceptar operaciones con idempotencia.

**C03: Identidad y aceptación técnica.** Detenerse para revisión.

- [x] T10: Gestionar invitaciones.
- [x] T11: Gestionar cuenta y dispositivos autorizados.
- [x] T12: Registrar y consultar auditoría.

**C04: Permisos y dos usuarios.** Detenerse para revisión.

- [x] T13: Registrar fichas borrador.
- [x] T14: Gestionar contactos y vínculos.
- [x] T15: Completar fichas y añadir documentos declarados.

**C05: Pacientes y contactos.** Detenerse para revisión.

- [x] T16: Gestionar catálogo propio.
- [x] T17: Gestionar ofertas por cuenta.
- [x] T18: Gestionar reglas semanales.

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

## Corrección aprobada de C06 · In progress · 2026-10-26

### Resultado y límites

Corregir las causas de los avisos sobre EmptyType y None, completar los tipos de los validadores y los recorridos afectados, validar cada payload una sola vez y devolver diccionarios tipados en las respuestas de lectura de C06. La aprobación de esta ampliación no acepta C06 ni habilita T19. Los registros completos viven solo en todo.md.

No cambia acciones, rutas, campos públicos, credenciales, permisos, versiones funcionales, huellas de operaciones existentes ni el modelo SQL. No añade clases de comandos, otra fábrica, una capa de coordinación, dependencias por preferencia o una configuración que oculte los avisos. Los modelos Pydantic siguen como fuente de entrada/salida; que el caso devuelva un dict no elimina ese contrato. La corrección de tipos puede tocar soporte común y sus consumidores actuales, sin reescribir código ajeno a los hallazgos.

### Acuerdos aprobados

- **Ausencia:** comprobar Python y el analizador reales con un caso mínimo. Preferir `Empty = sentinel("Empty")` de Python 3.15 y el tipo que representa ese mismo valor; conservar `is Empty`. Revisar los alias EmptyType/UndefinedType y sus usos antes de retirarlos. No cambiar a None ni actualizar el analizador en silencio si falta soporte. La prueba de compatibilidad precede al cambio común.

  **Decisión posterior del usuario, 2026-10-26:** tras mostrar la falta de soporte de basedpyright 1.40.2 y una alternativa con Enum/Final, el usuario indica «Si tenemos Python 3.15 podemos utilizar sentinel() tranquilamente, si esa fue la propuesta inicial, por favor síguela». Se conserva sentinel de Python 3.15, sin Enum ni cambios del analizador. Registrar por separado la ejecución correcta y el límite estático; no dar la reducción numérica de errores por prueba de tipos ni ocultar diagnósticos. Esta decisión resuelve la elección de T46, sin aceptar C16/C06.
- **Resultados:** expresar los retornos de Ok/Err y comprobar error/state antes de acceder a sus campos cuando el modelo permite None. Acotar el resultado de invitaciones a su tipo real. No usar cast, Any o ignores para evitar el diagnóstico ni crear una jerarquía por cada acción sin necesidad.
- **Anotaciones:** `before` recibe entrada sin validar, normalmente object; `after` usa el tipo real del campo; validadores de modelo devuelven Self y serializadores declaran entrada/salida. Completar también parámetros y retornos de DAOs/casos afectados. SQLAlchemy en aplicación solo bajo TYPE_CHECKING; sin repositorios ajenos.
- **Entrada:** una selección y validación por acción produce los datos que reutilizan la huella y el caso. Retirar la cadena de seis normalizadores y la segunda validación del original al migrar cada componente. Conservar exactamente ausencia frente a null en patches, defaults, aliases, texto normalizado válido y payload inválido como JSON recibido. No persistir el payload personal para simplificar ese flujo.
- **Salida:** usar dict tipado y `response_model` en las lecturas afectadas. Las proyecciones de recibos/journal se validan y serializan dentro de la transacción, antes del commit, con una fuente de esquema y campos explícitos. FastAPI no sustituye ese control interno ni autoriza devolver un ORM completo. Conservar modelos que sí se usan para reglas, como intervalos y propuestas de agenda.
- **Evidencia:** mantener la comprobación real de citas en T22/T32. T57 separa las casillas probadas con intervalos ficticios de la protección pendiente con reservas; no adelanta tablas o rutas para marcarlas completas.

### Orden aprobado

Una tarea a la vez, sin delegación. Cada tarea deja un recorrido utilizable. Detenerse para revisión tras cada grupo; el usuario acepta cada checkpoint, no las pruebas.

- [x] T46: Corregir el tipo de ausencia tras comprobar el analizador; sentinel conservado por decisión posterior del usuario, con límite estático registrado.
- [x] T47: Acotar los resultados opcionales de operaciones.
- [x] T48: Anotar los validadores compartidos.

**C16: Tipos base.** Comprobar ausencia, resultados y validadores compartidos antes de seguir.

- [x] T49: Anotar validadores de pacientes, servicios y agenda.
- [x] T50: Tipar el acceso de identidad y cuentas afectado.
- [x] T51: Tipar los DAOs de datos operativos afectados.

**C17: Tipos de los recorridos.** Revisar los tipos sin ocultar diagnósticos.

- [x] T52: Unificar la validación de operaciones de cuentas.
- [x] T53: Reutilizar el payload validado de pacientes y contactos.
- [x] T54: Reutilizar el payload validado de servicios y reglas.

**C18: Validación e idempotencia.** Probar equivalencia de huellas y persistencia antes de simplificar salidas.

- [ ] T55: Separar la proyección de ofertas de su serialización.
- [ ] T56: Simplificar las lecturas HTTP restantes de C06.
- [ ] T57: Cerrar la corrección y ajustar la evidencia de C06.

**Revisión C06, ya existente:** entregar la corrección completa, evidencia nueva y límites pendientes. Solo su aceptación expresa habilita T19. C16–C18 son revisiones de esta ampliación; no sustituyen C06 ni renumeran checkpoints previos.

### Comprobación y fuentes

T46 localiza basedpyright 1.40.2 instalado por Zed fuera de PATH y registra su comando, intérprete, configuración y resultados en todo.md. El caso mínimo reproduce el aviso de EmptyType y muestra falta de soporte para las anotaciones del sentinel propuesto. Se pide decisión antes de cambiar de diseño o instalar/actualizar; no declarar la comprobación estática pasada por leer el código.

Comandos existentes que se usarán tras aprobar: suite unittest, probes de acceso/cuentas/sync/equipo/pacientes/servicios/agenda/persistencia, build offline y git diff --check. Cada tarea fija sus checks enfocados; cada revisión añade la suite completa y el build. Reutilizar servicios de prueba y PostgreSQL aislado; nunca SQLite para acreditar integridad. Omitir la prueba HTTP separada del wheel. Las 108 pruebas y ocho probes del cierre anterior son evidencia histórica, no validación de esta corrección.

Fuentes consultadas en la revisión, que se contrastarán con las versiones resueltas antes de implementar:

- [Python 3.15: sentinel](https://docs.python.org/3.15/library/functions.html#sentinel), [reglas de tipos para sentinels](https://typing.python.org/en/latest/spec/special-types.html#sentinels) y [basedpyright: reducción de tipos](https://docs.basedpyright.com/latest/usage/type-concepts-advanced/#type-guards).
- [Pydantic: validadores](https://docs.pydantic.dev/latest/concepts/validators/) y [FastAPI: response_model](https://fastapi.tiangolo.com/tutorial/response-model/#response_model-parameter). El lockfile conserva Pydantic 2.14.1 y FastAPI 0.159.1.
- [Contrato de huella e idempotencia](../../docs/api-v1.md#6-resultados-idempotencia-y-errores), arquitectura, instrucciones del usuario y reglas locales de planificación.

Riesgos: soporte del analizador para sentinel; consumidores de la ausencia común; hashes antiguos que deben seguir reconociéndose; serialización de UUID/fechas/UTC al pasar a dict; filtrado de campos; errores internos opcionales. Cada riesgo tiene un control antes de la revisión que lo cierra. No hay una decisión funcional nueva pendiente; la disponibilidad del analizador se resuelve en T46.

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

