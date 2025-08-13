import os
import pandas as pd
from datetime import datetime
from dagster import asset, AssetExecutionContext, MetadataValue
from dotenv import load_dotenv

from domain.models import WikipediaApiConfig, ProcessingResult
from domain.services import ValidationService, DataProcessingService
from infrastructure.storage import StorageFactory, DataExporter
from infrastructure.api_clients import WikipediaApiClient

# Load environment variables
load_dotenv()


@asset(
    description="Wikipedia APIからページ一覧（pageid, title）を取得する",
    group_name="wikipedia_etl",
)
def fetch_raw_pages(context: AssetExecutionContext) -> pd.DataFrame:
    """Wikipedia APIからページ一覧を取得し、環境変数設定とAPI呼び出しを実行する。
    
    Args:
        context: Dagsterアセット実行コンテキスト
        
    Returns:
        pd.DataFrame: pageidとtitleカラムを含む生データのDataFrame
    """
    context.log.info("fetch_raw_pages: 開始")
    
    # Get configuration from environment
    api_url = os.getenv("WIKI_API_URL", "https://en.wikipedia.org/w/api.php")
    
    # Create API configuration
    api_config = WikipediaApiConfig(
        base_url=api_url,
        limit=50  # Limit for demo purposes
    )
    
    # Create API client and fetch data
    api_client = WikipediaApiClient()
    df = api_client.fetch_wikipedia_pages(api_config)
    
    # Add dynamic metadata
    preview_md = df.head(3).to_markdown(index=False) if not df.empty else "No data"
    context.add_output_metadata({
        "row_count": len(df),
        "preview": MetadataValue.md(preview_md),
        "api_url": MetadataValue.url(api_url),
        "columns": list(df.columns),
    })
    
    context.log.info(f"fetch_raw_pages: 完了 rows={len(df)} api_url={api_url}")
    
    return df


@asset(
    description="Panderaでスキーマ検証し、欠損/型不正を弾いたDataFrameを返す",
    group_name="wikipedia_etl",
)
def validate_pages(context: AssetExecutionContext, fetch_raw_pages: pd.DataFrame) -> pd.DataFrame:
    """Panderaでスキーマ検証を実行し、型変換と必須フィールドチェックを行う。
    
    Args:
        context: Dagsterアセット実行コンテキスト
        fetch_raw_pages: 生のWikipediaページデータ
        
    Returns:
        pd.DataFrame: 検証済みのpageidとtitleカラムを含むDataFrame
        
    Raises:
        ValueError: データ検証が失敗した場合
    """
    context.log.info("validate_pages: 開始")
    
    # Validate data using domain service
    validation_result = ValidationService.validate_wikipedia_pages(fetch_raw_pages)
    
    if not validation_result.success:
        error_msg = f"Data validation failed: {validation_result.message}"
        context.log.error(f"validate_pages: 検証失敗 {error_msg}")
        for error in validation_result.errors:
            context.log.error(f"Validation error: {error}")
        raise ValueError(error_msg)
    
    # Add dynamic metadata
    preview_md = fetch_raw_pages.head(3).to_markdown(index=False) if not fetch_raw_pages.empty else "No data"
    context.add_output_metadata({
        "row_count": len(fetch_raw_pages),
        "preview": MetadataValue.md(preview_md),
        "validation_success": validation_result.success,
        "validation_message": validation_result.message,
    })
    
    context.log.info(f"validate_pages: 完了 rows={len(fetch_raw_pages)} validation=OK")
    
    return fetch_raw_pages


