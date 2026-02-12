from fastapi import FastAPI
from .routers.auth import router as auth_router
from .routers.chat import router as chat_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(chat_router)
app.state.short_term_memory = ""
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
