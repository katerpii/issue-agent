"""
Agent Template for generating platform-specific crawling agents

This module provides a template system for creating new platform agents
with consistent structure and minimal code duplication.
"""
from typing import Dict, List, Any
from pathlib import Path
import importlib.util


class AgentTemplate:
    """
    Template for generating platform-specific crawling agents

    This template maintains a consistent structure across all agents
    while allowing customization of platform-specific details like:
    - Base URLs and domain patterns
    - HTML selectors for parsing
    - Request headers and authentication
    - Platform-specific query parameters
    """

    # Base template for new agent generation
    BASE_TEMPLATE = '''
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
    print("[WARNING] browser-use not installed. {platform_name} agent will not work.")

# Import Page type for type hints
try:
    from playwright.async_api import Page
except ImportError:
    Page = Any  # Fallback if playwright not available


class {class_name}(BaseAgent):
    """
    {platform_name_title} crawling agent using browser-use

    This agent uses browser-use's cloud browser to bypass bot detection
    with stealth mode automatically enabled.
    """

    SUPPORTED_DOMAINS = {supported_domains}

    def __init__(self):
        """Initialize {platform_name} agent"""
        super().__init__(platform_name="{platform_name}")
        self.base_url = "{base_url}"
        self.browser_use_available = BROWSER_USE_AVAILABLE

    def crawl(
        self,
        keywords: List[str],
        detail: str = "",
        max_pages: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Crawl {platform_name} for matching content
        """
        print(f"\\n[{{self.platform_name.upper()}}] Starting crawl...")
        print(f"  Keywords: {{', '.join(keywords)}}")
        print(f"  Max pages: {{max_pages}}")

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
                        lambda: asyncio.run(self._crawl_async(query, max_pages))
                    ).result()
            except RuntimeError:
                # No event loop - CLI mode (uv run main.py)
                results = asyncio.run(self._crawl_async(query, max_pages))

            print(f"  Found {{len(results)}} results")

        except Exception as e:
            print(f"  Error during crawling: {{e}}")
            import traceback
            traceback.print_exc()

        return results

    async def _crawl_async(
        self,
        query: str,
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

            search_url = self._build_search_url(query)
            print(f"  Navigating to {{search_url[:80]}}...")

            await page.goto(search_url)
            await asyncio.sleep(5)

            for page_num in range(1, max_pages + 1):
                print(f"  Crawling page {{page_num}}...")
                page_results = await self._parse_page_async(page, query)
                results.extend(page_results)

                if page_num < max_pages:
                    next_page_found = await self._go_to_next_page(page)
                    if not next_page_found:
                        print(f"  No more pages available, stopping at page {{page_num}}")
                        break
                    await asyncio.sleep(3)

        except Exception as e:
            print(f"  Error with browser-use: {{e}}")
            import traceback
            traceback.print_exc()
        finally:
            await session.stop()
            print(f"  Browser session closed")

        return results

    def _build_search_url(
        self,
        query: str
    ) -> str:
        encoded_query = quote_plus(query)
        search_url = "{search_url_template}"
        if '{{query}}' in search_url:
            search_url = search_url.replace('{{query}}', encoded_query)
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
            containers = soup.select("{container_selector}")
            print(f"  Found {{len(containers)}} result containers")

            for container in containers[:50]:
                try:
                    title_elem = container.select_one("{title_selector}")
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    if not title:
                        continue

                    link_elem = container.select_one("{link_selector}")
                    if not link_elem or not link_elem.get('href'):
                        continue
                    url = link_elem.get('href')
                    if not url.startswith('http'):
                        url = f"{{self.base_url}}{{url}}"

                    content = ""
                    content_elem = container.select_one("{content_selector}")
                    if content_elem:
                        content = content_elem.get_text(strip=True)

                    date = datetime.now()
                    date_elem = container.select_one("{date_selector}")
                    if date_elem:
                        date_str = date_elem.get_text(strip=True)

                    result = {{
                        'title': title,
                        'url': url,
                        'date': date,
                        'content': content,
                        'platform': self.platform_name,
                        'query': query
                    }}

                    results.append(result)

                except Exception:
                    continue

            print(f"  Extracted {{len(results)}} search results")

        except Exception as e:
            print(f"  Error parsing page: {{e}}")
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
                        print(f"    Found Next button with selector: {{selector}}")
                        await element.click()
                        await asyncio.sleep(2)
                        print(f"    Successfully navigated to next page")
                        return True
                except Exception:
                    continue

            print(f"    Could not find Next button")
            return False

        except Exception as e:
            print(f"    Error navigating to next page: {{e}}")
            return False

    def is_supported_domain(self, domain: str) -> bool:
        return any(domain.startswith(supported) for supported in self.SUPPORTED_DOMAINS)
'''


    @classmethod
    def generate_agent(
        cls,
        platform_name: str,
        base_url: str,
        supported_domains: List[str],
        selectors: Dict[str, str],
        search_url: str = None,
        url_params: Dict[str, str] = None
    ) -> str:
        """
        Generate agent code from template

        Args:
            platform_name: Name of platform (e.g., 'stackoverflow')
            base_url: Base URL for search (e.g., 'https://stackoverflow.com/search')
            supported_domains: List of supported domain URLs
            selectors: Dictionary of CSS selectors for parsing:
                - container_selector: Selector for result containers
                - title_selector: Selector for title within container
                - link_selector: Selector for link within container
                - content_selector: Selector for content/snippet
                - date_selector: Selector for date (optional)
            search_url: Complete search URL pattern with {query} placeholder (e.g., 'https://example.com/?s={query}')
            url_params: Additional URL parameters (optional, deprecated in favor of search_url)

        Returns:
            Generated agent code as string
        """
        # Format class name (e.g., 'stackoverflow' -> 'StackoverflowAgent')
        class_name = f"{platform_name.title()}Agent"
        platform_name_title = platform_name.replace('_', ' ').title()

        # Format supported domains as Python list
        domains_str = "[\n        " + ",\n        ".join(f'"{d}"' for d in supported_domains) + "\n    ]"

        # Use search_url if provided, otherwise fall back to old url_params method
        if search_url:
            # Keep {query} as is - it will be used in the generated agent code
            search_url_template = search_url
        else:
            # Fallback to old method with url_params (deprecated)
            if url_params:
                params_lines = []
                for key, value in url_params.items():
                    params_lines.append(f"            f\"{key}={value}\"")
                url_params_str = ",\n".join(params_lines)
            else:
                url_params_str = "            # Add platform-specific parameters here"
            search_url_template = f"{base_url}?q={{{{query}}}}"

        # Generate code from template
        code = cls.BASE_TEMPLATE.format(
            platform_name=platform_name,
            platform_name_title=platform_name_title,
            class_name=class_name,
            base_url=base_url,
            supported_domains=domains_str,
            search_url_template=search_url_template,
            container_selector=selectors.get('container_selector', 'div.result'),
            title_selector=selectors.get('title_selector', 'h3'),
            link_selector=selectors.get('link_selector', 'a'),
            content_selector=selectors.get('content_selector', 'p.description'),
            date_selector=selectors.get('date_selector', 'time')
        )

        return code

    @classmethod
    def save_agent(cls, platform_name: str, agent_code: str) -> Path:
        """
        Save generated agent code to file

        Args:
            platform_name: Name of platform
            agent_code: Generated agent code

        Returns:
            Path to saved agent file
        """
        agents_dir = Path(__file__).parent
        file_path = agents_dir / f"{platform_name}_agent.py"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(agent_code)

        print(f"[TEMPLATE] Saved agent to: {file_path}")
        return file_path

    @classmethod
    def load_agent_class(cls, platform_name: str):
        """
        Dynamically load agent class from file

        Args:
            platform_name: Name of platform

        Returns:
            Agent class or None if not found
        """
        agents_dir = Path(__file__).parent
        file_path = agents_dir / f"{platform_name}_agent.py"

        if not file_path.exists():
            return None

        # Load module dynamically
        spec = importlib.util.spec_from_file_location(
            f"agents.{platform_name}_agent",
            file_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get agent class
        class_name = f"{platform_name.title()}Agent"
        agent_class = getattr(module, class_name, None)

        return agent_class

    @classmethod
    def update_domains_file(cls, domains: List[str], domains_file: Path = None):
        """
        Update domains.txt file with new domains

        Args:
            domains: List of domain URLs to add
            domains_file: Path to domains.txt (default: data/domains.txt)
        """
        if domains_file is None:
            domains_file = Path(__file__).parent.parent / "data" / "domains.txt"

        # Read existing domains
        existing_domains = set()
        if domains_file.exists():
            with open(domains_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        existing_domains.add(line)

        # Add new domains
        new_domains = [d for d in domains if d not in existing_domains]

        if new_domains:
            with open(domains_file, 'a', encoding='utf-8') as f:
                f.write('\n')
                for domain in new_domains:
                    f.write(f"{domain}\n")

            print(f"[TEMPLATE] Added {len(new_domains)} new domains to {domains_file}")
        else:
            print(f"[TEMPLATE] No new domains to add")


class AgentGenerator:
    """
    High-level interface for generating and managing agents
    """

    @classmethod
    def create_agent(
        cls,
        platform_name: str,
        base_url: str,
        supported_domains: List[str],
        selectors: Dict[str, str],
        search_url: str = None,
        url_params: Dict[str, str] = None,
        save_to_file: bool = True,
        update_domains: bool = True
    ):
        """
        Create a new platform agent with all necessary setup

        Args:
            platform_name: Name of platform
            base_url: Base URL for search
            supported_domains: List of supported domains
            selectors: CSS selectors for parsing
            search_url: Complete search URL pattern with {query} placeholder (optional)
            url_params: URL parameters (optional, deprecated in favor of search_url)
            save_to_file: Whether to save agent to file
            update_domains: Whether to update domains.txt

        Returns:
            Agent class instance
        """
        print(f"\n[GENERATOR] Creating agent for: {platform_name}")

        # Generate agent code
        agent_code = AgentTemplate.generate_agent(
            platform_name=platform_name,
            base_url=base_url,
            supported_domains=supported_domains,
            selectors=selectors,
            search_url=search_url,
            url_params=url_params
        )

        # Save to file if requested
        if save_to_file:
            AgentTemplate.save_agent(platform_name, agent_code)

        # Update domains.txt if requested
        if update_domains:
            AgentTemplate.update_domains_file(supported_domains)

        # Load and return agent class
        agent_class = AgentTemplate.load_agent_class(platform_name)

        if agent_class:
            print(f"[GENERATOR] Successfully created {platform_name} agent")
            return agent_class()
        else:
            print(f"[GENERATOR] Failed to load {platform_name} agent")
            return None
