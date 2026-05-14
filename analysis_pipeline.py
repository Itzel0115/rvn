from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analyzer import AnalysisArtifacts, analyze_data
from config import CHART_DIR, COL_GROUP_CODE, COL_GROUP_NAME, DATA_DIR, INVENTORY_FILE, MAPPING_FILE, OUTPUT_DIR, REVENUE_FILE
from data_loader import load_inventory, load_mapping_raw, load_real_data_sources, load_revenue
from logging_utils import get_logger
from mapping_parser import ParsedMapping, parse_mapping
from real_data import build_legacy_compatible_frames, build_real_analysis_tables
from utils import MessageCollector, ensure_directories


@dataclass
class PipelineContext:
    inventory_check: dict[str, list[str]]
    revenue_check: dict[str, list[str]]
    inventory_df: pd.DataFrame
    revenue_df: pd.DataFrame
    parsed_mapping: ParsedMapping
    artifacts: AnalysisArtifacts
    messages: MessageCollector
    supported_domains: dict[str, bool]
    source_files: dict[str, str]
    real_data_quality_report: dict | None = None


def build_pipeline_context(request_id: str) -> PipelineContext:
    logger = get_logger("analysis_pipeline", request_id, domain="pipeline")
    ensure_directories([DATA_DIR, OUTPUT_DIR, CHART_DIR])

    logger.info("Loading source files")
    logger.info("Using inventory file: %s", INVENTORY_FILE)
    logger.info("Using revenue file: %s", REVENUE_FILE)
    logger.info("Using mapping file: %s", MAPPING_FILE)

    messages = MessageCollector()
    real_inventory_df, real_revenue_df, real_source_metadata = load_real_data_sources(INVENTORY_FILE, REVENUE_FILE, messages)
    if not real_inventory_df.empty and not real_revenue_df.empty:
        logger.info("Loaded real data files by configured file path; building Phase 9A entity analysis tables")
        real_tables = build_real_analysis_tables(real_inventory_df, real_revenue_df, real_source_metadata)
        for message in real_tables.messages:
            messages.add_warning(message)

        frames = build_legacy_compatible_frames(real_tables)
        business_groups = sorted(
            set(real_inventory_df["business_group"].dropna().astype(str).tolist())
            | set(real_revenue_df["business_group"].dropna().astype(str).tolist())
        )
        business_group_mapping = pd.DataFrame(
            [{COL_GROUP_CODE: group, COL_GROUP_NAME: group} for group in business_groups]
        )
        parsed_mapping = ParsedMapping(
            raw_mapping=pd.DataFrame(),
            structured_mapping=business_group_mapping.copy(),
            business_group_mapping=business_group_mapping,
            inventory_hqbu_mapping=pd.DataFrame(),
            revenue_platform_mapping=pd.DataFrame(),
            anonymization_rules=pd.DataFrame(),
            bridge_candidates=pd.DataFrame(),
            mapping_success=True,
            warnings=real_tables.messages,
        )

        summary_metrics = {
            "monthly_revenue": frames["monthly_revenue"],
            "monthly_inventory_amount": frames["monthly_inventory_amount"],
            "monthly_inventory_qty": frames["monthly_inventory_qty"],
            "revenue_by_group": frames["revenue_by_group"],
            "inventory_by_group": frames["inventory_by_group"],
            "anomalies": frames["anomalies"],
            "correlation_analysis": frames["correlation_analysis"],
            "inventory_monthly_entity": real_tables.inventory_monthly_entity,
            "revenue_monthly_entity": real_tables.revenue_monthly_entity,
            "revenue_inventory_aligned": real_tables.revenue_inventory_aligned,
        }
        artifacts = AnalysisArtifacts(
            inventory_enriched=frames["inventory_enriched"],
            revenue_enriched=frames["revenue_enriched"],
            monthly_revenue=frames["monthly_revenue"],
            monthly_inventory_amount=frames["monthly_inventory_amount"],
            monthly_inventory_qty=frames["monthly_inventory_qty"],
            revenue_by_group=frames["revenue_by_group"],
            inventory_by_group=frames["inventory_by_group"],
            merged_analysis=frames["merged_analysis"],
            platform_monthly_analysis=frames["platform_monthly_analysis"],
            anomalies=frames["anomalies"],
            correlation_analysis=frames["correlation_analysis"],
            summary_metrics=summary_metrics,
            report_context={
                **real_tables.data_quality_report,
                "real_data": True,
                "monthly_revenue_records": frames["monthly_revenue"].to_dict(orient="records"),
                "monthly_inventory_amount_records": frames["monthly_inventory_amount"].to_dict(orient="records"),
                "monthly_inventory_qty_records": frames["monthly_inventory_qty"].to_dict(orient="records"),
                "revenue_by_group_records": frames["revenue_by_group"].to_dict(orient="records"),
                "inventory_by_group_records": frames["inventory_by_group"].to_dict(orient="records"),
                "platform_analysis_records": frames["platform_monthly_analysis"].head(20).to_dict(orient="records"),
                "merged_analysis_available": not frames["merged_analysis"].empty,
            },
            inventory_monthly_entity=real_tables.inventory_monthly_entity,
            revenue_monthly_entity=real_tables.revenue_monthly_entity,
            revenue_inventory_aligned=real_tables.revenue_inventory_aligned,
            data_quality_report=real_tables.data_quality_report,
        )
        inventory_check = {"missing": [], "extra": []}
        revenue_check = {"missing": [], "extra": []}
        supported_domains = {
            "sales": not artifacts.monthly_revenue.empty,
            "inventory": not artifacts.monthly_inventory_amount.empty,
            "financial": not artifacts.revenue_inventory_aligned.empty,
            "association": False,
            "chart": not artifacts.revenue_inventory_aligned.empty,
        }
        logger.info(
            "Real analysis complete: inventory_entity=%s revenue_entity=%s aligned=%s",
            len(real_tables.inventory_monthly_entity),
            len(real_tables.revenue_monthly_entity),
            len(real_tables.revenue_inventory_aligned),
        )
        return PipelineContext(
            inventory_check=inventory_check,
            revenue_check=revenue_check,
            inventory_df=real_inventory_df,
            revenue_df=real_revenue_df,
            parsed_mapping=parsed_mapping,
            artifacts=artifacts,
            messages=messages,
            supported_domains=supported_domains,
            source_files={
                "inventory": str(INVENTORY_FILE),
                "revenue": str(REVENUE_FILE),
                "mapping": str(MAPPING_FILE),
            },
            real_data_quality_report=real_tables.data_quality_report,
        )

    inventory_df, inventory_check, inventory_messages = load_inventory(INVENTORY_FILE)
    revenue_df, revenue_check, revenue_messages = load_revenue(REVENUE_FILE)
    mapping_raw_df, mapping_messages = load_mapping_raw(MAPPING_FILE)

    messages.extend(inventory_messages)
    messages.extend(revenue_messages)
    messages.extend(mapping_messages)

    logger.info(
        "Loaded raw dataframes: inventory_rows=%s, revenue_rows=%s, mapping_rows=%s",
        len(inventory_df),
        len(revenue_df),
        len(mapping_raw_df),
    )

    parsed_mapping, mapping_parse_messages = parse_mapping(mapping_raw_df)
    messages.extend(mapping_parse_messages)
    logger.info(
        "Parsed mapping: structured_rows=%s, bridge_candidates=%s, mapping_success=%s",
        len(parsed_mapping.structured_mapping),
        len(parsed_mapping.bridge_candidates),
        parsed_mapping.mapping_success,
    )

    if inventory_check.get("missing") or revenue_check.get("missing") or parsed_mapping.structured_mapping.empty:
        logger.error(
            "Pipeline prerequisites missing: inventory_missing=%s revenue_missing=%s mapping_empty=%s",
            inventory_check.get("missing"),
            revenue_check.get("missing"),
            parsed_mapping.structured_mapping.empty,
        )
        raise ValueError("Required input files or columns are missing; unable to build analysis context.")

    artifacts, analysis_messages = analyze_data(inventory_df, revenue_df, parsed_mapping)
    messages.extend(analysis_messages)
    logger.info(
        "Analysis complete: monthly_revenue=%s, anomalies=%s, correlations=%s",
        len(artifacts.monthly_revenue),
        len(artifacts.anomalies),
        len(artifacts.correlation_analysis),
    )

    supported_domains = {
        "sales": not artifacts.monthly_revenue.empty,
        "inventory": not artifacts.monthly_inventory_amount.empty,
        "financial": not artifacts.merged_analysis.empty or not artifacts.platform_monthly_analysis.empty,
        "association": not artifacts.correlation_analysis.empty,
        "chart": any(
            [
                not artifacts.monthly_revenue.empty,
                not artifacts.monthly_inventory_amount.empty,
                not artifacts.monthly_inventory_qty.empty,
                not artifacts.revenue_by_group.empty,
                not artifacts.inventory_by_group.empty,
                not artifacts.platform_monthly_analysis.empty,
            ]
        ),
    }
    logger.info("Supported domains: %s", supported_domains)

    return PipelineContext(
        inventory_check=inventory_check,
        revenue_check=revenue_check,
        inventory_df=inventory_df,
        revenue_df=revenue_df,
        parsed_mapping=parsed_mapping,
        artifacts=artifacts,
        messages=messages,
        supported_domains=supported_domains,
        source_files={
            "inventory": str(INVENTORY_FILE),
            "revenue": str(REVENUE_FILE),
            "mapping": str(MAPPING_FILE),
        },
    )
