---
name: discount-strategy
description: Multi-step discount strategy recommendation for sales reps based on customer pricing history from SAP S/4HANA, deal size, and competitor pricing provided by the rep
---

# Discount Strategy Recommendation Skill

## When to Use This Skill

Load this skill when a sales rep asks for:
- Discount recommendations for a deal
- Optimal pricing strategy for a customer
- How to respond to competitor pricing
- Whether a proposed discount is acceptable

## Prerequisites

Before generating a recommendation, ensure you have all three inputs:

1. **Customer ID or name** — to retrieve pricing history
2. **Deal size** — total deal value (approximate is acceptable)
3. **Competitor price** (optional but improves recommendation) — ask the rep if not provided

## Instructions

### Step 1: Retrieve Customer Pricing History

Use the `list_a_slsprcgconditionrecord` tool (or equivalent) to retrieve pricing condition records for the customer. Pass the customer/sold-to party ID as a filter.

- Set `$top=100` to prevent context overflow
- Look for condition types that represent discounts (e.g., `K007`, `K005`, `RA01`)
- Summarize: average discount %, range of discounts, most recent deal

If the tool returns an error, report it verbatim and ask the rep to verify the customer ID.

### Step 2: Retrieve Pricing Procedure Rules

Use the `list_a_slspricingprocedureitem_for_api_slspricingprocedure_srv` tool to retrieve the active pricing procedure steps.

- Look for condition types related to customer-specific discounts
- Note any mandatory/statistical flags that indicate hard limits
- Identify the condition type sequence to understand how discounts stack

### Step 3: Assess Deal Size

Based on the deal value provided by the rep, classify the deal tier:

| Deal Size | Tier | Typical Max Discount |
|-----------|------|---------------------|
| < $10,000 | Small | 5% |
| $10,000 – $50,000 | Medium | 10% |
| $50,000 – $200,000 | Large | 15% |
| > $200,000 | Strategic | 20% (requires approval) |

These are guideline maximums. The actual ceiling comes from the pricing procedure rules retrieved in Step 2.

### Step 4: Factor in Competitor Pricing

If the rep has shared competitor pricing:
- Calculate the gap between your price and competitor price
- Determine if the discount needed to match exceeds the deal tier ceiling
- If it does, flag this explicitly and recommend escalation for approval

### Step 5: Generate Ranked Recommendations

Produce **2–3 ranked discount options** in this format:

```
Option 1 (Recommended): X% discount
- Deal win likelihood: High / Medium / Low
- Margin impact: Low / Medium / High risk
- Rationale: [1 sentence referencing customer history or deal context]

Option 2: Y% discount
- Deal win likelihood: ...
- Margin impact: ...
- Rationale: ...

Option 3 (Stretch): Z% discount
- ⚠️ Warning: Exceeds standard ceiling for this deal tier. Manager approval required.
- Deal win likelihood: ...
- Margin impact: ...
- Rationale: ...
```

### Step 6: Apply Guardrails

Before presenting recommendations, check:

1. **Ceiling guardrail**: If any option exceeds the deal tier maximum, prepend a warning:
   > ⚠️ This option exceeds the standard discount ceiling for a [deal tier] deal. Confirm with your manager before quoting.

2. **History guardrail**: If the proposed discount is significantly higher than historical average for this customer (>5% above average), note this:
   > Note: This customer's average discount has been X%. The proposed Y% represents a significant increase.

3. **Competitor guardrail**: If matching competitor pricing would require exceeding the strategic ceiling (>20%), recommend escalation rather than a direct discount.

## Error Handling

- If pricing history retrieval fails: Proceed with deal-size-only analysis, but clearly state that historical context is unavailable.
- If pricing procedure retrieval fails: Use the deal tier table above as fallback.
- If competitor price exceeds strategic ceiling: Do NOT automatically generate an option above 20%. Instead, recommend escalation.

## Example Conversation

**Rep:** "I need a discount for customer ACME Corp on a $75,000 deal. Competitor is offering 12%."

**Agent flow:**
1. Retrieve ACME Corp's pricing history → finds average discount of 8%, range 5–11%
2. Retrieve pricing procedure → confirms max 15% for large deals
3. Classify: Large deal tier, max 15%
4. Competitor at 12% is within ceiling
5. Generate 3 options: 10% (safe), 12% (match competitor), 14% (stretch with warning)
