import uuid
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests
import base64

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

    def generate_inventory_pdf(self, items):
        """Genera un PDF del inventario con los productos"""
        if not items:
            return self._render_pdf('<div class="empty">No hay stock disponible.</div>')

        pages_html = ""
        items_per_page = 12
        chunks = [items[i:i + items_per_page] for i in range(0, len(items), items_per_page)]

        # Logo en Base64
        logo_base64 = self._image_to_base64(self.logo_path)

        for chunk_index, chunk in enumerate(chunks):
            cards_html = ""
            for i, item in enumerate(chunk):
                print("-------")
                print(item.product.brand)
                real_index = (chunk_index * items_per_page) + i + 1
                img_src = self._image_to_base64(getattr(item.product, "image", None))
                nombre = getattr(item.product, "name", "Producto")
                code = getattr(item.product, "code", "Producto")
                stock = getattr(item, "stock", 0)
                avg_cost = getattr(item, "avg_cost", 0)
                last_cost = getattr(item, "last_cost", 0)
                box_size = getattr(item, "box_size", 0)
                
                cards_html += f"""
                <div class="product-card">
                    <div class="product-badge">Producto {real_index:02d}</div>
                    <div class="image-container">
                        <img src="{img_src}"/>
                    </div>
                    <div class="info-table">
                        <div class="info-row">
                            <span class="label">Nombre</span>
                            <span class="value">{nombre[:18]}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">Código</span>
                            <span class="value">{code}</span>
                        </div>

                        <div class="info-row">
                            <div class="info-column">
                                <span class="label">Stock</span>
                                <span class="value">{stock} Cajas</span>
                            </div>
                            <div class="info-column">
                                <span class="label">Pz</span>
                                <span class="value">{box_size}</span>
                            </div>
                        </div>
                        <div class="info-row">
                            <div class="info-column">
                                <span class="label">AVG Cost</span>
                                <span class="value">${avg_cost}</span>
                            </div>
                            <div class="info-column">
                                <span class="label">Last Cost</span>
                                <span class="value">${last_cost}</span>
                            </div>
                        </div>

                    </div>
                </div>
                """
            
            pages_html += f"""
            <div class="page">
                <div class="header">
                    <div class="header-left">
                        <img src="{logo_base64}" alt="Logo" class="logo">
                       <!-- <span class="company-name">JAFEPA</span>-->
                    </div>
                    <div class="header-right">
                        <div class="contact-info">
                            <div>📍 Calle Falsa 123, Ciudad</div>
                            <div>📞 +52 55 1234 5678</div>
                            <div>✉️ contacto@miempresa.com</div>
                            <div>🌐 www.miempresa.com</div>
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

    def generate_sale_invoice_pdf(self, sale):
        """Genera un PDF de la factura de venta"""
        logo_base64 = self._image_to_base64(self.logo_path)
        
        lines_html = ""
        for line in sale.lines:
            if not line.is_active:
                continue
            
            product_name = "Producto"
            product_code = "N/A"
            if line.inventory and line.inventory.product:
                product_name = line.inventory.product.name
                product_code = line.inventory.product.code
            
            lines_html += f"""
            <tr class="item-row">
                <td class="col-code">{product_code}</td>
                <td class="col-desc">{product_name}</td>
                <td class="col-qty">{line.quantity_units}</td>
                <td class="col-price">${line.price:,.2f}</td>
                <td class="col-total">${line.total_price:,.2f}</td>
            </tr>
            """

        client_name = sale.client.name if sale.client else "Público en General"
        client_email = sale.client.email if sale.client else ""
        client_phone = sale.client.phone if sale.client else ""

        invoice_html = f"""
        <div class="page">
            <div class="invoice-header">
                <div class="header-main">
                    <img src="{logo_base64}" class="invoice-logo">
                    <div class="invoice-title">FACTURA DE VENTA</div>
                </div>
                <div class="header-info">
                    <div class="info-block">
                        <strong>EMISOR</strong><br>
                        JAFEPA S.A. de C.V.<br>
                        Calle Falsa 123, Ciudad<br>
                        RFC: JAF123456789<br>
                        Tel: +52 55 1234 5678
                    </div>
                    <div class="info-block text-right">
                        <strong>DETALLE</strong><br>
                        Folio: #SAL-{sale.id:06d}<br>
                        Fecha: {sale.sale_date}<br>
                        Estado: {sale.status.value}<br>
                    </div>
                </div>
            </div>

            <div class="invoice-client">
                <strong>CLIENTE</strong><br>
                Nombre: {client_name}<br>
                Email: {client_email}<br>
                Tel: {client_phone}
            </div>

            <table class="invoice-table">
                <thead>
                    <tr>
                        <th class="col-code">CÓDIGO</th>
                        <th class="col-desc">DESCRIPCIÓN</th>
                        <th class="col-qty">CANT.</th>
                        <th class="col-price">PRECIO UNIT.</th>
                        <th class="col-total">TOTAL</th>
                    </tr>
                </thead>
                <tbody>
                    {lines_html}
                </tbody>
            </table>

            <div class="invoice-summary">
                <div class="summary-row total">
                    <span>TOTAL:</span>
                    <span>${sale.total_price:,.2f}</span>
                </div>
            </div>

            <div class="invoice-footer">
                <p>Gracias por su preferencia.</p>
                <div class="footer-strip"></div>
            </div>
        </div>
        """

        # Estilos específicos para la factura
        invoice_styles = """
