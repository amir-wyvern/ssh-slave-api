from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException
)
from schemas import (
    CreateSsh,
    DeleteSsh,
    BlockSsh,
    HTTPError
)
from auth.auth import get_auth
import subprocess
import os


router = APIRouter(prefix='/ssh', tags=['ssh'])


@router.post('/create', responses= {status.HTTP_409_CONFLICT: {'model': HTTPError}, status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}})
def create_account(request: CreateSsh, token: str= Depends(get_auth)):
    
    for user in request.users:

        home_dir = "/home/" + user.username
        username = user.username

        if os.path.isdir(home_dir):
            raise HTTPException(status_code= status.HTTP_409_CONFLICT, detail={'message': f'user {user.username} already exist', 'internal_code': 3406})
    
    submited_users = []
    for user in request.users:

        home_dir = "/home/" + user.username
        username = user.username 
        
        try:
            subprocess.run(["useradd", "-m", "-s", "/usr/bin/rbash","-d", home_dir, username])

            passwd_cmd = ['passwd', username]
            p = subprocess.Popen(passwd_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate(input=f"{user.password}\n{user.password}".encode())

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'message': f'create user [{user.username}] , successfull users [{submited_users}] \nexception [{e}]', 'internal_code': 3511})
        
        if p.returncode != 0:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f"Failed to set password for user {user.username}: {stderr.decode()}\n successfull users [{submited_users}]", 'internal_code': 3502})
        
        submited_users.append(user)

    return f"users {submited_users} successfuly created"

@router.delete('/delete' ,responses= {status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}, status.HTTP_404_NOT_FOUND: {'model': HTTPError}})
def delete_account(request: DeleteSsh, token: str= Depends(get_auth)):

    for user in request.users:
    
        if not os.path.isdir(f'/home/{user}'):
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail={'message': f'user {user} is not exist', 'internal_code': 3403})

    submited_users = []
    for user in request.users:

        failed_count = 0
        while True:

            try:
                userdel_cmd = ['userdel', '-r', user]
                subprocess.run(['usermod', '-a', '-G', 'blockUsers', user])
                subprocess.run(['pkill', '-u', user])

                p = subprocess.Popen(userdel_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()

            except Exception as e:

                failed_count += 1
                if failed_count == 3:
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to delete user {user}: {stderr.decode()}\nsuccessfull users [{submited_users}]\nerror [{e}]', 'internal_code': 3503})
            
                continue

            if p.returncode != 0:
                failed_count += 1
                if failed_count == 3:
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to delete user {user}: {stderr.decode()}\nsuccessfull users [{submited_users}]\n error [userdel command error]', 'internal_code': 3503})
                
                continue

            break

        submited_users.append(user)

    return f"Users {submited_users} deleted successfully"


@router.post('/block')
def block_account(request: BlockSsh, token: str= Depends(get_auth)):

    for user in request.users:
    
        if not os.path.isdir(f'/home/{user}'):
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail={'message': f'user {user} is not exist', 'internal_code': 3403})

    submited_users = []
    for user in request.users:

        failed_count = 0
        while True:

            try: 
                subprocess.run(['usermod', '-a', '-G', 'blockUsers', user])
                subprocess.run(['pkill', '-u', user])

            except Exception as e:
                failed_count += 1

                if failed_count == 3:
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to block user {user}\nsuccessfull users [{submited_users}]\nerror [{e}]', 'internal_code': 3503})
                
                continue

            break
        
        submited_users.append(user)

    return f"Users {submited_users} blocked successfully"


@router.post('/unblock')
def unblock_account(request: BlockSsh, token: str= Depends(get_auth)):


    for user in request.users:
    
        if not os.path.isdir(f'/home/{user}'):
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail={'message': f'user {user} is not exist', 'internal_code': 3403})


    submited_users = []
    for user in request.users:

        failed_count = 0
        while True:

            try: 
                subprocess.run(['gpasswd', '-d', request.username, 'blockUsers'])

            except Exception as e:
                failed_count += 1

                if failed_count == 3:
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to unblock user {user}\nsuccessfull users [{submited_users}]\nerror [{e}]', 'internal_code': 3503})
                
                continue

            break
        
        submited_users.append(user)
    
    return f"Users {submited_users} unblocked successfully"
