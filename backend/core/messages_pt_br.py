"""
Mensagens do sistema em português brasileiro
"""

# Mensagens de autenticação
AUTH_MESSAGES = {
    # Sucesso
    'REGISTRATION_SUCCESS': 'Cadastro realizado com sucesso. Por favor, verifique seu e-mail para confirmar sua conta.',
    'LOGIN_SUCCESS': 'Login realizado com sucesso.',
    'LOGOUT_SUCCESS': 'Logout realizado com sucesso.',
    'PASSWORD_CHANGED': 'Senha alterada com sucesso.',
    'PASSWORD_RESET_SENT': 'Link de redefinição de senha foi enviado para seu e-mail.',
    'PASSWORD_RESET_SUCCESS': 'Senha redefinida com sucesso.',
    'EMAIL_VERIFIED': 'E-mail verificado com sucesso.',
    'EMAIL_VERIFICATION_SENT': 'E-mail de verificação foi enviado.',
    '2FA_ENABLED': '2FA ativada com sucesso.',
    '2FA_DISABLED': '2FA desativada com sucesso.',
    'BACKUP_CODES_GENERATED': 'Novos códigos de backup gerados. Por favor, guarde-os com segurança.',
    
    # Erros
    'INVALID_CREDENTIALS': 'Credenciais inválidas.',
    'ACCOUNT_DISABLED': 'Conta de usuário desativada.',
    'PASSWORDS_DONT_MATCH': 'As senhas não coincidem.',
    'EMAIL_PASSWORD_REQUIRED': 'Deve incluir "email" e "senha".',
    'USER_NOT_FOUND': 'Nenhum usuário encontrado com este endereço de e-mail.',
    'OLD_PASSWORD_INCORRECT': 'Senha atual está incorreta.',
    'INVALID_RESET_TOKEN': 'Token de redefinição inválido ou expirado.',
    'INVALID_VERIFICATION_TOKEN': 'Token de verificação inválido ou expirado.',
    'EMAIL_ALREADY_VERIFIED': 'E-mail já foi verificado.',
    'REFRESH_TOKEN_REQUIRED': 'Token de atualização é obrigatório.',
    'INVALID_REFRESH_TOKEN': 'Token de atualização inválido.',
    '2FA_CODE_REQUIRED': 'Código de autenticação de dois fatores necessário.',
    'INVALID_2FA_CODE': 'Código de autenticação inválido.',
    '2FA_SETUP_REQUIRED': 'Por favor, configure a 2FA primeiro.',
    'PASSWORD_REQUIRED': 'Senha necessária.',
    'INVALID_PASSWORD': 'Senha inválida.',
    '2FA_NOT_ENABLED': '2FA não está ativada.',
}

# Mensagens de banking/finanças
BANKING_MESSAGES = {
    # Sucesso
    'ACCOUNT_CONNECTED': 'Conta bancária conectada com sucesso.',
    'SYNC_STARTED': 'Sincronização iniciada.',
    'SYNC_COMPLETED': 'Sincronização concluída.',
    'TRANSACTION_CATEGORIZED': 'Transação categorizada com sucesso.',
    'TRANSACTIONS_IMPORTED': '{count} transações importadas com sucesso.',
    
    # Erros
    'BANK_CONNECTION_ERROR': 'Erro ao conectar com o banco.',
    'SYNC_FAILED': 'Falha na sincronização.',
    'INVALID_ACCOUNT_DATA': 'Dados da conta inválidos.',
    'ACCOUNT_NOT_FOUND': 'Conta não encontrada.',
    'INSUFFICIENT_PERMISSIONS': 'Permissões insuficientes.',
}

