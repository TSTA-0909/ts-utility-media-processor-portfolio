# -*- coding: utf-8 -*-
"""Format conversion helpers for TS Utility - Image Processor.

This module owns format-conversion mechanics. UI state and workflow decisions
remain in image_resizer.py. New output formats can be attached here without
expanding OptimizerApp responsibilities.
"""
from pathlib import Path
import io
import shutil
from PIL import Image, ImageOps, ImageSequence

try:
    import pymupdf
except ImportError:
    pymupdf = None


def _rgb_with_white_background(image):
    image = ImageOps.exif_transpose(image)
    if image.mode == "RGB":
        return image
    if image.mode == "L":
        return image.convert("RGB")
    background = Image.new("RGB", image.size, "white")
    alpha = image.getchannel("A") if "A" in image.getbands() else None
    background.paste(image, mask=alpha)
    return background


def _resize_for_preset(image, max_width=None, max_height=None):
    working = ImageOps.exif_transpose(image).copy()
    if max_width and max_height and (working.width > max_width or working.height > max_height):
        working.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return working


def _optimized_stream_for_pdf(source, max_width=None, max_height=None, jpeg_quality=88):
    """Return optimized image bytes for embedding in a PDF page."""
    with Image.open(source) as image:
        working = _resize_for_preset(image, max_width, max_height)
        output = io.BytesIO()
        if source.suffix.lower() in {".jpg", ".jpeg"}:
            convert = _rgb_with_white_background(working)
            convert.save(output, "JPEG", quality=max(1, min(100, int(jpeg_quality))), optimize=True, progressive=True, subsampling=1)
        else:
            working.save(output, "PNG", optimize=True, compress_level=9)
        return output.getvalue(), working.size


def images_to_single_pdf(images, destination, max_width=None, max_height=None, jpeg_quality=88):
    """Optimize source images for the selected use and place them on A4 pages."""
    if pymupdf is None:
        raise RuntimeError("PyMuPDF is required for PDF conversion.")
    doc = pymupdf.open()
    try:
        a4_portrait = pymupdf.paper_rect("a4")
        for source in images:
            image_bytes, (width, height) = _optimized_stream_for_pdf(source, max_width, max_height, jpeg_quality)
            landscape = width > height
            page_rect = (
                pymupdf.Rect(0, 0, a4_portrait.height, a4_portrait.width)
                if landscape else pymupdf.Rect(a4_portrait)
            )
            page = doc.new_page(width=page_rect.width, height=page_rect.height)
            margin = 18
            target = pymupdf.Rect(margin, margin, page_rect.width - margin, page_rect.height - margin)
            page.insert_image(target, stream=image_bytes, keep_proportion=True)
        doc.save(destination, garbage=4, deflate=True, clean=True)
    finally:
        doc.close()


def jpeg_to_png(source, destination, max_width=None, max_height=None):
    with Image.open(source) as image:
        working = _resize_for_preset(image, max_width, max_height)
        working.convert("RGB").save(destination, "PNG", optimize=True, compress_level=9)


def png_to_jpeg(source, destination, quality=88, max_width=None, max_height=None):
    with Image.open(source) as image:
        working = _resize_for_preset(image, max_width, max_height)
        rgb = _rgb_with_white_background(working)
        rgb.save(
            destination,
            "JPEG",
            quality=max(1, min(100, int(quality))),
            optimize=True,
            progressive=True,
            subsampling=1,
        )






