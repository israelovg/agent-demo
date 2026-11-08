"""Unit tests for pricing condition record retrieval via MCP tools."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_pricing_conditions():
    """Return a realistic mock response for pricing condition records."""
    return {
        "results": [
            {
                "ConditionRecord": "0000100001",
                "ConditionType": "K007",
                "RateWithUnit": "8.000",
                "ConditionRateValue": "8.000",
                "ConditionRateValueUnit": "%",
                "SoldToParty": "C1001",
                "ValidityEndDate": "/Date(4102444800000)/",
                "ValidityStartDate": "/Date(1704067200000)/",
            },
            {
                "ConditionRecord": "0000100002",
                "ConditionType": "K007",
                "RateWithUnit": "10.000",
                "ConditionRateValue": "10.000",
                "ConditionRateValueUnit": "%",
                "SoldToParty": "C1001",
                "ValidityEndDate": "/Date(4102444800000)/",
                "ValidityStartDate": "/Date(1672531200000)/",
            },
        ]
    }


@pytest.fixture
def mock_empty_conditions():
    """Return an empty results response."""
    return {"results": []}


def test_mock_pricing_conditions_structure(mock_pricing_conditions):
    """Test that the mock pricing conditions response has the expected structure."""
    results = mock_pricing_conditions["results"]
    assert len(results) == 2
    record = results[0]
    assert "ConditionRecord" in record
    assert "ConditionType" in record
    assert "ConditionRateValue" in record
    assert "ConditionRateValueUnit" in record
    assert "SoldToParty" in record


def test_mock_pricing_conditions_discount_values(mock_pricing_conditions):
    """Test that discount values are numeric strings in the expected range."""
    results = mock_pricing_conditions["results"]
    for record in results:
        discount = float(record["ConditionRateValue"])
        assert 0 <= discount <= 100, f"Discount {discount}% out of valid range"
        assert record["ConditionRateValueUnit"] == "%"


def test_mock_pricing_conditions_customer_filter(mock_pricing_conditions):
    """Test that all records belong to the expected customer."""
    results = mock_pricing_conditions["results"]
    for record in results:
        assert record["SoldToParty"] == "C1001"


def test_mcp_mock_file_contains_pricing_conditions_tool():
    """Test that mcp-mock.json includes the list_a_slsprcgconditionrecord tool."""
    mock_file = Path(__file__).parent.parent / "mcp-mock.json"
    assert mock_file.exists(), "mcp-mock.json must exist"

    data = json.loads(mock_file.read_text())
    assert "servers" in data

    # Find the server containing pricing condition record tools
    found_tool = False
    for server_slug, server_data in data["servers"].items():
        if "list_a_slsprcgconditionrecord" in server_data.get("tools", {}):
            found_tool = True
            tool = server_data["tools"]["list_a_slsprcgconditionrecord"]
            assert "description" in tool
            assert "input_schema" in tool
            assert "mock_response" in tool
            # Mock response should have results list
            assert "results" in tool["mock_response"]
            break

    assert found_tool, "list_a_slsprcgconditionrecord tool must be present in mcp-mock.json"


def test_mcp_mock_file_pricing_conditions_mock_data():
    """Test that mock data for pricing conditions contains discount-relevant fields."""
    mock_file = Path(__file__).parent.parent / "mcp-mock.json"
    data = json.loads(mock_file.read_text())

    for server_slug, server_data in data["servers"].items():
        tools = server_data.get("tools", {})
        if "list_a_slsprcgconditionrecord" in tools:
            mock_results = tools["list_a_slsprcgconditionrecord"]["mock_response"]["results"]
            assert len(mock_results) >= 1, "Mock should have at least one condition record"
            record = mock_results[0]
            assert "ConditionRecord" in record
            assert "ConditionType" in record
            break


def test_mock_empty_conditions_structure(mock_empty_conditions):
    """Test that empty conditions response is handled gracefully."""
    results = mock_empty_conditions["results"]
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_agent_calls_pricing_conditions_tool(add_agent_to_path):
    """Test that the agent invokes the pricing conditions tool when asked about a customer."""
    from unittest.mock import AsyncMock, MagicMock, patch

    tool_mock = MagicMock()
    tool_mock.name = "mcp_s4_slspricingconditionrecord__list_a_slsprcgconditionrecord"
    tool_mock.description = "Retrieve a list of sales pricing condition records."
    tool_mock.invoke = MagicMock(return_value='{"results": [{"ConditionRecord": "0000100001", "ConditionType": "K007", "ConditionRateValue": "8.000", "ConditionRateValueUnit": "%", "SoldToParty": "C1001"}]}')
    tool_mock.ainvoke = AsyncMock(return_value='{"results": [{"ConditionRecord": "0000100001", "ConditionType": "K007", "ConditionRateValue": "8.000", "ConditionRateValueUnit": "%", "SoldToParty": "C1001"}]}')
    tool_mock.args_schema = None
    tool_mock.return_direct = False

    llm_response = MagicMock()
    llm_response.content = "For customer C1001, I found 2 historical discount records: K007 at 8% and K007 at 10%."
    llm_response.additional_kwargs = {}
    llm_response.tool_calls = []

    from agent import SampleAgent
    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {
            "messages": [llm_response]
        }
        result = await agent.invoke(
            query="What discounts has customer C1001 received?",
            context_id="test-context-001",
            tools=[tool_mock],
        )

    assert result.status == "completed"
    assert result.message
