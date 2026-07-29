# Real Data Contract

This is the current contract for the two formal Excel sources. The current runtime does not require or read a mapping workbook.

## Source Files

- Inventory: `data/inventory.xlsx`
- Revenue: `data/revenue.xlsx`

The loader keeps these roles fixed. It does not swap files when fields do not match.

## Raw Required Fields

Inventory:

- `Wn日期`, `年`, `月`
- `HQBU`, `typename`
- `金額`, `QTY`
- `Productline_5`, `五大產品線`, `新事業群`

Revenue:

- `公司類別`, `年度`, `月份`
- `合併事業群`, `產品類別名稱`
- `實際營收`, `五大產品線`, `新事業群`

## Normalized Fields

Inventory is normalized to `month_key`, `year`, `month`, `hqbu`, `inventory_type`, `inventory_amount`, `inventory_qty`, `productline_raw`, `product_line_5`, and `business_group`.

Revenue is normalized to `month_key`, `year`, `month`, `company_type`, `merged_business_group`, `product_category_name`, `revenue_amount`, `product_line_5`, and `business_group`.

## Date Normalization

`month_key` is normalized to `YYYY-MM`. Accepted inputs include `Wn日期` values such as `202501`, separate year/month fields, and numeric or string year/month values. Invalid or missing dates become null and are reported in data quality output.

## Business Group and Product Line

- `business_group` = `新事業群`
- `product_line_5` = `五大產品線`
- `business_group` is the primary entity dimension.
- `product_line_5` is the drill-down dimension under a business group.

## Entity/Month Alignment

## Do not join

Do not join revenue and inventory by `HQBU`, by `product_line_5` alone, or by legacy platform codes.


The canonical alignment grain is:

```text
month_key + business_group + product_line_5
```

Revenue and inventory are outer-aligned at this grain. Rows are classified as both, revenue-only, or inventory-only. `HQBU` cannot be used as a cross-source join key because revenue has no corresponding HQBU field. Product line alone is also insufficient because names may repeat across business groups.

## Numeric and Proxy Rules

Numeric fields are `inventory_amount`, `inventory_qty`, and `revenue_amount`. Parse failures are recorded in data-quality results. Revenue/inventory ratios are proxy metrics only and require both sides, present numerator/denominator, and a non-zero denominator. They are not formal inventory-turnover metrics.

## Validation Failure

If either formal source is missing, unreadable, missing required raw fields, or produces no usable normalized rows, `build_pipeline_context()` raises a real-data validation error. The error identifies the inventory source status, revenue source status, missing fields or read errors, and normalization details. The runtime does not fall back to another workbook or legacy report path.

Data-quality output also surfaces missing business groups, missing product lines, numeric parse errors, invalid dates, unmatched months, and one-sided rows.

## Compatibility Note

`ParsedMapping` and related group/entity metadata are internal compatibility structures derived from the normalized inventory/revenue data. They are not a third source file.
