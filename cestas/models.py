from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Usuario(AbstractUser):
    class Perfil(models.TextChoices):
        VOLUNTARIO = "VOLUNTARIO", "Voluntário"
        RESPONSAVEL = "RESPONSAVEL", "Responsável"

    perfil = models.CharField(
        max_length=12, choices=Perfil.choices, default=Perfil.VOLUNTARIO
    )


class Familia(models.Model):
    nome_responsavel = models.CharField(max_length=150)
    endereco = models.CharField(max_length=200)
    numero_moradores = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    ativa = models.BooleanField(default=True)
    data_cadastro = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(numero_moradores__gte=1),
                name="familia_moradores_minimo_1",
            )
        ]

    def __str__(self):
        return self.nome_responsavel


class Item(models.Model):
    class Unidade(models.TextChoices):
        KG = "kg", "kg"
        LITRO = "litro", "litro"
        PACOTE = "pacote", "pacote"
        UNIDADE = "unidade", "unidade"

    nome = models.CharField(max_length=100, unique=True)
    unidade = models.CharField(max_length=10, choices=Unidade.choices)
    quantidade_atual = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=0)
    quantidade_na_cesta = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    @property
    def abaixo_do_minimo(self):
        return self.quantidade_atual < self.estoque_minimo


class Entrega(models.Model):
    familia = models.ForeignKey(
        Familia, on_delete=models.PROTECT, related_name="entregas"
    )
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name="entregas"
    )
    data_hora = models.DateTimeField(auto_now_add=True)
    mes_referencia = models.DateField(editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["familia", "mes_referencia"],
                name="entrega_unica_familia_mes",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.mes_referencia:
            self.mes_referencia = timezone.localdate().replace(day=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.familia} - {self.mes_referencia:%m/%Y}"


class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SAIDA = "SAIDA", "Saída"

    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, related_name="movimentacoes"
    )
    tipo = models.CharField(max_length=7, choices=Tipo.choices)
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    data_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name="movimentacoes"
    )
    entrega = models.ForeignKey(
        Entrega,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimentacoes",
    )
    observacao = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade__gt=0),
                name="movimentacao_quantidade_maior_que_zero",
            )
        ]

    def __str__(self):
        return f"{self.tipo} {self.quantidade} de {self.item}"