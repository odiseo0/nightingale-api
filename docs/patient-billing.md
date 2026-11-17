# Especificación del componente de facturación administrativa de pacientes

**Versión:** 0.1\
**Fecha:** 2026-11-17\
**Estado:** Aprobada por el usuario el 2026-11-17 como referencia funcional. No autoriza implementación, migraciones, almacenamiento de archivos ni cambios de contrato.\
**Ámbito:** precios, cargos, reportes de pago, aprobación administrativa y analítica de las cuentas de Nightingale.\
**Documentos relacionados:** [autorización RBAC/ABAC](authorization-rbac-abac.md), [suscripciones](account-subscriptions.md), [registro clínico](patient-clinical-record.md), [decisiones](decisions.md), [arquitectura](architecture.md), [diseño de acceso](access-design.md), [contrato HTTP v1](api-v1.md) y [esquema físico](database-schema.md).

## 1. Propósito

Este documento define la parte administrativa de facturación entre una consulta y sus pacientes. Nightingale registra precios, cargos, documentos y pagos verificados, pero **no mueve dinero ni procesa transacciones**.

El recorrido principal es:

1. La consulta define precios para sus servicios.
2. Una persona autorizada crea un cargo para un paciente, normalmente desde una cita o atención.
3. El paciente consulta el cargo permitido, realiza el pago fuera de Nightingale y envía una captura con sus datos.
4. El reporte queda pendiente.
5. Una asistente autorizada revisa la evidencia, anota los datos verificados y aprueba o rechaza.
6. La aprobación crea un pago administrativo y actualiza el saldo una sola vez.
7. Las analíticas distinguen cargado, cobrado, pendiente de revisión y saldo.

### 1.1 Resultado esperado

La consulta debe poder conocer cuánto ha cargado, cuánto ha cobrado mediante pagos aprobados y qué saldos conserva. El paciente solo debe ver los cargos y reportes alcanzados por su acceso limitado. La asistente debe disponer de la información financiera mínima para revisar, sin recibir acceso clínico por esa función.

## 2. Decisiones confirmadas en el encargo

| ID | Decisión | Consecuencia |
|---|---|---|
| `BI-D01` | Nightingale no maneja los pagos | No hay pasarela, custodia de fondos, cargos automáticos ni integración bancaria |
| `BI-D02` | El componente es administrativo | Registra información financiera y documentos; no pretende ser contabilidad |
| `BI-D03` | Se incluyen precios para consultas y documentos de pago | El catálogo aporta precios y los cargos conservan su propia instantánea |
| `BI-D04` | El paciente reporta su pago y envía una captura | El reporte del paciente es online y contiene evidencia privada |
| `BI-D05` | La asistente valida, anota los datos y aprueba | Aprobar es una acción de personal autorizada, separada de presentar el reporte |
| `BI-D06` | El componente entrega analíticas de facturación | Debe definir importes, fechas, monedas y estados incluidos en cada indicador |
| `BI-D07` | Es independiente de las suscripciones de Nightingale | Un paciente paga a la consulta; una cuenta paga su plan a Nightingale |

La moneda inicial de los cargos, campos exactos de referencia, permisos iniciales de asistentes y reglas para pagos parciales/excedentes quedan identificados como decisiones pendientes.

## 3. Alcance y exclusiones

### 3.1 Incluye

- Precio base del servicio y posible precio de oferta por cuenta.
- Cargos por paciente, cita, atención o servicio.
- Instantáneas de descripción, precio y moneda.
- Reportes de pago presentados por pacientes.
- Capturas privadas y comprobantes administrativos.
- Revisión por personal autorizado.
- Pagos aprobados, saldos e historia.
- Pagos parciales como propuesta acotada.
- Anulación y correcciones trazadas.
- Permisos financieros separados de los clínicos.
- Acceso limitado del paciente desde el futuro Hub.
- Sincronización mínima, offline, auditoría y analítica.

### 3.2 Excluye

- Procesamiento de tarjetas, transferencias o pago móvil.
- Verificación bancaria automática.
- Factura fiscal, numeración fiscal, impuestos o contabilidad general.
- Seguros, reclamos, coberturas o autorizaciones de pagadores.
- Nómina, comisiones o liquidaciones del profesional.
- Reembolsos de dinero; solo una futura constancia administrativa si se aprueba.
- Descuentos, promociones, planes de financiamiento o intereses sin alcance propio.
- Suscripciones que la cuenta paga a Nightingale.
- Firma digital o validez fiscal de un comprobante generado.
- Tablas, rutas, formatos de archivo o proveedor de almacenamiento aprobados por este documento.

[database-schema.md](database-schema.md) conserva la única fuente física. [api-v1.md](api-v1.md) conserva el contrato actual. Las entidades y acciones siguientes son conceptuales hasta su incorporación expresa a esas fuentes.

## 4. Relación con el estado actual

### 4.1 Servicios y ofertas

