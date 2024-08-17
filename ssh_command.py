import time
import re
import paramiko

systems_info = {}


def get_server_info(hostname, user, password, port=22):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, port=port, username=user, password=password)
        shell = ssh.invoke_shell()
        shell.send(
            "echo START;echo OS: `hostnamectl | grep 'Operating System:' | awk -F': ' '{print $2}' | sed 's/ Linux//' | sed 's/ (.*)//' | sed 's/ LTS//'`;"
            "echo HOSTNAME: `hostname`;"
            "echo SWAP: `free -k|grep -i swap|awk '{print $2/1024/1024}'`; echo Mount Point: `grep ^[A-Z,a-z,/] /etc/fstab|egrep -v 'swap|boot' | awk '$2 != \"/\" {print $2}'`;"
            "echo NAS: `df -k | grep ^[1,2]|awk '{print $2/1024/1024,$6}'`;echo IPs: `hostname -I`;echo END\n")
        time.sleep(1.3)  # 명령어가 실행될 시간을 줌

        output = shell.recv(4096).decode()
        match = re.search(r'START\r\n(.*?)END\r\n', output, re.DOTALL)

        if match:
            data = match.group(1).strip()
            return parse_system_info(data)
        else:
            return {"error": "No valid data found between START and END markers"}

    except paramiko.AuthenticationException:
        print("Authentication failed, please verify your credentials")
    except paramiko.SSHException as sshException:
        print(f"Unable to establish SSH connection: {sshException}")
    except paramiko.BadHostKeyException as badHostKeyException:
        print(f"Unable to verify server's host key: {badHostKeyException}")
    except Exception as e:
        print(f"Operation error: {e}")
    finally:
        ssh.close()


def parse_system_info(data: str):
    os_name_match = re.search(r'OS:\s*\w+\s+\d+(\.\d+)*', data)
    os_info = os_name_match.group(0).split('OS: ')[1] if os_name_match else "Unknown"

    hostname_match = re.search(r'HOSTNAME:\s(\S*)', data)
    hostname = hostname_match.group(1) if hostname_match else ""

    # Swap 정보 추출
    swap_match = re.search(r'SWAP:\s*(\d+)', data)
    swap_size = "" if swap_match and swap_match.group(1) == "0" else swap_match.group(1)

    # import pdb;pdb.set_trace()
    mp_match = re.search(r'Mount Point:\s\s*(.*)', data)
    if mp_match:
        mp_list = mp_match.group(1).split() if mp_match else []
    else:
        mp_list = ''
    # NAS 정보 추출
    nas_match = re.search(r'NAS:\s*(\d+)\s+(/[^ ]+)', data)
    nas_size = nas_match.group(1) if nas_match else ""
    nas_point = nas_match.group(2) if nas_match else ""

    # IP 정보 추출
    ip_match = re.search(r'IPs:\s*(.*)', data)
    if ip_match:
        ip_list = ip_match.group(1).split() if ip_match else []
    else:
        ip_list = ''

    system_info = {
        ip_list[0]: {
            "OS": os_info,
            "hostname": hostname,
            "swap": swap_size,
            "MountPoint": mp_list,
            "NASsize": nas_size,
            "NASpoint": nas_point,
            "IPs": ip_list
        }
    }
    systems_info.update(system_info)


def get_system_info(servers: list) -> dict:
    for server in servers:
        hostname = server['ip']
        user = server['user']
        password = server['password']
        port = server['port']
        get_server_info(hostname=hostname, port=port, user=user, password=password)
    return systems_info
