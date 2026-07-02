import json

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.config import get_settings
from app.core.templates import render_template
from app.domains.auth.service import AuthService


router = APIRouter(tags=["auth"])
_settings = get_settings()
auth_service = AuthService(_settings)


def _login_template(request: Request, error_message: str | None = None):
    return render_template(
        "domains/auth/views/login.mako",
        request,
        google_configured=auth_service.google_is_configured(),
        google_emails_configured=auth_service.google_emails_configured(),
        password_configured=auth_service.password_login_configured(),
        error_message=error_message,
    )


@router.get("/login", name="login_page")
async def login_page(request: Request):
    # Hosted mode: login lives entirely on noteeli.com. The session cookie
    # set there is shared with this subdomain, so we just bounce.
    if _settings.hosted_mode:
        return_to = str(request.url_for("workspace_page"))
        return RedirectResponse(
            url=f"{_settings.portal_url}/login?return_to={return_to}",
            status_code=303,
        )
    if auth_service.get_current_user(request):
        return RedirectResponse(url=request.url_for("workspace_page"), status_code=303)
    return _login_template(request)


@router.get("/auth/google", name="auth_google_login")
async def auth_google_login(request: Request):
    if auth_service.is_local_request(request):
        return RedirectResponse(url=request.url_for("workspace_page"), status_code=303)

    client = auth_service.get_google_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured.")

    redirect_uri = str(request.url_for("auth_google_callback"))
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback", name="auth_google_callback")
async def auth_google_callback(request: Request):
    import logging as _logging
    _log = _logging.getLogger(__name__)

    client = auth_service.get_google_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured.")

    try:
        token = await client.authorize_access_token(request)
        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo = await client.parse_id_token(request, token)
    except OAuthError as exc:
        _log.warning("Google OAuth callback failed: %s (%s)", exc.error, exc.description)
        return _login_template(request, error_message=f"Login failed: {exc.error}")
    except Exception as exc:
        _log.exception("Unexpected error during Google OAuth token exchange")
        return _login_template(request, error_message=f"Login error: {type(exc).__name__}: {exc}")

    email = userinfo.get("email", "")
    if not auth_service.google_email_is_allowed(email):
        # Log the exact identity Google sent — without this, "user can't
        # log in" reports are undiagnosable (wrong account picked? typo in
        # the allowlist? stale env?). Warning level: it's an access event.
        _log.warning("Google login DENIED for %r (not on the allowlist)", email)
        return _login_template(request, error_message=f"Access denied for {email}.")

    session_user: dict = {
        "sub": userinfo.get("sub"),
        "email": email,
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
        "is_local": False,
    }

    # In hosted mode: create/update the DB user and check subscription.
    if _settings.hosted_mode:
        try:
            from app.domains.billing.service import BillingService
            billing = BillingService(_settings)
            db_id = billing.get_or_create_user(userinfo.get("sub", ""), email)
            session_user["db_id"] = db_id
            session_user["subscription_active"] = billing.is_subscription_active(db_id)
        except Exception as exc:
            _log.exception("Error during hosted-mode user lookup for %s", email)
            return _login_template(request, error_message=f"Account setup error: {type(exc).__name__}: {exc}")

    request.session["user"] = session_user

    # Hosted mode without an active subscription → paywall (admins bypass).
    if _settings.hosted_mode and not session_user.get("subscription_active"):
        if not auth_service.is_admin(session_user.get("email", "")):
            return RedirectResponse(url=request.url_for("subscribe_page"), status_code=303)

    return RedirectResponse(url=request.url_for("workspace_page"), status_code=303)


@router.post("/auth/password", name="auth_password_login")
async def auth_password_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if auth_service.check_password(username, password):
        request.session["user"] = {
            "sub": f"local:{username}",
            "email": username,
            "name": username,
            "picture": None,
            "is_local": False,
        }
        return RedirectResponse(url=request.url_for("workspace_page"), status_code=303)

    return _login_template(request, error_message="Invalid username or password.")


@router.post("/logout", name="logout_action")
async def logout_action(request: Request):
    request.session.pop("user", None)
    if _settings.hosted_mode:
        # Hosted mode: noteeli.com clears the session (cookie is on .noteeli.com),
        # so just send the user there.
        return RedirectResponse(url=f"{_settings.portal_url}/logout", status_code=303)
    destination = request.url_for("workspace_page") if auth_service.is_local_request(request) else request.url_for("login_page")
    return RedirectResponse(url=destination, status_code=303)


