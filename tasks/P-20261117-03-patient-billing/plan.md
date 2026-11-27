# P-20261117-03-patient-billing: facturación administrativa de pacientes

**Estado:** Completed. **Creado:** 2026-11-17. **Actualizado:** 2026-11-27. **Lista de tareas:** [todo.md](todo.md).

## 1. Contexto y resultado

La especificación [patient-billing.md](../../docs/patient-billing.md) está aprobada. El plan implementará precios base/de oferta, cargos por paciente con instantáneas, reportes de pago con captura, revisión por asistente autorizada, pagos administrativos, saldos, comprobantes no fiscales, sincronización financiera y analítica.

Nightingale no procesará dinero ni emitirá factura fiscal. Presentar un reporte no altera saldo; solo la aprobación crea un pago administrativo único. Datos declarados y verificados, evidencia, cargo, pago y comprobante permanecen separados.

## 2. Precondiciones y límites

- Iniciar después de C10 aceptado de [P-20261117-02-account-subscriptions](../P-20261117-02-account-subscriptions/plan.md). Se reutilizan políticas, almacenamiento privado y patrones de revisión sin mezclar pagos de planes y pacientes.
- Trabajo secuencial, sin delegación y con aceptación expresa de checkpoints. `BI-O01`–`BI-O12` se resuelven en T01–T04 durante la ejecución, no mediante supuestos del plan.
- No se implementa pasarela, banco, seguro, factura fiscal, contabilidad, nómina, reembolso real o interfaz completa del Hub.
- El soporte de paciente se limita a concesiones de cargo/reporte/comprobante. No crea cuenta general, pertenencia, acceso clínico ni publicación en micrositio.
- PDF/comprobante y cualquier dependencia nueva requieren manifiesto/lockfile y documentación oficial de versión antes de elegir. No se instala nada durante planificación.

## 3. Fuentes de verdad

