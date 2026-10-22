# Registro de decisiones

**Fecha:** 2026-10-21. Confirmada significa acordada en el encargo o fuente vigente; propuesta requiere revisión; pendiente no autoriza una elección por defecto. Ningún estado acredita implementación.

## Confirmadas

### D01 · Tres proyectos y API transaccional

**Contexto:** el escritorio puede modificarse y operar sin red. **Decisión:** conserva casos de uso Rust/SQLite y envía operaciones completas; API autoriza y acepta el estado compartido en PostgreSQL privado. Hub conserva su web, API, enlaces, reglas y solicitudes y usa API para citas. Repositorios separados.

**Sustituye:** propuestas históricas de sincronización SQL directa y de un solo proyecto cloud. **Consecuencia:** ni escritorio ni Hub reciben credenciales SQL; API debe validar aun si el cliente afirma haberlo hecho. No convierte el guardado local en dependiente de la red. Fuente: encargo y especificación §§1–5; ADR del escritorio del 2026-10-21 identificado en [fuentes](sources.md).

### D02 · Propiedad y aceptación

API posee contratos remotos, migraciones operativas, idempotencia, Change Log, historial/auditoría y trabajo persistente. Acepta cada operación en su límite atómico y responde tras commit; los contratos no exponen el esquema SQL. Fuente: especificación §§2–4 y 8. Consecuencia: los adaptadores del Hub y los workers no crean otra vía de escritura de citas.

### D03 · Apoyo posterior al commit

Recordatorios, entregas/webhooks, n8n y analítica son módulos/workers de API. Persisten intención duradera, ejecutan fuera de la transacción de sync y usan permisos propios. Analítica tiene PostgreSQL separado. n8n es una herramienta externa sin SQL operativo. Fuente: especificación §6.

### D04 · Organización y alcance

Python/FastAPI/PostgreSQL y arquitectura hexagonal práctica por componentes según `src/application.py`, `api/`, `core/`, `settings/`. Sin una clase o puerto obligatorio por acción. Primera versión y exclusiones: [README](../README.md). Fuente: encargo y especificación; Free-Win Orders solo aporta organización.

### D05 · Trabajo revisable

La entrega inicial T01 solo documentó. El usuario autorizó T03 después y, tras pedir la corrección de anotaciones, autorizó continuar con T04. Plan y checkpoints conservan la revisión antes del trabajo que habilitan. La especificación copiada a `docs/nightingale-api.md` es la fuente de alcance de este proyecto; la copia previa del escritorio es referencia de procedencia, sin cambios aquí. Su sustitución por enlace debe hacerla su propietario fuera de esta entrega.

### D06 · Identidad externa y permisos vigentes

**Confirmada por el usuario el 2026-10-21:** proveedor externo OIDC para el personal; Nightingale API conserva permisos y dispositivos. Al aceptar una operación pendiente se aplican los permisos vigentes. Si falta permiso, se rechaza sin efecto y el escritorio conserva la intención para revisión. No se deduce autorización de la fecha local.

Proveedor concreto, sesiones, vínculo de dispositivos y alcance del Hub siguen por cerrar en T04. La comparación y las propuestas tienen una sola fuente en [diseño de acceso](access-design.md). Esta decisión no implementa autenticación ni autoriza una excepción a los permisos vigentes.

## Propuestas

| ID | Propuesta, motivo y alternativa | Consecuencia / revisión |
|---|---|---|
| P01 | Una aplicación modular con procesos HTTP y worker; componentes de [arquitectura](architecture.md). Evita dividir despliegues por capacidad antes de necesitarlo | Compartir casos de uso y recursos con permisos separados; revisar en C01 |
| P02 | Una unidad de trabajo pequeña coordina propietarios sin commits en repositorios. Alternativa: función explícita equivalente si resulta más simple | No filtrar SQL al dominio/aplicación; demostrar rollback integral; C01 y T07 |
| P03 | OpenAPI y JSON Schema con una fuente por tipo. Alternativas de fuente: esquema primero o modelos del adaptador que generan artefactos | Elegir origen, generación y compatibilidad en T05 antes del contrato ejecutable |
| P04 | Trabajo duradero en PostgreSQL y publicación tras commit; un broker puede servir de transporte | Un broker no sustituye la evidencia persistente. Comparar sondeo y publicación en T16; no escoger cola ahora |

## Herramientas: propuesta inicial y selección actual

La propuesta inicial no fijaba versiones. Después, el usuario añadió Python, `uv` y las dependencias del manifiesto y autorizó iniciar la fundación. Se conservó esa selección y se añadió el extra `sqlalchemy[asyncio]` que exige su API asíncrona. Versiones comprobadas y fuentes por API: [guía de desarrollo](operations/development.md). La tabla siguiente conserva la comparación inicial; no ordena instalar alternativas.

