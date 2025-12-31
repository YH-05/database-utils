# pydev-claude-code: Claude Code 向け Python テンプレート

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-latest-green.svg)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/discus0434/python-template-for-claude-code/actions/workflows/ci.yml/badge.svg)](https://github.com/discus0434/python-template-for-claude-code/actions/workflows/ci.yml)

このリポジトリは、[Claude Code](https://www.anthropic.com/claude-code) との協働に最適化された、本番環境に対応可能な Python プロジェクトテンプレートです。適度な型チェック、Claude Code のパフォーマンスを引き出すための包括的なドキュメントやテンプレート、便利なカスタムスラッシュコマンドなどを備えています。

## 🚀 クイックスタート

1.  GitHub で「Use this template」ボタンをクリックして、新しいリポジトリを作成
2.  新しいリポジトリをクローン
3.  セットアップスクリプトを実行
4.  Claude Code を初回起動して認証
5.  Claude Code の対話モードで`/initialize-project` コマンドを実行して、プロジェクトを初期化

```bash
# 新しいリポジトリをクローン
git clone https://github.com/yourusername/database-utils.git
cd database-utils

# ⚠️ 重要: Pythonバージョンを3.12に固定
uv python pin 3.12

# セットアップ
make setup
claude

# プロジェクトの初期化
claude  # /initialize-projectを実行
```

**⚠️ 重要:** セットアップ前に必ず`uv python pin 3.12`を実行してください。これにより、プロジェクトが正しい Python バージョンを使用することが保証されます。

セットアップスクリプトは、以下の処理を自動的に実行します。

-   プロジェクト内のすべての `database_utils` を、指定したプロジェクト名に置換
-   `uv` を使用して Python の仮想環境を構築（Python 3.12）
-   Claude Code をインストール
-   GitHub CLI (`gh`) をインストール（途中でログインを求められることがあります）
-   すべての依存関係をインストール
-   pre-commit フックを設定
-   初期テストを実行

## ⚠️ よくある問題とトラブルシューティング

### Python バージョンの問題

このプロジェクトは**Python 3.12**をターゲットバージョンとしています。異なるバージョンの Python を使用すると、型チェックや CI/CD で問題が発生する場合があります。

**問題の症状：**

-   pyright が「Template string literals (t-strings) require Python 3.14 or newer」などのエラーを報告
-   GitHub CI の lint ジョブが失敗
-   ローカルでは問題ないのに CI で失敗する

**原因：**

-   システムに複数の Python バージョンがインストールされている場合、意図しないバージョン（例: Python 3.14）が使用される可能性があります
-   pyright がプロジェクトのターゲットバージョンと異なる標準ライブラリをチェックしようとしてエラーが発生

**解決方法：**

1. **Python バージョンを明示的に固定：**

    ```bash
    uv python pin 3.12
    ```

    これにより`.python-version`ファイルが作成され、uv が常に Python 3.12 を使用するようになります。

2. **仮想環境を再構築：**

    ```bash
    uv sync --all-extras
    ```

3. **pre-commit フックを確認：**
    ```bash
    uv run pre-commit run --all-files
    ```

**予防策：**

-   プロジェクトのセットアップ時に必ず`uv python pin 3.12`を実行
-   `.python-version`ファイルを gitignore から除外することを検討（チームで統一するため）
-   CI/CD ワークフローで明示的に Python バージョンを指定（すでに`.github/workflows/ci.yml`で設定済み）

### その他のトラブルシューティング

**依存関係のエラー：**

```bash
# 依存関係をクリーンインストール
uv sync --reinstall
```

**pre-commit フックのエラー：**

```bash
# pre-commitキャッシュをクリア
uv run pre-commit clean
uv run pre-commit install --install-hooks
```

**型チェックエラー：**

```bash
# pyright設定の確認
uv run pyright --version
# pyproject.tomlのpyright設定を確認
```

## 📁 プロジェクト構造

```
project-root/
├── .claude/                      # Claude Codeの設定ファイル
│   ├── skills/                   # スキル定義
│   ├── commands/                 # スラッシュコマンド
│   └── agents/                   # サブエージェント
├── docs/                         # ドキュメント
│   ├── ideas/                    # アイデアメモ
├── .steering/                    # 作業単位のドキュメント
│   └── [YYYYMMDD]_[開発タイトル]/ # 作業ドキュメント（日付と開発タイトルを記載）
│       ├── requirements.md       # 作業の要求内容
│       ├── design.md             # 変更内容の設計
│       ├── tasklist.md           # タスクリスト
│       └── decisiongs.md         # 議論の内容や重要な決定事項の記録
├── .github/                      # GitHub Actionsの設定ファイル
│   ├── workflows/                # CI/CD + ベンチマークのワークフロー
│   │   ├── ci.yml                # メインCI（テスト、リント、型チェック）
│   │   └── benchmark.yml         # パフォーマンスベンチマーク
│   ├── dependabot.yml            # Dependabotの設定
│   ├── ISSUE_TEMPLATE/           # Issueテンプレート
│   └── PULL_REQUEST_TEMPLATE.md  # Pull Requestテンプレート
├── scripts/                      # セットアップ用スクリプト
├── src/                          # ソースコード
│   └── database_utils/             # メインパッケージ（`uv sync` でインストール可能）
│       ├── __init__.py
│       ├── py.typed              # PEP 561に準拠した型情報マーカー
│       ├── types.py              # プロジェクト共通の型定義
│       ├── core/                 # コアロジック
│       └── utils/                # ユーティリティ
├── tests/                        # テストコード
│   ├── unit/                     # 単体テスト
│   ├── property/                 # プロパティベーステスト
│   ├── integration/              # 結合テスト
│   └── conftest.py               # pytestの設定
├── .pre-commit-config.yaml       # pre-commitの設定
├── pyproject.toml                # 依存関係とツールの設定
├── README.md                     # プロジェクトの説明
└── CLAUDE.md                     # Claude Code用ガイド
```

## 📚 ドキュメント階層

### 🎯 主要ドキュメント

-   **[CLAUDE.md](CLAUDE.md)** - プロジェクト全体の包括的なガイド
    -   プロジェクト概要とコーディング規約
    -   よく使うコマンドと GitHub 操作
    -   型ヒント、テスト戦略、セキュリティ
