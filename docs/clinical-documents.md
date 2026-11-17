# Especificación del componente de récipes y órdenes de diagnóstico

**Versión:** 0.1\
**Fecha:** 2026-11-17\
**Estado:** Aprobada por el usuario el 2026-11-17 como referencia funcional. No autoriza implementación, migraciones, generación de PDF, almacenamiento ni cambios de contrato.\
**Ámbito:** documentos clínicos imprimibles emitidos por un profesional y consulta privada posterior.\
**Documentos relacionados:** [registro clínico](patient-clinical-record.md), [autorización RBAC/ABAC](authorization-rbac-abac.md), [facturación de pacientes](patient-billing.md), [decisiones](decisions.md), [arquitectura](architecture.md), [diseño de acceso](access-design.md), [contrato HTTP v1](api-v1.md) y [esquema físico](database-schema.md).

## 1. Propósito

Este documento define dos tipos de documentos clínicos:

- **Récipe o prescripción:** medicamentos e indicaciones preparados y emitidos por el médico.
- **Orden de diagnóstico:** exámenes solicitados, motivo/diagnóstico e indicaciones.

Ambos se presentan como documentos imprimibles con un espacio para que el médico firme a mano después de imprimirlos. API conserva los datos emitidos, la historia y el archivo necesario para consultarlos nuevamente.

Si se crean desde una cita, quedan vinculados automáticamente a ella. El paciente puede consultar el documento permitido desde el enlace privado que recibe, sin obtener acceso general a la historia clínica.

### 1.1 Resultado esperado

El profesional debe poder preparar, emitir, imprimir, sustituir y anular documentos con trazabilidad. El paciente debe poder consultar una copia autorizada. Una corrección no debe reescribir el contenido ya emitido, y un fallo del PDF no debe crear otro número ni repetir la emisión clínica.

## 2. Decisiones confirmadas en el encargo

| ID | Decisión | Consecuencia |
|---|---|---|
| `CD-D01` | El componente incluye récipes y órdenes de laboratorio/diagnóstico | Comparte infraestructura documental, pero conserva contenido clínico tipado |
| `CD-D02` | La presentación sigue el estilo de las imágenes aportadas | Encabezado, profesional, paciente, contenido, número, fecha, QR y espacio de firma |
| `CD-D03` | El médico firma a mano después de imprimir | No se implementa firma digital ni se dibuja una firma como sustituto |
| `CD-D04` | API conserva los datos para volver a consultar | El documento no existe solo como PDF temporal |
| `CD-D05` | El documento se adjunta automáticamente a la cita desde la que se genera | La relación se conserva sin copiar contenido clínico a `appointment_histories` |
| `CD-D06` | El paciente puede consultarlo desde el enlace enviado | Se amplía el acceso limitado del Hub con lectura/descarga de documentos autorizados |
| `CD-D07` | El récipe tiene copia para farmacia y copia con posología para el paciente | La plantilla diferencia el contenido visible de cada copia |
| `CD-D08` | La orden incluye diagnóstico/motivo, exámenes e indicaciones | No se reduce a una lista de exámenes sin contexto |

No se ha decidido un catálogo farmacológico, envío a farmacias/laboratorios, validez jurídica automática, campos profesionales obligatorios ni emisión offline.

## 3. Alcance y exclusiones

### 3.1 Incluye

- Borradores y edición con versiones.
- Emisión profesional e instantánea inmutable.
- Numeración legible por tipo.
- Récipes con uno o varios medicamentos.
- Órdenes con uno o varios exámenes.
- Encabezado y datos profesionales/paciente.
- Plantillas versionadas y paginación.
- Línea para firma y sello manuscritos.
- PDF privado y recuperación del archivo.
- Sustitución y anulación.
- Vínculos con paciente, cita y atención.
- Entrada de referencia en el historial clínico.
- Acceso limitado del paciente.
- QR para verificación mínima y estado.
- Permisos, sincronización, offline, auditoría y concurrencia.

### 3.2 Excluye

- Firma electrónica, certificados, sellos de tiempo o custodia de claves.
- Escaneo o reconocimiento de la firma manuscrita.
- Envío electrónico a farmacias o redes de prescripción.
- Dispensación, entrega o administración del medicamento.
- Recomendación automática de medicamentos, dosis o interacciones.
- Conversión de la receta en medicación declarada/consumida.
- Transmisión a laboratorios, agenda de muestras o seguimiento de cumplimiento.
- Resultados de laboratorio o informes diagnósticos.
- Cierre o firma universal de atenciones y notas.
- Facturación automática por emitir un documento.
- Validez legal garantizada para todo país, especialidad o medicamento.
- Tablas, rutas, biblioteca PDF o proveedor de almacenamiento aprobados por este documento.

[database-schema.md](database-schema.md) conserva la única fuente física. [api-v1.md](api-v1.md) conserva el contrato actual. FHIR se usa como referencia conceptual, sin declarar conformidad o intercambio FHIR.

## 4. Relación con el modelo clínico actual

### 4.1 Prescripción prevista

[patient-clinical-record.md](patient-clinical-record.md) ya distingue:

