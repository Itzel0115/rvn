from __future__ import annotations

import html.parser
import json
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag, urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "frontend" / "public" / "handoff"
ASSET_REF_ATTRS = {"href", "src"}
EXTERNAL_PREFIXES = ("http://", "https://", "//")
REQUIRED_PAGES = [
    "index.html",
    "overview.html",
    "question-journey.html",
    "tools.html",
    "architecture.html",
    "operations.html",
    "maintenance.html",
    "appendix.html",
]
REQUIRED_ASSETS = [
    "assets/css/style.css",
    "assets/js/app.js",
    "assets/diagrams/system-architecture.svg",
    "assets/diagrams/question-flow.svg",
    "assets/diagrams/tool-boundary.svg",
    "assets/diagrams/proactive-flow.svg",
    "assets/data/tool-catalog.json",
    "assets/data/file-index.json",
]


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.details_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "details":
            self.details_count += 1
        if "id" in values and values["id"]:
            self.ids.add(values["id"] or "")
        for attr in ASSET_REF_ATTRS | {"href"}:
            value = values.get(attr)
            if value:
                self.links.append((attr, value))


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def is_external(value: str) -> bool:
    return value.startswith(EXTERNAL_PREFIXES)


def validate_html(path: Path, errors: list[str]) -> None:
    raw = path.read_text(encoding="utf-8")
    parser = LinkParser()
    try:
        parser.feed(raw)
    except Exception as exc:
        fail(f"HTML parse failed: {path.relative_to(ROOT)}: {exc}", errors)
        return
    if "file://" in raw:
        fail(f"file:// found in {path.relative_to(ROOT)}", errors)
    if re.search(r"/home/user\d|[A-Z]:\\\\|localhost:(?!11434)", raw):
        fail(f"local absolute path or hardcoded localhost found in {path.relative_to(ROOT)}", errors)
    if re.search(r"https?://(?:cdn|unpkg|cdnjs|fonts\.googleapis|fonts\.gstatic)", raw):
        fail(f"external CDN/font dependency found in {path.relative_to(ROOT)}", errors)
    if path.name == "appendix.html" and "fileSearch" not in raw:
        fail("appendix missing dynamic file search", errors)
    for token in ["page-toc", "page-toc-links", "data-toc-collapse", "data-toc-expand", "data-toc-mobile-open"]:
        if token not in raw:
            fail(f"page TOC token missing in {path.relative_to(ROOT)}: {token}", errors)
    if '<aside class="toc"' in raw:
        fail(f"legacy top TOC class found in {path.relative_to(ROOT)}", errors)
    if parser.details_count == 0 and path.name not in {"index.html"}:
        fail(f"no <details> sections found in {path.relative_to(ROOT)}", errors)
    for _attr, link in parser.links:
        if link.startswith("#") or link.startswith("mailto:") or link.startswith("tel:"):
            continue
        if is_external(link):
            fail(f"external link/reference found in {path.relative_to(ROOT)}: {link}", errors)
            continue
        if link.startswith("/"):
            if link not in {"/", "/dashboard", "/mobile"} and not link.startswith("/api/"):
                fail(f"absolute site link found in {path.relative_to(ROOT)}: {link}", errors)
            continue
        target, fragment = urldefrag(link)
        if not target:
            if fragment and fragment not in parser.ids:
                fail(f"missing fragment #{fragment} in {path.relative_to(ROOT)}", errors)
            continue
        target_path = (path.parent / target).resolve()
        try:
            target_path.relative_to(SITE.resolve())
        except ValueError:
            fail(f"link escapes handoff site in {path.relative_to(ROOT)}: {link}", errors)
            continue
        if target.endswith("/"):
            target_path = target_path / "index.html"
        if not target_path.exists():
            fail(f"broken link/reference in {path.relative_to(ROOT)}: {link}", errors)
        elif fragment and target_path.suffix == ".html":
            sub = LinkParser()
            sub.feed(target_path.read_text(encoding="utf-8"))
            if fragment not in sub.ids:
                fail(f"missing fragment #{fragment} in {target_path.relative_to(ROOT)}", errors)


