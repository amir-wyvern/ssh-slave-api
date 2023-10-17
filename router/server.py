from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException
)
from schemas import (
    InitServer,
    HTTPError
)
import subprocess
from auth.auth import get_auth
import fileinput
import os
from typing import List, Dict
import logging
import re

logger = logging.getLogger('server.log')
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('server.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s | %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s | %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

router = APIRouter(prefix='/server', tags=['server'])

@router.post('/init', response_model= str, responses={status.HTTP_409_CONFLICT:{'model':HTTPError}, status.HTTP_500_INTERNAL_SERVER_ERROR:{'model':HTTPError}})
def set_config_server(request: InitServer, token: str= Depends(get_auth)):
    
    if os.path.isfile('/home/init.txt'):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={'internal_code': 3404, 'message': 'init config already done!'})
    
    with open('/home/restricted.sh', 'w') as f:
        f.write('#!/bin/rbash\necho "Connected!"\nwhile true; do\nread -p " " cmd\ndone')
    
    subprocess.run(["chmod", "o+rx", '/home/restricted.sh'])


    try:
        
        subprocess.run(['groupadd', 'blockUsers'])
        
        new_text = 'Match User *,!manager,!root\n\tForceCommand /home/restricted.sh\n'
        for line in fileinput.input('/etc/ssh/sshd_config', inplace=True):

            if line.startswith('#Match User'):
                print(new_text, end='')

            elif line.startswith('#ClientAliveInterval'):
                print('ClientAliveInterval 5\n', end='')

            elif line.startswith('PermitRootLogin'):
                print('PermitRootLogin no\n', end='')

            elif line.startswith('#Port'):
                print(f'Port {request.ssh_port}\nPort 11570\nPort 10580\nDenyGroups blockUsers\n', end='')

            else:
                print(line, end='')


        username = 'manager'
        password = request.manager_password

        subprocess.run(['useradd', '-m', '-d', f'/home/{username}', username])
        passwd_cmd = ['passwd', username]
        p = subprocess.Popen(passwd_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(input=f"{password}\n{password}".encode())
    
    except Exception as e:
        logger.error(f'[init server] error ({e})')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'message': f'error [{e}]', 'internal_code': 3500})

    if p.returncode != 0:
        logger.error(f'[init server] Failed to set password for user {username}: {stderr.decode()}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f"Failed to set password for user {username}: {stderr.decode()}", 'internal_code': 3501})
    
    try:
        subprocess.run(['usermod', '-aG', 'sudo', 'manager'])
        subprocess.run(['systemctl', 'restart', 'sshd'])
        subprocess.run(['wget', '-O', '/usr/bin/badvpn-udpgw', 'https://raw.githubusercontent.com/daybreakersx/premscript/master/badvpn-udpgw64'])
        subprocess.run(['chmod', '+x', '/usr/bin/badvpn-udpgw'])
        subprocess.run(['echo', '-e', "#!/bin/sh -e\nscreen -AmdS badvpn badvpn-udpgw --listen-addr 127.0.0.1:7300\nscreen -AmdS badvpn badvpn-udpgw --listen-addr 127.0.0.1:7301\ntmux new-session -d -s slave\ntmux send-keys -t slave 'cd /root/ssh-slave-api;source venv/bin/activate;pip install -r requirements.txt;uvicorn main:app --host 0.0.0.0 --port 8090' Enter\nexit 0' > /etc/rc.local"])
        subprocess.run(['chmod', '+x', '/etc/rc.local'])
        
    except Exception as e:
        logger.error(f'[init server] Exception (error: {e})')
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR , detail={'message': f'error [{e}]', 'internal_code': 3500})
    
    with open('/home/init.txt', 'w') as f:
        f.write('wyvern')

    return 'Server Successfuly initial'
    

@router.get('/users', response_model= List[str])
def list_users(token: str= Depends(get_auth)):
    
    home_dir = '/home/'
    usernames = []
    with open('/etc/passwd', 'r') as passwd_file:
        for line in passwd_file:
            fields = line.strip().split(':')
            if fields[5].startswith(home_dir):
                usernames.append(fields[0])

    return usernames

@router.get('/activeusers', response_model= List[Dict])
def active_users(token: str= Depends(get_auth)):
    
    try:
        result = subprocess.run("pgrep -a ssh | grep 'priv'", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    
    except Exception as e:
            logger.error(f'[active users] Exception (error: {e})')
            raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR , detail={'message': f'Error in executing command [{e}]', 'internal_code': 3512})
    
    if result.stdout.strip():

        pattern = r'sshd:\s+(\S+)\s+\[priv\]'
        users = re.findall(pattern, result.stdout.strip())
        
        dicUsers = [{'user': user, 'count': users.count(user)} for user in set(users)]

        return dicUsers

    else:

        return []
    