@asset(
    description="データクリーニングと前処理を実行し、メタデータを付与する",
    group_name="wikipedia_etl",
)
def clean_and_process_pages(context: AssetExecutionContext, validate_pages: pd.DataFrame) -> pd.DataFrame:
    """テキストクリーニング、重複除去、メタデータ付与を実行する。
    
    Args:
        context: Dagsterアセット実行コンテキスト
        validate_pages: 検証済みのWikipediaページデータ
        
    Returns:
        pd.DataFrame: 元のカラム + processed_at, sourceを含む処理済みDataFrame
    """
    context.log.info("clean_and_process_pages: 開始")
    
    # Create processing service
    api_client = WikipediaApiClient()  # Not used in processing, but required for service
    processing_service = DataProcessingService(api_client)
    
    # Clean text data
    processed_df = processing_service.clean_text_data(
        validate_pages, 
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
    
    # Add dynamic metadata
    preview_md = processed_df.head(3).to_markdown(index=False) if not processed_df.empty else "No data"
    context.add_output_metadata({
        "row_count": len(processed_df),
        "preview": MetadataValue.md(preview_md),
        "columns_added": ["processed_at", "source"],
        "duplicates_removed": len(validate_pages) - len(processed_df),
    })
    
    context.log.info(f"clean_and_process_pages: 完了 rows={len(processed_df)} duplicates_removed={len(validate_pages) - len(processed_df)}")
    
    return processed_df


@asset(
    description="処理済みデータをCSVファイルに出力する",
    group_name="wikipedia_etl",
)
def store_pages_to_csv(context: AssetExecutionContext, clean_and_process_pages: pd.DataFrame) -> str:
    """処理済みデータを環境変数で指定されたパスにCSVファイルとして出力する。
    
    Args:
        context: Dagsterアセット実行コンテキスト
        clean_and_process_pages: クリーニング済みのDataFrame
        
    Returns:
        str: 出力先CSVファイルのパス
        
    Raises:
        RuntimeError: エクスポート処理が失敗した場合
    """
    context.log.info("store_pages_to_csv: 開始")
    
    # Get output path from environment
    output_path = os.getenv("OUTPUT_PATH", "data/pages.csv")
    
    # Create storage adapter and exporter
    storage_adapter = StorageFactory.create_adapter("csv")
    exporter = DataExporter(storage_adapter)
    
    # Export data with additional metadata
    export_metadata = {
        "export_timestamp": datetime.now().isoformat(),
        "record_count": len(clean_and_process_pages)
    }
    
    result = exporter.export_with_metadata(
        clean_and_process_pages,
        output_path,
        export_metadata
    )
    
    if not result.success:
        error_msg = f"Export failed: {result.message}"
        context.log.error(f"store_pages_to_csv: エクスポート失敗 {error_msg}")
        for error in result.errors:
            context.log.error(f"Export error: {error}")
        raise RuntimeError(error_msg)
    
    # Add dynamic metadata
    resolved_path = os.path.abspath(output_path)
    context.add_output_metadata({
        "output_path": MetadataValue.path(resolved_path),
        "record_count": len(clean_and_process_pages),
        "file_size_bytes": os.path.getsize(resolved_path) if os.path.exists(resolved_path) else 0,
    })
    
    context.log.info(f"store_pages_to_csv: 完了 rows={len(clean_and_process_pages)} path={resolved_path}")
    
    return output_path


@asset(
    description="特定の条件でページをフィルタリングし、対象データを抽出する",
    group_name="wikipedia_etl",
)
def filter_pages_by_criteria(context: AssetExecutionContext, clean_and_process_pages: pd.DataFrame) -> pd.DataFrame:
    """タイトル条件でページをフィルタリングし、フォールバック機能で必ずデータを返す。
    
    Args:
        context: Dagsterアセット実行コンテキスト
        clean_and_process_pages: クリーニング済みのDataFrame
        
    Returns:
        pd.DataFrame: フィルタリング条件に合致したDataFrame
    """
    context.log.info("filter_pages_by_criteria: 開始")
    
    # Create processing service
    api_client = WikipediaApiClient()
    processing_service = DataProcessingService(api_client)
    
    # Apply filters - try multiple criteria
    filters = {
        "title": "contains:Wikipedia"
    }
    
    filtered_df = processing_service.filter_data(clean_and_process_pages, filters)
    filter_criteria = "title contains 'Wikipedia'"
    
    # If no results with first filter, try a broader filter
    if len(filtered_df) == 0:
        context.log.info("filter_pages_by_criteria: フィルタ1（Wikipedia）該当なし、フィルタ2を実行")
        filters = {
            "title": "contains:Main"
        }
        filtered_df = processing_service.filter_data(clean_and_process_pages, filters)
        filter_criteria = "title contains 'Main'"
    
    # If still no results, take first half of pages
    if len(filtered_df) == 0:
        context.log.info("filter_pages_by_criteria: フィルタ2（Main）該当なし、先頭半分を取得")
        half_point = len(clean_and_process_pages) // 2
        filtered_df = clean_and_process_pages.head(half_point) if half_point > 0 else clean_and_process_pages.head(1)
        filter_criteria = f"first {half_point} records (fallback)"
    
    # Add dynamic metadata
    preview_md = filtered_df.head(3).to_markdown(index=False) if not filtered_df.empty else "No data"
    context.add_output_metadata({
        "row_count": len(filtered_df),
        "preview": MetadataValue.md(preview_md),
        "filter_criteria": filter_criteria,
        "original_count": len(clean_and_process_pages),
        "filter_ratio": len(filtered_df) / len(clean_and_process_pages) if len(clean_and_process_pages) > 0 else 0,
    })
    
    context.log.info(f"filter_pages_by_criteria: 完了 rows={len(filtered_df)} criteria='{filter_criteria}'")
    
    return filtered_df


@asset(
    description="フィルタリング済みデータを別のCSVファイルに出力する",
    group_name="wikipedia_etl",
)
def store_filtered_pages_to_csv(context: AssetExecutionContext, filter_pages_by_criteria: pd.DataFrame) -> str:
    """フィルタリング済みデータを空チェックしてCSVファイルに出力する。
    
    Args:
        context: Dagsterアセット実行コンテキスト
        filter_pages_by_criteria: フィルタリング済みのDataFrame
        
    Returns:
        str: フィルタ済みCSVファイルのパス
        
    Raises:
        RuntimeError: エクスポート処理が失敗した場合
    """
    context.log.info("store_filtered_pages_to_csv: 開始")
    
    output_path = "data/filtered_pages.csv"
    
    # Check if filtered_pages is empty
    if filter_pages_by_criteria.empty:
        context.log.warning("store_filtered_pages_to_csv: 空のDataFrame、プレースホルダー作成")
        # Create empty CSV with headers
        empty_df = pd.DataFrame(columns=["pageid", "title", "processed_at", "source"])
        empty_df.to_csv(output_path, index=False)
        
        # Add metadata for empty case
        resolved_path = os.path.abspath(output_path)
        context.add_output_metadata({
            "output_path": MetadataValue.path(resolved_path),
            "record_count": 0,
            "is_placeholder": True,
            "file_size_bytes": os.path.getsize(resolved_path) if os.path.exists(resolved_path) else 0,
        })
        
        context.log.info(f"store_filtered_pages_to_csv: プレースホルダー完了 path={resolved_path}")
        return output_path
    
    # Create storage adapter and exporter
    storage_adapter = StorageFactory.create_adapter("csv")
    exporter = DataExporter(storage_adapter)
    
    # Export filtered data
    export_metadata = {
        "export_timestamp": datetime.now().isoformat(),
        "filter_criteria": "dynamic_filter_applied",
        "record_count": len(filter_pages_by_criteria)
    }
    
    result = exporter.export_with_metadata(
        filter_pages_by_criteria,
        output_path,
        export_metadata
    )
    
    if not result.success:
        error_msg = f"Filtered export failed: {result.message}"
        context.log.error(f"store_filtered_pages_to_csv: エクスポート失敗 {error_msg}")
        for error in result.errors:
            context.log.error(f"Export error: {error}")
        raise RuntimeError(error_msg)
    
    # Add dynamic metadata for successful export
    resolved_path = os.path.abspath(output_path)
    context.add_output_metadata({
        "output_path": MetadataValue.path(resolved_path),
        "record_count": len(filter_pages_by_criteria),
        "is_placeholder": False,
        "file_size_bytes": os.path.getsize(resolved_path) if os.path.exists(resolved_path) else 0,
    })
    
    context.log.info(f"store_filtered_pages_to_csv: 完了 rows={len(filter_pages_by_criteria)} path={resolved_path}")
    
    return output_path