
"""
Executive PDF Report Generator for AI Startup Idea Validator.
Generates three different PDF exports:
1. Executive PDF Dossier
2. Full Report PDF
3. Structured Data PDF
"""

import io
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models import FullValidationReport


# ---------------------------------------------------------
# 1. REGISTER FONTS
# ---------------------------------------------------------

pdfmetrics.registerFont(
    TTFont("Ventura", r"C:\Windows\Fonts\arial.ttf")
)

pdfmetrics.registerFont(
    TTFont("Ventura-Bold", r"C:\Windows\Fonts\arialbd.ttf")
)

pdfmetrics.registerFontFamily(
    "Ventura",
    normal="Ventura",
    bold="Ventura-Bold",
    italic="Ventura",
    boldItalic="Ventura-Bold"
)


# ---------------------------------------------------------
# 2. CLEAN SPECIAL CHARACTERS
# ---------------------------------------------------------

def clean_text(value):
    if value is None:
        return ""

    text = str(value)

    replacements = {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00A0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# ---------------------------------------------------------
# 3. NUMBERED PDF CANVAS
# ---------------------------------------------------------

class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)

        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()

        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()

        self.setFont("Ventura", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        if self._pageNumber > 1:
            self.drawString(
                54,
                755,
                "Ventura AI - Executive Startup Idea Validation Dossier"
            )

            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 748, 558, 748)

        footer_text = f"Page {self._pageNumber} of {page_count}"

        self.drawRightString(558, 35, footer_text)

        self.drawString(
            54,
            35,
            "CONFIDENTIAL & PROPRIETARY - PREPARED BY VENTURA MULTI-AGENT ENGINE"
        )

        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)

        self.restoreState()


# ---------------------------------------------------------
# 4. EXECUTIVE PDF GENERATION
# ---------------------------------------------------------

