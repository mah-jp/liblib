#!/usr/bin/env python3

# book2json_opac.py for 神戸市立図書館 (Ver.20251024)
# Usage: LIBLIB_USERNAME=foo LIBLIB_PASSWORD=bar $0

from bs4 import BeautifulSoup # pip3 install bs4
from playwright.sync_api import Playwright, sync_playwright, expect # pip3 install playwright
from playwright_stealth import stealth_sync # reCAPTCHA対策 Ref: https://pypi.org/project/playwright-stealth/
import datetime
import json
import logging
import os
import re
import sys
logger = logging.getLogger(__name__)

BROWER_TIMEOUT = 20000 # msec
URL_START: str = 'https://www.lib.city.kobe.jp/winj/sp/top.do?lang=ja' # winj スマートフォン版
URL_DETAIL: str = 'https://www.lib.city.kobe.jp/winj/opac/switch-detail.do?lang=ja&bibid={:s}' # ID部分は{:s}

class KobeCityLibraryScraper:
    # ウェブスクレイピング
    def run(self, playwright: Playwright, url: str, username: str, password: str) -> list:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        stealth_sync(page)
        page.goto(url)
        page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
        page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
        expect(page).to_have_title(re.compile('トップメニュー'))
        books_borrowing, books_reservation = self._run(page, url, username, password)
        page.close()
        context.close()
        browser.close()
        return books_borrowing, books_reservation

    def _run(self, page: object, url: str, username: str, password: str) -> tuple[dict, dict]:
        self.login(page, username, password)
        books_borrowing: dict = self.get_borrowing_books(page)
        books_reservation: dict = self.get_reservation_books(page)
        return books_borrowing, books_reservation

    def login(self, page: object, username: str, password: str) -> None:
        try:
            page.get_by_role('link', name='ログイン').click()
            page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
            page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
            expect(page).to_have_title(re.compile('認証'))
            page.get_by_label('図書館カードの番号').fill(username)
            page.get_by_label('パスワード').fill(password)
            page.get_by_role('button', name='ログイン').click()
            page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
            page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
            expect(page).to_have_title(re.compile('トップメニュー'))
        except Exception as e:
            logger.error(f'Login failed: {e}')
            raise

    def get_borrowing_books(self, page: object) -> dict:
        books_borrowing: dict = { 'status': False, 'items': [] }
        try:
            page.get_by_role('link', name='Myライブラリ').click()
            page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
            page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
            expect(page).to_have_title(re.compile('Myライブラリ'))
            page.get_by_role('link', name='借りている資料').click()
            page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
            page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
            expect(page).to_have_title(re.compile('貸出状況一覧'))
            soup = BeautifulSoup(page.content(), 'html.parser')
            soup_checktext: str = soup.find('div', attrs={ 'class': 'strMain' }).text
            logger.debug(f'borrowing soup_checktext={self.cut_space(soup_checktext)}')
            if not re.search('該当するリストが存在しません。', soup_checktext):
                # 内容が表示されていたら
                page.get_by_role('combobox', name='一覧表示件数').select_option('50')
                page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
                page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
                expect(page).to_have_title(re.compile('貸出状況一覧'))
                soup = BeautifulSoup(page.content(), 'html.parser')
                soup_books = soup.find('ul', attrs={ 'class': 'listBookBa-2 function' }).find_all('li')
                books_borrowing.update({ 'status': True, 'items': self.parse_html(soup_books, 'borrowing') })
            books_borrowing.update({ 'datetime': self.get_datetime() })
        except Exception as e:
            logger.error(f'Failed to get borrowing books: {e}')
            raise
        return books_borrowing

    def get_reservation_books(self, page: object) -> dict:
        books_reservation: dict = { 'status': False, 'items': [] }
        try:
            page.get_by_role('link', name='戻る').click()
            page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
            page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
            expect(page).to_have_title(re.compile('Myライブラリ'))
            page.get_by_role('link', name='予約した資料').click()
            page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
            page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
            expect(page).to_have_title(re.compile('予約状況一覧'))
            soup = BeautifulSoup(page.content(), 'html.parser')
            soup_checktext: str = soup.find('div', attrs={ 'class': 'strMain' }).text
            logger.debug(f'reservation soup_checktext={self.cut_space(soup_checktext)}')
            if not re.search('該当するリストが存在しません。', soup_checktext):
                # 内容が表示されていたら
                page.get_by_role('combobox', name='一覧表示件数').select_option('50')
                page.wait_for_load_state('load', timeout=BROWER_TIMEOUT)
                page.wait_for_load_state('domcontentloaded', timeout=BROWER_TIMEOUT)
                expect(page).to_have_title(re.compile('予約状況一覧'))
                soup = BeautifulSoup(page.content(), 'html.parser')
                soup_books = soup.find('ul', attrs={ 'class': 'listBookBa' }).find_all('li')
                books_reservation.update({ 'status': True, 'items': self.parse_html(soup_books, 'reservation') })
            books_reservation.update({ 'datetime': self.get_datetime() })
        except Exception as e:
            logger.error(f'Failed to get reservation books: {e}')
            raise
        return books_reservation

    def parse_html(self, soup_books, mode: str) -> list:
        books: list = []
        i: int = 1
        for book in soup_books:
            logger.debug(f'{mode} book={self.cut_space(book.text)}')
            if book.find('p', attrs={ 'class': 'title' }): # 資料のタイトルがあったら
                title_raw: str = book.find('p', attrs={ 'class': 'title' }).find('span', attrs={ 'class': 'title' }).text
                logger.debug(f'{mode} title_raw={self.cut_space(title_raw)}')
                title: str = self.pickup_title(title_raw)
                if mode == 'borrowing':
                    # 借りている資料
                    date_start_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[1].text
                    logger.debug(f'{mode} date_start_raw={self.cut_space(date_start_raw)}')
                    date_start: str = self.pickup_date(date_start_raw, 'borrowing')
                    date_end_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[2].text
                    logger.debug(f'{mode} date_end_raw={self.cut_space(date_end_raw)}')
                    date_end: str = self.pickup_date(date_end_raw, 'borrowing')
                    count_reserve: int = self.pickup_reserve(date_end_raw) # date_end_rawから無理矢理に取得
                    imgsrc_raw: str = book.find('p', attrs={ 'class': 'title' }).find('img').get('src')
                    url: str = self.make_url(URL_DETAIL, imgsrc_raw)
                    flag_extended: bool = self.pickup_extended(book)
                    flag_reserved: bool = self.pickup_reserved(book)
                    d: dict = {
                        'id': i,
                        'name': title,
                        'url': url,
                        '貸出日': date_start,
                        '返却予定日': date_end,
                        '予約件数': count_reserve,
                        'flag_extended': flag_extended,
                        'flag_reserved': flag_reserved }
                    if date_end:
                        dt = datetime.datetime.strptime(date_end + ' 00:00:00 JST', '%Y-%m-%d %H:%M:%S %Z')
                        d['date_return'] = dt.isoformat() + '.000000+09:00'
                    books.append(d)
                elif mode == 'reservation':
                    # 予約した資料
                    date_order_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[1].text
                    logger.debug(f'{mode} date_order_raw={self.cut_space(date_order_raw)}')
                    date_order: str = self.pickup_date(date_order_raw, 'reservation')
                    library_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[1].text
                    logger.debug(f'{mode} library_raw={self.cut_space(library_raw)}')
                    library: str = self.pickup_library(library_raw)
                    orderstatus_raw: str = book.find_all('p', attrs={ 'class': 'txt' })[2].text
                    logger.debug(f'{mode} orderstatus_raw={self.cut_space(orderstatus_raw)}')
                    orderstatus: str = self.pickup_orderstatus(orderstatus_raw)
                    imgsrc_raw: str = book.find('p', attrs={ 'class': 'title' }).find('img').get('src')
                    url: str = self.make_url(URL_DETAIL, imgsrc_raw)
                    d: dict = {
                        'id': i,
                        'name': title,
                        'url': url,
                        '予約日': date_order,
                        '受取館': library,
                        '予約状態': orderstatus,
                        'ready': False }
                    if re.match('利用可能', orderstatus): # Ref: https://www.city.kobe.lg.jp/documents/1570/k-lib_help.pdf#page=30
                        d['ready'] = True
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
        orderstatus_str: list = re.findall(r'予約状態：\s+(.+)', text, flags=re.DOTALL)
        r: str = '{0}'.format(self.cut_space(orderstatus_str[0]))
        return r

    def pickup_library(self, text: str) -> str:
        r: str = re.findall(r'受取館\s+([^\s]+)\s+', text)[0]
        return r

    def pickup_title(self, text: str) -> str:
        r: str = self.cut_space(re.findall(r'\n*【.*?】\n*(.+)', text, flags=re.DOTALL)[0])
        return r

    def pickup_date(self, text: str, mode: str) -> str:
        if mode == 'borrowing':
            ymd_str: list = re.findall(r'.*日:\n*(\d{4})\.(\d{1,2})\.(\d{1,2})', text)
        elif mode == 'reservation':
            ymd_str: list = re.findall(r'日\s+(\d{4})\.(\d{1,2})\.(\d{1,2})\s+', text)
        ymd_int_list: list = list(map(int, ymd_str[0]))
        r: str = '{0[0]:0>4d}-{0[1]:0>2d}-{0[2]:0>2d}'.format(ymd_int_list)
        return r

    def pickup_reserve(self, text: str) -> int:
        r: int = 0
        count_str: list = re.findall(r'予約:(\d+)件', text)
        if len(count_str) > 0:
            r = int(count_str[0])
        return r

    def make_url(self, url_base: str, path: str) -> str:
        bibid: str = re.findall(r'bibid=(\d+)', path)[0]
        url: str = url_base.format(bibid)
        return url

    def pickup_extended(self, book) -> bool:
        if book.find('li'):
            for li in book.find_all('li'):
                tag_em = li.find('em', attrs={ 'class': 'icon2 extend' })
                if tag_em and re.match('延長済', tag_em.text):
                    return True
        return False

    def pickup_reserved(self, book) -> bool:
        if book.find('li'):
            for li in book.find_all('li'):
                tag_em = li.find('em', attrs={ 'class': 'icon2 reserveExist' })
                if tag_em and re.match('予約有', tag_em.text):
                    return True
        return False

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
            scraper = KobeCityLibraryScraper()
            r1, r2 = scraper.run(playwright, url, username, password)
            logger.debug('borrowing={}, reservation={}'.format(r1, r2))
            d.update({ 'status': True, 'borrowing': r1, 'reservation': r2 })
        print(json.dumps(d, ensure_ascii=False, indent=2))
    except KeyboardInterrupt as e:
        logging.error('{}'.format(e))
        raise
