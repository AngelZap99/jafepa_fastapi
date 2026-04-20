# Backend API Reference

Documento generado desde el backend actual para compartir con frontend. La intención es que funcione como referencia tipo Swagger, pero en Markdown.

## Convenciones Generales

- Base URL: `/api`
- Endpoints públicos: `POST /api/auth/login` y `POST /api/auth/refresh`.
- Todos los demás endpoints requieren `Authorization: Bearer <access_token>`.
- Requests JSON usan `Content-Type: application/json`.
- Endpoints con imágenes usan `multipart/form-data`.
- Endpoints PDF responden `application/pdf` con header `Content-Disposition` para descarga.
- Los `datetime` salen en UTC con offset explícito, por ejemplo `2026-04-17T12:00:00+00:00`.
- Los campos monetarios/decimales en respuestas suelen serializarse como `string` para preservar precisión.
- En requests, los decimales normalmente pueden enviarse como número o string; los ejemplos usan el formato más legible posible.
- Los campos `image` siguen siendo URLs públicas. Actualmente el backend sirve esas imágenes localmente bajo `/media/...` en el mismo host del API.

### Contrato de Error

Todas las rutas usan el mismo shape de error a nivel runtime:

```json
{
  "message": "Texto principal del error",
  "errors": [
    {
      "field": "campo.opcional",
      "message": "detalle del error",
      "code": "codigo.opcional"
    }
  ]
}
```

### Headers Comunes

| Header | Valor | Cuándo aplica |
|---|---|---|
| `Authorization` | `Bearer <access_token>` | Todos los endpoints protegidos |
| `Content-Type` | `application/json` | Requests JSON |
| `Content-Type` | `multipart/form-data` | Endpoints con archivo/imagen |
| `Accept` | `application/pdf` | Descarga de PDFs |

## Índice de Módulos

| Módulo | Endpoints |
|---|---:|
| Autenticación (`auth`) | 2 |
| Usuarios (`users`) | 8 |
| Clientes (`clients`) | 5 |
| Almacenes (`warehouses`) | 5 |
| Categorías (`categories`) | 5 |
| Marcas (`brands`) | 5 |
| Productos (`products`) | 6 |
| Facturas (`invoices`) | 6 |
| Líneas de Factura (`invoice-lines`) | 4 |
| Inventario (`inventory`) | 8 |
| Ventas (`sales`) | 11 |
| BFF / Dashboard (`bff`) | 1 |

## Autenticación

### POST `/api/auth/login`

- Descripción: Login
- Auth: No

**Headers**

- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `LoginRequest`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "email": "usuario@ejemplo.com",
  "password": "Password123"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `LoginResponse` |

**Ejemplo de salida**

```json
{
  "access_token": "<access_token>",
  "refresh_token": "<refresh_token>",
  "token_type": "bearer",
  "user": {
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com",
    "role": "Administrador",
    "id": 1,
    "is_active": true,
    "is_verified": true,
    "is_admin": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  }
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/auth/refresh`

- Descripción: Refresh Token
- Auth: No

**Headers**

- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `RefreshTokenRequest`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "refresh_token": "<refresh_token>"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `TokenPairResponse` |

**Ejemplo de salida**

```json
{
  "access_token": "<access_token>",
  "refresh_token": "<refresh_token>",
  "token_type": "bearer"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Usuarios

### GET `/api/users/list`

- Descripción: Get Users
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<UserResponse>` |

**Ejemplo de salida**

```json
[
  {
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com",
    "role": "Administrador",
    "id": 1,
    "is_active": true,
    "is_verified": true,
    "is_admin": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/users/me`

- Descripción: Get User Me
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

Sin parámetros.

**Body**

Sin body.

**Ejemplo de entrada**

No aplica.

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `UserResponse` |

**Ejemplo de salida**

```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador",
  "id": 1,
  "is_active": true,
  "is_verified": true,
  "is_admin": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/users/{user_id}`

- Descripción: Get User
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `user_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "user_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `UserResponse` |

**Ejemplo de salida**

```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador",
  "id": 1,
  "is_active": true,
  "is_verified": true,
  "is_admin": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/users/createUser`

- Descripción: Create User
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `UserCreate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "password": "Password123",
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `UserResponse` |

**Ejemplo de salida**

```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador",
  "id": 1,
  "is_active": true,
  "is_verified": true,
  "is_admin": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/users/createAdmin`

- Descripción: Create Admin
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `UserCreateAdmin`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "password": "Password123",
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `UserResponse` |

**Ejemplo de salida**

```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador",
  "id": 1,
  "is_active": true,
  "is_verified": true,
  "is_admin": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/users/update/{user_id}`

- Descripción: Update User
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `user_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `UserUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "password": "Password123",
  "role": "Administrador"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `UserResponse` |

**Ejemplo de salida**

```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador",
  "id": 1,
  "is_active": true,
  "is_verified": true,
  "is_admin": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PATCH `/api/users/status/{user_id}`

- Descripción: Update User Status
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `user_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `UserUpdateStatus`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `UserResponse` |

**Ejemplo de salida**

```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador",
  "id": 1,
  "is_active": true,
  "is_verified": true,
  "is_admin": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/users/delete/{user_id}`

- Descripción: Delete User
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `user_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "user_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `UserResponse` |

**Ejemplo de salida**

```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador",
  "id": 1,
  "is_active": true,
  "is_verified": true,
  "is_admin": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Clientes

### GET `/api/clients/list`

