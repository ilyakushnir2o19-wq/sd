"""Attio CRM adapter — upsert enriched OpenGTM leads as People records.

Attio's People object has one unique attribute: email_addresses. The adapter
therefore uses Attio's native upsert endpoint for normal pushes and
PATCH-by-record-id for rows that were previously synced.
"""

import os
from typing import Any, Dict, Optional

import httpx

from apps.api.services.crm import request_with_retry

BASE_URL = "https://api.attio.com/v2"

DEFAULT_FIELD_MAP = {
    "email": "email_addresses",
    "contact_person": "name",
    "contact_title": "job_title",
    "phone": "phone_numbers",
    "linkedin_url": "linkedin",
}


def _get_token(workspace_id: Optional[str] = None) -> str:
    """Resolve an Attio token from workspace secrets, then environment."""
    try:
        from apps.api.services.workspace.secrets import get_secret
        return get_secret(workspace_id, "ATTIO_API_TOKEN", "")
    except Exception:
        return os.getenv("ATTIO_API_TOKEN", "")


def is_connected(workspace_id: Optional[str] = None) -> bool:
    return bool(_get_token(workspace_id))


def _read(source: Any, field: str) -> Any:
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


def _name_value(raw: str) -> Dict[str, str]:
    full = str(raw).strip()
    if not full:
        return {}
    first, sep, last = full.partition(" ")
    value = {"first_name": first, "full_name": full}
    if sep and last.strip():
        value["last_name"] = last.strip()
    return value


def _attio_value(attribute: str, raw: Any) -> Any:
    """Convert an OpenGTM scalar to Attio's typed attribute write shape."""
    if raw in (None, ""):
        return None
    value = str(raw).strip()
    if not value:
        return None

    if attribute == "email_addresses":
        return [{"email_address": value}]
    if attribute == "name":
        name = _name_value(value)
        return [name] if name else None
    if attribute == "phone_numbers":
        return [{"original_phone_number": value}]
    return [{"value": value}]


def _values_from_lead(source: Any, field_map: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    fmap = field_map or DEFAULT_FIELD_MAP
    values: Dict[str, Any] = {}
    for lead_field, attio_attribute in fmap.items():
        converted = _attio_value(attio_attribute, _read(source, lead_field))
        if converted is not None:
            values[attio_attribute] = converted
    return values


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _record_id(payload: Dict[str, Any]) -> Optional[str]:
    record_id = ((payload.get("data") or {}).get("id") or {}).get("record_id")
    return str(record_id) if record_id else None


async def push_lead_as_contact(
    lead: Any,
    field_map: Optional[Dict[str, str]] = None,
    workspace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update an Attio Person, matching by email address."""
    token = _get_token(workspace_id)
    if not token:
        return {"success": False, "error": "No Attio API token configured"}

    email = str(_read(lead, "email") or "").strip()
    if not email:
        return {"success": False, "error": "Lead has no email — required for Attio person upsert"}

    values = _values_from_lead(lead, field_map)
    values["email_addresses"] = [{"email_address": email}]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await request_with_retry(
                client,
                "PUT",
                f"{BASE_URL}/objects/people/records",
                params={"matching_attribute": "email_addresses"},
                headers=_headers(token),
                json={"data": {"values": values}},
            )
        if response.status_code == 200:
            return {
                "success": True,
                "action": "upserted",
                "attio_id": _record_id(response.json()),
            }
        return {
            "success": False,
            "error": f"HTTP {response.status_code}: {response.text[:200]}",
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)[:200]}


async def update_person_by_id(
    record_id: str,
    lead_data: Any,
    field_map: Optional[Dict[str, str]] = None,
    workspace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing Attio Person by record id."""
    token = _get_token(workspace_id)
    if not token:
        return {"success": False, "error": "No Attio API token configured"}

    values = _values_from_lead(lead_data, field_map)
    if not values:
        return {"success": False, "error": "No mapped fields to update"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await request_with_retry(
                client,
                "PATCH",
                f"{BASE_URL}/objects/people/records/{record_id}",
                headers=_headers(token),
                json={"data": {"values": values}},
            )
        if response.status_code == 200:
            return {
                "success": True,
                "action": "updated",
                "attio_id": _record_id(response.json()) or str(record_id),
            }
        if response.status_code == 404:
            return {
                "success": False,
                "not_found": True,
                "error": f"person {record_id} not found in Attio",
            }
        return {
            "success": False,
            "error": f"HTTP {response.status_code}: {response.text[:200]}",
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)[:200]}