- Medicación declarada.
- Prescripción.
- Dispensación/administración.
- Preparación, emisión, sustitución y anulación.

Esta especificación concreta la prescripción imprimible y añade la orden de diagnóstico como solicitud, no como informe de resultados.

### 4.2 Citas y atenciones

- Una cita es un compromiso.
- Una atención afirma que ocurrió y puede existir sin cita.
- Una cita admite varias atenciones.
- Registrar un documento no cierra la atención ni cambia la cita.
- La última visita se deriva de atenciones válidas, no de documentos.

El documento pertenece al paciente/cuenta. Cita y atención aportan contexto, pero no son el lugar para duplicar medicamentos o exámenes.

### 4.3 Datos profesionales y del paciente

El perfil profesional actual conserva esencialmente `publicName`, usuario, estado y versión. Las plantillas necesitan además especialidad y registros profesionales cuando correspondan.

El paciente puede tener nombre, nacimiento, documentos y sexo al nacer opcionales en distintos estados de captura. La plantilla no debe:

- Inventar documento o nacimiento.
- Deducir sexo del nombre.
- Convertir una edad declarada en fecha exacta.
- Mostrar un dato actual distinto del que se usó al emitir.

### 4.4 Componente propietario

Se propone `clinical_documents` como propietario de contenido, emisión, historia, artefactos y relaciones documentales.

| Componente | Dependencia permitida |
|---|---|
| `patients` | Datos y ámbito de ficha mediante casos/tipos |
| `accounts` | Contexto, profesional, permisos y datos del encabezado |
| `appointments` | Validación de cita y vínculo, sin recibir cuerpos clínicos |
| `encounters` | Validación de atención y profesional responsable |
| `clinical_records` | Entrada de referencia en timeline e historial, sin duplicar contenido |
| `sync` | Recibo, cambios, capturas y recuperación |
| `audit` | Evidencia mínima de emisión, lectura y descarga |

No se importan repositorios ajenos ni se escribe en tablas de citas/atenciones.

## 5. Conceptos

| Concepto | Definición |
|---|---|
| **Borrador** | Contenido editable que todavía no se ha emitido. |
| **Emisión** | Decisión profesional que fija contenido, número, autor e instante. |
| **Instantánea** | Copia histórica de los datos mostrados en el documento. |
| **Artefacto** | Archivo PDF u otra representación generada desde una emisión. |
| **Plantilla** | Regla versionada de presentación; no decide el contenido clínico. |
| **Firma manuscrita** | Marca realizada por el médico sobre el papel impreso. |
| **Sustitución** | Nuevo documento que reemplaza uno emitido, conservando ambos. |
| **Anulación** | Declaración de que un documento emitido ya no debe usarse. |
| **Concesión del paciente** | Acceso limitado a lectura/descarga de un documento autorizado. |
| **Verificación QR** | Consulta mínima de identidad y estado del documento, no acceso clínico completo. |

Emitir en API no demuestra que el médico firmó el papel. Tener un PDF no demuestra dispensación, realización del examen o consumo.

## 6. Actores

### 6.1 Profesional emisor

Debe:

- Tener identidad de usuario activa.
- Estar vinculado como profesional activo a la cuenta.
- Poseer la acción de emisión del tipo de documento.
- Ser el profesional responsable exigido por la atención cuando esa regla aplique.

Ser propietario sin relación profesional no basta. Un médico de otra cuenta no emite en esta solo por compartir identidad global.

### 6.2 Asistente

Si se aprueba, puede preparar o corregir borradores con permiso explícito. No emite, sustituye ni anula como si fuera el médico.

El autor del borrador y el profesional emisor se conservan por separado. El sistema no atribuye al asistente una decisión clínica que no tomó.

### 6.3 Propietario

Puede consultar y administrar accesos según permisos. No obtiene capacidad de emitir por propiedad si no es el profesional autorizado.

### 6.4 Paciente

Puede leer y descargar documentos emitidos cubiertos por su concesión. No edita, emite, anula, sustituye ni administra accesos de otras personas.

### 6.5 Farmacia, laboratorio o público

No reciben cuentas ni acceso directo a API. La copia impresa se entrega fuera del sistema. El QR ofrece solo la verificación mínima aprobada, no una sesión de farmacia/laboratorio.

## 7. Modelo común del documento

Todo documento conserva conceptualmente:

- Identificador estable.
- Cuenta y paciente.
- Tipo `prescription` o `diagnostic_order`.
- Número legible, una vez emitido.
- Cita opcional.
- Atención opcional.
- Profesional emisor y usuario autenticado.
- Autor del borrador si difiere.
- Estado, versión e historia.
- Instantáneas de encabezado, profesional y paciente.
- Contenido tipado.
- `createdAt`, `issuedAt`, `updatedAt` cuando proceda.
- Documento sustituido/sustituto cuando exista.
- Motivo de anulación/corrección permitido.
- Versión de plantilla y artefactos asociados.

Cuenta, paciente y tipo no cambian después de crear el documento. Un error de ámbito se resuelve anulando/descartando según estado y creando otro, no reasignando silenciosamente.

## 8. Instantáneas y datos de emisión

### 8.1 Encabezado de la cuenta

