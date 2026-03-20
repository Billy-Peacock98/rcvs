from __future__ import annotations

import pandas as pd
import streamlit as st

DEFAULT_TEMPLATE = """\
Dear {greeting},

I am writing to enquire about graduate veterinary positions at {practice_name}. \
I found your practice through the RCVS VetGDP register and was particularly \
interested in your work with {animals}.

I am a recent veterinary graduate looking for a supportive VetGDP-approved \
practice to begin my career. I would welcome the opportunity to discuss any \
current or upcoming vacancies with you.

I have attached my CV for your consideration and would be happy to provide \
any further information.

Kind regards,
{sender_name}"""

DEFAULT_SUBJECT = "VetGDP Graduate Position Enquiry — {practice_name}"


def _get_greeting(
    row: pd.Series
) -> str:
    """
    Build a greeting from the director/principal name.

    Falls back to 'Hiring Manager' if no director is known.

    :param row: Practice DataFrame row

    :return: Greeting string e.g. 'Dr Smith' or 'Hiring Manager'
    """
    director = row.get("director", "")
    if not director or director == "":
        return "Hiring Manager"

    # director is like "Dr Jane Smith (Director)" or "Mr John Doe (Partner)"
    name_part = director.split("(")[0].strip()
    return name_part


def _get_animals_phrase(
    row: pd.Series
) -> str:
    """
    Build a natural phrase describing the animals the practice treats.

    :param row: Practice DataFrame row

    :return: Animals phrase e.g. 'dogs and cats' or 'small animals and equines'
    """
    animals_str = row.get("animals_str", "")
    if not animals_str:
        return "small animals"

    animals = [a.strip().lower() for a in animals_str.split(",") if a.strip()]
    if not animals:
        return "small animals"

    if len(animals) == 1:
        return animals[0]
    if len(animals) == 2:
        return f"{animals[0]} and {animals[1]}"

    return f"{', '.join(animals[:3])} and more"


def render_email_draft(
    row: pd.Series
) -> None:
    """
    Render an email draft section for a practice.

    Shows a pre-filled subject and body that the user can edit,
    with a copy-to-clipboard button.

    :param row: Practice DataFrame row
    """
    st.subheader("Draft Email")

    practice_email = row.get("email", "")
    if not practice_email:
        st.warning("No email address on file for this practice.")
        return

    # Sender name (persisted in session state)
    if "email_sender_name" not in st.session_state:
        st.session_state.email_sender_name = ""

    sender_name = st.text_input(
        "Your name",
        value=st.session_state.email_sender_name,
        key="email_sender_input",
        placeholder="Enter your name...",
    )
    st.session_state.email_sender_name = sender_name

    greeting = _get_greeting(row)
    animals = _get_animals_phrase(row)
    practice_name = row["name"]

    subject = DEFAULT_SUBJECT.format(practice_name=practice_name)
    body = DEFAULT_TEMPLATE.format(
        greeting=greeting,
        practice_name=practice_name,
        animals=animals,
        sender_name=sender_name if sender_name else "[Your Name]",
    )

    st.markdown(f"**To:** {practice_email}")

    edited_subject = st.text_input(
        "Subject",
        value=subject,
        key=f"email_subject_{practice_name}",
    )

    edited_body = st.text_area(
        "Email body",
        value=body,
        key=f"email_body_{practice_name}",
        height=300,
    )

    # Build full email text for copying
    full_email = f"To: {practice_email}\nSubject: {edited_subject}\n\n{edited_body}"

    col1, col2 = st.columns(2)
    with col1:
        st.code(full_email, language=None)
    with col2:
        st.markdown(
            "**How to use:**\n"
            "1. Edit the draft above as needed\n"
            "2. Select and copy the text from the box on the left\n"
            "3. Paste into your email client\n"
            "4. The status will update when you change it above"
        )
