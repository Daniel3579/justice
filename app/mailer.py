import logging
import smtplib
import ssl
from email.message import EmailMessage

from config import RESET_TOKEN_TTL_MINUTES, SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


def send_reset_email(to: str, link: str):
    if not SMTP_HOST:
        logging.warning(f"SMTP не настроен. Ссылка для сброса пароля {to}: {link}")
        return

    msg = EmailMessage()
    msg["Subject"] = "Сброс пароля для Justice"
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg.set_content(
        "Здравствуйте!\n\n"
        "Мы получили запрос на сброс пароля для вашего аккаунта в Justice.\n"
        f"Чтобы задать новый пароль, перейдите по ссылке (действует {RESET_TOKEN_TTL_MINUTES} минут):\n\n"
        f"{link}\n\n"
        "Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо."
    )

    context = ssl.create_default_context()
    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=20) as smtp:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
                smtp.starttls(context=context)
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.send_message(msg)
        logging.info(f"Письмо для сброса пароля отправлено: {to}")
    except (smtplib.SMTPException, OSError) as e:
        logging.error(f"Не удалось отправить письмо на {to}: {e}")
