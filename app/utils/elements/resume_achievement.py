from reportlab.platypus import Paragraph
from app.constants.resume_constants import JOB_DETAILS_PARAGRAPH_STYLE
from docx.shared import Pt

class Achievement:
    def __init__(self, elements=[]) -> None:
        self.elements = elements

    def set_elements(self, elements : list) -> None:
        self.elements = elements

    def append_element(self, element : str) -> None:
        self.elements.append(element)

    def get_table_element(self, running_row_index : list, table_styles : list) -> list:
        """Render achievements as bullet points in PDF"""
        table = []
        for achievement in self.elements:
            if achievement:
                table.append([
                    Paragraph(f"• {achievement}", style=JOB_DETAILS_PARAGRAPH_STYLE), ''
                ])
                table_styles.append(('TOPPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 0))
                table_styles.append(('BOTTOMPADDING', (0, running_row_index[0]), (1, running_row_index[0]), 0))
                table_styles.append(('SPAN', (0, running_row_index[0]), (1, running_row_index[0])))
                running_row_index[0] += 1
        return table

    def get_docx_content(self, doc):
        """Add achievement content to DOCX document"""
        for achievement in self.elements:
            if achievement:
                achievement_paragraph = doc.add_paragraph(achievement, style='List Bullet')
                achievement_run = achievement_paragraph.runs[0] if achievement_paragraph.runs else achievement_paragraph.add_run()
                achievement_run.font.size = Pt(11)
                achievement_run.font.name = 'Calibri'