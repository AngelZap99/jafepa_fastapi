from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _cell(reference: str, value, style: int = 0) -> str:
    style_attribute = f' s="{style}"' if style else ""
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return f'<c r="{reference}"{style_attribute}><v>{value}</v></c>'

    raw_text = "" if value is None else str(value)
    text = escape(
        "".join(
            character
            for character in raw_text
            if character in {"\t", "\n", "\r"} or ord(character) >= 32
        )
    )
    return (
        f'<c r="{reference}" t="inlineStr"{style_attribute}>'
        f"<is><t>{text}</t></is></c>"
    )


def build_inventory_history_xlsx(
    *,
    title: str,
    warehouse: str,
    presentation: str,
    filter_description: str,
    entries: int,
    exits: int,
    available: int,
    rows: list[dict],
) -> bytes:
    table_header_row = 9
    worksheet_rows = [
        (["Historial de inventario"], 1),
        (["Producto", title], 0),
        (["Almacén", warehouse], 0),
        (["Presentación", presentation], 0),
        (["Filtros", filter_description], 0),
        (["Entradas filtradas", entries], 0),
        (["Salidas filtradas", exits], 0),
        (["Disponible actual", available], 0),
        (
            [
                "Cantidad",
                "Operación",
                "Tipo",
                "Cliente",
                "Responsable",
                "Costo / Precio",
                "Total",
                "Fecha",
            ],
            2,
        ),
    ]

    for row in rows:
        worksheet_rows.append(
            (
                [
                    row["quantity"],
                    row["operation"],
                    row["movement_type"],
                    row["client_name"],
                    row["actor_name"],
                    row["unit_value"],
                    row["total_value"],
                    row["movement_date"],
                ],
                0,
            )
        )

    row_xml: list[str] = []
    for row_index, (values, row_style) in enumerate(worksheet_rows, start=1):
        cells = []
        for column_index, value in enumerate(values, start=1):
            cell_style = row_style
            if row_index > table_header_row and column_index in {6, 7}:
                cell_style = 3
            cells.append(
                _cell(
                    f"{_column_name(column_index)}{row_index}",
                    value,
                    cell_style,
                )
            )
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    last_row = max(table_header_row, len(worksheet_rows))
    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews>
    <sheetView workbookViewId="0">
      <pane ySplit="{table_header_row}" topLeftCell="A{table_header_row + 1}" activePane="bottomLeft" state="frozen"/>
    </sheetView>
  </sheetViews>
  <cols>
    <col min="1" max="1" width="16" customWidth="1"/>
    <col min="2" max="2" width="24" customWidth="1"/>
    <col min="3" max="3" width="13" customWidth="1"/>
    <col min="4" max="4" width="30" customWidth="1"/>
    <col min="5" max="5" width="24" customWidth="1"/>
    <col min="6" max="7" width="17" customWidth="1"/>
    <col min="8" max="8" width="22" customWidth="1"/>
  </cols>
  <sheetData>{"".join(row_xml)}</sheetData>
  <mergeCells count="1"><mergeCell ref="A1:H1"/></mergeCells>
  <autoFilter ref="A{table_header_row}:H{last_row}"/>
</worksheet>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""
    root_relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Historial" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    workbook_relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""
    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="1"><numFmt numFmtId="164" formatCode="$#,##0.00"/></numFmts>
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFDCE6F1"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="4">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0"/>
    <xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as workbook_zip:
        workbook_zip.writestr("[Content_Types].xml", content_types)
        workbook_zip.writestr("_rels/.rels", root_relationships)
        workbook_zip.writestr("xl/workbook.xml", workbook)
        workbook_zip.writestr("xl/_rels/workbook.xml.rels", workbook_relationships)
        workbook_zip.writestr("xl/styles.xml", styles)
        workbook_zip.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return output.getvalue()


def format_history_datetime(value: datetime) -> str:
    return value.strftime("%d/%m/%Y %H:%M")
