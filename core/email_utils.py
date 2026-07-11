from __future__ import annotations

from html import escape
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def _default_html(subject: str, message: str) -> str:
    body = escape(message).replace('\n', '<br>')
    return f"""
    <div style="margin:0;padding:0;background:#f5f7fb;font-family:Arial,sans-serif;">
      <div style="max-width:640px;margin:0 auto;padding:32px 16px;">
        <div style="background:#ffffff;border:1px solid #e8ecf4;border-radius:22px;overflow:hidden;box-shadow:0 18px 40px rgba(20,30,60,.08)">
          <div style="padding:24px 28px;background:linear-gradient(135deg,#4f7cff,#6e87ff);color:#fff;">
            <div style="font-size:12px;letter-spacing:.22em;text-transform:uppercase;font-weight:700;opacity:.9;">AURA // LINK</div>
            <div style="font-size:24px;line-height:1.2;font-weight:800;margin-top:10px;">{escape(subject)}</div>
          </div>
          <div style="padding:28px;color:#1f2a44;font-size:15px;line-height:1.7;">
            {body}
            <div style="margin-top:24px;padding-top:18px;border-top:1px solid #eef1f7;color:#6b7280;font-size:13px;">
              Это автоматическое сообщение сервиса AURA // LINK.
            </div>
          </div>
        </div>
      </div>
    </div>
    """


def send_booking_email(email, subject, message, *, html_message=None, reply_to=None):
    email = (email or '').strip()
    if not email:
        return False

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@aura-link.local')
    msg = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=from_email,
        to=[email],
        reply_to=reply_to or None,
    )
    msg.attach_alternative(html_message or _default_html(subject, message), 'text/html')

    try:
        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception('Failed to send booking email to %s', email)
        return False
