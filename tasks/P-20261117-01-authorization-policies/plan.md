# P-20261117-01-authorization-policies: normalización de autorización RBAC/ABAC

**Estado:** Approved. **Creado:** 2026-11-17. **Actualizado:** 2026-11-17. **Lista de tareas:** [todo.md](todo.md).

## 1. Contexto y resultado

La especificación [authorization-rbac-abac.md](../../docs/authorization-rbac-abac.md) está aprobada. La implementación actual ya aplica permisos por cuenta, objeto, acción y sección, pero el descubrimiento `allowedActions`, la ejecución de lotes, las lecturas clínicas y las audiencias de sincronización mantienen correspondencias distribuidas.

El resultado debe ser una capacidad lógica de autorización con un catálogo tipado y funciones pequeñas que sirvan tanto para descubrir acciones como para exigirlas. Se conservarán los roles `owner`/`assistant`, las ocho secciones clínicas, los niveles `none`/`read`/`read_write`, las reglas por objeto y todos los comportamientos públicos vigentes.

No se crea un microservicio, motor de políticas, lenguaje de reglas, rol nuevo ni propietario alternativo de identidad/pertenencias. No se añaden permisos financieros, documentales, de paciente, operador o suscripción: sus planes posteriores extenderán el catálogo.

## 2. Precondiciones y límites

- Antes de iniciar cualquier tarea, C09 de [P-20261116-02-clinical-routine](../P-20261116-02-clinical-routine/plan.md) debe estar aceptado y ese plan debe quedar Completed. Este plan no modifica su evidencia ni ejecuta trabajo clínico pendiente.
- Trabajo secuencial, una tarea a la vez y sin delegación. Cada checkpoint exige revisión expresa del usuario.
- No se cambian tablas, migraciones, token opaco, OIDC/Keycloak, rutas, modelos JSON, `contractVersion`, `modelRevision` ni dependencias.
- No se modifica Rust/Hub ni se declara integración con consumidores o producción.
- Si las pruebas de caracterización descubren una diferencia entre comportamiento actual y especificación aprobada, se detiene solo la parte afectada para decisión del usuario; no se amplía acceso en silencio.

## 3. Fuentes de verdad

