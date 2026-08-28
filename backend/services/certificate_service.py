"""Certificate issuance and PDF rendering for confirmed donations."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from backend.database.models import DonationCertificate, DonationHistory


def ensure_certificate(db: Session, donation: DonationHistory) -> DonationCertificate:
    """Create the one certificate owned by a confirmed donation, if needed."""
    if donation.certificate is not None:
        return donation.certificate
    certificate = DonationCertificate(
        donation_history_id=donation.id,
        certificate_number=f"BL-{donation.donation_date:%Y%m%d}-{donation.id:06d}",
    )
    db.add(certificate)
    db.flush()
    return certificate


def _centered(page: canvas.Canvas, text: str, y: float, font: str, size: int) -> None:
    page.setFont(font, size)
    page.drawString((A4[0] - stringWidth(text, font, size)) / 2, y, text)


def render_certificate(donation: DonationHistory, certificate: DonationCertificate) -> bytes:
    """Render a polished, one-page PDF certificate into memory."""
    donor = donation.donor
    buffer = BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4, pageCompression=1)
    width, height = A4
    page.setTitle(f"BloodLink Donation Certificate {certificate.certificate_number}")
    page.setAuthor("BloodLink")
    page.setStrokeColor(colors.HexColor("#B91C2C"))
    page.setLineWidth(2.5)
    page.rect(14 * mm, 14 * mm, width - 28 * mm, height - 28 * mm)
    page.setStrokeColor(colors.HexColor("#F2B84B"))
    page.setLineWidth(.8)
    page.rect(19 * mm, 19 * mm, width - 38 * mm, height - 38 * mm)
    page.setFillColor(colors.HexColor("#B91C2C"))
    _centered(page, "BLOODLINK", height - 46 * mm, "Helvetica-Bold", 23)
    page.setFillColor(colors.HexColor("#172033"))
    _centered(page, "Certificate of Appreciation", height - 62 * mm, "Helvetica-Bold", 25)
    _centered(page, "This certificate is proudly presented to", height - 82 * mm, "Helvetica", 13)
    page.setFillColor(colors.HexColor("#B91C2C"))
    _centered(page, donor.full_name, height - 104 * mm, "Helvetica-Bold", 27)
    page.setStrokeColor(colors.HexColor("#F2B84B"))
    page.line(55 * mm, height - 109 * mm, width - 55 * mm, height - 109 * mm)
    page.setFillColor(colors.HexColor("#172033"))
    _centered(page, "In recognition of their confirmed voluntary blood donation", height - 126 * mm, "Helvetica", 12)
    _centered(page, f"at {donation.hospital_name}", height - 136 * mm, "Helvetica-Bold", 12)
    _centered(page, f"Donation date: {donation.donation_date:%d %B %Y}", height - 151 * mm, "Helvetica", 11)
    _centered(page, f"Reward points awarded: {donation.points_awarded}", height - 161 * mm, "Helvetica", 11)
    page.setFillColor(colors.HexColor("#65718A"))
    _centered(page, "Your generosity helps save lives. Thank you for being a BloodLink donor.", height - 181 * mm, "Helvetica-Oblique", 10)
    page.setFillColor(colors.HexColor("#172033"))
    page.setFont("Helvetica", 8.5)
    page.drawString(28 * mm, 32 * mm, f"Certificate no. {certificate.certificate_number}")
    page.drawRightString(width - 28 * mm, 32 * mm, f"Issued {certificate.issued_at:%d %B %Y}")
    page.showPage()
    page.save()
    return buffer.getvalue()
