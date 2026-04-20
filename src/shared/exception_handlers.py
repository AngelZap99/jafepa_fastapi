from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.shared.schemas.common_responses import ErrorDetailResponse, ErrorResponse


logger = logging.getLogger(__name__)


STATUS_MESSAGES = {
    400: "Solicitud inválida",
    401: "No autorizado",
    403: "Acceso denegado",
    404: "Recurso no encontrado",
    405: "Método no permitido",
    409: "Conflicto con la solicitud",
    422: "Error de validación",
    500: "Error interno del servidor",
    503: "Servicio no disponible",
}


def _default_message(status_code: int) -> str:
    return STATUS_MESSAGES.get(status_code, "No se pudo procesar la solicitud")


def _translate_known_message(message: str) -> str:
    exact_messages = {
        "Validation error": "Error de validación",
        "Internal server error": "Error interno del servidor",
        "Not Found": "Recurso no encontrado",
        "Method Not Allowed": "Método no permitido",
        "Not authenticated": "No autenticado",
        "Invalid credentials": "Credenciales inválidas",
        "User is inactive": "El usuario está inactivo",
        "Invalid refresh token": "El token de actualización no es válido",
        "Invalid token": "El token no es válido",
        "Invalid token type": "El tipo de token no es válido",
        "Invalid token payload": "El contenido del token no es válido",
        "Token has expired": "El token ha expirado",
        "User not found or inactive": "El usuario no existe o está inactivo",
        "User not found": "Usuario no encontrado",
        "An admin user already exists": "Ya existe un usuario administrador",
        "Brand not found": "Marca no encontrada",
        "Category not found": "Categoría no encontrada",
        "Client not found": "Cliente no encontrado",
        "Warehouse not found": "Almacén no encontrado",
        "Product not found": "Producto no encontrado",
        "Invoice not found": "Factura no encontrada",
        "Invoice line not found": "Línea de factura no encontrada",
        "Sale not found": "Venta no encontrada",
        "Sale line not found": "Línea de venta no encontrada",
        "Inventory record not found": "Registro de inventario no encontrado",
        "Inventory record not found for invoice line": "No se encontró el inventario para la línea de factura",
        "Inventory record not found for sale line": "No se encontró el inventario para la línea de venta",
        "Inactive inventory cannot be used in sales": "El inventario inactivo no puede usarse en ventas",
        "Insufficient stock in boxes for sale line": "No hay stock suficiente en cajas para la línea de venta",
        "Inventory stock cannot be negative": "El inventario no puede quedar en negativo",
        "Invalid category_id reference": "La categoría seleccionada no es válida",
        "Invalid brand_id reference": "La marca seleccionada no es válida",
        "Invalid warehouse_id or product_id reference": "El almacén o producto seleccionado no es válido",
        "Invalid warehouse_id reference": "El almacén seleccionado no es válido",
        "Invalid product_id reference": "El producto seleccionado no es válido",
        "Invalid client_id or inventory reference": "El cliente o inventario seleccionado no es válido",
        "Invalid client_id reference": "El cliente seleccionado no es válido",
        "Invalid inventory reference": "El inventario seleccionado no es válido",
        "Invoice number or sequence already exists": "El número o folio de la factura ya existe.",
        "Unique constraint violated": "Ya existe un registro con esos datos.",
        "Invalid status transition.": "La transición de estado no es válida.",
        "Integrity constraint violated": "No se pudo procesar la solicitud.",
        "Integrity constraint violated while updating sale status.": "No se pudo actualizar el estado de la venta.",
        "Integrity constraint violated while creating product inventory": "No se pudo crear el inventario del producto.",
        "Inventory could not be created": "No se pudo crear el inventario.",
        "Failed to create sale line": "No se pudo crear la línea de venta.",
        "Invoice must be created in DRAFT or ARRIVED status.": "La factura debe crearse en estado borrador o recibida.",
        "Cannot modify an ARRIVED invoice. Revert status first.": "No se puede modificar una factura recibida. Primero revierte su estado.",
        "Cannot delete an ARRIVED invoice. Revert status first.": "No se puede eliminar una factura recibida. Primero revierte su estado.",
        "Cannot modify lines of an ARRIVED invoice. Revert status first.": "No se pueden modificar las líneas de una factura recibida. Primero revierte su estado.",
        "Sale must be created in DRAFT status.": "La venta debe crearse en estado borrador.",
        "Cannot delete a PAID sale. Revert status first.": "No se puede eliminar una venta pagada. Primero revierte su estado.",
        "Duplicate inventory_id in sale lines is not allowed": "No se permite repetir el inventario en las líneas de venta.",
        "Duplicate (product, box_size) in invoice lines is not allowed": "No se permite repetir la combinación de producto y tamaño de caja en las líneas de factura.",
        "At least one field must be provided": "Debes enviar al menos un campo.",
        "order_date cannot be earlier than invoice_date": "La fecha de orden no puede ser anterior a la fecha de factura.",
        "arrival_date cannot be earlier than order_date": "La fecha de llegada no puede ser anterior a la fecha de orden.",
        "total_units must equal box_size * quantity_boxes": "El total de unidades debe coincidir con la cantidad de cajas y el tamaño de caja.",
        "Product data conflicts with existing records": "Los datos del producto entran en conflicto con registros existentes.",
        "Product data conflicts with an existing record": "Los datos del producto entran en conflicto con un registro existente.",
        "Inventory already exists for this product, warehouse, and box size": "Ya existe un inventario para este producto, almacén y tamaño de caja.",
        "Duplicate inventory for selected warehouse and box size": "Ya existe un inventario para el almacén y tamaño de caja seleccionados.",
        "This box size already exists for the selected product and warehouse": "Este tamaño de caja ya existe para el producto y almacén seleccionados.",
        "exclude_ids must be a comma-separated list of integers": "La lista de IDs a excluir debe contener enteros separados por comas.",
        "Invalid inventory id list format": "El formato de la lista de ids de inventario no es válido.",
        "images cannot be empty": "La lista de imágenes no puede estar vacía.",
        "Missing env AWS_S3_BUCKET": "Falta configurar AWS_S3_BUCKET.",
        "file_path_or_url cannot be empty": "La ruta o URL del archivo no puede estar vacía.",
        "files and object_keys must have the same length": "La cantidad de archivos y claves de objeto debe coincidir.",
        "content_types must have the same length as files": "La cantidad de tipos de contenido debe coincidir con la cantidad de archivos.",
        "The password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number": "La contraseña debe tener al menos 8 caracteres e incluir una letra mayúscula, una letra minúscula y un número.",
    }
    if message in exact_messages:
        return exact_messages[message]

    pattern_translations: list[tuple[str, str]] = [
        (r"^Email (.+) is already taken$", r"El correo \1 ya está en uso."),
        (r"^Brand '(.+)' already exists$", r"La marca '\1' ya existe."),
        (r"^Category '(.+)' already exists\.?$", r"La categoría '\1' ya existe."),
        (
            r"^Warehouse name '(.+)' is already taken$",
            r"El nombre del almacén '\1' ya está en uso.",
        ),
        (
            r"^Image at index (\d+) exceeds max size \((.+) > (.+)\)$",
            r"La imagen en el índice \1 excede el tamaño máximo permitido (\2 > \3).",
        ),
        (
            r"^Image at index (\d+) has invalid extension '(.+)'$",
            r"La imagen en el índice \1 tiene una extensión no válida '\2'.",
        ),
        (
            r"^Image at index (\d+) has invalid MIME type '(.+)'$",
            r"La imagen en el índice \1 tiene un tipo MIME no válido '\2'.",
        ),
        (
            r"^Image at index (\d+) does not look like a valid JPG/PNG/WEBP by signature$",
            r"La imagen en el índice \1 no parece ser un archivo JPG, PNG o WEBP válido.",
        ),
        (
            r"^Item at index (\d+) is not readable$",
            r"El elemento en el índice \1 no se puede leer.",
        ),
        (
            r"^Item at index (\d+) must be seekable \(seek/tell required\)$",
            r"El elemento en el índice \1 debe permitir seek y tell.",
        ),
    ]
    for pattern, replacement in pattern_translations:
        translated = re.sub(pattern, replacement, message)
        if translated != message:
            return translated
    return message


