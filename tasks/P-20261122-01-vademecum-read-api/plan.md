# P-20261122-01-vademecum-read-api: consulta del vademecum venezolano

**Estado:** Completed. **Creado:** 2026-11-22. **Actualizado:** 2026-11-22. **Lista de tareas:** [todo.md](todo.md).

## 1. Contexto y resultado

Nightingale necesita un vademecum global de solo lectura para profesionales médicos y asistentes autenticados. El componente organizará en PostgreSQL los productos vigentes del registro venezolano y sus monografías investigadas, y expondrá lecturas estructuradas mediante FastAPI y Pydantic para que el escritorio las consulte en línea.

La fuente autoritativa de importación es [vademecum_venezuela_2026-11-03.json](../../vademecum/vademecum_venezuela_2026-11-03.json). [monograph.schema.json](../../vademecum/monograph.schema.json) define la forma de las monografías. Los archivos individuales de `vademecum/monographs/` son copias de apoyo; `data.js` no es una fuente de importación.

La primera versión comprende:

- Los 6.264 productos vigentes, incluidos los no resueltos o sin monografía, y las 868 monografías, incluidas combinaciones y monografías sin productos vinculados.
- Búsqueda por nombres de productos y monografías, registro sanitario, texto de principio activo, alias, identificadores canónicos de ingredientes y ATC.
- Solo productos vigentes y monografías. Quedan fuera el histórico de 2017 y el dataset suplementario independiente.
- Publicación del contenido pendiente de revisión con aviso visible, estado de revisión, fuentes, procedencia, fecha de corte y calidad del vínculo.
- Consultas en línea de solo lectura. Sin sincronización, capturas, almacenamiento offline, escrituras, flujo de revisión, acceso público o búsqueda en todo el texto clínico.

## 2. Precondiciones y límites

- Trabajo secuencial, una tarea a la vez y sin delegación. Cada checkpoint exige revisión expresa del usuario.
- La aprobación de este plan no acepta C01 ni habilita T03 antes de esa revisión.
- Conservar todos los cambios existentes, el plan de revisión cerrado y los archivos de `vademecum/`; no revertir trabajo ajeno.
- No modificar Rust, Hub, planes de suscripciones/facturación/documentos, operaciones de lote, sincronización o permisos clínicos existentes.
- No añadir dependencias, extensiones PostgreSQL, infraestructura de texto completo, editor, revisión manual mediante API o endpoints administrativos.
- No declarar integración con el escritorio, revisión profesional, despliegue o producción por completar pruebas locales.

## 3. Fuentes de verdad

- [Decisión D20](../../docs/decisions.md), que se añadirá en T01.
- [Contrato HTTP v1](../../docs/api-v1.md), [diseño de acceso](../../docs/access-design.md), [arquitectura](../../docs/architecture.md) y [esquema físico](../../docs/database-schema.md), actualizados en T02.
- [Esquema de monografía](../../vademecum/monograph.schema.json) y [dataset autoritativo](../../vademecum/vademecum_venezuela_2026-11-03.json).
- `src/api/accounts/application/accounts_cases.py`: autenticación de cuenta, pertenencia y dispositivo.
- `src/api/medications/`: separación frente a medicación declarada por paciente y estilo de lecturas.
- `src/core/db/`, `src/core/schema/` y `scripts/create_practice.py`: persistencia, paginación, resultados y proceso administrativo.
- `tests/test_authorization_structure.py`, `test-support/persistence/check.py` y `test-support/contracts/check.py`: controles estructurales y comprobación real.

## 4. Decisiones de arquitectura

- **Componente interno:** crear `src/api/vademecum/` dentro de la aplicación FastAPI existente, con domain/application/repository/infrastructure. No montar una segunda aplicación.
- **Datos globales, acceso por cuenta:** las rutas llevan `account_id` para reutilizar el contexto vigente; el contenido no se duplica por cuenta ni se filtra por paciente.
- **Acceso común del personal:** propietario profesional y asistente activo, con cuenta activa y dispositivo registrado activo. No se añade una sección clínica ni un permiso por paciente.
- **Persistencia híbrida:** tablas relacionales para releases, identidades, búsqueda y vínculos; documento JSONB para la monografía completa y estable, validado con modelos Pydantic al importar y al responder.
- **Releases atómicas:** cada archivo importado crea un release identificado por huella SHA-256. Solo uno está activo. El nuevo release se activa después de guardar todo su contenido en una transacción; repetir la misma huella no cambia datos.
- **Importación administrativa:** script pequeño con identidad administrativa separada, fuera del arranque del servidor. El rol runtime recibe solo SELECT.
- **Respuestas explícitas:** no serializar el producto fuente completo. Excluir `oficios`, identificadores de usuarios de la fuente, RIF y demás administración no seleccionada.
- **Búsqueda acotada:** texto normalizado en Python para mayúsculas y acentos, coincidencia literal escapada y alias de monografías vinculadas disponibles al buscar productos. No buscar en mecanismo, posología, seguridad u otro texto clínico.

