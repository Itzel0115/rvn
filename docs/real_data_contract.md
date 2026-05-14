# Phase 9A Real Data Contract

## Source Files

- Inventory source path: `data/inventory.xlsx`
- Revenue source path: `data/revenue.xlsx`

The loader treats `data/inventory.xlsx` as the inventory source and `data/revenue.xlsx` as the revenue source. If either file does not contain the required columns for its declared role, the pipeline records a data quality error instead of swapping files automatically.

## Raw Columns

Inventory raw columns:

- `Wn日期`
- `年`
- `月`
- `HQBU`
- `typename`
- `金額`
- `QTY`
- `Productline_5`
- `五大產品線`
- `新事業群`

Revenue raw columns:

- `公司類別`
- `年度`
- `月份`
- `合併事業群`
- `產品類別名稱`
- `實際營收`
- `五大產品線`
- `新事業群`

## Standard Columns

Inventory standard columns:

- `month_key`
- `year`
- `month`
- `hqbu`
- `inventory_type`
- `inventory_amount`
- `inventory_qty`
- `productline_raw`
- `product_line_5`
- `business_group`

Revenue standard columns:

- `month_key`
- `year`
- `month`
- `company_type`
- `merged_business_group`
- `product_category_name`
- `revenue_amount`
- `product_line_5`
- `business_group`

## Join Key And Grain

Join key:

- `month_key`
- `business_group`
- `product_line_5`

Analysis grain:

- `month_key + business_group + product_line_5`

`business_group` is the primary entity dimension. `product_line_5` is the drill-down entity dimension under a business group.

## Month Key Normalization

`month_key` must be normalized to `YYYY-MM`.

Accepted source forms include:

- `Wn日期` such as `202501`
- separate year/month columns such as `年度` + `月份`
- numeric or string year/month values

Invalid or missing dates are kept as null and counted in data quality output.

## Required Fields

Inventory required fields:

- `month_key`
- `business_group`
- `product_line_5`
- `inventory_amount`
- `inventory_qty`

Revenue required fields:

- `month_key`
- `business_group`
- `product_line_5`
- `revenue_amount`

## Numeric Fields

Inventory numeric fields:

- `inventory_amount`
- `inventory_qty`

Revenue numeric fields:

- `revenue_amount`

Numeric parse failures must be counted in `numeric_parse_errors`.

## Entity Dimensions

- `business_group` = `新事業群`
- `product_line_5` = `五大產品線`

For backward compatibility only, legacy `platform` wording and fields may wrap `business_group`. Core analysis must not depend on platform codes.

## Disallowed Joins

Do not join revenue and inventory by:

- `HQBU`, because revenue does not contain `HQBU`
- `product_line_5` alone, because different business groups may contain same-named product lines
- legacy platform codes such as `GG-01` / `GG-02`, unless those values exist in real data

## Ratio Rules

`revenue_inventory_amount_ratio` and `revenue_inventory_qty_ratio` are proxy metrics. They are calculated only when:

- `data_presence_flag = both`
- numerator and denominator are present
- denominator is not zero

Rows flagged `revenue_only` or `inventory_only` must not be used for ratio calculation.

These proxy ratios must not be described as formal inventory turnover.

## Known Limitations

- The available data supports descriptive comparison and proxy efficiency signals, not causal root-cause claims.
- Forecasting is not supported in Phase 9A.
- Missing business group, missing product line, numeric parse errors, unmatched months, and one-sided rows must be surfaced as data quality limitations.
- Any legacy `/api/ask` response fields must remain backward compatible; new entity-aware fields may be added.
