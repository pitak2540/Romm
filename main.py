import os
import json
import tempfile
from pathlib import Path
from collections import Counter

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

Window.clearcolor = (0.07, 0.09, 0.13, 1)

THAI = list("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮะาำิีึืุูเแโใไๅ็่้๊๋์ํ๎๐๑๒๓๔๕๖๗๘๙")
LATIN = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
PUNCT = list(" .,!?;:-'\"()[]{}<>/@#$%&*+=_\\|~`")
JAPANESE = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンー。、「」！？・")
GLYPHS = list(dict.fromkeys(THAI + LATIN + PUNCT + JAPANESE))

def button(text, fn, height=dp(44)):
    b = Button(text=text, size_hint_y=None, height=height,
               background_normal="", background_color=(0.16, 0.22, 0.32, 1),
               color=(0.92, 0.95, 1, 1))
    b.bind(on_release=lambda *_: fn())
    return b

def label(text, size=dp(14), height=None, color=(0.9,0.93,0.98,1)):
    kwargs = {"text": text, "font_size": size, "color": color,
              "size_hint_y": None}
    if height is not None:
        kwargs["height"] = height
    else:
        kwargs["height"] = max(dp(26), size * 2.2)
    return Label(**kwargs)

class PixelGrid(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid = 8
        self.pixels = set()
        self.bind(pos=self.redraw, size=self.redraw)

    def set_grid(self, n):
        self.grid = int(n)
        self.pixels = {(x,y) for x,y in self.pixels if x < n and y < n}
        self.redraw()

    def redraw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(0.055, 0.07, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)
            side = min(self.width, self.height)
            cell = side / self.grid
            ox = self.x + (self.width - side) / 2
            oy = self.y + (self.height - side) / 2
            Color(0.11, 0.14, 0.2, 1)
            Rectangle(pos=(ox,oy), size=(side,side))
            Color(0.91, 0.95, 1, 1)
            for x,y in self.pixels:
                Rectangle(pos=(ox+x*cell, oy+(self.grid-1-y)*cell),
                          size=(max(1,cell), max(1,cell)))
            Color(0.25, 0.31, 0.42, 1)
            for i in range(self.grid + 1):
                xx = ox + i*cell
                yy = oy + i*cell
                Line(points=[xx,oy,xx,oy+side], width=1)
                Line(points=[ox,yy,ox+side,yy], width=1)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        side = min(self.width, self.height)
        cell = side / self.grid
        ox = self.x + (self.width - side) / 2
        oy = self.y + (self.height - side) / 2
        x = int((touch.x - ox) / cell)
        y = self.grid - 1 - int((touch.y - oy) / cell)
        if 0 <= x < self.grid and 0 <= y < self.grid:
            point = (x,y)
            if point in self.pixels:
                self.pixels.remove(point)
            else:
                self.pixels.add(point)
            self.redraw()
            return True
        return super().on_touch_down(touch)

class ROMTranslatorAndroid(App):
    def build(self):
        self.title = "ROM Translator GBA"
        self.current_char = "ก"
        self.glyph_size = 8
        self.glyph_pixels = {ch:set() for ch in GLYPHS}
        self.rom_bytes = None
        self.rom_name = ""
        self.last_report = None
        self.rootbox = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        self.header = label("ROM TRANSLATOR • GBA EDITION", dp(18), dp(34), (0.62,0.75,1,1))
        self.rootbox.add_widget(self.header)
        nav = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
        nav.add_widget(button("Font Studio", lambda: self.show_font()))
        nav.add_widget(button("ROM Analyzer", lambda: self.show_rom()))
        nav.add_widget(button("ขยาย ROM", lambda: self.show_expansion()))
        self.rootbox.add_widget(nav)
        self.body = BoxLayout(orientation="vertical", spacing=dp(7))
        self.rootbox.add_widget(self.body)
        self.show_font()
        return self.rootbox

    def show_font(self):
        self.body.clear_widgets()
        top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        self.char_spinner = Spinner(text=self.current_char, values=GLYPHS, size_hint_x=0.42)
        self.char_spinner.bind(text=self.select_char)
        top.add_widget(self.char_spinner)
        self.size_spinner = Spinner(text=f"{self.glyph_size} × {self.glyph_size}",
                                    values=["8 × 8","8 × 16","16 × 16","16 × 24","16 × 32","32 × 32"])
        self.size_spinner.bind(text=self.select_size)
        top.add_widget(self.size_spinner)
        self.body.add_widget(top)
        self.grid_widget = PixelGrid(size_hint=(1, 0.68))
        self.grid_widget.set_grid(self.glyph_size)
        self.grid_widget.pixels = set(self.glyph_pixels.get(self.current_char,set()))
        self.grid_widget.redraw()
        self.body.add_widget(self.grid_widget)
        self.pixel_info = label(f"Glyph {self.current_char} • {len(self.grid_widget.pixels)} pixels", dp(13), dp(28))
        self.body.add_widget(self.pixel_info)
        clear_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        clear_row.add_widget(button("ล้าง Glyph", self.clear_glyph))
        clear_row.add_widget(button("บันทึก JSON", self.save_project))
        self.body.add_widget(clear_row)
        export_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        export_row.add_widget(button("ส่งออก PNG Atlas", self.export_png))
        export_row.add_widget(button("Glyph Map JSON", self.export_map))
        self.body.add_widget(export_row)
        note = label("แตะช่องเพื่อวาด/ลบ • รุ่น Android นี้เป็นตัวแก้ไขพิกเซลแบบสัมผัส", dp(12), dp(38), (0.62,0.68,0.78,1))
        self.body.add_widget(note)
        self.grid_widget.bind(on_touch_up=lambda *_: self.update_pixel_count())
        self.grid_widget.bind(on_touch_move=lambda *_: self.update_pixel_count())

    def select_char(self, spinner, text):
        if hasattr(self, "grid_widget"):
            self.glyph_pixels[self.current_char] = set(self.grid_widget.pixels)
        self.current_char = text
        if hasattr(self, "grid_widget"):
            self.grid_widget.pixels = set(self.glyph_pixels.get(text,set()))
            self.grid_widget.redraw()
            self.pixel_info.text = f"Glyph {text} • {len(self.grid_widget.pixels)} pixels"

    def select_size(self, spinner, text):
        try:
            w,h = [int(x.strip()) for x in text.split("×")]
            # The editor uses a square canvas; preserve requested dimensions for export is planned.
            if w != h:
                self.toast("หน้าวาดในรุ่นนี้เป็นสี่เหลี่ยม จึงปรับเป็นขนาดสี่เหลี่ยมที่เล็กกว่า")
                n = min(w,h)
            else:
                n = w
            self.glyph_size = n
            if hasattr(self, "grid_widget"):
                self.grid_widget.set_grid(n)
                self.grid_widget.pixels = set(self.glyph_pixels.get(self.current_char,set()))
                self.grid_widget.redraw()
        except Exception:
            pass

    def update_pixel_count(self):
        if hasattr(self, "pixel_info"):
            self.glyph_pixels[self.current_char] = set(self.grid_widget.pixels)
            self.pixel_info.text = f"Glyph {self.current_char} • {len(self.grid_widget.pixels)} pixels"

    def clear_glyph(self):
        self.grid_widget.pixels.clear()
        self.grid_widget.redraw()
        self.update_pixel_count()

    def toast(self, message):
        Popup(title="แจ้งเตือน", content=label(message, dp(14)),
              size_hint=(0.88,0.3)).open()

    def save_to_android(self, suggested_name, data, mime="application/json"):
        # On Android use the Storage Access Framework document picker.
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            activity = PythonActivity.mActivity
            intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType(mime)
            intent.putExtra(Intent.EXTRA_TITLE, suggested_name)
            self._pending_save = data
            self._pending_mime = mime
            # registerActivityResult not exposed uniformly; use Android helper bridge below if available.
            from androidstorage4kivy import Chooser
            Chooser(activity).save_file(data.encode("utf-8") if isinstance(data,str) else data,
                                        suggested_name, mime)
            self.toast("เปิดหน้าบันทึกไฟล์แล้ว")
        except Exception:
            # Safe fallback: write into app-private files directory.
            out = Path(self.user_data_dir) / suggested_name
            out.write_bytes(data.encode("utf-8") if isinstance(data,str) else data)
            self.toast(f"บันทึกในโฟลเดอร์แอปแล้ว:\n{out}")

    def save_project(self):
        self.update_pixel_count()
        data = {
            "format":"ROM Translator GBA Android Font Project",
            "version":1, "glyph_size":self.glyph_size, "glyphs":GLYPHS,
            "pixels":{ch:[[x,y] for x,y in sorted(points,key=lambda p:(p[1],p[0]))]
                      for ch,points in self.glyph_pixels.items()}
        }
        self.save_to_android("thai_pixel_font_project.json", json.dumps(data,ensure_ascii=False,indent=2))

    def _atlas(self):
        from PIL import Image
        chars = GLYPHS
        columns = 16
        rows = (len(chars)+columns-1)//columns
        img = Image.new("RGBA",(columns*self.glyph_size,rows*self.glyph_size),(0,0,0,0))
        px = img.load()
        self.update_pixel_count()
        for i,ch in enumerate(chars):
            ox,oy=(i%columns)*self.glyph_size,(i//columns)*self.glyph_size
            for x,y in self.glyph_pixels.get(ch,set()):
                px[ox+x,oy+y]=(255,255,255,255)
        return img

    def export_png(self):
        try:
            import io
            buf=io.BytesIO()
            self._atlas().save(buf,format="PNG")
            self.save_to_android("thai_glyph_atlas.png",buf.getvalue(),"image/png")
        except Exception as exc:
            self.toast(f"ส่งออก PNG ไม่สำเร็จ: {exc}")

    def export_map(self):
        self.update_pixel_count()
        cols=16
        data={"format":"ROM Translator GBA Glyph Map","version":1,
              "cell":{"width":self.glyph_size,"height":self.glyph_size},
              "encoding_note":"game_code is null until a ROM-specific character table is verified.",
              "glyphs":[]}
        for i,ch in enumerate(GLYPHS):
            data["glyphs"].append({"index":i,"character":ch,"unicode":f"U+{ord(ch):04X}",
                "atlas_cell":{"column":i%cols,"row":i//cols},
                "bitmap_pixels":[[x,y] for x,y in sorted(self.glyph_pixels.get(ch,set()),key=lambda p:(p[1],p[0]))],
                "game_code":None})
        self.save_to_android("glyph_map.json",json.dumps(data,ensure_ascii=False,indent=2))

    def _open_rom(self):
        try:
            from androidstorage4kivy import Chooser
            chooser = Chooser()
            chooser.choose_content(self._rom_selected, mime_type="*/*")
        except Exception:
            self.toast("ในรุ่นต้นแบบนี้ ให้คัดลอก ROM ไปยังโฟลเดอร์ที่แอปเข้าถึงได้ แล้วเปิดผ่านตัวเลือกไฟล์ในรุ่นถัดไป")

    def _rom_selected(self, uri):
        if not uri:
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()
            stream = resolver.openInputStream(uri)
            data = bytearray()
            buf = bytearray(65536)
            while True:
                n = stream.read(buf)
                if n <= 0: break
                data.extend(buf[:n])
            stream.close()
            self.rom_bytes = bytes(data)
            self.rom_name = str(uri)
            self.toast(f"โหลด ROM แล้ว: {len(data):,} bytes")
            self.show_rom()
        except Exception as exc:
            self.toast(f"เปิด ROM ไม่สำเร็จ: {exc}")

    def show_rom(self):
        self.body.clear_widgets()
        self.body.add_widget(label("GBA ROM Analyzer", dp(19), dp(38), (0.62,0.75,1,1)))
        self.body.add_widget(button("เลือก ROM จากเครื่อง", self._open_rom, dp(48)))
        if self.rom_bytes is None:
            self.body.add_widget(label("ยังไม่ได้เลือก ROM\nเลือกไฟล์ .gba เพื่อเริ่มตรวจข้อมูล", dp(15), dp(70)))
            return
        data=self.rom_bytes
        title=data[0xA0:0xAC].decode("ascii",errors="replace").strip("\x00 ")
        code=data[0xAC:0xB0].decode("ascii",errors="replace").strip("\x00 ")
        self.body.add_widget(label(f"ชื่อ Header: {title or '(ไม่มี)'} • Game Code: {code or '(ไม่มี)'}", dp(13), dp(44)))
        self.body.add_widget(label(f"ขนาด ROM: {len(data):,} bytes", dp(13), dp(30)))
        runs=[]
        # Fast ASCII run scanner
        start=None
        for i,b in enumerate(data):
            if 0x20 <= b <= 0x7e:
                if start is None: start=i
            else:
                if start is not None and i-start>=4:
                    runs.append((start,data[start:i].decode("ascii","replace")))
                start=None
        if start is not None and len(data)-start>=4:
            runs.append((start,data[start:].decode("ascii","replace")))
        self.body.add_widget(label(f"พบช่วง ASCII เบื้องต้น {len(runs)} รายการ (อาจมีผลบวกลวง)", dp(13), dp(32)))
        scroll=ScrollView()
        listing=GridLayout(cols=1,spacing=dp(2),size_hint_y=None)
        listing.bind(minimum_height=listing.setter("height"))
        for off,txt in runs[:100]:
            listing.add_widget(label(f"0x{off:X}  {txt[:90]}",dp(11),dp(30),(0.8,0.84,0.91,1)))
        scroll.add_widget(listing)
        self.body.add_widget(scroll)
        self.body.add_widget(button("บันทึกรายงาน ROM", lambda: self.save_rom_report(runs,title,code), dp(44)))

    def save_rom_report(self,runs,title,code):
        report={"rom_name":self.rom_name,"size":len(self.rom_bytes),
                "header_title":title,"game_code":code,
                "ascii_runs":[{"offset":o,"text":t} for o,t in runs[:1000]],
                "warning":"ASCII scan only; custom game encodings and pointers are not inferred."}
        self.save_to_android("rom_scan_report.json",json.dumps(report,ensure_ascii=False,indent=2))

    def show_expansion(self):
        self.body.clear_widgets()
        self.body.add_widget(label("ROM Space Planner", dp(19), dp(38), (0.62,0.75,1,1)))
        self.body.add_widget(label("วางแผนพื้นที่ข้อความเบื้องต้น • ยังไม่เขียน ROM",dp(13),dp(35)))
        if self.rom_bytes is None:
            self.body.add_widget(label("กรุณาเลือก ROM ในหน้า ROM Analyzer ก่อน",dp(14),dp(45)))
            self.body.add_widget(button("ไปหน้า ROM Analyzer",self.show_rom))
            return
        self.size_input=TextInput(text="256",multiline=False,input_filter="int",size_hint_y=None,height=dp(46))
        self.body.add_widget(label("ขนาดข้อความที่ต้องการเพิ่ม (bytes)",dp(14),dp(30)))
        self.body.add_widget(self.size_input)
        self.body.add_widget(button("ค้นหา + จับพื้นที่อัตโนมัติ",self.plan_expansion,dp(46)))
        self.expansion_result=label("",dp(13),dp(100))
        self.body.add_widget(self.expansion_result)
        self.body.add_widget(button("สร้าง ROM สำเนาและจองพื้นที่",self.build_reserved_rom,dp(46)))
        self.body.add_widget(button("ส่งออกแผน JSON",self.export_expansion_plan,dp(44)))
        self.body.add_widget(label("หมายเหตุ: การจองพื้นที่ยังไม่ทำให้เกมอ่านฟอนต์ได้ ต้องมีตาราง/Pointer ของเกมก่อน",dp(11),dp(42),(0.95,0.72,0.4,1)))

    def plan_expansion(self):
        data=self.rom_bytes
        try: need=max(1,int(self.size_input.text))
        except: need=256
        alignment=4
        candidates=[]
        i=0
        while i<len(data):
            b=data[i]
            if b not in (0,255):
                i+=1
                continue
            st=i
            while i<len(data) and data[i]==b:
                i+=1
            length=i-st
            if length>=max(32,need) and st>=0xC0:
                aligned=((st+alignment-1)//alignment)*alignment
                usable_end=i
                if aligned+need<=usable_end:
                    # Count existing GBA pointers that point at this candidate start.
                    ptr=0x08000000+st
                    needle=ptr.to_bytes(4,"little",signed=False)
                    pointer_hits=data.count(needle)
                    # Rank large runs, aligned offsets and fewer apparent references higher.
                    score=(min(length,need*8) / max(need,1)) + (0.5 if st%4==0 else 0) - pointer_hits*0.25
                    candidates.append({"start":st,"aligned_start":aligned,"end":i,
                        "size":length,"fill":f"{b:02X}","pointer_hits_exact_start":pointer_hits,
                        "score":round(score,3)})
        candidates.sort(key=lambda x:(x["score"],x["size"]),reverse=True)
        fit=next((r for r in candidates if r["size"]>=need),None)
        self.expansion_plan={"format":"ROM Translator GBA Auto Allocation Plan","version":2,
            "rom_size":len(data),"requested_bytes":need,"alignment":alignment,
            "candidate_count":len(candidates),"free_space_candidates":candidates[:300],
            "allocation":({"offset":fit["aligned_start"],"original_candidate_start":fit["start"],
                           "size":need,"fill":fit["fill"],"status":"heuristic_candidate"}
                          if fit else None),
            "requires_expansion":fit is None,
            "expansion_target_size": self._next_rom_size(len(data)+need) if fit is None else len(data),
            "warning":"FF/00 scan is heuristic. Pointer-hit count is only a clue, not proof that a region is unused. This plan does not patch game pointers."}
        if fit:
            self.expansion_result.text=(f"เลือก candidate อัตโนมัติ: 0x{fit['aligned_start']:X}\\n"
                f"ขนาดช่วง {fit['size']:,} bytes • fill={fit['fill']} • score={fit['score']}\\n"
                "ยังต้องตรวจ references และ pointer format ของเกมก่อนใช้จริง")
        else:
            target=self._next_rom_size(len(data)+need)
            self.expansion_result.text=(f"ไม่พบช่วงว่างที่ยาวพอ {need:,} bytes\\n"
                f"แนะนำขยายสำเนา ROM เป็น {target:,} bytes แล้วจองท้ายไฟล์\\n"
                "การขยายไฟล์อย่างเดียวไม่พอ ต้องอัปเดต pointer/ระบบโหลดฟอนต์ด้วย")

    def _next_rom_size(self, size):
        # GBA ROM sizes are commonly padded to a power of two; cap suggestion at 64 MiB.
        n=1
        while n<size and n < 64*1024*1024:
            n*=2
        return max(n, size)

    def build_reserved_rom(self):
        if self.rom_bytes is None:
            self.toast("กรุณาเลือก ROM ก่อน")
            return
        if not hasattr(self,"expansion_plan"):
            self.plan_expansion()
        plan=self.expansion_plan
        data=bytearray(self.rom_bytes)
        allocation=plan.get("allocation")
        need=int(plan["requested_bytes"])
        if allocation:
            offset=int(allocation["offset"])
            fill=int(allocation["fill"],16)
            # Reserve requested bytes by writing the same fill value to a copied ROM.
            # The region may be overwritten only in a copy; source bytes are never modified.
            data[offset:offset+need]=bytes([fill])*need
            status="reserved_existing_candidate"
        else:
            target=int(plan["expansion_target_size"])
            if target>64*1024*1024:
                self.toast("ขนาด ROM ที่แนะนำเกิน 64 MiB; ยกเลิกเพื่อความปลอดภัย")
                return
            offset=len(data)
            data.extend(bytes([0xFF])*(target-len(data)))
            # Reserve region at the old EOF; ensure it is filled with FF.
            data[offset:offset+need]=b"\\xFF"*need
            status="reserved_appended_region"
        manifest={
            "format":"ROM Translator GBA Reserved Region Manifest",
            "version":1,
            "source_rom_name":self.rom_name,
            "source_size":len(self.rom_bytes),
            "output_size":len(data),
            "reserved_offset":offset,
            "reserved_size":need,
            "reserved_offset_hex":f"0x{offset:X}",
            "gba_pointer_if_used":f"0x{0x08000000+offset:08X}",
            "status":status,
            "font_data_written":False,
            "pointers_updated":False,
            "warning":"This is a working copy with a reserved region only. It is NOT a playable translated ROM until font bytes, encoding table, loader references and/or pointers are correctly installed."
        }
        self.save_to_android("gba_rom_reserved_copy.gba",bytes(data),"application/octet-stream")
        self.save_to_android("gba_reserved_region_manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2))
        self.toast(f"สร้างสำเนาและจองพื้นที่ที่ 0x{offset:X} แล้ว\\nยังไม่ได้ติดตั้งฟอนต์หรือแก้ Pointer")

    def export_expansion_plan(self):
        if not hasattr(self,"expansion_plan"):
            self.plan_expansion()
        self.save_to_android("rom_expansion_plan.json",json.dumps(self.expansion_plan,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    ROMTranslatorAndroid().run()
