# ui-clarity

AIが作成・編集する成果物に含まれる日本語を、1つのスキルで扱います。UI（HTML・アプリ・可視化）、ドキュメント、コードコメントの作成・レビュー・改善に使い、対話そのものは対象に含めません。

UIでは、所属・対象・状態・操作などの役割を区別し、文言と視覚的な構造で表し分けます。例えば「A画面 / Bコンポーネント: 成功」を、確認済みの所属関係と対象の状態として読み取れるようにします。文章やコンポーネントの数を減らすことだけを目的にはしません。

## 導入・更新（macOS・個人用）

Node.js 22.20以降・pnpm・Gitと、使う方のCodex／Claude Codeを導入しておきます。[Vercel Skills CLI](https://github.com/vercel-labs/skills)を[pnpm dlx](https://pnpm.io/cli/dlx)で取得・実行します。

**初回も更新も、ターミナルで次のコマンドを実行します。** どのフォルダからでも実行でき、このMacの全プロジェクトで使えます。

```sh
pnpm dlx skills add 9uiLe/ui-clarity \
  --skill ui-clarity \
  --global \
  --agent codex claude-code \
  --yes
```

`ui-clarity`だけをCodexとClaude Codeへ導入します。更新時も同じコマンドで、このスキルを指定した2ツールへ配置し直します。片方だけなら、`--agent codex claude-code`を`--agent codex`または`--agent claude-code`へ変更してください（[オプションの公式資料](https://github.com/vercel-labs/skills/blob/main/docs/commands.md#skills-add)）。

上の2ツール向けコマンドでは`~/.agents/skills/ui-clarity/`に実体を置き、Claude Codeの`~/.claude/skills/ui-clarity`からリンクします。同名の導入先は置き換えられます。導入済みファイルを自分で編集している場合は、実行前に別フォルダへ退避してください。以前のコピー手順で導入済みの場合も、上のコマンドでCLI管理へ切り替えられます。

完了後は、このリポジトリ以外のプロジェクトで新しいセッションを開き、スキル一覧から`ui-clarity`を選びます。見つからない場合はツールを再起動してください。同名のスキルが複数ある場合は、上記の個人用配置先から読み込まれたことを確認してください。

## UI Clarity を使う

```text
Codex:       $ui-clarity この資料から、共有先を比較できる説明HTMLを作って
Claude Code: /ui-clarity この画面の文言と情報設計をレビューして。変更はしないで
```

READMEやコードコメントの改善、表示文言だけの編集にも使えます。依頼には対象と変更範囲を指定し、用語集、仕様、実データ、対象画面があれば一緒に渡してください。

スキルの実体は [`skills/ui-clarity/SKILL.md`](skills/ui-clarity/SKILL.md) と参照資料です。このリポジトリ内の `.agents/skills/ui-clarity` と `.claude/skills/ui-clarity` は同じ実体への相対リンクで、このリポジトリ内での利用に使います。スキルの実行に追加のCLIや外部サービスは不要です。

## 検証

[`tests/README.md`](tests/README.md) に架空題材での再実行手順、[`tests/RESULTS.md`](tests/RESULTS.md) に実施結果と未確認事項を記録しています。

## 開発時のコミット検査

このリポジトリを編集する人は、Python 3が利用できる環境で、ルートから次を1回実行します。スキルを導入して使うだけなら設定は不要です。既存のhookや`core.hooksPath`を設定済みの場合は、既存の検査を維持するように統合してください。

```sh
git config --local core.hooksPath .githooks
```

[pre-commit hook](.githooks/pre-commit) は、変更をステージした通常ファイルについて、コミットされる版が5,000トークン（バイト数÷4、20,000バイト）を超えるとコミットを拒否します。lockfileと明示した生成物等は除外し、超過時にはファイルの分割と再ステージの方法を表示します。判定範囲・除外の指定は[テスト手順](tests/README.md#pre-commitのサイズ検査)を参照してください。hookの有効化はcloneごとに必要です（[Git公式資料](https://git-scm.com/docs/githooks)）。

## GitHub での更新と CI

公開リポジトリの既定ブランチは `master` とし、所有者が直接pushします。PR・Issue・Wiki・Projectは使いません。第三者へ書き込み権限を付与しません。公開物の閲覧・複製・フォークは可能です。

[CI](.github/workflows/ci.yml) は `master` へのpushと手動実行で動きます。スキルの単一入口・参照先・配布範囲、検査処理の正常／異常系、ワークフローの権限と固定参照を検査し、Gitleaksで全取得履歴の秘密情報を検出します。GitHub製Actionだけを使い、ActionのコミットSHA、Python依存の版とハッシュ、検査バイナリの版とハッシュを固定しています。

CIはpush後の検出で、失敗したコミットを自動的には戻しません。GitHubのシークレット検出・push保護を併用します。UI生成時の意味保持や見た目の有効性は、CIの構造検査だけでは保証できないため、スキルの実質的な変更では架空題材での行動検証も行います。
