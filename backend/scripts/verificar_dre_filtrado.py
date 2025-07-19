#!/usr/bin/env python
"""
Script para verificar transações e comparar com relatório DRE
Filtrando apenas receitas e despesas operacionais
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
    print("VERIFICAÇÃO DE TRANSAÇÕES - RELATÓRIO DRE (FILTRADO)")
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
        
        # Filtrar apenas transações operacionais (excluir investimentos e transferências internas)
        categorias_excluir = ['Investments', 'Transfer - Pix', 'Transfers']
        
        # Separar receitas e despesas operacionais
        receitas_operacionais = []
        despesas_operacionais = []
        outras_transacoes = []
        
        for transacao in transacoes:
            categoria_nome = transacao.category.name if transacao.category else "Sem categoria"
            
            # Verificar se é uma transação operacional
            if categoria_nome not in categorias_excluir:
                if transacao.transaction_type in ['credit', 'transfer_in', 'pix_in']:
                    receitas_operacionais.append(transacao)
                elif transacao.transaction_type in ['debit', 'transfer_out', 'pix_out', 'fee']:
                    despesas_operacionais.append(transacao)
            else:
                outras_transacoes.append(transacao)
        
        # Calcular totais operacionais
        total_receitas_op = sum(t.amount for t in receitas_operacionais)
        total_despesas_op = sum(t.amount for t in despesas_operacionais)
        
        print("\n" + "=" * 80)
        print("RESUMO OPERACIONAL (Excluindo Investimentos e Transferências)")
        print("=" * 80)
        print(f"Receitas Operacionais: {formatar_valor(total_receitas_op)} ({len(receitas_operacionais)} transações)")
        print(f"Despesas Operacionais: {formatar_valor(abs(total_despesas_op))} ({len(despesas_operacionais)} transações)")
        print(f"Resultado Operacional: {formatar_valor(total_receitas_op + total_despesas_op)}")
        
        # Detalhamento das transações operacionais
        print("\n" + "=" * 80)
        print("DETALHAMENTO DAS TRANSAÇÕES OPERACIONAIS")
        print("=" * 80)
        
        if receitas_operacionais:
            print("\nRECEITAS OPERACIONAIS:")
            for trans in receitas_operacionais:
                categoria_str = trans.category.name if trans.category else "Sem categoria"
                print(f"  {trans.transaction_date.strftime('%d/%m')} | {formatar_valor(trans.amount):>12} | "
                      f"{categoria_str:25} | {trans.description[:40]}")
            print(f"  {'TOTAL':8} | {formatar_valor(total_receitas_op):>12}")
        
        if despesas_operacionais:
            print("\nDESPESAS OPERACIONAIS:")
            for trans in despesas_operacionais:
                categoria_str = trans.category.name if trans.category else "Sem categoria"
                print(f"  {trans.transaction_date.strftime('%d/%m')} | {formatar_valor(abs(trans.amount)):>12} | "
                      f"{categoria_str:25} | {trans.description[:40]}")
            print(f"  {'TOTAL':8} | {formatar_valor(abs(total_despesas_op)):>12}")
        
        # Análise das transações PIX
        print("\n" + "=" * 80)
        print("ANÁLISE DETALHADA DE TRANSAÇÕES PIX")
        print("=" * 80)
        
        transacoes_pix = [t for t in transacoes if 'PIX' in t.description.upper()]
        
        print(f"\nTotal de transações PIX: {len(transacoes_pix)}")
        
        # Separar PIX recebidos e enviados
        pix_recebidos = []
        pix_enviados = []
        
        for trans in transacoes_pix:
            if 'RECEBIDO' in trans.description.upper():
                pix_recebidos.append(trans)
            elif 'ENVIADO' in trans.description.upper():
                pix_enviados.append(trans)
        
        # Filtrar PIX operacionais (excluir transferências internas)
        pix_operacionais_recebidos = []
        pix_operacionais_enviados = []
        
        palavras_internas = ['INTERNO', 'KAIZEN', 'GAMING', 'BANK', 'INTER SA']
        
        for trans in pix_recebidos:
            desc_upper = trans.description.upper()
            if not any(palavra in desc_upper for palavra in palavras_internas):
                pix_operacionais_recebidos.append(trans)
        
        for trans in pix_enviados:
            desc_upper = trans.description.upper()
            if not any(palavra in desc_upper for palavra in palavras_internas):
                pix_operacionais_enviados.append(trans)
        
        print(f"\nPIX RECEBIDOS OPERACIONAIS (excluindo transferências internas):")
        total_pix_rec_op = Decimal('0.00')
        for trans in pix_operacionais_recebidos:
            print(f"  {trans.transaction_date.strftime('%d/%m')} | {formatar_valor(trans.amount):>12} | {trans.description[:50]}")
            total_pix_rec_op += trans.amount
        print(f"  {'TOTAL':8} | {formatar_valor(total_pix_rec_op):>12}")
        
        print(f"\nPIX ENVIADOS OPERACIONAIS (excluindo transferências internas):")
        total_pix_env_op = Decimal('0.00')
        for trans in pix_operacionais_enviados:
            print(f"  {trans.transaction_date.strftime('%d/%m')} | {formatar_valor(abs(trans.amount)):>12} | {trans.description[:50]}")
            total_pix_env_op += trans.amount
        print(f"  {'TOTAL':8} | {formatar_valor(abs(total_pix_env_op)):>12}")
        
        # Comparação final com DRE
        print("\n" + "=" * 80)
        print("COMPARAÇÃO FINAL COM RELATÓRIO DRE")
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
        
        # Calcular valores operacionais reais
        receita_operacional_real = total_pix_rec_op
        despesa_operacional_real = abs(total_pix_env_op) if total_pix_env_op < 0 else total_pix_env_op
        
        print(f"\nDRE Fornecido:")
        print(f"  Receita Bruta: {formatar_valor(dre_valores['receita_bruta'])}")
        print(f"  (-) Despesas Operacionais: {formatar_valor(dre_valores['despesas_operacionais'])}")
        print(f"  (=) Resultado Líquido: {formatar_valor(dre_valores['resultado_liquido'])}")
        
        print(f"\nDados Calculados (PIX Operacionais):")
        print(f"  Receitas PIX Operacionais: {formatar_valor(receita_operacional_real)}")
        print(f"  Despesas PIX Operacionais: {formatar_valor(despesa_operacional_real)}")
        print(f"  Resultado: {formatar_valor(receita_operacional_real - despesa_operacional_real)}")
        
        print(f"\nAnálise:")
        if abs(receita_operacional_real - dre_valores['receita_bruta']) < Decimal('0.50'):
            print("  ✓ As receitas operacionais correspondem ao DRE fornecido")
        else:
            print(f"  ✗ Diferença nas receitas: {formatar_valor(receita_operacional_real - dre_valores['receita_bruta'])}")
        
        if abs(despesa_operacional_real - dre_valores['despesas_operacionais']) < Decimal('0.50'):
            print("  ✓ As despesas operacionais correspondem ao DRE fornecido")
        else:
            print(f"  ✗ Diferença nas despesas: {formatar_valor(despesa_operacional_real - dre_valores['despesas_operacionais'])}")
        
    except User.DoesNotExist:
        print(f"ERRO: Usuário com email '{email_usuario}' não encontrado!")
    except Exception as e:
        print(f"ERRO: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verificar_transacoes_dre()