#!/bin/bash

# Usage: $0

PATH_ME=$(dirname $(readlink -f $0)) # Linuxなど (macOSでは使えない方法)
CMD_LIBLIB="${PATH_ME}/book2json.py"
CMD_ALERT="${PATH_ME}/json2alert.py"
CMD_VOICE2GH="${PATH_ME}/../voice2googlehome/voice2gh.sh"

TMP_FILE=$(mktemp)
# 鉄板のtmpfile処理 https://fumiyas.github.io/2013/12/06/tempfile.sh-advent-calendar.html
function func_atexit() {
	[[ -n ${TMP_FILE-} ]] && rm -f "${TMP_FILE}"
}
trap func_atexit EXIT
trap 'rc=$?; trap - EXIT; func_atexit; exit $?' INT PIPE TERM

function func_main () {
	${CMD_LIBLIB} "$@" | jq . | tee >(${CMD_ALERT} > ${TMP_FILE})
	TMP_TEXT=`cat ${TMP_FILE}`
	if [ -s ${TMP_FILE} ]; then
		logger -t `basename "$0"` "${TMP_TEXT}"
		${CMD_VOICE2GH} "${TMP_TEXT}"
	fi
}

export LIBLIB_USERNAME='★★'
export LIBLIB_PASSWORD='☆☆'
func_main
