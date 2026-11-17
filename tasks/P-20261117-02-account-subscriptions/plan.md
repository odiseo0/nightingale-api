# P-20261117-02-account-subscriptions: suscripciones con verificación manual

**Estado:** Approved. **Creado:** 2026-11-17. **Actualizado:** 2026-11-17. **Lista de tareas:** [todo.md](todo.md).

## 1. Contexto y resultado

La especificación [account-subscriptions.md](../../docs/account-subscriptions.md) está aprobada. El plan implementará planes para médico independiente, consultorio pequeño y centro médico; precios USD con equivalente VES a tasa BCV; periodos de 30 días o un año; límite de asientos como única diferencia funcional; reportes de pago con evidencia; y revisión manual por un operador de Nightingale.

No habrá Stripe, pasarela, cargos automáticos, tarjetas ni diferencias de funciones entre planes. Reportar un pago no activa ni extiende servicio. La aprobación debe generar una sola vez el periodo y conservar datos declarados, verificados, tasa, precio, evidencia e historia.

## 2. Precondiciones y límites

- Iniciar solo después de C06 aceptado de [P-20261117-01-authorization-policies](../P-20261117-01-authorization-policies/plan.md), que aporta el catálogo de políticas. Este plan lo extiende sin crear roles clínicos ni acceso global.
- Trabajo secuencial, sin delegación y con revisión expresa en cada checkpoint. Las decisiones de producto de T01–T04 requieren respuesta del usuario durante la ejecución; redactar este plan no las resuelve.
- No se implementa facturación de pacientes, gestión interna de clínicas, pruebas gratuitas, prorrateo o integración BCV automática salvo decisión expresa en T01–T04.
- No se cambia Rust/Hub ni se elige una interfaz de operador dentro del Hub por deducción. Las capturas nunca se publican en micrositios.
- Dependencias, almacenamiento y APIs de plataforma se eligen solo tras consultar manifiesto/lockfile y documentación oficial de la versión. No se instala nada durante la planificación.

## 3. Fuentes de verdad

