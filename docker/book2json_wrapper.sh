#!/usr/bin/env -S bash

# book2json_wrapper.sh (Ver.20260331)

set -euo pipefail

# --- Constants & Path Definitions ---
readonly DIR_ME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DIR_OUTPUT="${DIR_ME}/output/"
readonly CMD_JSON2MESSAGE="${DIR_ME}/json2message.py"

# --- Helper Functions ---

# タイムスタンプ付きログ出力
log() {
	local level=$1
	shift
	echo "[$(date +'%Y-%m-%d %H:%M:%S')] [${level}] $*" >&2
}

# ファイル準備（バックアップ & 権限設定付き作成）
prepare_file() {
	local file_target=$1
	if [[ -e "${file_target}" ]]; then
		mv "${file_target}" "${file_target}.bak"
	fi
	# 600 (rw-------) で空ファイルを作成
	install -m 600 /dev/null "${file_target}"
}

# 抽出・変換処理のメインロジック
run_extraction() {
	local flag=$1
	local username=$2
	local password=$3
	local cmd_extractor=$4
	local file_json=$5
	local file_txt=$6
	local prefix_txt=$7

	# フラグが 1 でなければスキップ
	if [[ "${flag}" -ne 1 ]]; then
		log "INFO" "Skipping: ${prefix_txt} (Flag is 0)"
		return 0
	fi

	log "INFO" "Starting extraction for: ${prefix_txt}"
		
	# 出力ファイルの準備
	prepare_file "${DIR_OUTPUT}/${file_json}"
	prepare_file "${DIR_OUTPUT}/${file_txt}"

	log "INFO" "Exec: ${cmd_extractor}"
		
	# パスワード漏洩防止のため xtrace (set -x) を一時的に無効化
	{ set +x; } 2>/dev/null
		
	# 環境変数を渡して実行
	LIBLIB_USERNAME="${username}" \
	LIBLIB_PASSWORD="${password}" \
	"${cmd_extractor}" > "${DIR_OUTPUT}/${file_json}"
		
	# デバッグモードなら xtrace を復帰（必要に応じて）
	if [[ "${LOGGING_DEBUG:-0}" -eq 1 ]]; then set -x; fi

	# JSON -> Message 変換
	# cat を使わずリダイレクト入力 (<) を使用
	"${CMD_JSON2MESSAGE}" "${prefix_txt}" < "${DIR_OUTPUT}/${file_json}" > "${DIR_OUTPUT}/${file_txt}"
		
	log "INFO" "Completed: ${prefix_txt}"
}

# --- Main Execution ---

# 環境変数ファイルの読み込みチェック
if [[ -z "${FILE_ENV-}" ]]; then
	log "ERROR" "FILE_ENV is not defined."
	exit 1
fi

log "INFO" "Loading environment: ${DIR_ME}/env/${FILE_ENV}"

# 環境変数読み込み中もパスワード保護のため xtrace オフ
{ set +x; } 2>/dev/null
source "${DIR_ME}/env/${FILE_ENV}"
if [[ "${LOGGING_DEBUG:-0}" -eq 1 ]]; then set -x; fi

# デフォルト値の設定 (Modern Bash Idiom)
: "${FLAG_OPAC:=0}"
: "${OPAC_USERNAME:=}"
: "${OPAC_PASSWORD:=}"
: "${FILE_JSON_OPAC:=opac.json}"
: "${FILE_TXT_OPAC:=opac.txt}"
: "${PREFIX_TXT_OPAC:=神戸市立図書館の}"

: "${FLAG_DLIBRARY:=0}"
: "${DLIBRARY_USERNAME:=}"
: "${DLIBRARY_PASSWORD:=}"
: "${FILE_JSON_DLIBRARY:=d-library.json}"
: "${FILE_TXT_DLIBRARY:=d-library.txt}"
: "${PREFIX_TXT_DLIBRARY:=神戸市電子図書館の}"

export LOGGING_DEBUG="${LOGGING_DEBUG:-0}"

# --- Process: OPAC ---
run_extraction \
	"${FLAG_OPAC}" \
	"${OPAC_USERNAME}" \
	"${OPAC_PASSWORD}" \
	"${DIR_ME}/book2json_opac.py" \
	"${FILE_JSON_OPAC}" \
	"${FILE_TXT_OPAC}" \
	"${PREFIX_TXT_OPAC}"

# --- Process: DLIBRARY ---
run_extraction \
	"${FLAG_DLIBRARY}" \
	"${DLIBRARY_USERNAME}" \
	"${DLIBRARY_PASSWORD}" \
	"${DIR_ME}/book2json_d-library.py" \
	"${FILE_JSON_DLIBRARY}" \
	"${FILE_TXT_DLIBRARY}" \
	"${PREFIX_TXT_DLIBRARY}"
