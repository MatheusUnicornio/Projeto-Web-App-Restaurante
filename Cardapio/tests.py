from django.test import TestCase
from unittest.mock import patch, MagicMock
from . import use_cases
from .models import Restaurante, Pedido, ItemCardapio, ItemPedido


# Create your tests here.
#
#
#TESTES UNITÁRIOS SISTEMA DE CARRINHO
#
#
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

#
#
# TESTES UNITÁRIOS DE PAGAMENTO
#
#

class GerarPagamentoTestCase(TestCase):

    def setUp(self):
        self.restaurante = Restaurante.objects.create(nome='Restaurante Teste')
        self.pedido = Pedido.objects.create(
            restaurante=self.restaurante,
            mesa=1,
            status=Pedido.Status.AGUARDANDO_PAGAMENTO,
        )
        self.item = ItemCardapio.objects.create(
            restaurante=self.restaurante,
            nome='Pizza',
            preco=45.90,
            disponivel=True,
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            item_cardapio=self.item,
            quantidade=2,
            preco_unitario=45.90,
        )

    @patch('mercadopago.SDK')
    def test_gerar_pagamento_retorna_url(self, mock_sdk):
        mock_instance = MagicMock()
        mock_sdk.return_value = mock_instance
        mock_instance.preference().create.return_value = {
            'response': {
                'sandbox_init_point': 'https://sandbox.mercadopago.com/checkout/v1/redirect?pref_id=123'
            }
        }

        mock_request = MagicMock()
        mock_request.build_absolute_uri.return_value = 'http://127.0.0.1:8000/'

        url = use_cases.gerar_pagamento(self.pedido, mock_request)

        self.assertEqual(url, 'https://sandbox.mercadopago.com/checkout/v1/redirect?pref_id=123')

    @patch('mercadopago.SDK')
    def test_gerar_pagamento_envia_itens_corretos(self, mock_sdk):
        mock_instance = MagicMock()
        mock_sdk.return_value = mock_instance
        mock_instance.preference().create.return_value = {
            'response': {
                'sandbox_init_point': 'https://sandbox.mercadopago.com/checkout/test'
            }
        }

        mock_request = MagicMock()
        mock_request.build_absolute_uri.return_value = 'http://127.0.0.1:8000/'

        use_cases.gerar_pagamento(self.pedido, mock_request)

        args = mock_instance.preference().create.call_args[0][0]

        self.assertEqual(len(args['items']), 1)
        self.assertEqual(args['items'][0]['title'], 'Pizza')
        self.assertEqual(args['items'][0]['quantity'], 2)
        self.assertEqual(args['items'][0]['unit_price'], 45.90)

    @patch('mercadopago.SDK')
    def test_gerar_pagamento_envia_external_reference(self, mock_sdk):
        mock_instance = MagicMock()
        mock_sdk.return_value = mock_instance
        mock_instance.preference().create.return_value = {
            'response': {
                'sandbox_init_point': 'https://sandbox.mercadopago.com/checkout/test'
            }
        }

        mock_request = MagicMock()
        mock_request.build_absolute_uri.return_value = 'http://127.0.0.1:8000/'

        use_cases.gerar_pagamento(self.pedido, mock_request)

        args = mock_instance.preference().create.call_args[0][0]

        self.assertEqual(args['external_reference'], str(self.pedido.id))