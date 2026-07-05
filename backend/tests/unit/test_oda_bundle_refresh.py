from unittest.mock import patch

from app.services import oda_bundle


def test_incomplete_bundle_requires_refresh_source(tmp_path, monkeypatch):
    executable = tmp_path / ".oda_bundle" / "ODAFileConverter"
    executable.parent.mkdir()
    executable.write_bytes(b"binary")
    monkeypatch.setattr(oda_bundle, "backend_root", lambda: tmp_path)
    monkeypatch.setattr(oda_bundle.settings, "DWG_ODA_DEB_URL", "")

    with (
        patch.object(oda_bundle, "_read_bundle", return_value=(str(executable), None, None)),
        patch.object(oda_bundle, "ensure_headless_qt_plugins", return_value=False),
        patch.object(oda_bundle, "_r2_download_config", return_value=None),
    ):
        assert oda_bundle._ensure_oda_bundle_locked() is False
        assert "missing compatible Qt platform plugins" in (oda_bundle.get_last_oda_error() or "")


def test_incomplete_bundle_refreshes_when_source_is_configured(tmp_path, monkeypatch):
    executable = tmp_path / ".oda_bundle" / "ODAFileConverter"
    executable.parent.mkdir()
    executable.write_bytes(b"binary")
    monkeypatch.setattr(oda_bundle, "backend_root", lambda: tmp_path)
    monkeypatch.setattr(oda_bundle.settings, "DWG_ODA_DEB_URL", "https://example.com/oda.deb")

    with (
        patch.object(oda_bundle, "_read_bundle", return_value=(str(executable), None, None)),
        patch.object(oda_bundle, "ensure_headless_qt_plugins", return_value=False),
        patch.object(oda_bundle, "_r2_download_config", return_value=None),
        patch.object(oda_bundle, "_download_oda_deb", side_effect=RuntimeError("refresh attempted")),
    ):
        assert oda_bundle._ensure_oda_bundle_locked() is False
        assert oda_bundle.get_last_oda_error() == "refresh attempted"
