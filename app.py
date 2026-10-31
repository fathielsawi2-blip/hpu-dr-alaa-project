import streamlit as st
import sqlite3
import pandas as pd
import json
import re
from datetime import date, datetime

# ==========================================
# HPU - HUMAN PROCESSING UNIT
# DR. ALAA ZAHRAN PILOT
# ==========================================

st.set_page_config(
    page_title="HPU | Alaa Zahran",
    page_icon="🧠",
    layout="wide"
)

DB = "hpu_alaa.db"


# ==========================================
# DATABASE
# ==========================================

def connect_db():
    return sqlite3.connect(DB)


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

        # Safely add interview relationship to old databases
        columns = [
            row[1] for row in
            conn.execute("PRAGMA table_info(content)").fetchall()
        ]

        if "source_interview_id" not in columns:
            conn.execute(
                "ALTER TABLE content ADD COLUMN source_interview_id INTEGER"
            )


initialize_database()


def read_table(table):

    allowed = [
        "experiences", "content",
        "performance", "interviews"
    ]

    if table not in allowed:
        raise ValueError("Invalid table")

    with connect_db() as conn:
        return pd.read_sql_query(
            f"SELECT * FROM {table}", conn
        )


# ==========================================
# HPU INTELLIGENCE ENGINE
# ==========================================

EXPERTISE_MAP = {

    "Strategic Communication": [
        "strategy", "strategic communication",
        "communication strategy", "messaging"
    ],

    "Integrated Marketing": [
        "marketing", "campaign", "advertising",
        "integrated marketing"
    ],

    "Project Leadership": [
        "project", "leadership", "team",
        "management", "portfolio"
    ],

    "Corporate Affairs": [
        "corporate affairs", "corporate",
        "government", "institution"
    ],

    "Brand Strategy": [
        "brand", "branding", "reputation",
        "identity"
    ],

    "Change Management": [
        "change", "transformation",
        "vision 2030", "reform"
    ],

    "Stakeholder Engagement": [
        "stakeholder", "engagement",
        "executive", "partnership"
    ],

    "Crisis Communication": [
        "crisis", "risk", "issues",
        "reputation management"
    ],

    "Digital and Social Media": [
        "digital", "social media",
        "linkedin", "online"
    ],

    "Academic and Research": [
        "research", "phd", "academic",
        "university", "publication"
    ]
}


def analyze_experience(answer):

    text = answer.lower()

    detected = []

    for expertise, keywords in EXPERTISE_MAP.items():

        if any(word in text for word in keywords):
            detected.append(expertise)

    if not detected:
        detected = ["General Professional Experience"]

    # Identify potential achievement indicators
    numbers = re.findall(
        r'\b\d+(?:\.\d+)?\s*%?\b', answer
    )

    # Identify experience signals
    achievement_words = [
        "achieved", "delivered", "improved",
        "increased", "reduced", "developed",
        "implemented", "managed", "led",
        "established", "launched"
    ]

    achievements = [
        word for word in achievement_words
        if word in text
    ]

    # Audience intelligence
    audiences = []

    if any(x in text for x in [
        "strategy", "leadership", "executive",
        "corporate", "transformation"
    ]):
        audiences.append("Business Executives")

    if any(x in text for x in [
        "research", "academic", "phd",
        "university", "study"
    ]):
        audiences.append("Academics and Researchers")

    if any(x in text for x in [
        "communication", "campaign", "marketing",
        "brand", "stakeholder"
    ]):
        audiences.append("Communication Professionals")

    if any(x in text for x in [
        "consulting", "consultant", "advisory",
        "client"
    ]):
        audiences.append("Consultants")

    if not audiences:
        audiences = ["General Professional Audience"]

    # Identify missing evidence
    followups = []

    if not numbers:
        followups.append(
            "Can you provide measurable results or numbers?"
        )

    if not any(x in text for x in [
        "led", "managed", "responsible", "developed"
    ]):
        followups.append(
            "What was your personal responsibility in this experience?"
        )

    if not any(x in text for x in [
        "challenge", "problem", "difficulty", "risk"
    ]):
        followups.append(
            "What was the main challenge you faced?"
        )

    if not any(x in text for x in [
        "result", "outcome", "achieved", "improved"
    ]):
        followups.append(
            "What was the final outcome?"
        )

    if not any(x in text for x in [
        "year", "month", "during", "between"
    ]):
        followups.append(
            "When did this experience take place?"
        )

    return {
        "expertise": detected,
        "audiences": audiences,
        "achievement_signals": achievements,
        "numbers": numbers,
        "followups": followups
    }


