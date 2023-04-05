from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from schemas import (
    CreateSsh,
    DeleteSsh,
    BlockSsh
)

router = APIRouter(prefix='/v2ray', tags=['v2ray'])

@router.post('/create')
def user_info(request: CreateSsh):
    
    return True

@router.delete('/delete' )
def update_user_profile(request: DeleteSsh):

    return True

@router.post('/block')
def update_user_password(request: BlockSsh):

    return True
