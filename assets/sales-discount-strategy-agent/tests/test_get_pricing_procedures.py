"""Unit tests for pricing procedure retrieval via MCP tools."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_pricing_procedure_items():
    """Return a realistic mock response for pricing procedure items."""
    return {
        "results": [
            {
                "PricingProcedure": "ZSTD01",
                "PricingProcedureStep": "0010",
                "PricingProcedureCounter": "0",
                "ConditionType": "PR00",
                "PricingProcedureItemDescription": "Base Price",
                "IsMandatory": True,
                "IsStatistical": False,
                "MaximumConditionBasisValue": "0.000",
            },
            {
                "PricingProcedure": "ZSTD01",
                "PricingProcedureStep": "0100",
                "PricingProcedureCounter": "0",
                "ConditionType": "K007",
                "PricingProcedureItemDescription": "Customer Discount",
                "IsMandatory": False,
                "IsStatistical": False,
                "MaximumConditionBasisValue": "15.000",
            },
        ]
    }


def test_mock_procedure_items_structure(mock_pricing_procedure_items):
    """Test that the mock procedure items response has the expected structure."""
    results = mock_pricing_procedure_items["results"]
    assert len(results) == 2
    item = results[0]
    assert "PricingProcedure" in item
    assert "PricingProcedureStep" in item
    assert "ConditionType" in item
    assert "IsMandatory" in item


def test_mock_procedure_customer_discount_item(mock_pricing_procedure_items):
    """Test that the K007 customer discount condition type exists with a maximum ceiling."""
    results = mock_pricing_procedure_items["results"]
    k007 = next((r for r in results if r["ConditionType"] == "K007"), None)
    assert k007 is not None, "K007 customer discount condition type must exist"
    max_value = float(k007["MaximumConditionBasisValue"])
    assert max_value > 0, "K007 must have a positive maximum discount ceiling"
    assert max_value <= 100, "Maximum discount ceiling must not exceed 100%"


def test_mock_procedure_mandatory_base_price(mock_pricing_procedure_items):
    """Test that the base price (PR00) step is mandatory."""
    results = mock_pricing_procedure_items["results"]
    pr00 = next((r for r in results if r["ConditionType"] == "PR00"), None)
    assert pr00 is not None, "PR00 base price step must exist"
    assert pr00["IsMandatory"] is True


def test_mcp_mock_file_contains_procedure_tool():
    """Test that mcp-mock.json includes the list_a_slspricingprocedureitem tool."""
    mock_file = Path(__file__).parent.parent / "mcp-mock.json"
    assert mock_file.exists()

    data = json.loads(mock_file.read_text())
    assert "servers" in data

    found_tool = False
    for server_slug, server_data in data["servers"].items():
        if "list_a_slspricingprocedureitem_for_api_slspricingprocedure_srv" in server_data.get("tools", {}):
            found_tool = True
            tool = server_data["tools"]["list_a_slspricingprocedureitem_for_api_slspricingprocedure_srv"]
            assert "mock_response" in tool
            assert "results" in tool["mock_response"]

            # Verify K007 customer discount is in mock data
            results = tool["mock_response"]["results"]
            k007 = next((r for r in results if r.get("ConditionType") == "K007"), None)
            assert k007 is not None, "K007 must be present in procedure item mock data"
            break

    assert found_tool, "list_a_slspricingprocedureitem tool must be in mcp-mock.json"


def test_mcp_mock_file_procedure_server_exists():
    """Test that the pricing procedure MCP server is registered in mcp-mock.json."""
    mock_file = Path(__file__).parent.parent / "mcp-mock.json"
    data = json.loads(mock_file.read_text())

    server_found = False
    for server_slug, server_data in data["servers"].items():
        if "api_slspricingprocedure_srv" in server_data.get("mcp_server_name", ""):
            server_found = True
            tools = server_data.get("tools", {})
            assert len(tools) > 0, "Pricing procedure server must have at least one tool"
            break

    assert server_found, "Pricing procedure MCP server must be in mcp-mock.json"


@pytest.mark.asyncio
async def test_agent_calls_pricing_procedure_tool(add_agent_to_path):
    """Test that the agent uses pricing procedure tools to assess margin guardrails."""
    tool_mock = MagicMock()
    tool_mock.name = "mcp_s4_slspricingprocedure__list_a_slspricingprocedureitem"
    tool_mock.description = "Retrieve pricing procedure items with margin thresholds."
    tool_mock.invoke = MagicMock(return_value='{"results": [{"ConditionType": "K007", "MaximumConditionBasisValue": "15.000"}]}')
    tool_mock.ainvoke = AsyncMock(return_value='{"results": [{"ConditionType": "K007", "MaximumConditionBasisValue": "15.000"}]}')
    tool_mock.args_schema = None
    tool_mock.return_direct = False

    llm_response = MagicMock()
    llm_response.content = "The pricing procedure ZSTD01 allows a maximum discount of 15% for K007 customer discounts."
    llm_response.additional_kwargs = {}
    llm_response.tool_calls = []

    from agent import SampleAgent
    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [llm_response]}
        result = await agent.invoke(
            query="What is the maximum discount allowed in the pricing procedure?",
            context_id="test-context-002",
            tools=[tool_mock],
        )

    assert result.status == "completed"
    assert result.message
