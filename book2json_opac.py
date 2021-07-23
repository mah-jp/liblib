#!/usr/bin/env python3

# book2json_opac.py for 神戸市立図書館 (ver.20210723)
# Usage: export LIBLIB_USERNAME=foo LIBLIB_PASSWORD=bar $0

import datetime
import json
import os
import sys
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

timeout = 30
url_base = 'https://www.lib.city.kobe.jp'
url_login = url_base + '/opac/opacs/mypage_display'
url_lending = url_base + '/opac/opacs/lending_display'
url_reservation = url_base + '/opac/opacs/reservation_display'
url_logout = url_base + '/opac/opacs/logout'

def do_login(username, password):
	driver.find_element_by_id('user_login').send_keys(username)
	driver.find_element_by_id('user_passwd').send_keys(password)
	driver.find_element_by_xpath('//*[@id="tabmain"]/form/div/div[3]/input[1]').click()
	return

def wait_element(attribute, target):
	try:
		if attribute == 'ID':
			element_present = EC.presence_of_element_located((By.ID, target))
		elif attribute == 'CLASS_NAME':
			element_present = EC.presence_of_element_located((By.CLASS_NAME, target))
		elif attribute == 'XPATH':
			element_present = EC.presence_of_element_located((By.XPATH, target))
		elif attribute == 'CSS_SELECTOR':
			element_present = EC.presence_of_element_located((By.CSS_SELECTOR, target))
		WebDriverWait(driver, timeout).until(element_present)
	except TimeoutException:
		return False
	else:
		return True

def parse_table(mode, driver, url):
	output = {}
	output['items'] = []
	output['datetime'] = datetime.datetime.now().isoformat() + '+09:00'
	output['url'] = url
	trs = driver.find_elements_by_xpath('//*[@id="tabmain"]/form[1]/div/table/tbody/tr')
	ths = driver.find_elements_by_xpath('//*[@id="tabmain"]/form[1]/div/table/tbody/tr/th')
	if ths:
		ths_text = [a.text for a in ths]
		if mode == 'reservation':
			ths_text.insert(0, 'id')
		else:
			ths_text[0] = 'id'
		for i in range(len(trs)):
			tds = trs[i].find_elements_by_tag_name('td')
			if tds:
				item = {}
				for j in range(len(tds)):
					item[ths_text[j]] = tds[j].text
					if ths_text[j] == '返却期限日':
						dt = datetime.datetime.strptime(tds[j].text + ' 00:00:00 JST', '%Y%m%d %H:%M:%S %Z')
						item['date_return'] = dt.isoformat() + '.000000+09:00'
					if '/' in ths_text[j]:
						keys = ths_text[j].split('/')
						values = tds[j].text.split('/')
						for k in range(len(keys)):
							if k < len(values):
								item[keys[k].strip()] = values[k].strip()
						item['name'] = item['書名']
				if mode == 'reservation':
					if item['状況'] == '受取可':
						item['ready'] = True # 動作確認はまだ
					else:
						item['ready'] = False
				output['items'].append(item)
		output['status'] = 'success'
	else:
		output['status'] = 'failure'
	return output

def main():
	driver.get(url_login)
	wait_element('XPATH', '//*[@id="tabmain"]/form/div/div[3]/input[1]') # ログインボタン
	do_login(username, password)
	wait_element('XPATH', '//*[@id="tabmain"]/div[2]/dl/dt[1]/a') # 貸出状況
	outputs = {}
	outputs['status'] = 'failure'
	# 貸出状況照会
	driver.get(url_reservation)
	wait_element('XPATH', '//*[@id="tabmain"]/form/p/input[6]') # 終了ボタン
	outputs['reservation'] = parse_table('reservation', driver, url_reservation)
	# 予約状況照会
	driver.get(url_lending)
	wait_element('XPATH', '//*[@id="tabmain"]/form[2]/input[1]') # 終了ボタン
	outputs['borrowing'] = parse_table('borrowing', driver, url_lending)
	if (outputs['reservation']['status'] == 'success') or (outputs['borrowing']['status'] == 'success'):
		outputs['status'] = 'success'
	print(json.dumps(outputs), end='')
	driver.get(url_logout)
	wait_element('XPATH', '//*[@id="footer"]') # footer
	return

if __name__ == '__main__':
	try:
		args = sys.argv
		if not(os.environ.get('LIBLIB_USERNAME') and os.environ.get('LIBLIB_PASSWORD')):
			print(('Usage: export LIBLIB_USERNAME=foo LIBLIB_PASSWORD=bar; %s ID ...' % args[0]), file=sys.stderr)
			sys.exit(1)
		else:
			username = os.environ.get('LIBLIB_USERNAME')
			password = os.environ.get('LIBLIB_PASSWORD')
			if len(username) * len(password) == 0:
				print(('ERROR: LIBLIB_USERNAME and/or LIBLIB_PASSWORD is empty.' % args[0]), file=sys.stderr)
				sys.exit(2)
		options = webdriver.ChromeOptions()
		options.add_argument('--headless')
		driver = webdriver.Chrome(options=options)
		main()
		driver.quit()
	except KeyboardInterrupt:
		driver.quit()
	finally:
		driver.quit()