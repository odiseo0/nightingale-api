# Especificación del componente de suscripciones de Nightingale

**Versión:** 0.1\
**Fecha:** 2026-11-17\
**Estado:** Aprobada por el usuario el 2026-11-17 como referencia funcional. No autoriza implementación, migraciones, almacenamiento de archivos ni cambios de contrato.\
**Ámbito:** relación comercial entre Nightingale y las cuentas que usan el producto en Venezuela.\
**Documentos relacionados:** [autorización RBAC/ABAC](authorization-rbac-abac.md), [especificación general](nightingale-api.md), [decisiones](decisions.md), [arquitectura](architecture.md), [diseño de acceso](access-design.md), [contrato HTTP v1](api-v1.md) y [esquema físico](database-schema.md).

## 1. Propósito

Este documento define cómo Nightingale administra planes, suscripciones, asientos, cotizaciones en USD con tasa BCV, reportes de pago y verificación manual.

El componente no procesa pagos ni se integra con una plataforma de Billing. El cliente realiza el pago fuera de Nightingale y después presenta:

- Una captura del pago y los últimos cuatro dígitos de la referencia; o
- Los datos del pago introducidos manualmente.

Un operador autorizado de Nightingale revisa la información y aprueba o rechaza el reporte. Solo la aprobación activa o extiende una suscripción.

### 1.1 Resultado esperado

Una cuenta debe poder conocer su plan, límite de asientos, vigencia y estado comercial. El propietario debe poder consultar el importe debido, reportar un pago y seguir su revisión. Nightingale debe poder verificar reportes sin obtener acceso a pacientes, historias clínicas o credenciales bancarias.

Cada aprobación debe dejar una historia completa: plan y precio aplicados, tasa BCV, importe declarado y verificado, periodo concedido, evidencia, operador y resultado. Repetir una aprobación no puede conceder dos veces el mismo periodo.

## 2. Decisiones confirmadas en el encargo

| ID | Decisión | Consecuencia |
|---|---|---|
| `SU-D01` | El ámbito inicial es Venezuela | Se usa zona civil `America/Caracas` y regulación/retención local queda por revisar antes de datos reales |
| `SU-D02` | Los precios comerciales se expresan en USD | El plan conserva importe y moneda; no se usa un número sin moneda |
| `SU-D03` | El cobro se calcula a la tasa BCV del día | Toda cotización y aprobación conserva tasa y fecha aplicables |
| `SU-D04` | No se utiliza Stripe ni otra plataforma de Billing | No hay cargos automáticos, webhooks de pasarela, tarjetas o conciliación con proveedor |
| `SU-D05` | El cliente reporta el pago y Nightingale lo verifica manualmente | Reportar no equivale a pagar ni a activar; la aprobación es una acción separada |
| `SU-D06` | La evidencia puede ser captura más últimos cuatro dígitos, o datos manuales | La captura no es obligatoria en todos los casos; el operador decide con la información disponible |
| `SU-D07` | Existen periodos de 30 días y de un año | Ambos tienen precio propio y generan periodos de servicio distintos |
| `SU-D08` | Todos los planes tienen las mismas capacidades, ilimitadas salvo asientos | No se crea una matriz de funciones por plan ni límites de pacientes, citas o documentos |
| `SU-D09` | Los planes son médico independiente, consultorio pequeño y centro médico | El plan distingue la oferta comercial y los asientos; no implementa por sí solo nuevas funciones operativas |

