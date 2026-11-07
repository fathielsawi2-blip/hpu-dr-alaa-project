import os
import re
import json
import sqlite3
import base64
import streamlit as st
import pandas as pd

from datetime import date, datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


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


# ============================================================
# 1. VERIFIED CV REFERENCE KNOWLEDGE
# ============================================================

CV_KNOWLEDGE = [
    {
        "category": "Executive Profile",
        "title": "Professional profile",
        "details": (
            "Strategic and corporate communications executive with 19+ years "
            "of experience across Saudi government, Vision 2030 transformation, "
            "consulting and events. Specialisms include strategic communications, "
            "integrated marketing communications, reputation and brand management, "
            "and leadership of communication projects, programmes and campaigns."
        )
    },
    {
        "category": "Career Achievement",
        "title": "Ministry of Municipalities and Housing",
        "details": (
            "Led a team of 45+ and managed municipal transformation campaigns "
            "with budgets exceeding SAR 250M; contributed to municipal "
            "transformation awareness reaching 45%. Career period: April 2016 "
            "to October 2019."
        )
    },
    {
        "category": "Career Achievement",
        "title": "Ministry of Health - Vision Realization Office",
        "details": (
            "Led teams exceeding 35 professionals and managed communication "
            "projects and campaigns with budgets exceeding SAR 65M. Career "
            "period: October 2019 to February 2021."
        )
    },
    {
        "category": "Career Achievement",
        "title": "Health Sector Transformation Program",
        "details": (
            "Led or coordinated 25+ professionals and managed communication "
            "projects and campaigns with budgets exceeding SAR 42M. A major "
            "national campaign generated 500M+ media impressions through "
            "participation of 30+ government entities and received CEDA "
            "recognition. Contributed to increasing awareness from 16% to 78%. "
            "Career period: February 2021 to May 2024."
        )
    },
    {
        "category": "Career Achievement",
        "title": "Nahj Arabia for Media Consulting Company",
        "details": (
            "General Manager / Partner from June 2024 to November 2025. "
            "Managed 60+ professionals across company and client-project teams."
        )
    },
    {
        "category": "Current Role",
        "title": "SUMMIT Events & Exhibitions",
        "details": (
            "Operations Director from November 2025 to present. Leads a "
            "25-person multidisciplinary team and directs end-to-end delivery "
            "of client projects and communication experiences."
        )
    },
    {
        "category": "Specialized Methodology",
        "title": "Change management",
        "details": (
            "Designed a Prosci-aligned change management methodology at "
            "Saudi national health-sector level and conducted change-readiness "
            "assessments."
        )
    },
    {
        "category": "Specialized Project",
        "title": "Health Volunteering platform",
        "details": (
            "Launched and managed the Health Volunteering platform, established "
            "its media centre and supervised promotional communication, "
            "reaching 600K+ registrations."
        )
    },
    {
        "category": "Core Expertise",
        "title": "Professional expertise",
        "details": (
            "Strategic and Corporate Communications; Integrated Marketing "
            "Communications; Project, Programme and Portfolio Leadership; "
            "Campaign Planning; Corporate Affairs; Reputation and Brand "
            "Strategy; Vision 2030 Transformation; Change Management; "
            "Stakeholder Engagement; Governance; KPIs and Impact Measurement; "
            "Crisis Communication; Digital and Social Media; Events; "
            "Team Leadership; Training and Knowledge Transfer."
        )
    },
    {
        "category": "Education",
        "title": "Academic qualifications",
        "details": (
            "PhD in Communications, Media and Public Relations - Mansoura "
            "University. Master's Degree in Media and Public Relations - "
            "Mansoura University. Postgraduate Diploma in Public Relations - "
            "Cairo University. Degree in Mass Communications - Tanta University."
        )
    }
]


# ============================================================
# 2. DATABASE
# ============================================================

def connect_db():
    return sqlite3.connect(DB, check_same_thread=False)


def initialize_database():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                expertise TEXT,
                date_added TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                audience TEXT,
                platform TEXT,
                content_type TEXT,
                status TEXT,
                objective TEXT,
                publish_date TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                views INTEGER,
                likes INTEGER,
                comments INTEGER,
                shares INTEGER
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                analysis TEXT,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS cv_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                title TEXT,
                details TEXT,
                source TEXT,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS source_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                source_type TEXT,
                raw_text TEXT,
                audience TEXT,
                platform TEXT,
                language TEXT,
                tone TEXT,
                objective TEXT,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                analysis_json TEXT,
                engine TEXT,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS generated_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                asset_type TEXT,
                title TEXT,
                content TEXT,
                file_data BLOB,
                file_name TEXT,
                status TEXT,
                created_at TEXT
            )
        """)

        # Safe migrations for databases created by earlier app versions.
        migrations = {
            "content": {
                "source_interview_id": "INTEGER"
            },
            "interviews": {
                "question": "TEXT",
                "answer": "TEXT",
                "analysis": "TEXT",
                "created_at": "TEXT"
            },
            "source_materials": {
                "title": "TEXT",
                "source_type": "TEXT",
                "raw_text": "TEXT",
                "audience": "TEXT",
                "platform": "TEXT",
                "language": "TEXT",
                "tone": "TEXT",
                "objective": "TEXT",
                "created_at": "TEXT"
            },
            "generated_assets": {
                "source_id": "INTEGER",
                "asset_type": "TEXT",
                "title": "TEXT",
                "content": "TEXT",
                "file_data": "BLOB",
                "file_name": "TEXT",
                "status": "TEXT",
                "created_at": "TEXT"
            }
        }

        for table, columns in migrations.items():
            existing = {
                row[1]
                for row in conn.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            }

            for column, data_type in columns.items():
                if column not in existing:
                    conn.execute(
                        f"ALTER TABLE {table} "
                        f"ADD COLUMN {column} {data_type}"
                    )

        # Seed the CV knowledge base once, without duplicating records.
        count = conn.execute(
            "SELECT COUNT(*) FROM cv_knowledge"
        ).fetchone()[0]

        if count == 0:
            for item in CV_KNOWLEDGE:
                conn.execute("""
                    INSERT INTO cv_knowledge
                    (category, title, details, source, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    item["category"],
                    item["title"],
                    item["details"],
                    "Dr. Alaa Zahran detailed CV 2026",
                    datetime.now().isoformat(timespec="seconds")
                ))