Actualmente `services` conserva nombre, duración base, profesional propietario, estado y versión. `professional_services` indica dónde se ofrece y permite ajustar duración por cuenta. No existen precios.

Las citas ya conservan instantáneas de:

- Nombre del servicio.
- Duración ofrecida.
- Profesional.
- Lugar y zona.

Ese patrón evita que cambios de catálogo reescriban citas anteriores. Facturación debe aplicar el mismo principio a descripción, importe y moneda del cargo.

### 4.2 Citas y atenciones

- Una cita es un compromiso programado.
- Una atención afirma que ocurrió y puede existir sin cita.
- Una cita admite varias atenciones.
- Completar, cancelar o marcar ausencia no crea por sí solo una atención.

Por tanto, facturación no debe inferir automáticamente un cargo del estado de cita. El personal decide cuándo crearlo y qué importe cobrar.

### 4.3 Componente propietario

Se propone un componente `billing` que posee cargos, reportes, pagos, evidencias financieras y proyecciones de saldo.

| Componente | Relación permitida |
|---|---|
| `services` | Aporta catálogo y precios base/oferta mediante casos y tipos |
| `patients` | Comprueba ficha y ámbito cuenta/paciente |
| `appointments` | Comprueba cita y sus instantáneas, sin recibir pagos en su historial |
| `encounters` | Comprueba atención y vínculo con paciente, sin convertir notas en datos financieros |
| `accounts` | Aporta contexto, rol y permisos financieros |
| `sync` | Coordina recibo, efecto, auditoría y proyecciones autorizadas |
| `analytics` | Consume hechos autorizados para indicadores, sin reabrir datos clínicos |

`billing` no importa repositorios ajenos ni escribe en citas o atenciones.

## 5. Conceptos y separación

| Concepto | Definición |
|---|---|
| **Precio de catálogo** | Valor habitual de un servicio, sin afirmar que ya se cobró. |
| **Precio efectivo** | Precio base o ajuste de oferta aplicable a una cuenta. |
| **Cargo** | Importe que la consulta decide cobrar a un paciente. |
| **Reporte de pago** | Declaración del paciente sobre un pago realizado fuera del sistema. |
| **Evidencia** | Captura y datos que apoyan la revisión. |
| **Pago aprobado** | Constancia administrativa aceptada por personal autorizado. |
| **Saldo** | Cargo vigente menos pagos aprobados y aplicados, con regla para ajustes. |
| **Comprobante** | Representación no fiscal de un pago aprobado. |
| **Dato declarado** | Valor enviado por el paciente. |
| **Dato verificado** | Valor asentado por quien revisa. |
| **Acceso financiero** | Permiso del personal sobre datos financieros, independiente del clínico. |

Una captura no es un pago aprobado. Un reporte pendiente no reduce el saldo. Un pago aprobado no demuestra una transacción bancaria verificada por integración; registra la decisión humana de la consulta.

## 6. Actores

### 6.1 Propietario

Puede administrar precios y todas las funciones financieras de su cuenta, dentro de las reglas de objeto. Configura los permisos de asistentes cuando se defina esa operación.

### 6.2 Asistente autorizado

Puede recibir acciones financieras concretas:

- Consultar cargos y saldos.
- Crear o corregir borradores.
- Emitir/cancelar cargos según permiso.
- Revisar reportes.
- Registrar datos verificados.
- Aprobar o rechazar pagos.
- Descargar evidencia necesaria.

No hereda acceso a notas, diagnósticos, mediciones o historias clínicas. Los permisos iniciales y la separación exacta de acciones se revisan en §15 y `BI-O05`.

### 6.3 Paciente

Con una concesión limitada y vigente puede:

- Consultar el cargo permitido y su saldo.
- Presentar un reporte con captura.
- Consultar el estado de sus propios reportes.
- Consultar el resultado de una revisión.
- Descargar un comprobante permitido, si se implementa.

No puede:

- Aprobar o rechazar.
- Modificar el importe del cargo.
- Ver otros cargos del paciente fuera de la concesión.
- Ver datos de otros pacientes.
- Consultar notas internas o revisiones de la asistente.
- Obtener acceso a toda la ficha clínica por conocer el enlace de pago.

### 6.4 Operador de Nightingale

No interviene en la aprobación ordinaria de pagos de pacientes. Su función de suscripciones no le concede acceso a cargos, evidencias o pacientes de una cuenta.

## 7. Precios de servicios

### 7.1 Precio base y oferta

Propuesta coherente con duración:

- `services` puede definir un precio base del profesional.
- `professional_services` puede definir un ajuste para esa cuenta.
- Si el ajuste es nulo, se usa el precio base.
- Si ambos son nulos, el servicio no tiene precio configurado y no se crea automáticamente un cargo con importe cero.
- Un importe cero explícito significa servicio gratuito; es distinto de “sin precio”.

La moneda forma parte del precio. No se mezclan precios base y ajuste con monedas distintas sin una regla de conversión aprobada.

