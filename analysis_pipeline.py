from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analyzer import AnalysisArtifacts, analyze_data
from config import CHART_DIR, DATA_DIR, INVENTORY_FILE, MAPPING_FILE, OUTPUT_DIR, REVENUE_FILE
from data_loader import load_inventory, load_mapping_raw, load_revenue
from logging_utils import get_logger
from mapping_parser import ParsedMapping, parse_mapping
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


def build_pipeline_context(request_id: str) -> PipelineContext:
    logger = get_logger("analysis_pipeline", request_id, domain="pipeline")
    ensure_directories([DATA_DIR, OUTPUT_DIR, CHART_DIR])

    logger.info("Loading source files")
    logger.info("Using inventory file: %s", INVENTORY_FILE)
    logger.info("Using revenue file: %s", REVENUE_FILE)
    logger.info("Using mapping file: %s", MAPPING_FILE)

    messages = MessageCollector()
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
