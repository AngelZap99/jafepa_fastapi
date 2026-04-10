# Contrato API - Inventario

Base URL:

```text
/api/inventory
```

Reglas generales:

- `Product` no maneja precio.
- `Inventory` devuelve `avg_cost` y `last_cost`, pero frontend no debe mandarlos en create/update.
- `avg_cost` y `last_cost` sólo se actualizan automáticamente por facturas.
- La unicidad actual del inventario es `product_id + warehouse_id + box_size`.
- En creación manual de inventario, `avg_cost` y `last_cost` inician en `0`.

## 1. Listar Inventario

Endpoint:

```http
GET /api/inventory/list
```

Query params:

| Param | Tipo | Requerido | Descripción |
|---|---:|---:|---|
| `almacen` | `string` | No | Puede ser nombre o id del almacén |
| `skip` | `number` | No | Default `0` |
| `limit` | `number` | No | Límite de registros |

Ejemplo:

```http
GET /api/inventory/list?almacen=3&skip=0&limit=20
```

Response `200`:

```json
[
  {
    "id": 10,
    "stock": 120,
    "box_size": 12,
    "warehouse_id": 3,
    "product_id": 25,
    "avg_cost": 45.5,
    "last_cost": 47.0,
    "is_active": true,
    "created_at": "2026-04-09T12:00:00Z",
    "updated_at": "2026-04-09T12:00:00Z",
    "warehouse": {
      "id": 3,
      "name": "Almacen Centro",
      "address": "Calle 1",
      "email": "centro@example.com",
      "phone": "+525500000000",
      "is_active": true,
      "deleted_at": null,
      "created_at": "2026-04-09T12:00:00Z",
      "updated_at": "2026-04-09T12:00:00Z"
    },
    "product": {
      "id": 25,
      "name": "Taladro",
      "code": "TAL-001",
      "description": "Taladro industrial",
      "category_id": 2,
      "subcategory_id": 8,
      "brand_id": 4,
      "image": "https://...",
      "is_active": true,
      "created_at": "2026-04-09T12:00:00Z",
      "updated_at": "2026-04-09T12:00:00Z",
      "category": {
        "id": 2,
        "name": "Herramientas"
      },
      "subcategory": {
        "id": 8,
        "name": "Electricas"
      },
      "brand": {
        "id": 4,
        "name": "Bosch"
      }
    }
  }
]
```

## 2. Obtener Inventario Por ID

Endpoint:

```http
GET /api/inventory/{inventory_id}
```

Path params:

| Param | Tipo | Requerido | Descripción |
|---|---:|---:|---|
| `inventory_id` | `number` | Si | ID del inventario |

Response `200`:

Devuelve un inventario expandido con el mismo shape de `GET /api/inventory/list`.

Error `404`:

```json
{
  "message": "Inventory record not found"
}
```

## 3. Crear Inventario Para Producto Existente

Endpoint:

```http
POST /api/inventory/create
```

Content-Type:

```text
application/json
```

Body:

```json
{
  "product_id": 25,
  "warehouse_id": 3,
  "stock": 120,
  "box_size": 12,
  "is_active": true
}
```

Body params:

| Prop | Tipo | Requerido | Validación |
|---|---:|---:|---|
| `product_id` | `number` | Si | `> 0`, debe existir |
| `warehouse_id` | `number` | Si | `> 0`, debe existir |
| `stock` | `number` | Si | `>= 0` |
| `box_size` | `number` | Si | `>= 1` |
| `is_active` | `boolean` | No | Default `true` |

No enviar:

```json
{
  "avg_cost": 10,
  "last_cost": 10
}
```

Response `201`:

Devuelve un inventario expandido con el mismo shape de `GET /api/inventory/list`.

Error `404`:

```json
{
  "message": "Product not found"
}
```

```json
{
  "message": "Warehouse not found"
}
```

Error `409`:

