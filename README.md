# Data Pipeline ETL with Dagster & Onion Architecture

汎用的なETLパイプラインプロジェクトです。Dagsterを使ったデータオーケストレーションと、オニオンアーキテクチャに基づいた構成を採用しています。

## 🎯 プロジェクト概要

このプロジェクトは**Wikipedia API**から記事リストを取得し、**CSV**に保存するETLパイプラインですが、将来的に様々なデータソースに対応できるよう汎用的に設計されています。

## 🏗️ アーキテクチャ

### ディレクトリ構成
```
data-pipeline-etl/
├── domain/                 # ドメイン層（ビジネスロジックの中心）
│   ├── models.py           # Pandera でのスキーマ定義
│   ├── repositories.py     # 外部APIの取得処理
│   └── services.py         # バリデーションなどロジック処理
├── infrastructure/         # 外部インターフェース層（永続化やI/O）
│   └── storage.py          # CSV・JSON保存処理
├── usecase/                # ユースケース層（Dagster資産の定義）
│   ├── assets.py           # Dagsterの @asset 定義
│   └── jobs.py             # Dagsterのジョブ定義
├── ui/                     # プレゼンテーション層（CLIなど）
│   └── cli.py              # CLI でジョブを実行するエントリポイント
├── tests/                  # テストコード
├── definitions.py          # Dagster Definitions をまとめる
└── pyproject.toml          # Python 環境構成（uv 用）
```

## 🚀 実行方法

### 1. 環境セットアップ

```bash
# uvを使って依存関係をインストール
uv sync

# 環境変数の設定
cp .env.example .env

# 必要に応じて .env ファイルを編集
# vim .env
```

### 2. CLIでの実行

```bash
# 利用可能なジョブの確認
python ui/cli.py --list-jobs

# メインETLジョブの実行
python ui/cli.py --job wikipedia_etl_job

# フィルタ処理ジョブの実行
python ui/cli.py --job filter_pages_job

# 完全パイプラインの実行
python ui/cli.py --job full_pipeline_job

# ドライランモード（実行せずに確認）
python ui/cli.py --job wikipedia_etl_job --dry-run

# 詳細ログ付きで実行
python ui/cli.py --job wikipedia_etl_job --verbose
```

### 3. Dagster Web UIでの実行

```bash
# Dagster開発サーバーの起動
uv run dagster dev

# ブラウザで http://localhost:3000 にアクセス
```

### 4. Docker実行

```bash
# Docker Composeでの実行
docker-compose up --build

# 特定のジョブを実行
docker-compose run dagster-app
```

## 🔧 利用可能なジョブ

| ジョブ名 | 説明 |
|---------|------|
| `wikipedia_etl_job` | 基本的なWikipedia ETLパイプライン |
| `filter_pages_job` | フィルタ処理を含む特定ページの抽出 |
| `full_pipeline_job` | 完全パイプライン（標準+フィルタ出力） |
| `validation_job` | データ品質チェックのみ |

## 🧪 テスト実行

```bash
# 全テスト実行
uv run pytest

# カバレッジ付きでテスト実行
uv run pytest --cov=domain --cov=infrastructure --cov=usecase

# 特定のテストファイルのみ実行
uv run pytest tests/test_domain.py
```

## 📊 アセット構成

### データフロー
1. `raw_wikipedia_pages` - Wikipedia APIからの生データ取得
2. `validated_pages` - Panderaによるデータバリデーション
3. `processed_pages` - データクリーニングと前処理
4. `exported_csv` - CSV形式でのエクスポート
5. `filtered_pages` - 条件による絞り込み処理
6. `filtered_csv_export` - フィルタ済みデータのエクスポート

## 🔧 設定とカスタマイズ

### 環境変数（.env）
`.env.example`をコピーして`.env`ファイルを作成してください：

```env
WIKI_API_URL=https://en.wikipedia.org/w/api.php
OUTPUT_PATH=data/pages.csv
```

**注意**: `.env`ファイルは`.gitignore`に含まれており、リポジトリにコミットされません。

### 新しいデータソースの追加

1. `domain/repositories.py`に新しいRepositoryクラスを追加
2. `domain/models.py`にスキーマ定義を追加
3. `usecase/assets.py`に新しいアセットを定義
4. `usecase/jobs.py`に新しいジョブを追加

### 出力形式の拡張

`infrastructure/storage.py`にて、新しいStorageAdapterを追加することで、BigQuery、PostgreSQL、S3などの出力先に対応可能です。

## 🛠️ 技術スタック

- **Dagster**: データオーケストレーション
- **Pandera**: データスキーマ検証
- **Requests**: HTTP API通信
- **Pandas**: データフレーム操作
- **pytest**: テストフレームワーク
- **uv**: Python依存関係管理
- **Docker**: コンテナ実行環境

## 📝 開発のポイント

- **オニオンアーキテクチャ**: ドメインロジックがインフラストラクチャの詳細から分離
- **型安全性**: Panderaによるデータスキーマ検証
- **拡張性**: 新しいデータソースや出力先の追加が容易
- **テスタビリティ**: 各層が独立してテスト可能
- **CLI対応**: コマンドラインから簡単に実行可能