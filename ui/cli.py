#!/usr/bin/env python3

import argparse
import sys
import os
from typing import Optional
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dagster import DagsterInstance, materialize
from definitions import defs


def setup_argparse() -> argparse.ArgumentParser:
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Data Pipeline ETL CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Jobs:
  wikipedia_etl_job     - Complete ETL pipeline for Wikipedia pages
  filter_pages_job      - Filter and export specific pages  
  full_pipeline_job     - Complete pipeline with filtered exports
  validation_job        - Data validation and quality checks

Examples:
  python ui/cli.py --job wikipedia_etl_job
  python ui/cli.py --job filter_pages_job --verbose
  python ui/cli.py --list-jobs
        """
    )
    
    parser.add_argument(
        "--job",
        type=str,
        help="Job name to execute"
    )
    
    parser.add_argument(
        "--list-jobs",
        action="store_true",
        help="List all available jobs"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running"
    )
    
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to environment file (default: .env)"
    )
    
    return parser


def load_environment(env_file: str) -> bool:
    """Load environment variables from file"""
    env_path = Path(env_file)
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print(f"✓ Loaded environment from {env_path}")
        return True
    else:
        print(f"⚠ Environment file not found: {env_path}")
        return False


def list_available_jobs() -> None:
    """List all available jobs"""
    print("\n📋 Available Jobs:")
    print("=" * 50)
    
    jobs = [
        ("wikipedia_etl_job", "Complete ETL pipeline for Wikipedia pages"),
        ("filter_pages_job", "Filter and export specific pages"),
        ("full_pipeline_job", "Complete pipeline with filtered exports"),
        ("validation_job", "Data validation and quality checks")
    ]
    
    for job_name, description in jobs:
        print(f"  {job_name:<20} - {description}")
    
    print("\n💡 Usage: python ui/cli.py --job <job_name>")


def execute_job(job_name: str, verbose: bool = False, dry_run: bool = False) -> bool:
    """Execute a Dagster job"""
    try:
        # Get the job from definitions
        jobs_dict = {}
        
        # Try different ways to get jobs depending on Dagster version
        if hasattr(defs, 'jobs') and defs.jobs:
            jobs_dict = {job.name: job for job in defs.jobs}
        elif hasattr(defs, 'get_all_job_defs'):
            jobs_dict = {job.name: job for job in defs.get_all_job_defs()}
        elif hasattr(defs, 'job_defs'):
            jobs_dict = {job.name: job for job in defs.job_defs}
        else:
            print("❌ Unable to retrieve jobs from definitions")
            return False
        
        if job_name not in jobs_dict:
            available_jobs = list(jobs_dict.keys())
            print(f"❌ Job '{job_name}' not found.")
            print(f"Available jobs: {', '.join(available_jobs)}")
            return False
        
        job_def = jobs_dict[job_name]
        
        if dry_run:
            print(f"🔍 Dry run for job: {job_name}")
            print(f"Description: {job_def.description or 'No description available'}")
            print("Assets that would be materialized:")
            
            # Get assets from job
            if hasattr(job_def, 'asset_selection') and job_def.asset_selection:
                for asset_key in job_def.asset_selection:
                    print(f"  - {asset_key}")
            else:
                print("  - No specific assets defined")
            
            return True
        
        print(f"🚀 Executing job: {job_name}")
        print(f"Description: {job_def.description or 'No description available'}")
        
        # Create Dagster instance
        instance = DagsterInstance.ephemeral()
        
        # Execute the job using dagster APIs
        try:
            # For all jobs, use materialize with all assets
            from dagster import materialize
            
            # Get all assets from definitions
            all_assets = defs.assets or []
            
            if not all_assets:
                print("❌ No assets found to execute")
                return False
            
            print(f"📊 Materializing {len(all_assets)} assets...")
            
            # Show asset names if verbose
            if verbose:
                for asset in all_assets:
                    asset_name = getattr(asset, 'key', getattr(asset, 'name', 'unknown'))
                    print(f"  - {asset_name}")
            
            result = materialize(all_assets, instance=instance)
        
        except Exception as e:
            print(f"❌ Job execution failed with error: {str(e)}")
            if verbose:
                import traceback
                traceback.print_exc()
            return False
        
        if result.success:
            print(f"✅ Job '{job_name}' completed successfully!")
            
            if verbose:
                print("\n📊 Execution Summary:")
                for event in result.all_events:
                    if event.event_type_value == "STEP_SUCCESS":
                        print(f"  ✓ {event.step_key}")
            
            return True
        else:
            print(f"❌ Job '{job_name}' failed!")
            
            if verbose:
                print("\n🔍 Error Details:")
                for event in result.all_events:
                    if event.event_type_value == "STEP_FAILURE":
                        print(f"  ✗ {event.step_key}: {event.event_specific_data}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error executing job '{job_name}': {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main CLI function"""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Show help if no arguments provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    # Load environment variables
    load_environment(args.env_file)
    
    # List jobs if requested
    if args.list_jobs:
        list_available_jobs()
        sys.exit(0)
    
    # Execute job if specified
    if args.job:
        success = execute_job(
            args.job, 
            verbose=args.verbose,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)
    
    # Show help if no action specified
    parser.print_help()


if __name__ == "__main__":
    main()