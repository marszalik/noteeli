import json

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.templates import render_template
from app.domains.auth.service import AuthService


router = APIRouter(tags=["auth"])
_settings = get_settings()
auth_service = AuthService(_settings)


@router.get("/login", name="login_page")
async def login_page(request: Request):
    if auth_service.get_current_user(request):
        return RedirectResponse(url=request.url_for("workspace_page"), status_code=303)

    return render_template(
        "domains/auth/views/login.mako",
        request,
        google_configured=auth_service.google_is_configured(),
        error_message=None,
    )


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
    client = auth_service.get_google_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured.")

    try:
        token = await client.authorize_access_token(request)
        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo = await client.parse_id_token(request, token)
    except OAuthError as exc:
        return render_template(
            "domains/auth/views/login.mako",
            request,
            google_configured=True,
            error_message=f"Logowanie nie powiodlo sie: {exc.error}",
        )

    request.session["user"] = {
        "sub": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
        "is_local": False,
    }
    return RedirectResponse(url=request.url_for("workspace_page"), status_code=303)


@router.post("/logout", name="logout_action")
async def logout_action(request: Request):
    request.session.pop("user", None)
    destination = request.url_for("workspace_page") if auth_service.is_local_request(request) else request.url_for("login_page")
    return RedirectResponse(url=destination, status_code=303)


# ---------------------------------------------------------------------------
# Google Drive OAuth – grant access to Drive (separate scope from login)
# ---------------------------------------------------------------------------

@router.get("/auth/gdrive", name="auth_gdrive_start")
async def auth_gdrive_start(request: Request):
    user = auth_service.get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": _settings.google_client_id,
                "client_secret": _settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [str(request.url_for("auth_gdrive_callback"))],
            }
        },
        scopes=["https://www.googleapis.com/auth/drive"],
        redirect_uri=str(request.url_for("auth_gdrive_callback")),
    )
    authorization_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    request.session["gdrive_oauth_state"] = state
    return RedirectResponse(authorization_url)


@router.get("/auth/gdrive/callback", name="auth_gdrive_callback")
async def auth_gdrive_callback(request: Request):
    user = auth_service.get_current_user(request)
    if user is None:
        return RedirectResponse(url=request.url_for("login_page"), status_code=303)

    from google_auth_oauthlib.flow import Flow
    from app.domains.preferences.repository import PreferencesRepository

    state = request.session.get("gdrive_oauth_state")
    callback_url = str(request.url_for("auth_gdrive_callback"))

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

    flow.fetch_token(authorization_response=str(request.url))
    creds = flow.credentials

    creds_json = json.dumps({
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "client_id": _settings.google_client_id,
        "client_secret": _settings.google_client_secret,
    })

    repo = PreferencesRepository(_settings)
    repo.update_app_preferences(gdrive_credentials=creds_json)

    return RedirectResponse(url="/?gdrive_connected=1", status_code=303)
