"""
Reddit search agent for crawling Reddit posts using browser-use
"""
from typing import List, Dict, Any
from datetime import datetime
import asyncio
from urllib.parse import quote_plus
from .base_agent import BaseAgent
from bs4 import BeautifulSoup

# Try to import browser-use
try:
    from browser_use import Browser
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    print("[WARNING] browser-use not installed. Reddit agent will not work.")

# Import Page type for type hints
try:
    from playwright.async_api import Page
except ImportError:
    Page = Any  # Fallback if playwright not available


class RedditAgent(BaseAgent):
    """
    Reddit crawling agent using browser-use

    This agent uses browser-use's cloud browser to crawl Reddit
    and bypass bot detection with stealth mode.
    """

    SUPPORTED_DOMAINS = [
        "https://www.reddit.com",
        "https://reddit.com",
        "https://old.reddit.com"
    ]

    def __init__(self):
        """Initialize Reddit agent"""
        super().__init__(platform_name="reddit")
        self.browser_use_available = BROWSER_USE_AVAILABLE

    def crawl(
        self,
        keywords: List[str],
        detail: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Crawl Reddit posts

        Args:
            keywords: List of keywords to search for
            detail: Additional detail for filtering

        Returns:
            List of crawled Reddit posts
        """
        print(f"\n[{self.platform_name.upper()}] Starting crawl...")
        print(f"  Keywords: {', '.join(keywords)}")

        if not self.browser_use_available:
            print("  [ERROR] browser-use is not available.")
            print("  Install with: pip install browser-use")
            return []

        query = " ".join(keywords)
        results = []

        try:
            # Check if we're already in an async context (e.g., FastAPI)
            try:
                loop = asyncio.get_running_loop()
                # Already in event loop - create task in thread pool
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    results = pool.submit(
                        lambda: asyncio.run(self._crawl_async(query))
                    ).result()
            except RuntimeError:
                # No event loop - CLI mode (uv run main.py)
                results = asyncio.run(self._crawl_async(query))

            print(f"  Found {len(results)} results")

        except Exception as e:
            print(f"  Error during crawling: {e}")
            import traceback
            traceback.print_exc()

        return results

    async def _crawl_async(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Async crawl using browser-use

        Args:
            query: Search query

        Returns:
            List of Reddit posts
        """
        results = []

        # Create browser with cloud mode
        session = Browser(
            use_cloud=True,
        )

        try:
            print("  Starting browser-use cloud session...")
            await session.start()

            page = await session.get_current_page()

            # Calculate time filter based on date range
            time_diff = (end_date - start_date).days
            if time_diff <= 1:
                time_filter = 'day'
            elif time_diff <= 7:
                time_filter = 'week'
            elif time_diff <= 31:
                time_filter = 'month'
            elif time_diff <= 365:
                time_filter = 'year'
            else:
                time_filter = 'all'

            # Use old Reddit for easier parsing
            encoded_query = quote_plus(query)
            url = f"https://old.reddit.com/search?q={encoded_query}&sort=new&t={time_filter}"
            print(f"  Navigating to: {url}")

            await page.goto(url)
            await asyncio.sleep(5)

            # Parse results
            results = await self._parse_page_async(page, query, start_date, end_date)
            print(f"  Found {len(results)} results")

        except Exception as e:
            print(f"  Error with browser-use: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.stop()
            print("  Browser session closed")

        return results

    async def _parse_page_async(
        self,
        page: Page,
        query: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Parse Reddit search results from page

        Args:
            page: browser-use page object
            query: Search query
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            List of parsed posts
        """
        results = []

        try:
            await asyncio.sleep(2)

            print("  Getting page HTML...")
            html = await page.evaluate('() => document.documentElement.outerHTML')

            if not html or not isinstance(html, str):
                print("  Warning: Could not get page HTML")
                return results

            results = self._parse_reddit_html(html, query, start_date, end_date)

        except Exception as e:
            print(f"  Error parsing page: {e}")
            import traceback
            traceback.print_exc()

        return results

    def _parse_reddit_html(
        self,
        html: str,
        query: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Parse Reddit search results HTML

        Args:
            html: HTML content
            query: Search query
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            List of parsed posts
        """
        soup = BeautifulSoup(html, 'lxml')
        results = []

        # Find all post containers in old Reddit search results
        # Search results use 'search-result-link' class for posts
        posts = soup.find_all('div', class_='search-result-link')

        print(f"  Found {len(posts)} post containers")

        parsed_count = 0
        filtered_count = 0

        for post in posts:
            try:
                # Extract title from search-title class
                title_elem = post.find('a', class_='search-title')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')

                # Make URL absolute if needed
                if url.startswith('/r/'):
                    url = f"https://reddit.com{url}"
                elif not url.startswith('http'):
                    url = f"https://old.reddit.com{url}"

                # Extract subreddit
                subreddit_elem = post.find('a', class_='search-subreddit-link')
                subreddit = subreddit_elem.get_text(strip=True) if subreddit_elem else 'unknown'

                # Extract comments count (search results don't have score easily accessible)
                comments_elem = post.find('a', class_='search-comments')
                num_comments = 0
                if comments_elem:
                    comments_text = comments_elem.get_text(strip=True)
                    try:
                        num_comments = int(comments_text.split()[0])
                    except:
                        num_comments = 0

                # Extract time
                time_elem = post.find('time')
                post_date = None
                if time_elem and time_elem.get('datetime'):
                    try:
                        post_date = datetime.fromisoformat(time_elem['datetime'].replace('Z', '+00:00'))
                        # Convert to naive datetime for comparison
                        post_date = post_date.replace(tzinfo=None)
                    except Exception:
                        pass

                parsed_count += 1

                # Filter by date - only if we successfully parsed the date
                if post_date and (post_date < start_date or post_date > end_date):
                    filtered_count += 1
                    continue

                # If no date found, include the post (don't filter)
                if not post_date:
                    post_date = datetime.now()

                result = {
                    'title': title,
                    'url': url,
                    'date': post_date,
                    'content': '',  # Not available in search results
                    'platform': self.platform_name,
                    'query': query,
                    'num_comments': num_comments,
                    'subreddit': subreddit
                }

                results.append(result)

                # Limit results
                if len(results) >= 50:
                    break

            except Exception:
                # Skip individual posts that fail to parse
                continue

        print(f"  Parsed {parsed_count} posts, filtered {filtered_count} by date")

        return results

    def is_supported_domain(self, domain: str) -> bool:
        """
        Check if the given domain is supported by Reddit agent

        Args:
            domain: Domain URL to check

        Returns:
            True if domain is a Reddit URL
        """
        return any(domain.startswith(supported) for supported in self.SUPPORTED_DOMAINS)