- Descripción: List Clients
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<ClientResponse>` |

**Ejemplo de salida**

```json
[
  {
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678",
    "id": 1,
    "is_active": true,
    "deleted_at": "2026-04-20T12:00:00+00:00",
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/clients/{client_id}`

- Descripción: Get Client
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `client_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "client_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `ClientResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/clients/create`

- Descripción: Create Client
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `ClientCreate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `ClientResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/clients/update/{client_id}`

- Descripción: Update Client
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `client_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `ClientUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `ClientResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/clients/delete/{client_id}`

- Descripción: Delete Client
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `client_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "client_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `ClientResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Almacenes

### GET `/api/warehouses/list`

- Descripción: List Warehouses
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<WarehouseResponse>` |

**Ejemplo de salida**

```json
[
  {
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678",
    "id": 1,
    "is_active": true,
    "deleted_at": "2026-04-20T12:00:00+00:00",
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/warehouses/{warehouse_id}`

- Descripción: Get Warehouse
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `warehouse_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "warehouse_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `WarehouseResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/warehouses/create`

- Descripción: Create Warehouse
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `WarehouseCreate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `WarehouseResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/warehouses/update/{warehouse_id}`

- Descripción: Update Warehouse
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `warehouse_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `WarehouseUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `WarehouseResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/warehouses/delete/{warehouse_id}`

- Descripción: Delete Warehouse
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `warehouse_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "warehouse_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `WarehouseResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Categorías

### GET `/api/categories/list`

- Descripción: List Categories
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<CategoryResponse>` |

**Ejemplo de salida**

```json
[
  {
    "name": "Nombre de ejemplo",
    "description": "Descripción de ejemplo",
    "is_active": true,
    "id": 1,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/categories/{category_id}`

- Descripción: Get Category
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `category_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "category_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `CategoryResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "description": "Descripción de ejemplo",
  "is_active": true,
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/categories/create`

- Descripción: Create Category
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `CategoryCreate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "name": "Nombre de ejemplo",
  "description": "Descripción de ejemplo",
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `CategoryResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "description": "Descripción de ejemplo",
  "is_active": true,
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/categories/update/{category_id}`

- Descripción: Update Category
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `category_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `CategoryUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "name": "Nombre de ejemplo",
  "description": "Descripción de ejemplo",
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `CategoryResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "description": "Descripción de ejemplo",
  "is_active": true,
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/categories/delete/{category_id}`

- Descripción: Delete Category
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `category_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "category_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `CategoryResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "description": "Descripción de ejemplo",
  "is_active": true,
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Marcas

### GET `/api/brands/list`

- Descripción: List Brands
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<BrandResponse>` |

**Ejemplo de salida**

```json
[
  {
    "name": "Nombre de ejemplo",
    "id": 1,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "deleted_at": "2026-04-20T12:00:00+00:00",
    "is_active": true
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/brands/{brand_id}`

- Descripción: Get Brand
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `brand_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "brand_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `BrandResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "is_active": true
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/brands/create`

- Descripción: Create Brand
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `BrandCreate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "name": "Nombre de ejemplo"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `BrandResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "is_active": true
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/brands/update/{brand_id}`

- Descripción: Update Brand
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `brand_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `BrandUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "name": "Nombre de ejemplo",
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `BrandResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "is_active": true
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/brands/delete/{brand_id}`

- Descripción: Delete Brand
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `brand_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "brand_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `BrandResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "is_active": true
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Productos

### GET `/api/products/list`

- Descripción: List Products
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<ProductResponse>` |

**Ejemplo de salida**

```json
[
  {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1,
    "image": "https://ejemplo.com/imagen.webp",
    "id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "category": {
      "id": 1,
      "name": "Nombre de ejemplo"
    },
    "brand": {
      "id": 1,
      "name": "Nombre de ejemplo"
    }
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/products/create`

- Descripción: Create Product
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: multipart/form-data`
- Schema: `Body_create_product_api_products_create_post`

**Ejemplo de entrada**

- Ejemplo de `multipart/form-data`:
```json
{
  "image_file": "(binary)",
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `ProductResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp",
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "category": {
    "id": 1,
    "name": "Nombre de ejemplo"
  },
  "brand": {
    "id": 1,
    "name": "Nombre de ejemplo"
  }
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/products/update/{product_id}`

- Descripción: Update Product
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `product_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: multipart/form-data`
- Schema: `Body_update_product_api_products_update__product_id__put`

**Ejemplo de entrada**

- Ejemplo de `multipart/form-data`:
```json
{
  "image_file": "(binary)",
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp",
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `ProductResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp",
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "category": {
    "id": 1,
    "name": "Nombre de ejemplo"
  },
  "brand": {
    "id": 1,
    "name": "Nombre de ejemplo"
  }
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/products/delete/{product_id}`

- Descripción: Delete Product
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `product_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "product_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `ProductResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp",
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "category": {
    "id": 1,
    "name": "Nombre de ejemplo"
  },
  "brand": {
    "id": 1,
    "name": "Nombre de ejemplo"
  }
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/products/list-stock`

- Descripción: List Products With Stock
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `warehouse_id` | `query` | `integer` | Sí | `` |  |
| `search` | `query` | `string | null` | No | `` |  |
| `only_in_stock` | `query` | `boolean` | No | `False` |  |
| `include_inactive` | `query` | `boolean` | No | `True` |  |
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "warehouse_id": 1,
    "search": "Texto de ejemplo",
    "only_in_stock": true,
    "include_inactive": true,
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<ProductStockResponse-Output>` |

**Ejemplo de salida**

```json
[
  {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1,
    "image": "https://ejemplo.com/imagen.webp",
    "id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "category": {
      "id": 1,
      "name": "Nombre de ejemplo"
    },
    "brand": {
      "id": 1,
      "name": "Nombre de ejemplo"
    },
    "stock_total": 25,
    "stock_boxes_total": 25,
    "inventory": [
      {
        "id": 1,
        "warehouse_id": 1,
        "product_id": 1,
        "box_size": 12,
        "stock": 25,
        "reserved_stock": 3,
        "available_boxes": 22,
        "avg_cost": "125.50",
        "last_cost": "125.50",
        "sales_last_price": 125.5,
        "sales_avg_price": 125.5,
        "is_active": true,
        "is_over_reserved": true
      }
    ]
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/products/{product_id}`

- Descripción: Get Product
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `product_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "product_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `ProductResponse` |

**Ejemplo de salida**

```json
{
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp",
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "category": {
    "id": 1,
    "name": "Nombre de ejemplo"
  },
  "brand": {
    "id": 1,
    "name": "Nombre de ejemplo"
  }
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Facturas

### GET `/api/invoices/list`

- Descripción: List Invoices
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<InvoiceResponse>` |

**Ejemplo de salida**

```json
[
  {
    "id": 1,
    "invoice_number": "FAC-001",
    "sequence": 1,
    "invoice_date": "2026-04-20",
    "order_date": "2026-04-20",
    "arrival_date": "2026-04-20",
    "status": "DRAFT",
    "dollar_exchange_rate": "125.50",
    "general_expenses": "125.50",
    "approximate_profit_rate": "125.50",
    "notes": "Texto de ejemplo",
    "warehouse_id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "warehouse": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "address": "Calle Ejemplo 123",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678"
    },
    "lines": [
      {
        "id": 1,
        "invoice_id": 1,
        "product_id": 1,
        "box_size": 12,
        "quantity_boxes": 2,
        "total_units": 24,
        "price": "125.50",
        "price_type": "UNIT",
        "inventory_applied": true,
        "is_active": true,
        "created_at": "2026-04-20T12:00:00+00:00",
        "updated_at": "2026-04-20T12:00:00+00:00",
        "product": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "code": "PROD-001"
        },
        "box_price": "125.50",
        "unit_price": "125.50",
        "total_price": "125.50"
      }
    ],
    "subtotal": "125.50",
    "general_expenses_total": "125.50",
    "approximate_profit_total": "125.50",
    "total": "125.50"
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/invoices/{invoice_id}`

- Descripción: Get Invoice
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `invoice_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "invoice_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `InvoiceResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "status": "DRAFT",
  "dollar_exchange_rate": "125.50",
  "general_expenses": "125.50",
  "approximate_profit_rate": "125.50",
  "notes": "Texto de ejemplo",
  "warehouse_id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "lines": [
    {
      "id": 1,
      "invoice_id": 1,
      "product_id": 1,
      "box_size": 12,
      "quantity_boxes": 2,
      "total_units": 24,
      "price": "125.50",
      "price_type": "UNIT",
      "inventory_applied": true,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "product": {
        "id": 1,
        "name": "Nombre de ejemplo",
        "code": "PROD-001"
      },
      "box_price": "125.50",
      "unit_price": "125.50",
      "total_price": "125.50"
    }
  ],
  "subtotal": "125.50",
  "general_expenses_total": "125.50",
  "approximate_profit_total": "125.50",
  "total": "125.50"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/invoices/create`

- Descripción: Create Invoice
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `InvoiceCreateWithLines`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "status": "DRAFT",
  "dollar_exchange_rate": 125.5,
  "general_expenses": 125.5,
  "approximate_profit_rate": 125.5,
  "notes": "Texto de ejemplo",
  "warehouse_id": 1,
  "lines": [
    {
      "product_id": 1,
      "new_product": {
        "name": "Nombre de ejemplo",
        "code": "PROD-001",
        "description": "Descripción de ejemplo",
        "category_id": 1,
        "brand_id": 1
      },
      "box_size": 12,
      "quantity_boxes": 2,
      "total_units": 24,
      "price": 125.5,
      "price_type": "UNIT"
    }
  ]
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `InvoiceResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "status": "DRAFT",
  "dollar_exchange_rate": "125.50",
  "general_expenses": "125.50",
  "approximate_profit_rate": "125.50",
  "notes": "Texto de ejemplo",
  "warehouse_id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "lines": [
    {
      "id": 1,
      "invoice_id": 1,
      "product_id": 1,
      "box_size": 12,
      "quantity_boxes": 2,
      "total_units": 24,
      "price": "125.50",
      "price_type": "UNIT",
      "inventory_applied": true,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "product": {
        "id": 1,
        "name": "Nombre de ejemplo",
        "code": "PROD-001"
      },
      "box_price": "125.50",
      "unit_price": "125.50",
      "total_price": "125.50"
    }
  ],
  "subtotal": "125.50",
  "general_expenses_total": "125.50",
  "approximate_profit_total": "125.50",
  "total": "125.50"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/invoices/update/{invoice_id}`

- Descripción: Update Invoice
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `invoice_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `InvoiceUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "dollar_exchange_rate": 125.5,
  "general_expenses": 125.5,
  "approximate_profit_rate": 125.5,
  "notes": "Texto de ejemplo",
  "warehouse_id": 1
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `InvoiceResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "status": "DRAFT",
  "dollar_exchange_rate": "125.50",
  "general_expenses": "125.50",
  "approximate_profit_rate": "125.50",
  "notes": "Texto de ejemplo",
  "warehouse_id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "lines": [
    {
      "id": 1,
      "invoice_id": 1,
      "product_id": 1,
      "box_size": 12,
      "quantity_boxes": 2,
      "total_units": 24,
      "price": "125.50",
      "price_type": "UNIT",
      "inventory_applied": true,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "product": {
        "id": 1,
        "name": "Nombre de ejemplo",
        "code": "PROD-001"
      },
      "box_price": "125.50",
      "unit_price": "125.50",
      "total_price": "125.50"
    }
  ],
  "subtotal": "125.50",
  "general_expenses_total": "125.50",
  "approximate_profit_total": "125.50",
  "total": "125.50"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/invoices/update-status/{invoice_id}`

- Descripción: Update Invoice Status
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `invoice_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `InvoiceUpdateStatus`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "status": "DRAFT"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `InvoiceResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "status": "DRAFT",
  "dollar_exchange_rate": "125.50",
  "general_expenses": "125.50",
  "approximate_profit_rate": "125.50",
  "notes": "Texto de ejemplo",
  "warehouse_id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "lines": [
    {
      "id": 1,
      "invoice_id": 1,
      "product_id": 1,
      "box_size": 12,
      "quantity_boxes": 2,
      "total_units": 24,
      "price": "125.50",
      "price_type": "UNIT",
      "inventory_applied": true,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "product": {
        "id": 1,
        "name": "Nombre de ejemplo",
        "code": "PROD-001"
      },
      "box_price": "125.50",
      "unit_price": "125.50",
      "total_price": "125.50"
    }
  ],
  "subtotal": "125.50",
  "general_expenses_total": "125.50",
  "approximate_profit_total": "125.50",
  "total": "125.50"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/invoices/delete/{invoice_id}`

- Descripción: Delete Invoice
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `invoice_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "invoice_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `InvoiceResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "status": "DRAFT",
  "dollar_exchange_rate": "125.50",
  "general_expenses": "125.50",
  "approximate_profit_rate": "125.50",
  "notes": "Texto de ejemplo",
  "warehouse_id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "lines": [
    {
      "id": 1,
      "invoice_id": 1,
      "product_id": 1,
      "box_size": 12,
      "quantity_boxes": 2,
      "total_units": 24,
      "price": "125.50",
      "price_type": "UNIT",
      "inventory_applied": true,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "product": {
        "id": 1,
        "name": "Nombre de ejemplo",
        "code": "PROD-001"
      },
      "box_price": "125.50",
      "unit_price": "125.50",
      "total_price": "125.50"
    }
  ],
  "subtotal": "125.50",
  "general_expenses_total": "125.50",
  "approximate_profit_total": "125.50",
  "total": "125.50"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Líneas de Factura

### GET `/api/invoice-lines/list/{invoice_id}`

- Descripción: List Invoice Lines
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `invoice_id` | `path` | `integer` | Sí | `` |  |
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "invoice_id": 1
  },
  "query": {
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<InvoiceLineResponse>` |

**Ejemplo de salida**

```json
[
  {
    "id": 1,
    "invoice_id": 1,
    "product_id": 1,
    "box_size": 12,
    "quantity_boxes": 2,
    "total_units": 24,
    "price": "125.50",
    "price_type": "UNIT",
    "inventory_applied": true,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "product": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "code": "PROD-001"
    },
    "box_price": "125.50",
    "unit_price": "125.50",
    "total_price": "125.50"
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/invoice-lines/create/{invoice_id}`

- Descripción: Create Invoice Line
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `invoice_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `InvoiceLineCreate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "product_id": 1,
  "new_product": {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1
  },
  "box_size": 12,
  "quantity_boxes": 2,
  "total_units": 24,
  "price": 125.5,
  "price_type": "UNIT"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `InvoiceLineResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "invoice_id": 1,
  "product_id": 1,
  "box_size": 12,
  "quantity_boxes": 2,
  "total_units": 24,
  "price": "125.50",
  "price_type": "UNIT",
  "inventory_applied": true,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "product": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "code": "PROD-001"
  },
  "box_price": "125.50",
  "unit_price": "125.50",
  "total_price": "125.50"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/invoice-lines/update/{invoice_id}/{line_id}`

- Descripción: Update Invoice Line
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `invoice_id` | `path` | `integer` | Sí | `` |  |
| `line_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `InvoiceLineUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "product_id": 1,
  "box_size": 12,
  "quantity_boxes": 2,
  "price": 125.5,
  "price_type": "UNIT"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `InvoiceLineResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "invoice_id": 1,
  "product_id": 1,
  "box_size": 12,
  "quantity_boxes": 2,
  "total_units": 24,
  "price": "125.50",
  "price_type": "UNIT",
  "inventory_applied": true,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "product": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "code": "PROD-001"
  },
  "box_price": "125.50",
  "unit_price": "125.50",
  "total_price": "125.50"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/invoice-lines/delete/{invoice_id}/{line_id}`

- Descripción: Delete Invoice Line
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `invoice_id` | `path` | `integer` | Sí | `` |  |
| `line_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "invoice_id": 1,
    "line_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `InvoiceLineResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "invoice_id": 1,
  "product_id": 1,
  "box_size": 12,
  "quantity_boxes": 2,
  "total_units": 24,
  "price": "125.50",
  "price_type": "UNIT",
  "inventory_applied": true,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "product": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "code": "PROD-001"
  },
  "box_price": "125.50",
  "unit_price": "125.50",
  "total_price": "125.50"
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Inventario

### GET `/api/inventory/list`

- Descripción: List Inventory
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `almacen` | `query` | `string | null` | No | `` | Filtra por almacén |
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "almacen": "Texto de ejemplo",
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<InventoryResponse>` |

**Ejemplo de salida**

```json
[
  {
    "avg_cost": "125.50",
    "last_cost": "125.50",
    "stock": 25,
    "reserved_stock": 3,
    "box_size": 12,
    "warehouse_id": 1,
    "product_id": 1,
    "id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "warehouse": {
      "name": "Nombre de ejemplo",
      "address": "Calle Ejemplo 123",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678",
      "id": 1,
      "is_active": true,
      "deleted_at": "2026-04-20T12:00:00+00:00",
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00"
    },
    "product": {
      "name": "Nombre de ejemplo",
      "code": "PROD-001",
      "description": "Descripción de ejemplo",
      "category_id": 1,
      "brand_id": 1,
      "image": "https://ejemplo.com/imagen.webp",
      "id": 1,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "category": {
        "id": 1,
        "name": "Nombre de ejemplo"
      },
      "brand": {
        "id": 1,
        "name": "Nombre de ejemplo"
      }
    },
    "active_reservations": [
      {
        "sale_line_id": 1,
        "sale_id": 1,
        "quantity_boxes": 2,
        "quantity_mode": "BOX",
        "price": "125.50",
        "price_type": "UNIT",
        "total_price": "125.50",
        "product_code": "Texto de ejemplo",
        "product_name": "Texto de ejemplo",
        "source_box_size": 12,
        "projected_units_from_stock": 25,
        "projected_boxes_to_open": 1,
        "projected_units_leftover": 1,
        "sale": {
          "id": 1,
          "sale_date": "2026-04-20",
          "status": "DRAFT",
          "notes": "Texto de ejemplo",
          "client": {
            "id": 1,
            "name": "Nombre de ejemplo",
            "email": "usuario@ejemplo.com",
            "phone": "5512345678"
          },
          "created_by": 1,
          "updated_at": "2026-04-20T12:00:00+00:00"
        }
      }
    ],
    "available_stock": 22,
    "is_over_reserved": true
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/inventory/movements`

- Descripción: List Inventory Movements
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |
| `inventory_id` | `query` | `integer | null` | No | `` |  |
| `product_id` | `query` | `integer | null` | No | `` |  |
| `warehouse_id` | `query` | `integer | null` | No | `` |  |
| `invoice_id` | `query` | `integer | null` | No | `` |  |
| `invoice_line_id` | `query` | `integer | null` | No | `` |  |
| `sale_id` | `query` | `integer | null` | No | `` |  |
| `sale_line_id` | `query` | `integer | null` | No | `` |  |
| `source_type` | `query` | `InventorySourceType | null` | No | `` |  |
| `event_type` | `query` | `InventoryEventType | null` | No | `` |  |
| `movement_type` | `query` | `InventoryMovementType | null` | No | `` |  |
| `value_type` | `query` | `InventoryValueType | null` | No | `` |  |
| `from_date` | `query` | `string<date-time> | null` | No | `` |  |
| `to_date` | `query` | `string<date-time> | null` | No | `` |  |
| `include_inactive` | `query` | `boolean` | No | `False` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "skip": 0,
    "limit": 50,
    "inventory_id": 1,
    "product_id": 1,
    "warehouse_id": 1,
    "invoice_id": 1,
    "invoice_line_id": 1,
    "sale_id": 1,
    "sale_line_id": 1,
    "source_type": "INVOICE",
    "event_type": "INVOICE_RECEIVED",
    "movement_type": "IN",
    "value_type": "COST",
    "from_date": "2026-04-20",
    "to_date": "2026-04-20",
    "include_inactive": true
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<InventoryMovementResponse-Output>` |

**Ejemplo de salida**

```json
[
  {
    "id": 1,
    "movement_date": "2026-04-20",
    "movement_group_id": "8d2e4c8a-5f7a-4f11-9b6c-123456789abc",
    "movement_sequence": 1,
    "source_type": "INVOICE",
    "event_type": "INVOICE_RECEIVED",
    "movement_type": "IN",
    "value_type": "COST",
    "quantity": 1,
    "unit_value": "125.50",
    "prev_stock": 25,
    "new_stock": 25,
    "inventory_id": 1,
    "invoice_line_id": 1,
    "sale_line_id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "inventory": {
      "id": 1,
      "product_id": 1,
      "warehouse_id": 1,
      "box_size": 12
    },
    "invoice_line": {
      "id": 1,
      "invoice_id": 1,
      "product_id": 1,
      "box_size": 12,
      "quantity_boxes": 2,
      "total_units": 24,
      "price": "125.50"
    },
    "sale_line": {
      "id": 1,
      "sale_id": 1,
      "inventory_id": 1,
      "quantity_units": 5,
      "price": "125.50",
      "total_price": "125.50"
    }
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/inventory/{inventory_id}`

- Descripción: Get Inventory
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `inventory_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "inventory_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `InventoryResponse` |

**Ejemplo de salida**

```json
{
  "avg_cost": "125.50",
  "last_cost": "125.50",
  "stock": 25,
  "reserved_stock": 3,
  "box_size": 12,
  "warehouse_id": 1,
  "product_id": 1,
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678",
    "id": 1,
    "is_active": true,
    "deleted_at": "2026-04-20T12:00:00+00:00",
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  },
  "product": {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1,
    "image": "https://ejemplo.com/imagen.webp",
    "id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "category": {
      "id": 1,
      "name": "Nombre de ejemplo"
    },
    "brand": {
      "id": 1,
      "name": "Nombre de ejemplo"
    }
  },
  "active_reservations": [
    {
      "sale_line_id": 1,
      "sale_id": 1,
      "quantity_boxes": 2,
      "quantity_mode": "BOX",
      "price": "125.50",
      "price_type": "UNIT",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "sale": {
        "id": 1,
        "sale_date": "2026-04-20",
        "status": "DRAFT",
        "notes": "Texto de ejemplo",
        "client": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        },
        "created_by": 1,
        "updated_at": "2026-04-20T12:00:00+00:00"
      }
    }
  ],
  "available_stock": 22,
  "is_over_reserved": true
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/inventory/create`

- Descripción: Create Inventory
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `InventoryCreate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "stock": 25,
  "reserved_stock": 3,
  "box_size": 12,
  "warehouse_id": 1,
  "product_id": 1,
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `InventoryResponse` |

**Ejemplo de salida**

```json
{
  "avg_cost": "125.50",
  "last_cost": "125.50",
  "stock": 25,
  "reserved_stock": 3,
  "box_size": 12,
  "warehouse_id": 1,
  "product_id": 1,
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678",
    "id": 1,
    "is_active": true,
    "deleted_at": "2026-04-20T12:00:00+00:00",
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  },
  "product": {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1,
    "image": "https://ejemplo.com/imagen.webp",
    "id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "category": {
      "id": 1,
      "name": "Nombre de ejemplo"
    },
    "brand": {
      "id": 1,
      "name": "Nombre de ejemplo"
    }
  },
  "active_reservations": [
    {
      "sale_line_id": 1,
      "sale_id": 1,
      "quantity_boxes": 2,
      "quantity_mode": "BOX",
      "price": "125.50",
      "price_type": "UNIT",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "sale": {
        "id": 1,
        "sale_date": "2026-04-20",
        "status": "DRAFT",
        "notes": "Texto de ejemplo",
        "client": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        },
        "created_by": 1,
        "updated_at": "2026-04-20T12:00:00+00:00"
      }
    }
  ],
  "available_stock": 22,
  "is_over_reserved": true
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/inventory/create-with-product`

- Descripción: Create Inventory With Product
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: multipart/form-data`
- Schema: `Body_create_inventory_with_product_api_inventory_create_with_product_post`

**Ejemplo de entrada**

- Ejemplo de `multipart/form-data`:
```json
{
  "image_file": "(binary)",
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "warehouse_id": 1,
  "stock": 25,
  "box_size": 12,
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `InventoryResponse` |

**Ejemplo de salida**

```json
{
  "avg_cost": "125.50",
  "last_cost": "125.50",
  "stock": 25,
  "reserved_stock": 3,
  "box_size": 12,
  "warehouse_id": 1,
  "product_id": 1,
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678",
    "id": 1,
    "is_active": true,
    "deleted_at": "2026-04-20T12:00:00+00:00",
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  },
  "product": {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1,
    "image": "https://ejemplo.com/imagen.webp",
    "id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "category": {
      "id": 1,
      "name": "Nombre de ejemplo"
    },
    "brand": {
      "id": 1,
      "name": "Nombre de ejemplo"
    }
  },
  "active_reservations": [
    {
      "sale_line_id": 1,
      "sale_id": 1,
      "quantity_boxes": 2,
      "quantity_mode": "BOX",
      "price": "125.50",
      "price_type": "UNIT",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "sale": {
        "id": 1,
        "sale_date": "2026-04-20",
        "status": "DRAFT",
        "notes": "Texto de ejemplo",
        "client": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        },
        "created_by": 1,
        "updated_at": "2026-04-20T12:00:00+00:00"
      }
    }
  ],
  "available_stock": 22,
  "is_over_reserved": true
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/inventory/update/{inventory_id}`

- Descripción: Update Inventory
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `inventory_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `InventoryUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "stock": 25,
  "box_size": 12,
  "is_active": true
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `InventoryResponse` |

**Ejemplo de salida**

```json
{
  "avg_cost": "125.50",
  "last_cost": "125.50",
  "stock": 25,
  "reserved_stock": 3,
  "box_size": 12,
  "warehouse_id": 1,
  "product_id": 1,
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678",
    "id": 1,
    "is_active": true,
    "deleted_at": "2026-04-20T12:00:00+00:00",
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  },
  "product": {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1,
    "image": "https://ejemplo.com/imagen.webp",
    "id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "category": {
      "id": 1,
      "name": "Nombre de ejemplo"
    },
    "brand": {
      "id": 1,
      "name": "Nombre de ejemplo"
    }
  },
  "active_reservations": [
    {
      "sale_line_id": 1,
      "sale_id": 1,
      "quantity_boxes": 2,
      "quantity_mode": "BOX",
      "price": "125.50",
      "price_type": "UNIT",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "sale": {
        "id": 1,
        "sale_date": "2026-04-20",
        "status": "DRAFT",
        "notes": "Texto de ejemplo",
        "client": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        },
        "created_by": 1,
        "updated_at": "2026-04-20T12:00:00+00:00"
      }
    }
  ],
  "available_stock": 22,
  "is_over_reserved": true
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/inventory/delete/{inventory_id}`

- Descripción: Delete Inventory
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `inventory_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "inventory_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `InventoryResponse` |

**Ejemplo de salida**

```json
{
  "avg_cost": "125.50",
  "last_cost": "125.50",
  "stock": 25,
  "reserved_stock": 3,
  "box_size": 12,
  "warehouse_id": 1,
  "product_id": 1,
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678",
    "id": 1,
    "is_active": true,
    "deleted_at": "2026-04-20T12:00:00+00:00",
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  },
  "product": {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1,
    "image": "https://ejemplo.com/imagen.webp",
    "id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "category": {
      "id": 1,
      "name": "Nombre de ejemplo"
    },
    "brand": {
      "id": 1,
      "name": "Nombre de ejemplo"
    }
  },
  "active_reservations": [
    {
      "sale_line_id": 1,
      "sale_id": 1,
      "quantity_boxes": 2,
      "quantity_mode": "BOX",
      "price": "125.50",
      "price_type": "UNIT",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "sale": {
        "id": 1,
        "sale_date": "2026-04-20",
        "status": "DRAFT",
        "notes": "Texto de ejemplo",
        "client": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        },
        "created_by": 1,
        "updated_at": "2026-04-20T12:00:00+00:00"
      }
    }
  ],
  "available_stock": 22,
  "is_over_reserved": true
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/inventory/pdf/all`

- Descripción: Generate All Inventory Pdf
- Auth: Sí
- Respuesta especial: archivo PDF binario.

**Headers**

- `Authorization: Bearer <access_token>`
- `Accept: application/pdf` recomendado

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `categoria` | `query` | `string | null` | No | `` | Filtra por categoría |
| `marca` | `query` | `string | null` | No | `` | Filtra por marca |
| `almacen` | `query` | `string | null` | No | `` | Filtra por almacén |
| `buscar` | `query` | `string | null` | No | `` | Buscar por nombre o código |
| `exclude_ids` | `query` | `string | null` | No | `` | IDs de inventario excluidos, en formato CSV: 10,11,15 |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "categoria": "Texto de ejemplo",
    "marca": "Texto de ejemplo",
    "almacen": "Texto de ejemplo",
    "buscar": "Texto de ejemplo",
    "exclude_ids": "Texto de ejemplo"
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/pdf` | `binary` |

**Ejemplo de salida**

- Respuesta binaria `application/pdf`. No regresa JSON.

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Ventas

### GET `/api/sales/report`

- Descripción: Get Sales Report
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `from_date` | `query` | `string<date>` | Sí | `` |  |
| `to_date` | `query` | `string<date>` | Sí | `` |  |
| `status` | `query` | `SaleStatus | null` | No | `` |  |
| `client_id` | `query` | `integer | null` | No | `` |  |
| `product_id` | `query` | `integer | null` | No | `` |  |
| `warehouse_id` | `query` | `integer | null` | No | `` |  |
| `inventory_id` | `query` | `integer | null` | No | `` |  |
| `group_by` | `query` | `enum(product, warehouse, client, inventory) | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "from_date": "2026-04-20",
    "to_date": "2026-04-20",
    "status": "DRAFT",
    "client_id": 1,
    "product_id": 1,
    "warehouse_id": 1,
    "inventory_id": 1,
    "group_by": "product"
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `SaleReportResponse` |

**Ejemplo de salida**

```json
{
  "period": {},
  "filters": {},
  "totals": {
    "sales_count": 1,
    "total_boxes": 1,
    "total_amount": "125.50"
  },
  "rows": [
    {
      "group_by": "product",
      "group_id": 1,
      "group_label": "Grupo de ejemplo",
      "total_boxes": 1,
      "total_amount": "125.50"
    }
  ],
  "sales": [
    {
      "id": 1,
      "sale_date": "2026-04-20",
      "status": "DRAFT",
      "client": {
        "id": 1,
        "name": "Nombre de ejemplo",
        "email": "usuario@ejemplo.com"
      },
      "total_amount": "125.50",
      "created_by": 1,
      "updated_by": 1,
      "paid_by": 1,
      "cancelled_by": 1,
      "created_by_name": "Texto de ejemplo",
      "updated_by_name": "Texto de ejemplo",
      "paid_by_name": "Texto de ejemplo",
      "cancelled_by_name": "Texto de ejemplo",
      "lines": [
        {
          "id": 1,
          "inventory_id": 1,
          "quantity_boxes": 2,
          "box_size": 12,
          "price": "125.50",
          "price_type": "UNIT",
          "unit_price": "125.50",
          "box_price": "125.50",
          "total_price": "125.50",
          "product_code": "Texto de ejemplo",
          "product_name": "Texto de ejemplo",
          "inventory": {
            "id": 1,
            "stock": 25,
            "reserved_stock": 3,
            "box_size": 12,
            "product": {
              "id": 1,
              "name": "Nombre de ejemplo",
              "code": "PROD-001"
            },
            "warehouse": {
              "id": 1,
              "name": "Nombre de ejemplo",
              "address": "Calle Ejemplo 123",
              "email": "usuario@ejemplo.com",
              "phone": "5512345678"
            }
          }
        }
      ]
    }
  ]
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/sales/list`

- Descripción: List Sales
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `skip` | `query` | `integer` | No | `0` |  |
| `limit` | `query` | `integer | null` | No | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "skip": 0,
    "limit": 50
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `array<SaleResponse>` |

**Ejemplo de salida**

```json
[
  {
    "id": 1,
    "sale_date": "2026-04-20",
    "status": "DRAFT",
    "total_price": "125.50",
    "notes": "Texto de ejemplo",
    "client_id": 1,
    "client": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678"
    },
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "created_by": 1,
    "updated_by": 1,
    "paid_by": 1,
    "cancelled_by": 1,
    "paid_at": "2026-04-20T12:00:00+00:00",
    "cancelled_at": "2026-04-20T12:00:00+00:00",
    "created_by_name": "Texto de ejemplo",
    "updated_by_name": "Texto de ejemplo",
    "paid_by_name": "Texto de ejemplo",
    "cancelled_by_name": "Texto de ejemplo",
    "created_by_user": {
      "id": 1,
      "first_name": "Juan",
      "last_name": "Pérez",
      "email": "usuario@ejemplo.com"
    },
    "paid_by_user": {
      "id": 1,
      "first_name": "Juan",
      "last_name": "Pérez",
      "email": "usuario@ejemplo.com"
    },
    "cancelled_by_user": {
      "id": 1,
      "first_name": "Juan",
      "last_name": "Pérez",
      "email": "usuario@ejemplo.com"
    },
    "lines": [
      {
        "id": 1,
        "sale_id": 1,
        "inventory_id": 1,
        "quantity_boxes": 2,
        "box_size": 12,
        "price": "125.50",
        "price_type": "UNIT",
        "quantity_mode": "BOX",
        "unit_price": "125.50",
        "box_price": "125.50",
        "total_price": "125.50",
        "product_code": "Texto de ejemplo",
        "product_name": "Texto de ejemplo",
        "reservation_applied": true,
        "inventory_applied": true,
        "source_box_size": 12,
        "projected_units_from_stock": 25,
        "projected_boxes_to_open": 1,
        "projected_units_leftover": 1,
        "is_active": true,
        "created_at": "2026-04-20T12:00:00+00:00",
        "updated_at": "2026-04-20T12:00:00+00:00",
        "inventory": {
          "id": 1,
          "stock": 25,
          "reserved_stock": 3,
          "box_size": 12,
          "product": {
            "id": 1,
            "name": "Nombre de ejemplo",
            "code": "PROD-001"
          },
          "warehouse": {
            "id": 1,
            "name": "Nombre de ejemplo",
            "address": "Calle Ejemplo 123",
            "email": "usuario@ejemplo.com",
            "phone": "5512345678"
          }
        }
      }
    ]
  }
]
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/sales/{sale_id}`

- Descripción: Get Sale
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `sale_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "sale_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `SaleResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "total_price": "125.50",
  "notes": "Texto de ejemplo",
  "client_id": 1,
  "client": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "created_by": 1,
  "updated_by": 1,
  "paid_by": 1,
  "cancelled_by": 1,
  "paid_at": "2026-04-20T12:00:00+00:00",
  "cancelled_at": "2026-04-20T12:00:00+00:00",
  "created_by_name": "Texto de ejemplo",
  "updated_by_name": "Texto de ejemplo",
  "paid_by_name": "Texto de ejemplo",
  "cancelled_by_name": "Texto de ejemplo",
  "created_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "paid_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "cancelled_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "lines": [
    {
      "id": 1,
      "sale_id": 1,
      "inventory_id": 1,
      "quantity_boxes": 2,
      "box_size": 12,
      "price": "125.50",
      "price_type": "UNIT",
      "quantity_mode": "BOX",
      "unit_price": "125.50",
      "box_price": "125.50",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "reservation_applied": true,
      "inventory_applied": true,
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "inventory": {
        "id": 1,
        "stock": 25,
        "reserved_stock": 3,
        "box_size": 12,
        "product": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "code": "PROD-001"
        },
        "warehouse": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "address": "Calle Ejemplo 123",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        }
      }
    }
  ]
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### GET `/api/sales/{sale_id}/invoice`

