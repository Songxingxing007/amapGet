import re

PREFIXES = ("广东省", "广东", "广州市", "广州")
PAREN_RE = re.compile(r"（([^）]*)）|\(([^)]*)\)")
KEEP_PAREN_TOKENS = ("地铁", "公交", "停车", "游客中心", "驿站", "售票", "派出所", "管理处", "充电", "餐厅", "商店", "酒店")


def normalize_name(value: str) -> str:
    # Bracketed access points such as (南门) are noise; facility qualifiers such as
    # (地铁站) must stay, otherwise a station ranks as the park itself.
    def _replace(match: re.Match) -> str:
        inner = (match.group(1) or match.group(2) or "").strip()
        if any(token in inner for token in KEEP_PAREN_TOKENS):
            return inner
        return ""
    text = PAREN_RE.sub(_replace, value or "")
    text = re.sub(r"\s+", "", text)
    for prefix in PREFIXES:
        if text.startswith(prefix) and len(text) > len(prefix) + 1:
            return text[len(prefix):]
    return text


def classify_match(query: str, poi_name: str) -> str:
    left = normalize_name(query)
    right = normalize_name(poi_name)
    if not left or not right:
        return "weak"
    if left == right:
        return "exact"
    if left in right or right in left:
        return "contains"
    return "weak"
