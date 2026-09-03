import io


def _sample_csv_bytes() -> bytes:
    csv = """item_id,name,cost,value,risk,category
1,Item A,10,50,0.1,Cat1
2,Item B,20,70,0.2,Cat1
3,Item C,15,40,0.3,Cat2
"""
    return csv.encode("utf-8")


def _upload_sample_dataset(client) -> str:
    response = client.post(
        "/api/datasets/upload",
        data={"name": "test-ds"},
        files={
            "file": (
                "test.csv",
                io.BytesIO(_sample_csv_bytes()),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_execute_all_flow(client, signup_and_login):
    signup_and_login()
    dataset_id = _upload_sample_dataset(client)

    budget = 30
    max_items = 2

    response = client.post(
        "/api/runs/execute-all",
        json={
            "dataset_id": dataset_id,
            "budget": budget,
            "max_items": max_items,
            "lambda_risk": 0.5,
            "objective": "risk_adjusted_value",
            "time_limit_s": 2.0,
        },
    )

    assert response.status_code == 200, response.text

    run = response.json()

    assert run["dataset_id"] == dataset_id
    assert run["status"] == "succeeded"
    assert run["error"] is None
    assert run["result_json"] is not None

    for result_name in ("baseline", "optimal"):
        result = run["result_json"][result_name]
        summary = result["summary"]

        assert summary["selected_count"] <= max_items
        assert summary["total_cost"] <= budget
        assert len(result["selected_items"]) == summary["selected_count"]


def test_optimal_solver_returns_selected_variables_not_complement(
    client,
    signup_and_login,
):
    signup_and_login()
    dataset_id = _upload_sample_dataset(client)

    response = client.post(
        "/api/runs/execute-all",
        json={
            "dataset_id": dataset_id,
            "budget": 30,
            "max_items": 2,
            "lambda_risk": 0,
            "objective": "value",
            "time_limit_s": 2.0,
        },
    )

    assert response.status_code == 200, response.text

    run = response.json()

    assert run["status"] == "succeeded"

    optimal = run["result_json"]["optimal"]
    selected_items = optimal["selected_items"]
    selected_ids = {item["item_id"] for item in selected_items}

    assert selected_ids == {"1", "2"}
    assert optimal["summary"]["selected_count"] == 2
    assert optimal["summary"]["total_cost"] == 30
    assert optimal["summary"]["total_value"] == 120


def test_optimal_solver_respects_tight_budget_and_item_cap(
    client,
    signup_and_login,
):
    signup_and_login()
    dataset_id = _upload_sample_dataset(client)

    response = client.post(
        "/api/runs/execute-all",
        json={
            "dataset_id": dataset_id,
            "budget": 15,
            "max_items": 1,
            "lambda_risk": 0,
            "objective": "value",
            "time_limit_s": 2.0,
        },
    )

    assert response.status_code == 200, response.text

    run = response.json()

    assert run["status"] == "succeeded"

    optimal = run["result_json"]["optimal"]

    assert optimal["summary"]["selected_count"] == 1
    assert optimal["summary"]["total_cost"] <= 15
    assert optimal["selected_items"][0]["item_id"] == "1"
