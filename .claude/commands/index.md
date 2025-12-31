# SuperClaude コマンドリファレンス

このディレクトリには、Pythonプロジェクト開発を効率化するためのカスタムスラッシュコマンドが定義されています。

## コマンドカテゴリ

### 開発ワークフロー
- `/initialize-project` - テンプレートリポジトリの初期化（初回のみ）
- `/kickoff` - 新アイデアから開発を開始（PRD・設計ドキュメント作成）
- `/add-feature` - 新機能を既存パターンに従って完全自動実装

### 分析・改善
- `/analyze` - 多次元コード分析（品質、セキュリティ、パフォーマンス）
- `/improve` - エビデンスベースの改善提案と実装
- `/scan` - セキュリティと品質の包括的検証

### 品質・リファクタリング
- `/ensure-quality` - コード品質の自動改善（make check-all成功まで）
- `/safe-refactor` - テストカバレッジを維持した安全なリファクタリング
- `/write-tests` - t-wada流TDDによるテスト作成

### 開発・デバッグ
- `/troubleshoot` - 体系的なデバッグとトラブルシューティング
- `/task` - 複雑なタスクの管理とトラッキング

### ドキュメント・Git
- `/review-docs` - ドキュメントの詳細レビュー（サブエージェント実行）
- `/commit-and-pr` - 変更のコミットとPR作成

## コマンド選択ガイド

### 何をしたいか → どのコマンドを使うか

#### 品質関連
| やりたいこと | コマンド | 役割 |
|-------------|---------|------|
| エラーを自動修正したい | `/ensure-quality` | make check-all相当の自動修正 |
| 品質スコアを確認したい | `/scan --validate` | 検証・スコアリング専用 |
| コードを分析したい | `/analyze` | 分析レポート出力専用 |
| 改善を実装したい | `/improve` | エビデンスベース改善実装 |

#### 開発フロー
| やりたいこと | コマンド |
|-------------|---------|
| 新規開発を始めたい | `/kickoff` |
| 機能を追加したい | `/add-feature` |
| テストを書きたい | `/write-tests` |
| リファクタリングしたい | `/safe-refactor` |
| 問題を解決したい | `/troubleshoot` |

## 基本的な使用方法

```bash
# コード品質の分析
/analyze --code

# パフォーマンスの改善
/improve --perf --iterate

# セキュリティスキャン
/scan --security --owasp

# タスクの作成と管理
/task:create "新機能の実装"
```

## 既存ツールとの連携

これらのコマンドは、プロジェクトの既存ツールと連携して動作します：

- `make format/lint/typecheck` - コード品質チェック
- `make test` - テスト実行
- `make security/audit` - セキュリティ検証
- `uv` - パッケージ管理
- `gh` - GitHub操作

## 効率的なワークフロー

### 新機能開発
```bash
/task:create "機能名" → /analyze → 実装 → /improve → /scan --validate → make test
```

### バグ修正
```bash
/troubleshoot --fix → /analyze --code → 修正 → make test → /scan --validate
```

### パフォーマンス最適化
```bash
/analyze --perf → /improve --perf --iterate → make benchmark → /scan --validate
```

## 記号体系

効率的なコミュニケーションのための記号：

- `→` : 処理の流れ
- `|` : 選択・区切り
- `&` : 結合・並列
- `:` : 定義
- `»` : シーケンス
- `@` : 場所・参照
