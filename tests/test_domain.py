import pytest
import pandas as pd
import pandera.pandas as pa
from unittest.mock import Mock, patch

from domain.models import WikipediaApiConfig, ProcessingResult, PageSchema
from infrastructure.api_clients import WikipediaApiClient, GenericApiClient
from domain.services import ValidationService, DataProcessingService


class TestWikipediaApiConfig:
    
    def test_config_creation(self):
        config = WikipediaApiConfig(
            base_url="https://test.api.com",
            limit=50
        )
        assert config.base_url == "https://test.api.com"
        assert config.limit == 50
        assert config.action == "query"
        assert config.format == "json"
    
    def test_to_params(self):
        config = WikipediaApiConfig(
            base_url="https://test.api.com",
            limit=25
        )
        params = config.to_params()
        
        expected = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "aplimit": 25
        }
        assert params == expected


class TestPageSchema:
    
    def test_valid_data(self):
        data = {
            "pageid": [1, 2, 3],
            "title": ["Test Page 1", "Test Page 2", "Test Page 3"]
        }
        df = pd.DataFrame(data)
        
        # Should not raise an exception
        validated = PageSchema.validate(df)
        assert len(validated) == 3
    
    def test_invalid_data_missing_column(self):
        data = {"pageid": [1, 2, 3]}
        df = pd.DataFrame(data)
        
        with pytest.raises(pa.errors.SchemaError):
            PageSchema.validate(df)
    
    def test_invalid_data_wrong_type(self):
        data = {
            "pageid": ["not_a_number", 2, 3],
            "title": ["Test Page 1", "Test Page 2", "Test Page 3"]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(pa.errors.SchemaError):
            PageSchema.validate(df)


class TestWikipediaApiClient:
    
    def test_init(self):
        repo = WikipediaApiClient(timeout=45)
        assert repo.timeout == 45
    
    @patch('infrastructure.api_clients.requests.get')
    def test_fetch_wikipedia_pages_success(self, mock_get):
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "allpages": [
                    {"pageid": 1, "title": "Test Page 1"},
                    {"pageid": 2, "title": "Test Page 2"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        repo = WikipediaApiClient()
        config = WikipediaApiConfig("https://test.api.com")
        
        df = repo.fetch_wikipedia_pages(config)
        
        assert len(df) == 2
        assert list(df.columns) == ["pageid", "title"]
        assert df.iloc[0]["title"] == "Test Page 1"
    
    @patch('infrastructure.api_clients.requests.get')
    def test_fetch_wikipedia_pages_empty_response(self, mock_get):
        # Mock empty API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {"allpages": []}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        repo = WikipediaApiClient()
        config = WikipediaApiConfig("https://test.api.com")
        
        df = repo.fetch_wikipedia_pages(config)
        
        assert len(df) == 0
        assert list(df.columns) == ["pageid", "title"]
    
    @patch('infrastructure.api_clients.requests.get')
    def test_fetch_wikipedia_pages_api_error(self, mock_get):
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        repo = WikipediaApiClient()
        config = WikipediaApiConfig("https://test.api.com")
        
        with pytest.raises(Exception):
            repo.fetch_wikipedia_pages(config)


class TestValidationService:
    
    def test_validate_wikipedia_pages_success(self):
        data = {
            "pageid": [1, 2, 3],
            "title": ["Test Page 1", "Test Page 2", "Test Page 3"]
        }
        df = pd.DataFrame(data)
        
        result = ValidationService.validate_wikipedia_pages(df)
        
        assert result.success is True
        assert result.record_count == 3
        assert "successful" in result.message.lower()
    
    def test_validate_wikipedia_pages_failure(self):
        # Invalid data - missing required column
        data = {"pageid": [1, 2, 3]}
        df = pd.DataFrame(data)
        
        result = ValidationService.validate_wikipedia_pages(df)
        
        assert result.success is False
        assert result.record_count == 3
        assert len(result.errors) > 0
    
    def test_validate_generic_data_success(self):
        data = {
            "id": [1, 2, 3],
            "name": ["Item 1", "Item 2", "Item 3"],
            "value": [10, 20, 30]
        }
        df = pd.DataFrame(data)
        required_columns = ["id", "name"]
        
        result = ValidationService.validate_generic_data(df, required_columns)
        
        assert result.success is True
        assert result.record_count == 3
    
    def test_validate_generic_data_missing_columns(self):
        data = {"id": [1, 2, 3]}
        df = pd.DataFrame(data)
        required_columns = ["id", "name", "value"]
        
        result = ValidationService.validate_generic_data(df, required_columns)
        
        assert result.success is False
        assert "Missing columns" in result.message
        assert len(result.errors) > 0


class TestDataProcessingService:
    
    def setup_method(self):
        self.mock_repo = Mock()
        self.service = DataProcessingService(self.mock_repo)
    
    def test_clean_text_data(self):
        data = {
            "title": ["  Test Page 1  ", "Test    Page   2", "Test Page 3"],
            "description": ["  Description 1  ", "", None]
        }
        df = pd.DataFrame(data)
        
        cleaned_df = self.service.clean_text_data(df, ["title", "description"])
        
        assert cleaned_df.iloc[0]["title"] == "Test Page 1"
        assert cleaned_df.iloc[1]["title"] == "Test Page 2"
        assert pd.isna(cleaned_df.iloc[1]["description"])
    
    def test_filter_data_contains(self):
        data = {
            "title": ["List of countries", "Wikipedia article", "List of cities", "Random page"],
            "id": [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        filters = {"title": "contains:List of"}
        filtered_df = self.service.filter_data(df, filters)
        
        assert len(filtered_df) == 2
        assert "List of countries" in filtered_df["title"].values
        assert "List of cities" in filtered_df["title"].values
    
    def test_filter_data_startswith(self):
        data = {
            "title": ["Wikipedia:Policy", "Wikipedia:Guidelines", "Main article", "Wikipedia:Help"],
            "id": [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        filters = {"title": "startswith:Wikipedia:"}
        filtered_df = self.service.filter_data(df, filters)
        
        assert len(filtered_df) == 3
        assert all(title.startswith("Wikipedia:") for title in filtered_df["title"].values)
    
    def test_deduplicate_data(self):
        data = {
            "pageid": [1, 2, 1, 3, 2],
            "title": ["Page 1", "Page 2", "Page 1 Duplicate", "Page 3", "Page 2 Duplicate"]
        }
        df = pd.DataFrame(data)
        
        deduped_df = self.service.deduplicate_data(df, subset_columns=["pageid"])
        
        assert len(deduped_df) == 3
        unique_ids = deduped_df["pageid"].unique()
        assert set(unique_ids) == {1, 2, 3}
    
    def test_add_metadata_columns(self):
        data = {
            "title": ["Page 1", "Page 2"],
            "id": [1, 2]
        }
        df = pd.DataFrame(data)
        
        metadata = {
            "source": "test",
            "processed_at": "2023-01-01T00:00:00"
        }
        
        result_df = self.service.add_metadata_columns(df, metadata)
        
        assert "source" in result_df.columns
        assert "processed_at" in result_df.columns
        assert all(result_df["source"] == "test")
        assert all(result_df["processed_at"] == "2023-01-01T00:00:00")