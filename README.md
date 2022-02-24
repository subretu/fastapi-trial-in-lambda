# fastapi-trial-in-lambda

## 内容

- FastAPIを使ったToDoアプリをLambdaで実装。
- 実装は下記サイトを参照。
  - https://rightcode.co.jp/tag/fastapi

## LambdaでFastAPIを使うにあたって

- FastAPIをLambdaで使用するには「mangum」を使う必要がある。
  - mangum・・・AWS Lambda＆APIGatewayでASGIアプリケーションを使用するためのアダプタ。
- mangum自体はpipでインストール可能だが、Lambdaではpipの使用ができないため、下記の方法でライブラリーを追加する必要あり。
  - パッケージデプロイ
  - レイヤーで追加
- 今回は「レイヤーで追加」を行い、備忘録も兼ねて下記にまとめた（雑に書いているので清書予定）
  - Lambda Layersを使った追加方法についての記事を作成。
    - https://qiita.com/subretu/items/2a0c40326cc857e63922

### Lambdaレイヤーへの追加方法

- 環境はWindows11
- AmazonLinuxの環境で作成しないといけないらしい
  - ローカルでpipインストールしてzipではダメやった
- WindowsでのDockerのインストール方法は省略
- 下記コマンドを実行
  - requirements.txtに必要なライブラリーを記載しておく
  - 初回だけイメージpullに時間がかかるが、2回目以降はしないので早くなる

```docker
docker run --rm -v "$(PWD):/var/task" lambci/lambda:build-python3.8 pip install -r ./requirements.txt -t python/lib/python3.8/site-packages/
```
- マウント先に「python」フォルダができているのでzipする
- lambda開いて、レイヤーに追加（多分S3経由かな）
    - 「互換性のあるアーキテクチャ」を「x86_64」
    - 「互換性のあるランタイム」を「python3.8」
- lambda関数作成
  - レイヤーに対象レイヤーのARN貼り付ける
    - psycopg2のレイヤーも必要だが、下記を参照に追加
    - https://qiita.com/Bacchus/items/db0750865d1c597e1dc0
  - ハンドラーを「handler」に変更