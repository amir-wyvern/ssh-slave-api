from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException
)
from schemas import (
    CreateSshResponse,
    DeleteSshResponse,
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
  

@router.post('/create',  response_model= CreateSshResponse, responses= {status.HTTP_409_CONFLICT: {'model': HTTPError}, status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}})
def create_account(request: CreateSsh, token: str= Depends(get_auth)):
    
    logger.info(f'[create] receive signal (users: {request.users})')

    processing_users = []
    exists_users = []
    for user in request.users:

        home_dir = "/home/" + user.username
        username = user.username

        if os.path.isdir(home_dir):
            logger.error(f'- [create] user already exist (username: {user} -ignore: {request.ignore_exists_users})')
            if request.ignore_exists_users:
                exists_users.append(user.username)
                continue

            raise HTTPException(status_code= status.HTTP_409_CONFLICT, detail={'message': f'user {user.username} already exist', 'internal_code': 3406})

        processing_users.append(user)

    submited_users = []
    for user in processing_users:

        home_dir = "/home/" + user.username
        username = user.username 
        
        try:
            subprocess.run(["useradd", "-m", "-s", "/usr/bin/rbash","-d", home_dir, username])

            passwd_cmd = ['passwd', username]
            p = subprocess.Popen(passwd_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate(input=f"{user.password}\n{user.password}".encode())
            
            logger.info(f'- [create] successfully created account (username: {user})')

        except Exception as e:
            logger.error(f'- [create] failed created (username: {user} - error: {e})')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'message': f'failed in create user [{user.username}] -successfull creation users {submited_users} -exists_users: {exists_users} -error [{e}]', 'internal_code': 3511})

        if p.returncode != 0:
            logger.error(f'- [craete] failed to set password (username: {user} -error: return code 0)')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f"Failed to set password for user {user.username}: {stderr.decode()} -successfull users {submited_users} -exists_users: {exists_users} -error [returncode 0]", 'internal_code': 3502})
        
        logger.info(f'- [create] successfully set password (username: {user})')

        submited_users.append(username)

    logger.info(f'# [create] successfully created users')
    
    return CreateSshResponse(exists_users= exists_users, success_users= submited_users)


@router.delete('/delete', response_model= DeleteSshResponse, responses= {status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}, status.HTTP_404_NOT_FOUND: {'model': HTTPError}})
def delete_account(request: DeleteSsh, token: str= Depends(get_auth)): 

    logger.info(f'[delete] receive signal (users: {request.users})')
    
    not_exists_users = []
    processing_users = []

    for user in request.users:
        
        if not os.path.isdir(f'/home/{user}'):
            logger.error(f'- [delete] user is not exist (username: {user})')
            
            if request.ignore_not_exists_users:
                not_exists_users.append(user)
                continue

            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail={'message': f'user {user} is not exist', 'internal_code': 3403})
        
        processing_users.append(user)

    submited_users = []    
    for user in processing_users:

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
                    logger.error(f'- [delete] failed to delete user (username: {user} -error: {e})')
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to delete user [{user}] -successfull users [{submited_users}] -not_exists_users: {not_exists_users} -error [stderr: {stderr.decode()}, e: {e}]', 'internal_code': 3503})
            
                continue

            if p.returncode != 0:
                failed_count += 1
                if failed_count == 3:
                    logger.error(f'- [delete] failed to delete user (username: {user} -error: return code 0)')
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to delete user [{user}] -successfull users [{submited_users}] -not_exists_users: {not_exists_users} -error [stderr: {stderr.decode()}, e: returncode 0]', 'internal_code': 3503})
                
                continue

            break
            
        submited_users.append(user)

        logger.info(f'- [delete] successfully delete user (username: {user})')

    logger.info(f'# [delete] successfully delete users')

    return DeleteSshResponse(not_exists_users= not_exists_users, success_users= submited_users)


@router.post('/block', response_model= DeleteSshResponse, responses= {status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}, status.HTTP_404_NOT_FOUND: {'model': HTTPError}})
def block_account(request: BlockSsh, token: str= Depends(get_auth)):

    logger.info(f'[block] receive signal (users: {request.users})')

    not_exists_users = []
    processing_users = []

    for user in request.users:
    
        if not os.path.isdir(f'/home/{user}'):
            logger.error(f'- [block] user is not exist (username: {user}) ')

            if request.ignore_not_exists_users:
                not_exists_users.append(user)
                continue

            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail={'message': f'user {user} is not exist', 'internal_code': 3403})
        
        processing_users.append(user)

    submited_users = []
    for user in processing_users:

        failed_count = 0
        while True:

            try: 
                subprocess.run(['usermod', '-a', '-G', 'blockUsers', user])
                subprocess.run(['pkill', '-u', user])

            except Exception as e:
                failed_count += 1

                if failed_count == 3:
                    logger.error(f'- [block] failed to block user (username: {user} -error: {e})')
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to block user [{user}] -successfull users [{submited_users}] -not_exists_users: {not_exists_users} -error [{e}]', 'internal_code': 3503})
                
                continue

            break
        
        submited_users.append(user)
        
        logger.info(f'- [block] successfully blocked user (username: {user})')

    logger.info(f'# [block] successfully blocked users')
    return DeleteSshResponse(not_exists_users= not_exists_users, success_users= submited_users)


@router.post('/unblock', response_model= DeleteSshResponse, responses= {status.HTTP_500_INTERNAL_SERVER_ERROR: {'model': HTTPError}, status.HTTP_404_NOT_FOUND: {'model': HTTPError}})
def unblock_account(request: BlockSsh, token: str= Depends(get_auth)):

    logger.info(f'[unblock] receive signal (users: {request.users})')

    not_exists_users = []
    processing_users = []

    for user in request.users:
    
        if not os.path.isdir(f'/home/{user}'):
            logger.error(f'- [unblock] user is not exist (username: {user})')

            if request.ignore_not_exists_users:
                not_exists_users.append(user)
                continue
        
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail={'message': f'user {user} is not exist', 'internal_code': 3403})
        
        processing_users.append(user)

    submited_users = []
    for user in processing_users:

        failed_count = 0
        while True:

            try: 
                subprocess.run(['gpasswd', '-d', user, 'blockUsers'])

            except Exception as e:
                failed_count += 1

                if failed_count == 3:
                    logger.error(f'- [unblock] failed to unblock user (username: {user} -error: {e})')
                    raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR ,detail={'message': f'Failed to unblock user [{user}] -successfull users [{submited_users}] -not_exists_users: {not_exists_users} -error [{e}]', 'internal_code': 3503})
                
                continue

            break

        submited_users.append(user)
        
        logger.info(f'- [unblock] successfully unblocked user (username: {user})')
    
    logger.info(f'# [unblock] successfully unblocked users')
    
    return DeleteSshResponse(not_exists_users= not_exists_users, success_users= submited_users)
