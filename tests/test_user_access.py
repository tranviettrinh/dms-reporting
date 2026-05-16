import pytest

from dms_reporting.reporting import ALL_REPORT_IDS
from dms_reporting.user_access import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME, UserStore


def test_user_store_bootstraps_default_admin(tmp_path):
    user_store = UserStore(tmp_path / "users.json")

    admin_account = user_store.authenticate(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)

    assert user_store.default_admin_created
    assert admin_account is not None
    assert admin_account.is_admin
    assert admin_account.accessible_reports == ALL_REPORT_IDS


def test_user_store_saves_and_reloads_report_permissions(tmp_path):
    settings_path = tmp_path / "users.json"
    user_store = UserStore(settings_path)
    user_store.save_user(
        username="sales-user",
        role="user",
        allowed_reports=("summary", "invoice-territory"),
        password="secret123",
    )

    reloaded_store = UserStore(settings_path)
    reloaded_account = reloaded_store.authenticate("sales-user", "secret123")

    assert reloaded_account is not None
    assert not reloaded_account.is_admin
    assert reloaded_account.accessible_reports == ("summary", "invoice-territory")


def test_user_store_collapses_legacy_territory_permissions_into_invoice_territory(tmp_path):
    settings_path = tmp_path / "users.json"
    user_store = UserStore(settings_path)
    user_store.save_user(
        username="sales-user",
        role="user",
        allowed_reports=("correct-territory", "inactive-customer"),
        password="secret123",
    )

    reloaded_store = UserStore(settings_path)
    reloaded_account = reloaded_store.authenticate("sales-user", "secret123")

    assert reloaded_account is not None
    assert reloaded_account.accessible_reports == ("invoice-territory",)


def test_user_store_preserves_password_when_updating_without_new_password(tmp_path):
    settings_path = tmp_path / "users.json"
    user_store = UserStore(settings_path)
    user_store.save_user(
        username="sales-user",
        role="user",
        allowed_reports=("summary",),
        password="secret123",
    )

    user_store.save_user(
        username="sales-user",
        role="user",
        allowed_reports=("summary", "detail"),
    )

    account = user_store.authenticate("sales-user", "secret123")

    assert account is not None
    assert account.accessible_reports == ("summary", "detail")


def test_user_store_requires_at_least_one_admin(tmp_path):
    user_store = UserStore(tmp_path / "users.json")

    with pytest.raises(ValueError, match="ít nhất một tài khoản admin"):
        user_store.delete_user(DEFAULT_ADMIN_USERNAME)
