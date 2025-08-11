from dagster import define_asset_job
from .assets import (
    fetch_raw_pages,
    validate_pages, 
    clean_and_process_pages,
    store_pages_to_csv,
    filter_pages_by_criteria,
    store_filtered_pages_to_csv
)


# Main ETL job for Wikipedia data processing
wikipedia_etl_job = define_asset_job(
    name="wikipedia_etl_job",
    description="Complete ETL pipeline for Wikipedia pages data",
    selection=[
        fetch_raw_pages,
        validate_pages,
        clean_and_process_pages,
        store_pages_to_csv
    ]
)


# Filtered pages job
filter_pages_job = define_asset_job(
    name="filter_pages_job", 
    description="Filter and export specific Wikipedia pages",
    selection=[
        fetch_raw_pages,
        validate_pages,
        clean_and_process_pages,
        filter_pages_by_criteria,
        store_filtered_pages_to_csv
    ]
)


# Full pipeline job (includes both standard and filtered exports)
full_pipeline_job = define_asset_job(
    name="full_pipeline_job",
    description="Complete pipeline including standard and filtered exports",
    selection=[
        fetch_raw_pages,
        validate_pages,
        clean_and_process_pages,
        store_pages_to_csv,
        filter_pages_by_criteria,
        store_filtered_pages_to_csv
    ]
)


# Data validation job (for testing data quality)
validation_job = define_asset_job(
    name="validation_job",
    description="Data validation and quality checks",
    selection=[
        fetch_raw_pages,
        validate_pages
    ]
)