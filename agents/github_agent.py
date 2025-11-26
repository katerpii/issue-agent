
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
            # Check if we're already in an async context (e.g., FastAPI)
            try:
                loop = asyncio.get_running_loop()
                # Already in event loop - create task in thread pool
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    results = pool.submit(
                        lambda: asyncio.run(self._crawl_async(query, start_date, end_date, max_pages))
                    ).result()
            except RuntimeError:
                # No event loop - CLI mode (uv run main.py)
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
        """
        results = []
        session = Browser(use_cloud=True)

        try:
            print(f"  Starting browser-use cloud session...")
            await session.start()
            page = await session.get_current_page()

            search_url = self._build_search_url(query, start_date, end_date)
            print(f"  Navigating to {search_url[:80]}...")

            await page.goto(search_url)
            await asyncio.sleep(5)

            for page_num in range(1, max_pages + 1):
                print(f"  Crawling page {page_num}...")
                page_results = await self._parse_page_async(page, query)
                results.extend(page_results)

                if page_num < max_pages:
                    next_page_found = await self._go_to_next_page(page)
                    if not next_page_found:
                        print(f"  No more pages available, stopping at page {page_num}")
                        break
                    await asyncio.sleep(3)

        except Exception as e:
            print(f"  Error with browser-use: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.stop()
            print(f"  Browser session closed")

        return results

    def _build_search_url(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        encoded_query = quote_plus(query)
        search_url = "https://github.com/search?q={query}&type=repositories"
        if '{query}' in search_url:
            search_url = search_url.replace('{query}', encoded_query)
        return search_url

    async def _parse_page_async(self, page: Page, query: str) -> List[Dict[str, Any]]:
        results = []
        try:
            # Wait for page to render
            await asyncio.sleep(5)

            # Get page HTML
            print(f"  Getting page HTML...")
            html = await page.evaluate('() => document.documentElement.outerHTML')

            if not html or not isinstance(html, str):
                print(f"  Warning: Could not get page HTML")
                return results


            soup = BeautifulSoup(html, 'lxml')
            containers = soup.select("div.Box-sc-62in7e-0.fXzjPH")
            print(f"  Found {len(containers)} result containers")

            for container in containers[:50]:
                try:
                    title_elem = container.select_one("a.Link__StyledLink-sc-1syctfj-0.prc-Link-Link-85e08")
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    if not title:
                        continue

                    link_elem = container.select_one("a.Link__StyledLink-sc-1syctfj-0.prc-Link-Link-85e08")
                    if not link_elem or not link_elem.get('href'):
                        continue
                    url = link_elem.get('href')
                    if not url.startswith('http'):
                        url = f"{self.base_url}{url}"

                    content = ""
                    content_elem = container.select_one("span.Text__StyledText-sc-1klmep6-0.hkFRpV.search-match.prc-Text-Text-0ima0")
                    if content_elem:
                        content = content_elem.get_text(strip=True)

                    date = datetime.now()
                    date_elem = container.select_one("div[title*='Updated'], div[title*='on']")
                    if date_elem:
                        date_str = date_elem.get_text(strip=True)

                    result = {
                        'title': title,
                        'url': url,
                        'date': date,
                        'content': content,
                        'platform': self.platform_name,
                        'query': query
                    }

                    results.append(result)

                except Exception:
                    continue

            print(f"  Extracted {len(results)} search results")

        except Exception as e:
            print(f"  Error parsing page: {e}")
            import traceback
            traceback.print_exc()

        return results

    async def _go_to_next_page(self, page: Page) -> bool:
        try:
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
                    if element and await element.is_visible():
                        print(f"    Found Next button with selector: {selector}")
                        await element.click()
                        await asyncio.sleep(2)
                        print(f"    Successfully navigated to next page")
                        return True
                except Exception:
                    continue

            print(f"    Could not find Next button")
            return False

        except Exception as e:
            print(f"    Error navigating to next page: {e}")
            return False

    def is_supported_domain(self, domain: str) -> bool:
        return any(domain.startswith(supported) for supported in self.SUPPORTED_DOMAINS)
