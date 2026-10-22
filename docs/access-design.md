# T04 · Identidad, permisos y alcance del Hub

**Estado:** acuerdo parcial de seguridad, en revisión. **Confirmado por el usuario:** proveedor externo OIDC para el personal; API conserva permisos y dispositivos; acepta cambios con los permisos vigentes y conserva para revisión la intención rechazada. El alcance del Hub sigue como propuesta. No se elige proveedor, biblioteca de autenticación, duración ni esquema SQL. No hay controles de acceso implementados todavía.

## Identidad del personal

El proveedor prueba quién inició sesión; Nightingale API decide qué puede hacer en cada cuenta. La clave externa propuesta es la pareja emisor/sujeto (`iss`, `sub`), vinculada a un usuario interno. El correo no concede pertenencia ni sirve para enlazar cuentas automáticamente. Autenticarse no crea una cuenta profesional ni otorga acceso a una existente.

El escritorio será un cliente público: navegador externo, Authorization Code y PKCE S256, sin secreto de cliente distribuido. Rust mantiene el retorno de autenticación y los secretos locales; esos cambios pertenecen al escritorio. API recibe un access token destinado a su audiencia; no acepta un ID token como credencial de operaciones. Las reglas de validación dependen del formato y del proveedor aprobado. [RFC 8252](https://www.rfc-editor.org/rfc/rfc8252) y [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700) sustentan el flujo nativo y la protección de tokens; no eligen un proveedor.

Para un access token JWT se verifican firma, algoritmos permitidos, emisor, audiencia, vigencia y propósito antes de consultar permisos locales. No se toma una URL de claves aportada por el cliente. Para tokens opacos, evaluar introspección autenticada. Las claves, su rotación, renovación y fallos requieren el contrato del proveedor. La validación del ID token del inicio de sesión corresponde al cliente OIDC; no sustituye la validación del access token de API. Referencias: [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation), [perfil de access tokens JWT](https://www.rfc-editor.org/rfc/rfc9068) e [introspección](https://www.rfc-editor.org/rfc/rfc7662).

## Propiedad y altas

| Propietario | Información y autoridad |
|---|---|
| Proveedor OIDC | Autenticación del personal, credenciales del proveedor, factores y tokens según su contrato |
| API / `access` | Usuario interno y vínculo externo, cuentas, pertenencias, permisos, dispositivos, estado de acceso remoto y evidencia de revocación |
| Escritorio | Sesión/secretos locales en almacenamiento seguro, copia de permisos e intenciones pendientes; no puede modificar permisos sin conexión |
| Hub | Identidad y acceso del paciente, enlaces, reglas propias y solicitudes; no usa la sesión del profesional como identidad del paciente |

Propuesta: el primer acceso administrativo se habilita mediante un procedimiento online controlado. Un usuario autorizado invita a asistentes y concede permisos limitados a su cuenta. No habrá un alta pública que permita elegir cuenta, rol o pertenencia. Antes de T08 deben acordarse el alta inicial, la prueba de aceptación de invitación y la recuperación de la cuenta; no se crea una ruta administrativa abierta para pruebas.

Un dispositivo necesita un registro autorizado y una credencial o sesión ligada a ese registro. Un `device_id` enviado por el cliente no prueba esa relación. El protocolo concreto de vínculo y renovación queda abierto hasta elegir proveedor; debe impedir reutilizar el registro de otro usuario o dispositivo. No se promete atestación del equipo ni resistencia a un equipo intervenido.

## Política remota ante revocación

**Confirmada por el usuario el 2026-10-21:** aplicar los permisos vigentes al aceptar la operación. No conceder autorización retroactiva solo porque el equipo afirma que guardó el cambio antes. Si ya no existe permiso, rechazar sin aplicar el efecto y conservar la intención en el escritorio para revisión. Propuesta de tratamiento posterior: una persona aún autorizada podrá crear una operación nueva tras revisar la intención; no se restaura la antigua credencial ni se reenvía el cambio con un actor falso.

La API coordina la comprobación local de acceso y la escritura. Propuesta de orden:

1. La aceptación y la revocación de usuario/pertenencia/dispositivo comparten una referencia de autorización versionada y un mecanismo de coordinación en PostgreSQL.
2. Si revocación se confirma primero, la operación no puede aplicar efectos usando la versión anterior. Si aceptación obtiene el orden válido primero y confirma, una revocación posterior no borra ese hecho.
3. Un fallo no publica revocación o aceptación como completada antes de su commit. T07/T08 deben demostrar la carrera con conexiones distintas y orden de bloqueos definido.

Los tiempos del servidor y las versiones aportan evidencia; la hora del cliente no decide el orden. La revocación local de API puede impedir operaciones aunque el access token del proveedor siga vigente. En cambio, cerrar sesión en el proveedor no garantiza revocación inmediata en API: elegir entre introspección, notificación fiable y vigencia limitada, con demora acordada. No se promete equivalencia entre logout, revocación de sesión, dispositivo y pertenencia.

El escritorio conserva los últimos permisos válidos sin red. API no puede revocar de inmediato esa copia ni retirar datos ya descifrados. Al reconectar, devuelve el rechazo o la necesidad de revisión, sin ordenar un borrado silencioso de intenciones. También reautoriza consultas de resultados idempotentes y páginas; conocer un ID anterior no permite recuperar datos tras revocación.

## Propuesta de autorización del Hub

Una credencial de servicio prueba que llama el backend del Hub, no que pueda operar cualquier cita. Comparación:

| Opción | Ventaja | Riesgo y coste |
|---|---|---|
| A. Concesión limitada registrada por API y comprobada con la operación | API puede comprobar y revocar su alcance dentro de la aceptación local | Exige emitir/vincular la concesión con la cita y conciliar su ciclo con los accesos del Hub |
| B. Consultar autorización al Hub en cada acción | Hub responde por el estado de su acceso y política | Añade dependencia de red y un intervalo entre consulta y commit; no demuestra revocación atómica entre servicios |
| C. Afirmación firmada del Hub sin estado de revocación en API | Evita una consulta por acción | Una firma prueba origen e integridad, no vigencia de permisos; necesita un límite de exposición y otro mecanismo de revocación |

**Propuesta para revisión:** A. Personal autorizado habilita el acceso a una cita mediante un caso de API que registra una concesión ligada a cuenta, cita, servicio destinatario y acciones. El Hub no puede crear concesiones para objetos arbitrarios solo con su identidad técnica. Su backend conserva la referencia necesaria y valida además su propio acceso del paciente. API exige identidad de servicio más concesión vigente; no acepta el actor o `practice_id` como prueba.

La concesión no es el enlace del paciente. API conserva el límite de autorización remota; Hub conserva el secreto del enlace, sus sesiones, reglas de cancelación y solicitudes. Se acuerdan identificación de actor, versión/época de la cita, vencimiento y revocación de la concesión; no se fija un formato firmado o duración antes de revisarlo. Los secretos de servicio no llegan al navegador.

Hub debe revocar su acceso local y comunicar a API la invalidación de la concesión. Si esa comunicación falla, mantiene el resultado remoto pendiente y reintenta por una identidad estable. La revocación compartida surte efecto cuando API la confirma. Una acción ya en curso puede tener un orden anterior; no hay revocación distribuida instantánea. La política de este intervalo necesita revisión. Reprogramar invalida la confirmación anterior y debe acordarse cómo afecta a la concesión y al enlace en T06/T15.

No se amplían las acciones del paciente: consultar su cita, confirmar, cancelar si Hub lo permite y solicitar cambio en Hub. Pedir cambio no modifica ni reserva horario. Las llamadas de proveedor o introspección ocurren fuera de las transacciones PostgreSQL; el alcance local se revalida con la escritura.

## Matriz de amenazas y pruebas futuras

| Entrada o carrera | Resultado exigido / propuesta a comprobar | Tarea |
|---|---|---|
| Token con otro emisor/audiencia, firma inválida o ID token usado como access token | Rechazo antes de leer datos operativos | T08 |
| Mismo correo con otro sujeto OIDC | No enlazar automáticamente ni heredar permisos | T08 |
| Actor cambia cuenta, rol, dispositivo o referencia de objeto en el payload | Usar contexto comprobado y rechazar cruce de cuenta/dispositivo | T08, T14 |
| Permisos revocados, reloj atrasado y operación pendiente | Aplicar la política confirmada: no aplicar; conservar intención para revisión | T08, T14, T23 |
| Aceptación y revocación simultáneas | Un orden verificable; sin éxito anterior al commit ni autorización anterior reutilizada | T08, T14 |
| Hub autenticado sin concesión, con otra cita o más acciones | Rechazar sin filtrar existencia ni resultado previo | T15 |
| Concesión revocada o cita reprogramada frente a una acción Hub antigua | Revalidar alcance/versión; no sobrescribir el estado nuevo | T15 |
| Respuesta de aceptación/revocación perdida | Recuperar resultado autorizado con la misma identidad; no repetir efecto | T14, T15 |
| Proveedor OIDC, claves o canal de revocación no disponibles | Fallo controlado según política aprobada; no permitir por error ni confundir indisponibilidad con rechazo definitivo | T08, T23 |

## Antes de cerrar T04

- Precisar el recorrido de revisión y nueva operación bajo la política de permisos vigentes ya confirmada.
- Aprobar o cambiar la opción del Hub y su comportamiento durante una revocación pendiente.
- Seleccionar proveedor OIDC y su contrato de access tokens, renovación, logout/revocación y disponibilidad; no hace falta contratarlo durante esta etapa.
- Precisar alta administrativa/invitaciones, vínculo dispositivo/sesión, recuperación y matriz mínima de permisos. Duraciones y límites requieren una decisión explícita antes de implementar acceso.

T04 sigue en curso. OIDC y permisos vigentes están confirmados, pero O01/O02 no están cerrados. El documento separa esos acuerdos de las propuestas restantes; no hay pruebas de seguridad ejecutadas. [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) respalda comprobar cada solicitud y denegar por defecto; no sustituye estas decisiones.
