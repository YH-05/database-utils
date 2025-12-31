---
title: CLAUDE.md
created_at: 2025-12-30
updated_at: 2025-12-31
# このプロパティは、Claude Codeが関連するドキュメントの更新を検知するために必要です。消去しないでください。
---

# database-utils

SQLite を中心としたデータベース接続ユーティリティ。金融データの管理（CRUD操作）とバックアップ/同期機能を提供する。

## プロジェクト概要

| 項目 | 内容 |
| --- | --- |
| 目的 | 金融データのデータベース管理を簡素化 |
| 主要DB | SQLite（将来的に他DBへの拡張を考慮） |
| 主な機能 | データの読み書き（CRUD）、バックアップ/同期 |

**Python 3.12** | uv | Ruff | pyright | pytest + Hypothesis | pre-commit | GitHub Actions

## クイックリファレンス

### 必須コマンド

```bash
# 品質チェック
make check-all          # 全チェック（format, lint, typecheck, test）
make format             # コードフォーマット
make lint               # リント
make typecheck          # 型チェック
make test               # テスト実行
make test-cov           # カバレッジ付きテスト

# 依存関係
uv add package_name     # 通常パッケージ追加
uv add --dev pkg        # 開発用パッケージ追加
uv sync --all-extras    # 全依存関係を同期

# GitHub操作
/commit-and-pr コマンド  # PR作成（gh pr create使用）
make issue TITLE="x" BODY="y"           # Issue作成
```

### Git 規則

-   **ブランチ**: `feature/` | `fix/` | `refactor/` | `docs/` | `test/` | `release/`
-   **ラベル**: `enhancement` | `bug` | `refactor` | `documentation` | `test`

## 実装規約

### 実装フロー

1. format → lint → typecheck → test
2. 新機能は TDD 必須
3. 全コードにログ必須
4. 重い処理はプロファイル実施

### コーディングスタイル

| 項目         | 規約                            |
| ------------ | ------------------------------- |
| 型ヒント     | Python 3.12 スタイル（PEP 695） |
| Docstring    | Google 形式                     |
| クラス名     | PascalCase                      |
| 関数/変数名  | snake_case                      |
| 定数         | UPPER_SNAKE                     |
| プライベート | \_prefix                        |

### エラーメッセージ

```python
# ❌ Bad
raise ValueError("Invalid input")

# ✅ Good
raise ValueError(f"Expected positive integer, got {count}")
raise ValueError(f"Failed to process {source_file}: {e}")
raise FileNotFoundError(f"Config not found. Create by: python -m {__package__}.init")
```

### ロギング（必須）

```python
from database_utils.utils.logging_config import get_logger

logger = get_logger(__name__)

def process_data(data: list) -> list:
    logger.debug("Processing started", item_count=len(data))
    try:
        result = transform(data)
        logger.info("Processing completed", output_count=len(result))
        return result
    except Exception as e:
        logger.error("Processing failed", error=str(e), exc_info=True)
        raise
```

### 環境変数

| 変数名      | 説明                              | デフォルト  |
| ----------- | --------------------------------- | ----------- |
| LOG_LEVEL   | ログレベル                        | INFO        |
| LOG_FORMAT  | フォーマット (json/text)          | text        |
| PROJECT_ENV | 環境 (development/production)     | development |

### アンカーコメント

```python
# AIDEV-NOTE: 実装の意図や背景の説明
# AIDEV-TODO: 未完了タスク
# AIDEV-QUESTION: 確認が必要な疑問点
```

## コード参照パターン

| 実装対象         | 参照先                                              |
| ---------------- | --------------------------------------------------- |
| DB接続           | `@src/database_utils/core/connection.py`            |
| CRUD操作         | `@src/database_utils/core/repository.py`            |
| バックアップ     | `@src/database_utils/core/backup.py`                |
| 型定義           | `@src/database_utils/types.py`                      |
| ユーティリティ   | `@src/database_utils/utils/helpers.py`              |
| ロギング設定     | `@src/database_utils/utils/logging_config.py`       |
| 単体テスト       | `@tests/unit/`                                      |
| 統合テスト       | `@tests/integration/`                               |

