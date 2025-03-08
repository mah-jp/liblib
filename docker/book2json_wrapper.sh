#!/usr/bin/env -S bash

set -exuo pipefail

# book2json_wrapper.sh (Ver.20240519)

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
OPAC_PASSWORD=${OPAC_PASSWORD:-''}
FILE_JSON_OPAC=${FILE_JSON_OPAC:-'opac.json'}
FILE_TXT_OPAC=${FILE_TXT_OPAC:-'opac.txt'}
PREFIX_TXT_OPAC=${PREFIX_TXT_OPAC:-'神戸市立図書館の'}
FLAG_DLIBRARY=${FLAG_DLIBRARY:-0}
DLIBRARY_USERNAME=${DLIBRARY_USERNAME:-''}
DLIBRARY_PASSWORD=${DLIBRARY_PASSWORD:-''}
FILE_JSON_DLIBRARY=${FILE_JSON_DLIBRARY:-'d-library.json'}
FILE_TXT_DLIBRARY=${FILE_TXT_DLIBRARY:-'d-library.txt'}
PREFIX_TXT_DLIBRARY=${PREFIX_TXT_DLIBRARY:-'神戸市電子図書館の'}
export LOGGING_DEBUG=${LOGGING_DEBUG:-0}

# FILE_TARGETが存在したら.bakにmvし、FILE_TARGETを600で新規作成する
function prepare_file () {
	FILE_TARGET=$1
	if [ -e "${FILE_TARGET}" ]; then
		mv "${FILE_TARGET}" "${FILE_TARGET}.bak"
	fi
	install -m 600 /dev/null "${FILE_TARGET}"
}

# OPAC (神戸市立図書館)
if [ $FLAG_OPAC -eq 1 ]; then
	prepare_file "${DIR_OUTPUT}/${FILE_JSON_OPAC}"
	echo "exec: ${CMD_OPAC}"
	set +x
	LIBLIB_USERNAME=${OPAC_USERNAME} \
	LIBLIB_PASSWORD=${OPAC_PASSWORD} \
	"${CMD_OPAC}" > "${DIR_OUTPUT}/${FILE_JSON_OPAC}"
	set -x
	prepare_file "${DIR_OUTPUT}/${FILE_TXT_OPAC}"
	cat "${DIR_OUTPUT}/${FILE_JSON_OPAC}" | "${CMD_JSON2MESSAGE}" "${PREFIX_TXT_OPAC}" > "${DIR_OUTPUT}/${FILE_TXT_OPAC}"
fi

# DLIBRARY (神戸市電子図書館)
if [ $FLAG_DLIBRARY -eq 1 ]; then
	prepare_file "${DIR_OUTPUT}/${FILE_JSON_DLIBRARY}"
	echo "exec: ${CMD_DLIBRARY}"
	set +x
	LIBLIB_USERNAME=${DLIBRARY_USERNAME} \
	LIBLIB_PASSWORD=${DLIBRARY_PASSWORD} \
	"${CMD_DLIBRARY}" > "${DIR_OUTPUT}/${FILE_JSON_DLIBRARY}"
	set -x
	prepare_file "${DIR_OUTPUT}/${FILE_TXT_DLIBRARY}"
	cat "${DIR_OUTPUT}/${FILE_JSON_DLIBRARY}" | "${CMD_JSON2MESSAGE}" "${PREFIX_TXT_DLIBRARY}" > "${DIR_OUTPUT}/${FILE_TXT_DLIBRARY}"
fi