```json
{
  "message": "Inventory already exists for this product, warehouse, and box size",
  "errors": [
    {
      "field": "product_id",
      "message": "Duplicate inventory for selected warehouse and box size"
    },
    {
      "field": "box_size",
      "message": "This box size already exists for the selected product and warehouse"
    }
  ]
}
```

Error `422`:

Validación de payload.

## 4. Crear Producto + Inventario

Endpoint:

```http
POST /api/inventory/create-with-product
```

Content-Type:

```text
multipart/form-data
```

Form data:

| Campo | Tipo | Requerido | Validación |
|---|---:|---:|---|
| `name` | `string` | Si | Min 2, max 250 |
| `code` | `string` | Si | Min 1, max 100, se normaliza a mayúsculas |
| `description` | `string` | No | Max 500 |
| `category_id` | `number` | Si | `> 0`, debe existir |
| `subcategory_id` | `number` | No | `> 0`, debe existir si se envía |
| `brand_id` | `number` | Si | `> 0`, debe existir |
| `warehouse_id` | `number` | Si | `> 0`, debe existir |
| `stock` | `number` | Si | `>= 0` |
| `box_size` | `number` | Si | `>= 1` |
| `is_active` | `boolean` | No | Default `true` |
| `image_file` | `file` | No | Imagen opcional |

Ejemplo:

```text
name=Taladro
code=TAL-001
description=Taladro industrial
category_id=2
subcategory_id=8
brand_id=4
warehouse_id=3
stock=120
box_size=12
is_active=true
image_file=<archivo opcional>
```

Response `201`:

Devuelve un inventario expandido con el mismo shape de `GET /api/inventory/list`.

Error `409`:

```json
{
  "message": "Product data conflicts with an existing record",
  "errors": [
    {
      "field": "code",
      "message": "El código 'TAL-001' ya está registrado"
    }
  ]
}
```

```json
{
  "message": "Inventory already exists for this product, warehouse, and box size",
  "errors": [
    {
      "field": "product_id",
      "message": "Duplicate inventory for selected warehouse and box size"
    }
  ]
}
```

Error `422`:

```json
{
  "message": "Invalid category_id reference"
}
```

```json
{
  "message": "Invalid brand_id reference"
}
```

```json
{
  "message": "Invalid subcategory_id reference"
}
```

## 5. Actualizar Inventario

Endpoint:

```http
PUT /api/inventory/update/{inventory_id}
```

Content-Type:

```text
application/json
```

Path params:

| Param | Tipo | Requerido | Descripción |
|---|---:|---:|---|
| `inventory_id` | `number` | Si | ID del inventario |

Body:

Todos los campos son opcionales, pero debe enviarse al menos uno.

```json
{
  "stock": 150,
  "box_size": 10,
  "is_active": true
}
```

Body params:

| Prop | Tipo | Requerido | Validación |
|---|---:|---:|---|
| `stock` | `number` | No | `>= 0` |
| `box_size` | `number` | No | `>= 1` |
| `is_active` | `boolean` | No | `true` o `false` |

No enviar:

```json
{
  "avg_cost": 10,
  "last_cost": 10,
  "product_id": 25,
  "warehouse_id": 3
}
```

Response `200`:

Devuelve un inventario expandido con el mismo shape de `GET /api/inventory/list`.

Error `404`:

```json
{
  "message": "Inventory record not found"
}
```

Error `409`:

```json
{
  "message": "Inventory already exists for this product, warehouse, and box size",
  "errors": [
    {
      "field": "box_size",
      "message": "This box size already exists for the selected product and warehouse"
    }
  ]
}
```

Error `422`:

Si mandan campos no permitidos o body vacío.

## 6. Eliminar Inventario

Endpoint:

```http
DELETE /api/inventory/delete/{inventory_id}
```

Path params:

| Param | Tipo | Requerido | Descripción |
|---|---:|---:|---|
| `inventory_id` | `number` | Si | ID del inventario |