# ==========================================
# HPU STRATEGY GENERATOR
# ==========================================

def generate_strategy(analysis, answer):

    ideas = []

    expertise = ", ".join(analysis["expertise"])

    for audience in analysis["audiences"]:

        if audience == "Business Executives":

            ideas.append({
                "title": "Strategic Leadership: Lessons from Professional Experience",
                "audience": audience,
                "format": "LinkedIn Post",
                "objective": "Establish executive credibility."
            })

        elif audience == "Academics and Researchers":

            ideas.append({
                "title": "Research and Professional Practice",
                "audience": audience,
                "format": "Article",
                "objective": "Demonstrate academic knowledge."
            })

        elif audience == "Communication Professionals":

            ideas.append({
                "title": "Practical Lessons in Strategic Communication",
                "audience": audience,
                "format": "Video",
                "objective": "Share professional expertise."
            })

        elif audience == "Consultants":

            ideas.append({
                "title": "Professional Insights for Organizational Development",
                "audience": audience,
                "format": "Podcast",
                "objective": "Build consulting authority."
            })

        else:

            ideas.append({
                "title": "Professional Experience and Lessons Learned",
                "audience": audience,
                "format": "LinkedIn Post",
                "objective": "Build professional visibility."
            })

    return ideas


# ==========================================
# INTERVIEW QUESTIONS
# ==========================================

