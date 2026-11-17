# Especificación del componente de autorización RBAC/ABAC

**Versión:** 0.1\
**Fecha:** 2026-11-17\
**Estado:** Aprobada por el usuario el 2026-11-17 como referencia funcional. No autoriza implementación, migraciones ni cambios de contrato.\
**Ámbito:** Nightingale API y las reglas que sus consumidores deben interpretar.\
**Documentos relacionados:** [especificación general](nightingale-api.md), [decisiones](decisions.md), [diseño de acceso vigente](access-design.md), [arquitectura](architecture.md), [contrato HTTP v1](api-v1.md), [esquema físico](database-schema.md) y [calidad](quality.md).

## 1. Propósito

Este documento define cómo Nightingale decide si un actor autenticado puede ejecutar una acción sobre un objeto. Convierte en reglas explícitas un modelo que hasta ahora surgió de las necesidades de pacientes, agenda, citas y registro clínico.

El componente combina:

- **RBAC:** roles que conceden un conjunto base de acciones.
- **ABAC:** atributos del sujeto, la cuenta, el objeto, la acción y el contexto.
- **Reglas por relaciones:** pertenencia, propiedad y vínculos profesionales o asistenciales. Estas reglas son una parte concreta del modelo de atributos; no requieren otro motor.

El resultado buscado es una sola semántica de autorización para lecturas, escrituras, resultados idempotentes, capturas, descargas incrementales, avisos y auditoría. La interfaz puede ocultar acciones no permitidas, pero la API siempre vuelve a decidir.

### 1.1 Problema que debe resolver

La implementación actual ya aplica seguridad por cuenta, objeto y acción. Sin embargo:

- El catálogo `allowedActions` y las comprobaciones de ejecución se construyen en lugares distintos.
- Varias reglas dependen de conjuntos de acciones distribuidos entre casos de uso.
- Los permisos clínicos usan niveles por sección, mientras que los permisos administrativos dependen principalmente del rol.
- Las reglas por objeto, como propiedad del catálogo o bloqueos globales, se comprueban en casos específicos.

Estas diferencias no implican que el comportamiento actual sea incorrecto. Sí aumentan el riesgo de que una acción aparezca como disponible y después se rechace, o de que una ruta nueva olvide una comprobación. El componente debe hacer explícitas y comprobables esas reglas antes de añadir suscripciones, facturación y documentos clínicos.

## 2. Alcance y exclusiones

### 2.1 Incluye

- Identidad autenticada como entrada, sin redefinir su emisión.
- Roles actuales por cuenta y su significado exacto.
- Atributos y relaciones necesarios para decidir.
- Permisos administrativos y clínicos existentes.
- Reglas para operaciones, lecturas, páginas, resultados y sincronización.
- Revocación, cambios de permisos y coordinación transaccional.
- Comportamiento de los consumidores offline.
- Auditoría y no divulgación de objetos ajenos.
- Requisitos para extender el catálogo sin crear reglas contradictorias.
- Separación entre autorización y disponibilidad comercial de una función.

### 2.2 Excluye

- Sustituir Keycloak, OIDC, PKCE o el token opaco de dispositivo.
- Añadir sesiones API, renovación o revocación por logout del proveedor.
- Diseñar tablas, columnas, rutas o esquemas JSON nuevos.
- Definir planes, asientos, pagos o vigencia de suscripciones.
- Definir permisos financieros o de récipes antes de sus especificaciones.
- Elegir un motor externo de políticas, lenguaje de reglas o dependencia nueva.
- Crear un administrador global con acceso a todos los datos clínicos.
- Implementar el mecanismo de enlaces del paciente.
- Resolver el borrado remoto de datos ya descargados.

[database-schema.md](database-schema.md) conserva la única fuente física. [api-v1.md](api-v1.md) conserva el contrato HTTP. Este documento no crea una segunda definición editable de esos artefactos.

## 3. Estado normativo y lectura

Se usan tres categorías:

| Marca | Significado |
|---|---|
| **Vigente** | Comportamiento implementado o acordado en las fuentes actuales. Debe conservarse salvo una decisión posterior expresa. |
| **Decisión de este componente** | Dirección acordada en el encargo: estandarización deliberada mediante RBAC y atributos, sin trasladar la autoridad de negocio a Keycloak. |
| **Propuesta de destino aprobada** | Regla de diseño aceptada como referencia para trabajo posterior. No se presenta como implementada ni modifica por sí sola el contrato actual. |

Los identificadores `AU-xx` son requisitos de esta especificación. No equivalen a tareas ni sustituyen los pendientes `Oxx` del registro general.

## 4. Fuentes y comportamiento actual

### 4.1 Decisiones vigentes

- **D01/D02:** API es el límite remoto de seguridad y acepta operaciones completas en PostgreSQL privado.
- **D06:** el proveedor OIDC autentica; API conserva permisos y dispositivos y aplica permisos vigentes al aceptar una operación pendiente.
- **D09:** Keycloak de desarrollo, token opaco sin vencimiento, roles fijos y alta controlada.
- **D10:** `authorization` posee identidad, credenciales y dispositivos globales; `accounts` posee cuenta, pertenencias, profesional y autorización por cuenta.
- **D11:** el futuro acceso del paciente es limitado por cita/acción; no equivale a una pertenencia del personal.
- **D12/D13:** las secciones clínicas tienen permisos independientes, filtrado cerrado, historial y descarga autorizados.

### 4.2 Evidencia de implementación

El estado vigente se comprueba en:

- `src/api/authorization/application/authorization_cases.py`: autenticación del token, estados de usuario/dispositivo y orden de bloqueos.
- `src/api/accounts/application/accounts_cases.py`: contexto de cuenta, propietario, permisos clínicos y `AccessResponse`.
- `src/api/clinical_records/application/access_cases.py`: correspondencia entre acciones y secciones clínicas.
- `src/api/sync/application/operations_cases.py`: autorización antes de recibos y ejecución, reglas administrativas y alcance por objeto.
- `src/api/sync/application/download_cases.py`: audiencias, secciones clínicas, época y cursor.
- `src/api/accounts/domain/accounts.py`: roles `owner`/`assistant` y niveles `none`/`read`/`read_write`.

Esta especificación no vuelve a ejecutar esas pruebas ni certifica consumidores o producción.

## 5. Conceptos

| Concepto | Definición |
|---|---|
| **Autenticación** | Prueba de quién es el actor y de que su credencial sigue siendo válida. |
| **Autorización** | Decisión de permitir una acción concreta sobre un objeto y dentro de un ámbito. |
| **Actor** | Persona, dispositivo o servicio representado por una credencial autenticada. |
| **Cuenta** | Ámbito administrativo que aísla datos y permisos. |
| **Pertenencia** | Relación vigente entre una persona y una cuenta. |
| **Rol** | Conjunto base de permisos dentro de una cuenta; no una etiqueta global de la persona. |
| **Atributo** | Dato comprobado que interviene en una regla, como estado, propiedad o relación profesional. |
| **Recurso** | Objeto al que se aplica la acción, incluido su ámbito y versión cuando proceda. |
| **Acción** | Intención cerrada y conocida, no una ruta arbitraria ni un verbo SQL. |
| **Alcance** | Conjunto de cuentas, secciones, objetos y datos que una decisión permite ver o cambiar. |
| **Época de permisos** | Contador que invalida capturas y posiciones construidas con un alcance anterior. |
| **Audiencia** | Clase cerrada de destinatarios de una proyección de sincronización. |
| **Entitlement** | Disponibilidad comercial de una función para una cuenta. No es un permiso personal. |

## 6. Decisiones de dirección

**AU-01 · Modelo híbrido deliberado.** El componente usará RBAC como base y reglas por atributos/relaciones para el ámbito real. No se escogerá entre RBAC y ABAC como si fueran alternativas excluyentes.

**AU-02 · Autoridad en API.** Keycloak prueba identidad durante el canje inicial. La autorización de negocio permanece en Nightingale y se evalúa con estado actual de API.

**AU-03 · Estandarizar sin reescribir la propiedad.** El componente es una capacidad lógica transversal. No crea un tercer propietario de identidad o pertenencias ni obliga a un microservicio.

**AU-04 · Conservar el comportamiento vigente.** La normalización no debe ampliar permisos por accidente. Cualquier ampliación de roles, secciones o acciones requiere una decisión explícita.

**AU-05 · Sin motor genérico anticipado.** Las políticas serán funciones y tipos cerrados del dominio. No se introduce un lenguaje de expresiones, un servicio externo o una base de reglas arbitrarias sin una necesidad demostrada.

**AU-06 · Una fuente para descubrimiento y ejecución.** Propuesta de destino: el catálogo que calcula acciones visibles y secciones legibles debe proceder de las mismas definiciones usadas para autorizar. Una respuesta de capacidades nunca sustituye la comprobación de ejecución.

## 7. Principios obligatorios

### AU-10 · Denegar por defecto

Una acción desconocida, un recurso sin regla, una audiencia no reconocida o una combinación incompleta se deniegan. La ausencia de una comprobación no equivale a permiso.

### AU-11 · Mínimo privilegio

Cada actor recibe solo las acciones necesarias. La propiedad de una cuenta no concede acceso a otras cuentas. Ser profesional no concede acceso global a pacientes. Ser operador de Nightingale no concede acceso clínico por defecto.

### AU-12 · Decisión completa

Toda decisión privada considera, según corresponda:

1. Actor y credencial.
2. Usuario y dispositivo.
3. Cuenta y pertenencia.
4. Rol y permisos configurados.
5. Acción conocida.
6. Objeto, cuenta propietaria y relaciones.
7. Estado funcional necesario para autorizar.
8. Alcance de lectura, resultado o sincronización.

### AU-13 · Autorización en servidor

Rust, React, el Hub, n8n o un worker pueden reducir la interfaz o preparar una solicitud. Ninguno concede autoridad remota. La API repite la decisión aunque otro componente afirme haberla realizado.

### AU-14 · Sin identidad declarada por el cliente

`userId`, `accountId`, `professionalId`, `deviceId`, fechas o roles del payload no prueban identidad o permiso. Las referencias necesarias se contrastan con el actor y la base de datos.

### AU-15 · Sin permiso retroactivo

Una operación creada localmente antes de perder un permiso no conserva autorización anterior. La fecha del dispositivo no cambia esta regla.

### AU-16 · Autorización antes de canales laterales

La decisión precede a:

- Lectura de cuerpos y detalles.
- Conteos y paginación.
- Consulta de resultados previos.
- Resolución de duplicados.
- Mensajes de conflicto informativos.
- Capturas, páginas y deltas.
- Descarga de documentos.

Las reglas estructurales que rechazan un lote completo antes de procesarlo siguen el contrato; no deben convertirse en un oráculo de existencia de objetos.

## 8. Arquitectura y propiedad

### 8.1 Responsabilidades

