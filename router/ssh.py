from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from schemas import (
    SshAccount,
    DeleteSsh,
    BlockSsh,
    HTTPError
)
import subprocess
import os
import configparser


router = APIRouter(prefix='/ssh', tags=['ssh'])

@router.post('/create', responses= {500: {'model': HTTPError}})
def user_info(request: SshAccount):
    
    try:
        home_dir = "/home/" + request.username
        username = request.username
        password = request.password

        subprocess.run(["useradd", "-m", "-d", home_dir, username])

        passwd_cmd = ['passwd', username]
        p = subprocess.Popen(passwd_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(input=f"{password}\n{password}".encode())

        if p.returncode != 0:
            raise HTTPException(status_code=500 ,detail={'message': f"Failed to set password for user {username}: {stderr.decode()}", 'internal_code': 1500})
        
        else:
            return f"Password set successfully for user {username}"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={'message':f'Exception : {e}', 'internal_code': 1500})
    

@router.delete('/delete' ,responses= {500: {'model': HTTPError}})
def update_user_profile(request: DeleteSsh):

    try:
        userdel_cmd = ['userdel', '-r', request.username]
        p = subprocess.Popen(userdel_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            raise HTTPException(status_code=500 ,detail={'message': f'Failed to delete user {request.username}: {stderr.decode()}', 'internal_code': 1500})
        
        else:
            return f"User {request.username} deleted successfully"

    except Exception as e:
        raise HTTPException(status_code=500 ,detail={'message': f'Exception : {e}', 'internal_code': 1500})

@router.post('/block')
def update_user_password(request: BlockSsh):

    subprocess.run(['usermod', '-a', '-G', 'blockUsers', request.username])

    return True

@router.post('/unblock')
def update_user_password(request: BlockSsh):

    subprocess.run(['gpasswd', '-d', request.username, 'blockUsers'])
    return True



#Match User *,!wyvern,!root
#       ForceCommand /home/res.sh
