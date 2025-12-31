# 識別子解決 - タスクリスト

## 実装タスク

- [x] カスタム例外クラスの作成 (`exceptions.py`)
- [x] SecurityRepository のテスト作成 (`test_security_repository.py`)
- [x] SecurityRepository の実装 (`repositories/security.py`)
- [x] IdentifierResolver のテスト作成 (`test_identifier.py`)
- [x] IdentifierResolver の実装 (`identifier.py`)
- [x] 公開APIの更新 (`__init__.py`)
- [x] 統合テストの作成 (`tests/integration/test_identifier_flow.py`)
- [x] make check-all で最終検証

---

## 振り返り

### 実装完了日
2025-12-31

### 計画と実績の差分

| 項目 | 計画 | 実績 |
| --- | --- | --- |
| テスト数 | 未定 | 41テスト（単体34 + 統合7） |
| ファイル数 | 4ファイル | 5ファイル（repositoriesディレクトリ追加） |
| 識別子タイプ | 7種類 | 7種類（ISIN, CUSIP, SEDOL, FIGI, JP_CODE, TICKER_YAHOO, TICKER_BBG） |

### 発見した問題と解決策

1. **FIGI/ISIN パターン衝突**
   - 問題: 両方12文字でISINパターンがFIGIにマッチ
   - 解決: FIGIパターンを `^BBG[A-Z0-9]{9}$` に変更し、検出順序でFIGIを先に配置

2. **DatabaseConnection.connection プロパティ追加**
   - 問題: スキーマ初期化テストで内部`_conn`にアクセス
   - 解決: 公開`connection`プロパティを追加

### 学んだこと

- TDDによる段階的実装が複雑な識別子ロジックの検証に効果的
- パターンマッチングは順序依存性があり、より具体的なパターンを先に評価すべき
- structlogによる構造化ログでデバッグが容易になった

### 次回への改善提案

- パターン検出の優先度を明示的に定義する仕組み（priority属性など）
- 識別子タイプの動的追加対応（DBから読み込み）
- バッチ解決APIの追加（複数識別子の一括解決）