| Elemento | Responsabilidad | No debe hacer |
|---|---|---|
| `authorization` | Autenticar token, actor, usuario y dispositivo global | Decidir permisos clínicos o importar repositorios de cuentas |
| `accounts` | Construir contexto de cuenta, rol, pertenencia, dispositivo por cuenta y permisos configurados | Consultar tablas clínicas para aplicar sus reglas |
| Componente propietario del recurso | Resolver existencia visible, cuenta propietaria y relaciones propias | Cambiar roles o pertenencias |
| Catálogo de políticas | Describir acción, nivel requerido, rol base y regla de objeto aplicable | Ejecutar SQL o recibir una sesión para construir consultas |
| `sync` | Coordinar autorización, recibo, efecto, auditoría y Change Log en la aceptación | Conceder acceso por conocer `operationId` o cursor |
| `audit` | Conservar evidencia mínima de decisiones y accesos | Sustituir la autorización o guardar contenido sensible innecesario |

### 8.2 Flujo de dependencias

El punto de entrada autentica y solicita un contexto de cuenta. El propietario del recurso aporta atributos mediante casos de uso y tipos de dominio. La política combina esos datos sin importar repositorios ajenos.

No se propone una clase por permiso ni una interfaz abstracta universal. Un catálogo de descriptores y funciones pequeñas es suficiente mientras cubra los casos reales.

### 8.3 Contexto de autorización

Como modelo lógico de destino, una decisión puede recibir:

```text
Subject
  userId, deviceId, tokenId
  userStatus, deviceStatus

AccountAccess
  accountId, accountStatus
  membershipStatus, membershipVersion
  role, accountDeviceStatus
  clinicalPermissions, permissionEpoch

Action
  name, operationKind, ownerOnly
  clinicalSection?, requiredClinicalLevel?
  objectRule?, onlineOnly?

Resource
  type, id?, accountId?
  patientId?, professionalId?
  ownership and relationship attributes needed by a closed rule
```

Los nombres describen conceptos, no un esquema Python aprobado. El token o su huella no forman parte de proyecciones, auditoría o logs.

### 8.4 Resultado de una decisión

Internamente debe distinguir al menos:

- Permitido.
- Credencial inválida.
- Cuenta no visible.
- Dispositivo no habilitado.
- Cuenta o pertenencia no utilizable.
- Acción no concedida.
- Sección sin nivel suficiente.
- Objeto fuera de alcance.
- Relación requerida ausente.
- Alcance de sincronización caducado.

Estas razones ayudan a probar y auditar. No se exponen todas al cliente; la proyección pública conserva las reglas de no divulgación de §16.

## 9. Modelo RBAC vigente

### 9.1 `owner`

- Se deriva de `accounts.owner_user_id`; no es un rol global persistido ni un claim elegido por Keycloak.
- Debe tener pertenencia e identidad utilizables.
- Tiene acceso administrativo completo dentro de su cuenta y acceso clínico completo.
- Puede configurar permisos de asistentes, equipo, dispositivos de cuenta, catálogo y ofertas según las reglas de propiedad.
- No puede editar sus propios niveles clínicos mediante `SetMemberClinicalPermissions`.
- La cuenta inactiva conserva solo las excepciones administrativas documentadas para su reactivación.
- No puede transferir la propiedad en el contrato actual.
- No elude relaciones de objeto, versiones, estados o restricciones de integridad.

### 9.2 `assistant`

- Es toda pertenencia activa que no corresponde al propietario.
- Puede ejecutar las operaciones administrativas comunes enumeradas en §10.2 con dispositivo habilitado y cuenta activa.
- No administra cuenta, equipo, invitaciones, políticas, auditoría o catálogo privado.
- Tiene niveles clínicos independientes por sección.
- Los asistentes existentes y nuevos conservan actualmente `read_write` como valor inicial de las ocho secciones clínicas.
- Desactivar y reactivar conserva su configuración.

### 9.3 La condición de profesional no es un rol global

`professionals` y `account_professionals` describen quién atiende y dónde. La relación profesional:

- Permite comprobar propiedad del catálogo o del perfil propio.
- Determina qué tiempo se reserva.
- Puede limitar bloqueos globales y participación en atenciones.
- No sustituye la pertenencia ni convierte al profesional en propietario.
- No concede lectura de todas las fichas donde existe una identidad común.

### 9.4 Roles futuros

No se aprueban aquí roles como `billing`, `viewer`, `receptionist` o `clinic_admin`. Antes de añadir uno se debe definir:

- Necesidad real que `assistant` más permisos no resuelve.
- Acciones iniciales y exclusiones.
- Ámbito por cuenta.
- Valor para miembros existentes.
- Reglas de asignación y revocación.
- Efecto en capturas, cursores y consumidores.

No se introducen jerarquías, herencia múltiple ni roles personalizados por anticipación.

## 10. Matriz funcional vigente

Esta matriz explica la autorización actual. Los nombres exactos de acciones y su transporte permanecen en [api-v1.md](api-v1.md).

### 10.1 Identidad y acceso propio

| Acción o lectura | Regla |
|---|---|
| Emitir token de dispositivo | Access token OIDC válido; puede crear identidad sin permisos de cuenta |
| Consultar identidad y dispositivos propios | Token API válido y usuario activo |
| Rotar token | El token actual pertenece al dispositivo que se rota |
| Revocar dispositivo propio | El dispositivo pertenece al mismo usuario, aunque no sea el actual |
| Consultar invitaciones propias | Destinatario autenticado |
| Aceptar invitación | Invitación dirigida al actor, pendiente y vigente; idempotencia propia |
| Descubrir cuentas | Solo cuentas donde el actor tiene pertenencia visible |
| Registrar dispositivo en cuenta | Pertenencia activa y dispositivo autenticado; excepción documentada de registro |
| Consultar `AccessResponse` | Pertenencia visible; funciona antes del registro del dispositivo |

