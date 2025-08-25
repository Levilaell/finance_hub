#!/usr/bin/env python
"""
Debug script to test cash flow endpoint in production-like environment
This simulates the same conditions that would exist in production
"""

import requests
import json
from datetime import datetime, date
import os

def test_production_cash_flow():
    """Test cash flow endpoint with production URL"""
    
    # Production URL from the screenshot
    base_url = "https://backend-production-2e6b.up.railway.app"
    cash_flow_endpoint = f"{base_url}/api/reports/dashboard/cash-flow/"
    category_endpoint = f"{base_url}/api/reports/dashboard/category-spending/"
    
    print("=== TESTE DE PRODUÇÃO: CASH FLOW ===")
    
    # Test parameters from screenshot (03 jul - 30 jul)
    start_date = "2024-07-03"
    end_date = "2024-07-30"
    
    # Headers that would be sent in production
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'CaixaHub-Frontend/1.0'
    }
    
    print(f"URL de teste: {cash_flow_endpoint}")
    print(f"Período: {start_date} até {end_date}")
    
    # Test cash flow endpoint (the broken one)
    print("\n1. TESTANDO CASH FLOW ENDPOINT:")
    try:
        cash_flow_params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        print(f"GET {cash_flow_endpoint}")
        print(f"Parâmetros: {cash_flow_params}")
        
        cash_flow_response = requests.get(
            cash_flow_endpoint, 
            params=cash_flow_params, 
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {cash_flow_response.status_code}")
        
        if cash_flow_response.status_code == 200:
            cash_flow_data = cash_flow_response.json()
            print(f"Dados recebidos: {len(cash_flow_data)} registros")
            
            if len(cash_flow_data) > 0:
                print("✅ CASH FLOW: Dados encontrados!")
                print(f"Primeira entrada: {cash_flow_data[0]}")
                print(f"Última entrada: {cash_flow_data[-1]}")
                
                # Check if there's actual data (not all zeros)
                total_income = sum(entry.get('income', 0) for entry in cash_flow_data)
                total_expenses = sum(entry.get('expenses', 0) for entry in cash_flow_data)
                print(f"Total receitas: R$ {total_income:.2f}")
                print(f"Total despesas: R$ {total_expenses:.2f}")
                
                if total_income == 0 and total_expenses == 0:
                    print("❌ PROBLEMA: Todos os valores são zero!")
                else:
                    print("✅ CASH FLOW: Valores não-zero detectados!")
            else:
                print("❌ CASH FLOW: Array vazio retornado")
        else:
            print(f"❌ CASH FLOW: Erro HTTP {cash_flow_response.status_code}")
            print(f"Resposta: {cash_flow_response.text[:200]}")
            
    except Exception as e:
        print(f"❌ CASH FLOW: Erro de conexão: {e}")
    
    # Test category endpoint (the working one) for comparison  
    print("\n2. TESTANDO CATEGORY ENDPOINT (CONTROLE):")
    try:
        category_params = {
            'start_date': start_date,
            'end_date': end_date,
            'type': 'expense'
        }
        
        print(f"GET {category_endpoint}")
        print(f"Parâmetros: {category_params}")
        
        category_response = requests.get(
            category_endpoint,
            params=category_params,
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {category_response.status_code}")
        
        if category_response.status_code == 200:
            category_data = category_response.json()
            print(f"Dados recebidos: {len(category_data)} registros")
            
            if len(category_data) > 0:
                print("✅ CATEGORY: Dados encontrados!")
                total_amount = sum(entry.get('amount', 0) for entry in category_data)
                print(f"Total por categoria: R$ {total_amount:.2f}")
                print(f"Categorias: {[c.get('category', {}).get('name', 'N/A') for c in category_data[:3]]}")
            else:
                print("❌ CATEGORY: Array vazio retornado")
        else:
            print(f"❌ CATEGORY: Erro HTTP {category_response.status_code}")
            print(f"Resposta: {category_response.text[:200]}")
            
    except Exception as e:
        print(f"❌ CATEGORY: Erro de conexão: {e}")
    
    print("\n=== DIAGNÓSTICO ===")
    print("Se CATEGORY funciona mas CASH FLOW não:")
    print("1. 🔄 Correção não foi deployada ainda")
    print("2. 📦 Cache impedindo nova lógica") 
    print("3. 🐛 Bug adicional não identificado")
    print("4. 🔧 Lógica de correção incorreta")

if __name__ == '__main__':
    test_production_cash_flow()