Precios y límites de asientos quedaron fijados en [D21](decisions.md#d21--planes-precios-y-asientos-de-suscripciones-t01) (2026-11-26). La duración de la gracia y las demás reglas abiertas no se inventan en esta especificación.

## 3. Alcance y exclusiones

### 3.1 Incluye

- Catálogo histórico de planes y precios.
- Suscripción actual e historia de periodos por cuenta.
- Límite y consumo de asientos.
- Cotización USD/VES con evidencia de tasa BCV.
- Reportes de pago con datos declarados y evidencia privada.
- Revisión, aprobación, rechazo y nueva presentación.
- Renovación, cambio de plan y cancelación.
- Actor operador de Nightingale.
- Separación entre acceso comercial y permisos personales.
- Comportamiento de sincronización y consumidores offline.
- Auditoría, seguridad, concurrencia y consultas administrativas.

### 3.2 Excluye

- Cobros automáticos o custodia de fondos.
- Datos completos de tarjetas, cuentas bancarias o claves.
- Facturación fiscal, contabilidad, impuestos o conciliación bancaria automática.
- Pagos de pacientes por consultas; pertenecen a la futura especificación de facturación.
- Prorrateo, créditos, reembolsos o notas de crédito sin decisión expresa.
- Pruebas gratuitas, promociones, cupones o comisiones.
- Integración automática con el BCV.
- Gestión interna de clínicas o varias sedes por contratar el plan correspondiente.
- Definición física de tablas, rutas, formatos de archivo o proveedor de almacenamiento.

[database-schema.md](database-schema.md) conserva la única fuente física. [api-v1.md](api-v1.md) conserva el contrato actual. Este documento usa entidades conceptuales sin presentarlas como tablas aprobadas.

## 4. Relación con el estado actual

La implementación vigente posee cuentas, pertenencias, profesionales, invitaciones y dispositivos. No posee planes, suscripciones, reportes de pago, cotizaciones BCV ni operador de plataforma.

`account_memberships` ya significa que una persona pertenece a una cuenta. Por ello:

- El componente nuevo se denomina **`subscriptions`**.
- Una suscripción une una cuenta con un plan comercial.
- Una pertenencia une una persona con una cuenta.
- Un dispositivo autorizado no es una pertenencia ni un asiento.

El contrato actual limita la cuenta operativa a `kind=independent`, aunque el modelo físico documental contempla clínicas. Ofrecer comercialmente los tres planes no cambia esa realidad ni acredita gestión de clínicas.

La aceptación remota seguirá siendo transaccional, con operaciones idempotentes, auditoría y recuperación. La autorización consume [authorization-rbac-abac.md](authorization-rbac-abac.md), aprobada como referencia funcional.

## 5. Conceptos

| Concepto | Definición |
|---|---|
| **Plan** | Oferta comercial: independiente, consultorio pequeño o centro médico. |
| **Versión de plan** | Configuración histórica de nombre, límite de asientos y precios. |
| **Periodicidad** | Regla de duración elegida: 30 días o un año. |
| **Suscripción** | Relación de una cuenta con un plan y su historia comercial. |
| **Periodo de servicio** | Intervalo pagado y aprobado durante el cual se concede servicio. |
| **Asiento** | Unidad de uso humano contada para el límite del plan, según §8. |
| **Cotización** | Cálculo de importe USD, tasa BCV y equivalente VES para una periodicidad. |
| **Reporte de pago** | Declaración del cliente sobre un pago ya realizado fuera del sistema. |
| **Dato declarado** | Valor aportado por el cliente; todavía no verificado. |
| **Dato verificado** | Valor asentado por el operador al revisar. |
| **Evidencia** | Captura o datos que apoyan la revisión; no prueban por sí solos el pago. |
| **Operador** | Actor administrativo de Nightingale autorizado para revisar suscripciones. |
| **Acceso comercial** | Disponibilidad del servicio por vigencia y plan, separada del RBAC personal. |

## 6. Actores y autorización

### 6.1 Propietario de la cuenta

Como alcance propuesto:

- Consulta plan, precio, vigencia, asientos y estado.
- Solicita una cotización para periodicidad y plan disponibles.
- Presenta reportes de pago.
- Consulta el estado e historia de sus propios reportes.
- Descarga evidencia que su cuenta haya presentado, mientras conserve el permiso administrativo.
- Solicita cambio de plan o cancelación.

No puede aprobar su propio pago, asignarse periodos, cambiar la tasa verificada ni editar datos verificados.

### 6.2 Asistente

No recibe permiso de suscripción por ser asistente. Su capacidad para consultar o reportar pagos requiere una decisión de permiso administrativo. Hasta entonces, las acciones de suscripción se consideran exclusivas del propietario.

### 6.3 Operador de Nightingale

El operador:

- Consulta reportes pendientes y su historia administrativa.
- Descarga evidencia de pago necesaria para revisar.
- Registra datos verificados, tasa y fuente aplicada.
- Aprueba o rechaza reportes.
- Administra versiones de planes/precios si recibe esa acción separada.
- Consulta suscripciones y periodos necesarios para su función.

No obtiene por defecto:

- Pertenencia a la cuenta.
- Rol `owner` o `assistant`.
- Acceso a pacientes, citas, notas o registros clínicos.
- Capacidad para modificar profesionales o dispositivos.
- Acceso SQL directo.

La autenticación, recuperación, alta y revocación del operador quedaron **decididas el 2026-11-26 en [D23](decisions.md#d23--operador-de-nightingale-identidad-ciclo-de-vida-y-canal-t03)** (`SU-O01` y `SU-O12` cerradas): Keycloak con identidad separada del personal, credencial opaca revocable en API, ciclo de vida gestionado como componente de la propia API por operadores con la acción separada (alta inicial por flujo administrativo de despliegue; recuperación = revocar y emitir nueva credencial), y canal en rutas de la misma aplicación FastAPI. No se reutiliza un token del personal con un claim que lo convierta en administrador global.

### 6.4 Paciente

El paciente no participa en las suscripciones de Nightingale. Un reporte de pago de consulta no debe mezclarse con este componente.

## 7. Catálogo de planes

### 7.1 Planes iniciales

| Código conceptual | Nombre | Diferencia permitida |
|---|---|---|
| `independent` | Médico independiente | Precio y límite de asientos |
| `small_practice` | Consultorio pequeño | Precio y límite de asientos |
| `medical_center` | Centro médico | Precio y límite de asientos |

Los códigos son conceptuales; no crean todavía una enumeración pública. Precios y límites iniciales decididos en [D21](decisions.md#d21--planes-precios-y-asientos-de-suscripciones-t01) (2026-11-26):

| Plan | Asientos | 30 días | Un año |
|---|---:|---:|---:|
| Médico independiente | 2 | USD 18 | USD 100 |
| Consultorio pequeño | 5 | USD 24 | USD 240 |
| Centro médico | 20 | USD 75 | USD 500 |

Cada plan exige:

- Nombre y descripción comercial.
- Estado de disponibilidad para nuevas suscripciones.
- Límite entero positivo de asientos.
- Precio para 30 días.
- Precio para un año.
- Moneda `USD`.
- Versión e historia de cambios.

### 7.2 Capacidades comunes

Todos los planes incluyen las mismas funciones disponibles en el producto. No habrá diferencias por plan en:

- Número de pacientes.
- Número de citas o atenciones.
- Secciones clínicas.
- Facturación administrativa.
- Récipes u órdenes.
- Almacenamiento por uso, salvo límites técnicos de seguridad aplicables por igual.

La palabra **ilimitado** describe ausencia de límite comercial por plan, no ausencia de límites técnicos de petición, archivo, frecuencia, almacenamiento seguro o protección contra abuso.

### 7.3 Historial de precios

Cambiar un precio o límite crea una versión nueva del plan. Una cotización, reporte o periodo anterior conserva la versión utilizada.

- Un precio nuevo aplica a cotizaciones nuevas.
- No modifica periodos ya aprobados.
- No cambia importes históricos.
- Retirar un plan impide nuevas contrataciones, pero no borra su historia.
- La política para renovaciones de un plan retirado se decide antes de retirarlo.

## 8. Asientos

### 8.1 Regla propuesta de cómputo

Un asiento corresponde a una **pertenencia humana activa y única dentro de la cuenta**, incluido el propietario.

| Elemento | ¿Consume asiento bajo la propuesta? | Motivo |
|---|---:|---|
| Propietario activo | Sí | Es un usuario humano de la cuenta |
| Asistente activo | Sí | Usa una pertenencia activa |
| Profesional activo con usuario y pertenencia | Sí, una vez | La relación profesional no crea otra persona |
| Segunda relación profesional del mismo usuario en la cuenta | No adicional | El asiento ya se cuenta por pertenencia |
| Pertenencia inactiva | No mientras esté inactiva | Al reactivar se vuelve a comprobar el límite |
| Invitación pendiente | No todavía | Se comprueba al aceptar |
| Dispositivo o token | No | Una persona puede usar varios dispositivos |
| Paciente o contacto | No | No es integrante de la cuenta |
| Operador de Nightingale | No | No pertenece al equipo de la cuenta |

Esta regla quedó **confirmada el 2026-11-26 en [D21](decisions.md#d21--planes-precios-y-asientos-de-suscripciones-t01)** (`SU-O02` cerrada). Los límites por plan son 2, 5 y 20 asientos según §7.1.

### 8.2 Operaciones que comprueban el límite

La comprobación se aplica al:

- Aceptar una invitación.
- Incorporar una pertenencia por otro flujo autorizado.
- Reactivar una pertenencia.
- Cambiar a un plan con menor límite.
- Corregir administrativamente una suscripción.

Consultar una invitación o crear una pendiente no garantiza que habrá asiento al aceptarla.

### 8.3 Concurrencia

La aceptación/reactivación y el cambio de plan deben coordinarse en PostgreSQL. Dos personas no pueden ocupar el último asiento por lecturas simultáneas independientes.

El efecto, la comprobación del límite, el recibo, la auditoría y los cambios de acceso comparten la transacción correspondiente. No se confirma primero una pertenencia y se verifica el límite después.

### 8.4 Exceso de asientos

Si una cuenta queda por encima del límite por una reducción de plan o corrección:

- No se desactivan personas automáticamente.
- Se conserva el acceso y la historia mientras se aplica la política acordada.
- Se impiden nuevas incorporaciones/reactivaciones hasta volver al límite.
- El propietario recibe una señal administrativa clara.

El tratamiento del exceso quedó **confirmado el 2026-11-26 en [D21](decisions.md#d21--planes-precios-y-asientos-de-suscripciones-t01)** (`SU-O08` cerrada): se aplican las reglas anteriores sin desactivación automática.

## 9. Moneda, precios y tasa BCV

### 9.1 Valores monetarios

Los importes se representan con decimales exactos, nunca con números binarios de punto flotante. PostgreSQL documenta `numeric`/`decimal` como tipos recomendados para cantidades monetarias.

Cada valor monetario incluye:

- Importe.
- Moneda ISO 4217, inicialmente `USD` o `VES` según el dato.
- Precisión y regla de redondeo.
- Origen: catálogo, declaración o verificación.

No se aceptan NaN, infinito, importes negativos para precios o valores ambiguos con formato regional.

### 9.2 Cotización

Una cotización conserva conceptualmente:

```text
accountId
planId y planVersion
periodicity
amountUsd
bcvRate (VES por 1 USD)
bcvRateDate
bcvRateSource
quotedAt y quotedBy
calculatedAmountVes
roundingRule
```

La fórmula propuesta es:

```text
montoVesSinRedondear = montoUsd * tasaBcv
montoVesCobrable = redondear(montoVesSinRedondear, 2 decimales, ROUND_HALF_UP)
```

Ejemplo puramente ficticio: USD 30,00 con tasa 400,25 produce VES 12.007,50. El ejemplo no representa una tasa real.

El redondeo se aplica una vez al total de la cotización. No se redondea la tasa ni cada operación intermedia con precisiones distintas.

### 9.3 Tasa del día

La referencia oficial es el [Banco Central de Venezuela](https://www.bcv.org.ve/). La primera versión no exige consultar su sitio automáticamente. Un operador puede registrar la tasa y su fecha/fuente, con evidencia administrativa.

La regla debe fijar:

- Qué fecha selecciona la tasa: pago, reporte o aprobación.
- Qué publicación se usa cuando el día no tiene tasa.
- Qué ocurre si el cliente declara una fecha dudosa.
- Quién puede corregir una tasa antes de aprobar.

**Regla decidida el 2026-11-26 en [D22](decisions.md#d22--tasa-bcv-monedas-y-periodos-de-suscripciones-t02)** (`SU-O03` cerrada): se usa la tasa BCV de la fecha del pago declarada y verificada por el operador. Si ese día no hay publicación, se usa la tasa publicada más reciente anterior. Si la fecha del pago no es verificable, el operador no aprueba automáticamente con una tasa elegida por el cliente; registra la decisión conforme a la política administrativa.

Las monedas de pago admitidas son **VES y USD**; la aprobación conserva importe y moneda efectivamente verificados.

### 9.4 Conservación histórica

Una aprobación congela:

- Precio USD y versión del plan.
- Periodicidad.
- Tasa BCV, fecha y fuente.
- Equivalente VES calculado.
- Importe y moneda efectivamente verificados.

Los informes posteriores no recalculan pagos antiguos con la tasa actual. Una corrección crea un evento administrativo nuevo; no reescribe silenciosamente el pasado.

### 9.5 Diferencias de importe

Pago insuficiente, excedente, abono parcial, pagos combinados o diferencias por redondeo quedaron **decididos el 2026-11-26 en [D24](decisions.md#d24--gracia-evidencias-y-excepciones-de-pago-en-suscripciones-t04)** (`SU-O10` cerrada): solo se aprueba como periodo completo un reporte cuyo importe verificado cubre el importe debido. Los pagos parciales o excedentes se rechazan con motivo y el cliente presenta un reporte corregido. Varios periodos requieren un reporte por periodo. No se infiere un crédito a favor ni se aplica el excedente a otro periodo.

## 10. Suscripción y estados

### 10.1 Separación de estados

No se reutiliza `accounts.status` para la condición comercial:

- `accounts.status` expresa estado administrativo/operativo existente.
- La suscripción expresa vigencia comercial.
- La pertenencia expresa acceso de una persona.
- El dispositivo expresa una instalación autorizada.

Suspender comercialmente no desactiva identidades, no revoca tokens y no cambia permisos clínicos.

### 10.2 Estados conceptuales propuestos

| Estado | Significado |
|---|---|
| `pending_activation` | Existe relación comercial o reporte, pero no hay periodo aprobado utilizable |
| `active` | Existe periodo aprobado vigente |
| `grace` | El periodo terminó y se aplica una gracia explícita |
| `suspended` | No existe acceso comercial vigente; los datos se conservan |
| `cancelled` | Se canceló la renovación o relación; puede existir tiempo ya pagado hasta su fin |

Estos nombres no forman todavía un contrato. La disponibilidad efectiva se calcula también con fechas y servidor; no depende solo de una etiqueta persistida.

No se incluye `trialing` porque no se aprobó un periodo de prueba.

### 10.3 Transiciones

- Aprobación inicial válida: sin periodo vigente → `active`.
- Fin del periodo: `active` → `grace` si existe gracia; en otro caso → `suspended`.
- Aprobación durante gracia o suspensión: → `active` con el periodo calculado.
- Cancelación: conserva el tiempo ya pagado y evita nueva renovación ordinaria hasta reactivar.
- Nuevo reporte pendiente no cambia por sí solo el estado ni interrumpe un periodo activo.
- Rechazo deja la suscripción en la condición anterior.

### 10.4 Sin borrado

Suspensión, vencimiento o cancelación:

- No borran cuentas, pacientes, citas, documentos o auditoría.
- No eliminan reportes o evidencias por sí solos.
- No prometen borrado de copias locales.
- Conservan una vía autenticada para renovar y consultar la situación comercial.

La disponibilidad de lecturas y escrituras durante gracia/suspensión queda en `SU-O07`.

## 11. Periodos de servicio y renovaciones

### 11.1 Intervalos

Cada periodo usa un intervalo `[startsAt, endsAt)` con inicio incluido y fin excluido. Conserva:

- Cuenta y suscripción.
- Plan y versión.
- Periodicidad.
- Inicio y fin.
- Reporte aprobado de origen.
- Secuencia respecto de periodos anteriores.
- Estado y motivo de corrección si lo hubiera.

No se solapan periodos ordinarios de una misma suscripción. Una corrección administrativa conserva trazabilidad.

### 11.2 Periodo de 30 días

La periodicidad mensual acordada significa **30 días**, no “el mismo día del mes siguiente”.

Propuesta: calcular 30 días civiles en `America/Caracas` desde el inicio acordado, con instante de fin explícito. Así se evita interpretar enero/febrero como una cuota distinta por longitud del mes.

### 11.3 Periodo anual

**Decidido el 2026-11-26 en [D22](decisions.md#d22--tasa-bcv-monedas-y-periodos-de-suscripciones-t02)** (`SU-O04` cerrada): un año es el **año civil** en `America/Caracas`. El periodo termina en la misma fecha civil del año siguiente; un inicio el 29 de febrero termina el 28 de febrero del año siguiente.

### 11.4 Renovación anticipada

Propuesta: si queda tiempo pagado, el nuevo periodo comienza en el `endsAt` del último periodo vigente. El cliente no pierde días por pagar antes.

```text
inicioNuevo = finDelUltimoPeriodoAprobado
finNuevo = inicioNuevo + duracionDeLaPeriodicidad
```

La cotización puede tener fecha/tasa distinta del inicio del periodo. Ambas fechas se conservan.

### 11.5 Renovación tardía

**Decidido el 2026-11-26 en [D22](decisions.md#d22--tasa-bcv-monedas-y-periodos-de-suscripciones-t02)** (`SU-O06` cerrada): el nuevo inicio es el instante de aprobación del servidor, salvo una corrección administrativa justificada. No se concede retroactividad por una fecha declarada del cliente.

### 11.6 Una aprobación, un efecto

Un reporte aprobado se vincula al periodo que generó. Repetir la misma acción recupera el resultado original. Una aprobación distinta sobre el mismo reporte no crea otro periodo.

Para comprar varios periodos se necesita una intención y evidencia explícitas; no se multiplica por repetir la petición.

## 12. Reportes de pago

### 12.1 Identidad y ámbito

Cada reporte pertenece a una sola cuenta y a una intención de plan/periodicidad. Conserva actor que lo presentó, fecha del servidor, versión y estado.

El cliente no elige el operador, el resultado ni el periodo aprobado. El `accountId` de ruta o payload se contrasta con la identidad autenticada.

### 12.2 Datos declarados

Según el caso, el reporte puede contener:

- Plan y periodicidad que pretende pagar.
- Fecha del pago.
- Importe y moneda.
- Método o banco descrito por el cliente.
- Últimos cuatro dígitos de la referencia.
- Nota administrativa breve.
- Captura de pago.

Los cuatro dígitos se conservan como texto para no perder ceros iniciales. No se solicita el número completo si no es necesario.

### 12.3 Modalidades de evidencia

| Modalidad | Requisito mínimo propuesto |
|---|---|
| Captura | Archivo privado válido y últimos cuatro dígitos de referencia |
| Manual | Datos declarados suficientes para revisión: fecha, importe, moneda, método y referencia parcial cuando exista |

Ambas modalidades necesitan revisión humana. Una captura visualmente convincente no cambia el estado por sí sola.

### 12.4 Estados del reporte

| Estado | Significado |
|---|---|
| `pending` | Presentado y pendiente de revisión |
| `approved` | Aceptado por un operador y vinculado a un efecto único |
| `rejected` | Rechazado con motivo administrativo |

No se reabre un reporte aprobado. Una corrección del cliente crea otro reporte relacionado o una nueva versión según el diseño posterior, conservando el original.

### 12.5 Datos verificados separados

La revisión conserva dos conjuntos:

- **Declarados:** lo que envió el cliente, inmutables después de presentar salvo corrección trazada antes de revisar.
- **Verificados:** lo que el operador asienta al aprobar o rechazar.

El operador no sobrescribe la declaración para hacerla coincidir con su decisión. Registra sus propios valores, instante, identidad y motivo.

### 12.6 Referencias y duplicados

Los últimos cuatro dígitos no son únicos globalmente. No se impone una restricción de unicidad sobre ellos.

El sistema puede advertir coincidencias de cuenta, fecha, importe y referencia parcial para ayudar a revisar. La coincidencia no prueba fraude ni justifica borrar/rechazar automáticamente otro reporte.

## 13. Capturas y almacenamiento privado

### 13.1 Reglas de carga

La captura:

- Solo la presenta un usuario autorizado para esa cuenta.
- Tiene tamaño máximo y tipos permitidos definidos antes del contrato.
- Se valida por extensión, tipo real y firma de archivo; no se confía solo en `Content-Type`.
- Recibe un nombre interno generado por API.
- Se almacena fuera de una ruta pública/webroot.
- Se vincula a cuenta y reporte mediante una referencia interna.
- No se entrega mediante una URL pública permanente.

Los límites concretos quedaron **decididos el 2026-11-26 en [D24](decisions.md#d24--gracia-evidencias-y-excepciones-de-pago-en-suscripciones-t04)** (`SU-O09` cerrada): formatos JPG, PNG y PDF; máximo 5 MB por archivo; una captura por reporte.

### 13.2 Descarga

La descarga vuelve a autorizar:

- Propietario de la cuenta para sus propias evidencias.
- Operador con acción de revisión para evidencias necesarias.

Conocer `storageKey`, UUID o nombre de archivo no concede acceso. No se incluyen capturas en páginas públicas, logs, auditoría, métricas o sincronización general.

### 13.3 Ciclo de vida

Una carga fallida o un archivo huérfano no activa nada. El reporte solo referencia evidencia cuya carga terminó y cuyo vínculo es válido.

La retención quedó **decidida el 2026-11-26 en [D24](decisions.md#d24--gracia-evidencias-y-excepciones-de-pago-en-suscripciones-t04)** (`SU-O09` cerrada): la evidencia y los reportes se conservan mientras la cuenta exista; no se borran al rechazar ni al vencer la suscripción; la eliminación solo ocurre por un proceso administrativo trazado. Copias y restauración siguen la política general de operación antes de datos reales.

## 14. Revisión y aprobación

### 14.1 Secuencia de aprobación

1. Autenticar al operador y comprobar la acción de revisión.
2. Obtener el reporte y coordinar su versión/estado.
3. Releer cuenta, suscripción, plan y precio aplicable.
4. Comprobar evidencia y datos declarados disponibles.
5. Registrar los datos verificados, tasa y fuente.
6. Calcular el periodo conforme a la historia aprobada.
7. Confirmar en una transacción: decisión, periodo, suscripción, historia, auditoría y resultado idempotente.
8. Publicar después del commit solo las proyecciones permitidas.

Las llamadas de red o lectura de archivos externos no ocurren dentro de la transacción PostgreSQL.

### 14.2 Condiciones

El operador solo puede aprobar un reporte pendiente. Deben existir plan, periodicidad y cotización/datos suficientes. La aprobación asienta su decisión humana; no declara una integración bancaria ni una comprobación automática que no ocurrió.

### 14.3 Idempotencia y dos operadores

Si dos operadores revisan a la vez:

- Uno obtiene el orden válido y confirma.
- El otro recibe duplicado o conflicto de versión, sin segundo periodo.
- El resultado conserva quién aprobó realmente.
- Ningún reintento duplica días, importes o historias.

### 14.4 Resultado

El propietario puede conocer el resultado de su reporte y el periodo concedido. No recibe datos internos del operador ni reportes de otras cuentas.

## 15. Rechazo y nueva presentación

Al rechazar se conserva:

- Operador e instante.
- Motivo administrativo seguro.
- Datos declarados originales.
- Evidencia.
- Versión e historia.

El motivo no incluye secretos ni datos bancarios completos. La suscripción no cambia de estado por el rechazo.

Si el cliente corrige la información:

- Se crea una nueva presentación vinculada al reporte anterior, o se aplica una versión previa a revisión si así se contrata.
- No se modifica un reporte ya aprobado/rechazado para borrar su historia.
- La nueva presentación vuelve a `pending`.
- Cada aprobación sigue teniendo un efecto único.

## 16. Cambios de plan y cancelación

### 16.1 Cambio de plan

Un cambio conserva:

- Plan anterior y nuevo.
- Versiones y precios.
- Instante solicitado y efectivo.
- Reporte que paga el cambio, si corresponde.
- Regla de asientos comprobada.

Un plan superior no cambia las funciones, porque todas son comunes; cambia límite de asientos y precio futuro.

Un plan inferior exige que el consumo de asientos cumpla el nuevo límite o la política de exceso aprobada.

### 16.2 Prorrateo

**Decidido el 2026-11-26 en [D24](decisions.md#d24--gracia-evidencias-y-excepciones-de-pago-en-suscripciones-t04)** (`SU-O11` cerrada): no hay prorrateo ni crédito por días restantes. El cambio de plan se aplica al siguiente periodo aprobado; el tiempo pagado del plan anterior se conserva completo.

### 16.3 Cancelación

Cancelar detiene la renovación ordinaria; no acorta el tiempo pagado ni borra datos. Una cancelación puede deshacerse solo mediante una acción administrativa explícita y trazada antes de iniciar otro periodo.

No hay cargos pendientes automáticos porque no existe pasarela.

## 17. Acceso comercial a las funciones

### 17.1 Dos decisiones independientes

```text
acceso_efectivo =
    autorizacion_personal_vigente
    y disponibilidad_comercial_vigente
    y reglas_del_objeto
```

- La suscripción no concede permisos personales.
- Un rol no evita una suspensión comercial.
- El límite de asientos no cambia niveles clínicos.
- Un pago aprobado no convierte al reportante en propietario.

### 17.2 Acciones siempre administrables

Incluso con suscripción no vigente, la cuenta necesita un alcance mínimo autenticado para:

- Consultar su situación comercial.
- Presentar o consultar reportes.
- Solicitar renovación.
- Recuperar acceso según la política.

Estas acciones no abren datos operativos por defecto.

### 17.3 Gracia y suspensión

La duración de la gracia y las funciones permitidas quedaron **decididas el 2026-11-26 en [D24](decisions.md#d24--gracia-evidencias-y-excepciones-de-pago-en-suscripciones-t04)** (`SU-O07` cerrada):

- Gracia de **7 días** con servicio normal tras el fin del periodo.
- Después, suspensión: se impiden las escrituras operativas.
- Se conserva la lectura/exportación de datos durante la suspensión.
- La renovación y la consulta del estado comercial permanecen siempre disponibles.
- Offline: la proyección del servidor comunica el fin de gracia; el reloj local no extiende vigencia.

### 17.4 Errores

La indisponibilidad comercial no se presenta como credencial inválida. Después de autenticar y autorizar, el contrato futuro debe distinguir:

- Suscripción ausente.
- Periodo vencido/en gracia.
- Servicio suspendido.
- Límite de asientos alcanzado.
- Plan no disponible para la acción solicitada.

Los códigos públicos exactos no se fijan aquí. Un objeto ajeno sigue devolviendo la misma ausencia que uno inexistente antes de revelar su situación comercial.

## 18. Offline y sincronización

### 18.1 Proyección mínima

El escritorio necesita una proyección suficiente para presentar estado comercial y aplicar la política aprobada. Como mínimo conceptual:

- Estado de disponibilidad.
- Plan y versión visibles.
- `startsAt`, `endsAt` y fin de gracia cuando corresponda.
- Límite y consumo de asientos para administración autorizada.
- Versión de suscripción e instante de actualización del servidor.

Los detalles de reportes, notas de revisión y evidencias no se distribuyen a todos los miembros.

### 18.2 Audiencias

Propuesta:

- Miembros: disponibilidad mínima necesaria para explicar acceso.
- Propietario: plan, asientos, cotizaciones, reportes y periodos administrativos.
- Operador: proyección de revisión fuera de la sincronización ordinaria del escritorio.

La captura nunca se incluye en snapshots o deltas generales.

### 18.3 Vigencia offline

La copia local no puede extender una suscripción. El reloj del cliente no crea días adicionales ni prueba que un pago fue aprobado.

La política offline debe resolver:

- Qué ocurre al superar `endsAt` sin conexión.
- Si se admite gracia ya comunicada por el servidor.
- Qué escrituras locales se permiten durante suspensión.
- Cómo se conservan intenciones al recuperar servicio.

No se promete suspensión inmediata en equipos desconectados ni borrado remoto de datos.

### 18.4 Cambios comerciales

La versión comercial es distinta de `permissionEpoch` cuando solo cambia disponibilidad y no permisos de lectura. Si una política cambia qué datos puede descargar un actor, debe invalidar también el alcance de sincronización afectado.

No se reutiliza un cursor para conceder acceso comercial.

## 19. Modelo conceptual de datos

Sin definir tablas físicas, el componente necesita representar:

| Entidad conceptual | Responsabilidad |
|---|---|
| `plans` | Identidad comercial estable y estado del plan |
| `plan_versions` | Asientos, precios y periodicidades históricas |
| `account_subscriptions` | Relación actual de una cuenta con su plan y estado |
| `subscription_periods` | Intervalos aprobados, secuencia y origen |
| `payment_reports` | Declaración, estado, versión y cuenta |
| `payment_report_evidence` | Referencia privada a captura y metadatos mínimos |
| `subscription_reviews` | Decisión, datos verificados, operador y motivo |
| `bcv_exchange_rates` | Tasa, fecha, fuente y evidencia administrativa |

Reglas conceptuales:

- Una suscripción pertenece a una sola cuenta.
- Un reporte no cruza cuentas.
- Un periodo referencia una sola aprobación de origen.
- Una aprobación produce como máximo un periodo ordinario.
- Los periodos ordinarios no se solapan.
- Los importes usan decimal exacto y moneda.
- Los estados/historias no se borran al cambiar el plan.
- Las pertenencias existentes son la base del cómputo de asientos; no se duplican usuarios para suscripciones.

El diseño físico deberá añadir restricciones e índices solo en [database-schema.md](database-schema.md) cuando se revise ese trabajo.

## 20. Casos de uso y contratos futuros

### 20.1 Cuenta

Casos conceptuales:

- Consultar suscripción y consumo de asientos.
- Obtener cotización para plan/periodicidad.
- Presentar reporte con evidencia.
- Consultar lista/detalle de reportes propios.
- Descargar evidencia propia autorizada.
- Solicitar cambio de plan o cancelación.

### 20.2 Operador

- Consultar reportes pendientes con filtros administrativos.
- Consultar detalle y evidencia.
- Registrar tasa BCV o seleccionar una ya verificada.
- Aprobar reporte.
- Rechazar reporte.
- Consultar periodos e historia.
- Administrar catálogo si posee esa acción separada.

### 20.3 Uso interno

- Resolver disponibilidad comercial de una cuenta.
- Comprobar asiento antes de aceptar/reactivar pertenencia.
- Proyectar estado mínimo a consumidores.
- Emitir aviso de cambio comercial sin contenido financiero sensible.

### 20.4 Transporte

Todas las altas, decisiones y cambios administrativos son online. Deben usar identidad de operación, versión esperada, resultado idempotente y autorización vigente.

No se fijan aquí rutas, nombres `CamelCase`, campos JSON o códigos HTTP. Los contratos se añadirán a sus fuentes únicas cuando exista un diseño aprobado para ello.

## 21. Auditoría, privacidad y seguridad

### 21.1 Evidencia de decisiones

Registrar como mínimo:

- Cuenta y reporte.
- Actor que presentó.
- Operador que revisó.
- Acción y resultado.
- Instante del servidor.
- Plan/versión y periodo generado.
- Correlación e identidad de operación.
- Motivo de rechazo o corrección administrativa.

### 21.2 Datos que no se registran en logs

- Captura o sus bytes.
- URL firmada o clave de almacenamiento.
- Número bancario completo.
- Credenciales o tokens.
- Datos personales contenidos dentro de la imagen.
- Información clínica ajena a la revisión.

### 21.3 Aislamiento

Una cuenta no puede consultar reportes, importes, planes históricos contratados o evidencias de otra. Un operador solo recibe las acciones administrativas necesarias; su alcance no se convierte en acceso clínico.

### 21.4 Conservación

Antes de datos reales se debe aprobar retención de:

- Reportes aprobados/rechazados.
- Capturas.
- Historia de planes y periodos.
- Auditoría.
- Copias de seguridad y restauración.

La supresión de una cuenta no se deduce del vencimiento de su suscripción.

## 22. Consultas e indicadores administrativos

El componente puede ofrecer, sin convertirse en contabilidad:

- Cuentas por plan y estado.
- Vigencias próximas a terminar.
- Reportes pendientes y antigüedad.
- Periodos aprobados por plan/periodicidad.
- Importes verificados en USD y VES histórico.
- Uso de asientos por cuenta.
- Cuentas por encima del límite.
- Historia de cambios de plan.

Los importes VES conservan la tasa del momento aprobado. No se suman como si fueran comparables sin indicar periodo y moneda. Un reporte pendiente no cuenta como ingreso verificado.

Estas consultas no exponen pacientes ni justifican una base analítica clínica.

## 23. Fallos, conflictos y recuperación

| Situación | Resultado exigido |
|---|---|
| Respuesta perdida al presentar reporte | Recuperar la misma intención sin duplicar evidencia o reporte |
| Respuesta perdida al aprobar | Consultar/reintentar la misma aprobación; no crear otro periodo |
| Dos aprobaciones simultáneas | Un solo efecto y un operador real |
| Renovación y cambio de plan simultáneos | Un orden verificable; periodo coherente con una versión de plan |
| Aceptación de invitación y reducción de asientos | Un solo ganador del último asiento |
| Captura cargada pero reporte falla | Archivo sin efecto comercial; limpieza/retención controlada |
| Reporte aprobado y aviso perdido | El periodo persiste; el consumidor recupera por versión/sincronización |
| Tasa corregida antes de aprobar | Historia de tasas y valor usado explícito |
| Error después del commit | No repetir efecto; recuperar resultado |
| Cuenta sin conexión al vencer | Aplicar política offline aprobada; no extender por reloj local |

## 24. Criterios verificables

Estos criterios son requisitos futuros, no pruebas ejecutadas por esta entrega.

### 24.1 Catálogo y dinero

- Los tres planes comparten funciones y solo difieren en precio/asientos.
- Cambiar un precio no altera cotizaciones o periodos anteriores.
- La multiplicación USD × BCV usa decimal exacto y redondeo documentado.
- La tasa, fecha y fuente quedan en la aprobación.
- Los informes no revalorizan pagos antiguos.

### 24.2 Periodos

- 30 días no se interpreta como mes calendario.
- La regla anual queda probada también alrededor de 29 de febrero después de decidirla.
- Renovación anticipada no pierde días.
- Renovación tardía aplica el inicio acordado.
- Periodos ordinarios no se solapan.
- Repetir aprobación no añade días.

### 24.3 Reportes

- Presentar no activa.
- Aprobar activa/extiende una vez.
- Rechazar conserva estado comercial anterior.
- Datos declarados y verificados permanecen diferenciados.
- Los cuatro dígitos conservan ceros iniciales y no se tratan como clave única.
- Una nueva presentación conserva la historia anterior.

### 24.4 Asientos

- El propietario y cada pertenencia activa cuentan según la regla aprobada.
- Un usuario con varias relaciones profesionales en la misma cuenta no duplica asiento.
- Dispositivos, invitaciones pendientes y pacientes no cuentan.
- Dos aceptaciones concurrentes no superan el límite.
- Una reducción de plan no desactiva integrantes automáticamente.

### 24.5 Seguridad

- Una cuenta no accede a reportes/evidencias ajenos.
- El operador no accede a clínica por su función.
- Archivos validan tipo real, tamaño y almacenamiento privado.
- La descarga reautoriza aunque se conozca el identificador.
- Ninguna captura aparece en sincronización general, logs o micrositio.

### 24.6 Offline

- El cliente no extiende vigencia con su reloj.
- Una aprobación desconocida se recupera sin duplicarla.
- La suspensión no borra intenciones o copias locales.
- La experiencia del escritorio requiere pruebas en su repositorio; API no acredita ese consumidor.

## 25. Criterios para aceptar esta especificación

- Refleja las nueve decisiones `SU-D01`–`SU-D09` sin añadir pasarela ni diferencias de funciones.
- Mantiene separados suscripción, pertenencia, dispositivo y autorización personal.
- Define cotización, evidencia, revisión, aprobación y periodo sin confundirlos.
- No inventa precios, asientos, gracia o duración anual.
- Conserva historia, idempotencia, aislamiento y recuperación.
- Trata capturas como documentos privados.
- No presenta planes de clínicas como funciones internas ya implementadas.
- Deja los puntos abiertos necesarios antes del contrato físico/HTTP.

## 26. Decisiones pendientes

| ID | Decisión | Impacto |
|---|---|---|
| `SU-O01` | ~~Alta, autenticación, recuperación y revocación del operador~~ **Cerrada 2026-11-26 en [D23](decisions.md#d23--operador-de-nightingale-identidad-ciclo-de-vida-y-canal-t03):** Keycloak + credencial opaca revocable en API; ciclo de vida como componente de API gestionado por operadores con acción separada | — |
| `SU-O02` | ~~Confirmar qué pertenencias consumen asiento y límites numéricos por plan~~ **Cerrada 2026-11-26 en [D21](decisions.md#d21--planes-precios-y-asientos-de-suscripciones-t01):** regla §8.1 confirmada; límites 2/5/20 | — |
| `SU-O03` | ~~Fecha que selecciona tasa BCV, días sin publicación y monedas de pago admitidas~~ **Cerrada 2026-11-26 en [D22](decisions.md#d22--tasa-bcv-monedas-y-periodos-de-suscripciones-t02):** tasa de la fecha del pago verificada, tasa anterior si no hay publicación; pagos en VES y USD | — |
| `SU-O04` | ~~Año de 365 días o año civil y regla para 29 de febrero~~ **Cerrada 2026-11-26 en [D22](decisions.md#d22--tasa-bcv-monedas-y-periodos-de-suscripciones-t02):** año civil; 29 de febrero termina el 28 de febrero siguiente | — |
| `SU-O05` | ~~Precios USD por plan y periodicidad~~ **Cerrada 2026-11-26 en [D21](decisions.md#d21--planes-precios-y-asientos-de-suscripciones-t01):** 18/100, 24/240, 75/500 USD | — |
| `SU-O06` | ~~Inicio de periodo inicial y renovación tardía~~ **Cerrada 2026-11-26 en [D22](decisions.md#d22--tasa-bcv-monedas-y-periodos-de-suscripciones-t02):** inicio en aprobación; anticipada desde `endsAt` sin perder días | — |
| `SU-O07` | ~~Duración de gracia y funciones permitidas en gracia/suspensión, incluida política offline~~ **Cerrada 2026-11-26 en [D24](decisions.md#d24--gracia-evidencias-y-excepciones-de-pago-en-suscripciones-t04):** 7 días de gracia; suspensión con lectura y renovación; reloj local no extiende | — |
| `SU-O08` | ~~Tratamiento de cuentas que superan el asiento tras cambio de plan~~ **Cerrada 2026-11-26 en [D21](decisions.md#d21--planes-precios-y-asientos-de-suscripciones-t01):** §8.4 confirmado, sin desactivación automática | — |
| `SU-O09` | ~~Formatos/tamaños de captura, retención, copias y eliminación~~ **Cerrada 2026-11-26 en [D24](decisions.md#d24--gracia-evidencias-y-excepciones-de-pago-en-suscripciones-t04):** JPG/PNG/PDF, 5 MB, una captura por reporte; retención mientras la cuenta exista | — |
| `SU-O10` | ~~Pagos parciales, excedentes, varios periodos y duplicados sospechosos~~ **Cerrada 2026-11-26 en [D24](decisions.md#d24--gracia-evidencias-y-excepciones-de-pago-en-suscripciones-t04):** solo pago completo; parcial/excedente se rechaza; un reporte por periodo; coincidencias solo advierten | — |
| `SU-O11` | ~~Prorrateo o cambio solo en el siguiente periodo~~ **Cerrada 2026-11-26 en [D24](decisions.md#d24--gracia-evidencias-y-excepciones-de-pago-en-suscripciones-t04):** sin prorrateo; el cambio aplica al siguiente periodo aprobado | — |
| `SU-O12` | ~~Canal/interfaz del operador~~ **Cerrada 2026-11-26 en [D23](decisions.md#d23--operador-de-nightingale-identidad-ciclo-de-vida-y-canal-t03):** rutas de operador en la misma aplicación FastAPI; sin módulo del Hub deducido | — |

Las decisiones pendientes no impiden revisar la especificación base. Bloquean solo el comportamiento que dependa de ellas.

## 27. Referencias

- [Banco Central de Venezuela](https://www.bcv.org.ve/): fuente institucional de referencia para tasas y calendario bancario. Esta especificación no acredita una API pública ni integración automática.
- [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html): códigos de moneda como `USD` y `VES`.
- [PostgreSQL 18, tipos numéricos](https://www.postgresql.org/docs/18/datatype-numeric.html): `numeric`/`decimal` para exactitud monetaria.
- [PostgreSQL 18, bloqueo explícito](https://www.postgresql.org/docs/18/explicit-locking.html): coordinación de aprobaciones y asientos; requiere pruebas propias.
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html): tipos permitidos, validación real, nombres generados, límites, autorización y almacenamiento fuera del webroot.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): mínimo privilegio y autorización en cada solicitud.
- [Especificación de autorización RBAC/ABAC](authorization-rbac-abac.md): separación de permisos personales, operador, paciente y acceso comercial.
- [D09 · Primera etapa de API compartida](decisions.md#d09--primera-etapa-de-api-compartida-para-escritorio): altas controladas, operaciones tipadas y límites actuales.
- [D14 · Autorización RBAC/ABAC](decisions.md#d14--especificación-separada-de-autorización-rbacabac): modelo aprobado y separación comercial.

## 28. Resultado de esta entrega

Esta revisión define el alcance funcional de suscripciones sin introducir Billing externo ni un sistema de entitlements innecesario. No declara implementados planes, pagos, operador, archivos o enforcement comercial. Las reglas abiertas deben resolverse antes de convertir los conceptos afectados en esquema físico o contrato HTTP.
