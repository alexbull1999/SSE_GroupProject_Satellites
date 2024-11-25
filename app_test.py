from app import process_query


def test_knows_about_moon():
    assert process_query("moon") == "Moon made of cheese"
