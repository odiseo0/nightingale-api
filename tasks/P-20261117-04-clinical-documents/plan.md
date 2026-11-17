# P-20261117-04-clinical-documents: récipes y órdenes de diagnóstico

**Estado:** Approved. **Creado:** 2026-11-17. **Actualizado:** 2026-11-17. **Lista de tareas:** [todo.md](todo.md).

## 1. Contexto y resultado

La especificación [clinical-documents.md](../../docs/clinical-documents.md) está aprobada. Este plan implementa el primer bloque documental de Etapa 3: borradores, récipes con copia farmacia/paciente, órdenes de diagnóstico, emisión profesional, numeración, instantáneas, firma manuscrita sobre impresión, PDF privado, sustitución/anulación, timeline, acceso del paciente y QR de verificación mínima.

API acredita contenido, emisor, instante, número y estado; no afirma que el médico firmó el papel, que una farmacia dispensó o que un laboratorio realizó exámenes. No se añade firma digital, red de farmacias/laboratorios, recomendación clínica, resultados, cierre universal de atenciones ni otras funciones de Etapa 3.

## 2. Precondiciones y límites

- Iniciar después de C10 aceptado de [P-20261117-03-patient-billing](../P-20261117-03-patient-billing/plan.md), reutilizando concesiones limitadas y almacenamiento privado. Las dependencias de autorización/suscripciones se conservan por la cadena de planes.
- Trabajo secuencial, sin delegación y con aceptación expresa de checkpoints. `CD-O01`–`CD-O12` se resuelven en T01–T04 durante ejecución; este plan no toma esas decisiones.
- La revisión jurídica venezolana debe usar fuentes oficiales/profesional competente y queda separada de pruebas técnicas. Sin ella no se habilita uso real, aunque el software local pase.
- No se implementa interfaz completa del Hub ni cuenta general de paciente. El QR no es una credencial de descarga clínica.
- Biblioteca PDF/renderizado se selecciona con manifiesto/lockfile y documentación oficial de versión en T16. No se instala nada durante planificación.

## 3. Fuentes de verdad

