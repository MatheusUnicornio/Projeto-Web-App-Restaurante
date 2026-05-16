from django.db import models
from django.utils import timezone

#Camada de Domínio
class Restaurante(models.Model):
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)

    class Meta:
        app_label = 'Cardapio'

    def __str__(self):
        return self.nome

class ItemCardapio(models.Model):
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='itens')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    restricoes = models.CharField(max_length=200, blank=True, help_text="Ex: glúten, lactose")
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    disponivel = models.BooleanField(default=True)
    foto = models.ImageField(upload_to='cardapio/', blank=True, null=True)

    class Meta:
        app_label = 'Cardapio'

    def __str__(self):
        return f"{self.nome} (R$ {self.preco})"

class Pedido(models.Model):
    class Status(models.TextChoices):
        AGUARDANDO_PAGAMENTO = 'AGUARD_PAG', 'Aguardando Pagamento'
        PAGO                 = 'PAGO',      'Pago'
        EM_PREPARO           = 'PREPARO',   'Em Preparo'
        PRONTO               = 'PRONTO',    'Pronto'

    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='pedidos')
    mesa        = models.PositiveIntegerField()
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.AGUARDANDO_PAGAMENTO)
    criado_em   = models.DateTimeField(auto_now_add=True)
    pronto_em   = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'Cardapio'

    def __str__(self):
        return f"Pedido #{self.pk} - Mesa {self.mesa} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if self.status == self.Status.PRONTO and self.pronto_em is None:
            self.pronto_em = timezone.now()
        super().save(*args, **kwargs)


class ItemPedido(models.Model):
    pedido          = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    item_cardapio   = models.ForeignKey(ItemCardapio, on_delete=models.PROTECT)
    quantidade      = models.PositiveIntegerField(default=1)
    preco_unitario  = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        app_label = 'Cardapio'

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __str__(self):
        return f"{self.quantidade}x {self.item_cardapio.nome}"