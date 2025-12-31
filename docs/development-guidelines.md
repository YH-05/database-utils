# 開発ガイドライン (Development Guidelines)

## コーディング規約

### Python規約

#### 型ヒント（PEP 695スタイル）

```python
# ✅ Good: Python 3.12スタイル - 型エイリアス
type SecurityId = int
type IdentifierType = Literal['ISIN', 'CUSIP', 'SEDOL', 'TICKER_YAHOO', 'JP_CODE']

def resolve(identifier: str) -> SecurityId | None:
    ...

# ❌ Bad: 旧スタイル
from typing import Optional, Union
def resolve(identifier: str) -> Optional[int]:  # 使わない
    ...
```

#### ジェネリック型パラメータ（PEP 695スタイル）

```python
# ✅ Good: Python 3.12スタイル - ジェネリッククラス
class Repository[T]:
    def __init__(self, model_type: type[T]) -> None:
        self._model_type = model_type
        self._items: list[T] = []

    def add(self, item: T) -> None:
        self._items.append(item)

    def get_all(self) -> list[T]:
        return self._items.copy()

# ✅ Good: Python 3.12スタイル - ジェネリック関数
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

def map_items[T, U](items: list[T], func: Callable[[T], U]) -> list[U]:
    return [func(item) for item in items]

# ✅ Good: Python 3.12スタイル - 型パラメータ付き型エイリアス
type Result[T] = T | None
type Callback[T] = Callable[[T], None]

# ❌ Bad: 旧スタイル - TypeVarを明示的に定義
from typing import TypeVar, Generic
T = TypeVar('T')

class Repository(Generic[T]):  # 使わない
    ...

def first(items: list[T]) -> T | None:  # 使わない
    ...
```

#### dataclass使用

```python
from dataclasses import dataclass

# ✅ Good: frozen=True, slots=True を使用
@dataclass(frozen=True, slots=True)
class Security:
    security_id: int
    name: str
    is_active: bool = True

# ❌ Bad: オプションなし
@dataclass
class Security:
    security_id: int
    name: str
```

### 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| クラス | PascalCase | `DatabaseConnection`, `IdentifierResolver` |
| 関数/メソッド | snake_case | `get_prices()`, `resolve_auto()` |
| 変数 | snake_case | `security_id`, `price_data` |
| 定数 | UPPER_SNAKE | `DEFAULT_PRIORITY`, `MAX_RETRIES` |
| プライベート | _prefix | `_connection`, `_validate()` |
| 型エイリアス | PascalCase | `SecurityId`, `IdentifierType` |

### Docstring（Google形式）

```python
def resolve(
    self,
    identifier_value: str,
    identifier_type: IdentifierType,
    as_of: date | None = None,
) -> int | None:
    """外部識別子を内部IDに解決する。

    Args:
        identifier_value: 識別子の値。
        identifier_type: 識別子のタイプ（ISIN, CUSIP等）。
        as_of: ポイントインタイム検索日。Noneの場合は現在日。

    Returns:
        内部セキュリティID。見つからない場合はNone。

    Raises:
        ValidationError: 識別子の形式が不正な場合。

    Examples:
        >>> resolver.resolve("7203", "JP_CODE")
        42
        >>> resolver.resolve("INVALID", "JP_CODE")
        None
    """
```

### エラーハンドリング

```python
# ✅ Good: 具体的なエラーメッセージ
raise IdentifierNotFoundError(
    identifier_type="JP_CODE",
    identifier_value="9999",
)

# ❌ Bad: 曖昧なエラー
raise ValueError("Not found")
```

### ロギング

```python
from database_utils.utils.logging_config import get_logger

logger = get_logger(__name__)

def resolve(self, identifier_value: str, identifier_type: str) -> int | None:
    logger.debug(
        "Resolving identifier",
        identifier_type=identifier_type,
        identifier_value=identifier_value,
    )

    result = self._lookup(identifier_value, identifier_type)

    if result is None:
        logger.warning(
            "Identifier not found",
            identifier_type=identifier_type,
            identifier_value=identifier_value,
        )
    else:
        logger.debug(
            "Identifier resolved",
            identifier_type=identifier_type,
            security_id=result,
        )

    return result
```