- [Especificación de suscripciones](../../docs/account-subscriptions.md), incluidas `SU-D01`–`SU-D09` y `SU-O01`–`SU-O12`.
- [D15](../../docs/decisions.md#d15--especificación-de-suscripciones-con-verificación-manual) y [autorización aprobada](../../docs/authorization-rbac-abac.md).
- [Esquema físico](../../docs/database-schema.md), [contrato v1](../../docs/api-v1.md), [acceso](../../docs/access-design.md), [arquitectura](../../docs/architecture.md) y [calidad](../../docs/quality.md).
- `account_memberships`, invitaciones y dispositivos actuales para asientos, sin duplicar identidades.
- Patrones existentes de operaciones, DAOs, transacciones, auditoría, snapshots/deltas y probes PostgreSQL/Keycloak.

## 4. Decisiones de arquitectura

- **Componente `subscriptions`:** posee planes/versiones, suscripciones/periodos, cotizaciones, reportes, revisiones, tasas BCV y metadatos de evidencias.
- **Operador separado:** autenticación y canal según T03; acciones mínimas de plataforma sin pertenencia, rol `owner` ni acceso clínico.
- **Dinero exacto:** decimal y moneda explícitos; instantánea de plan, precio, tasa, fuente y redondeo en cada aprobación. No se revaloriza historia.
- **Dos conjuntos de datos:** declaración del cliente inmutable frente a verificación del operador; aprobación/rechazo como casos distintos.
- **Archivos fuera de sync:** evidencia privada con referencia autorizada; bytes fuera de journal, snapshots, logs y transacciones de base.
- **Asientos por pertenencia:** regla exacta decidida en T01, comprobada de nuevo al aceptar/reactivar y coordinada con cambios de plan.
- **Acceso comercial independiente:** no modifica roles, permisos clínicos, tokens o `accounts.status`; gracia/suspensión según T04 y sin borrado de datos.

## 5. Orden de dependencias

```text
Autorización C06 aceptada
  → decisiones comerciales, BCV/periodos, operador y políticas pendientes
  → diseño físico y contractual
  → dominio de dinero, planes y reportes
  → operador y migraciones
  → catálogo, cotizaciones y asientos
  → almacenamiento y presentación de reportes
  → revisión/aprobación/rechazo
  → sync, renovaciones y enforcement
  → indicadores, seguridad, contratos y cierre
```

No hay trabajo paralelo. Facturación de pacientes depende de este plan solo para reutilizar patrones concretos de evidencia/revisión; sus monedas y flujos se decidirán por separado.

## 6. Fases, tareas y checkpoints

### Fase 1 · Decisiones de producto

- [ ] **T01:** Cerrar planes, precios, cómputo/límites de asientos y exceso.
- [ ] **T02:** Cerrar BCV, monedas, duración anual e inicio/renovación de periodos.

#### C01 · Catálogo y reglas temporales decididos

- [ ] `SU-O02`–`SU-O06` y `SU-O08` tienen respuesta registrada sin valores supuestos.
- [ ] Ejemplos ficticios de dinero/periodos y enlaces documentales son coherentes.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 2 · Operador, políticas y diseño físico

- [ ] **T03:** Cerrar autenticación, recuperación y canal del operador.
- [ ] **T04:** Cerrar gracia/offline, archivos, pagos excepcionales y cambio de plan.
- [ ] **T05:** Diseñar físicamente planes, suscripciones, periodos y asientos.

#### C02 · Políticas y núcleo físico revisables

- [ ] `SU-O01`, `SU-O07` y `SU-O09`–`SU-O12` tienen decisiones explícitas.
- [ ] El núcleo físico protege moneda, historia, intervalos y unicidad de efecto.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 3 · Revisión y contratos de diseño

- [ ] **T06:** Diseñar físicamente tasas, reportes, revisiones y evidencias.
- [ ] **T07:** Diseñar rutas/operaciones, acceso y proyecciones en fuentes únicas.
- [ ] **T08:** Implementar dominio de dinero, BCV y cálculo de periodos.

#### C03 · Diseño completo y dominio temporal/monetario

- [ ] Contratos cubren cuenta, operador, revisión, recuperación y no divulgación.
- [ ] Cálculos exactos, 30 días, anual y renovaciones pasan pruebas de dominio.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 4 · Dominio y base de operador/persistencia

- [ ] **T09:** Implementar dominio de planes, suscripciones y asientos.
- [ ] **T10:** Implementar dominio de reportes, evidencia y transiciones de revisión.
- [ ] **T11:** Implementar identidad y contexto limitado del operador según T03.

#### C04 · Reglas y actor administrativo verificados

- [ ] Dominio deniega estados/relaciones inválidos sin SQL ni proveedores.
- [ ] Operador autentica solo con acciones aprobadas y sin acceso clínico.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 5 · Persistencia y catálogo operativo

- [ ] **T12:** Implementar migración/modelos/DAOs de planes, suscripciones y periodos.
- [ ] **T13:** Implementar migración/modelos/DAOs de tasas, reportes, revisiones y evidencias.
- [ ] **T14:** Implementar administración versionada del catálogo de planes.

#### C05 · Persistencia y catálogo funcionales

- [ ] Migraciones up/down/reapply, restricciones y privilegios SQL pasan en PostgreSQL.
- [ ] Versiones de planes preservan precios/asientos históricos y autorización de operador.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 6 · Cotización, asientos y almacenamiento

- [ ] **T15:** Implementar registro BCV y cotizaciones para cuentas.
- [ ] **T16:** Integrar límite de asientos con invitaciones/reactivaciones/cambios de plan.
- [ ] **T17:** Seleccionar con fuentes oficiales e implementar almacenamiento privado de evidencias.

#### C06 · Recorrido previo al pago y evidencia privada

- [ ] Cotizaciones conservan tasa/redondeo y no alteran historia.
- [ ] Carreras de asientos y validación/descarga privada de archivos pasan.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 7 · Reportes y decisión manual

- [ ] **T18:** Implementar presentación/consulta de reportes por la cuenta.
- [ ] **T19:** Implementar bandeja/detalle/evidencia para el operador.
- [ ] **T20:** Implementar aprobación atómica y creación/extensión única de periodos.

#### C07 · Activación manual transaccional

- [ ] Presentar no activa; aprobar confirma decisión, periodo, historia, recibo y auditoría una vez.
- [ ] Respuesta perdida y dos operadores no duplican días o efectos.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 8 · Rechazo, sincronización y administración comercial

- [ ] **T21:** Implementar rechazo y nueva presentación con historia.
- [ ] **T22:** Implementar proyección comercial mínima en snapshot/delta/SSE.
- [ ] **T23:** Implementar renovación anticipada/tardía, cambio de plan y cancelación.

#### C08 · Ciclo comercial recuperable

- [ ] Rechazos conservan estado anterior y nuevas presentaciones no borran historia.
- [ ] Sync no entrega evidencias y renovaciones/cambios no solapan periodos.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 9 · Enforcement, indicadores y seguridad

- [ ] **T24:** Aplicar gracia/suspensión y política offline sin cambiar permisos personales.
- [ ] **T25:** Implementar indicadores administrativos por plan, estado, moneda y asientos.
- [ ] **T26:** Completar pruebas de aislamiento, concurrencia, archivos y recuperación.

#### C09 · Seguridad y operación local comprobadas

- [ ] Suspensión no borra datos ni abre acceso; indicadores no mezclan monedas/estados.
- [ ] Aprobaciones, asientos, cambios de plan y accesos cruzados pasan probes reales.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 10 · Contratos y cierre

- [ ] **T27:** Generar/verificar contratos y actualizar documentación de comportamiento.
- [ ] **T28:** Ejecutar cierre integral y registrar evidencia y límites.

#### C10 · Suscripciones listas para revisión final

- [ ] Suite, probes, migraciones, contratos y build pasan sobre el entregable.
- [ ] El flujo cotización→reporte→revisión→periodo→renovación funciona con datos ficticios.
- [ ] Revisión y aceptación expresa del usuario.

## 7. Riesgos y mitigación

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Aprobación duplicada concede días extra | Alto | Restricción de origen único, bloqueos, recibo idempotente y carrera de dos operadores |
| Tasa/fecha/redondeo ambiguos | Alto | T02 antes del esquema/contrato; decimal exacto e instantáneas históricas |
| Dos integrantes ocupan el último asiento | Alto | Coordinación con pertenencia/cambio de plan y prueba con conexiones independientes |
| Operador obtiene acceso clínico | Alto | Actor/acciones separados, pruebas negativas y ausencia de rol de cuenta |
| Capturas quedan públicas o en sync | Alto | Storage privado, descarga reautorizada y exclusión explícita de journal/logs |
| Periodos se solapan o pierden días | Alto | Intervalos `[start,end)`, restricciones físicas y casos anticipado/tardío/anual |
| Suspensión borra datos o revoca identidades | Alto | Estado comercial separado y pruebas de conservación/recuperación |
| Dependencia de storage elegida por costumbre | Medio | T17 docs-first con versión oficial, justificación y revisión antes del adaptador |

## 8. Preguntas abiertas durante la planificación

Todas las `SU-Oxx` se asignan a T01–T04. Ninguna queda sin propietario. Las tareas dependientes no pueden iniciar hasta la respuesta y el checkpoint correspondiente; el resto del orden permanece explícito sin elegir valores por defecto.

## 9. Evidencia y límites

Cada tarea registra comandos y resultados reales en `todo.md`. Integridad y carreras requieren PostgreSQL Test aislado; archivos usan datos ficticios. No se acredita banco, BCV en vivo, operador en producción, Rust/Hub, copias/restauración, datos reales o despliegue sin pruebas específicas posteriores.
