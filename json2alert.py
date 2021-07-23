#!/usr/bin/env python3

# json2alert.py (ver.20210723)
# Usage: cat BOOK.json | $0 [図書館名]

import json
import datetime
import sys

hour_deadline = 24 # 期限日00:00のN時間前から発動させるか

def main(pretext):
	data_json = json.loads(sys.stdin.read())
	d_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
	counter_b = 0
	counter_r = 0
	text_b = ''
	text_r = ''
	# 借りている資料のチェック
	if 'borrowing' in data_json:
		if data_json['borrowing']['status'] == 'success':
			for i in range(len(data_json['borrowing']['items'])):
				item = data_json['borrowing']['items'][i]
				d_end = datetime.datetime.fromisoformat(item['date_return'])
				s_diff = (d_end - d_now).total_seconds()
				if s_diff < (60*60) * hour_deadline:
					counter_b = counter_b + 1
					text_b = text_b + ('%d冊目、『%s』。' % (counter_b, item['name']))
			if counter_b > 0:
				text_b = ('%s次の本、%d冊が返却期限です！ ' % (pretext, counter_b)) + text_b
	# 予約している資料のチェック
	if 'reservation' in data_json:
		if data_json['reservation']['status'] == 'success':
			for i in range(len(data_json['reservation']['items'])):
				item = data_json['reservation']['items'][i]
				if item['ready'] == True:
					counter_r = counter_r + 1
					text_r = text_r + ('%d冊目、『%s』。' % (counter_r, item['name']))
			if counter_r > 0:
				text_r = ('%s次の予約本、%d冊が取り置き中です！ ' % (pretext, counter_r)) + text_r
	return(counter_b + counter_r, text_b + text_r)

if __name__ == '__main__':
	args = sys.argv
	pretext = ''
	if len(args) > 1:
		pretext = args[1]
	(counter, text) = main(pretext)
	if counter > 0:
		print(text + '以上です。')
