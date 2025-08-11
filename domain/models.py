from typing import Dict, Any, List
from dataclasses import dataclass
import pandera.pandas as pa
from pandera.typing import DataFrame, Series


class PageSchema(pa.DataFrameModel):
    """Wikipedia page schema definition using Pandera"""
    pageid: Series[int] = pa.Field(ge=1, description="Wikipedia page ID")
    title: Series[str] = pa.Field(description="Page title")
    
    class Config:
        strict = True
        coerce = True
    
    @pa.check("title")
    def title_not_empty(cls, series):
        """Check that title is not empty"""
        return series.str.len() > 0


@dataclass
class WikipediaApiConfig:
    """Configuration for Wikipedia API requests"""
    base_url: str
    action: str = "query"
    format: str = "json"
    list_type: str = "allpages"
    limit: int = 100
    
    def to_params(self) -> Dict[str, Any]:
        """Convert config to API parameters"""
        return {
            "action": self.action,
            "format": self.format,
            "list": self.list_type,
            "aplimit": self.limit
        }


@dataclass
class DataSource:
    """Generic data source configuration"""
    name: str
    url: str
    parameters: Dict[str, Any]
    
    
@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    success: bool
    message: str
    record_count: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []