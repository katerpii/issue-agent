# tests/integration/test_email_sender.py
import os
import pytest
from unittest.mock import MagicMock, patch
from email.message import Message
import email_sender

# SMTP credentials needed for this test
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Skip this test if SMTP credentials are not set
pytestmark = pytest.mark.skipif(
    not all([SMTP_USERNAME, SMTP_PASSWORD]),
    reason="This test requires SMTP_USERNAME and SMTP_PASSWORD environment variables."
)

def test_send_notification_email_prepares_correct_content(mocker):
    """
    Tests if the send_notification_email function correctly prepares the email content
    without actually sending it, by mocking smtplib.SMTP.
    """
    # --- 1. Setup ---
    # Mock the SMTP server to intercept the email
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.starttls.return_value = None # starttls doesn't return anything
    mock_smtp_instance.login.return_value = None # login doesn't return anything
    mock_smtp_instance.send_message.return_value = None # send_message doesn't return anything

    mocker.patch("smtplib.SMTP", return_value=mock_smtp_instance)

    # Prepare some dummy processed data to simulate results from ResultProcessor
    mock_processed_results = [
        {
            'title': 'Test Result 1',
            'url': 'http://test1.com',
            'content': 'This is content for test result 1.',
            'platform': 'google',
            'relevance_score': 9,
            'relevance_reason': 'Very relevant to query.'
        },
        {
            'title': 'Test Result 2',
            'url': 'http://test2.com',
            'content': 'This is content for test result 2.',
            'platform': 'reddit',
            'relevance_score': 7,
            'relevance_reason': 'Somewhat relevant.'
        }
    ]    
    recipient = "test_recipient@example.com"
    keywords = ["test", "keyword"]
    platforms = ["google", "reddit"]
    total_new_results = 2
    
    # --- 2. Execution ---
    success = email_sender.send_notification_email(
        recipient_email=recipient,
        keywords=keywords,
        platforms=platforms,
        new_results=mock_processed_results,
        total_new=total_new_results
    )

    # --- 3. Assertion ---
    # Verify that the email was "sent" successfully (i.e., no exceptions occurred during preparation)
    assert success is True

    # Verify that SMTP connection, login, and send_message were attempted
    mocker.patch("smtplib.SMTP").assert_called_once_with(email_sender.SMTP_SERVER, email_sender.SMTP_PORT)
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with(email_sender.SMTP_USERNAME, email_sender.SMTP_PASSWORD)
    mock_smtp_instance.send_message.assert_called_once()

    # Get the sent message object
    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert isinstance(sent_msg, Message)

    # Verify headers
    assert sent_msg['To'] == recipient
    assert f"새로운 이슈 {total_new_results}건 발견!" in sent_msg['Subject']
    assert email_sender.SENDER_EMAIL in sent_msg['From']

    # Verify content (check for some unique text from our mock data)
    html_payload = ""
    for part in sent_msg.walk():
        if part.get_content_type() == "text/html":
            html_payload = part.get_payload(decode=True).decode('utf-8')
            break
    
    assert html_payload, "HTML content not found in the email."
    assert "Test Result 1" in html_payload
    assert "http://test1.com" in html_payload
    assert "관련성: 9/10" in html_payload
    assert "This is content for test result 1." in html_payload
    assert "Test Result 2" in html_payload
    assert "총 2건 중 상위 2개만 표시됩니다." in html_payload
    
    print("\n[TEST] EmailSender preparation test passed successfully.")
