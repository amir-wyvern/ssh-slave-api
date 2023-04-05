from pydantic import BaseModel

class InitServer(BaseModel):

    ssh_port: int
    manager_password: str

class UserResponse(BaseModel):

    username: str

class SshAccount(BaseModel):

    username : str
    password: str

class DeleteSsh(BaseModel):

    username : str

class BlockSsh(BaseModel):

    username : str

class HTTPError(BaseModel):

    message: str 
    internal_code: str

    class Config:
        schema_extra = {
            "example": {"detail": "HTTPException raised.", 'internal_code':1001},
        }
        
