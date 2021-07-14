# LibLibとは

図書館で借りた本の返却忘れを防ぐための、次のスクリプトのセットです。

- `book2json.py`: 神戸市立図書館で借りている本の情報をJSON化するPythonスクリプト
- `json2alert.py`: `book2json.py`が出力するJSONを読み込み、返却期限が近い本の書名を出力するPythonスクリプト
- `bookcheck_sample.sh`: `book2json.py`と`json2alert.py`を組み合わせて起動するbashスクリプトのサンプル

## 各スクリプトの使い方

### book2json.py

1. 次の環境変数に値を代入します
	|環境変数名|値の内容|
	|---|---|
	|LIBLIB_USERNAME|図書館カード番号|
	|LIBLIB_PASSWORD|パスワード|
2. `book2json.py`を実行すると、借りている本の冊数分の情報がJSON形式で標準出力されます
	```
	$ export LIBLIB_USERNAME='★★'
	$ export LIBLIB_PASSWORD='☆☆'
	$ ./book2json.py | jq
	[
	{
		"datetime": "2021-07-14T01:11:57.521594+09:00",
		"status": "failure"
	},
	{
		"datetime": "2021-07-14T01:11:57.530070+09:00",
		"id": "1",
		"延長": "",
		"書名/シリーズ名/巻次/著者名/出版社名": "●●/●●/●●/●●/●●",
		"書名": "●●",
		"シリーズ名": "●●",
		"巻次": "●●",
		"著者名": "●●",
		"出版社名": "●●",
		"返却期限日": "2021-07-14T00:00:00.000000+09:00",
		"延滞": "",
		"予約": "なし",
		"紛失": "",
		"窓口館\n/ 資料ID\n/ 書架分類": "●●\n/ 0000000000\n/ Y●●",
		"窓口館": "●●",
		"資料ID": "0000000000",
		"書架分類": "Y●●",
		"備考": "",
		"status": "success"
	},
	{
		"datetime": "2021-07-14T01:11:57.692307+09:00",
		"id": "2",
		"延長": "",
		"書名/シリーズ名/巻次/著者名/出版社名": "■■/■■/■■/■■/■■",
		"書名": "■■",
		〜途中省略〜
	}
	]
	```

### json2alert.py

1. `json2alert.py`を、`bookcheck.sh`が標準出力するJSONを標準入力する形で実行します
2. 返却日までの残り時間が12時間未満の本の書名がJSONから抽出され (例: 返却日が「7月15日」の本は7月14日12:00以降から抽出対象になる)、音声アナウンス向けにまとめられたものが標準出力されます
	```
	$ export LIBLIB_USERNAME='★★'
	$ export LIBLIB_PASSWORD='☆☆'
	$ ./book2json.py | ./json2alert.py 
	図書館の次の本、2冊が返却期限です！ 1冊目、『●●』。2冊目、『■■』。以上です。
	```

### bookcheck_sample.sh

`book2json.py`と`json2alert.py`を組み合わせて起動するbashスクリプトのサンプルです。

私の家では、`json2alert.py`の標準出力を音声として、部屋のスマートスピーカーに喋らせるために別のスクリプトを呼び出しており、そのまんまの内容を本サンプルにしています。この点ご留意ください。

## AUTHOR

大久保 正彦 (Masahiko OHKUBO)
