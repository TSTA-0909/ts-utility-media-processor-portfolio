# -*- coding: utf-8 -*-
import io
import os
import shutil
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps, ImageStat
try:
    import pymupdf
except ImportError:
    pymupdf = None

def convert_to_rgb(image):
    if image.mode == "RGB": return image
    if image.mode == "L": return image.convert("RGB")
    background = Image.new("RGB", image.size, "white")
    background.paste(image, mask=image.getchannel("A") if "A" in image.getbands() else None)
    return background

def color_range_mask(image, ranges, min_saturation=70, min_value=65):
    hsv = image.convert("HSV")
    hue, saturation, value = hsv.split()
    hue_mask = Image.new("L", image.size, 0)
    for low, high in ranges:
        if low <= high:
            current = hue.point(lambda x, lo=low, hi=high: 255 if lo <= x <= hi else 0)
        else:
            current = hue.point(lambda x, lo=low, hi=high: 255 if x >= lo or x <= hi else 0)
        hue_mask = ImageChops.lighter(hue_mask, current)
    saturation_mask = saturation.point(lambda x: 255 if x >= min_saturation else 0)
    value_mask = value.point(lambda x: 255 if x >= min_value else 0)
    mask = ImageChops.multiply(hue_mask, saturation_mask)
    mask = ImageChops.multiply(mask, value_mask)
    return mask.filter(ImageFilter.GaussianBlur(radius=0.45))

def strengthen_marking_colors(image):
    base = image.convert("RGB")
    h, s, v = base.convert("HSV").split()
    vivid = Image.merge("HSV", (h, s.point(lambda x: min(255, int(x * 1.20 + 8))), v.point(lambda x: min(255, int(x * 1.04 + 2))))).convert("RGB")
    masks = [
        color_range_mask(base, [(246, 255), (0, 12)], 75, 55),
        color_range_mask(base, [(25, 55)], 65, 75),
        color_range_mask(base, [(112, 145)], 55, 75),
        color_range_mask(base, [(202, 238)], 55, 70),
    ]
    combined = Image.new("L", base.size, 0)
    for mask in masks: combined = ImageChops.lighter(combined, mask)
    return Image.composite(vivid, base, combined)

def apply_enhancement(image, mode):
    if mode == "standard": return image
    base = image.convert("RGB")
    if mode == "boundary":
        base = strengthen_marking_colors(base)
        base = ImageEnhance.Contrast(base).enhance(1.045)
        base = base.filter(ImageFilter.UnsharpMask(radius=0.90, percent=115, threshold=3))
        lut = [max(0, int(v * 0.86)) if v < 125 else v for v in range(256)]
        darker = base.point(lut * 3)
        mask = ImageOps.invert(base.convert("L")).point(lambda v: max(0, min(255, int((v - 82) * 1.55))))
        return Image.composite(darker, base, mask)
    if mode == "drawing":
        base = strengthen_marking_colors(base)
        base = ImageOps.autocontrast(base, cutoff=0.20)
        base = ImageEnhance.Contrast(base).enhance(1.12)
        base = base.filter(ImageFilter.UnsharpMask(radius=0.72, percent=150, threshold=2))
        lut = [max(0, int(v * 0.78)) if v < 175 else v for v in range(256)]
        darker = base.point(lut * 3)
        mask = ImageOps.invert(base.convert("L")).point(lambda v: max(0, min(255, int((v - 45) * 1.95))))
        return Image.composite(darker, base, mask)
    return base

def enhance_pdf_images(doc, enhancement_mode, quality):
    processed = set()
    for page in doc:
        for item in page.get_images(full=True):
            xref, smask = item[0], item[1]
            if xref in processed or smask: continue
            processed.add(xref)
            try:
                data = doc.extract_image(xref)
                if str(data.get("ext", "")).lower() not in {"jpg", "jpeg", "png"}: continue
                with Image.open(io.BytesIO(data["image"])) as image:
                    image = apply_enhancement(convert_to_rgb(image), enhancement_mode)
                    buffer = io.BytesIO()
                    image.save(buffer, "JPEG", quality=max(quality, 62), optimize=True, progressive=True, subsampling=1)
                page.replace_image(xref, stream=buffer.getvalue())
            except Exception:
                continue


