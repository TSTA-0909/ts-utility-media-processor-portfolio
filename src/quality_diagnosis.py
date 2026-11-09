# -*- coding: utf-8 -*-
from processing_presets import IMAGE_PRESETS, PDF_PRESETS, DEFAULT_PDF_PRESET

def stars(score):
    score = max(1, min(5, int(round(score))))
    return "★" * score + "☆" * (5 - score)

def build_print_quality_diagnosis(
    image_count=0, pdf_count=0, image_preset_name=None, pdf_preset_name=None,
    enhancement_name=None, reduction=0, operation="optimize"
):
    text_score = drawing_score = photo_score = 3.0
    reasons = []

    if operation == "images_to_pdf":
        text_score, drawing_score, photo_score = 5.0, 5.0, 5.0
        reasons.append("元画像を再圧縮せずPDFへ直接配置しているため、変換だけで文字や罫線が崩れにくい構成です。")
    elif operation in {"pdf_to_jpeg", "pdf_to_png"}:
        dpi, quality, _ = PDF_PRESETS.get(pdf_preset_name, PDF_PRESETS[DEFAULT_PDF_PRESET])
        if dpi >= 300:
            text_score, drawing_score, photo_score = 5.0, 5.0, 5.0
        elif dpi >= 200:
            text_score, drawing_score, photo_score = 5.0, 4.0, 4.0
        elif dpi >= 150:
            text_score, drawing_score, photo_score = 4.0, 4.0, 4.0
        else:
            text_score, drawing_score, photo_score = 4.0, 3.0, 3.0
        target = "JPEG" if operation == "pdf_to_jpeg" else "PNG"
        quality_note = f"・JPEG品質{quality}" if target == "JPEG" else ""
        reasons.append(f"PDFを{dpi}dpi{quality_note}で{target}画像化する設定です。")
    else:
        scores = []
        if image_count and image_preset_name in IMAGE_PRESETS:
            width, height, quality, _ = IMAGE_PRESETS[image_preset_name]
            long_side = max(width, height)
            if "推奨・最軽量" in image_preset_name:
                s = (4.0, 3.5, 3.5)
                reasons.append("最軽量画像設定は社内資料への貼付印刷を想定した実用優先の設定です。")
            elif long_side >= 2000:
                s = (5.0, 5.0, 5.0)
            elif long_side >= 1500:
                s = (5.0, 4.5, 4.5)
            elif long_side >= 1000:
                s = (4.5, 4.0, 4.0)
            else:
                s = (4.0, 3.5, 3.5)
            scores.append(s)
            reasons.append(f"画像は{width}×{height}px基準・JPEG品質{quality}で処理しています。")

        if pdf_count and pdf_preset_name in PDF_PRESETS:
            dpi, quality, _ = PDF_PRESETS[pdf_preset_name]
            if dpi >= 300:
                s = (5.0, 5.0, 5.0)
            elif dpi >= 200:
                s = (5.0, 4.5, 4.0)
            elif dpi >= 150:
                s = (4.5, 4.0, 3.5)
            else:
                s = (4.0, 3.5, 3.0)
            scores.append(s)
            reasons.append(f"PDFは{dpi}dpi基準で画像部分を最適化し、文字・ベクター線は可能な限り維持します。")

        if scores:
            text_score = sum(s[0] for s in scores) / len(scores)
            drawing_score = sum(s[1] for s in scores) / len(scores)
            photo_score = sum(s[2] for s in scores) / len(scores)

        if enhancement_name == "図面・文字優先":
            text_score = min(5, text_score + 0.5)
            drawing_score = min(5, drawing_score + 0.5)
            reasons.append("図面・文字優先の強調で、細線と文字の視認性を補っています。")
        elif enhancement_name == "境界線・テープ優先（おすすめ）":
            drawing_score = min(5, drawing_score + 0.25)
            reasons.append("境界線・マーキング色の視認性を補う設定です。")

        if reduction >= 90:
            photo_score = max(1, photo_score - 0.5)
            reasons.append("削減率が非常に高いため、背景や細かな写真部分には圧縮感が出る場合があります。")

    overall = min(text_score, drawing_score, photo_score)
    if overall >= 4.5:
        verdict = "高品質印刷まで期待できる設定です。"
    elif overall >= 3.0:
        verdict = "一般的な社内資料・帳票の印刷なら実用範囲の目安です。"
    else:
        verdict = "画面確認・軽量共有向けです。細部が重要な印刷は標準以上の設定も比較してください。"

    return (
        f"総合判定：{verdict}\n"
        f"文字　{stars(text_score)}\n"
        f"図面・罫線　{stars(drawing_score)}\n"
        f"写真　{stars(photo_score)}\n"
        + " ".join(reasons)
        + "\n※設定・解像度・圧縮率から算出する目安です。プリンター・用紙・原稿品質によって実際の印刷結果は変わります。"
    )
