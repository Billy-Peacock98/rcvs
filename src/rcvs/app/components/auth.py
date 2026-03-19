"""
Authentication gate using streamlit-authenticator.

Credentials are loaded from ``st.secrets["auth"]``.  Expected TOML layout::

    [auth]
    cookie_key = "some-random-string"

    [auth.credentials.usernames.billy]
    name = "Billy"
    email = "billy@example.com"
    password = "plaintext-or-bcrypt-hash"

Passwords are auto-hashed on first load (bcrypt).
"""

from __future__ import annotations

import streamlit as st
import streamlit_authenticator as stauth


def _build_authenticator() -> stauth.Authenticate | None:
    """
    Build an Authenticate instance from st.secrets.

    :return: Authenticator instance, or None if secrets are missing
    """
    try:
        if "auth" not in st.secrets:
            return None
    except FileNotFoundError:
        return None

    auth_cfg = st.secrets["auth"]

    credentials: dict = {"usernames": {}}
    raw_usernames = auth_cfg.get("credentials", {}).get("usernames", {})
    for username, info in raw_usernames.items():
        credentials["usernames"][username] = {
            "name": info["name"],
            "email": info["email"],
            "password": info["password"],
        }

    return stauth.Authenticate(
        credentials=credentials,
        cookie_name="rcvs_auth",
        cookie_key=auth_cfg.get("cookie_key", "rcvs-default-key"),
        cookie_expiry_days=30,
        auto_hash=True,
    )


def require_auth() -> None:
    """
    Gate the current page behind authentication.

    If ``st.secrets`` has no ``[auth]`` section the page loads without
    restriction (convenient for local development).  Otherwise the user
    must log in before any page content is rendered.

    Call this at the very top of every page, before any other rendering.
    """
    authenticator = _build_authenticator()

    if authenticator is None:
        return

    if not st.session_state.get("authentication_status"):
        authenticator.login(location="main")

        if st.session_state.get("authentication_status") is False:
            st.error("Incorrect username or password.")
        elif st.session_state.get("authentication_status") is None:
            st.info("Please log in to continue.")

        st.stop()

    authenticator.logout(location="sidebar")