def _sample_page_indices(page_count, max_pages=12):
    """Return evenly distributed page indices without loading every page."""
    page_count = max(0, int(page_count or 0))
    max_pages = max(1, int(max_pages or 1))
    if page_count <= max_pages:
        return list(range(page_count))
    if max_pages == 1:
        return [0]
    return sorted({round(i * (page_count - 1) / (max_pages - 1)) for i in range(max_pages)})


def estimate_pdf_optimized_size(source, dpi, quality, enhancement_mode="standard", max_sample_pages=12):
    """Estimate optimized PDF size by rewriting only evenly sampled pages.

    The real optimizer still processes every page.  This helper is intentionally
    sample-based so preflight diagnosis remains practical even for hundreds or
    thousands of pages.
    """
    if pymupdf is None:
        raise ValueError("PDF機能に必要なPyMuPDFがありません。")
    source_size = max(1, source.stat().st_size)
    with pymupdf.open(source) as doc:
        if doc.needs_pass:
            raise ValueError("パスワード付きPDFには対応していません。")
        indices = _sample_page_indices(doc.page_count, max_sample_pages)
        if not indices:
            return source_size
        sample = pymupdf.open()
        try:
            for page_index in indices:
                sample.insert_pdf(doc, from_page=page_index, to_page=page_index)

            baseline = io.BytesIO()
            sample.save(baseline, garbage=4, deflate=True, clean=True)
            baseline_size = max(1, len(baseline.getvalue()))

            sample.rewrite_images(
                dpi_threshold=max(dpi + 40, 180),
                dpi_target=dpi, quality=quality,
                lossy=True, lossless=True, bitonal=False,
            )
            if enhancement_mode != "standard":
                enhance_pdf_images(sample, enhancement_mode, quality)
            optimized = io.BytesIO()
            sample.save(optimized, garbage=4, deflate=True, clean=True)
            ratio = len(optimized.getvalue()) / baseline_size
        finally:
            sample.close()

    # optimize_pdf() keeps the original when compression would make it larger.
    return min(source_size, max(1, int(source_size * ratio)))


def optimize_pdf(source, destination, dpi, quality, enhancement_mode="standard"):
    temp = destination.with_suffix(".tmp.pdf")
    if temp.exists(): temp.unlink()
    try:
        with pymupdf.open(source) as doc:
            if doc.needs_pass: raise ValueError("パスワード付きPDFには対応していません。")
            doc.rewrite_images(dpi_threshold=max(dpi + 40, 180), dpi_target=dpi, quality=quality, lossy=True, lossless=True, bitonal=False)
            if enhancement_mode != "standard": enhance_pdf_images(doc, enhancement_mode, quality)
            doc.save(temp, garbage=4, deflate=True, clean=True)
        if temp.stat().st_size >= source.stat().st_size:
            shutil.copy2(source, destination); temp.unlink(missing_ok=True)
        else:
            os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)

def resize_image(source, destination, width, height, quality, enhancement_mode="standard"):
    with Image.open(source) as image:
        image = convert_to_rgb(ImageOps.exif_transpose(image))
        target = (width, height) if image.width >= image.height else (height, width)
        resized = image.resize(target, Image.Resampling.LANCZOS)
        enhanced = apply_enhancement(resized, enhancement_mode)
        enhanced.save(destination, "JPEG", quality=quality, optimize=True, progressive=True, subsampling=1 if enhancement_mode != "standard" else 2)

def detail_score(image):
    preview = image.copy(); preview.thumbnail((256, 256), Image.Resampling.LANCZOS)
    return float(ImageStat.Stat(preview.convert("L").filter(ImageFilter.FIND_EDGES)).mean[0])

def estimate_image_size(image, width, height, quality):
    target = (width, height) if image.width >= image.height else (height, width)
    buffer = io.BytesIO(); image.resize(target, Image.Resampling.LANCZOS).save(buffer, "JPEG", quality=quality, optimize=True, progressive=True)
    return buffer.tell()
