# Reglas para colaboradores y agentes

## Antes de cambiar algo

1. Lee [la especificación](docs/nightingale-api.md), las decisiones vigentes y la tarea activa en [tasks/](tasks/README.md).
2. Inspecciona los archivos y el estado real de Git, si existe. Conserva el trabajo ajeno. No crees repositorios, remotos, commits o despliegues como efecto de otra tarea.
3. Si una instrucción nueva cambia con claridad el alcance, regístrala. Ante una contradicción sin resolver, detén solo el trabajo afectado y pide una decisión.

El usuario autorizó iniciar la fundación el 2026-10-21 y, después de pedir la corrección de anotaciones de contextos asíncronos, autorizó continuar con T04. El alcance actual es documental: identidad, revocación y alcance del Hub. Los acuerdos de seguridad pendientes requieren decisión antes de implementar acceso. No crear tablas, ejecutar migraciones ni desplegar con esta autorización; esas acciones pertenecen a etapas posteriores del plan.

## Trabajo por tareas

- Para cambios amplios, prepara tareas pequeñas con propietario, entradas, dependencias, aceptación y comprobaciones. Sigue [las reglas del plan](tasks/README.md).
- Trabaja en una tarea aprobada a la vez. No delegues ni abras trabajo paralelo salvo autorización expresa del usuario o del plan aprobado.
- En cada checkpoint, registra evidencia real y detente para revisión. Solo el usuario acepta el checkpoint; las pruebas no lo sustituyen.
- Antes de añadir código, recorre el caso real y busca la opción mínima: no cambiar, reutilizar, biblioteca estándar o dependencia ya justificada. No crees capas, clases ni archivos vacíos por anticipación.
- Antes de usar APIs de herramientas, consulta el manifiesto y las versiones resueltas. Lee la página oficial de esa versión, registra el enlace y explica cualquier dependencia nueva. No instales ni actualices herramientas dentro de una tarea ajena.
- No copies código Rust, planes históricos ni instrucciones exclusivas del escritorio. No modifiques otros repositorios sin una instrucción nueva.

## Límites de diseño

Usa [la arquitectura](docs/architecture.md) y [la propiedad de contratos](docs/contracts.md). El dominio no depende de FastAPI, SQLAlchemy ni transporte. La aplicación coordina transacciones; los repositorios no confirman partes de una operación por su cuenta. `core/` solo contiene soporte técnico concreto.

Toda operación remota exige autorización vigente por cuenta, objeto y acción, aunque Rust o el Hub ya la hayan validado. No confíes en campos de identidad o fechas del cliente. No entregues credenciales SQL al escritorio o al Hub. n8n usa una API interna limitada.

Conserva efectos, versiones, historial, auditoría, resultado idempotente, cambios y trabajo derivado en el límite atómico aprobado. Ejecuta llamadas externas después del commit. Ante un resultado desconocido, conserva ese estado y concilia antes de repetir efectos externos.

## Evidencia y documentación

- Usa datos ficticios. No guardes secretos, enlaces reales, cuerpos personales ni copias de pacientes en archivos, registros o pruebas.
- Ejecuta las comprobaciones pertinentes de la tarea. Para integridad y concurrencia usa PostgreSQL real aislado; SQLite no acredita esas reglas.
- Separa documentación comprobada, pruebas locales, integración con consumidores y pruebas de operación. No declares una función hecha por describirla.
- Entrega qué cambió, por qué, evidencia y límites pendientes. Actualiza el plan después de comprobar, sin marcar aceptación del usuario por tu cuenta.
- Conserva una sola fuente editable por contrato. Los artefactos generados y las copias de consulta deben indicar origen y versión.
- Si el usuario comienza en inglés, responde en inglés salvo que pida español. En inglés aplica ASD-STE100. En ambos idiomas usa palabras cortas, voz activa y frases directas, sin figuras retóricas.
