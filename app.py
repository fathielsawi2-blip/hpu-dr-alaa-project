import streamlit as st
import sqlite3
import pandas as pd
import json
import re
import base64
from datetime import date, datetime
from io import BytesIO

from openai import OpenAI

# ============================================================
# HPU | HUMAN PROCESSING UNIT
# Dr. Alaa Zahran - Personal Brand Intelligence
# ============================================================

st.set_page_config(
    page_title="HPU | Alaa Zahran",
    page_icon="⚙️",
    layout="wide"
)

DB = "hpu_alaa.db"
TEXT_MODEL = "gpt-4.1-mini"
IMAGE_MODEL = "gpt-image-1"
AUDIO_MODEL = "gpt-4o-mini-tts"

# ------------------------------------------------------------
# VERIFIED CV KNOWLEDGE
# Extracted from Alaa_Zahran_Communication Executive_detailed
# CV2026.pdf. This is inserted once into the local SQLite DB.
# ------------------------------------------------------------

CV_KNOWLEDGE = [
    {
        "category": "Executive Profile",
        "title": "Professional profile",
        "details": (
            "Strategic and corporate communications executive with 19+ years "
            "of experience across Saudi government, Vision 2030 transformation, "
            "consulting, and events. Specialisms include strategic communications, "
            "integrated marketing communications, reputation and brand management, "
            "and leadership of communication projects, programs and campaign portfolios. "
            "Builds communication and change functions, translates institutional "
            "priorities into strategies and delivery plans, and leads multidisciplinary "
            "teams, agencies, budgets, governance, KPIs and senior stakeholder relationships."
        )
    },
    {
        "category": "Career Achievement",
        "title": "Ministry of Municipalities and Housing",
        "details": (
            "Led a team of 45+ and managed municipal transformation campaigns with "
            "budgets exceeding SAR 250M; contributed to municipal-transformation "
            "awareness reaching 45%. Career period: April 2016 to October 2019."
        )
    },
    {
        "category": "Career Achievement",
        "title": "Ministry of Health - Vision Realization Office",
        "details": (
            "Led teams exceeding 35 professionals and managed communication projects "
            "and campaigns with budgets exceeding SAR 65M. Career period: October 2019 "
            "to February 2021."
        )
    },
    {
        "category": "Career Achievement",
        "title": "Health Sector Transformation Program",
        "details": (
            "Led/coordinated 25+ professionals across the program and initiatives and "
            "managed communication projects and campaigns with budgets exceeding SAR 42M. "
            "Led one major national campaign that generated 500M+ media impressions through "
            "participation of 30+ government entities and received recognition from CEDA. "
            "Contributed to increasing HSTP brand and initiative awareness from 16% to 78%. "
            "Career period: February 2021 to May 2024."
        )
    },
    {
        "category": "Career Achievement",
        "title": "Nahj Arabia for Media Consulting Company",
        "details": (
            "As General Manager / Partner from June 2024 to November 2025, managed "
            "60+ professionals across company and client-project teams; led consulting, "
            "strategic communication, content, media, marketing and event workstreams."
        )
    },
    {
        "category": "Current Role",
        "title": "SUMMIT Events & Exhibitions",
        "details": (
            "Operations Director from November 2025 to present. Leads a 25-person "
            "multidisciplinary team and directs end-to-end delivery of client projects "
            "and integrated communication experiences, including strategy, creative "
            "development, production, logistics and execution."
        )
    },
    {
        "category": "Specialized Methodology",
        "title": "Change management",
        "details": (
            "Designed the first Prosci-aligned Change Management methodology at Saudi "
            "national health-sector level and conducted sector-wide change-readiness "
            "assessments."
        )
    },
    {
        "category": "Specialized Project",
        "title": "Health Volunteering platform",
        "details": (
            "Launched and managed the Health Volunteering platform, established its "
            "media center, and supervised Kingdom-wide promotional communication, "
            "reaching 600K+ registers."
        )
    },
    {
        "category": "Specialized Project",
        "title": "Selected consulting and transformation projects",
        "details": (
            "Selected projects in the CV include development of guidance materials for "
            "the Kingdom's waste-management ecosystem and contribution to a national "
            "waste-awareness program; design, preparation and launch of a municipal "
            "inspection program in NEOM; marketing strategy for integration involving "
            "event companies add+ and GL; and strategic content for the LEARN Conference."
        )
    },
    {
        "category": "Core Expertise",
        "title": "Professional expertise",
        "details": (
            "Strategic and Corporate Communications; Integrated Marketing Communications; "
            "Communication Project, Program and Portfolio Leadership; Campaign Planning "
            "and Delivery; Corporate Affairs; Reputation and Brand Strategy; Vision 2030 "
            "Transformation; Change Management and Change Communication; Stakeholder and "
            "Executive Engagement; Communication Governance and Operating Models; Project "
            "Scope, Budgets, Timelines and Resources; KPIs and Impact Measurement; Crisis "
            "and Issues Communication; Internal and External Communications; Digital and "
            "Social Media; SOWs and RFPs; Events and Experience Delivery; Team Leadership; "
            "Certified Training and Knowledge Transfer."
        )
    },
    {
        "category": "Education",
        "title": "Academic qualifications",
        "details": (
            "Ph.D. in Communications, Media & Public Relations - Mansoura University, Egypt. "
            "Master's Degree in Media & Public Relations - Mansoura University. "
            "Post-Graduate Diploma in Public Relations, Distinction - Cairo University. "
            "Degree in Mass Communications - Tanta University, Egypt, 2006."
        )
    },
    {
        "category": "Certifications",
        "title": "Professional certifications",
        "details": (
            "Certified Strategic Communication Thinking, Planning & Execution - Oxford "
            "Management Center, Dubai; Certified Change Management Practitioner - Prosci; "
            "Founding Board Member, Saudi Chapter - Association of Change Management "
            "Professionals (ACMP); Lean Six Sigma Green Belt - Lawrence Technological "
            "University; Certified Trainer - Ain Shams University; TOT / Accredited Trainer, "
            "CPD - United Kingdom; Digital Marketing Specialist Training."
        )
    },
    {
        "category": "Training",
        "title": "Training and knowledge transfer",
        "details": (
            "Designs and delivers specialized training programs, executive workshops and "
            "knowledge-transfer sessions in strategic and corporate communication, "
            "integrated marketing communication, campaign planning, PR, branding and "
            "change communication."
        )
    },
    {
        "category": "Languages",
        "title": "Languages",
        "details": "Arabic: Native. English: Professional Working Proficiency."
    }
]

