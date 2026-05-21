from enum import StrEnum


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMMode(StrEnum):
    """How agents call LLMs. Use STUB during early phases, VERTEX in Phase 7+."""

    STUB = "stub"
    VERTEX = "vertex"


class Role(StrEnum):
    PM = "pm"
    BACKEND = "backend"
    FRONTEND = "frontend"
    QA = "qa"
    AI = "ai"


class Seniority(StrEnum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
