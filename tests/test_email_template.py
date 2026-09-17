from datetime import date
from types import SimpleNamespace

from backend.services.email_service import (
    build_email_subject,
    build_html_email,
    build_text_email,
)


def _request(**overrides):
    values = {
        "blood_group": "A+",
        "units_required": 3,
        "hospital_name": "Little Flower Hospital",
        "hospital_location": "Angamaly, Kerala",
        "required_date": date(2026, 8, 30),
        "priority": "Urgent",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_donation_email_has_accessible_responsive_structure():
    html = build_html_email(
        donor=SimpleNamespace(full_name="Abel Leslie"),
        blood_request=_request(),
        accept_url="https://bloodlink.example/email/accept/token",
        decline_url="https://bloodlink.example/email/decline/token",
    )

    assert '<html lang="en" dir="ltr">' in html
    assert "<title>Urgent A+ blood request for Little Flower Hospital</title>" in html
    assert 'role="presentation"' in html
    assert '<h1 class="hero-title"' in html
    assert "Yes, I can donate" in html
    assert "I can&rsquo;t donate" in html
    assert "@media only screen and (max-width: 620px)" in html


def test_donation_email_escapes_dynamic_html_and_urls():
    html = build_html_email(
        donor=SimpleNamespace(full_name='<script>alert("x")</script>'),
        blood_request=_request(hospital_name="Care & Hope <Hospital>"),
        accept_url="https://bloodlink.example/accept?one=1&two=2",
        decline_url="https://bloodlink.example/decline?one=1&two=2",
    )

    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
    assert "Care &amp; Hope &lt;Hospital&gt;" in html
    assert "accept?one=1&amp;two=2" in html
    assert "decline?one=1&amp;two=2" in html


def test_donation_email_plain_text_and_subject_are_actionable():
    request = _request()
    accept_url = "https://bloodlink.example/email/accept/token"
    decline_url = "https://bloodlink.example/email/decline/token"

    text = build_text_email(
        donor=SimpleNamespace(full_name="Abel Leslie"),
        blood_request=request,
        accept_url=accept_url,
        decline_url=decline_url,
    )

    assert build_email_subject(request) == "Urgent: A+ blood needed at Little Flower Hospital"
    assert "Required by: 30 August 2026" in text
    assert accept_url in text
    assert decline_url in text
    assert "Please do not forward this email." in text