def optimize_tiff(source, destination, max_width=None, max_height=None):
    """TIFF → TIFF optimization while preserving multiple frames/pages."""
    frames = []
    dpi = None
    with Image.open(source) as image:
        dpi = image.info.get("dpi")
        for frame in ImageSequence.Iterator(image):
            working = frame.copy()
            # TIFF orientation tags can exist per-frame.
            try:
                working = ImageOps.exif_transpose(working)
            except Exception:
                pass
            if max_width and max_height and (working.width > max_width or working.height > max_height):
                working.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            # Preserve useful native modes; normalize exotic modes.
            if working.mode not in {"1", "L", "P", "RGB", "RGBA", "CMYK", "I;16"}:
                working = working.convert("RGB")
            frames.append(working.copy())
    if not frames:
        raise ValueError("TIFF内に画像ページがありません。")
    kwargs = {
        "format": "TIFF",
        "save_all": True,
        "append_images": frames[1:],
        "compression": "tiff_deflate",
    }
    if dpi and isinstance(dpi, tuple) and len(dpi) >= 2:
        kwargs["dpi"] = dpi[:2]
    frames[0].save(destination, **kwargs)


def image_to_tiff(source, destination, max_width=None, max_height=None):
    with Image.open(source) as image:
        working = _resize_for_preset(image, max_width, max_height)
        # TIFF supports alpha, grayscale and RGB; preserve mode where practical.
        working.save(destination, "TIFF", compression="tiff_deflate")


def tiff_to_png(source, destination, max_width=None, max_height=None):
    with Image.open(source) as image:
        working = _resize_for_preset(image, max_width, max_height)
        working.save(destination, "PNG", optimize=True, compress_level=9)


def tiff_to_jpeg(source, destination, quality=88, max_width=None, max_height=None):
    with Image.open(source) as image:
        working = _resize_for_preset(image, max_width, max_height)
        rgb = _rgb_with_white_background(working)
        rgb.save(
            destination, "JPEG",
            quality=max(1, min(100, int(quality))),
            optimize=True, progressive=True, subsampling=1,
        )


def pdf_to_multipage_tiff(source, destination, dpi):
    if pymupdf is None:
        raise RuntimeError("PyMuPDF is required for PDF conversion.")
    frames = []
    with pymupdf.open(source) as doc:
        if doc.needs_pass:
            raise ValueError(f"パスワード付きPDFには対応していません: {Path(source).name}")
        for page in doc:
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            frame = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            frames.append(frame)
    if not frames:
        raise ValueError("TIFFへ変換するPDFページがありません。")
    first, *rest = frames
    first.save(
        destination, "TIFF",
        save_all=True, append_images=rest,
        compression="tiff_deflate", dpi=(dpi, dpi),
    )


def optimize_png(source, destination, max_width, max_height):
    """Format-preserving PNG optimization for automatic optimization mode."""
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)
        working = image.copy()
        if max_width and max_height and (working.width > max_width or working.height > max_height):
            working.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        working.save(destination, "PNG", optimize=True, compress_level=9)
    try:
        # Only keep original bytes when no resize occurred and recompression was not useful.
        with Image.open(source) as original:
            original = ImageOps.exif_transpose(original)
            resized = bool(max_width and max_height and (original.width > max_width or original.height > max_height))
        if not resized and destination.stat().st_size >= source.stat().st_size:
            shutil.copy2(source, destination)
    except OSError:
        pass


def png_to_png(source, destination):
    """Losslessly optimize PNG while preserving transparency and dimensions.

    If Pillow's optimized output is not smaller, keep the original bytes so
    PNG optimization never increases the file size.
    """
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)
        image.save(destination, "PNG", optimize=True, compress_level=9)
    try:
        if destination.stat().st_size >= source.stat().st_size:
            shutil.copy2(source, destination)
    except OSError:
        pass


def image_to_individual_pdf(source, destination, max_width=None, max_height=None, jpeg_quality=88):
    """Create one automatically optimized PDF from one image."""
    images_to_single_pdf([source], destination, max_width, max_height, jpeg_quality)


def render_pdf_page(page, destination, dpi, image_format, jpeg_quality=90):
    """Render one PDF page to JPEG or PNG."""
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    png_bytes = pix.tobytes("png")
    if image_format == "PNG":
        destination.write_bytes(png_bytes)
        return
    with Image.open(io.BytesIO(png_bytes)) as image:
        image.convert("RGB").save(
            destination,
            "JPEG",
            quality=max(1, min(100, int(jpeg_quality))),
            optimize=True,
            subsampling=1,
        )