- [Especificación de autorización](../../docs/authorization-rbac-abac.md), especialmente §§6–22.
- [D14](../../docs/decisions.md#d14--especificación-separada-de-autorización-rbacabac), D06, D09 y D10.
- [Diseño de acceso](../../docs/access-design.md), [arquitectura](../../docs/architecture.md) y [contrato v1](../../docs/api-v1.md).
- `src/api/authorization/application/authorization_cases.py`: autenticación y bloqueos globales.
- `src/api/accounts/application/accounts_cases.py`: contexto, rol, acciones y secciones.
- `src/api/clinical_records/application/access_cases.py`: correspondencia clínica.
- `src/api/sync/application/operations_cases.py`, `download_cases.py`, `snapshot_cases.py` y `events_cases.py`: ejecución y alcance.
- `tests/test_authorization.py`, `test_accounts.py`, `test_clinical_permissions.py`, `test_downloads.py` y `test_events.py`.
- Probes reales `access`, `sync`, `clinical_permissions`, `downloads` y `events`.

## 4. Decisiones de arquitectura

- **Catálogo sin SQL:** descriptores de dominio en `accounts` describen acciones de lote, rol base, sección/nivel y regla de objeto. No reciben sesión ni construyen consultas.
- **Autenticación separada:** `authorization` conserva actor, credenciales y dispositivos globales. `accounts` conserva contexto y permisos por cuenta.
- **Objetos con propietario:** servicios, agenda/bloqueos y demás componentes siguen aportando atributos propios mediante casos públicos; el catálogo no importa repositorios.
- **Compatibilidad observable:** mismos nombres/orden de `allowedActions`, códigos HTTP, ausencia de objetos ajenos, resultados idempotentes, audiencias, épocas y defaults.
- **Denegación cerrada:** toda acción de lote y audiencia conocida tiene descriptor; lo desconocido se rechaza. No se usan `Any`, `cast` o supresiones para el despacho.
- **Sin contrato duplicado:** los esquemas Pydantic y api-v1 conservan sus responsabilidades. El catálogo es interno, no un nuevo endpoint de políticas.

## 5. Orden de dependencias

```text
C09 Etapa 2 aceptado
  → caracterización de roles, secciones y contratos
  → catálogo tipado de dominio
  → AccessResponse y ejecución administrativa
  → escrituras/resultados clínicos y reglas por objeto
  → lecturas y proyecciones de sincronización
  → SSE/cambios de permisos y carreras reales
  → compatibilidad contractual, documentación y cierre
```

No hay tareas paralelas. Los planes de suscripciones, facturación y documentos pueden diseñarse después, pero su implementación que extienda políticas depende del cierre aceptado de este plan.

## 6. Fases y tareas

### Fase 1 · Caracterización y diseño ejecutable

- [ ] **T01:** Caracterizar matriz de roles y acciones publicadas.
- [ ] **T02:** Caracterizar secciones, resultados y audiencias clínicas.
- [ ] **T03:** Fijar correspondencia del catálogo y compatibilidad en documentación vigente.

#### C01 · Línea base de autorización

- [ ] Pruebas de caracterización y suite completas pasan.
- [ ] La correspondencia propuesta cubre todas las acciones/secciones sin cambiar comportamiento.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 2 · Catálogo y escrituras administrativas

- [ ] **T04:** Introducir descriptores y evaluación pura de políticas.
- [ ] **T05:** Derivar `AccessResponse.allowedActions` del catálogo.
- [ ] **T06:** Autorizar acciones administrativas del lote mediante descriptores.

#### C02 · Descubrimiento y ejecución administrativa unificados

- [ ] Catálogo, acciones publicadas y rechazos administrativos coinciden.
- [ ] Pruebas de estructura, acceso, cuentas y operaciones pasan.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 3 · Clínica y reglas por objeto

- [ ] **T07:** Unificar sección/nivel de escrituras y resultados clínicos.
- [ ] **T08:** Integrar reglas de catálogo profesional y bloqueos sin trasladar propiedad.
- [ ] **T09:** Unificar lecturas y secciones legibles con el catálogo.

#### C03 · Autorización clínica y de objetos coherente

- [ ] `none`/`read`/`read_write`, recibos y reglas por objeto conservan comportamiento.
- [ ] Probes reales de permisos clínicos, servicios y acceso pasan.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 4 · Sincronización y cambios de alcance

- [ ] **T10:** Derivar audiencias de snapshot/delta del catálogo.
- [ ] **T11:** Aplicar el mismo alcance a cursores, época y SSE.
- [ ] **T12:** Conservar versiones y épocas al cambiar permisos/pertenencias.

#### C04 · Alcance de sincronización unificado

- [ ] Capturas, deltas, grupos invisibles y cierre de streams pasan.
- [ ] Los cambios de permisos conservan atomicidad y recuperación.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 5 · Riesgo transaccional y compatibilidad

- [ ] **T13:** Demostrar carreras de aceptación/revocación y cambio de sección en PostgreSQL.
- [ ] **T14:** Ejecutar matriz HTTP de aislamiento, resultados y no divulgación.
- [ ] **T15:** Comprobar compatibilidad de contratos y ejemplos generados.

#### C05 · Seguridad y compatibilidad demostradas localmente

- [ ] Carreras y matriz HTTP pasan en servicios Test aislados.
- [ ] Contratos, ejemplos y build conservan compatibilidad.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 6 · Documentación y cierre

- [ ] **T16:** Actualizar arquitectura, acceso y explicación contractual.
- [ ] **T17:** Ejecutar cierre integral y registrar evidencia/límites.

#### C06 · Normalización lista para revisión final

- [ ] Suite, probes afectados, contratos y build pasan.
- [ ] Documentación y diff no contienen afirmaciones de consumidores/producción.
- [ ] Revisión y aceptación expresa del usuario; solo entonces pueden extenderlo otros planes.

## 7. Riesgos y mitigación

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Una refactorización amplía o reduce permisos | Alto | Caracterización previa, matriz exacta y comparación de respuestas/estado en cada fase |
| `allowedActions` diverge del despacho | Alto | Una sola fuente de descriptores y pruebas de cobertura exhaustiva |
| Se rompe el orden de bloqueos o revocación | Alto | No cambiar autenticación/orden salvo necesidad demostrada; probes PostgreSQL con esperas reales |
| Audiencias nuevas omiten una entidad | Alto | Prueba cerrada entidad→audiencia→sección y capturas/deltas reales |
| Recibos antiguos pierden sección o resultado | Alto | Sin migración; conservar `clinical_section` y casos ambiguos fail-closed |
| El catálogo se convierte en framework genérico | Medio | Funciones/datos cerrados, sin lenguaje de reglas, dependencias ni clases por acción |
| Se acepta trabajo de Etapa 2 por dependencia | Medio | Precondición explícita y estados de planes conservados |

## 8. Preguntas abiertas

- `AU-O01`: roles futuros; no bloquea esta normalización porque se conservan los dos actuales.
- `AU-O02`/`AU-O03`: defaults financieros/documentales; se resolverán en sus planes, sin adelantar permisos.
- `AU-O04`/`AU-O07`: operador y política comercial; pertenecen a suscripciones.
- `AU-O05`: concesiones de documentos; pertenece a documentos/Hub.
- `AU-O06`: explicación pública adicional de denegaciones; fuera de este plan.

## 9. Evidencia y cierre

Cada tarea registra comandos y resultados reales en `todo.md`. La concurrencia e integridad se acreditan solo con PostgreSQL Test aislado. Las pruebas HTTP no acreditan Rust/Hub, datos reales, saturación, despliegue o producción. Ningún checkpoint se marca aceptado por el agente.
