# tests/integration/test_browser_use_startup.py
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# browser_use가 설치되어 있는지 확인
try:
    from agents.google_agent import GoogleAgent
    BROWSER_USE_INSTALLED = True
except ImportError:
    BROWSER_USE_INSTALLED = False

# API Key needed for this test
BROWSER_USE_API_KEY = os.getenv("BROWSER_USE_API_KEY")

# Skip this test if BROWSER_USE_API_KEY is not set or browser-use is not installed
pytestmark = pytest.mark.skipif(
    not BROWSER_USE_API_KEY or not BROWSER_USE_INSTALLED,
    reason="This test requires BROWSER_USE_API_KEY and the 'browser-use' library to be installed."
)

@pytest.mark.asyncio
async def test_browser_use_starts_and_stops_correctly(mocker):
    """
    Tests if the browser-use cloud browser starts and stops correctly via GoogleAgent.
    Parsing logic is NOT tested here.
    """
    # --- 1. Setup ---
    agent = GoogleAgent()
    keywords = ["dummy keyword"]

    # Mock the actual browser-use Browser class and its async methods
    mock_browser_instance = MagicMock()
    mock_browser_instance.start = AsyncMock()
    mock_browser_instance.stop = AsyncMock()
    
    # Mock get_current_page to return a mock page object with a goto method
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_browser_instance.get_current_page = AsyncMock(return_value=mock_page)

    # Patch the Browser constructor in the google_agent module
    mocker.patch("agents.google_agent.Browser", return_value=mock_browser_instance)

    # Mock internal methods to isolate the startup/shutdown logic
    mocker.patch.object(agent, '_parse_page_async', new_callable=AsyncMock, return_value=[])
    mocker.patch.object(agent, '_go_to_next_page', new_callable=AsyncMock, return_value=False)

    # --- 2. Execution ---
    # Call the _crawl_async method which contains the core browser-use logic
    await agent._crawl_async(query=" ".join(keywords), max_pages=1)

    # --- 3. Assertion ---
    # Verify that browser-use's start and stop methods were called
    mock_browser_instance.start.assert_called_once()
    mock_browser_instance.stop.assert_called_once()

    print("\n[TEST] browser-use startup and shutdown test passed successfully.")