def generate_pdf_report(report: FullValidationReport) -> bytes:

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    c_primary = colors.HexColor("#0F172A")
    c_accent = colors.HexColor("#2563EB")
    c_success = colors.HexColor("#059669")
    c_warning = colors.HexColor("#D97706")
    c_danger = colors.HexColor("#DC2626")
    c_card_bg = colors.HexColor("#F8FAFC")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Ventura-Bold",
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=4
    )

    tagline_style = ParagraphStyle(
        "DocTagline",
        parent=styles["Normal"],
        fontName="Ventura",
        fontSize=12,
        leading=16,
        textColor=c_accent,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Ventura-Bold",
        fontSize=15,
        leading=19,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Ventura-Bold",
        fontSize=11,
        leading=15,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Ventura",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=5
    )

    body_bold = ParagraphStyle(
        "BodyDarkBold",
        parent=body_style,
        fontName="Ventura-Bold"
    )

    card_text = ParagraphStyle(
        "CardText",
        parent=styles["Normal"],
        fontName="Ventura",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # HEADER

    super_header = ParagraphStyle(
        "SuperH",
        fontName="Ventura-Bold",
        fontSize=9,
        textColor=c_accent,
        leading=12,
        spaceAfter=2
    )

    story.append(
        Paragraph(
            "VENTURA AI: STARTUP VALIDATION DOSSIER",
            super_header
        )
    )

    story.append(
        Paragraph(
            escape(clean_text(report.structured_idea.title)),
            title_style
        )
    )

    story.append(
        Paragraph(
            escape(clean_text(report.structured_idea.tagline)),
            tagline_style
        )
    )

    verdict_color = (
        c_success if "STRONG GO" in report.executive_verdict
        else c_warning if "CAUTION" in report.executive_verdict
        else c_danger
    )

    verdict_style = ParagraphStyle(
        "Verdict",
        parent=card_text,
        fontName="Ventura-Bold",
        textColor=verdict_color
    )

    meta_data = [[
        Paragraph(
            "<b>Report ID:</b> " + escape(clean_text(report.report_id)),
            card_text
        ),
        Paragraph(
            "<b>Domain:</b> " + escape(clean_text(report.structured_idea.industry_domain)),
            card_text
        ),
        Paragraph(
            f"<b>Viability Score:</b> {report.composite_viability_score} / 100",
            card_text
        ),
        Paragraph(
            "<b>Verdict:</b> " + escape(clean_text(report.executive_verdict)),
            verdict_style
        )
    ]]

    meta_table = Table(
        meta_data,
        colWidths=[120, 140, 110, 134]
    )

    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_card_bg),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(meta_table)
    story.append(Spacer(1, 10))

    # EXECUTIVE SUMMARY

    story.append(
        Paragraph("1. Executive Summary &amp; Strategic Verdict", h1_style)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=c_accent,
            spaceBefore=1,
            spaceAfter=6
        )
    )

    summary = escape(clean_text(report.executive_summary))
    summary = summary.replace("\n\n", "<br/><br/>")

    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 4))

    story.append(
        Paragraph("<b>Key Strategic Directives:</b>", body_style)
    )

    for rec in report.key_recommendations:
        story.append(
            Paragraph("&#8226; " + escape(clean_text(rec)), body_style)
        )

    story.append(Spacer(1, 10))

    # VENTURE FOUNDATION

    story.append(
        Paragraph("2. Venture Foundation &amp; Core Mechanics", h1_style)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=c_accent,
            spaceBefore=1,
            spaceAfter=6
        )
    )

    idea_table_data = [
        [
            Paragraph("<b>Problem Statement</b>", body_bold),
            Paragraph(escape(clean_text(report.structured_idea.problem_statement)), body_style)
        ],
        [
            Paragraph("<b>Proposed Solution</b>", body_bold),
            Paragraph(escape(clean_text(report.structured_idea.solution_statement)), body_style)
        ],
        [
            Paragraph("<b>Primary Customer</b>", body_bold),
            Paragraph(escape(clean_text(report.structured_idea.target_customer)), body_style)
        ],
        [
            Paragraph("<b>Value Proposition</b>", body_bold),
            Paragraph(escape(clean_text(report.structured_idea.core_value_prop)), body_style)
        ],
        [
            Paragraph("<b>Monetization Model</b>", body_bold),
            Paragraph(escape(clean_text(report.structured_idea.monetization_model)), body_style)
        ],
    ]

    idea_table = Table(
        idea_table_data,
        colWidths=[130, 374]
    )

    idea_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), c_card_bg),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(idea_table)
    story.append(Spacer(1, 10))

    # MARKET OPPORTUNITY

    story.append(
        Paragraph("3. Market Opportunity &amp; Sizing (TAM/SAM/SOM)", h1_style)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=c_accent,
            spaceBefore=1,
            spaceAfter=6
        )
    )

    market_data = [
        [
            Paragraph("<b>TAM (Total Market)</b>", body_bold),
            Paragraph("<b>SAM (Serviceable)</b>", body_bold),
            Paragraph("<b>SOM (Year 3)</b>", body_bold),
            Paragraph("<b>Growth (CAGR)</b>", body_bold),
            Paragraph("<b>Timing Score</b>", body_bold),
        ],
        [
            Paragraph(escape(clean_text(report.market_opportunity.tam_estimate)), card_text),
            Paragraph(escape(clean_text(report.market_opportunity.sam_estimate)), card_text),
            Paragraph(escape(clean_text(report.market_opportunity.som_estimate)), card_text),
            Paragraph(escape(clean_text(report.market_opportunity.cagr_growth_rate)), card_text),
            Paragraph(f"{report.market_opportunity.market_timing_score} / 100", card_text),
        ]
    ]

    market_table = Table(
        market_data,
        colWidths=[110, 100, 100, 100, 94]
    )

    market_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(market_table)
    story.append(Spacer(1, 6))

    if report.market_opportunity.personas:
        story.append(
            Paragraph("<b>Primary Customer Personas:</b>", h2_style)
        )

        for p in report.market_opportunity.personas[:2]:
            p_text = (
                f"<b>{escape(clean_text(p.persona_name))}</b> "
                f"({escape(clean_text(p.target_demographics))}) - "
                f"<i>Pain Points:</i> "
                f"{escape(clean_text(', '.join(p.core_pain_points[:2])))} | "
                f"<i>Willingness to Pay:</i> "
                f"{escape(clean_text(p.willingness_to_pay))}"
            )

            story.append(
                Paragraph("&#8226; " + p_text, body_style)
            )

    story.append(Spacer(1, 10))
    story.append(PageBreak())

    # COMPETITOR DISCOVERY

    story.append(
        Paragraph("4. Competitor Discovery &amp; White Space Matrix", h1_style)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=c_accent,
            spaceBefore=1,
            spaceAfter=6
        )
    )

    comp_header = [
        Paragraph("<b>Competitor</b>", body_bold),
        Paragraph("<b>Type / Position</b>", body_bold),
        Paragraph("<b>Strengths</b>", body_bold),
        Paragraph("<b>Weaknesses</b>", body_bold)
    ]

    comp_rows = [comp_header]

    for c in report.competitor_analysis.competitors[:3]:
        comp_rows.append([
            Paragraph(
                f"<b>{escape(clean_text(c.name))}</b><br/>"
                f"<i>{escape(clean_text(c.pricing_model))}</i>",
                card_text
            ),
            Paragraph(
                f"{escape(clean_text(c.competitor_type))}<br/>"
                f"{escape(clean_text(c.estimated_market_position))}",
                card_text
            ),
            Paragraph(escape(clean_text(", ".join(c.strengths[:2]))), card_text),
            Paragraph(escape(clean_text(", ".join(c.weaknesses[:2]))), card_text),
        ])

    comp_table = Table(
        comp_rows,
        colWidths=[120, 110, 137, 137]
    )

    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))

    story.append(comp_table)
    story.append(Spacer(1, 6))

    story.append(
        Paragraph("<b>Unfilled White Space Opportunities:</b>", h2_style)
    )

    for ws in report.competitor_analysis.white_space_opportunities[:3]:
        story.append(
            Paragraph("&#8226; " + escape(clean_text(ws)), body_style)
        )

    story.append(Spacer(1, 10))

    # SWOT AND RISK REGISTER

    story.append(
        Paragraph("5. SWOT Matrix &amp; Execution Risk Register", h1_style)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=c_accent,
            spaceBefore=1,
            spaceAfter=6
        )
    )

    swot_data = [
        [
            Paragraph(
                "<b>STRENGTHS</b><br/>"
                + "<br/>&#8226; ".join(
                    [""] + [escape(clean_text(x)) for x in report.swot_and_risk.strengths[:3]]
                ),
                card_text
            ),
            Paragraph(
                "<b>WEAKNESSES</b><br/>"
                + "<br/>&#8226; ".join(
                    [""] + [escape(clean_text(x)) for x in report.swot_and_risk.weaknesses[:3]]
                ),
                card_text
            ),
        ],
        [
            Paragraph(
                "<b>OPPORTUNITIES</b><br/>"
                + "<br/>&#8226; ".join(
                    [""] + [escape(clean_text(x)) for x in report.swot_and_risk.opportunities[:3]]
                ),
                card_text
            ),
            Paragraph(
                "<b>THREATS</b><br/>"
                + "<br/>&#8226; ".join(
                    [""] + [escape(clean_text(x)) for x in report.swot_and_risk.threats[:3]]
                ),
                card_text
            ),
        ]
    ]

    swot_table = Table(
        swot_data,
        colWidths=[252, 252]
    )

    swot_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#ECFDF5")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FEF2F2")),
        ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#EFF6FF")),
        ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#FFFBEB")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))

    story.append(swot_table)
    story.append(Spacer(1, 8))

    risk_header = [
        Paragraph("<b>Risk Category &amp; Title</b>", body_bold),
        Paragraph("<b>Likelihood / Severity</b>", body_bold),
        Paragraph("<b>Mitigation Strategy</b>", body_bold)
    ]

    risk_rows = [risk_header]

    for r in report.swot_and_risk.risk_items[:3]:
        risk_rows.append([
            Paragraph(
                f"<b>[{escape(clean_text(r.category))}]</b> "
                f"{escape(clean_text(r.risk_title))}",
                card_text
            ),
            Paragraph(
                f"{escape(clean_text(r.likelihood))} / "
                f"{escape(clean_text(r.severity))}",
                card_text
            ),
            Paragraph(escape(clean_text(r.mitigation_strategy)), card_text)
        ])

    risk_table = Table(
        risk_rows,
        colWidths=[150, 100, 254]
    )

    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))

    story.append(risk_table)
    story.append(Spacer(1, 10))

    # MVP ROADMAP AND GTM STRATEGY

    story.append(
        Paragraph(
            "6. MVP Feature Prioritization (MoSCoW) &amp; GTM Plan",
            h1_style
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=c_accent,
            spaceBefore=1,
            spaceAfter=6
        )
    )

    story.append(
        Paragraph(
            f"<b>Build Timeline:</b> "
            f"{escape(clean_text(report.mvp_recommendation.estimated_build_time_weeks))} Weeks | "
            f"<b>Estimated Budget:</b> "
            f"{escape(clean_text(report.mvp_recommendation.estimated_mvp_budget_usd))} | "
            f"<b>North Star Metric:</b> "
            f"{escape(clean_text(report.mvp_recommendation.critical_success_metric))}",
            body_style
        )
    )

    story.append(Spacer(1, 4))

    must_haves = [
        escape(clean_text(f.feature_name))
        for f in report.mvp_recommendation.core_features
        if f.moscow_category == "Must-Have"
    ]

    story.append(
        Paragraph(
            "&#8226; <b>Must-Have Core (Phase 1):</b> "
            + ", ".join(must_haves),
            body_style
        )
    )

    should_haves = [
        escape(clean_text(f.feature_name))
        for f in report.mvp_recommendation.core_features
        if f.moscow_category == "Should-Have"
    ]

    if should_haves:
        story.append(
            Paragraph(
                "&#8226; <b>Should-Have (Phase 2):</b> "
                + ", ".join(should_haves),
                body_style
            )
        )

    story.append(Spacer(1, 6))

    story.append(
        Paragraph("<b>First 100 Customers Playbook:</b>", h2_style)
    )

    for step in report.gtm_strategy.first_100_customers_playbook[:3]:
        story.append(
            Paragraph("&#8226; " + escape(clean_text(step)), body_style)
        )

    # BUILD EXECUTIVE PDF

    doc.build(
        story,
        canvasmaker=NumberedCanvas
    )

    return buffer.getvalue()


