"""2GIS bridge tests (offline)."""

from apps.api.services.leadgen.twogis import normalize_2gis_row, normalize_2gis_rows


def test_normalize_raw_2gis_row_to_hunter_fields():
    raw = {
        "id": "2gis-123",
        "name_ex": {"primary": "Acme Distribution"},
        "address_name": "1 Test Street",
        "reviews": {"general_rating": 4.8, "general_review_count": 42},
        "rubrics": [{"name": "Оптовая компания"}, {"name": "Дистрибьютор"}],
        "contact_groups": [{
            "contacts": [
                {"type": "phone", "text": "+7 495 000-00-00"},
                {"type": "phone", "text": "+7 495 111-11-11"},
                {"type": "email", "text": "sales@acme.ru"},
                {"type": "website", "text": "acme.ru"},
                {"type": "website", "text": "Перейти в Telegram-канал"},
                {"type": "telegram", "url": "https://t.me/acme"},
                {"type": "whatsapp", "url": "https://wa.me/79990000000"},
            ]
        }],
    }

    row = normalize_2gis_row(
        raw,
        city="moscow",
        discovery_url="https://2gis.ru/moscow/search/test",
    )

    assert row["company"] == "Acme Distribution"
    assert row["website"] == "acme.ru"
    assert row["phone"] == "+7 495 000-00-00"
    assert row["secondary_phones"] == "+7 495 111-11-11"
    assert row["email"] == "sales@acme.ru"
    assert row["address"] == "1 Test Street"
    assert row["city"] == "moscow"
    assert row["source"] == "2gis"
    assert row["source_url"] == "https://2gis.ru/moscow/search/test"
    assert row["specialization"] == "Оптовая компания, Дистрибьютор"
    assert row["2gis_rating"] == 4.8
    assert row["2gis_reviews"] == 42
    assert row["2gis_id"] == "2gis-123"
    assert row["telegram"] == ["https://t.me/acme"]
    assert row["whatsapp"] == ["https://wa.me/79990000000"]


def test_normalize_accepts_existing_slim_artifact():
    slim = {
        "2gis_id": "abc",
        "name": "Slim Co",
        "address": "Somewhere",
        "rating": 5,
        "reviews": 8,
        "phone": ["+7 900 000-00-00"],
        "whatsapp": ["https://wa.me/79000000000"],
        "telegram": ["https://t.me/slim"],
        "email": [],
        "website": ["slim.example", "Перейти в Telegram-канал"],
        "rubrics": ["Рыба и морепродукты"],
    }

    row = normalize_2gis_row(slim, city="moscow")
    assert row["company"] == "Slim Co"
    assert row["website"] == "slim.example"
    assert row["phone"] == "+7 900 000-00-00"
    assert row["specialization"] == "Рыба и морепродукты"
    assert row["2gis_reviews"] == 8


def test_social_links_are_not_mistaken_for_company_website():
    row = normalize_2gis_row({
        "name": "Social Only",
        "website": [
            "https://t.me/socialonly",
            "https://wa.me/79990000000",
            "Перейти в Telegram-канал",
        ],
    })
    assert "website" not in row


def test_batch_dedupes_by_domain_then_company():
    rows = normalize_2gis_rows([
        {"name": "Acme", "website": ["https://www.acme.ru/path"]},
        {"name": "Acme Branch", "website": ["acme.ru"]},
        {"name": "No Site"},
        {"name": " no site "},
        {"name": "", "website": []},
    ])
    assert len(rows) == 2
    assert rows[0]["company"] == "Acme"
    assert rows[1]["company"] == "No Site"


def test_identity_less_rows_are_dropped():
    assert normalize_2gis_rows([{}, {"address": "nowhere"}]) == []
