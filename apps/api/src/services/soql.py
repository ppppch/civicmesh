from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class DatasetSchema:
    dataset_id: str
    columns: list[dict[str, str]]


class SoqlClient:
    def __init__(self, domain: str, app_token: str | None = None, timeout_seconds: int = 20) -> None:
        self.domain = domain
        self.app_token = app_token
        self.timeout_seconds = timeout_seconds

    def fetch_schema(self, dataset_id: str) -> DatasetSchema:
        headers: dict[str, str] = {}
        if self.app_token:
            headers["X-App-Token"] = self.app_token

        url = f"https://{self.domain}/api/views/{dataset_id}.json"
        with httpx.Client(timeout=self.timeout_seconds, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()

        raw_columns = payload.get("columns", [])
        columns = [
            {
                "name": (c.get("fieldName") or "").strip(),
                "display_name": (c.get("name") or "").strip(),
                "data_type": (c.get("dataTypeName") or "").strip().lower(),
            }
            for c in raw_columns
            if (c.get("fieldName") or "").strip()
        ]

        return DatasetSchema(dataset_id=dataset_id, columns=columns)

    def query(self, dataset_id: str, soql_params: dict[str, str]) -> list[dict[str, Any]]:
        headers: dict[str, str] = {}
        if self.app_token:
            headers["X-App-Token"] = self.app_token

        endpoint = f"https://{self.domain}/resource/{dataset_id}.json"
        with httpx.Client(timeout=self.timeout_seconds, headers=headers) as client:
            response = client.get(endpoint, params=soql_params)
            response.raise_for_status()
            payload = response.json()

        if isinstance(payload, list):
            return payload
        return []


def sanitize_identifier(column_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "", column_name)