La emisión puede conservar:

- Nombre del consultorio/centro.
- Dirección y localidad.
- Datos de contacto destinados al documento, si se aprueban.
- Identificadores administrativos del encabezado solo cuando exista una necesidad aprobada.

Cambiar la cuenta después no reescribe el encabezado antiguo.

### 8.2 Profesional

Campos soportados:

- Nombre público/profesional.
- Documento profesional o personal permitido.
- Especialidad.
- Registro MPPS cuando aplique.
- Número de colegiatura cuando aplique.
- Otros registros explícitos que exija la normativa aprobada.

El modelo actual no contiene todos estos datos; deberá ampliarse mediante una decisión física y contractual propia. No se acepta texto libre del cliente para afirmar que un registro está verificado.

### 8.3 Paciente

Campos soportados:

- Nombre.
- Fecha de nacimiento.
- Documento seleccionado, con país/tipo cuando proceda.
- Sexo al nacer, conservando su significado.
- Edad derivada solo si se muestra y puede calcularse.

Si el paciente tiene varios documentos, el emisor selecciona uno o aplica una regla explícita. No se concatenan todos ni se escoge otro después al reimprimir.

### 8.4 Datos ausentes

Propuesta:

- Nombre del paciente es obligatorio para emitir.
- Nombre del profesional y vínculo profesional activo son obligatorios.
- Nacimiento, documento y sexo pueden mostrarse como “No registrado” cuando falten, salvo una exigencia normativa aprobada.
- No se usan ceros, fechas ficticias, `unknown` como si fuera un valor clínico conocido o cadenas vacías invisibles.

Los campos profesionales mínimos y los datos obligatorios del paciente se cierran en `CD-O02`.

### 8.5 Fecha de emisión

`issuedAt` procede del servidor. La fecha civil visible se calcula en la zona de la cuenta, inicialmente `America/Caracas`, y se conserva como instantánea junto con la zona. La fecha del dispositivo no retrocede ni adelanta la emisión.

## 9. Contenido del récipe

### 9.1 Conjunto de medicamentos

Un récipe contiene al menos un medicamento. Cada elemento tiene orden visual estable y conserva:

| Campo | Regla propuesta |
|---|---|
| Medicamento o principio activo | Texto obligatorio |
| Concentración | Texto/valor permitido cuando corresponda |
| Forma farmacéutica | Opcional |
| Dosis e instrucción de uso | Obligatoria para la copia del paciente |
| Vía | Opcional o estructurada si se define |
| Frecuencia | Opcional si ya queda inequívoca en posología |
| Duración | Opcional |
| Cantidad | Opcional, si se decide incluirla |
| Instrucciones particulares | Opcional |

No se exige un catálogo externo para guardar texto clínico. Los campos estructurados y el texto mostrado deben ser coherentes; no se calcula una dosis ni se completa una frecuencia por inferencia.

### 9.2 Indicaciones generales

El médico puede añadir indicaciones generales y observaciones relevantes. No se generan automáticamente desde diagnósticos, alergias o mediciones.

### 9.3 Copia para farmacia

La copia mostrada en la imagen se centra en:

- Identidad del documento, profesional y paciente.
- Medicamentos, concentración/forma y cantidad cuando corresponda.
- Número, fecha, QR y espacio de firma.

No repite necesariamente toda la posología del paciente. La composición exacta debe aprobarse con la plantilla y normativa aplicable.

### 9.4 Copia para el paciente

Incluye:

- Los mismos datos de identidad del documento.
- Medicamentos.
- Posología completa, duración e instrucciones.
- Indicaciones generales.
- Número, fecha, QR y espacio de firma.

Ambas copias pertenecen a una misma emisión y comparten número. No son dos recetas independientes.

### 9.5 Lo que no se deriva

Emitir no:

- Añade medicación declarada.
- Afirma consumo o adherencia.
- Registra dispensación.
- Crea una condición/diagnóstico.
- Comprueba interacciones o contraindicaciones.
- Reserva inventario de farmacia.

## 10. Contenido de la orden de diagnóstico

### 10.1 Motivo o diagnóstico

La orden conserva un motivo/diagnóstico redactado por el profesional. Puede relacionarse conceptualmente con información de la atención, pero no copia automáticamente todo `assessment`.

El texto impreso es una instantánea. Corregir una nota después no cambia la orden.

### 10.2 Exámenes

Debe existir al menos un examen. Cada entrada conserva:

- Orden visual.
- Nombre del examen/estudio.
- Nota o indicación particular opcional.
- Código de catálogo solo si en el futuro se adopta uno; no necesario para el texto inicial.

No se inventan valores, unidades, ayuno, preparación o prioridad por el nombre del examen.

### 10.3 Indicaciones generales

El médico puede registrar preparación, ayuno u otras instrucciones como texto. Nightingale no valida automáticamente su corrección clínica ni las genera sin alcance propio.

### 10.4 Sin cumplimiento

La orden no contiene estados de laboratorio como recibida, procesada o completada. Emitirla no crea:

- Cita con laboratorio.
- Muestra.
- Resultado.
- Informe diagnóstico.
- Cargo de facturación.

Esas funciones requieren componentes y relaciones propios.

