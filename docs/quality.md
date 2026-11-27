# Requisitos de calidad y estrategia de pruebas

**Estado:** C05 aceptado. T16–T18 añaden catálogo, ofertas y reglas semanales comprobadas para revisión C06, sin aceptar. Las pruebas distinguen propiedad/privacidad, rollback entre cuentas, unicidad abierta y bloqueo real del profesional de la integración pendiente con citas. Disponibilidad completa, reservas, descarga y operación siguen pendientes. La [guía de desarrollo](operations/development.md) separa pruebas locales, PostgreSQL/Keycloak y límites de consumidores. **R** indica requisito confirmado; **P**, prueba propuesta; **A**, decisión abierta en [el registro](decisions.md).

## Requisitos verificables

| ID / estado | Condición de aceptación | Comprobación futura y evidencia |
|---|---|---|
| Q01 · R | Cada entrada privada comprueba cuenta, objeto, acción y acceso vigente; no revela datos ajenos en éxito, error, resultado previo o página. La futura lectura pública de D11 solo devuelve información destinada a publicación, sin permisos del personal | A/B con IDs cruzados en HTTP, repositorios, workers, n8n, snapshots e indicadores; verificar respuesta y estado persistido. Para el futuro Hub, probar por separado lectura pública y acceso limitado a citas |
| Q02 · R | Solo se acepta identidad/contexto comprobado; la revocación no se elude con permisos o reloj del cliente | Operaciones manipuladas, credenciales vencidas/revocadas, rol cambiado y carrera revocación/escritura. O01 debe fijar el resultado según el orden autorizado |
| Q03 · R | HTTPS validado, secretos fuera de código/logs y PostgreSQL operativo privado con identidades mínimas separadas | Pruebas de permisos SQL de ejecución/worker/migración; revisión de red y certificados en entorno de prueba; intento de acceso desde clientes sin credenciales |
| Q04 · R | Efecto, versión, historial, auditoría, resultado, cambios y trabajo derivado se confirman juntos o no aparecen | Fallos inyectados entre escrituras y antes del commit; comprobar todas las filas relacionadas. Repositorios sin commits parciales |
| Q05 · R | Reservas incompatibles no coexisten y una versión antigua no sobrescribe el estado aceptado | Conexiones PostgreSQL independientes y barreras controladas; dos reservas, reprogramación frente a bloqueo/cancelación y revocación frente a aceptación |
| Q06 · R | Reintentar no repite efectos; misma clave con otro contenido se rechaza. Una respuesta perdida se recupera sin segunda escritura | Solicitudes iguales simultáneas, contenido distinto y corte tras commit. Ver un efecto, un resultado y sus hechos; repetir con acceso revocado sin filtrar resultado |
| Q07 · R | Páginas/snapshot cubren todos los cambios autorizados y bajas, sin saltos por orden de confirmación | Transacción A asigna primero y confirma después de B; descargar entre ambos commits y continuar. Snapshot concurrente, caída por página, cursor ajeno/manipulado/vencido y cambios de alcance |
| Q08 · R | Recuperación conserva intenciones y compatibilidad con consumidores soportados | Prueba contractual de base vacía, cursor vencido, bajas retenidas y operación pendiente. Comprobación Rust real en su repositorio sigue pendiente hasta integración |
| Q09 · R | Se guardan datos mínimos; auditoría y logs tienen acceso y fin distintos; colas y errores excluyen secretos y datos personales innecesarios | Fixtures ficticios con marcadores de secreto/contacto; revisar logs, métricas, errores, mensajes, auditoría y copias. Aprobar campos y retención antes de datos reales |
| Q10 · R/A | Consultas paginadas y acotadas, lotes y frecuencia limitados, tiempos de espera y cancelación definidos | Casos al límite y por encima de límites aprobados; plan de consulta e índices con volúmenes representativos. Medir respuesta, transacción, bloqueos y demora de sync por separado; cifras pendientes |
| Q11 · R | Un commit no pierde trabajo aunque caiga el proceso antes de publicar; reiniciar workers recupera trabajo sin repetir cambios | Caídas tras commit, tras reclamar y antes de registrar resultado; entrega duplicada, reclamación vencida y competencia de workers. Inspeccionar trabajo e intentos persistidos |
| Q12 · R | Un timeout externo conserva resultado desconocido; solo repite con garantía del proveedor o conciliación | Proveedor de prueba que recibe y corta respuesta; verificar consulta/revisión, reintentos acotados y ausencia de reenvío ciego. Duplicados y webhooks fuera de orden |
| Q13 · R | Correlación técnica y auditoría permiten seguir una operación sin incluir su payload personal | Recorrer HTTP, transacción, trabajo, webhook y ETL con IDs. Métricas sin etiquetas de paciente/operación de alta cardinalidad; no confundir métricas con auditoría |
| Q14 · R/A | Salud separa proceso vivo, preparación y dependencias; los entornos no comparten credenciales ni datos reales | Caer PostgreSQL/proveedor/worker por separado y observar señales. Verificar configuración inválida antes de tráfico, aislamiento de entornos y cierre de recursos |
| Q15 · R/A | Copias y restauración recuperan un estado coherente y permiten conciliar trabajos/resultados | Restaurar en entorno aislado; comparar entidades, versiones, resultados, cambios y trabajos. Ensayar reanudación sin duplicados; medir pérdida/tiempo y contrastar con RPO/RTO por aprobar |
| Q16 · R | Contratos/migraciones tienen versión, compatibilidad y pruebas reproducibles; dependencias justificadas | Instalación con lockfile sin cambios, pruebas desde entorno limpio, cambios contractuales y actualización de esquema desde la versión soportada; fallo sin pérdida y respaldo antes de cambios destructivos |

