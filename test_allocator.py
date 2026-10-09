import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"app"))
from auto_allocator import scan_candidates, make_plan, next_power_of_two

class AllocatorTests(unittest.TestCase):
    def test_finds_aligned_ff_region(self):
        rom = b"X"*256 + b"\xff"*1024 + b"A"*64
        hits = scan_candidates(rom, 128)
        self.assertTrue(hits)
        self.assertEqual(hits[0].aligned_start % 4, 0)
        self.assertGreaterEqual(hits[0].size,128)
    def test_requires_expansion_when_no_candidate(self):
        rom = bytes(range(1,256))*4
        plan=make_plan(rom, 512)
        self.assertTrue(plan["requires_expansion"])
        self.assertEqual(plan["expanded_size"] & (plan["expanded_size"]-1),0)
    def test_source_is_unchanged(self):
        rom=b"X"*256+b"\x00"*1024
        before=bytes(rom)
        scan_candidates(rom,100)
        self.assertEqual(rom,before)
    def test_power_of_two(self):
        self.assertEqual(next_power_of_two(0x800001),0x1000000)

if __name__=="__main__":
    unittest.main()