- [Especificación de facturación](../../docs/patient-billing.md), decisiones `BI-D01`–`BI-D07` y pendientes `BI-O01`–`BI-O12`.
- [D16](../../docs/decisions.md#d16--especificación-de-facturación-administrativa-de-pacientes), D11 y D14.
- [Autorización](../../docs/authorization-rbac-abac.md), [suscripciones](../../docs/account-subscriptions.md), [esquema físico](../../docs/database-schema.md), [api-v1](../../docs/api-v1.md) y [arquitectura](../../docs/architecture.md).
- Servicios/ofertas y citas/atenciones actuales para propiedad, instantáneas y relaciones por cuenta/paciente.
- Evidencia y revisión del plan de suscripciones; operaciones, recibos, sync, auditoría y probes reales existentes.

## 4. Decisiones de arquitectura

- **Componente `billing`:** posee cargos/historias, reportes/revisiones, pagos/aplicaciones, comprobantes y metadatos de evidencia.
- **Precios en `services`:** base/oferta se resuelven mediante casos públicos; el cargo copia descripción, importe, moneda, tasa y origen. Las citas actuales no reciben precio nuevo por deducción.
- **Sin cargo automático:** crear/completar/cancelar citas o atenciones no genera cargos. Un cargo es una acción explícita con vínculos coherentes.
- **Paciente con concesión:** soporte mínimo en API con propietario fijado en T08; acciones read/report/result/receipt sobre objetos concretos. El UUID no es autorización.
- **Permisos financieros separados:** lectura, cargos, revisión, corrección y analítica según T03; acceso clínico no concede financiero ni viceversa.
- **Saldo coordinado:** pagos vigentes aplicados y decimal exacto; aprobaciones parciales/excedentes según T02, protegidas por restricciones y bloqueos PostgreSQL.
- **Archivos privados:** capturas/comprobantes fuera de journal y logs; se reutiliza soporte de suscripciones extrayendo solo lo común demostrado.

## 5. Orden de dependencias

```text
Suscripciones C10 aceptado
  → decisiones de moneda, cargos, reportes, permisos, enlace y archivos
  → diseño físico y contractual
  → dominio y persistencia de cargos/pagos/concesiones
  → precios y cargos del personal
  → evidencia, concesión y reporte del paciente
  → revisión/aprobación/rechazo y pagos directos
  → correcciones, comprobantes, sync/offline y analítica
  → seguridad, contratos y cierre
```

Documentos clínicos podrá reutilizar la concesión y el almacenamiento solo después del cierre aceptado de este plan; no se anticipa su contenido aquí.

## 6. Fases, tareas y checkpoints

### Fase 1 · Decisiones financieras y de acceso

- [ ] **T01:** Cerrar monedas/BCV, precios y vínculos/ajustes de cargos.
- [ ] **T02:** Cerrar datos del reporte, parciales/excedentes y pagos directos.
- [ ] **T03:** Cerrar permisos financieros y correcciones/anulaciones.

#### C01 · Reglas financieras decididas

- [x] `BI-O01`–`BI-O08` tienen respuesta registrada sin elegir valores por defecto.
- [x] Ejemplos de cargo, pago parcial/excedente y corrección son coherentes.
- [x] Revisión y aceptación expresa del usuario.

### Fase 2 · Paciente, archivos y diseño físico

- [ ] **T04:** Cerrar concesión del paciente, offline, retención y primer panel.
- [ ] **T05:** Diseñar físicamente precios, cargos, pagos y saldos.
- [ ] **T06:** Diseñar físicamente reportes, revisiones, evidencias y concesiones.

#### C02 · Alcance y núcleo físico revisables

- [x] `BI-O09`–`BI-O12` tienen decisiones y el mecanismo de enlace es limitado/revocable.
- [x] Restricciones cubren cuenta/paciente, moneda, historia, saldo y efecto único.
- [x] Revisión y aceptación expresa del usuario.

### Fase 3 · Contratos y dominio financiero

- [ ] **T07:** Diseñar rutas/operaciones del personal y paciente en fuentes únicas.
- [ ] **T08:** Diseñar audiencias, sync, analítica y propiedad de integración.
- [ ] **T09:** Implementar dominio de dinero, precios y saldos.

#### C03 · Contratos y cálculos básicos verificados

- [x] Contratos cubren todos los actores/recorridos y no divulgación.
- [x] Nulo/cero, monedas, conversiones y saldos pasan pruebas de dominio.
- [x] Revisión y aceptación expresa del usuario.

### Fase 4 · Dominio y persistencia

- [ ] **T10:** Implementar dominio de cargos, reportes, revisiones y pagos.
- [ ] **T11:** Implementar migración/modelos/DAOs de precios y cargos.
- [ ] **T12:** Implementar migración/modelos/DAOs de reportes, pagos y concesiones.

#### C04 · Base transaccional funcional

- [x] Migraciones, privilegios y restricciones pasan en PostgreSQL aislado.
- [x] Dominio y DAOs conservan instantáneas, historia y aislamiento por cuenta.
- [x] Revisión y aceptación expresa del usuario.

### Fase 5 · Precios, cargos y evidencia

- [ ] **T13:** Integrar precios base/oferta con servicios y permisos de catálogo.
- [ ] **T14:** Implementar creación/edición/emisión/cancelación de cargos por personal.
- [ ] **T15:** Extraer/reutilizar almacenamiento privado común para capturas de facturación.

#### C05 · Cargos y capturas listos para el paciente

- [x] Cambios de catálogo no alteran cargos; borradores no son visibles al paciente.
- [x] Archivos válidos/inválidos y descargas cruzadas cumplen seguridad.
- [x] Revisión y aceptación expresa del usuario.

### Fase 6 · Recorrido del paciente y bandeja de revisión

- [ ] **T16:** Implementar concesión y proyección mínima de cargos para paciente.
- [ ] **T17:** Implementar presentación/consulta de reportes con captura e idempotencia.
- [ ] **T18:** Implementar bandeja/detalle/evidencia para personal revisor.

#### C06 · Reporte completo sin efecto financiero anticipado

- [x] Paciente solo accede a su concesión y presentar deja saldo sin cambios.
- [x] Personal revisa con permiso explícito y sin acceso clínico derivado.
- [x] Revisión y aceptación expresa del usuario.

### Fase 7 · Pagos aprobados y rechazos

- [ ] **T19:** Implementar aprobación atómica, pago único y actualización de saldo.
- [ ] **T20:** Implementar rechazo y nueva presentación con historia.
- [ ] **T21:** Implementar registro directo de pagos por personal si T02 lo aprobó.

#### C07 · Cobro administrativo transaccional

- [x] Dos revisores/pagos parciales no duplican pago ni exceden cargo.
- [x] Rechazo conserva estado anterior y altas directas quedan diferenciadas de reportes.
- [x] Revisión y aceptación expresa del usuario.

### Fase 8 · Correcciones, comprobantes y sincronización

- [ ] **T22:** Implementar anulación/corrección de pagos y cargos con historia.
- [ ] **T23:** Seleccionar con fuentes oficiales e implementar comprobante no fiscal.
- [ ] **T24:** Implementar audiencia financiera en snapshot/delta/SSE.

#### C08 · Historia y recuperación financiera

- [x] Anulaciones no borran ni suman al vigente; comprobantes conservan instantánea/estado.
- [x] Sync recupera efectos sin incluir capturas/comprobantes o datos no autorizados.
- [x] Revisión y aceptación expresa del usuario.

### Fase 9 · Offline, analítica y seguridad

- [ ] **T25:** Implementar preparación offline permitida y reautorización al aceptar.
- [ ] **T26:** Implementar indicadores por fecha/moneda/servicio/profesional/estado.
- [ ] **T27:** Completar pruebas de aislamiento, carreras, archivos y recuperación.

#### C09 · Facturación segura y medible localmente

- [x] Reloj/caché local no altera autoridad; indicadores no mezclan fechas o monedas.
- [x] Aprobaciones, saldo, revocación, concesiones y respuestas perdidas pasan probes reales.
- [x] Revisión y aceptación expresa del usuario.

### Fase 10 · Contratos y cierre

- [ ] **T28:** Generar/verificar contratos, ejemplos y documentación real.
- [x] **T29:** Ejecutar cierre integral y registrar evidencia/límites.

#### C10 · Facturación lista para revisión final

- [x] Suite, probes, migraciones, contratos y build pasan sobre el entregable.
- [x] El flujo precio→cargo→reporte→revisión→pago→comprobante→analítica funciona con datos ficticios.
- [x] Revisión y aceptación expresa del usuario.

## 7. Riesgos y mitigación

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Dos aprobaciones exceden cargo o duplican pago | Alto | Restricción de origen, bloqueo cargo/reporte y carreras PostgreSQL |
| Mezcla de monedas/tasas o revalorización | Alto | T01 antes de contratos; decimal/moneda/tasa instantánea y totales separados |
| Permiso clínico abre finanzas o revisión abre clínica | Alto | Acciones independientes y pruebas negativas en ambas direcciones |
| Enlace de cita expone otros cargos/pacientes | Alto | Concesión por objeto/acción, revocación y proyección mínima |
| Captura/comprobante aparece en sync/logs | Alto | Bytes fuera del journal, descarga reautorizada y revisión de artefactos |
| Cargo/cita/atención se cruzan | Alto | FK compuestas y validación de cuenta/paciente en la aceptación |
| Anulación borra historia o simula reembolso | Medio | Estado/versiones y comprobante no fiscal, sin movimiento de dinero |
| Librería de comprobante elegida sin soporte | Medio | T23 docs-first y revisión antes de dependencia/adaptador |

## 8. Preguntas abiertas durante la planificación

T01–T04 asignan todas las `BI-Oxx`. Ninguna tarea dependiente puede comenzar antes de la decisión/checkpoint correspondiente. La redacción no escoge moneda, permisos, excedentes, mecanismo de enlace, formatos o indicadores por adelantado.

## 9. Evidencia y límites

La concurrencia se acredita con PostgreSQL Test aislado y datos ficticios. Las pruebas de API/archivos no acreditan banco, validez fiscal, firma, Rust/Hub, datos reales, copias/restauración o producción. Cada tarea registra evidencia real en `todo.md`; ningún checkpoint se acepta automáticamente.