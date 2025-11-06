"""
Company Models
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class Company(models.Model):
    """
    Company model
    """
    
    # Choices
    COMPANY_TYPES = [
        ('mei', 'MEI'),
        ('me', 'Microempresa'),
        ('epp', 'Empresa de Pequeno Porte'),
        ('ltda', 'Limitada'),
        ('sa', 'Sociedade Anônima'),
        ('other', 'Outros'),
    ]
    
    BUSINESS_SECTORS = [
        ('retail', 'Comércio'),
        ('services', 'Serviços'),
        ('industry', 'Indústria'),
        ('technology', 'Tecnologia'),
        ('healthcare', 'Saúde'),
        ('education', 'Educação'),
        ('food', 'Alimentação'),
        ('construction', 'Construção'),
        ('automotive', 'Automotivo'),
        ('agriculture', 'Agricultura'),
        ('other', 'Outros'),
    ]
    
    # Core company information
    owner = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='company'
    )
    name = models.CharField(_('company name'), max_length=200)
    
    # Brazilian company details
    cnpj = models.CharField(
        _('CNPJ'), 
        max_length=18, 
        unique=True,
        help_text='CNPJ no formato XX.XXX.XXX/XXXX-XX'
    )
    company_type = models.CharField(
        _('company type'), 
        max_length=20,
        choices=COMPANY_TYPES
    )
    business_sector = models.CharField(
        _('business sector'),
        max_length=50,
        choices=BUSINESS_SECTORS
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'companies'
        constraints = [
            models.UniqueConstraint(
                fields=['cnpj'], 
                name='unique_active_cnpj',
                condition=models.Q(is_active=True)
            )
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Validar CNPJ
        if self.cnpj and not self._validate_cnpj(self.cnpj):
            raise ValidationError({'cnpj': 'CNPJ inválido'})
    
    def save(self, *args, **kwargs):
        # Skip validation if explicitly requested (for AI insights placeholder creation)
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)
    
    def _validate_cnpj(self, cnpj):
        """Validação básica de CNPJ - implemente a lógica completa"""
        clean_cnpj = ''.join(filter(str.isdigit, cnpj))
        return len(clean_cnpj) == 14