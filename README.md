# LibLibとは

図書館で借りた本の返却忘れと予約本の借り忘れを防ぐための、次のスクリプトのセットです。

|スクリプト名|内容|
|---|---|
|`book2json_opac.py`|神戸市立図書館で借りている本と予約している本の情報をJSON化するPythonスクリプト|
|`book2json_d-library.py`|神戸市電子図書館で借りている本と予約している本の情報をJSON化するPythonスクリプト|
|`json2alert.py`|`book2json_{opac,d-library}.py`が出力するJSONを読み込み、返却期限が近い本と取り置き中の予約本の書名を出力するPythonスクリプト|
|`bookcheck_sample.sh`|`book2json_{opac,d-library}.py`と`json2alert.py`を組み合わせて起動するbashスクリプトのサンプル|

## 各スクリプトの使い方

### book2json_opac.py

1. 次の環境変数に値を代入します
	|環境変数名|値の内容|
	|---|---|
	|LIBLIB_USERNAME|図書館カード番号|
	|LIBLIB_PASSWORD|パスワード|
2. `book2json_opac.py`を実行すると、神戸市立図書館で借りている本と予約している本の情報が以下のJSON形式で標準出力されます
	```
	$ export LIBLIB_USERNAME='★★'
	$ export LIBLIB_PASSWORD='☆☆'
	$ ./book2json_opac.py | jq
	{
	  "status": true,
	  "url": "https://www.lib.city.kobe.jp/winj/sp/top.do?lang=ja",
	  "borrowing": {
	    "status": true,
	    "items": [
	      {
	        "id": 1,
	        "書名": "●●",
	        "name": "●●",
	        "貸出日": "2023-02-01",
	        "返却予定日": "2023-02-15",
	        "date_return": "2023-02-15T00:00:00.000000+09:00"
	      }
	    ],
	    "datetime": "2023-02-08T23:07:59.114602+09:00"
	  },
	  "reservation": {
	    "status": true,
	    "items": [
	      {
	        "id": 1,
	        "書名": "●●",
	        "name": "●●",
	        "予約日": "2022-11-04",
	        "受取館": "●●図書館",
	        "予約状態": "利用可能 取置期限日:2023.02.16",
	        "ready": true
	      },
	      {
	        "id": 2,
	        "書名": "●●",
	        "name": "●●",
	        "予約日": "2022-09-10",
	        "受取館": "●●図書館",
	        "予約状態": "返却待ち 順番：4",
	        "ready": false
	      }
	    ],
	    "datetime": "2023-02-08T23:07:04.519431+09:00"
	  }
	}
	```

### book2json_d-library.py

1. 次の環境変数に値を代入します
	|環境変数名|値の内容|
	|---|---|
	|LIBLIB_USERNAME|利用者ID|
	|LIBLIB_PASSWORD|パスワード|
2. `book2json_d-library.py`を実行すると、神戸市電子図書館で借りている本と予約している本の情報が以下のJSON形式で標準出力されます
	```
	$ export LIBLIB_USERNAME='★★'
	$ export LIBLIB_PASSWORD='▲▲'
	$ ./book2json_d-library.py | jq
	{
	  "datetime": "2021-07-23T17:21:15.112613+09:00",
	  "url": "https://www.d-library.jp/kobe/g1003/mypage/",
	  "status": true,
	  "reservation": {
	    "status": true,
	    "items": [
	      {
	        "id": 1,
	        "取り置き期限": "2021年7月30日",
	        "取り置き資料名": "●●",
	        "name": "●●",
	        "著者": "●●",
	        "ready": true
	      },
	      {
	        "id": 2,
	        〜〜途中省略〜〜
	        "ready": false
	      }
	    ]
	  },
	  "borrowing": {
	    "status": true,
	    "items": [
	      {
	        "id": 1,
	        "資料名": "●●",
	        "name": "●●",
	        "著者": "●●",
	        "ご利用期限日": "2021年8月1日",
	        "date_return": "2021-08-01T00:00:00.000000+09:00"
	      }
	    ]
	  }
	}
	```

### json2alert.py

1. `json2alert.py`を、`book2json_opac.py`または`book2json_d-library.py`が標準出力するJSONを標準入力する形で実行します
2. 返却日までの残り時間が48時間以内の本の書名がJSONから抽出され (例: 返却日が「7月15日」の本は7月13日00:00以降から抽出対象になる)、音声アナウンス向けにまとめられたものが標準出力されます
	```
	$ ./book2json_opac.py | ./json2alert.py '神戸市立図書館の'
	神戸市立図書館の次の本、2冊が返却期限です！ 1冊目、『●●』が明日。2冊目、『■■』が明後日。以上です。

	$ ./book2json_d-library.py | ./json2alert.py '神戸市電子図書館の'
	神戸市電子図書館の次の本、1冊が返却期限です！ 1冊目、『●●』が明日。以上です。
	```
3. 同様に、取り置き中になっている予約本の書名がJSONから抽出され、音声アナウンス向けにまとめられたものが標準出力されます (まだ少し実験中)
	```
	$ ./book2json_opac.py | ./json2alert.py '神戸市立図書館の'
	神戸市立図書館の次の本、1冊が取り置き中です！ 1冊目、『●●』。以上です。

	$ ./book2json_d-library.py | ./json2alert.py '神戸市電子図書館の'
	神戸市電子図書館の次の本、1冊が取り置き中です！ 1冊目、『●●』。以上です。
	```
4. `json2alert.py`実行時に第1引数が指定されていると、それを標準出力の冒頭に挿入するようにしています (図書館名や家族の名前にしておくとよいでしょう)

### bookcheck_sample.sh

`book2json_{opac,d-library}.py`と`json2alert.py`を組み合わせて起動するbashスクリプトのサンプルです。

私の家では、`json2alert.py`の標準出力を音声として、部屋のスマートスピーカーに喋らせるために別のスクリプトを呼び出しており、そのまんまの内容を本サンプルにしています。この点ご留意ください。

## AUTHOR

大久保 正彦 (Masahiko OHKUBO)
