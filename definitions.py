from dagster import Definitions

from usecase.assets import (
    raw_wikipedia_pages,
    validated_pages,
    processed_pages,
    exported_csv,
    filtered_pages,
    filtered_csv_export
)

from usecase.jobs import (
    wikipedia_etl_job,
    filter_pages_job,
    full_pipeline_job,
    validation_job
)


# Define all assets
assets = [
    raw_wikipedia_pages,
    validated_pages,
    processed_pages,
    exported_csv,
    filtered_pages,
    filtered_csv_export
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