### 10.2 Acciones administrativas comunes de miembros

Con cuenta activa, pertenencia activa y dispositivo habilitado, propietario y asistente pueden ejecutar:

| Área | Acciones |
|---|---|
| Pacientes | `RegisterPatient`, `UpdatePatientProfile`, `SetPatientProfileStatus`, `SetPatientCompletion`, `AddPatientIdentifier` |
| Contactos | `CreateContactPerson`, `UpdateContactPerson`, `SetContactPersonStatus` |
| Vínculos | `CreatePatientContactRelationship`, `UpdatePatientContactRelationship`, `SetPatientContactRelationshipStatus` |
| Horarios | `CreateScheduleRule`, `UpdateScheduleRule`, `SetScheduleRuleStatus` |
| Excepciones | `CreateScheduleException`, `UpdateScheduleException`, `SetScheduleExceptionStatus` |
| Bloqueos | `CreateScheduleBlock`, `UpdateScheduleBlock`, `SetScheduleBlockStatus`, limitados por la regla de bloqueo global |
| Citas | `CreateAppointment`, `ConfirmAppointment`, `RescheduleAppointment`, `CancelAppointment`, `CompleteAppointment`, `MarkAppointmentNoShow` |

Estas acciones no autorizan cruzar cuentas, fichas, profesionales o contactos. Las restricciones de completitud, disponibilidad, propiedad y versión se aplican además del rol.

### 10.3 Acciones exclusivas del propietario

| Área | Acciones o lecturas |
|---|---|
| Equipo | `CreateInvitation`, `RevokeInvitation`, `SetMembershipStatus`, `SetMemberClinicalPermissions` |
| Cuenta | `UpdateAccountDetails`, `UpdateAccountPolicy`, `SetAccountStatus` |
| Dispositivos de cuenta | `RevokeAccountDevice`, `RestoreAccountDevice` |
| Perfil y catálogo | `UpdateProfessionalProfile`, `CreateService`, `UpdateService`, `SetServiceStatus` |
| Ofertas | `OfferService`, `UpdateServiceOffer`, `SetServiceOfferStatus` |
| Consultas | Equipo, invitaciones, dispositivos de cuenta, auditoría y catálogo privado según api-v1 |

`UpdateProfessionalProfile` y las acciones de catálogo también exigen que el objeto pertenezca al profesional propio. Ser propietario de la cuenta no permite editar el catálogo de otro profesional.

### 10.4 Permisos clínicos

| Nivel | Lectura actual e historia | Escritura y corrección | Resultados de escritura | Captura y delta |
|---|---:|---:|---:|---:|
| `none` | No | No | No | No |
| `read` | Sí | No | No | Solo esa sección legible |
| `read_write` | Sí | Sí | Sí, con permiso vigente | Sí |

Secciones y acciones:

| Sección | Acciones protegidas |
|---|---|
| `profile` | `SetPatientSexAtBirth`; lecturas de perfil clínico |
| `conditions` | `CreatePatientCondition`, `UpdatePatientCondition`, `InvalidatePatientCondition` y revisión de esa sección |
| `allergies` | `CreatePatientAllergyIntolerance`, `UpdatePatientAllergyIntolerance`, `InvalidatePatientAllergyIntolerance` y revisión de esa sección |
| `encounters` | `CreatePatientEncounter`, `UpdatePatientEncounter`, `InvalidatePatientEncounter` y última visita |
| `notes` | `CreatePatientNote`, `UpdatePatientNote`, `InvalidatePatientNote` |
| `measurements` | `RecordPatientMeasurement`, `CorrectPatientMeasurement`, `InvalidatePatientMeasurement` y resumen |
| `immunizations` | `RecordPatientImmunization`, `UpdatePatientImmunization`, `InvalidatePatientImmunization` |
| `antecedents` | `CreatePatientAntecedent`, `UpdatePatientAntecedent`, `InvalidatePatientAntecedent` |

`SetPatientClinicalSectionReview` obtiene su sección del payload validado. Una acción sin sección conocida no puede ejecutarse como clínica genérica.

El historial integrado no tiene un permiso global que lo abra completo. Filtra cada fuente por su sección antes de contar y paginar; cada detalle vuelve a autorizar.

### 10.5 Reglas por objeto que se añaden al rol

- Paciente, contacto, cita, atención y registro clínico deben pertenecer a la cuenta de la ruta.
- Una relación entre objetos exige que todos pertenezcan al mismo ámbito y a la ficha indicada cuando aplique.
- Un profesional o asistente participante debe tener vínculo activo en la cuenta.
- Un bloqueo global solo lo gestiona el profesional propio autorizado; un asistente recibe del bloqueo ajeno solo la proyección permitida.
- El catálogo propio no ofrecido tiene audiencia `owner`; las ofertas se proyectan a miembros sin abrir el resto del catálogo.
- La auditoría de cuenta solo la consulta el propietario vigente.

## 11. Algoritmo de decisión propuesto

Toda entrada privada debe seguir una secuencia equivalente:

1. **Autenticar.** Validar token, usuario, dispositivo y relación entre ellos.
2. **Identificar la acción.** Resolver un descriptor conocido para lectura u operación.
3. **Coordinar el contexto.** Obtener los bloqueos y el estado de sincronización en el orden establecido.
4. **Construir el contexto de cuenta.** Releer cuenta, pertenencia, dispositivo de cuenta, rol y permisos después de esperas.
5. **Comprobar estados base.** Exigir los estados necesarios, incluida la excepción explícita de registro o reactivación.
6. **Resolver el objeto visible.** Comprobar cuenta propietaria y relaciones sin filtrar existencia ajena.
7. **Aplicar RBAC.** Comprobar si el rol concede la acción base.
8. **Aplicar nivel de sección.** Para clínica, exigir `read`, `read_write` o el nivel específico de la acción.
9. **Aplicar reglas del objeto.** Propiedad, participación, profesional propio y otras reglas cerradas.
10. **Autorizar el canal secundario.** Recibo, página, captura, cursor o descarga conserva su alcance.
11. **Ejecutar o proyectar.** Solo después de permitir se consulta el contenido o se aplica el efecto.
12. **Registrar evidencia.** La aceptación conserva auditoría y demás efectos en su transacción.

Una comprobación de versión o regla de negocio posterior no sustituye autorización. A la inversa, tener permiso no garantiza que una operación sea válida.

### 11.1 Fórmula conceptual

```text
permitir =
    identidad_vigente
    y dispositivo_vigente
    y contexto_de_cuenta_utilizable
    y accion_conocida
    y rol_concede_accion
    y nivel_de_seccion_suficiente
    y objeto_en_ambito
    y relaciones_requeridas_vigentes
    y alcance_del_canal_vigente
```

No hay una cláusula `owner = verdadero` que omita las últimas condiciones.

## 12. Escrituras, recibos e idempotencia

### AU-30 · Reautorizar toda ejecución

La aceptación obtiene contexto actual dentro de su transacción. Debe coordinarse con cambios de permisos y revocación; una lectura anterior no basta.

### AU-31 · Autorizar antes de consultar duplicados

El recibo se consulta después de autenticar y autorizar la acción y su sección. La secuencia evita que un `operationId` conocido revele:

- Existencia del recibo.
- Estado anterior.
- Cuerpo o error.
- Conflicto de contenido.
- Datos de una sección revocada.

### AU-32 · Recuperación de resultados

`GET` de resultado exige el mismo actor, cuenta y permiso vigente exigidos por el contrato. Un dispositivo nuevo del mismo usuario puede recuperar solo si está autorizado. Para clínica, una escritura exige `read_write` vigente en la sección persistida en el recibo; `read` no basta.

Un recibo histórico sin alcance clínico inequívoco falla cerrado. No se intenta adivinar su sección a partir del contenido devuelto.

### AU-33 · Dependencias

Una dependencia solo se considera satisfecha dentro del mismo actor/cuenta y bajo las reglas contractuales. Conocer el identificador de una operación ajena no permite consultarla ni usarla para eludir alcance.

### AU-34 · Rechazo y efecto

La autorización denegada no cambia datos de negocio. La conservación de auditoría o recibo sigue el contrato de aceptación; nunca confirma una parte del efecto. Un fallo temporal no fija una denegación permanente.

## 13. Lecturas, listas y proyecciones

### AU-40 · Detalle

La ruta autentica, construye contexto y obtiene el objeto en su cuenta. Un objeto ajeno o inexistente produce la misma ausencia pública. No se proyecta primero y se comprueba después.

### AU-41 · Listas y conteos

Los filtros de autorización se aplican antes de `total`, `LIMIT` y `OFFSET`. Esto incluye secciones clínicas y audiencias. Una página no puede revelar mediante `total` cuántos objetos existen fuera del alcance.

### AU-42 · Historiales

El permiso se comprueba sobre la fuente y su sección, no solamente sobre el paciente. Las versiones anteriores conservan la misma o mayor restricción que el estado vigente; una corrección no convierte contenido restringido en público.

### AU-43 · Resúmenes y datos derivados

Resúmenes, última visita, indicadores y referencias del timeline se consideran lecturas de su fuente. No se puede eludir `none` consultando un resumen sin cuerpo, un conteo, una fecha derivada o un identificador.

### AU-44 · Archivos futuros

Conocer una URL, nombre de objeto o identificador no concede descarga. La especificación de cada documento definirá su acción y alcance; este componente exige que se comprueben antes de entregar bytes o una URL firmada.

## 14. Sincronización, capturas y avisos

### 14.1 Audiencias cerradas

Las audiencias actuales son:

- `members`: datos operativos visibles para miembros autorizados.
- `owner`: administración, catálogo privado y otros datos exclusivos del propietario.
- Una audiencia por sección clínica: perfil, condiciones, alergias, atenciones, notas, mediciones, vacunas y antecedentes.

Añadir una audiencia exige registrar su propietario, proyección y regla de acceso. Una audiencia desconocida no se entrega.

### 14.2 Capturas

Una captura queda ligada a cuenta, usuario, dispositivo, ventana, audiencia, época y secciones clínicas incluidas. Solo su creador autorizado puede consultarla o liberarla.

- `includeClinical=false` no incluye datos clínicos.
- Con clínica, solo se materializan secciones legibles.
- El total cuenta solo elementos permitidos.
- Cambiar el alcance invalida la captura.
- Liberar una captura no borra negocio, historias o intenciones locales.

### 14.3 Cursor y delta

El cursor conserva la posición y el alcance. Se rechaza si cambia cuenta, usuario, dispositivo, audiencia, época, ventana o conjunto permitido de secciones según el contrato.

Los grupos invisibles permiten avanzar sin entregar cuerpos. La posición no es una prueba de autorización ni permite reconstruir contenido filtrado.

### 14.4 SSE

El aviso no sustituye la descarga. Se reautoriza al emitir y en heartbeat:

