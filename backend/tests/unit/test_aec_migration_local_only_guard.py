"""Safety contract: AEC DDL verifier cannot target cloud or staging databases."""
from unittest.mock import patch

import pytest

from scripts.verify_aec_review_migrations import (
    main,
    require_disposable_database_url,
)


LOCAL = "postgresql://krafzen_ci:local_ci_only@127.0.0.1:5432/krafzen_ci"


def test_local_ci_postgresql_url_is_accepted_without_connecting():
    assert require_disposable_database_url(LOCAL) == LOCAL


@pytest.mark.parametrize("bad", [
    "",
    "postgresql://postgres:secret@127.0.0.1:5432/postgres",
    "postgresql://krafzen_ci:local_ci_only@db.example.com:5432/krafzen_ci",
    "postgresql://krafzen_ci:local_ci_only@db.remote.supabase.co:5432/krafzen_ci",
    "postgresql://krafzen_ci:local_ci_only@127.0.0.1:5433/krafzen_ci",
    "postgresql://krafzen_ci:local_ci_only@127.0.0.1/krafzen_ci",
    "postgresql://krafzen_ci:local_ci_only@127.0.0.1:5432/postgres",
    "postgresql://krafzen_ci:local_ci_only@127.0.0.1:5432/krafzen_ci?host=remote.example.com",
    "postgresql://krafzen_ci:local_ci_only@127.0.0.1:5432/krafzen_ci?hostaddr=203.0.113.25",
    "postgresql://krafzen_ci:local_ci_only@127.0.0.1:5432/krafzen_ci#remote",
    "postgresql:///krafzen_ci?host=/var/run/postgresql",
])
def test_remote_or_redirected_url_is_rejected_before_connect(bad):
    with patch("scripts.verify_aec_review_migrations.psycopg2.connect") as connect:
        with pytest.raises(RuntimeError, match="disposable local CI"):
            with patch.dict("os.environ", {"DATABASE_URL": bad}):
                main()
        connect.assert_not_called()
