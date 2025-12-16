# Generated manually for BillPayment model
from django.db import migrations, models
import django.db.models.deletion
import uuid
from decimal import Decimal


def migrate_linked_transactions(apps, schema_editor):
    """
    Migra dados existentes para o novo modelo BillPayment.

    Cenários tratados:
    1. Bill com linked_transaction -> Criar BillPayment com transação
    2. Bill com amount_paid > 0 sem linked_transaction -> Criar BillPayment manual
    3. Bill paga sem linked_transaction -> Criar BillPayment manual com amount total
    """
    Bill = apps.get_model('banking', 'Bill')
    BillPayment = apps.get_model('banking', 'BillPayment')

    # Cenário 1: Bills com linked_transaction
    bills_with_tx = Bill.objects.filter(
        linked_transaction__isnull=False
    ).select_related('linked_transaction')

    for bill in bills_with_tx:
        BillPayment.objects.create(
            bill=bill,
            amount=bill.amount_paid if bill.amount_paid > 0 else bill.amount,
            payment_date=bill.paid_at or bill.linked_transaction.date,
            transaction=bill.linked_transaction,
            notes='Migrado de linked_transaction'
        )
        # Limpa o campo legado
        bill.linked_transaction = None
        bill.save(update_fields=['linked_transaction'])

    # Cenário 2 e 3: Bills com amount_paid > 0 mas sem linked_transaction
    bills_with_payments = Bill.objects.filter(
        linked_transaction__isnull=True,
        amount_paid__gt=Decimal('0.00')
    )

    for bill in bills_with_payments:
        # Verifica se já não foi criado um BillPayment
        if not BillPayment.objects.filter(bill=bill).exists():
            BillPayment.objects.create(
                bill=bill,
                amount=bill.amount_paid,
                payment_date=bill.paid_at or bill.updated_at,
                transaction=None,
                notes='Migrado de pagamento manual legado'
            )


def reverse_migration(apps, schema_editor):
    """
    Reverte a migração restaurando linked_transaction onde possível.
    """
    Bill = apps.get_model('banking', 'Bill')
    BillPayment = apps.get_model('banking', 'BillPayment')

    # Restaura linked_transaction para payments que tinham transação
    for payment in BillPayment.objects.filter(transaction__isnull=False).select_related('bill', 'transaction'):
        bill = payment.bill
        bill.linked_transaction = payment.transaction
        bill.save(update_fields=['linked_transaction'])

    # Remove todos os BillPayments criados na migração
    BillPayment.objects.filter(
        notes__in=['Migrado de linked_transaction', 'Migrado de pagamento manual legado']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0013_categoryrule'),
    ]

    operations = [
        # 1. Criar modelo BillPayment
        migrations.CreateModel(
            name='BillPayment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('payment_date', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bill', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payments',
                    to='banking.bill'
                )),
                ('transaction', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='bill_payment',
                    to='banking.transaction'
                )),
            ],
            options={
                'ordering': ['-payment_date', '-created_at'],
            },
        ),

        # 2. Adicionar índice
        migrations.AddIndex(
            model_name='billpayment',
            index=models.Index(fields=['bill', 'payment_date'], name='banking_bil_bill_id_paymen_idx'),
        ),

        # 3. Migrar dados existentes
        migrations.RunPython(migrate_linked_transactions, reverse_migration),
    ]
