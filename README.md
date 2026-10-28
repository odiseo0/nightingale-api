# Nightingale API

API de autorización, aceptación del estado compartido y sincronización de Nightingale. Python y FastAPI; PostgreSQL operativo privado. Este repositorio también tendrá los módulos y workers de recordatorios, entregas, integración con n8n e indicadores básicos.

**Estado al 2026-10-28:** C10 aceptado; T31–T33 para revisión expresa C11. SSE, descarga y recuperación comprobados con PostgreSQL/Keycloak aislados y dos procesos API reales. Diez streams/20 commits/200 avisos: p95 local 120.1 ms, con cota superior que incluye commit de 122.5 ms. Migración 20261028_01: 28 tablas y btree_gist. [Contratos generados](contracts/README.md): 46 rutas, 47 operaciones HTTP y 70 esquemas, más los 42 payloads por lote. [Guía para Rust](docs/rust-api-guide.md) con ejemplos comprobados. Se conserva la aceptación atómica y el alta mediante [scripts/create_practice.py](scripts/create_practice.py). API_SYNC_SIGNING_KEY es secreta y común a procesos. C11 sigue sin aceptar; consumidores Rust/Hub y producción siguen fuera. Evidencia y límites en la [lista de control](tasks/P-20261024-01-desktop-shared-api/todo.md).

El escritorio guarda su trabajo con Rust/SQLite sin esperar a esta API. Patient Hub tiene su web, backend y datos propios; usa esta API para consultar y cambiar citas autorizadas. Ninguno recibe acceso SQL al PostgreSQL operativo.

## Documentos

| Documento | Función |
|---|---|
| [Especificación](docs/nightingale-api.md) | Fuente del alcance y los límites confirmados |
| [Reglas de trabajo](AGENTS.md) | Guía común para colaboradores y agentes |
| [Desarrollo y evidencia](docs/operations/development.md) | Corrección actual y registros de comprobaciones previas |
| [Soporte local de pruebas](test-support/README.md) | PostgreSQL y Keycloak sin Docker; OIDC, migraciones y transacciones con datos ficticios |
| [Arquitectura](docs/architecture.md) | Componentes, datos, dependencias y flujos propuestos |
| [Contratos](docs/contracts.md) | Propiedad, criterios de diseño y acuerdos por cerrar |
| [Contrato de diseño HTTP v1](docs/api-v1.md) | Rutas, operaciones, modelos públicos, permisos y recuperación de esta etapa |
| [Artefactos de contrato](contracts/README.md) | OpenAPI/JSON Schema generados desde código, origen y huellas |
| [Guía para Rust](docs/rust-api-guide.md) | Acceso, lotes, conflictos, SSE, cursores y recuperación; consumidor pendiente |
| [Esquema físico de diseño](docs/database-schema.md) | Única fuente del modelo; implementación parcial en migraciones y pruebas aisladas |
| [Calidad y pruebas](docs/quality.md) | Requisitos verificables y pruebas futuras |
| [Decisiones](docs/decisions.md) | Qué está confirmado, propuesto o pendiente |
| [Diseño de acceso](docs/access-design.md) | OIDC de emisión y token API sin vencimiento/revocable; Hub posterior aún en revisión |
| [Fuentes y revisión](docs/sources.md) | Referencias, diferencias y comprobaciones documentales |
| [Plan sucesor aprobado](tasks/P-20261024-01-desktop-shared-api/plan.md) | Tareas, dependencias y checkpoints de API para escritorio |

## Empezar a colaborar

Lee la especificación y el plan antes de cambiar archivos. Esta etapa cubre acceso, consulta independiente/equipo, pacientes, contactos, servicios, agenda, citas e intercambio entre dispositivos. Recordatorios, Hub, espera e indicadores corresponden a etapas posteriores. Se excluyen datos reales, producción, historia clínica, pagos, gestión clínica avanzada y cambios al escritorio.

Comandos de la base, desde la raíz con `uv` disponible:

```powershell
uv sync --locked
uv run --locked uvicorn src.application:app --host 127.0.0.1 --port 8000
```

El comando usa la app de módulo y la fábrica de sesiones existente, sin lifespan para la base ni comando propio del paquete. Configura la URI de PostgreSQL antes de importar la app: el motor actual la exige, aunque no abre conexiones al importar. `/health/live` responde 200 y `/health/ready` comprueba disponibilidad SQL. Las pruebas unitarias usan sustitutos; el soporte de integración usa PostgreSQL/Keycloak reales aislados, sin Docker. Se omite la prueba HTTP separada del wheel por petición del usuario. Cada checkpoint conserva revisión expresa.