### 7.2 Permisos

La modificación del precio base sigue la propiedad del catálogo profesional. El ajuste de oferta requiere autorización sobre esa oferta. Tener permiso para revisar pagos no concede cambiar precios.

### 7.3 Cambios de catálogo

Un cambio de precio:

- Aplica a cotizaciones/cargos nuevos.
- No altera cargos emitidos.
- No altera pagos aprobados.
- No cambia citas anteriores.
- Conserva versión e historia.

Desactivar un servicio no cancela cargos o saldos existentes.

### 7.4 Precio comunicado frente a cargo

Mostrar un precio en agenda o en el enlace es una estimación hasta que exista un cargo emitido. La reserva no fija el precio salvo que se decida expresamente otra regla.

El paciente debe poder distinguir:

- Precio informativo.
- Cargo emitido.
- Importe pendiente.
- Pago aprobado.

## 8. Cargos

### 8.1 Alcance mínimo

Para evitar construir una factura general anticipada, el primer modelo propuesto usa **un cargo por concepto**. Una consulta puede tener varios cargos independientes si necesita varios conceptos.

Cada cargo conserva conceptualmente:

- Cuenta y paciente.
- Cita opcional.
- Atención opcional.
- Servicio y profesional cuando correspondan.
- Descripción visible e instantánea del servicio.
- Importe y moneda.
- Origen del precio: catálogo, oferta o ajuste autorizado.
- Fecha de emisión y vencimiento opcional si se decide.
- Estado, versión, autor e historia.

No incluye impuestos, líneas fiscales, seguros o contabilidad.

### 8.2 Vínculos

El paciente es obligatorio. Cita y atención son opcionales para admitir:

- Cargo desde una cita.
- Cargo desde una atención sin cita.
- Cargo administrativo permitido sin forzar una cita ficticia.

Si ambos vínculos existen, deben pertenecer a la misma cuenta y paciente. Si la atención está vinculada a otra cita, se rechaza la combinación.

### 8.3 Creación explícita

Crear una cita, completarla o registrar una atención no crea un cargo automáticamente. La persona autorizada inicia el cargo y confirma descripción/importe.

El sistema puede proponer el precio efectivo del catálogo. Un ajuste manual queda identificado y requiere permiso; no modifica el catálogo.

### 8.4 Ciclo propuesto

| Estado | Significado |
|---|---|
| `draft` | Editable y todavía no presentado al paciente |
| `open` | Emitido y admite reportes/pagos |
| `cancelled` | Anulado administrativamente, conservando historia |

El estado de cobro se deriva por separado:

- Sin pagos.
- Parcialmente pagado.
- Pagado.
- Excedido, si se habilita esa situación.

Así se evita que `open`, `paid` y `cancelled` compitan en un solo campo.

### 8.5 Edición y anulación

- Un borrador puede corregirse con versión esperada.
- Un cargo abierto no cambia paciente, cuenta o identidad.
- Importe/descripción de un cargo abierto no se reescriben silenciosamente.
- Un cargo erróneo sin pagos puede cancelarse y, si hace falta, sustituirse por otro vinculado.
- Si ya tiene pagos, la corrección exige la política de `BI-O08`.
- Cancelar no borra reportes, evidencias o pagos.

Cancelar/reprogramar una cita no cancela automáticamente el cargo. La política de cobro por ausencia o cancelación es de producto y no se deduce.

## 9. Acceso del paciente desde el Hub

### 9.1 Ampliación de alcance

D11 solo contemplaba información y acciones de una cita. Esta especificación añade, para el diseño futuro:

- Consulta de un cargo relacionado con la cita.
- Presentación de un reporte de pago.
- Consulta del estado/resultado del reporte.
- Descarga de comprobante permitido.

No crea una cuenta general de paciente ni abre las rutas del personal. El micrositio público continúa sin datos privados.

### 9.2 Concesión limitada

La autorización debe comprobar:

- Cuenta, paciente y cita accesibles.
- Cargo relacionado con ese ámbito.
- Acción concreta de lectura o reporte.
- Vigencia y revocación del acceso.
- Versión/estado aplicables.

Conocer UUID de cargo, cita, paciente o reporte no basta.

### 9.3 Proyección mínima

El paciente recibe solo:

- Descripción del servicio/cargo.
- Importe, moneda y saldo.
- Fecha de emisión/vencimiento si aplica.
- Estado de revisión.
- Datos mínimos del pago aprobado.
- Identificadores necesarios para idempotencia.

No recibe notas de revisión, datos internos de la asistente, otros cargos o contenido clínico.

### 9.4 Cargos sin cita

El acceso desde una cita solo cubre cargos vinculados a ella. Un cargo sin cita necesita otra concesión explícita o gestión por el personal; no se expone por pertenecer al mismo paciente.

### 9.5 Revocación y acciones en curso

