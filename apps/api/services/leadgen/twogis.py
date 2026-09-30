"""2GIS parser -> OpenGTM workbook row normalization.

The external parser emits rich, nested 2GIS objects. Opportunity Hunter only
needs a stable company identity plus public contact/context fields. This module
keeps the conversion deterministic and loss-aware so GitHub Actions, local CLI
runs, and future source adapters all produce the same row shape.
"""

from __future__ import annotations

import re
from typing import Any, Iterable
from urllib.parse import urlparse

import requests


_SOCIAL_HOSTS = {
    "t.me", "telegram.me", "wa.me", "whatsapp.com", "vk.com", "ok.ru",
    "youtube.com", "youtu.be", "instagram.com", "facebook.com",
}
_BAD_WEBSITE_LABELS = (
    "перейти в telegram", "перейти в канал", "telegram-канал", "написать в",
)


def _listify(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    return value if isinstance(value, list) else [value]


def _unique_strings(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _contact_map(item: dict[str, Any]) -> dict[str, list[str]]:
    """Read either raw parser contact_groups or an already-slim row."""
    contacts: dict[str, list[str]] = {}

    for group in item.get("contact_groups") or []:
        for contact in group.get("contacts") or []:
            ctype = str(contact.get("type") or "").strip().lower()
            value = (
                contact.get("text")
                or contact.get("value")
                or contact.get("url")
                or ""
            )
            if ctype and value:
                contacts.setdefault(ctype, []).append(str(value).strip())

    # The repo's quick/lead workflows already flatten these fields. Accept them
    # too so artifacts can be re-ingested without the original raw parser file.
    aliases = {
        "phone": ("phone", "phones"),
        "email": ("email", "emails"),
        "website": ("website", "websites"),
        "whatsapp": ("whatsapp",),
        "telegram": ("telegram",),
    }
    for ctype, keys in aliases.items():
        for key in keys:
            contacts.setdefault(ctype, []).extend(
                str(v).strip() for v in _listify(item.get(key)) if str(v or "").strip()
            )

    return {k: _unique_strings(v) for k, v in contacts.items()}


def _looks_like_business_website(value: str) -> bool:
    text = (value or "").strip()
    lowered = text.lower()
    if not text or any(label in lowered for label in _BAD_WEBSITE_LABELS):
        return False

    candidate = text if "://" in text else f"https://{text}"
    try:
        parsed = urlparse(candidate)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if not host or "." not in host:
        return False
    if host in _SOCIAL_HOSTS or any(host.endswith("." + s) for s in _SOCIAL_HOSTS):
        return False
    return True


def _first_business_website(values: Iterable[str]) -> str:
    for value in values:
        if _looks_like_business_website(value):
            return str(value).strip()
    return ""


def _name(item: dict[str, Any]) -> str:
    name_ex = item.get("name_ex")
    if isinstance(name_ex, dict):
        primary = str(name_ex.get("primary") or "").strip()
        if primary:
            return primary
    return str(item.get("name") or "").strip()


def _rubrics(item: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for rubric in item.get("rubrics") or []:
        if isinstance(rubric, dict):
            values.append(str(rubric.get("name") or "").strip())
        else:
            values.append(str(rubric or "").strip())
    # Some slim artifacts may use category/categories.
    values.extend(str(x).strip() for x in _listify(item.get("categories")))
    return _unique_strings(values)


def normalize_2gis_row(
    item: dict[str, Any],
    *,
    city: str = "",
    discovery_url: str = "",
) -> dict[str, Any]:
    """Convert one raw/slim 2GIS object into an OpenGTM workbook row."""
    contacts = _contact_map(item)
    reviews = item.get("reviews") if isinstance(item.get("reviews"), dict) else {}

    company = _name(item)
    website = _first_business_website(contacts.get("website", []))
    phones = contacts.get("phone", [])
    emails = contacts.get("email", [])
    rubrics = _rubrics(item)

    rating = (
        item.get("rating")
        if item.get("rating") not in (None, "")
        else reviews.get("general_rating")
    )
    review_count = (
        item.get("reviews_count")
        if item.get("reviews_count") not in (None, "")
        else item.get("review_count")
    )
    if review_count in (None, ""):
        slim_reviews = item.get("reviews")
        review_count = (
            slim_reviews
            if isinstance(slim_reviews, (int, float, str))
            else reviews.get("general_review_count")
        )

    source_url = str(
        item.get("source_url")
        or item.get("url")
        or item.get("link")
        or discovery_url
        or ""
    ).strip()

    row: dict[str, Any] = {
        "company": company,
        "website": website,
        "phone": phones[0] if phones else "",
        "email": emails[0] if emails else "",
        "address": str(item.get("address_name") or item.get("address") or "").strip(),
        "city": city,
        "specialization": ", ".join(rubrics),
        "source": "2gis",
        "source_url": source_url,
        "2gis_id": str(item.get("2gis_id") or item.get("id") or "").strip(),
        "2gis_rating": rating,
        "2gis_reviews": review_count,
        "2gis_rubrics": rubrics,
        "whatsapp": contacts.get("whatsapp", []),
        "telegram": contacts.get("telegram", []),
        "secondary_phones": "|".join(phones[1:3]) if len(phones) > 1 else "",
        "secondary_emails": "|".join(emails[1:3]) if len(emails) > 1 else "",
    }

    # Do not ingest identity-less junk rows. Unknown/custom keys are intentionally
    # retained by the ingest API, but empty noise adds no value to Hunter.
    return {k: v for k, v in row.items() if v not in (None, "", [], {})}


def normalize_2gis_rows(
    rows: list[dict[str, Any]],
    *,
    city: str = "",
    discovery_url: str = "",
) -> list[dict[str, Any]]:
    """Normalize and dedupe a batch by website domain, else company name."""
    from apps.api.services.leadgen.dedup import normalize_company, normalize_domain

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows or []:
        row = normalize_2gis_row(raw or {}, city=city, discovery_url=discovery_url)
        company = str(row.get("company") or "").strip()
        website = str(row.get("website") or "").strip()
        if not company and not website:
            continue

        domain = normalize_domain(website)
        identity = f"d:{domain}" if domain else f"n:{normalize_company(company)}"
        if identity in seen:
            continue
        seen.add(identity)
        out.append(row)
    return out


MAX_INGEST_BATCH = 500


def ingest_2gis_rows(
    rows: list[dict[str, Any]],
    *,
    opengtm_url: str,
    workbook_id: str,
    token: str,
    source_fingerprint: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Push normalized rows through the public workbook ingest contract.

    Every batch receives a stable Idempotency-Key derived from the source file
    fingerprint, so retrying the same 2GIS artifact cannot duplicate rows even
    before the workbook's domain/company dedupe runs.
    """
    if not rows:
        return {
            "added": 0,
            "skipped_duplicates": 0,
            "skipped_empty": 0,
            "batches": 0,
            "total_rows": None,
            "unmapped_keys": [],
        }

    base = (opengtm_url or "").strip().rstrip("/")
    workbook_id = (workbook_id or "").strip()
    token = (token or "").strip()
    if not base or not workbook_id or not token:
        raise ValueError("OpenGTM URL, workbook id and ingest token are required")

    endpoint = f"{base}/api/v2/workbooks/{workbook_id}/rows/ingest"
    totals: dict[str, Any] = {
        "added": 0,
        "skipped_duplicates": 0,
        "skipped_empty": 0,
        "batches": 0,
        "total_rows": None,
        "unmapped_keys": set(),
    }

    for offset in range(0, len(rows), MAX_INGEST_BATCH):
        batch_index = offset // MAX_INGEST_BATCH
        batch = rows[offset: offset + MAX_INGEST_BATCH]
        idem = f"2gis-{source_fingerprint[:32]}-{batch_index}"
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": idem,
                "Content-Type": "application/json",
                "User-Agent": "OpenGTM-2GIS-Bridge/1.0",
            },
            json={"rows": batch, "dedupe": True},
            timeout=timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"OpenGTM ingest failed: HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )
        payload = response.json()
        totals["added"] += int(payload.get("added") or 0)
        totals["skipped_duplicates"] += int(payload.get("skipped_duplicates") or 0)
        totals["skipped_empty"] += int(payload.get("skipped_empty") or 0)
        totals["batches"] += 1
        totals["total_rows"] = payload.get("total_rows")
        totals["unmapped_keys"].update(payload.get("unmapped_keys") or [])

    totals["unmapped_keys"] = sorted(totals["unmapped_keys"])
    return totals
