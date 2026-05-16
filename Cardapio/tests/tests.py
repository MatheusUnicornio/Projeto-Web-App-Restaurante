from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from Cardapio.application import use_cases
from Cardapio.domain.models import Restaurante, Pedido, ItemCardapio, ItemPedido
from django.contrib.admin.sites import AdminSite
from Cardapio.admin import PedidoAdmin
from django.urls import reverse

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

#
#
# TESTES - FUNCIONALIDADES PAINEL DO ADMIN
#
#

#Teste unitário
class ProximaAcaoUnitarioTestCase(TestCase):
    #Testa a função proxima_acao do PedidoAdmin

    def setUp(self):
        self.site = AdminSite()
        self.admin = PedidoAdmin(Pedido, self.site)
        self.restaurante = Restaurante.objects.create(nome='Restaurante Teste')

    def test_proxima_acao_aguardando_pagamento(self):
        pedido = Pedido(
            restaurante=self.restaurante,
            mesa=1,
            status=Pedido.Status.AGUARDANDO_PAGAMENTO
        )
        resultado = self.admin.proxima_acao(pedido)
        self.assertIn('Aguardando pagamento', resultado)

    def test_proxima_acao_pago(self):
        pedido = Pedido(
            restaurante=self.restaurante,
            mesa=1,
            status=Pedido.Status.PAGO
        )
        resultado = self.admin.proxima_acao(pedido)
        self.assertIn('Iniciar preparo', resultado)

    def test_proxima_acao_em_preparo(self):
        pedido = Pedido(
            restaurante=self.restaurante,
            mesa=1,
            status=Pedido.Status.EM_PREPARO
        )
        resultado = self.admin.proxima_acao(pedido)
        self.assertIn('Marcar como pronto', resultado)

    def test_proxima_acao_pronto(self):
        pedido = Pedido(
            restaurante=self.restaurante,
            mesa=1,
            status=Pedido.Status.PRONTO
        )
        resultado = self.admin.proxima_acao(pedido)
        self.assertIn('Entregar na mesa', resultado)

#Teste de Integração
class AcoesEmLoteIntegracaoTestCase(TestCase):
    #Testa as ações em lote do cardapio que tocam o banco de dados.
    def setUp(self):
        self.site = AdminSite()
        self.admin = PedidoAdmin(Pedido, self.site)
        self.restaurante = Restaurante.objects.create(nome='Restaurante Teste')

    def test_marcar_em_preparo_atualiza_apenas_pedidos_pagos(self):
       pedido_pago = Pedido.objects.create(
            restaurante=self.restaurante,
            mesa=1,
            status=Pedido.Status.PAGO
        )
       pedido_aguardando = Pedido.objects.create(
            restaurante=self.restaurante,
            mesa=2,
            status=Pedido.Status.AGUARDANDO_PAGAMENTO
        )

       queryset = Pedido.objects.filter(
            pk__in=[pedido_pago.pk, pedido_aguardando.pk]
        )
       self.admin.marcar_em_preparo(None, queryset)

       pedido_pago.refresh_from_db()
       pedido_aguardando.refresh_from_db()

       self.assertEqual(pedido_pago.status, Pedido.Status.EM_PREPARO)
       self.assertEqual(pedido_aguardando.status, Pedido.Status.AGUARDANDO_PAGAMENTO)

    def test_marcar_pronto_atualiza_apenas_pedidos_em_preparo(self):
        pedido_em_preparo = Pedido.objects.create(
            restaurante=self.restaurante,
            mesa=1,
            status=Pedido.Status.EM_PREPARO
        )
        pedido_pago = Pedido.objects.create(
            restaurante=self.restaurante,
            mesa=2,
            status=Pedido.Status.PAGO
        )

        queryset = Pedido.objects.filter(
            pk__in=[pedido_em_preparo.pk, pedido_pago.pk]
        )
        self.admin.marcar_pronto(None, queryset)

        pedido_em_preparo.refresh_from_db()
        pedido_pago.refresh_from_db()

        self.assertEqual(pedido_em_preparo.status, Pedido.Status.PRONTO)
        self.assertEqual(pedido_pago.status, Pedido.Status.PAGO)

#
#
#Adendo: Testes de integração - Cardápio
#
#