# Mensagens de relatórios
REPORT_MESSAGES = {
    # Sucesso
    'REPORT_GENERATED': 'Relatório gerado com sucesso.',
    'REPORT_SCHEDULED': 'Relatório agendado com sucesso.',
    'REPORT_EXPORTED': 'Relatório exportado com sucesso.',
    
    # Erros
    'REPORT_GENERATION_FAILED': 'Falha ao gerar relatório.',
    'INVALID_DATE_RANGE': 'Intervalo de datas inválido.',
    'NO_DATA_AVAILABLE': 'Sem dados disponíveis para o período selecionado.',
}

# Mensagens de empresas
COMPANY_MESSAGES = {
    # Sucesso
    'COMPANY_CREATED': 'Empresa criada com sucesso.',
    'COMPANY_UPDATED': 'Empresa atualizada com sucesso.',
    'INVITATION_SENT': 'Convite enviado com sucesso.',
    'MEMBER_ADDED': 'Membro adicionado com sucesso.',
    'MEMBER_REMOVED': 'Membro removido com sucesso.',
    
    # Erros
    'COMPANY_NOT_FOUND': 'Empresa não encontrada.',
    'INVITATION_EXPIRED': 'Convite expirado.',
    'INVALID_CNPJ': 'CNPJ inválido.',
    'CNPJ_ALREADY_EXISTS': 'CNPJ já cadastrado.',
    'SUBSCRIPTION_EXPIRED': 'Assinatura expirada.',
    'USER_LIMIT_REACHED': 'Limite de usuários atingido para este plano.',
}

# Mensagens de categorias
CATEGORY_MESSAGES = {
    # Sucesso
    'CATEGORY_CREATED': 'Categoria criada com sucesso.',
    'CATEGORY_UPDATED': 'Categoria atualizada com sucesso.',
    'CATEGORY_DELETED': 'Categoria excluída com sucesso.',
    'RULE_CREATED': 'Regra de categorização criada com sucesso.',
    
    # Erros
    'CATEGORY_NOT_FOUND': 'Categoria não encontrada.',
    'CATEGORY_IN_USE': 'Categoria está em uso e não pode ser excluída.',
    'INVALID_RULE': 'Regra de categorização inválida.',
}

# Mensagens de pagamentos/assinatura
PAYMENT_MESSAGES = {
    # Sucesso
    'SUBSCRIPTION_ACTIVATED': 'Assinatura ativada com sucesso.',
    'SUBSCRIPTION_CANCELLED': 'Assinatura cancelada.',
    'PAYMENT_SUCCESSFUL': 'Pagamento realizado com sucesso.',
    'CARD_UPDATED': 'Cartão atualizado com sucesso.',
    
    # Erros
    'PAYMENT_FAILED': 'Falha no pagamento.',
    'INVALID_CARD': 'Cartão inválido.',
    'SUBSCRIPTION_ALREADY_ACTIVE': 'Assinatura já está ativa.',
    'INVALID_PLAN': 'Plano inválido.',
}

# Mensagens gerais do sistema
SYSTEM_MESSAGES = {
    # Sucesso
    'SAVED_SUCCESSFULLY': 'Salvo com sucesso.',
    'DELETED_SUCCESSFULLY': 'Excluído com sucesso.',
    'UPDATED_SUCCESSFULLY': 'Atualizado com sucesso.',
    
    # Erros
    'GENERIC_ERROR': 'Ocorreu um erro. Por favor, tente novamente.',
    'PERMISSION_DENIED': 'Você não tem permissão para realizar esta ação.',
    'NOT_FOUND': 'Recurso não encontrado.',
    'VALIDATION_ERROR': 'Erro de validação. Verifique os dados informados.',
    'SERVER_ERROR': 'Erro interno do servidor.',
    'RATE_LIMIT_EXCEEDED': 'Limite de requisições excedido. Tente novamente mais tarde.',
}

