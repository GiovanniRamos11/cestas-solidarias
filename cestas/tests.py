from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Entrega, Familia, Item, MovimentacaoEstoque, Usuario
from .servicos import EntregaDuplicada, EstoqueInsuficiente, registrar_entrega


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


class RegistroEntregaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="voluntario_teste", password="senha-de-teste-123"
        )
        self.familia = Familia.objects.create(
            nome_responsavel="João Teste Almeida",
            endereco="Rua Exemplo, 25",
            numero_moradores=5,
        )
        self.arroz = Item.objects.create(
            nome="Arroz", unidade="kg",
            quantidade_atual=10, estoque_minimo=3, quantidade_na_cesta=5,
        )
        self.feijao = Item.objects.create(
            nome="Feijão", unidade="kg",
            quantidade_atual=10, estoque_minimo=3, quantidade_na_cesta=2,
        )

    def test_registra_entrega_e_da_baixa_no_estoque(self):
        entrega = registrar_entrega(self.familia, self.usuario)

        self.arroz.refresh_from_db()
        self.feijao.refresh_from_db()
        self.assertEqual(self.arroz.quantidade_atual, 5)
        self.assertEqual(self.feijao.quantidade_atual, 8)
        saidas = MovimentacaoEstoque.objects.filter(
            entrega=entrega, tipo=MovimentacaoEstoque.Tipo.SAIDA
        )
        self.assertEqual(saidas.count(), 2)

    def test_segunda_entrega_no_mes_e_barrada_sem_mexer_no_estoque(self):
        registrar_entrega(self.familia, self.usuario)
        with self.assertRaises(EntregaDuplicada) as contexto:
            registrar_entrega(self.familia, self.usuario)

        self.assertIsNotNone(contexto.exception.data_anterior)
        self.arroz.refresh_from_db()
        self.assertEqual(self.arroz.quantidade_atual, 5)
        self.assertEqual(Entrega.objects.count(), 1)

    def test_estoque_insuficiente_nao_grava_nada(self):
        self.feijao.quantidade_atual = 1
        self.feijao.save()

        with self.assertRaises(EstoqueInsuficiente) as contexto:
            registrar_entrega(self.familia, self.usuario)

        self.assertEqual(contexto.exception.item.nome, "Feijão")
        self.arroz.refresh_from_db()
        self.assertEqual(self.arroz.quantidade_atual, 10)
        self.assertEqual(Entrega.objects.count(), 0)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)



class AcessoTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="voluntario_teste", password="senha-de-teste-123"
        )

    def test_anonimo_e_redirecionado_ao_login(self):
        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login/", resposta["Location"])

    def test_login_valido_acessa_a_pagina_inicial(self):
        self.client.login(username="voluntario_teste", password="senha-de-teste-123")
        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 200)

    def test_login_invalido_mostra_mensagem_generica(self):
        resposta = self.client.post(
            "/login/", {"username": "voluntario_teste", "password": "errada"}
        )
        self.assertContains(resposta, "Usuário ou senha inválidos")

    def test_sair_encerra_a_sessao(self):
        self.client.login(username="voluntario_teste", password="senha-de-teste-123")
        self.client.post("/sair/")
        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 302)