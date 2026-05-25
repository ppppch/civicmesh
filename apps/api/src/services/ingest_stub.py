from dataclasses import dataclass


@dataclass
class IngestRunSummary:
    datasets_scanned: int
    datasets_selected: int
    status: str


def run_catalog_selection(limit: int = 200) -> IngestRunSummary:
    # Placeholder until Socrata discovery integration is added.
    selected = min(limit, 100)
    return IngestRunSummary(
        datasets_scanned=limit,
        datasets_selected=selected,
        status="stubbed",
    )
