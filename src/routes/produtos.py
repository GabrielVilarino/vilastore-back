from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pool.pool import get_db
from models import Produto, BuscaProduto, DeleteById, UpdateById
from pool.models import Produtos, Movimentacoes

router = APIRouter()

@router.post("/get-produtos")
async def busca_produtos(filtros: BuscaProduto | None = None, db: AsyncSession = Depends(get_db)):
    """
    Rota para buscar produtos com base nos filtros fornecidos.
    """
    try:
        query = select(Produtos)

        if filtros:
            if filtros.nome:
                query = query.where(Produtos.nome_produto.ilike(f"%{filtros.nome}%"))

        result = await db.execute(query)
        produtos = result.scalars().all()

        if not produtos:
            raise HTTPException(status_code=204, detail="Não foi encontrado nenhum produto.")

        return {
            "detail": "sucesso",
            "produtos": produtos
        }
    except HTTPException as e:
        print(f"Erro ao executar a consulta: {e}")
        raise e
    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        raise HTTPException(status_code=500, detail="Erro ao realizar busca.")
    

@router.post("/add-produto")
async def add_produto(
    form_data: Produto = Body(...), 
    db: AsyncSession = Depends(get_db)
):
    """
    Rota para adicionar um novo produto ao banco de dados.
    """
    print(form_data)
    try:
        novo_produto = Produtos(
            nome_produto=form_data.nome_produto,
            valor=form_data.valor,
            quantidade=form_data.quantidade
        )
        
        db.add(novo_produto)
        await db.commit()
        await db.refresh(novo_produto)

        return {
            "detail": "Produto adicionado com sucesso.",
            "produto": {
                "id": novo_produto.id,
                "nome": novo_produto.nome_produto,
                "valor": novo_produto.valor,
                "quantidade": novo_produto.quantidade
            }
        }

    except HTTPException as e:
        print(f"Erro ao adicionar produto: {e}")
        raise e
    except Exception as e:
        print(f"Erro ao adicionar produto: {e}")
        raise HTTPException(status_code=500, detail="Erro ao adicionar produto.")
    
@router.put("/update-produto/{produto_id}")
async def update_produto(
    produto_id: int,
    form_data: Produto = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Rota para atualizar um produto pelo ID.
    """
    try:
        # Busca o produto pelo ID
        result = await db.execute(select(Produtos).where(Produtos.id == produto_id))
        produto = result.scalars().first()

        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado.")

        # Atualiza os campos
        produto.nome_produto = form_data.nome_produto
        produto.valor = form_data.valor
        produto.quantidade = form_data.quantidade

        db.add(produto)
        await db.commit()
        await db.refresh(produto)

        return {
            "detail": "Produto atualizado com sucesso.",
            "produto": {
                "id": produto.id,
                "nome": produto.nome_produto,
                "valor": produto.valor,
                "quantidade": produto.quantidade
            }
        }

    except HTTPException as e:
        print(f"Erro ao atualizar produto: {e}")
        raise e
    except Exception as e:
        print(f"Erro ao atualizar produto: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar produto.")
    
@router.delete("/delete-produto")
async def delete_produto(
    model_delete: DeleteById,
    db: AsyncSession = Depends(get_db)
):
    """
    Rota para deletar um produto pelo ID.
    """
    try:
        # Busca o produto pelo ID
        result = await db.execute(select(Produtos).where(Produtos.id == model_delete.id))
        produto = result.scalars().first()

        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado.")
        
        movimentacao = await db.execute(select(Movimentacoes).where(Movimentacoes.produto_id == produto.id))
        if movimentacao.scalars().first():
            raise HTTPException(status_code=400, detail="Produto não pode ser deletado porque possui movimentações.")

        # Deleta o produto
        await db.delete(produto)
        await db.commit()

        return {"detail": f"Produto '{produto.nome_produto}' deletado com sucesso."}

    except HTTPException as e:
        print(f"Erro ao deletar produto: {e}")
        raise e
    except Exception as e:
        print(f"Erro ao deletar produto: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar produto.")
