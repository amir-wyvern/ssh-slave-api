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
import logging
import os

# Create a file handler to save logs to a file

file_handler = logging.FileHandler('ssh.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s | %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger('ssh.log')
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s | %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.setLevel(logging.INFO)

router = APIRouter(prefix='/ssh', tags=['ssh'])


@router.post('/test', responses= {status.HTTP_409_CONFLICT: {'model': HTTPError}, status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}})
def test(request: DeleteSsh, token: str= Depends(get_auth)):
    
    logger.info(f'[create] receive signal [users: {request.users}]')
    return 'ok'    

@router.post('/create', responses= {status.HTTP_409_CONFLICT: {'model': HTTPError}, status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}})
def create_account(request: CreateSsh, token: str= Depends(get_auth)):
    
    logger.info(f'[create] receive signal [users: {request.users}]')

    for user in request.users:

        home_dir = "/home/" + user.username
        username = user.username

        if os.path.isdir(home_dir):
            logger.error(f'- [create] user already exist [username: {user}]')
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
            
            logger.info(f'- [create] successfully created account [username: {user}]')

        except Exception as e:
            logger.error(f'- [create] failed created [username: {user}] - [error: {e}]')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'message': f'failed in create user [{user.username}] , successfull creation users [{submited_users}] \nexception [{e}]', 'internal_code': 3511})
        
        if p.returncode != 0:
            logger.error(f'- [craete] failed to set password [username: {user}] - [error: return code 0]')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f"Failed to set password for user {user.username}: {stderr.decode()}\n successfull users [{submited_users}]", 'internal_code': 3502})
        
        logger.info(f'- [create] successfully set password [username: {user}]')

        submited_users.append(user)
    
    logger.info(f'# [create] successfully created users')
    
    return f"users {submited_users} successfuly created"

@router.delete('/delete' ,responses= {status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}, status.HTTP_404_NOT_FOUND: {'model': HTTPError}})
def delete_account(request: DeleteSsh, token: str= Depends(get_auth)): 

    logger.info(f'[delete] receive signal [users: {request.users}]')
    
    for user in request.users:
        
        if not os.path.isdir(f'/home/{user}'):
            logger.error(f'- [delete] user is not exist [username: {user}]')
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
                    logger.error(f'- [delete] failed to delete user [username: {user}] - [error: {e}]')
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to delete user {user}: {stderr.decode()}\nsuccessfull users [{submited_users}]\nerror [{e}]', 'internal_code': 3503})
            
                continue

            if p.returncode != 0:
                failed_count += 1
                if failed_count == 3:
                    logger.error(f'- [delete] failed to delete user [username: {user}] - [error: return code 0')
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to delete user {user}: {stderr.decode()}\nsuccessfull users [{submited_users}]\n error [userdel command error]', 'internal_code': 3503})
                
                continue

            break
        logger.info(f'- [delete] successfully delete user [username: {user}]')
        submited_users.append(user)

    logger.info(f'# [delete] successfully delete users')
    return f"Users {submited_users} deleted successfully"


@router.post('/block')
def block_account(request: BlockSsh, token: str= Depends(get_auth)):

    logger.info(f'[block] receive signal [users: {request.users}]')

    for user in request.users:
    
        if not os.path.isdir(f'/home/{user}'):
            logger.error(f'- [block] user is not exist [username: {user}] ')
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
                    logger.error(f'- [block] failed to block user [username: {user} -error: {e}]')
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to block user {user}\nsuccessfull users [{submited_users}]\nerror [{e}]', 'internal_code': 3503})
                
                continue

            break
        
        logger.info(f'- [block] successfully blocked user [username: {user}]')
        submited_users.append(user)

    logger.info(f'# [block] successfully blocked users')
    return f"Users {submited_users} blocked successfully"


@router.post('/unblock')
def unblock_account(request: BlockSsh, token: str= Depends(get_auth)):

    logger.info(f'[unblock] receive signal [users: {request.users}]')

    for user in request.users:
    
        if not os.path.isdir(f'/home/{user}'):
            logger.error(f'- [unblock] user is not exist [username: {user}] ')
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail={'message': f'user {user} is not exist', 'internal_code': 3403})


    submited_users = []
    for user in request.users:

        failed_count = 0
        while True:

            try: 
                subprocess.run(['gpasswd', '-d', user, 'blockUsers'])

            except Exception as e:
                failed_count += 1

                if failed_count == 3:
                    logger.error(f'- [unblock] failed to unblock user [username: {user} -error: {e}]')
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to unblock user {user}\nsuccessfull users [{submited_users}]\nerror [{e}]', 'internal_code': 3503})
                
                continue

            break
        
        logger.info(f'- [unblock] successfully unblocked user [username: {user}]')
        submited_users.append(user)
    
    logger.info(f'# [unblock] successfully unblocked users')
    return f"Users {submited_users} unblocked successfully"