EXPERTISE_MAP = {
    "Strategic & Corporate Communications": ["strategic communication", "corporate communication", "communication strategy"],
    "Integrated Marketing Communications": ["integrated marketing", "marketing communication", "campaign"],
    "Project, Program & Portfolio Leadership": ["project", "program", "portfolio", "delivery"],
    "Reputation & Brand Strategy": ["reputation", "brand", "branding", "identity"],
    "Vision 2030 Transformation": ["vision 2030", "transformation", "transformation program"],
    "Change Management": ["change management", "change communication", "change readiness"],
    "Stakeholder & Executive Engagement": ["stakeholder", "executive engagement", "senior leadership"],
    "Governance & Operating Models": ["governance", "operating model", "workflow", "operating"],
    "KPIs & Impact Measurement": ["kpi", "measurement", "impact", "awareness", "impressions"],
    "Crisis & Issues Communication": ["crisis", "issues communication", "risk"],
    "Digital & Social Media": ["digital", "social media", "linkedin"],
    "Events & Experience Delivery": ["event", "exhibition", "experience delivery"],
    "Training & Knowledge Transfer": ["training", "workshop", "knowledge transfer", "capability"]
}

# ============================================================
# DATABASE
# ============================================================

def connect_db():
    return sqlite3.connect(DB, check_same_thread=False)

