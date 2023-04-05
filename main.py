from fastapi import FastAPI
from router import server, ssh
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(ssh.router)
app.include_router(server.router)