## 11. Borradores y validación

### 11.1 Creación

Un borrador exige cuenta, paciente, tipo y autor autorizado. Puede crearse desde cita/atención, lo que propone sus vínculos.

Los UUID nuevos pueden proceder del cliente para trabajo offline si el contrato lo admite. El número legible no se asigna todavía.

### 11.2 Edición

- Usa versión esperada.
- Ausencia conserva y `null` borra solo campos anulables.
- Un cambio sin diferencia devuelve `NO_CHANGES` sin nueva versión.
- Los elementos conservan identidad/orden para evitar duplicados al editar.
- No se cambia cuenta/paciente/tipo mediante patch.
- Un borrador no aparece como documento emitido al paciente.

### 11.3 Validación combinada

Antes de emitir se valida el documento completo:

- Vínculos y ámbito.
- Permisos y relación profesional.
- Datos mínimos de instantánea.
- Al menos un medicamento o examen.
- Campos obligatorios por tipo.
- Coherencia de posología y textos mostrados.
- Versión actual del borrador.

Guardar un borrador incompleto puede ser válido; emitirlo no.

## 12. Emisión y numeración

### 12.1 Acción explícita

El médico revisa y ejecuta una acción de emisión. No se emite por:

- Guardar borrador.
- Completar cita.
- Cerrar atención.
- Imprimir una vista previa.
- Descargar un borrador.

### 12.2 Efectos atómicos

La aceptación de emisión conserva juntos:

- Estado `issued`.
- Número legible único.
- Instantáneas y contenido.
- Profesional/usuario emisor e instante.
- Historia.
- Vínculos con cita/atención.
- Entrada de timeline cuando corresponda.
- Auditoría, recibo y cambios de sincronización.
- Intención duradera para generar el artefacto.

No incluye llamadas de red ni generación externa dentro de la transacción PostgreSQL.

### 12.3 Numeración

Propuesta:

- Prefijo `REC` para récipes.
- Prefijo `ORD` para órdenes.
- Secuencia independiente por cuenta y tipo.
- Representación con ceros para presentación, sin convertir el número en un entero que pierda formato.
- Asignación en emisión, no en borrador.
- Unicidad protegida en PostgreSQL.
- Números anulados/sustituidos no se reutilizan.
- Se admiten huecos técnicos; no se promete una secuencia fiscal sin huecos.

El formato exacto se cierra en `CD-O04`. El número no es secreto ni concede acceso.

### 12.4 Idempotencia

Repetir la misma emisión recupera el mismo documento y número. Dos peticiones con distinta identidad no deben crear duplicados por una respuesta perdida; el consumidor conserva `operationId`.

## 13. Presentación imprimible

### 13.1 Récipe

La plantilla reproduce la intención de las imágenes:

- Encabezado del consultorio.
- Número y fecha.
- Datos del médico y paciente.
- Dos copias en una hoja cuando el contenido cabe de forma legible.
- Copia farmacia y copia paciente claramente identificadas.
- Posología solo en las copias que correspondan.
- Indicaciones generales.
- Línea para firma y nombre/registro del médico.
- QR y referencia de verificación.

### 13.2 Orden

- Encabezado, número y fecha.
- Médico y paciente.
- Diagnóstico/motivo.
- Tabla de exámenes con nota/indicación.
- Indicaciones generales.
- Línea para firma y nombre/registro.
- QR y referencia de verificación.

### 13.3 Paginación y desbordamiento

No se trunca contenido para conservar una página:

- Un elemento no se corta de forma que separe medicamento de su posología sin indicación clara.
- Las páginas adicionales repiten identificación mínima y número.
- Se indica paginación de forma no ambigua.
- Las dos copias pueden ocupar páginas enfrentadas o adicionales si el contenido no cabe.
- El QR y firma se mantienen en cada copia exigida por la plantilla.

### 13.4 Versión de plantilla

Cada artefacto registra plantilla y versión. Cambiar estilos, textos fijos o disposición no modifica documentos emitidos ni altera su contenido clínico.

La vista previa del borrador no es una copia emitida y debe identificarse como tal.

## 14. Firma manuscrita y significado

El documento impreso deja un espacio en blanco para firma y, si se desea, sello.

API acredita:

- Qué usuario/profesional emitió.
- Qué contenido se emitió.
- Cuándo se aceptó la emisión.
- Estado actual: vigente, sustituido o anulado.
- Integridad/historia del archivo conservado.

API no acredita:

- Que el médico firmó físicamente.
- Que una marca impresa es auténtica.
- Que una copia escaneada corresponde al original firmado.
- Firma digital, certificado o no repudio jurídico.

No se inserta una imagen de firma por defecto. La revisión jurídica de requisitos venezolanos queda en `CD-O01`.

## 15. Generación y almacenamiento del PDF

### 15.1 Separación de estados

El estado clínico y el artefacto son independientes:

```text
Documento: draft | issued | superseded | annulled
Artefacto: pending | ready | failed
```

Un documento puede estar emitido con PDF pendiente o fallido. Esto no permite repetir la emisión ni asignar otro número.

### 15.2 Trabajo posterior al commit

