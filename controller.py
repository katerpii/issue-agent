"""
Controller Agent - Main orchestrator for issue notification system

This agent receives user form input and coordinates platform agents
to collect relevant issues from various platforms.
"""
from typing import List, Dict, Any
from models.user_form import UserForm
from agents import RedditAgent, BaseAgent, GoogleAgent
from result_processor import ResultProcessor


class ControllerAgent:
    """
    Controller Agent that orchestrates platform agents

    This agent:
    1. Receives user form input (keywords, platforms, date range, detail)
    2. Dispatches tasks to appropriate platform agents
    3. Collects and aggregates results from platform agents
    """

    def __init__(self):
        """Initialize controller agent with available platform agents"""
        self.available_agents: Dict[str, BaseAgent] = {
            'google': GoogleAgent(),
            'reddit': RedditAgent()
        }

        # Initialize result processor for filtering and summarization
        try:
            print("[CONTROLLER] Initializing ResultProcessor...")
            self.processor = ResultProcessor()
            print("[CONTROLLER] ResultProcessor initialized successfully")
        except Exception as e:
            print(f"[CONTROLLER] Failed to initialize ResultProcessor: {e}")
            import traceback
            traceback.print_exc()
            self.processor = None

        # Auto-discover and load generated agents from agents/ directory
        self._load_generated_agents()

    def run(self, user_form: UserForm) -> Dict[str, Any]:
        """
        Execute the controller agent workflow

        Args:
            user_form: User form containing search criteria

        Returns:
            Processed results with filtering and summary
        """
        print("\n" + "=" * 50)
        print("CONTROLLER AGENT - Starting execution")
        print("=" * 50)
        print(user_form)
        print("=" * 50)

        results_by_platform = {}

        # Iterate through requested platforms
        for platform in user_form.platforms:
            agent = self._get_agent(platform)

            if agent:
                print(f"\n[CONTROLLER] Dispatching to {platform} agent...")

                try:
                    # Execute platform agent
                    results = agent.crawl(
                        keywords=user_form.keywords,
                        detail=user_form.detail
                    )

                    # Store results by platform for processing
                    results_by_platform[platform] = results
                    print(f"[CONTROLLER] Received {len(results)} results from {platform}")

                except Exception as e:
                    print(f"[CONTROLLER] Error executing {platform} agent: {e}")

            else:
                print(f"[CONTROLLER] Agent for '{platform}' not found - attempting auto-generation...")

                # Try to auto-generate the agent
                success = self._auto_generate_agent(platform)

                if success:
                    # Retry with newly generated agent
                    agent = self._get_agent(platform)
                    if agent:
                        try:
                            results = agent.crawl(
                                keywords=user_form.keywords,
                                detail=user_form.detail
                            )

                            # Store results by platform for processing
                            results_by_platform[platform] = results
                            print(f"[CONTROLLER] Received {len(results)} results from {platform}")
                        except Exception as e:
                            print(f"[CONTROLLER] Error executing auto-generated {platform} agent: {e}")
                else:
                    print(f"[CONTROLLER] Warning: No agent found for platform '{platform}'")
                    print(f"[CONTROLLER] Available platforms: {', '.join(self.available_agents.keys())}")

        print("\n" + "=" * 50)
        total_raw = sum(len(r) for r in results_by_platform.values())
        print(f"[CONTROLLER] Total raw results collected: {total_raw}")
        print("=" * 50)

        # Process results: filter + summarize
        if self.processor:
            processed_results = self.processor.process_all_results(
                results_by_platform=results_by_platform,
                detail=user_form.detail,
                keywords=user_form.keywords
            )
        else:
            # No processor - return raw results
            print("[CONTROLLER] No ResultProcessor available - returning raw results")
            total = sum(len(r) for r in results_by_platform.values())
            processed_results = {
                'summary': f'Found {total} results across {len(results_by_platform)} platforms. (No filtering applied)',
                'total_results': total,
                'results_by_platform': results_by_platform
            }

        print("\n" + "=" * 50)
        print(f"[CONTROLLER] Processing complete")
        print(f"  Filtered results: {processed_results.get('total_results', 0)}")
        print("=" * 50)

        return processed_results

    def _get_agent(self, platform: str) -> BaseAgent:
        """
        Get the appropriate agent for the given platform

        Args:
            platform: Platform name

        Returns:
            Platform agent instance or None if not found
        """
        return self.available_agents.get(platform.lower())

    def get_available_platforms(self) -> List[str]:
        """Get list of available platform names"""
        return list(self.available_agents.keys())

    def add_agent(self, platform: str, agent: BaseAgent):
        """
        Add a new platform agent dynamically

        Args:
            platform: Platform name
            agent: Agent instance
        """
        self.available_agents[platform.lower()] = agent
        print(f"[CONTROLLER] Added agent for platform: {platform}")

    def _load_generated_agents(self):
        """
        Auto-discover and load agent files from agents/ directory

        This loads all *_agent.py files (except base_agent.py) that were
        generated during runtime.
        """
        from pathlib import Path
        import importlib.util

        # Get agents directory
        agents_dir = Path(__file__).parent / 'agents'

        if not agents_dir.exists():
            return

        # Find all *_agent.py files
        agent_files = list(agents_dir.glob('*_agent.py'))

        for agent_file in agent_files:
            platform_name = agent_file.stem.replace('_agent', '')

            # Skip agents we already have and base_agent
            if platform_name in ['base', 'google', 'reddit']:
                continue

            # Skip if already loaded
            if platform_name in self.available_agents:
                continue

            try:
                # Dynamically load the module
                spec = importlib.util.spec_from_file_location(
                    f"agents.{agent_file.stem}",
                    agent_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find the Agent class (e.g., GithubAgent)
                class_name = f"{platform_name.replace('.', '_').replace('-', '_').title().replace('_', '')}Agent"

                # Try different class name variations
                agent_class = None
                for attr_name in dir(module):
                    if attr_name.endswith('Agent') and attr_name != 'BaseAgent':
                        agent_class = getattr(module, attr_name)
                        break

                if agent_class and callable(agent_class):
                    # Instantiate and add to available agents
                    agent_instance = agent_class()
                    self.available_agents[platform_name.lower()] = agent_instance
                    print(f"[CONTROLLER] Auto-loaded agent: {platform_name}")

            except Exception as e:
                # Silently skip agents that fail to load
                print(f"[CONTROLLER] Could not load {platform_name} agent: {e}")
                continue

    def _filter_by_date(self, results: List[Dict[str, Any]], start_date, end_date) -> List[Dict[str, Any]]:
        """
        Filter results by date range

        Args:
            results: List of results to filter
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Filtered list of results
        """
        from datetime import datetime

        filtered = []
        for result in results:
            if 'date' not in result:
                # Include results without date
                filtered.append(result)
                continue

            result_date = result['date']

            # Convert to datetime if needed
            if isinstance(result_date, str):
                try:
                    result_date = datetime.fromisoformat(result_date.replace('Z', '+00:00'))
                except:
                    # If parsing fails, include the result
                    filtered.append(result)
                    continue

            # Remove timezone info for comparison if present
            if hasattr(result_date, 'tzinfo') and result_date.tzinfo is not None:
                result_date = result_date.replace(tzinfo=None)
            if hasattr(start_date, 'tzinfo') and start_date.tzinfo is not None:
                start_date = start_date.replace(tzinfo=None)
            if hasattr(end_date, 'tzinfo') and end_date.tzinfo is not None:
                end_date = end_date.replace(tzinfo=None)

            # Check if date is within range
            if start_date <= result_date <= end_date:
                filtered.append(result)

        return filtered

    def _auto_generate_agent(self, platform: str) -> bool:
        """
        Attempt to auto-generate an agent for the given platform

        Args:
            platform: Platform name

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"[CONTROLLER] 🤖 Using LLM to analyze {platform} and extract selectors...")
            from agents.selector_extractor import auto_generate_agent_config
            from agents.agent_template import AgentGenerator
            import asyncio

            # Generate config - handle both sync and async contexts
            try:
                loop = asyncio.get_running_loop()
                # Already in event loop - create task in thread pool
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    config = pool.submit(
                        lambda: asyncio.run(auto_generate_agent_config(platform))
                    ).result()
            except RuntimeError:
                # No event loop - CLI mode (uv run main.py)
                config = asyncio.run(auto_generate_agent_config(platform))

            if config:
                # Create agent
                generator = AgentGenerator()
                new_agent = generator.create_agent(
                    platform_name=config['platform_name'],
                    base_url=config['base_url'],
                    search_url=config['search_url'],  # Pass the actual search URL pattern
                    supported_domains=config['supported_domains'],
                    selectors=config['selectors']
                )

                # Add to available agents
                self.add_agent(platform, new_agent)
                print(f"[CONTROLLER] ✓ Successfully auto-generated {platform} agent")
                return True
            else:
                print(f"[CONTROLLER] Failed to generate config for {platform}")
                print(f"[CONTROLLER] ✗ Failed to auto-generate {platform} agent")
                return False

        except Exception as e:
            print(f"[CONTROLLER] Error during auto-generation: {e}")
            import traceback
            traceback.print_exc()
            print(f"[CONTROLLER] ✗ Failed to auto-generate {platform} agent")
            return False

    def __repr__(self) -> str:
        platforms = ', '.join(self.available_agents.keys())
        return f"ControllerAgent(platforms=[{platforms}])"
