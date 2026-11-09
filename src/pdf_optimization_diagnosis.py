# -*- coding: utf-8 -*-
try:
    import pymupdf
except ImportError:
    pymupdf = None

from processing_presets import PDF_PRESETS, ENHANCEMENT_PROFILES
from image_engine import estimate_pdf_optimized_size


def _sample_files(files, count=5):
    files = list(files)
    if len(files) <= count:
        return files
    return [files[round(i * (len(files) - 1) / (count - 1))] for i in range(count)]


def _sample_page_indices(page_count, count=20):
    if page_count <= count:
        return list(range(page_count))
    return sorted({round(i * (page_count - 1) / (count - 1)) for i in range(count)})


def diagnose_pdf_optimization(files):
    """Fast PDF diagnosis that samples page contents and compression effect.

    Page count is always taken from the complete input set. Visual/content analysis
    and capacity estimation are sampled so very large PDFs do not need a complete
    preflight rewrite before the user can see the result.
    """
    if pymupdf is None:
        raise ValueError("PDF機能に必要なPyMuPDFがありません。")

    files = list(files)
    total = sum(path.stat().st_size for path in files)
    total_pages = 0
    images = drawings = text_chars = inspected_pages = 0

    for source in files:
        try:
            with pymupdf.open(source) as doc:
                total_pages += doc.page_count
        except Exception:
            continue

    for source in _sample_files(files, 5):
        with pymupdf.open(source) as doc:
            for page_index in _sample_page_indices(doc.page_count, 20):
                page = doc[page_index]
                images += len(page.get_images(full=True))
                drawings += len(page.get_drawings())
                text_chars += len(page.get_text("text"))
                inspected_pages += 1

    per_page_images = images / max(inspected_pages, 1)
    per_page_drawings = drawings / max(inspected_pages, 1)
    chars_per_page = text_chars / max(inspected_pages, 1)
    very_dense_drawing = per_page_drawings >= 90 or chars_per_page >= 2600
    drawing_like = per_page_drawings >= 12 or chars_per_page >= 650

    if very_dense_drawing:
        category = "極細字・高密度図面主体"
        recommendation = "細字・求積図用（高精細）"
        reason = (
            "小さな文字や図形が非常に密集しています。標準でも軽量化できますが、"
            "拡大確認や数値判読を優先して高精細設定へ引き上げました。"
        )
    elif drawing_like:
        category = "公図・求積図・細線図面主体"
        recommendation = "図面・公図用（標準）"
        reason = (
            "細い斜線・境界線・小さな数字が多い図面です。最軽量では線がギザつく可能性があるため、"
            "印刷確認で線がきれいに保たれた標準設定をおすすめします。"
        )
    elif chars_per_page < 20 and per_page_images >= 1.0:
        category = "スキャン資料・画像図面主体"
        recommendation = "図面・公図用（標準）"
        reason = (
            "文字情報を持たない画像主体のPDFです。公図・求積図などの細線を守るため、"
            "最軽量ではなく標準設定をおすすめします。"
        )
    elif per_page_images >= 2.5 and chars_per_page < 500 and per_page_drawings < 10:
        category = "現場写真報告書"
        recommendation = "現場写真報告書用（推奨・最軽量）"
        reason = (
            "1ページあたりの写真が多く、文字・図形が少ない写真報告書です。"
            "実機印刷で元資料と遜色が出にくかった最軽量設定をおすすめします。"
        )
    elif per_page_images >= 1.0:
        category = "写真・図面混在資料"
        recommendation = "図面・公図用（標準）"
        reason = "写真だけでなく線・文字も含むため、最軽量よりも線の滑らかさを守れる標準設定をおすすめします。"
    else:
        category = "文字・ベクター主体"
        recommendation = "社内共有用（軽量）"
        reason = "文字・ベクター中心なので、軽量設定でも見た目が変わりにくい構成です。"

    enhancement = (
        "図面・文字優先"
        if category in {"極細字・高密度図面主体", "公図・求積図・細線図面主体", "スキャン資料・画像図面主体", "写真・図面混在資料"}
        else "境界線・テープ優先（おすすめ）"
    )
    enhancement_mode = ENHANCEMENT_PROFILES[enhancement][0]
    dpi, quality, _ = PDF_PRESETS[recommendation]

    estimated_total = 0
    for source in files:
        try:
            estimated_total += estimate_pdf_optimized_size(
                source, dpi, quality, enhancement_mode, max_sample_pages=12
            )
        except Exception:
            estimated_total += source.stat().st_size

    return {
        "count": len(files),
        "total": total,
        "category": category,
        "recommendation": recommendation,
        "enhancement": enhancement,
        "reason": reason,
        "estimated": min(total, estimated_total),
        "pages": total_pages,
        "images": images,
        "drawings": drawings,
        "text_chars": text_chars,
        "inspected_pages": inspected_pages,
    }
