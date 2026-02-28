"""Email notification service using SendGrid.

Sends lead alerts to the business owner when a new quote request comes in.
Falls back to logging if SendGrid is not configured.
"""

import logging
from datetime import datetime, timezone

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _build_lead_html(
    first_name: str,
    last_name: str,
    phone: str,
    email: str,
    address: str,
    city: str,
    state: str,
    zip_code: str,
) -> str:
    """Build a professional HTML email for a new lead notification."""
    now = datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")
    return f"""\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5;padding:24px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background-color:#4338ca;padding:24px 32px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:bold;">
                New Solar Quote Request
              </h1>
              <p style="margin:8px 0 0;color:#c7d2fe;font-size:14px;">
                {now}
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 20px;font-size:16px;color:#374151;">
                A new customer has submitted a quote request through the Solar Command website.
              </p>

              <!-- Lead Details Table -->
              <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
                <tr style="background-color:#f9fafb;">
                  <td style="padding:12px 16px;font-size:14px;color:#6b7280;font-weight:bold;width:120px;border-bottom:1px solid #e5e7eb;">
                    Name
                  </td>
                  <td style="padding:12px 16px;font-size:16px;color:#111827;font-weight:600;border-bottom:1px solid #e5e7eb;">
                    {first_name} {last_name}
                  </td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-size:14px;color:#6b7280;font-weight:bold;border-bottom:1px solid #e5e7eb;">
                    Phone
                  </td>
                  <td style="padding:12px 16px;font-size:16px;color:#111827;border-bottom:1px solid #e5e7eb;">
                    <a href="tel:{phone}" style="color:#4338ca;text-decoration:none;">{phone}</a>
                  </td>
                </tr>
                <tr style="background-color:#f9fafb;">
                  <td style="padding:12px 16px;font-size:14px;color:#6b7280;font-weight:bold;border-bottom:1px solid #e5e7eb;">
                    Email
                  </td>
                  <td style="padding:12px 16px;font-size:16px;color:#111827;border-bottom:1px solid #e5e7eb;">
                    <a href="mailto:{email}" style="color:#4338ca;text-decoration:none;">{email}</a>
                  </td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-size:14px;color:#6b7280;font-weight:bold;">
                    Address
                  </td>
                  <td style="padding:12px 16px;font-size:16px;color:#111827;">
                    {address}<br>{city}, {state} {zip_code}
                  </td>
                </tr>
              </table>

              <!-- CTA -->
              <div style="margin-top:24px;text-align:center;">
                <p style="margin:0 0 8px;font-size:14px;color:#6b7280;">
                  Follow up with this lead as soon as possible.
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f9fafb;padding:16px 32px;text-align:center;border-top:1px solid #e5e7eb;">
              <p style="margin:0;font-size:12px;color:#9ca3af;">
                Solar Command &mdash; Automated Lead Notification
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


async def send_new_lead_notification(
    first_name: str,
    last_name: str,
    phone: str,
    email: str,
    address: str,
    city: str,
    state: str,
    zip_code: str,
) -> bool:
    """Send a new-lead email notification to the business owner.

    Returns True if sent successfully, False otherwise.
    Non-blocking — failures are logged but do not raise exceptions.
    """
    settings = get_settings()

    if not settings.sendgrid_api_key:
        logger.warning(
            "SendGrid API key not configured — skipping email notification for %s %s",
            first_name,
            last_name,
        )
        return False

    if not settings.notification_email:
        logger.warning(
            "NOTIFICATION_EMAIL not configured — skipping email notification for %s %s",
            first_name,
            last_name,
        )
        return False

    try:
        html_body = _build_lead_html(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
        )

        message = Mail(
            from_email=settings.sendgrid_from_email,
            to_emails=settings.notification_email,
            subject=f"New Solar Quote Request - {first_name} {last_name}",
            html_content=html_body,
        )

        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            logger.info(
                "Lead notification email sent for %s %s to %s",
                first_name,
                last_name,
                settings.notification_email,
            )
            return True
        else:
            logger.error(
                "SendGrid returned status %s for lead %s %s",
                response.status_code,
                first_name,
                last_name,
            )
            return False

    except Exception:
        logger.exception(
            "Failed to send lead notification email for %s %s",
            first_name,
            last_name,
        )
        return False
