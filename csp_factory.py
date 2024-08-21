# csp_factory.py

from ktc_api import KTCAPI
from nhn_api import NHNAPI
from ncp_api import NCPAPI


class CSPFactory:
    """
    CSP 인스턴스를 생성하는 팩토리 클래스.

    주어진 CSP 유형에 따라 적절한 API 클래스 인스턴스를 생성하고 반환합니다.
    """
    def __init__(self, csp_type):
        """
        CSPFactory 클래스의 생성자.

        Args:
            csp_type (str): CSP 유형.
        """
        self.csp_type = csp_type
    @staticmethod
    def get_csp(csp_type, **kwargs):
        """
        주어진 CSP 유형에 따라 적절한 API 인스턴스를 반환하는 정적 메서드.

        Args:
            csp_type (str): CSP 유형 (예: "KTC", "NHN", "NCP", "KTCG", "NHNG", "NCPG").
            **kwargs: 해당 CSP 인스턴스를 생성하는 데 필요한 추가 인자들.

        Returns:
            object: 주어진 CSP 유형에 해당하는 API 인스턴스.

        Raises:
            ValueError: 지원되지 않는 CSP 유형이 주어졌을 때 발생.
        """
        if csp_type in ["KTC", "KTCG"]:
            return CSPFactory._create_ktc_api(csp_type, **kwargs)
        elif csp_type in ["NHN", "NHNG"]:
            return CSPFactory._create_nhn_api(csp_type, **kwargs)
        elif csp_type in ["NCP", "NCPG"]:
            return CSPFactory._create_ncp_api(csp_type, **kwargs)
        else:
            raise ValueError(f"Unknown CSP type: {csp_type}")

    @staticmethod
    def _create_ktc_api(csp_type, username, password, zone='d1', gov=False):
        """
        KTC API 인스턴스를 생성하는 헬퍼 메서드.

        Args:
            csp_type (str): CSP 유형 (예: "KTC", "KTCG").
            username (str): 사용자 이름.
            password (str): 비밀번호.
            zone (str, optional): 존(zone) 정보. 기본값은 'd1'.
            gov (bool, optional): 공공 클라우드 여부. 기본값은 False.

        Returns:
            KTCAPI: KTC API 인스턴스.
        """
        if csp_type == "KTCG":
            zone = 'gd1'
            gov = True
        return KTCAPI(username, password, zone, gov)

    @staticmethod
    def _create_nhn_api(csp_type, username, password, tenantid, zone='kr1', gov=False):
        """
        NHN API 인스턴스를 생성하는 헬퍼 메서드.

        Args:
            csp_type (str): CSP 유형 (예: "NHN", "NHNG").
            username (str): 사용자 이름.
            password (str): 비밀번호.
            tenantid (str): 테넌트 ID.
            zone (str, optional): 존(zone) 정보. 기본값은 'kr1'.
            gov (bool, optional): 공공 클라우드 여부. 기본값은 False.

        Returns:
            NHNAPI: NHN API 인스턴스.
        """
        if csp_type == "NHNG":
            gov = True
        return NHNAPI(username, password, tenantid, zone, gov)

    @staticmethod
    def _create_ncp_api(csp_type, access_key, secret_key, zone='KR', gov=False):
        """
        NCP API 인스턴스를 생성하는 헬퍼 메서드.

        Args:
            csp_type (str): CSP 유형 (예: "NCP", "NCPG").
            access_key (str): 액세스 키.
            secret_key (str): 비밀 키.
            zone (str, optional): 존(zone) 정보. 기본값은 'KR'.
            gov (bool, optional): 공공 클라우드 여부. 기본값은 False.

        Returns:
            NCPAPI: NCP API 인스턴스.
        """
        if csp_type == "NCPG":
            gov = True
        return NCPAPI(access_key, secret_key, zone, gov)