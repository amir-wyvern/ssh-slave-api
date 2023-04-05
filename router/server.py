from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from schemas import (
    SshAccount,
    UserResponse,
    DeleteSsh,
    BlockSsh,
    InitServer
)
import subprocess
from auth.auth import get_auth
import configparser
import fileinput
import os
from typing import List
router = APIRouter(prefix='/server', tags=['server'])

@router.post('/init')
def user_info(request: InitServer, token: str= Depends(get_auth)):
    
    if os.path.isfile('/home/init.txt'):
        raise HTTPException(status_code=404, detail={'internal_code': 1404, 'message': 'init config already done!'})
    
    with open('/home/restricted.sh', 'w') as f:
        f.write('#!/bin/rbash\necho "Connected!"\nwhile true; do\nread -p " " cmd\ndone')
    subprocess.run(["chmod", "o+rx", '/home/restricted.sh'])
    try:
        
        subprocess.run(['groupadd', 'blockUsers'])
        
        new_text = 'Match User *,!manager,!root\n\tForceCommand /home/restricted.sh\n'
        for line in fileinput.input('/etc/ssh/sshd_config', inplace=True):

            if line.startswith('Match User'):
                print(new_text, end='')

            if line.startswith('#Match User'):
                print(new_text, end='')

            elif line.startswith('ClientAliveInterval'):
                print('ClientAliveInterval 5\n', end='')

            elif line.startswith('PermitRootLogin'):
                print('PermitRootLogin no\n', end='')

            elif line.startswith('Port'):
                print(f'Port {request.ssh_port}\nDenyGroups blockUsers\n', end='')

            else:
                print(line, end='')

        with open('/home/init.txt', 'w') as f:
            f.write('wyvern')

        username = 'manager'
        password = request.manager_password

        subprocess.run(['useradd', '-m', '-d', f'/home/{username}', username])
        passwd_cmd = ['passwd', username]
        p = subprocess.Popen(passwd_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(input=f"{password}\n{password}".encode())

        if p.returncode != 0:
            raise HTTPException(status_code=500 ,detail={'message': f"Failed to set password for user {username}: {stderr.decode()}", 'internal_code': 1500})
        
        subprocess.run(['usermod', '-aG', 'sudo', 'manager'])
        subprocess.run(['systemctl', 'restart', 'sshd'])
    
        return 'Server Successfuly initial'
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={'message': str(Exception), 'internal_code': 1500})
    

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

