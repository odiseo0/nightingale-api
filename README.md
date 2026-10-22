# Nightingale API

API de autorización, aceptación del estado compartido y sincronización de Nightingale. Python y FastAPI; PostgreSQL operativo privado. Este repositorio también tendrá los módulos y workers de recordatorios, entregas, integración con n8n e indicadores básicos.

**Estado al 2026-10-21:** base de proceso T03 comprobada; el usuario autorizó continuar con el acuerdo de acceso T04. El repositorio usa Python 3.15.1 y `uv.lock`; arranca FastAPI, valida configuración y expone salud. No hay esquema ni operaciones de negocio.

El escritorio guarda su trabajo con Rust/SQLite sin esperar a esta API. Patient Hub tiene su web, backend y datos propios; usa esta API para consultar y cambiar citas autorizadas. Ninguno recibe acceso SQL al PostgreSQL operativo.

## Documentos

| Documento | Función |
|---|---|
| [Especificación](docs/nightingale-api.md) | Fuente del alcance y los límites confirmados |
| [Reglas de trabajo](AGENTS.md) | Guía común para colaboradores y agentes |
| [Desarrollo y evidencia de T03](docs/operations/development.md) | Comandos, configuración, versiones, pruebas y límites actuales |
| [Arquitectura](docs/architecture.md) | Componentes, datos, dependencias y flujos propuestos |
| [Contratos](docs/contracts.md) | Propiedad, criterios de diseño y acuerdos por cerrar |
| [Calidad y pruebas](docs/quality.md) | Requisitos verificables y pruebas futuras |
| [Decisiones](docs/decisions.md) | Qué está confirmado, propuesto o pendiente |
| [Diseño de acceso T04](docs/access-design.md) | OIDC y permisos vigentes confirmados; sesiones, dispositivos y Hub en revisión |
| [Fuentes y revisión](docs/sources.md) | Referencias, diferencias y comprobaciones documentales |
| [Plan de implementación](tasks/P-20261021-01-api-foundation/plan.md) | Tareas, dependencias y puntos de revisión |

## Empezar a colaborar

Lee la especificación y el plan antes de cambiar archivos. La primera versión cubre pacientes, servicios, agenda, citas, recordatorios, lista de espera e indicadores básicos. Excluye historias clínicas, diagnósticos, resultados médicos, pagos y gestión de clínicas con varias sedes.

Desde la raíz, con `uv` disponible:

```powershell
uv sync --locked
uv run --locked nightingale-api
```

El servicio escucha en `127.0.0.1:8000`. `/health/live` indica si responde; `/health/ready` devuelve 503 sin PostgreSQL configurado. Consulta la guía de desarrollo para pruebas y configuración. Los acuerdos pendientes de T04 y los checkpoints posteriores conservan sus límites.
