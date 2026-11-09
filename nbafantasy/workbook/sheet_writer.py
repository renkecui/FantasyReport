from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Side
from openpyxl.utils import get_column_letter as L

from .theme import Theme


class SheetWriter:
    """Base class for one tab: title banner, group row, header row, data from row 5."""

    TITLE = ""
    TAB_COLOR = Theme.MID
    FIRST = 5  # first data row

    def __init__(self, wb, data, stamp, colors, index=None):
        self.data, self.stamp, self.colors = data, stamp, colors
        self.ws = wb.create_sheet(self.sheet_title(), index)

    def sheet_title(self):
        return self.TITLE

    @property
    def ncols(self):
        return len(self.headers())

    def headers(self):
        raise NotImplementedError

    def write(self):
        raise NotImplementedError

    # ---------------------------------------------------------------- shared styling
    def banner(self, title, sub):
        ws, n = self.ws, self.ncols
        ws.sheet_view.showGridLines = False
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n)
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n)
        a = ws.cell(1, 1, value=title)
        a.font = Theme.font(bold=True, size=16, color="FFFFFF")
        a.alignment = Theme.LEFT
        for c in range(1, n + 1):
            ws.cell(1, c).fill = Theme.fill(Theme.NAVY)
        b = ws.cell(2, 1, value=sub)
        b.font = Theme.font(italic=True, size=9, color=Theme.GREY)
        b.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
        ws.row_dimensions[1].height = 34
        ws.row_dimensions[2].height = 30

    def groups(self, spec):
        ws = self.ws
        ws.row_dimensions[3].height = 20
        for s, e, txt, col in spec:
            ws.merge_cells(start_row=3, start_column=s, end_row=3, end_column=e)
            c = ws.cell(3, s, value=txt)
            c.font = Theme.font(bold=True, size=10, color="FFFFFF")
            c.alignment = Theme.CENTER
            for k in range(s, e + 1):
                ws.cell(3, k).fill = Theme.fill(col)
                ws.cell(3, k).border = Border(left=Side(style="thin", color="FFFFFF"),
                                              right=Side(style="thin", color="FFFFFF"))

    def header(self):
        ws = self.ws
        ws.row_dimensions[4].height = 30
        for i, h in enumerate(self.headers(), 1):
            x = ws.cell(4, i, value=h)
            x.font = Theme.font(bold=True, size=10, color=Theme.NAVY)
            x.fill = Theme.fill("D6DCE4")
            x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            x.border = Border(bottom=Theme.THICK, top=Theme.THIN, left=Theme.THIN, right=Theme.THIN)

    def scale(self, rng, low_good=True):
        a, b = ("63BE7B", "F8696B") if low_good else ("F8696B", "63BE7B")
        self.ws.conditional_formatting.add(rng, ColorScaleRule(
            start_type="min", start_color=a, mid_type="percentile", mid_value=50,
            mid_color="FFEB84", end_type="max", end_color=b))

    def paint(self, r1, r2, seps, color_col, group_col=None):
        """Fill each row with its team's color; thick left border at `seps` columns;
        thick bottom border where the value in `group_col` changes."""
        ws = self.ws
        for r in range(r1, r2 + 1):
            tc = self.colors.get(ws.cell(r, color_col).value, "FFFFFF")
            ws.row_dimensions[r].height = 21
            new_group = (group_col and r < r2
                         and ws.cell(r, group_col).value != ws.cell(r + 1, group_col).value)
            for c in range(1, self.ncols + 1):
                x = ws.cell(r, c)
                x.fill = Theme.fill(tc)
                if x.alignment.horizontal is None:
                    x.alignment = Theme.CENTER
                x.border = Border(left=Theme.THICK if c in seps else Theme.THIN, right=Theme.THIN, top=Theme.THIN,
                                  bottom=Theme.THICK if new_group else Theme.THIN)

    def widths(self, widths):
        for i, w in enumerate(widths, 1):
            self.ws.column_dimensions[L(i)].width = w

    def page_setup(self):
        ws = self.ws
        ws.sheet_properties.tabColor = self.TAB_COLOR
        ws.page_setup.orientation = "landscape"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToHeight = 0
