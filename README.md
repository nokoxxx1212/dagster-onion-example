# Data Pipeline ETL with Dagster & Onion Architecture

汎用的なETLパイプラインプロジェクトです。Dagsterを使ったデータオーケストレーションと、オニオンアーキテクチャに基づいた構成を採用しています。

## 🎯 プロジェクト概要

このプロジェクトは**Wikipedia API**から記事リストを取得し、**CSV**に保存するETLパイプラインですが、将来的に様々なデータソースに対応できるよう汎用的に設計されています。

## 🏗️ アーキテクチャ

### ディレクトリ構成
```
data-pipeline-etl/
├── domain/                 # ドメイン層（抽象化とビジネスロジック）
│   ├── models.py           # Pandera でのスキーマ定義・データ構造
│   ├── repositories.py     # 抽象インターフェース定義
│   └── services.py         # バリデーションなどビジネスロジック処理
├── infrastructure/         # インフラ層（外部システム実装）
│   ├── api_clients.py      # 外部API実装（HTTP通信）
│   └── storage.py          # ファイルシステム実装（CSV・JSON保存）
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

## 🔄 処理フローの詳細

### CLIからファイル保存までの実行フロー

#### 1. エントリポイント: `ui/cli.py`
```python
# python ui/cli.py --job wikipedia_etl_job の実行
main() → execute_job() → materialize(all_assets)
```

#### 2. アセット定義の取得: `definitions.py`
Dagsterが依存関係順に以下のアセットを実行：
```python
assets = [
    fetch_raw_pages,           # ① データ取得
    validate_pages,            # ② データ検証  
    clean_and_process_pages,   # ③ データ処理
    store_pages_to_csv,        # ④ ファイル保存 🎯
    # ...
]
```

#### 3. 各アセットの処理詳細

**① `fetch_raw_pages()` - データ取得**
```
usecase/assets.py:fetch_raw_pages()
    ↓ 環境変数から設定取得
    ↓ WikipediaApiConfig作成
    ↓ infrastructure/api_clients.py:WikipediaApiClient.fetch_wikipedia_pages()
    ↓ requests.get() → Wikipedia API呼び出し
    ↓ JSONレスポンス → pandas.DataFrame変換
```

**② `validate_pages()` - データ検証**
```
usecase/assets.py:validate_pages()
    ↓ domain/services.py:ValidationService.validate_wikipedia_pages()
    ↓ domain/models.py:PageSchema.validate() (Pandera)
    ↓ 型チェック・必須フィールド検証
```

**③ `clean_and_process_pages()` - データ処理**
```
usecase/assets.py:clean_and_process_pages()
    ↓ domain/services.py:DataProcessingService
    ↓ clean_text_data() → テキストクリーニング
    ↓ deduplicate_data() → 重複除去
    ↓ add_metadata_columns() → メタデータ付与
```

**④ `store_pages_to_csv()` - ファイル保存** 🎯
```
usecase/assets.py:store_pages_to_csv()
    ↓ 環境変数から出力パス取得
    ↓ infrastructure/storage.py:StorageFactory.create_adapter("csv")
    ↓ infrastructure/storage.py:DataExporter.export_with_metadata()
    ↓ infrastructure/storage.py:CsvStorageAdapter.save_dataframe()
    ↓ pandas.DataFrame.to_csv() → data/pages.csv保存完了 ✅
```

### 実行フロー図
```
CLI実行
  ↓
ui/cli.py
  ↓
definitions.py (アセット定義)
  ↓
Dagster実行エンジン
  ↓
┌─ fetch_raw_pages ─────────────────┐
│ infrastructure/api_clients.py     │
│ └─ Wikipedia API → DataFrame      │
└───────────────────┬───────────────┘
                    ↓
┌─ validate_pages ──┴───────────────┐
│ domain/services.py                │
│ └─ Pandera検証                    │
└───────────────────┬───────────────┘
                    ↓
┌─ clean_and_process_pages ─┴──────┐
│ domain/services.py               │
│ └─ クリーニング・重複除去・メタデータ │
└───────────────────┬──────────────┘
                    ↓
┌─ store_pages_to_csv ──┴──────────┐
│ infrastructure/storage.py        │
│ └─ CSV出力 → data/pages.csv     │
└──────────────────────────────────┘
```

### オニオンアーキテクチャでの責務分離

#### **正しい層分離（修正後）**
- **UI層** (`ui/cli.py`): コマンドライン入力・ユーザーインターフェース
- **ユースケース層** (`usecase/assets.py`): Dagsterアセット定義・ワークフローの組み立て
- **ドメイン層** (`domain/`): **抽象インターフェース・ビジネスロジック・データ検証**
  - `repositories.py`: 抽象インターフェース定義のみ
  - `services.py`: ビジネスロジック
  - `models.py`: データ構造・スキーマ定義
- **インフラ層** (`infrastructure/`): **外部システムとの実際の通信**
  - `api_clients.py`: 外部API実装（HTTP通信）
  - `storage.py`: ファイルシステム実装

#### **アーキテクチャの利点**
```
🔵 Domain層: 抽象化により外部依存なし
    ↑ 実装
