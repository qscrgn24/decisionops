from app.services.csv_normalize import resolve_columns
from app.services.dataset_preview import preview_and_validate_csv


def test_resolve_columns_accepts_common_aliases() -> None:
    result = resolve_columns(
        ["Project Name", "Estimated Cost USD", "Expected Annual Value USD", "Risk Score"]
    )

    assert result.mapping["name"] == "Project Name"
    assert result.mapping["cost"] == "Estimated Cost USD"
    assert result.mapping["value"] == "Expected Annual Value USD"
    assert result.mapping["risk"] == "Risk Score"
    assert result.missing_required == []


def test_preview_normalizez_percentage_risk_to_fraction() -> None:
    csv_bytes = (
        b"Project Name,Estimated Cost USD,Expected Annual Value USD,Risk Score\n"
        b"Project Alpha,100,250,55\n"
    )

    result = preview_and_validate_csv(csv_bytes)

    assert result.risk_scale == "0-100"
    assert result.missing_required == []
    assert len(result.rows) == 1
    assert result.rows[0]["Risk Score"] == 0.55
    assert any("normalizing to [0,1]" in warning for warning in result.warnings)