"""Config tests — covers the dotenv loader (ARB M1b)."""

from pathlib import Path

import pytest

from footballiq.infrastructure.config import load_settings


def test_dotenv_loaded_without_overriding_real_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment line\n"
        "FIQ_DATA_DIR=from_dotenv\n"
        "FIQ_API_KEY_HASHES=aaa, bbb ,\n"
        "not_a_kv_line\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("FIQ_DATA_DIR", raising=False)
    monkeypatch.delenv("FIQ_API_KEY_HASHES", raising=False)
    monkeypatch.setenv("FIQ_DATABASE_URL", "sqlite://real-env-wins")

    settings = load_settings(dotenv_path=env_file)

    assert settings.data_dir == Path("from_dotenv")
    assert settings.api_key_hashes == ("aaa", "bbb")
    assert settings.database_url == "sqlite://real-env-wins"  # real env never overridden


def test_missing_dotenv_uses_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for var in ("FIQ_DATABASE_URL", "FIQ_DATA_DIR", "FIQ_API_KEY_HASHES"):
        monkeypatch.delenv(var, raising=False)

    settings = load_settings(dotenv_path=tmp_path / "absent.env")

    assert settings.data_dir == Path("data/raw")
    assert settings.api_key_hashes == ()
    assert "postgresql" in settings.database_url