🟠 Infrastructure層: 具体的な外部アクセス
    ↑ 使用
🟡 Usecase層: ビジネスロジックの組み立て
    ↑ 操作
🟢 UI層: ユーザーとの接点
```

この正しい設計により、各層が独立してテスト可能で、将来的な拡張（BigQuery出力、キャッシュ機能、別API連携など）が容易になっています。

## 🔧 設定とカスタマイズ

### 環境変数（.env）
`.env.example`をコピーして`.env`ファイルを作成してください：

```env
WIKI_API_URL=https://en.wikipedia.org/w/api.php
OUTPUT_PATH=data/pages.csv
```

**注意**: `.env`ファイルは`.gitignore`に含まれており、リポジトリにコミットされません。

### 新しいデータソースの追加

1. `domain/repositories.py`に新しい抽象インターフェースを追加
2. `infrastructure/api_clients.py`に実際のAPI実装クラスを追加
3. `domain/models.py`にスキーマ定義を追加
4. `usecase/assets.py`に新しいアセットを定義（infrastructure実装を使用）
5. `usecase/jobs.py`に新しいジョブを追加

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

## 👥 チーム別開発ルール

### データサイエンティスト担当エリア

**主な責務**: データ分析・モデリング・ビジネスロジック定義

| ディレクトリ | ファイル | 役割 |
|-------------|----------|------|
| `domain/` | `models.py` | データスキーマ・バリデーションルール定義 |
| `domain/` | `services.py` | データ処理・分析ロジック |
| `usecase/` | `assets.py` | データパイプライン設計・アセット定義 |

**修正権限**:
- ✅ データスキーマ（Pandera）の追加・変更
- ✅ バリデーションルール・データ品質チェック
- ✅ データ処理・変換ロジック
- ✅ アセット間の依存関係・パイプライン設計
- ✅ メタデータ・ログ定義

**変更例**:
```python
# domain/models.py - 新しいデータスキーマ追加
class NewDataSchema(pa.DataFrameModel):
    id: int
    category: str
    score: float

# domain/services.py - 新しい分析ロジック追加  
def analyze_data_quality(df: pd.DataFrame) -> ProcessingResult:
    # データ品質分析ロジック
    
# usecase/assets.py - 新しいアセット追加
@asset
def analyze_data_trends(processed_data: pd.DataFrame):
    # トレンド分析処理
```

### ソフトウェアエンジニア担当エリア

**主な責務**: インフラ実装・システム設計・UI/UX

| ディレクトリ | ファイル | 役割 |
|-------------|----------|------|
| `infrastructure/` | `api_clients.py` | 外部API・HTTP通信実装 |
| `infrastructure/` | `storage.py` | データストレージ・出力実装 |
| `ui/` | `cli.py` | CLI・ユーザーインターフェース |
| `domain/` | `repositories.py` | 抽象インターフェース設計 |

**修正権限**:
- ✅ API実装・HTTP通信・認証
- ✅ ファイル・データベース・クラウドストレージ実装
- ✅ CLI引数・オプション・ユーザビリティ改善
- ✅ エラーハンドリング・例外処理
- ✅ パフォーマンス最適化・接続設定

**変更例**:
```python
# infrastructure/api_clients.py - 新API実装
class SlackApiClient(NotificationRepository):
    def send_notification(self, message: str):
        # Slack API実装

# infrastructure/storage.py - 新出力先実装
class BigQueryAdapter(StorageAdapter):
    def save_dataframe(self, df: pd.DataFrame, table: str):
        # BigQuery出力実装

# ui/cli.py - 新CLIオプション追加
parser.add_argument('--notify', help='通知先指定')
```

### 🔄 協働フロー

#### 新機能追加時の進め方

1. **要件整理** (データサイエンティスト主導)
   - 何のデータが必要か
   - どんな処理・分析が必要か
   - 出力形式・品質要件

2. **設計協議** (両チーム)
   - データスキーマ設計
   - 抽象インターフェース設計
   - アーキテクチャレビュー

3. **並行開発**
   - **データサイエンティスト**: `domain/` + `usecase/` の実装
   - **ソフトウェアエンジニア**: `infrastructure/` + `ui/` の実装

4. **統合テスト** (両チーム)
   - パイプライン全体のテスト
   - パフォーマンス検証

#### ⚠️ 注意事項

| 禁止事項 | 理由 |
|----------|------|
| データサイエンティストが`infrastructure/`の実装詳細を修正 | 技術実装の責務分離 |
| ソフトウェアエンジニアが`domain/services.py`のビジネスロジックを修正 | ドメイン知識の責務分離 |
| 一方のチームが勝手にスキーマや抽象インターフェースを変更 | 影響範囲が広いため要協議 |

#### 🤝 協議が必要なケース

- データスキーマの大幅変更
- 新しい抽象インターフェースの追加
- パフォーマンスに影響する変更
- 外部システムとの連携仕様変更