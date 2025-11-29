"""
Email Sender - Send notification emails to subscribers

This module handles sending email notifications when new results are found.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any

# SMTP Configuration from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)
SENDER_NAME = os.getenv("SENDER_NAME", "Issue Agent Bot")


def send_notification_email(
    recipient_email: str,
    keywords: List[str],
    platforms: List[str],
    new_results: List[Dict[str, Any]],
    total_new: int
) -> bool:
    """
    Send notification email with new results

    Args:
        recipient_email: Email address to send to
        keywords: Search keywords
        platforms: Platforms searched
        new_results: List of new results (max 10)
        total_new: Total number of new results

    Returns:
        bool: True if email sent successfully
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🤖 새로운 이슈 {total_new}건 발견! - {', '.join(keywords)}"
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = recipient_email

        # Create HTML content
        html_content = generate_email_html(keywords, platforms, new_results, total_new)

        # Attach HTML
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL] Successfully sent notification to {recipient_email}")
        return True

    except Exception as e:
        print(f"[EMAIL] Failed to send email to {recipient_email}: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_email_html(
    keywords: List[str],
    platforms: List[str],
    results: List[Dict[str, Any]],
    total_new: int
) -> str:
    """Generate HTML email content"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007BFF;
        }}
        .header h1 {{
            color: #007BFF;
            margin: 0;
            font-size: 24px;
        }}
        .summary {{
            background-color: #e7f3ff;
            padding: 15px;
            border-left: 4px solid #007BFF;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        .summary p {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .result-item {{
            background-color: #f8f9fa;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        }}
        .result-item h3 {{
            margin: 0 0 10px 0;
            color: #007BFF;
            font-size: 16px;
        }}
        .result-item a {{
            color: #007BFF;
            text-decoration: none;
            word-break: break-all;
        }}
        .result-item a:hover {{
            text-decoration: underline;
        }}
        .result-item .meta {{
            font-size: 13px;
            color: #666;
            margin-top: 8px;
        }}
        .result-item .score {{
            display: inline-block;
            background-color: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            font-size: 12px;
            color: #666;
        }}
        .cta-button {{
            display: inline-block;
            background-color: #007BFF;
            color: white;
            padding: 12px 24px;
            border-radius: 4px;
            text-decoration: none;
            margin-top: 20px;
            font-weight: bold;
        }}
        .cta-button:hover {{
            background-color: #0056b3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Issue Agent 알림</h1>
            <p>새로운 이슈가 발견되었습니다!</p>
        </div>

        <div class="summary">
            <p><strong>키워드:</strong> {', '.join(keywords)}</p>
            <p><strong>플랫폼:</strong> {', '.join(platforms)}</p>
            <p><strong>새 결과:</strong> {total_new}건</p>
            <p><strong>확인 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <h2 style="color: #333; font-size: 18px; margin-bottom: 15px;">📋 상위 {len(results)}개 결과</h2>
"""

    # Add results
    for idx, result in enumerate(results, 1):
        title = result.get('title', 'No title')
        url = result.get('url', '#')
        platform = result.get('platform', 'Unknown')
        score = result.get('relevance_score', 0)
        reason = result.get('relevance_reason', '')
        content = result.get('content', '')[:200]

        html += f"""
        <div class="result-item">
            <h3>[{idx}] {title}</h3>
            <p><a href="{url}" target="_blank">{url}</a></p>
            <div class="meta">
                <span class="score">관련성: {score}/10</span>
                <span style="margin-left: 10px;">플랫폼: {platform}</span>
            </div>
            {f'<p style="margin-top: 8px; font-size: 13px;">{reason}</p>' if reason else ''}
            {f'<p style="margin-top: 8px; font-size: 13px; color: #666;">{content}...</p>' if content else ''}
        </div>
"""

    html += f"""
        {f'<p style="text-align: center; color: #666; margin-top: 20px;">총 {total_new}건 중 상위 {len(results)}개만 표시됩니다.</p>' if total_new > len(results) else ''}

        <div class="footer">
            <p>이 이메일은 Issue Agent 구독 서비스를 통해 자동으로 발송되었습니다.</p>
            <p>구독을 취소하려면 설정 페이지를 방문하세요.</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def test_email_connection() -> bool:
    """Test SMTP connection"""
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("[EMAIL] SMTP connection test successful")
        return True
    except Exception as e:
        print(f"[EMAIL] SMTP connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test email sending
    print("Testing email configuration...")
    if test_email_connection():
        print("✓ Email configuration is valid")
    else:
        print("✗ Email configuration failed. Please check your SMTP settings.")