# ---------------------------------------------------------------------------
# Google Drive OAuth – grant access to Drive (separate scope from login)
# ---------------------------------------------------------------------------

def _gdrive_callback_url(request: Request) -> str:
    """Return the canonical redirect URI for the GDrive OAuth callback.

    Prefers NOTEELI_APP_URL so the URI is stable regardless of proxy
    header behaviour.  Falls back to url_for when app_url is not set.
    """
    if _settings.app_url:
        return _settings.app_url.rstrip("/") + "/auth/gdrive/callback"
    return str(request.url_for("auth_gdrive_callback"))


@router.get("/auth/gdrive", name="auth_gdrive_start")
async def auth_gdrive_start(request: Request):
    user = auth_service.get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    from google_auth_oauthlib.flow import Flow

    callback_url = _gdrive_callback_url(request)
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": _settings.google_client_id,
                "client_secret": _settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [callback_url],
            }
        },
        scopes=["https://www.googleapis.com/auth/drive"],
        redirect_uri=callback_url,
    )
    authorization_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    request.session["gdrive_oauth_state"] = state
    # PKCE: store the code_verifier so we can reuse it in the callback,
    # otherwise Google rejects the token exchange with "Missing code verifier".
    if getattr(flow, "code_verifier", None):
        request.session["gdrive_code_verifier"] = flow.code_verifier
    return RedirectResponse(authorization_url)


@router.get("/auth/gdrive/callback", name="auth_gdrive_callback")
async def auth_gdrive_callback(request: Request):
    user = auth_service.get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    from google_auth_oauthlib.flow import Flow
    from app.domains.preferences.repository import PreferencesRepository

    state = request.session.get("gdrive_oauth_state")
    callback_url = _gdrive_callback_url(request)

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": _settings.google_client_id,
                "client_secret": _settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [callback_url],
            }
        },
        scopes=["https://www.googleapis.com/auth/drive"],
        state=state,
        redirect_uri=callback_url,
    )

    # Restore PKCE code_verifier saved when we initiated the flow.
    code_verifier = request.session.pop("gdrive_code_verifier", None)
    if code_verifier:
        flow.code_verifier = code_verifier

    # Reconstruct the authorization_response using the canonical public URL
    # so it matches the redirect_uri exactly regardless of what the reverse
    # proxy reports as request.url (which may be http://127.0.0.1:...).
    authorization_response = f"{callback_url}?{request.url.query}"

    import os as _os
    # Allow oauthlib to proceed even if the scheme appears as http (proxy strips TLS).
    _os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as exc:
        import logging as _log
        from urllib.parse import quote_plus
        _log.getLogger(__name__).exception("GDrive token exchange failed")
        # Try to extract the descriptive part of the error
        msg = str(exc) or type(exc).__name__
        return RedirectResponse(
            url=f"/?gdrive_error={quote_plus(msg[:200])}",
            status_code=303,
        )

    creds = flow.credentials

    creds_json = json.dumps({
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "client_id": _settings.google_client_id,
        "client_secret": _settings.google_client_secret,
    })

    repo = PreferencesRepository(_settings)
    repo.update_app_preferences(gdrive_credentials=creds_json)

    # Send the user to the folder picker so they can choose which Drive
    # folder will be the content root.
    return RedirectResponse(url="/auth/gdrive/folder", status_code=303)


