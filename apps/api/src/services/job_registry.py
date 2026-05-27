from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    title: str
    objective: str
    required_roles: dict[str, list[str]]
    output_fields: list[str]


MVP_JOB_SPECS: dict[str, JobSpec] = {
    "heat-vulnerability-zones": JobSpec(
        job_id="heat-vulnerability-zones",
        title="Heat Vulnerability Zones",
        objective="Identify areas where heat complaints are increasing and likely risk factors are elevated.",
        required_roles={
            "complaints": ["311", "heat", "hot water", "complaint"],
            "housing": ["housing", "building", "violations", "hpd"],
            "boundaries": ["community district", "borough", "boundaries"],
        },
        output_fields=["geography", "heat_signal", "housing_signal", "combined_risk_score"],
    ),
    "tree-canopy-equity": JobSpec(
        job_id="tree-canopy-equity",
        title="Tree Canopy Equity",
        objective="Surface geographies with low tree indicators alongside elevated heat-related burden.",
        required_roles={
            "trees": ["tree", "census", "canopy"],
            "complaints": ["311", "heat", "hot water"],
            "boundaries": ["community district", "borough", "boundaries"],
        },
        output_fields=["geography", "tree_signal", "heat_signal", "equity_gap_score"],
    ),
    "housing-violations-near-schools": JobSpec(
        job_id="housing-violations-near-schools",
        title="Housing Violations Near Schools",
        objective="Quantify housing-related risk signals in areas associated with schools.",
        required_roles={
            "violations": ["housing", "violation", "hpd"],
            "schools": ["school", "location", "education"],
            "boundaries": ["community district", "borough", "boundaries"],
        },
        output_fields=["geography", "violation_signal", "school_signal", "proximity_risk_score"],
    ),
    "transit-accessibility-score": JobSpec(
        job_id="transit-accessibility-score",
        title="Transit Accessibility Score",
        objective="Estimate differences in transit accessibility proxies across NYC geographies.",
        required_roles={
            "transit": ["subway", "bus", "mta", "transit"],
            "health": ["health", "hospital", "outcome"],
            "boundaries": ["community district", "borough", "boundaries"],
        },
        output_fields=["geography", "transit_signal", "health_signal", "accessibility_score"],
    ),
    "health-environment-risk": JobSpec(
        job_id="health-environment-risk",
        title="Health Outcomes vs Environmental Hazard Proxies",
        objective="Compare environmental stress indicators with health burden proxies by geography.",
        required_roles={
            "health": ["health", "hospital", "asthma", "outcome"],
            "environment": ["air quality", "pollution", "environment", "hazard"],
            "boundaries": ["community district", "borough", "boundaries"],
        },
        output_fields=["geography", "environment_signal", "health_signal", "risk_alignment_score"],
    ),
}
