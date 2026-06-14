# Discord NG Word Manager Bot

サーバーごとにNGワードを設定し、使用したユーザーに対して自動でペナルティ（ミュート、キック、BAN）を科すことができるDiscord Botです。Botの権限が不足している場合の「代替措置（メッセージ即時削除）」機能や、多言語対応（日本語/英語）を備えています。

自身でホストすることを想定していますが、  
製作者:kyonshiがホストしている[Discord BOT](https://discord.com/oauth2/authorize?client_id=1515005326728888400&permissions=8&integration_type=0&scope=bot+applications.commands)を利用することもできます。

(おそらく問題ありませんが動作についての保証はしません。また管理者権限の受け入れが必要です。)

## ✨ 主な機能

* **個別NGワード設定**: ユーザーごとにNGワードを設定可能（サーバー管理者が1〜10個の間で上限を設定可能）。
* **自動ペナルティ適用**: NGワードを検知した際、サーバー管理者が設定したペナルティ（タイムアウト、キック、BAN）を自動で実行します。
* **権限不足時の代替措置（フォールバック）**: Botの権限不足によりタイムアウト等のペナルティが実行できない場合、指定期間中そのユーザーのメッセージを即時削除する代替措置に切り替えることができます。
* **ゲーム除外機能**: 特定のユーザーをNGワード判定やペナルティの対象外（nogame）に設定可能です。
* **多言語対応**: サーバーの優先言語設定に基づいて、メッセージを日本語または英語で表示します。

## ⚙️ 必須環境

* Python 3.10 以上

## 🚀 セットアップ方法

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/kyonshi0104/discord_NGWordGameBot.git
   cd discord_NGWordGameBot
   ```

2. **依存ライブラリのインストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **環境変数の設定**
   プロジェクトのルートディレクトリに `.env` ファイルを作成し、Botのトークンを記述します。
   ```env
   DISCORD_BOT_TOKEN=your_bot_token_here
   ```

4. **ディレクトリとファイルの準備**
   本BotはデータをJSONファイルとして保存します。実行前に `locales` ディレクトリを作成し、同梱の `locales.json` を配置してください。(`data` ディレクトリおよび各種保存用JSONファイルは実行時に自動生成されます。)

5. **Discord Developer Portal の設定**
   Botがメッセージの内容を読み取るため、Discord Developer Portal の Bot 設定画面にて **「Message Content Intent」** を有効（ON）にしてください。

6. **Botの起動**
   ```bash
   python main.py
   ```

## 📜 コマンド一覧

すべてのコマンドはスラッシュコマンド（`/`）として提供されます。

| コマンド | 説明 | 権限 |
| --- | --- | --- |
| `/ngwords_set [words]` | NGワードを登録します。 | 一般 |
| `/ngwords_unset [words]` | 登録したNGワードを削除します。 | 一般 |
| `/ngwords_list` | 自分が登録しているNGワードの一覧を表示します。 | 一般 |
| `/game_status` | 現在のNGワード登録数、サーバーのペナルティ設定などを確認します。 | 一般 |
| `/ngwords_max_setting [limit]` | 1ユーザーあたりのNGワード登録上限（1〜10）を設定します。 | 管理者 |
| `/game_penalty [penalty] [duration]` | NGワード検知時のペナルティ（mute, kick, ban）を設定します。 | 管理者 |
| `/game_fallback_setting [enable]` | 権限不足時の代替タイムアウト措置（メッセージ即時削除）の有効/無効を切り替えます。 | 管理者 |
| `/game_exclude [user]` | 特定のユーザーをNGワードゲームの対象から除外します。 | 管理者 |

## ⚠️ 運用上の注意点（管理者向け）

* **データのバックアップについて**
  Botの設定データ（NGワード、ペナルティ設定等）はすべて `data/` フォルダ内のJSONファイルに保存されます。ファイル書き込み時の不慮のクラッシュ等によるデータ消失を防ぐため、定期的なバックアップ（cron等での自動コピー）を推奨します。
* **レート制限（Rate Limit）への警戒**
  代替措置（メッセージ即時削除）が有効な状態において、対象ユーザーが外部ツール等を用いて超高速でメッセージを連投した場合、BotがDiscord APIのレート制限（Rate Limit）に抵触する恐れがあります。極端な荒らし行為が発生した場合は、手動でのキックやBANなどの対応を行ってください。

## 📄 ライセンス

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