# ---------------------------------------------------------
# 5. COMMON TEXT PDF GENERATOR
# ---------------------------------------------------------

def generate_text_pdf(content, heading):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ExportTitle",
        parent=styles["Title"],
        fontName="Ventura-Bold",
        fontSize=20
    )

    body_style = ParagraphStyle(
        "ExportBody",
        parent=styles["Normal"],
        fontName="Ventura",
        fontSize=9,
        leading=13,
        wordWrap="CJK"
    )

    heading_style = ParagraphStyle(
        "ExportHeading",
        parent=styles["Heading2"],
        fontName="Ventura-Bold"
    )

    story = [
        Paragraph(escape(heading), title_style),
        Spacer(1, 12)
    ]

    for line in str(content).splitlines():

        line = clean_text(line).strip()

        if not line:
            story.append(Spacer(1, 5))

        elif line.startswith("#"):
            story.append(
                Paragraph(
                    escape(line.lstrip("# ")),
                    heading_style
                )
            )

        else:
            story.append(
                Paragraph(
                    escape(line),
                    body_style
                )
            )

    doc.build(story)

    return buffer.getvalue()


# ---------------------------------------------------------
# 6. FULL REPORT PDF
# ---------------------------------------------------------

def generate_markdown_pdf(markdown_text):

    return generate_text_pdf(
        markdown_text,
        "Full Startup Validation Report"
    )


# ---------------------------------------------------------
# 7. STRUCTURED DATA PDF
# ---------------------------------------------------------

def generate_json_pdf(json_text):

    return generate_text_pdf(
        json_text,
        "Structured Startup Data"
    )
