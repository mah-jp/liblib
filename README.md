# LibLibとは

- Date: 2025-10-24

図書館で借りた本の返却忘れと予約本の借り忘れを防ぐための、作者の事情により神戸市立図書館と神戸市電子図書館に特化している、次のスクリプトのセットです。v2.0.0ではDocker環境での動作を前提とした作り変えを行い、セットアップが以前より簡単になりました。

|スクリプト名|内容|
|---|---|
|`book2json_opac.py`|神戸市立図書館にログインし、貸出・予約状況をスクレイピングしてJSON形式で出力します。|
|`book2json_d-library.py`|神戸市電子図書館にログインし、貸出・予約状況をスクレイピングしてJSON形式で出力します。|
|`json2message.py`|上記スクリプトが出力したJSONを標準入力から受け取り、通知が必要な書籍情報 (返却期限が近い、予約本が準備完了など) を人間が読みやすいテキスト形式で出力します。<br>引数で、メッセージの接頭辞 (`pretext`)、通知対象とする返却期限までの時間 (`--hour_deadline`)、短い書籍名を利用するか (`--use_name_short`) を指定できます。|
|`book2json_wrapper.sh`|設定ファイル (`env/*.env`) に基づいて上記スクリプト群を実行し、結果を`output`ディレクトリに保存するラッパーシェルスクリプトです。|

## セットアップ方法・使い方

1. LibLibを動作させたいサーバ・パソコンにDocker環境を整えます (`docker compose`が使えるようにします)
2. 本リポジトリをcloneします
	```
	$ git clone https://github.com/mah-jp/liblib
	$ cd liblib
	```
3. envディレクトリ内の設定ファイル`sample.env`を参考に、`お好みの名前.env`というファイル名で設定ファイルを作成します。
4. `お好みの名前.env`をテキストエディタで開き、各種変数を定義します。
   - `FLAG_OPAC=1`: 神戸市立図書館の情報を取得する場合に`1`を設定します。
   - `OPAC_USERNAME="..."`: 神戸市立図書館の図書館カードの番号
   - `OPAC_PASSWORD="..."`: 〃のパスワード
   - `PREFIX_TXT_OPAC="..."`: `json2message.py`で生成するメッセージの接頭辞 (例: `神戸市立図書館の`)。
   - `FLAG_DLIBRARY=1`: 神戸市電子図書館の情報を取得する場合に`1`を設定します。
   - `DLIBRARY_USERNAME="..."`: 神戸市電子図書館の利用者ID
   - `DLIBRARY_PASSWORD="..."`: 〃のパスワード
   - `PREFIX_TXT_DLIBRARY="..."`: `json2message.py`で生成するメッセージの接頭辞 (例: `神戸市電子図書館の`)。
   - `LOGGING_DEBUG=1`: デバッグログを有効にする場合に`1`を設定します。
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
        "name": "タイトルHOGEHOGE1",
        "url": "https://www.lib.city.kobe.jp/winj/opac/switch-detail.do?lang=ja&bibid=XXXXXXXXXX",
        "貸出日": "2024-05-19",
        "返却予定日": "2024-06-02",
        "予約件数": 0,
        "flag_extended": false,
        "flag_reserved": false,
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

このJSONファイルは`book2json_d-library.py`が出力し、神戸市電子図書館で借りている本と予約している本の情報を含みます。JSONの構造は次のとおりです。
```json
{
  "status": true,
  "url": "https://web.d-library.jp/kobe/g1001/top/",
  "borrowing": {
    "status": true,
    "items": [
      {
        "id": 1,
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

例えば、次のような状況を考えます。
- 神戸市立図書館：『●●』 (延長可能) と『■■』 (延長不可) の返却期限が近づいており、『▲▲』が取り置き中
- 神戸市電子図書館：『◆◆』の利用期限が近づいている

この場合、`opac.txt`と`d-library.txt`はそれぞれ以下のようになります。
- **opac.txt**: `神戸市立図書館の次の本、2冊が返却期限です！ 1冊目、『●●』が明日で、延長は可能です。2冊目、『■■』が明後日で、延長はできません。次の予約本、1冊が取り置き中です！ 1冊目、『▲▲』。 以上です。`
- **d-library.txt**: `神戸市電子図書館の次の本、1冊が返却期限です！ 1冊目、『◆◆』が本日。 以上です。`

#### TXTファイルの使い道は？

作者は、返却期限が近い本の返却を忘れないためのリマインダーとして、また予約本が取り置き状態になったことを知らせる通知として、このTXTファイルの内容を家のスマートスピーカーに喋らせています。

## AUTHOR

大久保 正彦 (Masahiko OHKUBO)
