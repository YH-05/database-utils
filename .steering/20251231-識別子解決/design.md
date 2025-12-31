# 識別子解決 - 設計書

## アーキテクチャ

```
┌─────────────────────────────────────┐
│   IdentifierResolver                │ ← 識別子解決の公開API
├─────────────────────────────────────┤
│   SecurityRepository                │ ← 銘柄CRUDとデータアクセス
├─────────────────────────────────────┤
│   DatabaseConnection                │ ← 既存の接続管理
└─────────────────────────────────────┘
```

## ファイル構成

```
src/database_utils/
├── core/
│   ├── identifier.py          # IdentifierResolver（新規）
│   └── repositories/
│       └── security.py        # SecurityRepository（新規）
├── exceptions.py              # カスタム例外（新規）
└── __init__.py                # 公開API更新
```

## クラス設計

### IdentifierResolver

```python
class IdentifierResolver:
    def __init__(self, db: DatabaseConnection) -> None: ...

    def resolve(
        self,
        identifier_value: str,
        identifier_type: IdentifierType,
        as_of: date | None = None,
    ) -> SecurityId | None:
        """識別子タイプを指定して解決"""

    def resolve_auto(
        self,
        identifier_value: str,
        as_of: date | None = None,
    ) -> SecurityId | None:
        """識別子タイプを自動検出して解決"""

    def resolve_or_create(
        self,
        identifier_value: str,
        identifier_type: IdentifierType,
        security_name: str,
        **kwargs,
    ) -> SecurityId:
        """解決できなければ新規作成"""

    def detect_identifier_type(
        self,
        identifier_value: str,
    ) -> IdentifierType | None:
        """識別子のパターンからタイプを検出"""
```

### SecurityRepository

```python
class SecurityRepository:
    def __init__(self, db: DatabaseConnection) -> None: ...

    def create(
        self,
        name: str,
        description: str | None = None,
        asset_class: str | None = None,
        currency: str | None = None,
    ) -> SecurityId:
        """銘柄を作成"""

    def get(self, security_id: SecurityId) -> SecurityDict | None:
        """銘柄を取得"""

    def get_by_identifier(
        self,
        identifier_type: IdentifierType,
        identifier_value: str,
        as_of: date | None = None,
    ) -> SecurityDict | None:
        """識別子で銘柄を取得"""

    def add_identifier(
        self,
        security_id: SecurityId,
        identifier_type: IdentifierType,
        identifier_value: str,
        is_primary: bool = False,
        valid_from: date | None = None,
        valid_to: date | None = None,
    ) -> None:
        """識別子を追加"""

    def get_identifiers(
        self,
        security_id: SecurityId,
    ) -> list[SecurityIdentifierDict]:
        """銘柄の全識別子を取得"""

    def search(
        self,
        name_pattern: str | None = None,
        identifier_value: str | None = None,
    ) -> list[SecurityDict]:
        """銘柄を検索"""
```

## 識別子パターン

| タイプ | パターン | 例 |
|--------|----------|-----|
| ISIN | `^[A-Z]{2}[A-Z0-9]{9}[0-9]$` | US0378331005 |
| CUSIP | `^[A-Z0-9]{9}$` | 037833100 |
| SEDOL | `^[A-Z0-9]{7}$` | 2046251 |
| JP_CODE | `^[0-9]{4}$` | 7203 |
| FIGI | `^[A-Z]{3}[A-Z0-9]{9}$` | BBG000B9XRY4 |

## SQL クエリ

### 識別子解決（ポイントインタイム）

```sql
SELECT security_id
FROM security_identifiers
WHERE identifier_type = ?
  AND identifier_value = ?
  AND (valid_from IS NULL OR valid_from <= ?)
  AND (valid_to IS NULL OR valid_to > ?)
ORDER BY valid_from DESC NULLS LAST
LIMIT 1
```

## テスト戦略

1. **ユニットテスト**: パターンマッチング、解決ロジック
2. **統合テスト**: DB操作を含む一連のフロー
3. **プロパティテスト**: 任意の識別子での解決サイクル
