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

### ✅ Claude に出すべき具体的な指示フォーマット

```markdown
以下の仕様で asset を追加して：
- validated_pages の後に、title に "List of" を含むページだけを抽出する filter_pages アセットを追加
- 新たなジョブ filter_job を作成
```

```markdown
domain/models.py の PageSchema に namespace カラム（str型）を追加し、関連コードも更新して
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
| **アセットの追加**     | 必ず `usecase/assets.py` に追加し、`definitions.py` にも登録 |
| **ジョブの追加**      | `usecase/jobs.py` に定義し、CLI 実行可能にする                |
| **スキーマ修正**      | `domain/models.py` を更新し、影響範囲のサービス層・アセットも更新        |
| **出力処理の変更**     | `infrastructure/storage.py` に実装（例：BQ出力に拡張）        |
| **新CLIオプション追加** | `ui/cli.py` にコマンド引数として拡張（例：--env, --output）       |

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

* `@asset`：Dagster のアセット定義
* `define_asset_job()`：ジョブの定義関数
* `validate(df)`：Pandera によるデータバリデーション
* `requests.get()`：Wikipedia API 通信
* `.to_csv()`：CSV 出力
* `argparse`：CLI 引数パーサ