"""
Serviço de Detecção de Anomalias
Usa Machine Learning para identificar transações e padrões anômalos
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

from apps.banking.models import Transaction, BankAccount
from ..models import AIInsight

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """Serviço para detecção de anomalias em dados financeiros"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Espera 10% de anomalias
            random_state=42,
            n_estimators=100
        )
        
    def detect_transaction_anomalies(self, company_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """
        Detecta anomalias em transações individuais
        
        Args:
            company_id: ID da empresa
            days: Período de análise em dias
            
        Returns:
            Lista de insights sobre anomalias detectadas
        """
        try:
            # Buscar transações do período
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            transactions = Transaction.objects.filter(
                bank_account__company_id=company_id,
                transaction_date__range=[start_date, end_date]
            ).values(
                'id', 'amount', 'transaction_type', 'category_id',
                'transaction_date', 'description', 'bank_account_id'
            )
            
            if len(transactions) < 20:
                logger.info(f"Não há transações suficientes para análise de anomalias (company: {company_id})")
                return []
            
            # Converter para DataFrame
            df = pd.DataFrame(list(transactions))
            
            # Feature engineering
            df = self._prepare_transaction_features(df)
            
            # Detectar anomalias
            anomalies = self._detect_anomalies_isolation_forest(df)
            
            # Detectar anomalias por clustering
            cluster_anomalies = self._detect_anomalies_clustering(df)
            
            # Combinar resultados
            all_anomalies = pd.concat([anomalies, cluster_anomalies]).drop_duplicates()
            
            # Gerar insights
            insights = self._generate_anomaly_insights(all_anomalies, company_id)
            
            return insights
            
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias: {str(e)}")
            return []
    
    def _prepare_transaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara features para detecção de anomalias"""
        try:
            # Converter valores para numéricos
            df['amount_abs'] = pd.to_numeric(df['amount'], errors='coerce').abs()
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            
            # Features temporais
            df['day_of_week'] = df['transaction_date'].dt.dayofweek
            df['day_of_month'] = df['transaction_date'].dt.day
            df['hour'] = df['transaction_date'].dt.hour
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            df['is_month_end'] = (df['day_of_month'] > 25).astype(int)
            
            # Features de conta e categoria
            df['account_encoded'] = pd.Categorical(df['bank_account_id']).codes
            df['category_encoded'] = pd.Categorical(df['category_id']).codes
            df['type_encoded'] = pd.Categorical(df['transaction_type']).codes
            
            # Features estatísticas (por conta)
            account_stats = df.groupby('bank_account_id')['amount_abs'].agg(['mean', 'std']).reset_index()
            account_stats.columns = ['bank_account_id', 'account_mean', 'account_std']
            df = df.merge(account_stats, on='bank_account_id', how='left')
            
            # Z-score por conta
            df['z_score'] = (df['amount_abs'] - df['account_mean']) / (df['account_std'] + 1e-8)
            
            # Features de texto (comprimento da descrição)
            df['description_length'] = df['description'].astype(str).str.len()
            df['has_special_chars'] = df['description'].astype(str).str.contains(r'[!@#$%^&*(),.?":{}|<>]').astype(int)
            
            # Preencher valores nulos
            df = df.fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao preparar features: {str(e)}")
            return df
    
    def _detect_anomalies_isolation_forest(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detecta anomalias usando Isolation Forest"""
        try:
            # Features para o modelo
            feature_columns = [
                'amount_abs', 'day_of_week', 'day_of_month', 'hour',
                'is_weekend', 'is_month_end', 'account_encoded',
                'category_encoded', 'type_encoded', 'z_score',
                'description_length', 'has_special_chars'
            ]
            
            # Selecionar apenas features disponíveis
            available_features = [col for col in feature_columns if col in df.columns]
            X = df[available_features].copy()
            
            # Normalizar dados
            X_scaled = self.scaler.fit_transform(X)
            
            # Detectar anomalias
            anomaly_labels = self.isolation_forest.fit_predict(X_scaled)
            anomaly_scores = self.isolation_forest.score_samples(X_scaled)
            
            # Filtrar anomalias
            df['anomaly_score'] = anomaly_scores
            df['is_anomaly'] = anomaly_labels == -1
            
            anomalies = df[df['is_anomaly']].copy()
            anomalies['anomaly_method'] = 'isolation_forest'
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Erro no Isolation Forest: {str(e)}")
            return pd.DataFrame()
    
    def _detect_anomalies_clustering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detecta anomalias usando DBSCAN clustering"""
        try:
            # Features para clustering
            feature_columns = ['amount_abs', 'z_score', 'day_of_week', 'hour']
            available_features = [col for col in feature_columns if col in df.columns]
            
            if len(available_features) < 2:
                return pd.DataFrame()
            
            X = df[available_features].copy()
            X_scaled = StandardScaler().fit_transform(X)
            
            # DBSCAN clustering
            dbscan = DBSCAN(eps=0.5, min_samples=5)
            cluster_labels = dbscan.fit_predict(X_scaled)
            
            # Pontos com label -1 são considerados outliers
            df['cluster'] = cluster_labels
            anomalies = df[df['cluster'] == -1].copy()
            anomalies['anomaly_method'] = 'clustering'
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Erro no clustering: {str(e)}")
            return pd.DataFrame()
    
    def _generate_anomaly_insights(self, anomalies: pd.DataFrame, company_id: str) -> List[Dict[str, Any]]:
        """Gera insights baseados nas anomalias detectadas"""
        insights = []
        
        if anomalies.empty:
            return insights
        
        try:
            # Anomalias por valor alto
            high_value_anomalies = anomalies[anomalies['amount_abs'] > anomalies['amount_abs'].quantile(0.9)]
            
            for _, anomaly in high_value_anomalies.head(3).iterrows():
                insights.append({
                    'type': 'anomaly',
                    'priority': 'high' if anomaly['amount_abs'] > 10000 else 'medium',
                    'title': f"Transação atípica de alto valor detectada",
                    'description': self._format_anomaly_description(anomaly),
                    'data_context': {
                        'transaction_id': str(anomaly['id']),
                        'amount': float(anomaly['amount_abs']),
                        'date': anomaly['transaction_date'].isoformat() if pd.notna(anomaly['transaction_date']) else None,
                        'anomaly_score': float(anomaly.get('anomaly_score', 0)),
                        'method': anomaly.get('anomaly_method', 'unknown')
                    },
                    'potential_impact': float(anomaly['amount_abs']),
                    'action_items': [
                        'Verificar se a transação foi autorizada',
                        'Investigar possível fraude ou erro',
                        'Revisar controles internos de aprovação'
                    ]
                })
            
            # Anomalias por horário incomum
            unusual_time_anomalies = anomalies[
                (anomalies['hour'] < 6) | (anomalies['hour'] > 22)
            ]
            
            if len(unusual_time_anomalies) > 0:
                total_value = unusual_time_anomalies['amount_abs'].sum()
                insights.append({
                    'type': 'anomaly',
                    'priority': 'medium',
                    'title': f"Transações em horários incomuns detectadas",
                    'description': f"Identificamos {len(unusual_time_anomalies)} transações realizadas fora do horário comercial, totalizando R$ {total_value:,.2f}",
                    'data_context': {
                        'count': len(unusual_time_anomalies),
                        'total_value': float(total_value),
                        'transactions': unusual_time_anomalies[['id', 'amount_abs', 'hour']].to_dict('records')
                    },
                    'potential_impact': float(total_value),
                    'action_items': [
                        'Revisar transações fora do horário comercial',
                        'Verificar necessidade de aprovações especiais',
                        'Considerar implementar controles por horário'
                    ]
                })
            
            # Anomalias por frequência
            if 'z_score' in anomalies.columns:
                extreme_outliers = anomalies[abs(anomalies['z_score']) > 3]
                
                if len(extreme_outliers) > 0:
                    insights.append({
                        'type': 'anomaly',
                        'priority': 'high',
                        'title': f"Transações com valores extremamente atípicos",
                        'description': f"Detectamos {len(extreme_outliers)} transações com valores muito fora do padrão histórico da conta",
                        'data_context': {
                            'count': len(extreme_outliers),
                            'max_z_score': float(extreme_outliers['z_score'].abs().max()),
                            'transactions': extreme_outliers[['id', 'amount_abs', 'z_score']].head(5).to_dict('records')
                        },
                        'potential_impact': float(extreme_outliers['amount_abs'].sum()),
                        'action_items': [
                            'Investigar transações com Z-score > 3',
                            'Verificar se são compras excepcionais legítimas',
                            'Revisar limites de aprovação por conta'
                        ]
                    })
            
        except Exception as e:
            logger.error(f"Erro ao gerar insights de anomalias: {str(e)}")
        
        return insights[:5]  # Máximo 5 insights por análise
    
    def _format_anomaly_description(self, anomaly: pd.Series) -> str:
        """Formata descrição da anomalia"""
        try:
            date_str = anomaly['transaction_date'].strftime('%d/%m/%Y %H:%M') if pd.notna(anomaly['transaction_date']) else 'Data inválida'
            description = str(anomaly.get('description', 'Sem descrição'))[:50]
            
            return (
                f"Transação de R$ {anomaly['amount_abs']:,.2f} em {date_str}. "
                f"Descrição: {description}{'...' if len(str(anomaly.get('description', ''))) > 50 else ''}. "
                f"Score de anomalia: {anomaly.get('anomaly_score', 0):.3f}"
            )
        except Exception:
            return f"Transação atípica de R$ {anomaly.get('amount_abs', 0):,.2f}"
    
    def detect_spending_pattern_anomalies(self, company_id: str) -> List[Dict[str, Any]]:
        """
        Detecta anomalias em padrões de gastos por categoria
        """
        try:
            # Período de análise: últimos 6 meses
            end_date = timezone.now()
            start_date = end_date - timedelta(days=180)
            
            # Gastos mensais por categoria
            monthly_spending = Transaction.objects.filter(
                bank_account__company_id=company_id,
                transaction_date__range=[start_date, end_date],
                amount__lt=0  # Apenas despesas
            ).extra(
                select={'month': "DATE_TRUNC('month', transaction_date)"}
            ).values('month', 'category__name').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('month', 'category__name')
            
            if not monthly_spending:
                return []
            
            # Converter para DataFrame
            df = pd.DataFrame(list(monthly_spending))
            df['total'] = df['total'].abs()  # Converter para valores positivos
            df['month'] = pd.to_datetime(df['month'])
            
            # Pivot para ter categorias como colunas
            pivot_df = df.pivot_table(
                index='month',
                columns='category__name',
                values='total',
                fill_value=0
            )
            
            insights = []
            
            # Detectar aumentos anômalos por categoria
            for category in pivot_df.columns:
                series = pivot_df[category]
                if len(series) < 3:  # Precisa de pelo menos 3 meses
                    continue
                
                # Calcular variação percentual mês a mês
                pct_change = series.pct_change()
                
                # Detectar aumentos > 50%
                anomalous_increases = pct_change[pct_change > 0.5]
                
                if len(anomalous_increases) > 0:
                    latest_increase = anomalous_increases.iloc[-1]
                    latest_month = anomalous_increases.index[-1]
                    current_value = series[latest_month]
                    previous_value = series[series.index < latest_month].iloc[-1] if len(series[series.index < latest_month]) > 0 else 0
                    
                    insights.append({
                        'type': 'cost_anomaly',
                        'priority': 'high' if latest_increase > 1.0 else 'medium',
                        'title': f"Aumento anômalo em {category}",
                        'description': f"Os gastos com {category} aumentaram {latest_increase*100:.1f}% em {latest_month.strftime('%B/%Y')}, saltando de R$ {previous_value:,.2f} para R$ {current_value:,.2f}",
                        'data_context': {
                            'category': category,
                            'increase_percentage': float(latest_increase * 100),
                            'previous_value': float(previous_value),
                            'current_value': float(current_value),
                            'month': latest_month.isoformat()
                        },
                        'potential_impact': float(current_value - previous_value),
                        'action_items': [
                            f'Investigar causa do aumento em {category}',
                            'Revisar contratos e fornecedores da categoria',
                            'Analisar se é um gasto sazonal ou permanente'
                        ]
                    })
            
            return insights[:3]  # Máximo 3 insights
            
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias de padrão: {str(e)}")
            return []
    
    def generate_automated_insights(self, company_id: str) -> List[Dict[str, Any]]:
        """
        Gera todos os tipos de insights de anomalias automaticamente
        """
        all_insights = []
        
        # Detectar anomalias em transações
        transaction_insights = self.detect_transaction_anomalies(company_id)
        all_insights.extend(transaction_insights)
        
        # Detectar anomalias em padrões de gastos
        pattern_insights = self.detect_spending_pattern_anomalies(company_id)
        all_insights.extend(pattern_insights)
        
        return all_insights