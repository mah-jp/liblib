#!/usr/bin/env python3

# book2json_d-library.py for 神戸市電子図書館 (Ver.20250309)
# Usage: LIBLIB_USERNAME=foo LIBLIB_PASSWORD=bar $0

from bs4 import BeautifulSoup # pip3 install bs4
from playwright.sync_api import Playwright, sync_playwright, expect # pip install playwright
from playwright_stealth import stealth_sync # reCAPTCHA対策 Ref: https://pypi.org/project/playwright-stealth/
import datetime
import json
import logging
import os
import re
import sys
logger = logging.getLogger(__name__)

BROWER_TIMEOUT = 20000 # msec
URL_START: str = 'https://web.d-library.jp/kobe/g1001/top/' # テキスト版
URL_DETAIL: str = 'https://web.d-library.jp/kobe/g0102/libcontentsinfo/?conid={:s}' # ID部分は{:s}

# ウェブスクレイピング
class DLibraryScraper:
    def __init__(self, url_start, url_detail):
        self.url_start = url_start
        self.url_detail = url_detail

    def login(self, page, username, password):
        page.goto(self.url_start)
        page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
        page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
        expect(page).to_have_title(re.compile('トップページ'))
        page.get_by_role('link', name='サイトにログインする').click()
        page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
        page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
        expect(page).to_have_title(re.compile('ログイン'))
        page.get_by_label('利用者ID').fill(username)
        page.get_by_label('パスワード').fill(password)
        page.get_by_role('button', name='ログインする').click()
        page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
        page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
        expect(page).to_have_title(re.compile('トップページ'))

    def get_borrowing_books(self, page):
        books_borrowing: dict = { 'status': False, 'items': [] }
        page.get_by_role('link', name=re.compile('借りている資料')).click()
        page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
        page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
        expect(page).to_have_title(re.compile('マイページ'))
        soup = BeautifulSoup(page.content(), 'html.parser')
        soup_checktext: str = soup.find('section', attrs={ 'id': 'borrowed-material' }).text
        logger.debug('borrowing soup_checktext={}'.format(self.cut_space(soup_checktext)))
        if not re.search('該当の資料はありません', soup_checktext):
            # 内容が表示されていたら
            soup = BeautifulSoup(page.content(), 'html.parser')
            soup_books = soup.find('section', attrs={ 'id': 'borrowed-material' }).find('ol', attrs={ 'class': 'book-list' }).find_all('li')
            books_borrowing.update({ 'status': True, 'items': self.parse_html(soup_books, 'borrowing') })
        books_borrowing.update({ 'datetime': self.get_datetime() })
        return books_borrowing

    def get_reservation_books(self, page):
        books_reservation: dict = { 'status': False, 'items': [] }
        page.get_by_role('link', name='トップ', exact=True).click()
        page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
        page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
        expect(page).to_have_title(re.compile('トップページ'))
        page.get_by_role('link', name=re.compile('予約している資料')).click()
        page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
        page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
        expect(page).to_have_title(re.compile('マイページ'))
        soup = BeautifulSoup(page.content(), 'html.parser')
        soup_checktext: str = soup.find('section', attrs={ 'id': 'reservation-material' }).text
        logger.debug('reservation soup_checktext={}'.format(self.cut_space(soup_checktext)))
        if not re.search('該当の資料はありません', soup_checktext):
            # 内容が表示されていたら
            soup = BeautifulSoup(page.content(), 'html.parser')
            soup_books = soup.find('section', attrs={ 'id': 'reservation-material' }).find('ol', attrs={ 'class': 'book-list' }).find_all('li')
            books_reservation.update({ 'status': True, 'items': self.parse_html(soup_books, 'reservation') })
        books_reservation.update({ 'datetime': self.get_datetime() })
        return books_reservation

    def run(self, playwright: Playwright, url: str, username: str, password: str) -> list:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        stealth_sync(page)

        # DLibraryScraperのインスタンスを作成
        scraper = DLibraryScraper(URL_START, URL_DETAIL)
        scraper.login(page, username, password)
        books_borrowing = scraper.get_borrowing_books(page)
        books_reservation = scraper.get_reservation_books(page)
        page.close()
        context.close()
        browser.close()
        return books_borrowing, books_reservation

    # HTMLの解析
    def parse_html(self, soup_books, mode: str) -> list:
        books: list = []
        i: int = 1
        for book in soup_books:
            logger.debug('{} book={}'.format(mode, self.cut_space(book.text)))
            if mode == 'borrowing':
                # 借りている資料
                if book.find_all('dt')[0].text == '資料名': # 資料のタイトルがあったら
                    title_raw: str = book.find_all('dd')[0].find('a').text
                    logger.debug('{:s} title_raw={}'.format(mode, self.cut_space(title_raw)))
                    title: str = self.pickup_title(title_raw)
                    date_end_raw: str = book.find('dd', attrs={ 'class': 'value-return-date' }).text
                    logger.debug('{:s} date_end_raw={}'.format(mode, self.cut_space(date_end_raw)))
                    date_end: str = self.pickup_date(date_end_raw, 'borrowing')
                    url_raw: str = book.find_all('dd')[0].find('a').get('href')
                    url: str = self.make_url(url_raw)
                    d: dict = { 'id': i, '書名': title, 'name': title, 'url': url, '利用期限日': date_end }
                    if date_end:
                        dt = datetime.datetime.strptime(date_end + ' 00:00:00 JST', '%Y-%m-%d %H:%M:%S %Z')
                        d['date_return'] = dt.isoformat() + '.000000+09:00'
                    books.append(d)
            elif mode == 'reservation':
                # 予約している資料
                if book.find_all('dt')[2].text == '予約資料名': # 資料のタイトルがあったら
                    title_raw: str = book.find_all('dd')[2].find('a').text
                    logger.debug('{:s} title_raw={}'.format(mode, self.cut_space(title_raw)))
                    title: str = self.pickup_title(title_raw)
                    date_order_raw: str = book.find_all('dd')[0].text
                    logger.debug('{:s} date_order_raw={}'.format(mode, self.cut_space(date_order_raw)))
                    date_order: str = self.pickup_date(date_order_raw, 'reservation')
                    orderstatus_raw: str =book.find_all('dd')[1].text
                    logger.debug('{:s} orderstatus_raw={}'.format(mode, self.cut_space(orderstatus_raw)))
                    orderstatus: str = self.pickup_orderstatus(orderstatus_raw)
                    url_raw: str = book.find_all('dd')[2].find('a').get('href')
                    logger.debug('{:s} url_raw={}'.format(mode, self.cut_space(url_raw)))
                    url: str = self.make_url(url_raw)
                    d: dict = { 'id': i, '書名': title, 'name': title, 'url': url, '予約日': date_order, '予約状態': orderstatus, 'ready': False }
                    books.append(d)
                elif book.find_all('dt')[1].text == '取り置き資料名': # 資料のタイトルがあったら
                    title_raw: str = book.find_all('dd')[1].find('a').text
                    logger.debug('{:s} title_raw={}'.format(mode, self.cut_space(title_raw)))
                    title: str = self.pickup_title(title_raw)
                    date_order_raw: str = book.find_all('dd')[0].text
                    logger.debug('{:s} date_order_raw={}'.format(mode, self.cut_space(date_order_raw)))
                    date_order: str = self.pickup_date(date_order_raw, 'reservation')
                    orderstatus_raw: str = book.find_all('dd')[1].find('em').text
                    logger.debug('{:s} orderstatus_raw={}'.format(mode, self.cut_space(orderstatus_raw)))
                    orderstatus: str = self.pickup_orderstatus(orderstatus_raw)
                    url_raw: str = book.find_all('dd')[1].find('a').get('href')
                    logger.debug('{:s} url_raw={}'.format(mode, self.cut_space(url_raw)))
                    url: str = self.make_url(url_raw)
                    d: dict = { 'id': i, '書名': title, 'name': title, 'url': url, '取り置き期限': date_order, '予約状態': orderstatus, 'ready': True }
                    books.append(d)
                i += 1
        return books

    def get_datetime(self) -> str:
        return datetime.datetime.now().isoformat() + '+09:00'

    def cut_space(self, s: str) -> str:
        s = s.strip()
        s = re.sub(r'\s+', ' ', s)
        return s

    def pickup_orderstatus(self, text: str) -> str:
        # orderstatus_str: list = re.findall(r'(\d+)人中(\d+)番目', text)
        # orderstatus_int_list: list = list(map(int, orderstatus_str[0]))
        # r: str = '{0[1]}/{0[0]}'.format(orderstatus_int_list)
        r: str = self.cut_space(text)
        return r

    def pickup_title(self, text: str) -> str:
        r: str = self.cut_space(text)
        return r

    def pickup_date(self, text: str, mode: str) -> str:
        if mode == 'borrowing':
            ymd_str: list = re.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        elif mode == 'reservation':
            ymd_str: list = re.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        ymd_int_list: list = list(map(int, ymd_str[0]))
        r: str = '{0[0]:0>4d}-{0[1]:0>2d}-{0[2]:0>2d}'.format(ymd_int_list)
        return r

    def pickup_reserve(self, text: str, mode: str) -> int:
        r: int = 0
        if mode == 'borrowing':
            count_str: str = re.findall(r'予約:(\d+)件', text)
        # elif mode == 'reservation':
        # 
        if len(count_str) > 0:
            r = int(count_str[0])
        return r

    def make_url(self, path: str) -> str:
        bibid: str = re.findall(r'conid=(\d+)', path)[0]
        url: str = self.url_detail.format(bibid)
        return url

