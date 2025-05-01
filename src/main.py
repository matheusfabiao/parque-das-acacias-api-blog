from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import posts

app = FastAPI(
    title='API Blog Parque das Acácias',
    description='API para obter os posts do blog do Parque das Acácias',
    version='0.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restringir na produção
    allow_methods=["GET"],
)

app.include_router(posts.router)

@app.get("/")
async def root():
    return {"message": "API Blog está funcionando!"}
