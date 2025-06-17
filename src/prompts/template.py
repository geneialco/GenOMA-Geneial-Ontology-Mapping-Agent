import os
from jinja2 import Template
from typing import Dict, Any

PROMPT_DIR = os.path.dirname(__file__)  

def get_prompt_template(prompt_name: str) -> Template:
    template_path = os.path.join(PROMPT_DIR, f"{prompt_name}.md")
    with open(template_path, "r") as f:
        template = Template(f.read())
    return template

def apply_prompt_template(prompt_name: str, state: Dict[str, Any]) -> str:
    prompt_template = get_prompt_template(prompt_name)
    rendered_prompt = prompt_template.render(**state)
    return rendered_prompt