| Necesidad | Candidato y razón | Alternativa / condición de elección |
|---|---|---|
| Entorno y dependencias reproducibles | `uv`, por gestión de entorno y [lockfile verificable](https://docs.astral.sh/uv/concepts/projects/sync/) | `venv`/pip con estrategia de bloqueo explícita; elegir un solo gestor en T02 |
| Persistencia y migraciones | SQLAlchemy, por consultas y [control de transacciones](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), con Alembic para [migraciones versionadas](https://alembic.sqlalchemy.org/en/latest/) | Psycopg con SQL explícito y migraciones controladas; comparar coste y claridad antes de elegir. No mantener dos vías de persistencia para el mismo caso; SQLAlchemy sí necesita un controlador |
| Controlador PostgreSQL | Psycopg si satisface el modo de I/O y las versiones elegidas | Comparar con el controlador compatible requerido; su [gestión de transacciones](https://www.psycopg.org/psycopg3/docs/basic/transactions.html) exige límites explícitos |
| Configuración | Validación de entorno al iniciar; evaluar `pydantic-settings` si reduce código real | Biblioteca estándar con validación concreta. No convertir configuración ni DTO en dominio |
| Pruebas y revisión estática | Evaluar pytest y Ruff; HTTPX solo si hace falta al cliente de prueba | Biblioteca estándar donde baste; T02 debe justificar cada herramienta, versiones y comandos |
| Servicio HTTP | Evaluar Uvicorn como servidor ASGI de FastAPI | Modo y número de procesos según entorno y medidas, sin copiar Docker/Compose ni elegir cloud |

**Selección para T03:** Python 3.15.1, uv/uv_build 0.13.4, FastAPI 0.159.1, Pydantic 2.14.1, pydantic-settings 2.16.1, SQLAlchemy 2.1.6, asyncpg 0.32.0 y Uvicorn 0.54.0. `uv.lock` fija las dependencias; greenlet 3.5.6 llegó mediante el extra asyncio. Se usa unittest y el cliente HTTPX ya instalado, sin añadir pytest o Ruff. PostgreSQL de prueba, migraciones/Alembic y despliegue siguen pendientes. No se interpreta “PostgreSQL 18” en una referencia como versión elegida.

## Pendientes y condición para resolverlos

| ID | Decisión y evidencia necesaria | Propietario de decisión / antes de |
|---|---|---|
| O01 | Parcialmente resuelta por D06: OIDC externo, permisos/dispositivos en API y permisos vigentes al aceptar. Faltan proveedor, sesiones, alta/vínculo de dispositivo, roles, orden de revocación y recorrido de revisión | Usuario y responsable de seguridad/API; T04, antes de T08 |
| O02 | Cómo API verifica el alcance del Hub y su revocación; confianza, concesiones, rotación y consulta de resultados | API + Hub con revisión del usuario; T04, antes de T15 |
| O03 | Orden confirmado, snapshot/cursor, expiración, bajas, retención de idempotencia y ventana de compatibilidad | API + consumidores; prueba razonada de carreras y recuperación en T05, antes de T07/T13 |
| O04 | Datos mínimos de pacientes, duración fija/variable, zona temporal, conflictos con bloqueos/servicios inactivos y transiciones; ciclo de `reschedule_requested`, rechazo y retirada | Usuario/producto, API + Hub; T06, antes de T09–T12/T15 |
| O05 | Lista de espera: prioridad, oferta/expiración, quién responde y qué hace el personal. Las fuentes mencionan aceptación de ofertas pero el paciente no puede reservar otro horario | Usuario/producto y propietarios; T19 antes de T20. Mantener límite actual del Hub hasta decisión expresa |
| O06 | Política y proveedor oficial de WhatsApp, datos permitidos, cancelación de trabajos y conciliación de resultado desconocido | Usuario/producto y comunicaciones; evidencia del proveedor en T17 antes de envíos reales |
| O07 | Cola, reclamación y recuperación de workers; reintentos, límite, revisión manual y autenticación de n8n | API/operación; diseño y fallos controlados en T16/T18, antes de activar integración |
| O08 | Entornos de desarrollo/prueba, versión de PostgreSQL, proveedor cloud, red, secretos y despliegue | Usuario/operación; T02 para entorno de prueba, T22 para despliegue. No heredar las decisiones cloud históricas del escritorio |
| O09 | Límites, carga representativa, latencia, disponibilidad y demora admisible; alertas y umbrales | Usuario/producto/operación; medición y presupuesto en T22, antes de aceptar producción |
| O10 | Retención por clase (cambios, resultados, auditoría, datos, trabajos, copias), acceso y eliminación; RPO/RTO y restauración | Usuario/producto/operación; T05 para sync, T22 antes de datos reales/producción |
| O11 | Definición de indicadores, datos mínimos, ventana y frecuencia ETL; límites de uso analítico | Usuario/producto + API; T21 antes de fijar proyecciones |

Los pendientes no impiden revisar esta propuesta. Sí impiden implementar la parte que dependa de ellos. Para cambiar una decisión, registrar fecha, motivo, alcance, alternativa, consecuencia y qué ID sustituye; conservar la anterior como historial.
