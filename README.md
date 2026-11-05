# MemeSite

A Flask learning project with account registration, login, a profile page, and
a meme game. Signed-in users can select an image, add a short text caption, and
download a generated PNG.

## Status

This is a local-development prototype. The game shows up to three randomly
selected images from `website/static/images/`. Generated memes are returned as
downloads; they are not saved to a public gallery or a shared output file.
Legacy note endpoints remain, but the current home page has no note editor.

## Local setup

Use Python 3.10 or later. Clone with an account that has access while the repo
is private, then create a virtual environment:

```bash
git clone git@github.com:AugustLind/MemeSite.git
cd MemeSite
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the generated value after `SECRET_KEY=` in your local `.env`. Do not
commit it. On Windows PowerShell, activate the environment with
`.venv\Scripts\Activate.ps1` instead of the `source` command.

Start the local development server:

```bash
python main.py
```

Visit `http://127.0.0.1:5000`, create a new account, and open **Game**. Debug mode
is off by default. To opt into the debugger locally:

```bash
python -m flask --app main run --debug
```

The HTML templates load Bootstrap, jQuery, and related assets from external
CDNs. Those visual components need network access unless hosted locally.
Dependencies use compatibility ranges rather than an exact lockfile.

## Configuration and local data

| Setting/file | Purpose |
|---|---|
| `SECRET_KEY` | Required signing secret, read from the environment or root `.env` |
| `DATABASE_URL` | Optional SQLAlchemy URL; defaults to `sqlite:///database.db` |
| `instance/database.db` | Default local SQLite database, created on startup |
| `website/static/images/` | Source images used by the game |

Environment variables take precedence over `.env`. Relative SQLite URLs are
resolved under Flask's instance directory. Startup creates missing tables;
`create_all()` does not migrate existing schemas.

A fresh checkout creates an empty database; it does not include existing user
accounts or notes. Source images are served as static content and are not
private uploads. The gallery tolerates fewer than three supported image files.

### Updating an existing checkout

**Back up the existing `instance/` directory outside the repository before
pulling this cleanup.** The database was previously tracked, and the cleanup
removes it from the tracked tree. A Git update can remove that working-tree
file. Restore your private backup after updating if you need the old accounts
and notes, then confirm Git ignores it.

The previously hardcoded signing secret has also been removed. Configure a new
random value for each installation; changing it invalidates existing signed
sessions. Database passwords, user data, `.env`, and Python bytecode must stay
out of version control.

The old database and signing secret remain in earlier commits. This cleanup
neither rewrites history nor certifies the repository as safe to publish.
If an installation used that secret, replace it there as well.

## Repository layout

| Path | Purpose |
|---|---|
| `main.py` | Local development entry point |
| `website/__init__.py` | App factory, local configuration, database setup, and session loading |
| `website/auth.py` | Registration, login, and logout |
| `website/models.py` | User and legacy note models |
| `website/views.py` | Game, image downloads, profiles, and note endpoints |
| `website/templates/` | Jinja templates |
| `website/static/images/` | Existing meme-image collection |
| `tests/test_app.py` | App regression checks with an in-memory database and synthetic images |

## Checks

After installing the dependencies:

```bash
python -m unittest discover -s tests -v
```

The suite covers required configuration, authentication, empty forms, small
image libraries, downloads, path validation, and note ownership. It never uses
the old user database. During cleanup, syntax, ignore rules, templates, and
isolated handler checks were run; the full Flask suite could not run because
dependency downloads were unavailable in that environment.

## Before deployment or publication

- Keep the app local until deployment behavior has been reviewed. It does not
  yet provide CSRF protection, login rate limiting, or a production deployment
  configuration. The built-in Flask server is for development.
- Use HTTPS and suitable secure-cookie settings for any deployment, with a
  production WSGI server and a separately managed secret.
- Review both current files and Git history for private data. Removing the
  database in the latest commit does not remove historical copies.
- Review the bundled images and confirm their sources and redistribution
  permissions before making the repository public. This cleanup preserves
  those assets and does not establish ownership or a license for them.
- No project-wide license has been added. Make a separate license decision for
  your code after checking applicable third-party material.