Revocar el enlace impide nuevas lecturas/reportes después del orden de revocación. Un reporte ya aceptado conserva su historia y puede ser revisado por el personal. La consulta posterior del resultado requiere un acceso todavía válido.

## 10. Reportes de pago del paciente

### 10.1 Datos declarados

El reporte puede incluir:

- Cargo al que se aplica.
- Fecha del pago.
- Importe y moneda.
- Método declarado.
- Referencia declarada o parcial.
- Nota breve.
- Captura del pago.
- Identidad de operación para reintentos.

Los campos obligatorios y la forma de referencia se cierran en `BI-O04`. No se solicitan números bancarios completos si no son necesarios.

### 10.2 Captura obligatoria en el recorrido del paciente

A diferencia de las suscripciones, el encargo describe que el paciente envía una captura. Por tanto, el reporte del paciente requiere evidencia gráfica válida.

Un futuro alta manual por personal puede tener otra evidencia, pero no cambia esta regla del recorrido del paciente.

### 10.3 Estados

| Estado | Significado |
|---|---|
| `pending` | Recibido, sin efecto sobre saldo |
| `approved` | Revisado y vinculado a un pago aprobado único |
| `rejected` | Revisado y rechazado con motivo |

El paciente no puede cambiar el estado. Presentar/repetir no aprueba.

### 10.4 Datos inmutables y nueva presentación

Después de presentar:

- Los datos declarados y la captura original se conservan.
- La asistente no los sobrescribe para hacerlos coincidir con la revisión.
- Una corrección antes de revisar, si se permite, crea versión/historia.
- Después de rechazo, el paciente crea una nueva presentación relacionada.
- Un reporte aprobado no se reabre.

### 10.5 Varios reportes

El sistema debe impedir que reintentos idempotentes creen varios reportes. Reportes realmente distintos pueden existir para pagos parciales o nuevas presentaciones, pero cada aprobación comprueba el saldo y los demás pagos aprobados.

Una coincidencia de importe/fecha/referencia puede advertirse a la asistente; no prueba duplicidad por sí sola.

## 11. Capturas y documentos privados

### 11.1 Carga segura

La captura:

- Se carga mediante acceso autorizado al cargo.
- Tiene tipos, tamaño y dimensiones máximas definidos antes del contrato.
- Se valida por extensión, tipo real y firma de archivo.
- Recibe nombre interno generado por API.
- Se guarda fuera del webroot y sin URL pública permanente.
- Queda vinculada a cuenta, paciente, cargo y reporte.
- No se registra en logs ni se incluye en sincronización general.

### 11.2 Descarga

Solo pueden descargarla:

- Personal con permiso financiero y acción de revisión sobre esa cuenta.
- Paciente con concesión vigente para su propio reporte, si se decide ofrecer esa lectura.

La API vuelve a autorizar antes de entregar bytes o una URL temporal. Conocer la clave de almacenamiento no concede acceso.

### 11.3 Comprobante administrativo

Después de aprobar se puede generar un comprobante no fiscal con:

- Identificador del pago.
- Paciente y consulta en la medida permitida.
- Cargo y concepto.
- Importe/moneda verificados.
- Fecha de pago y aprobación.
- Método/referencia parcial permitida.
- Estado y versión.

Debe identificarse como constancia administrativa, no factura fiscal. Su contenido conserva instantánea; cambios posteriores de nombres no lo reescriben.

### 11.4 Retención

Las capturas, comprobantes, copias y eliminación requieren política antes de datos reales. Rechazar un reporte no borra inmediatamente la evidencia. Vencer una suscripción de Nightingale tampoco borra estos documentos.

## 12. Revisión por la asistente

### 12.1 Secuencia

1. Autenticar y comprobar permiso financiero de revisión.
2. Obtener reporte, cuenta, paciente y cargo en el mismo ámbito.
3. Consultar la evidencia fuera de la transacción larga cuando sea necesario.
4. Registrar datos verificados por separado.
5. Recoordinar reporte, cargo y saldo antes del efecto.
6. Aprobar o rechazar con versión esperada.
7. En aprobación, confirmar juntos pago, aplicación al cargo, historia, auditoría, recibo y cambios.
8. Entregar después del commit solo la proyección autorizada.

### 12.2 Datos verificados

Pueden incluir:

- Importe y moneda aceptados.
- Fecha de pago aceptada.
- Método.
- Referencia parcial o dato administrativo permitido.
- Observación interna mínima.
- Motivo de rechazo.
- Persona que revisó e instante del servidor.

El dato verificado no reemplaza el declarado. La observación interna no se proyecta automáticamente al paciente.

### 12.3 Aprobación humana

La aprobación significa que una persona autorizada aceptó la evidencia para el registro administrativo. No afirma:

- Confirmación bancaria automática.
- Titularidad de la cuenta emisora.
- Ausencia de fraude.
- Recepción de fondos por Nightingale.

### 12.4 Rechazo

Rechazar:

- No crea pago.
- No cambia saldo.
- Conserva evidencia y motivo.
- Permite nueva presentación.
- No cancela el cargo ni la cita.

## 13. Pagos aprobados y saldos

### 13.1 Pago administrativo

Cada pago conserva:

- Cuenta, paciente y cargo.
- Reporte de origen cuando exista.
- Importe/moneda verificados.
- Fecha declarada/verificada y fecha de aprobación.
- Método y referencia permitida.
- Actor que aprobó.
- Estado y versión.
- Historia de anulación/corrección.

Un reporte aprobado genera como máximo un pago ordinario.

### 13.2 Pagos parciales

Como propuesta, se admiten varios pagos aprobados sobre un cargo mientras la suma no supere el total:

```text
saldo = max(totalDelCargo - suma(pagosVigentesAplicados), 0)
```

El estado es:

- `unpaid`: suma vigente = 0.
- `partially_paid`: 0 < suma vigente < total.
- `paid`: suma vigente = total.

Los cálculos usan decimal exacto y una sola moneda por cargo.

### 13.3 Excedentes

Un pago que supera el saldo no genera crédito ni se aplica a otro cargo automáticamente. La asistente debe rechazarlo, ajustar la revisión conforme a una política aprobada o seguir el procedimiento de `BI-O06`.

No se permite que dos aprobaciones simultáneas superen el total por leer el mismo saldo anterior.

### 13.4 Pagos directos del personal

El registro de efectivo u otro pago recibido directamente por la consulta puede ser útil, pero no fue descrito como recorrido principal. Se propone un origen `staff_entry` separado, con permiso y evidencia propios.

Su inclusión inicial y obligaciones quedan en `BI-O07`; no se simula un reporte de paciente para registrarlo.

### 13.5 Anulación de pago

Una corrección no borra el pago:

- Se registra anulación con motivo, actor e instante.
- El pago deja de sumar al saldo vigente.
- Reporte y evidencia permanecen.
- El comprobante anterior muestra su estado posterior o conserva una historia consultable.
- No se afirma devolución de dinero.

Anular un pago requiere una acción distinta de aprobarlo.

## 14. Moneda y cálculos

### 14.1 Exactitud

Los importes usan decimal exacto, nunca punto flotante binario. Cada valor incluye moneda ISO 4217. No se aceptan NaN, infinito, negativos para cargos/pagos ordinarios ni cadenas ambiguas con formato regional.

### 14.2 Moneda del cargo

Un cargo y sus pagos aplicados comparten moneda. No se resta USD de VES. Si se admite pagar en otra moneda, debe existir una conversión explícita antes de aplicar el pago.

### 14.3 USD/VES y BCV

Las suscripciones ya usan USD con tasa BCV, pero esa decisión no se extiende automáticamente a pacientes.

`BI-O01` debe fijar:

- Monedas de catálogo/cargo.
- Si se admiten cargos USD pagados en VES.
- Fecha y fuente de tasa.
- Redondeo.
- Datos históricos de conversión.

Si se adopta BCV, el cargo/pago conserva importe USD, tasa, fecha/fuente, equivalente VES y redondeo, sin revalorizar después. Puede reutilizar el patrón de [account-subscriptions.md](account-subscriptions.md), pero mantiene su propia configuración e historia.

### 14.4 Totales

Las analíticas no suman monedas distintas en un único número. Todo total declara moneda y, si existe conversión, tasa/fecha del cálculo.

## 15. Autorización financiera

### 15.1 Acciones separadas

El catálogo de destino debe distinguir al menos:

| Acción conceptual | Permiso necesario |
|---|---|
| Consultar cargos/saldos | Lectura financiera |
| Crear/editar borradores | Escritura de cargos |
| Emitir/cancelar cargo | Administración de cargos |
| Consultar reportes/evidencias | Lectura de revisión |
| Aprobar/rechazar reporte | Revisión de pagos |
| Anular pago | Corrección financiera |
| Modificar precios | Permiso propio de catálogo/oferta |
| Consultar analítica | Lectura financiera con alcance de indicadores |

No se usa un único permiso clínico `read_write` para abrir todas estas acciones.

### 15.2 Propietario y asistentes

- El propietario conserva acceso financiero completo en su cuenta.
- La asistente que revisa necesita la acción explícita de revisión.
- Otros asistentes pueden tener solo lectura o ningún acceso.
- Los valores iniciales para asistentes existentes/nuevos se deciden en `BI-O05`.
- Cambiar permisos sigue siendo online, versionado, auditado e invalida capturas/cursores del alcance afectado.

### 15.3 Objeto y mínimo necesario

Todo cargo/pago/reporte pertenece a una cuenta. Las referencias de paciente/cita/atención se validan en esa cuenta. Un objeto ajeno devuelve la misma ausencia que uno inexistente.

Quien solo revisa pagos recibe datos administrativos mínimos del paciente y del servicio; no recibe contenido clínico.

### 15.4 Resultados y documentos

La autorización precede a:

