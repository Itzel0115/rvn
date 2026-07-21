from observability.redaction import redact_mapping,redact_text

def test_default_capture_hashes_and_redacts_sensitive_values():
    value=redact_mapping({"api_key":"secret","prompt":"hello"})
    assert value["api_key"]=="<redacted>" and "hello" not in str(value)
    assert "/tmp/private" not in redact_text("failure /tmp/private")