## 5. Contrato previsto

### 5.1 Rutas

`A` equivale a `/v1/accounts/{account_id}`:

| Método | Ruta | Respuesta | Reglas |
|---|---|---|---|
| GET | `A/vademecum/products` | Página tipada de productos con contexto de catálogo | `q`, `monographId` opcional, `page`, `shows`; orden nombre/registro |
| GET | `A/vademecum/products/{registration_number}` | Producto tipado con contexto | Registro dentro del release activo; 404 si no existe |
| GET | `A/vademecum/monographs` | Página tipada de monografías con contexto | `q`, `page`, `shows`; orden nombre/ID |
| GET | `A/vademecum/monographs/{monograph_id}` | Monografía completa con contexto | Documento completo; 404 si no existe |

Todas exigen token API, pertenencia activa, cuenta activa y dispositivo activo en la cuenta. Un catálogo sin release activo devuelve 503 controlado, no una página vacía. Los listados conservan `items`/`total`, `page` desde 1 y `shows=100`, máximo 500.

Toda respuesta incluye contexto de catálogo con `schemaVersion`, `registryCutoffDate`, `medicalNotice` y `sourceSha256`. El producto expone campos seleccionados del registro, texto de principio activo, ingredientes canónicos, vínculos simples/de combinación, evidencia de referencia por producto, `ingredientLinkStatus` e `ingredientResolution`. La monografía conserva todas sus secciones, fuentes, procedencia y revisión. Las especialidades de referencia extranjeras no se presentan como registros venezolanos.

### 5.2 Modelo físico previsto

| Tabla | Propósito y regla principal |
|---|---|
| `vademecum_datasets` | Release inmutable, huella fuente única, contexto, importación y marca de activo; índice único parcial para un solo activo |
| `vademecum_products` | Producto vigente por release y registro; campos públicos seleccionados, referencia opcional y texto de búsqueda normalizado |
| `vademecum_product_ingredients` | Referencias canónicas por producto, sin inventar ingredientes o nombres para IDs no resueltos |
| `vademecum_monographs` | Identidad, nombre, ATC, texto de búsqueda y documento JSONB completo por release |
| `vademecum_product_monographs` | Vínculo producto/monografía del mismo release y marca de combinación |

Las FK compuestas conservan release y existencia. Los IDs textuales de monografía y los registros sanitarios conservan su forma fuente. Las tablas de relación no reciben UUID propio. No hay FK de ingredientes canónicos no resueltos a monografías ni una tabla de ingredientes derivada de datos que la fuente principal no contiene.

El importador valida todo el contenido antes de abrir la transacción de escritura. Ignora explícitamente las colecciones históricas y suplementarias conocidas; rechaza registros o monografías inválidos, IDs/registros duplicados, referencias a monografías ausentes y desacuerdo entre estadísticas y contenido. Inserta en lotes acotados sin commits parciales y activa al final. Los releases anteriores se conservan; no hay administración HTTP ni retención automática en esta versión.

## 6. Orden de dependencias

```text
Plan aprobado
  → T01/T02: decisión y diseño HTTP/acceso/físico
  → C01 aceptado
  → T03/T04: contratos Pydantic fuente y públicos
  → C02 aceptado
  → T05: modelos y migración
  → T06/T07: importador transaccional y comando
  → C03 aceptado
  → T08/T09: lecturas HTTP de productos
  → T10: lecturas HTTP de monografías
  → C04 aceptado
  → T11/T12: contratos generados, evidencia y cierre
  → C05 aceptado
```

No hay tareas paralelas. Cada tarea deja el árbol en estado revisable y registra evidencia real en `todo.md`.

## 7. Fases y tareas

### Fase 1 · Diseño ejecutable

- [x] **T01:** Registrar el plan y la decisión D20 con fuente, alcance y arquitectura.
- [x] **T02:** Publicar el diseño HTTP, acceso y modelo físico.

#### C01 · Diseño del vademecum

- [x] El mapeo fuente→público, rutas, tablas, releases, avisos y autorización están documentados para revisión.
- [x] `git diff --check` y enlaces locales focales de los documentos modificados pasan.
- [x] Revisión y aceptación expresa del usuario el 2026-11-22; T03 queda habilitada.

### Fase 2 · Contratos fuente y persistencia

- [x] **T03:** Implementar y validar todos los modelos Pydantic de monografías.
- [x] **T04:** Implementar modelos de catálogo, productos, consultas y respuestas.

