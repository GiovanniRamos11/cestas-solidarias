from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Entrega, Item, MovimentacaoEstoque


class EntregaDuplicada(Exception):
    """A família já recebeu a cesta no mês."""

    def __init__(self, data_anterior):
        self.data_anterior = data_anterior
        super().__init__("A família já recebeu a cesta neste mês.")


class EstoqueInsuficiente(Exception):
    """Algum item da cesta não tem saldo suficiente."""

    def __init__(self, item):
        self.item = item
        super().__init__(f"Falta {item.nome} no estoque.")


def _data_da_entrega_do_mes(familia, mes):
    entrega = Entrega.objects.filter(familia=familia, mes_referencia=mes).first()
    if entrega is None:
        return None
    return timezone.localtime(entrega.data_hora).date()


def registrar_entrega(familia, usuario):
    """Registra a entrega da cesta padrão e dá baixa no estoque.

    Tudo ou nada: se a família já recebeu no mês ou se faltar saldo de
    algum item, nada é gravado.
    """
    mes = timezone.localdate().replace(day=1)

    data_anterior = _data_da_entrega_do_mes(familia, mes)
    if data_anterior:
        raise EntregaDuplicada(data_anterior)

    try:
        with transaction.atomic():
            itens = list(
                Item.objects.select_for_update()
                .filter(ativo=True, quantidade_na_cesta__gt=0)
                .order_by("nome")
            )
            for item in itens:
                if item.quantidade_atual < item.quantidade_na_cesta:
                    raise EstoqueInsuficiente(item)

            entrega = Entrega.objects.create(familia=familia, usuario=usuario)
            for item in itens:
                item.quantidade_atual -= item.quantidade_na_cesta
                item.save(update_fields=["quantidade_atual"])
                MovimentacaoEstoque.objects.create(
                    item=item,
                    tipo=MovimentacaoEstoque.Tipo.SAIDA,
                    quantidade=item.quantidade_na_cesta,
                    usuario=usuario,
                    entrega=entrega,
                )
    except IntegrityError:
        # Dois voluntários registraram ao mesmo tempo: o banco barrou o segundo.
        data_anterior = _data_da_entrega_do_mes(familia, mes)
        if data_anterior:
            raise EntregaDuplicada(data_anterior)
        raise

    return entrega