def initialize_database():
    with connect_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, description TEXT, expertise TEXT, date_added TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, audience TEXT, platform TEXT, content_type TEXT,
            status TEXT, objective TEXT, publish_date TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER, views INTEGER, likes INTEGER,
            comments INTEGER, shares INTEGER
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT, answer TEXT, analysis TEXT, created_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS cv_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, title TEXT, details TEXT, source TEXT,
            created_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS source_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, source_type TEXT, raw_text TEXT,
            audience TEXT, platform TEXT, language TEXT, tone TEXT,
            objective TEXT, created_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS generated_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER, asset_type TEXT, title TEXT,
            content TEXT, file_data BLOB, file_name TEXT,
            status TEXT, created_at TEXT
        )""")

        # Preserve compatibility with the original database.
        columns = [r[1] for r in conn.execute("PRAGMA table_info(content)").fetchall()]
        if "source_interview_id" not in columns:
            conn.execute("ALTER TABLE content ADD COLUMN source_interview_id INTEGER")

        # Add CV records only once.
        count = conn.execute("SELECT COUNT(*) FROM cv_knowledge").fetchone()[0]
        if count == 0:
            for item in CV_KNOWLEDGE:
                conn.execute(
                    """INSERT INTO cv_knowledge
                    (category, title, details, source, created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (item["category"], item["title"], item["details"],
                     "Dr. Alaa Zahran detailed CV 2026", datetime.now().isoformat(timespec="seconds"))
                )

initialize_database()

def read_table(table):
    allowed = ["experiences", "content", "performance", "interviews",
               "cv_knowledge", "source_materials", "generated_assets"]
    if table not in allowed:
        raise ValueError("Invalid table")
    with connect_db() as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)

def get_cv_context():
    cv = read_table("cv_knowledge")
    if cv.empty:
        return "No CV knowledge has been loaded."
    return "\n\n".join(
        f"[{r['category']}] {r['title']}: {r['details']}"
        for _, r in cv.iterrows()
    )

# ============================================================
# OPENAI CONNECTION
# ============================================================

def get_openai_client():
    key = st.secrets.get("key_ZogttToTgjc3Ynoh", "")
    if not key:
        return None
    return OpenAI(api_key=key)

def generate_text_with_ai(client, prompt):
    response = client.responses.create(
        model=TEXT_MODEL,
        instructions=(
            "You are HPU, a rigorous personal-brand intelligence and content "
            "strategist for Dr. Alaa Zahran. Use the CV knowledge as verified "
            "reference material, not as permission to invent facts. Clearly "
            "separate verified CV facts, facts from the supplied source, and "
            "your strategic interpretation. Never invent metrics, clients, dates, "
            "roles, quotations, or outcomes. If evidence is missing, flag it. "
            "Write polished, credible professional content. Avoid exaggerated "
            "self-promotion and generic AI language."
        ),
        input=prompt
    )
    return response.output_text

def make_image(client, prompt):
    result = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size="1024x1024"
    )
    return base64.b64decode(result.data[0].b64_json)

def make_audio(client, text, voice):
    result = client.audio.speech.create(
        model=AUDIO_MODEL,
        voice=voice,
        input=text,
        response_format="mp3"
    )
    return result.read()

# ============================================================
# CONTENT INTELLIGENCE
# ============================================================

def local_analysis(source_text):
    text = source_text.lower()
    detected = []
    for area, keywords in EXPERTISE_MAP.items():
        if any(k in text for k in keywords):
            detected.append(area)

    numbers = re.findall(r"\b\d+(?:\.\d+)?\s*%?\b", source_text)
    if not detected:
        detected = ["Needs deeper review"]

    return {"detected_expertise": detected, "numbers_in_source": numbers}

def build_analysis_prompt(source_text, audience, platform, language, tone, objective):
    return f"""
Analyze the following source material for Dr. Alaa Zahran.

CV KNOWLEDGE BASE (verified reference facts):
{get_cv_context()}

NEW SOURCE MATERIAL (treat this as a separate source; do not assume every claim is independently verified):
{source_text}

USER SETTINGS:
Target audience: {audience}
Platform: {platform}
Language: {language}
Tone: {tone}
Objective: {objective}

Produce a structured, detailed analysis with these headings:
1. Source material summary
2. Main themes and professional concepts
3. Relevant verified CV connections (cite role/project/achievement in plain language)
4. What is genuinely new in this source
5. Potential content angles (at least 5, each with audience and purpose)
6. Evidence and credibility check (facts, metrics, dates, claims that need confirmation)
7. Missing information / questions to ask Dr. Alaa
8. Recommended content strategy for the selected platform
9. Suggested text post
10. Suggested visual concept and image-generation prompt
11. Suggested audio narration script

Do not attribute a claim from the new source to the CV unless the CV supports it.
Do not invent missing context. If the source is too short, say what is missing.
"""

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("HPU")
st.sidebar.caption("Human Processing Unit | Content Intelligence")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "CV Knowledge Base", "Live Interview",
     "Interview Records", "Professional Experiences",
     "Content Studio", "Publishing Planner", "Performance"]
)
st.sidebar.markdown("---")
st.sidebar.caption("Dr. Alaa Zahran | Strategic Communications")

# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":
    st.title("Dr. Alaa Zahran")
    st.subheader("Personal Brand Intelligence Platform")
    experiences = read_table("experiences")
    content = read_table("content")
    interviews = read_table("interviews")
    sources = read_table("source_materials")
    assets = read_table("generated_assets")
    cv = read_table("cv_knowledge")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("CV Knowledge Items", len(cv))
    c2.metric("Experiences", len(experiences))
    c3.metric("Interview Answers", len(interviews))
    c4.metric("Source Materials", len(sources))
    c5.metric("Generated Assets", len(assets))

    st.markdown("---")
    st.subheader("HPU Processing Workflow")
    st.write("CV Knowledge → Source Analysis → Experience Matching → Content Strategy → Text / Visual / Audio → Review")
    st.info("The CV is loaded as the foundational reference database. Add new source material in Content Studio to generate evidence-aware content.")
    with st.expander("Current CV knowledge categories"):
        st.dataframe(cv[["category", "title"]], use_container_width=True, hide_index=True)

# ============================================================
# CV KNOWLEDGE BASE
# ============================================================

elif page == "CV Knowledge Base":
    st.title("CV Knowledge Base")
    st.caption("Foundational reference information extracted from Dr. Alaa's 2026 detailed CV.")
    cv = read_table("cv_knowledge")
    st.metric("Knowledge records", len(cv))
    categories = ["All"] + sorted(cv["category"].dropna().unique().tolist())
    selected_category = st.selectbox("Filter by knowledge category", categories)
    view = cv if selected_category == "All" else cv[cv["category"] == selected_category]
    for _, item in view.iterrows():
        with st.expander(f"{item['category']} | {item['title']}"):
            st.write(item["details"])
            st.caption(f"Source: {item['source']}")

    st.markdown("---")
    st.subheader("Add verified information")
    with st.form("add_cv_knowledge"):
        category = st.text_input("Category", placeholder="e.g. Additional Achievement")
        title = st.text_input("Record title")
        details = st.text_area("Verified information", height=130)
        add = st.form_submit_button("Add to knowledge base")
        if add:
            if category.strip() and title.strip() and details.strip():
                with connect_db() as conn:
                    conn.execute(
                        "INSERT INTO cv_knowledge (category,title,details,source,created_at) VALUES (?,?,?,?,?)",
                        (category, title, details, "User-added verified information", datetime.now().isoformat(timespec="seconds"))
                    )
                st.success("Added to the CV knowledge base.")
                st.rerun()
            else:
                st.warning("Complete all fields.")

# ============================================================
# LIVE INTERVIEW
# ============================================================

