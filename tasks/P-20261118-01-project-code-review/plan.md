# P-20261118-01 · Revisión y refactorización de Nightingale API

**Estado:** In progress. **Creado:** 2026-11-18. **Actualizado:** 2026-11-20.

[Revisión de críticos](review.md#críticos) · [Medianos y menores](review.md#tercera-revisión--medianos-y-menores) · [Código que se puede simplificar](review.md#cuarta-revisión--código-que-se-puede-simplificar) · [Reutilización, variables y constantes](review.md#quinta-revisión--reutilización-variables-y-constantes) · [Tareas y verificación](todo.md)

## Resultado y alcance

Revisar el código actual de todo el repositorio sin usar diffs de Git. Clasificar fallos por su efecto. Corregir primero la integridad y el acceso a datos, después reducir código duplicado de persistencia y por último simplificar las funciones largas. Conservar los límites entre componentes, los contratos públicos y la atomicidad. Toda corrección que cambie un contrato requiere evidencia y una decisión expresa.

El alcance incluye `src`, `scripts`, pruebas, soporte, configuración y migraciones. La revisión incluye las migraciones publicadas. Sus correcciones se aplican mediante migraciones nuevas. El plan previo [P-20261116-01](../P-20261116-01-clinical-review-refactor/plan.md) queda como antecedente cerrado. [Etapa clínica 3](../P-20261117-05-clinical-stage-3/plan.md) tiene C12 pendiente. En C01 el usuario decidió que las correcciones compartidas repitan las comprobaciones clínicas afectadas antes de ese cierre, sin cambiar su estado.

La segunda revisión del 2026-11-18 se limita a críticos. Conserva CR-01 y añade CR-02 a CR-05, confirmados por HTTP y PostgreSQL Test. Prioriza estos casos antes de retomar C03 y conserva el trabajo pendiente de las tres etapas. C01 completó la lectura manual de T02/T03 y queda pendiente de revisión del usuario. Las tareas de corrección siguen pendientes de ejecución.

La tercera revisión del 2026-11-18 es superficial y añade ME-10 a ME-14 y MN-04 a MN-06. C17 a C19 cubren errores del lote, filtros y paginación, versiones de plantilla, cierre de clientes S3 y fallos localizados de cálculo, datos opcionales y trazas. Las tareas incluyen comprobaciones focales y se sitúan entre C06 y el inicio de la etapa 2.

La cuarta revisión del 2026-11-18 añade RF-01 a RF-10. Aprovecha tareas existentes para el despacho, los DAOs y los casos clínicos. C20 a C22 cubren el trabajo repetido de permisos y persistencia, las capacidades sin consumidor y el código común de rutas y sesiones.

La quinta revisión añade RG-01 a RG-13 tras inventariar todo el código Python. C23 trata la diferencia entre ausencia y `null` en la huella de las correcciones de medición. C24 a C27 reúnen la paginación, las constantes del protocolo, los formatos, los cálculos clínicos y el soporte de pruebas. T23, T25 y T27 incorporan los límites publicados y los cambios de variables de aceptación.

## Fuentes y reglas

- [Especificación](../../docs/nightingale-api.md), [decisiones](../../docs/decisions.md), [arquitectura](../../docs/architecture.md), [esquema SQL](../../docs/database-schema.md), [API v1](../../docs/api-v1.md) y [contratos](../../docs/contracts.md).
- **Crítico** si puede atribuir o exponer datos privados fuera de su ámbito, causar pérdida de datos o comprometer una operación esencial. **Mediano** si da resultados incorrectos en un flujo acotado, impide un uso concreto o incumple un límite. **Menor** si el efecto es localizado o la deuda aumenta el costo de mantener el código. Cada hallazgo registra evidencia, consecuencia y prueba de cierre.
- **Relaciones.** SQLAlchemy 2.1.6. Usar `relationship()` con claves compuestas cuando simplifique un recorrido real. Expresar las FK en PostgreSQL, controlar la carga en DAO y comprobar el número de consultas y la cardinalidad. Mantener DAO específico para las consultas paginadas, bloqueos y reglas cuando hagan falta. [Uniones de relaciones](https://docs.sqlalchemy.org/en/21/orm/join_conditions.html) · [Carga explícita en modo asíncrono](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession)
- **Reloj y sellos.** La consulta de hora en Python reutiliza `src.core.utils.utils.datetime_now()`, por decisión expresa del usuario el 2026-11-20; no se consulta el reloj a PostgreSQL. Los modelos con sellos heredan `Date`; `CreatedDate` y `UpdatedDate` cubren las tablas con un solo sello. Los atributos Python `date_added`/`date_updated` se mapean a las columnas físicas `created_at`/`updated_at`. `insert_default` y `onupdate` ejecutan `datetime_now()`; los defaults contextuales de INSERT reutilizan el otro sello para conservar `updated_at>=created_at`. PostgreSQL mantiene `DEFAULT CURRENT_TIMESTAMP` como fallback de alta, sin triggers de UPDATE. Un instante explícito compartido por efecto, historial, recibo y journal se conserva. No se usa `default_factory` porque la conversión de todos los modelos a dataclasses vuelve obligatorios campos que antes solo tenían `server_default`. [Mixins declarativos](https://docs.sqlalchemy.org/en/21/orm/declarative_mixins.html#mixing-in-columns) · [Defaults Python y contexto](https://docs.sqlalchemy.org/en/21/core/defaults.html#context-sensitive-default-functions) · [Dataclasses y constructores](https://docs.sqlalchemy.org/en/21/orm/dataclasses.html#using-mixins-and-abstract-superclasses)
- **Reutilización.** Poner las constantes técnicas compartidas en `src/core/constants.py`. Compartir valores cuando representen la misma regla y deban cambiar juntos. Mantener reglas clínicas y de autorización en sus dueños, valores operativos en la configuración y constantes históricas en su migración. Revisar si se puede eliminar código antes de añadir una función genérica. Medir líneas y consultas antes y después.
- **Simplificación.** Empezar por retirar código con evidencia de falta de usos, y luego unificar fragmentos que cumplan el mismo propósito, con iguales tipos y efectos. Revisar puntos de entrada, importaciones, pruebas y superficie pública. Conservar los contratos, límites de transacción y los ejemplos que el proyecto usa como referencia. Medir consultas y reconstrucciones del catálogo en los recorridos que las repiten.
- **Lectura.** Máximo de 70 líneas físicas desde la declaración hasta la última línea del cuerpo. Incluye funciones anidadas. Aplicar a código activo, pruebas y migraciones nuevas. Dividir por pasos con una responsabilidad observable. Evitar compactar líneas o mover ramas completas a helpers de nombre genérico.

## Orden de trabajo

1. Completar la revisión de fuentes y obtener una decisión en C01. Corregir CR-01 en C02. Seguir con el conjunto vigente de resultados de informes en C13, las transiciones de especialidad en C14, la conservación y validación de valores en C15 y la verificación conjunta en C16. Retomar C03 después de revisar C16. Ejecutar C17 a C19 después de C06. Tratar la huella de correcciones y sus recibos antiguos en C23 antes de compartir el código que la calcula.
2. Probar relaciones, DAOs, relojes y constantes mediante cambios acotados. Completar C20 a C22 con medición, retiro de código y reducción del código común. Ejecutar C24 a C27 por regla y componente. Comprobar compatibilidad de datos anteriores y contratos en cada bloque.
3. Dividir flujos por función y componente. Empezar por aceptación, seguir con los casos de uso y cerrar con el inventario de funciones restantes.

Trabajar un bloque por vez. En tareas que nombren varios dueños o superen cinco archivos, detallar subtareas por archivo y recorrido antes de editar el primer bloque. Registrar comandos y resultados en [todo.md](todo.md). El usuario revisa cada checkpoint.

## Riesgos que requieren comprobación

| Riesgo | Comprobación |
|---|---|
| Datos anteriores con vínculos inválidos o historia incompleta | Contar y clasificar referencias antes de validar la FK. Acordar reparación antes de cambiar datos existentes. |
| Un informe corregido todavía presenta resultados previos como vigentes | Resolver la diferencia entre el payload publicado y la regla clínica. Confirmar nueva versión, retiro y alta de resultados, historia, recibo y delta en una transacción. |
| La historia o el estado vigente de especialidad pierde valores | Comprobar edición parcial, retiro, anulación y lectura por versión. Detectar datos anteriores con tipos incompatibles y reconstruir solo desde evidencia verificable con una corrección trazable. |
| Relaciones que cargan de más o amplían el ámbito | Medir consultas, probar dos cuentas y dos fichas, conservar filtro y bloqueo en SQL. |
| Cambios de reloj o de orden | Comparar sello en fila, historial, recibo y journal con PostgreSQL y dos conexiones. |
| Ruptura de sincronización al dividir funciones | Probar claves idempotentes antiguas, cambios agrupados completos y rollback ante fallo de persistencia o serialización. |
| Un recibo anterior conserva una huella que confunde omisión y `null` | Probar por acción ambas formas y los reintentos idénticos con recibos de ambas versiones. Acordar qué hacer cuando la huella anterior no permite distinguir el payload original. |
| Límites publicados o revisiones de modelo distintos de los aplicados | Comparar capacidades, validación, PostgreSQL y artefactos generados según la regla. Comprobar la lectura de capturas previas. |
| Compartir fechas, códigos o cálculos que siguen reglas distintas | Comparar por recurso formatos admitidos, ausencia y `null`, precisión, mensajes, datos limítrofes y salida pública antes de adoptar cada función común. |
| Cambios con impacto en consumidores | Comparar JSON y casos publicados. Registrar las corridas de Rust y del Hub que correspondan. |
