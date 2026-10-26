# Fuentes, diferencias y revisión documental

**Inspección inicial T01:** 2026-10-21. Este documento conserva la procedencia y evidencia de esa entrega. Estado y comprobaciones posteriores de T03: [guía de desarrollo](operations/development.md).

## Fuentes del repositorio

**Actualización del 2026-10-24:** [database-schema.md](database-schema.md) es la única fuente vigente del diseño de datos por instrucción del usuario, registrada en D08. El borrador lógico anterior queda retirado. Las revisiones de documentación, propuestas y pendientes actuales figuran en el propio esquema; los registros siguientes conservan la procedencia histórica.

La carpeta estaba vacía y sin `.git` al comenzar. El usuario añadió [la especificación v0.1](nightingale-api.md), fechada el 2026-10-21, después de la inspección inicial. Esa es la fuente de alcance de API. Se conservó su contenido técnico; se adaptaron enlaces y la nota de propiedad al nuevo repositorio. El encargo de esta entrega fija la organización y el modo de revisión.

No se inicializó Git ni se inventó un remoto. Por eso esta entrega no tiene `git diff --check` ni estado de rama; la revisión usa inventario y lectura de archivos.

## Fuentes del escritorio

Se leyeron en la copia local `C:/Users/Pedro/Documents/GitHub/nightingale/`. Son contexto de procedencia, no requisitos de acceso para trabajar aquí:

| Ruta en el escritorio | Versión/parte pertinente y uso |
|---|---|
| `docs/decisions/transactional-sync-three-projects.md` | Decisión aceptada el 2026-10-21; tres proyectos, API transaccional y sustitución del acceso SQL directo |
| `docs/specifications/nightingale-api.md` | v0.1, 2026-10-21; origen de la especificación copiada por el usuario |
| `docs/specifications/nightingale-patient-hub.md` | v0.1, 2026-10-21; accesos/solicitudes propios y contrato interno de citas propiedad de API |
| `docs/master-plan.md` | v0.3; §§3–7, 9.6–9.11, 12–15 y 17: precedencia, componentes, propiedad, concurrencia, contratos y recuperación |
| `docs/technical-architecture.md` | v0.3; principios, tres proyectos, sincronización, estados, flujos de Hub/lista de espera, seguridad, operación y recuperación |
| `docs/srs.md` | v0.5; alcance, RF-01–RF-16, reglas administrativas, WhatsApp inicial y preguntas abiertas |
| `AGENTS.md`, `CONTRIBUTING.md`, `tasks/README.md` | Plan previo, cambio mínimo, documentación oficial por versión, evidencia y revisión por checkpoints; se adaptan aquí sin exigir skills ni comandos del escritorio |
| `docs/decisions/native-desktop-cloud-boundaries.md` | Marcado como sustituido el 2026-10-21; solo se usa para detectar instrucciones históricas |

La especificación de API ahora se mantiene aquí. La copia previa del escritorio queda como antecedente; su propietario debe reemplazarla por una referencia a este documento en otra tarea. No se modificó ese repositorio ni se trasladaron sus planes o código. La SRS y el plan general del producto siguen allí; este repositorio contiene los límites de API necesarios para trabajar sin esa copia. Hub mantiene su propio contrato público; no se copia su especificación como una segunda fuente editable.

## Diferencias y decisiones abiertas detectadas

| Hallazgo | Tratamiento en esta entrega |
|---|---|
| Los enlaces relativos de la especificación apuntaban al antiguo árbol y su última nota anunciaba un traslado futuro | Referencias adaptadas; fuente de alcance en este repositorio, sin tocar la copia histórica |
| El ADR antiguo permitía SQL desde Rust y agrupaba servicios cloud | Sustituido por la decisión del 2026-10-21 y D01; no usar sus instrucciones de acceso o despliegue |
| El esquema de referencia separa carpetas pero algunos casos dependen de SQLAlchemy | Tomar organización; contratos pequeños de persistencia y composición conforme al encargo |
| `reschedule_requested` aparece como estado, pero una solicitud pertenece al Hub y faltan rechazo/retirada y confirmación previa | O04 y T06/T15 deben cerrar la relación; no inventar transiciones |
| SRS §9 y arquitectura §12.8 describen respuesta a oferta de lista de espera; el límite del Hub impide reservar otro horario | O05 y T19: definir actor y recorrido sin añadir una reserva por el paciente |
| Secuencia de cambios, política de revocación, capacidad técnica del Hub y retención no están cerradas | O01–O03/O10, con bloqueo de sus tareas de implementación; no confundir nombres de campos con una solución |

## Fuentes técnicas consultadas

**Corrección C15, 2026-10-26:** se conservan Python 3.15.1, SQLAlchemy 2.1.6 y las dependencias resueltas. Sin instalaciones ni cambios del esquema. El script pequeño usa biblioteca estándar y la fábrica existente:

