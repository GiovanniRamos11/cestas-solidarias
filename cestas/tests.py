from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Entrega, Familia, Item, Usuario


class RegrasDeDadosTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="voluntario_teste", password="senha-de-teste-123"
        )
        self.familia = Familia.objects.create(
            nome_responsavel="João Teste Almeida",
            endereco="Rua Exemplo, 25",
            numero_moradores=5,
        )

    def test_uma_entrega_por_familia_por_mes(self):
        Entrega.objects.create(familia=self.familia, usuario=self.usuario)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Entrega.objects.create(familia=self.familia, usuario=self.usuario)

    def test_estoque_nunca_negativo(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Item.objects.create(
                    nome="Arroz", unidade="kg", quantidade_atual=-1
                )
