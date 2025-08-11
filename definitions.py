from dagster import Definitions

from usecase.assets import (
    fetch_raw_pages,
    validate_pages,
    clean_and_process_pages,
    store_pages_to_csv,
    filter_pages_by_criteria,
    store_filtered_pages_to_csv
)

from usecase.jobs import (
    wikipedia_etl_job,
    filter_pages_job,
    full_pipeline_job,
    validation_job
)


# Define all assets
assets = [
    fetch_raw_pages,
    validate_pages,
    clean_and_process_pages,
    store_pages_to_csv,
    filter_pages_by_criteria,
    store_filtered_pages_to_csv
]

# Define all jobs
jobs = [
    wikipedia_etl_job,
    filter_pages_job,
    full_pipeline_job,
    validation_job
]

# Create Dagster definitions
defs = Definitions(
    assets=assets,
    jobs=jobs
)