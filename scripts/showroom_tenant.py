#!/usr/bin/env python3
"""Create a premium booking-showroom tenant from public business data.

The output is a sales demo, not a live booking deployment. It never claims that
appointments, notifications or AI are connected until the tenant is promoted
to a real backend.

Usage:
  python scripts/showroom_tenant.py \
    --company "ABC Auto" --slug abc-auto --city "Москва" \
    --phone "+7 999 000-00-00" --address "Москва, ..." \
    --hero "https://..." --accent "#C9FF3D" \
    --gallery "https://...|BMW X5|полировка" \
    --service "Замена масла|50 мин|2500|без стоимости масла|https://..."
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
        raise ValueError("service must be NAME|DURATION|PRICE[|NOTE|IMAGE]")
    name, duration, price_raw = parts[:3]
    note = parts[3] if len(parts) > 3 else ""
    image = parts[4] if len(parts) > 4 else ""
    price = int(re.sub(r"\D", "", price_raw) or "0")
    out = {
        "id": f"service-{index}",
        "name": name,
        "duration": duration,
        "price": price,
        "note": note,
        "description": f"{name}. Детали и финальную стоимость подтвердит специалист.",
    }
    if image:
        out["image"] = image
    return out


def parse_gallery(raw: str, index: int) -> dict:
    parts = [p.strip() for p in raw.split("|")]
    if not parts or not parts[0]:
        raise ValueError("gallery must be URL[|TITLE|META]")
    return {
        "src": parts[0],
        "title": parts[1] if len(parts) > 1 and parts[1] else f"Работа {index}",
        "meta": parts[2] if len(parts) > 2 else "",
    }


def build_config(args: argparse.Namespace) -> dict:
    services = [parse_service(raw, i + 1) for i, raw in enumerate(args.service or [])]
    if not services:
        services = [
            {
                "id": "service-1",
                "name": "Диагностика",
                "duration": "45 мин",
                "price": 1500,
                "note": "первичный осмотр",
                "description": "Первичный осмотр и рекомендации специалиста.",
                "image": args.hero,
            },
            {
                "id": "service-2",
                "name": "Основная услуга",
                "duration": "1–2 часа",
                "price": 3500,
                "note": "по записи",
                "description": "Работа по предварительной записи с подтверждением мастером.",
                "image": args.hero,
            },
        ]

    gallery = [parse_gallery(raw, i + 1) for i, raw in enumerate(args.gallery or [])]
    if not gallery and args.hero:
        gallery = [{"src": args.hero, "title": args.company, "meta": "наши работы"}]

    short_name = args.short_name or args.company[:18]
    return {
        "slug": args.slug,
        "name": args.company,
        "shortName": short_name,
        "logoMark": args.logo_mark or short_name[:1].upper(),
        "brandLine": args.brand_line,
        "category": args.category,
        "city": args.city,
        "headline": args.headline or "Запишитесь без звонка.",
        "subheadline": args.subheadline or "Выберите услугу и удобное время.",
        "phone": args.phone,
        "address": args.address,
        "hours": args.hours,
        "status": args.status,
        "rating": args.rating,
        "reviewsLabel": args.reviews_label,
        "accent": args.accent,
        "accentSecondary": args.accent_secondary or args.accent,
        "themeColor": "#08090B",
        "nearestLabel": args.nearest_label,
        "nearestSlot": args.nearest_slot,
        "nearestNote": args.nearest_note,
        "hero": args.hero,
        "about": args.about,
        "routeNote": args.route_note,
        "galleryLabel": args.gallery_label,
        "gallery": gallery,
        "aiExample": args.ai_example,
        "proof": [
            {"icon": "shield", "title": "Цена заранее", "text": "Согласуем до начала работ"},
            {"icon": "camera", "title": "Фотоотчёт", "text": "Фиксируем результат"},
            {"icon": "clock", "title": "По записи", "text": "Без ожидания в очереди"},
        ],
        "slots": ["10:00", "11:30", "13:00", "15:30", "17:00", "19:00"],
        "services": services,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--company", required=True)
    p.add_argument("--slug", default="")
    p.add_argument("--short-name", default="")
    p.add_argument("--logo-mark", default="")
    p.add_argument("--brand-line", default="online booking")
    p.add_argument("--category", default="Автосервис")
    p.add_argument("--city", default="")
    p.add_argument("--phone", default="")
    p.add_argument("--address", default="")
    p.add_argument("--hours", default="09:00–21:00")
    p.add_argument("--status", default="Открыто сегодня")
    p.add_argument("--rating", default="4.9")
    p.add_argument("--reviews-label", default="по отзывам клиентов")
    p.add_argument("--accent", default="#C9FF3D")
    p.add_argument("--accent-secondary", default="")
    p.add_argument("--hero", default="https://images.unsplash.com/photo-1487754180451-c456f719a1fc?auto=format&fit=crop&w=1400&q=88")
    p.add_argument("--headline", default="")
    p.add_argument("--subheadline", default="")
    p.add_argument("--nearest-label", default="Сегодня")
    p.add_argument("--nearest-slot", default="19:00")
    p.add_argument("--nearest-note", default="Подтверждение записи за минуту")
    p.add_argument("--about", default="")
    p.add_argument("--route-note", default="Построить маршрут")
    p.add_argument("--gallery-label", default="последние работы")
    p.add_argument("--ai-example", default="Хочу записаться завтра вечером")
    p.add_argument("--gallery", action="append", default=[])
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
        "gallery": len(cfg["gallery"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
