# Seeder (datos demo) — JAFEPA FastAPI

Este proyecto incluye un **seeder por CLI** para generar datos de prueba de las **tablas de negocio**:
catálogos → productos → facturas (entrada a inventario) → ventas (salida de inventario).

No es un endpoint.

## Requisitos

- Tener una base de datos accesible y las variables de entorno configuradas (ver `.env.example`).
- No ejecutar contra producción: el `--reset` borra datos **de negocio**.

## Cómo se ejecuta

Desde la raíz del repo:

```bash
python3 -m src.shared.seed --help
```

Ejecución completa (por default corre todas las fases):

```bash
python3 -m src.shared.seed
```

## Reset seguro (solo negocio)

El flag `--reset --yes` **limpia únicamente tablas de negocio** (no borra `users`), y reinicia IDs en Postgres.

```bash
python3 -m src.shared.seed --reset --yes
```

## Reset (negocio + borrar usuarios no-admin)

Si además necesitas dejar únicamente el/los usuarios admin, puedes combinar:

```bash
python3 -m src.shared.seed --reset --prune-users-except-admin --yes
```

Notas:
- Requiere que exista al menos un usuario con `users.is_admin = TRUE`; si no existe, el comando se rehúsa a borrar usuarios para evitar dejarte sin acceso.
- Solo borra usuarios **no-admin**; el/los admin se conservan.

## Solo reset (sin reinsertar datos demo)

Si lo que quieres es dejar todo **vacío** (tablas de negocio limpias) sin volver a sembrar datos demo:

```bash
python3 -m src.shared.seed --reset-only --yes
```

Y si además quieres quedarte solo con el usuario admin:

```bash
python3 -m src.shared.seed --reset-only --prune-users-except-admin --yes
```

Notas:
- Si la tabla `users` no existe, el seeder puede **crear el schema** completo (incluida `users`). Por default **no** hace TRUNCATE/DELETE de `users` (salvo que uses `--prune-users-except-admin`).
- En Postgres usa `TRUNCATE ... RESTART IDENTITY CASCADE` sobre tablas de negocio.

## Fases disponibles

Puedes ejecutar una o varias fases (el orden importa):

```bash
python3 -m src.shared.seed --phases catalogs
python3 -m src.shared.seed --phases products
python3 -m src.shared.seed --phases invoices
python3 -m src.shared.seed --phases sales
```

Ejemplo: solo catálogos y productos:

```bash
python3 -m src.shared.seed --phases catalogs --phases products
```

## Qué crea cada fase

### 1) `catalogs`

Crea:
- `category` (raíces) y subcategorías usando `parent_id`
- `brand`
- `warehouse`
- `client`

### 2) `products`

Crea `product` con referencias a `category/subcategory/brand`.
Deja `image=None` (no sube imágenes a S3).

### 3) `invoices`

Crea `invoice` + `invoice_line` en `DRAFT`.
Si `--arrive-invoices` está activo (default), cambia a `ARRIVED` usando `InvoiceService`, lo que:
- crea/actualiza `inventory`
- registra `inventory_movement` (entradas)

### 4) `sales`

Crea `sale` + `sale_line` en `DRAFT` tomando inventario con stock disponible.
Si `--pay-sales` está activo (default), cambia a `PAID` usando `SaleService`, lo que:
- descuenta `inventory.stock`
- registra `inventory_movement` (salidas)

Nota: `PAID` es el estado que aplica inventario; volver de `PAID -> DRAFT` revierte inventario.

## Controles de cantidad

Puedes ajustar cuántos registros crear por entidad:

```bash
python3 -m src.shared.seed \
  --categories 10 \
  --subcategories-per-category 4 \
  --brands 12 \
  --warehouses 2 \
  --clients 50 \
  --products 200 \
  --invoices 30 --invoice-lines 6 \
  --sales 60 --sale-lines 4
```

## Modo de inserción (`--insert-mode`)

Aplica a **catálogos** y **productos**:

- `skip` (default): si encuentra un registro existente (por llave “única” interna del seeder), lo deja igual y no inserta otro.
- `upsert`: si existe, lo actualiza (y lo reactiva con `is_active=True`).
- `append`: intenta insertar de todas formas. Útil con DB vacía o después de `--reset`.

Recomendación:
- Para desarrollo diario: `--insert-mode skip` o `--insert-mode upsert`
- Para reset completo de negocio: `--reset --yes --insert-mode append`

## Determinismo (`--seed-value`)

El seeder usa un RNG determinístico:

```bash
python3 -m src.shared.seed --seed-value 123
```

Con el mismo `--seed-value` tendrás datos “similares” (aunque si ya había registros, los IDs/offsets pueden cambiar).

## Docker (opcional)

Si levantas con Docker Compose, puedes ejecutar dentro del contenedor `api`:

```bash
docker-compose up -d postgres api
docker-compose exec api python -m src.shared.seed --help
docker-compose exec api python -m src.shared.seed --reset --yes
```

## Troubleshooting

- `RuntimeError: Missing environment variables ...` → completa tu `.env` (DB_*).
- No se crean ventas → no hay stock suficiente; corre `invoices` con `--arrive-invoices` o incrementa `--invoices/--invoice-lines`.
- Errores por duplicados en `append` → usa `--insert-mode skip`/`upsert` o ejecuta `--reset --yes`.
