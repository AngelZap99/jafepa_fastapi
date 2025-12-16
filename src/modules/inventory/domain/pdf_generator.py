import uuid
from datetime import datetime
from playwright.sync_api import sync_playwright


class PDFGenerator:

    def __init__(self):
        pass

    # ===========================================================
    #   PDF de Productos
    # ===========================================================
    def generate_products_pdf(self, products):

        cards_html = ""

        for p in products:
            cards_html += f"""
            <div class="card">
                <img
                    src="https://cdn.dribbble.com/userupload/37102398/file/original-791362681d9b12363a8091a297e1c5a1.png"
                    class="logo"
                />

                <div class="content">
                    <div class="title">{p.name}</div>
                    <div class="subtitle">Empresa · Ubicación</div>

                    <div class="tags">
                        <div class="tag">$90,000 - $120,000 / yr</div>
                        <div class="tag">Full-time</div>
                        <div class="tag">Mid-level</div>
                    </div>
                </div>

                <div class="action">
                    <button class="btn">Apply</button>
                </div>
            </div>
            """

        return self._render_pdf(cards_html, title="Listado de Productos")

    # ===========================================================
    #   PDF de Inventario
    # ===========================================================
    def generate_inventory_pdf(self, items):

        if not items:
            cards_html = """
            <div class="empty">
                No hay elementos de inventario para mostrar.
            </div>
            """
        else:
            cards_html = ""

            for item in items:
                cards_html += f"""
                <div class="card">
                    <img
                        src="https://cdn-icons-png.flaticon.com/512/679/679922.png"
                        class="logo"
                    />

                    <div class="content">
                        <div class="title">
                            {item.product.name if item.product else 'Producto sin nombre'}
                        </div>

                        <div class="subtitle">
                            Almacén: {item.warehouse.name if item.warehouse else '-'}
                        </div>

                        <div class="tags">
                            <div class="tag">Stock: {item.stock}</div>
                            <div class="tag">Caja: {item.box_size}</div>
                            <div class="tag">Costo prom.: {item.avg_cost}</div>
                            <div class="tag">Último costo: {item.last_cost}</div>
                        </div>
                    </div>
                </div>
                """

        return self._render_pdf(cards_html, title="Reporte de Inventario")

    # ===========================================================
    #   RENDER HTML → PDF (CON ENCABEZADO)
    # ===========================================================
    def _render_pdf(self, cards_html, title):

        today = datetime.now().strftime("%d/%m/%Y")

        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f5f6fa;
                    padding: 0;
                    margin: 0;
                }}

                /* ========= HEADER ========= */
                .header {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 80px;
                    background: white;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 0 40px;
                    border-bottom: 1px solid #e6e6e6;
                }}

                .header img {{
                    height: 45px;
                }}

                .header-title {{
                    font-size: 18px;
                    font-weight: bold;
                }}

                .header-date {{
                    font-size: 12px;
                    color: #666;
                }}

                /* ========= CONTENT ========= */
                .content-wrapper {{
                    padding: 120px 40px 40px;
                }}

                .list {{
                    display: flex;
                    flex-direction: column;
                    gap: 18px;
                }}

                .card {{
                    background: #ffffff;
                    border-radius: 14px;
                    padding: 18px 22px;
                    display: flex;
                    align-items: center;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                    page-break-inside: avoid;
                }}

                .logo {{
                    width: 52px;
                    height: 52px;
                    border-radius: 12px;
                    object-fit: cover;
                    margin-right: 20px;
                }}

                .content {{
                    flex: 1;
                }}

                .title {{
                    font-size: 17px;
                    font-weight: bold;
                    margin-bottom: 4px;
                }}

                .subtitle {{
                    font-size: 13px;
                    color: #666;
                    margin-bottom: 8px;
                }}

                .tags {{
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                }}

                .tag {{
                    background: #f1f3f6;
                    padding: 4px 10px;
                    border-radius: 20px;
                    font-size: 11px;
                    color: #333;
                }}

                .action {{
                    margin-left: 20px;
                }}

                .btn {{
                    background: #ff7a18;
                    color: white;
                    border: none;
                    padding: 8px 18px;
                    border-radius: 20px;
                    font-size: 13px;
                    font-weight: bold;
                }}

                .empty {{
                    font-size: 24px;
                    text-align: center;
                    margin-top: 200px;
                    color: #555;
                    font-weight: bold;
                }}
            </style>
        </head>

        <body>

            <!-- HEADER -->
            <div class="header">
                <img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg" />
                <div class="header-title">{title}</div>
                <div class="header-date">{today}</div>
            </div>

            <!-- CONTENT -->
            <div class="content-wrapper">
                <div class="list">
                    {cards_html}
                </div>
            </div>

        </body>
        </html>
        """

        filename = f"/tmp/{uuid.uuid4()}.pdf"

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html)
            page.pdf(
                path=filename,
                format="A4",
                margin={
                    "top": "100px",
                    "bottom": "30px",
                    "left": "20px",
                    "right": "20px"
                }
            )
            browser.close()

        return filename
