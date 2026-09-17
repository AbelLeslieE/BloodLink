"""Prevent spreadsheet software from interpreting user data as formulas."""


def safe_spreadsheet_cell(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


def protect_workbook(workbook):
    for sheet in workbook:
        for row in sheet:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.value = safe_spreadsheet_cell(cell.value)
                    cell.data_type = "s"
