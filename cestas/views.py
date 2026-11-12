import unicodedata

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Entrega, Familia, Item
from .servicos import EntregaDuplicada, EstoqueInsuficiente, registrar_entrega


def _sem_acento(texto):
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn").lower()


@login_required
def inicio(request):
    termo = request.GET.get("q", "").strip()
    resultados = []

    if termo:
        mes = timezone.localdate().replace(day=1)
        buscado = _sem_acento(termo)
        entregas = {
            e.familia_id: timezone.localtime(e.data_hora).date()
            for e in Entrega.objects.filter(mes_referencia=mes)
        }
        for familia in Familia.objects.filter(ativa=True).order_by("nome_responsavel"):
            if buscado in _sem_acento(familia.nome_responsavel):
                familia.recebeu_em = entregas.get(familia.id)
                resultados.append(familia)

    return render(
        request,
        "cestas/inicio.html",
        {"termo": termo, "resultados": resultados},
    )


@login_required
def entrega(request, familia_id):
    familia = get_object_or_404(Familia, pk=familia_id, ativa=True)

    if request.method == "POST":
        try:
            registrar_entrega(familia, request.user)
        except EntregaDuplicada as erro:
            return render(
                request,
                "cestas/resultado.html",
                {"familia": familia, "tipo": "duplicada", "data": erro.data_anterior},
            )
        except EstoqueInsuficiente as erro:
            return render(
                request,
                "cestas/resultado.html",
                {"familia": familia, "tipo": "estoque", "item": erro.item},
            )
        return render(
            request, "cestas/resultado.html", {"familia": familia, "tipo": "sucesso"}
        )

    itens = Item.objects.filter(ativo=True, quantidade_na_cesta__gt=0).order_by("nome")
    return render(request, "cestas/entrega.html", {"familia": familia, "itens": itens})