initialize_database()


def read_table(table):
    allowed = [
        "experiences",
        "content",
        "performance",
        "interviews",
        "cv_knowledge",
        "source_materials",
        "analysis_records",
        "generated_assets"
    ]

    if table not in allowed:
        raise ValueError("Invalid database table.")

    with connect_db() as conn:
        return pd.read_sql_query(
            f"SELECT * FROM {table}",
            conn
        )


def get_cv_context():
    cv = read_table("cv_knowledge")

    if cv.empty:
        return "No CV knowledge is available."

    return "\n\n".join(
        f"[{row['category']}] {row['title']}: {row['details']}"
        for _, row in cv.iterrows()
    )


# ============================================================
# 3. OPTIONAL OPENAI CONNECTION
# ============================================================

def get_openai_key():
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    return os.getenv("OPENAI_API_KEY", "")


def get_openai_client():
    key = get_openai_key()

    if not key or OpenAI is None:
        return None

    try:
        return OpenAI(api_key=key)
    except Exception:
        return None


def generate_text_with_ai(client, prompt):
    if client is None:
        return None

    try:
        response = client.responses.create(
            model=TEXT_MODEL,
            input=prompt
        )
        return response.output_text.strip()
    except Exception:
        return None


def generate_ai_analysis(client, source_text, goal, audience):
    """Optional AI analysis engine, independent from HPU Core."""
    if client is None:
        raise RuntimeError("AI engine unavailable.")

    cv_context = get_cv_context()

    prompt = f"""
You are the optional contextual analysis engine within HPU.

Analyse the professional source material below. Use the CV reference
knowledge only as context. Do not assume every CV item relates to this
source. Never invent facts, achievements, dates, statistics or outcomes.
Clearly distinguish source facts from interpretation and identify
information that requires verification.

VERIFIED CV REFERENCE CONTEXT:
{cv_context}

SOURCE:
{source_text}

OBJECTIVE:
{goal}

TARGET AUDIENCE:
{audience}

Return valid JSON only, using exactly these keys:
{{
  "main_theme": "Main strategic theme",
  "contextual_insight": "Deeper interpretation",
  "content_opportunities": ["Opportunity 1", "Opportunity 2"],
  "strategic_recommendations": ["Recommendation 1", "Recommendation 2"],
  "missing_information": ["Information requiring verification"],
  "potential_audiences": ["Relevant audience"]
}}
"""

    response = client.responses.create(
        model=TEXT_MODEL,
        input=prompt
    )

    raw = response.output_text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)

    result = json.loads(raw)

    if not isinstance(result, dict):
        raise ValueError("AI returned an invalid analysis format.")

    return result


# ============================================================
# 4. INDEPENDENT HPU CORE
# ============================================================

EXPERTISE_MAP = {
    "Strategic Communication": [
        "strategic communication",
        "communication strategy",
        "الاتصال الاستراتيجي",
        "التواصل الاستراتيجي"
    ],
    "Leadership and Management": [
        "leadership",
        "management",
        "team",
        "governance",
        "القيادة",
        "الإدارة",
        "الحوكمة"
    ],
    "Change Management": [
        "change management",
        "transformation",
        "change readiness",
        "إدارة التغيير",
        "التحول"
    ],
    "Marketing and Branding": [
        "marketing",
        "brand",
        "reputation",
        "campaign",
        "التسويق",
        "العلامة التجارية",
        "السمعة"
    ],
    "Performance and Measurement": [
        "measurement",
        "baseline",
        "performance",
        "kpi",
        "خط الأساس",
        "الأداء",
        "مؤشرات الأداء",
        "القياس"
    ],
    "Stakeholder Engagement": [
        "stakeholder",
        "engagement",
        "audience",
        "أصحاب المصلحة",
        "التفاعل",
        "الجمهور"
    ],
    "Events and Experiences": [
        "event",
        "exhibition",
        "experience",
        "الفعاليات",
        "المعارض",
        "التجارب"
    ]
}


def local_analysis(source_text):
    """Deterministic local analysis. Does not require an AI connection."""
    text = (source_text or "").strip()
    lower = text.lower()

    detected = []
    for category, keywords in EXPERTISE_MAP.items():
        if any(word in lower for word in keywords):
            detected.append(category)

    if not detected:
        detected = ["General Professional Insight"]

    objective_terms = [
        "objective", "goal", "purpose",
        "هدف", "أهداف", "غاية", "الغرض"
    ]

    measurement_terms = [
        "baseline", "kpi", "metric", "measurement",
        "خط الأساس", "مؤشر", "قياس", "مؤشرات الأداء"
    ]

    evidence_terms = [
        "%", "million", "thousand", "sar",
        "budget", "increase", "decrease",
        "مليون", "ألف", "ميزانية", "نسبة"
    ]

    has_objective = any(x in lower for x in objective_terms)
    has_measurement = any(x in lower for x in measurement_terms)
    has_evidence = any(x in lower for x in evidence_terms)

    numbers = re.findall(
        r"\b\d+(?:\.\d+)?\s*%?\b",
        text
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
            "Consider adding verified examples or supporting evidence."
        )

    if not recommendations:
        recommendations.append(
            "Check whether the evidence demonstrates the intended outcome."
        )

    if has_objective and not has_measurement:
        observation = (
            "An objective appears in the source, but measurement needs "
            "further development. Define a baseline and select indicators "
            "that can assess progress."
        )
    elif has_measurement and not has_objective:
        observation = (
            "Measurement concepts appear in the source. However, the "
            "indicators should be connected to a clearly defined "
            "communication objective."
        )
    elif has_objective and has_measurement:
        observation = (
            "The source includes objective and measurement concepts. "
            "The next step is to check whether the indicators genuinely "
            "demonstrate the intended outcome."
        )
    else:
        observation = (
            "The source contains professional material that can be "
            "developed into a strategic insight. Clarify the problem, "
            "audience, objective and intended outcome."
        )

    return {
        "status": "Analysis completed",
        "detected_expertise": detected,
        "main_theme": ", ".join(detected),
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
            "No clear evidence indicators detected"
        ),
        "strategic_observation": observation,
        "recommendations": recommendations,
        "numbers_in_source": numbers,
        "source_length": len(text),
        "analysis_engine": "HPU Core - Local Rules Engine"
    }