- Si el acceso deja de ser válido, se cierra.
- Si cambia la época, el alcance anterior no continúa.
- El aviso contiene datos mínimos, nunca contenido clínico.
- `Last-Event-ID` no concede permiso ni prueba aplicación local.

### 14.5 Una fuente de proyecciones

Propuesta: la misma definición que relaciona entidad, audiencia y sección debe alimentar captura, delta y comprobación de permisos. No se deben mantener listas independientes que puedan omitir una entidad nueva.

## 15. Cambios de permisos y revocación

### 15.1 Configuración por el propietario

La configuración de asistentes:

- Es online.
- Exige propietario vigente y dispositivo habilitado.
- Usa versión esperada de pertenencia.
- No cambia propietario, identidad global o cuenta.
- No permite configurar al propietario como asistente.
- Conserva niveles al desactivar/reactivar.
- Devuelve `NO_CHANGES` sin incrementar versiones si el estado efectivo no cambia.

### 15.2 Efectos atómicos

Un cambio efectivo de permisos conserva en una transacción:

- Nivel o estado modificado.
- Nueva versión de pertenencia.
- Auditoría.
- Recibo.
- Cambio de sincronización.
- Incremento de época cuando cambia el alcance.

Una captura o cursor anterior no puede seguir entregando el alcance viejo después del commit.

### 15.3 Carrera entre aceptación y revocación

El orden vigente se coordina en PostgreSQL:

- Si revocación confirma primero, la operación posterior con acceso viejo no tiene efecto.
- Si aceptación válida obtiene primero el orden y confirma, una revocación posterior no borra ese hecho.
- Un fallo no publica una operación como aceptada antes del commit.
- Después de esperar un bloqueo se relee el estado de acceso.

Se conserva el orden de bloqueos de identidad y el coordinado por cuenta/profesional documentado en el código y api-v1. Cambiarlo exige pruebas de concurrencia en PostgreSQL real.

### 15.4 Revocaciones diferentes

| Cambio | Efecto |
|---|---|
| Revocar token/dispositivo global | Impide autenticación futura con esa credencial/dispositivo |
| Revocar dispositivo en una cuenta | Impide operar en esa cuenta, sin revocar otras cuentas |
| Desactivar pertenencia | Retira acceso a esa cuenta |
| Desactivar usuario | Impide el acceso global del actor |
| Reducir una sección | Retira lecturas/escrituras y descargas de esa sección |
| Cerrar sesión OIDC | No revoca por sí solo el token API ya emitido |

## 16. Errores y no divulgación

La forma HTTP vigente se conserva:

| Situación | Resultado público |
|---|---|
| Credencial ausente, inválida o revocada | `401 AUTHENTICATION_REQUIRED` |
| Acción no permitida en un ámbito conocido o dispositivo no habilitado | `403 PERMISSION_DENIED` |
| Objeto inexistente o no visible | `404 NOT_FOUND` |
| Cursor/captura con alcance inválido o vencido | `410` con el código contractual aplicable |
| Regla funcional después de autorizar | Resultado o error de negocio correspondiente |

La API no distingue públicamente entre objeto ajeno e inexistente. Tampoco revela permisos de otro miembro, identidad externa, rol en otra cuenta o existencia de un resultado.

Los motivos internos de denegación no deben convertirse en mensajes que permitan explorar cuentas, pacientes o documentos.

## 17. Funcionamiento offline

### AU-50 · Copia local como ayuda, no autoridad

El escritorio puede conservar rol, acciones y secciones conocidas para presentar la interfaz y aplicar reglas locales permitidas. Esa copia puede estar desactualizada y no prueba permiso actual.

### AU-51 · Aceptación posterior

Al reconectar:

- API aplica permisos vigentes.
- Si falta permiso, rechaza sin efecto.
- La intención permanece local para revisión.
- Una persona autorizada puede crear una operación nueva con su identidad real; no reenvía suplantando al actor anterior.
- No se cambia la fecha para justificar una autorización anterior.

### AU-52 · Lecturas ya descargadas

La revocación impide nuevas lecturas y entrega de deltas, pero no demuestra borrado de copias, archivos, memoria o exportaciones ya obtenidas. No se promete borrado remoto ni se borran intenciones locales en silencio.

### AU-53 · Acciones online

Las acciones de administración de acceso son online. Las futuras funciones que exijan conexión deben declararlo en su propio catálogo. No se deduce que emitir un récipe o aprobar un pago sea offline u online por esta especificación.

## 18. Separación de otros tipos de acceso

### 18.1 Suscripciones y asientos

La suscripción responde si una función está comercialmente disponible para una cuenta. RBAC/ABAC responde si una persona puede ejecutar la acción.

Reglas de coordinación propuestas:

- Autenticación y autorización personal se comprueban antes de revelar detalles comerciales.
- Una suscripción activa no concede permiso a un usuario sin rol o sección.
- Un permiso personal no evita una restricción comercial vigente.
- Un límite de asientos se aplica al incorporar o reactivar integrantes según la especificación de suscripciones.
- Un cambio comercial no convierte a nadie en propietario ni modifica permisos clínicos.
- La suspensión no implica borrado de datos.

Estados, gracia y comportamiento offline pertenecen a la especificación de suscripciones.

### 18.2 Paciente con enlace limitado

El paciente no recibe rol `assistant` ni una pertenencia del personal. Su sujeto y concesión son distintos y se limitan a:

- Cuenta y objeto concedidos.
- Acciones expresas.
- Proyección mínima.
- Vigencia y revocación.
- Consulta de resultado bajo el mismo alcance.

