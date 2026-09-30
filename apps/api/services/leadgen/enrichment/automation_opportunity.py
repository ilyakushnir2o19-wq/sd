"""Deterministic evidence-to-automation scoring for Opportunity Hunter.

The research layer may extract evidence; it does not award itself a score.
This module turns structured public evidence into a repeatable opportunity
score, mechanism hint, and qualification gate. It also mines the job-posting
text already fetched by JobSpy for concrete repetitive digital work.
"""

from __future__ import annotations

import json
import re
from typing import Any, Iterable
from urllib.parse import urlparse


_MANUAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "data_entry": (
        r"\bdata entry\b",
        r"\benter(?:ing)?\s+(?:data|orders?|invoices?|records?|information)\b",
        r"\bupdate\s+(?:the\s+)?(?:crm|erp|spreadsheet|system|database|records?)\b",
        r"\bmaintain\s+(?:the\s+)?(?:crm|erp|spreadsheet|database|records?)\b",
    ),
    "order_processing": (
        r"\border processing\b",
        r"\bprocess(?:ing)?\s+(?:customer\s+)?orders?\b",
        r"\border entry\b",
        r"\bconfirm(?:ing)?\s+orders?\b",
    ),
    "scheduling": (
        r"\bschedul(?:e|ing)\s+(?:appointments?|meetings?|jobs?|deliveries?|visits?)\b",
        r"\bbook(?:ing)?\s+(?:appointments?|slots?|meetings?)\b",
        r"\breschedul(?:e|ing)\b",
        r"\bappointment\s+(?:confirmation|reminder)s?\b",
    ),
    "document_processing": (
        r"\bprocess(?:ing)?\s+(?:documents?|forms?|applications?|claims?|invoices?)\b",
        r"\bverify(?:ing)?\s+(?:documents?|forms?|applications?|invoices?)\b",
        r"\bextract(?:ing)?\s+(?:data|information)\s+from\s+(?:documents?|pdfs?|forms?)\b",
    ),
    "reporting": (
        r"\bprepare\s+(?:daily|weekly|monthly|regular)?\s*reports?\b",
        r"\bcompile\s+(?:data|reports?)\b",
        r"\bgenerate\s+(?:daily|weekly|monthly|regular)?\s*reports?\b",
        r"\breconcil(?:e|ing|iation)\b",
    ),
    "inbox_support": (
        r"\brespond(?:ing)?\s+to\s+(?:customer|client|vendor)?\s*(?:emails?|messages?|inquiries|enquiries)\b",
        r"\bmonitor(?:ing)?\s+(?:shared\s+)?(?:inbox|mailbox|email)\b",
        r"\btriag(?:e|ing)\s+(?:tickets?|requests?|inquiries|enquiries)\b",
        r"\bfollow[- ]?up\s+(?:with|on)\b",
    ),
    "portal_work": (
        r"\bvendor\s+portal\b",
        r"\bcustomer\s+portal\b",
        r"\bupload(?:ing)?\s+(?:data|documents?|files?)\b",
        r"\bdownload(?:ing)?\s+(?:data|documents?|reports?|files?)\b",
    ),
    "crm_erp_admin": (
        r"\b(?:update|maintain|enter|record|log|reconcile)(?:ing)?\b.{0,48}\b(?:crm|erp|salesforce|hubspot|sap|netsuite)\b",
        r"\b(?:crm|erp|salesforce|hubspot|sap|netsuite)\b.{0,48}\b(?:update|maintenance|data entry|record keeping|reconciliation)\b",
    ),
    "spreadsheet_ops": (
        r"\b(?:update|maintain|prepare|reconcile|compile)(?:ing)?\b.{0,48}\b(?:excel|google sheets?|spreadsheets?)\b",
        r"\b(?:excel|google sheets?|spreadsheets?)\b.{0,48}\b(?:update|maintenance|reporting|reconciliation|data entry)\b",
    ),
}

