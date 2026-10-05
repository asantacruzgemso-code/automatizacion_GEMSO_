# Requerimientos técnicos y funcionales del middleware

## 1. Información general

Proyecto: Middleware de integración SAP Business One ↔ Xternall

Tecnologías base del entorno:

- Frontend: Vue 3 + Vite
- Backend: FastAPI
- Base de datos: PostgreSQL
- Entorno de desarrollo: Docker / Dev Containers

## 2. Objetivo del sistema

Crear un middleware independiente que sirva como capa de integración y seguridad entre las instancias SAP Business One de GEMSO y el portal de proveedores Xternall.

El sistema debe permitir:

- sincronizar datos de SAP hacia Xternall
- recibir y validar eventos de Xternall dirigidos a SAP
- diferenciar instancias por `CompanyDB`
- mantener trazabilidad, seguridad y reintentos

## 3. Requisitos funcionales

### 3.1 SAP → Xternall

El middleware debe consultar por proceso y publicar los cambios pendientes en Xternall:

- proveedores
- órdenes de compra
- entradas de mercancía
- pagos efectuados

Reglas:

- solo procesar registros con `U_SYNC = tYES`
- validar `CompanyDB`
- transformar los datos al esquema de Xternall
- asegurar upsert
- actualizar `U_SYNC = tNO` solo cuando el proceso termine correctamente
- mantener registro pendiente si hay error

### 3.2 Xternall → SAP

El middleware debe exponer APIs para recibir eventos provenientes de Xternall:

- facturas de proveedor
- complemento de pago

Reglas:

- autenticar la solicitud
- validar payload y firma/autenticación
- identificar `CompanyDB`
- validar proveedor/documento antes de registrar en SAP
- registrar en SAP sin pasar por acceso directo del Service Layer
- registrar eventos en la bitácora del middleware

### 3.3 Multiempresa

El sistema debe administrar múltiples instancias SAP y no mezclar información entre compañías.

Se debe cumplir:

- cada solicitud incluye `CompanyDB`
- cada operación se enruta a la conexión SAP correcta
- la clave lógica del negocio debe considerar `CompanyDB`
- la configuración de cada compañía debe almacenarse de forma segura

### 3.4 Idempotencia

El middleware debe garantizar que una misma operación no se procese dos veces.

Se debe implementar:

- correlación por CompanyDB + tipo de operación + identificador del documento
- prevención de duplicados
- validación antes de crear un registro duplicado
- tratamiento de respuestas indeterminadas

## 4. Requisitos no funcionales

### 4.1 Seguridad

- HTTPS/TLS obligatorio
- autenticación de clientes externos
- JWT/OAuth o mecanismo equivalente aprobado
- almacenamiento seguro de secretos
- rotación de secretos
- auditoría de acciones
- no exponer el Service Layer completo a Internet

### 4.2 Operación

- periodicidades configurables sin recompilar
- habilitar/deshabilitar procesos
- ejecución manual de sincronización
- reintentos automáticos con backoff
- registro de estados de operación
- auditoría administrativa

### 4.3 Observabilidad

- request/response completos con enmascaramiento de datos sensibles
- métricas básicas de éxito/error
- correlación por operación
- filtros por fecha, proceso, CompanyDB, estado y correlación

### 4.4 Persistencia

- persistencia propia del middleware
- no usar SAP como base de datos operativa del middleware
- almacenar:
  - conexiones
  - procesos
  - periodicidades
  - eventos
  - reintentos
  - auditoría
  - errores

## 5. Requisitos de negocio por flujo

### 5.1 Proveedores

- consultar BusinessPartners con `U_SYNC = tYES`
- mapear a contrato Xternall
- validar RFC, CardCode, CompanyDB y estado del proveedor
- hacer upsert en Xternall
- si la operación resulta exitosa, marcar `U_SYNC = tNO`

### 5.2 Órdenes de compra

- consultar PurchaseOrders pendientes
- transportar cabecera y líneas
- respetar `DocEntry`, `DocNum`, `CardCode`, monedas, importes y estados
- publicar en Xternall y actualizar `U_SYNC`

### 5.3 Entradas de mercancía

- consultar PurchaseDeliveryNotes pendientes
- conservar relación con la OC mediante:
  - `BaseType`
  - `BaseEntry`
  - `BaseLine`
- soportar múltiples recepciones por compra
- no asumir relación 1:1

### 5.4 Pagos efectuados

- consultar VendorPayments pendientes
- soportar relación 1:N con facturas
- preservar vínculo técnico entre pago y factura
- notificar `SumApplied`
- actualizar `U_SYNC` solo al confirmar éxito

### 5.5 Facturas Xternall → SAP

- recibir request con CompanyDB y proveedor
- validar factura y XML/PDF
- identificar la instancia SAP correcta
- crear o actualizar la factura
- manejar duplicidad por UUID o idempotency key

### 5.6 Complemento de pago

- recibir complemento con archivos XML/PDF
- identificar CompanyDB
- asociar al pago SAP correspondiente
- registrar la información en la entidad SAP indicada

## 6. Requisitos del visor

El visor debe permitir:

- consultar llamadas realizadas
- ver request y response
- filtrar por fecha, CompanyDB, proceso, estado y correlación
- consultar reintentos
- ejecutar reintento manual autorizado
- consultar conexiones y configuración
- ver auditoría de eventos administrativos

## 7. Requisitos de error y reintento

Se debe definir tratamiento explícito para:

- `2xx`: éxito
- `4xx`: error funcional
- `401/403`: autenticación/autorización
- `408/429`: reintento automático con backoff
- `5xx`: reintento automático con backoff
- timeout: procesamiento indeterminado
- errores SAP: guardar detalle y mantener pendiente

No debe permitirse:

- reintentos infinitos por credenciales inválidas
- duplicidad de registros por procesamiento concurrente
- marcación prematura de `U_SYNC = tNO`

## 8. Entregables mínimos esperados

- código fuente del middleware
- API REST documentada con OpenAPI/Swagger
- modelo de base de datos y migraciones
- visor web administrativo
- diseño de seguridad y gestión de secretos
- configuración operativa
- pruebas unitarias e integración
- documentación técnica de instalación y operación

## 9. Criterios de aceptación

- se procesa proveedor con `U_SYNC=tYES` y solo se publica una vez
- el sistema puede procesar varios `CompanyDB` sin mezclarlos
- Ordenes de compra, recepciones y pagos se sincronizan con trazabilidad documental
- un webhook duplicado no genera una segunda factura
- errores de Xternall dejan el registro pendiente
- la operación se puede consultar y reintentar desde el visor
- Xternall no accede directamente al Service Layer de SAP

## 10. Conclusión

El sistema debe funcionar como un middleware de integración seguro, multiempresa y reutilizable, con FastAPI como base de backend, PostgreSQL como persistencia y Vue como interfaz administrativa. El principal eje del diseño es preservar idempotencia, trazabilidad y separación por CompanyDB para evitar errores en sincronización y procesamiento de eventos.
