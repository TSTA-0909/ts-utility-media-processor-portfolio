# 公開したPythonの実装部分

このフォルダには、実際のWindowsアプリから選定したPythonモジュールを掲載しています。ポートフォリオ向けに全面的な書き換えをした実装例ではなく、提供された最新版コードからの抜粋です。

| ソース | 主な処理 |
|---|---|
| `image_engine.py` | Pillowによる画像の縮小・画像補正、PDF最適化 |
| `conversion_engine.py` | JPEG/PNG/TIFF/PDFの形式変換・画像統合 |
| `processing_presets.py` | 用途別のサイズ・品質・DPI設定 |
| `quality_diagnosis.py` | 設定値と削減率に基づく印刷適性のルール評価 |
| `pdf_optimization_diagnosis.py` | PDF内容の特徴を抽出して用途別の設定を判断する関数 |
| `video_engine.py` | FFmpeg処理条件、ファイル名の競合回避（試作段階） |

## 注意点

- ブラウザ体験の画像は、`image_engine.py` の処理結果を事前生成したものです。GitHub PagesでPythonを実行しているわけではありません。
- 「AI診断」の表示はローカルの判定ロジックであり、外部LLMや画像認識モデルによる評価ではありません。
- 元アプリのTkinter GUI・DocuWorks専用部品・その他の業務固有コードは公開対象から除外しています。実際の画面は `docs/assets/native-*.png` に掲載しています。
- 本コードの `resize_image` は指定された固定サイズに変換します。元画像の比率が異なる場合、縦横比が変化する可能性があります。例示する架空画像はプリセットと同じ比率です。
- すべての入力への対応・Windows実機での全機能検証は保証していません。変更・再利用の前に要件と動作を確認してください。
