#!/usr/bin/env python3

# book2json_d-library.py for 神戸市電子図書館 (ver.20220118)
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
url_base = 'https://www.d-library.jp'
url_login = url_base + '/kobe/g1001/login/#main-contents'
url_check = url_base + '/kobe/g1003/mypage/'
url_logout = url_base + '/kobe/g1001/login/logout/'

def do_login(username, password):
	driver.find_element_by_id('loginID').send_keys(username)
	driver.find_element_by_id('loginPass').send_keys(password)
	driver.find_element_by_xpath('//*[@id="main-contents"]/div[1]/form/div[3]/button').click()
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

def main():
	driver.get(url_login)
	wait_element('XPATH', '//*[@id="main-contents"]/div[1]/form/div[3]/button') # ログインボタン
	do_login(username, password)
	wait_element('XPATH', '//*[@id="footer"]/p[1]') # ページの終わりです
	# 利用状況
	driver.get(url_check)
	wait_element('XPATH', '//*[@id="footer"]/p[1]') # ページの終わりです
	r_lis = driver.find_elements_by_xpath('//*[@id="reservation-material"]/ol/li') # 予約している資料
	b_lis = driver.find_elements_by_xpath('//*[@id="borrowed-material"]/ol/li') # 借りている資料
	output = {}
	output['datetime'] = datetime.datetime.now().isoformat() + '+09:00'
	output['url'] = url_check
	output['status'] = 'failure'
	if r_lis:
		# 予約している資料
		output['reservation'] = {}
		output['reservation']['status'] = 'failure'
		output['reservation']['items'] = []
		for i in range(len(r_lis)):
			dts = r_lis[i].find_elements_by_tag_name('dt')
			dds = r_lis[i].find_elements_by_tag_name('dd')
			item = {}
			item['id'] = int(i + 1)
			for j in range(len(dts)):
				item[dts[j].text] = dds[j].text
				if dts[j].text == '予約資料名' or dts[j].text == '取り置き資料名':
					item['name'] = dds[j].find_element_by_tag_name('a').text
			lend = r_lis[i].find_element_by_xpath('child::form/div/div/button[1]')
			if lend.get_attribute('disabled'):
				item['ready'] = False
			else:
				item['ready'] = True
			output['reservation']['items'].append(item)
			output['reservation']['status'] = 'success'
	if b_lis:
		# 借りている資料
		output['borrowing'] = {}
		output['borrowing']['status'] = 'failure'
		output['borrowing']['items'] = []
		for i in range(len(b_lis)):
			dts = b_lis[i].find_elements_by_tag_name('dt')
			dds = b_lis[i].find_elements_by_tag_name('dd')
			item = {}
			item['id'] = int(i + 1)
			for j in range(len(dts)):
				item[dts[j].text] = dds[j].text
				if dts[j].text == 'ご利用期限日':
					dt = datetime.datetime.strptime(dds[j].text + ' 00:00:00 JST', '%Y年%m月%d日 %H:%M:%S %Z')
					item['date_return'] = dt.isoformat() + '.000000+09:00'
				if dts[j].text == '資料名':
					item['name'] = dds[j].text
			output['borrowing']['items'].append(item)
			output['borrowing']['status'] = 'success'
	if r_lis or b_lis:
		output['status'] = 'success'
	print(json.dumps(output), end='')
	driver.get(url_logout)
	wait_element('XPATH', '//*[@id="footer"]/p[1]') # ページの終わりです
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
		options.add_argument('--disable-gpu')
		driver = webdriver.Chrome(options=options)
		main()
		driver.quit()
	except KeyboardInterrupt:
		driver.quit()
	finally:
		driver.quit()