from fastapi import FastAPI
from src.shared.auth import router as auth_router
from src.shared.userdb_handler import router as userdb_router
from src.shared.documentdb_handler import router as documentdb_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(userdb_router)
app.include_router(documentdb_router)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}