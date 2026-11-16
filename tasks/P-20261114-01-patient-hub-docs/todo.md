# Lista de control · P-20261114-01-patient-hub-docs

**Plan:** [plan.md](plan.md). **Estado:** In progress. **Fecha:** 2026-11-14.

| Tarea | Estado | Evidencia |
|---|---|---|
| T01 | Done | Fuentes y Git leídos; árbol inicial limpio. Búsqueda global de referencias; lectura de routers, acceso, servicios y citas. Las rutas de negocio actuales usan acceso del personal; no hay contrato público del Hub. Revisión inicial de 25 Markdown y 145 enlaces locales: 15 destinos ausentes previos, entre ellos contracts/ y antiguas copias del escritorio |
| T02 | Done | D11 registra las decisiones y sus sustituciones; fuentes e índices alineados. Revisión secuencial de contenido y diff: lectura pública y acceso privado a cita separados, contrato actual sin ampliación y antecedentes conservados |
| T03 | Done | 27 Markdown, 196 enlaces locales y 43 anclas comprobados; cero destinos ausentes nuevos y cero anclas rotas. Permanecen los 15 enlaces ausentes previos. git diff --check correcto; 18 archivos cambiados, todos Markdown. Catálogo/modelos HTTP actuales y esquema físico sin cambios, salvo aclaraciones de alcance |

- [ ] C01: revisión y aceptación expresa del usuario.

**Entrega C01 lista para revisión.** T01–T03 comprobadas en secuencia; el plan conserva In progress y no se registra aceptación del usuario.

No se ejecutan pruebas de producto por este cambio documental. No se acepta C11 del plan de escritorio ni se acredita implementación del Hub.

## Archivos y motivos

| Archivos | Motivo |
|---|---|
| [README.md](../../README.md), [AGENTS.md](../../AGENTS.md) | Reparto de proyectos y reglas vigentes; límites de lectura pública y acciones del paciente |
| [nightingale-api.md](../../docs/nightingale-api.md) | Especificación 0.5: ambas plantillas, acceso a cita, exclusiones y diseño pendiente |
| [architecture.md](../../docs/architecture.md) | Diagrama web → API, sin segundo servidor/almacén; funciones de servidor y reglas comunes en API |
| [contracts.md](../../docs/contracts.md) | API posee contratos públicos y limitados futuros; Hub posee interfaz web |
| [access-design.md](../../docs/access-design.md) | Separar acceso del personal, micrositio público y acceso limitado a cita; propuesta anterior marcada como sustituida |
| [decisions.md](../../docs/decisions.md) | D11, actualización de D01/P05/O02 y conservación del resto del historial |
| [api-v1.md](../../docs/api-v1.md) | Aclarar que v1 no ofrece micrositios ni acciones del paciente; sin cambiar catálogo o formas actuales |
| [database-schema.md](../../docs/database-schema.md) | Solo explicación de alcance; sin cambios al modelo físico |
| [data-model.md](../../docs/data-model.md) | Mantener borrador retirado y marcar como sustituido su almacén propio del Hub |
| [quality.md](../../docs/quality.md), [sources.md](../../docs/sources.md) | Criterios futuros sin acreditarlos como pruebas; fuente nueva y precedencia sobre antecedentes |
| [tasks/README.md](../README.md), [plan de escritorio](../P-20261024-01-desktop-shared-api/plan.md) | Indexar el encargo y conservar límites de implementación y checkpoints previos |
| [plan anterior](../P-20261021-01-api-foundation/plan.md), [evidencia anterior](../P-20261021-01-api-foundation/todo.md) | Notas de sustitución sobre T04/T15/T17, sin reescribir pruebas ni estados históricos |
| [plan.md](plan.md), [todo.md](todo.md) | Alcance autorizado, tareas secuenciales y evidencia de este encargo |

## Decisiones sustituidas y pendientes

D11 sustituye el backend/API y almacén privados del Hub en D01 y fuentes antiguas, la autorización entre dos servidores de T04/O02 y la propiedad/conciliación entre almacenes de los recorridos de P05. Conserva el criterio funcional de P05 y la asignación por personal de P06. La presentación pública de clínicas no amplía la implementación de escritorio de D09.

Siguen pendientes: mecanismo/ciclo del enlace y acceso limitado, vigencia/revocación, proyecciones públicas y de cita, formas HTTP y ciclo de solicitudes/resultados. No se inventan rutas, campos, tablas o cuentas de paciente. No se halló una contradicción adicional que impida el ajuste documental. El trabajo futuro de `patient-hub-docs/` y `Master-Plan.md` queda fuera de este repositorio y de esta sesión.

## Límites de la comprobación de enlaces

La revisión inicial encontró 15 referencias locales con destinos ausentes, todas previas al encargo:

- Nueve referencias a `contracts/README.md`, `contracts/api-v1/nightingale-api.md` y `contracts/examples.json` desde README, api-v1, contracts, nightingale-api, operations/development, rust-api-guide y test-support/README.
- Cuatro referencias en database-schema a `master-plan.md`, `technical-architecture.md`, `srs.md` y `decisions/transactional-sync-three-projects.md`, procedentes del escritorio.
- Dos referencias a `nightingale-desktop-docs/README.md` desde decisions y sources.

Se conservan como antecedentes; no se generan contratos ni se restauran copias retiradas. Los enlaces nuevos apuntan a archivos presentes. La revisión no comprueba URLs externas, no renderiza Mermaid ni acredita funciones, seguridad, integración con consumidores u operación.

## Comprobaciones finales · 2026-11-14

Se ejecutó un comprobador temporal con la biblioteca estándar de Python sobre Markdown versionado y los dos documentos nuevos. Comparó los destinos locales y anclas con HEAD: 145 enlaces/24 anclas antes, 196 enlaces/43 anclas después; mismos 15 destinos ausentes y ninguna ancla rota. Comprobó bloques de código cerrados y ausencia de espacios finales en los archivos nuevos. No se añadió el comprobador al repositorio.

La comparación del esquema con HEAD, al retirar solo la nota de alcance nueva, da texto idéntico. El contenido del contrato v1 desde la autenticación Keycloak, incluido el catálogo, los modelos y las operaciones, también permanece idéntico. Git confirma solo 18 archivos Markdown cambiados y git diff --check sin errores. Las búsquedas globales de Hub/backend/almacén/concesiones y la lectura del diff dejan las referencias al reparto anterior solo como antecedentes marcados, sustituciones o exclusiones.

No se ejecutaron suite, integración, PostgreSQL, Keycloak, exportación de contratos o build por no cambiar producto. Sin código, migraciones, dependencias, artefactos generados, otros repositorios, commits o despliegues. El diagrama se revisó como texto, sin renderizador.
