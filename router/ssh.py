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
from auth.auth import get_auth
import subprocess
import os


router = APIRouter(prefix='/ssh', tags=['ssh'])

@router.post('/create', responses= {500: {'model': HTTPError}})
def user_info(request: SshAccount, token: str= Depends(get_auth)):
    
    try:
        home_dir = "/home/" + request.username
        username = request.username
        password = request.password

        if os.path.isdir(home_dir):
            raise HTTPException(status_code= 403, detail={'message': 'user already exist', 'internal_code': 1403})

        subprocess.run(["useradd", "-m", "-d", home_dir, username])

        passwd_cmd = ['passwd', username]
        p = subprocess.Popen(passwd_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(input=f"{password}\n{password}".encode())

        if p.returncode != 0:
            raise HTTPException(status_code=500 ,detail={'message': f"Failed to set password for user {username}: {stderr.decode()}", 'internal_code': 1500})
        
        else:
            return f"username {username} successfuly created"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={'message':f'Exception : {e}', 'internal_code': 1500})
    

@router.delete('/delete' ,responses= {500: {'model': HTTPError}})
def update_user_profile(request: DeleteSsh, token: str= Depends(get_auth)):

    try:

        userdel_cmd = ['userdel', '-r', request.username]
        subprocess.run(['usermod', '-a', '-G', 'blockUsers', request.username])
        subprocess.run(['pkill', '-u', request.username])

        p = subprocess.Popen(userdel_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        subprocess.run(['gpasswd', '-d', request.username, 'blockUsers'])

        if p.returncode != 0:
            raise HTTPException(status_code=500 ,detail={'message': f'Failed to delete user {request.username}: {stderr.decode()}', 'internal_code': 1500})
        
        else:
            return f"User {request.username} deleted successfully"

    except Exception as e:
        raise HTTPException(status_code=500 ,detail={'message': f'Exception : {e}', 'internal_code': 1500})

@router.post('/block')
def update_user_password(request: BlockSsh, token: str= Depends(get_auth)):

    subprocess.run(['usermod', '-a', '-G', 'blockUsers', request.username])

    return f'username {request.username} is blocked'

@router.post('/unblock')
def update_user_password(request: BlockSsh, token: str= Depends(get_auth)):

    subprocess.run(['gpasswd', '-d', request.username, 'blockUsers'])
    
    return f'username {request.username} is unbloked' 
