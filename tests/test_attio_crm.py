"""
Attio CRM adapter and workbook output routing.

These tests define the MVP contract:
- workspace/global token resolution is honored by the adapter;
- people are upserted by the unique email_addresses attribute;
- updates by external Attio record id use PATCH;
- workbook CRM output can dispatch to crm_type=attio.
"""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

import httpx

import apps.api.services.crm.attio as attio
from apps.api.services.workbook import output as workbook_output


def _patch_transport(monkeypatch, handler):
    real_init = httpx.AsyncClient.__init__

    def init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", init)


def _lead(**overrides):
    data = {
        "email": "ada@example.com",
        "contact_person": "Ada Lovelace",
        "contact_title": "CTO",
        "phone": "+44 20 7946 0958",
        "linkedin_url": "https://www.linkedin.com/in/ada",
        "company": "Analytical Engines",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_attio_upserts_person_by_email(monkeypatch):
    monkeypatch.setattr(attio, "_get_token", lambda workspace_id=None: "attio-token")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"data": {"id": {"record_id": "person-123"}}},
        )

    _patch_transport(monkeypatch, handler)
    result = asyncio.run(attio.push_lead_as_contact(_lead(), workspace_id="ws-1"))

    assert result == {
        "success": True,
        "action": "upserted",
        "attio_id": "person-123",
    }
    assert seen["method"] == "PUT"
    assert seen["url"] == (
        "https://api.attio.com/v2/objects/people/records"
        "?matching_attribute=email_addresses"
    )
    assert seen["auth"] == "Bearer attio-token"

    values = seen["body"]["data"]["values"]
    assert values["email_addresses"] == [{"email_address": "ada@example.com"}]
    assert values["name"] == [{
        "first_name": "Ada",
        "last_name": "Lovelace",
        "full_name": "Ada Lovelace",
    }]
    assert values["job_title"] == [{"value": "CTO"}]
    assert values["phone_numbers"] == [{
        "original_phone_number": "+44 20 7946 0958"
    }]
    assert values["linkedin"] == [{"value": "https://www.linkedin.com/in/ada"}]


def test_attio_requires_email(monkeypatch):
    monkeypatch.setattr(attio, "_get_token", lambda workspace_id=None: "attio-token")
    result = asyncio.run(attio.push_lead_as_contact(_lead(email="")))
    assert result["success"] is False
    assert "email" in result["error"].lower()


def test_attio_update_by_record_id_returns_not_found(monkeypatch):
    monkeypatch.setattr(attio, "_get_token", lambda workspace_id=None: "attio-token")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/v2/objects/people/records/person-missing"
        return httpx.Response(404, json={"status_code": 404})

    _patch_transport(monkeypatch, handler)
    result = asyncio.run(attio.update_person_by_id(
        "person-missing",
        {
            "email": "ada@example.com",
            "contact_title": "Chief Scientist",
        },
        workspace_id="ws-1",
    ))
    assert result["success"] is False
    assert result["not_found"] is True


def test_workbook_crm_dispatch_routes_to_attio(monkeypatch):
    monkeypatch.setattr(attio, "is_connected", lambda workspace_id=None: True)

    async def fake_push(lead, field_map=None, workspace_id=None):
        assert lead.email == "ada@example.com"
        assert workspace_id == "ws-1"
        return {"success": True, "action": "upserted", "attio_id": "person-789"}

    monkeypatch.setattr(attio, "push_lead_as_contact", fake_push)

    result = asyncio.run(workbook_output._push_crm(
        {"type": "attio"},
        {
            "email": "ada@example.com",
            "contact_person": "Ada Lovelace",
            "company": "Analytical Engines",
        },
        "ws-1",
        workbook_id="wb-1",
        lead_id=1,
    ))

    assert result == {
        "success": True,
        "value": "Attio: upserted person-789",
        "error": None,
    }


def test_settings_exposes_attio_integration():
    from apps.api.routers.settings import INTEGRATIONS

    integration = next(item for item in INTEGRATIONS if item["id"] == "attio")
    assert integration["name"] == "Attio"
    assert integration["fields"] == [{
        "key": "ATTIO_API_TOKEN",
        "label": "API Token",
        "secret": True,
        "placeholder": "Attio workspace token",
    }]
