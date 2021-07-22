#!/usr/bin/env python3

# json2alert.py (ver.20210722)
# Usage: cat BOOK.json | $0 [図書館名]

import json
import datetime
import sys

hour_deadline = 12 # 期限日00:00のN時間前から発動させるか

def main(facility):
	data_json = json.loads(sys.stdin.read())
	d_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
	counter_b = 0
	counter_r = 0
	text = ''
	if data_json['status'] == 'success':
		# 貸出チェック
		if 'borrowing' in data_json:
			data_borrowing = data_json['borrowing']
			for i in range(len(data_borrowing)):
				input = data_borrowing[i]
				d_end = datetime.datetime.fromisoformat(input['date_return'])
				s_diff = (d_end - d_now).total_seconds()
				if s_diff < (60*60) * hour_deadline:
					counter_b = counter_b + 1
					text = text + ('%d冊目、『%s』。' % (counter_b, input['name']))
			if counter_b > 0:
				text = ('%s次の本、%d冊が返却期限です！ ' % (facility, counter_b)) + text
		# 予約チェック
		if 'reservation' in data_json:
			data_reservation = data_json['reservation']
			for i in range(len(data_reservation)):
				input = data_reservation[i]
				if input['button_lend'] == True:
					counter_r = counter_r + 1
					text = text + ('%d冊目、『%s』。' % (counter_r, input['name']))
			if counter_r > 0:
				text = ('%s次の予約本、%d冊が貸出できます！ ' % (facility, counter_r)) + text
	return(counter_b + counter_r, text)

if __name__ == '__main__':
	args = sys.argv
	if len(args) > 1:
		facility = args[1] + 'の'
	else:
		facility = ''
	(counter, text) = main(facility)
	if counter > 0:
		print(text + '以上です。')
		sys.exit(0)
	else:
		sys.exit(0)
