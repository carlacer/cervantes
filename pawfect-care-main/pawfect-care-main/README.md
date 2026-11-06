# Pawfect Care

## Prerequisites

- Install [uv](https://docs.astral.sh/uv/getting-started/installation/). The project
  is configured for Python 3.14; uv reads `.python-version` and manages the
  project's isolated `.venv` environment.
- Have a desktop environment with Tcl/Tk available for the CustomTkinter GUI.
  Standard Python installers include Tkinter on Windows and macOS; some Linux
  distributions require installing their Tk package separately. Check it with
  `uv run python -m tkinter` if the GUI does not start.
- Internet access is needed for the first `uv sync` so uv can download Python
  (if needed) and project packages. No separate `pip install customtkinter` is
  required: `uv sync` installs `customtkinter` and `bcrypt` from the project
  dependency files.

## First-time setup

Use Python 3.14 and run these commands from the project root:

```powershell
uv sync
uv run python -m database.schema
uv run python -m database.seed
uv run python -m database.setup_admin
uv run python main.py
```

The seed step installs the default service categories and services. It does not
create an Admin account. The setup step securely prompts for the first Admin's
username, full name, and password; password input is hidden and must be at least
12 characters. It refuses to create a bootstrap account if any user already
exists. Later accounts can be added through **User Management**.

Keep `pawfect_care.db` private because it contains customer, pet, appointment,
and password-hash data. Do not commit the local database to a public repository.

## Existing local database

Updating the source code does not remove accounts already stored in
`pawfect_care.db`. Sign in with an existing Admin, change its password in User
Management, and deactivate any old demo accounts you no longer need. The
first-Admin setup command intentionally refuses to overwrite an existing user
database.