#### C02 · Contrato de datos

- [x] Las 868 monografías validan y los productos conservan solo campos previstos.
- [x] Pruebas focales y `git diff --check` pasan; el fallo estructural ajeno documentado permanece.
- [x] Revisión y aceptación expresa del usuario el 2026-11-22; autorizó continuar hasta C05.

- [x] **T05:** Añadir modelos SQLAlchemy, migración reversible, permisos runtime y controles estructurales.
- [x] **T06:** Implementar importación validada, por lotes, idempotente y transaccional.
- [x] **T07:** Añadir el comando administrativo y su guía de operación.

#### C03 · Importación real aislada

- [x] Migración, importación completa, repetición, rollback y activación atómica pasan en PostgreSQL Test.
- [x] Conteos y relaciones representativas coinciden con la fuente; runtime no puede escribir.
- [x] El usuario revisó y aceptó C03 junto con el cierre el 2026-11-22.

### Fase 3 · API de solo lectura

- [x] **T08:** Implementar acceso, consultas y proyecciones de productos.
- [x] **T09:** Exponer rutas de productos y errores HTTP tipados.
- [x] **T10:** Implementar consultas y rutas de monografías completas.

#### C04 · Recorrido HTTP del personal

- [x] Probe real cubre cuatro rutas, ambos roles, rechazos, búsqueda, vínculos, avisos y contenido completo.
- [x] Las respuestas no contienen administración fuente ni colecciones fuera de alcance.
- [x] El usuario revisó y aceptó C04 junto con el cierre el 2026-11-22.

### Fase 4 · Contratos y cierre

- [x] **T11:** Conectar el router, exportar contratos y documentar consumo en línea.
- [x] **T12:** Ejecutar verificación integral y registrar evidencia y límites.

#### C05 · Cierre de la primera versión

- [x] Pruebas focales, probes, contratos, build y diff cubren el componente y pasan; la suite conserva el error ajeno documentado.
- [x] La evidencia distingue pruebas locales de consumidores, revisión profesional y producción.
- [x] El usuario revisó y aceptó C05 el 2026-11-22 después de corregir y comprobar el detalle de registros con `/`; plan Completed.

## 8. Comprobaciones previstas

Los módulos focales se crean en sus tareas; no se ejecutan antes de existir:

```bash
./.venv/Scripts/python.exe -m unittest tests.test_vademecum_monographs tests.test_vademecum_contracts tests.test_vademecum_import tests.test_vademecum_access tests.test_vademecum_products_api tests.test_vademecum_monographs_api -v
./.venv/Scripts/python.exe test-support/vademecum/check.py
./.venv/Scripts/python.exe -m unittest discover -s tests -v
./.venv/Scripts/python.exe -m scripts.export_contracts
./.venv/Scripts/python.exe -m scripts.export_contracts --check
uv build --offline
git diff --check
```

La integridad, importación, activación y autorización HTTP se comprueban con PostgreSQL Test y Keycloak Test aislados. SQLite no acredita esas reglas. El probe elimina sus bases temporales y no usa datos de pacientes.

## 9. Riesgos y mitigación

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Contenido pendiente o vínculos inferidos parecen aprobados | Alto | Contexto, aviso, revisión, fuentes, procedencia, estado y resolución explícitos en cada respuesta |
| Una actualización destruye el catálogo activo | Alto | Validación previa, una transacción, releases inmutables y activación al final |
| JSONB se convierte en contenido opaco | Medio | Esquema Pydantic completo, validación de entrada/salida y prueba de las 868 monografías |
| Alias o acentos ocultan resultados | Medio | Normalización común, búsqueda de monografías vinculadas y casos reales representativos |
| La proyección expone administración de la fuente | Alto | Modelos explícitos y pruebas de ausencia de claves crudas |
| El trabajo existente se pierde o se mezcla | Alto | Ediciones acotadas, revisión de diff y ninguna restauración de archivos ajenos |

## 10. Supuestos y límites

- El propietario de una cuenta representa al profesional registrado; los demás miembros activos son asistentes según el modelo vigente.
- Fuentes y procedencia dentro de cada monografía están incluidas; el dataset suplementario separado no.
- No se crean eventos de auditoría por lectura porque el catálogo no contiene datos privados de pacientes; la autenticación y pertenencia siguen siendo obligatorias.
- La lista actual registra un fallo previo no relacionado de `UsersStructureTests` y deriva de metadatos de contratos. Este plan no corrige trabajo de usuarios; cualquier fallo ajeno persistente se informa sin ocultarlo.
- Las fuentes externas y archivos originales no se descargan ni verifican en este plan; se conservan sus referencias y huellas presentes en la fuente autoritativa.

## 11. Preguntas abiertas

Ninguna para esta primera versión.
