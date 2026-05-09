"""Admin panel — accessible only to emails listed in NOTEELI_ADMIN_EMAILS."""
from __future__ import annotations

import sqlite3
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.config import get_settings
from app.domains.auth.service import AuthService

router = APIRouter(tags=["admin"])


def _require_admin(request: Request) -> dict:
    settings = get_settings()
    auth = AuthService(settings)
    user = auth.get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Login required.")
    if not auth.is_admin(user.get("email", "")):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


def _get_users_with_subs(db_path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT
            u.id,
            u.email,
            u.paddle_customer_id,
            u.created_at,
            s.status        AS sub_status,
            s.current_period_end,
            s.updated_at    AS sub_updated
        FROM users u
        LEFT JOIN subscriptions s ON s.user_id = u.id
        ORDER BY u.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/admin", name="admin_page")
async def admin_page(request: Request):
    user = _require_admin(request)
    settings = get_settings()

    users = _get_users_with_subs(settings.database_path)

    active   = sum(1 for u in users if u["sub_status"] in ("active", "trialing"))
    inactive = len(users) - active

    rows_html = ""
    for u in users:
        status = u["sub_status"] or "—"
        badge = (
            '<span style="color:#4ade80">● active</span>'   if status in ("active", "trialing")
            else '<span style="color:#f87171">● inactive</span>' if status not in ("—",)
            else '<span style="color:#9ca3af">—</span>'
        )
        rows_html += f"""
        <tr>
          <td>{u['id']}</td>
          <td>{u['email']}</td>
          <td>{badge}</td>
          <td>{u['current_period_end'] or '—'}</td>
          <td>{u['paddle_customer_id'] or '—'}</td>
          <td>{u['created_at'][:10] if u['created_at'] else '—'}</td>
        </tr>"""

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Noteeli Admin</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:"IBM Plex Sans",system-ui,sans-serif;background:#08111a;color:#edf3f8;padding:32px}}
    h1{{font-size:1.4rem;font-weight:700;margin-bottom:24px}}
    .stats{{display:flex;gap:16px;margin-bottom:32px}}
    .stat{{background:#0d1824;border:1px solid rgba(140,188,234,.14);border-radius:10px;padding:16px 24px}}
    .stat-n{{font-size:2rem;font-weight:700;color:#f2b01d}}
    .stat-l{{font-size:.85rem;color:#9db0c2;margin-top:4px}}
    table{{width:100%;border-collapse:collapse;font-size:.9rem}}
    th{{text-align:left;padding:10px 12px;background:#0d1824;color:#9db0c2;font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid rgba(140,188,234,.14)}}
    td{{padding:10px 12px;border-bottom:1px solid rgba(140,188,234,.07)}}
    tr:hover td{{background:rgba(140,188,234,.04)}}
    .back{{display:inline-block;margin-bottom:20px;color:#9db0c2;font-size:.9rem;text-decoration:none}}
    .back:hover{{color:#edf3f8}}
  </style>
</head>
<body>
  <a class="back" href="/">← Back to workspace</a>
  <h1>Admin — Noteeli</h1>
  <div class="stats">
    <div class="stat"><div class="stat-n">{len(users)}</div><div class="stat-l">Total users</div></div>
    <div class="stat"><div class="stat-n" style="color:#4ade80">{active}</div><div class="stat-l">Active subscriptions</div></div>
    <div class="stat"><div class="stat-n" style="color:#9db0c2">{inactive}</div><div class="stat-l">No subscription</div></div>
  </div>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>Email</th><th>Subscription</th><th>Renews</th><th>Paddle customer</th><th>Joined</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</body>
</html>"""
    return HTMLResponse(html)
