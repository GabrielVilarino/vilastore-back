# models.py

from sqlalchemy import Column, Integer, String, Float, Boolean, Enum, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Movimentacoes(Base):
    __tablename__ = "movimentacao"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    tipo = Column(String(10), nullable=False)
    produto_id = Column(Integer, nullable=False)
    data_movimentacao = Column(DateTime, nullable=False)
    quantidade = Column(Integer, nullable=False)
    valor_und = Column(Float, nullable=False)
    valor_total = Column(Float, nullable=False)

class Produtos(Base):
    __tablename__ = "estoque"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    nome_produto = Column(String(100), nullable=False)
    quantidade = Column(Integer, nullable=False)
    descricao = Column(String(50), nullable=True)
