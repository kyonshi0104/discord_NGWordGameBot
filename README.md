# Discord NG Word Game BOT

サーバー内で「NGワードゲーム」を遊ぶためのDiscord Botです。各ユーザーが他人に言わせたいNGワードを設定し、それを発言してしまったプレイヤーに対して自動でペナルティ（ミュート、キック、BAN）を科すことができます。

Botの権限が不足している場合の「代替措置（メッセージ即時削除）」機能や、多言語対応（日本語/英語）を備えています。

自身でホストすることを想定していますが、  
製作者:kyonshiがホストしている[Discord BOT](https://discord.com/oauth2/authorize?client_id=1515005326728888400&permissions=8&integration_type=0&scope=bot+applications.commands)を利用することもできます。

(動作についての保証はしません。また管理者権限の受け入れが必要です。)

## ✨ 主な機能

* **ゲーム用NGワード設定**: 各プレイヤーが他人に言わせたいNGワードを設定可能（サーバー管理者が1〜10個の間で1人あたりの上限を設定可能）。
* **自動ペナルティ適用**: チャット中に自分のNGワードを発言したプレイヤーを自動検知。設定されたペナルティ（タイムアウト、キック、BAN）を実行します。
* **権限不足時の代替措置（フォールバック）**: Botの権限不足によりタイムアウト等のペナルティが実行できない場合、指定期間中そのユーザーのメッセージを即時削除する代替措置（事実上の発言禁止状態）に切り替えることができます。
* **ゲーム除外機能**: ゲームに参加しない特定のユーザーや、管理用BotなどをNGワード判定・ペナルティの対象外（nogame）に設定可能です。
* **多言語対応**: サーバーの優先言語設定に基づいて、ゲームメッセージを日本語または英語で表示します。

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
   Botがメッセージの内容を読み取ってNGワードを判定するため、Discord Developer Portal の Bot 設定画面にて **「Message Content Intent」** を有効（ON）にしてください。

6. **Botの起動**
   ```bash
   python main.py
   ```

## 📜 コマンド一覧

すべてのコマンドはスラッシュコマンド（`/`）として提供されます。

| コマンド | 説明 | 権限 |
| --- | --- | --- |
| `/ngwords_set [words]` | 他のプレイヤーに言わせたいNGワードを登録します。 | 一般 |
| `/ngwords_unset [words]` | 登録したNGワードを取り消します。 | 一般 |
| `/ngwords_list` | 自分が誰に対して何のワードを仕掛けているか（登録一覧）を表示します。 | 一般 |
| `/game_status` | 自分が仕掛けられているNGワードの数や、サーバーのペナルティ設定、ゲーム状況を確認します。 | 一般 |
| `/ngwords_max_setting [limit]` | 1ユーザーあたりが登録できるNGワードの上限（1〜10）を設定します。 | 管理者 |
| `/game_penalty [penalty] [duration]` | NGワードを言った（脱落した）プレイヤーへのペナルティ（mute, kick, ban）を設定します。 | 管理者 |
| `/game_fallback_setting [enable]` | 権限不足時の代替タイムアウト措置（メッセージ即時削除）の有効/無効を切り替えます。 | 管理者 |
| `/game_exclude [user]` | 特定のユーザー（不参加者やBotなど）をゲームの対象から除外します。 | 管理者 |

## ⚠️ 運用上の注意点（管理者向け）

* **データのバックアップについて**
  Botのゲーム進行データや設定はすべて `data/` フォルダ内のJSONファイルに保存されます。ファイル書き込み時の不慮のクラッシュ等によるデータ破損を防ぐため、定期的なバックアップ（cron等での自動コピー）を推奨します。
* **レート制限（Rate Limit）への警戒**
  代替措置（メッセージ即時削除）が有効な状態において、脱落したユーザーが外部ツール等を用いて超高速でメッセージを連投した場合、BotがDiscord APIのレート制限（Rate Limit）に抵触する恐れがあります。極端な荒らし行為が発生した場合は、手動でのキックやBANなどの対応を行ってください。

## 📄 ライセンス

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.