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

    users : List[SshAccount]

class DeleteSsh(BaseModel):

    users : List[str]
    
class BlockSsh(BaseModel):

    users : List[str]


class HTTPError(BaseModel):

    message: str 
    internal_code: str

    class Config:
        schema_extra = {
            "example": {"detail": "HTTPException raised.", 'internal_code':1001},
        }
        
