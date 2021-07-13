#!/usr/bin/env python3

# json2alert.py (ver.20210713)
# Usage: cat BOOK.json | $0

import json
import datetime
import sys

def main():
	data_json = json.loads(sys.stdin.read())
	d_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
	counter = 0
	text = ''
	for i in range(len(data_json)):
		input = data_json[i]
		if input['status'] == 'success':
			d_end = datetime.datetime.fromisoformat(input['返却期限日'])
			s_diff = (d_end - d_now).total_seconds()
			if s_diff < (60*60) * 12: # 期限日00:00の12時間前から発動
				counter = counter + 1
				text = text + ('%d冊目、『%s』。' % (counter, input['書名']))
	if counter > 0:
		text = ("図書館の次の本、%d冊が返却期限です！ " % counter) + text + "以上です。"
	return(counter, text)

(counter, text) = main()
if counter > 0:
	print(text)
	sys.exit(0)
else:
	sys.exit(0)
