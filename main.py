from fastapi import FastAPI
from src.routes import produtos, movimentacoes


app = FastAPI()

app.include_router(movimentacoes.router)
app.include_router(produtos.router)

if __name__ == "__main__":
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)