La emisión deja una intención duradera. Un worker:

1. Lee la instantánea y plantilla versionada.
2. Genera el PDF.
3. Valida tipo/tamaño y contenido básico.
4. Guarda el archivo privado.
5. Registra artefacto, huella, versión y resultado.

Si falla, reintenta el mismo artefacto/documento sin duplicar la emisión. El dato clínico permanece consultable aunque el archivo esté pendiente.

### 15.3 Conservación

El artefacto listo conserva:

- Documento y emisión de origen.
- Tipo MIME y tamaño.
- Huella.
- Plantilla/versión.
- Fecha de generación.
- Clave privada de almacenamiento.
- Estado.

No se expone una URL pública permanente. Cambiar plantilla no reemplaza silenciosamente el PDF antiguo.

### 15.4 Descarga

La descarga reautoriza y devuelve el artefacto permitido. No se incluyen bytes en `change_log`, snapshots, auditoría o logs. Una URL temporal, si se usa, no es una concesión transferible indefinida.

## 16. Sustitución, anulación e historia

### 16.1 Documento emitido inmutable

El contenido clínico y las instantáneas de una emisión no se editan. Reimprimir no crea versión clínica ni cambia número.

### 16.2 Sustitución

Para corregir un documento emitido:

1. Se crea otro documento basado en el anterior.
2. Conserva `replacesDocumentId`.
3. Se revisa como borrador o mediante el recorrido aprobado.
4. Al emitirlo recibe nuevo ID y número.
5. El anterior pasa a `superseded` y referencia el sustituto.

Ambos quedan consultables. No se copia una emisión como si fuera consumo o cumplimiento.

### 16.3 Anulación

Anular:

- Exige profesional/acción autorizada y versión.
- Conserva motivo, actor e instante.
- Impide presentar el documento como vigente.
- No borra PDF, datos o historia.
- No elimina copias impresas o descargadas.
- No revierte automáticamente otra entidad clínica.

La anulación es terminal salvo una corrección administrativa explícita; no se reabre el mismo documento.

### 16.4 Sustitución frente a anulación

- Sustituir comunica cuál es el documento posterior.
- Anular declara que no debe usarse y no exige sustituto.
- Un documento sustituido puede conservar valor histórico, pero no es la versión vigente.

### 16.5 Historia

La historia conserva creación, cambios de borrador, emisión, sustitución y anulación. No se reescriben versiones para reflejar datos actuales del paciente o profesional.

## 17. Vínculos con cita, atención e historial

### 17.1 Vínculo automático desde cita

Si el recorrido comienza en una cita, el documento conserva su `appointmentId` al crearlo. La emisión vuelve a comprobar cuenta, paciente y vínculo.

Una cita puede tener varios récipes/órdenes. No hay unicidad por cita.

### 17.2 Atención opcional

Si se vincula atención:

- Debe pertenecer a la misma cuenta/paciente.
- Si también hay cita, debe ser coherente con ella.
- El profesional emisor debe cumplir la regla de responsable definida para esa atención.

Una atención sin cita permite emitir sin crear una cita ficticia.

### 17.3 Cambios posteriores de la cita

Reprogramar no cambia el contenido ni el vínculo histórico. Cancelar/marcar ausencia no anula automáticamente el documento. Si el vínculo fue erróneo, se corrige mediante el ciclo documental aprobado, no reasignación silenciosa.

### 17.4 Timeline clínico

Los documentos emitidos añaden una referencia al timeline:

- Tipo, ID, cuenta/paciente.
- Fecha de emisión.
- Estado y versión.
- Sección/audiencia de origen.

No incluye medicamentos, exámenes, posología o PDF en la entrada. Borradores no forman parte del historial clínico emitido. Los detalles vuelven a autorizar.

### 17.5 Sin efectos colaterales

El documento no cambia:

- Estado de cita.
- Última visita.
- Condiciones o alergias.
- Medicación declarada.
- Resultados de laboratorio.
- Cargos de facturación.

## 18. Acceso del paciente desde el enlace

### 18.1 Ampliación de D11/D16

El acceso limitado de cita se amplía para:

- Consultar metadatos permitidos del documento emitido.
- Leer el contenido necesario de la copia del paciente.
- Descargar el PDF.
- Conocer si está vigente, sustituido o anulado.

No incluye borradores, notas internas, otros documentos o historia clínica completa.

### 18.2 Concesión

La concesión se limita a:

- Cuenta, paciente y cita.
- Documento o serie documental explícita.
- Acciones `read`/`download` según contrato.
- Vigencia y revocación.
- Proyección permitida.

Poseer el UUID, número o QR no basta para leer el contenido completo.

### 18.3 Sustituciones

Un acceso al documento original no abre automáticamente cualquier documento del paciente. Propuesta: el sustituto hereda la concesión solo si conserva cuenta, paciente y cita, y la política la extiende expresamente a esa serie. En otro caso requiere una nueva concesión.

El paciente debe ver el estado del original y la relación permitida con su sustituto.

### 18.4 Revocación

Revocar impide nuevas lecturas/descargas después del orden de revocación. No borra copias descargadas ni retira el papel. El documento y su estado permanecen para el personal autorizado.

