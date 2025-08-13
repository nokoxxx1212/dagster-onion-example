from typing import Optional
import requests
import pandas as pd
from domain.repositories import WikipediaRepository, DataRepository, GenericApiRepository
from domain.models import WikipediaApiConfig, DataSource


class WikipediaApiClient(WikipediaRepository):
    """Wikipedia API client for actual HTTP requests"""
    
    def __init__(self, timeout: int = 30):
        """Initialize Wikipedia API client
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        
    def fetch_wikipedia_pages(self, api_config: WikipediaApiConfig) -> pd.DataFrame:
        """Wikipedia APIからページ一覧を取得し、HTTP通信を実行する。
        
        Args:
            api_config: Wikipedia API設定
            
        Returns:
            pd.DataFrame: pageidとtitleカラムを含むページデータ
            
        Raises:
            requests.RequestException: HTTP通信が失敗した場合
            ValueError: APIレスポンス形式が無効な場合
        """
        try:
            response = requests.get(
                api_config.base_url,
                params=api_config.to_params(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "query" not in data or "allpages" not in data["query"]:
                raise ValueError("Invalid Wikipedia API response format")
                
            pages = data["query"]["allpages"]
            
            if not pages:
                return pd.DataFrame(columns=["pageid", "title"])
                
            df = pd.DataFrame(pages)
            
            # Ensure required columns exist
            required_columns = ["pageid", "title"]
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
                    
            return df[required_columns]
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch Wikipedia data: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse Wikipedia response: {str(e)}")


class GenericApiClient(GenericApiRepository):
    """Generic API client for future data sources"""
    
    def __init__(self, timeout: int = 30):
        """Initialize generic API client
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
    
    def fetch_data(self, config: DataSource) -> pd.DataFrame:
        """汎用APIエンドポイントからデータを取得し、HTTP通信を実行する。
        
        Args:
            config: データソース設定
            
        Returns:
            pd.DataFrame: 取得したデータ
            
        Raises:
            requests.RequestException: HTTP通信が失敗した場合
            ValueError: レスポンス形式が不明な場合
        """
        try:
            response = requests.get(
                config.url,
                params=config.parameters,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                # Try to find the data array in common locations
                for key in ["data", "results", "items", "records"]:
                    if key in data and isinstance(data[key], list):
                        return pd.DataFrame(data[key])
                # If no array found, treat the dict as a single record
                return pd.DataFrame([data])
            else:
                raise ValueError("Unsupported data format")
                
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch data from {config.url}: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse API response: {str(e)}")


class DataApiClient(DataRepository):
    """Generic data API client implementing DataRepository interface"""
    
    def __init__(self, timeout: int = 30):
        """Initialize data API client
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
    
    def fetch_data(self, config: DataSource) -> pd.DataFrame:
        """データソース設定に基づいてデータを取得し、HTTP通信を実行する。
        
        Args:
            config: データソース設定
            
        Returns:
            pd.DataFrame: 取得したデータ
        """
        # Delegate to GenericApiClient for actual HTTP communication
        generic_client = GenericApiClient(self.timeout)
        return generic_client.fetch_data(config)