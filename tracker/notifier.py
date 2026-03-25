import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tracker import config
from tracker.models import Product

logger = logging.getLogger(__name__)


def send_alert(products: list[Product]) -> None:
    config.validate()

    subject = (
        f"[Salmón Tracker] {len(products)} oferta{'s' if len(products) > 1 else ''} "
        f"a menos de {config.PRICE_MAX:.0f}€/kg"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_USER
    msg["To"] = config.NOTIFY_TO
    msg.attach(MIMEText(_build_text(products), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html(products), "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            server.sendmail(config.GMAIL_USER, config.NOTIFY_TO, msg.as_string())
        logger.info(f"Email enviado a {config.NOTIFY_TO} con {len(products)} producto(s)")
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Error de autenticación Gmail. Comprueba que GMAIL_APP_PASSWORD "
            "sea una App Password (no tu contraseña habitual). "
            "Actívala en: https://myaccount.google.com/apppasswords"
        )
        raise
    except Exception as e:
        logger.error(f"Error enviando email: {e}", exc_info=True)
        raise


def _build_text(products: list[Product]) -> str:
    lines = [
        "Hola,",
        "",
        f"Se han encontrado {len(products)} producto(s) de salmón ahumado "
        f"a menos de {config.PRICE_MAX:.2f}€/kg:",
        "",
    ]
    for p in products:
        weight = f" ({p.weight})" if p.weight else ""
        kg = f"{p.price_per_kg:.2f}€/kg" if p.price_per_kg else "€/kg desconocido"
        lines.append(f"• {p.store}: {p.name}{weight}")
        lines.append(f"  Precio: {p.price:.2f}€ ({kg})")
        lines.append(f"  Enlace: {p.url}")
        lines.append("")
    lines.append("-- Salmón Tracker")
    return "\n".join(lines)


def _build_html(products: list[Product]) -> str:
    rows = ""
    for p in products:
        weight = f" ({p.weight})" if p.weight else ""
        kg_str = f"{p.price_per_kg:.2f}€/kg" if p.price_per_kg else "—"
        rows += f"""
        <tr>
            <td style="padding:8px 12px; border-bottom:1px solid #eee;">{p.store}</td>
            <td style="padding:8px 12px; border-bottom:1px solid #eee;">{p.name}{weight}</td>
            <td style="padding:8px 12px; border-bottom:1px solid #eee; color:#888;">{p.price:.2f}€</td>
            <td style="padding:8px 12px; border-bottom:1px solid #eee; font-weight:bold; color:#c00;">{kg_str}</td>
            <td style="padding:8px 12px; border-bottom:1px solid #eee;">
                <a href="{p.url}" style="color:#0066cc;">Ver</a>
            </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif; color:#333; max-width:650px; margin:0 auto;">
  <h2 style="color:#2c7a2c;">Salmon ahumado a menos de {config.PRICE_MAX:.0f}€/kg</h2>
  <p>Se han encontrado <strong>{len(products)} producto(s)</strong> por debajo de {config.PRICE_MAX:.2f}€/kg:</p>
  <table style="width:100%; border-collapse:collapse; margin-top:16px;">
    <thead>
      <tr style="background:#f0f0f0;">
        <th style="padding:10px 12px; text-align:left;">Supermercado</th>
        <th style="padding:10px 12px; text-align:left;">Producto</th>
        <th style="padding:10px 12px; text-align:left;">Precio paquete</th>
        <th style="padding:10px 12px; text-align:left;">Precio/kg</th>
        <th style="padding:10px 12px; text-align:left;">Enlace</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
  <p style="margin-top:24px; font-size:12px; color:#999;">
    Busqueda automatica · Salmon Tracker
  </p>
</body>
</html>"""
