* NOTE

asdf plugin add python
asdf install python 3.10.7
asdf local python 3.10.7

poetry init
poetry shell
poetry add build

git clone https://github.com/mitmproxy/mitmproxy.git
cd mitmproxy
python -m build
pip install dist/mitmproxy-10.0.0.dev0-py3-none-any.whl

$ mitmproxy --version
Mitmproxy: 10.0.0.dev
Python:    3.10.7
OpenSSL:   OpenSSL 3.0.7 1 Nov 2022
Platform:  Linux-5.15.79.1-microsoft-standard-WSL2-x86_64-with-glibc2.27

firefox を起動して「設定」から「ネットワーク設定」を検索して「接続設定...(E)」ボタンを押します。「インターネット接続」画面が表示されるので「手動でプロキシー設定をする(M)」を選択し、「HTTP プロキシー」に localhost 「ポート」に 8080 と入力して OK を押します。

mitmproxy を起動します。一番上の行に「Flows」と表示されるのを確認します。
この時点で Firefox でウェブページにアクセスすると mitmproxy の画面に 00:00:00 HTTP GET mitm.it / 200 text/html のようなログが表示されますが、まだ mitmproy の証明書をインストールしていないので SSL で保護されたページには警告が出てアクセスできません。

Firefox で http://mitm.it/ を開いて Firefox 用の証明書 (mitmproxy-ca-cert.pem) をダウンロードします。

Firefox の「設定」から「証明書」を検索して「証明書を表示...(C)」ボタンを押します。
「あなたの証明書」タブの「インポート(M)...」ボタンを押します。
で証明書をインポートすると「証明書のインポート」画面で「"mitmproy" が行う認証のうち、信頼するものを選択してください。」と聞かれるので「この認証局によるウェブサイトの識別を信頼する」にチェックを入れて「OK」ボタンを押します。

https://google.com/ を開いて URL 欄の鍵アイコンをクリックして安全な接続と表示されている事を確認します。「安全な接続」をクリックすると「認証局」が mitmproxy になっている事が判ります。


POST https://heroes-wb.nextersglobal.com/api/

{
    "calls": [
        {
            "args": {
                "limit": 20,
                "offset": 0,
                "type": "arena"
            },
            "ident": "body",
            "name": "battleGetByType"
        }
    ]
}

{
 "date":1674150687.366961,"results":[ {
   "ident":"body","result": {
     "response": {
       "replays":[ {
         "userId":"24494389","typeId":"24768289","attackers": {
           "7": {
             "id":7,"xp":1491749,"level":97,"color":10,"slots": {
               "2":0,"0":0,"3":0
             }
             ,"skills": {
               "357":97,"358":97,"359":97,"360":97
             }
             ,"power":30644,"star":4,"runes":[3740,3220,3220,3230,3220],"skins": {
               "7":37
             }
             ,"currentSkin":0,"titanGiftLevel":19,"titanCoinsSpent": {
               "consumable": {
                 "24":23530
               }
...



mitmdump --flow-detail 4


## mitmproxy のアドオン作成


https://jsonplaceholder.typicode.com/users


https://docs.mitmproxy.org/stable/addons-overview/

## データベース

tinydb



## パケットについて

ヒーローIDの調べ方

ExpeditionMapPopup: 遠征マップ画面に移動すると各拠点毎の遠征に送り出しているヒーローを含めた情報のパケットが送信される。(packet-30)

expeditionSendHeroes: または開始していない遠征マップ画面の拠点をクリックしてヒーローを選択して開始したときに拠点IDと選択したヒーローの組み合わせで expeditionSendHeroes パケットが送信される。(packet-28)


エイダン、セレステ、クリスタ、ケイラ、アスタロスの場合
(確認画面だと逆に表示される事に注意)

packet-21:
            "heroes": [
              58,
              43,
              34,	クリスタ
              59,
              4
            ],

エイダン、ラース、セレステ、ケイラ、アスタロスの場合

packet-28:
        "heroes": [
          58,
          33,	ラース
          43,
          59,
          4
        ]

エイダン、セレステ、クリスタ、ダンテ、ケイラの場合

packet-32:
        "heroes": [
          58,	エイダン
          43,	セレステ
          34,	クリスタ
          16,	ダンテ
          59	ケイラ
        ]
