"""Amap infocode classification shared by every client call."""

OK = "10000"
KEY_INVALID = "10001"
INSUFFICIENT_PRIVILEGES = "10012"
DAILY_QUOTA = {"10003", "10044"}
RATE_LIMITED = {"10014", "10015"}
RETRYABLE = {"10016", "10017", "10018", "10019", "10020", "10021"}

MESSAGES = {
    "ok": "正常",
    "key_invalid": "Key 无效，请检查配置",
    "insufficient_privileges": "接口权限不足，AOI 边界查询需提工单开通",
    "quota_exhausted": "账号日调用配额已耗尽，请次日续跑",
    "rate_limited": "请求过快被限流，请降低 QPS 或稍后重试",
    "retryable": "临时错误，可重试",
    "fatal": "接口返回未知错误",
}


def classify(infocode: str) -> str:
    """Map an Amap infocode to an action bucket the pipeline can switch on."""
    code = (infocode or "").strip()
    if code == OK:
        return "ok"
    if code == KEY_INVALID:
        return "key_invalid"
    if code == INSUFFICIENT_PRIVILEGES:
        return "insufficient_privileges"
    if code in DAILY_QUOTA:
        return "quota_exhausted"
    if code in RATE_LIMITED:
        return "rate_limited"
    if code in RETRYABLE:
        return "retryable"
    return "fatal"


def message(bucket: str) -> str:
    return MESSAGES.get(bucket, MESSAGES["fatal"])