- Descripción: Invoice Sale
- Auth: Sí
- Respuesta especial: archivo PDF binario.

**Headers**

- `Authorization: Bearer <access_token>`
- `Accept: application/pdf` recomendado

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `sale_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "sale_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/pdf` | `binary` |

**Ejemplo de salida**

- Respuesta binaria `application/pdf`. No regresa JSON.

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/sales/create`

- Descripción: Create Sale
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

Sin parámetros.

**Body**

- `Content-Type: application/json`
- Schema: `SaleCreateWithLines`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "notes": "Texto de ejemplo",
  "client_id": 1,
  "lines": [
    {
      "inventory_id": 1,
      "quantity_boxes": 2,
      "quantity_units": 5,
      "price": 125.5,
      "price_type": "UNIT"
    }
  ]
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `SaleResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "total_price": "125.50",
  "notes": "Texto de ejemplo",
  "client_id": 1,
  "client": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "created_by": 1,
  "updated_by": 1,
  "paid_by": 1,
  "cancelled_by": 1,
  "paid_at": "2026-04-20T12:00:00+00:00",
  "cancelled_at": "2026-04-20T12:00:00+00:00",
  "created_by_name": "Texto de ejemplo",
  "updated_by_name": "Texto de ejemplo",
  "paid_by_name": "Texto de ejemplo",
  "cancelled_by_name": "Texto de ejemplo",
  "created_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "paid_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "cancelled_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "lines": [
    {
      "id": 1,
      "sale_id": 1,
      "inventory_id": 1,
      "quantity_boxes": 2,
      "box_size": 12,
      "price": "125.50",
      "price_type": "UNIT",
      "quantity_mode": "BOX",
      "unit_price": "125.50",
      "box_price": "125.50",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "reservation_applied": true,
      "inventory_applied": true,
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "inventory": {
        "id": 1,
        "stock": 25,
        "reserved_stock": 3,
        "box_size": 12,
        "product": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "code": "PROD-001"
        },
        "warehouse": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "address": "Calle Ejemplo 123",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        }
      }
    }
  ]
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/sales/update/{sale_id}`

- Descripción: Update Sale
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `sale_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `SaleUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "sale_date": "2026-04-20",
  "notes": "Texto de ejemplo",
  "client_id": 1
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `SaleResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "total_price": "125.50",
  "notes": "Texto de ejemplo",
  "client_id": 1,
  "client": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "created_by": 1,
  "updated_by": 1,
  "paid_by": 1,
  "cancelled_by": 1,
  "paid_at": "2026-04-20T12:00:00+00:00",
  "cancelled_at": "2026-04-20T12:00:00+00:00",
  "created_by_name": "Texto de ejemplo",
  "updated_by_name": "Texto de ejemplo",
  "paid_by_name": "Texto de ejemplo",
  "cancelled_by_name": "Texto de ejemplo",
  "created_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "paid_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "cancelled_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "lines": [
    {
      "id": 1,
      "sale_id": 1,
      "inventory_id": 1,
      "quantity_boxes": 2,
      "box_size": 12,
      "price": "125.50",
      "price_type": "UNIT",
      "quantity_mode": "BOX",
      "unit_price": "125.50",
      "box_price": "125.50",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "reservation_applied": true,
      "inventory_applied": true,
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "inventory": {
        "id": 1,
        "stock": 25,
        "reserved_stock": 3,
        "box_size": 12,
        "product": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "code": "PROD-001"
        },
        "warehouse": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "address": "Calle Ejemplo 123",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        }
      }
    }
  ]
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/sales/update-status/{sale_id}`

- Descripción: Update Sale Status
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `sale_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `SaleUpdateStatus`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "status": "DRAFT"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `SaleResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "total_price": "125.50",
  "notes": "Texto de ejemplo",
  "client_id": 1,
  "client": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "created_by": 1,
  "updated_by": 1,
  "paid_by": 1,
  "cancelled_by": 1,
  "paid_at": "2026-04-20T12:00:00+00:00",
  "cancelled_at": "2026-04-20T12:00:00+00:00",
  "created_by_name": "Texto de ejemplo",
  "updated_by_name": "Texto de ejemplo",
  "paid_by_name": "Texto de ejemplo",
  "cancelled_by_name": "Texto de ejemplo",
  "created_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "paid_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "cancelled_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "lines": [
    {
      "id": 1,
      "sale_id": 1,
      "inventory_id": 1,
      "quantity_boxes": 2,
      "box_size": 12,
      "price": "125.50",
      "price_type": "UNIT",
      "quantity_mode": "BOX",
      "unit_price": "125.50",
      "box_price": "125.50",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "reservation_applied": true,
      "inventory_applied": true,
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "inventory": {
        "id": 1,
        "stock": 25,
        "reserved_stock": 3,
        "box_size": 12,
        "product": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "code": "PROD-001"
        },
        "warehouse": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "address": "Calle Ejemplo 123",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        }
      }
    }
  ]
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/sales/delete/{sale_id}`

