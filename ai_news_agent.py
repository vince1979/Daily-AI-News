"""
AI News Agent - Fetches top AI news daily and sends via Email
Requires: pip install anthropic
(smtplib and email are built into Python — no extra installs needed)

Gmail setup:
  1. Enable 2-Factor Authentication on your Google account
  2. Go to myaccount.google.com → Security → App Passwords
  3. Create an App Password for "Mail" and use it as GMAIL_APP_PASSWORD below
"""

import anthropic
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

# ─── Configuration ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GMAIL_ADDRESS      = os.environ.get("GMAIL_ADDRESS")         # Your Gmail address (sender)
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")   # Gmail App Password (not your real password)
TO_EMAIL           = os.environ.get("TO_EMAIL")              # Where to send the digest (can be same or different)
# ──────────────────────────────────────────────────────────────────────────────


def fetch_ai_news() -> tuple[str, str]:
    """Use Claude with web search to find today's top AI news articles.
    Returns (plain_text, html) versions of the digest."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = date.today().strftime("%B %d, %Y")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Today is {today}. Search for the 5 most important and interesting "
                    "AI news articles from the last 24 hours. "
                    "Return ONLY a plain-text list in this exact format, nothing else:\n\n"
                    "1. [Headline] | [One sentence summary] | [URL]\n"
                    "2. [Headline] | [One sentence summary] | [URL]\n"
                    "... and so on."
                ),
            }
        ],
    )

    # Extract plain text response
    plain_text = ""
    for block in response.content:
        if block.type == "text":
            plain_text = block.text.strip()
            break

    # Build HTML version
    html_lines = []
    for line in plain_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            # Parse "1. Headline | Summary | URL"
            parts = line.split("|")
            headline_part = parts[0].strip()   # e.g. "1. Headline"
            summary       = parts[1].strip() if len(parts) > 1 else ""
            url           = parts[2].strip() if len(parts) > 2 else ""

            # Strip leading number/dot
            headline = headline_part.lstrip("0123456789. ").strip()

            if url:
                html_lines.append(
                    f'<li style="margin-bottom:16px;">'
                    f'<a href="{url}" style="font-size:16px;font-weight:bold;color:#1a0dab;text-decoration:none;">{headline}</a><br>'
                    f'<span style="color:#555;font-size:14px;">{summary}</span>'
                    f'</li>'
                )
            else:
                html_lines.append(f'<li style="margin-bottom:16px;"><strong>{headline}</strong><br><span style="color:#555;font-size:14px;">{summary}</span></li>')
        except Exception:
            html_lines.append(f'<li style="margin-bottom:16px;">{line}</li>')

    today_str = date.today().strftime("%B %d, %Y")
    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:620px;margin:auto;padding:24px;">
      <h2 style="color:#222;border-bottom:2px solid #e0e0e0;padding-bottom:8px;">
        🤖 Daily AI News — {today_str}
      </h2>
      <ul style="padding-left:20px;">
        {"".join(html_lines)}
      </ul>
      <p style="color:#aaa;font-size:12px;margin-top:32px;">
        Powered by Claude AI • Unsubscribe by disabling the GitHub Actions workflow
      </p>
    </body></html>
    """

    return plain_text, html


def send_email(plain_text: str, html: str) -> None:
    """Send the news digest via Gmail SMTP."""
    today_str = date.today().strftime("%B %d, %Y")
    subject = f"🤖 Daily AI News — {today_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = TO_EMAIL

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, TO_EMAIL, msg.as_string())

    print(f"Email sent to {TO_EMAIL}!")


def main():
    print("Fetching AI news...")
    plain_text, html = fetch_ai_news()
    print(f"News fetched:\n{plain_text}\n")
    send_email(plain_text, html)


if __name__ == "__main__":
    main()
