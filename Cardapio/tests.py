from django.test import TestCase
from . import use_cases

# Create your tests here.

#TESTES UNITÁRIOS SISTEMA DE CARRINHO
class AdicionarItemTestCase(TestCase):
    def test_adicionar_item_novo(self):
        carrinho = {}
        carrinho = use_cases.adicionar_item(carrinho, 1, 'Pizza', 45.90)

        self.assertIn('1', carrinho)
        self.assertEqual(carrinho['1']['quantidade'], 1)
        self.assertEqual(carrinho['1']['preco'], 45.90)

    def test_adicionar_item_existente_aumenta_quantidade(self):
        carrinho = {'1': {'nome': 'Pizza', 'preco': 45.90, 'quantidade': 1}}
        carrinho = use_cases.adicionar_item(carrinho, 1, 'Pizza', 45.90)

        self.assertEqual(carrinho['1']['quantidade'], 2)


class RemoverItemTestCase(TestCase):

    def test_remover_item_diminui_quantidade(self):
        carrinho = {'1': {'nome': 'Pizza', 'preco': 45.90, 'quantidade': 2}}
        carrinho = use_cases.remover_item(carrinho, 1)

        self.assertEqual(carrinho['1']['quantidade'], 1)

    def test_remover_item_com_quantidade_1_exclui_do_carrinho(self):
        carrinho = {'1': {'nome': 'Pizza', 'preco': 45.90, 'quantidade': 1}}
        carrinho = use_cases.remover_item(carrinho, 1)

        self.assertNotIn('1', carrinho)

    def test_remover_item_inexistente_nao_quebra(self):
        carrinho = {}
        carrinho = use_cases.remover_item(carrinho, 99)

        self.assertEqual(carrinho, {})


class CalcularTotalTestCase(TestCase):

    def test_total_correto(self):
        carrinho = {
            '1': {'nome': 'Pizza', 'preco': 45.90, 'quantidade': 2},
            '2': {'nome': 'Refrigerante', 'preco': 8.00, 'quantidade': 3},
        }
        total = use_cases.calcular_total(carrinho)
        self.assertAlmostEqual(total, 115.80, places=2)

    def test_total_carrinho_vazio(self):
        self.assertEqual(use_cases.calcular_total({}), 0)