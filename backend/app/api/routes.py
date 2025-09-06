from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services import parser, template, generator, export
from pydantic import BaseModel

class GenerateRequest(BaseModel):
	template_id: str
	query: str

router = APIRouter()

@router.post('/upload')
async def upload_file(file: UploadFile = File(...)):
	return await parser.parse_file(file)

@router.get('/templates')
def get_templates():
	return template.list_templates()

@router.post('/templates')
def create_template(template_json: dict):
	return template.create_template(template_json)

@router.post('/generate')
def generate_report(req: GenerateRequest):
	sections = ["Executive Summary", "Key Findings", "Recommendations"]
	return generator.generate_report_from_query(sections, req.query, top_k=3)

@router.get('/preview/{report_id}')
def preview_report(report_id: str):
	return generator.preview(report_id)

@router.get('/export/{report_id}')
def export_report(report_id: str, format: str):
	return export.export_report(report_id, format)
