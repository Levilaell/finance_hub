"""
OAuth2 provider implementations
"""
import requests
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, parse_qs
import secrets
import hashlib
from django.conf import settings
from django.utils import timezone
from ..security.encryption import default_encryption
import logging

logger = logging.getLogger(__name__)


class OAuth2Provider:
    """Base OAuth2 provider class"""
    
    def __init__(self, provider_config: Dict):
        self.name = provider_config['name']
        self.provider_id = provider_config['provider_id']
        self.client_id = provider_config['client_id']
        self.client_secret = provider_config['client_secret']
        self.authorization_url = provider_config['authorization_url']
        self.token_url = provider_config['token_url']
        self.user_info_url = provider_config['user_info_url']
        self.scope = provider_config.get('scope', 'email profile')
        self.redirect_uri = provider_config.get('redirect_uri')
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generate authorization URL for OAuth2 flow"""
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': self.scope,
            'redirect_uri': self.redirect_uri,
            'state': state,
        }
        
        return f"{self.authorization_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str, state: str = None) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
        }
        
        try:
            response = requests.post(
                self.token_url,
                data=data,
                headers={'Accept': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            if 'access_token' not in token_data:
                logger.error(f"No access token in response from {self.name}")
                return None
            
            return token_data
            
        except requests.RequestException as e:
            logger.error(f"Token exchange failed for {self.name}: {str(e)}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user information using access token"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        
        try:
            response = requests.get(
                self.user_info_url,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            user_data = response.json()
            return self.normalize_user_data(user_data)
            
        except requests.RequestException as e:
            logger.error(f"User info request failed for {self.name}: {str(e)}")
            return None
    
    def normalize_user_data(self, raw_data: Dict) -> Dict:
        """Normalize user data from provider to standard format"""
        # Override in subclasses
        return raw_data
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh access token using refresh token"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }
        
        try:
            response = requests.post(
                self.token_url,
                data=data,
                headers={'Accept': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Token refresh failed for {self.name}: {str(e)}")
            return None


class GoogleOAuth2Provider(OAuth2Provider):
    """Google OAuth2 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        config = {
            'name': 'Google',
            'provider_id': 'google',
            'client_id': client_id,
            'client_secret': client_secret,
            'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
            'scope': 'email profile',
            'redirect_uri': redirect_uri,
        }
        super().__init__(config)
    
    def normalize_user_data(self, raw_data: Dict) -> Dict:
        """Normalize Google user data"""
        return {
            'provider_user_id': raw_data.get('id'),
            'email': raw_data.get('email'),
            'first_name': raw_data.get('given_name', ''),
            'last_name': raw_data.get('family_name', ''),
            'avatar_url': raw_data.get('picture'),
            'email_verified': raw_data.get('verified_email', False),
            'locale': raw_data.get('locale'),
            'raw_data': raw_data,
        }


class FacebookOAuth2Provider(OAuth2Provider):
    """Facebook OAuth2 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        config = {
            'name': 'Facebook',
            'provider_id': 'facebook',
            'client_id': client_id,
            'client_secret': client_secret,
            'authorization_url': 'https://www.facebook.com/v18.0/dialog/oauth',
            'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
            'user_info_url': 'https://graph.facebook.com/v18.0/me',
            'scope': 'email',
            'redirect_uri': redirect_uri,
        }
        super().__init__(config)
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get Facebook user info with specific fields"""
        fields = 'id,email,first_name,last_name,picture,name'
        url = f"{self.user_info_url}?fields={fields}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            user_data = response.json()
            return self.normalize_user_data(user_data)
            
        except requests.RequestException as e:
            logger.error(f"Facebook user info request failed: {str(e)}")
            return None
    
    def normalize_user_data(self, raw_data: Dict) -> Dict:
        """Normalize Facebook user data"""
        picture_url = None
        if 'picture' in raw_data and 'data' in raw_data['picture']:
            picture_url = raw_data['picture']['data'].get('url')
        
        return {
            'provider_user_id': raw_data.get('id'),
            'email': raw_data.get('email'),
            'first_name': raw_data.get('first_name', ''),
            'last_name': raw_data.get('last_name', ''),
            'avatar_url': picture_url,
            'email_verified': True,  # Facebook emails are generally verified
            'raw_data': raw_data,
        }


class GitHubOAuth2Provider(OAuth2Provider):
    """GitHub OAuth2 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        config = {
            'name': 'GitHub',
            'provider_id': 'github',
            'client_id': client_id,
            'client_secret': client_secret,
            'authorization_url': 'https://github.com/login/oauth/authorize',
            'token_url': 'https://github.com/login/oauth/access_token',
            'user_info_url': 'https://api.github.com/user',
            'scope': 'user:email',
            'redirect_uri': redirect_uri,
        }
        super().__init__(config)
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get GitHub user info including email from separate endpoint"""
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json',
        }
        
        try:
            # Get basic user info
            response = requests.get(self.user_info_url, headers=headers, timeout=30)
            response.raise_for_status()
            user_data = response.json()
            
            # Get email separately (required for private emails)
            email_response = requests.get(
                'https://api.github.com/user/emails',
                headers=headers,
                timeout=30
            )
            
            if email_response.status_code == 200:
                emails = email_response.json()
                # Find primary email
                primary_email = None
                for email in emails:
                    if email.get('primary'):
                        primary_email = email.get('email')
                        break
                
                if primary_email:
                    user_data['email'] = primary_email
            
            return self.normalize_user_data(user_data)
            
        except requests.RequestException as e:
            logger.error(f"GitHub user info request failed: {str(e)}")
            return None
    
    def normalize_user_data(self, raw_data: Dict) -> Dict:
        """Normalize GitHub user data"""
        name_parts = (raw_data.get('name') or '').split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        return {
            'provider_user_id': str(raw_data.get('id')),
            'email': raw_data.get('email'),
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': raw_data.get('avatar_url'),
            'email_verified': True,  # GitHub emails are verified
            'username': raw_data.get('login'),
            'raw_data': raw_data,
        }


