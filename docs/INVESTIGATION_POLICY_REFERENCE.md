# Investigation Policy Reference

<!-- Generated policy reference: proactive-policy.v1 -->

| Detector | Candidate | Metrics | Period | Threshold | Semantic task | Evidence | Limitation |
|---|---|---|---|---|---|---|---|
| revenue_inventory_relationship | revenue_drop | revenue_amount | paired latest periods | `PROACTIVE_MIN_ABSOLUTE_CHANGE` | metric_relationship_analysis | paired relationship evidence | descriptive only |
| revenue_inventory_relationship | inventory_increase | inventory_amount | paired latest periods | `PROACTIVE_MIN_ABSOLUTE_CHANGE` | metric_relationship_analysis | paired relationship evidence | amount is not quantity |
| revenue_inventory_relationship | revenue_inventory_divergence | revenue_amount + inventory_amount | paired period pair | revenue down and inventory up | metric_relationship_analysis | primary relationship evidence; snapshot supporting only | non-causal; ratio is proxy |
| data_quality | data_quality_issue | none | n/a | high/critical finding | data_quality | quality finding | blocks business conclusion when critical |

Thresholds are POC heuristics, are centralized in `proactive_workflow/policies.py`, and can be overridden only through documented environment variables.


## Evidence closure matrix

`revenue_drop` is a revenue amount time-series investigation; it does not require inventory evidence. `inventory_increase` is inventory amount and `inventory_quantity_increase` is inventory quantity: they are not interchangeable. Only divergence requires paired revenue/inventory relationship evidence. `not_available` counter evidence means no legal search capability, not no counterevidence.