- Descripción: Delete Sale
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `sale_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "sale_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `SaleResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "total_price": "125.50",
  "notes": "Texto de ejemplo",
  "client_id": 1,
  "client": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "created_by": 1,
  "updated_by": 1,
  "paid_by": 1,
  "cancelled_by": 1,
  "paid_at": "2026-04-20T12:00:00+00:00",
  "cancelled_at": "2026-04-20T12:00:00+00:00",
  "created_by_name": "Texto de ejemplo",
  "updated_by_name": "Texto de ejemplo",
  "paid_by_name": "Texto de ejemplo",
  "cancelled_by_name": "Texto de ejemplo",
  "created_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "paid_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "cancelled_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "lines": [
    {
      "id": 1,
      "sale_id": 1,
      "inventory_id": 1,
      "quantity_boxes": 2,
      "box_size": 12,
      "price": "125.50",
      "price_type": "UNIT",
      "quantity_mode": "BOX",
      "unit_price": "125.50",
      "box_price": "125.50",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "reservation_applied": true,
      "inventory_applied": true,
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "inventory": {
        "id": 1,
        "stock": 25,
        "reserved_stock": 3,
        "box_size": 12,
        "product": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "code": "PROD-001"
        },
        "warehouse": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "address": "Calle Ejemplo 123",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        }
      }
    }
  ]
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### POST `/api/sales/{sale_id}/lines`

- Descripción: Add Sale Line
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `sale_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `SaleLineCreate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "inventory_id": 1,
  "quantity_boxes": 2,
  "quantity_units": 5,
  "price": 125.5,
  "price_type": "UNIT"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `201` | `application/json` | `SaleLineResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "sale_id": 1,
  "inventory_id": 1,
  "quantity_boxes": 2,
  "box_size": 12,
  "price": "125.50",
  "price_type": "UNIT",
  "quantity_mode": "BOX",
  "unit_price": "125.50",
  "box_price": "125.50",
  "total_price": "125.50",
  "product_code": "Texto de ejemplo",
  "product_name": "Texto de ejemplo",
  "reservation_applied": true,
  "inventory_applied": true,
  "source_box_size": 12,
  "projected_units_from_stock": 25,
  "projected_boxes_to_open": 1,
  "projected_units_leftover": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "inventory": {
    "id": 1,
    "stock": 25,
    "reserved_stock": 3,
    "box_size": 12,
    "product": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "code": "PROD-001"
    },
    "warehouse": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "address": "Calle Ejemplo 123",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678"
    }
  }
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### PUT `/api/sales/{sale_id}/lines/{line_id}`

- Descripción: Update Sale Line
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `sale_id` | `path` | `integer` | Sí | `` |  |
| `line_id` | `path` | `integer` | Sí | `` |  |

**Body**

- `Content-Type: application/json`
- Schema: `SaleLineUpdate`

**Ejemplo de entrada**

- Ejemplo de body JSON:
```json
{
  "inventory_id": 1,
  "quantity_boxes": 2,
  "quantity_units": 5,
  "price": 125.5,
  "price_type": "UNIT"
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `SaleLineResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "sale_id": 1,
  "inventory_id": 1,
  "quantity_boxes": 2,
  "box_size": 12,
  "price": "125.50",
  "price_type": "UNIT",
  "quantity_mode": "BOX",
  "unit_price": "125.50",
  "box_price": "125.50",
  "total_price": "125.50",
  "product_code": "Texto de ejemplo",
  "product_name": "Texto de ejemplo",
  "reservation_applied": true,
  "inventory_applied": true,
  "source_box_size": 12,
  "projected_units_from_stock": 25,
  "projected_boxes_to_open": 1,
  "projected_units_leftover": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "inventory": {
    "id": 1,
    "stock": 25,
    "reserved_stock": 3,
    "box_size": 12,
    "product": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "code": "PROD-001"
    },
    "warehouse": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "address": "Calle Ejemplo 123",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678"
    }
  }
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor

### DELETE `/api/sales/{sale_id}/lines/{line_id}`

- Descripción: Delete Sale Line
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `sale_id` | `path` | `integer` | Sí | `` |  |
| `line_id` | `path` | `integer` | Sí | `` |  |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "path": {
    "sale_id": 1,
    "line_id": 1
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `SaleLineResponse` |

**Ejemplo de salida**

```json
{
  "id": 1,
  "sale_id": 1,
  "inventory_id": 1,
  "quantity_boxes": 2,
  "box_size": 12,
  "price": "125.50",
  "price_type": "UNIT",
  "quantity_mode": "BOX",
  "unit_price": "125.50",
  "box_price": "125.50",
  "total_price": "125.50",
  "product_code": "Texto de ejemplo",
  "product_name": "Texto de ejemplo",
  "reservation_applied": true,
  "inventory_applied": true,
  "source_box_size": 12,
  "projected_units_from_stock": 25,
  "projected_boxes_to_open": 1,
  "projected_units_leftover": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "inventory": {
    "id": 1,
    "stock": 25,
    "reserved_stock": 3,
    "box_size": 12,
    "product": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "code": "PROD-001"
    },
    "warehouse": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "address": "Calle Ejemplo 123",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678"
    }
  }
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## BFF / Dashboard

### GET `/api/bff/system-summary`

- Descripción: Get System Summary
- Auth: Sí

**Headers**

- `Authorization: Bearer <access_token>`
- Sin headers especiales además de auth

**Path / Query Params**

| Nombre | En | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|---|
| `days` | `query` | `integer` | No | `14` | Window in days for recent ARRIVED invoices and PAID sales. |

**Body**

Sin body.

**Ejemplo de entrada**

- Ejemplo de parámetros (`path` / `query`):
```json
{
  "query": {
    "days": 14
  }
}
```

**Respuesta exitosa**

| Status | Content-Type | Schema |
|---|---|---|
| `200` | `application/json` | `SystemSummaryResponse` |

**Ejemplo de salida**

```json
{
  "days": 14,
  "cutoff_date": "2026-04-20",
  "generated_at": "2026-04-20T12:00:00+00:00",
  "catalogs": {
    "products": 1,
    "clients": 1,
    "warehouses": 1,
    "users": 1,
    "categories": 1,
    "brands": 1
  },
  "invoices": {
    "pending": 1,
    "cancelled": 1,
    "arrived_last_n_days": 14
  },
  "sales": {
    "pending": 1,
    "cancelled": 1,
    "paid_last_n_days": 14
  }
}
```