def run_hybrid_analysis(source_text, goal, audience):
    """
    Run HPU Core and AI independently.
    If either engine fails, the other can still provide its result.
    """
    hpu_result = None
    ai_result = None
    hpu_error = None
    ai_error = None

    # Engine 1: independent local HPU Core.
    try:
        hpu_result = local_analysis(source_text)
    except Exception as error:
        hpu_error = str(error)

    # Engine 2: optional AI analysis.
    try:
        client = get_openai_client()
        if client is None:
            raise RuntimeError("AI connection unavailable.")

        ai_result = generate_ai_analysis(
            client,
            source_text,
            goal,
            audience
        )
    except Exception as error:
        ai_error = str(error)

    hpu_ok = hpu_result is not None
    ai_ok = ai_result is not None

    # Boolean orchestration.
    if hpu_ok and ai_ok:
        engine = "Combined HPU + AI"
    elif hpu_ok:
        engine = "HPU-only fallback"
    elif ai_ok:
        engine = "AI-only fallback"
    else:
        engine = "Safe fallback"

    # Keep a consistent result structure even if both engines fail.
    result = hpu_result or {
        "status": "Partial analysis",
        "detected_expertise": ["Requires further classification"],
        "main_theme": "Requires further analysis",
        "objective_check": "Not assessed",
        "measurement_check": "Not assessed",
        "evidence_check": "Not assessed",
        "strategic_observation": (
            "The HPU Core could not complete its analysis."
        ),
        "recommendations": [
            "Review the source material and try again."
        ],
        "numbers_in_source": [],
        "source_length": len(source_text or ""),
        "analysis_engine": "Fallback"
    }

    result["engine_status"] = engine
    result["hpu_available"] = hpu_ok
    result["ai_available"] = ai_ok
    result["hpu_error"] = hpu_error
    result["ai_error"] = ai_error

    result["ai_insights"] = (
        ai_result.get("contextual_insight", "") if ai_ok else ""
    )
    result["ai_theme"] = (
        ai_result.get("main_theme", "") if ai_ok else ""
    )
    result["ai_opportunities"] = (
        ai_result.get("content_opportunities", []) if ai_ok else []
    )
    result["ai_recommendations"] = (
        ai_result.get("strategic_recommendations", []) if ai_ok else []
    )
    result["missing_information"] = (
        ai_result.get("missing_information", []) if ai_ok else []
    )
    result["potential_audiences"] = (
        ai_result.get("potential_audiences", []) if ai_ok else []
    )

    # Report engine outputs side by side; human review remains necessary.
    if hpu_ok and ai_ok:
        result["comparison"] = {
            "both_engines_completed": True,
            "hpu_themes": hpu_result.get("detected_expertise", []),
            "ai_theme": ai_result.get("main_theme", ""),
            "requires_human_review": True
        }
    else:
        result["comparison"] = {
            "both_engines_completed": False,
            "requires_human_review": True
        }

    result["analysis_engine"] = engine
    return result, engine


# ============================================================
# 5. OPTIONAL GENERATION SERVICES
# ============================================================

def generate_actual_image(client, prompt):
    if client is None:
        raise RuntimeError("OpenAI is not configured.")

    result = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size="1024x1024"
    )

    return base64.b64decode(result.data[0].b64_json)


def generate_actual_audio(client, narration, voice="alloy"):
    if client is None:
        raise RuntimeError("OpenAI is not configured.")

    result = client.audio.speech.create(
        model=AUDIO_MODEL,
        voice=voice,
        input=narration,
        response_format="mp3"
    )

    return result.read()


# ============================================================
# 6. LOCAL CONTENT GENERATION
# ============================================================

def select_content_angle(analysis, objective):
    themes = analysis.get("detected_expertise", [])

    if (
        "Performance and Measurement" in themes
        or "Baseline" in str(analysis)
    ):
        return "Measurement and performance"

    if "Change Management" in themes:
        return "Communication during transformation"

    if "Marketing and Branding" in themes:
        return "Trust, reputation and brand"

    if "Strategic Communication" in themes:
        return "Strategic communication practice"

    if "Thought Leadership" in objective:
        return "Executive perspective and professional insight"

    return "Practical communication insight"


def generate_local_post(source, audience, language, tone, objective, analysis):
    angle = select_content_angle(analysis, objective)

    if language == "Arabic":
        return f"""**{source}**

في الممارسة المهنية، لا يكفي أن ننفذ الأنشطة الاتصالية أو نزيد من حجم المحتوى المنشور.

الأهم هو أن نفهم المشكلة التي نحاول معالجتها، والهدف الذي نسعى إلى تحقيقه، والتغيير الذي نريد أن نراه.

من هنا تظهر أهمية التفكير الاتصالي الاستراتيجي:
أن نربط كل نشاط اتصالي بهدف واضح،
وأن نحدد نقطة البداية قبل تقييم الأداء،
وأن نختار مؤشرات تعكس النتائج لا مجرد حجم النشاط.

التواصل الفعّال ليس مجرد نشاط يُنفذ،
بل عملية هادفة يمكن قياس أثرها.

زاوية المعالجة: {angle}
الجمهور المستهدف: {audience}
الهدف: {objective}
النبرة: {tone}

#التواصل_الاستراتيجي #الاتصال_المؤسسي #قياس_الأثر
"""

    return f"""**{source}**

In professional practice, communication success cannot be determined simply by the volume of activities or the amount of content published.

The more important questions are:

What problem are we addressing?
What objective are we pursuing?
What change do we want to achieve?

Strategic communication connects activities to a clear purpose, establishes a starting point and selects indicators that reflect meaningful results.

Effective communication is not simply an activity. It is a purposeful process whose impact can be assessed.

Content angle: {angle}
Target audience: {audience}
Objective: {objective}
Tone: {tone}

#StrategicCommunication #CorporateCommunication #ImpactMeasurement
"""


