"""Service for sending emails using FastAPI-Mail."""

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from app.core.config import settings
from app.core.errors import EmailSendingError

# BASE_DIR = Path(__file__).resolve().parent.parent


mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    SUPPRESS_SEND=int(settings.suppress_send),
    # TEMPLATE_FOLDER=Path(BASE_DIR, "templates"),
)


mail = FastMail(config=mail_config)


class EmailService:
    """Service for sending emails using FastAPI-Mail."""

    @staticmethod
    def create_message(recipients: list[EmailStr], subject: str, body: str) -> MessageSchema:
        """Create an email message."""
        return MessageSchema(
            recipients=recipients,  # type: ignore [arg-type]
            subject=subject,
            body=body,
            subtype=MessageType.html,
        )

    @staticmethod
    async def send_email(message: MessageSchema) -> None:
        """Send an email message."""
        try:
            await mail.send_message(message)
        except ConnectionErrors as e:
            raise EmailSendingError() from e

    @staticmethod
    async def send_welcome_email(addresses: list[EmailStr]) -> None:
        """Send a welcome email to the specified addresses."""
        html = "<h1>Welcome to the app</h1>"
        subject = "Welcome to our app"
        message = EmailService.create_message(addresses, subject, html)
        await EmailService.send_email(message)

    @staticmethod
    async def send_verification_email(addresses: list[EmailStr], verification_link: str) -> None:
        """Send an email verification message to the specified addresses."""
        html = f"<h1>Email Verification</h1><p>Please verify your email by clicking <a href='{verification_link}'>here</a>.</p>"
        subject = "Verify your email address"
        message = EmailService.create_message(addresses, subject, html)
        await EmailService.send_email(message)

    @staticmethod
    async def send_password_reset_email(addresses: list[EmailStr], reset_link: str) -> None:
        """Send a password reset email to the specified addresses."""
        html = f"<h1>Password Reset</h1><p>You can reset your password by clicking <a href='{reset_link}'>here</a>.</p>"
        subject = "Reset your password"
        message = EmailService.create_message(addresses, subject, html)
        await EmailService.send_email(message)
