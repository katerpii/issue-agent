"""
Google search agent for crawling Google search results using browser-use
"""
from typing import List, Dict, Any
from datetime import datetime
import asyncio
from urllib.parse import quote_plus
from .base_agent import BaseAgent

# Try to import browser-use
try:
    from browser_use import Browser
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    print("[WARNING] browser-use not installed. Google agent will not work.")

# Import Page type for type hints
try:
    from playwright.async_api import Page
except ImportError:
    Page = Any  # Fallback if playwright not available


class GoogleAgent(BaseAgent):
    """
    Google search crawling agent using browser-use cloud

    This agent uses browser-use's cloud browser to bypass Google's bot detection
    with stealth mode automatically enabled.
    """

    SUPPORTED_DOMAINS = [
        "https://www.google.com/search",
        "https://google.com/search"
    ]

    def __init__(self):
        """Initialize Google agent"""
        super().__init__(platform_name="google")
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
        Crawl Google search results

        Args:
            keywords: List of keywords to search for
            start_date: Start date for search period
            end_date: End date for search period
            detail: Additional detail for filtering
            max_pages: Maximum number of pages to crawl (default: 3)

        Returns:
            List of crawled search results
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
            max_pages: Maximum number of pages to crawl (default: 3)

        Returns:
            List of search results
        """
        results = []

        # Create browser with cloud mode (Browser is already a session)
        session = Browser(
            use_cloud=True,  # Use cloud browser for stealth
        )

        try:
            # Start browser
            print(f"  Starting browser-use cloud session...")
            await session.start()

            # Get current page
            page = await session.get_current_page()

            # Format dates for Google (mm/dd/yyyy)
            start_str = start_date.strftime("%m/%d/%Y")
            end_str = end_date.strftime("%m/%d/%Y")

            # Build URL with custom date range
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&tbs=cdr:1,cd_min:{start_str},cd_max:{end_str}&num=20"

            print(f"  Navigating to Google...")
            await page.goto(url)

            # Wait for page to load (human-like behavior)
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

    async def _parse_page_async(self, page: Page, query: str) -> List[Dict[str, Any]]:
        """
        Parse Google search results from page HTML

        Args:
            page: browser-use page object
            query: Original query

        Returns:
            List of parsed results
        """
        from bs4 import BeautifulSoup
        results = []

        try:
            # Wait for page to render
            await asyncio.sleep(2)

            # Get page HTML using JavaScript
            print(f"  Getting page HTML...")
            html = await page.evaluate('() => document.documentElement.outerHTML')

            if not html or not isinstance(html, str):
                print(f"  Warning: Could not get page HTML")
                return results

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')

            # Try multiple selectors for search result containers
            selectors = ['div.g', 'div.MjjYud', 'div.Gx5Zad', 'div[data-hveid]']
            containers = []

            for selector in selectors:
                containers = soup.select(selector)
                if containers:
                    print(f"  Found {len(containers)} results using selector: {selector}")
                    break

            # Parse each container
            for container in containers[:20]:
                try:
                    # Find title (h3)
                    h3 = container.find('h3')
                    if not h3:
                        continue

                    title = h3.get_text().strip()
                    if not title:
                        continue

                    # Find link
                    link = container.find('a')
                    if not link or not link.get('href'):
                        continue

                    url = link.get('href')
                    if not url.startswith('http'):
                        continue

                    # Find snippet
                    snippet = ''
                    desc_selectors = ['.VwiC3b', '.IsZvec', '.aCOpRe', '.kb0PBd', '.s']

                    for desc_selector in desc_selectors:
                        desc_elem = container.select_one(desc_selector)
                        if desc_elem:
                            snippet = desc_elem.get_text().strip()
                            if snippet:
                                break

                    result = {
                        'title': title,
                        'url': url,
                        'date': datetime.now(),
                        'content': snippet,
                        'platform': self.platform_name,
                        'query': query
                    }
                    results.append(result)

                except Exception as e:
                    # Skip individual results that fail
                    continue

            print(f"  Extracted {len(results)} search results")

        except Exception as e:
            print(f"  Error parsing page: {e}")
            import traceback
            traceback.print_exc()

        return results

    async def _go_to_next_page(self, page: Page) -> bool:
        """
        Navigate to the next page of Google search results

        Args:
            page: browser-use page object

        Returns:
            True if successfully navigated to next page, False otherwise
        """
        try:
            # Try multiple methods to find and click the "Next" button

            # Method 1: Find "Next" button by aria-label
            print(f"    Looking for Next button...")
            next_selectors = [
                'a#pnnext',  # Next button ID
                'a[aria-label*="Next"]',  # Next button with aria-label
                'a[aria-label*="다음"]',  # Korean "Next"
                'td.d6cvqb a[id="pnnext"]',  # More specific selector
                'span:text("Next")',  # Text-based selector
                'span:text("다음")',  # Korean text
            ]

            for selector in next_selectors:
                try:
                    # Check if element exists
                    element = await page.query_selector(selector)
                    if element:
                        print(f"    Found Next button with selector: {selector}")

                        # Check if element is visible and enabled
                        is_visible = await element.is_visible()
                        if not is_visible:
                            continue

                        # Click the element
                        await element.click()

                        # Wait for navigation
                        await asyncio.sleep(2)

                        print(f"    Successfully navigated to next page")
                        return True

                except Exception as e:
                    # Try next selector
                    continue

            # Method 2: Try to find next page link in pagination
            try:
                # Get all pagination links
                pagination_html = await page.evaluate('''
                    () => {
                        const nextLink = document.querySelector('a#pnnext');
                        return nextLink ? nextLink.href : null;
                    }
                ''')

                if pagination_html:
                    print(f"    Found next page URL via JavaScript")
                    await page.goto(pagination_html)
                    await asyncio.sleep(2)
                    return True

            except Exception as e:
                pass

            print(f"    Could not find Next button")
            return False

        except Exception as e:
            print(f"    Error navigating to next page: {e}")
            return False

    def is_supported_domain(self, domain: str) -> bool:
        """
        Check if the given domain is supported by Google agent

        Args:
            domain: Domain URL to check

        Returns:
            True if domain is a Google search URL
        """
        return any(domain.startswith(supported) for supported in self.SUPPORTED_DOMAINS)
