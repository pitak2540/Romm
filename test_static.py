import unittest
from pathlib import Path

class AndroidProjectStaticTests(unittest.TestCase):
    def test_buildozer_spec_exists(self):
        root=Path(__file__).resolve().parents[1]
        spec=(root/"buildozer.spec").read_text(encoding="utf-8")
        self.assertIn("requirements = python3,kivy,pillow,androidstorage4kivy",spec)
        self.assertIn("android.archs",spec)
    def test_main_has_main_screens(self):
        root=Path(__file__).resolve().parents[1]
        code=(root/"main.py").read_text(encoding="utf-8")
        self.assertIn("def show_font",code)
        self.assertIn("def show_rom",code)
        self.assertIn("def show_expansion",code)

if __name__=="__main__":
    unittest.main()
