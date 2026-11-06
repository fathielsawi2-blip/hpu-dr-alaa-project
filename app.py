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

def get_table(table_name):
    allowed_tables = {
        "experiences",
        "content",
        "performance",
        "interviews",
        "source_materials",
        "generated_assets",
        "cv_knowledge",
        "analysis_records"
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid database table")

    conn = get_db()

    try:
        df = pd.read_sql_query(
            f"SELECT * FROM {table_name}",
            conn
        )
    finally:
        conn.close()

    return df

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
    key = st.secrets.get("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", "")
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
# ============================================================
# SECTION 2 — HPU CONTENT INTELLIGENCE & GENERATION ENGINE
# Add below Section 1
# ============================================================

# ------------------------------------------------------------
# 9. OPTIONAL AI CONFIGURATION
# ------------------------------------------------------------

def get_openai_kst.secrets.get("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():
    """
    OpenAI is optional.
    HPU Core continues working if the key is missing.
    """

    try:
        key = ", "")
        if key:
            return key
    except Exception:
        pass

    return os.environ.get("OPENAI_API_KEY", "")


def openai_request(endpoint, payload, timeout=120):
    """
    Send a request to OpenAI.
    Returns the response as JSON.
    """

    api_key = get_openai_key()

    if not api_key:
        raise RuntimeError(
            "OpenAI API key is not configured. "
            "HPU Core is still available."
        )

    url = "https://api.openai.com/v1/" + endpoint

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenAI request failed ({error.code}): {details[:1000]}"
        )

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Could not connect to OpenAI: {error.reason}"
        )


def openai_binary_request(endpoint, payload, timeout=180):
    """
    Send an OpenAI request that returns binary data,
    such as generated audio.
    """

    api_key = get_openai_key()

    if not api_key:
        raise RuntimeError("OpenAI API key is missing.")

    url = "https://api.openai.com/v1/" + endpoint

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenAI binary request failed ({error.code}): "
            f"{details[:1000]}"
        )


# ------------------------------------------------------------
# 10. CONTENT STRATEGY ENGINE
# ------------------------------------------------------------

def select_content_angle(analysis, objective):
    """
    Select a content angle using HPU Core rules.
    """

    themes = analysis.get("themes", [])
    signals = analysis.get("signals", {})

    if (
        signals.get("Outputs")
        and not signals.get("Outcomes")
    ):
        return "Outputs versus outcomes"

    if (
        "KPIs and Impact Measurement" in themes
        or not signals.get("Baseline")
    ):
        return "Measurement and performance"

    if "Change Management" in themes:
        return "Communication during transformation"

    if "Reputation and Brand Strategy" in themes:
        return "Trust and reputation"

    if "Strategic Communication" in themes:
        return "Strategic communication practice"

    if objective == "Thought leadership":
        return "Executive perspective and professional insight"

    if objective == "Professional awareness":
        return "Professional education and awareness"

    return "Practical communication insight"


def generate_content_strategy(source, analysis, audience, objective):
    """
    Produce a content strategy independently of OpenAI.
    """

    angle = select_content_angle(analysis, objective)
    recommendations = recommend_strategy(analysis)

    strategy = {
        "central_idea": source,
        "content_angle": angle,
        "audience": audience,
        "objective": objective,
        "expertise": analysis.get("themes", []),
        "recommendations": recommendations,
        "suggested_formats": [
            "LinkedIn thought-leadership post",
            "Professional article",
            "Educational infographic",
            "Short video narration",
            "Audio commentary"
        ],
        "suggested_sequence": [
            "Introduce the central issue",
            "Explain why it matters",
            "Identify the professional challenge",
            "Present a strategic perspective",
            "Provide a practical recommendation"
        ]
    }

    return strategy


# ------------------------------------------------------------
# 11. LOCAL TEXT GENERATION — LINKEDIN POST
# ------------------------------------------------------------

def generate_local_post(
    source,
    audience,
    language,
    tone,
    objective,
    analysis
):
    """
    Generate a post using HPU Core templates.
    The original source remains the central idea.
    """

    angle = select_content_angle(analysis, objective)

    if language == "Arabic":

        post = f"""{source}

في الممارسة المهنية، لا يكفي أن ننفذ الأنشطة الاتصالية
أو نزيد من حجم المحتوى المنشور.

الأهم هو أن نفهم المشكلة التي نحاول معالجتها،
والهدف الذي نسعى إلى تحقيقه، والتغيير الذي نريد أن نراه.

من هنا تظهر أهمية التفكير الاتصالي الاستراتيجي:
أن نربط كل نشاط اتصالي بهدف واضح،
وأن نحدد نقطة البداية قبل تقييم الأداء،
وأن نختار مؤشرات تعكس النتائج لا مجرد حجم النشاط.

**التواصل الفعّال ليس مجرد نشاط يُنفذ،
بل عملية هادفة يمكن قياس أثرها.**

زاوية المعالجة: {angle}

الجمهور المستهدف: {audience}

الهدف: {objective}

#التواصل_الاستراتيجي
#الاتصال_المؤسسي
#قياس_الأثر
"""

    else:

        post = f"""{source}

In professional practice, communication success cannot
be determined simply by the volume of activities
or the amount of content published.

The more important questions are:

What problem are we addressing?
What objective are we pursuing?
What change do we want to achieve?

Strategic communication connects every activity
to a clear purpose, establishes a starting point
and selects indicators that reflect actual results.

**Effective communication is not simply an activity.
It is a purposeful process whose impact can be assessed.**

Content angle: {angle}

Target audience: {audience}

Objective: {objective}

#StrategicCommunication
#CorporateCommunication
#ImpactMeasurement
"""

    return post


# ------------------------------------------------------------
# 12. LOCAL TEXT GENERATION — PROFESSIONAL ARTICLE
# ------------------------------------------------------------

