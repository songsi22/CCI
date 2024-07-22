from abc import ABC, abstractmethod

class CSPInterface(ABC):
    @abstractmethod
    def get_inventory(self):
        pass
