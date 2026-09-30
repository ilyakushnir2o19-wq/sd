from argparse import Namespace

from scripts.showroom_tenant import build_config, parse_gallery, parse_service, slugify


def test_slugify_is_stable_for_demo_paths():
    assert slugify("GRAPHITE Detailing") == "graphite-detailing"
    assert slugify("  abc---auto  ") == "abc-auto"


def test_service_parser_supports_image():
    service = parse_service(
        "Замена масла|50 мин|2500 ₽|без стоимости масла|https://example.com/oil.jpg",
        2,
    )
    assert service["id"] == "service-2"
    assert service["name"] == "Замена масла"
    assert service["price"] == 2500
    assert service["note"] == "без стоимости масла"
    assert service["image"] == "https://example.com/oil.jpg"


def test_gallery_parser():
    shot = parse_gallery("https://example.com/work.jpg|BMW X5|полировка", 1)
    assert shot == {
        "src": "https://example.com/work.jpg",
        "title": "BMW X5",
        "meta": "полировка",
    }


def test_config_is_a_rebrandable_premium_preview():
    args = Namespace(
        slug="demo",
        company="Demo Auto",
        short_name="DEMO",
        logo_mark="D",
        brand_line="garage & service",
        category="Автосервис · Москва",
        city="Москва",
        phone="+79990000000",
        address="Москва",
        hours="09:00–21:00",
        status="Открыто до 21:00",
        rating="4.9",
        reviews_label="100 отзывов",
        accent="#C9FF3D",
        accent_secondary="#83FF74",
        hero="https://example.com/hero.jpg",
        headline="Запись без звонка",
        subheadline="Выберите время",
        nearest_label="Сегодня",
        nearest_slot="19:00",
        nearest_note="Можно сегодня",
        about="Городской автосервис.",
        route_note="10 минут от центра",
        gallery_label="последние работы",
        ai_example="Нужна диагностика",
        gallery=["https://example.com/work.jpg|BMW X5|полировка"],
        service=["Диагностика|45 мин|1800|ходовая|https://example.com/service.jpg"],
    )
    cfg = build_config(args)
    assert cfg["slug"] == "demo"
    assert cfg["name"] == "Demo Auto"
    assert cfg["logoMark"] == "D"
    assert cfg["nearestSlot"] == "19:00"
    assert cfg["services"][0]["price"] == 1800
    assert cfg["services"][0]["image"] == "https://example.com/service.jpg"
    assert cfg["gallery"][0]["title"] == "BMW X5"
    assert cfg["hero"] == "https://example.com/hero.jpg"
