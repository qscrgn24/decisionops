import csv
import io
import math


class OptimizationLimitError(ValueError):
    pass



def validate_optimization_dataset(
        file_bytes: bytes,
        *,
        max_rows: int,
) -> None:
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise OptimizationLimitError("Dataset must contain CSV bytes.")

    if not file_bytes:
        raise OptimizationLimitError("Dataset is empty.")

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OptimizationLimitError("Dataset must use UTF-8 encoding.") from exc

    stream = io.StringIO(text, newline="")

    try:
        reader = csv.reader(stream, strict=True)
        next(reader)
    except StopIteration as exc:
        raise OptimizationLimitError("Dataset is missing a header row.") from exc
    except csv.Error as exc:
        raise OptimizationLimitError("Dataset CSV could not be parsed.") from exc

    row_count = 0

    try:
        for _row in reader:
            row_count += 1

            if row_count > max_rows:
                raise OptimizationLimitError(f"Dataset exceeds the maximum of {max_rows} rows allowed for optimization.")
    except csv.Error as exc:
        raise OptimizationLimitError("Dataset CSV could not be parsed.") from exc


def require_finite_bounded_number(
        value: float,
        *,
        field_name: str,
        max_abs_value: float,
) -> float:
    number = float(value)

    if not math.isfinite(number):
        raise OptimizationLimitError(f"{field_name} must be a finite number.")

    if abs(number) > max_abs_value:
        raise OptimizationLimitError(f"{field_name} exceeds the supported numeric range.")

    return number
