from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter(prefix="")


@router.get("/login-link", response_class=HTMLResponse)
async def login_link_redirect(token: str):
    return f"""
    <html>
        <head>
            <meta http-equiv="refresh" content="0; URL=wonderspaced://open/passwordless-login?token={token}" />
        </head>
        <body>
            <p>Redirecting...</p>
            <script>
                window.location.href = "wonderspaced://open/passwordless-login?token={token}";
            </script>
        </body>
    </html>
    """
    
    
@router.get("/verify-email-link", response_class=HTMLResponse)
async def verify_email_redirect(token: str):
    return f"""
    <html>
        <head>
            <meta http-equiv="refresh" content="0; URL=wonderspaced://open/verify-email?token={token}" />
        </head>
        <body>
            <p>Redirecting...</p>
            <script>
                window.location.href = "wonderspaced://open/verify-email?token={token}";
            </script>
        </body>
    </html>
    """