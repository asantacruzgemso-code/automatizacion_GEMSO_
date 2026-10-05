# Arquitectura técnica del middleware SAP Business One ↔ Xternall

## 1. Objetivo

Desarrollar un middleware independiente que funcione como capa de integración y seguridad entre las instancias SAP Business One de GEMSO y el portal de proveedores Xternall.

La solución debe permitir:

- consultar registros pendientes en SAP Business One mediante el campo `U_SYNC`
- transformar y validar la información antes de enviarla a Xternall
- hacer upsert de proveedores, órdenes de compra, recepciones y pagos
- recibir webhooks de Xternall para facturas y complementos de pago
- registrar datos en SAP Business One sin exponer directamente el Service Layer a Internet
- mantener trazabilidad, seguridad, reintentos y auditoría de todas las operaciones

## 2. Alcance funcional

### 2.1 Flujos SAP → Xternall

El middleware debe ejecutar sincronizaciones periódicas por proceso:

- Proveedores: cada 60 minutos (configurable)
- Órdenes de compra: cada 10 minutos (configurable)
- Entradas de mercancía: cada 10 minutos (configurable)
- Pagos efectuados: cada 30 minutos (configurable)

Regla general:

- consultar registros con `U_SYNC = tYES`
- validar `CompanyDB`
- transformar al contrato de Xternall
- consultar si existe el registro en Xternall
- crear o actualizar según corresponda
- confirmar éxito antes de marcar `U_SYNC = tNO`
- mantener el registro pendiente si ocurre un error

### 2.2 Flujos Xternall → SAP

El middleware debe exponer endpoints propios para recibir solicitudes de Xternall:

- Factura de proveedor
- Complemento de pago

Estas solicitudes deben:

- autenticarse
- validar el payload
- identificar `CompanyDB`
- validar identidad del proveedor y documento
- crear o actualizar la factura o complemento en la instancia SAP correcta
- registrar el resultado en la bitácora y el estado del proceso

## 3. Arquitectura general

La arquitectura queda diseñada en tres capas:

1. SAP Business One / Service Layer
2. Middleware de integración
3. Xternall

### 3.1 Capa 1: SAP Business One

- cada compañía/instancia SAP tiene una conexión independiente
- cada conexión se identifica por `CompanyDB`
- el acceso se realiza a través del Service Layer
- el middleware se conecta de forma segura mediante HTTPS
- el Service Layer completo no se expone directamente a Internet

### 3.2 Capa 2: Middleware de integración

Este componente será la pieza central del sistema y debe estar implementado sobre la tecnología base actual del proyecto:

- Frontend: Vue 3 + Vite
- Backend: FastAPI
- Base de datos: PostgreSQL
- Contenedores: Docker / Dev Containers

El middleware debe incluir los siguientes módulos:

#### a) API REST

- endpoints para health checks
- endpoints para webhooks de Xternall
- endpoints administrativos
- endpoints de consulta de llamadas, reintentos y configuración

#### b) Scheduler / workers

- procesamiento de polling para SAP → Xternall
- ejecución periódica por proceso
- reintento programado con backoff
- ejecución manual por proceso

#### c) Servicios de integración SAP

- cliente HTTP para Service Layer
- resolución de `CompanyDB`
- lectura de entidades SAP
- actualización de `U_SYNC`
- manejo de errores SAP

#### d) Servicios de integración Xternall

- cliente HTTP para APIs externas
- validación de payloads
- upsert y manejo de respuestas
- control de duplicados y idempotencia

#### e) Motor de validación y transformación

- mapas entre SAP y Xternall
- validación de RFC, fechas, montos, currency, CompanyDB
- normalización de payloads
- comprobación de campos requeridos

#### f) Persistencia central

- conexiones SAP
- conexiones Xternall
- configuración por proceso
- eventos de sincronización
- estados de operación
- requests y responses
- reintentos y auditoría

#### g) Visor administrativo

- vista de llamadas
- filtros por fecha, CompanyDB, proceso, estado, correlación
- detalle de request/response
- reintento manual
- configuración operativa

