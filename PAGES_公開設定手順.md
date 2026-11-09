# GitHubへの登録・公開手順

## 1. 新しいリポジトリを作る

GitHub [New repository](https://github.com/new) にアクセスし、次の設定で作成してください。

- Owner：`TSTA-0909`
- Repository name：`ts-utility-media-processor-portfolio`
- Visibility：**Private**（最初は非公開）
- **Add a README file**：ON（GitHub側で初期ブランチを作るため）

以前の `ts-utility-media-processor`（元アプリの非公開開発リポジトリ）とは別のリポジトリです。**元の開発リポジトリをPublicにはしないでください。**

## 2. ファイルをアップロード

リポジトリの作成後、このパッケージ直下の `UPLOAD_TO_GITHUB_WINDOWS.cmd` をダブルクリックすると、Gitを使って公開用27ファイルを **Privateリポジトリのmainブランチにアップロード** できます。実行前にファイル内容を確認してください。

Webから自分でアップロードする場合は、ZIPを解凍し、中にある `docs/`・`src/`・`tests/` などをルートへ配置してください。ZIP本体を1ファイルとしてアップロードしてもサイトは動きません。

## 3. 非公開のまま確認

GitHub上で `README.md`、`docs/index.html`、Pythonソースやテスト、GitHub Actionsの成功を確認します。必要に応じて内容を調整します。

## 4. 公開する

ユーザーが内容を確認して問題なければ、`Settings` → `General` → `Danger Zone` → `Change repository visibility` から `Public` に変更します。

次に `Settings` → `Pages` → `Deploy from a branch` → `main` / `/docs` → `Save` を選択。

公開後の予定URL：

- 紹介・体験： https://tsta-0909.github.io/ts-utility-media-processor-portfolio/
- ソース： https://github.com/TSTA-0909/ts-utility-media-processor-portfolio

公開後にChromeのシークレットウィンドウなどで操作し、画像・診断・リンクが正常に表示されることを確認してください。
