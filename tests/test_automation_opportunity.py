"""Offline contract tests for Opportunity Hunter evidence-to-automation logic."""

import json

from apps.api.services.leadgen.enrichment.automation_opportunity import (
    analyze_job_evidence,
    automation_gate,
    automation_mechanism,
    automation_score,
    score_opportunity_evidence,
)
from apps.api.services.workbook.formula_column import evaluate_formula


def _strong_evidence(**overrides):
    data = {
        "manual_tasks": [{
            "task": "Enter customer orders from email into ERP",
            "input": "customer order email",
            "output": "ERP order record and confirmation",
            "systems": ["SAP", "Email"],
            "frequency_signal": "daily repetitive",
            "source_url": "https://jobs.example.com/order-coordinator",
        }],
        "website_evidence": [{
            "fact": "Customers send orders through the company order portal.",
            "source_url": "https://example.com/order",
        }],
        "budget_signals": [{
            "kind": "salary",
            "value": "EUR 40k-45k",
            "source_url": "https://jobs.example.com/order-coordinator",
        }],
        "automation_paths": ["api", "workflow"],
        "acceptance_test": {
            "possible": True,
            "metric": "ERP order fields match the source order and confirmation is created",
        },
        "frequency_signal": "daily repetitive",
        "systems": ["SAP", "Email"],
        "risk_level": "low",
        "judgment_level": "low",
        "physical_only": False,
        "relationship_heavy": False,
        "source_urls": [
            "https://jobs.example.com/order-coordinator",
            "https://example.com/order",
        ],
    }
    data.update(overrides)
    return data


def test_job_evidence_surfaces_manual_digital_work_and_source_url():
    result = analyze_job_evidence([{
        "title": "Order Processing Coordinator",
        "description": (
            "Process customer orders, enter order data into SAP, update Excel "
            "tracking sheets and confirm orders by email. Salary €40,000-€45,000."
        ),
        "job_url": "https://jobs.example.com/123",
    }])

    assert result["manual_ops_score"] >= 50
    assert "order_processing" in result["task_categories"]
    assert {"SAP", "Excel", "Email"} <= set(result["systems"])
    assert result["budget_signals"]
    assert result["evidence_urls"] == ["https://jobs.example.com/123"]
    assert result["mechanism_hint"] == "rpa-api"
    assert all(item["source_url"] for item in result["task_evidence"])


def test_job_evidence_does_not_promote_physical_role_without_digital_task():
    result = analyze_job_evidence([{
        "title": "Warehouse Forklift Driver",
        "description": "Operate a forklift, load pallets, perform manual handling and warehouse cleaning.",
        "job_url": "https://jobs.example.com/warehouse",
    }])

    assert result["task_categories"] == []
    assert result["manual_ops_score"] == 0
    assert result["physical_work_signal"] is True
    assert result["mechanism_hint"] == "unknown"


def test_strong_independent_evidence_passes_deterministic_gate():
    result = score_opportunity_evidence(_strong_evidence())
    assert result["gate"] == "PASS"
    assert result["score"] >= 70
    assert result["mechanism"] == "rpa-api"
    assert result["metrics"]["independent_source_domains"] == 2
    assert result["metrics"]["testable"] is True


def test_single_source_stays_review_even_with_good_task():
    evidence = _strong_evidence(
        website_evidence=[],
        source_urls=["https://jobs.example.com/order-coordinator"],
    )
    result = score_opportunity_evidence(evidence)
    assert result["gate"] == "REVIEW"
    assert "needs_second_independent_source" in result["reasons"]


def test_missing_automation_path_is_killed():
    result = score_opportunity_evidence(_strong_evidence(automation_paths=[]))
    assert result["gate"] == "KILL"
    assert "no_credible_automation_path" in result["reasons"]


def test_high_risk_opportunity_requires_review_and_human_gate():
    result = score_opportunity_evidence(_strong_evidence(risk_level="high"))
    assert result["mechanism"] == "human-in-loop"
    assert result["gate"] == "REVIEW"
    assert "high_risk_requires_human_gate" in result["reasons"]


def test_formula_functions_expose_same_deterministic_contract():
    payload = json.dumps(_strong_evidence())
    row = {"evidence": payload}

    assert evaluate_formula("automation_score({evidence})", row) == automation_score(payload)
    assert evaluate_formula("automation_mechanism({evidence})", row) == automation_mechanism(payload)
    assert evaluate_formula("automation_gate({evidence})", row) == automation_gate(payload)


def test_invalid_evidence_fails_closed():
    assert automation_score("not-json") == 0
    assert automation_mechanism("not-json") == "unknown"
    assert automation_gate("not-json") == "KILL"