<style>
    .invoice-header { padding: 10mm; background: #fff; }
    .header-main { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #1A1A1A; padding-bottom: 5mm; margin-bottom: 5mm; }
    .invoice-logo { height: 20mm; }
    .invoice-title { font-family: 'Oswald', sans-serif; font-size: 28px; color: #1A1A1A; }
    
    .header-info { display: flex; justify-content: space-between; font-family: 'Roboto', sans-serif; font-size: 12px; line-height: 1.5; }
    .text-right { text-align: right; }
    
    .invoice-client { margin: 5mm 10mm; padding: 5mm; background: #F5F5F5; border-radius: 4px; font-family: 'Roboto', sans-serif; font-size: 12px; }
    
    .invoice-table { width: calc(100% - 20mm); margin: 5mm 10mm; border-collapse: collapse; font-family: 'Roboto', sans-serif; }
    .invoice-table th { background: #1A1A1A; color: #fff; padding: 3mm; font-size: 11px; text-align: left; }
    .invoice-table td { padding: 3mm; border-bottom: 1px solid #EEE; font-size: 11px; }
    
    .col-code { width: 15%; }
    .col-desc { width: 45%; }
    .col-qty { width: 10%; text-align: center; }
    .col-price { width: 15%; text-align: right; }
    .col-total { width: 15%; text-align: right; }
    
    .invoice-summary { margin: 5mm 10mm; display: flex; justify-content: flex-end; }
    .summary-row { width: 40%; display: flex; justify-content: space-between; padding: 2mm 0; font-family: 'Roboto', sans-serif; }
    .summary-row.total { border-top: 2px solid #1A1A1A; font-weight: bold; font-size: 16px; margin-top: 2mm; }
    
    .invoice-footer { position: absolute; bottom: 0; width: 100%; text-align: center; font-family: 'Roboto', sans-serif; font-size: 10px; color: #777; padding-bottom: 5mm; }
</style>
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
                .company-name {{
                    font-size: 24px;
                    font-weight: 700;
                    letter-spacing: 2px;
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
                    padding: 5mm;
                    font-size: 0;
                }}

                .product-card {{
                    display: inline-block;
                    vertical-align: top;
                    width: calc(33.33% - 4mm);
                    height: 60mm;
                    margin: 2mm;
                    border: 1px solid #E0E0E0;
                    border-radius: 10px;
                    padding: 6mm 3mm 3mm 3mm;
                    position: relative;
                    background: #FAFAFA;
                    font-size: 12px;
                }}

                .product-badge {{
                    background-color: #1A1A1A;
                    color: #FAFAFA;
                    padding: 2px 15px;
                    border-radius: 12px;
                    font-size: 10px;
                    position: absolute;
                    top: -10px; left: 50%;
                    transform: translateX(-50%);
                    font-weight: bold;
                }}

                .image-container {{
                    width: 100%; height: 28mm;
                    display: flex; align-items: center; justify-content: center;
                    margin-bottom: 2mm;
                }}
                .image-container img {{ max-height: 100%; max-width: 100%; object-fit: contain; }}

                .info-table {{ width: 100%; font-size: 11px; }}
                .info-row {{
                    display: flex; justify-content: space-between; align-items: center;
                    padding: 4px 0; border-bottom: 0.5px solid #eee;
                }}
                .label {{ color: #777; }}
                .value {{ font-weight: 700; color: #333; }}

                .footer-strip {{
                    background-color: #1A1A1A;
                    height: 1mm;
                    width: 100%;
                    position: absolute;
                    bottom: 0;
                }}
            </style>
        </head>
        <body>
            {pages_html}
        </body>
        </html>
        """

        filename = os.path.join(os.getcwd(), f"catalogo_final_{uuid.uuid4()}.pdf")
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
            page.pdf(
                path=filename,
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
            )
            browser.close()
        return filename
