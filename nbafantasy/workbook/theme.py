from openpyxl.styles import Alignment, Font, PatternFill, Side


class Theme:
    """Fonts, colors and borders shared by every tab."""
    FONT = "Arial"
    NAVY, MID, GREY, PURP, ORNG = "1F3864", "2F5597", "595959", "7030A0", "C55A11"
    GREEN_TAB = "00873C"  # my team's roster tab
    PALETTE = ["DDEBF7", "FFF2CC", "EDEDED", "E4DFEC", "FCE4D6", "EFE6DA",
               "D9E1F2", "FFE699", "D0CECE", "CCC0DA", "F8CBAD", "E2D5C3"]
    THIN = Side(style="thin", color="D9D9D9")
    THICK = Side(style="medium", color=NAVY)
    CENTER = Alignment(horizontal="center", vertical="center")
    LEFT = Alignment(horizontal="left", vertical="center", indent=1)
    VALUE = Font(name=FONT, size=10, color="000000")  # names and numbers

    @staticmethod
    def fill(color):
        return PatternFill("solid", start_color=color, end_color=color)

    @classmethod
    def font(cls, **kw):
        return Font(name=cls.FONT, **kw)
