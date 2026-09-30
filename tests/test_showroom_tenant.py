from argparse import Namespace

from scripts.showroom_tenant import build_config, parse_service, slugify


def test_slugify_is_stable_for_demo_paths():
    assert slugify("GRAPHITE Detailing") == "graphite-detailing"
    assert slugify("  abc---auto  ") == "abc-auto"


def test_service_parser():
    service = parse_service("Замена масла|50 мин|2500 ₽|без стоимости масла", 2)
    assert service["id"] == "service-2"
    assert service["name"] == "Замена масла"
    assert service["price"] == 2500
    assert service["note"] == "без стоимости масла"


def test_config_is_a_rebrandable_preview():
    args = Namespace(
        slug="demo",
        company="Demo Auto",
        short_name="DEMO",
        category="Автосервис · Москва",
        phone="+79990000000",
        address="Москва",
        hours="09:00–21:00",
        rating="4.9",
        reviews_label="100 отзывов",
        accent="#c6ff38",
        hero="https://example.com/hero.jpg",
        headline="Запись без звонка",
        subheadline="Выберите время",
        ai_example="Нужна диагностика",
        service=["Диагностика|45 мин|1800|ходовая"],
    )
    cfg = build_config(args)
    assert cfg["slug"] == "demo"
    assert cfg["name"] == "Demo Auto"
    assert cfg["services"][0]["price"] == 1800
    assert cfg["hero"] == "https://example.com/hero.jpg"