- Detalles y listas.
- Totales y saldos.
- Resultados idempotentes.
- Evidencia y comprobantes.
- Analítica.
- Capturas y deltas financieros.

Una revocación impide nuevas lecturas, pero no promete borrar copias ya obtenidas.

## 16. Sincronización y offline

### 16.1 Audiencia financiera

Se propone una audiencia financiera cerrada, separada de `members`, `owner` y audiencias clínicas. Solo los miembros con permiso correspondiente reciben cargos/pagos en su alcance.

Los datos mínimos para interfaz pueden distinguirse de la revisión completa. Las capturas no viajan en snapshots/deltas ordinarios.

### 16.2 Filtrado

- Autorización antes de contar y paginar.
- Grupos invisibles permiten avanzar sin cuerpos.
- Cambiar permiso financiero invalida capturas/cursores afectados.
- Una ficha clínica legible no implica cargo legible.
- Un cargo legible no implica atención clínica legible.

### 16.3 Operaciones online

Son online como mínimo:

- Presentación del reporte del paciente.
- Carga/descarga de evidencia.
- Aprobación/rechazo.
- Anulación de pagos.
- Cambios de permisos.

La aprobación necesita estado compartido actual para impedir duplicados y exceso de saldo.

### 16.4 Trabajo local

El escritorio puede mostrar la última proyección autorizada y preparar borradores si se decide. La copia local no prueba saldo actual ni permiso vigente.

Si se permite crear cargos offline:

- Se envían como operaciones tipadas.
- API revalida precio, objeto, permiso y versión.
- Un rechazo conserva la intención local.
- No se marca como pagado por una captura local sin aprobación remota.

La política concreta de borradores/pagos directos offline queda en `BI-O10`.

## 17. Modelo conceptual de datos

Sin definir tablas físicas:

| Entidad conceptual | Responsabilidad |
|---|---|
| `service_prices` o campos versionados equivalentes | Precio base del profesional |
| `service_offer_prices` | Ajuste por cuenta/oferta |
| `patient_charges` | Cargo, instantáneas, estado y versión |
| `charge_histories` | Cambios, emisión, cancelación y correcciones |
| `patient_payment_reports` | Declaración, estado, vínculo y versión |
| `payment_report_evidence` | Referencia privada a captura |
| `billing_reviews` | Datos verificados, revisor y decisión |
| `patient_payments` | Pago aprobado, importe y estado |
| `payment_applications` | Aplicación de un pago a un cargo si se necesita separarla |
| `payment_receipts` | Instantánea del comprobante no fiscal |

Reglas conceptuales:

- Ninguna fila cruza cuentas.
- Paciente/cita/atención/cargo son coherentes.
- Un reporte aprobado produce como máximo un pago ordinario.
- Los pagos aplicados no superan el cargo salvo política de excedente.
- Los importes usan decimal exacto y moneda.
- Las historias son conservables y no se borran al cancelar.
- La evidencia no es una proyección general de sincronización.
- El precio del cargo no depende del valor actual del catálogo.

El diseño físico deberá fijar claves, restricciones e índices en [database-schema.md](database-schema.md) durante su propia revisión.

## 18. Casos de uso y contratos futuros

### 18.1 Personal

- Configurar precio base/oferta.
- Consultar precio efectivo.
- Crear/editar borrador de cargo.
- Emitir, consultar y cancelar cargo.
- Consultar cargos/saldos por paciente y filtros.
- Consultar reportes pendientes.
- Descargar evidencia autorizada.
- Aprobar/rechazar reporte.
- Registrar pago directo si se aprueba.
- Anular pago con motivo.
- Consultar comprobante e historia.
- Consultar analítica autorizada.

### 18.2 Paciente

- Consultar cargo de su cita.
- Presentar reporte con captura.
- Recuperar resultado tras respuesta perdida.
- Consultar reportes/resultados permitidos.
- Descargar comprobante aprobado permitido.

### 18.3 Interno

- Resolver precio efectivo sin importar repositorios ajenos.
- Comprobar pertenencia y relaciones.
- Calcular saldo con pagos vigentes.
- Proyectar cambios por audiencia financiera.
- Emitir hechos mínimos para analítica.

### 18.4 Contratos

Las escrituras usan identidad de operación, versión esperada e idempotencia. Las lecturas usan autorización y filtros antes de total/página. Las formas HTTP y nombres de acciones no se fijan aquí.

## 19. Analítica de facturación

### 19.1 Indicadores básicos

| Indicador | Definición |
|---|---|
| Total cargado | Cargos emitidos no cancelados en el periodo/criterio elegido |
| Total cobrado | Pagos aprobados y vigentes según fecha de referencia documentada |
| Saldo pendiente | Cargos vigentes menos pagos vigentes aplicados |
| Pendiente de revisión | Cantidad de reportes `pending`; no cuenta como cobrado |
| Pagos parciales | Cargos con suma vigente mayor que cero y menor que el total |
| Cargos pagados | Cargos cuyo saldo vigente es cero |
| Anulaciones | Cargos/pagos anulados, mostrados aparte |

