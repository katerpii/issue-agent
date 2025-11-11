"""
Github crawling agent
Auto-generated from agent template
"""
from typing import List, Dict, Any
from datetime import datetime
import asyncio
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from .base_agent import BaseAgent

# Try to import browser-use
try:
    from browser_use import Browser
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    print("[WARNING] browser-use not installed. github agent will not work.")

# Import Page type for type hints
try:
    from playwright.async_api import Page
except ImportError:
    Page = Any  # Fallback if playwright not available


class GithubAgent(BaseAgent):
    """
    Github crawling agent using browser-use

    This agent uses browser-use's cloud browser to bypass bot detection
    with stealth mode automatically enabled.
    """

    SUPPORTED_DOMAINS = [
        "https://github.com/search",
        "https://github.com"
    ]

    def __init__(self):
        """Initialize github agent"""
        super().__init__(platform_name="github")
        self.base_url = "https://github.com/search"
        self.browser_use_available = BROWSER_USE_AVAILABLE

    def crawl(
        self,
        keywords: List[str],
        start_date: datetime,
        end_date: datetime,
        detail: str = "",
        max_pages: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Crawl github for matching content

        Args:
            keywords: List of keywords to search for
            start_date: Start date for search period
            end_date: End date for search period
            detail: Additional detail for filtering
            max_pages: Maximum number of pages to crawl (default: 3)

        Returns:
            List of crawled items
        """
        print(f"\n[{self.platform_name.upper()}] Starting crawl...")
        print(f"  Keywords: {', '.join(keywords)}")
        print(f"  Period: {start_date.date()} ~ {end_date.date()}")
        print(f"  Max pages: {max_pages}")

        if not self.browser_use_available:
            print(f"  [ERROR] browser-use is not available.")
            print(f"  Install with: pip install browser-use")
            return []

        results = []
        query = " ".join(keywords)

        try:
            # Run async crawl in sync context
            results = asyncio.run(self._crawl_async(query, start_date, end_date, max_pages))
            print(f"  Found {len(results)} results")

        except Exception as e:
            print(f"  Error during crawling: {e}")
            import traceback
            traceback.print_exc()

        return results

    async def _crawl_async(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime,
        max_pages: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Async crawl using browser-use

        Args:
            query: Search query
            start_date: Start date
            end_date: End date
            max_pages: Maximum number of pages to crawl

        Returns:
            List of search results
        """
        results = []

        # Create browser with cloud mode
        session = Browser(
            use_cloud=True,  # Use cloud browser for stealth
        )

        try:
            # Start browser
            print(f"  Starting browser-use cloud session...")
            await session.start()

            # Get current page
            page = await session.get_current_page()

            # Build search URL
            search_url = self._build_search_url(query, start_date, end_date)
            print(f"  Navigating to {search_url[:80]}...")

            await page.goto(search_url)

            # Wait for page to load
            await asyncio.sleep(5)

            # Crawl multiple pages
            for page_num in range(1, max_pages + 1):
                print(f"  Crawling page {page_num}...")

                # Parse results from current page
                page_results = await self._parse_page_async(page, query)
                results.extend(page_results)

                # Try to go to next page if not the last page
                if page_num < max_pages:
                    next_page_found = await self._go_to_next_page(page)
                    if not next_page_found:
                        print(f"  No more pages available, stopping at page {page_num}")
                        break

                    # Wait for page to load
                    await asyncio.sleep(3)

        except Exception as e:
            print(f"  Error with browser-use: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Stop browser session
            await session.stop()
            print(f"  Browser session closed")

        return results

    def _build_search_url(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """
        Build platform-specific search URL

        Args:
            query: Search query
            start_date: Start date
            end_date: End date

        Returns:
            Complete search URL
        """
        # URL parameters specific to github
        encoded_query = quote_plus(query)
        params = [
            f"q={encoded_query}",
            # Add platform-specific parameters here
        ]

        # Build query string
        query_string = '&'.join(params)
        return f"{self.base_url}?{query_string}"

    async def _parse_page_async(self, page: Page, query: str) -> List[Dict[str, Any]]:
        """
        Parse search results from page HTML

        Args:
            page: browser-use page object
            query: Original query

        Returns:
            List of parsed results
        """
        results = []

        try:
            # Wait for page to render
            await asyncio.sleep(2)

            # Get page HTML
            print(f"  Getting page HTML...")
            html = await page.evaluate('() => document.documentElement.outerHTML')

            if not html or not isinstance(html, str):
                print(f"  Warning: Could not get page HTML")
                return results

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')

            # Find result containers using platform-specific selectors
            containers = soup.select(".Box-sc-62in7e-0.fXzjPH")
            print(f"  Found {len(containers)} result containers")

            for container in containers[:50]:
                try:
                    # Extract title
                    title_elem = container.select_one("a.Link__StyledLink-sc-1syctfj-0.prc-Link-Link-85e08")
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    if not title:
                        continue

                    # Extract URL
                    link_elem = container.select_one("a.Link__StyledLink-sc-1syctfj-0.prc-Link-Link-85e08")
                    if not link_elem or not link_elem.get('href'):
                        continue
                    url = link_elem.get('href')

                    # Make URL absolute if needed
                    if not url.startswith('http'):
                        url = f"{self.base_url}{url}"

                    # Extract content/snippet
                    content = ""
                    content_elem = container.select_one(".prc-Truncate-Truncate-A9Wn6")
                    if content_elem:
                        content = content_elem.get_text(strip=True)

                    # Extract date (if available)
                    date = datetime.now()
                    date_elem = container.select_one("li.Box-sc-62in7e-0.gbntE")
                    if date_elem:
                        date_str = date_elem.get_text(strip=True)
                        # Add date parsing logic here if needed

                    result = {
                        'title': title,
                        'url': url,
                        'date': date,
                        'content': content,
                        'platform': self.platform_name,
                        'query': query
                    }

                    results.append(result)

                except Exception as e:
                    # Skip individual results that fail to parse
                    continue

            print(f"  Extracted {len(results)} search results")

        except Exception as e:
            print(f"  Error parsing page: {e}")
            import traceback
            traceback.print_exc()

        return results

    async def _go_to_next_page(self, page: Page) -> bool:
        """
        Navigate to the next page of search results

        Args:
            page: browser-use page object

        Returns:
            True if successfully navigated to next page, False otherwise
        """
        try:
            # Try to find and click the "Next" button
            print(f"    Looking for Next button...")
            next_selectors = [
                'a[aria-label*="Next"]',
                'a[aria-label*="next"]',
                'a.next',
                'button.next',
                'a:has-text("Next")',
                'button:has-text("Next")',
            ]

            for selector in next_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            print(f"    Found Next button with selector: {selector}")
                            await element.click()
                            await asyncio.sleep(2)
                            print(f"    Successfully navigated to next page")
                            return True
                except Exception as e:
                    continue

            print(f"    Could not find Next button")
            return False

        except Exception as e:
            print(f"    Error navigating to next page: {e}")
            return False

    def is_supported_domain(self, domain: str) -> bool:
        """
        Check if domain is supported by this agent

        Args:
            domain: Domain URL to check

        Returns:
            True if domain is supported
        """
        return any(domain.startswith(supported) for supported in self.SUPPORTED_DOMAINS)