Body:

No requiere body.

Response `200`:

Devuelve un inventario expandido con el mismo shape de `GET /api/inventory/list`, con `is_active=false`.

Error `404`:

```json
{
  "message": "Inventory record not found"
}
```

## 7. Listar Movimientos De Inventario

Endpoint:

```http
GET /api/inventory/movements
```

Query params:

| Param | Tipo | Requerido | Descripción |
|---|---:|---:|---|
| `inventory_id` | `number` | No | Filtra por inventario |
| `product_id` | `number` | No | Filtra por producto |
| `warehouse_id` | `number` | No | Filtra por almacén |
| `invoice_id` | `number` | No | Filtra por factura |
| `invoice_line_id` | `number` | No | Filtra por línea de factura |
| `sale_id` | `number` | No | Filtra por venta |
| `sale_line_id` | `number` | No | Filtra por línea de venta |
| `source_type` | `string` | No | `INVOICE`, `SALE`, `MANUAL` |
| `event_type` | `string` | No | Ver valores abajo |
| `movement_type` | `string` | No | `IN`, `OUT` |
| `from_date` | `datetime` | No | Fecha inicial |
| `to_date` | `datetime` | No | Fecha final |
| `include_inactive` | `boolean` | No | Default `false` |
| `skip` | `number` | No | Default `0` |
| `limit` | `number` | No | Límite de registros |

`event_type` posibles:

```text
INVOICE_RECEIVED
INVOICE_UNRECEIVED
SALE_APPROVED
SALE_REVERSED
MANUAL_CREATED
MANUAL_STOCK_ADJUSTED
```

Response `200`:

```json
[
  {
    "id": 1,
    "movement_date": "2026-04-09T12:00:00Z",
    "movement_group_id": "uuid",
    "movement_sequence": 1,
    "source_type": "MANUAL",
    "event_type": "MANUAL_STOCK_ADJUSTED",
    "movement_type": "OUT",
    "quantity": 4,
    "unit_cost": 0,
    "prev_stock": 10,
    "new_stock": 6,
    "inventory_id": 10,
    "invoice_line_id": null,
    "sale_line_id": null,
    "is_active": true,
    "created_at": "2026-04-09T12:00:00Z",
    "updated_at": "2026-04-09T12:00:00Z",
    "inventory": {
      "id": 10,
      "product_id": 25,
      "warehouse_id": 3,
      "box_size": 12
    },
    "invoice_line": null,
    "sale_line": null
  }
]
```

## 8. Descargar PDF De Inventario

Endpoint:

```http
GET /api/inventory/pdf/all
```

Query params:

| Param | Tipo | Requerido | Descripción |
|---|---:|---:|---|
| `categoria` | `string` | No | Nombre o id |
| `subcategoria` | `string` | No | Nombre o id |
| `marca` | `string` | No | Nombre o id |
| `almacen` | `string` | No | Nombre o id |
| `buscar` | `string` | No | Busca por nombre o código |
| `exclude_ids` | `string` | No | CSV de ids a excluir |

Ejemplo:

```http
GET /api/inventory/pdf/all?almacen=3&marca=Bosch&exclude_ids=10,11,15
```

Response `200`:

```text
application/pdf
```

Error `422`:

```json
{
  "message": "exclude_ids must be a comma-separated list of integers",
  "errors": [
    {
      "field": "exclude_ids",
      "message": "Invalid inventory id list format"
    }
  ]
}
```

Error `503`:

```json
{
  "message": "Playwright browser executable is missing or unavailable. Run `playwright install chromium` in this environment."
}
```

## Formato General De Errores

Error simple:

```json
{
  "message": "Inventory record not found"
}
```

Error con campos:

```json
{
  "message": "Inventory already exists for this product, warehouse, and box size",
  "errors": [
    {
      "field": "product_id",
      "message": "Duplicate inventory for selected warehouse and box size"
    }
  ]
}
```
