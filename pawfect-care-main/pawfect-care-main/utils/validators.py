def validate_login_input(username, password):
    """Validate the login username and password."""

    username = username.strip()

    if not username:
        return False, "Username is required."

    if not password:
        return False, "Password is required."

    return True, ""