### 18.5 Sin cuenta general

Esta función no exige crear una cuenta global de paciente ni inicio de sesión del personal. El micrositio público no publica récipes u órdenes.

## 19. QR y verificación

### 19.1 Finalidad

El QR ayuda a comprobar que número, emisión y estado corresponden a un documento registrado. No prueba la autenticidad de la firma manuscrita ni la identidad de quien presenta el papel.

### 19.2 Separación del enlace privado

Propuesta recomendada:

- El QR abre una verificación mínima.
- El enlace privado del paciente abre el contenido autorizado.
- Son mecanismos y secretos distintos.

El QR no debe contener directamente el token que descarga todo el documento.

### 19.3 Proyección de verificación

Como máximo, y sujeto a aprobación:

- Tipo y número.
- Consultorio/profesional destinado a publicación en el documento.
- Fecha de emisión.
- Estado vigente/sustituido/anulado.
- Relación con sustituto cuando sea necesaria.

No muestra nombre del paciente, documento de identidad, medicamentos, posología, diagnóstico, exámenes o indicaciones.

### 19.4 Documento inexistente

La respuesta pública no revela información adicional de otras cuentas. La política antienumeración y límites de frecuencia se definen antes de habilitar verificación pública.

## 20. Autorización

### 20.1 Acciones separadas

El catálogo debe distinguir:

- Leer récipes/órdenes.
- Crear/editar borradores.
- Emitir récipe.
- Emitir orden.
- Sustituir.
- Anular.
- Descargar artefacto.
- Administrar concesión del paciente.
- Consultar verificación pública mínima.

Leer notas o atenciones no abre documentos por herencia. Revisar pagos no concede acceso clínico.

### 20.2 Emisión profesional

La emisión exige atributos adicionales al permiso:

- Profesional activo en la cuenta.
- Usuario autenticado ligado a ese profesional.
- Paciente/cita/atención de la misma cuenta.
- Relación con el profesional a cargo cuando aplique.
- Versión actual del borrador.

Un asistente con permiso de borrador no satisface estos atributos por tener `read_write` en otra sección.

### 20.3 Valores iniciales

Los permisos para asistentes existentes/nuevos se deciden en `CD-O03`. No se copia automáticamente el actual `read_write` de notas a emisión o anulación.

### 20.4 No divulgación

Un objeto ajeno o inexistente devuelve la misma ausencia pública para personal. Para paciente, una concesión inválida no revela existencia. Autorización precede a detalles, totales, historias, resultados y descargas.

## 21. Sincronización y offline

### 21.1 Audiencias

Se proponen audiencias documentales cerradas, separadas de notas y demás secciones. Pueden ser comunes para lectura y distintas para emisión según el diseño de permisos.

Solo se sincronizan documentos y metadatos autorizados. Los PDF no se serializan en el journal; se sincroniza una referencia descargable y su estado.

### 21.2 Timeline y filtrado

- Autorización antes de contar/paginar.
- Una entrada de timeline invisible no entrega contenido.
- Cambiar permisos invalida capturas/cursores afectados.
- Grupos invisibles permiten avanzar sin cuerpos.
- Una concesión del paciente no forma parte de la sincronización del personal.

### 21.3 Borradores offline

El escritorio puede preparar borradores localmente si el contrato lo admite. Al sincronizar:

- API revalida permiso, profesional, paciente y versión.
- Un rechazo conserva la intención local.
- La fecha local no prueba autorización anterior.

### 21.4 Emisión online propuesta

La primera versión propone emisión online para coordinar:

- Permiso vigente.
- Número único.
- Historia compartida.
- Acceso del paciente.
- Artefacto durable.

Permitir emisión offline exigiría otra solución para numeración, conflictos y validez; queda en `CD-O07` y no se deduce del borrador offline.

### 21.5 Impresión local

Un artefacto ya descargado y autorizado puede imprimirse sin red. Esto no demuestra que el documento siga vigente. La verificación de estado requiere conexión.

## 22. Modelo conceptual de datos

Sin definir tablas físicas:

| Entidad conceptual | Responsabilidad |
|---|---|
| `clinical_documents` | Cabecera común, ámbito, estado, versión y relaciones |
| `prescription_items` | Medicamentos e instrucciones tipadas |
| `diagnostic_order_items` | Exámenes y notas tipadas |
| `document_snapshots` | Contenido e instantáneas inmutables de cada emisión |
| `document_histories` | Creación, cambios, emisión, sustitución y anulación |
| `document_artifacts` | PDF, plantilla, huella, estado y almacenamiento |
| `document_number_sequences` | Coordinación por cuenta/tipo |
| `document_patient_grants` | Concesión privada futura, si no se reutiliza otra entidad del Hub |

Reglas conceptuales:

- Cuenta/paciente/tipo son estables.
- Toda referencia respeta la misma cuenta y paciente.
- Cada emisión tiene contenido inmutable y número único.
- Una sustitución referencia otra emisión, no un borrador ambiguo.
- Un artefacto referencia una sola emisión y plantilla.
- Los elementos tienen orden estable.
- No se usa un JSON libre para mezclar récipe y orden sin tipos propios.
- Historias y anulaciones no se borran al cambiar datos del paciente/profesional.