### プロファイリング使用例

```python
from database_utils.utils.profiling import profile, timeit, profile_context

@profile  # 詳細プロファイリング
def heavy_function():
    ...

@timeit  # 実行時間計測
def timed_function():
    ...

with profile_context("処理名"):  # コンテキスト計測
    ...
```

## タスク別ガイド参照

| タスク             | 参照先                                                     |
| ------------------ | ---------------------------------------------------------- |
| 開発開始           | `/kickoff` コマンド（アイデア → PRD → 設計 → 実装）        |
| 新機能追加         | `/add-feature` コマンド                                    |
| テスト作成         | `/write-tests` コマンド または `@docs/testing-strategy.md` |
| ドキュメント作成   | `@docs/document-management.md`                             |
| 図表作成           | `@docs/diagram-guidelines.md`                              |
| コード品質改善     | `/ensure-quality` コマンド（自動修正）                     |
| リファクタリング   | `/safe-refactor` コマンド                                  |
| コード分析         | `/analyze` コマンド（分析レポート出力）                    |
| 改善実装           | `/improve` コマンド（エビデンスベース改善）                |
| セキュリティ検証   | `/scan` コマンド（検証・スコアリング）                     |
| デバッグ           | `/troubleshoot` コマンド（体系的デバッグ）                 |
| タスク管理         | `/task` コマンド（複雑タスク分解・管理）                   |
| Git操作            | `/commit-and-pr` コマンド                                  |
| ドキュメントレビュー | `/review-docs` コマンド                                  |
| 初期化（初回のみ） | `/initialize-project` コマンド                             |
| コマンド一覧       | `/index` コマンド                                          |

## エビデンスベース開発

### 禁止語と推奨語

| 禁止           | 推奨                       |
| -------------- | -------------------------- |
| best, optimal  | measured X, documented Y   |
| faster, slower | reduces X%, increases Y ms |
| always, never  | typically, in most cases   |
| perfect, ideal | meets requirement X        |

### 証拠要件

-   **性能**: "measured Xms" | "reduces X%"
-   **品質**: "coverage X%" | "complexity Y"
-   **セキュリティ**: "scan detected X"

## 効率化テクニック

### コミュニケーション記法

```
→  処理フロー      analyze → fix → test
|  選択/区切り     option1 | option2
&  並列/結合       task1 & task2
»  シーケンス      step1 » step2
@  参照/場所       @file:line
```

### 実行パターン

-   **並列**: 依存なし & 競合なし → 複数ファイル読込、独立テスト
-   **バッチ**: 同種操作 → 一括フォーマット、インポート修正
-   **逐次**: 依存あり | 状態変更 → DB マイグレ、段階的リファクタ

### エラーリカバリー

-   **リトライ**: max 3 回、指数バックオフ
-   **フォールバック**: 高速手法 → 確実な手法
-   **状態復元**: チェックポイント » ロールバック

## ディレクトリ構成

```
src/database_utils/     # メインパッケージ
├── core/               # コアロジック（DB接続、CRUD操作）
├── utils/              # ユーティリティ
├── types.py            # 型定義
└── py.typed            # PEP 561マーカー

tests/
├── unit/               # 単体テスト
├── property/           # プロパティベーステスト
├── integration/        # 統合テスト
└── conftest.py         # フィクスチャ

docs/                   # 永続ドキュメント
.steering/              # 作業単位ドキュメント
.claude/                # Claude Code設定
```

## 更新トリガー

-   仕様/依存関係/構造/規約の変更時
-   同一質問 2 回以上 → FAQ 追加
-   エラーパターン 2 回以上 → トラブルシューティング追加