def generate_local_article(source, audience, language, objective, analysis):
    angle = select_content_angle(analysis, objective)

    if language == "Arabic":
        return f"""# {source}

## مقدمة
يمثل هذا المفهوم مدخلاً مهماً لفهم التحديات التي تواجه ممارسات التواصل المؤسسي والاستراتيجي.

## فهم المشكلة
كثيراً ما تنشغل المؤسسات بتنفيذ الأنشطة دون أن تربطها بصورة واضحة بالهدف المطلوب تحقيقه.

## أهمية الهدف
يحتاج كل نشاط اتصالي إلى هدف واضح يحدد ما الذي تريد المؤسسة تحقيقه ولماذا.

## خط الأساس والقياس
لا يمكن تقييم التغيير بصورة دقيقة دون معرفة الوضع الذي بدأت منه المؤسسة.

## من النشاط إلى الأثر
يجب أن تتجاوز عملية التقييم عدّ الأنشطة إلى فهم النتائج والتغيرات التي تحققت.

## خاتمة
إن تطوير ممارسات التواصل يبدأ من الانتقال من تنفيذ الأنشطة إلى إدارة عملية اتصالية مرتبطة بهدف ومؤشرات ونتائج واضحة.

زاوية المعالجة: {angle}
الجمهور: {audience}
الهدف: {objective}
"""

    return f"""# {source}

## Introduction
This concept provides an important starting point for understanding the challenges facing strategic and corporate communication practice.

## Understanding the Problem
Organizations can become focused on activities without connecting those activities to the results they are expected to achieve.

## The Importance of Objectives
Every communication activity should have a clear purpose. An objective explains what the organization wants to achieve and why.

## Baselines and Measurement
Performance assessment requires an understanding of the starting position.

## Moving from Activity to Impact
Evaluation should go beyond counting activities. It should examine the outcomes and changes achieved.

## Conclusion
Better communication practice connects activities with clear objectives, relevant indicators and demonstrable outcomes.

Content angle: {angle}
Audience: {audience}
Objective: {objective}
"""


def generate_visual_brief(source, audience, language, analysis):
    angle = select_content_angle(analysis, "Professional awareness")

    return f"""VISUAL CONTENT BRIEF

Main idea:
{source}

Content angle:
{angle}

Target audience:
{audience}

Suggested layout:
1. Central message.
2. Communication objective.
3. Target audience.
4. Baseline and indicators.
5. Intended outcome.

Visual direction:
Professional corporate design, clean information hierarchy,
analytical diagrams and clear visual structure.

Important:
This is a design brief, not an actual generated image.
Do not introduce unsupported statistics or claims.
"""


def generate_audio_script(source, language, audience):
    if language == "Arabic":
        return f"""النص المقترح للتعليق الصوتي

{source}

في كثير من المؤسسات، يتم التركيز على الأنشطة الاتصالية وما يتم إنتاجه ونشره.

لكن السؤال الأهم هو:
ما الهدف الذي نريد تحقيقه؟
وكيف يمكننا معرفة ما إذا كنا قد حققناه؟

يبدأ التواصل الاستراتيجي من فهم المشكلة، وتحديد الهدف، ومعرفة نقطة البداية.

ثم نختار مؤشرات تساعدنا على قياس النتائج والتغيير الذي تحقق.

التواصل ليس مجرد نشر للمعلومات، بل عملية استراتيجية تهدف إلى تحقيق أثر واضح.

الجمهور المستهدف: {audience}
"""

    return f"""SUGGESTED AUDIO NARRATION

{source}

Many organizations focus on communication activities and the amount of content they produce and publish.

But the more important question is:
What are we trying to achieve?
And how will we know whether we achieved it?

Strategic communication begins by understanding the problem, defining the objective and identifying the starting point.

We then select indicators that help measure the results and the change achieved.

Communication is not simply the distribution of information. It is a strategic process designed to create meaningful impact.

Target audience: {audience}
"""


# ============================================================
# 7. DATABASE SAVE HELPERS
# ============================================================

def save_source(title, source_type, raw_text, audience,
                platform, language, tone, objective):
    with connect_db() as conn:
        cursor = conn.execute("""
            INSERT INTO source_materials
            (title, source_type, raw_text, audience, platform,
             language, tone, objective, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            source_type,
            raw_text,
            audience,
            platform,
            language,
            tone,
            objective,
            datetime.now().isoformat(timespec="seconds")
        ))
        return cursor.lastrowid


def save_analysis(source_id, analysis, engine=None):
    with connect_db() as conn:
        conn.execute("""
            INSERT INTO analysis_records
            (source_id, analysis_json, engine, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            source_id,
            json.dumps(analysis, ensure_ascii=False),
            engine or analysis.get("engine_status", "HPU Core"),
            datetime.now().isoformat(timespec="seconds")
        ))


def save_asset(source_id, asset_type, title, content,
               file_data=None, file_name=None):
    with connect_db() as conn:
        conn.execute("""
            INSERT INTO generated_assets
            (source_id, asset_type, title, content,
             file_data, file_name, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_id,
            asset_type,
            title,
            content,
            sqlite3.Binary(file_data) if file_data else None,
            file_name,
            "Draft",
            datetime.now().isoformat(timespec="seconds")
        ))


# ============================================================
# 8. DASHBOARD
# ============================================================

def render_dashboard():
    st.title("Dr. Alaa Zahran")
    st.subheader("Personal Brand Intelligence Platform")

    cv = read_table("cv_knowledge")
    experiences = read_table("experiences")
    interviews = read_table("interviews")
    sources = read_table("source_materials")
    assets = read_table("generated_assets")
    analyses = read_table("analysis_records")

    columns = st.columns(5)
    columns[0].metric("CV Records", len(cv))
    columns[1].metric("Experiences", len(experiences))
    columns[2].metric("Interviews", len(interviews))
    columns[3].metric("Source Materials", len(sources))
    columns[4].metric("Generated Assets", len(assets))

    st.divider()
    st.subheader("HPU Processing Workflow")
    st.write(
        "Professional Knowledge → Source Analysis → "
        "Experience Matching → Content Strategy → "
        "Content Development → Review → Measurement"
    )

    st.metric("Analysis Records", len(analyses))
    st.info(
        "HPU Core analysis and local content generation work without "
        "an OpenAI API key. OpenAI is an optional enhancement."
    )


# ============================================================
# 9. CV KNOWLEDGE BASE
# ============================================================

def render_cv_knowledge():
    st.title("CV Knowledge Base")

    cv = read_table("cv_knowledge")
    st.metric("Knowledge Records", len(cv))

    if not cv.empty:
        categories = ["All"] + sorted(
            cv["category"].dropna().unique().tolist()
        )
        selected = st.selectbox("Filter category", categories)

        view = (
            cv if selected == "All"
            else cv[cv["category"] == selected]
        )

        for _, item in view.iterrows():
            with st.expander(
                f"{item['category']} | {item['title']}"
            ):
                st.write(item["details"])
                st.caption(f"Source: {item['source']}")

    st.divider()
    st.subheader("Add professional knowledge")

    with st.form("cv_form"):
        category = st.text_input("Category")
        title = st.text_input("Title")
        details = st.text_area("Details", height=130)
        submitted = st.form_submit_button("Save Knowledge")

    if submitted:
        if category.strip() and title.strip() and details.strip():
            with connect_db() as conn:
                conn.execute("""
                    INSERT INTO cv_knowledge
                    (category, title, details, source, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    category,
                    title,
                    details,
                    "User-added information - verify before publication",
                    datetime.now().isoformat(timespec="seconds")
                ))

            st.success("Knowledge record saved.")
            st.rerun()
        else:
            st.warning("Complete all fields.")