def generate_local_article(
    source,
    audience,
    language,
    objective,
    analysis
):

    angle = select_content_angle(analysis, objective)

    if language == "Arabic":

        article = f"""# {source}

## مقدمة

يمثل هذا المفهوم مدخلاً مهماً لفهم التحديات التي تواجه
ممارسات التواصل المؤسسي والاستراتيجي.

فكثيراً ما تنشغل المؤسسات بتنفيذ الأنشطة،
دون أن تربطها بصورة واضحة بالهدف المطلوب تحقيقه.

## أولاً: فهم المشكلة

تبدأ المشكلة عندما يصبح التركيز على المخرجات
أكبر من التركيز على القيمة التي يفترض أن تحققها.

عدد المنشورات أو حجم التغطية لا يوضح وحده
مدى نجاح التواصل في إحداث تغيير.

## ثانياً: أهمية الهدف

يحتاج كل نشاط اتصالي إلى هدف واضح يحدد
ما الذي تريد المؤسسة تحقيقه ولماذا.

## ثالثاً: خط الأساس والقياس

لا يمكن تقييم التغيير بصورة دقيقة دون معرفة
الوضع الذي بدأت منه المؤسسة.

ومن هنا تأتي أهمية خط الأساس ومؤشرات الأداء
المناسبة لطبيعة الهدف.

## رابعاً: من النشاط إلى الأثر

يجب أن تتجاوز عملية التقييم عدّ الأنشطة
إلى فهم النتائج والتغيرات التي تحققت.

## خاتمة

إن تطوير ممارسات التواصل يبدأ من الانتقال
من تنفيذ الأنشطة إلى إدارة عملية اتصالية
مرتبطة بهدف ومؤشرات ونتائج واضحة.

زاوية المعالجة: {angle}

الجمهور: {audience}

الهدف الاتصالي: {objective}
"""

    else:

        article = f"""# {source}

## Introduction

This concept provides an important starting point
for understanding the challenges facing strategic
and corporate communication practice.

Organizations can become focused on activities
without clearly connecting those activities
to the results they are expected to achieve.

## 1. Understanding the Problem

The challenge begins when outputs receive
more attention than the value they are meant to create.

The number of posts or the volume of media coverage
cannot independently demonstrate communication success.

## 2. The Importance of Objectives

Every communication activity should have a clear purpose.
An objective explains what the organization wants
to achieve and why.

## 3. Baselines and Measurement

Performance assessment requires an understanding
of the starting position.

Baselines and appropriate indicators help
organizations assess whether meaningful change occurred.

## 4. Moving from Activity to Impact

Evaluation should go beyond counting activities.
It should examine the outcomes and changes achieved.

## Conclusion

Better communication practice begins by connecting
activities with clear objectives, relevant indicators
and demonstrable outcomes.

Content angle: {angle}

Audience: {audience}

Objective: {objective}
"""

    return article


# ------------------------------------------------------------
# 13. LOCAL VISUAL CONTENT BRIEF
# ------------------------------------------------------------

def generate_visual_brief(
    source,
    audience,
    language,
    analysis
):

    angle = select_content_angle(
        analysis,
        "Professional awareness"
    )

    if language == "Arabic":

        return f"""التصور البصري المقترح

الفكرة الرئيسية:
{source}

العنوان المقترح:
من النشاط الاتصالي إلى الأثر القابل للقياس

المحور:
{angle}

الجمهور:
{audience}

مكونات التصميم:

1. المشكلة:
   أنشطة ومخرجات اتصالية دون هدف واضح.

2. التحدي:
   غياب خط الأساس وصعوبة تقييم الأداء.

3. الحل:
   تحديد الهدف، وتوثيق خط الأساس،
   واختيار مؤشرات الأداء.

4. النتيجة:
   تواصل أكثر وضوحاً وقابلية للتقييم.

التوجه البصري:
تصميم مؤسسي احترافي، مخطط تحليلي،
عناصر قياس ومؤشرات أداء،
وتسلسل بصري واضح من المشكلة إلى الحل.

ملاحظة:
هذا تصور تصميمي مولد بواسطة HPU Core،
وليس صورة فعلية.
"""

    return f"""VISUAL CONTENT BRIEF

Main idea:
{source}

Suggested headline:
From Communication Activity to Measurable Impact

Content angle:
{angle}

Target audience:
{audience}

Suggested layout:

1. Problem:
   Communication activities without clear objectives.

2. Challenge:
   Missing baselines and unclear performance evaluation.

3. Solution:
   Define objectives, establish baselines
   and select relevant KPIs.

4. Intended result:
   More purposeful and measurable communication.

Visual direction:
Professional corporate infographic,
analytical diagrams, KPI elements,
clear information hierarchy.

Note:
This is an HPU Core design brief,
not an actual generated image.
"""


# ------------------------------------------------------------
# 14. LOCAL AUDIO NARRATION SCRIPT
# ------------------------------------------------------------

def generate_audio_script(source, language, audience):

    if language == "Arabic":

        return f"""النص المقترح للتعليق الصوتي

{source}

في كثير من المؤسسات، يتم التركيز على الأنشطة
الاتصالية وما يتم إنتاجه ونشره.

لكن السؤال الأهم هو:
ما الهدف الذي نريد تحقيقه؟

وكيف يمكننا معرفة ما إذا كنا قد حققناه؟

التواصل الاستراتيجي يبدأ من فهم المشكلة،
وتحديد الهدف، ومعرفة نقطة البداية.

بعد ذلك نختار مؤشرات تساعدنا على قياس
النتائج والتغير الذي تحقق.

فالتواصل ليس مجرد نشر للمعلومات،
بل عملية استراتيجية تهدف إلى تحقيق أثر واضح.

الجمهور المستهدف: {audience}
"""

    return f"""SUGGESTED AUDIO NARRATION

{source}

Many organizations focus on communication activities
and the amount of content they produce and publish.

But the more important question is:

What are we trying to achieve?

And how will we know whether we achieved it?

Strategic communication begins by understanding
the problem, defining the objective
and identifying the starting point.

We then select indicators that help us measure
the results and the change achieved.

Communication is not simply the distribution
of information. It is a strategic process
designed to create meaningful impact.

Target audience: {audience}
"""


# ------------------------------------------------------------
# 15. OPTIONAL OPENAI TEXT ENHANCEMENT
# ------------------------------------------------------------

