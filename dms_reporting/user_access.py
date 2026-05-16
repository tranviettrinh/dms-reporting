from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from pathlib import Path

from dms_reporting.app_info import get_app_support_dir
from dms_reporting.reporting import ALL_REPORT_IDS, collapse_report_ids, normalize_report_ids

USER_SETTINGS_NAME = "users.json"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
PBKDF2_ITERATIONS = 200_000


def get_user_settings_path() -> Path:
    return get_app_support_dir() / USER_SETTINGS_NAME


@dataclass(frozen=True, slots=True)
class UserAccount:
    username: str
    role: str
    allowed_reports: tuple[str, ...]
    password_salt: str
    password_hash: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def accessible_reports(self) -> tuple[str, ...]:
        if self.is_admin:
            return ALL_REPORT_IDS
        return tuple(report_id for report_id in collapse_report_ids(self.allowed_reports) if report_id in ALL_REPORT_IDS)


class UserStore:
    def __init__(self, settings_path: Path | None = None) -> None:
        self.settings_path = settings_path or get_user_settings_path()
        self.default_admin_created = False
        self._accounts = self._load_accounts()

    def list_users(self) -> list[UserAccount]:
        return sorted(
            self._accounts.values(),
            key=lambda account: (not account.is_admin, account.username.lower()),
        )

    def get_user(self, username: str) -> UserAccount | None:
        return self._accounts.get(username.strip())

    def authenticate(self, username: str, password: str) -> UserAccount | None:
        account = self.get_user(username)
        if account is None:
            return None
        if not _verify_password(password, account.password_salt, account.password_hash):
            return None
        return account

    def save_user(
        self,
        *,
        username: str,
        role: str,
        allowed_reports: tuple[str, ...] | list[str],
        password: str | None = None,
    ) -> UserAccount:
        cleaned_username = username.strip()
        if not cleaned_username:
            raise ValueError("Tên đăng nhập không được để trống.")
        if any(character.isspace() for character in cleaned_username):
            raise ValueError("Tên đăng nhập không được chứa khoảng trắng.")

        normalized_role = role.strip().lower()
        if normalized_role not in {"admin", "user"}:
            raise ValueError("Vai trò tài khoản chỉ hỗ trợ admin hoặc user.")

        normalized_reports = self._normalize_allowed_reports(normalized_role, allowed_reports)
        existing_account = self._accounts.get(cleaned_username)
        cleaned_password = (password or "").strip()

        if existing_account is None and not cleaned_password:
            raise ValueError("Cần nhập mật khẩu cho tài khoản mới.")

        if cleaned_password:
            password_salt = secrets.token_hex(16)
            password_hash = _hash_password(cleaned_password, password_salt)
        elif existing_account is not None:
            password_salt = existing_account.password_salt
            password_hash = existing_account.password_hash
        else:
            raise ValueError("Không thể tạo tài khoản mới khi thiếu mật khẩu.")

        account = UserAccount(
            username=cleaned_username,
            role=normalized_role,
            allowed_reports=normalized_reports,
            password_salt=password_salt,
            password_hash=password_hash,
        )

        updated_accounts = dict(self._accounts)
        updated_accounts[cleaned_username] = account
        self._ensure_has_admin(updated_accounts)
        self._accounts = updated_accounts
        self._persist()
        return account

    def delete_user(self, username: str) -> None:
        cleaned_username = username.strip()
        if cleaned_username not in self._accounts:
            raise ValueError(f"Không tìm thấy tài khoản: {cleaned_username}")

        updated_accounts = dict(self._accounts)
        del updated_accounts[cleaned_username]
        self._ensure_has_admin(updated_accounts)
        self._accounts = updated_accounts
        self._persist()

    def _load_accounts(self) -> dict[str, UserAccount]:
        if not self.settings_path.exists():
            accounts = {DEFAULT_ADMIN_USERNAME: _create_account(DEFAULT_ADMIN_USERNAME, "admin", ALL_REPORT_IDS, DEFAULT_ADMIN_PASSWORD)}
            self.default_admin_created = True
            self._persist_accounts(accounts)
            return accounts

        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Không thể đọc file tài khoản: {self.settings_path}") from exc

        raw_users = payload.get("users", [])
        if not isinstance(raw_users, list):
            raise ValueError("File tài khoản không hợp lệ: trường users phải là danh sách.")

        accounts: dict[str, UserAccount] = {}
        for raw_user in raw_users:
            if not isinstance(raw_user, dict):
                raise ValueError("File tài khoản không hợp lệ: mỗi user phải là object.")
            username = str(raw_user.get("username", "")).strip()
            role = str(raw_user.get("role", "")).strip().lower()
            password_salt = str(raw_user.get("password_salt", "")).strip()
            password_hash = str(raw_user.get("password_hash", "")).strip()
            if not username or not password_salt or not password_hash:
                raise ValueError("File tài khoản thiếu thông tin đăng nhập bắt buộc.")
            allowed_reports = raw_user.get("allowed_reports", [])
            account = UserAccount(
                username=username,
                role=role,
                allowed_reports=self._normalize_allowed_reports(role, allowed_reports),
                password_salt=password_salt,
                password_hash=password_hash,
            )
            accounts[username] = account

        if not accounts:
            accounts = {DEFAULT_ADMIN_USERNAME: _create_account(DEFAULT_ADMIN_USERNAME, "admin", ALL_REPORT_IDS, DEFAULT_ADMIN_PASSWORD)}
            self.default_admin_created = True
            self._persist_accounts(accounts)
            return accounts

        self._ensure_has_admin(accounts)
        return accounts

    def _normalize_allowed_reports(
        self,
        role: str,
        allowed_reports: tuple[str, ...] | list[str],
    ) -> tuple[str, ...]:
        if role == "admin":
            return ALL_REPORT_IDS

        normalized_reports = collapse_report_ids(normalize_report_ids(allowed_reports))
        if not normalized_reports:
            raise ValueError("Tài khoản user phải được cấp ít nhất một loại báo cáo.")
        return normalized_reports

    @staticmethod
    def _ensure_has_admin(accounts: dict[str, UserAccount]) -> None:
        if not any(account.is_admin for account in accounts.values()):
            raise ValueError("Hệ thống phải luôn có ít nhất một tài khoản admin.")

    def _persist(self) -> None:
        self._persist_accounts(self._accounts)

    def _persist_accounts(self, accounts: dict[str, UserAccount]) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "users": [
                {
                    "username": account.username,
                    "role": account.role,
                    "allowed_reports": list(account.allowed_reports),
                    "password_salt": account.password_salt,
                    "password_hash": account.password_hash,
                }
                for account in self.list_users_from(accounts)
            ]
        }
        temp_path = self.settings_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.settings_path)

    @staticmethod
    def list_users_from(accounts: dict[str, UserAccount]) -> list[UserAccount]:
        return sorted(
            accounts.values(),
            key=lambda account: (not account.is_admin, account.username.lower()),
        )


def _create_account(
    username: str,
    role: str,
    allowed_reports: tuple[str, ...] | list[str],
    password: str,
) -> UserAccount:
    password_salt = secrets.token_hex(16)
    return UserAccount(
        username=username,
        role=role,
        allowed_reports=ALL_REPORT_IDS if role == "admin" else collapse_report_ids(normalize_report_ids(allowed_reports)),
        password_salt=password_salt,
        password_hash=_hash_password(password, password_salt),
    )


def _hash_password(password: str, salt_hex: str) -> str:
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        PBKDF2_ITERATIONS,
    )
    return derived_key.hex()


def _verify_password(password: str, salt_hex: str, expected_hash: str) -> bool:
    return _hash_password(password, salt_hex) == expected_hash
