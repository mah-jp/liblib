#!/usr/bin/env python3

# json2message.py (Ver.20240519)
# Usage: cat hoge.json | $0 [PREFIX]

import json
import datetime
import sys

hour_deadline: int = 48 # 期限日00:00のN時間前からメッセージを出力するか

def main(pretext: str = '') -> tuple[int, str]:
	data_json: dict = json.loads(sys.stdin.read())
	d_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
	counter_b: int = 0
	counter_r: int = 0
	text_b: str = ''
	text_r: str = ''
	# 借りている資料のチェック
	if 'borrowing' in data_json:
		if data_json['borrowing']['status'] == True:
			for i in range(len(data_json['borrowing']['items'])):
				item: dict = data_json['borrowing']['items'][i]
				d_end = datetime.datetime.fromisoformat(item['date_return'])
				s_diff: int = (d_end - d_now).total_seconds() # 期限までの秒数
				if s_diff < (60*60) * hour_deadline:
					counter_b = counter_b + 1
					d_diff: int = (s_diff - 1) // (60*60*24) # 期限までの日数 (本日=-1)
					if d_diff <= -2:
						text_d = 'が期限切れ'
					elif d_diff == -1:
						text_d = 'が本日'
					elif d_diff == 0:
						text_d = 'が明日'
					elif d_diff == 1:
						text_d = 'が明後日'
					else:
						text_d = ''
					text_b = text_b + ('%d冊目、『%s』%s。' % (counter_b, item['name'], text_d))
					# text_b = text_b + ('%d冊目、『%s』%s。' % (counter_b, item['name_short'], text_d))
			if counter_b > 0:
				text_b = ('%s次の本、%d冊が返却期限です！ ' % (pretext, counter_b)) + text_b
	# 予約している資料のチェック
	if 'reservation' in data_json:
		if data_json['reservation']['status'] == True:
			for i in range(len(data_json['reservation']['items'])):
				item: dict = data_json['reservation']['items'][i]
				if item['ready'] == True:
					counter_r = counter_r + 1
					text_r = text_r + ('%d冊目、『%s』。' % (counter_r, item['name']))
					# text_r = text_r + ('%d冊目、『%s』。' % (counter_r, item['name_short']))
			if counter_r > 0:
				text_r = ('%s次の予約本、%d冊が取り置き中です！ ' % (pretext, counter_r)) + text_r
	return(counter_b + counter_r, text_b + text_r)

if __name__ == '__main__':
	args: list = sys.argv
	pretext: str = ''
	counter: int = 0
	text: str = ''
	if len(args) > 1:
		pretext = args[1]
	(counter, text) = main(pretext)
	if counter > 0:
		print(text + '以上です。')