def _field_from_loc(loc: Any) -> str | None:
    if not isinstance(loc, (list, tuple)):
        return None

    parts = list(loc)
    if parts and parts[0] in {"body", "query", "path", "header", "cookie"}:
        parts = parts[1:]

    if not parts:
        return None
    return ".".join(str(part) for part in parts)


def _request_summary(request: Request) -> str:
    client = getattr(request.client, "host", None) or "-"
    return f"{request.method} {request.url.path} client={client}"


def _log_error_response(
    *,
    request: Request,
    status_code: int,
    payload: dict[str, Any],
    raw_detail: Any,
) -> None:
    log_message = (
        "request=%s status=%s message=%s errors=%s raw_detail=%s"
        % (
            _request_summary(request),
            status_code,
            payload.get("message"),
            payload.get("errors", []),
            raw_detail,
        )
    )

    if status_code >= 500:
        logger.error(log_message)
    else:
        logger.warning(log_message)


def _translate_validation_message(item: dict[str, Any]) -> str:
    error_type = str(item.get("type") or "")
    ctx = item.get("ctx") or {}

    if error_type == "missing":
        return "Este campo es obligatorio."
    if error_type == "extra_forbidden":
        return "Este campo no está permitido."
    if error_type == "greater_than":
        return f"El valor debe ser mayor que {ctx.get('gt')}."
    if error_type == "greater_than_equal":
        return f"El valor debe ser mayor o igual que {ctx.get('ge')}."
    if error_type == "less_than":
        return f"El valor debe ser menor que {ctx.get('lt')}."
    if error_type == "less_than_equal":
        return f"El valor debe ser menor o igual que {ctx.get('le')}."
    if error_type in {"string_too_short", "too_short"}:
        return (
            f"Debe tener al menos {ctx.get('min_length') or ctx.get('min_items')} "
            "caracteres."
        )
    if error_type in {"string_too_long", "too_long"}:
        return (
            f"Debe tener como máximo {ctx.get('max_length') or ctx.get('max_items')} "
            "caracteres."
        )
    if error_type in {"int_parsing", "int_type"}:
        return "Debe ser un número entero válido."
    if error_type in {
        "float_parsing",
        "float_type",
        "decimal_parsing",
        "decimal_type",
    }:
        return "Debe ser un número válido."
    if error_type in {"bool_parsing", "bool_type"}:
        return "Debe ser un valor booleano válido."
    if error_type in {"date_parsing", "date_type"}:
        return "Debe ser una fecha válida."
    if error_type in {"datetime_parsing", "datetime_type"}:
        return "Debe ser una fecha y hora válida."
    if error_type in {"enum", "literal_error"}:
        return "El valor no es válido."
    if error_type == "value_error" and ctx.get("error") is not None:
        return _translate_known_message(str(ctx["error"]))

    raw_message = str(item.get("msg") or "")
    if raw_message.startswith("Value error, "):
        raw_message = raw_message.removeprefix("Value error, ")
    return _translate_known_message(raw_message)