No se promete revocación instantánea sin red ni borrado seguro de datos ya descifrados en un equipo intervenido. El escritorio no pierde una intención local porque API la rechace. API no puede recuperar cambios que nunca recibió.

## Capas de prueba propuestas

1. **Dominio:** reglas y transiciones puras; tiempo e identificadores controlados. Sin red ni base de datos.
2. **Aplicación:** coordinación, permisos y resultados con sustitutos pequeños. Estas pruebas no acreditan restricciones SQL ni concurrencia.
3. **Persistencia:** PostgreSQL real aislado, misma familia/versiones que se aprueben para operación; migraciones desde vacío y desde versión previa, fallos y carreras con conexiones independientes. No ejecutar contra bases de colaboradores ni producción.
4. **HTTP y contratos:** autenticación, alcance por objeto, campos manipulados, errores, límites y matriz de consumidores. Validar el mismo artefacto que consumen Rust y Hub.
5. **Workers e integraciones:** reloj controlado, proceso reiniciado, proveedor de prueba y resultado desconocido. Añadir pruebas reales del proveedor y del Hub cuando existan, con datos ficticios.
6. **Operación:** carga con datos representativos, caídas, copias y restauración. Separar evidencia local, CI y entorno desplegado. Una configuración de CI no acredita su ejecución.

## Escenarios que deben constar en el plan

| Escenario | Resultado a demostrar | Tareas |
|---|---|---|
| Cuenta A envía un objeto de B o el acceso limitado del Hub apunta a otra cita | Sin lectura, escritura ni filtración del resultado; D11 no elige un mecanismo de concesión | T08, T14, T15 históricas; futuro contrato Hub pendiente |
| Ejecutable modificado omite validación Rust | API rechaza transición, referencia o permiso inválido | T12, T14 |
| Dos conexiones reservan o modifican agenda/cita | Solo un estado compatible; conflicto explícito y sin pérdida de historial | T11, T12, T14 |
| Duplicados, distinta carga y respuesta perdida | Mismo resultado permitido y un efecto; conflicto para distinto contenido | T12, T14 |
| Revocación con pendientes y reloj cambiado | Política aprobada aplicada con evidencia del servidor; intención conservada por el consumidor | T04, T08, T14, T23 |
| Paginación con commits invertidos, bajas y recuperación inicial | Sin omisiones; snapshot/cursor coherentes y recuperación explícita | T05, T13, T14 |
| Hub cancela mientras escritorio reprograma/confirma | La versión impide sobrescritura; respuesta perdida se concilia | T15, T23 |
| Worker cae y proveedor recibió un envío sin responder | Trabajo recuperable y resultado desconocido visible; sin repetición ciega | T16, T17, T18 |