class LinkedInOAuth2Provider(OAuth2Provider):
    """LinkedIn OAuth2 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        config = {
            'name': 'LinkedIn',
            'provider_id': 'linkedin',
            'client_id': client_id,
            'client_secret': client_secret,
            'authorization_url': 'https://www.linkedin.com/oauth/v2/authorization',
            'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
            'user_info_url': 'https://api.linkedin.com/v2/people/~',
            'scope': 'r_liteprofile r_emailaddress',
            'redirect_uri': redirect_uri,
        }
        super().__init__(config)
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get LinkedIn user info from multiple endpoints"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        
        try:
            # Get profile info
            profile_response = requests.get(
                'https://api.linkedin.com/v2/people/~:(id,firstName,lastName,profilePicture(displayImage~:playableStreams))',
                headers=headers,
                timeout=30
            )
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            
            # Get email
            email_response = requests.get(
                'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
                headers=headers,
                timeout=30
            )
            
            email = None
            if email_response.status_code == 200:
                email_data = email_response.json()
                if 'elements' in email_data and email_data['elements']:
                    email = email_data['elements'][0]['handle~']['emailAddress']
            
            # Combine data
            user_data = profile_data.copy()
            if email:
                user_data['email'] = email
            
            return self.normalize_user_data(user_data)
            
        except requests.RequestException as e:
            logger.error(f"LinkedIn user info request failed: {str(e)}")
            return None
    
    def normalize_user_data(self, raw_data: Dict) -> Dict:
        """Normalize LinkedIn user data"""
        first_name = ''
        last_name = ''
        
        if 'firstName' in raw_data and 'localized' in raw_data['firstName']:
            # Get first available localized name
            localized_first = raw_data['firstName']['localized']
            first_name = next(iter(localized_first.values()), '')
        
        if 'lastName' in raw_data and 'localized' in raw_data['lastName']:
            localized_last = raw_data['lastName']['localized']
            last_name = next(iter(localized_last.values()), '')
        
        # Extract profile picture
        avatar_url = None
        if 'profilePicture' in raw_data:
            picture_data = raw_data['profilePicture'].get('displayImage~', {})
            if 'elements' in picture_data and picture_data['elements']:
                # Get largest image
                images = picture_data['elements']
                if images:
                    avatar_url = images[-1].get('identifiers', [{}])[0].get('identifier')
        
        return {
            'provider_user_id': raw_data.get('id'),
            'email': raw_data.get('email'),
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': avatar_url,
            'email_verified': True,  # LinkedIn emails are verified
            'raw_data': raw_data,
        }


class OAuth2Manager:
    """Manages OAuth2 providers and flows"""
    
    def __init__(self):
        self.providers = {}
        self._load_providers()
    
    def _load_providers(self):
        """Load OAuth2 providers from settings"""
        oauth_settings = getattr(settings, 'OAUTH2_PROVIDERS', {})
        
        for provider_id, config in oauth_settings.items():
            if not config.get('client_id') or not config.get('client_secret'):
                continue
            
            redirect_uri = config.get('redirect_uri')
            
            if provider_id == 'google':
                self.providers[provider_id] = GoogleOAuth2Provider(
                    config['client_id'],
                    config['client_secret'],
                    redirect_uri
                )
            elif provider_id == 'facebook':
                self.providers[provider_id] = FacebookOAuth2Provider(
                    config['client_id'],
                    config['client_secret'],
                    redirect_uri
                )
            elif provider_id == 'github':
                self.providers[provider_id] = GitHubOAuth2Provider(
                    config['client_id'],
                    config['client_secret'],
                    redirect_uri
                )
            elif provider_id == 'linkedin':
                self.providers[provider_id] = LinkedInOAuth2Provider(
                    config['client_id'],
                    config['client_secret'],
                    redirect_uri
                )
    
    def get_provider(self, provider_id: str) -> Optional[OAuth2Provider]:
        """Get OAuth2 provider by ID"""
        return self.providers.get(provider_id)
    
    def get_available_providers(self) -> Dict[str, str]:
        """Get list of available providers"""
        return {
            provider_id: provider.name
            for provider_id, provider in self.providers.items()
        }
    
    def initiate_oauth_flow(self, provider_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Initiate OAuth2 flow"""
        provider = self.get_provider(provider_id)
        if not provider:
            return None, None
        
        state = self._generate_state()
        auth_url = provider.get_authorization_url(state)
        
        return auth_url, state
    
    def complete_oauth_flow(self, provider_id: str, code: str, state: str) -> Optional[Dict]:
        """Complete OAuth2 flow and return user data"""
        provider = self.get_provider(provider_id)
        if not provider:
            return None
        
        # Exchange code for token
        token_data = provider.exchange_code_for_token(code, state)
        if not token_data:
            return None
        
        # Get user info
        user_info = provider.get_user_info(token_data['access_token'])
        if not user_info:
            return None
        
        # Combine token and user data
        return {
            'provider_id': provider_id,
            'provider_name': provider.name,
            'token_data': token_data,
            'user_info': user_info,
        }
    
    def _generate_state(self) -> str:
        """Generate secure state parameter"""
        return secrets.token_urlsafe(32)
    
    def _verify_state(self, provided_state: str, expected_state: str) -> bool:
        """Verify state parameter"""
        return provided_state == expected_state


# Global OAuth2 manager instance
oauth_manager = OAuth2Manager()