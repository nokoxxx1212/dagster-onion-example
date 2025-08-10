import os
import pandas as pd
from datetime import datetime
from dagster import asset, AssetExecutionContext
from dotenv import load_dotenv

from domain.models import WikipediaApiConfig, ProcessingResult
from domain.repositories import WikipediaRepository
from domain.services import ValidationService, DataProcessingService
from infrastructure.storage import StorageFactory, DataExporter

# Load environment variables
load_dotenv()


@asset
def raw_wikipedia_pages(context: AssetExecutionContext) -> pd.DataFrame:
    """
    Fetch raw Wikipedia pages from API
    
    Returns:
        DataFrame with raw Wikipedia page data
    """
    context.log.info("Fetching Wikipedia pages from API")
    
    # Get configuration from environment
    api_url = os.getenv("WIKI_API_URL", "https://en.wikipedia.org/w/api.php")
    
    # Create API configuration
    api_config = WikipediaApiConfig(
        base_url=api_url,
        limit=50  # Limit for demo purposes
    )
    
    # Create repository and fetch data
    repository = WikipediaRepository()
    df = repository.fetch_wikipedia_pages(api_config)
    
    context.log.info(f"Fetched {len(df)} pages from Wikipedia API")
    
    return df


@asset
def validated_pages(context: AssetExecutionContext, raw_wikipedia_pages: pd.DataFrame) -> pd.DataFrame:
    """
    Validate Wikipedia pages data
    
    Args:
        raw_wikipedia_pages: Raw data from Wikipedia API
        
    Returns:
        Validated DataFrame
        
    Raises:
        ValueError: If validation fails
    """
    context.log.info("Validating Wikipedia pages data")
    
    # Validate data using domain service
    validation_result = ValidationService.validate_wikipedia_pages(raw_wikipedia_pages)
    
    if not validation_result.success:
        error_msg = f"Data validation failed: {validation_result.message}"
        context.log.error(error_msg)
        for error in validation_result.errors:
            context.log.error(f"Validation error: {error}")
        raise ValueError(error_msg)
    
    context.log.info(f"Data validation successful: {validation_result.record_count} records validated")
    
    return raw_wikipedia_pages


@asset
def processed_pages(context: AssetExecutionContext, validated_pages: pd.DataFrame) -> pd.DataFrame:
    """
    Process and clean Wikipedia pages data
    
    Args:
        validated_pages: Validated Wikipedia pages data
        
    Returns:
        Processed DataFrame
    """
    context.log.info("Processing Wikipedia pages data")
    
    # Create processing service
    repository = WikipediaRepository()  # Not used in processing, but required for service
    processing_service = DataProcessingService(repository)
    
    # Clean text data
    processed_df = processing_service.clean_text_data(
        validated_pages, 
        text_columns=["title"]
    )
    
    # Remove duplicates
    processed_df = processing_service.deduplicate_data(
        processed_df, 
        subset_columns=["pageid"]
    )
    
    # Add metadata
    metadata = {
        "processed_at": datetime.now().isoformat(),
        "source": "wikipedia_api"
    }
    processed_df = processing_service.add_metadata_columns(processed_df, metadata)
    
    context.log.info(f"Processing complete: {len(processed_df)} records processed")
    
    return processed_df


@asset
def exported_csv(context: AssetExecutionContext, processed_pages: pd.DataFrame) -> str:
    """
    Export processed data to CSV file
    
    Args:
        processed_pages: Processed Wikipedia pages data
        
    Returns:
        Path to exported CSV file
    """
    context.log.info("Exporting data to CSV")
    
    # Get output path from environment
    output_path = os.getenv("OUTPUT_PATH", "data/pages.csv")
    
    # Create storage adapter and exporter
    storage_adapter = StorageFactory.create_adapter("csv")
    exporter = DataExporter(storage_adapter)
    
    # Export data with additional metadata
    export_metadata = {
        "export_timestamp": datetime.now().isoformat(),
        "record_count": len(processed_pages)
    }
    
    result = exporter.export_with_metadata(
        processed_pages,
        output_path,
        export_metadata
    )
    
    if not result.success:
        error_msg = f"Export failed: {result.message}"
        context.log.error(error_msg)
        for error in result.errors:
            context.log.error(f"Export error: {error}")
        raise RuntimeError(error_msg)
    
    context.log.info(f"Export successful: {result.message}")
    
    return output_path


@asset
def filtered_pages(context: AssetExecutionContext, processed_pages: pd.DataFrame) -> pd.DataFrame:
    """
    Filter pages based on title criteria
    
    Args:
        processed_pages: Processed Wikipedia pages data
        
    Returns:
        Filtered DataFrame
    """
    context.log.info("Filtering pages by title criteria")
    
    # Create processing service
    repository = WikipediaRepository()
    processing_service = DataProcessingService(repository)
    
    # Apply filters - example: pages containing "List of"
    filters = {
        "title": "contains:List of"
    }
    
    filtered_df = processing_service.filter_data(processed_pages, filters)
    
    context.log.info(f"Filtering complete: {len(filtered_df)} records match criteria")
    
    return filtered_df


@asset  
def filtered_csv_export(context: AssetExecutionContext, filtered_pages: pd.DataFrame) -> str:
    """
    Export filtered data to separate CSV file
    
    Args:
        filtered_pages: Filtered Wikipedia pages data
        
    Returns:
        Path to exported filtered CSV file
    """
    context.log.info("Exporting filtered data to CSV")
    
    # Create storage adapter and exporter
    storage_adapter = StorageFactory.create_adapter("csv")
    exporter = DataExporter(storage_adapter)
    
    # Export filtered data
    output_path = "data/filtered_pages.csv"
    export_metadata = {
        "export_timestamp": datetime.now().isoformat(),
        "filter_criteria": "title contains 'List of'",
        "record_count": len(filtered_pages)
    }
    
    result = exporter.export_with_metadata(
        filtered_pages,
        output_path,
        export_metadata
    )
    
    if not result.success:
        error_msg = f"Filtered export failed: {result.message}"
        context.log.error(error_msg)
        for error in result.errors:
            context.log.error(f"Export error: {error}")
        raise RuntimeError(error_msg)
    
    context.log.info(f"Filtered export successful: {result.message}")
    
    return output_path