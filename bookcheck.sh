#!/usr/bin/env -S bash

set -exuo pipefail

# bookcheck.sh (ver.20240519)
# Usage: FILE_ENV=sample.env $0 [--build]

PATH_ME=$(cd $(dirname $0); pwd)
TMP_FILE=$(mktemp)
function func_atexit() {
	[[ -n ${TMP_FILE-} ]] && rm -f "${TMP_FILE}"
}
trap func_atexit EXIT
trap 'rc=$?; trap - EXIT; func_atexit; exit $?' INT PIPE TERM

# 変数FILE_ENV (docker composeで用いる) が未定義または存在しないときエラー終了
if [ -z ${FILE_ENV-} ]; then
	echo 'ERROR: FILE_ENV が定義されていません。'
	exit 1
elif [ ! -f "${PATH_ME}/env/${FILE_ENV}" ]; then
	echo "ERROR: ${FILE_ENV} が見つかりません。"
	exit 1
else
	# FILE_ENVを表示する
	echo "FILE_ENV: ${FILE_ENV}"
fi

# 本体をdocker containerとして起動 (第一引数が存在して、かつ'--build'の場合はbuildしてから)
if [ $# -eq 1 ] && [ $1 = '--build' ]; then
	docker compose up --build
else
	docker compose up
fi
