from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from os import environ as env

from routes import router

app = FastAPI()

app.include_router(router)

app.mount(
    "/",
    StaticFiles(directory="web", html=True),
    name="frontend"
)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=env.get("HOST", "0.0.0.0"),
        port=env.get("PORT", 8230)
    )
