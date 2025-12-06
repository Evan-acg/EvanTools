import typing as t
from abc import ABC, abstractmethod

from rich.console import RenderableType
from rich.live import Live


class Tui(ABC):
    def __enter__(self) -> t.Self:
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.live.__exit__(exc_type, exc_value, traceback)

    def __init__(self) -> None:
        self.live: Live = Live()
        self.root_comp: RenderableType = self.assemble_root_renderable()

    @abstractmethod
    def assemble_root_renderable(self) -> RenderableType:
        raise NotImplementedError()

    def refresh(self, comp: RenderableType | None = None) -> None:
        assert self.root_comp is not None, "Root renderable not assembled yet."
        if comp is not None:
            self.live.update(comp)
        self.live.update(self.root_comp)
