"""Smoke/regression tests exercising actual Python processing functions."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "src"))
from image_engine import resize_image, detail_score, convert_to_rgb
from processing_presets import IMAGE_PRESETS, PDF_PRESETS
from conversion_engine import png_to_jpeg, jpeg_to_png, images_to_single_pdf, optimize_png
from video_engine import VIDEO_PRESETS, build_output_path


class RealEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)

    def test_presets_are_real_and_valid(self):
        for label, row in IMAGE_PRESETS.items():
            self.assertGreater(row[0],0)
            self.assertGreater(row[1],0)
            self.assertGreater(row[2],0)
            self.assertLessEqual(row[2],100)
        self.assertGreaterEqual(len(PDF_PRESETS),3)

    def test_jpeg_resize_calls_original_engine(self):
        src=self.base/'input.jpg';dst=self.base/'output.jpg'
        Image.new('RGB',(240,168),(100,130,170)).save(src,quality=96)
        resize_image(src,dst,120,84,68,'standard')
        with Image.open(dst) as im: self.assertEqual(im.size,(120,84))
        self.assertGreater(dst.stat().st_size,0)

    def test_png_to_jpeg_flattens_alpha(self):
        src=self.base/'input.png';dst=self.base/'output.jpg'
        Image.new('RGBA',(70,35),(0,70,180,0)).save(src)
        png_to_jpeg(src,dst,quality=80)
        with Image.open(dst) as im:
            self.assertEqual(im.size,(70,35));self.assertEqual(im.mode,'RGB')
            self.assertGreaterEqual(im.getpixel((2,2))[0],240)

    def test_jpeg_to_png(self):
        src=self.base/'input.jpg';dst=self.base/'output.png'
        Image.new('RGB',(80,40),(150,140,170)).save(src)
        jpeg_to_png(src,dst,max_width=40,max_height=20)
        with Image.open(dst) as im:self.assertEqual(im.size,(40,20))

    def test_png_optimization(self):
        src=self.base/'input.png';dst=self.base/'optimized.png'
        Image.new('RGB',(300,140),(10,50,80)).save(src)
        optimize_png(src,dst,max_width=150,max_height=70)
        with Image.open(dst) as im:self.assertEqual(im.size,(150,70))

    def test_pdf_creation(self):
        try:import pymupdf
        except ImportError:self.skipTest('PyMuPDF not installed')
        src=self.base/'input.jpg';dst=self.base/'output.pdf'
        Image.new('RGB',(400,300),(200,100,80)).save(src)
        images_to_single_pdf([src],dst,max_width=300,max_height=250,jpeg_quality=70)
        with pymupdf.open(dst) as pdf:self.assertEqual(pdf.page_count,1)

    def test_video_preset_configuration(self):
        self.assertIn('容量優先（かなり軽量）',VIDEO_PRESETS)
        self.assertLess(VIDEO_PRESETS['容量優先（かなり軽量）']['max_height'],1080)

    def test_nonclobbering_video_output_path(self):
        source=self.base/'movie.mov';destination=self.base/'out';destination.mkdir()
        first=build_output_path(source,destination)
        self.assertEqual(first.name,'movie_slim.mp4')
        first.write_bytes(b'x')
        second=build_output_path(source,destination)
        self.assertEqual(second.name,'movie_slim_2.mp4')

    def test_actual_sample_assets(self):
        for filename in ['before.jpg','after-share.jpg','after-email.jpg','after-report.jpg','after-screen.jpg']:
            path=ROOT/'docs'/'assets'/filename
            self.assertTrue(path.is_file(),path)
            with Image.open(path) as im:self.assertGreater(im.width,100)


if __name__=='__main__':unittest.main()
