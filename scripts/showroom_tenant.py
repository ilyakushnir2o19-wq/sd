#!/usr/bin/env python3
"""Create a showroom tenant config from a normalized 2GIS/OpenGTM row.

This is intentionally deterministic and safe for cold-demo generation:
- no credentials;
- no scraping side effects;
- no fake live integrations;
- every generated preview is clearly a preview until sold.

Usage:
  python scripts/showroom_tenant.py \
    --company "ABC Auto" \
    --slug abc-auto \
    --category "Автосервис · Москва" \
    --phone "+7 999 000-00-00" \
    --address "Москва, ..." \
    --hero "https://..." \
    --service "Замена масла|50 мин|2500|масло клиента" \
    --service "Диагностика|45 мин|1800|ходовая"
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TENANTS = ROOT / "apps" / "web" / "public" / "showroom" / "tenants"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "business"


def parse_service(raw: str, index: int) -> dict:
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 3:
        raise ValueError("service must be NAME|DURATION|PRICE[|NOTE]")
    name, duration, price_raw = parts[:3]
    note = parts[3] if len(parts) > 3 else ""
    price = int(re.sub(r"\D", "", price_raw) or "0")
    return {
        "id": f"service-{index}",
        "name": name,
        "duration": duration,
        "price": price,
        "note": note,
        "description": f"{name}. Детали и финальную стоимость подтвердит специалист.",
    }


def build_config(args: argparse.Namespace) -> dict:
    services = [
        parse_service(raw, i + 1)
        for i, raw in enumerate(args.service or [])
    ]
    if not services:
        services = [
            {
                "id": "service-1",
                "name": "Диагностика",
                "duration": "45 мин",
                "price": 1500,
                "note": "первичный осмотр",
                "description": "Первичный осмотр и рекомендации специалиста.",
            },
            {
                "id": "service-2",
                "name": "Основная услуга",
                "duration": "1–2 часа",
                "price": 3500,
                "note": "по записи",
                "description": "Работа по предварительной записи с подтверждением мастером.",
            },
        ]
    return {
        "slug": args.slug,
        "name": args.company,
        "shortName": args.short_name or args.company[:18],
        "category": args.category,
        "headline": args.headline or "Запишитесь без звонка.",
        "subheadline": args.subheadline or "Выберите услугу и удобное время.",
        "phone": args.phone,
        "address": args.address,
        "hours": args.hours,
        "rating": args.rating,
        "reviewsLabel": args.reviews_label,
        "accent": args.accent,
        "hero": args.hero,
        "aiExample": args.ai_example,
        "proof": [
            {"title": "Онлайн-запись", "text": "Свободные слоты перед глазами"},
            {"title": "Подтверждение", "text": "Мастер проверит детали"},
        ],
        "slots": ["10:00", "11:30", "13:00", "15:30", "17:00", "19:00"],
        "services": services,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--company", required=True)
    p.add_argument("--slug", default="")
    p.add_argument("--short-name", default="")
    p.add_argument("--category", default="Автосервис")
    p.add_argument("--phone", default="")
    p.add_argument("--address", default="")
    p.add_argument("--hours", default="09:00–21:00")
    p.add_argument("--rating", default="4.9")
    p.add_argument("--reviews-label", default="по отзывам клиентов")
    p.add_argument("--accent", default="#c6ff38")
    p.add_argument("--hero", default="https://images.unsplash.com/photo-1487754180451-c456f719a1fc?auto=format&fit=crop&w=1200&q=85")
    p.add_argument("--headline", default="")
    p.add_argument("--subheadline", default="")
    p.add_argument("--ai-example", default="Хочу записаться завтра вечером")
    p.add_argument("--service", action="append", default=[])
    p.add_argument("--output", type=Path)
    args = p.parse_args()

    args.slug = slugify(args.slug or args.company)
    cfg = build_config(args)

    out = args.output or TENANTS / f"{args.slug}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "tenant": args.slug,
        "path": str(out),
        "demo_url": f"/showroom/?tenant={args.slug}",
        "services": len(cfg["services"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