# ============================================================
# 10. PROFESSIONAL EXPERIENCES
# ============================================================

def render_experiences():
    st.title("Professional Experience Database")

    with st.form("experience_form"):
        title = st.text_input("Experience title")
        description = st.text_area("Description", height=150)
        expertise = st.selectbox(
            "Professional area",
            list(EXPERTISE_MAP.keys())
        )
        submitted = st.form_submit_button("Save Experience")

    if submitted:
        if title.strip() and description.strip():
            with connect_db() as conn:
                conn.execute("""
                    INSERT INTO experiences
                    (title, description, expertise, date_added)
                    VALUES (?, ?, ?, ?)
                """, (
                    title,
                    description,
                    expertise,
                    datetime.now().isoformat(timespec="seconds")
                ))

            st.success("Experience saved.")
            st.rerun()
        else:
            st.warning("Complete the title and description.")

    st.divider()
    st.dataframe(
        read_table("experiences"),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 11. INTERVIEW CAPTURE
# ============================================================

def render_interviews():
    st.title("Professional Interview Capture")

    questions = {
        "Professional Journey": [
            "Tell me about your professional journey.",
            "What were the most important turning points in your career?",
            "Which experience influenced your development most?"
        ],
        "Achievements": [
            "What are your three most important achievements?",
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
        "Future Vision": [
            "What professional impact would you like to create?",
            "Which areas would you like to be recognised for?",
            "What consulting opportunities interest you?"
        ]
    }

    category = st.selectbox(
        "Interview category",
        list(questions.keys())
    )
    question = st.selectbox(
        "Interview question",
        questions[category]
    )
    answer = st.text_area("Interview answer", height=220)

    if st.button("Save Interview Answer"):
        if len(answer.strip()) < 10:
            st.warning("Please enter a more complete answer.")
        else:
            analysis = local_analysis(answer)

            with connect_db() as conn:
                conn.execute("""
                    INSERT INTO interviews
                    (question, answer, analysis, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    question,
                    answer,
                    json.dumps(analysis, ensure_ascii=False),
                    datetime.now().isoformat(timespec="seconds")
                ))

            st.success("Interview answer saved.")
            st.write("HPU Core initial analysis:")
            st.json(analysis)

    st.divider()
    records = read_table("interviews")

    if records.empty:
        st.info("No interview records yet.")
    else:
        st.dataframe(
            records[["id", "question", "created_at"]],
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 12. CONTENT INTELLIGENCE STUDIO
# ============================================================

def render_content_studio():
    st.title("Content Intelligence Studio")
    st.caption(
        "Analyse source material independently, then develop content "
        "using HPU Core. OpenAI is optional."
    )

    client = get_openai_client()

    if client:
        st.success("Optional OpenAI enhancement is configured.")
    else:
        st.info(
            "OpenAI is not connected. HPU Core local analysis and "
            "content generation remain available."
        )

    with st.form("source_form"):
        title = st.text_input("Source title")

        source_type = st.selectbox(
            "Material type",
            [
                "Professional Experience",
                "Existing Post",
                "Project Description",
                "Research / Academic Material",
                "Interview Notes",
                "Article / Report",
                "Achievement",
                "Other"
            ]
        )

        source_text = st.text_area(
            "Original source material",
            height=230
        )

        col1, col2 = st.columns(2)

        with col1:
            audience = st.selectbox(
                "Target audience",
                [
                    "Business Executives",
                    "Communication Professionals",
                    "Academics and Researchers",
                    "Consultants",
                    "Government and Public-Sector Leaders",
                    "General Professional Audience"
                ]
            )

            platform = st.selectbox(
                "Platform",
                ["LinkedIn", "Facebook", "Instagram", "Website", "Other"]
            )

            language = st.selectbox(
                "Language",
                ["English", "Arabic", "Bilingual"]
            )

        with col2:
            tone = st.selectbox(
                "Tone",
                [
                    "Executive and insightful",
                    "Academic and analytical",
                    "Consultative and practical",
                    "Thought leadership",
                    "Personal and reflective"
                ]
            )

            objective = st.selectbox(
                "Primary objective",
                [
                    "Build executive credibility",
                    "Demonstrate expertise",
                    "Share a professional lesson",
                    "Explain a complex topic",
                    "Promote consulting services",
                    "Increase professional engagement"
                ]
            )

        submitted = st.form_submit_button(
            "Save Source and Analyse with HPU Core",
            type="primary"
        )

    if submitted:
        if not title.strip() or not source_text.strip():
            st.warning("Enter both a title and source material.")
        else:
            source_id = save_source(
                title,
                source_type,
                source_text,
                audience,
                platform,
                language,
                tone,
                objective
            )

            with st.spinner("HPU and AI engines are analysing the source..."):
                analysis, engine_status = run_hybrid_analysis(
                    source_text,
                    objective,
                    audience
                )

            save_analysis(source_id, analysis, engine_status)

            st.session_state["active_source_id"] = source_id
            st.session_state["active_source_text"] = source_text
            st.session_state["active_source_title"] = title
            st.session_state["active_audience"] = audience
            st.session_state["active_platform"] = platform
            st.session_state["active_language"] = language
            st.session_state["active_tone"] = tone
            st.session_state["active_objective"] = objective
            st.session_state["active_analysis"] = analysis

            # A new source should not display old generated assets.
            st.session_state.pop("generated_text", None)
            st.session_state.pop("enhanced_text", None)
            st.session_state.pop("hpu_image", None)
            st.session_state.pop("hpu_audio", None)

            st.success(
                f"Source saved and analysed. Reference #{source_id}."
            )

    if "active_analysis" not in st.session_state:
        st.info("Save source material above to begin.")
        return

    analysis = st.session_state["active_analysis"]

    st.subheader("Hybrid Intelligence Analysis")
    engine_status = analysis.get("engine_status", "HPU Core")

    if engine_status == "Combined HPU + AI":
        st.success("Both analytical engines completed successfully.")
    elif engine_status == "HPU-only fallback":
        st.warning("AI unavailable. HPU Core provided the analysis.")
    elif engine_status == "AI-only fallback":
        st.warning("HPU Core unavailable. AI provided the analysis.")
    else:
        st.error("Both engines encountered an issue. Safe fallback active.")

    # Engine status indicators.
    col1, col2 = st.columns(2)

    with col1:
        st.write("**HPU Core Engine**")
        if analysis.get("hpu_available"):
            st.success("Available")
        else:
            st.error("Unavailable")

    with col2:
        st.write("**AI Analytical Engine**")
        if analysis.get("ai_available"):
            st.success("Available")
        else:
            st.warning("Unavailable")

    # HPU findings.
    st.divider()
    st.subheader("HPU Core Findings")
    st.write("**Detected expertise:**")
    st.write(analysis.get("main_theme", "Not identified"))

    st.write("**Strategic observation:**")
    st.write(analysis.get("strategic_observation", "Not available"))

    st.write("**Objective check:**")
    st.write(analysis.get("objective_check", "Not assessed"))

    st.write("**Measurement check:**")
    st.write(analysis.get("measurement_check", "Not assessed"))

    st.write("**Evidence check:**")
    st.write(analysis.get("evidence_check", "Not assessed"))

    st.subheader("HPU Recommendations")
    for item in analysis.get("recommendations", []):
        st.write("•", item)

    # AI findings.
    if analysis.get("ai_available"):
        st.divider()
        st.subheader("AI Contextual Interpretation")
        st.write(
            analysis.get("ai_insights", "No contextual insight available.")
        )

        st.write("**AI Strategic Theme:**")
        st.write(analysis.get("ai_theme", "Not identified"))

        st.subheader("AI Content Opportunities")
        for item in analysis.get("ai_opportunities", []):
            st.write("•", item)

        st.subheader("AI Strategic Recommendations")
        for item in analysis.get("ai_recommendations", []):
            st.write("•", item)

        st.subheader("Information Requiring Verification")
        missing = analysis.get("missing_information", [])
        if missing:
            for item in missing:
                st.write("•", item)
        else:
            st.write("No additional missing information was identified by AI.")

    # Engine comparison.
    comparison = analysis.get("comparison")
    if comparison:
        st.divider()
        st.subheader("Engine Comparison")
        st.json(comparison)

    numbers = analysis.get("numbers_in_source", [])
    if numbers:
        st.write(
            "**Numbers detected in source:**",
            ", ".join(str(number) for number in numbers)
        )

    with st.expander("Engine diagnostics"):
        st.write("HPU error:", analysis.get("hpu_error"))
        st.write("AI error:", analysis.get("ai_error"))

    # Content development is always available after a source is analysed.
    st.divider()
    st.subheader("Develop Content")

    asset_type = st.selectbox(
        "Choose content format",
        [
            "LinkedIn Post",
            "Professional Article",
            "Visual Brief",
            "Audio Script"
        ],
        key="asset_type_selector"
    )

    if st.button("Generate with HPU Core", type="primary"):
        source = st.session_state["active_source_text"]
        current_audience = st.session_state["active_audience"]
        current_language = st.session_state["active_language"]
        current_tone = st.session_state["active_tone"]
        current_objective = st.session_state["active_objective"]

        if asset_type == "LinkedIn Post":
            generated = generate_local_post(
                source,
                current_audience,
                current_language,
                current_tone,
                current_objective,
                analysis
            )
        elif asset_type == "Professional Article":
            generated = generate_local_article(
                source,
                current_audience,
                current_language,
                current_objective,
                analysis
            )
        elif asset_type == "Visual Brief":
            generated = generate_visual_brief(
                source,
                current_audience,
                current_language,
                analysis
            )
        else:
            generated = generate_audio_script(
                source,
                current_language,
                current_audience
            )

        st.session_state["generated_text"] = generated
        st.session_state["generated_type"] = asset_type
        st.session_state.pop("enhanced_text", None)

    if "generated_text" in st.session_state:
        st.divider()
        st.subheader("Generated Draft")

        edited = st.text_area(
            "Review and edit the generated content",
            value=st.session_state["generated_text"],
            height=300,
            key="edited_generated_text"
        )

        if st.button("Save Generated Asset"):
            save_asset(
                st.session_state["active_source_id"],
                st.session_state["generated_type"],
                st.session_state["active_source_title"],
                edited
            )
            st.success("Generated asset saved.")

        st.download_button(
            "Download Draft",
            data=edited,
            file_name="hpu_content_draft.txt",
            mime="text/plain"
        )

        st.divider()
        st.subheader("Optional OpenAI Enhancement")

        if client is None:
            st.info(
                "Connect OpenAI in Streamlit Secrets to use this "
                "optional writing enhancement."
            )
        elif st.button("Enhance Draft with OpenAI"):
            prompt = f"""
Improve this HPU Core draft.

Original source:
{st.session_state['active_source_text']}

Draft:
{edited}

Audience:
{st.session_state['active_audience']}

Objective:
{st.session_state['active_objective']}

Language:
{st.session_state['active_language']}

Preserve the meaning. Do not invent facts or achievements.
Return the improved content only.
"""
            with st.spinner("Enhancing the draft..."):
                improved = generate_text_with_ai(client, prompt)

            if improved:
                st.session_state["enhanced_text"] = improved
            else:
                st.error("OpenAI enhancement failed. The original draft is unchanged.")

        if "enhanced_text" in st.session_state:
            st.text_area(
                "OpenAI-enhanced draft",
                value=st.session_state["enhanced_text"],
                height=280,
                key="enhanced_draft_display"
            )

        # Actual image generation is optional and separate from analysis.
        st.divider()
        st.subheader("Optional Image Generation")

        image_prompt = st.text_area(
            "Image prompt",
            value=(
                "Create a professional corporate editorial visual "
                "based on this source: "
                + st.session_state["active_source_text"][:1500]
            ),
            height=120
        )

        if st.button("Generate Actual Image"):
            if client is None:
                st.warning("OpenAI is not configured.")
            else:
                try:
                    with st.spinner("Generating image..."):
                        image_bytes = generate_actual_image(
                            client, image_prompt
                        )
                    st.session_state["hpu_image"] = image_bytes
                except Exception as error:
                    st.error(f"Image generation failed: {error}")

        if "hpu_image" in st.session_state:
            image_bytes = st.session_state["hpu_image"]
            st.image(
                image_bytes,
                caption="Generated HPU image",
                use_container_width=True
            )
            st.download_button(
                "Download Image",
                data=image_bytes,
                file_name="hpu_visual.png",
                mime="image/png"
            )

            if st.button("Save Image to Database"):
                save_asset(
                    st.session_state["active_source_id"],
                    "Visual",
                    st.session_state["active_source_title"],
                    image_prompt,
                    image_bytes,
                    "hpu_visual.png"
                )
                st.success("Image saved.")

        # Actual audio generation is optional and separate from analysis.
        st.divider()
        st.subheader("Optional Audio Generation")

        narration = st.text_area(
            "Audio narration text",
            value=st.session_state.get(
                "generated_text",
                st.session_state["active_source_text"]
            ),
            height=150,
            key="narration_text"
        )

        voice = st.selectbox(
            "Voice",
            [
                "alloy", "ash", "coral", "echo",
                "fable", "onyx", "nova", "sage", "shimmer"
            ]
        )

        if st.button("Generate Audio"):
            if client is None:
                st.warning("OpenAI is not configured.")
            else:
                try:
                    with st.spinner("Generating audio..."):
                        audio_bytes = generate_actual_audio(
                            client, narration, voice
                        )
                    st.session_state["hpu_audio"] = audio_bytes
                except Exception as error:
                    st.error(f"Audio generation failed: {error}")

        if "hpu_audio" in st.session_state:
            audio_bytes = st.session_state["hpu_audio"]
            st.audio(audio_bytes, format="audio/mp3")

            st.download_button(
                "Download Audio",
                data=audio_bytes,
                file_name="hpu_audio.mp3",
                mime="audio/mpeg"
            )

            if st.button("Save Audio to Database"):
                save_asset(
                    st.session_state["active_source_id"],
                    "Audio",
                    st.session_state["active_source_title"],
                    narration,
                    audio_bytes,
                    "hpu_audio.mp3"
                )
                st.success("Audio saved.")


# ============================================================
# 13. SOURCE LIBRARY
# ============================================================

def render_source_library():
    st.title("Source Knowledge Library")

    sources = read_table("source_materials")

    if sources.empty:
        st.info("No source materials saved yet.")
    else:
        st.dataframe(
            sources,
            use_container_width=True,
            hide_index=True
        )

        selected_id = st.selectbox(
            "Open source",
            sources["id"].tolist(),
            format_func=lambda value: (
                f"#{value} - "
                f"{sources.loc[sources['id'] == value, 'title'].iloc[0]}"
            )
        )

        selected = sources[
            sources["id"] == selected_id
        ].iloc[0]

        st.subheader(selected["title"])
        st.write(selected["raw_text"])

    st.divider()
    st.subheader("Generated Assets")

    assets = read_table("generated_assets")

    if assets.empty:
        st.info("No generated assets saved yet.")
    else:
        display = assets.drop(
            columns=["file_data"],
            errors="ignore"
        )
        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

        asset_id = st.selectbox(
            "Open generated asset",
            assets["id"].tolist()
        )
        asset = assets[
            assets["id"] == asset_id
        ].iloc[0]

        st.write(f"**{asset['asset_type']} — {asset['title']}**")

        if asset["content"]:
            st.text_area(
                "Saved content",
                value=asset["content"],
                height=200,
                key=f"saved_asset_{asset_id}"
            )

        if asset["file_data"] is not None:
            raw = bytes(asset["file_data"])

            if asset["asset_type"] == "Visual":
                st.image(raw, use_container_width=True)
            elif asset["asset_type"] == "Audio":
                st.audio(raw, format="audio/mp3")

            if asset["file_name"]:
                st.download_button(
                    "Download saved file",
                    data=raw,
                    file_name=asset["file_name"],
                    key=f"asset_download_{asset_id}"
                )

        status_options = [
            "Draft", "Under Review", "Approved", "Rejected"
        ]
        current_status = (
            asset["status"]
            if asset["status"] in status_options
            else "Draft"
        )

        new_status = st.selectbox(
            "Review status",
            status_options,
            index=status_options.index(current_status),
            key=f"asset_status_{asset_id}"
        )

        if st.button("Update Asset Status"):
            with connect_db() as conn:
                conn.execute(
                    "UPDATE generated_assets SET status=? WHERE id=?",
                    (new_status, int(asset_id))
                )
            st.success("Status updated.")
            st.rerun()


# ============================================================
# 14. PUBLISHING PLANNER
# ============================================================

def render_publishing_planner():
    st.title("Publishing Planner")

    with st.form("publishing_form"):
        title = st.text_input("Content title")

        audience = st.selectbox(
            "Audience",
            [
                "Senior Executives",
                "Communication Professionals",
                "Government Leaders",
                "Business Leaders",
                "Consultants",
                "Academic Audience"
            ]
        )

        platform = st.selectbox(
            "Platform",
            ["LinkedIn", "Website", "Instagram", "X", "Podcast"]
        )

        content_type = st.selectbox(
            "Content format",
            ["Post", "Article", "Video", "Visual", "Podcast"]
        )

        objective = st.text_input("Content objective")

        status = st.selectbox(
            "Status",
            [
                "Idea", "Draft", "Under Review",
                "Approved", "Scheduled", "Published"
            ]
        )

        publish_date = st.date_input(
            "Publication date",
            value=date.today()
        )

        submitted = st.form_submit_button("Add to Planner")

    if submitted:
        if not title.strip():
            st.warning("Enter a content title.")
        else:
            with connect_db() as conn:
                conn.execute("""
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

            st.success("Content added.")
            st.rerun()

    st.divider()
    content = read_table("content")

    if content.empty:
        st.info("No content scheduled yet.")
    else:
        st.dataframe(
            content.sort_values("publish_date"),
            use_container_width=True,
            hide_index=True
        )

        selected = st.selectbox(
            "Select content to update",
            content["id"].tolist(),
            format_func=lambda value: (
                f"#{value} - "
                f"{content.loc[content['id'] == value, 'title'].iloc[0]}"
            )
        )

        new_status = st.selectbox(
            "New status",
            [
                "Idea", "Draft", "Under Review",
                "Approved", "Scheduled", "Published"
            ]
        )

        if st.button("Update Publication Status"):
            with connect_db() as conn:
                conn.execute(
                    "UPDATE content SET status=? WHERE id=?",
                    (new_status, int(selected))
                )

            st.success("Publication status updated.")
            st.rerun()


# ============================================================
# 15. PERFORMANCE ANALYTICS
# ============================================================

def render_performance():
    st.title("Content Performance Analytics")

    content = read_table("content")

    if content.empty:
        st.info("Add content to the publishing planner first.")
        return

    published = content[
        content["status"] == "Published"
    ]

    if published.empty:
        st.info("No published content records yet.")
        return

    with st.form("performance_form"):
        selected = st.selectbox(
            "Published content",
            published["id"].tolist(),
            format_func=lambda value: (
                f"#{value} - "
                f"{published.loc[published['id'] == value, 'title'].iloc[0]}"
            )
        )

        views = st.number_input("Views", min_value=0, step=1)
        likes = st.number_input("Likes", min_value=0, step=1)
        comments = st.number_input("Comments", min_value=0, step=1)
        shares = st.number_input("Shares", min_value=0, step=1)

        submitted = st.form_submit_button("Save Performance")

    if submitted:
        with connect_db() as conn:
            conn.execute("""
                INSERT INTO performance
                (content_id, views, likes, comments, shares)
                VALUES (?, ?, ?, ?, ?)
            """, (
                int(selected),
                int(views),
                int(likes),
                int(comments),
                int(shares)
            ))

        st.success("Performance data saved.")
        st.rerun()

    performance = read_table("performance")

    if not performance.empty:
        views_total = int(performance["views"].fillna(0).sum())
        likes_total = int(performance["likes"].fillna(0).sum())
        comments_total = int(performance["comments"].fillna(0).sum())
        shares_total = int(performance["shares"].fillna(0).sum())

        a, b, c, d = st.columns(4)
        a.metric("Total Views", f"{views_total:,}")
        b.metric("Total Likes", f"{likes_total:,}")
        c.metric("Comments", f"{comments_total:,}")
        d.metric("Shares", f"{shares_total:,}")

        st.dataframe(
            performance,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 16. SYSTEM STATUS
# ============================================================

def render_system_status():
    st.title("HPU System Status")

    st.subheader("Independent HPU Core")
    st.success("Local analysis engine available.")
    st.success("Local content templates available.")
    st.success("SQLite database initialised.")

    st.write(
        "The local analysis and template-based content functions "
        "do not require OpenAI or an internet connection."
    )

    st.divider()
    st.subheader("Optional OpenAI Connection")

    if get_openai_client():
        st.success("OpenAI API key is configured.")
    else:
        st.info(
            "OpenAI is not configured. HPU Core remains available."
        )

    st.divider()
    st.subheader("Database Tables")

    with connect_db() as conn:
        tables = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """).fetchall()

    for table in tables:
        st.write("•", table[0])

    st.divider()
    st.warning(
        "For long-term production use, move the SQLite database "
        "to persistent external storage and maintain backups. "
        "Streamlit Community Cloud local files should not be treated "
        "as permanent storage."
    )


# ============================================================
# 17. METHODOLOGY
# ============================================================

def render_methodology():
    st.title("HPU Methodology and Architecture")

    st.markdown("""
### 1. Knowledge Input

Professional experiences, CV information, interviews,
original posts, articles and research material.

### 2. Independent HPU Core

- Expertise classification.
- Strategic theme detection.
- Objective assessment.
- Measurement and baseline checks.
- Evidence identification.
- Information-gap recommendations.

### 3. Content Development

- LinkedIn posts.
- Professional articles.
- Visual content briefs.
- Audio narration scripts.
- Publishing plans.

### 4. Optional AI Enhancement

OpenAI can improve selected writing tasks and generate
actual images or audio. It is not required for HPU Core.

### 5. Measurement and Improvement

Publishing records, performance indicators and feedback
support future strategic decisions.
""")

    st.warning(
        "The current local engine uses transparent rules and templates. "
        "It is an initial analytical foundation, not autonomous learning "
        "or human-level judgement."
    )


# ============================================================
# 18. MAIN APPLICATION NAVIGATION
# ============================================================

def main():
    st.sidebar.title("⚙️ HPU")
    st.sidebar.caption("HUMAN PROCESSING UNIT")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "APPLICATION MODULES",
        [
            "Executive Dashboard",
            "CV Knowledge Base",
            "Professional Experiences",
            "Interview Capture",
            "Content Intelligence Studio",
            "Source Knowledge Library",
            "Publishing Planner",
            "Performance Analytics",
            "HPU Methodology",
            "System Status"
        ]
    )

    st.sidebar.divider()
    st.sidebar.caption("Independent HPU Core")
    st.sidebar.caption("Optional AI Enhancement")
    st.sidebar.caption("Professional Knowledge Database")
    st.sidebar.caption("Content Development and Measurement")
    st.sidebar.divider()
    st.sidebar.caption("Dr. Alaa Zahran | HPU Pilot")

    if page == "Executive Dashboard":
        render_dashboard()
    elif page == "CV Knowledge Base":
        render_cv_knowledge()
    elif page == "Professional Experiences":
        render_experiences()
    elif page == "Interview Capture":
        render_interviews()
    elif page == "Content Intelligence Studio":
        render_content_studio()
    elif page == "Source Knowledge Library":
        render_source_library()
    elif page == "Publishing Planner":
        render_publishing_planner()
    elif page == "Performance Analytics":
        render_performance()
    elif page == "HPU Methodology":
        render_methodology()
    elif page == "System Status":
        render_system_status()

    st.divider()
    st.caption(
        "HPU | Human Processing Unit | Dr. Alaa Zahran | "
        "Personal Brand Intelligence"
    )


if __name__ == "__main__":
    main()
