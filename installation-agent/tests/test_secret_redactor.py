from app.services.security.secret_redactor import (
    collect_secrets,
    evaluate_variable,
    is_sensitive_name,
    redact_text,
)


def test_detects_variable_by_name():
    entry = evaluate_variable("DATABASE_HOST", "localhost", "app.env")
    assert entry["name"] == "DATABASE_HOST"
    assert entry["file"] == "app.env"
    assert entry["sensitivity"] == "NONE"
    assert entry["sensitive"] is False
    assert entry["value"] == "localhost"


def test_secret_value_never_returned_raw():
    entry = evaluate_variable("API_TOKEN", "secret-value", ".env")
    assert entry["sensitive"] is True
    assert "value" not in entry
    assert entry["value_redacted"] == "********"
    assert "secret-value" not in str(entry)


def test_secret_fingerprint_is_not_reversible():
    entry = evaluate_variable("API_TOKEN", "secret-value", ".env")
    assert entry["value_fingerprint"] != "secret-value"
    assert len(entry["value_fingerprint"]) == 12


def test_collect_secrets_filters_only_sensitive_entries():
    variables = [
        evaluate_variable("APP_NAME", "myapp", "config.yml"),
        evaluate_variable("API_TOKEN", "abcdef123456789", ".env"),
        evaluate_variable("PASSWORD", "hunter2", ".env"),
    ]
    secrets = collect_secrets(variables)
    names = {s["name"] for s in secrets}
    assert names == {"API_TOKEN", "PASSWORD"}
    for secret in secrets:
        assert "value" not in secret
        assert secret["value_redacted"] == "********"


def test_placeholder_secret_value_is_shown_but_not_a_real_leak():
    # A sensitive-named variable with an empty/placeholder value carries no
    # real secret, so it is safe to surface for debugging.
    entry = evaluate_variable("API_TOKEN", "", ".env.example")
    assert entry["sensitivity"] == "LOW"
    assert entry["value_redacted"] == "(empty)"


def test_value_shaped_like_secret_detected_even_with_generic_name():
    entry = evaluate_variable("HEADER_VALUE", "Bearer abcd1234efgh5678", "install.sh")
    assert entry["sensitive"] is True
    assert entry["category"] == "bearer_token"
    assert "value" not in entry


def test_credentials_embedded_in_url_are_flagged():
    entry = evaluate_variable(
        "DATABASE_URL", "postgresql://user:hunter2@db-host:5432/app", "application.yml"
    )
    assert entry["sensitive"] is True
    assert "hunter2" not in str(entry)


def test_is_sensitive_name():
    assert is_sensitive_name("API_TOKEN")
    assert is_sensitive_name("client_secret")
    assert not is_sensitive_name("PORT")


def test_redact_text_masks_embedded_secrets_in_free_text():
    message = "Invalid config: Bearer abcd1234efgh5678 rejected by upstream"
    redacted = redact_text(message)
    assert "abcd1234efgh5678" not in redacted
    assert "[REDACTED]" in redacted
