import json

from src.logging_utils import build_error_response


def test_build_error_response_includes_error_and_message():
    payload = build_error_response(RuntimeError("quota exceeded"))
    decoded = json.loads(payload)

    assert decoded["error"] == "RuntimeError"
    assert decoded["message"] == "quota exceeded"
