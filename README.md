# ui-clarity

AIが作成・編集する成果物に含まれる日本語を、1つのスキルで扱います。UI（HTML・アプリ・可視化）、ドキュメント、コードコメントの作成・レビュー・改善に使い、対話そのものは対象に含めません。

UIでは、所属・対象・状態・操作などの役割を区別し、文言と視覚的な構造で表し分けます。例えば「A画面 / Bコンポーネント: 成功」を、確認済みの所属関係と対象の状態として読み取れるようにします。文章やコンポーネントの数を減らすことだけを目的にはしません。

## 導入する（macOS・個人用）

このMacの全プロジェクトで使い、必要なときに手動で更新する手順です。ターミナルを使います。Gitと、使う方のCodex／Claude Codeは導入・ログイン済みを前提にします。以下のコマンドは、作業中のプロジェクトとは別の場所へ取得・配置するため、どのフォルダからでも実行できます。

### 1. スキルを取得する

```sh
git --version
mkdir -p "$HOME/.local/share" &&
git clone --branch master --single-branch https://github.com/9uiLe/ui-clarity.git "$HOME/.local/share/ui-clarity"
```

取得先にすでにフォルダがある場合、`git clone` は停止します。この手順で取得済みなら、下の「更新する」へ進んでください。

### 2. 使うツールへコピーする

使う方のコマンドだけを実行します。両方で使う場合は、両方を実行してください。コピーするのは、スキル本文と参照資料を含む `skills/ui-clarity/` 一式です。取得元を更新しても、導入済みのコピーは変わりません。

| ツール | このMacの全プロジェクトに適用される配置先 |
| --- | --- |
| Codex | `~/.agents/skills/ui-clarity/`（[公式の配置先](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)） |
| Claude Code | `~/.claude/skills/ui-clarity/`（[公式の配置先](https://code.claude.com/docs/en/skills#choose-where-skills-load)） |

**Codex**

```sh
if [ -e "$HOME/.agents/skills/ui-clarity" ] || [ -L "$HOME/.agents/skills/ui-clarity" ]; then
  printf '%s\n' '導入先がすでにあります。下の「更新する」を確認してください。'
else
  mkdir -p "$HOME/.agents/skills" &&
  cp -R "$HOME/.local/share/ui-clarity/skills/ui-clarity" "$HOME/.agents/skills/ui-clarity"
fi
```

**Claude Code**

```sh
if [ -e "$HOME/.claude/skills/ui-clarity" ] || [ -L "$HOME/.claude/skills/ui-clarity" ]; then
  printf '%s\n' '導入先がすでにあります。下の「更新する」を確認してください。'
else
  mkdir -p "$HOME/.claude/skills" &&
  cp -R "$HOME/.local/share/ui-clarity/skills/ui-clarity" "$HOME/.claude/skills/ui-clarity"
fi
```

### 3. 導入を確認する

まず、導入した方のファイルをターミナルで確認します。

- Codex：`ls "$HOME/.agents/skills/ui-clarity"` と `ls "$HOME/.agents/skills/ui-clarity/references"`
- Claude Code：`ls "$HOME/.claude/skills/ui-clarity"` と `ls "$HOME/.claude/skills/ui-clarity/references"`

最初の一覧に `SKILL.md` と `references`、参照資料の一覧に `information-design.md`・`japanese-and-semantics.md`・`verification.md` があれば、ファイルの配置は完了です。

続いて、このリポジトリ以外のプロジェクトで新しいセッションを開き、スキル一覧に `ui-clarity` があることを確認してください。このリポジトリには元からプロジェクト用の入口があるため、個人用の導入確認には別のプロジェクトを使います。

デスクトップ版は、[公式資料](https://learn.chatgpt.com/docs/build-skills)が案内するChatGPTデスクトップアプリのサイドバー「Skills」で一覧を確認し、入力欄の `@` から選択します。Codex CLI／IDE拡張では `$` または `/skills` から選べます。

Codex CLI／IDE拡張では次の依頼を使えます。アプリではスキルを選んだ後に、`$ui-clarity` を除いた依頼本文を入力します。実行前のボタンが操作を表す文言になるかを試せます。

```text
$ui-clarity 「保存しました」というボタン文言をレビューして。クリックすると入力内容を保存する処理が実行されます。ファイルは変更しないで。
```

Claude Codeでは、次のように依頼します。

```text
/ui-clarity 「保存しました」というボタン文言をレビューして。クリックすると入力内容を保存する処理が実行されます。ファイルは変更しないで。
```

見つからない場合は、`ui-clarity/ui-clarity/SKILL.md` のようにフォルダが二重になっていないか、配置先と参照資料を確認し、ツールを再起動してください。同名のスキルを他にも導入している場合、Codexでは複数表示されることがあり、Claude Codeでは個人用がプロジェクト用より優先されます。読み込まれたパスも確認してください（[Codexの仕様](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)、[Claude Codeの仕様](https://code.claude.com/docs/en/skills#resolve-skills-that-share-a-name)）。

## 更新する

まず、取得元を更新して版を確認します。この時点では導入済みのコピーは変わりません。

```sh
git -C "$HOME/.local/share/ui-clarity" pull --ff-only &&
git -C "$HOME/.local/share/ui-clarity" rev-parse --short HEAD
```

次に、更新するツールの**どちらか1行**を実行します。

Codexの場合：

```sh
UI_CLARITY_TARGET="$HOME/.agents/skills/ui-clarity"
```

Claude Codeの場合：

```sh
UI_CLARITY_TARGET="$HOME/.claude/skills/ui-clarity"
```

同じターミナルで次を実行します。新版をコピーできた後に、旧版をスキルの検索先とは別の場所へ退避して入れ替えます。両方のツールを更新する場合は、対象の1行を切り替えて、この処理を繰り返してください。

```sh
if [ -d "$UI_CLARITY_TARGET" ] && [ ! -L "$UI_CLARITY_TARGET" ]; then
  mkdir -p "$HOME/.local/share/ui-clarity-backups" &&
  UI_CLARITY_BACKUP="$(mktemp -d "$HOME/.local/share/ui-clarity-backups/update.XXXXXX")" &&
  cp -R "$HOME/.local/share/ui-clarity/skills/ui-clarity" "$UI_CLARITY_BACKUP/new" &&
  mv "$UI_CLARITY_TARGET" "$UI_CLARITY_BACKUP/previous" &&
  mv "$UI_CLARITY_BACKUP/new" "$UI_CLARITY_TARGET" &&
  printf '更新しました。旧版の保存先: %s/previous\n' "$UI_CLARITY_BACKUP"
else
  printf '%s\n' '通常の導入先フォルダが見つかりません。対象の設定と初回導入手順を確認してください。リンクで導入済みの場合は、リンク先を確認してください。'
fi
```

更新後は、新しいセッションで「導入を確認する」をもう一度行います。

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