El diseño físico se incorporará solo a [database-schema.md](database-schema.md) cuando se revise.

## 23. Casos de uso y contratos futuros

### 23.1 Personal

- Crear/editar/consultar borrador.
- Consultar vista previa identificada como borrador.
- Emitir récipe u orden.
- Consultar documento actual/historia.
- Generar/recuperar/descargar PDF.
- Sustituir documento.
- Anular documento.
- Consultar documentos de paciente/cita/atención.
- Administrar acceso del paciente si posee permiso.

### 23.2 Paciente

- Consultar documento permitido.
- Consultar estado y sustituto autorizado.
- Descargar PDF.
- Recuperar una lectura tras fallo sin crear acciones clínicas.

### 23.3 Verificación

- Consultar estado mínimo mediante QR.
- No descargar contenido clínico por esa vía.

### 23.4 Transporte

Escrituras tipadas con `operationId`, versión esperada, idempotencia, resultado recuperable y auditoría. Lecturas con autorización antes de total/página. Nombres HTTP y esquemas JSON no se fijan aquí.

## 24. Auditoría, privacidad y retención

### 24.1 Evidencia

Registrar:

- Cuenta, paciente/objeto permitido.
- Actor, dispositivo o concesión del paciente.
- Acción, resultado, versión y correlación.
- Profesional emisor.
- Instante del servidor.
- Número/estado cuando proceda.
- Descarga de artefacto y cambio de concesión.

### 24.2 No registrar en logs/auditoría técnica

- Medicamentos, posología o exámenes.
- Diagnóstico/motivo o indicaciones.
- PDF o bytes.
- URL temporal, token de enlace o secreto QR.
- Contenido completo del payload para depuración.

### 24.3 Lecturas

Las lecturas clínicas, historias, capturas/deltas y descargas dejan evidencia según la política clínica. Si la evidencia obligatoria falla, no se entregan datos.

### 24.4 Retención

Antes de datos reales se define conservación de:

- Borradores.
- Emisiones e historias.
- PDF y copias.
- Concesiones y verificaciones.
- Auditoría y copias de seguridad.

Anular no equivale a eliminar. Suspender una suscripción no borra documentos. No se promete borrado de copias ya impresas o descargadas.

## 25. Fallos, concurrencia y recuperación

| Situación | Resultado exigido |
|---|---|
| Respuesta perdida al emitir | Recuperar misma emisión y número |
| Dos emisiones simultáneas | Números únicos y contenido coherente |
| Edición y emisión concurrentes | Versión vigente decide; no contenido mezclado |
| Sustitución y anulación concurrentes | Orden verificable e historia consistente |
| Cambio de permiso/profesional durante emisión | Coordinación con revocación; sin efecto con acceso viejo |
| PDF falla tras emisión | Documento emitido persiste; reintento sin nuevo número |
| Respuesta de descarga perdida | Reintentar lectura; no nueva emisión |
| Cambio de paciente/profesional después | La instantánea anterior no cambia |
| Cita reprogramada/cancelada | Documento e historia permanecen |
| Paciente abre enlace revocado | Sin lectura; no se revela contenido |
| QR de documento anulado | Muestra estado no vigente, sin contenido clínico |
| Cliente offline al vencer acceso | No extiende permisos ni promete borrado local |

## 26. Criterios verificables

Estos criterios son requisitos futuros, no pruebas ejecutadas por esta entrega.

### 26.1 Contenido

- Récipe exige al menos un medicamento y posología para copia paciente.
- Orden exige motivo/diagnóstico y al menos un examen.
- La copia farmacia/paciente muestra los campos acordados sin omitir posología necesaria.
- Datos ausentes no se inventan.
- Ninguna plantilla añade diagnósticos, ayuno o instrucciones no registradas.

### 26.2 Emisión e historia

- Solo profesional autorizado emite.
- Borrador/vista previa no tiene número emitido ni acceso paciente.
- Repetir emisión conserva número y efecto.
- Instantáneas no cambian al editar perfiles.
- Sustitución conserva original y nuevo.
- Anulación no borra ni reabre.
- Reimpresión no crea versión clínica.

### 26.3 Archivos y plantillas

- Fallo de PDF no repite emisión.
- Artefacto conserva plantilla/versión y huella.
- Contenido largo pagina sin truncar.
- La descarga reautoriza.
- Ningún PDF viaja en journal/logs.

### 26.4 Vínculos

- Documento desde cita queda vinculado automáticamente.
- Cita/atención/paciente/profesional no cruzan cuentas.
- Una cita admite varios documentos.
- Reprogramar/cancelar no altera emisión.
- Timeline contiene referencia sin contenido y no cambia última visita.

### 26.5 Paciente y QR

- Paciente solo lee/descarga su concesión.
- Borrador no es visible.
- Sustituto hereda acceso solo bajo la regla aprobada.
- Revocación impide nuevas lecturas.
- QR no entrega paciente, medicamentos, diagnóstico o exámenes.
- Verificación no afirma firma manuscrita o cumplimiento.

### 26.6 Concurrencia y consumidores

