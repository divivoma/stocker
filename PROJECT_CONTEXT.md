# Stock Tracker – Project Context
#how to use this: 
#When you start a new ChatGPT conversation, do this:
#Paste the content of this PROJECT_CONTEXT.md
#Then add one line in the bottom of the file:
#Continue from the current open question.
#
#

## Goal
Build a local-first stock tracking tool for non-professional investors that:
- Aggregates key financial metrics
- Visualizes earnings trends
- Supports informed but non-advisory decision-making
- Can later evolve into a web-based product

## Personas
1. Full-Time Employee (FTE)
   - Limited time
   - Interested in companies related to own industry
   - Focus on earnings performance, valuation, and exit rules

2. Investment Housewife (IHW)
   - Limited financial knowledge
   - Needs simple, interpretable signals
   - Trusts visual cues and explanations over raw numbers

## Feature 1 (Standard): Core Financial Metrics
- Price
- Market Cap
- P/E (TTM, Forward)
- Gross Margin
- Net Income (last quarter)
- Net Income (last 4 quarters)
- Net Income trend visualization

## Feature 1 (Premium – Backlog)
- Revenue Contribution by Segment
  - Derived from earnings call PDFs
  - Generic across companies
  - Not Amazon-specific

## Current Implementation State
- Data source: yfinance
- Backend: Python
- UI: Streamlit (local)
- Mock UI preserved in separate app
- Live data UI implemented and committed
- Matrix 1: Core metrics comparison
- Matrix 2: Net income last 4 quarters (table)
- Line chart: Net income trend per ticker

## Branching Strategy
- mainline: stable, working code only
- feature/*: incremental development
- Each increment:
  - Implement
  - Smoke test
  - Commit
  - Merge only when stable

## Current Open Question
- Whether to add "Earnings Momentum" label (Improving / Stable / Declining)
  - Descriptive only
  - Based on historical net income
  - No buy/sell signals

## Coding Constraints
- Incremental steps only
- No feature jumps
- Commit after each verified increment
- UI before automation

#uncomment below line before issung this as a prompt
#Continue from the current open question.
