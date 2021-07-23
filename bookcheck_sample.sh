#!/bin/bash

# bookcheck_sample.sh (ver.20210718)
# Usage: $0

PATH_ME=$(dirname $(readlink -f $0)) # Linuxなど (macOSでは使えない方法)
CMD_BOOK_1="${PATH_ME}/book2json_opac.py"
CMD_BOOK_2="${PATH_ME}/book2json_d-library.py"
CMD_ALERT="${PATH_ME}/json2alert.py"
CMD_VOICE2GH="${PATH_ME}/../voice2googlehome/voice2gh.sh"
TIME_WAIT=5

TMP_FILE=$(mktemp)
function func_atexit() {
	[[ -n ${TMP_FILE-} ]] && rm -f "${TMP_FILE}"
}
trap func_atexit EXIT
trap 'rc=$?; trap - EXIT; func_atexit; exit $?' INT PIPE TERM

function func_main () {
	$1 | jq . | tee >(${CMD_ALERT} $2 > ${TMP_FILE})
	TMP_TEXT=`cat ${TMP_FILE}`
	if [ -s ${TMP_FILE} ]; then
		logger -t `basename "$0"` "${TMP_TEXT}"
		${CMD_VOICE2GH} "${TMP_TEXT}"
	fi
}

# sample1
export LIBLIB_USERNAME='★★'
export LIBLIB_PASSWORD='☆☆'
func_main ${CMD_BOOK_1} '神戸花子さんの神戸市立図書館での'
sleep ${TIME_WAIT}

# sample2
export LIBLIB_USERNAME='★★'
export LIBLIB_PASSWORD='▲▲'
func_main ${CMD_BOOK_2} '神戸花子さんの神戸市電子図書館での'