- [Python: argparse](https://docs.python.org/3/library/argparse.html#the-add-argument-method): un único archivo de entrada, sin sistema de subcomandos.
- [SQLAlchemy 2.1: make_url](https://docs.sqlalchemy.org/en/21/core/engines.html#sqlalchemy.engine.make_url): validar controlador y partes de la URI administrativa sin imprimirla.
- [SQLAlchemy 2.1: AsyncEngine.dispose](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncEngine.dispose): liberar el motor al cerrar el proceso del script.

Los controles usan AST y carga aislada de archivos de esquemas para evitar activar los imports antiguos del componente users. No cambian ese componente ni acreditan su ejecución. La evidencia de suite, PostgreSQL/Keycloak y build figura en T45; C15 requiere revisión del usuario. Las listas usan posición; el avance incremental de sync conserva su contrato y aún no tiene implementación.

**Corrección C14, 2026-10-26:** se conservan Pydantic 2.14.1, SQLAlchemy 2.1.6 y pycountry 26.2.16 de uv.lock. No se instalan dependencias. Fuentes de los patrones usados:

- [SQLAlchemy: joins de modelos](https://docs.sqlalchemy.org/en/21/orm/queryguide/select.html#select-join) y [with_for_update](https://docs.sqlalchemy.org/en/21/core/selectable.html#sqlalchemy.sql.expression.Select.with_for_update): filtro de pertenencia antes de contar/paginar y bloqueo compartido con refresco en métodos de DAO. El caso no importa SQLAlchemy en ejecución.
- [PostgreSQL 18: pg_timezone_names](https://www.postgresql.org/docs/18/view-pg-timezone-names.html): fuente reconocida de zonas usada por el DAO y por el CHECK existente. [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html#data-sources) necesita datos del sistema o tzdata; el entorno local no tiene ninguno, comprobado con TZPATH vacío y ausencia del módulo. No se instala otro catálogo ni se cambia DDL.
- [Pydantic: validadores](https://docs.pydantic.dev/latest/concepts/validators/#field-validators) y [pycountry 26.2.16](https://raw.githubusercontent.com/pycountry/pycountry/26.2.16/README.rst): país ISO, campos permitidos y validación de texto conservando la identidad externa exacta. Serialización UTC y paginación común heredan de la base del proyecto.

Las pruebas de C14 incluyen cuentas y sync técnico con transacción compartida, alcance, rollback y duplicado concurrente. No acreditan nuevos endpoints, invitaciones, registro de dispositivos por operación ni sincronización incremental. C14 queda para revisión del usuario.

**Corrección C13, 2026-10-26:** se conservan las versiones del lockfile. Además de las fuentes de C12, se consultaron y comprobaron:

- [SQLAlchemy 2.1.6: upsert](https://docs.sqlalchemy.org/en/21/orm/queryguide/dml.html#orm-upsert-statements) y [populate_existing](https://docs.sqlalchemy.org/en/21/orm/queryguide/api.html#populate-existing): crear identidad sin duplicar y refrescar modelos tras adquirir el bloqueo, en métodos del DAO derivado. Se conserva la base DAO del usuario.
- [Pydantic 2.14.1: StringConstraints](https://docs.pydantic.dev/latest/api/types/#pydantic.types.StringConstraints): excepciones puntuales strip_whitespace=False para secretos y configuración OIDC; no anular las reglas ni alias de la base completa.
- [FastAPI 0.159.1: HTTPException](https://fastapi.tiangolo.com/tutorial/handling-errors/#use-httpexception): los endpoints traducen errores propios y el manejador común genera la respuesta correlacionada, sin Request en sus firmas.
- [PyJWT 2.15.1: decode](https://pyjwt.readthedocs.io/en/stable/api.html#jwt.decode): RS256, emisor, audiencia y claims requeridos conservados al mover el adaptador OIDC a core/services. El proveedor no elige claves desde URLs del token ni importa componentes del API.

La evidencia del bloque está en todo.md: 36 pruebas, integración real y build. No prueba todavía cuentas, sync, escritorio o producción; C13 necesita revisión del usuario.

**Corrección C12, 2026-10-26:** versiones resueltas de uv.lock: FastAPI 0.159.1, Pydantic 2.14.1 y SQLAlchemy 2.1.6. No se instalan ni actualizan dependencias. Patrones consultados y comprobados localmente:

- [FastAPI: manejadores comunes de excepciones](https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers): mantener Request en el manejo HTTP común y permitir endpoints con parámetros concretos. Los cuatro endpoints actuales se adaptan en T39, no en C12.
- [Pydantic: serialización](https://docs.pydantic.dev/latest/concepts/serialization/#python-mode): model_dump(mode="json", by_alias=True) para JSONResponse; conserva alias camelCase y convierte UUID a JSON. Los esquemas heredan de la base existente, sin cambiar su configuración.
- [SQLAlchemy 2.1.6: AsyncSession.begin](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncSession.begin): async with sobre la misma sesión, sin otra fábrica; confirma o revierte y rechaza scopes begin anidados. Pruebas de límites sobre sesión real sin conexión, sin afirmar integridad PostgreSQL por ellas.

Los enlaces apoyan criterios y candidatos; no seleccionan versiones ni demuestran controles:

- [PostgreSQL: aislamiento y secuencias](https://www.postgresql.org/docs/18/transaction-iso.html): visibilidad y concurrencia; una secuencia no prueba orden de commit.
- [OWASP: autorización](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): acceso mínimo, denegar por defecto y comprobar cada solicitud.
- [FastAPI: lifespan](https://fastapi.tiangolo.com/advanced/events/) y [trabajo tras la respuesta](https://fastapi.tiangolo.com/tutorial/background-tasks/): separar recursos del proceso del trabajo duradero requerido. Una tarea en memoria no sustituye el registro persistente exigido por el producto.
- Candidatos de herramientas y páginas de transacciones, migraciones y bloqueo de dependencias: [registro de decisiones](decisions.md#herramientas-propuesta-inicial-y-selección-actual).

## Comprobaciones de esta entrega

Comprobaciones ejecutadas el 2026-10-21 con lectura de archivos y PowerShell:

- Inventario: 11 archivos Markdown; ningún archivo de producto, manifiesto o migración. Diez documentos nuevos y la especificación aportada por el usuario con referencias adaptadas.
- Enlaces: 39 referencias locales y 3 anclas resueltas, sin destinos ausentes. Bloques de código cerrados y sin espacios al final de línea.
- Plan: 23 tareas y 12 checkpoints; mismas tareas en plan/lista de control, sin IDs desconocidos ni dependencias de tarea hacia pasos posteriores.
- Especificación: comparación del texto de §§1–8 con la fuente de procedencia, normalizando solo saltos de línea; contenido técnico idéntico. Cambios limitados a enlaces y nota de traslado/propiedad.
- Revisión de contenido: límites de tres proyectos, propiedad, decisiones abiertas y escenarios de fallo trazados a tareas. Diagrama Mermaid revisado como texto; no se ha comprobado con un renderizador.

No se han probado aislamiento, transacciones, API, workers, contratos ejecutables, rendimiento, CI ni despliegue. Tampoco hay verificación de consumidores Rust/Hub. Todo ello aparece como trabajo futuro, con criterios en [calidad](quality.md) y [plan](../tasks/P-20261021-01-api-foundation/plan.md).

## Revisión de la copia del escritorio · 2026-10-23

El usuario añadió [la documentación del escritorio](nightingale-desktop-docs/README.md) y autorizó alinear sus diferencias con API. Esta sección registra la revisión actual; las secciones anteriores conservan la evidencia de T01. La supresión previa por el usuario de la sección de referencia Free-Win Orders se conserva; no se restaura.

La copia aportada declara PMD/DAT 0.3 y SRS 0.5, todos del 2026-10-21; su índice distingue origen, versión y ajustes locales del 2026-10-23. No incluye una revisión Git del origen ni los planes del escritorio. No se ha consultado el estado remoto ni modificado el repositorio original. La especificación API pasa a 0.2 en este repositorio; su ruta duplicada se sustituye por referencia.

| Diferencia revisada | Tratamiento documental actual |
|---|---|
| Escritorio deja abiertas identidad y aceptación ante revocación | Se alinea con D06: OIDC externo, permisos/dispositivos en API y permisos vigentes al aceptar; proveedor, sesiones, vínculo, orden concurrente y revisión siguen pendientes |
| Flujo atribuye invalidar confirmación al aviso posterior al Hub | API invalida con el cambio de horario en una transacción; el aviso posterior concilia accesos y solicitudes |
| Clave local presentada como garantía de envío externo único | Se distingue trabajo duplicado de resultado externo desconocido; consulta/deduplicación del proveedor o revisión antes de repetir |
| Especificación API duplicada y enlaces a planes no importados | Una referencia a la fuente API por nombre de repositorio/documento; origen/versiones en el índice. Por instrucción posterior del usuario, se conservan los destinos originales de los planes para el traslado al escritorio |
| Solicitud de cambio y lista de espera sin acuerdo completo | P05/P06 aprobados como criterios revisables: solicitud separada e interés separado de reserva autorizada por personal. O04/O05 permanecen abiertos para detalles; no se amplía Hub |

El usuario aceptó C13 y los criterios P05/P06 el 2026-10-23, reservándose revisarlos al implementar. También indicó que trasladará los archivos al repositorio original del escritorio y pidió no cambiar rutas. Se restauran los destinos originales de sus enlaces y se retiran las dependencias relativas añadidas hacia documentos de API; dos referencias a planes siguen sin destino en esta copia porque sus archivos pertenecen al escritorio. No se afirma haberlos comprobado en el origen ni haber realizado el traslado. La aprobación no acredita funciones, contratos ejecutables ni cierre de T04. Las comprobaciones se registran después de ejecutarlas en [la lista de control](../tasks/P-20261021-01-api-foundation/todo.md).