elif page == "Live Interview":
    st.title("Live Interview")
    st.write("Capture professional knowledge and compare it with the CV reference database.")
    questions = {
        "Professional Journey": [
            "Tell me about your professional journey.",
            "What were the most important turning points in your career?",
            "Which professional experience influenced your development most?"
        ],
        "Achievements": [
            "What are your three most important professional achievements?",
            "Which project are you most proud of?",
            "What measurable results did your work produce?"
        ],
        "Leadership": [
            "Describe your experience leading teams.",
            "How do you approach executive engagement?",
            "How do you handle difficult stakeholders?"
        ],
        "Strategic Communication": [
            "How do you develop a communication strategy?",
            "How do you measure communication effectiveness?",
            "Describe a challenging communication project."
        ],
        "Transformation": [
            "What was your role in organizational transformation?",
            "How have you contributed to Vision 2030 objectives?",
            "How do you manage resistance to change?"
        ],
        "Academic Experience": [
            "What is the central idea of your PhD research?",
            "What practical problems does your research address?",
            "How can your academic research benefit organizations?"
        ],
        "Future Vision": [
            "What professional impact would you like to create?",
            "Which areas would you like to be recognized for?",
            "What consulting opportunities interest you most?"
        ]
    }
    category = st.selectbox("Interview category", list(questions.keys()))
    question = st.selectbox("Interview question", questions[category])
    answer = st.text_area("Dr. Alaa's answer", height=220)
    client = get_openai_client()
    if st.button("Analyze interview answer", type="primary"):
        if len(answer.strip()) < 30:
            st.warning("Enter a more complete answer (at least 30 characters).")
        elif client is None:
            st.error("OPENAI_API_KEY is missing from Streamlit Secrets.")
        else:
            with st.spinner("Comparing the answer with CV knowledge..."):
                prompt = build_analysis_prompt(
                    answer, "Professional audience", "LinkedIn",
                    "English", "Executive and insightful",
                    "Capture and develop professional knowledge"
                )
                analysis = generate_text_with_ai(client, prompt)
                st.session_state["interview_analysis"] = analysis
                st.session_state["interview_question"] = question
                st.session_state["interview_answer"] = answer
    if st.session_state.get("interview_analysis"):
        st.markdown(st.session_state["interview_analysis"])
        if st.button("Save interview record"):
            with connect_db() as conn:
                conn.execute(
                    "INSERT INTO interviews (question,answer,analysis,created_at) VALUES (?,?,?,?)",
                    (st.session_state["interview_question"],
                     st.session_state["interview_answer"],
                     st.session_state["interview_analysis"],
                     datetime.now().isoformat(timespec="seconds"))
                )
            st.success("Interview record saved.")

# ============================================================
# INTERVIEW RECORDS
# ============================================================

elif page == "Interview Records":
    st.title("Interview Knowledge Records")
    records = read_table("interviews")
    if records.empty:
        st.info("No interview records yet.")
    else:
        st.dataframe(records[["id", "question", "created_at"]], use_container_width=True, hide_index=True)
        selected = st.selectbox("Open record", records["id"].tolist())
        record = records[records["id"] == selected].iloc[0]
        st.subheader(record["question"])
        st.write(record["answer"])
        st.markdown(record["analysis"])

# ============================================================
# PROFESSIONAL EXPERIENCES
# ============================================================

elif page == "Professional Experiences":
    st.title("Professional Experience Database")
    with st.form("experience_form"):
        title = st.text_input("Experience title")
        description = st.text_area("Description", height=150)
        expertise = st.selectbox("Professional area", list(EXPERTISE_MAP.keys()))
        submitted = st.form_submit_button("Save Experience")
        if submitted:
            if title.strip() and description.strip():
                with connect_db() as conn:
                    conn.execute(
                        "INSERT INTO experiences (title,description,expertise,date_added) VALUES (?,?,?,?)",
                        (title, description, expertise, str(date.today()))
                    )
                st.success("Experience saved.")
            else:
                st.warning("Complete the required fields.")
    st.markdown("---")
    st.dataframe(read_table("experiences"), use_container_width=True, hide_index=True)

# ============================================================
# CONTENT STUDIO - MAIN GENERATION WORKSPACE
# ============================================================

