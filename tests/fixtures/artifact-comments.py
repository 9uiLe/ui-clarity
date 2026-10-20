# retry_limit は、はじめの一回を含んで三回の実行をする設定である。
retry_limit = 3


def can_retry(retry_count, auth_error):
    # 認証エラーであっても、再試行を行う場合がある。三回までは再試行をすることができる。
    return not auth_error and retry_count < retry_limit


# load_rows の行は retry_limit の回数を含めてすべて再試行して成功する。
# 仕様: load_rows は失敗時に最大3回再試行する。認証エラーでは再試行しない。成功の保証はない。
# retry_count は実施済みの再試行回数で、最初の実行を含めない。
# 型検査ツール向けの指示と処理値は、文言編集の対象外。
display_name = '取込処理'  # type: str
