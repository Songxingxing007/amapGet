from app.services.matching import classify_match, normalize_name


def test_match_levels():
    assert classify_match("越秀公园", "越秀公园") == "exact"
    assert classify_match("越秀公园", "广州越秀公园(南门)") == "exact"
    assert classify_match("越秀公园", "广州越秀公园东门") == "contains"
    assert classify_match("广东流溪河国家森林自然公园", "流溪河国家森林公园") == "weak"
    assert classify_match("越秀公园", "越秀公园(地铁站)") == "contains"
    assert classify_match("天河公园", "天河公园地铁站") == "contains"
    assert classify_match("云台花园", "广州文化公园") == "weak"


def test_normalize_strips_prefix_and_brackets():
    assert normalize_name("广州市越秀公园（南门）") == "越秀公园"
    assert normalize_name("广东省石门国家森林公园") == "石门国家森林公园"
    assert normalize_name("广州塔") == "广州塔"
