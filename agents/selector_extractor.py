"""
ChatBrowserUse-based CSS selector extractor

This module uses ChatBrowserUse's Agent to analyze web pages and extract
appropriate CSS selectors for crawling search results from any platform.
"""
from typing import Dict, Optional
from urllib.parse import quote_plus
import json
import re

try:
    from browser_use import Browser, Agent, ChatBrowserUse
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    print("[WARNING] browser-use not installed.")


class SelectorExtractor:
    """
    Extract CSS selectors from websites using ChatBrowserUse Agent
    """

    def __init__(self):
        """
        Initialize selector extractor

        Uses BROWSER_USE_API_KEY from environment (same key used by ChatBrowserUse)
        """
        if not BROWSER_USE_AVAILABLE:
            print("[WARNING] browser-use not installed. Cannot use ChatBrowserUse Agent.")
            print("  Install with: pip install browser-use")

    async def extract_selectors_from_url(
        self,
        platform_name: str,
        search_url: str,
        sample_query: str = "test"
    ) -> Optional[Dict[str, str]]:
        """
        Extract CSS selectors by analyzing a live search page using ChatBrowserUse Agent

        Args:
            platform_name: Name of the platform
            search_url: Search URL template (use {query} as placeholder)
            sample_query: Sample search query to use

        Returns:
            Dictionary of CSS selectors or None if failed
        """
        print(f"\n[SELECTOR EXTRACTOR] Analyzing {platform_name} with ChatBrowserUse Agent...")

        # Use ChatBrowserUse Agent to analyze the page directly
        selectors = await self._extract_selectors_with_agent(
            platform_name,
            search_url,
            sample_query
        )

        return selectors

    async def _extract_selectors_with_agent(
        self,
        platform_name: str,
        search_url: str,
        sample_query: str
    ) -> Optional[Dict[str, str]]:
        """
        Use ChatBrowserUse Agent to analyze web page and extract CSS selectors

        Args:
            platform_name: Platform name
            search_url: Search URL template
            sample_query: Sample query to use

        Returns:
            Dictionary of selectors or None if failed
        """
        if not BROWSER_USE_AVAILABLE:
            print(f"  [ERROR] ChatBrowserUse not available")
            return None

        # Extract base domain from search_url
        from urllib.parse import urlparse
        parsed = urlparse(search_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"

        print(f"  Agent will visit: {base_domain} and search for '{sample_query}'")

        task_prompt = f"""You are a web scraping expert analyzing {platform_name}.

Your task: Find CSS selectors by VISUALLY INTERACTING with the page.

STRATEGY (work quickly):

Step 1: Navigate to {base_domain}

Step 2: Do not use DOM, Find the search input VISUALLY and search for "{sample_query}"

Step 3: Wait for search results to appear and capture the search URL:
- After search results load, use evaluate() to get the current URL:
  ```javascript
  window.location.href
  ```
- This will show the search URL pattern (e.g., ?q=test, ?search=test, ?s=test)

Step 4: Inspect the first search result:
- Hover over the first result's title to see it highlighted
- Use extract_content action on that title element to get its class

Step 5: Find the container and other elements:
- Use ONE simple evaluate() call to get ALL selectors at once:
  ```javascript
  (function() {{
    const results = [];
    const titleLinks = document.querySelectorAll('a[href]');

    for (let link of titleLinks) {{
      const text = link.textContent.trim();
      if (text.length > 10 && text.length < 200) {{
        const container = link.closest('div, article, li, section');
        if (container) {{
          const dateEl = Array.from(container.querySelectorAll('*')).find(el =>
            /ago|hour|day|posted|created|opened|time/i.test(el.textContent) &&
            el.textContent.length < 100
          );

          // Find title element (h1-h6 containing the link)
          const titleParent = link.closest('h1, h2, h3, h4, h5, h6');

          // Find content element
          const contentEl = container.querySelector('p, div.excerpt, div.description, div.content');

          results.push({{
            container_tag: container.tagName.toLowerCase(),
            container_class: container.className,
            title_tag: titleParent ? titleParent.tagName.toLowerCase() : 'unknown',
            title_class: titleParent ? titleParent.className : '',
            link_class: link.className,
            content_tag: contentEl ? contentEl.tagName.toLowerCase() : 'p',
            content_class: contentEl ? contentEl.className : '',
            date_tag: dateEl ? dateEl.tagName.toLowerCase() : 'not found',
            date_class: dateEl ? dateEl.className : 'not found',
            date_text: dateEl ? dateEl.textContent.substring(0,30) : 'not found'
          }});

          if (results.length >= 3) break;
        }}
      }}
    }}

    return JSON.stringify(results, null, 2);
  }})()
  ```

Step 6: Build PRECISE selectors from Step 5 results:
- For container: use most common container_tag + container_class (e.g., "div.latest-post-block-content")
- For title: use title_tag + title_class + " a" (e.g., "h3.post-title a")
- For content: use content_tag + content_class (e.g., "div.post-excerpt-box p")
- For date: use date_tag + date_class (e.g., "li.slider-meta-date")
- IMPORTANT: Always include the tag name (h2, h3, div, etc.) in your selectors!

Step 7: Return JSON with all selectors found

IMPORTANT:
- Work VISUALLY - click things, look at the page
- Use evaluate() to GET selectors of elements you found visually
- Even dynamic classes (Box-sc-62in7e-0) are fine - USE THEM
- Verify container selector matches MULTIPLE results

Respond in this EXACT format (JSON):
{{
  "search_url": "The actual search results URL you're on (from Step 3)",
  "container_selector": "CSS selector for result container",
  "title_selector": "CSS selector for title within container",
  "link_selector": "CSS selector for link within container",
  "content_selector": "CSS selector for content/excerpt within container",
  "date_selector": "CSS selector for date within container OR 'not available'",
  "confidence": "high/medium/low",
  "notes": "Any important observations"
}}

Only return valid JSON, nothing else."""

        try:
            print(f"  Running Agent...")

            # Create ChatBrowserUse Agent (uses Browser Use Cloud's built-in LLM)
            browser = Browser(use_cloud=True)
            llm = ChatBrowserUse()
            agent = Agent(task=task_prompt, llm=llm, browser=browser)

            result = await agent.run()

            # Extract the final result from agent history
            # The result is in the last action's output
            response_text = ""
            if hasattr(result, 'final_result'):
                response_text = str(result.final_result())
            elif hasattr(result, 'history') and result.history:
                # Get the last action's output
                last_action = result.history[-1]
                if hasattr(last_action, 'result') and last_action.result:
                    for action_result in last_action.result:
                        if hasattr(action_result, 'extracted_content'):
                            response_text = action_result.extracted_content
                            break
                        elif hasattr(action_result, 'text'):
                            response_text = action_result.text
                            break

            # Fallback: convert result to string
            if not response_text:
                response_text = str(result)

            print(f"  Raw response: {response_text[:200]}...")

            # Extract JSON from response (might be wrapped in markdown or other text)
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            # Try to find JSON in the text
            if not response_text or not response_text.strip().startswith('{'):
                # Search for JSON pattern in the text
                json_match = re.search(r'\{[^{}]*"container_selector"[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)

            # Handle escaped JSON (if the JSON is returned as a string with escaped quotes)
            if response_text.startswith('{') and '\\"' in response_text:
                # Try to decode escaped JSON
                try:
                    response_text = json.loads('"' + response_text + '"')
                except:
                    pass  # If it fails, continue with original

            selectors = json.loads(response_text)

            print(f"  ✓ Extracted selectors (confidence: {selectors.get('confidence', 'unknown')})")
            print(f"    Container: {selectors.get('container_selector', 'N/A')}")
            print(f"    Title: {selectors.get('title_selector', 'N/A')}")
            print(f"    Link: {selectors.get('link_selector', 'N/A')}")
            print(f"    Content: {selectors.get('content_selector', 'N/A')}")

            if selectors.get('notes'):
                print(f"    Notes: {selectors['notes']}")

            return selectors

        except Exception as e:
            print(f"  [ERROR] Agent extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            try:
                await browser.close()
            except:
                pass

    def detect_platform_config(self, platform_name: str) -> Dict[str, any]:
        """
        Detect common platform configurations

        Args:
            platform_name: Platform name

        Returns:
            Configuration dictionary with base_url and search_url
        """
        platform_configs = {
            'stackoverflow': {
                'base_url': 'https://stackoverflow.com/search',
                'search_url': 'https://stackoverflow.com/search?q={query}',
                'supported_domains': [
                    'https://stackoverflow.com/search',
                    'https://stackoverflow.com'
                ]
            },
            'github': {
                'base_url': 'https://github.com/search',
                'search_url': 'https://github.com/search?q={query}&type=Issues',
                'supported_domains': [
                    'https://github.com/search',
                    'https://github.com'
                ]
            },
            'hackernews': {
                'base_url': 'https://hn.algolia.com',
                'search_url': 'https://hn.algolia.com/?q={query}',
                'supported_domains': [
                    'https://news.ycombinator.com',
                    'https://hn.algolia.com'
                ]
            }
        }

        if platform_name in platform_configs:
            return platform_configs[platform_name]

        # Try to infer from platform name
        return {
            'base_url': f'https://{platform_name}.com/search',
            'search_url': f'https://{platform_name}.com/search?q={{query}}',
            'supported_domains': [
                f'https://{platform_name}.com',
                f'https://www.{platform_name}.com'
            ]
        }


async def auto_generate_agent_config(
    platform_name: str,
    search_url: Optional[str] = None
) -> Optional[Dict[str, any]]:
    """
    Automatically generate complete agent configuration for a platform

    Args:
        platform_name: Platform name or URL
        search_url: Search URL (optional, will be inferred if not provided)

    Returns:
        Complete configuration dict for AgentGenerator.create_agent()
    """
    from urllib.parse import urlparse

    # Clean platform name if it's a URL
    actual_base_url = None
    if platform_name.startswith('http'):
        parsed = urlparse(platform_name)
        # Extract domain without www
        domain = parsed.netloc.replace('www.', '')
        # Use the domain name without TLD as platform name
        platform_name_clean = domain.split('.')[0]
        # Store the actual base URL
        actual_base_url = f"{parsed.scheme}://{parsed.netloc}"
        if not search_url:
            search_url = actual_base_url
    else:
        platform_name_clean = platform_name.lower().replace(' ', '_')

    extractor = SelectorExtractor()

    # Get platform config (this might be a guess)
    platform_config = extractor.detect_platform_config(platform_name_clean)

    # Override with actual URLs if we have them
    if actual_base_url:
        platform_config['base_url'] = actual_base_url
        platform_config['supported_domains'] = [actual_base_url]

    if search_url:
        platform_config['search_url'] = search_url

    # Extract selectors
    selectors = await extractor.extract_selectors_from_url(
        platform_name=platform_name_clean,
        search_url=platform_config['search_url'],
        sample_query='test'
    )

    if not selectors:
        print(f"[ERROR] Failed to extract selectors for {platform_name_clean}")
        return None

    # Use the actual search_url from selectors if available
    if selectors.get('search_url'):
        actual_search_url = selectors['search_url']
        # Replace the test query with {query} placeholder
        for test_param in ['test', 'Test', 'TEST']:
            if test_param in actual_search_url:
                actual_search_url = actual_search_url.replace(test_param, '{query}')
                break
        platform_config['search_url'] = actual_search_url

    # Build complete config
    config = {
        'platform_name': platform_name_clean,
        'base_url': platform_config['base_url'],
        'search_url': platform_config['search_url'],  # Include the actual search URL pattern
        'supported_domains': platform_config['supported_domains'],
        'selectors': {
            'container_selector': selectors.get('container_selector'),
            'title_selector': selectors.get('title_selector'),
            'link_selector': selectors.get('link_selector'),
            'content_selector': selectors.get('content_selector') if not selectors.get('content_selector', '').startswith('not available') else 'p',
            'date_selector': selectors.get('date_selector', 'time')
        }
    }

    return config
