from fastapi import (
    APIRouter,
    Depends,
    status,
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

@router.post('/create', responses= {status.HTTP_409_CONFLICT: {'model': HTTPError}, status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}})
def create_account(request: SshAccount, token: str= Depends(get_auth)):
    
    home_dir = "/home/" + request.username
    username = request.username
    password = request.password

    if os.path.isdir(home_dir):
        raise HTTPException(status_code= status.HTTP_409_CONFLICT, detail={'message': 'user already exist', 'internal_code': 3406})
    
    try:
        subprocess.run(["useradd", "-m", "-d", home_dir, username])

        passwd_cmd = ['passwd', username]
        p = subprocess.Popen(passwd_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(input=f"{password}\n{password}".encode())

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'message': f'create user exception [{e}]', 'internal_code': 3501})
    
    if p.returncode != 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f"Failed to set password for user {username}: {stderr.decode()}", 'internal_code': 3502})
    
    else:
        return f"username {username} successfuly created"
        

@router.delete('/delete' ,responses= {status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}, status.HTTP_404_NOT_FOUND: {'model': HTTPError}})
def delete_account(request: DeleteSsh, token: str= Depends(get_auth)):

    if not os.path.isdir(f'/home/{request.username}'):
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail={'message': 'user is not exist', 'internal_code': 3403})

    userdel_cmd = ['userdel', '-r', request.username]
    subprocess.run(['usermod', '-a', '-G', 'blockUsers', request.username])
    subprocess.run(['pkill', '-u', request.username])

    p = subprocess.Popen(userdel_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if p.returncode != 0:
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to delete user {request.username}: {stderr.decode()}', 'internal_code': 3503})
    
    else:
        return f"User {request.username} deleted successfully"


@router.post('/block')
def block_account(request: BlockSsh, token: str= Depends(get_auth)):

    subprocess.run(['pkill', '-u', request.username])
    subprocess.run(['usermod', '-a', '-G', 'blockUsers', request.username])

    return f'username {request.username} is blocked'

@router.post('/unblock')
def unblock_account(request: BlockSsh, token: str= Depends(get_auth)):

    subprocess.run(['gpasswd', '-d', request.username, 'blockUsers'])
    
    return f'username {request.username} is unbloked' 