def enhance_text_with_openai(
    source,
    local_draft,
    audience,
    objective,
    language,
    content_type
):
    """
    OpenAI improves the HPU Core draft.
    It does not replace the independent analysis.
    """

    prompt = f"""
You are the optional writing enhancement layer
of HPU — Human Processing Unit.

HPU Core has already analyzed the source material.
Your job is to improve the writing, structure
and clarity of the supplied draft.

CONTENT TYPE:
{content_type}

LANGUAGE:
{language}

AUDIENCE:
{audience}

COMMUNICATION OBJECTIVE:
{objective}

ORIGINAL SOURCE:
{source}

HPU CORE DRAFT:
{local_draft}

RULES:
- Preserve the original central idea.
- Do not invent statistics, projects, roles or achievements.
- Do not fabricate personal experiences.
- Do not create unsupported CV claims.
- Maintain a professional executive tone.
- Improve clarity, structure and argument.
- Return only the finished content.
"""

    result = openai_request(
        "responses",
        {
            "model": AI_TEXT_MODEL,
            "input": prompt
        }
    )

    output = []

    for item in result.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                output.append(content.get("text", ""))

    if not output:
        raise RuntimeError(
            "The AI response did not contain usable text."
        )

    return "\n".join(output)


# ------------------------------------------------------------
# 16. OPTIONAL ACTUAL IMAGE GENERATION
# ------------------------------------------------------------

def generate_actual_image(
    source,
    visual_brief,
    language,
    size="1024x1024"
):
    """
    Generate an actual image using OpenAI.
    This feature requires an API key and available credits.
    """

    image_prompt = f"""
Create a professional corporate communication infographic.

Original source:
{source}

Design brief:
{visual_brief}

Language of visible text: {language}

Requirements:
- Professional executive visual identity.
- Clean and modern information hierarchy.
- Clear diagrams and visual structure.
- No invented statistics or numerical claims.
- Avoid unnecessary decorative elements.
- Make the main message easy to understand.
"""

    result = openai_request(
        "images/generations",
        {
            "model": AI_IMAGE_MODEL,
            "prompt": image_prompt,
            "size": size,
            "quality": "medium",
            "n": 1
        },
        timeout=240
    )

    image_data = result["data"][0].get("b64_json")

    if not image_data:
        raise RuntimeError(
            "The image service did not return image data."
        )

    return base64.b64decode(image_data)


# ------------------------------------------------------------
# 17. OPTIONAL ACTUAL AUDIO GENERATION
# ------------------------------------------------------------

def generate_actual_audio(
    narration,
    voice="alloy"
):
    """
    Generate actual speech audio using OpenAI.
    Returns MP3 bytes.
    """

    if len(narration) > 4000:
        raise ValueError(
            "The narration is too long for this single request. "
            "Shorten it or split it into sections."
        )

    audio_data = openai_binary_request(
        "audio/speech",
        {
            "model": AI_AUDIO_MODEL,
            "voice": voice,
            "input": narration,
            "response_format": "mp3"
        },
        timeout=240
    )

    if not audio_data:
        raise RuntimeError(
            "The audio service returned an empty file."
        )

    return audio_data


# ------------------------------------------------------------
# 18. CONTENT FORMAT ROUTER
# ------------------------------------------------------------

def generate_local_asset(
    asset_type,
    source,
    audience,
    language,
    tone,
    objective,
    analysis
):
    """
    One central function routes requests to
    the independent HPU content generators.
    """

    if asset_type == "LinkedIn Post":
        return generate_local_post(
            source,
            audience,
            language,
            tone,
            objective,
            analysis
        )

    elif asset_type == "Professional Article":
        return generate_local_article(
            source,
            audience,
            language,
            objective,
            analysis
        )

    elif asset_type == "Visual Brief":
        return generate_visual_brief(
            source,
            audience,
            language,
            analysis
        )

    elif asset_type == "Audio Script":
        return generate_audio_script(
            source,
            language,
            audience
        )

    elif asset_type == "Content Strategy":
        strategy = generate_content_strategy(
            source,
            analysis,
            audience,
            objective
        )

        return json.dumps(
            strategy,
            ensure_ascii=False,
            indent=4
        )

    else:
        raise ValueError(
            f"Unsupported content type: {asset_type}"
        )


# ------------------------------------------------------------
# END OF SECTION 2
# ------------------------------------------------------------
# ============================================================
# SECTION 3 OF 4
# HPU APPLICATION PAGES
# Independent local analysis, content studio and data interface
# ============================================================

# ------------------------------------------------------------
# 1. GENERAL INTERFACE HELPERS
# ------------------------------------------------------------

def hpu_section_header(title, description=""):
    st.markdown(f"## {title}")
    if description:
        st.caption(description)


def hpu_read_table(table_name):
    """Read a permitted HPU table safely."""
    try:
        return get_table(table_name)
    except Exception as error:
        st.warning(f"Could not load {table_name}: {error}")
        return pd.DataFrame()


def hpu_save_source_record(title, source_text, source_type,
                           audience, platform, objective, language):
    """Save original material without changing its wording."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO source_materials
        (title, source_text, source_type, audience,
         platform, objective, language, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        source_text,
        source_type,
        audience,
        platform,
        objective,
        language,
        datetime.now().isoformat(timespec="seconds")
    ))

    source_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return source_id


def hpu_save_analysis_record(source_id, analysis):
    """Save the local HPU Core analysis."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analysis_records
        (source_id, analysis_json, engine, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        source_id,
        json.dumps(analysis, ensure_ascii=False),
        "HPU Core - Independent Analysis",
        datetime.now().isoformat(timespec="seconds")
    ))

    conn.commit()
    conn.close()


