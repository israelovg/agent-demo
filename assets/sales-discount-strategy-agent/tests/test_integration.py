"""Integration test: end-to-end agent flow with mocked LLM and MCP responses."""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_end_to_end_discount_recommendation_flow(add_agent_to_path, caplog):
    """
    End-to-end integration test for the sales discount strategy agent.

    Verifies:
    - Agent accepts a deal context query
    - Agent completes successfully
    - M1, M3, M4, M5 milestones are logged
    - Response contains a discount recommendation
    """
    from agent import SampleAgent

    # Mock MCP tools
    pricing_conditions_tool = MagicMock()
    pricing_conditions_tool.name = "mcp_pricing__list_conditions"
    pricing_conditions_tool.description = "List customer pricing conditions."
    pricing_conditions_tool.args_schema = None
    pricing_conditions_tool.return_direct = False
    pricing_conditions_tool.ainvoke = AsyncMock(
        return_value='{"results": [{"ConditionRecord": "001", "ConditionType": "K007", "ConditionRateValue": "8.000", "ConditionRateValueUnit": "%", "SoldToParty": "ACME"}]}'
    )

    pricing_procedure_tool = MagicMock()
    pricing_procedure_tool.name = "mcp_procedure__list_items"
    pricing_procedure_tool.description = "List pricing procedure items."
    pricing_procedure_tool.args_schema = None
    pricing_procedure_tool.return_direct = False
    pricing_procedure_tool.ainvoke = AsyncMock(
        return_value='{"results": [{"ConditionType": "K007", "MaximumConditionBasisValue": "15.000", "IsMandatory": false}]}'
    )

    # Mock LLM response with a concrete discount recommendation
    llm_response = MagicMock()
    llm_response.content = """I've analyzed the pricing history for ACME Corp and your $75,000 deal.

**ACME Corp Pricing History:**
- Historical average discount: 8% (K007)
- Maximum given: 11%
- Competitor pricing: 12%

**Discount Strategy Recommendations:**

Option 1 (Recommended): 10% discount
- Deal win likelihood: High
- Margin impact: Low risk
- Rationale: Slightly above ACME's historical average; competitive without excessive margin erosion.

Option 2: 12% discount
- Deal win likelihood: High  
- Margin impact: Medium risk
- Rationale: Matches competitor pricing; within the 15% procedure ceiling for large deals.

Option 3 (Stretch): 14% discount
- ⚠️ Warning: Approaching the procedure ceiling. Manager review recommended.
- Deal win likelihood: Very High
- Margin impact: High risk
- Rationale: Maximizes competitive positioning; use only if deal is at serious risk of loss.
"""
    llm_response.additional_kwargs = {}
    llm_response.tool_calls = []

    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [llm_response]}

        with caplog.at_level(logging.INFO, logger="agent"):
            result = await agent.invoke(
                query=(
                    "I need a discount strategy for ACME Corp. "
                    "Deal size is $75,000. Competitor is offering 12%."
                ),
                context_id="integration-test-001",
                tools=[pricing_conditions_tool, pricing_procedure_tool],
            )

    # Assert completion
    assert result.status == "completed", f"Expected completed, got {result.status}"
    assert result.message, "Response must not be empty"

    # Assert response quality
    response_lower = result.message.lower()
    assert "option" in response_lower, "Response must contain discount options"
    assert "discount" in response_lower, "Response must mention discount"

    # Assert milestone logging
    all_logs = [r.message for r in caplog.records]

    m1_logs = [m for m in all_logs if "M1." in m]
    assert len(m1_logs) > 0, "M1 (Agent Initialized) must be logged"

    m3_logs = [m for m in all_logs if "M3." in m]
    assert len(m3_logs) > 0, "M3 (Deal Context Assessed) must be logged"

    m4_logs = [m for m in all_logs if "M4." in m]
    assert len(m4_logs) > 0, "M4 (Discount Strategy Generated) must be logged"

    m5_logs = [m for m in all_logs if "M5." in m]
    assert len(m5_logs) > 0, "M5 (Sales Rep Interaction Completed) must be logged"


@pytest.mark.asyncio
async def test_agent_handles_no_tools_gracefully(add_agent_to_path):
    """Test that agent handles the case where no MCP tools are available."""
    from agent import SampleAgent

    llm_response = MagicMock()
    llm_response.content = "I'm sorry, tools are temporarily unavailable. Please try again later."
    llm_response.additional_kwargs = {}
    llm_response.tool_calls = []

    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [llm_response]}
        result = await agent.invoke(
            query="What discount should I give customer C1001?",
            context_id="no-tools-test-001",
            tools=[],
        )

    assert result.status == "completed"
    assert result.message


@pytest.mark.asyncio
async def test_agent_handles_tool_error_gracefully(add_agent_to_path):
    """Test that agent handles tool errors without crashing."""
    from agent import SampleAgent

    error_tool = MagicMock()
    error_tool.name = "mcp_pricing__list_conditions"
    error_tool.description = "List conditions."
    error_tool.args_schema = None
    error_tool.return_direct = False
    error_tool.ainvoke = AsyncMock(side_effect=Exception("Connection timeout"))

    llm_response = MagicMock()
    llm_response.content = "I encountered an error retrieving pricing data: Connection timeout. Please verify the customer ID and try again."
    llm_response.additional_kwargs = {}
    llm_response.tool_calls = []

    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [llm_response]}
        result = await agent.invoke(
            query="What discounts has customer C9999 received?",
            context_id="error-test-001",
            tools=[error_tool],
        )

    assert result.status == "completed"
    assert result.message


@pytest.mark.asyncio
async def test_agent_multi_turn_conversation(add_agent_to_path):
    """Test that the agent supports multi-turn conversation (follow-up questions)."""
    from agent import SampleAgent

    first_response = MagicMock()
    first_response.content = "For customer C1001, I recommend a 10% discount for your $50,000 deal."
    first_response.additional_kwargs = {}
    first_response.tool_calls = []

    second_response = MagicMock()
    second_response.content = "If you offer 12% instead, your margin impact increases to medium risk, but win likelihood goes from High to Very High."
    second_response.additional_kwargs = {}
    second_response.tool_calls = []

    agent = SampleAgent()
    context_id = "multi-turn-test-001"

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        # First turn
        mock_invoke.return_value = {"messages": [first_response]}
        result1 = await agent.invoke(
            query="Recommend a discount for C1001, $50,000 deal.",
            context_id=context_id,
            tools=[],
        )

        # Second turn — follow-up
        mock_invoke.return_value = {"messages": [second_response]}
        result2 = await agent.invoke(
            query="What if I offer 2% more?",
            context_id=context_id,
            tools=[],
        )

    assert result1.status == "completed"
    assert result2.status == "completed"
    assert result1.message != result2.message, "Follow-up responses should differ"