def _normalize_error_item(item: Any) -> ErrorDetailResponse:
    if isinstance(item, ErrorDetailResponse):
        return item

    if isinstance(item, dict):
        if "msg" in item:
            return ErrorDetailResponse(
                field=_field_from_loc(item.get("loc")),
                message=_translate_validation_message(item),
                code=item.get("type"),
            )
        return ErrorDetailResponse(
            field=item.get("field"),
            message=_translate_known_message(
                str(
                    item.get("message")
                    or item.get("error")
                    or item.get("detail")
                    or item
                )
            ),
            code=item.get("code"),
        )

    return ErrorDetailResponse(message=_translate_known_message(str(item)))


def _normalize_errors(raw_errors: Any) -> list[dict[str, Any]]:
    if raw_errors is None:
        return []

    if not isinstance(raw_errors, list):
        raw_errors = [raw_errors]

    return [
        _normalize_error_item(item).model_dump(exclude_none=True)
        for item in raw_errors
    ]


def build_error_payload(
    *,
    status_code: int,
    detail: Any,
    default_message: str | None = None,
) -> dict[str, Any]:
    message = default_message or _default_message(status_code)
    errors: list[dict[str, Any]] = []

    if status_code >= 500:
        return ErrorResponse(message=_default_message(status_code), errors=[]).model_dump(
            exclude_none=True
        )

    if isinstance(detail, dict):
        message = _translate_known_message(
            str(
                detail.get("message")
                or detail.get("error")
                or detail.get("detail")
                or message
            )
        )
        errors = _normalize_errors(detail.get("errors"))
    elif isinstance(detail, list):
        errors = _normalize_errors(detail)
        if not default_message:
            message = "Error de validación" if errors else message
    elif detail is not None:
        message = _translate_known_message(str(detail))

    return ErrorResponse(
        message=_translate_known_message(message), errors=errors
    ).model_dump(exclude_none=True)


async def http_exception_handler(
    request: Request, exc: HTTPException | StarletteHTTPException
) -> JSONResponse:
    payload = build_error_payload(status_code=exc.status_code, detail=exc.detail)
    _log_error_response(
        request=request,
        status_code=exc.status_code,
        payload=payload,
        raw_detail=exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    payload = build_error_payload(
        status_code=422,
        detail=exc.errors(),
        default_message="Error de validación",
    )
    _log_error_response(
        request=request,
        status_code=422,
        payload=payload,
        raw_detail=exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content=payload,
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(
        "request=%s status=500 message=%s",
        _request_summary(request),
        "Error interno del servidor",
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(message="Error interno del servidor", errors=[]).model_dump(),
    )