def hpu_save_generated_asset(source_id, asset_type, title, text_content):
    """Save a generated text asset."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO generated_assets
        (source_id, asset_type, title, asset_text,
         engine, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        source_id,
        asset_type,
        title,
        text_content,
        "HPU Core",
        datetime.now().isoformat(timespec="seconds")
    ))

    conn.commit()
    conn.close()


# ------------------------------------------------------------
# 2. INDEPENDENT HPU CORE ANALYSIS
# ------------------------------------------------------------

def hpu_core_diagnosis(source_text, audience, platform, objective):
    """
    A local analytical process.
    Does not require OpenAI, internet access or an API key.
    """

    text = source_text.strip()
    lower_text = text.lower()

    if not text:
        return {
            "status": "No source material",
            "main_theme": "Not available",
            "strategic_observation": "Add source material before analysis.",
            "objective_check": "Not assessed",
            "measurement_check": "Not assessed",
            "recommendations": []
        }

    expertise_map = {
        "Strategic Communication": [
            "strategic communication", "strategy", "communication",
            "الاتصال الاستراتيجي", "التواصل الاستراتيجي", "الاتصال"
        ],
        "Leadership and Management": [
            "leadership", "management", "team", "governance",
            "القيادة", "الإدارة", "الفريق", "الحوكمة"
        ],
        "Change Management": [
            "change", "transformation", "readiness",
            "التغيير", "التحول", "الجاهزية"
        ],
        "Marketing and Branding": [
            "marketing", "brand", "reputation", "campaign",
            "التسويق", "العلامة التجارية", "السمعة", "الحملة"
        ],
        "Performance and Measurement": [
            "measurement", "baseline", "performance", "kpi",
            "measurement", "القياس", "خط الأساس", "الأداء", "المؤشرات"
        ],
        "Stakeholder Engagement": [
            "stakeholder", "engagement", "audience",
            "أصحاب المصلحة", "التفاعل", "الجمهور"
        ]
    }

    detected_expertise = []

    for category, keywords in expertise_map.items():
        if any(keyword in lower_text for keyword in keywords):
            detected_expertise.append(category)

    if not detected_expertise:
        detected_expertise = ["General Professional Insight"]

    # Identify measurement concepts
    measurement_terms = [
        "baseline", "kpi", "metric", "measurement",
        "خط الأساس", "مؤشر", "قياس", "مؤشرات الأداء"
    ]

    has_measurement = any(
        term in lower_text for term in measurement_terms
    )

    # Identify objective concepts
    objective_terms = [
        "objective", "goal", "purpose", "هدف",
        "أهداف", "غاية", "الغرض"
    ]

    has_objective = any(
        term in lower_text for term in objective_terms
    )

    # Detect evidence indicators
    evidence_terms = [
        "percent", "%", "million", "thousand",
        "sar", "budget", "increase", "decrease",
        "نسبة", "مليون", "ألف", "ميزانية"
    ]

    has_evidence = any(
        term in lower_text for term in evidence_terms
    )

    recommendations = []

    if not has_objective:
        recommendations.append(
            "Clarify the intended communication objective."
        )

    if not has_measurement:
        recommendations.append(
            "Identify a measurable baseline and suitable KPIs."
        )

    if not has_evidence:
        recommendations.append(
            "Consider adding verified examples, evidence or experience."
        )

    if not recommendations:
        recommendations.append(
            "Review whether the evidence and indicators demonstrate "
            "the intended outcome."
        )

    strategic_observation = (
        "The source contains professional material that can be "
        "developed into a strategic communication insight. "
        "The next step is to connect its central idea to a specific "
        "audience need and a measurable outcome."
    )

    if has_objective and not has_measurement:
        strategic_observation = (
            "An objective appears in the source, but the measurement "
            "dimension needs further development. An objective without "
            "a baseline makes it difficult to evaluate performance."
        )

    if has_measurement and not has_objective:
        strategic_observation = (
            "The source includes measurement-related concepts. "
            "However, indicators should be connected to a clearly "
            "defined objective so that measurement reflects impact."
        )

    if has_objective and has_measurement:
        strategic_observation = (
            "The source connects objective-setting and measurement "
            "concepts. The next step is to check whether the selected "
            "indicators genuinely demonstrate the intended outcome."
        )

    return {
        "status": "Analysis completed",
        "main_theme": ", ".join(detected_expertise),
        "strategic_observation": strategic_observation,
        "objective_check": (
            "Objective-related language detected"
            if has_objective else
            "Objective needs clarification"
        ),
        "measurement_check": (
            "Measurement-related language detected"
            if has_measurement else
            "Baseline and KPIs need clarification"
        ),
        "evidence_check": (
            "Possible evidence indicators detected"
            if has_evidence else
            "No clear numerical or evidence indicators detected"
        ),
        "audience": audience,
        "platform": platform,
        "intended_objective": objective,
        "recommendations": recommendations,
        "source_length": len(text),
        "analysis_engine": "HPU Core - Local Rules Engine"
    }


# ------------------------------------------------------------
# 3. LOCAL CONTENT DEVELOPMENT
# ------------------------------------------------------------

def hpu_local_post(source_text, audience, tone="Professional"):
    """
    Create a structured draft from the original source.
    The original idea remains the foundation.
    """

    source_text = source_text.strip()

    return f"""[Opening insight]

{source_text}

[Strategic perspective]

This idea highlights an important consideration for
{audience.lower()}: professional communication should be
connected to a clear purpose, an identified audience and
a meaningful outcome.

The value of communication is not determined only by
the volume of activities or the visibility of published
content. It also depends on whether the intended message
supports a defined organizational objective.

[Closing reflection]

The question is not simply how much communication
an organization produces, but what that communication
is designed to achieve.

#StrategicCommunication #Leadership #PerformanceMeasurement
"""


def hpu_local_article(source_text, audience):
    return f"""# From Professional Insight to Strategic Impact

## The original idea

{source_text}

## Why this matters

For {audience.lower()}, this idea raises an important
question about the relationship between communication
activities and organizational priorities.

Communication should not be treated as an isolated
publishing activity. It needs to be connected to a
defined purpose, a relevant audience and an intended
result.

## From activity to outcome

Organizations can produce large volumes of content
without necessarily understanding the impact of that
content.

A stronger approach begins by defining the objective,
identifying the starting point and selecting indicators
that help assess progress.

## Questions for professional practice

- What is the intended outcome?
- Who needs to receive or act on the message?
- What is the starting point?
- Which indicators can demonstrate progress?
- How will the organization learn from the results?

## Conclusion

Strategic communication becomes more valuable when
planning, execution and measurement work together.
"""


def hpu_local_visual_brief(source_text, audience):
    return f"""VISUAL CONTENT BRIEF

