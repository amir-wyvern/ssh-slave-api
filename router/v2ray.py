from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from schemas import (
    SshAccount,
    DeleteSsh,
)

router = APIRouter(prefix='/v2ray', tags=['v2ray'])

@router.post('/create')
def create_account(request: SshAccount):
    
    return True

@router.delete('/delete' )
def delete_account(request: DeleteSsh):

    return True