### 3.3 Capa 3: Xternall

- API de proveedores y documentos
- recepción de webhooks
- origen de eventos para facturas y complementos de pago
- validación de integridad del documento y del flujo

## 4. Multiempresa y CompanyDB

Este requisito es crítico para la solución.

Cada evento debe contener `CompanyDB` y el middleware debe:

- resolver la compañía correcta
- consultar únicamente la instancia SAP asociada
- no mezclar datos entre compañías
- transportar el identificador técnico en todas las operaciones

Se debe mantener una configuración segura por compañía con:

- URL del Service Layer
- base de datos
- usuario técnico
- credenciales cifradas
- parámetros adicionales de conexión

## 5. Idempotencia y control de concurrencia

La solución debe ser idempotente para evitar duplicados.

Se recomienda usar una clave de correlación compuesta por:

- `CompanyDB`
- tipo de objeto
- identificador del documento (por ejemplo `DocEntry` o `CardCode`)

Reglas clave:

- no se debe marcar `U_SYNC = tNO` antes de confirmación satisfactoria
- si una operación no tiene respuesta definitiva, debe evaluarse como indeterminada
- si hay reintento, debe validarse duplicidad antes de crear nuevamente
- cada operación debe dejar trazabilidad de correlación

## 6. Arquitectura funcional por flujo

### 6.1 SAP → Xternall: proveedores

- consulta BusinessPartners con `U_SYNC=tYES`
- validación de CompanyDB y datos mínimos
- transformacion de `CardCode`, `CardName`, `RFC`, `EmailAddress`, etc.
- upsert en Xternall usando la clave funcional de empresa + proveedor
- confirmación de Xternall
- actualización de `U_SYNC=tNO` en SAP

### 6.2 SAP → Xternall: órdenes de compra

- consulta PurchaseOrders con `U_SYNC=tYES`
- lectura de cabecera y líneas
- transformación al contrato de Xternall
- validación de proveedor, importes y moneda
- upsert de la orden y sus líneas
- confirmación y actualización de `U_SYNC=tNO`

### 6.3 SAP → Xternall: entradas de mercancía

- consulta PurchaseDeliveryNotes con `U_SYNC=tYES`
- lectura de cabecera y líneas
- relación documental con la OC usando:
  - `BaseType`
  - `BaseEntry`
  - `BaseLine`
- validación de relación con `PurchaseOrders`
- upsert en Xternall
- actualizar `U_SYNC=tNO` si el proceso termina bien

### 6.4 SAP → Xternall: pagos

- consulta VendorPayments con `U_SYNC=tYES`
- lectura del pago y sus aplicaciones
- control de 1:N entre pago y facturas
- transformación del payload a Xternall
- validación con `CompanyDB` y `DocEntry`
- confirmación y posterior actualización de `U_SYNC=tNO`

### 6.5 Xternall → SAP: facturas

- webhook de factura recibe CompanyDB, proveedor, documentos, XML/PDF, etc.
- middleware valida autenticación y payload
- identifica la integración SAP correcta
- valida duplicidad con UUID o idempotency key
- crea o actualiza la factura en SAP
- persiste resultado y estado del evento

### 6.6 Xternall → SAP: complemento de pago

- webhook recibe información del complemento y archivos XML/PDF
- middleware identifica `CompanyDB`
- valida el pago asignado en SAP
- registra el complemento en la tabla o entidad SAP asociada
- deja auditoría del flujo y mensajes de error

## 7. Seguridad

El middleware debe ser la frontera de seguridad entre SAP y Xternall.

Se deben contemplar como mínimo:

- HTTPS y TLS obligatorios
- autenticación para clientes y webhooks externos
- tokens JWT/OAuth u otro mecanismo aprobado
- almacenamiento seguro de credenciales
- no incluir secretos en código, logs ni archivos de configuración visibles
- protección contra replay y duplicados
- auditoría por usuario, fecha, operación, instancia y resultado