elif page == "Content Studio":
    st.title("Content Studio")
    st.caption("Transform source material into evidence-aware text, visual and audio content.")

    client = get_openai_client()
    if client is None:
        st.error("OpenAI API key not found. Add OPENAI_API_KEY in Streamlit Community Cloud → Manage app → Settings → Secrets.")
    else:
        st.success("AI connection configured.")

    with st.form("source_material_form"):
        st.subheader("1. Insert source material")
        source_title = st.text_input("Material title", placeholder="e.g. HSTP transformation communication experience")
        source_type = st.selectbox(
            "Material type",
            ["Existing post", "Professional experience", "Project description",
             "Research / academic material", "Interview notes", "Article / report",
             "Achievement", "Other"]
        )
        source_text = st.text_area(
            "Paste the content or information you already have",
            height=260,
            placeholder="Paste the full text, notes, project details, article or experience here..."
        )
        st.subheader("2. Content direction")
        c1, c2 = st.columns(2)
        with c1:
            audience = st.selectbox(
                "Target audience",
                ["Business Executives", "Communication Professionals",
                 "Academics and Researchers", "Consultants",
                 "Government and Public-Sector Leaders",
                 "General Professional Audience"]
            )
            platform = st.selectbox("Platform", ["LinkedIn", "Facebook", "Instagram", "Other"])
            language = st.selectbox("Language", ["English", "Arabic", "Arabic and English"])
        with c2:
            tone = st.selectbox(
                "Tone",
                ["Executive and insightful", "Academic and analytical",
                 "Consultative and practical", "Thought leadership",
                 "Personal and reflective"]
            )
            objective = st.selectbox(
                "Primary objective",
                ["Build executive credibility", "Demonstrate expertise",
                 "Share a professional lesson", "Explain a complex topic",
                 "Promote consulting services", "Increase professional engagement"]
            )
        save_source = st.form_submit_button("Save source material", type="primary")

    if save_source:
        if not source_title.strip() or not source_text.strip():
            st.warning("Enter both a title and source material.")
        else:
            with connect_db() as conn:
                cur = conn.execute(
                    """INSERT INTO source_materials
                    (title,source_type,raw_text,audience,platform,language,tone,objective,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (source_title, source_type, source_text, audience, platform,
                     language, tone, objective, datetime.now().isoformat(timespec="seconds"))
                )
                st.session_state["active_source_id"] = cur.lastrowid
                st.session_state["active_source_text"] = source_text
                st.session_state["active_source_title"] = source_title
                st.session_state["active_source_settings"] = {
                    "audience": audience, "platform": platform, "language": language,
                    "tone": tone, "objective": objective
                }
            st.success(f"Source material saved as record #{st.session_state['active_source_id']}.")

    st.markdown("---")
    st.subheader("3. Select saved source material")
    sources = read_table("source_materials")
    if not sources.empty:
        source_options = sources["id"].tolist()
        selected_source = st.selectbox(
            "Choose source material to process",
            source_options,
            format_func=lambda x: f"#{x} — {sources.loc[sources['id'] == x, 'title'].iloc[0]}"
        )
        selected_row = sources[sources["id"] == selected_source].iloc[0]
        active_text = selected_row["raw_text"]
        active_title = selected_row["title"]
        active_settings = {
            "audience": selected_row["audience"],
            "platform": selected_row["platform"],
            "language": selected_row["language"],
            "tone": selected_row["tone"],
            "objective": selected_row["objective"]
        }
        st.caption(f"Source type: {selected_row['source_type']} | Added: {selected_row['created_at']}")
        with st.expander("View original source material"):
            st.write(active_text)

        local = local_analysis(active_text)
        st.markdown("**Initial technical signals**")
        st.write("Potential expertise matches:", ", ".join(local["detected_expertise"]))
        if local["numbers_in_source"]:
            st.write("Numbers found in source:", ", ".join(local["numbers_in_source"]))

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Run deep AI analysis", type="primary", use_container_width=True):
                if client is None:
                    st.error("API key is not configured.")
                else:
                    with st.spinner("Analysing source against the CV knowledge base..."):
                        prompt = build_analysis_prompt(
                            active_text, active_settings["audience"],
                            active_settings["platform"], active_settings["language"],
                            active_settings["tone"], active_settings["objective"]
                        )
                        try:
                            analysis = generate_text_with_ai(client, prompt)
                            st.session_state["analysis_result"] = analysis
                            st.session_state["analysis_source_id"] = int(selected_source)
                        except Exception as e:
                            st.error(f"Text generation failed: {e}")
        with col_b:
            if st.button("Clear generated results", use_container_width=True):
                for key in ["analysis_result", "generated_post", "visual_prompt", "audio_script"]:
                    st.session_state.pop(key, None)
                st.rerun()

        if st.session_state.get("analysis_source_id") == int(selected_source):
            st.markdown("---")
            st.subheader("HPU intelligence report")
            st.markdown(st.session_state.get("analysis_result", ""))

            st.markdown("---")
            st.subheader("4. Generate individual assets")
            st.caption("Generate only the formats you need. Image and audio generation may incur separate API charges.")

            post_prompt = f"""
Use the source material and verified CV context below to create a polished {active_settings['platform']} post.
Audience: {active_settings['audience']}
Language: {active_settings['language']}
Tone: {active_settings['tone']}
Objective: {active_settings['objective']}

Verified CV knowledge:
{get_cv_context()}

Source material:
{active_text}

Rules: Do not invent facts or metrics. Use only claims supported by the CV or source.
If a detail is uncertain, omit it or mark it for confirmation.
Provide a strong opening, coherent insight, practical value and a natural closing.
Include suitable hashtags at the end. Return the post only.
"""
            if st.button("Generate text post"):
                if client:
                    with st.spinner("Writing post..."):
                        try:
                            post = generate_text_with_ai(client, post_prompt)
                            st.session_state["generated_post"] = post
                            st.session_state["generated_post_source"] = int(selected_source)
                        except Exception as e:
                            st.error(f"Text generation failed: {e}")
            if st.session_state.get("generated_post_source") == int(selected_source):
                st.text_area("Editable generated post", key="generated_post_editor",
                             value=st.session_state.get("generated_post", ""), height=260)
                if st.button("Save text post"):
                    text_value = st.session_state.get("generated_post_editor", st.session_state.get("generated_post", ""))
                    with connect_db() as conn:
                        conn.execute(
                            """INSERT INTO generated_assets
                            (source_id,asset_type,title,content,status,created_at)
                            VALUES (?,?,?,?,?,?)""",
                            (int(selected_source), "Text", active_title, text_value,
                             "Draft", datetime.now().isoformat(timespec="seconds"))
                        )
                    st.success("Text post saved to generated assets.")

            visual_prompt = f"""
Create a professional editorial visual for a senior strategic communications executive's LinkedIn content.
Topic: {active_title}
Source material: {active_text[:2500]}
Style: premium corporate editorial photography, sophisticated composition, credible public-sector and organizational transformation context, realistic, clean visual hierarchy, no logos, no watermarks, no fake text, no invented people or identifiable public figures.
Create a strong visual metaphor for the core idea. Avoid generic stock-photo clichés.
"""
            if st.button("Generate visual image"):
                if client:
                    with st.spinner("Generating visual..."):
                        try:
                            image_bytes = make_image(client, visual_prompt)
                            st.session_state["generated_image_bytes"] = image_bytes
                            st.session_state["generated_image_source"] = int(selected_source)
                        except Exception as e:
                            st.error(f"Image generation failed: {e}")
            if st.session_state.get("generated_image_source") == int(selected_source):
                img = st.session_state["generated_image_bytes"]
                st.image(img, caption="Generated HPU visual", use_container_width=True)
                st.download_button("Download visual", data=img, file_name=f"hpu_visual_{selected_source}.png", mime="image/png")
                if st.button("Save visual to database"):
                    with connect_db() as conn:
                        conn.execute(
                            """INSERT INTO generated_assets
                            (source_id,asset_type,title,content,file_data,file_name,status,created_at)
                            VALUES (?,?,?,?,?,?,?,?)""",
                            (int(selected_source), "Visual", active_title, visual_prompt,
                             sqlite3.Binary(img), f"hpu_visual_{selected_source}.png",
                             "Draft", datetime.now().isoformat(timespec="seconds"))
                        )
                    st.success("Visual saved to generated assets.")

            audio_default = st.session_state.get("generated_post", active_text)
            audio_script = st.text_area("Audio narration script (editable)", value=audio_default, height=180, key="audio_script_editor")
            voice = st.selectbox("Narration voice", ["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"])
            if st.button("Generate audio narration"):
                if client:
                    with st.spinner("Generating audio..."):
                        try:
                            audio_bytes = make_audio(client, audio_script, voice)
                            st.session_state["generated_audio_bytes"] = audio_bytes
                            st.session_state["generated_audio_source"] = int(selected_source)
                        except Exception as e:
                            st.error(f"Audio generation failed: {e}")
            if st.session_state.get("generated_audio_source") == int(selected_source):
                audio_bytes = st.session_state["generated_audio_bytes"]
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button("Download audio", data=audio_bytes,
                                   file_name=f"hpu_audio_{selected_source}.mp3",
                                   mime="audio/mpeg")
                if st.button("Save audio to database"):
                    with connect_db() as conn:
                        conn.execute(
                            """INSERT INTO generated_assets
                            (source_id,asset_type,title,content,file_data,file_name,status,created_at)
                            VALUES (?,?,?,?,?,?,?,?)""",
                            (int(selected_source), "Audio", active_title, audio_script,
                             sqlite3.Binary(audio_bytes), f"hpu_audio_{selected_source}.mp3",
                             "Draft", datetime.now().isoformat(timespec="seconds"))
                        )
                    st.success("Audio saved to generated assets.")
    else:
        st.info("Save your first source material above to begin.")

    st.markdown("---")
    st.subheader("Saved generated assets")
    assets = read_table("generated_assets")
    if assets.empty:
        st.info("No generated assets saved yet.")
    else:
        st.dataframe(
            assets[["id", "source_id", "asset_type", "title", "status", "created_at"]],
            use_container_width=True, hide_index=True
        )
        asset_id = st.selectbox("Open saved asset", assets["id"].tolist(), key="open_asset")
        asset = assets[assets["id"] == asset_id].iloc[0]
        st.write(f"**{asset['asset_type']} — {asset['title']}**")
        if asset["asset_type"] == "Text":
            st.text_area("Saved text", value=asset["content"], height=220, key=f"asset_text_{asset_id}")
        elif asset["file_data"] is not None:
            raw = bytes(asset["file_data"])
            if asset["asset_type"] == "Visual":
                st.image(raw, use_container_width=True)
                st.download_button("Download saved visual", raw, file_name=asset["file_name"], key=f"dl_{asset_id}")
            elif asset["asset_type"] == "Audio":
                st.audio(raw, format="audio/mp3")
                st.download_button("Download saved audio", raw, file_name=asset["file_name"], mime="audio/mpeg", key=f"dl_{asset_id}")
        new_status = st.selectbox("Asset review status", ["Draft", "Under Review", "Approved", "Rejected"], key=f"status_{asset_id}")
        if st.button("Update asset status"):
            with connect_db() as conn:
                conn.execute("UPDATE generated_assets SET status=? WHERE id=?", (new_status, int(asset_id)))
            st.success("Asset status updated.")
            st.rerun()

# ============================================================
# PUBLISHING PLANNER
# ============================================================

elif page == "Publishing Planner":
    st.title("Publishing Planner")
    content = read_table("content")
    if content.empty:
        st.info("No legacy content ideas available yet. Generated assets are reviewed in Content Studio.")
    else:
        selected = st.selectbox(
            "Select content", content["id"].tolist(),
            format_func=lambda x: content.loc[content["id"] == x, "title"].iloc[0]
        )
        new_status = st.selectbox("Update status", ["Idea", "Draft", "Under Review", "Approved", "Published"])
        if st.button("Update Status"):
            with connect_db() as conn:
                conn.execute("UPDATE content SET status=? WHERE id=?", (new_status, selected))
            st.success("Status updated.")
            st.rerun()
        st.dataframe(content, use_container_width=True, hide_index=True)

# ============================================================
# PERFORMANCE
# ============================================================

elif page == "Performance":
    st.title("Content Performance")
    content = read_table("content")
    if content.empty:
        st.info("No legacy content records available.")
    else:
        published = content[content["status"] == "Published"]
        if published.empty:
            st.info("No published content yet.")
        else:
            with st.form("performance_form"):
                selected = st.selectbox(
                    "Published content", published["id"].tolist(),
                    format_func=lambda x: published.loc[published["id"] == x, "title"].iloc[0]
                )
                views = st.number_input("Views", min_value=0, step=1)
                likes = st.number_input("Likes", min_value=0, step=1)
                comments = st.number_input("Comments", min_value=0, step=1)
                shares = st.number_input("Shares", min_value=0, step=1)
                submitted = st.form_submit_button("Save Performance")
                if submitted:
                    with connect_db() as conn:
                        conn.execute(
                            "INSERT INTO performance (content_id,views,likes,comments,shares) VALUES (?,?,?,?,?)",
                            (selected, views, likes, comments, shares)
                        )
                    st.success("Performance saved.")
            results = read_table("performance")
            if not results.empty:
                c1, c2 = st.columns(2)
                c1.metric("Total Views", int(results["views"].sum()))
                c2.metric("Total Engagement", int(results["likes"].sum() + results["comments"].sum() + results["shares"].sum()))
                st.dataframe(results, use_container_width=True, hide_index=True)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption("HPU | Human Processing Unit | Dr. Alaa Zahran | Content Intelligence Platform")
