## ✅ プロジェクト概要

このプロジェクトは **Wikipedia API** から記事リストを取得し、**CSV に保存する ETL パイプライン**を構築するものです。
**Dagster** を使ったデータオーケストレーションと、**オニオンアーキテクチャ**に基づいたディレクトリ構成を採用しています。
実行は `python ui/cli.py --job <job_name>` によって CLI 経由で行われます。

---

## 💡 Claude に依頼する目的と指示例

### 🎯 Claude に期待するアウトプット例

* 新しい ETL ステップ（例：フィルタ処理、BQ 出力など）の追加
* バリデーションスキーマの拡張
* Dagster アセットの追加やリファクタ
* CLI の改善（例：複数ジョブ対応、環境選択対応）
* テストコードの生成
* **「UIだけ見れば8割わかる Dagster 資産」** ベストプラクティスの適用

### 🎨 「UIだけ見れば8割わかる Dagster 資産」とは

Dagster Web UIを見るだけで、アセットの内容や処理フローが直感的に理解できる設計手法です。本プロジェクトでは以下のベストプラクティスを適用しています：

#### ✅ 適用済みベストプラクティス

1. **動詞ベースの命名規則**
   ```python
   # ❌ 旧: raw_wikipedia_pages, validated_pages
   # ✅ 新: fetch_raw_pages, validate_pages, clean_and_process_pages, store_pages_to_csv
   ```

2. **Google style docstring（処理内容含む1行目 + Args/Returns）**
   ```python
   @asset(description="Wikipedia APIからページ一覧（pageid, title）を取得する")
   def fetch_raw_pages(context: AssetExecutionContext) -> pd.DataFrame:
       """Wikipedia APIからページ一覧を取得し、環境変数設定とAPI呼び出しを実行する。
       
       Args:
           context: Dagsterアセット実行コンテキスト
           
       Returns:
           pd.DataFrame: pageidとtitleカラムを含む生データのDataFrame
       """
   ```

3. **動的メタデータ（UI表示用）**
   ```python
   context.add_output_metadata({
       "row_count": len(df),
       "preview": MetadataValue.md(preview_md),
       "api_url": MetadataValue.url(api_url),
       "columns": list(df.columns),
   })
   ```

4. **構造化ログ（日本語、要点のみ）**
   ```python
   context.log.info("fetch_raw_pages: 開始")
   context.log.info(f"fetch_raw_pages: 完了 rows={len(df)} api_url={api_url}")
   ```

5. **明確な依存関係とフォールバック機能**
   - 各アセットが前段階の出力を明示的に受け取る
   - エラーハンドリングとフォールバック処理を含む

### ✅ Claude に出すべき具体的な指示フォーマット

```markdown
以下の仕様で asset を追加して：
- validate_pages の後に、title に "List of" を含むページだけを抽出する filter_pages_by_list アセットを追加
- 「UIだけ見れば8割わかる Dagster 資産」ベストプラクティスを適用（動詞命名、Google style docstring、動的メタデータ、構造化ログ）
- 新たなジョブ filter_job を作成
```

```markdown
domain/models.py の PageSchema に namespace カラム（str型）を追加し、関連コードも更新して
既存アセットも「UIだけ見れば8割わかる」パターンに合わせて更新
docstringはGoogle style（処理内容含む1行目 + Args/Returns）で記述
```

---

## 🧱 アーキテクチャ

### 📦 ディレクトリ構成（役割付き）

```
wikipedia_project/
├── domain/                 # ドメイン層（ビジネスロジックの中心）
│   ├── models.py           # Pandera でのスキーマ定義（入力・出力形式）
│   ├── repositories.py     # 外部API（Wikipedia）の取得処理
│   └── services.py         # バリデーションなどロジック処理
├── infrastructure/         # 外部インターフェース層（永続化やI/O）
│   └── storage.py          # CSV保存処理（BigQuery対応可能）
├── usecase/                # ユースケース層（Dagster資産の定義）
│   ├── assets.py           # Dagsterの @asset 定義（処理のステップ）
│   └── jobs.py             # Dagsterのジョブ定義（実行単位）
├── ui/                     # プレゼンテーション層（CLIなど）
│   └── cli.py              # CLI でジョブを実行するエントリポイント
├── definitions.py          # Dagster Definitions をまとめる
├── pyproject.toml          # Python 環境構成（uv 用）
├── Dockerfile              # Docker イメージ定義
├── docker-compose.yml      # コンテナオーケストレーション
├── .env                    # API URLや出力先などの環境変数

```

