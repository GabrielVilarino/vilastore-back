from pydantic import BaseModel
from typing import Optional
from datetime import date

class BuscaMovimentacoes(BaseModel):
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None

class BuscaProduto(BaseModel):
    nome: Optional[str] = None

class DeleteById(BaseModel):
    id: int

class UpdateById(BaseModel):
    id: int

class Produto(BaseModel):
    nome_produto: str
    quantidade: int
    descricao: str

class Movimentacao(BaseModel):
    tipo: str
    produto_id: int
    data_movimentacao: str
    quantidade: int
    valor_und: float
    valor_total: Optional[float] = None