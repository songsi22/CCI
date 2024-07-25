from abc import ABC, abstractmethod

class CSPInterface(ABC):
    @abstractmethod
    def get_instances(self):
        pass
    @abstractmethod
    def get_inventory(self):
        pass
    @abstractmethod
    def get_blockstorage(self):
        pass