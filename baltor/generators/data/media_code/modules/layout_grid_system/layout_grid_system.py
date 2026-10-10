"""Column and baseline grid for vertical (or any) video frames.

Defines a layout grid from frame size, outer margins, column count, gutter
and baseline unit, then places elements by column span and baseline rows so
titles, photos and captions line up consistently across videos.

Usage::

    from layout_grid_system import Grid
    g = Grid((1080, 1920), columns=12, margin=(60, 96), gutter=24, baseline=24)
    g.span(0, 12)                     # full-width x, w
    g.rect(col=1, span=10, row=10, rows=12)    # (x, y, w, h) snapped to the grid
    g.snap_y(437)                     # nearest baseline
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Grid:
    size: tuple
    columns: int = 12
    margin: tuple = (60, 96)   # (horizontal, vertical)
    gutter: int = 24
    baseline: int = 24

    def __post_init__(self):
        W, H = self.size
        if self.columns < 1 or self.baseline < 1:
            raise ValueError("columns and baseline must be >= 1")
        self.content_w = W - 2 * self.margin[0]
        self.content_h = H - 2 * self.margin[1]
        self.col_w = (self.content_w - (self.columns - 1) * self.gutter) / self.columns
        if self.col_w <= 0:
            raise ValueError("margins and gutters leave no column width")
        self.rows = self.content_h // self.baseline

    def span(self, col: int, span: int) -> tuple[float, float]:
        if col < 0 or span < 1 or col + span > self.columns:
            raise ValueError("column span outside the grid")
        x = self.margin[0] + col * (self.col_w + self.gutter)
        w = span * self.col_w + (span - 1) * self.gutter
        return round(x, 2), round(w, 2)

    def row_y(self, row: int) -> int:
        if not 0 <= row <= self.rows:
            raise ValueError("row outside the grid")
        return self.margin[1] + row * self.baseline

    def rect(self, col: int, span: int, row: int, rows: int) -> tuple[float, float, float, int]:
        x, w = self.span(col, span)
        y = self.row_y(row)
        if row + rows > self.rows:
            raise ValueError("rows run past the bottom margin")
        return x, y, w, rows * self.baseline

    def snap_y(self, y: float) -> int:
        r = round((y - self.margin[1]) / self.baseline)
        return self.row_y(min(max(r, 0), self.rows))

    def guides(self) -> dict:
        cols = [self.span(c, 1) for c in range(self.columns)]
        return {"columns": cols, "baselines": [self.row_y(r) for r in range(self.rows + 1)]}
