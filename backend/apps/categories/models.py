"""
Categories app models
AI-powered transaction categorization system
"""
import json

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CategoryRule(models.Model):
    """
    Rules for automatic transaction categorization
    Used by AI and rule-based systems
    """
    RULE_TYPES = [
        ('keyword', 'Palavra-chave'),
        ('amount_range', 'Faixa de valor'),
        ('counterpart', 'Contrapartida'),
        ('pattern', 'Padrão regex'),
        ('ai_prediction', 'Predição IA'),
    ]
    
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE, 
        related_name='category_rules'
    )
    category = models.ForeignKey(
        'banking.TransactionCategory', 
        on_delete=models.CASCADE,
        related_name='rules'
    )
    
    name = models.CharField(_('rule name'), max_length=200)
    rule_type = models.CharField(_('rule type'), max_length=20, choices=RULE_TYPES)
    
    # Rule conditions (stored as JSON)
    conditions = models.JSONField(_('conditions'), default=dict)
    
    # Rule settings
    priority = models.IntegerField(_('priority'), default=0, help_text="Higher priority rules are applied first")
    is_active = models.BooleanField(_('is active'), default=True)
    confidence_threshold = models.FloatField(_('confidence threshold'), default=0.8)
    
    # Statistics
    match_count = models.IntegerField(_('match count'), default=0)
    accuracy_rate = models.FloatField(_('accuracy rate'), default=0.0)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_rules'
    )
    
    class Meta:
        db_table = 'category_rules'
        verbose_name = _('Category Rule')
        verbose_name_plural = _('Category Rules')
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} → {self.category.name}"


