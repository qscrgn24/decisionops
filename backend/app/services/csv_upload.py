import csv
import io

from fastapi import UploadFile

_READ_CHUNK_BYTES = 64 * 1024


class UploadTooLargeError(ValueError):
    pass


class CSVValidationError(ValueError):
    pass


async def read_bounded_upload(
        file: UploadFile,
        *,
        max_bytes: int,
) -> bytes:
    content = bytearray()

    while True:
        chunk = await file.read(_READ_CHUNK_BYTES)

        if not chunk:
            break

        if len(content) + len(chunk) > max_bytes:
            raise UploadTooLargeError(
                f"Uploaded file exceeds maximum size of {max_bytes} bytes."
            )

        content.extend(chunk)

    return bytes(content)


def validate_csv_structure(
        file_bytes: bytes,
        *,
        max_rows: int,
        max_columns: int,
        max_cell_chars: int,
) -> None:
    if not file_bytes:
        raise CSVValidationError("Uploaded file is empty.")

    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CSVValidationError("Uploaded file is not valid UTF-8.") from exc

    stream = io.StringIO(text, newline="")

    try:
        reader = csv.reader(stream, strict=True)
        header = next(reader)
    except StopIteration as exc:
        raise CSVValidationError("CSV file is missing a header row.") from exc
    except csv.Error as exc:
        raise CSVValidationError("CSV file could not be parsed.") from exc

    if not header or all(cell.strip() == "" for cell in header):
        raise CSVValidationError("CSV file is missing a valid header row.")

    if len(header) > max_columns:
        raise CSVValidationError(
            f"CSV file exceeds the maximum of {max_columns} columns."
        )

    _validate_cells(
        header,
        max_cell_chars=max_cell_chars,
    )

    row_count = 0

    try:
        for row in reader:
            row_count += 1

            if row_count > max_rows:
                raise CSVValidationError(
                    f"CSV file exceeds the maximum of {max_rows} data rows."
                )

            if len(row) > max_columns:
                raise CSVValidationError(
                    f"Row {row_count + 1} exceeds the maximum of {max_columns} columns."
                )

            if len(row) != len(header):
                raise CSVValidationError(
                    f"CSV row {row_count} has a different number of "
                    "columns than the header."
                )

            _validate_cells(
                row,
                max_cell_chars=max_cell_chars,
            )

    except csv.Error as exc:
        raise CSVValidationError(
            "CSV file could not be parsed."
        ) from exc


def _validate_cells(
    cells: list[str],
    *,
    max_cell_chars: int,
) -> None:
    for cell in cells:
        if len(cell) > max_cell_chars:
            raise CSVValidationError(
                "CSV file contains a cell that exceeds the maximum "
                f"length of {max_cell_chars} characters."
            )
