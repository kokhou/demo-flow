from abc import ABC, abstractmethod

from langchain_core.runnables import Runnable

from app.global_state import State


class BasePrepareAssistant(ABC):
    def __init__(self):
        self._assistant_runnable = None
        self._state = None

    @abstractmethod
    def init_assistant_runnable(self) -> Runnable:
        pass

    def get_assistant_runnable(self) -> Runnable:
        if not self._assistant_runnable:
            raise ValueError("Set state before calling get_assistant_runnable()")

        return self._assistant_runnable

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state: State):
        if not new_state:
            raise ValueError("State cannot be None")

        self._state = new_state
        self._assistant_runnable = self.init_assistant_runnable()