def output_folder_name(mode):
    return {
        "jpeg_to_jpeg": "JPEG_lightweight",
        "jpeg_to_png": "JPEG_to_PNG",
        "png_to_jpeg": "PNG_to_JPEG",
        "png_to_png": "PNG_optimized",
        "jpeg_to_pdf_each": "JPEG_to_PDF_each",
        "png_to_pdf_each": "PNG_to_PDF_each",
        "pdf_to_jpeg": "PDF_to_JPEG",
        "pdf_to_png": "PDF_to_PNG",
        "jpeg_to_tiff": "JPEG_to_TIFF",
        "png_to_tiff": "PNG_to_TIFF",
        "tiff_to_jpeg": "TIFF_to_JPEG",
        "tiff_to_png": "TIFF_to_PNG",
        "pdf_to_tiff": "PDF_to_TIFF",
    }.get(mode, "converted")


def validate_conversion_request(mode, all_images, all_pdfs, output_dir, pdf_name, overwrite, pdf_available=True):
    if mode in {"images_to_pdf", "jpeg_merge_pdf", "png_merge_pdf", "mixed_merge_pdf", "jpeg_to_pdf_each", "png_to_pdf_each", "pdf_to_jpeg", "pdf_to_png", "pdf_to_tiff"} and not pdf_available:
        raise ValueError("PDF変換機能に必要なPyMuPDFがありません。BUILD_EXE.cmdを実行して作り直してください。")
    if mode in {"images_to_pdf", "jpeg_merge_pdf", "png_merge_pdf", "mixed_merge_pdf"}:
        if mode == "jpeg_merge_pdf":
            targets = [p for p in all_images if p.suffix.lower() in {".jpg", ".jpeg"}]
            missing = "まとめるJPEGがありません。"
        elif mode == "png_merge_pdf":
            targets = [p for p in all_images if p.suffix.lower() == ".png"]
            missing = "まとめるPNGがありません。"
        else:
            targets = list(all_images)
            missing = "PDFにまとめるJPEG・PNGがありません。"
        if not targets:
            raise ValueError(missing)
        if mode in {"jpeg_merge_pdf", "png_merge_pdf"} and len(targets) < 2:
            raise ValueError("『まとめて』は2枚以上の画像を選択してください。1枚だけなら画像形式変換のPDF化を使ってください。")
        if mode == "mixed_merge_pdf":
            exts = {p.suffix.lower() for p in targets}
            has_jpeg = bool(exts & {".jpg", ".jpeg"}); has_png = ".png" in exts
            if not (has_jpeg and has_png):
                raise ValueError("JPEG・PNG（複合）では、JPEGとPNGを両方1枚以上選択してください。")
        name = (pdf_name or "まとめ画像.pdf").strip() or "まとめ画像.pdf"
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        return mode, targets, [], output_dir, name, overwrite
    if mode in {"pdf_to_jpeg", "pdf_to_png", "pdf_to_tiff"}:
        if not all_pdfs:
            target = {"pdf_to_jpeg":"JPEG", "pdf_to_png":"PNG", "pdf_to_tiff":"TIFF"}[mode]
            raise ValueError(f"{target}に変換するPDFがありません。")
        return mode, all_images, all_pdfs, output_dir, "", overwrite
    if mode in {"jpeg_to_jpeg", "jpeg_to_png", "jpeg_to_pdf_each", "jpeg_to_tiff"}:
        targets = [p for p in all_images if p.suffix.lower() in {".jpg", ".jpeg"}]
        if not targets:
            raise ValueError("処理対象のJPEGファイルがありません。")
        return mode, targets, [], output_dir, "", overwrite
    if mode in {"png_to_jpeg", "png_to_png", "png_to_pdf_each", "png_to_tiff"}:
        targets = [p for p in all_images if p.suffix.lower() == ".png"]
        if not targets:
            raise ValueError("処理対象のPNGファイルがありません。")
        return mode, targets, [], output_dir, "", overwrite
    if mode in {"tiff_to_jpeg", "tiff_to_png"}:
        targets = [p for p in all_images if p.suffix.lower() in {".tif", ".tiff"}]
        if not targets:
            raise ValueError("処理対象のTIFFファイルがありません。")
        return mode, targets, [], output_dir, "", overwrite
    raise ValueError("変換モードを確認してください。")


