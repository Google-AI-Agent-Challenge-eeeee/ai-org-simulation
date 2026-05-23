from backend.agents.requirements_agent.modules.employee_team_ranking import (
    build_employee_team_rankings,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.agent_card_builder import (
    AgentCardBuilder,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.issue_risk_evaluator import (
    IssueRiskEvaluator,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.output_builder import (
    OutputBuilder,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.phase_log_collector import (
    PhaseLogCollector,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.privacy_column_filter import (
    PrivacyColumnFilter,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.scenario_phase_planner import (
    ScenarioPhasePlanner,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.score_calculator import (
    ScoreCalculator,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.simulation_input_builder import (
    EvidenceIndex,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.simulation_orchestrator import (
    SimulationOrchestrator,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.orchestrator import (
    LLMMode,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    SimulationInputPacket,
)


def _requirements_list():
    return {
        "_meta": {
            "requirements_list_id": "requirements_list_e2e",
            "project_id": "project_notification",
            "status": "completed",
        },
        "required_roles": [
            {"role": "Product Manager", "source_feature_keys": ["notification_center"]},
            {"role": "Backend Engineer", "source_feature_keys": ["notification_center"]},
            {"role": "Web Frontend Engineer", "source_feature_keys": ["notification_center"]},
            {"role": "Mobile Engineer", "source_feature_keys": ["notification_center"]},
            {"role": "QA Engineer", "source_feature_keys": ["notification_center"]},
        ],
        "required_skills": [
            {"skill": "API Design", "source_feature_keys": ["notification_center"]},
            {"skill": "React UI", "source_feature_keys": ["notification_center"]},
            {"skill": "Mobile Push Permission", "source_feature_keys": ["notification_center"]},
            {"skill": "QA Testing", "source_feature_keys": ["notification_center"]},
            {"skill": "Project Planning", "source_feature_keys": ["notification_center"]},
        ],
        "risk_factors": [
            {
                "risk_key": "duplicate_notifications",
                "text": "Duplicate notification delivery can occur across web and mobile.",
                "source_feature_keys": ["notification_center"],
            },
            {
                "risk_key": "mobile_permission_handling_issues",
                "text": "Mobile OS permission handling can block notification delivery.",
                "source_feature_keys": ["notification_center"],
            },
            {
                "risk_key": "delivery_delay",
                "text": "Short MVP delivery window.",
                "source_feature_keys": ["notification_center"],
            },
            {
                "risk_key": "security_and_compliance_issues",
                "text": "Notification preferences and audit data need security review.",
                "source_feature_keys": ["notification_center"],
            },
        ],
        "selected_employee_columns": [
            {"column_key": "employee.job_category_code"},
            {"column_key": "jira_activity.sprint_completion_rate"},
            {"column_key": "slack_activity.avg_response_time"},
        ],
        "column_weights": {
            "employee.job_category_code": 0.3,
            "employee.competency_score": 0.2,
            "jira_activity.sprint_completion_rate": 0.15,
            "jira_activity.completed_issue_count": 0.15,
            "slack_activity.avg_response_time": 0.1,
            "calendar_activity.busy_minutes": 0.1,
        },
        "column_priority_order": [
            "employee.job_category_code",
            "employee.competency_score",
            "jira_activity.sprint_completion_rate",
            "slack_activity.avg_response_time",
            "calendar_activity.busy_minutes",
        ],
        "unknown_requirements": [],
        "missing_extractions": [],
        "missing_fields": [],
        "low_confidence_items": [],
        "invalid_items": [],
    }


def _roleplay_requirements_input():
    return {
        "project_id": "project_notification",
        "project_name": "Notification Center MVP",
        "project_summary": "Build a web/mobile notification center.",
        "required_roles": [
            "PM",
            "Backend Developer",
            "Frontend Developer",
            "Mobile Engineer",
            "QA Engineer",
        ],
        "required_skills": [
            "API Design",
            "React UI",
            "Mobile Push Permission",
            "QA Testing",
            "Project Planning",
        ],
        "features": [
            {
                "feature_id": "notification_center",
                "feature_name": "Notification Center",
                "priority": "P0",
                "assigned_role": "Backend Developer",
                "tech_requirements": ["API Design", "React UI", "Mobile Push Permission"],
                "dependencies": [],
                "estimated_days": 3,
                "risk_notes": "duplicate_notifications",
            },
            {
                "feature_id": "mobile_permission",
                "feature_name": "Mobile Permission Handling",
                "priority": "P0",
                "assigned_role": "Mobile Engineer",
                "tech_requirements": ["Mobile Push Permission"],
                "dependencies": ["notification_center"],
                "estimated_days": 5,
                "risk_notes": "mobile_permission_handling_issues",
            },
        ],
        "timeline": {
            "total_sprint_days": 20,
            "milestones": [
                {
                    "name": "Notification Center complete",
                    "due_day": 10,
                    "owner_role": "Backend Developer",
                }
            ],
        },
        "constraints": ["Ship in 4 weeks.", "Protect user notification preference data."],
        "risk_flags": [
            "duplicate_notifications",
            "mobile_permission_handling_issues",
            "delivery_delay",
            "security_and_compliance_issues",
        ],
    }


def test_requirements_rankings_feed_roleplay_simulation_end_to_end() -> None:
    ranking_result = build_employee_team_rankings(
        _requirements_list(),
        _roleplay_requirements_input(),
        employee_data_dir="datasets/raw",
        max_team_size=5,
        top_candidates_per_role=3,
        max_ranked_teams=5,
        simulation_id="sim_e2e_requirements_roleplay",
    )
    packet = SimulationInputPacket.model_validate(
        ranking_result["roleplay_simulation_input_packet"]
    )
    evidence_index = EvidenceIndex.build(packet.evidence_metadata)
    sanitized = PrivacyColumnFilter().filter(packet)
    cards = AgentCardBuilder().build(sanitized.sanitized_snapshots, packet.project_context)
    phase_plan = ScenarioPhasePlanner().plan(
        packet.project_context,
        packet.team_risk_summary,
        evidence_index,
        packet.simulation_id,
    )
    orchestrator_output = SimulationOrchestrator(LLMMode.STUB).run(phase_plan, cards)
    simulation_log = PhaseLogCollector().collect(
        orchestrator_output,
        phase_plan,
        packet.project_context,
        packet.selected_team,
    )
    issue_summary = IssueRiskEvaluator().evaluate(
        simulation_log,
        packet.team_risk_summary,
        packet.evidence_metadata,
    )
    score_breakdown = ScoreCalculator().calculate(issue_summary, simulation_log)
    final_output = OutputBuilder().build(
        score_breakdown,
        issue_summary,
        simulation_log,
        packet.project_context.project_name,
    )

    scenario_event_count = sum(len(phase.scenario_events) for phase in phase_plan.phases)
    assert scenario_event_count > 0
    assert orchestrator_output.phase_runs
    assert simulation_log.phase_logs
    assert final_output.project_name == "Notification Center MVP"
    assert final_output.evidence_summary.total_evidence_refs > 0
    assert final_output.overall_project_fit < 1.0
    assert set(packet.team_risk_summary.risk_tags) >= {
        "integration_risk",
        "schedule_risk",
        "technical_dependency_risk",
    }
