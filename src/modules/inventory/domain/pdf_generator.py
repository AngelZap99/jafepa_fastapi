import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from playwright.sync_api import Error as PlaywrightError, sync_playwright
import requests
import base64
from html import escape

from src.shared.enums.sale_enums import SaleLinePriceType


SALE_TAX_PERCENT = Decimal("16")
SALE_TAX_RATE = SALE_TAX_PERCENT / Decimal("100")
MONEY_QUANTIZER = Decimal("0.01")


def _display_value(value, fallback="No disponible"):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _money(value):
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)

class PDFGenerator:

    def __init__(self):
        """
        Inicializa el generador de PDFs.
        Logo se toma desde src/assets/fullLogo.svg
        """
        # Ruta absoluta al logo según tu estructura
        self.logo_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../assets/fullLogo.svg")
        )
        # Verifica que el logo exista
        if not os.path.exists(self.logo_path):
            raise FileNotFoundError(f"No se encontró el logo en: {self.logo_path}")

    def _image_to_base64(self, path_or_url):
        """
        Convierte una imagen local o remota a Base64.
        path_or_url: URL o ruta local
        """
        placeholder_icon = "https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg"

        if not path_or_url:
            return placeholder_icon

        # Si es URL
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            try:
                resp = requests.get(path_or_url, timeout=5)
                resp.raise_for_status()
                ext = path_or_url.split(".")[-1].split("?")[0]
                encoded = base64.b64encode(resp.content).decode("utf-8")
                return f"data:image/{ext};base64,{encoded}"
            except:
                return placeholder_icon
        else:
            # Ruta local
            if not os.path.exists(path_or_url):
                return placeholder_icon
            ext = path_or_url.split(".")[-1].lower()
            with open(path_or_url, "rb") as f:
                content = f.read()
                if ext == "svg":
                    # Escapar SVG a Base64
                    encoded = base64.b64encode(content).decode("utf-8")
                    return f"data:image/svg+xml;base64,{encoded}"
                else:
                    encoded = base64.b64encode(content).decode("utf-8")
                    return f"data:image/{ext};base64,{encoded}"

    def generate_inventory_pdf(self, items, warehouse=None):
        """Genera un PDF del inventario con los productos"""
        if not items:
            return self._render_pdf('<div class="empty">No hay stock disponible.</div>')

        pages_html = ""
        items_per_page = 9
        chunks = [items[i:i + items_per_page] for i in range(0, len(items), items_per_page)]

        # Logo en Base64
        logo_base64 = self._image_to_base64(self.logo_path)
        warehouse_name = escape(
            _display_value(getattr(warehouse, "name", None), "Reporte de inventario")
        )
        warehouse_address = escape(_display_value(getattr(warehouse, "address", None)))
        warehouse_phone = escape(_display_value(getattr(warehouse, "phone", None)))
        warehouse_email = escape(_display_value(getattr(warehouse, "email", None)))

        for chunk_index, chunk in enumerate(chunks):
            cards_html = ""
            for i, item in enumerate(chunk):
                img_src = self._image_to_base64(getattr(item.product, "image", None))
                nombre = escape(_display_value(getattr(item.product, "name", None), "Producto"))
                code = escape(_display_value(getattr(item.product, "code", None), "Producto"))
                description = escape(
                    _display_value(getattr(item.product, "description", None), "Sin descripcion")
                )
                box_size = escape(
                    _display_value(getattr(item, "box_size", None), "0")
                )
                
                cards_html += f"""
                <div class="product-card">
                    <div class="product-name">{nombre}</div>
                    <div class="image-container">
                        <img src="{img_src}" alt="{nombre}"/>
                    </div>
                    <div class="info-table">
                        <div class="info-row">
                            <span class="label">Código</span>
                            <span class="value">{code}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">Piezas por caja</span>
                            <span class="value">{box_size}</span>
                        </div>
                        <div class="info-row info-row-description">
                            <span class="label">Descripción</span>
                            <span class="value product-description">{description}</span>
                        </div>
                    </div>
                </div>
                """
            
            pages_html += f"""
            <div class="page">
                <div class="header">
                    <div class="header-left">
                        <img src="{logo_base64}" alt="Logo" class="logo">
                    </div>
                    <div class="header-right">
                        <div class="contact-info">
                            <div><strong>{warehouse_name}</strong></div>
                            <div>Direccion: {warehouse_address}</div>
                            <div>Telefono: {warehouse_phone}</div>
                            <div>Email: {warehouse_email}</div>
                        </div>
                    </div>
                </div>
                <div class="catalog-container">
                    {cards_html}
                </div>
                <div class="footer-strip"></div>
            </div>
            """

        return self._render_pdf(pages_html)

    def generate_sale_invoice_pdf(self, sale, delivered_by_name=None):
        """Genera un PDF de la nota de venta"""
        logo_base64 = self._image_to_base64(self.logo_path)

        lines_html = ""
        subtotal_amount = Decimal("0.00")
        for line in sale.lines:
            if not line.is_active:
                continue

            product_name = getattr(line, "product_name", None) or "Producto"
            product_code = getattr(line, "product_code", None) or "N/A"
            quantity_boxes = int(getattr(line, "quantity_boxes", line.quantity_units))
            box_size = int(getattr(line, "box_size", None) or 1)
            quantity_units = quantity_boxes * box_size
            price_type = getattr(line, "price_type", SaleLinePriceType.BOX)
            price_type_value = getattr(price_type, "value", price_type)
            is_unit_price = str(price_type_value).upper() == "UNIT" or box_size == 1
            pieces_label = "Unitario" if box_size == 1 else f"{box_size} Piezas/Caja"
            price_value = (
                getattr(line, "unit_price", None)
                if is_unit_price
                else getattr(line, "box_price", None)
            ) or line.price
            line_total = _money(getattr(line, "total_price", None))
            subtotal_amount += line_total

            lines_html += f"""
            <tr class="item-row">
                <td class="col-code">{product_code}</td>
                <td class="col-desc">{product_name}</td>
                <td class="col-qty">{quantity_boxes}</td>
                <td class="col-box">{pieces_label}</td>
                <td class="col-units">{quantity_units}</td>
                <td class="col-price"><div class="cell-value">${price_value:,.2f}</div></td>
                <td class="col-total">${line_total:,.2f}</td>
            </tr>
            """

        client_name = sale.client.name if sale.client else "Público en General"
        attended_by = delivered_by_name or "Pendiente"
        tax_amount = _money(subtotal_amount * SALE_TAX_RATE)
        total_amount = _money(subtotal_amount + tax_amount)

        invoice_html = f"""
        <div class="page">
            <div class="invoice-header">
                <div class="header-main">
                    <div class="header-text">
                        <div class="invoice-title">Nota de venta #{sale.id}</div>
                        <div class="invoice-meta">Fecha: {sale.sale_date}</div>
                        <div class="invoice-meta">Cliente: {client_name}</div>
                        <div class="invoice-meta">Atendido por: {attended_by}</div>
                    </div>
                    <img src="{logo_base64}" class="invoice-logo">
                </div>
            </div>

            <table class="invoice-table">
                <thead>
                    <tr>
                        <th class="col-code">Código</th>
                        <th class="col-desc">Nombre del producto</th>
                        <th class="col-qty">Cajas</th>
                        <th class="col-box">Piezas/Caja</th>
                        <th class="col-units">Piezas totales</th>
                        <th class="col-price">Precio producto</th>
                        <th class="col-total">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {lines_html}
                </tbody>
            </table>

            <div class="invoice-bottom">
                <div class="invoice-note">
                    <div>NO SE ACEPTAN DEVOLUCIONES.</div>
                    <div>LA MERCANCÍA VIAJA POR CUENTA Y RIESGO DEL CLIENTE.</div>
                    <div>POR SU ATENCIÓN GRACIAS.</div>
                </div>
                <div class="invoice-summary">
                    <div class="summary-row">
                        <span>Subtotal:</span>
                        <span>${subtotal_amount:,.2f}</span>
                    </div>
                    <div class="summary-row">
                        <span>Impuesto ({SALE_TAX_PERCENT:.0f}%):</span>
                        <span>${tax_amount:,.2f}</span>
                    </div>
                    <div class="summary-row total">
                        <span>Total:</span>
                        <span>${total_amount:,.2f}</span>
                    </div>
                </div>
            </div>
        </div>
        """

        invoice_styles = """
    .invoice-header { padding: 8mm 10mm 4mm; background: #fff; }
    .header-main { display: flex; justify-content: space-between; align-items: flex-start; gap: 8mm; border-bottom: 2px solid #1A1A1A; padding-bottom: 3mm; margin-bottom: 3mm; }
    .header-text { flex: 1; min-width: 0; }
    .invoice-logo { height: 22mm; width: auto; object-fit: contain; }
    .invoice-title { font-family: 'Oswald', sans-serif; font-size: 24px; color: #1A1A1A; line-height: 1.1; margin-bottom: 1mm; }
    .invoice-meta { font-family: 'Roboto', sans-serif; font-size: 11px; line-height: 1.3; color: #1A1A1A; }
    
    .invoice-table { width: calc(100% - 20mm); margin: 3mm 10mm 4mm; border-collapse: collapse; font-family: 'Roboto', sans-serif; }
    .invoice-table th { background: #1A1A1A; color: #fff; padding: 2.5mm 2mm; font-size: 10px; text-align: center; }
    .invoice-table td { padding: 2.5mm 2mm; border-bottom: 1px solid #EEE; font-size: 10px; vertical-align: top; }
    
    .col-code { width: 12%; }
    .col-desc { width: 28%; }
    .col-qty { width: 8%; text-align: center; }
    .col-box { width: 16%; text-align: center; }
    .col-units { width: 12%; text-align: center; }
    .col-price { width: 12%; text-align: right; }
    .col-total { width: 12%; text-align: right; }
    .cell-value { font-size: 10px; font-weight: 700; line-height: 1.1; }
    
    .invoice-bottom { margin: 3mm 10mm 0; display: flex; justify-content: space-between; gap: 8mm; align-items: flex-end; }
    .invoice-note { flex: 1; font-family: 'Roboto', sans-serif; font-size: 9.5px; line-height: 1.15; text-transform: uppercase; color: #1A1A1A; }
    .invoice-summary { width: 38%; min-width: 65mm; margin-left: auto; display: flex; flex-direction: column; gap: 1mm; }
    .summary-row { width: 100%; display: flex; justify-content: space-between; padding: 1.5mm 0; font-family: 'Roboto', sans-serif; font-size: 14px; font-weight: 700; }
    .summary-row.total { border-top: 2px solid #1A1A1A; margin-top: 1mm; }
"""

        return self._render_pdf(invoice_html, extra_styles=invoice_styles)

    def _render_pdf(self, pages_html, extra_styles=""):
        """Renderiza el HTML a PDF usando Playwright"""
        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
            <style>
                * {{ box-sizing: border-box; }}
                @page {{ size: A4; margin: 0; }}
                body {{ margin: 0; padding: 0; background-color: #FAFAFA; }}
                {extra_styles}
                
                .page {{
                    width: 210mm;
                    height: 297mm;
                    background: white;
                    position: relative;
                    overflow: hidden;
                    page-break-after: always;
                }}

                .header {{
                    background-color: #FAFAFA;
                    color: #333333;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 5mm 10mm;
                    height: 35mm;
                    font-family: 'Roboto', sans-serif;
                }}
                .header-left {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .logo {{
                    height: 28mm;
                    width: auto;
                    object-fit: contain;
                    border-radius: 4px;
                }}
                .header-right {{
                    text-align: right;
                    font-size: 10px;
                    line-height: 1.2;
                }}
                .contact-info div {{
                    margin-bottom: 2px;
                }}

                .catalog-container {{
                    width: 100%;
                    padding: 6mm 7mm 5mm;
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 5mm;
                }}

                .product-card {{
                    width: 100%;
                    height: 74mm;
                    border: 1px solid #E0E0E0;
                    border-radius: 10px;
                    padding: 4mm 4mm 5mm 4mm;
                    position: relative;
                    background: #FAFAFA;
                    font-size: 12px;
                }}

                .product-name {{
                    font-family: 'Oswald', sans-serif;
                    font-size: 12px;
                    font-weight: 500;
                    text-align: center;
                    color: #111111;
                    margin: -6.8mm auto 2.5mm auto;
                    display: block;
                    width: 85%;
                    padding: 0.8mm 4mm;
                    border: 1px solid #1A1A1A;
                    border-radius: 999px;
                    background: #FFFFFF;
                    min-height: 5mm;
                    line-height: 1.1;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    letter-spacing: 0.3px;
                }}

                .image-container {{
                    width: 100%;
                    height: 38mm;
                    display: flex; align-items: center; justify-content: center;
                    margin-bottom: 2.5mm;
                }}
                .image-container img {{
                    max-height: 100%;
                    max-width: 100%;
                    object-fit: contain;
                    border-radius: 8px;
                }}

                .info-table {{
                    width: 100%;
                    font-size: 11px;
                    font-family: 'Roboto', sans-serif;
                }}
                .info-row {{
                    display: flex; justify-content: space-between; align-items: center;
                    padding: 6px 0;
                }}
                .info-row-description {{
                    align-items: flex-start;
                }}
                .label {{
                    color: #777;
                    font-family: 'Roboto', sans-serif;
                }}
                .value {{
                    font-weight: 700;
                    color: #333;
                    text-align: right;
                    font-family: 'Roboto', sans-serif;
                }}
                .product-description {{
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    text-align: left;
                    max-height: 6.2em;
                    line-height: 1.25em;
                    white-space: normal;
                    margin-left: 2mm;
                }}

                .info-row + .info-row {{
                    border-top: 0.5px solid #eee;
                }}
                {extra_styles}
            </style>
        </head>
        <body>
            {pages_html}
        </body>
        </html>
        """

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ]
                )
                page = browser.new_page()
                page.set_content(html)
                page.wait_for_timeout(1000)
                pdf_bytes = page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
                )
                browser.close()
            return pdf_bytes
        except PlaywrightError as exc:
            raise RuntimeError(
                "Playwright browser executable is missing or unavailable. "
                "Run `playwright install chromium` in this environment."
            ) from exc
