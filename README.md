# TS Utility Media Processor｜Python開発ポートフォリオ

> **Python × 現場業務改善 × 画像・PDFの処理・診断**  
> Terakoya Systems が実際に開発した Windows 向けメディア処理ユーティリティを、架空データで紹介する採用・技術ポートフォリオです。

## まず体験してみる

**[ブラウザ版の紹介・操作デモを開く](https://tsta-0909.github.io/ts-utility-media-processor-portfolio/)**

インストール不要。次の順序で操作できます。

1. **用途を選ぶ**：社内提出／メール／報告書／画面確認を切り替える
2. **容量を比較する**：元画像と実際のPython処理後の容量の違いを見る
3. **画質を比較する**：スライダー・拡大表示で細部の変化を見る
4. **判断理由を読む**：元アプリのローカル診断ロジックによる設定・印刷適性の説明を確認する
5. **PDFの判定を試す**：架空のPDF特徴量を切り替え、推奨設定が変わる理由を確認する
6. **本物のGUIを見る**：Windowsアプリの画面と設計思想を見る

> ブラウザ版は事前にPythonで処理・計算した結果をHTML/CSS/JavaScriptで表示する**展示デモ**です。ブラウザでPythonを動かしたり、外部のサーバーへ任意のファイルを送信したりするものではありません。

## どんな課題を解決したか

現場写真や図面・報告書の圧縮や変換では、「どの形式・設定を使うか」「容量が小さくなる一方で文字や細い線が読み取れるか」を確認する手間がかかります。こうした繰り返し作業に対して、ファイルの種類ではなく**利用目的から選べるUI**、**用途別の処理プリセット**、**変換前後プレビューと理由付きの診断表示**を開発しました。

## 開発範囲と使用技術

| 領域 | 技術・実装例 | 公開範囲 |
|---|---|---|
| Python画像処理 | Pillow / 画質・サイズ・色補正 | [src/image_engine.py](src/image_engine.py) |
| 形式変換・PDF | Pillow / PyMuPDF / JPEG・PNG・TIFF・PDF | [src/conversion_engine.py](src/conversion_engine.py) |
| 自動設定 | 用途別プリセット（画素数・品質・DPI） | [src/processing_presets.py](src/processing_presets.py) |
| ローカル判定 | 設定値を使う画質評価のルール | [src/quality_diagnosis.py](src/quality_diagnosis.py) |
| PDF推奨設定 | PDF特徴量の分析・ルール判定 | [src/pdf_optimization_diagnosis.py](src/pdf_optimization_diagnosis.py) |
| 動画（試作） | FFmpeg実行条件・競合しない出力名生成 | [src/video_engine.py](src/video_engine.py) |
| Windows GUI | Tkinter / Windows用統合画面 | [実際の画面](docs/assets/native-hub.png)、[画像処理画面](docs/assets/native-image.png) |
| Web展示 | HTML / CSS / JavaScript（静的サイト） | [docs](docs/) |

このリポジトリは**公開用に選んだ実装部分**であり、元のWindowsアプリ一式ではありません。GUI全体やDocuWorks専用連携は本リポジトリには含めていません。DocuWorks機能は専用のWindows環境が必要、動画は試作段階です。

## 実際の出力（架空画像）

元画像（2400×1680px、約1.04MiB）を元の `image_engine.resize_image` で処理した一例です。

| 用途 | 出力サイズ | 元画像からの削減率 |
|---|---:|---:|
| 社内提出・共有 | 600×420px | 約98.3% |
| メール添付 | 800×560px | 約97.3% |
| 社内報告書 | 1000×700px | 約95.5% |
| 画面確認 | 1600×1120px | 約86.3% |

数値は**比較用に合成した架空画像に対する実測値**。実際の写真や資料で同じ削減率・画質を保証するものではありません。

## 「AI診断」について正確に

元アプリの機能名は「AI診断」ですが、外部生成AIや画像意味認識ではなく、設定・解像度・圧縮率などに基づく**ローカルルール判定**です。公開デモでは `quality_diagnosis.build_print_quality_diagnosis` の出力を実際に保存して表示します。PDF推奨設定のデモは架空特徴量を使ったルールの説明で、ブラウザ上で実PDFを解析するものではありません。

## Pythonコードを動かす

Python 3.11以降を推奨します。

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python tools/run_sample.py
```

サンプル再生成は `output_demo/` にのみ出力し、元画像を上書きしません。GitHub ActionsでもPythonテストとWebデモの文法チェックを実施します。

## 公開前に確認した注意点

- `image_engine.resize_image` は**幅と高さを固定指定**するため、入力画像の縦横比によっては歪む可能性があります。現在の比較画像は同じ比率を使用しています。
- DocuWorks専用機能やGUI・動画機能のWindows実機での完全な動作検証は、この公開デモでは行っていません。
- 作品コードは機能の一部を公開したもので、業務用データ・設定・認証情報を含めない構成です。
- 開発過程では生成AIを補助的に活用し、課題整理・実装・確認・改善を進めています。

## 関連作品

- JavaScript作品：**[TSTA Reserve｜予約管理の体験デモ](https://tsta-0909.github.io/tsta-reserve-portfolio/)**
- Pythonポートフォリオ：**[GitHub Pages](https://tsta-0909.github.io/ts-utility-media-processor-portfolio/)**

© Terakoya Systems. 公開されているコードの利用・再配布については、権利者に確認してください。
