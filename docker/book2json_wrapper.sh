#!/usr/bin/env -S bash

set -exuo pipefail

# book2json_wrapper.sh (Ver.20250309)

# 変数定義 (カスタマイズ部分)
DIR_ME=$(cd $(dirname $0) && pwd) # スクリプトが存在するディレクトリ
DIR_OUTPUT="${DIR_ME}/output/" # JSONの出力先ディレクトリ
CMD_OPAC="${DIR_ME}/book2json_opac.py"
CMD_DLIBRARY="${DIR_ME}/book2json_d-library.py"
CMD_JSON2MESSAGE="${DIR_ME}/json2message.py"
NAME_ME=$(basename $0)

# 変数定義 (環境変数ファイルの読み込み)
if [ -z ${FILE_ENV-} ]; then
	echo 'ERROR: FILE_ENV is not defined.'
	exit 1
fi
set +x
echo "source: ${DIR_ME}/env/${FILE_ENV}"
source "${DIR_ME}/env/${FILE_ENV}"
set -x

# 変数定義がされてないときのデフォルト値
FLAG_OPAC=${FLAG_OPAC:-0}
OPAC_USERNAME=${OPAC_USERNAME:-''}
set +x
OPAC_PASSWORD=${OPAC_PASSWORD:-''}
set -x
FILE_JSON_OPAC=${FILE_JSON_OPAC:-'opac.json'}
FILE_TXT_OPAC=${FILE_TXT_OPAC:-'opac.txt'}
PREFIX_TXT_OPAC=${PREFIX_TXT_OPAC:-'神戸市立図書館の'}
FLAG_DLIBRARY=${FLAG_DLIBRARY:-0}
DLIBRARY_USERNAME=${DLIBRARY_USERNAME:-''}
set +x
DLIBRARY_PASSWORD=${DLIBRARY_PASSWORD:-''}
set -x
FILE_JSON_DLIBRARY=${FILE_JSON_DLIBRARY:-'d-library.json'}
FILE_TXT_DLIBRARY=${FILE_TXT_DLIBRARY:-'d-library.txt'}
PREFIX_TXT_DLIBRARY=${PREFIX_TXT_DLIBRARY:-'神戸市電子図書館の'}
export LOGGING_DEBUG=${LOGGING_DEBUG:-0}

# FILE_TARGETが存在したら.bakにmvし、FILE_TARGETを600で新規作成する
function prepare_file () {
	local FILE_TARGET=$1
	if [ -e "${FILE_TARGET}" ]; then
		mv "${FILE_TARGET}" "${FILE_TARGET}.bak"
	fi
	touch "${FILE_TARGET}"
	chmod 600 "${FILE_TARGET}"
}

# 図書館ごとの処理をまとめた関数
function process_library() {
	local cmd=$1
	local username=$2
	local password=$3
	local file_json=$4
	local file_txt=$5
	local prefix_txt=$6

	prepare_file "${DIR_OUTPUT}/${file_json}"
	echo "exec: ${cmd}"
	set +x
	LIBLIB_USERNAME=${username} LIBLIB_PASSWORD=${password} \
	"${cmd}" > "${DIR_OUTPUT}/${file_json}"
	set -x
	prepare_file "${DIR_OUTPUT}/${file_txt}"
	cat "${DIR_OUTPUT}/${file_json}" | "${CMD_JSON2MESSAGE}" "${prefix_txt}" > "${DIR_OUTPUT}/${file_txt}"
}

# OPAC (神戸市立図書館)
if [ $FLAG_OPAC -eq 1 ]; then
	process_library "${CMD_OPAC}" "${OPAC_USERNAME}" "${OPAC_PASSWORD}" "${FILE_JSON_OPAC}" "${FILE_TXT_OPAC}" "${PREFIX_TXT_OPAC}"
fi

# DLIBRARY (神戸市電子図書館)
if [ $FLAG_DLIBRARY -eq 1 ]; then
	process_library "${CMD_DLIBRARY}" "${DLIBRARY_USERNAME}" "${DLIBRARY_PASSWORD}" "${FILE_JSON_DLIBRARY}" "${FILE_TXT_DLIBRARY}" "${PREFIX_TXT_DLIBRARY}"
fi
