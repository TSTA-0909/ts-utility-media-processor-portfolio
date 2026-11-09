"""Assert portfolio examples derive from the real local Python quality-diagnosis function."""
import sys, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from quality_diagnosis import build_print_quality_diagnosis
from PIL import Image
class DiagnosisTests(unittest.TestCase):
    def test_diagnosis_matches_original_engine(self):
        meta=json.loads((ROOT/'docs/assets/results.json').read_text(encoding='utf-8'))
        for x in meta['variants']:
            expected=build_print_quality_diagnosis(image_count=1,image_preset_name=x['preset_key'],reduction=x['reduction'],operation='optimize')
            self.assertEqual(x['diagnosis'], expected)
    def test_image_dimensions_and_files_match(self):
        meta=json.loads((ROOT/'docs/assets/results.json').read_text(encoding='utf-8'))
        for x in meta['variants']:
            path=ROOT/'docs/assets'/x['filename']
            self.assertEqual(path.stat().st_size,x['bytes'])
            with Image.open(path) as im:self.assertEqual(im.size,(x['width'],x['height']))
        orig=ROOT/'docs/assets/before.jpg'
        self.assertEqual(orig.stat().st_size,meta['original']['bytes'])
if __name__=='__main__':unittest.main()
