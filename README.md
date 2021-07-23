# LibLibとは

図書館で借りた本の返却忘れと借り忘れを防ぐための、次のスクリプトのセットです。

|スクリプト名|内容|
|---|---|
|`book2json_opac.py`|神戸市立図書館で借りている本の情報をJSON化するPythonスクリプト|
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
2. `book2json_opac.py`を実行すると、神戸市立図書館で借りている本と予約している本の情報がJSON形式で標準出力されます (JSONの構造は`book2json_d-library.py`と共通)
	```
	$ export LIBLIB_USERNAME='★★'
	$ export LIBLIB_PASSWORD='☆☆'
	$ ./book2json_opac.py | jq
	{
	  "status": "success",
	  "reservation": {
	    "items": [
	      {
	        "id": "1",
	        "チェック": "",
	        "予約日\n予約番号\n問い合わせ番号": "●●\n●●\nPV:●●",
	        "書名/シリーズ名/巻次/著者名/出版社名": "●●/●●/●●/●●/●●",
	        "書名": "●●",
	        "シリーズ名": "●●",
	        "巻次": "●●",
	        "著者名": "●●",
	        "出版社名": "●●",
	        "name": "●●",
	        "状況": "予約中",
	        "取り置き日 /\n受取館 /\n備考": "（未定） /\n●●図書館",
	        "取り置き日": "（未定）",
	        "受取館": "●●図書館",
	        "連絡方法 /\n連絡先": "E-mail(1) /●●",
	        "連絡方法": "E-mail(1)",
	        "連絡先": "●●,
	        "ready": false
	      }
	    ],
	    "datetime": "2021-07-23T17:19:47.884284+09:00",
	    "url": "https://www.lib.city.kobe.jp/opac/opacs/reservation_display",
	    "status": "success"
	  },
	  "borrowing": {
	    "items": [
	      {
	        "id": "1",
	        "延長": "",
	        "書名/シリーズ名/巻次/著者名/出版社名": "●●/●●//●●/●●",
	        "書名": "●●",
	        "シリーズ名": "●●",
	        "巻次": "",
	        "著者名": "●●",
	        "出版社名": "●●",
	        "name": "●●",
	        "返却期限日": "20210731",
	        "date_return": "2021-07-31T00:00:00.000000+09:00",
	        "延滞": "",
	        "予約": "なし",
	        "紛失": "",
	        "窓口館\n/ 資料ID\n/ 書架分類": "●●\n/ ●●\n/ ●●",
	        "窓口館": "●●",
	        "資料ID": "●●",
	        "書架分類": "●●",
	        "備考": ""
	      },
	      {
	        "id": "2",
			〜〜途中省略〜〜
	      }
	    ],
	    "datetime": "2021-07-23T17:19:49.442669+09:00",
	    "url": "https://www.lib.city.kobe.jp/opac/opacs/lending_display",
	    "status": "success"
	  }
	}
	```

### book2json_d-library.py

1. 次の環境変数に値を代入します
	|環境変数名|値の内容|
	|---|---|
	|LIBLIB_USERNAME|利用者ID|
	|LIBLIB_PASSWORD|パスワード|
2. `book2json_d-library.py`を実行すると、神戸市電子図書館で借りている本と予約している本の情報がJSON形式で標準出力されます (JSONの構造は`book2json_opac.py`と共通)
	```
	$ export LIBLIB_USERNAME='★★'
	$ export LIBLIB_PASSWORD='▲▲'
	$ ./book2json_d-library.py | jq
	{
	  "datetime": "2021-07-23T17:21:15.112613+09:00",
	  "url": "https://www.d-library.jp/kobe/g1003/mypage/",
	  "status": "success",
	  "reservation": {
	    "status": "success",
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
	    "status": "success",
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
2. 返却日までの残り時間が24時間未満の本の書名がJSONから抽出され (例: 返却日が「7月15日」の本は7月14日00:00以降から抽出対象になる)、音声アナウンス向けにまとめられたものが標準出力されます
	```
	$ ./book2json_opac.py | ./json2alert.py '神戸市立図書館の'
	神戸市立図書館の次の本、2冊が返却期限です！ 1冊目、『●●』。2冊目、『■■』。以上です。

	$ ./book2json_d-library.py | ./json2alert.py '神戸市電子図書館の'
	神戸市電子図書館の次の本、1冊が返却期限です！ 1冊目、『●●』。以上です。
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
