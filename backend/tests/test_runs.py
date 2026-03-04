import io


def _sample_csv_bytes():
    csv = """item_id,name,cost,value,risk,category
1,Item A,10,50,0.1,Cat1
2,Item B,20,70,0.2,Cat1
3,Item C,15,40,0.3,Cat2
"""
    return csv.encode("utf-8")


def test_execute_all_flow(client, signup_and_login):
    signup_and_login()

    # upload dataset
    f = io.BytesIO(_sample_csv_bytes())
    r = client.post(
        "/api/datasets/upload",
        data={"name": "test-ds"},
        files={"file": ("test.csv", f, "text/csv")},
    )
    assert r.status_code == 200, r.text
    dataset_id = r.json()["id"]

    # execute all (greedy + optimal)
    payload = {
        "dataset_id": dataset_id,
        "budget": 30,
        "max_items": None,
        "lambda_risk": 0.5,
        "objective": "risk_adjusted_value",
        "time_limit_s": 2.0,
    }
    r = client.post("/api/runs/execute-all", json=payload)
    assert r.status_code == 200, r.text

    run = r.json()
    assert run["dataset_id"] == dataset_id
    assert run["status"] in ("completed", "success", "done", "finished", "COMPLETED", "SUCCESS") or run["result_json"] is not None
    assert run["error"] is None
    assert run["result_json"] is not None