#!/usr/bin/env python3

# book2json.py for 神戸市立図書館 (ver.20210717)
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

def print_comma(i, j):
	if i < (j - 1):
		print(',', end='')
		return True
	else:
		return False

def main():
	driver.get(url_login)
	wait_element('XPATH', '//*[@id="tabmain"]/form/div/div[3]/input[1]') # ログインボタン
	do_login(username, password)
	wait_element('XPATH', '//*[@id="tabmain"]/div[2]/dl/dt[1]/a') # 貸出状況
	driver.find_element_by_xpath('//*[@id="tabmain"]/div[2]/dl/dt[1]/a').click()
	wait_element('XPATH', '//*[@id="tabmain"]/form[2]/input[1]') # 終了ボタン

	print('[', end='')
	trs = driver.find_elements_by_xpath('//*[@id="tabmain"]/form[1]/div/table/tbody/tr')
	ths = driver.find_elements_by_xpath('//*[@id="tabmain"]/form[1]/div/table/tbody/tr/th')
	if ths:
		ths_text = [a.text for a in ths]
		ths_text[0] = 'id'
		for i in range(len(trs)):
			tds = trs[i].find_elements_by_tag_name('td')
			output = {}
			output['datetime'] = datetime.datetime.now().isoformat() + '+09:00'
			if tds:
				for j in range(len(tds)):
					if ths_text[j] == '返却期限日':
						dt = datetime.datetime.strptime(tds[j].text + ' 00:00:00 JST', '%Y%m%d %H:%M:%S %Z')
						output[ths_text[j]] = dt.isoformat() + '.000000+09:00'
					else:
						output[ths_text[j]] = tds[j].text
					if '/' in ths_text[j]:
						keys = ths_text[j].split('/')
						values = tds[j].text.split('/')
						for k in range(len(keys)):
							output[keys[k].strip()] = values[k].strip()
				output['status'] = 'success'
			else:
				output['status'] = 'failure'
			print(json.dumps(output), end='')
			print_comma(i, len(trs))

	print(']')
	return

#if __name__ == '__main__':
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
	sys.exit()
