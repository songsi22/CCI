from csp_factory import CSPFactory
from data_to_excel import data_to_excel


def main():
    csp = CSPFactory.get_csp('KTCG',username="test@test.com",
                             password="testCom")
    data_to_excel(csp.get_inventory())

if __name__ == "__main__":
    main()
