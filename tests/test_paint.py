from pathlib import Path
from typing import NamedTuple
import pytest
from cop_agent.domain.belief import Belief
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, step_record
from cop_agent.infra.ceremony import StepCeremony
from cop_agent.infra.match_log import MatchLog
from cop_agent.ui.app import STAMP_COLOUR, CanvasPainter, draw_live, draw_replay, main
from cop_agent.ui.banner import Tone, banner
from cop_agent.ui.paint import (
    BARRIER_FILL,
    HEAT,
    OURS,
    SUSPECT,
    board_size,
    cell_box,
    paint_banner,
    paint_board,
)
from cop_agent.ui.replay import load
from cop_agent.ui.verdict import Stamp
from cop_agent.ui.view import View, render
class Rect(NamedTuple):
    x0: int
    y0: int
    x1: int
    y1: int
    fill: str
    outline: str
class Text(NamedTuple):
    x: int
    y: int
    body: str
    fill: str
class Recording:
    def __init__(self) -> None:
        self.rects: list[Rect] = []
        self.texts: list[Text] = []
    def rectangle(self, x0: int, y0: int, x1: int, y1: int, fill: str, outline: str) -> None:
        self.rects.append(Rect(x0, y0, x1, y1, fill, outline))
    def text(self, x: int, y: int, body: str, fill: str) -> None:
        self.texts.append(Text(x, y, body, fill))
    def clear(self) -> None:
        self.rects.clear()
        self.texts.clear()
    def fill_at(self, cell: tuple[int, int]) -> str:
        x0, y0, _, _ = cell_box(cell)
        return next(r.fill for r in self.rects if (r.x0, r.y0) == (x0, y0))
    def glyph_at(self, cell: tuple[int, int]) -> str:
        x0, y0, x1, y1 = cell_box(cell)
        centre = ((x0 + x1) // 2, (y0 + y1) // 2)
        return next((t.body for t in self.texts if (t.x, t.y) == centre), "")
def a_board(grid: int = 6) -> BoardState:
    return BoardState(
        grid_size=grid, cop=(3, 3), thief=(4, 4), barriers=frozenset({(2, 2)}), step=3
    )
def a_view(state: BoardState | None = None, belief: Belief | None = None) -> View:
    board = state or a_board()
    return render(board, belief or Belief.uniform(board), "police", board.cop, "C", "T")
def sealed_log(tmp_path: Path, corrupt: bool = False) -> Path:
    log = MatchLog(game_id="uoh26-s82kma9e", sub_game=1, role="police", game_uid="u-1")
    for step in (1, 2):
        board = BoardState(
            grid_size=6, cop=(1, step), thief=(4, 4), barriers=frozenset(), step=step
        )
        record = step_record(board, "police", "N", "truth", f"s{step}")
        secret = f"{step:032x}"
        log.commit(step, commit_of(record, secret))
        log.reveal(step, {**record, "move": "S"} if corrupt and step == 2 else record)
        log.disclose(step, secret)
    return log.write(tmp_path)