@router.get("/auth/gdrive/folder", name="auth_gdrive_folder_picker")
async def auth_gdrive_folder_picker(request: Request):
    """Render a simple page that lists Drive folders and lets the user
    pick one as the workspace content root."""
    user = auth_service.get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    from app.domains.preferences.repository import PreferencesRepository
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    repo = PreferencesRepository(_settings)
    prefs = repo.get_app_preferences()
    creds_json = getattr(prefs, "gdrive_credentials", None)
    if not creds_json:
        return RedirectResponse(url="/auth/gdrive", status_code=303)

    creds_data = json.loads(creds_json)
    creds = Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_data.get("client_id"),
        client_secret=creds_data.get("client_secret"),
    )

    parent_id = request.query_params.get("parent", "root")
    try:
        service = build("drive", "v3", credentials=creds)
        results = service.files().list(
            q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=200,
            fields="files(id, name)",
            orderBy="name",
        ).execute()
        folders = results.get("files", [])
    except Exception as exc:
        return RedirectResponse(url=f"/?gdrive_error=List+folders+failed", status_code=303)

    rows = ""
    for f in folders:
        rows += (
            f'<li><a class="row" href="?parent={f["id"]}">📁 {f["name"]}</a>'
            f' <form method="post" action="/auth/gdrive/folder/select" style="display:inline">'
            f'<input type="hidden" name="folder_id" value="{f["id"]}"/>'
            f'<input type="hidden" name="folder_name" value="{f["name"]}"/>'
            f'<button class="pick" type="submit">Use this folder</button></form></li>'
        )

    parent_link = ""
    if parent_id != "root":
        parent_link = '<a class="back" href="?parent=root">← Back to My Drive</a>'

    html = f"""<!doctype html>
<html><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Pick a Drive folder — Noteeli</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"IBM Plex Sans",system-ui,sans-serif;background:#08111a;color:#edf3f8;padding:32px;max-width:700px;margin:0 auto}}
h1{{font-size:1.4rem;font-weight:700;margin-bottom:8px}}
.lead{{color:#9db0c2;margin-bottom:24px;font-size:.95rem}}
.back{{color:#f2b01d;text-decoration:none;font-size:.85rem;margin-bottom:16px;display:inline-block}}
ul{{list-style:none;display:flex;flex-direction:column;gap:8px}}
li{{display:flex;justify-content:space-between;align-items:center;background:#0d1824;border:1px solid rgba(140,188,234,.14);border-radius:8px;padding:12px 16px}}
li:hover{{border-color:rgba(140,188,234,.3)}}
.row{{color:#edf3f8;text-decoration:none;flex:1;font-size:.95rem}}
.row:hover{{color:#f2b01d}}
.pick{{background:#f2b01d;color:#08111a;border:0;padding:8px 14px;border-radius:6px;cursor:pointer;font-weight:600;font-size:.85rem}}
.pick:hover{{opacity:.88}}
.empty{{color:#9db0c2;text-align:center;padding:40px}}
</style></head>
<body>
<h1>Pick a Google Drive folder</h1>
<p class="lead">This folder will become your Noteeli workspace. You can change it later in Settings.</p>
{parent_link}
<ul>
{rows or '<li class="empty">No subfolders here. Click "Use this folder" on a folder above, or open one to look inside.</li>'}
</ul>
</body></html>"""
    return HTMLResponse(html)


@router.post("/auth/gdrive/folder/select", name="auth_gdrive_folder_select")
async def auth_gdrive_folder_select(request: Request):
    user = auth_service.get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    form = await request.form()
    folder_id = str(form.get("folder_id", "")).strip()
    folder_name = str(form.get("folder_name", "")).strip()
    if not folder_id:
        return RedirectResponse(url="/auth/gdrive/folder", status_code=303)

    from app.domains.preferences.repository import PreferencesRepository
    repo = PreferencesRepository(_settings)
    repo.update_app_preferences(
        gdrive_folder_id=folder_id,
        source_type="gdrive",
    )
    return RedirectResponse(url="/?gdrive_connected=1", status_code=303)


# ---------------------------------------------------------------------------
# SFTP folder picker — mirrors the Google Drive flow above.
# Reads stored SFTP creds from prefs (decrypted), browses remote dirs.
# ---------------------------------------------------------------------------