**Errores comunes**

- `401` no autenticado, token inválido o token expirado
- `404` recurso no encontrado cuando aplica
- `409` conflicto de negocio / duplicados / transición inválida cuando aplica
- `422` error de validación de parámetros, query o body
- `500` error interno del servidor


## Referencia de Schemas

> Nota: algunos schemas aparecen con sufijos `-Input` / `-Output` o con nombres largos generados por FastAPI. Aquí se listan tal como salen del OpenAPI actual, con alias legibles cuando aplica.

### `Body_create_inventory_with_product_api_inventory_create_with_product_post`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `image_file` | `string<binary> | null` | No |  |
| `name` | `string` | Sí |  |
| `code` | `string` | Sí |  |
| `description` | `string | null` | No |  |
| `category_id` | `integer` | Sí |  |
| `brand_id` | `integer` | Sí |  |
| `warehouse_id` | `integer` | Sí |  |
| `stock` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `is_active` | `boolean` | No |  |

Ejemplo:
```json
{
  "image_file": "(binary)",
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "warehouse_id": 1,
  "stock": 25,
  "box_size": 12,
  "is_active": true
}
```

### `Body_create_product_api_products_create_post`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `image_file` | `string<binary> | null` | No |  |
| `name` | `string` | Sí |  |
| `code` | `string` | Sí |  |
| `description` | `string | null` | No |  |
| `category_id` | `integer` | Sí |  |
| `brand_id` | `integer` | Sí |  |
| `image` | `string | null` | No |  |

Ejemplo:
```json
{
  "image_file": "(binary)",
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp"
}
```

### `Body_update_product_api_products_update__product_id__put`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `image_file` | `string<binary> | null` | No |  |
| `name` | `string | null` | No |  |
| `code` | `string | null` | No |  |
| `description` | `string | null` | No |  |
| `category_id` | `integer | null` | No |  |
| `brand_id` | `integer | null` | No |  |
| `image` | `string | null` | No |  |
| `is_active` | `boolean | null` | No |  |

Ejemplo:
```json
{
  "image_file": "(binary)",
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp",
  "is_active": true
}
```

### `BrandCreate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo"
}
```

### `BrandUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string | null` | No |  |
| `is_active` | `boolean | null` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "is_active": true
}
```

### `CatalogCounts`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `products` | `integer` | Sí |  |
| `clients` | `integer` | Sí |  |
| `warehouses` | `integer` | Sí |  |
| `users` | `integer` | Sí |  |
| `categories` | `integer` | Sí |  |
| `brands` | `integer` | Sí |  |

Ejemplo:
```json
{
  "products": 1,
  "clients": 1,
  "warehouses": 1,
  "users": 1,
  "categories": 1,
  "brands": 1
}
```

### `CategoryCreate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `description` | `string | null` | No |  |
| `is_active` | `boolean` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "description": "Descripción de ejemplo",
  "is_active": true
}
```

### `CategoryUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string | null` | No |  |
| `description` | `string | null` | No |  |
| `is_active` | `boolean | null` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "description": "Descripción de ejemplo",
  "is_active": true
}
```

### `ClientCreate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `email` | `string<email> | null` | No |  |
| `phone` | `string | null` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678"
}
```

### `ClientLineResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `name` | `string` | Sí |  |
| `email` | `string | null` | No |  |
| `phone` | `string | null` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678"
}
```

### `ClientResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `email` | `string<email> | null` | No |  |
| `phone` | `string | null` | No |  |
| `id` | `integer` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `deleted_at` | `string | null` | No |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

### `ClientUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string | null` | No |  |
| `email` | `string<email> | null` | No |  |
| `phone` | `string | null` | No |  |
| `is_active` | `boolean | null` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "is_active": true
}
```

### `HTTPValidationError`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `detail` | `array<ValidationError>` | No |  |

Ejemplo:
```json
{
  "detail": [
    {
      "loc": [
        "Texto de ejemplo"
      ],
      "msg": "Texto de ejemplo",
      "type": "Texto de ejemplo"
    }
  ]
}
```

### `InlineInvoiceProductCreate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `code` | `string` | Sí |  |
| `description` | `string | null` | No |  |
| `category_id` | `integer` | Sí |  |
| `brand_id` | `integer` | Sí |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1
}
```

### `InventoryCreate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `stock` | `integer` | Sí |  |
| `reserved_stock` | `integer` | No |  |
| `box_size` | `integer` | Sí |  |
| `warehouse_id` | `integer` | Sí |  |
| `product_id` | `integer` | Sí |  |
| `is_active` | `boolean` | No |  |

Ejemplo:
```json
{
  "stock": 25,
  "reserved_stock": 3,
  "box_size": 12,
  "warehouse_id": 1,
  "product_id": 1,
  "is_active": true
}
```

### `InventoryEventType`

- Tipo: `enum`
- Valores: `INVOICE_RECEIVED, INVOICE_UNRECEIVED, SALE_RESERVED, SALE_RELEASED, SALE_APPROVED, SALE_REVERSED, BOX_OPENED_OUT, BOX_OPENED_IN, MANUAL_CREATED, MANUAL_STOCK_ADJUSTED`

### `InventoryMovementInventoryRef`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `product_id` | `integer` | Sí |  |
| `warehouse_id` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "product_id": 1,
  "warehouse_id": 1,
  "box_size": 12
}
```

### `InventoryMovementInvoiceLineRef-Input`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `invoice_id` | `integer` | Sí |  |
| `product_id` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `quantity_boxes` | `integer` | Sí |  |
| `total_units` | `integer` | Sí |  |
| `price` | `number | string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "invoice_id": 1,
  "product_id": 1,
  "box_size": 12,
  "quantity_boxes": 2,
  "total_units": 24,
  "price": 125.5
}
```

### `InventoryMovementInvoiceLineRef-Output`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `invoice_id` | `integer` | Sí |  |
| `product_id` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `quantity_boxes` | `integer` | Sí |  |
| `total_units` | `integer` | Sí |  |
| `price` | `string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "invoice_id": 1,
  "product_id": 1,
  "box_size": 12,
  "quantity_boxes": 2,
  "total_units": 24,
  "price": "125.50"
}
```

### `InventoryMovementResponse-Input`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `movement_date` | `string<date-time>` | Sí |  |
| `movement_group_id` | `string` | Sí |  |
| `movement_sequence` | `integer` | Sí |  |
| `source_type` | `InventorySourceType` | Sí |  |
| `event_type` | `InventoryEventType` | Sí |  |
| `movement_type` | `InventoryMovementType` | Sí |  |
| `value_type` | `InventoryValueType` | Sí |  |
| `quantity` | `integer` | Sí |  |
| `unit_value` | `number | string` | Sí |  |
| `prev_stock` | `integer` | Sí |  |
| `new_stock` | `integer` | Sí |  |
| `inventory_id` | `integer` | Sí |  |
| `invoice_line_id` | `integer | null` | Sí |  |
| `sale_line_id` | `integer | null` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string<date-time>` | Sí |  |
| `updated_at` | `string<date-time>` | Sí |  |
| `inventory` | `InventoryMovementInventoryRef | null` | No |  |
| `invoice_line` | `InventoryMovementInvoiceLineRef-Input | null` | No |  |
| `sale_line` | `InventoryMovementSaleLineRef-Input | null` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "movement_date": "2026-04-20",
  "movement_group_id": "8d2e4c8a-5f7a-4f11-9b6c-123456789abc",
  "movement_sequence": 1,
  "source_type": "INVOICE",
  "event_type": "INVOICE_RECEIVED",
  "movement_type": "IN",
  "value_type": "COST",
  "quantity": 1,
  "unit_value": 125.5,
  "prev_stock": 25,
  "new_stock": 25,
  "inventory_id": 1,
  "invoice_line_id": 1,
  "sale_line_id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "inventory": {
    "id": 1,
    "product_id": 1,
    "warehouse_id": 1,
    "box_size": 12
  },
  "invoice_line": {
    "id": 1,
    "invoice_id": 1,
    "product_id": 1,
    "box_size": 12,
    "quantity_boxes": 2,
    "total_units": 24,
    "price": 125.5
  },
  "sale_line": {
    "id": 1,
    "sale_id": 1,
    "inventory_id": 1,
    "quantity_units": 5,
    "price": 125.5,
    "total_price": 125.5
  }
}
```

### `InventoryMovementResponse-Output`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `movement_date` | `string` | Sí |  |
| `movement_group_id` | `string` | Sí |  |
| `movement_sequence` | `integer` | Sí |  |
| `source_type` | `InventorySourceType` | Sí |  |
| `event_type` | `InventoryEventType` | Sí |  |
| `movement_type` | `InventoryMovementType` | Sí |  |
| `value_type` | `InventoryValueType` | Sí |  |
| `quantity` | `integer` | Sí |  |
| `unit_value` | `string` | Sí |  |
| `prev_stock` | `integer` | Sí |  |
| `new_stock` | `integer` | Sí |  |
| `inventory_id` | `integer` | Sí |  |
| `invoice_line_id` | `integer | null` | Sí |  |
| `sale_line_id` | `integer | null` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |
| `inventory` | `InventoryMovementInventoryRef | null` | No |  |
| `invoice_line` | `InventoryMovementInvoiceLineRef-Output | null` | No |  |
| `sale_line` | `InventoryMovementSaleLineRef-Output | null` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "movement_date": "2026-04-20",
  "movement_group_id": "8d2e4c8a-5f7a-4f11-9b6c-123456789abc",
  "movement_sequence": 1,
  "source_type": "INVOICE",
  "event_type": "INVOICE_RECEIVED",
  "movement_type": "IN",
  "value_type": "COST",
  "quantity": 1,
  "unit_value": "125.50",
  "prev_stock": 25,
  "new_stock": 25,
  "inventory_id": 1,
  "invoice_line_id": 1,
  "sale_line_id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "inventory": {
    "id": 1,
    "product_id": 1,
    "warehouse_id": 1,
    "box_size": 12
  },
  "invoice_line": {
    "id": 1,
    "invoice_id": 1,
    "product_id": 1,
    "box_size": 12,
    "quantity_boxes": 2,
    "total_units": 24,
    "price": "125.50"
  },
  "sale_line": {
    "id": 1,
    "sale_id": 1,
    "inventory_id": 1,
    "quantity_units": 5,
    "price": "125.50",
    "total_price": "125.50"
  }
}
```

### `InventoryMovementSaleLineRef-Input`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `sale_id` | `integer` | Sí |  |
| `inventory_id` | `integer` | Sí |  |
| `quantity_units` | `integer` | Sí |  |
| `price` | `number | string` | Sí |  |
| `total_price` | `number | string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "sale_id": 1,
  "inventory_id": 1,
  "quantity_units": 5,
  "price": 125.5,
  "total_price": 125.5
}
```

### `InventoryMovementSaleLineRef-Output`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `sale_id` | `integer` | Sí |  |
| `inventory_id` | `integer` | Sí |  |
| `quantity_units` | `integer` | Sí |  |
| `price` | `string` | Sí |  |
| `total_price` | `string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "sale_id": 1,
  "inventory_id": 1,
  "quantity_units": 5,
  "price": "125.50",
  "total_price": "125.50"
}
```

### `InventoryMovementType`

- Tipo: `enum`
- Valores: `IN, OUT`

### `InventoryReservationResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `sale_line_id` | `integer` | Sí |  |
| `sale_id` | `integer` | Sí |  |
| `quantity_boxes` | `integer` | Sí |  |
| `quantity_mode` | `SaleLineQuantityMode` | Sí |  |
| `price` | `string` | Sí |  |
| `price_type` | `SaleLinePriceType` | Sí |  |
| `total_price` | `string` | Sí |  |
| `product_code` | `string | null` | No |  |
| `product_name` | `string | null` | No |  |
| `source_box_size` | `integer | null` | No |  |
| `projected_units_from_stock` | `integer | null` | No |  |
| `projected_boxes_to_open` | `integer | null` | No |  |
| `projected_units_leftover` | `integer | null` | No |  |
| `sale` | `InventoryReservationSaleRef | null` | No |  |

Ejemplo:
```json
{
  "sale_line_id": 1,
  "sale_id": 1,
  "quantity_boxes": 2,
  "quantity_mode": "BOX",
  "price": "125.50",
  "price_type": "UNIT",
  "total_price": "125.50",
  "product_code": "Texto de ejemplo",
  "product_name": "Texto de ejemplo",
  "source_box_size": 12,
  "projected_units_from_stock": 25,
  "projected_boxes_to_open": 1,
  "projected_units_leftover": 1,
  "sale": {
    "id": 1,
    "sale_date": "2026-04-20",
    "status": "DRAFT",
    "notes": "Texto de ejemplo",
    "client": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678"
    },
    "created_by": 1,
    "updated_at": "2026-04-20T12:00:00+00:00"
  }
}
```

