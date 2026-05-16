from django.db import migrations


def criar_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    gerencia, _ = Group.objects.get_or_create(name='Gerência')
    atendente, _ = Group.objects.get_or_create(name='Atendente')

    perms_cardapio = Permission.objects.filter(
        content_type__app_label='Cardapio',
        content_type__model='itemcardapio',
    )
    gerencia.permissions.add(*perms_cardapio)

    perms_pedido_view = Permission.objects.filter(
        content_type__app_label='Cardapio',
        content_type__model='pedido',
        codename__in=['view_pedido', 'change_pedido'],
    )
    gerencia.permissions.add(*Permission.objects.filter(
        content_type__app_label='Cardapio',
        content_type__model='pedido',
    ))
    atendente.permissions.add(*perms_pedido_view)

    # Permissões de Restaurante — só Gerência
    perms_restaurante = Permission.objects.filter(
        content_type__app_label='Cardapio',
        content_type__model='restaurante',
    )
    gerencia.permissions.add(*perms_restaurante)


def remover_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Gerência', 'Atendente']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Cardapio', '0002_pedido_pronto_em'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(criar_grupos, remover_grupos),
    ]