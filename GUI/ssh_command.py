import time
import re
import paramiko
import winrm

def get_server_info(ip, hostname, user, password, port=22) -> dict:
    """
    SSH를 통해 서버에 접속하여 시스템 정보를 수집하는 함수.

    Args:
        hostname (str): 서버의 호스트 이름 또는 IP 주소.
        user (str): SSH 로그인 사용자 이름.
        password (str): SSH 로그인 비밀번호.
        port (int): SSH 포트 (기본값은 22).

    Returns:
        dict: 수집된 시스템 정보가 포함된 사전.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=ip, port=port, username=user, password=password, timeout=3)
        shell = ssh.invoke_shell()
        shell.send(
            "echo START;"
            "echo OS:`hostnamectl | grep 'Operating System:' | awk -F': ' '{print $2}' | sed 's/ Linux//' | sed 's/ (.*)//' | sed 's/ LTS//'`;"
            "echo HOSTNAME:`hostname`;"
            "echo SWAP:`free -k|grep -i swap|awk '{print int($2/1024/1024+0.5)}'`; "
            "echo NAS:`df -k | grep ^[1,2]|awk '{print int($2/1024/1024+0.5),$6}'`;"
            "echo Mount Point:`df -h | grep -vE '^Filesystem|/boot|/$|swap|tmp' | grep -Ff <(awk '{print $2}' /etc/fstab | grep -v -E 'UUID=|swap|/boot|/ ') | awk '{print $1, $NF, $2}'`;"
            "echo IPs:`hostname -I`;"
            "echo END\n"
        )

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
        print(f"Authentication failed for {hostname}, please verify your credentials")
    except paramiko.SSHException as sshException:
        print(f"Unable to establish SSH connection to {hostname}: {sshException}")
    except paramiko.BadHostKeyException as badHostKeyException:
        print(f"Unable to verify server's host key for {hostname}: {badHostKeyException}")
    except Exception as e:
        print(f"Operation error on {hostname}: {e}")
        try:
            print(f"winrm 접속 시도 중 {hostname} ...")
            session = winrm.Session(f'http://{ip}:5985/wsman', auth=(user, password), transport='ntlm',
                                    read_timeout_sec=5,operation_timeout_sec=3)
            command = ("Write-Host START; "
                       "Write-Host OS:(Get-CimInstance -ClassName Win32_OperatingSystem).Caption; "
                       "Write-Host HOSTNAME:$env:COMPUTERNAME; "
                       "$swapSizeMB = (Get-CimInstance -ClassName Win32_OperatingSystem).TotalVirtualMemorySize / 1MB;Write-Host SWAP:$([math]::Round($swapSizeMB, 2)); "
                       # "Write-Host 'Mount Point:'(Get-PSDrive -PSProvider FileSystem | Where-Object {$_.Used -gt 0} | ForEach-Object {\"$($_.Name) $($_.Root) $([math]::Round(($_.Used + $_.Free)/1GB, 2))\"}); "
                       "Write-Host 'Mount Point:'(Get-PSDrive -PSProvider FileSystem | Where-Object {$_.Used -gt 0} | ForEach-Object {\"$($_.Root) $([math]::Round(($_.Used + $_.Free)/1GB, 2))GB\"}); "
                       "Write-Host IPs:(Get-NetIPAddress | Where-Object {$_.AddressFamily -eq \"IPv4\" -and $_.PrefixOrigin -eq \"Dhcp\"} | Select-Object -ExpandProperty IPAddress); "
                       "Write-Host END")
            output = session.run_ps(command)
            print(output)
            match = re.search(r'START\n([\s\S]*?)\nEND', output.std_out.decode('utf-8'), re.DOTALL)
            if match:
                data = match.group(1).strip()
                print(data)
                return win_parse_system_info(data)
            else:
                return {"error": "No valid data found between START and END markers"}

        # except winrm.exceptions.WinRMError as winrm_error:
        #     print(f"WinRM connection failed for {hostname}: {winrm_error}")
            # 알 수 없는 오류에 대한 예외 처리
            try:
                raise Exception(
                    f"Failed to connect to {hostname} using both SSH and WinRM. The system might not be Windows or there could be an unknown error.")
            except Exception as unknown_error:
                print(unknown_error)
        except Exception as unknown_winrm_error:
            print(f"An unknown error occurred while trying to connect using WinRM: {unknown_winrm_error}")
    finally:
        ssh.close()

def win_parse_system_info(data: str) -> dict:
    """
    서버에서 수집한 시스템 정보를 파싱하는 함수.

    Args:
        data (str): 수집된 원시 시스템 정보.

    Returns:
        dict: 파싱된 시스템 정보가 포함된 사전.
    """
    os_info = re.search(r'OS:(.+)', data)
    hostname = re.search(r'HOSTNAME:(.+)', data)
    swap_size = re.search(r'SWAP:(.+)', data)
    mount_points = re.search(r'Mount Point:(.+)', data)
    ip_list = re.search(r'IPs:(.+)', data)

    system_info = {
        ip_list.group(1).split()[0]: {
            "OS": os_info.group(1).strip() if os_info else "Unknown",
            "hostname": hostname.group(1).strip() if hostname else "Unknown",
            "swap": swap_size.group(1).strip() if swap_size else "",
            "MountPoint": re.findall(r'[A-Z]:\\+\s\S*', mount_points.group(1)) if mount_points else [],
            "IPs": ip_list.group(1).strip().split() if ip_list else []
        }
    }

    return system_info

def parse_system_info(data: str) -> dict:
    """
    서버에서 수집한 시스템 정보를 파싱하는 함수.

    Args:
        data (str): 수집된 원시 시스템 정보.

    Returns:
        dict: 파싱된 시스템 정보가 포함된 사전.
    """
    os_info = re.search(r'OS:(.+)', data)
    hostname = re.search(r'HOSTNAME:(.+)', data)
    swap_size = re.search(r'SWAP:(.+)', data)
    mount_points = re.search(r'Mount Point:(.+)', data)
    nas_data = re.search(r'NAS:(.+)', data).group(1)
    nas_size_list = re.findall(r'\d+(?:\.\d+)?', nas_data)
    ip_list = re.search(r'IPs:(.+)', data)
    system_info = {
        ip_list.group(1).split()[0]: {
            "OS": os_info.group(1).strip() if os_info else "Unknown",
            "hostname": hostname.group(1).strip() if hostname else "Unknown",
            "swap": swap_size.group(1).strip() if swap_size else "",
            "MountPoint": re.findall(r'(\S+\s+/\S+\s+\S+)', mount_points.group(1)) if mount_points else [],
            "NASsize": sum(int(size) for size in nas_size_list) if nas_size_list else '',
            "IPs": ip_list.group(1).strip().split() if ip_list else []
        }
    }

    return system_info


def get_system_info(servers: list) -> dict:
    """
    주어진 서버 리스트에서 시스템 정보를 수집하는 함수.

    Args:
        servers (list): 서버 정보가 포함된 리스트.

    Returns:
        dict: 모든 서버의 시스템 정보가 포함된 사전.
    """
    systems_info = {}
    for server in servers:
        ip = server['ip']
        hostname = server['hostname']
        user = server['user']
        password = server['password']
        port = server['port']
        system_info = get_server_info(ip=ip, port=port, user=user, password=password, hostname=hostname)
        if system_info:
            systems_info.update(system_info)
    return systems_info
