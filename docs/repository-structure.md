# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造

```
database-utils/
├── src/database_utils/    # メインパッケージ
│   ├── core/              # コアロジック
│   └── utils/             # ユーティリティ
├── tests/                 # テストコード
│   ├── unit/              # ユニットテスト
│   ├── integration/       # 統合テスト
│   └── property/          # プロパティベーステスト
├── docs/                  # プロジェクトドキュメント
├── template/              # テンプレート参照（変更禁止）
├── .claude/               # Claude Code設定
└── .steering/             # 作業単位ドキュメント
```

## ディレクトリ詳細

### src/database_utils/ (メインパッケージ)

#### ルートファイル

**配置ファイル**:
- `__init__.py`: パッケージエクスポート（公開API）
- `types.py`: 型定義（TypedDict, dataclass, Literal）
- `exceptions.py`: カスタム例外クラス
- `py.typed`: PEP 561マーカー

**命名規則**:
- snake_case
- 型定義は `types.py` に集約

#### core/

**役割**: コアビジネスロジック

**配置ファイル**:
- `connection.py`: DatabaseConnection クラス
- `schema.py`: SQLスキーマ定義
- `identifier.py`: IdentifierResolver クラス
- `repositories/`: リポジトリクラス群

**命名規則**:
- 機能単位でファイル分割
- リポジトリは `repositories/` サブディレクトリに配置

**依存関係**:
- 依存可能: utils/
- 依存禁止: なし

**例**:
```
core/
├── __init__.py
├── connection.py
├── schema.py
├── identifier.py
└── repositories/
    ├── __init__.py
    ├── security.py
    ├── price.py
    └── factor.py
```

#### utils/

**役割**: 汎用ユーティリティ関数

**配置ファイル**:
- `backup.py`: BackupManager クラス
- `logging_config.py`: ログ設定
- `helpers.py`: 汎用ヘルパー関数

**命名規則**:
- 機能単位でファイル分割
- 汎用関数は `helpers.py` に配置

**依存関係**:
- 依存可能: なし（最下層）
- 依存禁止: core/

### tests/ (テストディレクトリ)

#### unit/

**役割**: ユニットテストの配置

**構造**:
```
tests/unit/
├── core/
│   ├── test_connection.py
│   ├── test_identifier.py
│   └── repositories/
│       ├── test_security.py
│       ├── test_price.py
│       └── test_factor.py
└── utils/
    └── test_backup.py
```

**命名規則**:
- パターン: `test_[テスト対象ファイル名].py`
- 例: `connection.py` → `test_connection.py`

#### integration/

**役割**: 統合テストの配置

**構造**:
```
tests/integration/
├── test_crud_flow.py      # CRUD一連フロー
├── test_multi_source.py   # 複数ソース統合
└── test_transaction.py    # トランザクション
```

#### property/

**役割**: プロパティベーステスト（Hypothesis）

**構造**:
```
tests/property/
├── test_identifier_patterns.py  # 識別子パターン
└── test_date_queries.py         # 日付クエリ
```

### docs/ (ドキュメントディレクトリ)

**配置ドキュメント**:
- `product-requirements.md`: プロダクト要求定義書
- `functional-design.md`: 機能設計書
- `architecture.md`: アーキテクチャ設計書
- `repository-structure.md`: リポジトリ構造定義書（本ドキュメント）
- `development-guidelines.md`: 開発ガイドライン
- `glossary.md`: 用語集

### template/ (テンプレート参照)

**役割**: 実装パターンの参照元（変更・削除禁止）

**使用方法**: 新規コード作成時にパターンを参照

### .steering/ (ステアリングファイル)

**役割**: 特定の開発作業における作業計画・タスク管理

**構造**:
```
.steering/
└── [YYYYMMDD]-[task-name]/
    ├── requirements.md      # 今回の作業の要求内容
    ├── design.md            # 変更内容の設計
    └── tasklist.md          # タスクリスト
```

**命名規則**: `20250101-add-factor-repository` 形式

## ファイル配置規則

### ソースファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| 型定義 | src/database_utils/types.py | 集約 | SecurityDict, PriceDataDict |
| 例外 | src/database_utils/exceptions.py | 集約 | IdentifierNotFoundError |
| 接続管理 | src/database_utils/core/connection.py | 単一 | DatabaseConnection |
| リポジトリ | src/database_utils/core/repositories/*.py | 機能別 | security.py, price.py |
| ユーティリティ | src/database_utils/utils/*.py | 機能別 | backup.py |

### テストファイル

| テスト種別 | 配置先 | 命名規則 | 例 |
|-----------|--------|---------|-----|
| ユニットテスト | tests/unit/ | test_[対象].py | test_connection.py |
| 統合テスト | tests/integration/ | test_[機能].py | test_crud_flow.py |
| プロパティテスト | tests/property/ | test_[対象].py | test_identifier_patterns.py |

## 命名規則

### ディレクトリ名

- **レイヤーディレクトリ**: snake_case
  - 例: `core/`, `utils/`, `repositories/`
- **テストディレクトリ**: snake_case
  - 例: `unit/`, `integration/`, `property/`

### ファイル名

- **モジュールファイル**: snake_case
  - 例: `connection.py`, `identifier.py`
- **テストファイル**: `test_` プレフィックス
  - 例: `test_connection.py`

### クラス名

- **PascalCase**
  - 例: `DatabaseConnection`, `IdentifierResolver`, `SecurityRepository`

### 関数/メソッド名

- **snake_case**
  - 例: `resolve_auto()`, `get_prices()`, `upsert_value()`

## 依存関係のルール

### レイヤー間の依存

```
公開API (__init__.py)
    ↓ (OK)
識別子解決 (identifier.py)
    ↓ (OK)
リポジトリ (repositories/*.py)
    ↓ (OK)
ユーティリティ (utils/*.py)
```

**禁止される依存**:
- utils/ → core/ (❌)
- repositories/ → identifier.py (❌ 循環防止)

### モジュール間の依存

**循環依存の禁止**:
```python
# ❌ 悪い例
# security.py
from .price import PriceRepository

# price.py
from .security import SecurityRepository  # 循環依存
```

**解決策**:
```python
# ✅ 良い例: Protocolを使用
# protocols.py
class SecurityRepositoryProtocol(Protocol):
    def get(self, security_id: int) -> Security | None: ...

# price.py
from .protocols import SecurityRepositoryProtocol
```

## スケーリング戦略

### 機能の追加

新しいリポジトリを追加する際:

1. `src/database_utils/core/repositories/` に新規ファイル作成
2. `types.py` に関連する型を追加
3. `core/__init__.py` でエクスポート
4. `tests/unit/core/repositories/` にテスト追加

**例**: TradeRepositoryの追加
```
src/database_utils/core/repositories/
├── __init__.py  # TradeRepository を追加
└── trade.py     # 新規作成

tests/unit/core/repositories/
└── test_trade.py  # 新規作成
```

### ファイルサイズの管理

**ファイル分割の目安**:
- 1ファイル: 300行以下を推奨
- 300-500行: リファクタリングを検討
- 500行以上: 分割を強く推奨

## 除外設定

### .gitignore

```
.venv/
__pycache__/
*.pyc
dist/
.env
.steering/
*.log
.DS_Store
*.db
backups/
```

### Ruff除外設定 (pyproject.toml)

```toml
[tool.ruff]
exclude = [
    ".venv",
    "__pycache__",
    ".steering",
    "dist",
    "template",
]
```
