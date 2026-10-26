# Requisitos de calidad y estrategia de pruebas

**Estado:** identidad, lecturas propias, aceptación técnica, equipo/cuenta/auditoría y pacientes/contactos T13–T15 comprobados para revisión C05. Servicios, agenda/citas, descarga y operación siguen pendientes. La [guía de desarrollo](operations/development.md) distingue pruebas locales, integración real PostgreSQL/Keycloak y límites de consumidores/operación. **R** indica un requisito confirmado por el encargo/especificación; **P**, una técnica de prueba propuesta; **A**, una decisión abierta en [el registro](decisions.md).

## Requisitos verificables

| ID / estado | Condición de aceptación | Comprobación futura y evidencia |
|---|---|---|
| Q01 · R | Cada entrada comprueba cuenta, objeto, acción y acceso vigente; no revela datos ajenos en éxito, error, resultado previo o página | A/B con IDs cruzados en HTTP, repositorios, workers, n8n, snapshots e indicadores; verificar respuesta y estado persistido |
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
| Cuenta A envía un objeto de B o Hub usa concesión de otra cita | Sin lectura, escritura ni filtración del resultado | T08, T14, T15 |
| Ejecutable modificado omite validación Rust | API rechaza transición, referencia o permiso inválido | T12, T14 |
| Dos conexiones reservan o modifican agenda/cita | Solo un estado compatible; conflicto explícito y sin pérdida de historial | T11, T12, T14 |
| Duplicados, distinta carga y respuesta perdida | Mismo resultado permitido y un efecto; conflicto para distinto contenido | T12, T14 |
| Revocación con pendientes y reloj cambiado | Política aprobada aplicada con evidencia del servidor; intención conservada por el consumidor | T04, T08, T14, T23 |
| Paginación con commits invertidos, bajas y recuperación inicial | Sin omisiones; snapshot/cursor coherentes y recuperación explícita | T05, T13, T14 |
| Hub cancela mientras escritorio reprograma/confirma | La versión impide sobrescritura; respuesta perdida se concilia | T15, T23 |
| Worker cae y proveedor recibió un envío sin responder | Trabajo recuperable y resultado desconocido visible; sin repetición ciega | T16, T17, T18 |

Los controles completos de Q01–Q16 siguen pendientes; T03 no acredita seguridad, integridad ni operación con PostgreSQL real. Las comprobaciones documentales iniciales se registran aparte en [fuentes y revisión](sources.md).
