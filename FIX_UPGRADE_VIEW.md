# 🚨 Correção Urgente: UpgradeSubscriptionView

## Problema Identificado

O `UpgradeSubscriptionView` está completamente quebrado:
1. Chama `create_subscription` ao invés de `update_subscription`
2. Não usa cálculo de proration
3. Atualiza plano localmente antes de confirmar com gateway
4. Não cria checkout session para cobrar diferença

## Correção Necessária

```python
class UpgradeSubscriptionView(APIView):
    """Upgrade/Downgrade company subscription"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # ... get company logic ...
        
        new_plan = SubscriptionPlan.objects.get(
            id=serializer.validated_data['plan_id']
        )
        billing_cycle = serializer.validated_data.get('billing_cycle', 'monthly')
        
        # Check if it's actually a change
        if company.subscription_plan.id == new_plan.id:
            return Response({
                'error': 'Already on this plan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.payments.payment_service import PaymentService
        payment_service = PaymentService()
        
        # Calculate proration
        proration = payment_service.calculate_proration(
            company, new_plan, billing_cycle
        )
        
        try:
            if company.subscription_id:
                # Existing subscription - update with Stripe
                result = payment_service.update_subscription(
                    company, new_plan, billing_cycle
                )
                
                # Stripe handles proration automatically
                return Response({
                    'message': 'Subscription updated successfully',
                    'new_plan': SubscriptionPlanSerializer(new_plan).data,
                    'proration': proration,
                    'payment_required': proration['net_amount'] > 0
                })
            else:
                # No subscription ID - create checkout
                return Response({
                    'error': 'Please use checkout endpoint for new subscriptions'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Upgrade error: {e}")
            return Response({
                'error': 'Failed to update subscription'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## Fluxo Correto

### Para Upgrade:
1. Calcular proration
2. Chamar `update_subscription` no Stripe
3. Stripe cria invoice automática para diferença
4. Cobra imediatamente se upgrade
5. Credita se downgrade

### Para Downgrade:
1. Calcular crédito
2. Atualizar subscription
3. Crédito aplicado na próxima fatura
4. Muda no final do período

## Teste Necessário

1. Testar upgrade de Professional → Enterprise
2. Testar downgrade de Enterprise → Professional
3. Verificar se proration está correta
4. Confirmar cobrança/crédito no Stripe