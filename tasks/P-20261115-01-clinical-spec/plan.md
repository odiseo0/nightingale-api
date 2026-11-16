# P-20261115-01-clinical-spec: especificación clínica del paciente

**Estado:** Completed. **Fecha:** 2026-11-15. **Lista y evidencia:** [todo.md](todo.md).

## Encargo y resultado

El usuario solicita una especificación detallada de la ampliación clínica, sus decisiones y referencias FHIR/OMS. Será la fuente funcional para preparar los planes de tres etapas. El encargo autoriza este trabajo documental; no consta aceptación separada de esta organización de tareas ni de su checkpoint.

Solo documentación en este repositorio. Se conservan los cambios previos del Hub y los checkpoints pendientes: C11 de P-20261024-01-desktop-shared-api y C01 de P-20261114-01-patient-hub-docs. No se modifica su evidencia ni se reanuda código. Trabajo secuencial, sin delegación.

## Tareas

| Tarea / propietario | Entradas y dependencia | Aceptación y comprobación |
|---|---|---|
| T01 · Reunir acuerdos / documentación API | Conversación, AGENTS, especificación, decisiones, esquema, contratos y planes; sin dependencia | Distinguir acuerdos del usuario, propuestas de diseño y cuestiones abiertas; verificar fuentes oficiales pertinentes y estado de Git |
| T02 · Escribir e indexar / documentación API | T01 | Crear patient-clinical-record.md con objetivos, etapas, datos, flujos, integración, criterios y referencias; registrar D12 y enlaces desde los índices sin duplicar el esquema |
| T03 · Comprobar y entregar / documentación API | T02 | Revisar cobertura de la conversación, enlaces locales/anclas, fuentes externas y diff; registrar evidencia y límites reales |

Contratos/datos afectados: explicación del alcance futuro. El esquema físico conserva su fuente en docs/database-schema.md; el contrato actual no cambia. Transacciones y sincronización ejecutables: sin cambios. Consumidores: solo requisitos futuros; sin modificar Rust, Hub ni otros repositorios.

## Checkpoint C01

Tras T03, entregar la especificación y sus límites para revisión. No marcar aceptación del usuario ni iniciar los planes de implementación de las etapas. Esos planes definirán propietarios de componentes, datos/contratos, dependencias, transacciones, sincronización, comprobaciones y checkpoints según tasks/README.md.
