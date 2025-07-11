"""
Belvo API Client for Open Banking Integration
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class BelvoClient:
    """Client for Belvo Open Banking API"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'BELVO_BASE_URL', 'https://sandbox.belvo.com')
        self.secret_id = getattr(settings, 'BELVO_SECRET_ID', '')
        self.secret_password = getattr(settings, 'BELVO_SECRET_PASSWORD', '')
        self.session = requests.Session()
        self.session.auth = (self.secret_id, self.secret_password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_link(self, institution: str, username: str, password: str) -> Dict[str, Any]:
        """Create a link to a financial institution"""
        endpoint = f"{self.base_url}/api/links/"
        
        payload = {
            "institution": institution,
            "username": username,
            "password": password,
            "access_mode": "single"  # or "recurrent" for automatic updates
        }
        
        try:
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Belvo link: {str(e)}")
            raise
    
    def get_accounts(self, link_id: str) -> List[Dict[str, Any]]:
        """Get accounts for a link"""
        endpoint = f"{self.base_url}/api/accounts/"
        
        params = {
            "link": link_id
        }
        
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching accounts: {str(e)}")
            raise
    
    def get_transactions(self, link_id: str, account_id: str, 
                        date_from: Optional[datetime] = None,
                        date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get transactions for an account"""
        endpoint = f"{self.base_url}/api/transactions/"
        
        if not date_from:
            date_from = datetime.now() - timedelta(days=90)
        if not date_to:
            date_to = datetime.now()
        
        params = {
            "link": link_id,
            "account": account_id,
            "date_from": date_from.strftime("%Y-%m-%d"),
            "date_to": date_to.strftime("%Y-%m-%d")
        }
        
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching transactions: {str(e)}")
            raise
    
    def get_institutions(self, country_code: str = "BR") -> List[Dict[str, Any]]:
        """Get list of supported institutions"""
        cache_key = f"belvo_institutions_{country_code}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        endpoint = f"{self.base_url}/api/institutions/"
        params = {"country_code": country_code}
        
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            institutions = response.json()
            
            # Cache for 24 hours
            cache.set(cache_key, institutions, 86400)
            return institutions
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching institutions: {str(e)}")
            raise
    
    def delete_link(self, link_id: str) -> bool:
        """Delete a link"""
        endpoint = f"{self.base_url}/api/links/{link_id}/"
        
        try:
            response = self.session.delete(endpoint)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting link: {str(e)}")
            return False
    
    def create_widget_token(self) -> Dict[str, Any]:
        """Create a widget token for frontend integration"""
        endpoint = f"{self.base_url}/api/token/"
        
        payload = {
            "id": self.secret_id,
            "password": self.secret_password,
            "scopes": "read_institutions,write_links,read_links"
        }
        
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating widget token: {str(e)}")
            raise