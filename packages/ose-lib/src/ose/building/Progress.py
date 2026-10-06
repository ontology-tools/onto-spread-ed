

from typing import Callable

from pydantic import BaseModel


class Progress(BaseModel):
    current_item: int | None
    total_items: int | None
    item: str | None
    message: str | None


class ProgressManager:
    def __init__(
        self,
        on_progress_update: Callable[[Progress], None] | None,
        total_items: int | None = None,
    ):
        self.total_items = total_items
        self.current_item = -1
        self.on_progress_update = on_progress_update

        if self.on_progress_update:
            self.on_progress_update(
                Progress(
                    current_item=None,
                    total_items=self.total_items,
                    item=None,
                    message="Starting",
                )
            )

    def next_item(self, *, item: str | None = None, message: str | None = None):
        self.current_item += 1
        if self.on_progress_update:
            progress = Progress(
                current_item=self.current_item,
                total_items=self.total_items,
                item=item,
                message=message,
            )
            self.on_progress_update(progress)