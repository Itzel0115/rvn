from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
CHART_DIR = OUTPUT_DIR / "charts"

INVENTORY_FILE = DATA_DIR / "inventory.xlsx"
REVENUE_FILE = DATA_DIR / "revenue.xlsx"
MAPPING_FILE = DATA_DIR / "mapping.xlsx"

CLEANED_INVENTORY_FILE = OUTPUT_DIR / "cleaned_inventory.xlsx"
CLEANED_REVENUE_FILE = OUTPUT_DIR / "cleaned_revenue.xlsx"
PARSED_MAPPING_FILE = OUTPUT_DIR / "parsed_mapping.xlsx"
MERGED_ANALYSIS_FILE = OUTPUT_DIR / "merged_analysis.xlsx"
SUMMARY_METRICS_FILE = OUTPUT_DIR / "summary_metrics.xlsx"
ANALYSIS_REPORT_FILE = OUTPUT_DIR / "analysis_report.md"
LLM_EXPLANATION_FILE = OUTPUT_DIR / "llm_explanation.md"
QA_TRANSCRIPT_FILE = OUTPUT_DIR / "qa_transcript.md"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma4:e4b"
OLLAMA_TIMEOUT_SECONDS = 90

# ---------------------------------------------------------------------------
# Column name contract — A and B must both import from here.
# A owns the definitions; B must not hardcode these strings directly.
# If A renames a column, update here and run --project-summary to verify.
# ---------------------------------------------------------------------------

# Shared identity columns
COL_DATE = "日期"
COL_MONTH = "月份"
COL_GROUP_CODE = "新事業群"
COL_GROUP_NAME = "事業群名稱"
COL_GROUP_CODE_ALT = "事業群代碼"   # mapping table uses this name
COL_PLATFORM = "平台"
COL_HQBU = "HQBU"

# Metric columns
COL_REVENUE = "營收"
COL_INV_AMOUNT = "金額"
COL_INV_QTY = "QTY"
COL_MOM_RATE = "月增率"
COL_METRIC_LABEL = "指標"

# Platform-merged analysis columns
COL_REVENUE_INV_AMOUNT_RATIO = "營收_庫存金額比值"
COL_REVENUE_INV_QTY_RATIO = "營收_庫存QTY比值"

# Anomaly columns
COL_ANOMALY_TYPE = "異常類型"
COL_ANOMALY_SIGNAL = "訊號"
COL_ANOMALY_REASON = "說明"

# Correlation columns
COL_CORR_LEVEL = "分析層級"
COL_CORR_TARGET = "分析對象"
COL_CORR_METRICS = "指標組合"
COL_CORR_SAMPLES = "樣本數"
COL_CORR_VALUE = "相關係數"
COL_CORR_LABEL = "關聯判讀"

EXPECTED_INVENTORY_COLUMNS = [COL_DATE, COL_HQBU, COL_INV_AMOUNT, COL_INV_QTY, COL_GROUP_CODE]
EXPECTED_REVENUE_COLUMNS = [COL_DATE, COL_PLATFORM, COL_REVENUE, COL_GROUP_CODE]

MAPPING_POSITION_COLUMNS = {
    "A": "事業群名稱",
    "B": "事業群代碼",
    "C": "庫存HQBU分類名稱",
    "D": "庫存HQBU代碼",
    "E": "金額處理方式",
    "F": "QTY處理方式",
    "G": "營收平台分類名稱",
    "H": "營收平台代碼",
    "I": "實際營收處理方式",
}

BU_CODE_PATTERN = r"^GG-(0[1-9]|[1-8][0-9]|9[0-1])$"
ANOMALY_MOM_THRESHOLD = 0.3
HIGH_INVENTORY_REVENUE_RATIO_THRESHOLD = 0.8
HIGH_REVENUE_INVENTORY_QTY_RATIO_THRESHOLD = 0.8
CORRELATION_MIN_OBSERVATIONS = 3

CHART_STYLE = {
    "figure_size": (12, 6),
    "dpi": 140,
    "line_width": 2.2,
    "bar_color": "#2E5B88",
    "accent_color": "#D96C06",
    "inventory_color": "#6C8E3D",
    "qty_color": "#8A4FFF",
}