_SYSTEM_PATTERNS: dict[str, str] = {
    "CRM": r"\bcrm\b",
    "ERP": r"\berp\b",
    "Salesforce": r"\bsalesforce\b",
    "HubSpot": r"\bhubspot\b",
    "SAP": r"\bsap\b",
    "NetSuite": r"\bnetsuite\b",
    "Excel": r"\bexcel\b",
    "Google Sheets": r"\bgoogle sheets?\b",
    "QuickBooks": r"\bquickbooks\b",
    "Shopify": r"\bshopify\b",
    "Zendesk": r"\bzendesk\b",
    "WhatsApp": r"\bwhats ?app\b",
    "Email": r"\bemail\b|\be-mail\b",
    "Portal": r"\b(?:vendor|customer|supplier) portal\b",
}

_PHYSICAL_PATTERNS = (
    r"\bwarehouse\b", r"\bforklift\b", r"\bdriver\b", r"\bconstruction\b",
    r"\bcleaning\b", r"\bmaintenance technician\b", r"\bfield technician\b",
    r"\bmachine operator\b", r"\bmanual handling\b",
)
_RELATIONSHIP_PATTERNS = (
    r"\baccount management\b", r"\brelationship management\b",
    r"\bnegotiat(?:e|ion|ing)\b", r"\bstrategic partnerships?\b",
    r"\bpeople management\b", r"\bteam leadership\b",
)
_JUDGMENT_PATTERNS = (
    r"\btriag(?:e|ing)\b", r"\bexception\b", r"\bdispute\b",
    r"\binvestigat(?:e|ion|ing)\b", r"\bapprove\b", r"\breview\b",
    r"\bprioriti[sz](?:e|ing)\b", r"\bdecision\b",
)
_SALARY_RE = re.compile(
    r"(?:[$€£₹]\s?\d[\d,.]*(?:\s?[kK])?(?:\s*[-–]\s*[$€£₹]?\s?\d[\d,.]*(?:\s?[kK])?)?)"
    r"|(?:\b\d[\d,.]*\s?(?:USD|EUR|GBP|INR)\b)",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"https?://[^\s\]\[)>'\"]+", re.IGNORECASE)


