from dedupe import normalize_email, normalize_phone


def test_phone_formats():
    assert normalize_phone("(202) 555-0101") == normalize_phone("202.555.0101") == "2025550101"


def test_phone_country_code():
    assert normalize_phone("+1 202 555 0101") == "2025550101"


def test_email_case_and_space():
    assert normalize_email("  Ada.Moreno@Example.COM ") == "ada.moreno@example.com"


def test_gmail_dots_and_tags():
    assert normalize_email("a.da.moreno@gmail.com") == normalize_email("adamoreno+crm@gmail.com")
