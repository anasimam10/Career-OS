"""
Career OS — Final Hackathon / Judge-Ready Master PPTX Presentation Deck Generator
Rebuilds the presentation into a world-class, visual-first, 14-slide master deck
with authentic high-resolution screenshots, vector diagrams, proportional aspect ratios,
and comprehensive speaker notes.
"""

import os
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------------------
# Design System Color Tokens (Dark Cyber / Enterprise Restrained)
# ---------------------------------------------------------------------------
BG_DARK = RGBColor(11, 15, 26)           # #0B0F1A (Master Background)
SURFACE_CARD = RGBColor(17, 24, 39)      # #111827 (Standard Card Surface)
SURFACE_ELEVATED = RGBColor(28, 37, 57)  # #1C2539 (Elevated Card Surface)
BORDER_DEFAULT = RGBColor(30, 45, 66)    # #1E2D42 (Subtle Border)
BORDER_ACTIVE = RGBColor(42, 58, 84)     # #2A3A54 (Active / Highlight Border)

BLUE_PRIMARY = RGBColor(37, 99, 235)     # #2563EB (Primary Brand Blue)
BLUE_LIGHT = RGBColor(59, 130, 246)      # #3B82F6 (Interactive Blue)
BLUE_GLOW = RGBColor(96, 165, 250)       # #60A5FA (Accent Glow)
AMBER_ACCENT = RGBColor(245, 158, 11)    # #F59E0B (Warning / Callout Accent)
GREEN_SUCCESS = RGBColor(16, 185, 129)   # #10B981 (Success / Validated Green)
RED_ALERT = RGBColor(239, 68, 68)        # #EF4444 (Problem / Alert Red)

TEXT_WHITE = RGBColor(241, 245, 249)     # #F1F5F9 (Primary Heading / Text)
TEXT_MUTED = RGBColor(148, 163, 184)     # #94A3B8 (Secondary Text)
TEXT_TERTIARY = RGBColor(100, 116, 139)  # #64748B (Footers / Citations)

FONT_FAMILY = "Segoe UI"
ASSETS_DIR = Path("Docs/presentation_assets")


