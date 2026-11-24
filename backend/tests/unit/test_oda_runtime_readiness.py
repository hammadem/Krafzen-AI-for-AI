"""Regression tests for incomplete ODA installations.

These tests do not assert successful conversion with a real licensed ODA bundle.
"""
from unittest.mock import patch

from app.services import oda_bundle


def test_resolver_rejects_binary_after_failed_runtime_bootstrap(tmp_path):
    with patch.object(oda_bundle, "backend_root", return_value=tmp_path), \
         patch.object(oda_bundle, "ensure_oda_bundle", return_value=False), \
         patch.object(oda_bundle, "_read_bundle", return_value=("/old/ODAFileConverter", None, None)) as read:
        assert oda_bundle.resolve_bundled_oda() == (None, None)
        read.assert_not_called()


def test_resolver_rejects_missing_qt_plugins_even_if_binary_is_executable(tmp_path):
    executable = tmp_path / "ODAFileConverter"
    executable.write_bytes(b"test-only")
    executable.chmod(0o755)
    with patch.object(oda_bundle, "backend_root", return_value=tmp_path), \
         patch.object(oda_bundle, "ensure_oda_bundle", return_value=True), \
         patch.object(oda_bundle, "_repair_bundle_manifest"), \
         patch.object(oda_bundle, "_read_bundle", return_value=(str(executable), None, None)), \
         patch.object(oda_bundle, "ensure_headless_qt_plugins", return_value=False):
        assert oda_bundle.resolve_bundled_oda() == (None, None)


def test_resolver_accepts_configured_bundle_only_with_runtime_prerequisites(tmp_path):
    executable = tmp_path / "ODAFileConverter"
    executable.write_bytes(b"test-only")
    executable.chmod(0o755)
    with patch.object(oda_bundle, "backend_root", return_value=tmp_path), \
         patch.object(oda_bundle, "ensure_oda_bundle", return_value=True), \
         patch.object(oda_bundle, "_repair_bundle_manifest"), \
         patch.object(oda_bundle, "_read_bundle", return_value=(str(executable), "/lib/oda", "/qt/platforms")), \
         patch.object(oda_bundle, "ensure_headless_qt_plugins", return_value=True):
        assert oda_bundle.resolve_bundled_oda() == (str(executable), "/lib/oda")