def validate_catalog(errors: list[str]) -> None:
    sys.path.insert(0, str(ROOT))
    from tool_registry import TOOL_REGISTRY

    catalog_path = SITE / "assets" / "data" / "tool-catalog.json"
    if not catalog_path.exists():
        fail("missing tool catalog JSON", errors)
        return
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    names = {item["tool_name"] for item in payload.get("tools", [])}
    registry_names = set(TOOL_REGISTRY)
    if names != registry_names:
        fail(f"tool catalog mismatch: missing={sorted(registry_names - names)} extra={sorted(names - registry_names)}", errors)
    mcp_catalog = {item["tool_name"] for item in payload.get("tools", []) if item.get("mcp_exposable")}
    mcp_registry = {name for name, contract in TOOL_REGISTRY.items() if contract.mcp_exposable}
    if mcp_catalog != mcp_registry:
        fail(f"MCP catalog mismatch: missing={sorted(mcp_registry - mcp_catalog)} extra={sorted(mcp_catalog - mcp_registry)}", errors)
    read_only = sum(1 for contract in TOOL_REGISTRY.values() if contract.read_only)
    if payload.get("stats", {}).get("read_only") != read_only:
        fail("read_only count mismatch", errors)
    for item in payload.get("tools", []):
        impl = item.get("implementation_path")
        tests = item.get("tests") or []
        if impl and not (ROOT / impl).exists():
            fail(f"implementation path missing for {item['tool_name']}: {impl}", errors)
        for test in tests:
            if test != "目前測試中未直接提及此 Tool 名稱" and not (ROOT / test).exists():
                fail(f"test path missing for {item['tool_name']}: {test}", errors)


def validate_file_index(errors: list[str]) -> None:
    path = SITE / "assets" / "data" / "file-index.json"
    if not path.exists():
        fail("missing file index JSON", errors)
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload:
        fail("file index JSON is empty or invalid", errors)
        return
    for group, items in payload.items():
        if not isinstance(items, list):
            fail(f"file index group is not a list: {group}", errors)
            continue
        for item in items:
            rel = item.get("path")
            if rel and not (ROOT / rel).exists():
                fail(f"file index path missing: {rel}", errors)


def validate_theme_assets(errors: list[str]) -> None:
    css = SITE / "assets" / "css" / "style.css"
    js = SITE / "assets" / "js" / "app.js"
    if css.exists():
        raw = css.read_text(encoding="utf-8")
        for token in ["html[data-theme=\"light\"]", "html[data-theme=\"dark\"]", "--surface", "--code-bg", ".content-layout.toc-collapsed", ".toc-mobile-button", ".toc-backdrop", "position:sticky"]:
            if token not in raw:
                fail(f"theme/TOC CSS token missing: {token}", errors)
    if js.exists():
        raw = js.read_text(encoding="utf-8")
        for token in ["handoff-theme", "data-theme", "file-index.json", "handoff-toc-collapsed", "IntersectionObserver", "toc-drawer-open", "Escape"]:
            if token not in raw:
                fail(f"theme/search/TOC JS token missing: {token}", errors)


def validate_source_paths(errors: list[str]) -> None:
    source_mentions = set(re.findall(r"(?:frontend|agent_runtime|semantic_layer|proactive_workflow|mcp_server|observability|evaluation|tests)/[A-Za-z0-9_./-]+|(?:demo_web|multi_agent|tool_registry|analysis_tools|answer_plan|plan_validator|writer_validator|task_profile|canonical_task|analysis_pipeline|real_data|data_loader|README)\.(?:py|md|js|json)", "\n".join(p.read_text(encoding="utf-8") for p in SITE.glob("*.html"))))
    for mention in source_mentions:
        clean = mention.split(":", 1)[0].rstrip(".")
        if clean.endswith((".py", ".js", ".jsx", ".json", ".md", ".toml", ".mjs", ".jsonl")) and not (ROOT / clean).exists():
            fail(f"mentioned source path does not exist: {clean}", errors)


def main() -> int:
    errors: list[str] = []
    if not SITE.exists():
        fail("handoff site directory missing", errors)
    for page in REQUIRED_PAGES:
        path = SITE / page
        if not path.exists():
            fail(f"required page missing: {page}", errors)
        else:
            validate_html(path, errors)
    for asset in REQUIRED_ASSETS:
        path = SITE / asset
        if not path.exists():
            fail(f"required asset missing: {asset}", errors)
        elif path.suffix == ".svg" and "<svg" not in path.read_text(encoding="utf-8"):
            fail(f"invalid SVG asset: {asset}", errors)
    validate_catalog(errors)
    validate_file_index(errors)
    validate_theme_assets(errors)
    validate_source_paths(errors)
    result = {
        "valid": not errors,
        "site": SITE.relative_to(ROOT).as_posix(),
        "pages": REQUIRED_PAGES,
        "required_assets": REQUIRED_ASSETS,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