### SQLインジェクション対策

```python
# ✅ Good: パラメータ化クエリ
cursor.execute(
    "SELECT * FROM securities WHERE security_id = ?",
    (security_id,)
)

# ❌ Bad: 文字列結合（絶対禁止）
cursor.execute(f"SELECT * FROM securities WHERE security_id = {security_id}")
```

## Git運用ルール

### ブランチ戦略（Git Flow簡易版）

```
main          ─────●─────────●─────────●─────
                   ↑         ↑         ↑
feature/*     ────○───○─────○    ────○───○
                      merge          merge

fix/*         ────────────────○───○
                               merge
```

| ブランチ | 用途 | マージ先 |
|---------|------|---------|
| main | 安定版 | - |
| feature/* | 新機能開発 | main |
| fix/* | バグ修正 | main |
| refactor/* | リファクタリング | main |
| docs/* | ドキュメント | main |
| test/* | テスト追加 | main |

### コミットメッセージ

**形式**: Conventional Commits

```
<type>(<scope>): <description>

[body]

[footer]
```

**type一覧**:
- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `docs`: ドキュメント
- `test`: テスト
- `chore`: ビルド・設定変更

**例**:
```
feat(identifier): add auto-detection for ISIN format

- Detect 12-character identifiers starting with country code
- Add validation pattern for ISIN check digit

Closes #123
```

### PRプロセス

1. featureブランチを作成
2. 実装・テスト追加
3. `make check-all` で品質チェック
4. PRを作成
5. レビュー後にmainへマージ

## テスト戦略

### テストピラミッド

```
        /\
       /  \  E2E (少)
      /----\
     /      \  統合 (中)
    /--------\
   /          \  ユニット (多)
  --------------
```

### カバレッジ目標

| テスト種別 | 目標 |
|-----------|------|
| 全体 | 80% |
| core/ | 90% |
| utils/ | 85% |

### テストパターン

```python
import pytest
from database_utils.core.identifier import IdentifierResolver

class TestIdentifierResolver:
    """IdentifierResolverのテスト"""

    @pytest.fixture
    def resolver(self, db_connection):
        return IdentifierResolver(db_connection)

    def test_resolve_existing_identifier(self, resolver):
        """存在する識別子が正しく解決される"""
        # Arrange
        expected_id = 42

        # Act
        result = resolver.resolve("7203", "JP_CODE")

        # Assert
        assert result == expected_id

    def test_resolve_nonexistent_returns_none(self, resolver):
        """存在しない識別子はNoneを返す"""
        result = resolver.resolve("9999", "JP_CODE")
        assert result is None

    @pytest.mark.parametrize("identifier,expected_type", [
        ("US0378331005", "ISIN"),
        ("7203", "JP_CODE"),
        ("BBG000B9XRY4", "FIGI"),
    ])
    def test_auto_detect_identifier_type(self, resolver, identifier, expected_type):
        """識別子タイプが正しく自動検出される"""
        detected = resolver._detect_type(identifier)
        assert detected == expected_type
```

### Hypothesisプロパティテスト

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=20))
def test_resolve_never_raises_on_arbitrary_input(resolver, identifier):
    """任意の入力でresolveがクラッシュしない"""
    result = resolver.resolve_auto(identifier)
    assert result is None or isinstance(result, int)
```

## 品質自動化

### pre-commit

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff format
        entry: uv run ruff format
        language: system
        types: [python]

      - id: ruff-lint
        name: ruff lint
        entry: uv run ruff check --fix
        language: system
        types: [python]

      - id: pyright
        name: pyright
        entry: uv run pyright
        language: system
        types: [python]
```

### CI/CD (GitHub Actions)

```yaml
name: CI

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --all-extras
      - run: make check-all
```

## 開発コマンド

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
```

## チェックリスト

### 実装前

- [ ] PRDで要件を確認した
- [ ] 機能設計書でインターフェースを確認した
- [ ] テストを先に書いた（TDD）

### 実装後

- [ ] 型ヒントを全ての関数/メソッドに付けた
- [ ] Docstringを公開APIに書いた
- [ ] ロギングを追加した
- [ ] `make check-all` が通る
- [ ] テストカバレッジ80%以上