- PostgreSQL real acredita numeración, emisión/revocación y sustitución/anulación.
- La respuesta perdida recupera el mismo resultado.
- Las pruebas de API no acreditan render visual, impresión física, Rust o Hub.
- Las plantillas requieren inspección de PDF renderizado con datos ficticios antes de aceptar presentación.

## 27. Criterios para aceptar esta especificación

- Refleja `CD-D01`–`CD-D08` sin introducir firma digital o redes externas.
- Distingue emisión, firma manuscrita, PDF, impresión y verificación.
- Conserva contenido tipado para récipe y orden.
- Mantiene instantáneas, historia, sustitución y anulación.
- No confunde prescripción con consumo ni orden con resultado.
- Vincula cita/atención sin duplicar contenido en sus historias.
- Limita paciente y QR sin crear cuenta general ni fuga clínica.
- Define concurrencia, recuperación, offline y permisos profesionales.
- No presenta requisitos jurídicos, campos mínimos o emisión offline como resueltos.

## 28. Decisiones pendientes

| ID | Decisión | Momento necesario |
|---|---|---|
| `CD-O01` | Revisión de requisitos venezolanos para récipes/órdenes impresos y registros obligatorios | Antes de uso real |
| `CD-O02` | Campos mínimos de paciente/profesional/cuenta para emitir | Antes de validación de emisión |
| `CD-O03` | Permisos iniciales de asistentes para borradores, lectura, sustitución y anulación | Antes de matriz de acceso |
| `CD-O04` | Formato exacto de numeración, reinicio y huecos | Antes de secuencias |
| `CD-O05` | Campos obligatorios/opcionales de medicamento, posología y cantidad | Antes del contrato de récipe |
| `CD-O06` | Catálogo de exámenes o texto libre inicial y campos de motivo | Antes del contrato de orden |
| `CD-O07` | Confirmar emisión online o diseñar emisión offline | Antes de sincronización de emisión |
| `CD-O08` | Plantillas finales, tamaño de papel, paginación y textos fijos | Antes de aceptar presentación |
| `CD-O09` | Proyección pública del QR y antienumeración | Antes de verificación pública |
| `CD-O10` | Vigencia/revocación del enlace y herencia a sustitutos | Antes del contrato del Hub |
| `CD-O11` | Almacenamiento, retención, copias y eliminación de PDF | Antes de datos reales |
| `CD-O12` | Regla para emitir sobre atención de otro profesional de la cuenta | Antes de validar esa relación |

Estas preguntas no impiden revisar la base. Bloquean únicamente las funciones que dependan de ellas.

## 29. Referencias

- [HL7 FHIR R5 MedicationRequest](https://hl7.org/fhir/R5/medicationrequest.html): orden de medicamento, instrucciones, sustitución y distinción frente a uso/dispensación.
- [HL7 FHIR R5 MedicationStatement](https://hl7.org/fhir/R5/medicationstatement.html): referencia para no confundir medicación declarada con prescripción.
- [HL7 FHIR R5 ServiceRequest](https://hl7.org/fhir/R5/servicerequest.html): solicitud de investigaciones diagnósticas y otros servicios; una orden no es su informe de cumplimiento.
- [HL7 FHIR R5 DiagnosticReport](https://hl7.org/fhir/R5/diagnosticreport.html): referencia para el límite entre orden y resultados posteriores.
- [HL7 FHIR R5 DocumentReference](https://hl7.org/fhir/R5/documentreference.html): metadatos y gestión de documentos/archivos, sin imponer su modelo completo.
- [HL7 FHIR R5 Provenance](https://hl7.org/fhir/R5/provenance.html): autoría, emisión, revisión y contexto histórico.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): mínimo privilegio, denegación por defecto y autorización en cada solicitud.
- [Registro clínico y seguimiento](patient-clinical-record.md): R13/R14, límites de prescripción y adjuntos.
- [Autorización RBAC/ABAC](authorization-rbac-abac.md): actor profesional, paciente y acciones separadas.
- [D11 · Hub y servidor en API](decisions.md#d11--interfaz-del-hub-y-servidor-en-nightingale-api): acceso limitado original.
- [D12 · Registro clínico](decisions.md#d12--registro-clínico-y-seguimiento-del-paciente): alcance clínico y prescripción futura.
- [D14 · Autorización](decisions.md#d14--especificación-separada-de-autorización-rbacabac): modelo de acceso aprobado.
- [D16 · Facturación y acceso del paciente](decisions.md#d16--especificación-de-facturación-administrativa-de-pacientes): ampliación previa del enlace, sin abrir contenido clínico.

## 30. Resultado de esta entrega

Esta especificación define documentos clínicos simples, imprimibles y trazables. El médico emite en API y firma a mano sobre el papel; Nightingale conserva contenido, historia y PDF, sin afirmar firma digital, dispensación o realización de exámenes.

La consulta del paciente se limita a documentos autorizados. El QR verifica identidad/estado mínimo y no sustituye el enlace privado. No se declaran implementados borradores, emisión, archivos, timeline, Hub o verificación. Las decisiones abiertas deben cerrarse antes de convertir las partes afectadas en esquema físico o contrato HTTP.
