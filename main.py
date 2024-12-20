from fastapi import FastAPI, HTTPException
from routers.endpoints import router

app = FastAPI()

app.include_router(router)