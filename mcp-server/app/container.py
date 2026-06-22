import logging
from functools import cached_property
from app.tools.epic_tool import EpicTool
from app.tools.ticket_tool import TicketTool


class Container:
    def logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)

    @cached_property
    def epic_tool(self) -> EpicTool:
        return EpicTool()

    @cached_property
    def ticket_tool(self) -> TicketTool:
        return TicketTool()


container = Container()
