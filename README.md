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

#### 🌐 Dagster Web UIでの実行（推奨）

```bash
# 環境変数ファイルを作成
cp .env.example .env

# Dagster Web UIを起動
docker-compose up -d dagster-web

# ブラウザで http://localhost:3000 にアクセス
```

**Web UIでの操作手順：**

1. **アセットの実行**
   - 「Assets」タブでアセット一覧を確認
   - 実行したいアセット（例: `store_pages_to_csv`）をクリック
   - 「Materialize」→「Materialize with upstream」で依存関係含めて実行

2. **ジョブの実行**
   - 「Jobs」タブで利用可能なジョブを確認
   - 実行したいジョブ（例: `wikipedia_etl_job`）をクリック  
   - 「Launch Run」ボタンで実行開始

3. **実行結果の確認**
   - 「Runs」タブで実行履歴とログを確認
   - `data/pages.csv` に結果が出力される

#### 💻 CLIでのジョブ実行

```bash
# 基本的なETLパイプライン実行
docker-compose run --rm dagster-cli uv run python ui/cli.py --job wikipedia_etl_job

# フィルタ処理付きパイプライン
docker-compose run --rm dagster-cli uv run python ui/cli.py --job filter_pages_job

# 完全パイプライン（全アセット実行）
docker-compose run --rm dagster-cli uv run python ui/cli.py --job full_pipeline_job

# データ検証のみ実行
docker-compose run --rm dagster-cli uv run python ui/cli.py --job validation_job

# 詳細ログ付きで実行
docker-compose run --rm dagster-cli uv run python ui/cli.py --job wikipedia_etl_job --verbose

# 利用可能なジョブ一覧を表示
docker-compose run --rm dagster-cli uv run python ui/cli.py --list-jobs
```

#### 📁 出力ファイルの確認

```bash
# 生成されたデータファイルを確認
docker-compose run --rm dagster-cli ls -la data/
docker-compose run --rm dagster-cli head -5 data/pages.csv

# ホストマシンから直接確認
ls -la data/
cat data/pages.csv
```

## 🔧 利用可能なジョブ

| ジョブ名 | 説明 |
|---------|------|
| `wikipedia_etl_job` | 基本的なWikipedia ETLパイプライン |
| `filter_pages_job` | フィルタ処理を含む特定ページの抽出 |
| `full_pipeline_job` | 完全パイプライン（標準+フィルタ出力） |
| `validation_job` | データ品質チェックのみ |

## 🧪 テスト実行

### ローカル実行
```bash
# 全テスト実行
uv run pytest

# カバレッジ付きでテスト実行
uv run pytest --cov=domain --cov=infrastructure --cov=usecase

# 特定のテストファイルのみ実行
uv run pytest tests/test_domain.py
```

### Docker実行
```bash
# Docker内で全テスト実行
docker-compose run --rm dagster-test

# 特定のテストファイルのみ実行
docker-compose run --rm dagster-test uv run pytest tests/test_domain.py

# カバレッジ付きでテスト実行
docker-compose run --rm dagster-test uv run pytest --cov=domain --cov=infrastructure --cov=usecase
```

## 📊 アセット構成

### データフロー（「UIだけ見れば8割わかる Dagster 資産」適用済み）
1. `fetch_raw_pages` - Wikipedia APIからページ一覧を取得し、環境変数設定とAPI呼び出しを実行
2. `validate_pages` - Panderaでスキーマ検証を実行し、型変換と必須フィールドチェックを行う
3. `clean_and_process_pages` - テキストクリーニング、重複除去、メタデータ付与を実行
4. `store_pages_to_csv` - 処理済みデータを環境変数で指定されたパスにCSVファイルとして出力
5. `filter_pages_by_criteria` - タイトル条件でページをフィルタリングし、フォールバック機能で必ずデータを返す
6. `store_filtered_pages_to_csv` - フィルタリング済みデータを空チェックしてCSVファイルに出力

### ベストプラクティス適用内容
- **動詞ベースの命名**: `fetch_`, `validate_`, `clean_`, `store_`, `filter_` パターン
- **Google style docstring**: 処理内容を含む1行目 + Args/Returns（日本語）
- **動的メタデータ**: UI表示用の`row_count`, `preview`, `output_path`等
- **構造化ログ**: `{asset_name}: 開始/完了 {key=value}` パターン
- **明確な依存関係**: アセット間の依存関係とフォールバック機能

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

## 🔧 Dockerトラブルシューティング

### コンテナの状態確認
```bash
# 実行中のコンテナを確認
docker-compose ps

# Web UIのログを確認
docker-compose logs -f dagster-web

# 特定のコンテナに接続
docker-compose exec dagster-web bash
```

### よくある問題と解決方法

#### 1. ポート3000が既に使用されている
```bash
# 別のポートを使用する場合（docker-compose.yml を編集）
# "3001:3000" に変更してアクセスは http://localhost:3001
```

#### 2. データが生成されない
```bash
# dataディレクトリの権限を確認
ls -la data/

# ボリュームマウントの確認
docker-compose run --rm dagster-cli ls -la /app/data/
```

#### 3. コンテナの完全リセット
```bash
# すべて停止してクリーンアップ
docker-compose down
docker volume prune -f
rm -rf data/*

# 再構築して起動
docker-compose up --build -d dagster-web
```

### よく使うコマンド集
```bash
# === 基本操作 ===
# Web UI起動（推奨）
docker-compose up -d dagster-web

# ETLパイプライン実行
docker-compose run --rm dagster-cli uv run python ui/cli.py --job wikipedia_etl_job

# テスト実行
docker-compose run --rm dagster-test

# === データ確認 ===
# 出力ファイルの確認
docker-compose run --rm dagster-cli head -10 data/pages.csv

# === メンテナンス ===
# 全停止
docker-compose down

# 完全リビルド
docker-compose build --no-cache && docker-compose up -d dagster-web
```

## 📝 開発のポイント

- **オニオンアーキテクチャ**: ドメインロジックがインフラストラクチャの詳細から分離
- **型安全性**: Panderaによるデータスキーマ検証
- **拡張性**: 新しいデータソースや出力先の追加が容易
- **テスタビリティ**: 各層が独立してテスト可能
- **CLI対応**: コマンドラインから簡単に実行可能