# Reglas para colaboradores y agentes

## Antes de cambiar algo

1. Lee [la especificación](docs/nightingale-api.md), las decisiones vigentes y la tarea activa en [tasks/](tasks/README.md).
2. Inspecciona los archivos y el estado real de Git, si existe. Conserva el trabajo ajeno. No crees repositorios, remotos, commits o despliegues como efecto de otra tarea.
3. Si una instrucción nueva cambia con claridad el alcance, regístrala. Ante una contradicción sin resolver, detén solo el trabajo afectado y pide una decisión.

El contrato de diseño v1 está en [api-v1.md](docs/api-v1.md); el modelo físico conserva su única fuente en [database-schema.md](docs/database-schema.md). Keycloak autentica al emitir un token opaco de dispositivo sin vencimiento y revocable en API. No añadir sesiones/renovación de API ni prometer revocación por logout del proveedor. La implementación del Hub permanece fuera de esa etapa; [D11](docs/decisions.md#d11--interfaz-del-hub-y-servidor-en-nightingale-api) fija su alcance futuro sin bloquear el núcleo aprobado.

Patient Hub tendrá repositorio propio para la interfaz web. Nightingale API tendrá todas sus funciones de servidor, sin servidor ni almacén privado del Hub y sin SQL desde la web. Su primera versión incluirá micrositios con plantillas para profesional independiente y clínica/centro, sin editor libre ni gestión de pacientes. La lectura pública no exige cuenta de paciente, inicio de sesión ni permisos del personal y solo entrega información destinada a publicación. Las rutas internas siguen protegidas; el micrositio no publica fichas, citas ni notas privadas.

La gestión de una cita existente usará acceso limitado a cita/acción e información necesaria, sin credenciales del personal: consultar, confirmar, cancelar según reglas, solicitar reprogramación y consultar resultado. El paciente no crea ni reserva citas, no explora horarios para elegir otro ni marca ausencias. La solicitud conserva estado, horario y confirmación; el personal decide el cambio y API lo aplica con las reglas comunes. El mecanismo del enlace y las formas HTTP siguen pendientes. No tratar la propuesta anterior entre dos servidores como obligatoria ni presentar estas funciones como implementadas. La presentación pública de clínicas no autoriza toda su gestión interna, varias sedes o cambios generales del escritorio.

## Trabajo por tareas

- Para cambios amplios, prepara tareas pequeñas con propietario, entradas, dependencias, aceptación y comprobaciones. Sigue [las reglas del plan](tasks/README.md).
- Trabaja en una tarea aprobada a la vez. No delegues ni abras trabajo paralelo salvo autorización expresa del usuario o del plan aprobado.
- En cada checkpoint, registra evidencia real y detente para revisión. Solo el usuario acepta el checkpoint; las pruebas no lo sustituyen.
- Antes de añadir código, recorre el caso real y busca la opción mínima: no cambiar, reutilizar, biblioteca estándar o dependencia ya justificada. No crees capas, clases ni archivos vacíos por anticipación.
- Antes de usar APIs de herramientas, consulta el manifiesto y las versiones resueltas. Lee la página oficial de esa versión, registra el enlace y explica cualquier dependencia nueva. No instales ni actualices herramientas dentro de una tarea ajena.
- No copies código Rust, planes históricos ni instrucciones exclusivas del escritorio. No modifiques otros repositorios sin una instrucción nueva.

Usa [la arquitectura](docs/architecture.md) y [la propiedad de contratos](docs/contracts.md), con `api/users` como referencia de estilo. La arquitectura es hexagonal con empaquetado por componentes. Estas reglas sustituyen las descripciones previas incompatibles:

- `infrastructure/` contiene solo endpoints y su configuración. No contiene esquemas, helpers ni adaptadores de proveedores.
- `application/` contiene casos de uso con funciones y resultados `Ok`/`Err`. No importa SQLAlchemy en ejecución ni consulta, escribe o hace flush sobre sesiones. Puede usar anotaciones de tipos como `users`.
- `repository/` contiene solo modelos SQLAlchemy y DAOs derivados de `core/db/dao.py`. Las consultas propias son métodos de esos DAOs.
- `domain/` contiene esquemas, objetos de valor, tipos y errores propios. Todos los esquemas de datos heredan del `BaseModel` del proyecto. No contiene SQL ni acceso a proveedores o generación de credenciales.
- Separar `authorization` (identidad, credenciales y dispositivos globales) de `accounts` (cuenta, pertenencias, perfil profesional y autorización por cuenta). Entre componentes, consumir casos de uso y tipos de dominio; no importar repositorios ajenos.
- `core/services/` contiene soporte técnico concreto para proveedores y credenciales. `core/db` ofrece el soporte mínimo para delimitar una transacción sobre la sesión existente. La aplicación la coordina; los DAOs usan `commit=False` y no confirman partes por su cuenta.
- JSON público en camelCase mediante la base existente; Python en snake_case. No alterar credenciales ni la pareja exacta issuer/subject. Respetar nombres propios de protocolos externos.
- Anotar entradas y salidas de validadores, serializadores, DAOs y casos afectados con sus tipos reales; comprobar campos opcionales antes de usarlos. No ocultar avisos con cast, Any ni supresiones. Conservar los sentinels de Python 3.15 y registrar el límite del analizador mientras no los admita.
- Validar una vez el payload de cada operación y reutilizar el modelo para huella y ejecución. Conservar la validación de estado combinado con patches, defaults equivalentes, ausencia frente a null y JSON recibido inválido.
- Las lecturas HTTP corregidas de servicios y reglas devuelven dicts con tipos y campos explícitos; las rutas declaran response_model y el tipo de retorno real. Recibos y journal validan y serializan sus proyecciones antes del commit. Conservar modelos que aplican reglas de dominio; no devolver un ORM completo ni __dict__.
- Listas y páginas de snapshot usan `page` desde 1 y `shows` 100 por defecto, máximo 500, con LIMIT/OFFSET en DAO y `items`/`total`. No usar cursores de página ni su configuración. Conservar el avance incremental de sincronización, sus controles y su recuperación.
- Sustituir `src/cli.py` por `scripts/create_practice.py`, un flujo pequeño de alta administrativa. No crear un sistema de comandos ni hacer que el servidor dependa de scripts.
- `src/core/constants.py` aquí van todas las constantes, si vas a añadir en un archivo una constante que pueda ser compartida por otros componentes debería ir aquí, todo lo que sea estático y una constante debería ir aquí.

Antes de cada cambio, releer el archivo y el diff actual. Al corregir cada componente, activar sus controles de estructura; el cierre no admite excepciones que oculten infracciones. No restaurar código retirado por el usuario para satisfacer pruebas antiguas. `core/` no contiene reglas del producto ni lógica de negocio.

Toda operación remota sobre datos privados exige autorización vigente por cuenta, objeto y acción, aunque Rust o el Hub ya la hayan validado. La futura lectura pública del micrositio solo devolverá información destinada a publicación; no exigirá permisos del personal ni dará acceso a las rutas privadas. API verificará el acceso limitado a citas del paciente. No confíes en campos de identidad o fechas del cliente. No entregues credenciales SQL al escritorio o al Hub. n8n usa una API interna limitada.

## Skills locales

Lee y aplica la skill que corresponda a la tarea:

- [minimal-code](.agents/minimal-code/SKILL.md): implementación, correcciones y cambios acotados.
- [docs-first-framework-code](.agents/docs-first-framework-code/SKILL.md): consultar fuentes oficiales antes de usar bibliotecas o API de la plataforma.
- [planning-task-breakdown](.agents/planning-task-breakdown/SKILL.md): planificar trabajo amplio o con dependencias; no hace falta para cambios pequeños y claros.
- [code-review](.agents/code-review/SKILL.md): revisar cambios respecto de una referencia Git indicada.


## Evidencia y documentación

- Usa datos ficticios. No guardes secretos, enlaces reales, cuerpos personales ni copias de pacientes en archivos, registros o pruebas.
- Ejecuta las comprobaciones pertinentes de la tarea. Para integridad y concurrencia usa PostgreSQL real aislado; SQLite no acredita esas reglas.
- Separa documentación comprobada, pruebas locales, integración con consumidores y pruebas de operación. No declares una función hecha por describirla.
- Entrega qué cambió, por qué, evidencia y límites pendientes. Actualiza el plan después de comprobar, sin marcar aceptación del usuario por tu cuenta.
- Conserva una sola fuente editable por contrato. Los artefactos generados y las copias de consulta deben indicar origen y versión.
- Si el usuario comienza en inglés, responde en inglés salvo que pida español. En inglés aplica ASD-STE100. En ambos idiomas usa palabras cortas, voz activa y frases directas, sin figuras retóricas.
