from docx import Document
from reportlab.pdfgen import canvas
import tempfile
import os
## REMOVED: from app.services.generator import reports

def export_report(report_id: str, format: str):
    from app.services.generator import preview
    # Use the preview function to get the existing report
    result = preview(report_id)
    if "error" in result:
        return {"error": f"Report not found: {result['error']}"}
    
    report = result["preview"]
    # Format the sections for export
    content = {}
    for section in report["sections"]:
        title = section["title"]
        text_content = ""
        for item in section["content"]:
            # Clean text content to handle Unicode properly
            clean_text = str(item["text"]).encode('utf-8', errors='ignore').decode('utf-8')
            text_content += clean_text + "\n\n"
            if item.get("citations"):
                text_content += "Citations:\n"
                for citation in item["citations"]:
                    clean_snippet = str(citation.get('snippet', '')).encode('utf-8', errors='ignore').decode('utf-8')
                    text_content += f"- {citation.get('source_id')}, Page {citation.get('page')}: {clean_snippet[:100]}...\n"
        content[title] = text_content
    if format == "docx":
        doc = Document()
        for section, text in content.items():
            doc.add_heading(section, level=1)
            doc.add_paragraph(text)
        tmp_path = tempfile.mktemp(suffix=".docx")
        doc.save(tmp_path)
        with open(tmp_path, "rb") as f:
            data = f.read()
        os.remove(tmp_path)
        return {"report_id": report_id, "format": format, "file": data}
    elif format == "pdf":
        tmp_path = tempfile.mktemp(suffix=".pdf")
        c = canvas.Canvas(tmp_path)
        y = 800
        for section, text in content.items():
            c.drawString(50, y, section)
            y -= 20
            for line in text.splitlines():
                c.drawString(70, y, line)
                y -= 15
            y -= 10
        c.save()
        with open(tmp_path, "rb") as f:
            data = f.read()
        os.remove(tmp_path)
        return {"report_id": report_id, "format": format, "file": data}
    else:
        return {"error": "Unsupported export format"}
