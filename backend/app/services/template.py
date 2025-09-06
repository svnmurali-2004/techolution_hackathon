import json
from typing import List, Dict
import uuid

templates = [
    {"id": "default", "template": ["Executive Summary", "Introduction", "Key Insights", "Recommendations"]}
]

def list_templates() -> List[Dict]:
    return templates

def create_template(template_json: Dict) -> Dict:
    template_id = str(uuid.uuid4())
    template_json["id"] = template_id
    templates.append(template_json)
    return {"status": "created", "template": template_json}

def update_template(template_id: str, new_template: Dict) -> Dict:
    for t in templates:
        if t["id"] == template_id:
            t["template"] = new_template["template"]
            return {"status": "updated", "template": t}
    return {"error": "Template not found"}

def delete_template(template_id: str) -> Dict:
    global templates
    templates = [t for t in templates if t["id"] != template_id]
    return {"status": "deleted", "id": template_id}
