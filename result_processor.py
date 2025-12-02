"""
Result Processor - LLM-based filtering and summarization

This module processes crawled results by:
1. Filtering based on user's detail preferences
2. Scoring relevance to keywords
3. Generating summaries of filtered results
"""
from typing import List, Dict, Any
import json

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

LLM_AVAILABLE = ANTHROPIC_AVAILABLE or GEMINI_AVAILABLE


class ResultProcessor:
    """
    Process crawled results with LLM-based filtering and summarization
    """

    def __init__(self):
        """Initialize result processor with LLM (Claude or Gemini)"""
        self.llm = None
        self.llm_type = None  # 'anthropic' or 'gemini'

        # Debug: Print available LLMs
        print(f"[PROCESSOR] DEBUG: GEMINI_AVAILABLE={GEMINI_AVAILABLE}, ANTHROPIC_AVAILABLE={ANTHROPIC_AVAILABLE}")

        if not LLM_AVAILABLE:
            print("[PROCESSOR] No LLM available - filtering and summarization disabled")
            print("[PROCESSOR] Install: pip install langchain-google-genai (Gemini, FREE!)")
            print("[PROCESSOR] Or: pip install langchain-anthropic (Claude, paid)")
            return

        import os

        # Debug: Check environment variables
        gemini_key = os.getenv('GOOGLE_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        print(f"[PROCESSOR] DEBUG: GOOGLE_API_KEY={'set' if gemini_key else 'not set'}")
        print(f"[PROCESSOR] DEBUG: ANTHROPIC_API_KEY={'set' if anthropic_key else 'not set'}")

        # Try Gemini first (FREE!)
        if GEMINI_AVAILABLE and gemini_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-lite",  # Free tier
                    google_api_key=gemini_key,
                    temperature=0.1
                )
                self.llm_type = 'gemini'
                print("[PROCESSOR] ✓ Initialized with Gemini 1.5 Flash (FREE!)")
                return
            except Exception as e:
                print(f"[PROCESSOR] Failed to initialize Gemini: {e}")

        # Fallback to Claude (paid)
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if ANTHROPIC_AVAILABLE and anthropic_key:
            try:
                self.llm = ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                    anthropic_api_key=anthropic_key
                )
                self.llm_type = 'anthropic'
                print("[PROCESSOR] ✓ Initialized with Claude 3.5 Sonnet (paid)")
                return
            except Exception as e:
                print(f"[PROCESSOR] Failed to initialize Claude: {e}")

        print("[PROCESSOR] No LLM could be initialized - filtering disabled")
        print("[PROCESSOR] Get FREE Gemini API key: https://aistudio.google.com/app/apikey")

    def filter_results(
        self,
        results: List[Dict[str, Any]],
        detail: str,
        keywords: List[str],
        platform: str
    ) -> List[Dict[str, Any]]:
        """
        Filter results based on relevance to keywords and detail

        Args:
            results: List of crawled results from a single platform
            detail: User's detail/preference description
            keywords: List of keywords
            platform: Platform name

        Returns:
            Filtered list of results with relevance scores
        """
        if not self.llm or not results:
            # No filtering - return all results
            return results

        print(f"[PROCESSOR] Filtering {len(results)} results from {platform}...")

        # Prepare results summary for LLM (limit content length)
        results_summary = []
        for i, result in enumerate(results[:50]):  # Limit to 50 results
            results_summary.append({
                'index': i,
                'title': result.get('title', '')[:200],
                'url': result.get('url', ''),
                'content': result.get('content', '')[:1500]  # Increased from 500 to 1500 chars
            })

        filter_prompt = f"""You are filtering search results based on user preferences.

User's keywords: {', '.join(keywords)}
User's detail/preferences: "{detail}"

Analyze these {len(results_summary)} search results and score each from 0-10 based on relevance to the user's keywords and preferences.

Results:
{json.dumps(results_summary, indent=2, ensure_ascii=False)}

IMPORTANT:
- Score 8-10: Highly relevant to keywords AND matches user preferences
- Score 5-7: Relevant to keywords but doesn't fully match preferences
- Score 0-4: Not relevant or doesn't match preferences
- If detail is empty, focus only on keyword relevance

Return ONLY a JSON array of objects with format:
[
  {{"index": 0, "score": 8, "reason": "brief reason"}},
  {{"index": 1, "score": 3, "reason": "brief reason"}},
  ...
]

Return ONLY valid JSON, no other text."""

        try:
            # Call LLM based on type
            print(f"[PROCESSOR] Calling {self.llm_type} LLM for filtering...")

            if self.llm_type == 'gemini':
                response = self.llm.invoke(filter_prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                print(f"[PROCESSOR] Received response from Gemini ({len(response_text)} chars)")
            elif self.llm_type == 'anthropic':
                response = self.llm.invoke(filter_prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                print(f"[PROCESSOR] Received response from Claude ({len(response_text)} chars)")
            elif self.llm_type == 'browser_use':
                # Use Agent for ChatBrowserUse
                import asyncio

                async def run_agent():
                    browser = Browser(use_cloud=True)
                    agent = Agent(
                        task=filter_prompt,
                        llm=self.llm,
                        browser=browser
                    )
                    result = await agent.run()
                    # Browser is auto-closed by agent, no need to manually close
                    return result

                # Run agent
                try:
                    loop = asyncio.get_running_loop()
                    # Already in event loop - use thread pool
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        result = pool.submit(lambda: asyncio.run(run_agent())).result()
                except RuntimeError:
                    # No event loop - direct run
                    result = asyncio.run(run_agent())

                # Extract text from result
                if hasattr(result, 'final_result'):
                    response_text = str(result.final_result())
                else:
                    response_text = str(result)
            else:
                print(f"[PROCESSOR] Unknown LLM type: {self.llm_type}")
                return results

            # Extract JSON from response
            response_text = response_text.strip()

            # Remove markdown code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            # Handle escaped newlines from ChatBrowserUse
            if '\\n' in response_text:
                # Replace escaped newlines with actual newlines for JSON parsing
                response_text = response_text.replace('\\n', '\n')

            # Try to find JSON array in response
            if not response_text.startswith('['):
                # Search for JSON array in text
                import re
                json_match = re.search(r'\[[\s\S]*\]', response_text)
                if json_match:
                    response_text = json_match.group(0)

            print(f"[PROCESSOR] DEBUG: Parsing JSON response (first 200 chars): {response_text[:200]}")
            scores = json.loads(response_text)

            # Filter results with score >= 5
            filtered = []
            for score_data in scores:
                idx = score_data['index']
                score = score_data['score']
                reason = score_data.get('reason', '')

                if score >= 5 and idx < len(results):
                    result = results[idx].copy()
                    result['relevance_score'] = score
                    result['relevance_reason'] = reason
                    filtered.append(result)

            print(f"[PROCESSOR] Filtered to {len(filtered)} relevant results (score >= 5)")
            return filtered

        except json.JSONDecodeError as e:
            print(f"[PROCESSOR] JSON parsing failed: {e}")
            print(f"[PROCESSOR] Raw response was: {response_text[:500]}")
            # Return all results with score 0
            for result in results:
                result['relevance_score'] = 0
                result['relevance_reason'] = 'Filtering failed - JSON parse error'
            return results
        except Exception as e:
            print(f"[PROCESSOR] Filtering failed: {e}")
            import traceback
            traceback.print_exc()
            # Return all results with score 0
            for result in results:
                result['relevance_score'] = 0
                result['relevance_reason'] = 'Filtering failed - unexpected error'
            return results

    def summarize_results(
        self,
        filtered_by_platform: Dict[str, List[Dict[str, Any]]],
        detail: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Generate summary of filtered results across all platforms

        Args:
            filtered_by_platform: Dict mapping platform names to filtered results
            detail: User's detail/preferences
            keywords: List of keywords

        Returns:
            Dictionary containing summary and filtered results
        """
        if not self.llm:
            # No summarization - return results as-is
            return {
                'summary': 'LLM not available - no summary generated',
                'total_results': sum(len(r) for r in filtered_by_platform.values()),
                'results_by_platform': filtered_by_platform
            }

        print("[PROCESSOR] Generating summary...")

        # Count results
        total = sum(len(results) for results in filtered_by_platform.values())

        if total == 0:
            return {
                'summary': 'No relevant results found matching your criteria.',
                'total_results': 0,
                'results_by_platform': filtered_by_platform
            }

        # Prepare summary data (top results from each platform)
        summary_data = {}
        for platform, results in filtered_by_platform.items():
            if results:
                # Get top 5 results sorted by score
                top_results = sorted(
                    results,
                    key=lambda x: x.get('relevance_score', 0),
                    reverse=True
                )[:5]

                summary_data[platform] = [
                    {
                        'title': r.get('title', '')[:150],
                        'score': r.get('relevance_score', 0),
                        'reason': r.get('relevance_reason', '')
                    }
                    for r in top_results
                ]

        summarize_prompt = f"""Generate a concise summary of search results.

User's keywords: {', '.join(keywords)}
User's preferences: "{detail}"

Results found: {total} relevant items across {len(filtered_by_platform)} platforms

Top results by platform:
{json.dumps(summary_data, indent=2, ensure_ascii=False)}

Generate a concise 2-3 sentence summary that:
1. Highlights the most relevant findings
2. Mentions which platforms had the best results
3. Notes any patterns or themes across results
4. Relates findings to user's preferences (if provided)

Return ONLY the summary text, no extra formatting."""

        try:
            # Call LLM based on type
            print(f"[PROCESSOR] Calling {self.llm_type} LLM for summarization...")

            if self.llm_type == 'gemini':
                response = self.llm.invoke(summarize_prompt)
                summary_text = response.content if hasattr(response, 'content') else str(response)
                print(f"[PROCESSOR] Received summary from Gemini ({len(summary_text)} chars)")
            elif self.llm_type == 'anthropic':
                response = self.llm.invoke(summarize_prompt)
                summary_text = response.content if hasattr(response, 'content') else str(response)
                print(f"[PROCESSOR] Received summary from Claude ({len(summary_text)} chars)")
            elif self.llm_type == 'browser_use':
                # Use Agent for ChatBrowserUse
                import asyncio

                async def run_agent():
                    browser = Browser(use_cloud=True)
                    agent = Agent(
                        task=summarize_prompt,
                        llm=self.llm,
                        browser=browser
                    )
                    result = await agent.run()
                    # Browser is auto-closed by agent, no need to manually close
                    return result

                # Run agent
                try:
                    loop = asyncio.get_running_loop()
                    # Already in event loop - use thread pool
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        result = pool.submit(lambda: asyncio.run(run_agent())).result()
                except RuntimeError:
                    # No event loop - direct run
                    result = asyncio.run(run_agent())

                # Extract text from result
                if hasattr(result, 'final_result'):
                    summary_text = str(result.final_result())
                else:
                    summary_text = str(result)
            else:
                print(f"[PROCESSOR] Unknown LLM type: {self.llm_type}")
                return {
                    'summary': f'Found {total} results across {len(filtered_by_platform)} platforms.',
                    'total_results': total,
                    'results_by_platform': filtered_by_platform
                }

            summary_text = summary_text.strip()

            # Remove any markdown formatting or extra whitespace
            if '```' in summary_text:
                summary_text = summary_text.split('```')[0].strip()

            print(f"[PROCESSOR] Summary: {summary_text[:150]}...")

            print("[PROCESSOR] Summary generation complete")

            return {
                'summary': summary_text,
                'total_results': total,
                'results_by_platform': filtered_by_platform,
                'top_results': summary_data
            }

        except Exception as e:
            print(f"[PROCESSOR] Summarization failed: {e}")
            return {
                'summary': f'Found {total} relevant results across {len(filtered_by_platform)} platforms.',
                'total_results': total,
                'results_by_platform': filtered_by_platform
            }

    def process_all_results(
        self,
        results_by_platform: Dict[str, List[Dict[str, Any]]],
        detail: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Complete processing pipeline: filter + summarize

        Args:
            results_by_platform: Dict mapping platform names to raw results
            detail: User's detail/preferences
            keywords: List of keywords

        Returns:
            Processed results with filtering and summary
        """
        print("\n[PROCESSOR] Starting result processing...")

        # Step 1: Filter results for each platform
        filtered_by_platform = {}
        for platform, results in results_by_platform.items():
            if results:
                filtered = self.filter_results(
                    results=results,
                    detail=detail,
                    keywords=keywords,
                    platform=platform
                )
                if filtered:
                    filtered_by_platform[platform] = filtered

        # Step 2: Generate summary
        processed = self.summarize_results(
            filtered_by_platform=filtered_by_platform,
            detail=detail,
            keywords=keywords
        )

        print("[PROCESSOR] Processing complete!")
        return processed