class AITrainingData(models.Model):
    """
    Training data for AI categorization model
    Stores manually reviewed transactions for learning
    """
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE, 
        related_name='ai_training_data'
    )
    
    # Transaction features (anonymized)
    description = models.CharField(_('transaction description'), max_length=500)
    amount = models.DecimalField(_('amount'), max_digits=15, decimal_places=2)
    transaction_type = models.CharField(_('transaction type'), max_length=20)
    counterpart_name = models.CharField(_('counterpart name'), max_length=200, blank=True)
    
    # Categorization
    category = models.ForeignKey(
        'banking.TransactionCategory', 
        on_delete=models.CASCADE,
        related_name='training_data'
    )
    subcategory = models.ForeignKey(
        'banking.TransactionCategory', 
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subcategory_training_data'
    )
    
    # Training metadata
    is_verified = models.BooleanField(_('is verified'), default=False)
    verification_source = models.CharField(
        _('verification source'),
        max_length=20,
        choices=[
            ('manual', 'Revisão Manual'),
            ('user_feedback', 'Feedback do Usuário'),
            ('rule_based', 'Baseado em Regras'),
            ('ai_confident', 'IA Alta Confiança'),
        ],
        default='manual'
    )
    
    # Feature extraction (for ML)
    extracted_features = models.JSONField(_('extracted features'), default=dict)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='verified_training_data'
    )
    
    class Meta:
        db_table = 'ai_training_data'
        verbose_name = _('AI Training Data')
        verbose_name_plural = _('AI Training Data')
        indexes = [
            models.Index(fields=['company', 'category']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.description[:50]} → {self.category.name}"


class CategorySuggestion(models.Model):
    """
    AI-generated category suggestions for user review
    """
    transaction = models.OneToOneField(
        'banking.Transaction', 
        on_delete=models.CASCADE,
        related_name='ai_suggestion'
    )
    
    # AI suggestions (ranked by confidence)
    suggested_category = models.ForeignKey(
        'banking.TransactionCategory', 
        on_delete=models.CASCADE,
        related_name='ai_suggestions'
    )
    confidence_score = models.FloatField(_('confidence score'))
    
    # Alternative suggestions
    alternative_suggestions = models.JSONField(_('alternative suggestions'), default=list)
    
    # AI model information
    model_version = models.CharField(_('model version'), max_length=50)
    features_used = models.JSONField(_('features used'), default=list)
    
    # User interaction
    is_accepted = models.BooleanField(_('is accepted'), default=False)
    is_rejected = models.BooleanField(_('is rejected'), default=False)
    user_feedback = models.TextField(_('user feedback'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    reviewed_at = models.DateTimeField(_('reviewed at'), blank=True, null=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='reviewed_suggestions'
    )
    
    class Meta:
        db_table = 'category_suggestions'
        verbose_name = _('Category Suggestion')
        verbose_name_plural = _('Category Suggestions')
        indexes = [
            models.Index(fields=['is_accepted', 'is_rejected']),
            models.Index(fields=['confidence_score']),
        ]
    
    def __str__(self):
        return f"{self.transaction.description[:30]} → {self.suggested_category.name} ({self.confidence_score:.2f})"


class CategoryPerformance(models.Model):
    """
    Performance metrics for categorization system
    Tracks accuracy and improvements over time
    """
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE, 
        related_name='category_performance'
    )
    category = models.ForeignKey(
        'banking.TransactionCategory', 
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )
    
    # Performance metrics
    total_predictions = models.IntegerField(_('total predictions'), default=0)
    correct_predictions = models.IntegerField(_('correct predictions'), default=0)
    false_positives = models.IntegerField(_('false positives'), default=0)
    false_negatives = models.IntegerField(_('false negatives'), default=0)
    
    # Calculated metrics
    accuracy = models.FloatField(_('accuracy'), default=0.0)
    precision = models.FloatField(_('precision'), default=0.0)
    recall = models.FloatField(_('recall'), default=0.0)
    f1_score = models.FloatField(_('F1 score'), default=0.0)
    
    # Time period
    period_start = models.DateField(_('period start'))
    period_end = models.DateField(_('period end'))
    
    # Metadata
    calculated_at = models.DateTimeField(_('calculated at'), auto_now_add=True)
    
    class Meta:
        db_table = 'category_performance'
        verbose_name = _('Category Performance')
        verbose_name_plural = _('Category Performance')
        unique_together = ('company', 'category', 'period_start', 'period_end')
    
    def __str__(self):
        return f"{self.category.name} - {self.accuracy:.2%} accuracy"
    
    def update_metrics(self):
        """
        Recalculate performance metrics
        """
        if self.total_predictions > 0:
            self.accuracy = self.correct_predictions / self.total_predictions
        
        if (self.correct_predictions + self.false_positives) > 0:
            self.precision = self.correct_predictions / (self.correct_predictions + self.false_positives)
        
        if (self.correct_predictions + self.false_negatives) > 0:
            self.recall = self.correct_predictions / (self.correct_predictions + self.false_negatives)
        
        if (self.precision + self.recall) > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        
        self.save()


class CategorizationLog(models.Model):
    """
    Log of categorization attempts and results
    """
    transaction = models.ForeignKey(
        'banking.Transaction', 
        on_delete=models.CASCADE,
        related_name='categorization_logs'
    )
    
    # Categorization attempt
    method = models.CharField(
        _('categorization method'),
        max_length=20,
        choices=[
            ('ai', 'Predição IA'),
            ('rule', 'Baseado em Regras'),
            ('manual', 'Manual'),
            ('bulk', 'Operação em Massa'),
            ('recurring', 'Padrão Recorrente'),
        ]
    )
    
    # Results
    suggested_category = models.ForeignKey(
        'banking.TransactionCategory', 
        on_delete=models.CASCADE,
        related_name='categorization_logs'
    )
    confidence_score = models.FloatField(_('confidence score'), default=0.0)
    processing_time_ms = models.IntegerField(_('processing time (ms)'), default=0)
    
    # Context
    rule_used = models.ForeignKey(
        CategoryRule, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    ai_model_version = models.CharField(_('AI model version'), max_length=50, blank=True)
    
    # Result
    was_accepted = models.BooleanField(_('was accepted'), default=False)
    final_category = models.ForeignKey(
        'banking.TransactionCategory', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='final_categorization_logs'
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'categorization_logs'
        verbose_name = _('Categorization Log')
        verbose_name_plural = _('Categorization Logs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.method} - {self.suggested_category.name} ({self.confidence_score:.2f})"