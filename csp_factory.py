# csp_factory.py

from ktc_api import KTCAPI
from nhn_api import NHNAPI
from ncp_api import NCPAPI


class CSPFactory:
    @staticmethod
    def get_csp(csp_type, **kwargs):
        if csp_type == "KTC":
            return KTCAPI(kwargs['username'], kwargs['password'], kwargs.get('zone', 'd1'), kwargs.get('gov', False))
        elif csp_type == "NHN":
            return NHNAPI(kwargs['username'], kwargs['password'], kwargs['tenantid'], kwargs.get('zone', 'kr1'), kwargs.get('gov', False))
        elif csp_type == "NCP":
            return NCPAPI(kwargs['access_key'], kwargs['secret_key'], kwargs['zone'],kwargs.get('gov', False))
        elif csp_type == "KTCG":
            return KTCAPI(kwargs['username'], kwargs['password'], kwargs.get('zone', 'gd1'), kwargs.get('gov', True))
        elif csp_type == "NHNG":
            return NHNAPI(kwargs['username'], kwargs['password'], kwargs['tenantid'],kwargs.get('zone', 'kr1'), kwargs.get('gov', True))
        elif csp_type == "NCPG":
            return NCPAPI(kwargs['access_key'], kwargs['secret_key'], kwargs.get('zone', 'KR'), kwargs.get('gov', True))
        else:
            raise ValueError(f"Unknown CSP type: {csp_type}")
