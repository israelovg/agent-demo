# Product Requirements Document (PRD)

**Title:** Sales Discount Strategy Agent
**Date:** 2026-10-20
**Owner:** Sales Operations
**Solution Category:** AI Agent

## Product Purpose & Value Proposition

**Elevator Pitch:**
Sales reps currently rely on gut feeling when deciding on discounts, leading to margin erosion and lost deals. This agent analyzes customer history, deal size, and competitor pricing to deliver real-time, data-backed discount recommendations.

**Business Need:**
Sales teams lack a consistent, data-driven approach to discount decisions. Without guidance, reps either over-discount (hurting margin) or under-discount (losing deals). A conversational AI agent that synthesizes SAP pricing data and deal context fills this gap directly in the sales workflow.

**Expected Value:**
- Increase win rate by 10% within 6 months by helping reps propose the right discount at the right moment.
- Reduce margin erosion through guardrails that flag high-risk discounts.

**Product Objectives:**
1. Deliver accurate, context-aware discount recommendations in real time during active deal negotiations.
2. Surface customer pricing history and deal patterns from SAP S/4HANA to support each recommendation.
3. Provide transparent rationale so sales reps can explain recommendations to customers and managers.

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Win Rate | — | +10% | 6 months | Discount Optimization / Sales Performance | user |

## Requirements

### Must-Have Requirements

**R1: Customer Pricing History Retrieval**
- **Problem to Solve**: Reps have no quick way to see what discounts a customer received historically.
- **User Story**: As a sales rep, I need the agent to retrieve and summarize a customer's past pricing and discount history so I can anchor my negotiation.
- **Acceptance Criteria**:
  - Given a customer name or ID, when I ask the agent, then it returns a summary of past deals, applied discounts, and pricing conditions from SAP S/4HANA.
- **Priority Rank**: 1

**R2: Deal Size & Margin Analysis**
- **Problem to Solve**: Reps don't know how deal size impacts acceptable discount thresholds.
- **User Story**: As a sales rep, I need the agent to analyze the current deal size and flag which discount levels protect margin so I know my floor.
- **Acceptance Criteria**:
  - Given a deal size and product mix, when I describe the deal, then the agent provides discount options with estimated margin impact per option.
- **Priority Rank**: 2

**R3: Competitor Pricing Context**
- **Problem to Solve**: There is no SAP source for competitor pricing; reps have this knowledge but no way to leverage it systematically.
- **User Story**: As a sales rep, I need to provide competitor pricing as context so the agent factors it into the recommendation.
- **Acceptance Criteria**:
  - Given a competitor price I share in the conversation, when I ask for a recommendation, then the agent incorporates it into the discount strategy without storing it permanently.
- **Priority Rank**: 3

**R4: Discount Strategy Recommendation**
- **Problem to Solve**: Reps need a clear, ranked recommendation — not just raw data.
- **User Story**: As a sales rep, I need the agent to recommend 2–3 discount options ranked by deal-close likelihood and margin impact so I can make an informed choice.
- **Acceptance Criteria**:
  - Given customer history, deal size, and competitor context, when I request a recommendation, then the agent returns at least 2 ranked options with a plain-language rationale for each.
- **Priority Rank**: 4

**R5: Conversational Interaction**
- **Problem to Solve**: Reps need to refine recommendations through follow-up questions, not static reports.
- **User Story**: As a sales rep, I need to interact with the agent conversationally so I can ask follow-up questions and iterate on the strategy.
- **Acceptance Criteria**:
  - Given a previous recommendation, when I ask "what if the customer wants 5% more?", then the agent recalculates and explains the trade-off.
- **Priority Rank**: 5

## Solution Architecture

**Architecture Overview:**
A pro-code Python AI agent built on the A2A protocol, deployed on SAP BTP. The agent uses SAP Generative AI Hub for LLM reasoning and calls SAP S/4HANA pricing APIs to retrieve structured data.

