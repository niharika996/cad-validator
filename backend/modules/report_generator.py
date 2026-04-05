"""
Module 4: Report Generator
Generates PDF reports of validation results.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import os
from datetime import datetime

def generate_pdf_report(data: dict) -> str:
    """
    Generate a PDF report from validation results.
    Returns the file path to the generated PDF.
    """
    
    # Create reports directory if it doesn't exist
    reports_dir = 'reports'
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"validation_report_{timestamp}.pdf"
    filepath = os.path.join(reports_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4, 
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1E3A5F'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2E6DA4'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    story = []
    
    # Title
    story.append(Paragraph("CAD Validation Report", title_style))
    story.append(Spacer(1, 10))
    
    # File info
    filename = data.get('filename', 'Unknown')
    story.append(Paragraph(f"<b>File:</b> {filename}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Compliance Score
    score = data.get('compliance_score', 0)
    score_color = '#27AE60' if score >= 80 else '#E67E22' if score >= 60 else '#C0392B'
    score_style = ParagraphStyle(
        'ScoreStyle',
        parent=styles['Normal'],
        fontSize=36,
        textColor=colors.HexColor(score_color),
        alignment=1
    )
    story.append(Paragraph(f"<b>Compliance Score: {score}/100</b>", score_style))
    story.append(Spacer(1, 20))
    
    # Geometry Information
    story.append(Paragraph("Part Information", heading_style))
    geo = data.get('geometry', {})
    ai = data.get('ai_analysis', {})
    
    geo_data = [
        ['Property', 'Value', 'Property', 'Value'],
        ['Part Type (AI)', ai.get('part_type', 'Unknown'), 'Confidence', ai.get('part_type_confidence', 'N/A')],
        ['Length', f"{geo.get('length_mm', 0)} mm", 'Width', f"{geo.get('width_mm', 0)} mm"],
        ['Height', f"{geo.get('height_mm', 0)} mm", 'Volume', f"{geo.get('volume_mm3', 0)} mm³"],
        ['Est. Weight', f"{geo.get('estimated_weight_g', 0)} g", 'Surface Area', f"{geo.get('surface_area_mm2', 0)} mm²"],
        ['Min Wall Thickness', f"{geo.get('min_wall_thickness_mm', 0)} mm", 'Holes Detected', str(geo.get('hole_count', 0))],
        ['Sharp Edges', str(geo.get('sharp_edge_count', 0)), 'Watertight', '✓' if geo.get('is_watertight') else '✗'],
        ['Manufacturability', ai.get('manufacturability_score', 'N/A'), 'Symmetric', '✓' if geo.get('is_symmetric') else '✗'],
    ]
    
    table = Table(geo_data, colWidths=[60*mm, 50*mm, 60*mm, 50*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A5F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # AI Design Assessment
    story.append(Paragraph("AI Design Assessment", heading_style))
    story.append(Paragraph(ai.get('design_summary', 'No AI analysis available'), styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Part type reasoning:</b> {ai.get('part_type_reasoning', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Violations
    all_violations = data.get('rule_violations', []) + ai.get('ai_violations', [])
    critical_count = sum(1 for v in all_violations if v.get('severity') == 'CRITICAL')
    warning_count = sum(1 for v in all_violations if v.get('severity') == 'WARNING')
    info_count = sum(1 for v in all_violations if v.get('severity') == 'INFO')
    
    story.append(Paragraph(f"Violations Found: {critical_count} Critical | {warning_count} Warnings | {info_count} Info", heading_style))
    
    for v in all_violations:
        severity = v.get('severity', 'INFO')
        color = '#C0392B' if severity == 'CRITICAL' else '#E67E22' if severity == 'WARNING' else '#2980B9'
        
        story.append(Paragraph(f"<b><font color='{color}'>{severity}: {v.get('rule', 'Unknown')}</font></b>", styles['Normal']))
        story.append(Paragraph(f"<b>Issue:</b> {v.get('detail', 'No details')}", styles['Normal']))
        story.append(Paragraph(f"<b>Fix:</b> {v.get('fix', 'No fix suggested')}", styles['Normal']))
        story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    
    return filepath