### `InventoryReservationSaleRef`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `sale_date` | `string<date>` | Sí |  |
| `status` | `SaleStatus` | Sí |  |
| `notes` | `string | null` | No |  |
| `client` | `ClientLineResponse | null` | No |  |
| `created_by` | `integer | null` | No |  |
| `updated_at` | `string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "notes": "Texto de ejemplo",
  "client": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "created_by": 1,
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

### `InventoryResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `avg_cost` | `string` | Sí |  |
| `last_cost` | `string` | Sí |  |
| `stock` | `integer` | Sí |  |
| `reserved_stock` | `integer` | No |  |
| `box_size` | `integer` | Sí |  |
| `warehouse_id` | `integer` | Sí |  |
| `product_id` | `integer` | Sí |  |
| `id` | `integer` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |
| `warehouse` | `WarehouseResponse | null` | No |  |
| `product` | `ProductResponse | null` | No |  |
| `active_reservations` | `array<InventoryReservationResponse>` | No |  |
| `available_stock` | `integer` | Sí |  |
| `is_over_reserved` | `boolean` | Sí |  |

Ejemplo:
```json
{
  "avg_cost": "125.50",
  "last_cost": "125.50",
  "stock": 25,
  "reserved_stock": 3,
  "box_size": 12,
  "warehouse_id": 1,
  "product_id": 1,
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678",
    "id": 1,
    "is_active": true,
    "deleted_at": "2026-04-20T12:00:00+00:00",
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  },
  "product": {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1,
    "image": "https://ejemplo.com/imagen.webp",
    "id": 1,
    "is_active": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00",
    "category": {
      "id": 1,
      "name": "Nombre de ejemplo"
    },
    "brand": {
      "id": 1,
      "name": "Nombre de ejemplo"
    }
  },
  "active_reservations": [
    {
      "sale_line_id": 1,
      "sale_id": 1,
      "quantity_boxes": 2,
      "quantity_mode": "BOX",
      "price": "125.50",
      "price_type": "UNIT",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "sale": {
        "id": 1,
        "sale_date": "2026-04-20",
        "status": "DRAFT",
        "notes": "Texto de ejemplo",
        "client": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        },
        "created_by": 1,
        "updated_at": "2026-04-20T12:00:00+00:00"
      }
    }
  ],
  "available_stock": 22,
  "is_over_reserved": true
}
```

### `InventorySourceType`

- Tipo: `enum`
- Valores: `INVOICE, SALE, MANUAL`

### `InventoryStockItem-Input`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `warehouse_id` | `integer` | Sí |  |
| `product_id` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `stock` | `integer` | Sí |  |
| `reserved_stock` | `integer` | No |  |
| `available_boxes` | `integer` | No |  |
| `avg_cost` | `number | string` | Sí |  |
| `last_cost` | `number | string` | Sí |  |
| `sales_last_price` | `number | null` | No |  |
| `sales_avg_price` | `number | null` | No |  |
| `is_active` | `boolean` | Sí |  |
| `is_over_reserved` | `boolean` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "warehouse_id": 1,
  "product_id": 1,
  "box_size": 12,
  "stock": 25,
  "reserved_stock": 3,
  "available_boxes": 22,
  "avg_cost": 125.5,
  "last_cost": 125.5,
  "sales_last_price": 125.5,
  "sales_avg_price": 125.5,
  "is_active": true,
  "is_over_reserved": true
}
```

### `InventoryStockItem-Output`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `warehouse_id` | `integer` | Sí |  |
| `product_id` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `stock` | `integer` | Sí |  |
| `reserved_stock` | `integer` | No |  |
| `available_boxes` | `integer` | No |  |
| `avg_cost` | `string` | Sí |  |
| `last_cost` | `string` | Sí |  |
| `sales_last_price` | `number | null` | No |  |
| `sales_avg_price` | `number | null` | No |  |
| `is_active` | `boolean` | Sí |  |
| `is_over_reserved` | `boolean` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "warehouse_id": 1,
  "product_id": 1,
  "box_size": 12,
  "stock": 25,
  "reserved_stock": 3,
  "available_boxes": 22,
  "avg_cost": "125.50",
  "last_cost": "125.50",
  "sales_last_price": 125.5,
  "sales_avg_price": 125.5,
  "is_active": true,
  "is_over_reserved": true
}
```

### `InventoryUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `stock` | `integer | null` | No |  |
| `box_size` | `integer | null` | No |  |
| `is_active` | `boolean | null` | No |  |

Ejemplo:
```json
{
  "stock": 25,
  "box_size": 12,
  "is_active": true
}
```

### `InventoryValueType`

- Tipo: `enum`
- Valores: `COST, PRICE`

### `InvoiceCreateWithLines`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `invoice_number` | `string` | Sí |  |
| `sequence` | `integer` | Sí |  |
| `invoice_date` | `string<date>` | No |  |
| `order_date` | `string<date> | null` | No |  |
| `arrival_date` | `string<date> | null` | No |  |
| `status` | `InvoiceStatus` | No |  |
| `dollar_exchange_rate` | `number | string` | No |  |
| `general_expenses` | `number | string` | No |  |
| `approximate_profit_rate` | `number | string` | No |  |
| `notes` | `string | null` | No |  |
| `warehouse_id` | `integer` | Sí |  |
| `lines` | `array<InvoiceLineCreate>` | No |  |

Ejemplo:
```json
{
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "status": "DRAFT",
  "dollar_exchange_rate": 125.5,
  "general_expenses": 125.5,
  "approximate_profit_rate": 125.5,
  "notes": "Texto de ejemplo",
  "warehouse_id": 1,
  "lines": [
    {
      "product_id": 1,
      "new_product": {
        "name": "Nombre de ejemplo",
        "code": "PROD-001",
        "description": "Descripción de ejemplo",
        "category_id": 1,
        "brand_id": 1
      },
      "box_size": 12,
      "quantity_boxes": 2,
      "total_units": 24,
      "price": 125.5,
      "price_type": "UNIT"
    }
  ]
}
```

### `InvoiceLineCreate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `product_id` | `integer | null` | No |  |
| `new_product` | `InlineInvoiceProductCreate | null` | No |  |
| `box_size` | `integer` | Sí |  |
| `quantity_boxes` | `integer` | Sí |  |
| `total_units` | `integer | null` | No |  |
| `price` | `number | string` | Sí |  |
| `price_type` | `InvoiceLinePriceType` | No |  |

Ejemplo:
```json
{
  "product_id": 1,
  "new_product": {
    "name": "Nombre de ejemplo",
    "code": "PROD-001",
    "description": "Descripción de ejemplo",
    "category_id": 1,
    "brand_id": 1
  },
  "box_size": 12,
  "quantity_boxes": 2,
  "total_units": 24,
  "price": 125.5,
  "price_type": "UNIT"
}
```

### `InvoiceLinePriceType`

- Tipo: `enum`
- Valores: `UNIT, BOX`

### `InvoiceLineResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `invoice_id` | `integer` | Sí |  |
| `product_id` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `quantity_boxes` | `integer` | Sí |  |
| `total_units` | `integer` | Sí |  |
| `price` | `string` | Sí |  |
| `price_type` | `InvoiceLinePriceType` | Sí |  |
| `inventory_applied` | `boolean` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |
| `product` | `ProductLineResponse | null` | No |  |
| `box_price` | `string` | Sí |  |
| `unit_price` | `string` | Sí |  |
| `total_price` | `string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "invoice_id": 1,
  "product_id": 1,
  "box_size": 12,
  "quantity_boxes": 2,
  "total_units": 24,
  "price": "125.50",
  "price_type": "UNIT",
  "inventory_applied": true,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "product": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "code": "PROD-001"
  },
  "box_price": "125.50",
  "unit_price": "125.50",
  "total_price": "125.50"
}
```

### `InvoiceLineUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `product_id` | `integer | null` | No |  |
| `box_size` | `integer | null` | No |  |
| `quantity_boxes` | `integer | null` | No |  |
| `price` | `number | string | null` | No |  |
| `price_type` | `InvoiceLinePriceType | null` | No |  |

Ejemplo:
```json
{
  "product_id": 1,
  "box_size": 12,
  "quantity_boxes": 2,
  "price": 125.5,
  "price_type": "UNIT"
}
```

### `InvoiceResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `invoice_number` | `string` | Sí |  |
| `sequence` | `integer` | Sí |  |
| `invoice_date` | `string<date>` | Sí |  |
| `order_date` | `string<date> | null` | No |  |
| `arrival_date` | `string<date> | null` | No |  |
| `status` | `InvoiceStatus` | Sí |  |
| `dollar_exchange_rate` | `string` | Sí |  |
| `general_expenses` | `string` | Sí |  |
| `approximate_profit_rate` | `string` | Sí |  |
| `notes` | `string | null` | No |  |
| `warehouse_id` | `integer` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |
| `warehouse` | `WarehouseLineResponse | null` | No |  |
| `lines` | `array<InvoiceLineResponse>` | No |  |
| `subtotal` | `string` | Sí |  |
| `general_expenses_total` | `string` | Sí |  |
| `approximate_profit_total` | `string` | Sí |  |
| `total` | `string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "status": "DRAFT",
  "dollar_exchange_rate": "125.50",
  "general_expenses": "125.50",
  "approximate_profit_rate": "125.50",
  "notes": "Texto de ejemplo",
  "warehouse_id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "warehouse": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "lines": [
    {
      "id": 1,
      "invoice_id": 1,
      "product_id": 1,
      "box_size": 12,
      "quantity_boxes": 2,
      "total_units": 24,
      "price": "125.50",
      "price_type": "UNIT",
      "inventory_applied": true,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "product": {
        "id": 1,
        "name": "Nombre de ejemplo",
        "code": "PROD-001"
      },
      "box_price": "125.50",
      "unit_price": "125.50",
      "total_price": "125.50"
    }
  ],
  "subtotal": "125.50",
  "general_expenses_total": "125.50",
  "approximate_profit_total": "125.50",
  "total": "125.50"
}
```

### `InvoiceStatus`

- Tipo: `enum`
- Valores: `DRAFT, ARRIVED, CANCELLED`

### `InvoiceStatusCounts`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `pending` | `integer` | Sí |  |
| `cancelled` | `integer` | Sí |  |
| `arrived_last_n_days` | `integer` | Sí |  |

Ejemplo:
```json
{
  "pending": 1,
  "cancelled": 1,
  "arrived_last_n_days": 14
}
```

### `InvoiceUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `invoice_number` | `string | null` | No |  |
| `sequence` | `integer | null` | No |  |
| `invoice_date` | `string<date> | null` | No |  |
| `order_date` | `string<date> | null` | No |  |
| `arrival_date` | `string<date> | null` | No |  |
| `dollar_exchange_rate` | `number | string | null` | No |  |
| `general_expenses` | `number | string | null` | No |  |
| `approximate_profit_rate` | `number | string | null` | No |  |
| `notes` | `string | null` | No |  |
| `warehouse_id` | `integer | null` | No |  |

Ejemplo:
```json
{
  "invoice_number": "FAC-001",
  "sequence": 1,
  "invoice_date": "2026-04-20",
  "order_date": "2026-04-20",
  "arrival_date": "2026-04-20",
  "dollar_exchange_rate": 125.5,
  "general_expenses": 125.5,
  "approximate_profit_rate": 125.5,
  "notes": "Texto de ejemplo",
  "warehouse_id": 1
}
```

### `InvoiceUpdateStatus`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `status` | `InvoiceStatus` | Sí |  |

Ejemplo:
```json
{
  "status": "DRAFT"
}
```

### `LoginRequest`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `email` | `string<email>` | Sí |  |
| `password` | `string<password>` | Sí |  |

Ejemplo:
```json
{
  "email": "usuario@ejemplo.com",
  "password": "Password123"
}
```

### `LoginResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `access_token` | `string` | Sí |  |
| `refresh_token` | `string` | Sí |  |
| `token_type` | `string` | No |  |
| `user` | `UserResponse` | Sí |  |

Ejemplo:
```json
{
  "access_token": "<access_token>",
  "refresh_token": "<refresh_token>",
  "token_type": "bearer",
  "user": {
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com",
    "role": "Administrador",
    "id": 1,
    "is_active": true,
    "is_verified": true,
    "is_admin": true,
    "created_at": "2026-04-20T12:00:00+00:00",
    "updated_at": "2026-04-20T12:00:00+00:00"
  }
}
```

### `ProductLineResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `name` | `string` | Sí |  |
| `code` | `string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "name": "Nombre de ejemplo",
  "code": "PROD-001"
}
```

