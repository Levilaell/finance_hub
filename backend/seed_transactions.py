#!/usr/bin/env python
"""
Seed realistic transactions for a digital marketing agency
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from apps.authentication.models import User
from apps.banking.models import Transaction, BankAccount, TransactionCategory
from apps.companies.models import Company

def create_categories_if_needed(company):
    """Create necessary categories for the company"""
    categories = {
        'Receitas': {
            'Serviços de Marketing': {'icon': '📈', 'color': '#10B981'},
            'Consultoria': {'icon': '💼', 'color': '#3B82F6'},
            'Gestão de Redes Sociais': {'icon': '📱', 'color': '#8B5CF6'},
            'Criação de Conteúdo': {'icon': '✍️', 'color': '#EC4899'},
            'Google Ads': {'icon': '🎯', 'color': '#F59E0B'},
            'Facebook Ads': {'icon': '👥', 'color': '#3B5998'},
        },
        'Despesas': {
            'Salários': {'icon': '💰', 'color': '#EF4444'},
            'Aluguel': {'icon': '🏢', 'color': '#6B7280'},
            'Internet e Telefone': {'icon': '📞', 'color': '#06B6D4'},
            'Software e Ferramentas': {'icon': '💻', 'color': '#8B5CF6'},
            'Material de Escritório': {'icon': '📎', 'color': '#F59E0B'},
            'Transporte': {'icon': '🚗', 'color': '#10B981'},
            'Alimentação': {'icon': '🍽️', 'color': '#EC4899'},
            'Impostos': {'icon': '📋', 'color': '#DC2626'},
            'Freelancers': {'icon': '👨‍💻', 'color': '#3B82F6'},
            'Publicidade': {'icon': '📢', 'color': '#7C3AED'},
            'Energia Elétrica': {'icon': '💡', 'color': '#FCD34D'},
            'Equipamentos': {'icon': '🖥️', 'color': '#4B5563'},
        }
    }
    
    created_categories = {}
    for type_name, cats in categories.items():
        for name, details in cats.items():
            cat, created = TransactionCategory.objects.get_or_create(
                name=name,
                category_type='income' if type_name == 'Receitas' else 'expense',
                defaults={
                    'slug': name.lower().replace(' ', '-'),
                    'icon': details['icon'],
                    'color': details['color'],
                    'is_active': True,
                    'is_system': False
                }
            )
            created_categories[name] = cat
            if created:
                print(f"Created category: {name}")
    
    return created_categories

def generate_transactions(user, start_date, end_date):
    """Generate realistic transactions for a digital marketing agency"""
    company = user.company
    
    # Update company name if needed
    if company.name == "Sei la":
        company.name = "Pixel Pro - Agência de Marketing Digital"
        company.save()
        print(f"Updated company name to: {company.name}")
    
    # Get bank accounts
    accounts = BankAccount.objects.filter(company=company, is_active=True)
    if not accounts.exists():
        print("No active bank accounts found!")
        return
    
    checking_account = accounts.filter(account_type='checking').first()
    if not checking_account:
        checking_account = accounts.first()
    
    # Create categories
    categories = create_categories_if_needed(company)
    
    # Client names for recurring revenue
    clients = [
        "Tech Solutions Ltda",
        "E-commerce Express",
        "Restaurante Sabor & Arte",
        "Clínica Saúde Total",
        "Imobiliária Prime",
        "Academia FitLife",
        "Petshop Amigos Peludos",
        "Advocacia Silva & Associados",
        "Construtora Horizonte",
        "Escola Crescer"
    ]
    
    # Software subscriptions
    software_subscriptions = [
        ("Adobe Creative Cloud", 299.90),
        ("Canva Pro", 119.90),
        ("Hootsuite", 199.00),
        ("SEMrush", 499.95),
        ("Mailchimp", 299.00),
        ("Zoom Pro", 149.90),
        ("Google Workspace", 180.00),
        ("Slack", 87.50),
        ("Trello Business", 62.50),
        ("Microsoft 365", 219.90)
    ]
    
    # Generate transactions
    current_date = start_date
    transactions_created = 0
    
    while current_date <= end_date:
        # Skip weekends for most business transactions
        is_weekend = current_date.weekday() in [5, 6]
        
        # Monthly fixed expenses (pay on specific days)
        if current_date.day == 5:
            # Rent
            Transaction.objects.create(
                bank_account=checking_account,
                transaction_type='debit',
                amount=Decimal('4500.00'),
                description='Aluguel - Sala Comercial Centro',
                transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                category=categories.get('Aluguel'),
                status='completed'
            )
            transactions_created += 1
            
        if current_date.day == 10:
            # Salaries
            salaries = [
                ("Salário - João Silva (Designer)", 4500.00),
                ("Salário - Maria Santos (Social Media)", 3800.00),
                ("Salário - Pedro Costa (Copywriter)", 4200.00),
                ("Salário - Ana Oliveira (Gerente de Contas)", 5500.00),
            ]
            for desc, amount in salaries:
                Transaction.objects.create(
                    bank_account=checking_account,
                    transaction_type='debit',
                    amount=Decimal(str(amount)),
                    description=desc,
                    transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                    category=categories.get('Salários'),
                    status='completed'
                )
                transactions_created += 1
        
        # Client payments (usually on 5th, 15th, or 25th)
        if current_date.day in [5, 15, 25]:
            num_payments = random.randint(1, 3)
            selected_clients = random.sample(clients, num_payments)
            
            for client in selected_clients:
                service_type = random.choice([
                    'Gestão de Redes Sociais',
                    'Google Ads',
                    'Facebook Ads',
                    'Consultoria',
                    'Criação de Conteúdo'
                ])
                
                # Different pricing tiers
                if 'Gestão' in service_type:
                    amount = random.choice([2500, 3500, 4500])
                elif 'Ads' in service_type:
                    amount = random.choice([3000, 5000, 8000])
                elif 'Consultoria' in service_type:
                    amount = random.choice([2000, 3500, 5000])
                else:
                    amount = random.choice([1500, 2500, 3500])
                
                Transaction.objects.create(
                    bank_account=checking_account,
                    transaction_type='credit',
                    amount=Decimal(str(amount)),
                    description=f"{client} - {service_type}",
                    transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                    category=categories.get(service_type),
                    status='completed'
                )
                transactions_created += 1
        
        # Software subscriptions (various days of the month)
        if current_date.day == 15:
            for software, price in random.sample(software_subscriptions, 4):
                Transaction.objects.create(
                    bank_account=checking_account,
                    transaction_type='debit',
                    amount=Decimal(str(price)),
                    description=f"{software} - Assinatura Mensal",
                    transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                    category=categories.get('Software e Ferramentas'),
                    status='completed'
                )
                transactions_created += 1
        
        # Utilities
        if current_date.day == 20:
            utilities = [
                ("Conta de Luz - CEMIG", random.uniform(350, 550)),
                ("Internet Fibra - 500MB", 299.90),
                ("Telefone Empresarial", 189.90)
            ]
            for desc, amount in utilities:
                cat_name = 'Energia Elétrica' if 'Luz' in desc else 'Internet e Telefone'
                Transaction.objects.create(
                    bank_account=checking_account,
                    transaction_type='debit',
                    amount=Decimal(str(round(amount, 2))),
                    description=desc,
                    transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                    category=categories.get(cat_name),
                    status='completed'
                )
                transactions_created += 1
        
        # Daily operational expenses (weekdays only)
        if not is_weekend and random.random() > 0.3:
            # Meals and transportation
            if random.random() > 0.5:
                meal_options = [
                    ("iFood - Almoço equipe", random.uniform(80, 150)),
                    ("Uber Eats - Reunião com cliente", random.uniform(60, 120)),
                    ("Starbucks - Café da manhã", random.uniform(25, 45))
                ]
                desc, amount = random.choice(meal_options)
                Transaction.objects.create(
                    bank_account=checking_account,
                    transaction_type='debit',
                    amount=Decimal(str(round(amount, 2))),
                    description=desc,
                    transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                    category=categories.get('Alimentação'),
                    status='completed'
                )
                transactions_created += 1
            
            # Transportation
            if random.random() > 0.7:
                transport_options = [
                    ("Uber - Visita cliente", random.uniform(25, 60)),
                    ("Gasolina - Posto Shell", random.uniform(100, 200)),
                    ("Estacionamento Centro", random.uniform(15, 30))
                ]
                desc, amount = random.choice(transport_options)
                Transaction.objects.create(
                    bank_account=checking_account,
                    transaction_type='debit',
                    amount=Decimal(str(round(amount, 2))),
                    description=desc,
                    transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                    category=categories.get('Transporte'),
                    status='completed'
                )
                transactions_created += 1
        
        # Freelancer payments (random days)
        if not is_weekend and random.random() > 0.85:
            freelancer_options = [
                ("Freelancer - Vídeo promocional", random.uniform(800, 1500)),
                ("Freelancer - Design banner", random.uniform(300, 600)),
                ("Freelancer - Redação blog", random.uniform(200, 400)),
                ("Freelancer - Fotografia produto", random.uniform(500, 1000))
            ]
            desc, amount = random.choice(freelancer_options)
            Transaction.objects.create(
                bank_account=checking_account,
                transaction_type='debit',
                amount=Decimal(str(round(amount, 2))),
                description=desc,
                transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                category=categories.get('Freelancers'),
                status='completed'
            )
            transactions_created += 1
        
        # Office supplies (occasional)
        if not is_weekend and random.random() > 0.9:
            supplies_options = [
                ("Kalunga - Material escritório", random.uniform(150, 300)),
                ("Amazon - Toner impressora", random.uniform(200, 400)),
                ("Papelaria - Cartões visita", random.uniform(100, 200))
            ]
            desc, amount = random.choice(supplies_options)
            Transaction.objects.create(
                bank_account=checking_account,
                transaction_type='debit',
                amount=Decimal(str(round(amount, 2))),
                description=desc,
                transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                category=categories.get('Material de Escritório'),
                status='completed'
            )
            transactions_created += 1
        
        # Ad spend for clients (reimbursable)
        if current_date.day in [10, 20] and random.random() > 0.5:
            ad_platforms = [
                ("Google Ads - Cliente Tech Solutions", random.uniform(2000, 5000)),
                ("Facebook Ads - Cliente E-commerce", random.uniform(1500, 3500)),
                ("LinkedIn Ads - Cliente B2B", random.uniform(1000, 2500))
            ]
            desc, amount = random.choice(ad_platforms)
            # Expense
            Transaction.objects.create(
                bank_account=checking_account,
                transaction_type='debit',
                amount=Decimal(str(round(amount, 2))),
                description=desc,
                transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                category=categories.get('Publicidade'),
                status='completed'
            )
            # Reimbursement (next day)
            if current_date < end_date:
                next_day = current_date + timedelta(days=1)
                Transaction.objects.create(
                    bank_account=checking_account,
                    transaction_type='credit',
                    amount=Decimal(str(round(amount, 2))),
                    description=f"Reembolso - {desc}",
                    transaction_date=timezone.make_aware(datetime.combine(next_day, datetime.min.time())),
                    category=categories.get('Serviços de Marketing'),
                    status='completed'
                )
                transactions_created += 2
            else:
                transactions_created += 1
        
        # Equipment purchases (occasional)
        if random.random() > 0.97:
            equipment_options = [
                ("Apple Store - MacBook Pro", 15000.00),
                ("Fast Shop - Monitor 4K", 2500.00),
                ("Mercado Livre - Webcam Logitech", 800.00),
                ("Kabum - SSD 1TB", 600.00)
            ]
            desc, amount = random.choice(equipment_options)
            Transaction.objects.create(
                bank_account=checking_account,
                transaction_type='debit',
                amount=Decimal(str(amount)),
                description=desc,
                transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                category=categories.get('Equipamentos'),
                status='completed'
            )
            transactions_created += 1
        
        # Taxes (quarterly)
        if current_date.day == 15 and current_date.month in [3, 6, 9, 12]:
            Transaction.objects.create(
                bank_account=checking_account,
                transaction_type='debit',
                amount=Decimal(str(random.uniform(5000, 8000))),
                description='DAS - Simples Nacional',
                transaction_date=timezone.make_aware(datetime.combine(current_date, datetime.min.time())),
                category=categories.get('Impostos'),
                status='completed'
            )
            transactions_created += 1
        
        current_date += timedelta(days=1)
    
    print(f"\nTotal transactions created: {transactions_created}")
    return transactions_created

def main():
    """Main function to seed transactions"""
    email = 'levilael44@gmail.com'
    
    # Find user
    user = User.objects.filter(email=email).first()
    if not user:
        print(f"User {email} not found!")
        return
    
    print(f"Found user: {user.email}")
    print(f"Company: {user.company.name}")
    
    # Define date range - last 12 months
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    
    print(f"\nGenerating transactions from {start_date} to {end_date}")
    
    # Generate transactions
    generate_transactions(user, start_date, end_date)
    
    # Show summary
    accounts = BankAccount.objects.filter(company=user.company)
    total_transactions = Transaction.objects.filter(bank_account__in=accounts).count()
    
    print(f"\nSummary:")
    print(f"Total transactions in database: {total_transactions}")
    
    # Calculate totals
    transactions = Transaction.objects.filter(
        bank_account__in=accounts,
        transaction_date__date__gte=start_date,
        transaction_date__date__lte=end_date
    )
    
    income = sum(t.amount for t in transactions.filter(
        transaction_type__in=['credit', 'transfer_in', 'pix_in']
    ))
    expenses = sum(t.amount for t in transactions.filter(
        transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
    ))
    
    print(f"Total income: R$ {income:,.2f}")
    print(f"Total expenses: R$ {expenses:,.2f}")
    print(f"Net profit: R$ {(income - expenses):,.2f}")

if __name__ == '__main__':
    main()