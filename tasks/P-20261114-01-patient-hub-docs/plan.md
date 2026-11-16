# P-20261114-01-patient-hub-docs: alcance documental de Patient Hub

**Estado:** In progress. **Fecha:** 2026-11-14. **Lista:** [todo.md](todo.md).

El encargo del usuario autoriza ajustar la documentación de API a las decisiones sobre Patient Hub. Se trabaja una tarea a la vez, sin delegación. El plan de API para escritorio conserva C11 pendiente; este encargo no lo acepta ni reanuda su implementación.

## Resultado y límites

Una descripción vigente de tres proyectos: Nightingale para escritorio, Patient Hub para la interfaz web y Nightingale API para todas las funciones de servidor del Hub. Distinguir contrato actual, alcance futuro acordado y diseño pendiente. Conservar antecedentes con sus sustituciones explícitas.

Solo documentación de este repositorio. Sin código, migraciones, dependencias, artefactos generados, rutas definitivas, campos o tablas nuevos, commits ni despliegues. No se modifica el escritorio ni se crea aquí `patient-hub-docs/` o su `Master-Plan.md`; el usuario reserva ese trabajo para otra sesión en el repositorio del escritorio.

## Tareas y comprobaciones

| Tarea / propietario | Entradas y dependencia | Aceptación y comprobación |
|---|---|---|
| T01 · Revisar fuentes / documentación API | Encargo, AGENTS, especificación, decisiones y planes vigentes; sin dependencia | Inspeccionar Git, localizar referencias al Hub en todo el repositorio y comprobar contrato actual por lectura del código. Registrar límites y enlaces previos |
| T02 · Alinear fuentes / documentación API | T01 | Registrar D11 y qué sustituye. Alinear alcance, propiedad, acceso y referencias. Mantener historia y separar micrositio público de acceso limitado a citas; revisión de diff |
| T03 · Comprobar y entregar / documentación API | T02 | Revisar enlaces locales y anclas, buscar arquitectura anterior aún vigente, ejecutar git diff --check y confirmar que solo cambia Markdown. Registrar resultados y límites en todo.md |

Contratos/datos afectados: solo su explicación y alcance futuro. Transacciones, sincronización y consumidores no cambian; no se acredita integración con Hub. El modelo físico conserva su fuente y contenido técnico.

## Checkpoint C01

Tras T03, entregar archivos y motivos, decisiones sustituidas, pendientes y evidencia. Detenerse para revisión del usuario, sin marcar aceptación ni cerrar el plan por cuenta propia.
