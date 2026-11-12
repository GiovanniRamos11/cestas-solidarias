import unicodedata

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from .models import Entrega, Familia


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