### 19.2 Dimensiones

- Cuenta.
- Periodo y zona local.
- Profesional.
- Servicio.
- Paciente, solo para usuarios autorizados.
- Método de pago verificado.
- Moneda.
- Estado de cargo/revisión.

### 19.3 Fechas

No mezclar sin etiqueta:

- Fecha de emisión del cargo.
- Fecha del servicio/cita/atención.
- Fecha de pago verificada.
- Fecha de aprobación.

Cada informe declara cuál usa. “Cobrado en noviembre” puede significar pagos fechados o aprobados en noviembre; el contrato debe escoger y mostrar una.

### 19.4 Moneda e historia

- Totales separados por moneda.
- VES histórico sin revalorizar a tasa actual.
- Pagos anulados excluidos del vigente pero conservados en historia.
- Reportes pendientes no incluidos en cobrado.
- Cargos cancelados no incluidos como deuda vigente.

### 19.5 Arquitectura

Consultas operativas pequeñas pueden usar proyecciones autorizadas y acotadas. La analítica histórica pesada pertenece al componente `analytics` y su PostgreSQL separado. Ninguna necesidad de gráficos permite consultas costosas sin límite sobre la transacción operativa.

## 20. Auditoría, privacidad y seguridad

### 20.1 Evidencia mínima

Registrar:

- Cuenta y tipo/ID del objeto.
- Actor/dispositivo o concesión del paciente.
- Acción, resultado, versión y correlación.
- Instante del servidor.
- Revisor y motivo de decisión/corrección.
- Origen del pago y relación cargo/reporte.

### 20.2 No registrar en logs

- Captura o bytes.
- URL temporal/clave de almacenamiento.
- Números bancarios completos.
- Tokens o secretos de enlace.
- Payload financiero completo para depuración.
- Contenido clínico innecesario.

### 20.3 Acceso a lecturas

Las lecturas financieras sensibles dejan evidencia conforme a la política aprobada. Los errores y totales no revelan objetos ajenos. El paciente no recibe observaciones internas ni identidad completa del personal.

### 20.4 Retención

Antes de datos reales se define retención de cargos, pagos, reportes, evidencias, comprobantes, auditoría y copias. Cancelar una cita, rechazar un reporte o suspender una suscripción no equivale a eliminarlos.

## 21. Fallos, concurrencia y recuperación

| Situación | Resultado exigido |
|---|---|
| Respuesta perdida al presentar reporte | Recuperar mismo reporte sin duplicar captura/efecto |
| Respuesta perdida al aprobar | Recuperar mismo pago; no aprobar dos veces |
| Dos asistentes aprueban a la vez | Un solo efecto y revisor real |
| Dos pagos parciales usan el último saldo | Coordinación impide exceder el cargo |
| Cambio/cancelación de cargo frente a aprobación | Un orden verificable; nunca saldo negativo silencioso |
| Cambio de precio durante creación | Cargo usa una versión coherente o solicita revisión |
| Captura cargada y reporte falla | Sin efecto financiero; archivo sujeto a limpieza/retención |
| Revocación de permiso durante revisión | Orden de revocación/aceptación verificable |
| Reporte aceptado y aviso perdido | Pago persiste y se recupera por sincronización/consulta autorizada |
| Cita cancelada después del reporte | Historia financiera conservada; no borrado automático |
| Pago aprobado con moneda distinta | Rechazo salvo conversión explícita aprobada |

## 22. Criterios verificables

Estos criterios son requisitos futuros, no pruebas ejecutadas por esta entrega.

### 22.1 Precios y cargos

- Precio base/oferta se resuelve correctamente, incluido nulo frente a cero.
- Cambiar catálogo no altera cargos anteriores.
- Una cita/atención no crea cargo sin acción explícita.
- Cita, atención, paciente y servicio no cruzan cuentas.
- Borrador no aparece al paciente.
- Cancelar conserva historia y no borra pagos.

### 22.2 Reportes y evidencia

- Presentar deja saldo sin cambios.
- El paciente no puede aprobar.
- La captura es obligatoria en el recorrido del paciente.
- Datos declarados y verificados permanecen separados.
- Rechazo no crea pago y permite nueva presentación.
- Archivo valida tipo real/tamaño y requiere autorización de descarga.

### 22.3 Pagos y saldos

- Aprobación crea un pago una vez.
- Pagos parciales calculan estados correctamente.
- Aprobaciones concurrentes no exceden el cargo.
- Excedente no se aplica a otro cargo automáticamente.
- Anulación deja de sumar al saldo sin borrar historia.
- No se mezclan monedas.

### 22.4 Autorización

- Asistente sin permiso financiero no lee cargos por tener acceso clínico.
- Revisar pagos no abre notas o diagnósticos.
- Paciente solo accede al cargo/reporte de su concesión.
- Objetos ajenos producen ausencia uniforme.
- Resultados, totales, evidencias y deltas se reautorizan.