QUESTIONS = {

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


# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("🧠 HPU")
st.sidebar.caption("Human Processing Unit")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Live Interview",
        "Interview Records",
        "Professional Experiences",
        "Content Studio",
        "Publishing Planner",
        "Performance"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Dr. Alaa Zahran | Pilot Project")


# ==========================================
# DASHBOARD
# ==========================================

if page == "Dashboard":

    st.title("Dr. Alaa Zahran")
    st.subheader("Personal Brand Intelligence")

    experiences = read_table("experiences")
    content = read_table("content")
    interviews = read_table("interviews")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Experiences", len(experiences))
    c2.metric("Interview Answers", len(interviews))
    c3.metric("Content Ideas", len(content))

    published = (
        len(content[content["status"] == "Published"])
        if not content.empty else 0
    )

    c4.metric("Published", published)

    st.markdown("---")

    st.subheader("HPU Processing Architecture")

    st.write(
        "Interview → Experience Analysis → "
        "Audience Intelligence → Content Strategy → Performance"
    )

    st.info(
        "Start with Live Interview to begin collecting "
        "and processing Dr. Alaa's professional knowledge."
    )


# ==========================================
# LIVE INTERVIEW
# ==========================================

elif page == "Live Interview":

    st.title("🎙️ HPU Live Interview")

    st.write(
        "Capture professional knowledge and "
        "generate immediate content intelligence."
    )

    category = st.selectbox(
        "Interview category",
        list(QUESTIONS.keys())
    )

    question = st.selectbox(
        "Interview question",
        QUESTIONS[category]
    )

    answer = st.text_area(
        "Dr. Alaa's answer",
        height=220,
        placeholder="Enter his answer here..."
    )

    st.markdown("---")

    st.subheader("Live Intelligence Analysis")

    if len(answer.strip()) >= 30:

        analysis = analyze_experience(answer)

        ideas = generate_strategy(analysis, answer)

        st.success("HPU has processed the answer.")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Detected Expertise**")

            for item in analysis["expertise"]:
                st.write("• " + item)

        with c2:
            st.markdown("**Potential Audiences**")

            for item in analysis["audiences"]:
                st.write("• " + item)

        st.markdown("---")

        st.subheader("Achievement Indicators")

        if analysis["achievement_signals"]:
            st.write(
                ", ".join(analysis["achievement_signals"])
            )
        else:
            st.info(
                "Ask for specific achievements and responsibilities."
            )

        if analysis["numbers"]:
            st.write(
                "Potential numerical evidence: "
                + ", ".join(analysis["numbers"])
            )

        st.markdown("---")

        st.subheader("Recommended Content Strategy")

        for i, idea in enumerate(ideas, 1):

            with st.container(border=True):

                st.markdown(
                    f"**Opportunity {i}: {idea['title']}**"
                )

                st.write("Audience:", idea["audience"])
                st.write("Format:", idea["format"])
                st.write("Objective:", idea["objective"])

        st.markdown("---")

        st.subheader("HPU Follow-up Questions")

        if analysis["followups"]:

            for item in analysis["followups"]:
                st.write("• " + item)

        else:
            st.success(
                "The answer contains several useful information signals."
            )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "💾 Save Interview Answer",
                use_container_width=True
            ):

                with connect_db() as conn:

                    cursor = conn.execute(
                        """
                        INSERT INTO interviews
                        (question, answer, analysis, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            question,
                            answer,
                            json.dumps(analysis),
                            datetime.now().isoformat(
                                timespec="seconds"
                            )
                        )
                    )

                    interview_id = cursor.lastrowid

                st.session_state["last_interview_id"] = interview_id

                st.success(
                    f"Interview answer saved. Record #{interview_id}"
                )

        with col2:

            if st.button(
                "🚀 Save All Content Ideas",
                use_container_width=True
            ):

                interview_id = st.session_state.get(
                    "last_interview_id"
                )

                if not interview_id:

                    st.warning(
                        "Save the interview answer first."
                    )

                else:

                    with connect_db() as conn:

                        for idea in ideas:

                            conn.execute(
                                """
                                INSERT INTO content
                                (
                                    title, audience, platform,
                                    content_type, status,
                                    objective, publish_date,
                                    source_interview_id
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    idea["title"],
                                    idea["audience"],
                                    "LinkedIn",
                                    idea["format"],
                                    "Idea",
                                    idea["objective"],
                                    str(date.today()),
                                    interview_id
                                )
                            )

                    st.success(
                        "Content opportunities added to Content Studio."
                    )

    else:

        st.info(
            "Enter at least 30 characters of an interview answer "
            "to activate HPU intelligence."
        )


# ==========================================
# INTERVIEW RECORDS
# ==========================================

elif page == "Interview Records":

    st.title("Interview Knowledge Database")

    records = read_table("interviews")

    if records.empty:

        st.info("No interview records yet.")

    else:

        st.dataframe(
            records[
                ["id", "question", "created_at"]
            ],
            use_container_width=True,
            hide_index=True
        )

        selected = st.selectbox(
            "Open interview record",
            records["id"].tolist()
        )

        record = records[
            records["id"] == selected
        ].iloc[0]

        st.subheader("Interview Question")
        st.write(record["question"])

        st.subheader("Recorded Answer")
        st.write(record["answer"])

        st.subheader("HPU Analysis")

        result = json.loads(record["analysis"])

        st.json(result)


# ==========================================
# PROFESSIONAL EXPERIENCES
# ==========================================

