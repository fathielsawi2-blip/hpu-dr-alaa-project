
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --------------------------------
# HPU - CORE APPLICATION
# --------------------------------

st.set_page_config(
    page_title="HPU | Alaa Zahran",
    page_icon="🧠",
    layout="wide"
)

DB = "hpu_alaa.db"


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


initialize_database()


# --------------------------------
# HPU DECISION ENGINE
# --------------------------------

def hpu_analyze(opportunity, risk, uncertainty):

    if uncertainty >= 8:
        return "Pause and collect more information"

    elif opportunity > risk:
        return "Develop and test this content idea"

    elif risk > opportunity:
        return "Review the idea before publishing"

    else:
        return "Run deeper analysis"


# --------------------------------
# SIDEBAR
# --------------------------------

st.sidebar.title("🧠 HPU")
st.sidebar.caption("Human Processing Unit")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Professional Experiences",
        "Content Studio",
        "Publishing Planner",
        "Performance"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Pilot Project | Dr. Alaa Zahran")


# --------------------------------
# DATABASE HELPERS
# --------------------------------

def read_table(table):
    with connect_db() as conn:
        return pd.read_sql_query(
            f"SELECT * FROM {table}",
            conn
        )


# --------------------------------
# DASHBOARD
# --------------------------------

if page == "Dashboard":

    st.title("Dr. Alaa Zahran")
    st.subheader("Personal Brand Intelligence")
    st.caption(
        "Academic | Executive | Strategic Consultant"
    )

    experiences = read_table("experiences")
    content = read_table("content")

    total_experiences = len(experiences)
    total_ideas = len(content)

    published = (
        len(content[content["status"] == "Published"])
        if total_ideas else 0
    )

    drafts = (
        len(content[content["status"] == "Draft"])
        if total_ideas else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Experiences", total_experiences)
    c2.metric("Content Items", total_ideas)
    c3.metric("Published", published)
    c4.metric("Drafts", drafts)

    st.markdown("---")
    st.subheader("Content Development")

    if total_ideas:
        st.dataframe(
            content,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(
            "Your content workspace is ready. "
            "Start by recording a professional experience."
        )

    st.markdown("---")
    st.subheader("HPU Intelligence")

    st.write(
        "HPU will help transform professional experiences "
        "into structured content opportunities."
    )


# --------------------------------
# PROFESSIONAL EXPERIENCES
# --------------------------------

elif page == "Professional Experiences":

    st.title("Professional Experience Database")

    st.write(
        "Record verified experiences, achievements "
        "and professional knowledge."
    )

    with st.form("experience_form"):

        title = st.text_input(
            "Experience or achievement title"
        )

        description = st.text_area(
            "Describe the experience"
        )

        expertise = st.selectbox(
            "Professional area",
            [
                "Strategic Communication",
                "Integrated Marketing",
                "Project Leadership",
                "Corporate Affairs",
                "Brand Strategy",
                "Change Management",
                "Stakeholder Engagement",
                "Communication Governance",
                "Crisis Communication",
                "Digital and Social Media",
                "Other"
            ]
        )

        submitted = st.form_submit_button(
            "Save Experience"
        )

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

                st.success("Experience saved successfully!")

            else:
                st.warning("Please complete the title and description.")

    st.markdown("---")
    st.subheader("Recorded Experiences")

    experiences = read_table("experiences")

    if not experiences.empty:
        st.dataframe(
            experiences,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No experiences recorded yet.")


# --------------------------------
# CONTENT STUDIO
# --------------------------------

elif page == "Content Studio":

    st.title("HPU Content Studio")

    st.write(
        "Turn professional knowledge into content opportunities."
    )

    with st.form("content_form"):

        title = st.text_input("Content title or idea")

        audience = st.selectbox(
            "Target audience",
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
            "Content format",
            [
                "LinkedIn Post",
                "Article",
                "Video",
                "Podcast",
                "Infographic"
            ]
        )

        objective = st.text_area(
            "What should this content achieve?"
        )

        status = st.selectbox(
            "Status",
            ["Idea", "Draft", "Under Review", "Approved", "Published"]
        )

        publish_date = st.date_input(
            "Planned publication date",
            value=date.today()
        )

        submitted = st.form_submit_button(
            "Save Content Idea"
        )

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
                            status,
                            objective,
                            str(publish_date)
                        )
                    )

                st.success("Content idea saved!")

            else:
                st.warning("Please enter a content title.")

    st.markdown("---")
    st.subheader("Current Content Ideas")

    content = read_table("content")

    if not content.empty:
        st.dataframe(
            content,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Your content studio is waiting for its first idea.")


# --------------------------------
# PUBLISHING PLANNER
# --------------------------------

elif page == "Publishing Planner":

    st.title("Publishing Planner")

    content = read_table("content")

    if content.empty:
        st.info("Add content ideas in Content Studio first.")
    else:

        st.subheader("Update Content Status")

        selected = st.selectbox(
            "Select content",
            content["id"].tolist(),
            format_func=lambda x: content.loc[
                content["id"] == x, "title"
            ].iloc[0]
        )

        new_status = st.selectbox(
            "New status",
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
                    "UPDATE content SET status = ? WHERE id = ?",
                    (new_status, selected)
                )

            st.success("Status updated!")
            st.rerun()

        st.markdown("---")
        st.dataframe(
            content,
            use_container_width=True,
            hide_index=True
        )


# --------------------------------
# PERFORMANCE TRACKING
# --------------------------------

elif page == "Performance":

    st.title("Content Performance")

    content = read_table("content")

    if content.empty:
        st.info("Create content before recording performance.")
    else:

        published_content = content[
            content["status"] == "Published"
        ]

        if published_content.empty:
            st.info("No published content available yet.")
        else:

            with st.form("performance_form"):

                selected = st.selectbox(
                    "Published content",
                    published_content["id"].tolist(),
                    format_func=lambda x: published_content.loc[
                        published_content["id"] == x, "title"
                    ].iloc[0]
                )

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

                    st.success("Performance recorded!")

            st.markdown("---")
            st.subheader("Performance History")

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

            else:
                st.info("No performance measurements recorded yet.")


# --------------------------------
# FOOTER
# --------------------------------

st.markdown("---")
st.caption(
    "HPU | Human Processing Unit | "
    "Dr. Alaa Zahran Pilot Project"
)