if __name__ == '__main__':
    DIR_ME: str = os.path.dirname(os.path.abspath(__file__))
    FILE_ME: str = os.path.basename(__file__)
    # loggingモジュールの設定 (debug, info, warning, error, critical)
    logging.basicConfig(
        level=logging.WARNING,
        format='[%(asctime)s] %(name)s[%(thread)d]:%(funcName)s:%(lineno)d <%(levelname)s> %(message)s'
    )
    if os.environ.get('LOGGING_DEBUG') and os.environ.get('LOGGING_DEBUG') == '1':
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug('LOGGING_DEBUG={:s}'.format(os.environ.get('LOGGING_DEBUG')))

    try:
        args = sys.argv
        if not(os.environ.get('LIBLIB_USERNAME') and os.environ.get('LIBLIB_PASSWORD')):
            logging.error('Usage: LIBLIB_USERNAME=foo LIBLIB_PASSWORD=bar; {:s}'.format(args[0]))
            sys.exit(1)
        else:
            username: str = os.environ.get('LIBLIB_USERNAME')
            password: str = os.environ.get('LIBLIB_PASSWORD')
            if len(username) * len(password) == 0:
                logging.error('ERROR: LIBLIB_USERNAME and/or LIBLIB_PASSWORD is empty.'.format())
                sys.exit(2)
        url: str = URL_START
        logger.debug('url={}'.format(url))
        d: dict = { 'status': False, 'url': url }
        with sync_playwright() as playwright:
            scraper = DLibraryScraper(URL_START, URL_DETAIL)
            r1, r2 = scraper.run(playwright, url, username, password)
            logger.debug('borrowing={}, reservation={}'.format(r1, r2))
            d.update({ 'status': True, 'borrowing': r1, 'reservation': r2 })
        print(json.dumps(d, ensure_ascii=False, indent=2))
    except KeyboardInterrupt as e:
        logging.error('{}'.format(e))
        raise
