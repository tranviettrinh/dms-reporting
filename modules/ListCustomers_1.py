from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests


@dataclass(slots=True)
class MisaCRMClient:
    client_id: str
    client_secret: str
    base_url: str = "https://crmconnect.misa.vn/api/v2"

    @classmethod
    def from_env(cls) -> "MisaCRMClient":
        client_id = os.getenv("MISA_CLIENT_ID")
        client_secret = os.getenv("MISA_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("Missing MISA_CLIENT_ID or MISA_CLIENT_SECRET environment variables")
        return cls(client_id=client_id, client_secret=client_secret)

    def authenticate(self) -> str:
        response = requests.post(
            f"{self.base_url}/Account",
            json={"client_id": self.client_id, "client_secret": self.client_secret},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success") or "data" not in payload:
            raise RuntimeError("CRM authentication failed")
        return payload["data"]

    def fetch_customers(self, *, page_size: int = 100) -> pd.DataFrame:
        token = self.authenticate()
        page = 1
        rows: list[dict[str, Any]] = []

        while True:
            response = requests.get(
                f"{self.base_url}/Customers",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Clientid": self.client_id,
                    "Content-Type": "application/json",
                },
                params={"page": page, "pageSize": page_size, "isDescending": True},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("success") is not True or payload.get("code") != 200:
                break

            records = payload.get("data", [])
            if not records:
                break

            for record in records:
                rows.append(
                    {
                        "Mã khách hàng": record.get("account_number"),
                        "Tên khách hàng": record.get("account_name"),
                        "Loại khách hàng": record.get("account_type"),
                        "Ngày ký hợp đồng": record.get("custom_field14"),
                        "Điện thoại": record.get("office_tel"),
                        "Số nhà, Đường phố (Giao hàng)": record.get("shipping_street"),
                        "Phường/Xã (Giao hàng)": record.get("shipping_ward"),
                        "Quận/Huyện (Giao hàng)": record.get("shipping_district"),
                        "Tỉnh/Thành phố (Giao hàng)": record.get("shipping_province"),
                        "Chủ sở hữu": record.get("owner_name"),
                    }
                )
            page += 1

        return pd.DataFrame(rows)
