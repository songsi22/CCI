from abc import ABC, abstractmethod


class CSPInterface(ABC):
    """
    클라우드 서비스 제공자(CSP) API 인터페이스를 정의하는 추상 클래스.
    모든 CSP 클래스는 이 인터페이스를 구현하여 일관된 메서드 구조를 제공해야 합니다.
    """

    @abstractmethod
    def get_instances(self):
        """
        클라우드의 모든 인스턴스 정보를 가져오는 메서드.
        이 메서드는 각 CSP에서 인스턴스 리스트를 가져오도록 구현되어야 합니다.
        Returns:
            list: 인스턴스 정보 리스트.
        """
        pass

    @abstractmethod
    def get_inventory(self):
        """
        클라우드 인프라의 인벤토리 정보를 가져오는 메서드.
        이 메서드는 각 CSP에서 인벤토리 정보를 수집하여 반환하도록 구현되어야 합니다.
        Returns:
            dict: 인벤토리 정보가 담긴 사전(dict).
        """
        pass

    @abstractmethod
    def get_blockstorage(self):
        """
        블록 스토리지 정보를 가져오는 메서드.
        이 메서드는 각 CSP에서 블록 스토리지 리스트를 가져오도록 구현되어야 합니다.
        Returns:
            list: 블록 스토리지 정보 리스트.
        """
        pass
