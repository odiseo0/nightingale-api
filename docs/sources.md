# Fuentes, diferencias y revisión documental

**Inspección inicial T01:** 2026-10-21. Este documento conserva la procedencia y evidencia de esa entrega. Estado y comprobaciones posteriores de T03: [guía de desarrollo](operations/development.md).

## Fuentes del repositorio

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

## Referencia de organización: Free-Win Orders

Origen verificado en la configuración de la copia: [odiseo0/free-win-orders](https://github.com/odiseo0/free-win-orders), rama `master`, revisión local `b961abb85cf022cfcd03f8ee06e1841317752bbf`. Copia leída: `C:/Users/Pedro/Documents/GitHub/nightingale/target/reference-free-win-orders-20261021/`. La consulta web falló y no se confirmó que esa revisión fuera la última remota. La lectura de archivos y de sus referencias Git sí estuvo disponible; no se ejecutó su aplicación.

| Archivos examinados dentro de `src/` | Qué aporta / límite observado |
|---|---|
| `application.py`, `api/api.py` | Composición, ciclo de recursos y agregación de rutas; no se trasladan su configuración ni contenido de producto |
| `api/roles/{domain,application,infrastructure,repository}/`, `api/order_periods/domain/rules.py` | Capacidad agrupada con reglas, casos, HTTP y persistencia. Sus casos de roles importan sesiones/modelos SQL; no se toma esa dependencia como regla para Nightingale |
| `api/deliveries/domain/providers.py` | Un contrato de proveedor tiene sentido cuando existe sustitución real; no exige uno por operación |
| `core/db/{dao,session}.py`, árbol de `core/` | Soporte técnico compartido. No se copia DAO genérico, sesiones globales, serialización o zona fija |
| `settings/{db_settings,__init__}.py`, árbol de `settings/` | Configuración agrupada por responsabilidad. No se copian campos, valores, carga de secretos ni dependencias |

La propuesta conserva la organización pedida y exige dominio y aplicación libres de detalles SQL/transporte. No adopta autenticación, PDM, caché, proveedor, Docker, comandos o versiones del proyecto de referencia.

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
