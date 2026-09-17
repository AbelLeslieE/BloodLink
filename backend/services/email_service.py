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
import smtplib
import ssl
from email.message import EmailMessage
from html import escape
from datetime import datetime, timedelta, timezone


from backend.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)



def _smtp_is_configured() -> bool:
    """Return whether a complete authenticated SMTP configuration exists."""
    return bool(
        settings.smtp_host
        and settings.smtp_username
        and settings.smtp_password
    )


def _send_with_smtp(
    recipient_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> bool:
    """Send a transactional message through SMTP with STARTTLS.

    Gmail uses smtp.gmail.com on port 587 with an App Password. The provider
    password remains server-side in Render's encrypted environment settings.
    """
    message = EmailMessage()
    message["From"] = settings.smtp_from or settings.smtp_username
    message["To"] = recipient_email
    message["Subject"] = subject
    message.set_content(
        text_body
        or "BloodLink sent you a transactional notification. Please view it in an HTML-capable email client."
    )
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as client:
            client.ehlo()
            client.starttls(context=ssl.create_default_context())
            client.ehlo()
            client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)
        logger.info("Donation request email accepted by SMTP")
        return True
    except Exception:
        logger.warning("SMTP email delivery failed")
        return False


def _send_with_resend(
    recipient_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> bool:
    """Send a transactional message through Resend when SMTP is unavailable."""
    if not settings.resend_api_key or not settings.email_from:
        return False

    resend.api_key = settings.resend_api_key
    try:
        payload = {
            "from": settings.email_from,
            "to": [recipient_email],
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            payload["text"] = text_body
        resend.Emails.send(payload)
        logger.info("Donation request email accepted by Resend")
        return True
    except Exception:
        logger.warning("Resend email delivery failed")
        return False
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
    text_body: str | None = None,
) -> bool:
    """
    Send an HTML email through the provider supported by the environment.

    Render blocks outbound SMTP on common mail ports, so production services use
    its HTTPS-based Resend integration and never wait on a doomed SMTP attempt.
    Local installations can use SMTP with Resend as a fallback.
    """
    if settings.on_render:
        if _send_with_resend(recipient_email, subject, html_body, text_body):
            return True
        logger.error("Resend is not configured or could not deliver the email")
        return False
    if _smtp_is_configured() and _send_with_smtp(
        recipient_email,
        subject,
        html_body,
        text_body,
    ):
        return True
    if _send_with_resend(recipient_email, subject, html_body, text_body):
        return True
    logger.error("No working email provider is configured")
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

    blood_group = " ".join(str(blood_request.blood_group).split())
    hospital_name = " ".join(str(blood_request.hospital_name).split())
    return f"Urgent: {blood_group} blood needed at {hospital_name}"


def _human_request_date(value) -> str:
    """Return a clear, locale-neutral date for donor notifications."""
    if isinstance(value, datetime):
        return value.strftime("%d %B %Y")
    if hasattr(value, "strftime"):
        return value.strftime("%d %B %Y")
    try:
        return datetime.fromisoformat(str(value)).strftime("%d %B %Y")
    except (TypeError, ValueError):
        return str(value)


def build_text_email(
    donor,
    blood_request,
    accept_url: str,
    decline_url: str,
) -> str:
    """Build the accessible plain-text alternative for a donation request."""
    required_date = _human_request_date(blood_request.required_date)
    return f"""BLOODLINK — URGENT BLOOD REQUEST

Hello {donor.full_name},

Your blood group is compatible with an urgent request. If you are healthy, eligible, and available, please review the details below and respond.

Blood group: {blood_request.blood_group}
Units required: {blood_request.units_required}
Hospital: {blood_request.hospital_name}
Location: {blood_request.hospital_location}
Required by: {required_date}
Priority: {blood_request.priority}

Accept this donation request:
{accept_url}

Unable to donate? Decline this request:
{decline_url}

These response links are personal to you. Please do not forward this email.

Thank you for being part of the BloodLink donor network.
"""


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
    units_required = escape(str(blood_request.units_required))
    hospital_name = escape(str(blood_request.hospital_name))
    hospital_location = escape(str(blood_request.hospital_location))
    required_date = escape(_human_request_date(blood_request.required_date))
    priority = escape(str(blood_request.priority))
    safe_accept_url = escape(accept_url, quote=True)
    safe_decline_url = escape(decline_url, quote=True)

    return f"""
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light">
  <meta name="supported-color-schemes" content="light">
  <title>Urgent {blood_group} blood request for {hospital_name}</title>
  <style>
    @media only screen and (max-width: 620px) {{
      .email-shell {{ width:100% !important; }}
      .mobile-pad {{ padding-left:20px !important; padding-right:20px !important; }}
      .hero-title {{ font-size:31px !important; line-height:36px !important; }}
      .summary-cell {{ display:block !important; width:100% !important; padding:0 0 12px !important; }}
      .action-cell {{ display:block !important; width:100% !important; padding:0 0 10px !important; }}
      .action-link {{ display:block !important; }}
      .detail-label {{ width:38% !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#f3f6fb;font-family:Arial,Helvetica,sans-serif;color:#17233d;">
  <div lang="en" dir="ltr" style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
    {blood_group} blood is needed at {hospital_name}. Review the request and respond.
  </div>
  <table role="presentation" lang="en" dir="ltr" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;background-color:#f3f6fb;">
    <tr>
      <td align="center" style="padding:38px 14px;">
        <table role="presentation" class="email-shell" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;background-color:#ffffff;border:1px solid #e3e9f2;border-radius:24px;overflow:hidden;box-shadow:0 18px 50px rgba(22,38,72,.13);">
          <tr>
            <td class="mobile-pad" style="padding:28px 38px 26px;background-color:#0c2447;border-bottom:5px solid #c5163d;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td valign="middle">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td align="center" valign="middle" width="44" height="44" style="width:44px;height:44px;border-radius:13px;background-color:#c5163d;color:#ffffff;font-size:21px;font-weight:800;">&#9679;</td>
                        <td style="padding-left:12px;color:#ffffff;">
                          <div style="font-size:22px;line-height:26px;font-weight:800;letter-spacing:-.4px;">BloodLink</div>
                          <div style="padding-top:2px;color:#bdcbe0;font-size:11px;line-height:15px;letter-spacing:1px;text-transform:uppercase;">Pranadan donor network</div>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td align="right" valign="middle">
                    <span style="display:inline-block;padding:7px 11px;border:1px solid #ff91a8;border-radius:999px;background-color:#8e1230;color:#ffffff;font-size:11px;line-height:14px;font-weight:800;letter-spacing:1px;text-transform:uppercase;">Urgent donor alert</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td class="mobile-pad" style="padding:38px 38px 16px;">
              <p style="margin:0 0 10px;color:#c5163d;font-size:12px;line-height:18px;font-weight:800;letter-spacing:1.6px;text-transform:uppercase;">A compatible request needs your response</p>
              <h1 class="hero-title" style="margin:0;color:#102542;font-size:38px;line-height:43px;font-weight:800;letter-spacing:-1.2px;">{blood_group} blood is needed</h1>
              <p style="margin:14px 0 0;color:#5f6e84;font-size:16px;line-height:25px;">Hello <strong style="color:#1c2b43;">{donor_name}</strong>, your blood group matches an urgent request from <strong style="color:#1c2b43;">{hospital_name}</strong>.</p>
            </td>
          </tr>

          <tr>
            <td class="mobile-pad" style="padding:14px 38px 8px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="summary-cell" width="50%" style="width:50%;padding-right:7px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#fff1f4;border:1px solid #f5c8d2;border-radius:16px;">
                      <tr>
                        <td style="padding:20px 18px;">
                          <div style="color:#9f1239;font-size:11px;line-height:16px;font-weight:800;letter-spacing:1px;text-transform:uppercase;">Blood group</div>
                          <div style="padding-top:5px;color:#b31337;font-size:31px;line-height:34px;font-weight:800;">{blood_group}</div>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td class="summary-cell" width="50%" style="width:50%;padding-left:7px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#edf5ff;border:1px solid #cddff8;border-radius:16px;">
                      <tr>
                        <td style="padding:20px 18px;">
                          <div style="color:#24528a;font-size:11px;line-height:16px;font-weight:800;letter-spacing:1px;text-transform:uppercase;">Units required</div>
                          <div style="padding-top:5px;color:#123b70;font-size:31px;line-height:34px;font-weight:800;">{units_required}</div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td class="mobile-pad" style="padding:18px 38px 12px;">
              <h2 style="margin:0 0 12px;color:#1a2b45;font-size:17px;line-height:23px;font-weight:800;">Request details</h2>
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;border:1px solid #e4e9f1;border-radius:16px;border-collapse:separate;overflow:hidden;">
                <tr>
                  <th scope="row" class="detail-label" width="34%" align="left" style="width:34%;padding:14px 16px;background-color:#f8fafc;border-bottom:1px solid #e8edf4;color:#66758b;font-size:13px;line-height:19px;font-weight:700;">Hospital</th>
                  <td style="padding:14px 16px;border-bottom:1px solid #e8edf4;color:#1f2d43;font-size:14px;line-height:19px;font-weight:700;">{hospital_name}</td>
                </tr>
                <tr>
                  <th scope="row" class="detail-label" align="left" style="padding:14px 16px;background-color:#f8fafc;border-bottom:1px solid #e8edf4;color:#66758b;font-size:13px;line-height:19px;font-weight:700;">Location</th>
                  <td style="padding:14px 16px;border-bottom:1px solid #e8edf4;color:#1f2d43;font-size:14px;line-height:19px;">{hospital_location}</td>
                </tr>
                <tr>
                  <th scope="row" class="detail-label" align="left" style="padding:14px 16px;background-color:#f8fafc;border-bottom:1px solid #e8edf4;color:#66758b;font-size:13px;line-height:19px;font-weight:700;">Required by</th>
                  <td style="padding:14px 16px;border-bottom:1px solid #e8edf4;color:#1f2d43;font-size:14px;line-height:19px;">{required_date}</td>
                </tr>
                <tr>
                  <th scope="row" class="detail-label" align="left" style="padding:14px 16px;background-color:#f8fafc;color:#66758b;font-size:13px;line-height:19px;font-weight:700;">Priority</th>
                  <td style="padding:14px 16px;color:#1f2d43;font-size:14px;line-height:19px;"><span style="display:inline-block;padding:5px 9px;border-radius:999px;background-color:#fff0e0;color:#9a4300;font-size:12px;font-weight:800;text-transform:uppercase;">{priority}</span></td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td class="mobile-pad" style="padding:24px 38px 12px;">
              <h2 style="margin:0;color:#172842;font-size:20px;line-height:26px;font-weight:800;text-align:center;">Are you available to donate?</h2>
              <p style="margin:8px 0 20px;color:#6a788d;font-size:14px;line-height:21px;text-align:center;">A quick response helps the hospital coordinate care sooner.</p>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="action-cell" width="62%" style="width:62%;padding-right:6px;">
                    <a class="action-link" href="{safe_accept_url}" style="display:block;padding:15px 18px;border:1px solid #047857;border-radius:12px;background-color:#047857;color:#ffffff;font-size:15px;line-height:20px;font-weight:800;text-align:center;text-decoration:none;">Yes, I can donate&nbsp; &rarr;</a>
                  </td>
                  <td class="action-cell" width="38%" style="width:38%;padding-left:6px;">
                    <a class="action-link" href="{safe_decline_url}" style="display:block;padding:15px 18px;border:1px solid #d8dee8;border-radius:12px;background-color:#ffffff;color:#5e6879;font-size:15px;line-height:20px;font-weight:700;text-align:center;text-decoration:none;">I can&rsquo;t donate</a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td class="mobile-pad" style="padding:12px 38px 34px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f7f9fc;border-radius:12px;">
                <tr>
                  <td width="32" valign="top" style="padding:15px 0 15px 15px;color:#51657e;font-size:16px;">&#128737;</td>
                  <td style="padding:14px 15px 14px 8px;color:#627188;font-size:12px;line-height:18px;">Only accept if you are healthy, eligible, and available. These response links are personal to you&mdash;please do not forward this email.</td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td class="mobile-pad" align="center" style="padding:25px 38px;background-color:#0c2447;border-top:1px solid #19385f;">
              <p style="margin:0;color:#ffffff;font-size:14px;line-height:20px;font-weight:800;">Thank you for being part of BloodLink.</p>
              <p style="margin:7px 0 0;color:#aebed3;font-size:11px;line-height:17px;">Pranadan donor network &middot; Sahrdaya College of Engineering &amp; Technology</p>
              <p style="margin:10px 0 0;color:#8195b0;font-size:10px;line-height:16px;">This automated message was sent because your donor profile matched this request.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
