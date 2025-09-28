from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from src.models import BuscaMovimentacoes
from src.pool.pool import get_db
from src.pool.models import Movimentacoes, Produtos
from src.models import Movimentacao, DeleteById
from datetime import datetime
router = APIRouter()

@router.post("/get-movimentacoes")
async def get_movimentacoes(filtros: BuscaMovimentacoes | None = None, db: AsyncSession = Depends(get_db)):
    """
    Rota para buscar as movimentações com base nos filtros fornecidos.
    """
    try:
        query = (
            select(Movimentacoes, Produtos)
            .join(Produtos, Produtos.id == Movimentacoes.produto_id)
            )

        if filtros:
            if filtros.data_inicio is not None:
                query = query.where(func.date(Movimentacoes.data_movimentacao) >= filtros.data_inicio)
            
            if filtros.data_fim is not None:
                query = query.where(func.date(Movimentacoes.data_movimentacao) <= filtros.data_fim)
        
        result = await db.execute(query)
        rows = result.all()

        if not rows:
            raise HTTPException(status_code=204, detail="Não foi encontrado nenhuma movimentação.")
        
        movimentacoes = []
        for mov, prod in rows:
            movimentacoes.append({
                "id": mov.id,
                "tipo": mov.tipo,
                "produto_id": mov.produto_id,
                "nome_produto": prod.nome_produto,
                "descricao": prod.descricao,
                "quantidade": mov.quantidade,
                "valor_unidade": mov.valor_und,
                "valor_total": mov.valor_total,
                "data_movimentacao": mov.data_movimentacao
            })

        return {
            "detail": "sucesso",
            "movimentacoes": movimentacoes
        }
    except HTTPException as e:
        print(f"Erro ao executar a consulta: {e}")
        raise e
    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        raise HTTPException(status_code=500, detail="Erro ao realizar busca.")


@router.post("/add-movimentacao")
async def add_movimentacao(
    form_data: Movimentacao = Body(...), 
    db: AsyncSession = Depends(get_db)
):
    """
    Rota para adicionar um nova movimentação ao banco de dados.
    """
    print(form_data)

    try:
        produto = await db.get(Produtos, form_data.produto_id)
        
        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        nome_produto = produto.nome_produto
        descricao = produto.descricao
        id_produto = produto.id
        quantidade_atual = produto.quantidade
    except Exception as e:
        print(f"Erro ao procurar produto: {e}")
        raise HTTPException(status_code=500, detail="Erro ao procurar produto.")

    if form_data.tipo == 'saida' and (form_data.quantidade > quantidade_atual):
        raise HTTPException(status_code=400, detail="Quantidade de produtos insuficiente no estoque.")

    try:
        data = datetime.fromisoformat(form_data.data_movimentacao)
        nova_movimentacao = Movimentacoes(
            tipo=form_data.tipo,
            produto_id=form_data.produto_id,
            data_movimentacao=data,
            quantidade=form_data.quantidade,
            valor_und=form_data.valor_und,
            valor_total=form_data.quantidade * form_data.valor_und
        )
        
        db.add(nova_movimentacao)

        # Atualiza a quantidade do produto
        if form_data.tipo == 'entrada':
            produto.quantidade += form_data.quantidade
        elif form_data.tipo == 'saida':
            produto.quantidade -= form_data.quantidade

        db.add(produto)  # Marca produto como modificado

        await db.commit()
        await db.refresh(nova_movimentacao)

        return {
            "detail": "Movimentação adicionada com sucesso.",
            "movimentacao": {
                "id": nova_movimentacao.id,
                "tipo": nova_movimentacao.tipo,
                "nomeProduto": nome_produto,
                "idProduto": id_produto,
                "descricao": descricao,
                "dataMovimentacao": nova_movimentacao.data_movimentacao,
                "quantidade": nova_movimentacao.quantidade,
                "valorUnidade": nova_movimentacao.valor_und,
                "valorTotal": nova_movimentacao.valor_total
            }
        }

    except HTTPException as e:
        print(f"Erro ao adicionar movimentação: {e}")
        raise e
    except Exception as e:
        print(f"Erro ao adicionar movimentação: {e}")
        raise HTTPException(status_code=500, detail="Erro ao adicionar movimentação.")

