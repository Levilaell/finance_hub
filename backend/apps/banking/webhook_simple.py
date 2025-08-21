"""
Webhook simples para debug - sem dependências complexas
"""
import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def simple_webhook(request):
    """
    Webhook simples para debug
    """
    try:
        logger.info("=== WEBHOOK DEBUG START ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"Path: {request.path}")
        logger.info(f"Content-Type: {request.content_type}")
        
        # Parse body
        try:
            payload = request.body.decode('utf-8')
            logger.info(f"Payload length: {len(payload)}")
            
            data = json.loads(payload)
            logger.info(f"JSON parsed successfully: {list(data.keys())}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Payload error: {e}")
            return JsonResponse({"error": "Payload error"}, status=400)
        
        # Simple response
        response_data = {
            "status": "success",
            "message": "Webhook received successfully",
            "debug": True
        }
        
        logger.info("=== WEBHOOK DEBUG SUCCESS ===")
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        return JsonResponse({"error": "Critical error", "details": str(e)}, status=500)