### 22.5 Analítica

- Pendiente no cuenta como cobrado.
- Anulado no suma al vigente.
- Cada indicador declara fecha y moneda.
- Los totales no mezclan USD/VES sin conversión.
- Cambios posteriores no revalorizan historia.

### 22.6 Concurrencia y consumidores

- PostgreSQL real acredita carreras de aprobación, saldo y revocación.
- La respuesta perdida recupera el mismo efecto.
- El escritorio no interpreta una proyección local como saldo autoritativo.
- Las pruebas de API no acreditan la experiencia Rust o Hub.

## 23. Criterios para aceptar esta especificación

- Refleja `BI-D01`–`BI-D07` sin introducir procesamiento de dinero.
- Distingue precio, cargo, reporte, pago, evidencia y comprobante.
- Conserva instantáneas, versiones, historia e idempotencia.
- Separa permisos financieros y clínicos.
- Amplía el Hub solo con concesiones limitadas, sin cuenta general de paciente.
- Define saldos y analítica por fecha/moneda/estado.
- Protege capturas y no las sincroniza indiscriminadamente.
- No presenta como decididas monedas, permisos iniciales, excedentes o retenciones pendientes.

## 24. Decisiones pendientes

| ID | Decisión | Momento necesario |
|---|---|---|
| `BI-O01` | Monedas de precios/cargos y adopción de USD/BCV para pacientes | Antes de contratos monetarios |
| `BI-O02` | Confirmar precio base/oferta y si el paciente ve estimación antes del cargo | Antes de catálogo/Hub |
| `BI-O03` | Permitir cargos sin cita/atención y ajustes manuales de importe | Antes de creación de cargos |
| `BI-O04` | Datos obligatorios del reporte y forma de referencia bancaria | Antes del formulario del paciente |
| `BI-O05` | Permisos iniciales y granularidad para asistentes | Antes de revisión por personal |
| `BI-O06` | Pagos parciales, excedentes y aplicación a varios cargos | Antes de aprobar esos casos |
| `BI-O07` | Registro directo de efectivo/pagos por el personal | Antes de `staff_entry` |
| `BI-O08` | Corrección de cargos con pagos, anulaciones y constancia de reembolso | Antes de correcciones financieras |
| `BI-O09` | Vigencia/revocación del enlace y efecto de cancelar/reprogramar cita | Antes del contrato del Hub |
| `BI-O10` | Qué borradores o pagos directos pueden prepararse offline | Antes de sincronización financiera |
| `BI-O11` | Formatos/tamaños de captura, retención, copias y eliminación | Antes de datos reales |
| `BI-O12` | Indicadores/fechas exactos del primer panel | Antes del contrato de analítica |

Estas preguntas no impiden revisar la base. Bloquean solo las funciones que dependan de ellas.

## 25. Referencias

- [HL7 FHIR R5 ChargeItem](https://hl7.org/fhir/R5/chargeitem.html): separa el cargo administrativo asociado a una prestación de la transacción financiera. Se usa como referencia conceptual, no como compromiso FHIR.
- [HL7 FHIR R5 Invoice](https://hl7.org/fhir/R5/invoice.html): muestra la agrupación posterior de cargos para paciente/pagador; este componente no adopta todavía una factura general.
- [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html): códigos de moneda.
- [PostgreSQL 18, tipos numéricos](https://www.postgresql.org/docs/18/datatype-numeric.html): `numeric`/`decimal` para exactitud monetaria.
- [PostgreSQL 18, bloqueo explícito](https://www.postgresql.org/docs/18/explicit-locking.html): coordinación de saldo y aprobaciones, con pruebas propias.
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html): validación de archivos, límites, autorización y almacenamiento privado.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): mínimo privilegio y autorización en cada solicitud.
- [Autorización RBAC/ABAC](authorization-rbac-abac.md): permisos personales, acceso de paciente y separación de actores.
- [Suscripciones](account-subscriptions.md): patrón USD/BCV y revisión manual, sin mezclar ambos dominios.
- [D11 · Hub y servidor en API](decisions.md#d11--interfaz-del-hub-y-servidor-en-nightingale-api): acceso limitado original de citas.
- [D14 · Autorización RBAC/ABAC](decisions.md#d14--especificación-separada-de-autorización-rbacabac): modelo aprobado.

## 26. Resultado de esta entrega

Esta especificación define una facturación administrativa pequeña y trazable: no procesa dinero, no emite factura fiscal y no convierte una captura en pago por sí sola. Separa el cargo del reporte y del pago aprobado, conserva evidencia y saldo, y limita el acceso del paciente y del personal.

No declara implementados precios, pagos, archivos, analítica o endpoints del Hub. Las decisiones abiertas deben cerrarse antes de convertir las partes afectadas en esquema físico o contrato HTTP.
