from dagster import define_asset_job
from .assets import (
    raw_wikipedia_pages,
    validated_pages, 
    processed_pages,
    exported_csv,
    filtered_pages,
    filtered_csv_export
)


# Main ETL job for Wikipedia data processing
wikipedia_etl_job = define_asset_job(
    name="wikipedia_etl_job",
    description="Complete ETL pipeline for Wikipedia pages data",
    selection=[
        raw_wikipedia_pages,
        validated_pages,
        processed_pages,
        exported_csv
    ]
)


# Filtered pages job
filter_pages_job = define_asset_job(
    name="filter_pages_job", 
    description="Filter and export specific Wikipedia pages",
    selection=[
        raw_wikipedia_pages,
        validated_pages,
        processed_pages,
        filtered_pages,
        filtered_csv_export
    ]
)


# Full pipeline job (includes both standard and filtered exports)
full_pipeline_job = define_asset_job(
    name="full_pipeline_job",
    description="Complete pipeline including standard and filtered exports",
    selection=[
        raw_wikipedia_pages,
        validated_pages,
        processed_pages,
        exported_csv,
        filtered_pages,
        filtered_csv_export
    ]
)


# Data validation job (for testing data quality)
validation_job = define_asset_job(
    name="validation_job",
    description="Data validation and quality checks",
    selection=[
        raw_wikipedia_pages,
        validated_pages
    ]
)