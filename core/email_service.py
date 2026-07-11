from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class AuraEmailService:
    """
    Центральный сервис отправки HTML-писем AURA.
    """

    @staticmethod
    def send_email(
        subject,
        template,
        context,
        recipient,
    ):

        html_message = render_to_string(template, context)

        email = EmailMultiAlternatives(
            subject=subject,
            body="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )

        email.attach_alternative(html_message, "text/html")

        email.send()

    @classmethod
    def booking_created(cls, recipient, context):

        cls.send_email(
            subject="Заявка успешно создана",
            template="emails/booking_created.html",
            context=context,
            recipient=recipient,
        )

    @classmethod
    def booking_confirmed(cls, recipient, context):

        cls.send_email(
            subject="Запись подтверждена",
            template="emails/booking_confirmed.html",
            context=context,
            recipient=recipient,
        )

    @classmethod
    def booking_declined(cls, recipient, context):

        cls.send_email(
            subject="Запись отклонена",
            template="emails/booking_declined.html",
            context=context,
            recipient=recipient,
        )

    @classmethod
    def new_booking_master(cls, recipient, context):

        cls.send_email(
            subject="Новая заявка",
            template="emails/new_booking_master.html",
            context=context,
            recipient=recipient,
        )