from app.services.amap_errors import classify, message


def test_classify_buckets():
    assert classify("10000") == "ok"
    assert classify("10001") == "key_invalid"
    assert classify("10012") == "insufficient_privileges"
    assert classify("10044") == "quota_exhausted"
    assert classify("10003") == "quota_exhausted"
    assert classify("10014") == "rate_limited"
    assert classify("10015") == "rate_limited"
    assert classify("10021") == "retryable"
    assert classify("99999") == "fatal"
    assert classify("") == "fatal"


def test_messages_are_human_readable():
    assert "工单" in message("insufficient_privileges")
    assert "配额" in message("quota_exhausted")