@router.get("/auth/sftp/folder", name="auth_sftp_folder_picker")
async def auth_sftp_folder_picker(request: Request):
    user = auth_service.get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    from app.domains.preferences.repository import PreferencesRepository
    repo = PreferencesRepository(_settings)
    prefs = repo.get_app_preferences()

    if not prefs.sftp_host:
        return RedirectResponse(url="/", status_code=303)

    parent = request.query_params.get("parent") or (prefs.sftp_path or "/")
    parent = parent.rstrip("/") or "/"

    # Password is persisted (encrypted) on /api/sftp/test success.
    password = prefs.sftp_password
    if not password:
        # Bounce back to settings — user needs to click Connect first.
        return RedirectResponse(url="/?sftp_password_required=1", status_code=303)

    # List subdirs
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                hostname=prefs.sftp_host,
                port=prefs.sftp_port,
                username=prefs.sftp_username,
                password=password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False,
            )
            sftp = ssh.open_sftp()
            try:
                entries = sftp.listdir_attr(parent)
            finally:
                sftp.close()
        finally:
            ssh.close()
    except Exception as exc:
        from urllib.parse import quote_plus
        return RedirectResponse(url=f"/?sftp_error={quote_plus(str(exc)[:200])}", status_code=303)

    import stat as _stat
    folders = sorted(
        [e.filename for e in entries if _stat.S_ISDIR(e.st_mode) and not e.filename.startswith(".")]
    )

    rows = ""
    for name in folders:
        sub_path = (parent + "/" + name).replace("//", "/") if parent != "/" else "/" + name
        rows += (
            f'<li><a class="row" href="?parent={sub_path}">📁 {name}</a>'
            f' <form method="post" action="/auth/sftp/folder/select" style="display:inline">'
            f'<input type="hidden" name="folder_path" value="{sub_path}"/>'
            f'<button class="pick" type="submit">Use this folder</button></form></li>'
        )

    # "Use this folder" for current parent dir as well
    use_current = (
        f'<form method="post" action="/auth/sftp/folder/select" style="margin:14px 0">'
        f'<input type="hidden" name="folder_path" value="{parent}"/>'
        f'<button class="pick pick-primary" type="submit">Use this folder ({parent})</button></form>'
    )

    parent_link = ""
    if parent != "/":
        up = parent.rsplit("/", 1)[0] or "/"
        parent_link = f'<a class="back" href="?parent={up}">← Up to {up}</a>'

    html = f"""<!doctype html>
<html><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Pick an SFTP folder — Noteeli</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"IBM Plex Sans",system-ui,sans-serif;background:#08111a;color:#edf3f8;padding:32px;max-width:700px;margin:0 auto}}
h1{{font-size:1.4rem;font-weight:700;margin-bottom:8px}}
.lead{{color:#9db0c2;margin-bottom:6px;font-size:.95rem}}
.path{{color:#f2b01d;font-family:"IBM Plex Mono",monospace;font-size:.85rem;margin-bottom:18px}}
.back{{color:#f2b01d;text-decoration:none;font-size:.85rem;margin-bottom:16px;display:inline-block}}
ul{{list-style:none;display:flex;flex-direction:column;gap:8px}}
li{{display:flex;justify-content:space-between;align-items:center;background:#0d1824;border:1px solid rgba(140,188,234,.14);border-radius:8px;padding:12px 16px}}
li:hover{{border-color:rgba(140,188,234,.3)}}
.row{{color:#edf3f8;text-decoration:none;flex:1;font-size:.95rem}}
.row:hover{{color:#f2b01d}}
.pick{{background:#f2b01d;color:#08111a;border:0;padding:8px 14px;border-radius:6px;cursor:pointer;font-weight:600;font-size:.85rem}}
.pick:hover{{opacity:.88}}
.pick-primary{{width:100%;padding:12px 16px;font-size:.95rem}}
.empty{{color:#9db0c2;text-align:center;padding:40px}}
</style></head>
<body>
<h1>Pick an SFTP folder</h1>
<p class="lead">This folder will become your Noteeli workspace.</p>
<p class="path">Current: {parent}</p>
{parent_link}
{use_current}
<ul>
{rows or '<li class="empty">No subfolders here. Click "Use this folder" above to pick the current one.</li>'}
</ul>
</body></html>"""
    return HTMLResponse(html)


@router.post("/auth/sftp/folder/select", name="auth_sftp_folder_select")
async def auth_sftp_folder_select(request: Request):
    user = auth_service.get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    form = await request.form()
    folder_path = str(form.get("folder_path", "")).strip()
    if not folder_path:
        return RedirectResponse(url="/auth/sftp/folder", status_code=303)

    from app.domains.preferences.repository import PreferencesRepository
    repo = PreferencesRepository(_settings)
    repo.update_app_preferences(
        sftp_path=folder_path,
        source_type="sftp",
    )
    # Clear session-stored password — it's done its job.
    # (User opted out of "remember", so password is gone for next session.)
    return RedirectResponse(url="/", status_code=303)