- [Especificación de documentos](../../docs/clinical-documents.md), `CD-D01`–`CD-D08` y `CD-O01`–`CD-O12`.
- [D17](../../docs/decisions.md#d17--especificación-de-récipes-y-órdenes-de-diagnóstico), D11, D12 y D14–D16.
- [Registro clínico](../../docs/patient-clinical-record.md), [autorización](../../docs/authorization-rbac-abac.md), [esquema físico](../../docs/database-schema.md), [api-v1](../../docs/api-v1.md) y [arquitectura](../../docs/architecture.md).
- Citas/atenciones/pacientes/profesionales actuales y timeline de Etapa 2.
- Concesiones/almacenamiento de facturación, trabajo durable, operaciones/recibos, sync/auditoría y probes PostgreSQL/Keycloak.

## 4. Decisiones de arquitectura

- **Componente `clinical_documents`:** posee cabecera común, elementos tipados, emisiones/snapshots, historias, numeración, artefactos y relaciones documentales.
- **Contenido separado por tipo:** `prescription_items` y `diagnostic_order_items`; no JSON libre compartido ni catálogo clínico obligatorio.
- **Emisión profesional:** owner sin vínculo profesional no emite; asistente prepara solo si T02 lo concede. El profesional a cargo se valida según T01.
- **Instantánea inmutable:** encabezado, profesional, paciente y contenido quedan fijados al emitir; reimprimir no crea versión clínica.
- **Documento/artefacto independientes:** `issued` puede tener PDF `pending`/`failed`; reintentar render no cambia número ni emisión.
- **Paciente y QR separados:** concesión read/download para documentos concretos; verificación pública mínima sin paciente, medicamentos, diagnóstico o exámenes.
- **Sin efectos derivados:** no cambia cita, última visita, medicación declarada, condiciones, resultados o facturación. Timeline guarda solo referencias.

## 5. Orden de dependencias

```text
Facturación C10 aceptada
  → requisitos jurídicos/datos, permisos, contenido, numeración y offline
  → plantillas/QR/enlace/retención y diseño físico/contractual
  → dominio tipado y persistencia
  → borradores, emisión y numeración transaccional
  → motor PDF, plantillas y worker de artefactos
  → sustitución/anulación, paciente y QR
  → sync/offline, carreras y validación visual
  → contratos, documentación y cierre
```

No hay tareas paralelas. La emisión offline, si T03 la aprueba, tiene una rama explícita T25; si no, se conserva online y se prueba su rechazo offline sin reducir alcance por decisión del agente.

## 6. Fases, tareas y checkpoints

### Fase 1 · Requisitos y decisiones clínicas

- [ ] **T01:** Cerrar revisión jurídica, datos mínimos y profesional a cargo.
- [ ] **T02:** Cerrar permisos de asistentes y numeración.
- [ ] **T03:** Cerrar campos de récipe/orden y emisión online/offline.

#### C01 · Reglas de emisión decididas

- [ ] `CD-O01`–`CD-O07` y `CD-O12` tienen respuesta/fuente registrada.
- [ ] Ejemplos ficticios de validación, numeración y emisión offline/online son coherentes.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 2 · Presentación y diseño físico

- [ ] **T04:** Cerrar plantillas, QR, enlace y retención.
- [ ] **T05:** Diseñar físicamente documentos, elementos, emisiones e historias.
- [ ] **T06:** Diseñar físicamente artefactos, secuencias, concesiones y datos profesionales.

#### C02 · Alcance documental y físico revisable

- [ ] `CD-O08`–`CD-O11` tienen decisiones y las plantillas no inventan contenido.
- [ ] Restricciones cubren ámbito, número único, instantáneas, elementos ordenados y archivos privados.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 3 · Contratos y dominio tipado

- [ ] **T07:** Diseñar rutas/operaciones, acceso, sync, timeline y verificación QR.
- [ ] **T08:** Implementar dominio común de documentos, borradores e instantáneas.
- [ ] **T09:** Implementar dominio y validación de récipes.

#### C03 · Contratos y núcleo de prescripción verificados

- [ ] Staff/paciente/QR tienen contratos y permisos sin fuga clínica.
- [ ] Borradores, instantáneas y elementos de récipe validan estados/contenido sin SQL.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 4 · Órdenes, datos profesionales y persistencia

- [ ] **T10:** Implementar dominio y validación de órdenes de diagnóstico.
- [ ] **T11:** Integrar credenciales profesionales y selección de datos del paciente.
- [ ] **T12:** Implementar migración/modelos/DAOs de documentos, elementos e historias.

#### C04 · Contenido y núcleo persistente funcionales

- [ ] Órdenes y snapshots usan datos reales del ámbito sin inferencias.
- [ ] Migraciones/DAOs protegen cuenta/paciente/tipo, orden e inmutabilidad.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 5 · Artefactos, borradores y emisión

- [ ] **T13:** Implementar persistencia de artefactos, secuencias y concesiones.
- [ ] **T14:** Implementar creación/edición/lectura de borradores y vista previa.
- [ ] **T15:** Implementar emisión atómica, numeración, vínculos y timeline.

#### C05 · Emisión transaccional disponible

- [ ] Solo profesional autorizado emite y repetición conserva número/contenido.
- [ ] Borradores no llegan al paciente y efectos/historia/timeline/recibo/grupo confirman juntos.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 6 · Motor PDF y plantillas

- [ ] **T16:** Seleccionar con fuentes oficiales e implementar base de renderizado PDF.
- [ ] **T17:** Implementar plantilla de récipe con copias farmacia/paciente.
- [ ] **T18:** Implementar plantilla de orden de diagnóstico.

#### C06 · Presentación visual comprobada

- [ ] PDF ficticios conservan campos, firma en blanco, QR y paginación sin truncado.
- [ ] Versiones de plantilla y datos ausentes no generan contenido clínico ficticio.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 7 · Archivos, historia y paciente

- [ ] **T19:** Implementar worker/almacenamiento/descarga de artefactos con recuperación.
- [ ] **T20:** Implementar sustitución, anulación e historia completa.
- [ ] **T21:** Extender concesiones del paciente para lectura/descarga documental.

#### C07 · Documentos emitidos consultables y corregibles

- [ ] Fallo de PDF no repite emisión y anulación/sustitución no borra.
- [ ] Paciente solo accede a documentos emitidos permitidos y sustitutos según T04.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 8 · QR, sincronización y offline

- [ ] **T22:** Implementar verificación pública mínima del QR con antienumeración.
- [ ] **T23:** Implementar audiencias documentales en snapshot/delta/SSE/timeline.
- [ ] **T24:** Implementar borradores offline y reautorización al sincronizar.

#### C08 · Acceso y recuperación sin contenido indebido

- [ ] QR no revela paciente/contenido y sync excluye PDF/audiencias no autorizadas.
- [ ] Reloj/caché local no emite ni extiende permisos; intenciones de borrador se conservan.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 9 · Rama offline, seguridad y presentación final

- [ ] **T25:** Implementar emisión offline si T03 la aprobó, o fijar/verificar su rechazo contractual.
- [ ] **T26:** Completar pruebas de concurrencia, aislamiento, revocación y respuestas perdidas.
- [ ] **T27:** Completar pruebas visuales, paginación y fallos/recuperación de artefactos.

#### C09 · Seguridad y renderizado demostrados localmente

- [ ] Numeración, emisión/revocación, sustitución/anulación y concesiones pasan carreras reales.
- [ ] Todos los tamaños/contenidos ficticios renderizan sin truncado ni fuga en logs/journal.
- [ ] Revisión y aceptación expresa del usuario.

### Fase 10 · Contratos y cierre

- [ ] **T28:** Generar/verificar contratos, ejemplos y documentación real.
- [ ] **T29:** Ejecutar cierre integral y registrar evidencia/límites.

#### C10 · Documentos clínicos listos para revisión final

- [ ] Suite, probes, migraciones, contratos, PDF y build pasan sobre el entregable.
- [ ] El flujo borrador→emisión→PDF→firma impresa→paciente/QR→sustitución funciona con datos ficticios.
- [ ] Revisión y aceptación expresa del usuario antes de uso real.

## 7. Riesgos y mitigación

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Se confunde emisión con firma física/validez legal | Alto | T01 jurídico, lenguaje explícito y línea en blanco; uso real bloqueado hasta revisión |
| Dos emisiones repiten número o contenido mezclado | Alto | Secuencia/transacción, versión esperada y carreras PostgreSQL |
| PDF fallido provoca segunda emisión | Alto | Estados separados y reintento del mismo artefacto/documento |
| Plantilla trunca posología o inventa indicaciones | Alto | Datos tipados, paginación y revisión visual de PDF ficticio |
| QR/enlace filtra contenido clínico | Alto | Proyecciones separadas, concesión read/download y pruebas de objeto ajeno |
| Owner/asistente emite sin ser profesional a cargo | Alto | Atributos profesionales en T01/T15 y pruebas negativas |
| Cambios de perfil reescriben historia | Alto | Snapshots inmutables y prueba de edición posterior |
| Dependencia PDF no soportada | Medio | T16 docs-first, versión oficial, build/lockfile y revisión previa |
| Emisión offline excede diseño de numeración | Alto | Decisión T03, rama T25 explícita y replanificar antes de crecer la tarea |

## 8. Preguntas abiertas durante la planificación

T01–T04 asignan todas las `CD-Oxx`. Ninguna tarea dependiente comienza antes de su decisión/checkpoint. Si la rama offline elegida exige otro mecanismo físico/contractual que no cabe en T25, se detiene ese alcance para replanificación sin cambiar la solución en silencio.

## 9. Evidencia y límites

PostgreSQL Test acredita integridad/carreras; los PDF se inspeccionan con datos ficticios. Nada de ello acredita validez jurídica, firma manuscrita, impresión física, farmacia/laboratorio, Rust/Hub, datos reales o producción. Cada tarea registra resultados reales en `todo.md`; no hay aceptaciones automáticas.
