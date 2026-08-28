"""
==========================================================
Email Service
==========================================================

Handles:

• Email token generation
• HTML email creation
• SMTP email delivery
"""

from __future__ import annotations

import secrets
import resend
import logging
from html import escape
from datetime import datetime, timedelta, timezone


from backend.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key
# ==========================================================
# TOKEN GENERATION
# ==========================================================

def generate_email_token() -> str:
    """
    Generate a secure random email token.
    """
    return secrets.token_urlsafe(48)


# ==========================================================
# TOKEN EXPIRY
# ==========================================================

def generate_expiry_time(hours: int = 24) -> datetime:
    """
    Tokens expire after the specified number of hours.
    """
    return datetime.now(timezone.utc) + timedelta(hours=hours)


# ==========================================================
# SEND EMAIL
# ==========================================================

# ==========================================================
# SEND EMAIL
# ==========================================================

def send_email(
    recipient_email: str,
    subject: str,
    html_body: str,
) -> bool:
    """
    Send an HTML email using Resend.
    """

    try:

        response = resend.Emails.send(
            {
                "from": settings.email_from,
                "to": [recipient_email],
                "subject": subject,
                "html": html_body,
            }
        )

        logger.info("Donation request email accepted by provider for %s", recipient_email)

        return True

    except Exception:
        logger.exception("Donation request email delivery failed for %s", recipient_email)

        return False
# ==========================================================
# EMAIL SUBJECT
# ==========================================================

def build_email_subject(
    blood_request,
) -> str:
    """
    Build the subject line for a blood request email.
    """

    return (
        f"🩸 Urgent Blood Request - "
        f"{blood_request.blood_group} Needed"
    )


# ==========================================================
# HTML EMAIL
# ==========================================================

def build_html_email(
    donor,
    blood_request,
    accept_url: str,
    decline_url: str,
) -> str:
    """
    Build the BloodLink HTML email.
    """

    donor_name = escape(str(donor.full_name))
    blood_group = escape(str(blood_request.blood_group))
    hospital_name = escape(str(blood_request.hospital_name))
    hospital_location = escape(str(blood_request.hospital_location))
    required_date = escape(str(blood_request.required_date))
    priority = escape(str(blood_request.priority))

    return f"""
<!DOCTYPE html>
<html>

<head>
<meta charset="UTF-8">

<style>

body{{
    margin:0;
    padding:0;
    background:#f5f7fb;
    font-family:Arial,Helvetica,sans-serif;
}}

.wrapper{{
    width:100%;
    padding:40px 0;
}}

.container{{
    max-width:650px;
    margin:auto;
    background:#ffffff;
    border-radius:14px;
    overflow:hidden;
    box-shadow:0 10px 30px rgba(0,0,0,.15);
}}

.header{{
    background:#d32f2f;
    color:white;
    text-align:center;
    padding:30px;
}}

.header h1{{
    margin:0;
}}

.content{{
    padding:35px;
    color:#333;
}}

.info-table{{
    width:100%;
    border-collapse:collapse;
}}

.info-table td{{
    padding:10px;
    border-bottom:1px solid #eeeeee;
}}

.button-area{{
    text-align:center;
    margin-top:35px;
}}

.accept-btn{{
    background:#2e7d32;
    color:white !important;
    text-decoration:none;
    padding:14px 28px;
    border-radius:8px;
    margin-right:10px;
    display:inline-block;
    font-weight:bold;
}}

.decline-btn{{
    background:#c62828;
    color:white !important;
    text-decoration:none;
    padding:14px 28px;
    border-radius:8px;
    display:inline-block;
    font-weight:bold;
}}

.footer{{
    background:#f5f5f5;
    text-align:center;
    padding:25px;
    color:#666;
    font-size:13px;
}}

</style>

</head>

<body>

<div class="wrapper">

<div class="container">

<div class="header">

<h1>🩸 BloodLink</h1>

<p>Emergency Blood Donation Request</p>

</div>

<div class="content">

<p>Hello <strong>{donor_name}</strong>,</p>

<p>
A compatible blood donation request has been found.
If you are available, please respond using one of the buttons below.
</p>

<table class="info-table">

<tr>
<td><strong>Blood Group</strong></td>
<td>{blood_group}</td>
</tr>

<tr>
<td><strong>Units Required</strong></td>
<td>{blood_request.units_required}</td>
</tr>

<tr>
<td><strong>Hospital</strong></td>
<td>{hospital_name}</td>
</tr>

<tr>
<td><strong>Location</strong></td>
<td>{hospital_location}</td>
</tr>

<tr>
<td><strong>Required Date</strong></td>
<td>{required_date}</td>
</tr>

<tr>
<td><strong>Priority</strong></td>
<td>{priority}</td>
</tr>

</table>

<div class="button-area">

<a class="accept-btn" href="{accept_url}">
✅ Accept Donation
</a>

<a class="decline-btn" href="{decline_url}">
❌ Decline
</a>

</div>

</div>

<div class="footer">

<p>
This email was sent automatically by the BloodLink Blood Donation Management System.
</p>

<p>
Please do not reply to this email.
</p>

</div>

</div>

</div>

</body>

</html>
"""
