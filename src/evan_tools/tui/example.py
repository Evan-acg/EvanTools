import typing as t
from enum import Enum

from rich import box
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from .main import Tui

E = t.TypeVar("E")

class VideoSimilarityTui(t.Generic[E], Tui):
    def __init__(self) -> None:
        self.bar: Progress = self._setup_progress_bar()
        self.bar_ids: dict[Enum, TaskID] = {}
        self.table: Table = self._setup_table()
        super().__init__()

    def _setup_group(self) -> Group:
        return Group(self.bar, self.table)

    def _setup_progress_bar(self) -> Progress:
        return Progress(
            "",
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TextColumn("|"),
            TimeElapsedColumn(),
            TextColumn("|"),
            TimeRemainingColumn(),
            expand=True,
        )

    def _setup_table(self, info: E | None = None) -> Table:
        return Table(expand=True, box=box.MINIMAL, show_header=False)

    @t.override
    def refresh(self, comp: RenderableType | None = None) -> None:
        t.cast(Panel, self.root_comp).renderable = self._setup_group()
        super().refresh(comp)