Los controles completos de Q01–Q16 siguen pendientes; T03 no acredita seguridad, integridad ni operación con PostgreSQL real. Las comprobaciones documentales iniciales se registran aparte en [fuentes y revisión](sources.md).

## Criterios clínicos de etapa 1 · diseño para C01

Los casos siguientes pertenecen a [P-20261115-02-patient-clinical-data](../tasks/P-20261115-02-patient-clinical-data/plan.md); no constan ejecutados por incorporar el diseño:

- Sexo al nacer ausente/desconocido, nacimiento opcional, edad y 29 de febrero; condiciones/sustancias vacías, texto libre repetido sin fusión y estados/certeza independientes.
- Fechas completas/parciales, bisiestos, inicio futuro y orden indeterminado; ausencia frente a null, patch vacío y `NO_CHANGES` sin versión.
- Historia completa e inmutable desde versión 1, anulación terminal y cambios de nacimiento sin continuidad artificial ni historia previa inventada.
- Listas `not_recorded`,`not_asked`,`unknown`,`none_known`,`has_entries`; alta y retirada del último pertinente; carrera entre alta y ausencia conocida.
- Propietario y asistente con `none`,`read`,`read_write` combinados por sección; miembro/cuenta inactiva, dispositivo revocado y resultado previo tras revocación.
- Paciente/registro ajeno en detalle, búsqueda, total, historia, error, resultado y captura; ninguna fuga de nombres, sustancias, reacciones o secretos en auditoría/logs.
- Duplicados, contenido distinto, respuesta perdida, versiones antiguas, rollback inmediato/diferido y recuperación con nueva instalación autorizada.
- Captura anterior sin clínica, captura clínica por subconjunto, datos fuera de ventana de citas, grupos invisibles, cambio de época y SSE abierto. Descarga del estado actual sin historias completas.

Dominio y aplicación se prueban sin red; integridad, historia, permisos y carreras exigen PostgreSQL real aislado. Contratos y ejemplos se validarán contra el código real en T17/T18; consumidor Rust y operación con datos reales quedan fuera de esa evidencia.

## Criterios futuros del Hub · D11