Core source:
{source_text}

Target audience:
{audience}

Suggested visual concept:
A professional strategic communication framework.

Suggested layout:
1. Central message.
2. Communication objective.
3. Target audience.
4. Baseline and indicators.
5. Intended outcome.

Visual direction:
Clean executive design, clear information hierarchy,
professional typography and restrained corporate colours.

Important:
The visual must communicate the original idea without
introducing unsupported statistics or claims.
"""


def hpu_local_audio_script(source_text, audience):
    return f"""AUDIO / PODCAST SCRIPT

Opening:
Welcome. Today, we are exploring an important
professional idea.

Main idea:
{source_text}

Discussion:
For professionals working with {audience.lower()},
this idea encourages us to look beyond routine activities
and consider the purpose and results of our work.

Reflection:
Are we measuring what we do, or are we measuring
what our work actually achieves?

Closing:
Thank you for listening. Strategic thinking begins
with asking the right questions.
"""


# ------------------------------------------------------------
# 4. DASHBOARD
# ------------------------------------------------------------

def hpu_render_dashboard():

    hpu_section_header(
        "HPU Executive Dashboard",
        "A central view of the Human Processing Unit knowledge "
        "and content development environment."
    )

    experiences = hpu_read_table("experiences")
    content = hpu_read_table("content")
    sources = hpu_read_table("source_materials")
    assets = hpu_read_table("generated_assets")
    interviews = hpu_read_table("interviews")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Professional Experiences", len(experiences))

    with c2:
        st.metric("Original Sources", len(sources))

    with c3:
        st.metric("Generated Assets", len(assets))

    c4, c5, c6 = st.columns(3)

    with c4:
        st.metric("Content Records", len(content))

    with c5:
        st.metric("Interview Records", len(interviews))

    with c6:
        analysis = hpu_read_table("analysis_records")
        st.metric("Analysis Records", len(analysis))

    st.divider()

    st.markdown("### HPU Processing Model")

    st.markdown("""
    **01 — Input**

    Professional experiences, CV information, interviews,
    original posts and other source materials.

    **02 — Interpretation**

    Independent HPU Core analysis, expertise classification,
    strategic diagnosis and evidence assessment.

    **03 — Development**

    Content strategies, posts, articles, visual briefs
    and audio scripts.

    **04 — Evaluation**

    Publishing records, performance indicators,
    feedback and continuous improvement.
    """)

    st.info(
        "HPU Core analysis operates independently. "
        "External AI services are optional enhancements."
    )


# ------------------------------------------------------------
# 5. CONTENT STUDIO
# ------------------------------------------------------------

def hpu_render_content_studio():

    hpu_section_header(
        "Content Intelligence Studio",
        "Convert original professional knowledge into structured "
        "content while preserving its central meaning."
    )

    with st.form("hpu_content_form"):

        title = st.text_input(
            "Source title",
            placeholder="Enter a title for the original material"
        )

        source_text = st.text_area(
            "Original source material",
            height=180,
            placeholder="Paste the original post, experience, "
                        "interview answer or professional idea here."
        )

        col1, col2 = st.columns(2)

        with col1:
            source_type = st.selectbox(
                "Source type",
                [
                    "Professional Insight",
                    "Social Media Post",
                    "Professional Experience",
                    "Interview",
                    "CV Information",
                    "Article",
                    "Other"
                ]
            )

            audience = st.selectbox(
                "Target audience",
                [
                    "Senior Executives",
                    "Communication Professionals",
                    "Government Leaders",
                    "Business Leaders",
                    "Consultants",
                    "Academic Audience",
                    "General Professional Audience"
                ]
            )

        with col2:
            platform = st.selectbox(
                "Platform",
                [
                    "LinkedIn",
                    "Website",
                    "Podcast",
                    "Instagram",
                    "X",
                    "Multiple Platforms"
                ]
            )

            language = st.selectbox(
                "Language",
                ["English", "Arabic", "Bilingual"]
            )

        objective = st.selectbox(
            "Communication objective",
            [
                "Build Professional Authority",
                "Share Professional Knowledge",
                "Demonstrate Experience",
                "Educate the Audience",
                "Strengthen Personal Brand",
                "Encourage Discussion",
                "Other"
            ]
        )

        submitted = st.form_submit_button(
            "Analyse Source with HPU Core",
            use_container_width=True
        )

    if submitted:

        if not source_text.strip():
            st.error("Please enter the original source material.")

        else:
            source_id = hpu_save_source_record(
                title or "Untitled Source",
                source_text,
                source_type,
                audience,
                platform,
                objective,
                language
            )

            analysis = hpu_core_diagnosis(
                source_text,
                audience,
                platform,
                objective
            )

            hpu_save_analysis_record(source_id, analysis)

            st.session_state["hpu_current_source_id"] = source_id
            st.session_state["hpu_current_source_text"] = source_text
            st.session_state["hpu_current_audience"] = audience
            st.session_state["hpu_current_analysis"] = analysis

            st.success(
                f"Source saved and analysed. Reference: {source_id}"
            )

    if "hpu_current_analysis" in st.session_state:

        analysis = st.session_state["hpu_current_analysis"]

        st.divider()
        st.markdown("### HPU Core Analysis")

        st.write("**Main theme:**", analysis["main_theme"])

        st.write(
            "**Strategic observation:**",
            analysis["strategic_observation"]
        )

        st.write(
            "**Objective assessment:**",
            analysis["objective_check"]
        )

        st.write(
            "**Measurement assessment:**",
            analysis["measurement_check"]
        )

        st.write(
            "**Evidence assessment:**",
            analysis["evidence_check"]
        )

        st.markdown("#### HPU Recommendations")

        for recommendation in analysis["recommendations"]:
            st.write("•", recommendation)

        st.divider()
        st.markdown("### Develop Content")

        content_type = st.selectbox(
            "Choose the content format",
            [
                "LinkedIn Post",
                "Professional Article",
                "Visual Content Brief",
                "Podcast / Audio Script"
            ],
            key="hpu_content_type"
        )

        if st.button("Generate with HPU Core", use_container_width=True):

            original = st.session_state["hpu_current_source_text"]
            target = st.session_state["hpu_current_audience"]
            source_id = st.session_state["hpu_current_source_id"]

            if content_type == "LinkedIn Post":
                generated = hpu_local_post(original, target)
                asset_type = "Post"

            elif content_type == "Professional Article":
                generated = hpu_local_article(original, target)
                asset_type = "Article"

            elif content_type == "Visual Content Brief":
                generated = hpu_local_visual_brief(original, target)
                asset_type = "Visual Brief"

            else:
                generated = hpu_local_audio_script(original, target)
                asset_type = "Audio Script"

            st.session_state["hpu_generated_text"] = generated
            st.session_state["hpu_generated_type"] = asset_type
            st.session_state["hpu_generated_source_id"] = source_id

        if "hpu_generated_text" in st.session_state:

            st.markdown("#### Generated Draft")

            edited_text = st.text_area(
                "Review and edit the draft",
                value=st.session_state["hpu_generated_text"],
                height=300,
                key="hpu_edited_generated_text"
            )

            if st.button("Save Generated Asset", use_container_width=True):

                hpu_save_generated_asset(
                    st.session_state["hpu_generated_source_id"],
                    st.session_state["hpu_generated_type"],
                    st.session_state["hpu_generated_type"] + " Draft",
                    edited_text
                )

                st.success("Generated asset saved to the HPU database.")

            st.download_button(
                "Download Draft",
                data=edited_text,
                file_name="hpu_content_draft.txt",
                mime="text/plain",
                use_container_width=True
            )


# ------------------------------------------------------------
# 6. SOURCE LIBRARY
# ------------------------------------------------------------

def hpu_render_source_library():

    hpu_section_header(
        "Source Knowledge Library",
        "Review original materials and generated knowledge assets."
    )

    sources = hpu_read_table("source_materials")

    if sources.empty:
        st.info("No source materials have been saved yet.")
    else:
        st.dataframe(
            sources,
            use_container_width=True,
            hide_index=True
        )

        if "id" in sources.columns:

            selected_id = st.selectbox(
                "Select a source reference",
                sources["id"].tolist(),
                key="hpu_source_library_id"
            )

            selected = sources[
                sources["id"] == selected_id
            ]

            if not selected.empty:
                st.markdown("### Original Source")
                st.write(selected.iloc[0]["source_text"])

    st.divider()
    st.markdown("### Generated Assets")

    assets = hpu_read_table("generated_assets")

    if assets.empty:
        st.info("No generated assets have been saved yet.")
    else:
        st.dataframe(
            assets.drop(columns=["file_data"], errors="ignore"),
            use_container_width=True,
            hide_index=True
        )


# ------------------------------------------------------------
# 7. PROFESSIONAL EXPERIENCES
# ------------------------------------------------------------

def hpu_render_experiences():

    hpu_section_header(
        "Professional Experience Database",
        "Build a structured knowledge base from professional "
        "experiences and achievements."
    )

    with st.form("hpu_experience_form"):

        experience_title = st.text_input("Experience title")

        description = st.text_area(
            "Experience description",
            height=150
        )

        expertise = st.text_input(
            "Expertise category",
            placeholder="Example: Strategic Communication"
        )

        submitted = st.form_submit_button(
            "Save Experience",
            use_container_width=True
        )

    if submitted:

        if not experience_title.strip() or not description.strip():
            st.error("Enter both an experience title and description.")

        else:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO experiences
                (title, description, expertise, date_added)
                VALUES (?, ?, ?, ?)
            """, (
                experience_title,
                description,
                expertise,
                datetime.now().isoformat(timespec="seconds")
            ))

            conn.commit()
            conn.close()

            st.success("Professional experience saved.")

    st.divider()
    st.markdown("### Existing Experiences")

    experiences = hpu_read_table("experiences")

    if experiences.empty:
        st.info("No professional experiences have been entered.")
    else:
        st.dataframe(
            experiences,
            use_container_width=True,
            hide_index=True
        )


