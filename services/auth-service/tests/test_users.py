from __future__ import annotations

from auth_service.users import username_to_filename_digest


def test_filename_digest_deterministic():
    u = "analyst@example.com"
    a = username_to_filename_digest(u)
    b = username_to_filename_digest(u)
    assert a == b
    assert a.endswith(".json")
