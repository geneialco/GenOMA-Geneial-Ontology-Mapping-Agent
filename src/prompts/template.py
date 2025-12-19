"""
Prompt template rendering utilities for the UMLS Mapping LangGraph-based Agent.
This module handles loading and rendering Jinja2 templates for LLM prompts.
"""

import os
from typing import Any, Mapping

from jinja2 import Template

# Directory containing all prompt template files
PROMPT_DIR = os.path.dirname(__file__)


def get_prompt_template(prompt_name: str) -> Template:
    """
    Load a Jinja2 template from the prompts directory.

    Args:
        prompt_name: Name of the template file (without .md extension)

    Returns:
        Jinja2 template object ready for rendering

    Raises:
        FileNotFoundError: If the template file doesn't exist
    """
    template_path = os.path.join(PROMPT_DIR, f"{prompt_name}.md")
    with open(template_path, "r") as f:
        template = Template(f.read())
    return template


def apply_prompt_template(prompt_name: str, state: Mapping[str, Any]) -> str:
    """
    Render a prompt template with the given state variables.

    Args:
        prompt_name: Name of the template file (without .md extension)
        state: Mapping of variables to inject into the template (dict or TypedDict)

    Returns:
        Rendered prompt string ready for LLM consumption
    """
    prompt_template = get_prompt_template(prompt_name)
    rendered_prompt = prompt_template.render(**state)
    return rendered_prompt
