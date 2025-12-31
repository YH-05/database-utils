---
description: 新アイデアから開発を開始: PRD・設計ドキュメントを作成/更新する
---

# 新アイデアからの開発キックオフ

このコマンドは、`docs/ideas/` にストックされた新しいアイデアから開発を開始します。
PRD・設計ドキュメントを作成/更新し、実装準備を整えます。

**繰り返し実行可能**: 新しいアイデアがストックされるたびに実行してください。

## 実行方法

```bash
claude
> /kickoff
```

## `/initialize-project` との違い

| コマンド              | 目的                           | 実行頻度       |
| --------------------- | ------------------------------ | -------------- |
| `/initialize-project` | テンプレートリポジトリの初期化 | **1回のみ**    |
| `/kickoff`            | 新アイデアから開発サイクル開始 | **繰り返し可** |

## 実行前の確認

`docs/ideas/` ディレクトリ内のファイルを確認します。

```bash
# 確認
ls docs/ideas/

# ファイルが存在する場合
-> docs/ideas/ にアイデアファイルが見つかりました
   この内容を元にPRDを作成/更新します

# ファイルが存在しない場合
-> docs/ideas/ にファイルがありません
   対話形式でPRDを作成します
```

## 開発サイクルフロー

```
docs/ideas/ にアイデアをストック
        |
        v
    /kickoff 実行
        |
        v
  PRD作成/更新 --> ユーザー承認（必須）
        |
        v
  設計ドキュメント作成/更新（自動）
        |
        v
  /add-feature で実装開始
```

## 手順

### ステップ 0: インプットの読み込み

1. `docs/ideas/` 内のマークダウンファイルを全て読む
2. 内容を理解し、PRD 作成/更新の参考にする

### ステップ 1: プロダクト要求定義書の作成/更新

1. **prd-writing スキル**をロード
2. `docs/ideas/`の内容を元に`docs/product-requirements.md`を作成/更新
3. アイデアを具体化：
    - 詳細なユーザーストーリー
    - 受け入れ条件
    - 非機能要件
    - 成功指標
4. ユーザーに確認を求め、**承認されるまで待機**

**重要: PRDの承認なしに次のステップには進まない**

### ステップ 2: 機能設計書の作成/更新

1. **functional-design スキル**をロード
2. `docs/product-requirements.md`を読む
3. スキルのテンプレートとガイドに従って`docs/functional-design.md`を作成/更新

### ステップ 3: アーキテクチャ設計書の作成/更新

1. **architecture-design スキル**をロード
2. 既存のドキュメントを読む
3. スキルのテンプレートとガイドに従って`docs/architecture.md`を作成/更新

### ステップ 4: リポジトリ構造定義書の作成/更新

1. **repository-structure スキル**をロード
2. 既存のドキュメントを読む
3. スキルのテンプレートに従って`docs/repository-structure.md`を作成/更新

### ステップ 5: 開発ガイドラインの作成/更新

1. **development-guidelines スキル**をロード
2. 既存のドキュメントを読む
3. スキルのテンプレートに従って`docs/development-guidelines.md`を作成/更新

### ステップ 6: 用語集の作成/更新

1. **glossary-creation スキル**をロード
2. 既存のドキュメントを読む
3. スキルのテンプレートに従って`docs/glossary.md`を作成/更新

## 完了条件

- PRD がユーザーに承認されていること
- 6 つの永続ドキュメントが全て作成/更新されていること

完了時のメッセージ:

```
「開発キックオフが完了しました!

作成/更新したドキュメント:
- docs/product-requirements.md
- docs/functional-design.md
- docs/architecture.md
- docs/repository-structure.md
- docs/development-guidelines.md
- docs/glossary.md

次のステップ:
- /add-feature [機能名] で実装を開始してください
  例: /add-feature ユーザー認証

- ドキュメントの編集が必要な場合は会話で依頼してください
  例: 「PRDに新機能を追加して」「architecture.mdを見直して」
」
```
