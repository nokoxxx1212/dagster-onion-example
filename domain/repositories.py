from abc import ABC, abstractmethod
import pandas as pd
from .models import WikipediaApiConfig, DataSource


class DataRepository(ABC):
    """Abstract base class for data repositories"""
    
    @abstractmethod
    def fetch_data(self, config: DataSource) -> pd.DataFrame:
        """Fetch data from external source
        
        Args:
            config: DataSource configuration
            
        Returns:
            DataFrame with fetched data
        """
        pass


class WikipediaRepository(ABC):
    """Abstract repository interface for Wikipedia API data"""
    
    @abstractmethod
    def fetch_wikipedia_pages(self, api_config: WikipediaApiConfig) -> pd.DataFrame:
        """Fetch Wikipedia pages using WikipediaApiConfig
        
        Args:
            api_config: Wikipedia API configuration
            
        Returns:
            DataFrame with page data (pageid, title columns)
        """
        pass


class GenericApiRepository(ABC):
    """Abstract repository interface for generic API data"""
    
    @abstractmethod
    def fetch_data(self, config: DataSource) -> pd.DataFrame:
        """Fetch data from generic API endpoint
        
        Args:
            config: DataSource configuration
            
        Returns:
            DataFrame with fetched data
        """
        pass