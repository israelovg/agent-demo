# Sales Discount Strategy Agent

AI agent that suggests optimal discount strategies for sales reps based on customer history, deal size, and competitor pricing.

## Business Challenge

Sales representatives lack data-driven guidance when deciding on discounts. They rely on intuition, leading to inconsistent pricing, margin erosion, and lost deals. An AI agent is needed to analyze customer history, deal size, and competitor pricing to recommend the best discount strategy in real time.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Win Rate | — | +10% | 6 months | Discount Optimization / Sales Performance | user |

## Key Milestones

1. **Agent Initialized** — Agent is deployed and accessible to sales reps via chat interface.
2. **Customer History Retrieved** — Agent fetches and analyzes past deal data and pricing conditions for the customer.
3. **Deal Context Assessed** — Agent evaluates current deal size, product mix, and competitive landscape inputs.
4. **Discount Strategy Generated** — Agent produces a ranked recommendation of discount options with rationale.
5. **Sales Rep Interaction Completed** — Rep receives, reviews, and optionally refines the recommendation through conversation.

## Business Architecture (RBA)

### End-to-End Process

Lead to Cash

### Process Hierarchy

```
Lead to Cash (E2E)
└── Plan to Optimize Marketing and Sales
    └── Plan Sales and Manage Performance (BPS-369)
        └── Develop sales forecast
        └── Discount determination and pricing optimization
```

### Summary

The challenge maps to the "Plan to Optimize Marketing and Sales" phase of Lead to Cash, specifically the sub-process for planning sales performance and discount determination, applicable across B2B, wholesale, and subscription variants.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ------------------ | ------------------- | ---- | ------------------- |
| Retrieve pricing conditions and discounts | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_SLSPRICINGCONDITIONRECORD_SRV:v1` | — | — | — | — | No | API available; no MCP server found — agent calls API directly |
| Read pricing procedures | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_SLSPRICINGPROCEDURE_SRV:v1` | — | — | — | — | No | API available; no MCP server found |
| Sales pipeline & performance context | SAP Sales Cloud Version 2 | — | — | — | — | — | Maybe | Pipeline Management and Sales Analytics capabilities available |
| Competitor pricing context | — | — | — | — | — | — | Yes | No standard SAP API; agent relies on sales rep input or external data |
| Customer purchase history analysis | SAP S/4HANA (Sales Analytics) | — | — | — | — | — | Maybe | Available via analytics capabilities; direct history API unavailable in landscape |

### Key Findings

- SAP S/4HANA Cloud Public Edition exposes pricing condition and procedure APIs that can feed the agent with structured pricing data.
- SAP Sales Cloud V2 covers pipeline management, forecasting, and sales analytics — useful as contextual data sources.
- No MCP servers exist for the identified APIs; the agent will invoke them directly via API calls.
- Competitor pricing is a critical gap — no standard SAP data source covers this; the agent must accept it as conversational input from the sales rep.
- The solution is well-suited for a standalone AI Agent (no fixed workflow graph needed) that reasons dynamically over deal context.
- Industry variants covered: B2B, wholesale distribution, make-to-order, subscription.

## Recommendations

### Sales Discount Strategy AI Agent

#### Executive Summary

Python AI agent delivering real-time, context-aware discount recommendations to sales reps.

#### Recommended Solution

A pro-code Python AI agent (A2A protocol) deployed on SAP BTP. The agent integrates with SAP S/4HANA pricing condition APIs to retrieve historical pricing data, accepts deal context (size, product, customer tier) and competitor pricing as conversational input from the sales rep, and uses an LLM to reason over all inputs and recommend an optimal discount strategy with business rationale.

#### Recommended solution category

AI Agent

#### Intent fit
88%