# ------------------------------------------------------------
# 8. INTERVIEW RECORDS
# ------------------------------------------------------------

def hpu_render_interviews():

    hpu_section_header(
        "Professional Interview Capture",
        "Record first-hand knowledge and insights from interviews."
    )

    with st.form("hpu_interview_form"):

        topic = st.text_input("Interview topic")

        question = st.text_area(
            "Interview question",
            height=90
        )

        answer = st.text_area(
            "Interview answer",
            height=180
        )

        insight = st.text_area(
            "Key insight or observation",
            height=120
        )

        submitted = st.form_submit_button(
            "Save Interview Record",
            use_container_width=True
        )

    if submitted:

        if not question.strip() or not answer.strip():
            st.error("A question and answer are required.")

        else:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO interviews
                (topic, question, answer, insight, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                topic,
                question,
                answer,
                insight,
                datetime.now().isoformat(timespec="seconds")
            ))

            conn.commit()
            conn.close()

            st.success("Interview record saved.")

    st.divider()
    st.markdown("### Interview History")

    interviews = hpu_read_table("interviews")

    if interviews.empty:
        st.info("No interview records have been saved.")
    else:
        st.dataframe(
            interviews,
            use_container_width=True,
            hide_index=True
        )


# ------------------------------------------------------------
# 9. PERFORMANCE ANALYTICS
# ------------------------------------------------------------