### `ProductResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `code` | `string` | Sí |  |
| `description` | `string | null` | No |  |
| `category_id` | `integer` | Sí |  |
| `brand_id` | `integer` | Sí |  |
| `image` | `string | null` | No |  |
| `id` | `integer` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |
| `category` | `ProductCategoryRef | null` | No |  |
| `brand` | `ProductBrandRef | null` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp",
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "category": {
    "id": 1,
    "name": "Nombre de ejemplo"
  },
  "brand": {
    "id": 1,
    "name": "Nombre de ejemplo"
  }
}
```

### `ProductStockResponse-Input`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `code` | `string` | Sí |  |
| `description` | `string | null` | No |  |
| `category_id` | `integer` | Sí |  |
| `brand_id` | `integer` | Sí |  |
| `image` | `string | null` | No |  |
| `id` | `integer` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string<date-time>` | Sí |  |
| `updated_at` | `string<date-time>` | Sí |  |
| `category` | `ProductCategoryRef | null` | No |  |
| `brand` | `ProductBrandRef | null` | No |  |
| `stock_total` | `integer` | No |  |
| `stock_boxes_total` | `integer` | No |  |
| `inventory` | `array<InventoryStockItem-Input>` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp",
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "category": {
    "id": 1,
    "name": "Nombre de ejemplo"
  },
  "brand": {
    "id": 1,
    "name": "Nombre de ejemplo"
  },
  "stock_total": 25,
  "stock_boxes_total": 25,
  "inventory": [
    {
      "id": 1,
      "warehouse_id": 1,
      "product_id": 1,
      "box_size": 12,
      "stock": 25,
      "reserved_stock": 3,
      "available_boxes": 22,
      "avg_cost": 125.5,
      "last_cost": 125.5,
      "sales_last_price": 125.5,
      "sales_avg_price": 125.5,
      "is_active": true,
      "is_over_reserved": true
    }
  ]
}
```

### `ProductStockResponse-Output`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `code` | `string` | Sí |  |
| `description` | `string | null` | No |  |
| `category_id` | `integer` | Sí |  |
| `brand_id` | `integer` | Sí |  |
| `image` | `string | null` | No |  |
| `id` | `integer` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |
| `category` | `ProductCategoryRef | null` | No |  |
| `brand` | `ProductBrandRef | null` | No |  |
| `stock_total` | `integer` | No |  |
| `stock_boxes_total` | `integer` | No |  |
| `inventory` | `array<InventoryStockItem-Output>` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "code": "PROD-001",
  "description": "Descripción de ejemplo",
  "category_id": 1,
  "brand_id": 1,
  "image": "https://ejemplo.com/imagen.webp",
  "id": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "category": {
    "id": 1,
    "name": "Nombre de ejemplo"
  },
  "brand": {
    "id": 1,
    "name": "Nombre de ejemplo"
  },
  "stock_total": 25,
  "stock_boxes_total": 25,
  "inventory": [
    {
      "id": 1,
      "warehouse_id": 1,
      "product_id": 1,
      "box_size": 12,
      "stock": 25,
      "reserved_stock": 3,
      "available_boxes": 22,
      "avg_cost": "125.50",
      "last_cost": "125.50",
      "sales_last_price": 125.5,
      "sales_avg_price": 125.5,
      "is_active": true,
      "is_over_reserved": true
    }
  ]
}
```

### `RefreshTokenRequest`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `refresh_token` | `string` | Sí |  |

Ejemplo:
```json
{
  "refresh_token": "<refresh_token>"
}
```

### `SaleCreateWithLines`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `sale_date` | `string<date>` | No |  |
| `status` | `SaleStatus` | No |  |
| `notes` | `string | null` | No |  |
| `client_id` | `integer` | Sí |  |
| `lines` | `array<SaleLineCreate>` | No |  |

Ejemplo:
```json
{
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "notes": "Texto de ejemplo",
  "client_id": 1,
  "lines": [
    {
      "inventory_id": 1,
      "quantity_boxes": 2,
      "quantity_units": 5,
      "price": 125.5,
      "price_type": "UNIT"
    }
  ]
}
```

### `SaleLineCreate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `inventory_id` | `integer` | Sí |  |
| `quantity_boxes` | `integer | null` | No |  |
| `quantity_units` | `integer | null` | No |  |
| `price` | `number | string` | Sí |  |
| `price_type` | `SaleLinePriceType` | No |  |

Ejemplo:
```json
{
  "inventory_id": 1,
  "quantity_boxes": 2,
  "quantity_units": 5,
  "price": 125.5,
  "price_type": "UNIT"
}
```

### `SaleLineInventoryRef`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `stock` | `integer` | Sí |  |
| `reserved_stock` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `product` | `ProductLineResponse | null` | No |  |
| `warehouse` | `WarehouseLineResponse | null` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "stock": 25,
  "reserved_stock": 3,
  "box_size": 12,
  "product": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "code": "PROD-001"
  },
  "warehouse": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "address": "Calle Ejemplo 123",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  }
}
```

### `SaleLinePriceType`

- Tipo: `enum`
- Valores: `UNIT, BOX`

### `SaleLineQuantityMode`

- Tipo: `enum`
- Valores: `BOX, UNIT`

### `SaleLineResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `sale_id` | `integer` | Sí |  |
| `inventory_id` | `integer` | Sí |  |
| `quantity_boxes` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `price` | `string` | Sí |  |
| `price_type` | `SaleLinePriceType` | Sí |  |
| `quantity_mode` | `SaleLineQuantityMode` | Sí |  |
| `unit_price` | `string` | Sí |  |
| `box_price` | `string` | Sí |  |
| `total_price` | `string` | Sí |  |
| `product_code` | `string | null` | No |  |
| `product_name` | `string | null` | No |  |
| `reservation_applied` | `boolean` | Sí |  |
| `inventory_applied` | `boolean` | Sí |  |
| `source_box_size` | `integer | null` | No |  |
| `projected_units_from_stock` | `integer | null` | No |  |
| `projected_boxes_to_open` | `integer | null` | No |  |
| `projected_units_leftover` | `integer | null` | No |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |
| `inventory` | `SaleLineInventoryRef | null` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "sale_id": 1,
  "inventory_id": 1,
  "quantity_boxes": 2,
  "box_size": 12,
  "price": "125.50",
  "price_type": "UNIT",
  "quantity_mode": "BOX",
  "unit_price": "125.50",
  "box_price": "125.50",
  "total_price": "125.50",
  "product_code": "Texto de ejemplo",
  "product_name": "Texto de ejemplo",
  "reservation_applied": true,
  "inventory_applied": true,
  "source_box_size": 12,
  "projected_units_from_stock": 25,
  "projected_boxes_to_open": 1,
  "projected_units_leftover": 1,
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "inventory": {
    "id": 1,
    "stock": 25,
    "reserved_stock": 3,
    "box_size": 12,
    "product": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "code": "PROD-001"
    },
    "warehouse": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "address": "Calle Ejemplo 123",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678"
    }
  }
}
```

### `SaleLineUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `inventory_id` | `integer | null` | No |  |
| `quantity_boxes` | `integer | null` | No |  |
| `quantity_units` | `integer | null` | No |  |
| `price` | `number | string | null` | No |  |
| `price_type` | `SaleLinePriceType | null` | No |  |

Ejemplo:
```json
{
  "inventory_id": 1,
  "quantity_boxes": 2,
  "quantity_units": 5,
  "price": 125.5,
  "price_type": "UNIT"
}
```

### `SaleReportClientRef`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `name` | `string` | Sí |  |
| `email` | `string | null` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "name": "Nombre de ejemplo",
  "email": "usuario@ejemplo.com"
}
```

### `SaleReportResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `period` | `object` | Sí |  |
| `filters` | `object` | Sí |  |
| `totals` | `SaleReportTotals-Output` | Sí |  |
| `rows` | `array<SaleReportRow-Output>` | No |  |
| `sales` | `array<SaleReportSaleDetail-Output>` | No |  |

Ejemplo:
```json
{
  "period": {},
  "filters": {},
  "totals": {
    "sales_count": 1,
    "total_boxes": 1,
    "total_amount": "125.50"
  },
  "rows": [
    {
      "group_by": "product",
      "group_id": 1,
      "group_label": "Grupo de ejemplo",
      "total_boxes": 1,
      "total_amount": "125.50"
    }
  ],
  "sales": [
    {
      "id": 1,
      "sale_date": "2026-04-20",
      "status": "DRAFT",
      "client": {
        "id": 1,
        "name": "Nombre de ejemplo",
        "email": "usuario@ejemplo.com"
      },
      "total_amount": "125.50",
      "created_by": 1,
      "updated_by": 1,
      "paid_by": 1,
      "cancelled_by": 1,
      "created_by_name": "Texto de ejemplo",
      "updated_by_name": "Texto de ejemplo",
      "paid_by_name": "Texto de ejemplo",
      "cancelled_by_name": "Texto de ejemplo",
      "lines": [
        {
          "id": 1,
          "inventory_id": 1,
          "quantity_boxes": 2,
          "box_size": 12,
          "price": "125.50",
          "price_type": "UNIT",
          "unit_price": "125.50",
          "box_price": "125.50",
          "total_price": "125.50",
          "product_code": "Texto de ejemplo",
          "product_name": "Texto de ejemplo",
          "inventory": {
            "id": 1,
            "stock": 25,
            "reserved_stock": 3,
            "box_size": 12,
            "product": {
              "id": 1,
              "name": "Nombre de ejemplo",
              "code": "PROD-001"
            },
            "warehouse": {
              "id": 1,
              "name": "Nombre de ejemplo",
              "address": "Calle Ejemplo 123",
              "email": "usuario@ejemplo.com",
              "phone": "5512345678"
            }
          }
        }
      ]
    }
  ]
}
```

### `SaleReportRow-Input`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `group_by` | `string` | Sí |  |
| `group_id` | `integer` | Sí |  |
| `group_label` | `string` | Sí |  |
| `total_boxes` | `integer` | Sí |  |
| `total_amount` | `number | string` | Sí |  |

Ejemplo:
```json
{
  "group_by": "product",
  "group_id": 1,
  "group_label": "Grupo de ejemplo",
  "total_boxes": 1,
  "total_amount": 125.5
}
```

### `SaleReportRow-Output`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `group_by` | `string` | Sí |  |
| `group_id` | `integer` | Sí |  |
| `group_label` | `string` | Sí |  |
| `total_boxes` | `integer` | Sí |  |
| `total_amount` | `string` | Sí |  |

Ejemplo:
```json
{
  "group_by": "product",
  "group_id": 1,
  "group_label": "Grupo de ejemplo",
  "total_boxes": 1,
  "total_amount": "125.50"
}
```

### `SaleReportSaleDetail-Input`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `sale_date` | `string<date>` | Sí |  |
| `status` | `SaleStatus` | Sí |  |
| `client` | `SaleReportClientRef | null` | No |  |
| `total_amount` | `number | string` | Sí |  |
| `created_by` | `integer | null` | No |  |
| `updated_by` | `integer | null` | No |  |
| `paid_by` | `integer | null` | No |  |
| `cancelled_by` | `integer | null` | No |  |
| `created_by_name` | `string | null` | No |  |
| `updated_by_name` | `string | null` | No |  |
| `paid_by_name` | `string | null` | No |  |
| `cancelled_by_name` | `string | null` | No |  |
| `lines` | `array<SaleReportSaleLine-Input>` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "client": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com"
  },
  "total_amount": 125.5,
  "created_by": 1,
  "updated_by": 1,
  "paid_by": 1,
  "cancelled_by": 1,
  "created_by_name": "Texto de ejemplo",
  "updated_by_name": "Texto de ejemplo",
  "paid_by_name": "Texto de ejemplo",
  "cancelled_by_name": "Texto de ejemplo",
  "lines": [
    {
      "id": 1,
      "inventory_id": 1,
      "quantity_boxes": 2,
      "box_size": 12,
      "price": 125.5,
      "price_type": "UNIT",
      "unit_price": 125.5,
      "box_price": 125.5,
      "total_price": 125.5,
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "inventory": {
        "id": 1,
        "stock": 25,
        "reserved_stock": 3,
        "box_size": 12,
        "product": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "code": "PROD-001"
        },
        "warehouse": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "address": "Calle Ejemplo 123",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        }
      }
    }
  ]
}
```

### `SaleReportSaleDetail-Output`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `sale_date` | `string<date>` | Sí |  |
| `status` | `SaleStatus` | Sí |  |
| `client` | `SaleReportClientRef | null` | No |  |
| `total_amount` | `string` | Sí |  |
| `created_by` | `integer | null` | No |  |
| `updated_by` | `integer | null` | No |  |
| `paid_by` | `integer | null` | No |  |
| `cancelled_by` | `integer | null` | No |  |
| `created_by_name` | `string | null` | No |  |
| `updated_by_name` | `string | null` | No |  |
| `paid_by_name` | `string | null` | No |  |
| `cancelled_by_name` | `string | null` | No |  |
| `lines` | `array<SaleReportSaleLine-Output>` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "client": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com"
  },
  "total_amount": "125.50",
  "created_by": 1,
  "updated_by": 1,
  "paid_by": 1,
  "cancelled_by": 1,
  "created_by_name": "Texto de ejemplo",
  "updated_by_name": "Texto de ejemplo",
  "paid_by_name": "Texto de ejemplo",
  "cancelled_by_name": "Texto de ejemplo",
  "lines": [
    {
      "id": 1,
      "inventory_id": 1,
      "quantity_boxes": 2,
      "box_size": 12,
      "price": "125.50",
      "price_type": "UNIT",
      "unit_price": "125.50",
      "box_price": "125.50",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "inventory": {
        "id": 1,
        "stock": 25,
        "reserved_stock": 3,
        "box_size": 12,
        "product": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "code": "PROD-001"
        },
        "warehouse": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "address": "Calle Ejemplo 123",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        }
      }
    }
  ]
}
```