class CardapioViewIntegracaoTestCase(TestCase):

    def setUp(self):
        #Cria os dados necessários para cada teste
        self.client = Client()
        self.restaurante = Restaurante.objects.create(nome='Restaurante Teste', ativo=True)
        self.item = ItemCardapio.objects.create(
            restaurante=self.restaurante,
            nome='Pizza',
            preco=45.90,
            disponivel=True,
        )

    def test_cardapio_retorna_200(self):
        url = reverse('cardapio', kwargs={
            'restaurante_id': self.restaurante.id,
            'mesa': 1
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cardapio_exibe_itens_do_restaurante(self):
        url = reverse('cardapio', kwargs={
            'restaurante_id': self.restaurante.id,
            'mesa': 1
        })
        response = self.client.get(url)
        self.assertContains(response, 'Pizza')

    def test_cardapio_nao_exibe_itens_de_outro_restaurante(self):

        outro_restaurante = Restaurante.objects.create(nome='Outro Restaurante', ativo=True)
        ItemCardapio.objects.create(
            restaurante=outro_restaurante,
            nome='Hamburguer',
            preco=35.00,
            disponivel=True,
        )

        url = reverse('cardapio', kwargs={
            'restaurante_id': self.restaurante.id,
            'mesa': 1
        })
        response = self.client.get(url)

        self.assertContains(response, 'Pizza')
        self.assertNotContains(response, 'Hamburguer')

    def test_restaurante_inativo_retorna_404(self):
        self.restaurante.ativo = False
        self.restaurante.save()

        url = reverse('cardapio', kwargs={
            'restaurante_id': self.restaurante.id,
            'mesa': 1
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class CarrinhoIntegracaoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.restaurante = Restaurante.objects.create(nome='Restaurante Teste', ativo=True)
        self.item = ItemCardapio.objects.create(
            restaurante=self.restaurante,
            nome='Pizza',
            preco=45.90,
            disponivel=True,
        )

    def test_adicionar_item_salva_na_sessao(self):
        url = reverse('adicionar_ao_carrinho', kwargs={
            'restaurante_id': self.restaurante.id,
            'mesa': 1,
            'item_id': self.item.id,
        })
        self.client.get(url)

        carrinho = self.client.session.get('carrinho', {})
        self.assertIn(str(self.item.id), carrinho)
        self.assertEqual(carrinho[str(self.item.id)]['quantidade'], 1)

    def test_adicionar_mesmo_item_duas_vezes_incrementa_quantidade(self):
        url = reverse('adicionar_ao_carrinho', kwargs={
            'restaurante_id': self.restaurante.id,
            'mesa': 1,
            'item_id': self.item.id,
        })
        self.client.get(url)
        self.client.get(url)

        carrinho = self.client.session.get('carrinho', {})
        self.assertEqual(carrinho[str(self.item.id)]['quantidade'], 2)

    def test_confirmar_pedido_cria_pedido_no_banco(self):
        self.client.get(reverse('adicionar_ao_carrinho', kwargs={
            'restaurante_id': self.restaurante.id,
            'mesa': 1,
            'item_id': self.item.id,
        }))

        with patch('Cardapio.use_cases.gerar_pagamento', return_value='http://fake-mp.com'):
            self.client.get(reverse('confirmar_pedido', kwargs={
                'restaurante_id': self.restaurante.id,
                'mesa': 1,
            }))

        self.assertEqual(Pedido.objects.count(), 1)
        pedido = Pedido.objects.first()
        self.assertEqual(pedido.mesa, 1)
        self.assertEqual(pedido.restaurante, self.restaurante)

        self.assertEqual(ItemPedido.objects.count(), 1)
        item_pedido = ItemPedido.objects.first()
        self.assertEqual(item_pedido.quantidade, 1)
        self.assertEqual(float(item_pedido.preco_unitario), 45.90)

    def test_confirmar_pedido_limpa_carrinho(self):
        self.client.get(reverse('adicionar_ao_carrinho', kwargs={
            'restaurante_id': self.restaurante.id,
            'mesa': 1,
            'item_id': self.item.id,
        }))

        with patch('Cardapio.use_cases.gerar_pagamento', return_value='http://fake-mp.com'):
            self.client.get(reverse('confirmar_pedido', kwargs={
                'restaurante_id': self.restaurante.id,
                'mesa': 1,
            }))

        carrinho = self.client.session.get('carrinho', {})
        self.assertEqual(carrinho, {})

    def test_confirmar_pedido_vazio_redireciona_para_cardapio(self):
        url = reverse('confirmar_pedido', kwargs={
            'restaurante_id': self.restaurante.id,
            'mesa': 1,
        })
        response = self.client.get(url)

        # Deve redirecionar de volta para o cardápio
        self.assertEqual(response.status_code, 302)
        self.assertIn('cardapio', response.url)