def hpu_render_analytics():

    hpu_section_header(
        "Content Performance Analytics",
        "Record and review the performance of published content."
    )

    content = hpu_read_table("content")
    performance = hpu_read_table("performance")

    if content.empty:
        st.info(
            "There are no content records yet. "
            "Add content records before recording performance."
        )
        return

    st.markdown("### Content Records")

    st.dataframe(
        content,
        use_container_width=True,
        hide_index=True
    )

    if "id" not in content.columns:
        st.warning("Content records do not contain an ID field.")
        return

    st.divider()
    st.markdown("### Record Performance")

    with st.form("hpu_performance_form"):

        content_id = st.selectbox(
            "Select content",
            content["id"].tolist()
        )

        col1, col2 = st.columns(2)

        with col1:
            views = st.number_input(
                "Views",
                min_value=0,
                step=1
            )

            likes = st.number_input(
                "Likes",
                min_value=0,
                step=1
            )

        with col2:
            comments = st.number_input(
                "Comments",
                min_value=0,
                step=1
            )

            shares = st.number_input(
                "Shares",
                min_value=0,
                step=1
            )

        submitted = st.form_submit_button(
            "Save Performance Data",
            use_container_width=True
        )

    if submitted:

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO performance
            (content_id, views, likes, comments, shares)
            VALUES (?, ?, ?, ?, ?)
        """, (
            content_id,
            int(views),
            int(likes),
            int(comments),
            int(shares)
        ))

        conn.commit()
        conn.close()

        st.success("Performance data saved.")

        performance = hpu_read_table("performance")

    if not performance.empty:

        st.divider()
        st.markdown("### Recorded Performance")

        st.dataframe(
            performance,
            use_container_width=True,
            hide_index=True
        )

        total_views = int(performance["views"].fillna(0).sum())
        total_likes = int(performance["likes"].fillna(0).sum())
        total_comments = int(performance["comments"].fillna(0).sum())
        total_shares = int(performance["shares"].fillna(0).sum())

        a, b, c, d = st.columns(4)

        a.metric("Total Views", f"{total_views:,}")
        b.metric("Total Likes", f"{total_likes:,}")
        c.metric("Comments", f"{total_comments:,}")
        d.metric("Shares", f"{total_shares:,}")


# ------------------------------------------------------------
# 10. HPU METHODOLOGY
# ------------------------------------------------------------

def hpu_render_methodology():

    hpu_section_header(
        "HPU Methodology and Architecture",
        "How HPU transforms professional knowledge into "
        "structured strategic content."
    )

    st.markdown("""
    ### 1. Knowledge Input

    HPU accepts professional experiences, CV information,
    interview answers, original posts, articles and other
    knowledge sources.

    ### 2. Independent HPU Core

    The local engine performs its own processing:

    - Keyword and expertise classification.
    - Identification of strategic themes.
    - Objective assessment.
    - Baseline and measurement checks.
    - Evidence and information-gap identification.
    - Recommendations based on predefined analytical rules.

    ### 3. Content Development

    HPU transforms source material into different formats:

    - LinkedIn posts.
    - Professional articles.
    - Visual content briefs.
    - Podcast and audio scripts.
    - Publishing concepts and strategies.

    ### 4. Optional AI Enhancement

    OpenAI can enhance selected tasks when configured.
    It is not required for the independent HPU Core
    analysis and local content-generation functions.

    ### 5. Learning and Measurement

    Content performance and human feedback can be recorded
    to support future strategic decisions.
    """)

    st.warning(
        "The current local engine uses transparent rules and "
        "templates. It is an initial analytical foundation, "
        "not a claim that the system already has human-level "
        "judgement or autonomous learning."
    )
    
# ============================================================
# SECTION 4 OF 4
# HPU FINAL INTEGRATION AND APPLICATION LAUNCH
# ============================================================


# ------------------------------------------------------------
# 1. CV KNOWLEDGE BASE
# ------------------------------------------------------------

def hpu_render_cv_knowledge():

    hpu_section_header(
        "CV Knowledge Base",
        "Organise professional information and distinguish verified "
        "facts from information requiring confirmation."
    )

    st.markdown("""
    The CV Knowledge Base is intended to preserve professional
    information as a structured source for future analysis and
    content development.

    **Verification principle**

    - Verified: checked against the original CV or supporting evidence.
    - Needs verification: entered but not yet checked.
    - Hypothesis: an interpretation that must not be presented as fact.
    - Missing information: requires an interview or additional evidence.
    """)

    st.warning(
        "Do not publish achievements, budgets, percentages, team sizes "
        "or project results until they have been checked against the "
        "original CV or supporting documentation."
    )

    # Display the initial CV reference material, if defined in Section 1.
    if "CV_FACTS" in globals():
        st.markdown("### Initial CV Reference Material")
        st.caption(
            "Treat these reference notes as requiring verification "
            "against the original CV."
        )
        st.write(CV_FACTS)
    else:
        st.info(
            "No initial CV reference material was found. "
            "You can add professional information below."
        )

    st.divider()
    st.markdown("### Add a CV Knowledge Record")

    with st.form("hpu_cv_knowledge_form"):

        title = st.text_input(
            "Professional fact or achievement",
            placeholder="Example: Led a strategic communication programme"
        )

        description = st.text_area(
            "Details and supporting context",
            height=130
        )

        expertise = st.selectbox(
            "Knowledge category",
            [
                "Strategic Communication",
                "Corporate Communication",
                "Integrated Marketing",
                "Leadership and Management",
                "Change Management",
                "Campaign Management",
                "Reputation and Branding",
                "Stakeholder Engagement",
                "Project and Programme Management",
                "Performance Measurement",
                "Events and Experiences",
                "Other"
            ]
        )

        verification = st.selectbox(
            "Verification status",
            [
                "Needs verification",
                "Verified against original CV",
                "Supported by additional evidence",
                "Hypothesis - not a confirmed fact"
            ]
        )

        submitted = st.form_submit_button(
            "Save CV Knowledge",
            use_container_width=True
        )

    if submitted:

        if not title.strip() or not description.strip():
            st.error("Please enter the title and details.")
        else:

            # Store the record with its verification status
            # in the description to avoid changing the existing schema.
            stored_description = (
                f"Verification status: {verification}\n\n"
                f"{description}"
            )

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO experiences
                (title, description, expertise, date_added)
                VALUES (?, ?, ?, ?)
            """, (
                title,
                stored_description,
                expertise,
                datetime.now().isoformat(timespec="seconds")
            ))

            conn.commit()
            conn.close()

            st.success("CV knowledge record saved.")

    st.divider()
    st.markdown("### Stored Professional Knowledge")

    experiences = hpu_read_table("experiences")

    if experiences.empty:
        st.info("No professional knowledge records have been saved.")
    else:
        st.dataframe(
            experiences,
            use_container_width=True,
            hide_index=True
        )


# ------------------------------------------------------------
# 2. PUBLISHING PLANNER
# ------------------------------------------------------------