def run_conversion_job(
    *, mode, images, pdfs, output_dir, pdf_name, overwrite,
    image_preset, pdf_preset, enhancement_mode,
    unique_destination, resize_image, messages,
):
    """Run one conversion job and publish progress/result messages."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if mode in {"images_to_pdf", "jpeg_merge_pdf", "png_merge_pdf", "mixed_merge_pdf"}:
        destination = unique_destination(output_dir / pdf_name, overwrite)
        messages.put(("total", (len(images), len(images), 0)))
        before = sum(p.stat().st_size for p in images)
        width, height, quality, _ = image_preset
        images_to_single_pdf(images, destination, width, height, quality)
        after = destination.stat().st_size
        for index, source in enumerate(images, 1):
            messages.put(("log", f"PDFへ追加: {index}/{len(images)}  {source.name}"))
            messages.put(("progress", (index, len(images), index, 0, 0)))
        merge_label = {
            "jpeg_merge_pdf": "JPEG（複数）→ PDF（1つ）",
            "png_merge_pdf": "PNG（複数）→ PDF（1つ）",
            "mixed_merge_pdf": "JPEG・PNG（複合）→ PDF（1つ）",
        }.get(mode, "JPEG・PNG → PDF")
        messages.put(("conversion_done", (len(images), 0, before, after, output_dir, destination, merge_label)))
        return

    if mode in {"jpeg_to_pdf_each", "png_to_pdf_each"}:
        target_dir = output_dir / output_folder_name(mode)
        target_dir.mkdir(parents=True, exist_ok=True)
        messages.put(("total", (len(images), len(images), 0)))
        before = sum(p.stat().st_size for p in images)
        produced = []
        width, height, quality, _ = image_preset
        label = "JPEG → PDF（1枚ずつ）" if mode == "jpeg_to_pdf_each" else "PNG → PDF（1枚ずつ）"
        for index, source in enumerate(images, 1):
            destination = unique_destination(target_dir / f"{source.stem}.pdf", overwrite)
            image_to_individual_pdf(source, destination, width, height, quality)
            produced.append(destination)
            messages.put(("log", f"個別PDF変換: {source.name} → {destination.name}"))
            messages.put(("progress", (index, len(images), index, 0, 0)))
        after = sum(p.stat().st_size for p in produced if p.exists())
        messages.put(("conversion_done", (len(images), 0, before, after, target_dir, None, label)))
        return

    if mode in {"pdf_to_jpeg", "pdf_to_png", "pdf_to_tiff"}:
        if pymupdf is None:
            raise RuntimeError("PDF変換機能に必要なPyMuPDFがありません。")
        if mode == "pdf_to_tiff":
            messages.put(("total", (len(pdfs), 0, len(pdfs))))
            before = sum(p.stat().st_size for p in pdfs)
            dpi, quality, _ = pdf_preset
            produced = []
            for index, source in enumerate(pdfs, 1):
                target_dir = output_dir / output_folder_name(mode)
                target_dir.mkdir(parents=True, exist_ok=True)
                destination = unique_destination(target_dir / f"{source.stem}.tif", overwrite)
                pdf_to_multipage_tiff(source, destination, dpi)
                produced.append(destination)
                messages.put(("log", f"TIFF変換: {source.name} → {destination.name}"))
                messages.put(("progress", (index, len(pdfs), index, 0, 0)))
            after = sum(p.stat().st_size for p in produced if p.exists())
            messages.put(("conversion_done", (len(pdfs), len(pdfs), before, after, target_dir, None, "PDF → TIFF")))
            return
        page_total = 0
        for source in pdfs:
            with pymupdf.open(source) as doc:
                page_total += doc.page_count
        messages.put(("total", (page_total, 0, len(pdfs))))
        dpi, quality, _ = pdf_preset
        jpeg_quality = max(quality, 88)
        completed = 0
        before = sum(p.stat().st_size for p in pdfs)
        produced = []
        target_format = "JPEG" if mode == "pdf_to_jpeg" else "PNG"
        extension = ".jpg" if mode == "pdf_to_jpeg" else ".png"
        for source in pdfs:
            target_dir = output_dir / f"{source.stem}_{target_format}"
            target_dir.mkdir(parents=True, exist_ok=True)
            with pymupdf.open(source) as doc:
                if doc.needs_pass:
                    raise ValueError(f"パスワード付きPDFには対応していません: {source.name}")
                for page_no, page in enumerate(doc, 1):
                    destination = unique_destination(target_dir / f"page_{page_no:03d}{extension}", overwrite)
                    render_pdf_page(page, destination, dpi, target_format, jpeg_quality)
                    produced.append(destination)
                    completed += 1
                    messages.put(("log", f"{target_format}変換: {source.name} / {page_no}ページ → {destination.name}"))
                    messages.put(("progress", (completed, page_total, completed, 0, 0)))
        after = sum(p.stat().st_size for p in produced if p.exists())
        messages.put(("conversion_done", (completed, len(pdfs), before, after, output_dir, None, f"PDF → {target_format}")))
        return

    target_dir = output_dir / output_folder_name(mode)
    target_dir.mkdir(parents=True, exist_ok=True)
    width, height, quality, _ = image_preset
    messages.put(("total", (len(images), len(images), 0)))
    before = sum(p.stat().st_size for p in images)
    produced = []
    operation = "画像変換"
    for index, source in enumerate(images, 1):
        if mode == "jpeg_to_jpeg":
            destination = unique_destination(target_dir / f"{source.stem}.jpg", overwrite)
            resize_image(source, destination, width, height, quality, enhancement_mode)
            operation = "JPEG → JPEG（軽量化）"
        elif mode == "jpeg_to_png":
            destination = unique_destination(target_dir / f"{source.stem}.png", overwrite)
            jpeg_to_png(source, destination, width, height)
            operation = "JPEG → PNG"
        elif mode == "png_to_jpeg":
            destination = unique_destination(target_dir / f"{source.stem}.jpg", overwrite)
            png_to_jpeg(source, destination, quality=max(quality, 82), max_width=width, max_height=height)
            operation = "PNG → JPEG"
        elif mode == "png_to_png":
            destination = unique_destination(target_dir / f"{source.stem}.png", overwrite)
            optimize_png(source, destination, width, height)
            operation = "PNG → PNG（可逆最適化）"
        elif mode == "jpeg_to_tiff":
            destination = unique_destination(target_dir / f"{source.stem}.tif", overwrite)
            image_to_tiff(source, destination, width, height)
            operation = "JPEG → TIFF"
        elif mode == "png_to_tiff":
            destination = unique_destination(target_dir / f"{source.stem}.tif", overwrite)
            image_to_tiff(source, destination, width, height)
            operation = "PNG → TIFF"
        elif mode == "tiff_to_jpeg":
            destination = unique_destination(target_dir / f"{source.stem}.jpg", overwrite)
            tiff_to_jpeg(source, destination, quality=max(quality, 82), max_width=width, max_height=height)
            operation = "TIFF → JPEG"
        elif mode == "tiff_to_png":
            destination = unique_destination(target_dir / f"{source.stem}.png", overwrite)
            tiff_to_png(source, destination, width, height)
            operation = "TIFF → PNG"
        else:
            raise ValueError("画像変換モードを確認してください。")
        produced.append(destination)
        messages.put(("log", f"変換: {source.name} → {destination.name}"))
        messages.put(("progress", (index, len(images), index, 0, 0)))
    after = sum(p.stat().st_size for p in produced if p.exists())
    messages.put(("conversion_done", (len(images), 0, before, after, target_dir, None, operation)))
