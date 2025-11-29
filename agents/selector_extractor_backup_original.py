"""
BACKUP: Original selector_extractor.py prompt (2025-11-26)

This is a backup of the original visual-interaction based approach
before switching to the hybrid snapshot + screenshot method.
"""

ORIGINAL_PROMPT_TEMPLATE = """You are a web scraping expert analyzing {platform_name}.

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
