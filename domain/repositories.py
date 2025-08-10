from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import requests
import pandas as pd
from .models import WikipediaApiConfig, DataSource, ProcessingResult


class DataRepository(ABC):
    """Abstract base class for data repositories"""
    
    @abstractmethod
    def fetch_data(self, config: DataSource) -> pd.DataFrame:
        """Fetch data from external source"""
        pass


class WikipediaRepository(DataRepository):
    """Repository for Wikipedia API data"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        
    def fetch_data(self, config: DataSource) -> pd.DataFrame:
        """
        Fetch Wikipedia pages data
        
        Args:
            config: DataSource configuration
            
        Returns:
            DataFrame with Wikipedia page data
            
        Raises:
            requests.RequestException: If API request fails
            ValueError: If response format is invalid
        """
        try:
            response = requests.get(
                config.url,
                params=config.parameters,
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
    
    def fetch_wikipedia_pages(self, api_config: WikipediaApiConfig) -> pd.DataFrame:
        """
        Fetch Wikipedia pages using WikipediaApiConfig
        
        Args:
            api_config: Wikipedia API configuration
            
        Returns:
            DataFrame with page data
        """
        data_source = DataSource(
            name="wikipedia",
            url=api_config.base_url,
            parameters=api_config.to_params()
        )
        
        return self.fetch_data(data_source)


class GenericApiRepository(DataRepository):
    """Generic API repository for future data sources"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def fetch_data(self, config: DataSource) -> pd.DataFrame:
        """
        Fetch data from generic API endpoint
        
        Args:
            config: DataSource configuration
            
        Returns:
            DataFrame with fetched data
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