elif page == "Professional Experiences":

    st.title("Professional Experience Database")

    with st.form("experience_form"):

        title = st.text_input("Experience title")

        description = st.text_area("Description")

        expertise = st.selectbox(
            "Professional area",
            list(EXPERTISE_MAP.keys())
        )

        submitted = st.form_submit_button("Save Experience")

        if submitted:

            if title.strip() and description.strip():

                with connect_db() as conn:

                    conn.execute(
                        """
                        INSERT INTO experiences
                        (title, description, expertise, date_added)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            title,
                            description,
                            expertise,
                            str(date.today())
                        )
                    )

                st.success("Experience saved!")

            else:
                st.warning("Complete the required fields.")

    st.markdown("---")

    st.dataframe(
        read_table("experiences"),
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# CONTENT STUDIO
# ==========================================

elif page == "Content Studio":

    st.title("HPU Content Studio")

    with st.form("content_form"):

        title = st.text_input("Content title")

        audience = st.selectbox(
            "Audience",
            [
                "Business Executives",
                "Communication Professionals",
                "Academics and Researchers",
                "Consultants",
                "General Professional Audience"
            ]
        )

        platform = st.selectbox(
            "Platform",
            ["LinkedIn", "Facebook", "Instagram", "Other"]
        )

        content_type = st.selectbox(
            "Format",
            [
                "LinkedIn Post",
                "Article",
                "Video",
                "Podcast",
                "Infographic"
            ]
        )

        objective = st.text_area("Content objective")

        submitted = st.form_submit_button("Save Content")

        if submitted:

            if title.strip():

                with connect_db() as conn:

                    conn.execute(
                        """
                        INSERT INTO content
                        (title, audience, platform, content_type,
                         status, objective, publish_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            title,
                            audience,
                            platform,
                            content_type,
                            "Idea",
                            objective,
                            str(date.today())
                        )
                    )

                st.success("Content saved!")

            else:
                st.warning("Enter a title.")

    st.markdown("---")

    st.dataframe(
        read_table("content"),
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# PUBLISHING PLANNER
# ==========================================

elif page == "Publishing Planner":

    st.title("Publishing Planner")

    content = read_table("content")

    if content.empty:

        st.info("No content available.")

    else:

        selected = st.selectbox(
            "Select content",
            content["id"].tolist(),
            format_func=lambda x: content.loc[
                content["id"] == x, "title"
            ].iloc[0]
        )

        new_status = st.selectbox(
            "Update status",
            [
                "Idea",
                "Draft",
                "Under Review",
                "Approved",
                "Published"
            ]
        )

        if st.button("Update Status"):

            with connect_db() as conn:

                conn.execute(
                    "UPDATE content SET status=? WHERE id=?",
                    (new_status, selected)
                )

            st.success("Status updated!")
            st.rerun()

        st.dataframe(
            content,
            use_container_width=True,
            hide_index=True
        )


# ==========================================
# PERFORMANCE
# ==========================================

elif page == "Performance":

    st.title("Content Performance")

    content = read_table("content")

    if content.empty:

        st.info("Create content first.")

    else:

        published = content[
            content["status"] == "Published"
        ]

        if published.empty:

            st.info("No published content yet.")

        else:

            with st.form("performance_form"):

                selected = st.selectbox(
                    "Published content",
                    published["id"].tolist(),
                    format_func=lambda x: published.loc[
                        published["id"] == x, "title"
                    ].iloc[0]
                )

                views = st.number_input(
                    "Views", min_value=0, step=1
                )

                likes = st.number_input(
                    "Likes", min_value=0, step=1
                )

                comments = st.number_input(
                    "Comments", min_value=0, step=1
                )

                shares = st.number_input(
                    "Shares", min_value=0, step=1
                )

                submitted = st.form_submit_button(
                    "Save Performance"
                )

                if submitted:

                    with connect_db() as conn:

                        conn.execute(
                            """
                            INSERT INTO performance
                            (content_id, views, likes, comments, shares)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                selected,
                                views,
                                likes,
                                comments,
                                shares
                            )
                        )

                    st.success("Performance saved!")

            results = read_table("performance")

            if not results.empty:

                st.dataframe(
                    results,
                    use_container_width=True,
                    hide_index=True
                )

                st.metric(
                    "Total Views",
                    int(results["views"].sum())
                )

                st.metric(
                    "Total Engagement",
                    int(
                        results["likes"].sum()
                        + results["comments"].sum()
                        + results["shares"].sum()
                    )
                )


# ==========================================
# FOOTER
# ==========================================

st.markdown("---")

st.caption(
    "HPU | Human Processing Unit | "
    "Dr. Alaa Zahran Intelligence Pilot"
)
