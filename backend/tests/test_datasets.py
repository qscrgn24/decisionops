import io

def _sample_csv_bytes():
    csv = """item_id,name,cost,value,risk,category
1,Item A,10,50,0.1,Cat1
2,Item B,20,70,0.2,Cat1
3,Item C,15,40,0.3,Cat2
"""
    return csv.encode("utf-8")


def test_dataset_upload_requires_auth(client):
    f = io.BytesIO(_sample_csv_bytes())
    r = client.post(
        "/api/datasets/upload",
        data={"name": "test-ds"},
        files={"file": ("test.csv", f, "text/csv")},
    )
    assert r.status_code in (401, 403), r.text


def test_dataset_upload_and_preview(client, signup_and_login):
    signup_and_login()

    f = io.BytesIO(_sample_csv_bytes())
    r = client.post(
        "/api/datasets/upload",
        data={"name": "test-ds"},
        files={"file": ("test.csv", f, "text/csv")},
    )
    assert r.status_code == 200, r.text
    dataset = r.json()
    dataset_id = dataset["id"]

    r = client.get(f"/api/datasets/{dataset_id}/preview?n=5")
    assert r.status_code == 200, r.text
    preview = r.json()
    assert "resolved_columns" in preview
    assert "rows" in preview
    assert len(preview["rows"]) > 0