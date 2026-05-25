from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx


@dataclass
class SocrataDataset:
    dataset_id: str
    title: str
    description: str
    agency_name: str
    category: str
    tags: list[str]
    rows_count: int
    columns_count: int
    source_url: str
    created_at: datetime | None
    updated_at: datetime | None


class SocrataClient:
    def __init__(self, domain: str, app_token: str | None = None, timeout_seconds: int = 20) -> None:
        self.domain = domain
        self.app_token = app_token
        self.timeout_seconds = timeout_seconds

    def fetch_catalog(self, limit: int = 200, offset: int = 0) -> list[SocrataDataset]:
        headers: dict[str, str] = {}
        if self.app_token:
            headers["X-App-Token"] = self.app_token

        params = {
            "domains": self.domain,
            "only": "datasets",
            "limit": limit,
            "offset": offset,
            "order": "dataset",
        }

        with httpx.Client(timeout=self.timeout_seconds, headers=headers) as client:
            response = client.get("https://api.us.socrata.com/api/catalog/v1", params=params)
            response.raise_for_status()
            payload = response.json()

        results = payload.get("results", [])
        datasets: list[SocrataDataset] = []
        for item in results:
            resource = item.get("resource", {})
            metadata = item.get("metadata", {})
            classification = metadata.get("classification", {})

            dataset_id = resource.get("id")
            title = resource.get("name")
            if not dataset_id or not title:
                continue

            columns = resource.get("columns_name", [])
            tags = classification.get("tags", []) or []
            description = resource.get("description", "") or ""
            agency_name = item.get("metadata", {}).get("custom_fields", {}).get("Dataset Information", {}).get(
                "Agency", "Unknown"
            )
            category = classification.get("domain_category", "Other") or "Other"
            rows_count = int(resource.get("count", 0) or 0)
            columns_count = len(columns)
            source_url = f"https://{self.domain}/resource/{dataset_id}.json"

            datasets.append(
                SocrataDataset(
                    dataset_id=dataset_id,
                    title=title,
                    description=description,
                    agency_name=agency_name,
                    category=category,
                    tags=[str(tag).strip().lower() for tag in tags if str(tag).strip()],
                    rows_count=rows_count,
                    columns_count=columns_count,
                    source_url=source_url,
                    created_at=_safe_parse_dt(resource.get("createdAt")),
                    updated_at=_safe_parse_dt(resource.get("updatedAt")),
                )
            )

        return datasets


def _safe_parse_dt(raw: int | str | None) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, int):
        # Socrata catalog often returns epoch seconds.
        return datetime.fromtimestamp(raw, tz=UTC)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
