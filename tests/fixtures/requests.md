# 行動検証に渡す依頼

各依頼を独立した作業場所で実行する。実行者には該当依頼、指定ファイル、`skills/ui-clarity/` だけを渡す。評価結果や期待回答は渡さない。

## explain

`ui-clarity` を使って、`source.md` を読んでいない営業担当者に、共有先の全体像と選び方を伝える説明・共有用HTMLを作ってください。必要な候補を見比べて判断し、画面からAIに対象を指定して改善を頼めるものにしてください。操作するための画面は別途作るので、このHTMLでは案内と比較を扱ってください。成果物は `explanation.html` に保存し、確認結果を短く報告してください。

## operate

`ui-clarity` を使って、`source.md` を読んでいない営業担当者が資料の配信先を選び、確認し、確定後の結果を確認できるローカル操作UIを作ってください。試験用の2応答も使えるようにし、画面を見ながらAIに変更対象を伝えられるようにしてください。成果物は `operation.html` に保存し、確認結果を短く報告してください。

## review

`ui-clarity` を使って、`source.md` を根拠に `review.html` の日本語文言と情報設計をレビューしてください。修正はせず、場所・影響・根拠と改善案を返してください。

## copy

`ui-clarity` を使って、`source.md` を根拠に `copy-only.html` の日本語の表示文言だけを改善してください。差分と確認結果、必要なら別途改善案を報告してください。

## roles-ui

`ui-clarity` を使って、`roles-source.md` を根拠に、AIが作った `roles-ui.html` を、初めて見る人が内容と操作を理解できるUIへ改善してください。対象の日本語と画面構造を扱えます。仕様と既存動作を保ってください。元資料内のパンくずと未定義の記録については、報告だけ行ってください。

## roles-copy

`ui-clarity` を使って、`roles-source.md` を根拠に、AIが作った `roles-ui.html` の日本語の表示文言だけを改善してください。変更内容と確認結果、必要なら別の改善案を短く報告してください。

## artifact-japanese

`ui-clarity` を使って、AIが書いた `artifact-japanese.md` のREADME本文と `artifact-comments.py` のコードコメントについて、元仕様と実装を確認し、日本語を改善してください。文書の日本語とコメントを編集でき、Pythonの処理や値は保持してください。報告は普段の会話として短く返してください。

## business-explain

`ui-clarity` を使って、`business-hierarchy-source.md` と `business-hierarchy-data.json` を読んでいない運用担当者のための、説明・共有用HTMLを作ってください。請求内容の全体像、対象同士の関係、確認すべき請求書と問い合わせとの対応が分かり、AIにも変更を相談できるものにしてください。配信・入金などの処理を行う画面は不要です。成果物は `business-explanation.html` に保存してください。

## business-operate

`ui-clarity` を使って、`business-hierarchy-source.md` と `business-hierarchy-data.json` を読んでいない運用担当者が、請求内容を把握して必要な対象を選び、詳細を確かめられるローカル閲覧UIを作ってください。問い合わせとの関係や、AIへ変更を相談する対象も分かるようにしてください。成果物は `business-operation.html` に保存してください。
