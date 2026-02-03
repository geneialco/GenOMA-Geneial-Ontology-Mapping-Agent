"""
AWS Lambda handler for GenOMA API.

NOTE: This module is only used for AWS deployment.
If you're running GenOMA locally or in notebooks, you can ignore this file.
See main.py for a local FastAPI server reference implementation.

This module provides the Lambda entry point that processes API Gateway events
and invokes the LangGraph-based ontology mapping workflow.
"""

import json
import logging
import time
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
    # Get API Gateway request ID (Lambda request ID is auto-logged by CloudWatch)
    request_id = event.get("requestContext", {}).get("requestId", "")
    
    start_time = time.time()
    
    # HTTP API v2.0 format
    http_method = event["requestContext"]["http"]["method"]
    path = event["requestContext"]["http"]["path"]
    
    logger.info(
        f"Request received - method: {http_method}, path: {path}, "
        f"request_id: {request_id}"
    )

    # CORS headers for all responses
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    }

    # Handle OPTIONS preflight requests
    if http_method == "OPTIONS":
        logger.debug(f"OPTIONS preflight request - request_id: {request_id}")
        return {"statusCode": 200, "headers": headers, "body": ""}

    # Route requests
    try:
        if path == "/health" and http_method == "GET":
            return _handle_health(headers, request_id)
        elif path == "/map" and http_method == "POST":
            return _handle_map(event, headers, request_id, start_time)
        else:
            logger.warning(
                f"Unknown route - method: {http_method}, path: {path}, "
                f"request_id: {request_id}"
            )
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": f"Not found: {http_method} {path}"}),
            }
    except Exception:
        elapsed = time.time() - start_time
        logger.exception(
            f"Unhandled exception in lambda_handler - request_id: {request_id}, "
            f"elapsed: {elapsed:.2f}s"
        )
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal server error"}),
        }


def _handle_health(headers: dict, request_id: str) -> dict:
    """
    Handle health check endpoint.

    Parameters:
        headers (dict): Response headers to include
        request_id (str): Lambda request ID for logging

    Returns:
        dict: API Gateway response with health status.
    """
    logger.info(f"Health check - request_id: {request_id}")
    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps({"status": "healthy", "service": "genoma-api"}),
    }


def _handle_map(event: dict, headers: dict, request_id: str, start_time: float) -> dict:
    """
    Handle the /map endpoint for ontology mapping.

    Parses the request body, invokes the LangGraph workflow, and returns
    the mapping results.

    Parameters:
        event (dict): API Gateway event containing request body.
        headers (dict): Response headers to include.
        request_id (str): Lambda request ID for logging.
        start_time (float): Request start timestamp.

    Returns:
        dict: API Gateway response with mapping results or error.
    """
    # Import here to avoid cold start overhead on health checks
    from src.graph.builder import build_umls_mapper_graph

    # Parse request body
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError as e:
        elapsed = time.time() - start_time
        logger.error(
            f"Invalid JSON in request body - request_id: {request_id}, "
            f"error: {e}, elapsed: {elapsed:.2f}s"
        )
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": f"Invalid JSON: {e}"}),
        }

    # Validate required fields
    text = body.get("text")
    field_type = body.get("field_type")
    ontology = body.get("ontology", "HPO")

    if not text or not field_type:
        elapsed = time.time() - start_time
        missing = [k for k, v in [("text", text), ("field_type", field_type)] if not v]
        logger.error(
            f"Missing required fields - request_id: {request_id}, "
            f"missing: {missing}, elapsed: {elapsed:.2f}s"
        )
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps(
                {"error": "Missing required fields: 'text' and 'field_type'"}
            ),
        }
    
    # Log request details (truncate long text for readability)
    text_preview = text[:100] + "..." if len(text) > 100 else text
    logger.info(
        f"Mapping request - request_id: {request_id}, field_type: {field_type}, "
        f"ontology: {ontology}, text_preview: {text_preview}"
    )

    # Build and invoke the graph
    graph_build_start = time.time()
    try:
        graph = build_umls_mapper_graph()
        graph_build_time = time.time() - graph_build_start
        logger.debug(
            f"Graph built - request_id: {request_id}, "
            f"build_time: {graph_build_time:.2f}s"
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.exception(
            f"Failed to build mapping graph - request_id: {request_id}, "
            f"elapsed: {elapsed:.2f}s"
        )
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

    # Invoke the graph workflow
    graph_invoke_start = time.time()
    try:
        result_state = graph.invoke(initial_state)
        graph_invoke_time = time.time() - graph_invoke_start
        total_time = time.time() - start_time
        
        # Log workflow results summary
        is_mappable = result_state.get("is_mappable", False)
        validated_count = len(result_state.get("validated_mappings", []))
        retry_count = result_state.get("retry_count", 0)
        
        logger.info(
            f"Graph completed - request_id: {request_id}, "
            f"is_mappable: {is_mappable}, validated_mappings: {validated_count}, "
            f"retry_count: {retry_count}, graph_time: {graph_invoke_time:.2f}s, "
            f"total_time: {total_time:.2f}s"
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.exception(
            f"Graph invocation failed - request_id: {request_id}, "
            f"elapsed: {elapsed:.2f}s"
        )
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": f"Graph invocation failed: {e}"}),
        }

    # Extract and normalize results
    validated = result_state.get("validated_mappings", [])
    if not validated:
        validated = result_state.get("ranked_mappings", [])
        logger.debug(
            f"Using ranked_mappings as fallback - request_id: {request_id}, "
            f"count: {len(validated)}"
        )

    normalized = []
    if isinstance(validated, list):
        for item in validated:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "code": item.get("best_match_code")
                    or item.get("code")
                    or item.get("id")
                    or "",
                    "term": item.get("best_match_term")
                    or item.get("term")
                    or item.get("label")
                    or "",
                    "description": item.get("description") or item.get("def"),
                    "confidence": item.get("confidence"),
                }
            )

    response_body = {
        "input": initial_state,
        "validated_mappings": normalized,
        "raw_state": result_state,
    }

    # Log response summary
    response_size = len(json.dumps(response_body, default=str))
    total_time = time.time() - start_time
    logger.info(
        f"Request completed - request_id: {request_id}, "
        f"status: 200, mappings_count: {len(normalized)}, "
        f"response_size: {response_size} bytes, total_time: {total_time:.2f}s"
    )

    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps(response_body, default=str),
    }
