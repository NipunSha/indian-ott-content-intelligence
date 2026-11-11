"""Small python-pptx helper giving the portfolio decks one visual identity."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

NAVY, TEAL, CLAY, GREY, INK = RGBColor(0x1F, 0x3A, 0x5F), RGBColor(0x2A, 0x9D, 0x8F), RGBColor(0xC8, 0x55, 0x3D), RGBColor(0x6B, 0x72, 0x80), RGBColor(0x1A, 0x1A, 0x1A)


class Deck:
    def __init__(self, footer):
        self.prs = Presentation(); self.prs.slide_width = Inches(13.333); self.prs.slide_height = Inches(7.5); self.footer = footer

    def _base(self, title, accent=NAVY):
        s = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.25), self.prs.slide_height); bar.fill.solid(); bar.fill.fore_color.rgb = accent; bar.line.fill.background()
        tb = s.shapes.add_textbox(Inches(0.7), Inches(0.45), Inches(12), Inches(1.2)); tf = tb.text_frame; tf.word_wrap = True
        r = tf.paragraphs[0].add_run(); r.text = title; r.font.size = Pt(28); r.font.bold = True; r.font.color.rgb = NAVY; r.font.name = "Calibri"
        fb = s.shapes.add_textbox(Inches(0.7), Inches(6.95), Inches(12), Inches(0.4)); fr = fb.text_frame.paragraphs[0].add_run()
        fr.text = f"{self.footer}   |   {len(self.prs.slides)}"; fr.font.size = Pt(10); fr.font.color.rgb = GREY
        return s

    def _bullets(self, s, items, left, top, width, height, size=18):
        tf = s.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height)).text_frame; tf.word_wrap = True
        for i, it in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            r = p.add_run(); r.text = it; r.font.size = Pt(size); r.font.color.rgb = INK; r.font.name = "Calibri"; p.space_after = Pt(10)

    def title(self, title, subtitle):
        s = self._base(title); self._bullets(s, [subtitle], 0.7, 2.2, 11.5, 2, size=20); return s

    def bullets(self, title, items, note=None):
        s = self._base(title); self._bullets(s, items, 0.7, 1.7, 11.8, 4.6)
        if note: self._bullets(s, [note], 0.7, 6.2, 11.8, 0.6, size=12)
        return s

    def picture(self, title, image, items=(), note=None):
        s = self._base(title)
        s.shapes.add_picture(str(image), Inches(0.7), Inches(1.7), width=Inches(7.4))
        if items: self._bullets(s, list(items), 8.4, 1.7, 4.5, 4.6, size=16)
        if note: self._bullets(s, [note], 0.7, 6.3, 11.8, 0.6, size=12)
        return s

    def table(self, title, header, rows, note=None, col_widths=None):
        s = self._base(title)
        n, m = len(rows) + 1, len(header)
        t = s.shapes.add_table(n, m, Inches(0.7), Inches(1.7), Inches(11.8), Inches(0.45 * n)).table
        for j, h in enumerate(header):
            c = t.cell(0, j); c.text = str(h); c.fill.solid(); c.fill.fore_color.rgb = NAVY
            for p in c.text_frame.paragraphs:
                for r in p.runs: r.font.size = Pt(14); r.font.bold = True; r.font.color.rgb = RGBColor(255, 255, 255)
        for i, row in enumerate(rows, 1):
            for j, v in enumerate(row):
                c = t.cell(i, j); c.text = str(v); c.fill.solid(); c.fill.fore_color.rgb = RGBColor(0xF4, 0xF6, 0xF8) if i % 2 else RGBColor(255, 255, 255)
                for p in c.text_frame.paragraphs:
                    for r in p.runs: r.font.size = Pt(14); r.font.color.rgb = INK
        if col_widths:
            for j, w in enumerate(col_widths): t.columns[j].width = Inches(w)
        if note: self._bullets(s, [note], 0.7, 1.9 + 0.45 * n + 0.3, 11.8, 1.2, size=13)
        return s

    def save(self, path):
        self.prs.save(str(path)); return path