La lectura pública del micrositio no usa este modelo y no entrega datos privados. La futura consulta de récipes desde un enlace requerirá ampliar el alcance documentado del Hub y definir una concesión de lectura específica.

### 18.3 Operador de Nightingale

La futura revisión de pagos de suscripciones requiere un operador de plataforma. Debe ser un tipo de actor separado:

- Sin equivalencia con `owner` de una cuenta.
- Sin acceso clínico por defecto.
- Con acciones administrativas explícitas.
- Con auditoría propia.
- Sin permiso para declararse miembro o profesional.

Su autenticación y funciones exactas se decidirán con suscripciones.

### 18.4 Workers, n8n y servicios

Una identidad técnica recibe acciones limitadas sobre trabajos o recursos necesarios. No hereda permisos de una persona ni obtiene SQL operativo. Cambiar una cita u otro objeto protegido exige el mismo caso de aceptación y reglas comunes.

## 19. Auditoría y seguridad

### AU-60 · Evidencia mínima

Cuando corresponda, registrar:

- Cuenta conocida.
- Actor y dispositivo autenticados.
- Acción.
- Tipo e identificador del objeto permitido.
- Resultado de la decisión o acceso.
- Instante del servidor y correlación.
- Versión o época cuando sea necesaria para explicar el alcance.

### AU-61 · Contenido prohibido

No registrar en auditoría o logs de autorización:

- Token, secreto o huella recuperable.
- Cuerpos clínicos, sustancias, valores o diagnósticos.
- Capturas de pago o datos financieros innecesarios.
- Filtros clínicos, cursores o URL firmadas.
- Payload completo para facilitar depuración.

### AU-62 · Denegaciones

Las denegaciones HTTP ya cuentan con evidencia técnica limitada. Una denegación sobre objeto no visible no debe convertir la auditoría en un canal que revele la cuenta ajena. El actor solo se asocia a `account_id` cuando ese ámbito le es conocido.

### AU-63 · Lecturas clínicas

Las lecturas clínicas correctas y los accesos a resultados/capturas/deltas conservan la evidencia exigida por el contrato. Si falla la evidencia obligatoria, no se entregan datos.

## 20. Extensión del catálogo

Toda acción nueva debe registrarse antes de implementar su caso con esta información:

| Campo conceptual | Pregunta obligatoria |
|---|---|
| Nombre | ¿Qué intención completa representa? |
| Tipo | ¿Lectura, escritura, resultado, descarga o acción administrativa? |
| Rol base | ¿Propietario, miembro o actor especial? |
| Objeto | ¿Qué recurso y cuenta determinan el alcance? |
| Sección | ¿Pertenece a una sección con nivel independiente? |
| Nivel | ¿Exige lectura o lectura/escritura? |
| Relaciones | ¿Propiedad, profesional propio, paciente o participación? |
| Conexión | ¿Online u offline desde el consumidor? |
| Resultado | ¿Qué permiso vigente permite recuperarlo? |
| Audiencia | ¿Qué proyección y destinatarios recibe? |
| Época | ¿Un cambio de configuración debe invalidar capturas? |
| Auditoría | ¿Qué evidencia mínima deja? |
| Errores | ¿Cómo evita revelar objetos ajenos? |

Una acción que no pueda responder estas preguntas todavía no está lista para su contrato.

### 20.1 Nuevos dominios

Propuesta de mínimo privilegio para extensiones:

- Los permisos financieros serán independientes de los clínicos.
- Aprobar un pago será distinto de consultar un cargo o un reporte.
- Preparar un documento clínico será distinto de emitirlo.
- Consultar un documento será distinto de administrar su acceso por enlace.
- Revisar suscripciones de plataforma no abrirá datos operativos de las cuentas.

El valor inicial para miembros existentes y nuevos debe decidirse por dominio. No se debe copiar automáticamente el actual `read_write` clínico a pagos, emisión de documentos o administración de plataforma.

## 21. Compatibilidad y transición de diseño

La normalización debe conservar:

- `contractVersion` y formas públicas mientras no se apruebe otra revisión.
- Significado de `role`, `allowedActions`, `clinicalPermissions` y `permissionEpoch`.
- Defaults equivalentes para clientes anteriores.
- Recibos históricos y su sección persistida.
- Audiencias y recuperación de capturas/cursores.
- Ausencia frente a `null` y validación de patches.
- Comportamiento de objetos no visibles.

Si una política nueva cambia una acción existente, se debe decidir expresamente:

- Si mantiene o amplía acceso.
- Qué ocurre con operaciones pendientes.
- Cómo se actualizan `allowedActions` y secciones.
- Si cambia la época.
- Cómo se recuperan clientes antiguos.

No se restaurarán permisos retirados para satisfacer una prueba antigua. Las pruebas deberán reflejar la decisión vigente.

## 22. Criterios verificables del comportamiento

Estos son requisitos para la futura implementación, no evidencia ejecutada por esta entrega documental.

### 22.1 Matriz de rol y sección

- Propietario y asistente reciben exactamente sus acciones vigentes.
- `none` excluye detalle, lista, total, resumen, historia, resultado y descarga.
- `read` permite lecturas pero no escrituras, duplicados de escritura ni recuperación de sus resultados.
- `read_write` permite ambas mientras el contexto siga vigente.
- Una acción desconocida se deniega.

### 22.2 Aislamiento

- Un miembro de A no lee ni modifica objetos de B aunque conozca sus UUID.
- Un profesional común a dos cuentas no comparte historias entre ellas.
- Los totales y errores no revelan objetos ajenos.
- Un operador de plataforma no obtiene acceso clínico implícito.

