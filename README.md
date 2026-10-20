# ui-clarity

AIが作成・編集する成果物に含まれる日本語を、1つのスキルで扱います。UI（HTML・アプリ・可視化）、ドキュメント、コードコメントの作成・レビュー・改善に使い、対話そのものは対象に含めません。

UIでは、所属・対象・状態・操作などの役割を区別し、文言と視覚的な構造で表し分けます。例えば「A画面 / Bコンポーネント: 成功」を、確認済みの所属関係と対象の状態として読み取れるようにします。文章やコンポーネントの数を減らすことだけを目的にはしません。

## UI Clarity を使う

実体は [`skills/ui-clarity/SKILL.md`](skills/ui-clarity/SKILL.md) です。リポジトリ内の `.agents/skills/ui-clarity` と `.claude/skills/ui-clarity` は、同じ実体への相対リンクです。過去の会話や別リポジトリへの参照は不要です。

このリポジトリを開いた新しいセッションで、次のように依頼します。

```text
Codex:       $ui-clarity この資料から、共有先を比較できる説明HTMLを作って
Claude Code: /ui-clarity この画面の文言と情報設計をレビューして。変更はしないで
```

`$ui-clarity このREADMEの日本語を改善して`、`/ui-clarity このコードコメントを実装と照合して改善して` のようにも使えます。成果物に合う基準を選び、コメント編集にUIの構造変更や画面検証を持ち込みません。

「表示文言だけを改善して」のように変更範囲も指定できます。スキルは依頼から必要な作業を選び、文言だけの依頼で構造や処理を変更しません。用語集、仕様、実データ、対象画面があれば依頼と一緒に渡してください。

別のプロジェクトで使う場合は `skills/ui-clarity/` を参照資料ごと配置し、利用するエージェントのスキル検索先からそのフォルダを参照させてください。配布物には特定のCLI、モデル、Moletta、外部サービスへの実行依存はありません。

## 検証

[`tests/README.md`](tests/README.md) に架空題材での再実行手順、[`tests/RESULTS.md`](tests/RESULTS.md) に実施結果と未確認事項を記録しています。

## GitHub での更新と CI

公開リポジトリの既定ブランチは `master` とし、所有者が直接pushします。PR・Issue・Wiki・Projectは使いません。第三者へ書き込み権限を付与しません。公開物の閲覧・複製・フォークは可能です。

[CI](.github/workflows/ci.yml) は `master` へのpushと手動実行で動きます。スキルの単一入口・参照先・配布範囲、検査処理の正常／異常系、ワークフローの権限と固定参照を検査し、Gitleaksで全取得履歴の秘密情報を検出します。GitHub製Actionだけを使い、ActionのコミットSHA、Python依存の版とハッシュ、検査バイナリの版とハッシュを固定しています。

CIはpush後の検出で、失敗したコミットを自動的には戻しません。GitHubのシークレット検出・push保護を併用します。UI生成時の意味保持や見た目の有効性は、CIの構造検査だけでは保証できないため、スキルの実質的な変更では架空題材での行動検証も行います。

## 開発支援

[Moletta](https://github.com/9uiLe/moletta) を開発支援に使用します。

### Moletta のローカル環境への導入

Python 3.11 以上が必要です。常設の Moletta checkout から、このプロジェクトへ5技能をまとめて導入します。

```sh
git clone --branch main https://github.com/9uiLe/moletta.git /path/to/moletta
python3 /path/to/moletta/scripts/install.py "$PWD"
```

`/path/to/moletta` は実際の保存先へ置き換え、このプロジェクトのルートで実行してください。既存の checkout があれば再利用できます。

Codex の `.agents/skills/` と Claude Code の `.claude/skills/` にリンクが作成されます。リンク先の checkout は同じ場所に維持し、別の worktree でも導入を実行してください。PC 固有のリンクは、導入された5項目だけを `.git/info/exclude` などで Git の管理対象から除外します。

導入後は新しいセッションで、Codex は `$moletta`、Claude Code は `/moletta` に続けて目的と必須条件を伝えます。