Estos criterios derivan del [alcance acordado](nightingale-api.md#5-integración-con-patient-hub); no son pruebas ejecutadas ni funciones disponibles. Las referencias Txx de las tablas anteriores son del plan histórico, no autorizan implementar Hub.

- Leer sin cuenta ni inicio de sesión ambas plantillas: médico independiente y clínica/centro. Exponer solo información destinada a publicación; no filtrar pacientes, citas o notas privadas ni abrir rutas internas.
- Gestionar una cita existente con acceso limitado y sin credenciales del personal: consulta permitida, confirmar, cancelar según reglas, pedir reprogramación y consultar resultado. Rechazar cruce de cita, acción o información y revalidar el acceso al resultado.
- Impedir creación/reserva de citas, exploración de disponibilidad para elegir otro horario y registro de ausencia por el paciente. El personal conserva las ausencias bajo las reglas actuales.
- Comprobar que una solicitud conserva estado, horario y confirmación y no reserva otro intervalo. Solo el personal decide el cambio; API aplica versiones, restricciones e invalidación de confirmación al reprogramar.
- Probar revocación, acción concurrente y respuesta perdida cuando exista el contrato de acceso. No exigir un segundo backend ni un almacén propio del Hub. No deducir gestión interna completa de clínicas, varias sedes o cambios generales del escritorio de su micrositio público.

## Criterios clínicos de etapa 2 · diseño para C01

Casos de [P-20261116-02-clinical-routine](../tasks/P-20261116-02-clinical-routine/plan.md), preparados pero no ejecutados. Todos usan datos ficticios y marcadores reconocibles para revisar que contenido clínico no aparezca en errores, logs, auditoría, cursores o timeline.

- **E06/E14:** atención sin cita, varias por cita, motivo en palabras del paciente y `serviceId` aún obligatorio al reservar; última visita solo desde atenciones válidas, con corrección/anulación/empates y sin efectos automáticos de citas/notas/ficha.
- **E07:** nota independiente/vinculada, autor/fecha/versiones, edición sin motivo y ausencia de diagnóstico/condición automática o cambio de última visita.
- **E08/E09:** dos pesajes válidos y corrección 700→70; la versión anterior queda en historia, no como punto vigente.
- **E10/E11:** hecho, captura local y aceptación separados; carga histórica no desplaza toma reciente; respuesta perdida no repite efecto.
- **E12:** presión con un componente desconocido, sin cero inventado ni mezcla de tomas.
- **E13:** vacuna antigua con fuente/precisión y detalles opcionales; declaración no prueba administración actual ni genera recomendación/alergia.
- **Antecedentes:** personales/familiares/otros, persona relacionada obligatoria en familia, incertidumbre y ninguna condición derivada.
- **E22/E23:** versiones antiguas, duplicados concurrentes, respuesta perdida, permiso retirado y objeto ajeno en lecturas, resultados, errores, capturas y deltas.
- **E24:** hechos anteriores a la ventana de citas; grupos invisibles, cambio de época, cursor/recibo vencido y retención técnica sin borrado funcional.
- **Integridad:** FK de cuenta/paciente/cita/atención, historias inmutables, timeline coincidente/reconstruible, backfill idempotente y rollback de efecto/historia/timeline/recibo/auditoría/grupo.

Dominio/aplicación no usan red. Integridad, migraciones, idempotencia concurrente y carreras usan PostgreSQL Test 18.3 y Keycloak Test aislados, con bases aleatorias eliminadas al terminar. SQLite no acredita esas reglas. No se declara integración Rust/Hub, operación con datos reales ni producción.

## Criterios clínicos de la primera especialidad · odontograma (T22)

Casos de la primera especialidad (odontología), preparados en T22 el 2026-11-18 sin ejecutarse: pieza FDI inválida (quadrante/diente fuera de rango o temporal con diente 6–8) rechazada por SQL; superficie fuera del conjunto cerrado rechazada; hallazgo duplicado vigente en misma pieza/superficie/tipo rechazado; resolver hallazgo conserva historia; actuación `planned`→`performed` con fecha y vínculo al hallazgo; cambio de plantilla no altera odontograma ni inventa hallazgos; usuario sin `specialty_templates read` no obtiene piezas, hallazgos ni evolución.

## Verificación de fuentes OMS · T28 (2026-11-18)

Fuentes oficiales comprobadas con enlaces y fixtures reproducibles:

| Referencia | Ámbito | Fuente oficial | Fixtures verificados |
|---|---|---|---|
| Patrones OMS 2006 | Peso/edad 0–60 meses | [Tabla LMS niños (z)](https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-age/wfa-boys-0-5-zscores.pdf?sfvrsn=be07c977_11), [tabla de campo simplificada](https://cdn.who.int/media/docs/default-source/child-growth/child-growth-standards/indicators/weight-for-age/sft-wfa-boys-z-0-5.pdf?sfvrsn=c735bc54_11) | Niños mes 0: L=0.3487, M=3.3464 kg, S=0.14602; mes 5: L=0.1395, M=7.5105 kg, S=0.11080; medianas de campo: 3.3 kg (mes 0), 4.5 kg (mes 1) |
| Referencia OMS 2007 | Talla/edad e IMC/edad 61–228 meses; peso/edad solo 5–10 años | [Referencia 5–19 años](https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators) | Pendiente de incorporación de tabla (límite registrado en todo.md) |

Método: parámetros LMS (z = ((valor/M)^L − 1)/(L·S); z = ln(valor/M)/S si L=0), conforme a [WHO Child Growth Standards: methods and development, 2006](https://www.who.int/publications/i/item/924154693X). Las publicaciones OMS se distribuyen con fines de salud pública; la incorporación completa del dataset queda registrada como límite hasta su descarga y huella. No se extrapola fuera de rango y no hay diagnóstico.

## Criterios clínicos de etapa 3 · línea base T01

Casos de [P-20261117-05-clinical-stage-3](../tasks/P-20261117-05-clinical-stage-3/plan.md), preparados en T01 el 2026-11-17 sin ejecutarse. Usan datos ficticios y distinguen medicación declarada de prescripción, actividad de objetivo, informe original de resultado estructurado, plantilla de hecho clínico y referencia OMS de diagnóstico. La línea base y la trazabilidad caso→tarea figuran en [plan.md §1.1](../tasks/P-20261117-05-clinical-stage-3/plan.md).

- **E15:** medicamento indicado por otro médico consta como uso declarado sin receta propia; fuente, periodo, precisión e incertidumbre explícitos; sin inferir consumo/adherencia.
- **E17:** plan con objetivos/acciones/revisiones; completar actividad no equivale a lograr objetivo; cierre/suspensión/sustitución con historia.
- **E18:** informe corregido conserva original y resultados vigentes sin puntos duplicados; adjuntos privados en S3 con metadatos/huella en PostgreSQL y descarga reautorizada; subir PDF no acredita extracción.
- **E19:** cambio de plantilla conserva significado/versión de registros previos; sin hechos normales ni respuestas por defecto.
- **E20/E21:** referencia OMS solo dentro de rango con indicador/método/versión; fuera de rango explica el límite; cambio de nacimiento/entrada recalcula o invalida derivados con versiones identificables.
- **Comunes (E03/E09/E22/E23/E24):** series solo con datos válidos; correcciones no duplican puntos; permisos, respuesta perdida y retención técnica sin borrado funcional ni filtrado por sync.

Dominio/aplicación sin red; integridad, migraciones, idempotencia concurrente y carreras exigen PostgreSQL Test aislado. Autorización sigue In progress: las pruebas de permisos de estos bloques reutilizan el mecanismo vigente de Etapas 1/2 hasta su cierre.

## Evidencia clínica de Etapa 2 · T25/C08

Los casos E06–E14 y E22–E24 están comprobados en el servidor mediante suite, persistencia y probes HTTP reales. Los siete tipos aparecen en timeline con filtros autorizados; captura/delta conservan hechos históricos, correcciones y anulaciones. Integración con consumidores, operación con datos reales y producción siguen pendientes.

## Evidencia de suscripciones de cuenta · P-20261117-02 (2026-11-26/27)

El componente `subscriptions` se comprobó con datos ficticios y servicios Test aislados. Criterios verificados de la especificación §24:

- **Catálogo y dinero (24.1):** los tres planes comparten funciones y difieren solo en precio/asientos (D21); cambiar un precio crea versión y no altera historia; USD×BCV con `Decimal` y redondeo único `ROUND_HALF_UP`; tasa/fecha/fuente congeladas en la aprobación; los informes no revalorizan.
- **Periodos (24.2):** 30 días no es mes calendario; año civil con 29-feb→28-feb; renovación anticipada sin perder días y tardía en la aprobación (D22); no solape por exclusión `tstzrange`; repetir aprobación no añade días (PK de revisión + UQ de origen).
- **Reportes (24.3):** presentar no activa; aprobar activa/extiende una vez; rechazar conserva el estado anterior; declarados y verificados separados; `referenceLast4` texto con ceros y sin unicidad; nueva presentación vinculada sin borrar historia.
- **Asientos (24.4):** regla D21 sobre pertenencias activas; dispositivos/invitaciones/pacientes no cuentan; dos aceptaciones concurrentes por la última plaza tienen un solo ganador (prueba con dos conexiones); la reducción de plan no desactiva a nadie.
- **Seguridad (24.5):** sin acceso a reportes/evidencias ajenos (404); el operador no accede a clínica (sin pertenencia ni rol); archivos validan firma real, tamaño y almacenamiento privado; la descarga reautoriza; ninguna captura en journal, logs, sync ni métricas (escaneo SQL en el probe).
- **Offline (24.6):** el reloj del cliente no extiende vigencia (proyección con `endsAt`/`graceEndsAt` del servidor); una aprobación desconocida se recupera por captura sin duplicarla; la suspensión no borra datos ni intenciones. La experiencia del escritorio requiere pruebas en su repositorio.

Comandos de cierre y resultados en la evidencia de T28 del plan. Límites: sin banco ni BCV en vivo, sin operador en producción, sin integración Rust/Hub acreditada, sin datos reales ni despliegue; el enforcement de cuentas nunca pagadas queda como decisión de producto pendiente.
