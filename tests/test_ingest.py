import io

from openpyxl import Workbook

from app.services.ingest import detect_columns, read_table

CSV_BYTES = (
    "﻿大类,亚类,行政区,公园名称,面积_公顷\n"
    "生态公园,自然公园,从化区,广东流溪河国家森林自然公园,8861.22\n"
).encode("utf-8")


def _xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["大类", "亚类", "行政区", "公园名称", "面积_公顷"])
    sheet.append(["生态公园", "自然公园", "从化区", "广东流溪河国家森林自然公园", 8861.22])
    sheet.append(["生态公园", "自然公园", "从化区", "广东石门国家森林自然公园", 2627.56])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_read_csv_strips_bom_and_detects_name_header():
    table = read_table("sample.csv", CSV_BYTES)
    assert table.columns[0] == "大类"
    assert table.rows[0][3].startswith("广东流溪河")
    detection = detect_columns(table)
    assert detection.name_column == "公园名称"
    assert detection.adname_column == "行政区"
    assert detection.confidence == "header"


def test_read_xlsx_and_detect():
    table = read_table("sample.xlsx", _xlsx_bytes())
    assert len(table.rows) == 2
    detection = detect_columns(table)
    assert detection.name_column == "公园名称"
    assert detection.adname_column == "行政区"


def test_heuristic_when_header_is_unhelpful():
    payload = (
        "a,b,c,d\n"
        "1,2,流花湖公园,越秀区\n"
        "3,4,天河公园,天河区\n"
    ).encode("utf-8")
    detection = detect_columns(read_table("x.csv", payload))
    assert detection.confidence == "heuristic"
    assert detection.name_column == "c"