### 22.3 Recibos y respuestas perdidas

- Un reintento se reautoriza antes de consultar el recibo.
- La misma operación con distinto contenido conserva conflicto sin filtrar el original a un actor no autorizado.
- Un resultado clínico exige su sección y nivel actuales.
- Un dispositivo nuevo autorizado recupera solo resultados permitidos del mismo actor.

### 22.4 Concurrencia

Con PostgreSQL real aislado:

- Revocación que confirma primero impide efecto posterior.
- Aceptación confirmada primero conserva su hecho.
- Cambio de sección y captura concurrente no entrega alcance retirado.
- Cambio de permisos y `allowedActions` no quedan en versiones incoherentes.
- Dos cambios de permisos con la misma versión no se sobrescriben.

### 22.5 Sincronización

- Capturas y deltas incluyen solo audiencias y secciones permitidas.
- Los grupos invisibles no entregan cuerpo ni impiden avanzar.
- Cambiar época cierra el stream anterior y exige recuperación.
- `total` y `itemCount` no cuentan elementos retirados por autorización.
- La proyección y la autorización usan la misma correspondencia entidad/sección.

### 22.6 Offline y consumidores

- Una intención sin permiso vigente se conserva localmente sin efecto remoto.
- La interfaz no interpreta `allowedActions` como permiso permanente.
- La aplicación atómica en SQLite y la experiencia del escritorio requieren pruebas en su repositorio; las pruebas de API no las sustituyen.

## 23. Criterios para aceptar esta especificación

La revisión documental debe comprobar:

- Una sola interpretación de autenticación, rol, atributo, relación y entitlement.
- Correspondencia con las decisiones D01, D02, D06 y D09–D13.
- Cobertura de todas las acciones y secciones actuales sin ampliar acceso.
- Propiedad arquitectónica compatible con `authorization`, `accounts` y componentes de recursos.
- Reglas explícitas para recibos, lecturas, sincronización, revocación y offline.
- Separación de paciente, operador y servicios.
- Ausencia de decisiones físicas o HTTP presentadas como aprobadas.
- Pendientes claramente separados de las reglas vigentes.

## 24. Decisiones pendientes

| ID | Decisión | Momento necesario |
|---|---|---|
| `AU-O01` | Mantener solo `owner`/`assistant` o introducir perfiles administrativos/financieros | Antes de añadir roles |
| `AU-O02` | Valor inicial de futuros permisos financieros y documentales para asistentes existentes/nuevos | En las especificaciones de facturación y documentos |
| `AU-O03` | Qué acciones clínicas futuras exigen profesional emisor y cuáles permiten preparación por asistente | En récipes y órdenes |
| `AU-O04` | Autenticación, alcance y recuperación del operador de Nightingale | En suscripciones |
| `AU-O05` | Concesión, vigencia y revocación del enlace para documentos del paciente | En documentos y contrato del Hub |
| `AU-O06` | Si el propietario puede consultar una explicación segura de sus decisiones denegadas | Antes de exponer motivos adicionales |
| `AU-O07` | Política de suspensión comercial y alcance offline | En suscripciones; no se resuelve con RBAC |

Estas preguntas no impiden aprobar la base vigente. Bloquean únicamente la parte que dependa de ellas.

## 25. Referencias

### Estándares y guías

- [NIST RBAC](https://csrc.nist.gov/projects/role-based-access-control): roles como conjuntos de privilegios y relación con ABAC. El proyecto histórico está archivado; se usa como referencia conceptual, no como guía de implementación actual.
- [NIST SP 800-162, ABAC](https://csrc.nist.gov/pubs/sp/800/162/upd2/final): evaluación de atributos del sujeto, objeto, operación y entorno.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): mínimo privilegio, denegación por defecto, validación en cada solicitud y controles por atributos/relaciones.
- [OIDC Core, validación de ID Token](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation): distingue validación de identidad del proveedor y autorización local.
- [RFC 8252](https://www.rfc-editor.org/rfc/rfc8252.html): Authorization Code con PKCE para aplicaciones nativas.
- [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html): prácticas de seguridad OAuth actuales.
- [RFC 9068](https://www.rfc-editor.org/rfc/rfc9068.html): perfil de access tokens JWT cuando corresponda al proveedor.
- [RFC 7662](https://www.rfc-editor.org/rfc/rfc7662.html): introspección para tokens opacos de proveedor cuando se adopte, no para el token opaco propio actual.
- [PostgreSQL 18, bloqueo explícito](https://www.postgresql.org/docs/18/explicit-locking.html): base para coordinar aceptación y revocación; requiere pruebas de carreras propias.

### Fuentes internas

- [D06 · Identidad externa y permisos vigentes](decisions.md#d06--identidad-externa-y-permisos-vigentes).
- [D09 · Primera etapa de API compartida](decisions.md#d09--primera-etapa-de-api-compartida-para-escritorio).
- [D10 · Corrección de arquitectura y estilo](decisions.md#d10--corrección-de-arquitectura-y-estilo).
- [Diseño de acceso](access-design.md).
- [Contrato HTTP v1](api-v1.md).
- [Arquitectura](architecture.md).

## 26. Resultado de esta entrega

Esta revisión define el lenguaje, los límites y el comportamiento que debe normalizar el componente. No declara implementado un motor nuevo, no cambia los roles actuales y no autoriza trabajo de código. Las especificaciones de suscripciones, facturación y documentos deberán consumir estas reglas y añadir solo sus acciones y atributos propios.