@router.put("/update-movimentacao/{movimentacao_id}")
async def update_movimentacao(
    movimentacao_id: int,
    form_data: Movimentacao = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Rota para atualizar uma movimentação pelo ID.
    """
    try:
        # Busca a movimentação pelo ID
        result = await db.execute(select(Movimentacoes).where(Movimentacoes.id == movimentacao_id))
        movimentacao = result.scalars().first()

        if not movimentacao:
            raise HTTPException(status_code=404, detail="Movimentação não encontrada.")

        # Busca o produto associado
        produto = await db.get(Produtos, form_data.produto_id)
        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado")

        nome_produto = produto.nome_produto

        # Armazena valores antigos antes de atualizar
        quantidade_antiga = movimentacao.quantidade
        tipo_antiga = movimentacao.tipo

        # Converte a data enviada para datetime
        data_atualizada = datetime.fromisoformat(form_data.data_movimentacao)

        # Atualiza os campos da movimentação
        movimentacao.tipo = form_data.tipo
        movimentacao.produto_id = form_data.produto_id
        movimentacao.data_movimentacao = data_atualizada
        movimentacao.quantidade = form_data.quantidade
        movimentacao.valor_und = form_data.valor_und
        movimentacao.valor_total = form_data.quantidade * form_data.valor_und

        db.add(movimentacao)

        # Ajusta o estoque: desfaz a movimentação antiga
        if tipo_antiga == 'entrada':
            produto.quantidade -= quantidade_antiga
        elif tipo_antiga == 'saida':
            produto.quantidade += quantidade_antiga

        # Aplica a nova movimentação
        if form_data.tipo == 'entrada':
            produto.quantidade += form_data.quantidade
        elif form_data.tipo == 'saida':
            if form_data.quantidade > produto.quantidade:
                raise HTTPException(status_code=400, detail="Quantidade de produtos insuficiente no estoque.")
            produto.quantidade -= form_data.quantidade

        db.add(produto)
        await db.commit()
        await db.refresh(movimentacao)

        return {
            "detail": "Movimentação atualizada com sucesso.",
            "movimentacao": {
                "id": movimentacao.id,
                "tipo": movimentacao.tipo,
                "idProduto": movimentacao.produto_id,
                "nomeProduto": nome_produto,
                "descricao": produto.descricao,
                "quantidade": movimentacao.quantidade,
                "dataMovimentacao": movimentacao.data_movimentacao,
                "valorUnidade": movimentacao.valor_und,
                "valorTotal": movimentacao.valor_total
            }
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro ao atualizar movimentação: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar movimentação.")

@router.delete("/delete-movimentacao")
async def delete_movimentacao(
    model_delete: DeleteById,
    db: AsyncSession = Depends(get_db)
):
    """
    Rota para deletar um movimentacao pelo ID.
    """
    try:
        # Busca o movimentacao pelo ID
        result = await db.execute(select(Movimentacoes).where(Movimentacoes.id == model_delete.id))
        movimentacao = result.scalars().first()

        if not movimentacao:
            raise HTTPException(status_code=404, detail="Movimentação não encontrada.")
        
        # Busca o produto relacionado
        result = await db.execute(select(Produtos).where(Produtos.id == movimentacao.produto_id))
        produto = result.scalars().first()

        if not produto:
            raise HTTPException(status_code=404, detail="Produto nao encontrado.")

        # Atualiza a quantidade do produto
        if movimentacao.tipo == 'entrada':
            produto.quantidade -= movimentacao.quantidade
        elif movimentacao.tipo == 'saida':
            produto.quantidade += movimentacao.quantidade

        db.add(produto)

        # Deleta a movimentação
        await db.delete(movimentacao)
        await db.commit()

        return {"detail": f"Movimentação '{movimentacao.id}' deletada com sucesso."}

    except HTTPException as e:
        print(f"Erro ao deletar movimentação: {e}")
        raise e
    except Exception as e:
        print(f"Erro ao deletar movimentação: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar movimentação.")