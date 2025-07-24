# LibLibとは

- Date: 2025-07-25

図書館で借りた本の返却忘れと予約本の借り忘れを防ぐための、作者の事情により神戸市立図書館と神戸市電子図書館に特化している、次のスクリプトのセットです。v2.0.0ではDocker環境での動作を前提とした作り変えを行い、セットアップが以前より簡単になりました。

|スクリプト名|内容|
|---|---|
|`book2json_opac.py`|神戸市立図書館で借りている本と予約している本の情報をJSON化するPythonスクリプト|
|`book2json_d-library.py`|神戸市電子図書館で借りている本と予約している本の情報をJSON化するPythonスクリプト|
|`json2message.py`|`book2json_{opac,d-library}.py`が出力するJSONを読み込み、返却期限が近い本と取り置き中の予約本の書名をテキスト出力するPythonスクリプト|

## セットアップ方法・使い方

1. LibLibを動作させたいサーバ・パソコンにDocker環境を整えます (`docker compose`が使えるようにします)
2. 本リポジトリをcloneします
	```
	$ git clone https://github.com/mah-jp/liblib
	$ cd liblib
	```
3. [envディレクトリ](./env/)内の設定ファイル`sample.env`を複製して、`お好みの名前.env`を作成します
4. `お好みの名前.env`をテキストエディタで開き、各種変数を定義します
5. 次のコマンドを実行します
	```
	$ FILE_ENV=お好みの名前.env docker compose up
	```
6. 設定ファイルの内容に基づいて図書館サイトへアクセスが行われ、借りている本と予約している本の情報がoutputディレクトリ内に保存されます

### 注意事項

- スクリプトを改造したり更新した後は、Dockerコンテナの再構築が必要となります。次のコマンドを実行してください。
  ```
  $ docker compose down
	$ FILE_ENV=お好みの名前.env docker compose up --build
  ```

## outputディレクトリ内に保存されるファイル

### 1. JSONファイルについて

|ファイル名|対象図書館|内容|
|---|---|---|
|`opac.json`|神戸市立図書館|借りている本と予約している本の情報|
|`d-library.json`|神戸市電子図書館|借りている本と予約している本の情報|

#### opac.json (神戸市立図書館)

このJSONファイルは`book2json_opac.py`が出力し、神戸市立図書館で借りている本と予約している本の情報を含みます。JSONの構造は次のとおりです。
```json
{
  "status": true,
  "url": "https://www.lib.city.kobe.jp/winj/sp/top.do?lang=ja",
  "borrowing": {
    "status": true,
    "items": [
      {
        "id": 1,
        "書名": "タイトルHOGEHOGE1",
        "name": "タイトルHOGEHOGE1",
        "url": "https://www.lib.city.kobe.jp/winj/opac/switch-detail.do?lang=ja&bibid=XXXXXXXXXX",
        "貸出日": "2024-05-19",
        "返却予定日": "2024-06-02",
        "予約件数": 0,
        "date_return": "2024-06-02T00:00:00.000000+09:00"
      }
    ],
    "datetime": "2024-05-19T23:22:41.947999+09:00"
  },
  "reservation": {
    "status": true,
    "items": [
      {
        "id": 1,
        "書名": "タイトルHOGEHOGE2",
        "name": "タイトルHOGEHOGE2",
        "url": "https://www.lib.city.kobe.jp/winj/opac/switch-detail.do?lang=ja&bibid=XXXXXXXXXX",
        "予約日": "2024-05-19",
        "受取館": "HOGE図書館",
        "予約状態": "返却待ち 順番：1",
        "ready": false
      }
    ],
    "datetime": "2024-05-19T23:22:42.640295+09:00"
  }
}
```

#### d-library.json (神戸市電子図書館)

このJSONファイルは`book2json_d-library.py.py`が出力し、神戸市電子図書館で借りている本と予約している本の情報を含みます。JSONの構造は次のとおりです。
```json
{
  "status": true,
  "url": "https://web.d-library.jp/kobe/g1001/top/",
  "borrowing": {
    "status": true,
    "items": [
      {
        "id": 1,
        "書名": "タイトルHOGEHOGE3",
        "name": "タイトルHOGEHOGE3",
        "url": "https://web.d-library.jp/kobe/g0102/libcontentsinfo/?conid=XXXXXX",
        "利用期限日": "2024-06-02",
        "date_return": "2024-06-02T00:00:00.000000+09:00"
      }
    ],
    "datetime": "2024-05-19T22:58:35.685335+09:00"
  },
  "reservation": {
    "status": true,
    "items": [
      {
        "id": 1,
        "書名": "タイトルHOGEHOGE4",
        "name": "タイトルHOGEHOGE4",
        "url": "https://web.d-library.jp/kobe/g0102/libcontentsinfo/?conid=XXXXXX",
        "予約日": "2024-04-03",
        "予約状態": "18人中16番目",
        "ready": false
      }
    ],
    "datetime": "2024-05-19T22:58:38.513928+09:00"
  }
}
```

### 2. TXTファイルについて

|ファイル名|対象図書館|内容|
|---|---|---|
|`opac.txt`|神戸市立図書館|`opac.json`から下記条件で抽出した情報|
|`d-library.txt`|神戸市電子図書館|`d-library.json`から下記条件で抽出した情報|

これらのTXTファイルの内容は、各JSONファイルから次の条件に該当する本の情報を抽出し、話し言葉になるようにテキスト化したものです。条件に該当する本の情報がなかった場合、ファイルはカラ (0バイト) になります。
- 返却日までの残り時間が48時間以内の本 (例: 返却日が「7月15日」の本は7月13日00:00以降から対象になる)
- 取り置き中になっている予約本

例えば神戸市立図書館に関して、『●●』と『■■』の返却期限が近づいており、『▲▲』が取り置き中の場合、`opac.txt`は次のような内容になります。
- `神戸市立図書館の次の本、2冊が返却期限です！ 1冊目、『●●』が明日。2冊目、『■■』が明後日。次の本、1冊が取り置き中です！ 1冊目、『▲▲』。以上です。`

#### TXTファイルの使い道は？

作者は、返却期限が近い本の返却を忘れないためのリマインダーとして、また予約本が取り置き状態になったら分かる通知として、このTXTファイルの内容を家のスマートスピーカーに喋らせています。

## AUTHOR

大久保 正彦 (Masahiko OHKUBO)
