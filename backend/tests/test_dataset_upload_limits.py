import io

from app.core.config import settings


def _upload_csv(
        client,
        *,
        csv_bytes: bytes,
        name: str = "test-dataset",
        filename: str = "test.csv",
):
    return client.post("/api/datasets/upload", data={"name": name}, files={"file": (filename, io.BytesIO(csv_bytes), "text/csv")})


def test_request_body_limit_rejects_oversized_request(client):
    body = b"x" * (settings.MAX_REQUEST_BYTES + 1)

    response = client.post("/api/does-not-exist", content=body)

    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"


def test_upload_rejects_file_over_byte_limits(
        client,
        signup_and_login,
):
    signup_and_login()

    header = b"name,cost,value\n"
    oversized_content = header + b"x" * (settings.MAX_UPLOAD_BYTES + 1 - len(header))

    response = _upload_csv(
        client,
        csv_bytes=oversized_content,
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Uploaded CSV file is too large."


def test_upload_rejects_too_many_rows(
        client,
        signup_and_login,
):
    signup_and_login()

    rows = ["name,cost,value"]

    for row_number in range(settings.MAX_DATASET_ROWS + 1):
        rows.append(f"item {row_number},10,20")

    response = _upload_csv(
        client,
        csv_bytes=("\n".join(rows) + "\n").encode("utf-8"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == f"CSV file exceeds the maximum of {settings.MAX_DATASET_ROWS} data rows."


def test_upload_rejects_too_many_columns(
        client,
        signup_and_login,
):
    signup_and_login()

    header = ",".join(f"column_{index}" for index in range(settings.MAX_DATASET_COLUMNS + 1))
    row = ",".join("1" for _ in range(settings.MAX_DATASET_COLUMNS + 1))

    response = _upload_csv(
        client,
        csv_bytes=f"{header}\n{row}\n".encode(),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == f"CSV file exceeds the maximum of {settings.MAX_DATASET_COLUMNS} columns."


def test_upload_rejects_oversized_cell(
    client,
    signup_and_login,
):
    signup_and_login()

    oversized_cell = "x" * (settings.MAX_CELL_CHARS + 1)

    csv_bytes = (
        "name,cost,value\n"
        f"{oversized_cell},10,20\n"
    ).encode()

    response = _upload_csv(
        client,
        csv_bytes=csv_bytes,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == (
            "CSV file contains a cell that exceeds the maximum "
            f"length of {settings.MAX_CELL_CHARS} characters."
        )
    )


def test_upload_rejects_mismatched_row_width(
    client,
    signup_and_login,
):
    signup_and_login()

    csv_bytes = (
        b"name,cost,value\n"
        b"Item A,10,20\n"
        b"Item B,30\n"
    )

    response = _upload_csv(
        client,
        csv_bytes=csv_bytes,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "CSV row 2 has a different number of columns than the header."
    )


def test_upload_rejects_long_dataset_name(
    client,
    signup_and_login,
):
    signup_and_login()

    response = _upload_csv(
        client,
        csv_bytes=b"name,cost,value\nItem A,10,20\n",
        name="x" * (settings.MAX_DATASET_NAME_CHARS + 1),
    )

    assert response.status_code == 400


def test_upload_rejects_long_filename(
    client,
    signup_and_login,
):
    signup_and_login()

    suffix = ".csv"
    filename = (
        "x" * (settings.MAX_FILENAME_CHARS - len(suffix) + 1)
        + suffix
    )

    response = _upload_csv(
        client,
        csv_bytes=b"name,cost,value\nItem A,10,20\n",
        filename=filename,
    )

    assert response.status_code == 400