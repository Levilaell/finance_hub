#!/usr/bin/env python
"""
Script para verificar transações e comparar com relatório DRE
Período: 01/07/2025 a 19/07/2025
Conta: levilaelsilvaa@gmail.com
"""

import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal
from collections import defaultdict

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Importar modelos após configurar Django
from apps.banking.models import Transaction, BankAccount
from apps.companies.models import Company
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q

User = get_user_model()


def formatar_valor(valor):
    """Formata valor monetário em BRL"""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def verificar_transacoes_dre():
    """Verifica transações e compara com DRE"""
    
    # Configurações do período
    data_inicio = date(2025, 7, 1)
    data_fim = date(2025, 7, 19)
    email_usuario = "levilaelsilvaa@gmail.com"
    
    print("=" * 80)
    print("VERIFICAÇÃO DE TRANSAÇÕES - RELATÓRIO DRE")
    print("=" * 80)
    print(f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    print(f"Usuário: {email_usuario}")
    print("=" * 80)
    
    try:
        # Buscar usuário
        usuario = User.objects.get(email=email_usuario)
        print(f"\nUsuário encontrado: {usuario.get_full_name() or usuario.email}")
        
        # Buscar empresa do usuário
        empresa = Company.objects.filter(owner=usuario).first()
        if not empresa:
            print("ERRO: Nenhuma empresa encontrada para este usuário!")
            return
            
        print(f"Empresa: {empresa.name} (CNPJ: {empresa.cnpj})")
        
        # Buscar contas bancárias da empresa
        contas = BankAccount.objects.filter(company=empresa)
        print(f"\nContas bancárias encontradas: {contas.count()}")
        for conta in contas:
            print(f"  - {conta.bank_provider.name} - {conta.masked_account} ({conta.account_type})")
        
        # Buscar transações do período
        transacoes = Transaction.objects.filter(
            bank_account__company=empresa,
            transaction_date__gte=data_inicio,
            transaction_date__lte=data_fim
        ).order_by('transaction_date')
        
        print(f"\nTotal de transações no período: {transacoes.count()}")
        
        # Categorizar transações por tipo
        tipos_receita = ['credit', 'transfer_in', 'pix_in']
        tipos_despesa = ['debit', 'transfer_out', 'pix_out', 'fee']
        
        # Calcular totais
        receitas = transacoes.filter(transaction_type__in=tipos_receita)
        despesas = transacoes.filter(transaction_type__in=tipos_despesa)
        
        total_receitas = receitas.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_despesas = despesas.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        print("\n" + "=" * 80)
        print("RESUMO GERAL")
        print("=" * 80)
        print(f"Total de Receitas: {formatar_valor(total_receitas)}")
        print(f"Total de Despesas: {formatar_valor(total_despesas)}")
        print(f"Resultado: {formatar_valor(total_receitas - total_despesas)}")
        
        # Detalhamento por tipo de transação
        print("\n" + "=" * 80)
        print("DETALHAMENTO POR TIPO DE TRANSAÇÃO")
        print("=" * 80)
        
        print("\nRECEITAS:")
        for tipo in tipos_receita:
            transacoes_tipo = receitas.filter(transaction_type=tipo)
            total_tipo = transacoes_tipo.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            count_tipo = transacoes_tipo.count()
            if count_tipo > 0:
                print(f"  {tipo.upper():20} {count_tipo:5} transações - {formatar_valor(total_tipo):>20}")
        
        print("\nDESPESAS:")
        for tipo in tipos_despesa:
            transacoes_tipo = despesas.filter(transaction_type=tipo)
            total_tipo = transacoes_tipo.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            count_tipo = transacoes_tipo.count()
            if count_tipo > 0:
                print(f"  {tipo.upper():20} {count_tipo:5} transações - {formatar_valor(total_tipo):>20}")
        
        # Detalhamento por categoria
        print("\n" + "=" * 80)
        print("DETALHAMENTO POR CATEGORIA")
        print("=" * 80)
        
        # Agrupar por categoria
        categorias_receita = defaultdict(lambda: {'count': 0, 'total': Decimal('0.00')})
        categorias_despesa = defaultdict(lambda: {'count': 0, 'total': Decimal('0.00')})
        sem_categoria = {'receitas': {'count': 0, 'total': Decimal('0.00')}, 
                        'despesas': {'count': 0, 'total': Decimal('0.00')}}
        
        for transacao in transacoes:
            if transacao.transaction_type in tipos_receita:
                if transacao.category:
                    categoria_nome = transacao.category.full_name
                    categorias_receita[categoria_nome]['count'] += 1
                    categorias_receita[categoria_nome]['total'] += transacao.amount
                else:
                    sem_categoria['receitas']['count'] += 1
                    sem_categoria['receitas']['total'] += transacao.amount
            elif transacao.transaction_type in tipos_despesa:
                if transacao.category:
                    categoria_nome = transacao.category.full_name
                    categorias_despesa[categoria_nome]['count'] += 1
                    categorias_despesa[categoria_nome]['total'] += transacao.amount
                else:
                    sem_categoria['despesas']['count'] += 1
                    sem_categoria['despesas']['total'] += transacao.amount
        
        print("\nRECEITAS POR CATEGORIA:")
        for categoria, dados in sorted(categorias_receita.items(), key=lambda x: x[1]['total'], reverse=True):
            print(f"  {categoria:40} {dados['count']:5} transações - {formatar_valor(dados['total']):>20}")
        if sem_categoria['receitas']['count'] > 0:
            print(f"  {'SEM CATEGORIA':40} {sem_categoria['receitas']['count']:5} transações - {formatar_valor(sem_categoria['receitas']['total']):>20}")
        
        print("\nDESPESAS POR CATEGORIA:")
        for categoria, dados in sorted(categorias_despesa.items(), key=lambda x: x[1]['total'], reverse=True):
            print(f"  {categoria:40} {dados['count']:5} transações - {formatar_valor(dados['total']):>20}")
        if sem_categoria['despesas']['count'] > 0:
            print(f"  {'SEM CATEGORIA':40} {sem_categoria['despesas']['count']:5} transações - {formatar_valor(sem_categoria['despesas']['total']):>20}")
        
        # Comparação com valores do DRE (valores fornecidos pelo usuário)
        print("\n" + "=" * 80)
        print("COMPARAÇÃO COM RELATÓRIO DRE FORNECIDO")
        print("=" * 80)
        
        # Valores do DRE fornecido
        dre_valores = {
            'receita_bruta': Decimal('44.10'),
            'custos_servicos': Decimal('0.00'),
            'despesas_operacionais': Decimal('5.00'),
            'despesas_administrativas': Decimal('0.00'),
            'despesas_pessoal': Decimal('0.00'),
            'resultado_liquido': Decimal('39.10')
        }
        
        print(f"\nDRE Fornecido:")
        print(f"  Receita Bruta: {formatar_valor(dre_valores['receita_bruta'])}")
        print(f"  (-) Custos dos Serviços: {formatar_valor(dre_valores['custos_servicos'])}")
        print(f"  (-) Despesas Operacionais: {formatar_valor(dre_valores['despesas_operacionais'])}")
        print(f"  (-) Despesas Administrativas: {formatar_valor(dre_valores['despesas_administrativas'])}")
        print(f"  (-) Despesas com Pessoal: {formatar_valor(dre_valores['despesas_pessoal'])}")
        print(f"  (=) Resultado Líquido: {formatar_valor(dre_valores['resultado_liquido'])}")
        
        print(f"\nDados Calculados:")
        print(f"  Total Receitas: {formatar_valor(total_receitas)}")
        print(f"  Total Despesas: {formatar_valor(total_despesas)}")
        print(f"  Resultado: {formatar_valor(total_receitas - total_despesas)}")
        
        print(f"\nDiferenças:")
        print(f"  Receitas: {formatar_valor(total_receitas - dre_valores['receita_bruta'])}")
        total_despesas_dre = (dre_valores['custos_servicos'] + dre_valores['despesas_operacionais'] + 
                             dre_valores['despesas_administrativas'] + dre_valores['despesas_pessoal'])
        print(f"  Despesas: {formatar_valor(total_despesas - total_despesas_dre)}")
        print(f"  Resultado: {formatar_valor((total_receitas - total_despesas) - dre_valores['resultado_liquido'])}")
        
        # Listar algumas transações de exemplo
        print("\n" + "=" * 80)
        print("ÚLTIMAS 10 TRANSAÇÕES")
        print("=" * 80)
        
        ultimas_transacoes = transacoes.order_by('-transaction_date')[:10]
        for trans in ultimas_transacoes:
            tipo_str = "RECEITA" if trans.transaction_type in tipos_receita else "DESPESA"
            categoria_str = trans.category.name if trans.category else "Sem categoria"
            print(f"{trans.transaction_date.strftime('%d/%m/%Y')} | {tipo_str:7} | {trans.transaction_type:12} | "
                  f"{formatar_valor(trans.amount):>15} | {categoria_str:20} | {trans.description[:40]}")
        
    except User.DoesNotExist:
        print(f"ERRO: Usuário com email '{email_usuario}' não encontrado!")
    except Exception as e:
        print(f"ERRO: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verificar_transacoes_dre()