#!/usr/bin/env python3

# book2json_opac.py for 神戸市立図書館 (Ver.20230205)
# Usage: export LIBLIB_USERNAME=foo LIBLIB_PASSWORD=bar $0

import datetime
import json
import os
import re
import sys
from bs4 import BeautifulSoup # pip3 install bs4
from playwright.sync_api import Playwright, sync_playwright, expect # pip3 install playwright

def run(playwright: Playwright, url: str, username: str, password: str) -> list:
	browser = playwright.chromium.launch(headless=True)
	context = browser.new_context()
	page = context.new_page()
	page.goto(url)
	expect(page).to_have_title(re.compile('トップメニュー'))
	page.get_by_role('link', name='ログイン').click()
	expect(page).to_have_title(re.compile('認証'))
	page.get_by_label('図書館カードの番号').fill(username)
	page.get_by_label('パスワード').fill(password)
	page.get_by_role('button', name='ログイン').click()
	expect(page).to_have_title(re.compile('トップメニュー'))

	# borrowing (借りている資料)
	books_borrowing: dict = { 'status': False, 'items': [] }
	page.get_by_role('link', name='Myライブラリ').click()
	expect(page).to_have_title(re.compile('Myライブラリ'))
	page.get_by_role('link', name='借りている資料').click()
	expect(page).to_have_title(re.compile('貸出状況一覧'))
	soup = BeautifulSoup(page.content(), 'html.parser')
	soup_checktext: str = soup.find('div', attrs={ 'class': 'strMain' }).text
	if not re.search('該当するリストが存在しません。', soup_checktext):
		page.get_by_role('combobox', name='一覧表示件数').select_option('50')
		expect(page).to_have_title(re.compile('貸出状況一覧'))
		soup = BeautifulSoup(page.content(), 'html.parser')
		soup_books = soup.find('ul', attrs={ 'class': 'listBookBa-2 function' }).find_all('li')
		books_borrowing.update({ 'status': True, 'items': parse_html(soup_books, 'borrowing') })
	books_borrowing.update({ 'datetime': get_datetime() })

	# reservation (予約した資料)
	books_reservation: dict = { 'status': False, 'items': [] }
	page.get_by_role("link", name="戻る").click()
	expect(page).to_have_title(re.compile('Myライブラリ'))
	page.get_by_role('link', name='予約した資料').click()
	expect(page).to_have_title(re.compile('予約状況一覧'))
	soup = BeautifulSoup(page.content(), 'html.parser')
	soup_checktext: str = soup.find('div', attrs={ 'class': 'strMain' }).text
	if not re.search('該当するリストが存在しません。', soup_checktext):
		page.get_by_role('combobox', name='一覧表示件数').select_option('50')
		expect(page).to_have_title(re.compile('予約状況一覧'))
		soup = BeautifulSoup(page.content(), 'html.parser')
		soup_books = soup.find('ul', attrs={ 'class': 'listBookBa' }).find_all('li')
		books_reservation.update({ 'status': True, 'items': parse_html(soup_books, 'reservation') })
	books_reservation.update({ 'datetime': get_datetime() })

	page.close()
	context.close()
	browser.close()
	return books_borrowing, books_reservation

def parse_html(soup_books, mode: str) -> list:
	books: list = []
	i: int = 1
	for book in soup_books:
		title_raw: str = book.find('p', attrs={ 'class': 'title' }).find('span', attrs={ 'class': 'title' }).text
		title: str = pickup_title(title_raw)
		if mode == 'borrowing':
			# 借りている資料
			date_start_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[1].text
			date_start: str = pickup_date(date_start_raw, 'borrowing')
			date_end_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[2].text
			date_end: str = pickup_date(date_end_raw, 'borrowing')
			d: dict = { 'id': i, '書名': title, 'name': title, '貸出日': date_start, '返却予定日': date_end }
			if date_end:
				dt = datetime.datetime.strptime(date_end + ' 00:00:00 JST', '%Y-%m-%d %H:%M:%S %Z')
				d['date_return'] = dt.isoformat() + '.000000+09:00'
			books.append(d)
		elif mode == 'reservation':
			# 予約した資料
			date_order_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[1].text
			date_order: str = pickup_date(date_order_raw, 'reservation')
			library_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[1].text
			library: str = pickup_library(library_raw)
			orderstatus_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[2].text
			orderstatus: str = pickup_orderstatus(orderstatus_raw)
			d: dict = { 'id': i, '書名': title, 'name': title, '予約日': date_order, '受取館': library, '予約状態': orderstatus, 'ready': False }
			if re.match('利用可能', orderstatus): # まだ動作未確認 Ref: https://www.city.kobe.lg.jp/documents/1570/k-lib_help.pdf#page=29
				d['ready'] = True
			books.append(d)
		i += 1
	return books

def get_datetime() -> str:
	return datetime.datetime.now().isoformat() + '+09:00'

def cut_space(s: str) -> str:
	s = s.strip()
	s = re.sub(r'\s+', ' ', s)
	return s

def pickup_orderstatus(text: str) -> str:
	orderstatus_str: list = re.findall(r'予約状態：\s+(.+)', text, flags=re.DOTALL)
	r: str = '{0}'.format(cut_space(orderstatus_str[0]))
	return r

def pickup_library(text: str) -> str:
	r: str = re.findall(r'受取館\s+([^\s]+)\s+', text)[0]
	return r

def pickup_title(text: str) -> str:
	r: str = cut_space(re.findall(r'\n*【.*?】\n*(.+)', text, flags=re.DOTALL)[0])
	return r

def pickup_date(text: str, mode: str) -> str:
	if mode == 'borrowing':
		ymd_str: list = re.findall(r'.*日:\n*(\d{4})\.(\d{1,2})\.(\d{1,2})', text)
	elif mode == 'reservation':
		ymd_str: list = re.findall(r'日\s+(\d{4})\.(\d{1,2})\.(\d{1,2})\s+', text)
	ymd_int: list = list(map(int, ymd_str[0]))
	r: str = '{0[0]:0>4d}-{0[1]:0>2d}-{0[2]:0>2d}'.format(ymd_int)
	return r

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

		url: str = 'https://www.lib.city.kobe.jp/winj/sp/top.do?lang=ja'
		d: dict = { 'status': False, 'url': url }
		with sync_playwright() as playwright:
			r1, r2 = run(playwright, url, username, password)
			d.update({ 'status': True, 'borrowing': r1, 'reservation': r2 })
		print(json.dumps(d))

	except KeyboardInterrupt as e:
		print(e)
		raise
