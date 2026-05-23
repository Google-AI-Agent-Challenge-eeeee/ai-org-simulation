from backend.agents.requirements_agent.modules.employee_feature_preprocessing import (
    build_employee_feature_preprocessing_outputs,
)


def test_employee_feature_preprocessing_builds_safe_feature_matrix() -> None:
    result = build_employee_feature_preprocessing_outputs("datasets/raw")

    matrix = result["employee_feature_matrix"]
    metadata = result["employee_feature_metadata"]
    profiles = matrix["feature_profiles"]

    assert matrix["_meta"]["employee_count"] == 100
    assert matrix["_meta"]["feature_key_count"] > 0
    assert metadata["_meta"]["feature_key_count"] == matrix["_meta"]["feature_key_count"]
    assert len(profiles) == 100

    first = profiles[0]
    assert first["employee_id"]
    assert first["feature_values"]
    assert first["role_eligibility"]
    assert first["derived_features"]

    for profile in profiles:
        for feature_key, feature in profile["feature_values"].items():
            lowered = feature_key.casefold()
            assert "email" not in lowered
            assert "github_id" not in lowered
            assert "slack_user_id" not in lowered
            assert 0 <= feature["normalized_value"] <= 1
