# UI Metric Contract (v1)

## Purpose

This document defines the **UI metric contract** for the Stock Tracker application.

The contract specifies:
- Which metrics are displayed
- How they are labeled and formatted
- How missing data is handled

This contract is **independent of data sources, valuation logic, or user personas**.
All UI components must rely exclusively on this contract.

---

## Scope

- Applies to **multi-ticker comparison view**
- Maximum of **10 tickers**
- Read-only data display
- No recommendations or investment advice

---

## Design Principles

- Neutral and factual
- No implicit valuation judgments
- Consistent formatting
- Explicit handling of missing data
- Extensible without breaking existing UI

---

## Supported Metrics (v1)

| Metric Key | Display Label | Description |
|----------|---------------|-------------|
| `price` | Price | Last traded market price |
| `market_cap` | Market_
| `pe_trailing` | float | ratio | `45.2` |
| `pe_forward` | float | ratio | `32.1` |
| `revenue_growth_yoy` | float | % | `12.3 %` |
| `last_earnings_date` | string (ISO) | — | `YYYY-MM-DD` |
| `earnings_result` | enum | — | `Beat`, `Meet`, `Miss` |

---

## Missing Data Rules

- Missing, null, NaN, or invalid values MUST be displayed as: `--`
- The UI MUST NOT:
- Infer values
- Hide rows
- Replace missing values with defaults
---

## Canonical Metric Structure

Each ticker MUST conform to the following structure:

```python
MetricSet = {
  "price": float | None,
  "market_cap": float | None,
  "pe_trailing": float | None,
  "pe_forward": float | None,
  "revenue_growth_yoy": float | None,
  "last_earnings_date": str | None,
  "earnings_result": str | None
}

