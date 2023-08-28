from pydantic import BaseModel
from typing import List

class InitServer(BaseModel):

    ssh_port: int
    manager_password: str

class UserResponse(BaseModel):

    username: str

class SshAccount(BaseModel):

    username : str
    password: str

class CreateSsh(BaseModel):

    ignore_exists_users: bool
    users : List[SshAccount]

class CreateSshResponse(BaseModel):

    exists_users: List[str]
    success_users : List[str]

class DeleteSshResponse(BaseModel):

    not_exists_users: List[str]
    success_users : List[str]

class DeleteSsh(BaseModel):

    ignore_not_exists_users: bool
    users : List[str]
    
class BlockSsh(BaseModel):

    ignore_not_exists_users: bool
    users : List[str]


class HTTPError(BaseModel):

    message: str 
    internal_code: str

    class Config:
        schema_extra = {
            "example": {"detail": "HTTPException raised.", 'internal_code':1001},
        }
        