def build_final_deck(output_path: Path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.500)
    blank_layout = prs.slide_layouts[6]

    def add_blank_slide(notes: str = ""):
        slide = prs.slides.add_slide(blank_layout)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.500))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.color.rgb = BG_DARK
        if notes:
            slide.notes_slide.notes_text_frame.text = notes
        return slide

    def add_header(slide, eyebrow: str, title: str, subline: str = ""):
        tx_box = slide.shapes.add_textbox(Inches(0.80), Inches(0.40), Inches(11.733), Inches(1.15))
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_eye = tf.paragraphs[0]
        p_eye.text = eyebrow.upper()
        p_eye.font.size = Pt(10)
        p_eye.font.bold = True
        p_eye.font.color.rgb = BLUE_LIGHT
        p_eye.font.name = FONT_FAMILY
        p_eye.space_after = Pt(2)
        
        p_title = tf.add_paragraph()
        p_title.text = title
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE
        p_title.font.name = FONT_FAMILY
        
        if subline:
            p_title.space_after = Pt(2)
            p_sub = tf.add_paragraph()
            p_sub.text = subline
            p_sub.font.size = Pt(11.5)
            p_sub.font.color.rgb = TEXT_MUTED
            p_sub.font.name = FONT_FAMILY

    def add_footer(slide, citation: str = "Career OS · Verified against current repository"):
        tx = slide.shapes.add_textbox(Inches(0.80), Inches(7.08), Inches(11.733), Inches(0.28))
        tf = tx.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = citation
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_TERTIARY
        p.font.name = FONT_FAMILY

    def add_card(slide, left, top, width, height, bg_color=SURFACE_CARD, border_color=BORDER_DEFAULT):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
        return shape

    def add_mockup_image(slide, img_name, left, top, width, border=True):
        """Adds a screenshot maintaining its exact aspect ratio, enclosed in an elevated container."""
        img_path = ASSETS_DIR / img_name
        if not img_path.exists():
            print(f"Warning: Image {img_name} not found, drawing placeholder card.")
            return add_card(slide, left, top, width, width * 0.6, SURFACE_CARD, BORDER_DEFAULT), width * 0.6
        
        with Image.open(img_path) as im:
            iw, ih = im.size
        aspect = ih / iw
        height = width * aspect

        if border:
            add_card(slide, left - 0.03, top - 0.03, width + 0.06, height + 0.06, SURFACE_ELEVATED, BORDER_ACTIVE)
        
        pic = slide.shapes.add_picture(str(img_path), Inches(left), Inches(top), width=Inches(width))
        return pic, height

    # =======================================================================
    # SLIDE 1: Title & Vision (Impact Opening)
    # =======================================================================
    s1 = add_blank_slide(
        "Welcome, judges. In Pakistan today, millions of students make high-stakes life decisions based on rumors, peer pressure, and fragmented advice. "
        "Career OS is Pakistan's Career Operating System. It replaces scattered searches with a structured, step-by-step operating system that walks a student from "
        "high school uncertainty all the way to their first job, grounded in verified local market realities.\n\n"
        "Notice on screen: We have 248 HEC universities, 210 degree programs, 22 localized career pathways, and 806 automated tests passing right now. "
        "The application is live on Vercel and Render."
    )
    # Brand Pill
    pill = add_card(s1, 0.80, 1.05, 3.40, 0.38, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_pill = pill.text_frame
    tf_pill.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_p = tf_pill.paragraphs[0]
    p_p.text = "PAKISTAN'S CAREER OPERATING SYSTEM"
    p_p.font.size = Pt(9.5)
    p_p.font.bold = True
    p_p.font.color.rgb = BLUE_LIGHT
    p_p.alignment = PP_ALIGN.CENTER
    p_p.font.name = FONT_FAMILY

    # Main Headline & Vision
    h_box = s1.shapes.add_textbox(Inches(0.80), Inches(1.55), Inches(5.60), Inches(2.30))
    tf_h = h_box.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = tf_h.margin_top = 0
    p1 = tf_h.paragraphs[0]
    p1.text = "Career OS"
    p1.font.size = Pt(40)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.font.name = FONT_FAMILY
    p1.space_after = Pt(8)

    p2 = tf_h.add_paragraph()
    p2.text = "Guiding Pakistani students from academic uncertainty to their first job through personalized, grounded intelligence."
    p2.font.size = Pt(13.5)
    p2.font.color.rgb = TEXT_MUTED
    p2.font.name = FONT_FAMILY
    p2.space_after = Pt(8)

    p3 = tf_h.add_paragraph()
    p3.text = "Live at: career-os-seven-flame.vercel.app"
    p3.font.size = Pt(11)
    p3.font.bold = True
    p3.font.color.rgb = BLUE_LIGHT
    p3.font.name = FONT_FAMILY

    # 4 Key Proof Metrics (2x2 grid on left bottom)
    m_data = [
        ("248", "HEC Universities", "166 Public, 82 Private across 8 regions"),
        ("210", "Degree Programs", "Verified across 64 academic disciplines"),
        ("22", "Career Pathways", "Pakistani labor demand & PKR salary bands"),
        ("806", "Automated Tests", "100% passing test suite across all layers"),
    ]
    for i, (val, lbl, sub) in enumerate(m_data):
        row = i // 2
        col = i % 2
        c_left = 0.80 + col * 2.85
        c_top = 4.05 + row * 1.35
        c = add_card(s1, c_left, c_top, 2.72, 1.25, SURFACE_CARD, BORDER_DEFAULT)
        tf_c = c.text_frame
        tf_c.word_wrap = True
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_val = tf_c.paragraphs[0]
        p_val.text = val
        p_val.font.size = Pt(22)
        p_val.font.bold = True
        p_val.font.color.rgb = GREEN_SUCCESS if i == 3 else BLUE_LIGHT
        p_val.font.name = FONT_FAMILY
        p_lbl = tf_c.add_paragraph()
        p_lbl.text = lbl
        p_lbl.font.size = Pt(10)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = TEXT_WHITE
        p_lbl.font.name = FONT_FAMILY
        p_sub = tf_c.add_paragraph()
        p_sub.text = sub
        p_sub.font.size = Pt(8)
        p_sub.font.color.rgb = TEXT_MUTED
        p_sub.font.name = FONT_FAMILY

    # Right side: Real Product Visual with proper 16:9 aspect ratio
    add_mockup_image(s1, "01_hero_home.png", 6.70, 1.15, width=5.83)

    # Right side bottom: Live Deployment Status Card
    c_live_s1 = add_card(s1, 6.70, 4.50, 5.83, 2.30, SURFACE_CARD, BORDER_DEFAULT)
    tf_ls1 = c_live_s1.text_frame
    tf_ls1.word_wrap = True
    p_lsh = tf_ls1.paragraphs[0]
    p_lsh.text = "VERIFIED PRODUCTION DEPLOYMENT"
    p_lsh.font.size = Pt(10)
    p_lsh.font.bold = True
    p_lsh.font.color.rgb = GREEN_SUCCESS
    p_lsh.font.name = FONT_FAMILY
    p_lsh.space_after = Pt(6)

    deps = [
        ("Vercel Edge Frontend", "HTTP 200 (1033 ms)", "career-os-seven-flame.vercel.app"),
        ("Render Backend Gateway", "HTTP 200 (406 ms)", "ah-career-backend.onrender.com"),
        ("Interactive OpenAPI / Docs", "HTTP 200 (352 ms)", "ah-career-backend.onrender.com/docs"),
    ]
    for dname, dstatus, durl in deps:
        p = tf_ls1.add_paragraph()
        p.text = f"✓  {dname} · {dstatus} · {durl}"
        p.font.size = Pt(8.8)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(3)

    add_footer(s1, "Career OS · Verified against current repository & active deployment · September 2026")

    # =======================================================================
    # SLIDE 2: The Problem (Visual Flow)
    # =======================================================================
    s2 = add_blank_slide(
        "Notice what happens to an intermediate student in Pakistan today. They are bombarded with viral salary rumors on TikTok and YouTube, "
        "confronted by 200+ scattered university websites, and pushed by societal expectations. The result is total confusion, leading to mid-degree "
        "dropouts and underemployment. Too much scattered information, but zero personal direction."
    )
    add_header(s2, "The Core Dilemma", "Students Don't Lack Information. They Lack a Path.",
               "Pakistani students face an overwhelming barrage of unstructured advice, viral salary rumors, and scattered portals.")

    # Top ecosystem of 4 fragmented sources
    sources = [
        ("Viral Salary Rumors", "Influencers claiming 500k PKR entry salaries with zero context on required skills.", AMBER_ACCENT),
        ("200+ Disjointed Portals", "Admission criteria, fees, and tests buried across unstandardized university websites.", BLUE_LIGHT),
        ("Family & Societal Pressure", "Blindly pushing students toward saturated medical and engineering seats.", TEXT_MUTED),
        ("Scattered Deadlines", "Scholarship dates, NTS/ECAT tests, and internship windows frequently missed.", RED_ALERT),
    ]
    for i, (stitle, sdesc, scolor) in enumerate(sources):
        c_left = 0.80 + i * (2.75 + 0.24)
        c = add_card(s2, c_left, 1.70, 2.75, 1.65, SURFACE_CARD, BORDER_DEFAULT)
        tf_c = c.text_frame
        tf_c.word_wrap = True
        p_t = tf_c.paragraphs[0]
        p_t.text = stitle
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = scolor
        p_t.font.name = FONT_FAMILY
        p_t.space_after = Pt(4)
        p_d = tf_c.add_paragraph()
        p_d.text = sdesc
        p_d.font.size = Pt(9)
        p_d.font.color.rgb = TEXT_MUTED
        p_d.font.name = FONT_FAMILY

    # Visual Flow connecting downward: 4 connected step badges
    flow_steps = [
        ("1. Fragmented Info", "Unverified sources & salary myths"),
        ("2. Confusion & FOMO", "Analysis paralysis & anxiety"),
        ("3. Blind Decisions", "Enrolling without career validation"),
        ("4. High Life Cost", "Degree regret, dropout & underemployment")
    ]
    for i, (f_title, f_sub) in enumerate(flow_steps):
        c_left = 0.80 + i * (2.75 + 0.24)
        fc = add_card(s2, c_left, 3.65, 2.75, 1.40, SURFACE_ELEVATED, BORDER_ACTIVE)
        tf_fc = fc.text_frame
        tf_fc.word_wrap = True
        tf_fc.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_f1 = tf_fc.paragraphs[0]
        p_f1.text = f_title
        p_f1.font.size = Pt(11.5)
        p_f1.font.bold = True
        p_f1.font.color.rgb = BLUE_LIGHT if i < 3 else RED_ALERT
        p_f1.font.name = FONT_FAMILY
        p_f1.space_after = Pt(3)
        p_f2 = tf_fc.add_paragraph()
        p_f2.text = f_sub
        p_f2.font.size = Pt(8.5)
        p_f2.font.color.rgb = TEXT_MUTED
        p_f2.font.name = FONT_FAMILY

    # Strong Contrast Statement
    stmt_box = add_card(s2, 0.80, 5.35, 11.733, 1.45, SURFACE_CARD, BORDER_DEFAULT)
    tf_s = stmt_box.text_frame
    tf_s.word_wrap = True
    tf_s.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_s1 = tf_s.paragraphs[0]
    p_s1.text = "\"Too much information. Too little direction.\""
    p_s1.font.size = Pt(20)
    p_s1.font.bold = True
    p_s1.font.color.rgb = AMBER_ACCENT
    p_s1.font.name = FONT_FAMILY
    p_s1.space_after = Pt(4)

    p_s2 = tf_s.add_paragraph()
    p_s2.text = "Raw search engines return 10 million links. Generic AI chatbots hallucinate ungrounded advice. Students need a personalized operating system."
    p_s2.font.size = Pt(11)
    p_s2.font.color.rgb = TEXT_WHITE
    p_s2.font.name = FONT_FAMILY

    add_footer(s2, "Source: README.md §'The Real Problem' & Pakistan Knowledge Engine Research (Docs/pakistan_knowledge_engine.md)")

    # =======================================================================
    # SLIDE 3: The Difference (Before vs After)
    # =======================================================================
    s3 = add_blank_slide(
        "Here is the fundamental difference. On the left: the old way. Keyword searches, scattered PDFs, and generic chatbots that hallucinate. "
        "On the right: Career OS. We turn scattered information into a continuous, deterministic pathway: Profile, Reality Check, Hands-on Trial, "
        "University Match, Skill Building, Mock Interview, and First Job."
    )
    add_header(s3, "The Transformation", "Career OS Turns Information Into a Path",
               "A direct architectural comparison between disconnected traditional discovery and our structured operating system.")

    # Left Column: Old Way
    c_old = add_card(s3, 0.80, 1.70, 5.65, 4.35, SURFACE_CARD, BORDER_DEFAULT)
    tf_old = c_old.text_frame
    tf_old.word_wrap = True
    p_oh = tf_old.paragraphs[0]
    p_oh.text = "TRADITIONAL SEARCH & CHAT (DISCONNECTED)"
    p_oh.font.size = Pt(12)
    p_oh.font.bold = True
    p_oh.font.color.rgb = RED_ALERT
    p_oh.font.name = FONT_FAMILY
    p_oh.space_after = Pt(10)

    old_steps = [
        ("Raw Keyword Search", "Returns millions of unstructured web documents with zero personal relevance to city or stage."),
        ("Open-Ended AI Chatbots", "Hallucinates salary bands, invents admission deadlines, and lacks grounded Pakistani context."),
        ("Disconnected Portals", "Student must manually cross-reference 200+ university sites and provincial education boards."),
        ("No Aptitude Validation", "Students commit four years and tuition fees before writing a line of code or testing the work."),
        ("Dead-End Experience", "Ends with unstructured links, leaving the student anxious about what immediate action to take.")
    ]
    for ot, od in old_steps:
        p = tf_old.add_paragraph()
        p.text = f"✗  {ot}: {od}"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(8)

    # Right Column: Career OS
    c_new = add_card(s3, 6.85, 1.70, 5.68, 4.35, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_new = c_new.text_frame
    tf_new.word_wrap = True
    p_nh = tf_new.paragraphs[0]
    p_nh.text = "CAREER OS (THE SEQUENTIAL OPERATING SYSTEM)"
    p_nh.font.size = Pt(12)
    p_nh.font.bold = True
    p_nh.font.color.rgb = GREEN_SUCCESS
    p_nh.font.name = FONT_FAMILY
    p_nh.space_after = Pt(10)

    new_steps = [
        ("5-D Structured Profile", "Tailored to Education Stage, City, Baseline Skills, Motivations, and Sports Interests."),
        ("Grounded Reality Check", "Evaluates real Pakistani employer expectations, local competition, and PKR salary bands."),
        ("7-Day Practical Career Trial", "Daily hands-on micro-tasks validate genuine interest before tuition commitment."),
        ("248 HEC Institutions", "Direct alignment with accredited Pakistani universities, degree fees, and entry tests."),
        ("Closing the Employability Gap", "86 curated learning resources and Qwen technical mock interviews prepare students for hiring.")
    ]
    for nt, nd in new_steps:
        p = tf_new.add_paragraph()
        p.text = f"✓  {nt}: {nd}"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_WHITE if "Reality" in nt or "Trial" in nt else TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(8)

    # Bottom: Visual Pipeline Chevron Ribbon
    c_ribbon = add_card(s3, 0.80, 6.25, 11.733, 0.65, SURFACE_CARD, BORDER_DEFAULT)
    tf_rb = c_ribbon.text_frame
    tf_rb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_rb = tf_rb.paragraphs[0]
    p_rb.text = "Profile   ➔   Reality Check   ➔   7-Day Trial   ➔   University Match   ➔   Skill Building   ➔   Mock Interview   ➔   First Job"
    p_rb.font.size = Pt(11)
    p_rb.font.bold = True
    p_rb.font.color.rgb = BLUE_LIGHT
    p_rb.alignment = PP_ALIGN.CENTER
    p_rb.font.name = FONT_FAMILY

    add_footer(s3, "Source: README.md §'The Solution' & Architecture Master Specification")

    # =======================================================================
    # SLIDE 4: The Core Product Experience (Continuous Pathway)
    # =======================================================================
    s4 = add_blank_slide(
        "This is the core product experience: One student, one continuous journey. Career OS takes the student through nine sequential nodes. "
        "Notice how each step gates the next: You don't pick a degree until you run a reality check. You don't commit tuition until you complete a 7-day trial. "
        "Every single step is actionable and grounded."
    )
    add_header(s4, "The Product Pipeline", "One Student. One Continuous Journey.",
               "A 9-stage sequential operating system guiding Pakistani youth from high school exploration to employment.")

    # Two rows representing the continuous pathway
    # Row 1: Steps 1 to 5 (Left to Right)
    row1_nodes = [
        ("01", "Onboarding", "7-step profile: stage, city, skills, motivations"),
        ("02", "Discovery", "22 Pakistani pathways across Tech, Business, Health"),
        ("03", "Reality Check", "PKR salary bands, market demand & sector risks"),
        ("04", "7-Day Trial", "Daily micro-tasks test-drive work before enrolling"),
        ("05", "Universities", "248 HEC universities & 210 degree programs"),
    ]
    for idx, (num, title, desc) in enumerate(row1_nodes):
        c_left = 0.80 + idx * (2.18 + 0.20)
        c = add_card(s4, c_left, 1.70, 2.18, 1.95, SURFACE_CARD, BORDER_DEFAULT if idx not in (2, 3) else BORDER_ACTIVE)
        tf_c = c.text_frame
        tf_c.word_wrap = True
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE

        p_num = tf_c.paragraphs[0]
        p_num.text = f"{num}  ·  {title}"
        p_num.font.size = Pt(11.5)
        p_num.font.bold = True
        p_num.font.color.rgb = AMBER_ACCENT if idx in (2, 3) else BLUE_LIGHT
        p_num.font.name = FONT_FAMILY
        p_num.space_after = Pt(4)

        p_desc = tf_c.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(8.8)
        p_desc.font.color.rgb = TEXT_MUTED
        p_desc.font.name = FONT_FAMILY

    # Row 2: Steps 6 to 9 (Left to Right)
    row2_nodes = [
        ("06", "Skill Building", "86 curated technical & vocational resources"),
        ("07", "Opportunities", "38 verified national scholarships & internships"),
        ("08", "Mock Screening", "10-question technical interview via Qwen 3.6-plus"),
        ("09", "First Job", "Career launch with verified skills & portfolio")
    ]
    for idx, (num, title, desc) in enumerate(row2_nodes):
        c_left = 0.80 + idx * (2.75 + 0.24)
        c = add_card(s4, c_left, 3.85, 2.75, 1.95, SURFACE_CARD, BORDER_DEFAULT if idx != 2 else BORDER_ACTIVE)
        tf_c = c.text_frame
        tf_c.word_wrap = True
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE

        p_num = tf_c.paragraphs[0]
        p_num.text = f"{num}  ·  {title}"
        p_num.font.size = Pt(12)
        p_num.font.bold = True
        p_num.font.color.rgb = GREEN_SUCCESS if idx in (2, 3) else BLUE_LIGHT
        p_num.font.name = FONT_FAMILY
        p_num.space_after = Pt(4)

        p_desc = tf_c.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(9)
        p_desc.font.color.rgb = TEXT_MUTED
        p_desc.font.name = FONT_FAMILY

    # Lower takeaway banner
    banner = add_card(s4, 0.80, 6.10, 11.733, 0.80, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_b = banner.text_frame
    tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_b = tf_b.paragraphs[0]
    p_b.text = "KEY INVARIANT: Every stage is sequential and gated. Students validate genuine aptitude and market reality before spending years in tuition."
    p_b.font.size = Pt(11)
    p_b.font.bold = True
    p_b.font.color.rgb = TEXT_WHITE
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.name = FONT_FAMILY

    add_footer(s4, "Source: README.md lines 44–66 & BackEnd/services/roadmap_service.py (MILESTONE_TEMPLATES)")

    # =======================================================================
    # SLIDE 5: Onboarding (Screenshot-Dominated)
    # =======================================================================
    s5 = add_blank_slide(
        "We start with the student, not the search. Look at our actual live onboarding interface. In seven structured steps, we capture "
        "their education stage, province and city in Pakistan, their baseline skills, whether they want an athletic quota, and what drives them. "
        "It takes under 90 seconds, eliminates typing fatigue, and instantiates their roadmap atomically."
    )
    add_header(s5, "Stage 1: Precision Profiling", "Start With the Student, Not the Search.",
               "Controlled 7-step onboarding wizard captures real student constraints without conversational ambiguity.")

    # Left: Two real screenshots side by side (Step 1 Education & Step 2 Location)
    add_mockup_image(s5, "02_onboarding_step1.png", 0.80, 1.70, width=3.40)
    add_mockup_image(s5, "03_onboarding_location.png", 4.35, 1.70, width=3.40)

    # Below screenshots: Bottom banner highlighting 5-D data model
    c_onb_b = add_card(s5, 0.80, 4.55, 6.95, 2.20, SURFACE_CARD, BORDER_DEFAULT)
    tf_ob = c_onb_b.text_frame
    tf_ob.word_wrap = True
    p_obh = tf_ob.paragraphs[0]
    p_obh.text = "THE 5-DIMENSIONAL STUDENT PROFILE MODEL"
    p_obh.font.size = Pt(10.5)
    p_obh.font.bold = True
    p_obh.font.color.rgb = BLUE_LIGHT
    p_obh.font.name = FONT_FAMILY
    p_obh.space_after = Pt(4)

    p_obt1 = tf_ob.add_paragraph()
    p_obt1.text = "• Education Stage: Matric / O-Level, FSc / A-Level, University (1–4), Fresh Graduate\n• Geographic Context: Sindh, Punjab, KPK, Balochistan, ICT & localized city hubs\n• Baseline Skills & Proficiencies: Beginner, Intermediate, Advanced technology proficiencies\n• Sports Pathways: Quota eligibility tracking across 11 national athletic disciplines"
    p_obt1.font.size = Pt(8.8)
    p_obt1.font.color.rgb = TEXT_MUTED
    p_obt1.font.name = FONT_FAMILY

    # Right: 7-Step Breakdown
    c_onb_r = add_card(s5, 7.95, 1.70, 4.58, 5.05, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_or = c_onb_r.text_frame
    tf_or.word_wrap = True
    p_orh = tf_or.paragraphs[0]
    p_orh.text = "7 CONTROLLED ONBOARDING STEPS"
    p_orh.font.size = Pt(12)
    p_orh.font.bold = True
    p_orh.font.color.rgb = GREEN_SUCCESS
    p_orh.font.name = FONT_FAMILY
    p_orh.space_after = Pt(8)

    steps_text = [
        ("1. Education Stage", "Matric, FSc, University, Fresh Graduate"),
        ("2. Location", "Sindh, Punjab, KPK, Balochistan, ICT & Cities"),
        ("3. Career Goal", "Target selection from 22 verified pathways"),
        ("4. Interests", "Structured domain tags & custom keywords"),
        ("5. Baseline Skills", "Beginner, Intermediate, Advanced proficiencies"),
        ("6. Sports Pathway", "Academic focus vs. athletic quotas (11 sports)"),
        ("7. Motivations", "High earnings, passion, remote work, stability")
    ]
    for s_num, s_desc in steps_text:
        p = tf_or.add_paragraph()
        p.text = f"• {s_num}: {s_desc}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(4)

    p_div = tf_or.add_paragraph()
    p_div.text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    p_div.font.size = Pt(8)
    p_div.font.color.rgb = BORDER_DEFAULT

    p_syn = tf_or.add_paragraph()
    p_syn.text = "Backend Result: Instantiates 13 sequenced milestones in SQLite and evaluates first Next Best Action via Qwen 3.6-plus."
    p_syn.font.size = Pt(9.5)
    p_syn.font.bold = True
    p_syn.font.color.rgb = TEXT_WHITE
    p_syn.font.name = FONT_FAMILY

    add_footer(s5, "Captured from live deployment: https://career-os-seven-flame.vercel.app/onboarding")

    # =======================================================================
    # SLIDE 6: Journey (Screenshot-Dominated)
    # =======================================================================
    s6 = add_blank_slide(
        "This is the student's cockpit: The Journey. On the left is the live Journey page. Notice how it enforces progressive disclosure. "
        "Completed milestones have green checkmarks. The active milestone is highlighted in electric blue with an immediate call to action. "
        "Upcoming milestones are locked. This isn't a passive checklist—it is an active state machine that loads in just 11 milliseconds."
    )
    add_header(s6, "The Student Cockpit", "The Journey Is the Operating System",
               "Progressive disclosure state machine: One active next step at a time, backed by sub-15ms cached roadmap retrieval.")

    # Left: Real screenshot of Journey page (dominating ~55% width)
    add_mockup_image(s6, "13_journey.png", 0.80, 1.70, width=7.00)

    # Right: The Progressive Disclosure Engine
    c_jr = add_card(s6, 8.00, 1.70, 4.53, 5.05, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_jr = c_jr.text_frame
    tf_jr.word_wrap = True
    p_jrh = tf_jr.paragraphs[0]
    p_jrh.text = "PROGRESSIVE DISCLOSURE ARCHITECTURE"
    p_jrh.font.size = Pt(12)
    p_jrh.font.bold = True
    p_jrh.font.color.rgb = BLUE_LIGHT
    p_jrh.font.name = FONT_FAMILY
    p_jrh.space_after = Pt(10)

    states = [
        ("✓ COMPLETED", "Milestones validated & logged in student profile.", GREEN_SUCCESS),
        ("▶ ACTIVE FOCUS", "Single actionable step (e.g. Start 7-Day Trial).", BLUE_LIGHT),
        ("🔒 LOCKED", "Future steps hidden to prevent decision fatigue.", TEXT_MUTED),
        ("★ LAUNCHPAD", "Terminal stage unlocked upon journey completion.", AMBER_ACCENT)
    ]
    for st, sd, sc in states:
        p = tf_jr.add_paragraph()
        p.text = f"{st}: {sd}"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = sc
        p.font.name = FONT_FAMILY
        p.space_after = Pt(6)

    p_j_div = tf_jr.add_paragraph()
    p_j_div.text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    p_j_div.font.size = Pt(8)
    p_j_div.font.color.rgb = BORDER_DEFAULT

    j_proofs = [
        ("Zero Duplicate Milestones", "Verified 0 duplicates via DB migration and seen_titles filter (24 passing tests)."),
        ("Synchronous Advancement", "Completing trial or reality check automatically advances active roadmap focus."),
        ("11.17 ms Retrieval Latency", "Next Best Action pre-computed and cached; eliminates redundant LLM round-trips.")
    ]
    for jt, jd in j_proofs:
        p = tf_jr.add_paragraph()
        p.text = f"• {jt}: {jd}"
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(4)

    add_footer(s6, "Captured from live deployment: https://career-os-seven-flame.vercel.app/journey · Benchmark: 11.17 ms avg")

    # =======================================================================
    # SLIDE 7: Career Validation (Reality Check & 7-Day Trial)
    # =======================================================================
    s7 = add_blank_slide(
        "Here is where we eliminate career regret: Before committing four years and tuition fees, students test the career. "
        "On the left: The Career Reality Check gives honest Pakistani salary bands, competition ratios, and local risks. "
        "On the right: The 7-Day Career Trial gives practical daily micro-tasks. Test the work before committing to the degree."
    )
    add_header(s7, "Stage 2: Validation", "Before You Commit, Test the Career.",
               "Grounding student expectations in verified Pakistani market realities, followed by hands-on 7-day trials.")

    # Left: Reality Check Screenshot
    add_mockup_image(s7, "05_reality_check.png", 0.80, 1.70, width=5.65)
    lbl_l = add_card(s7, 0.80, 5.65, 5.65, 1.10, SURFACE_CARD, BORDER_DEFAULT)
    tf_ll = lbl_l.text_frame
    tf_ll.word_wrap = True
    tf_ll.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_ll = tf_ll.paragraphs[0]
    p_ll.text = "REALITY CHECK: Software Engineer PKR 70k–120k entry salary · High demand · High admission cutoffs"
    p_ll.font.size = Pt(10)
    p_ll.font.bold = True
    p_ll.font.color.rgb = AMBER_ACCENT
    p_ll.font.name = FONT_FAMILY

    # Right: 7-Day Trial Screenshot
    add_mockup_image(s7, "06_seven_day_trial.png", 6.85, 1.70, width=5.68)
    lbl_r = add_card(s7, 6.85, 5.65, 5.68, 1.10, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_lr = lbl_r.text_frame
    tf_lr.word_wrap = True
    tf_lr.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_lr = tf_lr.paragraphs[0]
    p_lr.text = "7-DAY TRIAL: Day-by-day practical micro-tasks · Reflection prompts · Bi-directional journey sync"
    p_lr.font.size = Pt(10)
    p_lr.font.bold = True
    p_lr.font.color.rgb = GREEN_SUCCESS
    p_lr.font.name = FONT_FAMILY

    add_footer(s7, "Captured from live deployment: /careers/software-engineering/reality-check & /trial")

    # =======================================================================
    # SLIDE 8: Universities & Opportunities
    # =======================================================================
    s8 = add_blank_slide(
        "Once a career is validated, the student needs real options in Pakistan. We indexed 248 Higher Education Commission-recognized universities "
        "and 210 degree programs across all eight provinces and regions. Students filter by city, degree type, or public/private status, and immediately "
        "connect with 38 verified scholarships and corporate trainee internships."
    )
    add_header(s8, "Stage 3: Higher Education", "From Career Choice to Real Pakistani Options",
               "Connecting validated student pathways directly to 248 HEC universities, 210 degree programs, and 38 opportunities.")

    # 4 Metric Highlights Across Top
    u_metrics = [
        ("248", "HEC Universities", "166 Public, 82 Private across 8 regions"),
        ("210", "Degree Programs", "BS (129), BE (27), BBA (21), MBBS (8), Pharm-D (4)"),
        ("38", "Verified Opportunities", "18 National Scholarships, 17 Corporate Internships"),
        ("100%", "HEC-Recognized", "Zero unaccredited institutions in student directory"),
    ]
    for i, (val, lbl, sub) in enumerate(u_metrics):
        c_left = 0.80 + i * (2.75 + 0.24)
        c = add_card(s8, c_left, 1.70, 2.75, 1.15, SURFACE_ELEVATED, BORDER_ACTIVE)
        tf_c = c.text_frame
        tf_c.word_wrap = True
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_v = tf_c.paragraphs[0]
        p_v.text = val
        p_v.font.size = Pt(22)
        p_v.font.bold = True
        p_v.font.color.rgb = BLUE_LIGHT
        p_v.font.name = FONT_FAMILY
        p_l = tf_c.add_paragraph()
        p_l.text = lbl
        p_l.font.size = Pt(10)
        p_l.font.bold = True
        p_l.font.color.rgb = TEXT_WHITE
        p_l.font.name = FONT_FAMILY
        p_s = tf_c.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(8)
        p_s.font.color.rgb = TEXT_MUTED
        p_s.font.name = FONT_FAMILY

    # Left: Universities Screenshot
    add_mockup_image(s8, "07_universities.png", 0.80, 3.05, width=5.65)

    # Right: Opportunities Screenshot
    add_mockup_image(s8, "08_opportunities.png", 6.85, 3.05, width=5.68)

    add_footer(s8, "Captured from live deployment: /universities & /opportunities · BackEnd/ah_career.db verified")

    # =======================================================================
    # SLIDE 9: Skills → Job Readiness → Mock Interview
    # =======================================================================
    s9 = add_blank_slide(
        "Choosing a degree is only step one. Career OS takes the student all the way to employability through a three-stage progression: "
        "Learn through 86 curated resources. Prepare through automated Job Readiness audits. And Prove through our 10-question technical mock interview. "
        "Crucially, when a student finishes the mock interview, failed questions link directly back to learning resources to fix that specific gap."
    )
    add_header(s9, "Stage 4: Employability", "Choosing a Career Is Only Step One.",
               "A three-stage pipeline closing the employability gap: Learn foundational skills, prepare CV readiness, and prove technical competence.")

    # Stage 1: Learn
    c_s9_1 = add_card(s9, 0.80, 1.70, 3.65, 5.05, SURFACE_CARD, BORDER_DEFAULT)
    tf_s9_1 = c_s9_1.text_frame
    tf_s9_1.word_wrap = True
    p1 = tf_s9_1.paragraphs[0]
    p1.text = "1. LEARN (86 RESOURCES)"
    p1.font.size = Pt(12)
    p1.font.bold = True
    p1.font.color.rgb = BLUE_LIGHT
    p1.font.name = FONT_FAMILY
    p1.space_after = Pt(8)

    learn_bullets = [
        ("67 Technical Courses", "Curated curricula from Coursera, edX, MIT OCW, and DeepLearning.AI."),
        ("17 Vocational Programs", "Free training from NAVTTC, DigiSkills, and Punjab Skills Development Fund (PSDF)."),
        ("54 Free Resources", "High-quality zero-cost learning paths accessible across Pakistan."),
        ("Skill-Mapped Levels", "70 beginner, 15 intermediate, 1 advanced course linked to target career skills.")
    ]
    for lt, ld in learn_bullets:
        p = tf_s9_1.add_paragraph()
        p.text = f"• {lt}: {ld}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(6)

    # Stage 2: Prepare (Job Readiness screenshot embedded)
    add_mockup_image(s9, "12_job_readiness.png", 4.84, 1.70, width=3.65)
    c_s9_2 = add_card(s9, 4.84, 4.40, 3.65, 2.35, SURFACE_CARD, BORDER_DEFAULT)
    tf_s9_2 = c_s9_2.text_frame
    tf_s9_2.word_wrap = True
    p2 = tf_s9_2.paragraphs[0]
    p2.text = "2. PREPARE (JOB READINESS)"
    p2.font.size = Pt(11)
    p2.font.bold = True
    p2.font.color.rgb = AMBER_ACCENT
    p2.font.name = FONT_FAMILY
    p2.space_after = Pt(4)
    prep_bullets = [
        ("Dynamic Audit Score", "0–100% readiness score evaluating resume completeness and skills."),
        ("Missing Competency Alerts", "Flags immediate missing skills preventing interview selection.")
    ]
    for pt, pd in prep_bullets:
        p = tf_s9_2.add_paragraph()
        p.text = f"• {pt}: {pd}"
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(3)

    # Stage 3: Prove (Mock Interview screenshot embedded)
    add_mockup_image(s9, "09_mock_interview.png", 8.88, 1.70, width=3.65)
    c_s9_3 = add_card(s9, 8.88, 4.40, 3.65, 2.35, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_s9_3 = c_s9_3.text_frame
    tf_s9_3.word_wrap = True
    p3 = tf_s9_3.paragraphs[0]
    p3.text = "3. PROVE (QWEN MOCK INTERVIEW)"
    p3.font.size = Pt(11)
    p3.font.bold = True
    p3.font.color.rgb = GREEN_SUCCESS
    p3.font.name = FONT_FAMILY
    p3.space_after = Pt(4)
    prove_bullets = [
        ("10-Question Screening", "Domain-specific multiple-choice technical interview (4.73 ms cached setup)."),
        ("Direct Remediation Flow", "Weak topic areas link directly to specific Career OS learning resources.")
    ]
    for pt, pd in prove_bullets:
        p = tf_s9_3.add_paragraph()
        p.text = f"✓ {pt}: {pd}"
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_WHITE
        p.font.name = FONT_FAMILY
        p.space_after = Pt(3)

    add_footer(s9, "Captured from live deployment: /job-readiness & /mock-interview · BackEnd/services/mock_interview_service.py")

    # =======================================================================
    # SLIDE 10: Sports Pathway & Alumni Roadmap
    # =======================================================================
    s10 = add_blank_slide(
        "Career OS recognizes that not all student journeys are purely academic. On the left: Our live Sports Pathway features 18 verified athletic "
        "opportunities covering PCB academies, departmental trials like WAPDA, and university quotas. On the right: Our future Talk to Alumni roadmap. "
        "In keeping with strict product honesty, this is transparently presented as Coming Soon—we capture launch notification emails without faking AI personas."
    )
    add_header(s10, "Diversified Pathways", "Career Paths Aren't Only Academic",
               "Supporting athletic admissions today, while outlining a transparent roadmap for verified graduate mentorship.")

    # Left: Sports Pathway
    add_mockup_image(s10, "10_sports.png", 0.80, 1.70, width=5.65)
    c_sp = add_card(s10, 0.80, 5.60, 5.65, 1.15, SURFACE_CARD, BORDER_DEFAULT)
    tf_sp = c_sp.text_frame
    tf_sp.word_wrap = True
    p_sph = tf_sp.paragraphs[0]
    p_sph.text = "NOW LIVE: SPORTS & ATHLETIC PATHWAYS"
    p_sph.font.size = Pt(10.5)
    p_sph.font.bold = True
    p_sph.font.color.rgb = BLUE_LIGHT
    p_sph.font.name = FONT_FAMILY
    p_sph.space_after = Pt(3)
    p_spt = tf_sp.add_paragraph()
    p_spt.text = "• 18 Verified Listings across 11 Sports (Cricket, Football, Badminton, Squash, Athletics, Tennis)\n• PCB Regional Academies & Departmental Trials (WAPDA, Armed Forces)\n• University Sports Quotas at top institutions (NUST, FAST, Punjab University)"
    p_spt.font.size = Pt(8.8)
    p_spt.font.color.rgb = TEXT_MUTED
    p_spt.font.name = FONT_FAMILY

    # Right: Talk to Alumni (Coming Soon)
    add_mockup_image(s10, "11_alumni.png", 6.85, 1.70, width=5.68)
    c_al = add_card(s10, 6.85, 5.60, 5.68, 1.15, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_al = c_al.text_frame
    tf_al.word_wrap = True
    p_alh = tf_al.paragraphs[0]
    p_alh.text = "NEXT ROADMAP: TALK TO ALUMNI (COMING SOON)"
    p_alh.font.size = Pt(10.5)
    p_alh.font.bold = True
    p_alh.font.color.rgb = AMBER_ACCENT
    p_alh.font.name = FONT_FAMILY
    p_alh.space_after = Pt(3)
    p_alt = tf_al.add_paragraph()
    p_alt.text = "• Transparent Roadmap Preview: Clearly marked as Coming Soon on frontend & backend\n• Verified Institution Network: Preparing advisory connections with graduates from NUST, FAST, LUMS, IBA, GIKI\n• Live Notification Engine: Captures student emails on /alumni without fabricating AI chatbots"
    p_alt.font.size = Pt(8.8)
    p_alt.font.color.rgb = TEXT_WHITE
    p_alt.font.name = FONT_FAMILY

    add_footer(s10, "Captured from live deployment: /sports & /alumni · Product honesty: Alumni is strictly Coming Soon")

    # =======================================================================
    # SLIDE 11: Data Trust / PKE (Visual Pipeline)
    # =======================================================================
    s11 = add_blank_slide(
        "Look at this slide carefully: The AI is NOT the source of truth. In education, hallucinations destroy trust. "
        "Career OS separates reasoning from facts through the Pakistan Knowledge Engine. Level 1 official sources are parsed and quarantined in a staging table. "
        "Qwen extracts and normalizes fields, but deterministic validation gates decide what gets promoted. Unreviewed records are strictly blocked from student endpoints."
    )
    add_header(s11, "Data Integrity & Governance", "The AI Is Not the Source of Truth.",
               "Designed to prevent fabricated factual records through strict 4-level source hierarchy, content hashing, and hard visibility gates.")

    # Data Pipeline Diagram (5 horizontal steps)
    pke_steps = [
        ("1. Official Sources", "34 Level 1 authorities (HEC, NAVTTC, Unis, PCB, PFF)"),
        ("2. Extraction (Qwen)", "Qwen extracts & structures data; never asserts facts"),
        ("3. Pydantic Audit", "Strict schema enforcement against Pydantic models"),
        ("4. Staging Quarantine", "2,065 raw candidate records in pke_staging_records"),
        ("5. Visibility Gate", "CANDIDATE (Hidden) vs VALIDATED (Served to Students)")
    ]
    for i, (p_title, p_desc) in enumerate(pke_steps):
        c_left = 0.80 + i * (2.18 + 0.20)
        c = add_card(s11, c_left, 1.70, 2.18, 1.65, SURFACE_CARD, BORDER_DEFAULT if i != 4 else BORDER_ACTIVE)
        tf_c = c.text_frame
        tf_c.word_wrap = True
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_t = tf_c.paragraphs[0]
        p_t.text = p_title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = GREEN_SUCCESS if i == 4 else BLUE_LIGHT
        p_t.font.name = FONT_FAMILY
        p_t.space_after = Pt(4)
        p_d = tf_c.add_paragraph()
        p_d.text = p_desc
        p_d.font.size = Pt(8.5)
        p_d.font.color.rgb = TEXT_MUTED
        p_d.font.name = FONT_FAMILY

    # Lower Two Cards: Provenance & Visibility Gate
    c_prov = add_card(s11, 0.80, 3.55, 5.65, 3.20, SURFACE_CARD, BORDER_DEFAULT)
    tf_pr = c_prov.text_frame
    tf_pr.word_wrap = True
    p_prh = tf_pr.paragraphs[0]
    p_prh.text = "PROVENANCE COLUMNS ON EVERY RECORD"
    p_prh.font.size = Pt(11.5)
    p_prh.font.bold = True
    p_prh.font.color.rgb = BLUE_LIGHT
    p_prh.font.name = FONT_FAMILY
    p_prh.space_after = Pt(8)

    prov_fields = [
        ("source_id", "Canonical ID linking back to Level 1 / Level 2 registry"),
        ("source_url", "Direct link to official government/university source document"),
        ("content_hash", "SHA-256 hash guaranteeing document data integrity"),
        ("retrieved_at", "Timestamp ensuring freshness & automated stale-record purging"),
        ("Legal Compliance", "100% compliant with robots.txt; zero scraping of protected portals")
    ]
    for fld, fdesc in prov_fields:
        p = tf_pr.add_paragraph()
        p.text = f"• {fld}: {fdesc}"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(4)

    c_gate = add_card(s11, 6.85, 3.55, 5.68, 3.20, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_gt = c_gate.text_frame
    tf_gt.word_wrap = True
    p_gth = tf_gt.paragraphs[0]
    p_gth.text = "HARD STUDENT-FACING VISIBILITY GATE"
    p_gth.font.size = Pt(11.5)
    p_gth.font.bold = True
    p_gth.font.color.rgb = GREEN_SUCCESS
    p_gth.font.name = FONT_FAMILY
    p_gth.space_after = Pt(8)

    gate_items = [
        ("CANDIDATE / UNREVIEWED", "✗  Strictly isolated from student-facing endpoints", RED_ALERT),
        ("NEEDS_REVIEW", "✗  Quarantined until human/admin verification review", AMBER_ACCENT),
        ("VALIDATED", "✓  Only status permitted to reach student journeys & search", GREEN_SUCCESS),
        ("Deterministic Fallbacks", "If AI provider times out, grounded DB records serve answers", TEXT_WHITE)
    ]
    for gt_title, gt_desc, gt_color in gate_items:
        p = tf_gt.add_paragraph()
        p.text = f"• {gt_title} → {gt_desc}"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = gt_color
        p.font.name = FONT_FAMILY
        p.space_after = Pt(5)

    add_footer(s11, "Source: Docs/pakistan_knowledge_engine.md & BackEnd/retrieval/visibility.py · 2,065 staged records verified")

    # =======================================================================
    # SLIDE 12: Technical Architecture
    # =======================================================================
    s12 = add_blank_slide(
        "Here is how Career OS is engineered as a real full-stack system. Next.js 14 deployed on Vercel Edge. FastAPI on Render running SQLite in WAL mode. "
        "Three Model Context Protocol servers expose 19 verified database tools. And our AI layer runs on Alibaba Cloud Qwen 3.6-plus in Singapore with an "
        "automated four-model fallback chain. There is zero Gemini in production—startup fails closed if the model chain is misconfigured."
    )
    add_header(s12, "Engineering Blueprint", "Built as a Real Full-Stack System",
               "Next.js 14 Edge, FastAPI, Model Context Protocol (MCP), and Alibaba Qwen 3.6-plus with automated 4-model fallback.")

    # Left: Architecture Flow Block
    c_arch_flow = add_card(s12, 0.80, 1.70, 7.00, 5.05, SURFACE_CARD, BORDER_DEFAULT)
    tf_af = c_arch_flow.text_frame
    tf_af.word_wrap = True
    p_afh = tf_af.paragraphs[0]
    p_afh.text = "SYSTEM TOPOLOGY & DATA FLOW"
    p_afh.font.size = Pt(12)
    p_afh.font.bold = True
    p_afh.font.color.rgb = BLUE_LIGHT
    p_afh.font.name = FONT_FAMILY
    p_afh.space_after = Pt(10)

    arch_layers = [
        ("1. Frontend Layer", "Next.js 14 App Router, TypeScript, Tailwind CSS, Vercel Edge (17 routes, responsive)"),
        ("2. API Gateway Layer", "FastAPI on Render Starter, 47 REST endpoints, strict CORS, log sanitisation"),
        ("3. Model Context Protocol", "3 SSE server mounts (/mcp/career, /mcp/opportunity, /mcp/pke) with 19 tools"),
        ("4. Production AI Runtime", "Alibaba Cloud Model Studio / DashScope (Singapore MaaS endpoint)"),
        ("5. Persistent Storage Layer", "SQLAlchemy ORM + SQLite Write-Ahead-Logging (WAL) mode with FTS search")
    ]
    for lyr_t, lyr_d in arch_layers:
        p = tf_af.add_paragraph()
        p.text = f"• {lyr_t}: {lyr_d}"
        p.font.size = Pt(10.5)
        p.font.color.rgb = TEXT_WHITE if "Frontend" in lyr_t or "AI" in lyr_t else TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(8)

    # Right: Qwen Fallback Chain & Tool Spec
    c_qwen = add_card(s12, 8.00, 1.70, 4.53, 5.05, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_qw = c_qwen.text_frame
    tf_qw.word_wrap = True
    p_qwh = tf_qw.paragraphs[0]
    p_qwh.text = "MANDATED QWEN FALLBACK CHAIN"
    p_qwh.font.size = Pt(12)
    p_qwh.font.bold = True
    p_qwh.font.color.rgb = GREEN_SUCCESS
    p_qwh.font.name = FONT_FAMILY
    p_qwh.space_after = Pt(10)

    chain = [
        ("qwen3.6-plus", "PRIMARY", GREEN_SUCCESS),
        ("qwen-plus-2025-07-28", "FALLBACK 1", BLUE_LIGHT),
        ("qwen3-vl-235b-a22b-thinking", "FALLBACK 2", BLUE_LIGHT),
        ("qwen-turbo", "FALLBACK 3", AMBER_ACCENT),
    ]
    for mname, mrole, mcolor in chain:
        p = tf_qw.add_paragraph()
        p.text = f"▶ {mname} ({mrole})"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = mcolor
        p.font.name = FONT_FAMILY
        p.space_after = Pt(4)

    p_qdiv = tf_qw.add_paragraph()
    p_qdiv.text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    p_qdiv.font.size = Pt(8)
    p_qdiv.font.color.rgb = BORDER_DEFAULT

    p_rules = tf_qw.add_paragraph()
    p_rules.text = "• Fail-Closed Startup: Application validates Qwen model chain before accepting requests\n• Zero Gemini: Production strictly locked to verified Qwen MaaS\n• MCP Tools: 19 internal tools for career, opportunities, and PKE queries"
    p_rules.font.size = Pt(9.5)
    p_rules.font.color.rgb = TEXT_MUTED
    p_rules.font.name = FONT_FAMILY

    add_footer(s12, "Source: BackEnd/config.py, BackEnd/services/ai_service.py, Mcp/ directory, render.yaml")

    # =======================================================================
    # SLIDE 13: Proof (Testing, Performance & Live Status)
    # =======================================================================
    s13 = add_blank_slide(
        "Here is the proof that this isn't just a hackathon mockup. 806 automated tests passing in pytest with zero errors. "
        "Core database queries execute in 3 to 11 milliseconds thanks to SQLite Write-Ahead Logging and memory caching. "
        "And the frontend on Vercel, the API on Render, and our Swagger documentation are 100% live right now."
    )
    add_header(s13, "Verification Dashboard", "Built, Tested, and Live.",
               "Enterprise software engineering rigor with 806 automated test passes and verified production cloud health.")

    # 4 Top Verified Highlights
    p_highlights = [
        ("806", "Automated Tests", "100% passing across security, models, and E2E flows"),
        ("248", "HEC Universities", "100% recognized by Higher Education Commission"),
        ("22", "Career Pathways", "Curated Pakistani labor market intelligence"),
        ("210", "Degree Programs", "Comprehensive academic coverage across 64 fields"),
    ]
    for i, (val, lbl, sub) in enumerate(p_highlights):
        c_left = 0.80 + i * (2.75 + 0.24)
        c = add_card(s13, c_left, 1.70, 2.75, 1.25, SURFACE_ELEVATED, BORDER_ACTIVE)
        tf_c = c.text_frame
        tf_c.word_wrap = True
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_v = tf_c.paragraphs[0]
        p_v.text = val
        p_v.font.size = Pt(24)
        p_v.font.bold = True
        p_v.font.color.rgb = GREEN_SUCCESS if i == 0 else BLUE_LIGHT
        p_v.font.name = FONT_FAMILY
        p_l = tf_c.add_paragraph()
        p_l.text = lbl
        p_l.font.size = Pt(10)
        p_l.font.bold = True
        p_l.font.color.rgb = TEXT_WHITE
        p_l.font.name = FONT_FAMILY
        p_s = tf_c.add_paragraph()
        p_s.text = sub
        p_s.font.size = Pt(8)
        p_s.font.color.rgb = TEXT_MUTED
        p_s.font.name = FONT_FAMILY

    # Left: Measured Local Query Benchmarks
    c_lat = add_card(s13, 0.80, 3.15, 5.65, 3.60, SURFACE_CARD, BORDER_DEFAULT)
    tf_lt = c_lat.text_frame
    tf_lt.word_wrap = True
    p_lth = tf_lt.paragraphs[0]
    p_lth.text = "LOCAL DATABASE QUERY BENCHMARKS"
    p_lth.font.size = Pt(11.5)
    p_lth.font.bold = True
    p_lth.font.color.rgb = BLUE_LIGHT
    p_lth.font.name = FONT_FAMILY
    p_lth.space_after = Pt(8)

    lat_list = [
        ("Gateway Health Probe (/health)", "3.49 ms avg", "15 bytes payload"),
        ("Careers Catalog (/api/v1/careers)", "6.03 ms avg", "All 22 careers, 2,212 bytes"),
        ("Universities Directory (/api/v1/universities)", "4.83 ms avg", "248 institutions, 25,675 bytes"),
        ("Student Journey Retrieval (/api/v1/journey/{id})", "11.17 ms avg", "Full 4-phase state, 5,183 bytes"),
        ("Mock Interview Question Bank Cache", "4.73 ms avg", "10 questions, 4,169 bytes")
    ]
    for endp, lms, pld in lat_list:
        p = tf_lt.add_paragraph()
        p.text = f"• {endp}: {lms} ({pld})"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(4)

    # Right: Live Production Cloud Health
    c_live = add_card(s13, 6.85, 3.15, 5.68, 3.60, SURFACE_CARD, BORDER_DEFAULT)
    tf_lv = c_live.text_frame
    tf_lv.word_wrap = True
    p_lvh = tf_lv.paragraphs[0]
    p_lvh.text = "VERIFIED LIVE PRODUCTION HEALTH"
    p_lvh.font.size = Pt(11.5)
    p_lvh.font.bold = True
    p_lvh.font.color.rgb = GREEN_SUCCESS
    p_lvh.font.name = FONT_FAMILY
    p_lvh.space_after = Pt(8)

    live_list = [
        ("Web Application (Vercel Edge)", "HTTP 200 (1033 ms)", "career-os-seven-flame.vercel.app"),
        ("Backend Gateway (Render)", "HTTP 200 (406 ms)", "ah-career-backend.onrender.com"),
        ("Interactive Swagger API", "HTTP 200 (352 ms)", "ah-career-backend.onrender.com/docs"),
        ("Gateway Health Probe", "HTTP 200 (939 ms)", "ah-career-backend.onrender.com/health"),
        ("Automated Pytest Suite", "806 Tests Passing", "pytest in BackEnd/ (0 failures, 0 errors)")
    ]
    for sname, sres, surl in live_list:
        p = tf_lv.add_paragraph()
        p.text = f"✓  {sname}: {sres}\n    {surl}"
        p.font.size = Pt(9.2)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(3)

    add_footer(s13, "Source: Docs/PROJECT_REPORT.md §10, §12, §16 & live probe measurements September 7, 2026")

    # =======================================================================
    # SLIDE 14: Closing & Live Demonstration
    # =======================================================================
    s14 = add_blank_slide(
        "Pakistan has one of the youngest populations in the world, with over 60 million youth. By replacing rumors with structured, "
        "personalized operating systems, Career OS empowers the next generation of Pakistani engineers, doctors, entrepreneurs, and athletes "
        "to make confident, grounded life choices. The application is live right now. Thank you, and we invite you to experience the live demonstration."
    )
    add_header(s14, "Conclusion & Next Horizon", "Career OS Turns Uncertainty Into a Next Step.",
               "Bridging ambition and achievement for 60+ million Pakistani youth through structured, grounded guidance.")

    # Left: What We Built & Proved
    c_c_l = add_card(s14, 0.80, 1.70, 6.20, 5.05, SURFACE_CARD, BORDER_DEFAULT)
    tf_cl = c_c_l.text_frame
    tf_cl.word_wrap = True
    p_clh = tf_cl.paragraphs[0]
    p_clh.text = "WHAT WE BUILT & PROVED"
    p_clh.font.size = Pt(12)
    p_clh.font.bold = True
    p_clh.font.color.rgb = BLUE_LIGHT
    p_clh.font.name = FONT_FAMILY
    p_clh.space_after = Pt(10)

    c_summary = [
        ("The Operating System Works", "Proved that Pakistani career navigation can be structured into deterministic, stage-aware roadmaps."),
        ("Verified National Scale", "248 Universities, 210 Programs, 22 Pathways, 86 Learning Resources, 38 Opportunities, 18 Sports Pathways."),
        ("Enterprise Engineering", "806 automated tests, sub-15ms core queries, multi-model Qwen fallback, and active cloud deployment."),
        ("Immediate Next Horizon", "Partnering with secondary boards (FBISE, BIEK) and universities to embed Career OS into national counseling."),
        ("The Bottom Line", "Replaces anxiety, peer pressure, and rumors with confidence, clarity, and an actionable roadmap to employment.")
    ]
    for ct, cd in c_summary:
        p = tf_cl.add_paragraph()
        p.text = f"• {ct}: {cd}"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(8)

    # Right: Live Demonstration & Access Portal
    c_c_r = add_card(s14, 7.30, 1.70, 5.23, 5.05, SURFACE_ELEVATED, BORDER_ACTIVE)
    tf_cr = c_c_r.text_frame
    tf_cr.word_wrap = True
    p_crh = tf_cr.paragraphs[0]
    p_crh.text = "LIVE DEMONSTRATION & ACCESS"
    p_crh.font.size = Pt(12)
    p_crh.font.bold = True
    p_crh.font.color.rgb = GREEN_SUCCESS
    p_crh.font.name = FONT_FAMILY
    p_crh.space_after = Pt(12)

    p_wm = tf_cr.add_paragraph()
    p_wm.text = "CAREER OS"
    p_wm.font.size = Pt(26)
    p_wm.font.bold = True
    p_wm.font.color.rgb = TEXT_WHITE
    p_wm.font.name = FONT_FAMILY
    p_wm.space_after = Pt(12)

    demo_bullets = [
        ("Web Application", "https://career-os-seven-flame.vercel.app"),
        ("Backend Gateway", "https://ah-career-backend.onrender.com"),
        ("Interactive Swagger", "https://ah-career-backend.onrender.com/docs"),
        ("Repository", "https://github.com/anasimam10/Career-OS"),
        ("Live Demonstration Flow", "Try 7-Step Onboarding → Journey → 7-Day Trial → Mock Interview")
    ]
    for dt, du in demo_bullets:
        p = tf_cr.add_paragraph()
        p.text = f"→ {dt}:\n   {du}"
        p.font.size = Pt(9.8)
        p.font.color.rgb = BLUE_LIGHT if "http" in du else TEXT_MUTED
        p.font.name = FONT_FAMILY
        p.space_after = Pt(7)

    add_footer(s14, "Career OS — Pakistan's Career Operating System · All Rights Reserved 2026")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    print(f"Successfully generated final deck: {output_path} ({len(prs.slides)} slides)", flush=True)


if __name__ == "__main__":
    out = Path("Docs/Career_OS_Presentation_FINAL.pptx")
    build_final_deck(out)
