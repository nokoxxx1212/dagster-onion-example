import pytest
import pandas as pd
from unittest.mock import Mock
import tempfile
import os
from pathlib import Path


@pytest.fixture
def sample_wikipedia_data():
    """Sample Wikipedia page data for testing"""
    return {
        "pageid": [1, 2, 3, 4, 5],
        "title": [
            "List of countries",
            "Wikipedia:Policies", 
            "List of cities",
            "Main article",
            "Wikipedia:Guidelines"
        ]
    }


@pytest.fixture
def sample_dataframe(sample_wikipedia_data):
    """Sample DataFrame for testing"""
    return pd.DataFrame(sample_wikipedia_data)


@pytest.fixture
def empty_dataframe():
    """Empty DataFrame for testing"""
    return pd.DataFrame()


@pytest.fixture
def invalid_dataframe():
    """Invalid DataFrame (missing required columns) for testing"""
    return pd.DataFrame({
        "wrong_column": [1, 2, 3],
        "another_wrong_column": ["a", "b", "c"]
    })


@pytest.fixture
def temp_directory():
    """Temporary directory for file operations"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_wikipedia_api_response():
    """Mock successful Wikipedia API response"""
    return {
        "query": {
            "allpages": [
                {"pageid": 1, "title": "Test Page 1"},
                {"pageid": 2, "title": "Test Page 2"},
                {"pageid": 3, "title": "List of test items"}
            ]
        }
    }


@pytest.fixture
def mock_empty_api_response():
    """Mock empty Wikipedia API response"""
    return {
        "query": {
            "allpages": []
        }
    }


@pytest.fixture
def mock_repository():
    """Mock repository for testing services"""
    mock_repo = Mock()
    
    # Configure default return values
    mock_repo.fetch_data.return_value = pd.DataFrame({
        "pageid": [1, 2, 3],
        "title": ["Page 1", "Page 2", "Page 3"]
    })
    
    return mock_repo


@pytest.fixture
def mock_storage_adapter():
    """Mock storage adapter for testing"""
    from domain.models import ProcessingResult
    
    mock_adapter = Mock()
    
    # Configure default successful responses
    mock_adapter.save_data.return_value = ProcessingResult(
        success=True,
        message="Data saved successfully",
        record_count=3
    )
    
    mock_adapter.load_data.return_value = pd.DataFrame({
        "pageid": [1, 2, 3],
        "title": ["Page 1", "Page 2", "Page 3"]
    })
    
    return mock_adapter


@pytest.fixture(autouse=True)
def setup_environment():
    """Setup environment variables for testing"""
    os.environ["WIKI_API_URL"] = "https://test.api.com/api.php"
    os.environ["OUTPUT_PATH"] = "data/test_pages.csv"
    
    yield
    
    # Cleanup
    if "WIKI_API_URL" in os.environ:
        del os.environ["WIKI_API_URL"]
    if "OUTPUT_PATH" in os.environ:
        del os.environ["OUTPUT_PATH"]


@pytest.fixture
def mock_dagster_context():
    """Mock Dagster execution context for testing assets"""
    mock_context = Mock()
    mock_context.log = Mock()
    
    # Configure log methods
    mock_context.log.info = Mock()
    mock_context.log.error = Mock()
    mock_context.log.warning = Mock()
    
    return mock_context