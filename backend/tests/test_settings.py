from backend.core.config.settings import Settings


def test_cors_allow_origins_accepts_json_list() -> None:
    settings = Settings(CORS_ALLOW_ORIGINS='["http://localhost:3000", "http://localhost:8000"]')

    assert settings.cors_allow_origins == [
        "http://localhost:3000",
        "http://localhost:8000",
    ]


def test_cors_allow_origins_accepts_shell_stripped_wildcard() -> None:
    settings = Settings(CORS_ALLOW_ORIGINS="[*]")

    assert settings.cors_allow_origins == ["*"]


def test_cors_allow_origins_accepts_comma_separated_values() -> None:
    settings = Settings(CORS_ALLOW_ORIGINS="http://localhost:3000,http://localhost:8000")

    assert settings.cors_allow_origins == [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
