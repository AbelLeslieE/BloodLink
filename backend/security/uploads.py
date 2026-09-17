"""Bound compressed workbook size and reject unexpected ZIP features."""
from io import BytesIO
from zipfile import ZipFile


def validate_workbook_archive(contents: bytes) -> None:
    with ZipFile(BytesIO(contents)) as archive:
        entries = archive.infolist()
        if len(entries) > 1000 or sum(e.file_size for e in entries) > 50 * 1024 * 1024:
            raise ValueError("Workbook expands beyond the safe import limit.")
        if any(e.flag_bits & 1 or e.file_size > 20 * 1024 * 1024 for e in entries):
            raise ValueError("Encrypted or oversized workbook entries are not supported.")
        if "[Content_Types].xml" not in archive.namelist():
            raise ValueError("Invalid Excel workbook.")