def hpu_render_publishing_planner():

    hpu_section_header(
        "Publishing Planner",
        "Organise content ideas and planned publication dates."
    )

    with st.form("hpu_publishing_form"):

        title = st.text_input("Content title")

        audience = st.selectbox(
            "Target audience",
            [
                "Senior Executives",
                "Communication Professionals",
                "Government Leaders",
                "Business Leaders",
                "Consultants",
                "Academic Audience",
                "General Professional Audience"
            ]
        )

        platform = st.selectbox(
            "Publishing platform",
            [
                "LinkedIn",
                "Website",
                "Instagram",
                "X",
                "Podcast",
                "Multiple Platforms"
            ]
        )

        content_type = st.selectbox(
            "Content format",
            [
                "Post",
                "Article",
                "Video",
                "Visual",
                "Podcast",
                "Other"
            ]
        )

        objective = st.selectbox(
            "Content objective",
            [
                "Build Professional Authority",
                "Share Professional Knowledge",
                "Demonstrate Experience",
                "Educate the Audience",
                "Strengthen Personal Brand",
                "Encourage Discussion"
            ]
        )

        status = st.selectbox(
            "Publication status",
            [
                "Idea",
                "Draft",
                "Under Review",
                "Approved",
                "Scheduled",
                "Published"
            ]
        )

        publish_date = st.date_input(
            "Planned publication date",
            value=date.today()
        )

        submitted = st.form_submit_button(
            "Add to Publishing Planner",
            use_container_width=True
        )

    if submitted:

        if not title.strip():
            st.error("Please enter a content title.")
        else:

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO content
                (title, audience, platform, content_type,
                 status, objective, publish_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                title,
                audience,
                platform,
                content_type,
                status,
                objective,
                publish_date.isoformat()
            ))

            conn.commit()
            conn.close()

            st.success("Content added to the publishing planner.")

    st.divider()
    st.markdown("### Publishing Schedule")

    content = hpu_read_table("content")

    if content.empty:
        st.info("No content has been scheduled yet.")
    else:

        if "publish_date" in content.columns:
            content = content.sort_values(
                by="publish_date",
                ascending=True,
                na_position="last"
            )

        st.dataframe(
            content,
            use_container_width=True,
            hide_index=True
        )

        if "status" in content.columns:

            st.markdown("### Content Status Overview")

            status_counts = (
                content["status"]
                .fillna("Not specified")
                .value_counts()
            )

            st.bar_chart(status_counts)


# ------------------------------------------------------------
# 3. HPU SYSTEM STATUS
# ------------------------------------------------------------

def hpu_render_system_status():

    hpu_section_header(
        "System Status",
        "Review the independent HPU Core and optional external services."
    )

    st.markdown("### HPU Core")

    st.success("Local analytical engine: available")

    st.write(
        "The local analysis and template-based content functions "
        "do not require an OpenAI API key."
    )

    st.markdown("### Optional OpenAI Connection")

    api_key_available = False

    try:
        api_key_available = bool(
            st.secrets.get("OPENAI_API_KEY", "")
        )
    except Exception:
        api_key_available = False

    if api_key_available:
        st.success("An OpenAI API key is configured in Streamlit Secrets.")
    else:
        st.info(
            "No OpenAI API key is configured. HPU Core can still "
            "perform its local analysis and content-generation tasks."
        )

    st.markdown("### Database")

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)

        tables = cursor.fetchall()
        conn.close()

        table_names = [
            row[0] if not isinstance(row, dict) else row["name"]
            for row in tables
        ]

        st.success("Database connection successful.")

        st.write("Available database tables:")
        st.write(", ".join(table_names))

    except Exception as error:
        st.error(f"Database check failed: {error}")

    st.divider()

    st.markdown("### Important Deployment Note")

    st.warning(
        "Streamlit Cloud's local filesystem may not provide permanent "
        "SQLite storage across app restarts or redeployments. "
        "For a production HPU system, use a persistent external "
        "database and implement regular backups."
    )


# ------------------------------------------------------------
# 4. MAIN NAVIGATION
# ------------------------------------------------------------

def main():

    st.sidebar.title("HPU")
    st.sidebar.caption("HUMAN PROCESSING UNIT")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "APPLICATION MODULES",
        [
            "Executive Dashboard",
            "Content Intelligence Studio",
            "Professional Experiences",
            "CV Knowledge Base",
            "Interview Capture",
            "Source Knowledge Library",
            "Publishing Planner",
            "Performance Analytics",
            "HPU Methodology",
            "System Status"
        ]
    )

    st.sidebar.divider()

    st.sidebar.markdown("### HPU Architecture")

    st.sidebar.caption(
        "Independent Core Intelligence"
    )

    st.sidebar.caption(
        "Optional AI Enhancement"
    )

    st.sidebar.caption(
        "Professional Knowledge Database"
    )

    st.sidebar.caption(
        "Content Development and Measurement"
    )

    st.sidebar.divider()

    st.sidebar.caption(
        "HPU | Dr. Alaa Zahran Pilot"
    )

    # Route the selected page
    if page == "Executive Dashboard":
        hpu_render_dashboard()

    elif page == "Content Intelligence Studio":
        hpu_render_content_studio()

    elif page == "Professional Experiences":
        hpu_render_experiences()

    elif page == "CV Knowledge Base":
        hpu_render_cv_knowledge()

    elif page == "Interview Capture":
        hpu_render_interviews()

    elif page == "Source Knowledge Library":
        hpu_render_source_library()

    elif page == "Publishing Planner":
        hpu_render_publishing_planner()

    elif page == "Performance Analytics":
        hpu_render_analytics()

    elif page == "HPU Methodology":
        hpu_render_methodology()

    elif page == "System Status":
        hpu_render_system_status()


# ------------------------------------------------------------
# 5. APPLICATION ENTRY POINT
# ------------------------------------------------------------

if __name__ == "__main__":
    main()


# ============================================================
# END OF HPU APPLICATION
# ============================================================



# ============================================================
# END OF SECTION 3
# SECTION 4 WILL CONNECT THE NAVIGATION AND START THE APP
# ============================================================