# Mensagens de validação
VALIDATION_MESSAGES = {
    'REQUIRED_FIELD': 'Este campo é obrigatório.',
    'INVALID_EMAIL': 'Endereço de e-mail inválido.',
    'PASSWORD_TOO_SHORT': 'A senha deve ter pelo menos {min_length} caracteres.',
    'PASSWORD_TOO_COMMON': 'Esta senha é muito comum.',
    'PASSWORD_NUMERIC': 'A senha não pode ser inteiramente numérica.',
    'INVALID_CPF': 'CPF inválido.',
    'INVALID_CNPJ': 'CNPJ inválido.',
    'INVALID_PHONE': 'Número de telefone inválido.',
    'INVALID_DATE': 'Data inválida.',
    'INVALID_AMOUNT': 'Valor inválido.',
    'MAX_LENGTH_EXCEEDED': 'Máximo de {max_length} caracteres excedido.',
    'MIN_VALUE': 'O valor mínimo é {min_value}.',
    'MAX_VALUE': 'O valor máximo é {max_value}.',
}

# Labels e textos da interface
UI_LABELS = {
    # Campos de formulário
    'EMAIL': 'E-mail',
    'PASSWORD': 'Senha',
    'CONFIRM_PASSWORD': 'Confirmar Senha',
    'FIRST_NAME': 'Nome',
    'LAST_NAME': 'Sobrenome',
    'PHONE': 'Telefone',
    'COMPANY_NAME': 'Nome da Empresa',
    'CNPJ': 'CNPJ',
    'ADDRESS': 'Endereço',
    'CITY': 'Cidade',
    'STATE': 'Estado',
    'ZIP_CODE': 'CEP',
    
    # Botões
    'LOGIN': 'Entrar',
    'REGISTER': 'Cadastrar',
    'LOGOUT': 'Sair',
    'SAVE': 'Salvar',
    'CANCEL': 'Cancelar',
    'DELETE': 'Excluir',
    'EDIT': 'Editar',
    'CREATE': 'Criar',
    'SEARCH': 'Buscar',
    'FILTER': 'Filtrar',
    'EXPORT': 'Exportar',
    'IMPORT': 'Importar',
    'SYNC': 'Sincronizar',
    'BACK': 'Voltar',
    'NEXT': 'Próximo',
    'PREVIOUS': 'Anterior',
    'CONFIRM': 'Confirmar',
    
    # Navegação
    'DASHBOARD': 'Painel',
    'ACCOUNTS': 'Contas',
    'TRANSACTIONS': 'Transações',
    'CATEGORIES': 'Categorias',
    'REPORTS': 'Relatórios',
    'SETTINGS': 'Configurações',
    'HELP': 'Ajuda',
    'PROFILE': 'Perfil',
    'COMPANY': 'Empresa',
    'USERS': 'Usuários',
    'SUBSCRIPTION': 'Assinatura',
    
    # Status
    'ACTIVE': 'Ativo',
    'INACTIVE': 'Inativo',
    'PENDING': 'Pendente',
    'COMPLETED': 'Concluído',
    'FAILED': 'Falhou',
    'CANCELLED': 'Cancelado',
    'EXPIRED': 'Expirado',
    
    # Tipos de transação
    'INCOME': 'Receita',
    'EXPENSE': 'Despesa',
    'TRANSFER': 'Transferência',
    
    # Períodos
    'TODAY': 'Hoje',
    'YESTERDAY': 'Ontem',
    'THIS_WEEK': 'Esta Semana',
    'LAST_WEEK': 'Semana Passada',
    'THIS_MONTH': 'Este Mês',
    'LAST_MONTH': 'Mês Passado',
    'THIS_YEAR': 'Este Ano',
    'LAST_YEAR': 'Ano Passado',
    'CUSTOM': 'Personalizado',
}

# Formatar mensagens com parâmetros
def format_message(message: str, **kwargs) -> str:
    """
    Formata uma mensagem com parâmetros
    
    Exemplo:
        format_message(VALIDATION_MESSAGES['PASSWORD_TOO_SHORT'], min_length=8)
    """
    return message.format(**kwargs)