### `SaleReportSaleLine-Input`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `inventory_id` | `integer` | Sí |  |
| `quantity_boxes` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `price` | `number | string` | Sí |  |
| `price_type` | `SaleLinePriceType` | Sí |  |
| `unit_price` | `number | string` | Sí |  |
| `box_price` | `number | string` | Sí |  |
| `total_price` | `number | string` | Sí |  |
| `product_code` | `string | null` | No |  |
| `product_name` | `string | null` | No |  |
| `inventory` | `SaleLineInventoryRef | null` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "inventory_id": 1,
  "quantity_boxes": 2,
  "box_size": 12,
  "price": 125.5,
  "price_type": "UNIT",
  "unit_price": 125.5,
  "box_price": 125.5,
  "total_price": 125.5,
  "product_code": "Texto de ejemplo",
  "product_name": "Texto de ejemplo",
  "inventory": {
    "id": 1,
    "stock": 25,
    "reserved_stock": 3,
    "box_size": 12,
    "product": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "code": "PROD-001"
    },
    "warehouse": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "address": "Calle Ejemplo 123",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678"
    }
  }
}
```

### `SaleReportSaleLine-Output`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `inventory_id` | `integer` | Sí |  |
| `quantity_boxes` | `integer` | Sí |  |
| `box_size` | `integer` | Sí |  |
| `price` | `string` | Sí |  |
| `price_type` | `SaleLinePriceType` | Sí |  |
| `unit_price` | `string` | Sí |  |
| `box_price` | `string` | Sí |  |
| `total_price` | `string` | Sí |  |
| `product_code` | `string | null` | No |  |
| `product_name` | `string | null` | No |  |
| `inventory` | `SaleLineInventoryRef | null` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "inventory_id": 1,
  "quantity_boxes": 2,
  "box_size": 12,
  "price": "125.50",
  "price_type": "UNIT",
  "unit_price": "125.50",
  "box_price": "125.50",
  "total_price": "125.50",
  "product_code": "Texto de ejemplo",
  "product_name": "Texto de ejemplo",
  "inventory": {
    "id": 1,
    "stock": 25,
    "reserved_stock": 3,
    "box_size": 12,
    "product": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "code": "PROD-001"
    },
    "warehouse": {
      "id": 1,
      "name": "Nombre de ejemplo",
      "address": "Calle Ejemplo 123",
      "email": "usuario@ejemplo.com",
      "phone": "5512345678"
    }
  }
}
```

### `SaleReportTotals-Input`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `sales_count` | `integer` | Sí |  |
| `total_boxes` | `integer` | Sí |  |
| `total_amount` | `number | string` | Sí |  |

Ejemplo:
```json
{
  "sales_count": 1,
  "total_boxes": 1,
  "total_amount": 125.5
}
```

### `SaleReportTotals-Output`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `sales_count` | `integer` | Sí |  |
| `total_boxes` | `integer` | Sí |  |
| `total_amount` | `string` | Sí |  |

Ejemplo:
```json
{
  "sales_count": 1,
  "total_boxes": 1,
  "total_amount": "125.50"
}
```

### `SaleResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `sale_date` | `string<date>` | Sí |  |
| `status` | `SaleStatus` | Sí |  |
| `total_price` | `string` | Sí |  |
| `notes` | `string | null` | Sí |  |
| `client_id` | `integer` | Sí |  |
| `client` | `ClientLineResponse | null` | No |  |
| `is_active` | `boolean` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |
| `created_by` | `integer | null` | No |  |
| `updated_by` | `integer | null` | No |  |
| `paid_by` | `integer | null` | No |  |
| `cancelled_by` | `integer | null` | No |  |
| `paid_at` | `string | null` | No |  |
| `cancelled_at` | `string | null` | No |  |
| `created_by_name` | `string | null` | No |  |
| `updated_by_name` | `string | null` | No |  |
| `paid_by_name` | `string | null` | No |  |
| `cancelled_by_name` | `string | null` | No |  |
| `created_by_user` | `UserAuditLineResponse | null` | No |  |
| `paid_by_user` | `UserAuditLineResponse | null` | No |  |
| `cancelled_by_user` | `UserAuditLineResponse | null` | No |  |
| `lines` | `array<SaleLineResponse>` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "sale_date": "2026-04-20",
  "status": "DRAFT",
  "total_price": "125.50",
  "notes": "Texto de ejemplo",
  "client_id": 1,
  "client": {
    "id": 1,
    "name": "Nombre de ejemplo",
    "email": "usuario@ejemplo.com",
    "phone": "5512345678"
  },
  "is_active": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "created_by": 1,
  "updated_by": 1,
  "paid_by": 1,
  "cancelled_by": 1,
  "paid_at": "2026-04-20T12:00:00+00:00",
  "cancelled_at": "2026-04-20T12:00:00+00:00",
  "created_by_name": "Texto de ejemplo",
  "updated_by_name": "Texto de ejemplo",
  "paid_by_name": "Texto de ejemplo",
  "cancelled_by_name": "Texto de ejemplo",
  "created_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "paid_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "cancelled_by_user": {
    "id": 1,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "usuario@ejemplo.com"
  },
  "lines": [
    {
      "id": 1,
      "sale_id": 1,
      "inventory_id": 1,
      "quantity_boxes": 2,
      "box_size": 12,
      "price": "125.50",
      "price_type": "UNIT",
      "quantity_mode": "BOX",
      "unit_price": "125.50",
      "box_price": "125.50",
      "total_price": "125.50",
      "product_code": "Texto de ejemplo",
      "product_name": "Texto de ejemplo",
      "reservation_applied": true,
      "inventory_applied": true,
      "source_box_size": 12,
      "projected_units_from_stock": 25,
      "projected_boxes_to_open": 1,
      "projected_units_leftover": 1,
      "is_active": true,
      "created_at": "2026-04-20T12:00:00+00:00",
      "updated_at": "2026-04-20T12:00:00+00:00",
      "inventory": {
        "id": 1,
        "stock": 25,
        "reserved_stock": 3,
        "box_size": 12,
        "product": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "code": "PROD-001"
        },
        "warehouse": {
          "id": 1,
          "name": "Nombre de ejemplo",
          "address": "Calle Ejemplo 123",
          "email": "usuario@ejemplo.com",
          "phone": "5512345678"
        }
      }
    }
  ]
}
```

### `SaleStatus`

- Tipo: `enum`
- Valores: `DRAFT, PAID, CANCELLED`

### `SaleStatusCounts`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `pending` | `integer` | Sí |  |
| `cancelled` | `integer` | Sí |  |
| `paid_last_n_days` | `integer` | Sí |  |

Ejemplo:
```json
{
  "pending": 1,
  "cancelled": 1,
  "paid_last_n_days": 14
}
```

### `SaleUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `sale_date` | `string<date> | null` | No |  |
| `notes` | `string | null` | No |  |
| `client_id` | `integer | null` | No |  |

Ejemplo:
```json
{
  "sale_date": "2026-04-20",
  "notes": "Texto de ejemplo",
  "client_id": 1
}
```

### `SaleUpdateStatus`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `status` | `SaleStatus` | Sí |  |

Ejemplo:
```json
{
  "status": "DRAFT"
}
```

### `SystemSummaryResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `days` | `integer` | Sí |  |
| `cutoff_date` | `string<date>` | Sí |  |
| `generated_at` | `string` | Sí |  |
| `catalogs` | `CatalogCounts` | Sí |  |
| `invoices` | `InvoiceStatusCounts` | Sí |  |
| `sales` | `SaleStatusCounts` | Sí |  |

Ejemplo:
```json
{
  "days": 14,
  "cutoff_date": "2026-04-20",
  "generated_at": "2026-04-20T12:00:00+00:00",
  "catalogs": {
    "products": 1,
    "clients": 1,
    "warehouses": 1,
    "users": 1,
    "categories": 1,
    "brands": 1
  },
  "invoices": {
    "pending": 1,
    "cancelled": 1,
    "arrived_last_n_days": 14
  },
  "sales": {
    "pending": 1,
    "cancelled": 1,
    "paid_last_n_days": 14
  }
}
```

### `TokenPairResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `access_token` | `string` | Sí |  |
| `refresh_token` | `string` | Sí |  |
| `token_type` | `string` | No |  |

Ejemplo:
```json
{
  "access_token": "<access_token>",
  "refresh_token": "<refresh_token>",
  "token_type": "bearer"
}
```

### `UserAuditLineResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `first_name` | `string` | Sí |  |
| `last_name` | `string` | Sí |  |
| `email` | `string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com"
}
```

### `UserCreate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `password` | `string<password>` | Sí |  |
| `first_name` | `string` | Sí |  |
| `last_name` | `string` | Sí |  |
| `email` | `string<email>` | Sí |  |
| `role` | `UserRole` | No |  |

Ejemplo:
```json
{
  "password": "Password123",
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador"
}
```

### `UserCreateAdmin`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `password` | `string<password>` | Sí |  |
| `first_name` | `string` | Sí |  |
| `last_name` | `string` | Sí |  |
| `email` | `string<email>` | Sí |  |
| `role` | `UserRole` | No |  |

Ejemplo:
```json
{
  "password": "Password123",
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador"
}
```

### `UserResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `first_name` | `string` | Sí |  |
| `last_name` | `string` | Sí |  |
| `email` | `string<email>` | Sí |  |
| `role` | `UserRole` | Sí |  |
| `id` | `integer` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `is_verified` | `boolean` | Sí |  |
| `is_admin` | `boolean` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |

Ejemplo:
```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "role": "Administrador",
  "id": 1,
  "is_active": true,
  "is_verified": true,
  "is_admin": true,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

### `UserRole`

- Tipo: `enum`
- Valores: `Administrador, Vendedor, Almacenista, Mixto`

### `UserUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `first_name` | `string | null` | No |  |
| `last_name` | `string | null` | No |  |
| `email` | `string<email> | null` | No |  |
| `password` | `string<password> | null` | No |  |
| `role` | `UserRole | null` | No |  |

Ejemplo:
```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "usuario@ejemplo.com",
  "password": "Password123",
  "role": "Administrador"
}
```

### `UserUpdateStatus`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `is_active` | `boolean` | Sí |  |

Ejemplo:
```json
{
  "is_active": true
}
```

### `ValidationError`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `loc` | `array<string | integer>` | Sí |  |
| `msg` | `string` | Sí |  |
| `type` | `string` | Sí |  |

Ejemplo:
```json
{
  "loc": [
    "Texto de ejemplo"
  ],
  "msg": "Texto de ejemplo",
  "type": "Texto de ejemplo"
}
```

### `WarehouseCreate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `address` | `string` | Sí |  |
| `email` | `string | null` | No |  |
| `phone` | `string | null` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678"
}
```

### `WarehouseLineResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `name` | `string` | Sí |  |
| `address` | `string` | Sí |  |
| `email` | `string | null` | No |  |
| `phone` | `string | null` | No |  |

Ejemplo:
```json
{
  "id": 1,
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678"
}
```

### `WarehouseResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `address` | `string` | Sí |  |
| `email` | `string | null` | No |  |
| `phone` | `string | null` | No |  |
| `id` | `integer` | Sí |  |
| `is_active` | `boolean` | Sí |  |
| `deleted_at` | `string | null` | No |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "id": 1,
  "is_active": true,
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

### `WarehouseUpdate`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string | null` | No |  |
| `address` | `string | null` | No |  |
| `email` | `string | null` | No |  |
| `phone` | `string | null` | No |  |
| `is_active` | `boolean | null` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "address": "Calle Ejemplo 123",
  "email": "usuario@ejemplo.com",
  "phone": "5512345678",
  "is_active": true
}
```

### `BrandResponse`
> Nombre en OpenAPI: `src__modules__brand__brand_schema__BrandResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `id` | `integer` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |
| `deleted_at` | `string | null` | No |  |
| `is_active` | `boolean` | No |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00",
  "deleted_at": "2026-04-20T12:00:00+00:00",
  "is_active": true
}
```

### `CategoryResponse`
> Nombre en OpenAPI: `src__modules__category__category_schema__CategoryResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | `string` | Sí |  |
| `description` | `string | null` | No |  |
| `is_active` | `boolean` | No |  |
| `id` | `integer` | Sí |  |
| `created_at` | `string` | Sí |  |
| `updated_at` | `string` | Sí |  |

Ejemplo:
```json
{
  "name": "Nombre de ejemplo",
  "description": "Descripción de ejemplo",
  "is_active": true,
  "id": 1,
  "created_at": "2026-04-20T12:00:00+00:00",
  "updated_at": "2026-04-20T12:00:00+00:00"
}
```

### `ProductBrandRef`
> Nombre en OpenAPI: `src__modules__product__product_schema__BrandResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `name` | `string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "name": "Nombre de ejemplo"
}
```

### `ProductCategoryRef`
> Nombre en OpenAPI: `src__modules__product__product_schema__CategoryResponse`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | `integer` | Sí |  |
| `name` | `string` | Sí |  |

Ejemplo:
```json
{
  "id": 1,
  "name": "Nombre de ejemplo"
}
```
