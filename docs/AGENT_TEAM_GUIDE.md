# Stock Tracker Multi-Agent Team Guide

## Team Overview

Your development is supported by 6 specialized AI agents, each with distinct expertise:

| Agent | Trigger | Use For |
|-------|---------|---------|
| **Product Strategist** | `@product-strategist` | Competition analysis, business models, PRD refinement, pricing |
| **Technical Architect** | `@tech-architect` | System design, architecture, tech decisions, scalability |
| **Backend Developer** | `@backend-developer` | Python/yfinance implementation, calculations, data logic |
| **Frontend Developer** | `@frontend-developer` | Streamlit UI, charts, user experience |
| **QA Engineer** | `@qa-engineer` | Testing, verification, acceptance criteria |
| **Team Coordinator** | `@team-coordinator` | Task routing, workflow orchestration |

## Quick Start Examples

### Strategy & Business
```
@product-strategist Analyze top 5 competitors to Stock Tracker and identify our differentiation opportunity

@product-strategist Recommend a freemium pricing model for FTE and IHW personas

@product-strategist Review and improve User Story 2 acceptance criteria
```

### Architecture & Design
```
@tech-architect Design the Position data model with entry/exit tracking

@tech-architect Plan the migration path from Streamlit to web-based architecture

@tech-architect Review the current codebase and identify technical debt
```

### Implementation
```
@backend-developer Implement the net P&L calculation with configurable fees and taxes

@frontend-developer Build the multi-ticker comparison table with max 10 selection

@backend-developer Add earnings beat/meet/miss tracking for selected tickers
```

### Quality Assurance
```
@qa-engineer Create test cases for the exit rule calculations

@qa-engineer Verify User Story 2 acceptance criteria are met

@qa-engineer Run full regression after the new feature merge
```

## Recommended Workflow

### For New Features
1. **Clarify** → `@product-strategist` refine the user story
2. **Design** → `@tech-architect` create technical approach
3. **Implement** → `@backend-developer` + `@frontend-developer` build it
4. **Verify** → `@qa-engineer` test and approve
5. **Ship** → Merge to mainline

### For Quick Fixes
- Direct to `@backend-developer` or `@frontend-developer`
- Have `@qa-engineer` verify before merge

### For Strategic Decisions
- Start with `@product-strategist` for context
- Involve `@tech-architect` for technical feasibility

## Key Project Principles

1. **Incremental Development**: Small commits, verified before merge
2. **Decision Support Only**: Never recommend buy/sell actions
3. **Persona-Aware**: FTE wants data, IHW wants clarity
4. **Local-First**: Streamlit MVP, web evolution later

## Current Sprint Focus (from PRD)

### Immediate Priorities
- [ ] Earnings monitoring with historical comparison
- [ ] Entry/exit logic with trigger proximity
- [ ] Net gain calculation (fees + taxes)

### Backlog
- [ ] Market type ticker groupings (semiconductors, humanoids, etc.)
- [ ] Revenue contribution by segment (from earnings calls)
- [ ] Web-based migration

## Files Reference

| File | Purpose |
|------|---------|
| `PROJECT_CONTEXT.md` | Current state and open questions |
| `docs/ui_metric_contract.md` | UI metric definitions |
| `stock-tracker-PRD.odt` | Full product requirements (parent folder) |
| `src/` | Application source code |
| `tests/` | Test suite |
| `config/` | Configuration files |
