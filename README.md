# fastapi-trial-in-lambda

FastAPIをLambdaで使用するには「mangum」を使う必要がある。
※mangum・・・AWS Lambda＆APIGatewayでASGIアプリケーションを使用するためのアダプタ。

mangum自体はpipでインストール可能だが、Lambdaではpipの使用ができないため、下記の方法でパッケージを追加する必要あり。

- パッケージデプロイ
- レイヤーで追加

今回は「レイヤーで追加」を行ってみた。
以下、レイヤーへの追加方法だが、備忘録も兼ねて雑に書いているので清書予定。

## Lambdaレイヤーへの追加方法
- 環境はWindows11
- AmazonLinuxの環境で作成しないといけないらしい
  - ローカルでpipインストールしてzipではダメやった
- WindowsでのDockerのインストール方法は省略
- 下記コマンドを実行
  - requirements.txtに必要なモジュールを記載しておく
  - 初回だけイメージpullに時間がかかるが、2回目以降はしないので

```docker
docker run --rm -v "$(PWD):/var/task":/var/task lambci/lambda:build-python3.8 pip install -r ./requirements.txt -t python/lib/python3.8/site-packages/
```
- マウント先に「python」フォルダができているのでzipする
- lambda開いて、レイヤーに追加（多分S3経由かな）
- lambda関数作成
  - レイヤーに対象レイヤーのARN貼り付ける
  - ハンドラーを「handler」に変更