"""Unit tests for discount strategy recommendation generation."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def discount_recommendation_response():
    """A realistic multi-option discount recommendation response."""
    return """Based on customer C1001's pricing history and your $75,000 deal:

**Discount Strategy Recommendations:**

Option 1 (Recommended): 10% discount
- Deal win likelihood: High
- Margin impact: Low risk
- Rationale: Matches customer's historical average of 8-10% for similar deal sizes.

Option 2: 12% discount
- Deal win likelihood: High
- Margin impact: Medium risk
- Rationale: Matches competitor pricing of 12%, within the 15% ceiling for large deals.

Option 3 (Stretch): 14% discount
- ⚠️ Warning: Approaching the standard ceiling for this deal tier. Consider manager review.
- Deal win likelihood: Very High
- Margin impact: High risk
- Rationale: Maximizes competitive positioning but reduces margin significantly.
"""


@pytest.fixture
def guardrail_triggered_response():
    """A response where the guardrail warning is triggered."""
    return """⚠️ Warning: The requested discount of 22% exceeds the standard strategic ceiling of 20%.
    
This deal requires manager approval before quoting. I recommend escalating to your sales manager.

If approved, the maximum I can recommend is 20%."""


def test_recommendation_contains_multiple_options(discount_recommendation_response):
    """Test that the recommendation contains at least 2 options."""
    response = discount_recommendation_response.lower()
    option_count = response.count("option")
    assert option_count >= 2, f"Expected at least 2 options, found {option_count}"


def test_recommendation_contains_rationale(discount_recommendation_response):
    """Test that each option includes a rationale."""
    assert "rationale" in discount_recommendation_response.lower()


def test_recommendation_contains_margin_info(discount_recommendation_response):
    """Test that the recommendation includes margin impact information."""
    response = discount_recommendation_response.lower()
    assert "margin" in response


def test_recommendation_contains_win_likelihood(discount_recommendation_response):
    """Test that the recommendation includes deal win likelihood."""
    response = discount_recommendation_response.lower()
    assert "likelihood" in response or "win" in response


def test_guardrail_triggered_contains_warning(guardrail_triggered_response):
    """Test that the guardrail response contains a warning."""
    assert "⚠️" in guardrail_triggered_response or "warning" in guardrail_triggered_response.lower()


def test_guardrail_mentions_approval(guardrail_triggered_response):
    """Test that the guardrail response mentions manager approval."""
    response = guardrail_triggered_response.lower()
    assert "approval" in response or "manager" in response or "escalat" in response


@pytest.mark.asyncio
async def test_agent_generates_discount_strategy(add_agent_to_path):
    """Integration test: agent generates a discount strategy recommendation."""
    from agent import SampleAgent

    pricing_tool = MagicMock()
    pricing_tool.name = "mcp_s4_pricing__list_a_slsprcgconditionrecord"
    pricing_tool.description = "Retrieve customer pricing condition records."
    pricing_tool.invoke = MagicMock(return_value='{"results": [{"ConditionRecord": "001", "ConditionType": "K007", "ConditionRateValue": "8.000", "ConditionRateValueUnit": "%", "SoldToParty": "C1001"}]}')
    pricing_tool.ainvoke = AsyncMock(return_value='{"results": [{"ConditionRecord": "001", "ConditionType": "K007", "ConditionRateValue": "8.000", "ConditionRateValueUnit": "%", "SoldToParty": "C1001"}]}')
    pricing_tool.args_schema = None
    pricing_tool.return_direct = False

    procedure_tool = MagicMock()
    procedure_tool.name = "mcp_s4_procedure__list_a_slspricingprocedureitem"
    procedure_tool.description = "Retrieve pricing procedure items."
    procedure_tool.invoke = MagicMock(return_value='{"results": [{"ConditionType": "K007", "MaximumConditionBasisValue": "15.000"}]}')
    procedure_tool.ainvoke = AsyncMock(return_value='{"results": [{"ConditionType": "K007", "MaximumConditionBasisValue": "15.000"}]}')
    procedure_tool.args_schema = None
    procedure_tool.return_direct = False

    llm_response = MagicMock()
    llm_response.content = """Based on pricing history for customer C1001 and your $75,000 deal:

Option 1 (Recommended): 10% discount
- Deal win likelihood: High  
- Margin impact: Low risk
- Rationale: Aligns with customer's average historical discount of 8%.

Option 2: 12% discount  
- Deal win likelihood: High
- Margin impact: Medium risk
- Rationale: Matches competitor pricing, within 15% ceiling.
"""
    llm_response.additional_kwargs = {}
    llm_response.tool_calls = []

    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [llm_response]}
        result = await agent.invoke(
            query="Recommend a discount for customer C1001, $75,000 deal. Competitor at 12%.",
            context_id="test-discount-003",
            tools=[pricing_tool, procedure_tool],
        )

    assert result.status == "completed"
    assert "option" in result.message.lower()
    assert "discount" in result.message.lower()


@pytest.mark.asyncio
async def test_agent_m4_milestone_logged(add_agent_to_path, caplog):
    """Test that M4.achieved milestone is logged when discount strategy is generated."""
    import logging
    from agent import SampleAgent

    llm_response = MagicMock()
    llm_response.content = "Option 1: 10% discount. Option 2: 12% discount. Recommended option 1 for better margin."
    llm_response.additional_kwargs = {}
    llm_response.tool_calls = []

    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [llm_response]}
        with caplog.at_level(logging.INFO, logger="agent"):
            result = await agent.invoke(
                query="I need a discount for customer C1001 on a $50,000 deal.",
                context_id="test-milestone-004",
                tools=[],
            )

    assert result.status == "completed"
    milestone_logs = [r.message for r in caplog.records if "M4." in r.message]
    assert len(milestone_logs) > 0, "M4 milestone must be logged"


@pytest.mark.asyncio
async def test_agent_m5_milestone_logged(add_agent_to_path, caplog):
    """Test that M5.achieved milestone is logged when session completes."""
    import logging
    from agent import SampleAgent

    llm_response = MagicMock()
    llm_response.content = "I recommend a 10% discount for this deal."
    llm_response.additional_kwargs = {}
    llm_response.tool_calls = []

    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [llm_response]}
        with caplog.at_level(logging.INFO, logger="agent"):
            result = await agent.invoke(
                query="What discount should I offer?",
                context_id="test-milestone-005",
                tools=[],
            )

    assert result.status == "completed"
    m5_logs = [r.message for r in caplog.records if "M5." in r.message]
    assert len(m5_logs) > 0, "M5 milestone must be logged"
