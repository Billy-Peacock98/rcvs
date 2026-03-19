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


def _get_authenticator() -> stauth.Authenticate | None:
    """
    Get or create a cached Authenticate instance from st.secrets.

    The instance is stored in session_state to avoid creating
    duplicate CookieManager components within a single script run.

    :return: Authenticator instance, or None if secrets are missing
    """
    if "_authenticator" in st.session_state:
        return st.session_state["_authenticator"]

    try:
        if "auth" not in st.secrets:
            st.session_state["_authenticator"] = None
            return None
    except FileNotFoundError:
        st.session_state["_authenticator"] = None
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

    authenticator = stauth.Authenticate(
        credentials=credentials,
        cookie_name="rcvs_auth",
        cookie_key=auth_cfg.get("cookie_key", "rcvs-default-key"),
        cookie_expiry_days=30,
        auto_hash=True,
    )
    st.session_state["_authenticator"] = authenticator
    return authenticator


def is_authenticated() -> bool:
    """
    Check whether the user is authenticated.

    Returns True immediately when no auth secrets are configured
    (convenient for local development).

    :return: True if the user is logged in or auth is not configured
    """
    try:
        if "auth" not in st.secrets:
            return True
    except FileNotFoundError:
        return True

    return st.session_state.get("authentication_status") is True


def build_login_page() -> None:
    """
    Render the login form as a standalone page.

    Intended for use with ``st.Page(build_login_page, ...)``.
    """
    authenticator = _get_authenticator()
    if authenticator is None:
        return

    authenticator.login(location="main")

    if st.session_state.get("authentication_status") is False:
        st.error("Incorrect username or password.")
    elif st.session_state.get("authentication_status") is None:
        st.info("Please log in to continue.")


def render_logout() -> None:
    """
    Render the logout button in the sidebar.

    Only renders when auth is configured and user is logged in.
    """
    authenticator = _get_authenticator()
    if authenticator is None:
        return

    if st.session_state.get("authentication_status"):
        authenticator.logout(location="sidebar")
