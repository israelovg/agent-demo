# Specification: sales-discount-strategy-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [ ] Read `product-requirements-document.md` and `intent.md` from the solution root for full context.
- [ ] Bootstrap agent code in `assets/sales-discount-strategy-agent/` using instructions from the `sap-agent-bootstrap` skill. Invoke from inside `assets/sales-discount-strategy-agent/`, use copy commands — do NOT create files manually.
- [ ] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`.

---

## Runtime Skills

The agent needs one runtime skill to handle the multi-step discount recommendation workflow with conditional logic (deal size thresholds, margin guardrails, competitor pricing branching).

- [ ] Create `assets/sales-discount-strategy-agent/app/skills/discount-strategy/SKILL.md` with:
  - Frontmatter: `name: discount-strategy`, `description: Multi-step discount strategy recommendation for sales reps based on customer history, deal size, and competitor pricing`
  - Step-by-step instructions:
    1. Retrieve customer pricing history via `get_pricing_conditions` tool
    2. Retrieve pricing procedure rules via `get_pricing_procedures` tool
    3. Assess deal size and compute applicable margin floor
    4. Accept competitor pricing from the sales rep's conversational input (do not persist)
    5. Generate 2–3 ranked discount options with margin impact and plain-language rationale
    6. Apply guardrails: warn if proposed discount exceeds configurable threshold
  - Decision table: deal size tiers and corresponding discount ceiling per tier
  - Guardrail rules: flag discounts above threshold with a warning before presenting

---

## Project-Specific Tasks

### R1: Customer Pricing History Retrieval

- [ ] Implement agent tool `get_pricing_conditions` that calls the SAP S/4HANA Pricing Condition Record API (`API_SLSPRICINGCONDITIONRECORD_SRV`) to retrieve a customer's historical pricing conditions and applied discounts.
- [ ] The tool accepts `customer_id` (required) and optional `material_id` as parameters.
- [ ] Return a structured summary: discount percentages, pricing condition types, and effective date ranges for the customer.
- [ ] In `app/agent.py` system prompt: instruct the agent to always call `get_pricing_conditions` first when the user mentions a customer before generating any recommendation.

### R2: Deal Size & Margin Analysis

- [ ] Implement agent tool `get_pricing_procedures` that calls the SAP S/4HANA Pricing Procedure API (`API_SLSPRICINGPROCEDURE_SRV`) to retrieve the active pricing procedure rules and margin thresholds.
- [ ] The tool returns pricing procedure steps, condition type sequences, and mandatory/statistical flags.
- [ ] In the `discount-strategy` runtime skill, add logic to combine pricing procedure rules with deal size input to compute the margin floor and maximum allowed discount per deal tier.

### R3: Competitor Pricing Context

- [ ] Add an instruction in `app/agent.py` system prompt: "If the user provides competitor pricing, use it as context for the current session only. Do not store or log competitor pricing data."
- [ ] In the `discount-strategy` runtime skill, add a step that prompts the agent to ask for competitor price if not yet provided before finalizing the recommendation.

### R4: Discount Strategy Recommendation

- [ ] The `discount-strategy` runtime skill must generate at minimum 2 ranked discount options per recommendation, each with:
  - Discount percentage
  - Estimated margin impact (qualitative: low / medium / high risk)
  - One-sentence rationale referencing the customer's history or deal context
- [ ] Add a guardrail: if any recommended option exceeds the pricing procedure's maximum discount threshold, emit a warning to the sales rep before presenting the option.

### R5: Conversational Interaction

- [ ] The agent must maintain conversation context across turns to allow follow-up questions (e.g., "what if I offer 5% more?").
- [ ] In `app/agent.py` system prompt: "You are a Sales Discount Strategy Assistant. Help sales reps determine the optimal discount for a deal by analyzing customer pricing history from SAP S/4HANA, deal size, and competitor pricing provided by the rep. Always use tools to retrieve live data. Never fabricate pricing data. When calling tools that support pagination, set the page size to a maximum of 100 items. If a tool returns an error, report it exactly as received."
- [ ] The agent must re-invoke the `discount-strategy` runtime skill for each new recommendation cycle.

---

## API Integration (MCP)

```
MCP API: sap.s4:apiResource:API_SLSPRICINGCONDITIONRECORD_SRV:v1
MCP tool scope: read-only
Resources in scope: A_SlsPricingConditionRecord, A_SlsPricingConditionRecordValidity
```

```
MCP API: sap.s4:apiResource:API_SLSPRICINGPROCEDURE_SRV:v1
MCP tool scope: read-only
Resources in scope: A_SlsPricingProcedure, A_SlsPricingProcedureStep
```

- [ ] API specs are in `specification/sales-discount-strategy-agent/api-specs/`:
  - `API_SLSPRICINGCONDITIONRECORD_SRV.edmx` — customer-specific pricing condition records
  - `API_SLSPRICINGPROCEDURE_SRV.edmx` — pricing procedure rules and margin thresholds
- [ ] Invoke `mcp-translation-file` skill for each API spec file to generate translation cards in `specification/sales-discount-strategy-agent/mcps/`.
- [ ] Invoke `setup-solution` skill to register the generated MCP server assets in `solution.yaml`.
- [ ] Wire MCP tool loading in `app/agent.py` using `get_mcp_tools()` from the `mcp_tools` module (bootstrap-generated). NEVER import directly from `sap_cloud_sdk.agentgateway`. NEVER create direct HTTP clients.
- [ ] Add MCP server dependencies to `assets/sales-discount-strategy-agent/asset.yaml` under `requires` using the exact ORD IDs from the generated MCP `asset.yaml` files.
- [ ] Generate `mcp-mock.json` using the `mcp-mock-config` skill after MCP translation and setup-solution complete.

---

## Business Instrumentation

- [ ] Implement structured logging and OpenTelemetry spans for all 5 milestones from the PRD:

  | ID | Milestone | Log (achieved) | Log (missed) |
  |----|-----------|----------------|--------------|
  | M1 | Agent Initialized | `M1.achieved: Sales Discount Agent initialized and ready` | `M1.missed: Agent initialization failed or did not respond` |
  | M2 | Customer History Retrieved | `M2.achieved: Customer pricing history retrieved for customer {customer_id}` | `M2.missed: Failed to retrieve pricing history for customer {customer_id}` |
  | M3 | Deal Context Assessed | `M3.achieved: Deal context assessed — size={deal_size}, products={product_count}, competitor_price={competitor_price}` | `M3.missed: Deal context incomplete — missing {missing_fields}` |
  | M4 | Discount Strategy Generated | `M4.achieved: Discount strategy generated with {option_count} options` | `M4.missed: Discount strategy generation failed — {reason}` |
  | M5 | Sales Rep Interaction Completed | `M5.achieved: Session completed — rep action={rep_action}` | `M5.missed: Session ended without a rep decision` |

- [ ] Extract business logic from `stream()` into a plain async helper (e.g. `_run_agent()`) and apply `@tracer.start_as_current_span` decorator on that method — do NOT use context manager form inside async generators.
- [ ] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`.

---

## Testing

- [ ] `conftest.py` sets only `IBD_TESTING=true` — no other test configuration in conftest.
- [ ] Write unit tests in `assets/sales-discount-strategy-agent/tests/`:
  - `test_get_pricing_conditions.py` — tests customer history retrieval with mocked MCP responses
  - `test_get_pricing_procedures.py` — tests pricing procedure retrieval with mocked MCP responses
  - `test_discount_strategy.py` — tests recommendation generation with 2+ options and guardrail warnings
- [ ] Write one integration test: end-to-end flow with mocked LLM and MCP responses; assert M4.achieved log is emitted.
- [ ] Mock all external systems (S/4HANA APIs, MCP servers, SAP AI Core / LiteLLM) — tests must run offline.
- [ ] Run `pytest` from `assets/sales-discount-strategy-agent/` (no extra flags).
- [ ] If coverage < 70%, add targeted tests until threshold is met.
- [ ] Run final `pytest` (no args) to produce `test_report.json`.
- [ ] Verify `test_report.json` exists in `assets/sales-discount-strategy-agent/`.
