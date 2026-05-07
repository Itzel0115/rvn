from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import CHART_STYLE
from utils import MessageCollector


plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def render_chart_payload(chart_payload: dict, output_path: Path) -> None:
    chart_type = chart_payload.get("chart_type")
    title = chart_payload.get("title", output_path.stem)
    x_label = chart_payload.get("x_label", "")
    y_label = chart_payload.get("y_label", "")
    labels = chart_payload.get("labels", [])
    series = chart_payload.get("series", [])

    if not labels or not series:
        raise ValueError("Chart payload must include labels and series.")

    plt.figure(figsize=CHART_STYLE["figure_size"], dpi=CHART_STYLE["dpi"])

    if chart_type == "line":
        for index, item in enumerate(series):
            color = item.get("color") or _color_for_index(index)
            plt.plot(
                labels,
                item.get("data", []),
                marker="o",
                linewidth=CHART_STYLE["line_width"],
                label=item.get("name", f"series_{index + 1}"),
                color=color,
            )
        if len(series) > 1:
            plt.legend(loc="best", fontsize=8, ncol=2)
        plt.grid(alpha=0.3, linestyle="--")
    elif chart_type == "bar":
        color = series[0].get("color") if series else CHART_STYLE["bar_color"]
        plt.bar(labels, series[0].get("data", []), color=color or CHART_STYLE["bar_color"])
    elif chart_type == "area":
        for index, item in enumerate(series):
            color = item.get("color") or _color_for_index(index)
            plt.fill_between(
                labels,
                item.get("data", []),
                alpha=0.28,
                label=item.get("name", f"series_{index + 1}"),
                color=color,
            )
            plt.plot(
                labels,
                item.get("data", []),
                linewidth=CHART_STYLE["line_width"],
                color=color,
            )
        if len(series) > 1:
            plt.legend(loc="best", fontsize=8, ncol=2)
        plt.grid(alpha=0.3, linestyle="--")
    elif chart_type == "pie":
        values = series[0].get("data", []) if series else []
        colors = [_color_for_index(index) for index, _ in enumerate(labels)]
        plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
        plt.axis("equal")
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def create_all_charts(artifacts, chart_dir: Path) -> MessageCollector:
    collector = MessageCollector()
    _plot_line(artifacts.monthly_revenue, "月份", "營收", "各月份總營收趨勢", "營收", chart_dir / "monthly_revenue_trend.png", CHART_STYLE["accent_color"], collector)
    _plot_line(artifacts.monthly_inventory_amount, "月份", "金額", "各月份總庫存金額趨勢", "庫存金額", chart_dir / "monthly_inventory_amount_trend.png", CHART_STYLE["inventory_color"], collector)
    _plot_line(artifacts.monthly_inventory_qty, "月份", "QTY", "各月份總庫存 QTY 趨勢", "庫存 QTY", chart_dir / "monthly_inventory_qty_trend.png", CHART_STYLE["qty_color"], collector)
    _plot_bar(artifacts.revenue_by_group, "事業群名稱", "營收", "各新事業群營收分布", "營收", chart_dir / "revenue_by_group.png", CHART_STYLE["bar_color"], collector)
    _plot_bar(artifacts.inventory_by_group, "事業群名稱", "金額", "各新事業群庫存分布", "庫存金額", chart_dir / "inventory_by_group.png", CHART_STYLE["inventory_color"], collector)

    if not artifacts.platform_monthly_analysis.empty:
        _plot_platform_pivot(artifacts.platform_monthly_analysis, "營收", "各平台每月營收", chart_dir / "platform_monthly_revenue.png", collector)
        _plot_platform_pivot(artifacts.platform_monthly_analysis, "金額", "各平台每月庫存金額", chart_dir / "platform_monthly_inventory_amount.png", collector)
        _plot_platform_pivot(artifacts.platform_monthly_analysis, "QTY", "各平台每月庫存 QTY", chart_dir / "platform_monthly_inventory_qty.png", collector)
    else:
        collector.add_warning("未輸出平台層級圖表，因平台整合主表不可用。")
    return collector


def _plot_line(df: pd.DataFrame, x_col: str, y_col: str, title: str, y_label: str, output_path: Path, color: str, collector: MessageCollector) -> None:
    if df.empty or y_col not in df.columns:
        collector.add_warning(f"略過圖表 {output_path.name}，因缺少資料。")
        return
    plt.figure(figsize=CHART_STYLE["figure_size"], dpi=CHART_STYLE["dpi"])
    plt.plot(df[x_col], df[y_col], marker="o", linewidth=CHART_STYLE["line_width"], color=color)
    plt.title(title)
    plt.xlabel("月份")
    plt.ylabel(y_label)
    plt.xticks(rotation=45)
    plt.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def _plot_bar(df: pd.DataFrame, label_col: str, value_col: str, title: str, y_label: str, output_path: Path, color: str, collector: MessageCollector) -> None:
    if df.empty or value_col not in df.columns:
        collector.add_warning(f"略過圖表 {output_path.name}，因缺少資料。")
        return
    labels = df[label_col].fillna("未對應")
    plt.figure(figsize=CHART_STYLE["figure_size"], dpi=CHART_STYLE["dpi"])
    plt.bar(labels, df[value_col], color=color)
    plt.title(title)
    plt.xlabel(label_col)
    plt.ylabel(y_label)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def _plot_platform_pivot(df: pd.DataFrame, value_col: str, title: str, output_path: Path, collector: MessageCollector) -> None:
    if df.empty or value_col not in df.columns:
        collector.add_warning(f"略過圖表 {output_path.name}，因缺少資料。")
        return
    pivot = df.pivot_table(index="月份", columns="平台", values=value_col, aggfunc="sum")
    if pivot.empty:
        collector.add_warning(f"略過圖表 {output_path.name}，因 pivot 後無資料。")
        return
    plt.figure(figsize=(14, 7), dpi=CHART_STYLE["dpi"])
    for column in pivot.columns:
        plt.plot(pivot.index, pivot[column], marker="o", linewidth=1.8, label=column)
    plt.title(title)
    plt.xlabel("月份")
    plt.ylabel(value_col)
    plt.xticks(rotation=45)
    plt.grid(alpha=0.25, linestyle="--")
    plt.legend(loc="best", fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def _color_for_index(index: int) -> str:
    palette = [
        CHART_STYLE["accent_color"],
        CHART_STYLE["inventory_color"],
        CHART_STYLE["qty_color"],
        CHART_STYLE["bar_color"],
        "#D1495B",
        "#00798C",
        "#EDAe49",
        "#4F5D75",
    ]
    return palette[index % len(palette)]
