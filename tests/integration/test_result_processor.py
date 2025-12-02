# tests/integration/test_result_processor.py
import os
import pytest
import json
from unittest.mock import MagicMock
from result_processor import ResultProcessor

# API Key needed to instantiate the processor
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Skip this test if GOOGLE_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not GOOGLE_API_KEY,
    reason="This test requires GOOGLE_API_KEY to instantiate ResultProcessor."
)

@pytest.fixture
def mock_llm_response():
    """Provides a mock response from the Gemini LLM for filtering."""
    # This is the JSON data our mock LLM will "return"
    mock_scores = [
        {"index": 0, "score": 9, "reason": "Highly relevant, matches preference."}, 
        {"index": 1, "score": 4, "reason": "Not relevant to user preference."}, 
        {"index": 2, "score": 7, "reason": "Relevant, but not a perfect match."} 
    ]
    
    # langchain_google_genai returns an AIMessage object with the content
    # We create a mock object that mimics this structure.
    mock_ai_message = MagicMock()
    mock_ai_message.content = json.dumps(mock_scores)
    return mock_ai_message

def test_filter_results_with_mock_llm(mocker, mock_llm_response):
    """
    Tests the ResultProcessor's filtering logic using a mocked LLM call.
    It verifies that the processor correctly interprets the LLM's JSON response
    and filters the results based on the scores.
    """
    # --- 1. Setup ---
    processor = ResultProcessor()
    
    # We must have an LLM instance to proceed
    assert processor.llm is not None, "ResultProcessor could not be initialized. Check GOOGLE_API_KEY."

    # Mock the 'invoke' method of the llm instance to return our predefined response
    mocker.patch.object(processor.llm, 'invoke', return_value=mock_llm_response)

    # Create some dummy results to be filtered
    dummy_results = [
        {"title": "Result 1", "content": "Content 1"},
        {"title": "Result 2", "content": "Content 2"},
        {"title": "Result 3", "content": "Content 3"},
    ]
    
    # --- 2. Execution ---
    filtered_results = processor.filter_results(
        results=dummy_results,
        detail="some detail",
        keywords=["keyword"],
        platform="test_platform"
    )

    # --- 3. Assertion ---
    # The mock scores were: 9, 4, 7. We expect scores >= 5 to be kept.
    # So, Result 1 (score 9) and Result 3 (score 7) should be in the output.
    assert len(filtered_results) == 2
    
    # Check that the correct items were kept and scores were added
    result_titles = [res['title'] for res in filtered_results]
    assert "Result 1" in result_titles
    assert "Result 3" in result_titles
    assert "Result 2" not in result_titles # This one had a score of 4

    # Check the first filtered result for correctness
    assert filtered_results[0]['title'] == "Result 1"
    assert filtered_results[0]['relevance_score'] == 9
    assert "Highly relevant" in filtered_results[0]['relevance_reason']

    print("\n[TEST] ResultProcessor filtering logic test passed successfully.")
