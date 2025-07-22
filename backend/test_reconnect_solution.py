"""
SOLUÇÕES PARA O PROBLEMA DE SYNC:

O item está com status WAITING_USER_ACTION, que significa que o Inter
está pedindo nova autenticação. Isso acontece periodicamente por segurança.

OPÇÕES:

1. RECONECTAR CREDENCIAIS (recomendado):
   - Vá na tela de contas bancárias
   - Clique em "Reconectar" na conta do Inter
   - Faça login novamente
   - As transações existentes são mantidas
   - Transações novas serão sincronizadas

2. AGUARDAR (pode demorar):
   - Às vezes o status muda sozinho
   - Pode demorar horas ou dias
   - Não é garantido

3. RECONECTAR COMPLETAMENTE:
   - Excluir conta e conectar de novo
   - Todas as transações são re-importadas
   - Mais demorado mas 100% efetivo

RECOMENDAÇÃO: Opção 1 - Reconectar credenciais
"""

print(__doc__)