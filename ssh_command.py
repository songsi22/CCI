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
            "echo START;"
            "echo OS:`hostnamectl | grep 'Operating System:' | awk -F': ' '{print $2}' | sed 's/ Linux//' | sed 's/ (.*)//' | sed 's/ LTS//'`;"
            "echo HOSTNAME:`hostname`;"
            "echo SWAP:`free -k|grep -i swap|awk '{print int($2/1024/1024+0.5)}'`; echo Mount Point:`grep ^[A-Z,a-z,/] /etc/fstab|egrep -v 'swap|boot' | awk '$2 != \"/\" {print $2}'`;"
            "echo NAS:`df -k | grep ^[1,2]|awk '{print int($2/1024/1024+0.5),$6}'`;"
            "echo IPs:`hostname -I`;"
            "echo END\n")

        time.sleep(1.3)  # 명령어가 실행될 시간을 줌

        output = shell.recv(4096).decode()
        match = re.search(r'START\r\n(.*?)END\r\n', output, re.DOTALL)

        if match:
            data = match.group(1).strip()
            print(data)
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

    os_match = re.search(r'OS:\S+\s+\S+', data)
    os_info = os_match.group(0).split('OS:')[1] if os_match else "Unknown"

    hostname_match = re.search(r'HOSTNAME:([^\n]+)', data)
    hostname = hostname_match.group(1) if hostname_match else ""

    # Swap 정보 추출
    swap_match = re.search(r'SWAP:([^\n]+)', data)
    swap_size = "" if swap_match and swap_match.group(1) == "0" else swap_match.group(1)

    mp_match = re.search(r'Mount Point:*([^\n]+)', data)
    if mp_match:
        mp_list = mp_match.group(1).split() if mp_match else []
    else:
        mp_list = ''
    # NAS 정보 추출
    nas_match = re.search(r'NAS:*([^\n]+)', data)
    nas_data = nas_match.group(0).split("NAS:")[1].strip()
    nas_size = re.findall(r'\d+(?:\.\d+)?', nas_data)
    nas_point = re.findall(r'/\S+', nas_data)
    mountpoint = mp_list+nas_point
    # IP 정보 추출
    ip_match = re.search(r'IPs:*([^\n]+)', data)
    if ip_match:
        ip_list = ip_match.group(1).split() if ip_match else []
    else:
        ip_list = ''
    system_info = {
        ip_list[0]: {
            "OS": os_info,
            "hostname": hostname,
            "swap": swap_size,
            "MountPoint": mountpoint,
            "NASsize": nas_size,
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