**Key Components:**
- **Sales Discount Agent** (Python, A2A): Core reasoning engine; handles conversation, tool orchestration, and recommendation generation.
- **SAP S/4HANA Pricing Condition API** (`API_SLSPRICINGCONDITIONRECORD_SRV`): Source of historical pricing and discount data per customer.
- **SAP S/4HANA Pricing Procedure API** (`API_SLSPRICINGPROCEDURE_SRV`): Provides pricing procedure rules for margin guardrails.
- **SAP Generative AI Hub**: LLM backend (GPT-4o or equivalent) for reasoning and natural language generation.

**Integration Points:**
- SAP S/4HANA Cloud (Public Edition): read-only pricing data via OData APIs.
- SAP AI Core / Generative AI Hub: LLM inference for reasoning and response generation.

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The agent exposes extension points to add new data sources (e.g., CRM opportunity data, external competitor feeds) without modifying core logic.
- Tool definitions are modular — new pricing or market data tools can be registered independently.

**Business Step Instrumentation:**
All key business steps emit structured logs for observability. Log statements follow the pattern `[MILESTONE_ID].[achieved|missed]: [description]`.

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent (conversational, multi-turn reasoning)

**Actions performed without human approval:**
- Querying SAP S/4HANA pricing history (read-only)
- Generating discount recommendations and rationale

**Actions requiring human review:**
- Final discount selection and submission — the agent recommends; the rep decides and applies the discount in the CRM/ERP.

**Model or engine used:** GPT-4o (or equivalent) via SAP Generative AI Hub

**Knowledge & data sources accessed:**
- SAP S/4HANA pricing condition records (customer-specific historical discounts)
- SAP S/4HANA pricing procedures (margin thresholds and rules)
- Competitor pricing: provided by the sales rep in conversation (not persisted)

**Tools or connectors invoked:**
- `get_pricing_conditions`: Retrieves historical discount and pricing conditions per customer from S/4HANA (read-only)
- `get_pricing_procedures`: Retrieves active pricing procedure rules for margin guardrail evaluation (read-only)

**Guardrails & fail-safes:**
- Agent never modifies pricing records or submits discounts autonomously.
- If S/4HANA API call fails, agent informs the rep and offers to proceed with rep-provided context only.
- Competitor pricing input from the rep is used in-session only and never stored or logged.
- Recommendations above a configurable discount threshold trigger a warning to the rep.

## Milestones

### M1: Agent Initialized
- **Description**: Agent is deployed, accessible, and ready to serve sales rep queries.
- **Achieved when**: Agent responds successfully to an initial greeting or capability inquiry.
- **Log on achievement**: `M1.achieved: Sales Discount Agent initialized and ready`
- **Log on miss**: `M1.missed: Agent initialization failed or did not respond`

### M2: Customer History Retrieved
- **Description**: Agent has successfully fetched and summarized the customer's pricing history from SAP S/4HANA.
- **Achieved when**: Pricing condition records for the specified customer are returned and summarized.
- **Log on achievement**: `M2.achieved: Customer pricing history retrieved for customer {customer_id}`
- **Log on miss**: `M2.missed: Failed to retrieve pricing history for customer {customer_id}`

### M3: Deal Context Assessed
- **Description**: Agent has collected deal size, product mix, and competitor pricing context (from rep input or derived).
- **Achieved when**: All three context inputs are present in the agent's working context.
- **Log on achievement**: `M3.achieved: Deal context assessed — size={deal_size}, products={product_count}, competitor_price={competitor_price}`
- **Log on miss**: `M3.missed: Deal context incomplete — missing {missing_fields}`

### M4: Discount Strategy Generated
- **Description**: Agent has produced a ranked list of discount options with rationale.
- **Achieved when**: At least 2 discount options with margin impact and rationale are returned to the rep.
- **Log on achievement**: `M4.achieved: Discount strategy generated with {option_count} options`
- **Log on miss**: `M4.missed: Discount strategy generation failed — {reason}`

### M5: Sales Rep Interaction Completed
- **Description**: Rep has reviewed the recommendations and concluded the session (accepted, refined, or declined).
- **Achieved when**: Rep signals end of session or applies a discount decision.
- **Log on achievement**: `M5.achieved: Session completed — rep action={rep_action}`
- **Log on miss**: `M5.missed: Session ended without a rep decision`