## 8. API del middleware

Debe entregarse una API REST documentada con OpenAPI/Swagger.

### 8.1 Endpoints sugeridos

- `GET /health`
- `GET /ready`
- `POST /api/v1/xternall/invoices`
- `POST /api/v1/xternall/payment-complements`
- `POST /api/v1/admin/sync/{process}`
- `GET /api/v1/admin/calls`
- `GET /api/v1/admin/calls/{id}`
- `POST /api/v1/admin/calls/{id}/retry`

Estos nombres son conceptuales; el contrato final se debe definir con detalle de:

- método HTTP
- headers
- autenticación
- payloads
- respuestas
- códigos HTTP
- errores
- versionamiento

## 9. Visor web y bitácora

La solución debe incluir un visor administrativo con módulos y funciones como:

- LLAMADAS
- CONFIGURACIÓN
- BITÁCORA
- USUARIO
- CONEXIONES

Funciones esperadas:

- listar llamadas realizadas
- mostrar request y response
- mostrar request y response con datos sensibles enmascarados
- filtrar por CompanyDB, proceso, tipo, estado, código HTTP, correlación
- ver tiempos de ejecución
- reintentar operaciones fallidas
- consultar configuración y periodicidades
- consultar estado de conexión SAP y Xternall

## 10. Manejo de errores y reintentos

Debe definirse una política de errores clara:

- `2xx`: éxito
- `4xx`: error funcional; no marcar `U_SYNC=tNO`
- `401/403`: incidente de autenticación/autorización
- `408/429`: reintento con backoff
- `5xx`: reintento con backoff
- timeout: considerar indeterminado y validar idempotencia
- error SAP: guardar código y detalle, mantener pendiente

Reglas:

- no repetir indefinidamente credenciales inválidas
- no generar tormentas de reintentos
- mantener el estado del evento en base de datos
- permitir reintento administrativo controlado

## 11. Persistencia propuesta

La base de datos del middleware debe guardar al menos estas entidades:

- `companies` o `sap_companies`
- `connections`
- `processes`
- `configs`
- `integration_events`
- `call_logs`
- `retries`
- `audit_logs`

### Entidad principal sugerida: `integration_events`

Debe contener:

- id correlación
- CompanyDB
- tipo de proceso
- tipo de objeto
- identificador SAP
- payload de entrada
- payload de salida
- status
- http_code
- fecha de creación
- fecha de procesamiento
- última modificación

## 12. Estructura sugerida del proyecto

```text
project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── routes/
│   │   │   │   └── schemas/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   │   ├── sap/
│   │   │   ├── xternall/
│   │   │   ├── jobs/
│   │   │   └── sync/
│   │   ├── db/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── docs/
│   ├── architecture.md
│   ├── requirements.md
│   └── api.md
├── .devcontainer/
│   ├── docker-compose.yml
│   └── devcontainer.json
└── README.md
```

## 13. Criterios de aceptación del sistema

- un proveedor nuevo con `U_SYNC=tYES` se publica una sola vez en Xternall
- un cambio en proveedor con `U_SYNC=tYES` se actualiza sin duplicar
- una OC nueva y sus líneas se sincronizan correctamente
- una recepción parcial conserva relación documental con `BaseEntry`, `BaseLine` y `BaseType`
- una recepción múltiple se procesa sin perder trazabilidad
- un pago parcial conserva la relación con la factura correspondiente
- un webhook duplicado no crea una segunda factura
- Xternall no puede invocar directamente SAP Service Layer
- cada compañía procesa solo su `CompanyDB`
- la solución deja evidencia completa de operaciones, errores y reintentos

## 14. Conclusión

La solución debe ser un middleware de integración reutilizable, multiempresa y seguro, construido sobre FastAPI, PostgreSQL y Vue, con capacidad de orquestar polling y webhooks, mantener trazabilidad de cada operación y garantizar que SAP y Xternall se comuniquen sin exponer directamente el Service Layer ni romper el principio de idempotencia.
