# src/lambda_handler.py
"""
AWS Lambda handler for GenOMA API.

This module provides the Lambda entry point that processes API Gateway events
and invokes the LangGraph-based ontology mapping workflow.
"""

import json
import logging
from typing import Any, cast

# Configure logging for CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context: Any) -> dict:
    """
    AWS Lambda handler for API Gateway proxy integration.

    Processes incoming HTTP requests from API Gateway, routes them to the
    appropriate handler, and returns a properly formatted response.

    Parameters:
        event (dict): API Gateway proxy event containing request data.
        context (Any): Lambda context object with runtime information.

    Returns:
        dict: API Gateway proxy response with statusCode, headers, and body.
    """
    logger.info("Received event: %s", json.dumps(event, default=str))

    http_method = event.get("httpMethod", "")
    path = event.get("path", "")

    # CORS headers for all responses
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    }

    # Handle OPTIONS preflight requests
    if http_method == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    # Route requests
    if path == "/health" and http_method == "GET":
        return _handle_health(headers)
    elif path == "/map" and http_method == "POST":
        return _handle_map(event, headers)
    else:
        return {
            "statusCode": 404,
            "headers": headers,
            "body": json.dumps({"error": f"Not found: {http_method} {path}"}),
        }


def _handle_health(headers: dict) -> dict:
    """
    Handle health check endpoint.

    Parameters:
        headers (dict): Response headers to include.

    Returns:
        dict: API Gateway response with health status.
    """
    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps({"status": "healthy", "service": "genoma-api"}),
    }


def _handle_map(event: dict, headers: dict) -> dict:
    """
    Handle the /map endpoint for ontology mapping.

    Parses the request body, invokes the LangGraph workflow, and returns
    the mapping results.

    Parameters:
        event (dict): API Gateway event containing request body.
        headers (dict): Response headers to include.

    Returns:
        dict: API Gateway response with mapping results or error.
    """
    # Import here to avoid cold start overhead on health checks
    from src.graph.builder import build_umls_mapper_graph

    # Parse request body
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in request body: %s", e)
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": f"Invalid JSON: {e}"}),
        }

    # Validate required fields
    text = body.get("text")
    field_type = body.get("field_type")

    if not text or not field_type:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps(
                {"error": "Missing required fields: 'text' and 'field_type'"}
            ),
        }

    ontology = body.get("ontology", "HPO")

    # Build and invoke the graph
    try:
        graph = build_umls_mapper_graph()
    except Exception as e:
        logger.exception("Failed to build mapping graph")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": f"Failed to build mapping graph: {e}"}),
        }

    # Import MappingState for type casting
    from src.graph.types import MappingState

    initial_state = cast(
        MappingState,
        {
            "text": text,
            "field_type": field_type,
            "ontology": ontology,
        },
    )

    try:
        logger.info("Invoking graph with state: %s", initial_state)
        result_state = graph.invoke(initial_state)
        logger.info("Graph completed successfully")
    except Exception as e:
        logger.exception("Graph invocation failed")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": f"Graph invocation failed: {e}"}),
        }

    # Extract and normalize results
    validated = result_state.get("validated_mappings", [])
    if not validated:
        validated = result_state.get("ranked_mappings", [])

    normalized = []
    if isinstance(validated, list):
        for item in validated:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "code": item.get("code") or item.get("id") or "",
                    "term": item.get("term") or item.get("label") or "",
                    "description": item.get("description") or item.get("def"),
                    "confidence": item.get("confidence"),
                }
            )

    response_body = {
        "input": initial_state,
        "validated_mappings": normalized,
        "raw_state": result_state,
    }

    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps(response_body, default=str),
    }