def _snippet(text: str, match: re.Match[str], radius: int = 90) -> str:
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def _unique(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = (value or "").strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def analyze_job_evidence(jobs_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract concrete manual-digital-work signals from fetched vacancies."""
    categories: set[str] = set()
    systems: set[str] = set()
    evidence: list[dict[str, str]] = []
    urls: list[str] = []
    budget_signals: list[str] = []
    physical_hits = relationship_hits = judgment_hits = relevant_roles = 0

    for job in jobs_data or []:
        title = str(job.get("title") or "").strip()
        desc = str(job.get("description") or "").strip()
        text = f"{title}. {desc}".strip()
        lowered = text.lower()
        source_url = str(
            job.get("job_url") or job.get("source_url") or job.get("url") or ""
        ).strip()
        if source_url:
            urls.append(source_url)

        job_categories: list[str] = []
        for category, patterns in _MANUAL_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, lowered, re.IGNORECASE)
                if match:
                    categories.add(category)
                    job_categories.append(category)
                    if len(evidence) < 12:
                        evidence.append({
                            "category": category,
                            "job_title": title,
                            "evidence": _snippet(text, match),
                            "source_url": source_url,
                        })
                    break
        if job_categories:
            relevant_roles += 1

        for system, pattern in _SYSTEM_PATTERNS.items():
            if re.search(pattern, lowered, re.IGNORECASE):
                systems.add(system)

        physical_hits += sum(bool(re.search(p, lowered, re.IGNORECASE)) for p in _PHYSICAL_PATTERNS)
        relationship_hits += sum(bool(re.search(p, lowered, re.IGNORECASE)) for p in _RELATIONSHIP_PATTERNS)
        judgment_hits += sum(bool(re.search(p, lowered, re.IGNORECASE)) for p in _JUDGMENT_PATTERNS)

        salary_parts = []
        for key in ("min_amount", "max_amount", "currency", "interval"):
            item = job.get(key)
            if item not in (None, ""):
                salary_parts.append(str(item))
        if salary_parts:
            budget_signals.append(" ".join(salary_parts))
        else:
            match = _SALARY_RE.search(text)
            if match:
                budget_signals.append(match.group(0))

    task_density = min(1.0, len(categories) / 5.0)
    digital_density = min(1.0, len(systems) / 4.0)
    role_density = min(1.0, relevant_roles / 3.0)
    evidence_strength = round(
        min(1.0, 0.45 * task_density + 0.30 * digital_density + 0.25 * role_density), 3
    )
    score = int(round(100 * evidence_strength))
    if budget_signals:
        score = min(100, score + 10)
    if physical_hits > len(categories) and len(categories) <= 1:
        score = max(0, score - 35)
    if relationship_hits > 1 and len(categories) <= 1:
        score = max(0, score - 20)

    mechanism = (
        "unknown" if not categories
        else "assisted-agent" if judgment_hits > 0
        else "rpa-api"
    )
    return {
        "manual_ops_score": score,
        "manual_ops_roles": relevant_roles,
        "task_categories": sorted(categories),
        "task_evidence": evidence,
        "systems": sorted(systems),
        "budget_signals": _unique(budget_signals)[:5],
        "evidence_urls": _unique(urls)[:10],
        "evidence_strength": evidence_strength,
        "physical_work_signal": physical_hits > 0,
        "relationship_work_signal": relationship_hits > 0,
        "judgment_signal": judgment_hits > 0,
        "mechanism_hint": mechanism,
    }


def _coerce_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value in (None, ""):
        return {}
    try:
        parsed = json.loads(str(value).strip())
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {
        "1", "true", "yes", "y", "possible", "pass"
    }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _collect_urls(value: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in {"url", "source_url", "job_url", "evidence_url"} and isinstance(item, str):
                urls.extend(_URL_RE.findall(item))
            else:
                urls.extend(_collect_urls(item))
    elif isinstance(value, list):
        for item in value:
            urls.extend(_collect_urls(item))
    elif isinstance(value, str):
        urls.extend(_URL_RE.findall(value))
    return _unique(urls)


def _domains(urls: list[str]) -> set[str]:
    domains: set[str] = set()
    for url in urls:
        try:
            host = (urlparse(url).hostname or "").lower()
        except ValueError:
            host = ""
        if host:
            domains.add(host.removeprefix("www."))
    return domains


def score_opportunity_evidence(value: Any) -> dict[str, Any]:
    """Score normalized evidence; return score, mechanism and PASS/REVIEW/KILL."""
    payload = _coerce_payload(value)
    if not payload:
        return {
            "score": 0,
            "mechanism": "unknown",
            "gate": "KILL",
            "reasons": ["invalid_or_missing_evidence_json"],
            "metrics": {},
        }

    manual_tasks = _as_list(payload.get("manual_tasks") or payload.get("tasks"))
    website_evidence = _as_list(payload.get("website_evidence"))
    budget_signals = _as_list(payload.get("budget_signals") or payload.get("budget"))
    automation_paths = [
        str(x).strip().lower()
        for x in _as_list(payload.get("automation_paths"))
        if str(x).strip()
    ]
    systems = _as_list(payload.get("systems") or payload.get("digital_systems"))
    source_urls = _unique(_collect_urls(payload) + [
        str(x) for x in _as_list(payload.get("source_urls"))
        if str(x).startswith(("http://", "https://"))
    ])
    source_domains = _domains(source_urls)

    acceptance = payload.get("acceptance_test") or {}
    if isinstance(acceptance, dict):
        testable = _truthy(acceptance.get("possible")) or bool(
            acceptance.get("metric") or acceptance.get("success_condition")
        )
    else:
        testable = _truthy(acceptance)

    task_text = " ".join(
        json.dumps(t, ensure_ascii=False) if isinstance(t, dict) else str(t)
        for t in manual_tasks
    ).lower()
    has_input = any(isinstance(t, dict) and t.get("input") for t in manual_tasks)
    has_output = any(isinstance(t, dict) and t.get("output") for t in manual_tasks)
    has_system = bool(systems) or any(
        token in task_text
        for token in ("crm", "erp", "excel", "spreadsheet", "portal", "email", "whatsapp", "system")
    )

    frequency_raw = str(payload.get("frequency_signal") or payload.get("frequency") or "").lower()
    if any(x in frequency_raw for x in ("high", "daily", "many", "repeated", "repetitive")):
        frequency = 1.0
    elif any(x in frequency_raw for x in ("medium", "weekly", "regular")):
        frequency = 0.65
    else:
        frequency = 0.35 if frequency_raw else 0.0

    physical_only = _truthy(payload.get("physical_only"))
    relationship_heavy = _truthy(payload.get("relationship_heavy"))
    risk_value = payload.get("risk_level")
    if not risk_value:
        risk_field = payload.get("risk")
        risk_value = risk_field.get("level") if isinstance(risk_field, dict) else risk_field
    risk_level = str(risk_value or "").lower()
    judgment_level = str(payload.get("judgment_level") or "").lower()

    evidence_points = (10 if manual_tasks else 0) + (5 if source_urls else 0) + (5 if len(source_domains) >= 2 else 0)
    repetition_points = round(20 * min(1.0, 0.45 + 0.55 * frequency), 2) if manual_tasks else 0
    digital_points = (8 if has_system else 0) + (6 if has_input else 0) + (6 if has_output else 0)
    budget_points = 15 if budget_signals else 0
    feasibility_points = 15 if automation_paths else 0
    testability_points = 10 if testable else 0

    risk_penalty = 25 if risk_level in {"high", "critical", "regulated"} else 10 if risk_level in {"medium", "moderate"} else 0
    raw_score = (
        evidence_points + repetition_points + digital_points + budget_points
        + feasibility_points + testability_points - risk_penalty
    )
    score = max(0, min(100, int(round(raw_score))))

    if physical_only:
        mechanism = "human"
    elif risk_level in {"high", "critical", "regulated"}:
        mechanism = "human-in-loop"
    elif judgment_level in {"high", "medium"}:
        mechanism = "assisted-agent"
    elif automation_paths:
        mechanism = "rpa-api"
    else:
        mechanism = "unknown"

    kill_reasons: list[str] = []
    review_reasons: list[str] = []
    if not manual_tasks:
        kill_reasons.append("no_concrete_manual_task")
    if not source_urls:
        kill_reasons.append("no_citable_source")
    if physical_only:
        kill_reasons.append("physical_only_work")
    if relationship_heavy and not automation_paths:
        kill_reasons.append("relationship_heavy_without_automatable_subprocess")
    if not automation_paths:
        kill_reasons.append("no_credible_automation_path")
    if score < 45:
        kill_reasons.append("score_below_45")

    if not kill_reasons:
        if risk_level in {"high", "critical", "regulated"}:
            review_reasons.append("high_risk_requires_human_gate")
        if relationship_heavy:
            review_reasons.append("relationship_heavy_scope")
        if len(source_domains) < 2:
            review_reasons.append("needs_second_independent_source")
        if not budget_signals:
            review_reasons.append("no_budget_signal")
        if not testable:
            review_reasons.append("no_objective_acceptance_test")
        if score < 70:
            review_reasons.append("score_below_70")

    gate = "KILL" if kill_reasons else "REVIEW" if review_reasons else "PASS"
    return {
        "score": score,
        "mechanism": mechanism,
        "gate": gate,
        "reasons": kill_reasons or review_reasons or ["evidence_and_feasibility_thresholds_met"],
        "metrics": {
            "manual_task_count": len(manual_tasks),
            "website_evidence_count": len(website_evidence),
            "source_count": len(source_urls),
            "independent_source_domains": len(source_domains),
            "budget_signal_count": len(budget_signals),
            "automation_path_count": len(automation_paths),
            "testable": testable,
            "has_system": has_system,
            "has_input": has_input,
            "has_output": has_output,
            "risk_level": risk_level or "unknown",
        },
    }


def opportunity_score(value: Any) -> int:
    return int(score_opportunity_evidence(value)["score"])


def opportunity_mechanism(value: Any) -> str:
    return str(score_opportunity_evidence(value)["mechanism"])


def opportunity_gate(value: Any) -> str:
    return str(score_opportunity_evidence(value)["gate"])


# Stable aliases used by workbook formulas.
def automation_score(value: Any) -> int:
    return opportunity_score(value)


def automation_mechanism(value: Any) -> str:
    return opportunity_mechanism(value)


def automation_gate(value: Any) -> str:
    return opportunity_gate(value)