---

## ⚙️ 環境変数（.env）

```env
WIKI_API_URL=https://en.wikipedia.org/w/api.php
OUTPUT_PATH=data/pages.csv
```

---

## 🛠️ コア技術スタック

| 技術           | 用途               |
| ------------ | ---------------- |
| **Dagster**  | ETL パイプライン構築     |
| **Pandera**  | データスキーマ検証        |
| **Requests** | Wikipedia API 通信 |
| **Pandas**   | データフレーム操作        |
| **dotenv**   | 設定の環境変数管理        |
| **uv**       | Python 依存管理      |
| **Docker**   | 開発・実行環境の統一       |

---

## 🧪 Claude 向けルールと制約

| 目的              | 指針                                                |
| --------------- | ------------------------------------------------- |
| **アセットの追加**     | 必ず `usecase/assets.py` に追加し、`definitions.py` にも登録<br/>**「UIだけ見れば8割わかる」パターンを適用** |
| **ジョブの追加**      | `usecase/jobs.py` に定義し、CLI 実行可能にする                |
| **スキーマ修正**      | `domain/models.py` を更新し、影響範囲のサービス層・アセットも更新        |
| **出力処理の変更**     | `infrastructure/storage.py` に実装（例：BQ出力に拡張）        |
| **新CLIオプション追加** | `ui/cli.py` にコマンド引数として拡張（例：--env, --output）       |

### 📋 現在のアセット一覧（実行順）

1. **fetch_raw_pages** - Wikipedia APIからページ一覧を取得
2. **validate_pages** - Panderaでスキーマ検証・欠損処理
3. **clean_and_process_pages** - データクリーニングとメタデータ付与
4. **store_pages_to_csv** - 処理済みデータをCSVに出力
5. **filter_pages_by_criteria** - 特定条件でページをフィルタリング
6. **store_filtered_pages_to_csv** - フィルタ済みデータを別CSVに出力

---

## 🚀 実行方法（確認用）

### ローカルで実行（uv + CLI）

```bash
uv sync
python ui/cli.py --job wikipedia_etl_job
```

### Docker 実行

```bash
docker-compose up --build
```

---

## 🧠 Claude が知っておくべきエントリポイント

| 種類     | ファイル名               | 内容                   |
| ------ | ------------------- | -------------------- |
| 定義集約   | `definitions.py`    | Dagsterの Definitions |
| CLI    | `ui/cli.py`         | CLIエントリポイント          |
| アセット定義 | `usecase/assets.py` | ETLパイプラインの構成         |
| ジョブ定義  | `usecase/jobs.py`   | ジョブ名と処理の紐付け          |
| ドメイン層  | `domain/*.py`       | データスキーマ・ロジック         |

---

## 🧩 Claude 用リファレンスキーワード

### 🔧 基本的なDagster要素
* `@asset`：Dagster のアセット定義
* `define_asset_job()`：ジョブの定義関数
* `AssetExecutionContext`：アセット実行コンテキスト
* `MetadataValue`：UI表示用メタデータ（.md(), .url(), .path()）
* `context.add_output_metadata()`：動的メタデータ付与
* `context.log.info()`：構造化ログ出力

### 📊 データ処理・検証
* `validate(df)`：Pandera によるデータバリデーション
* `requests.get()`：Wikipedia API 通信
* `.to_csv()`：CSV 出力
* `pd.DataFrame`：データフレーム操作

### 🎨 「UIだけ見れば8割わかる」パターン
* **動詞命名**: `fetch_`, `validate_`, `clean_`, `store_`, `filter_`
* **Google style docstring**: 処理内容含む1行目 + Args/Returns（日本語）
* **動的メタデータ**: row_count, preview, output_path 等
* **構造化ログ**: `{asset_name}: 開始/完了 {key=value}`

### 🛠️ インフラ・CLI
* `argparse`：CLI 引数パーサ
* `load_dotenv()`：環境変数読み込み
* `StorageFactory`：CSV/BQ 出力アダプタ