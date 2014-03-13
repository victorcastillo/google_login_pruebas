"""
Google OpenID and OAuth support

OAuth works straightforward using anonymous configurations, username
is generated by requesting email to the not documented, googleapis.com
service. Registered applications can define settings GOOGLE_CONSUMER_KEY
and GOOGLE_CONSUMER_SECRET and they will be used in the auth process.
Setting GOOGLE_OAUTH_EXTRA_SCOPE can be used to access different user
related data, like calendar, contacts, docs, etc.

OAuth2 works similar to OAuth but application must be defined on Google
APIs console https://code.google.com/apis/console/ Identity option.

OpenID also works straightforward, it doesn't need further configurations.
"""
from urllib import urlencode
from urllib2 import Request

from oauth2 import Request as OAuthRequest

try:
    import json as simplejson
except ImportError:
    try:
        import simplejson
    except ImportError:
        from django.utils import simplejson

from social_auth.utils import setting, dsa_urlopen
from social_auth.backends import OpenIdAuth, ConsumerBasedOAuth, BaseOAuth2, \
                                 OAuthBackend, OpenIDBackend
from social_auth.exceptions import AuthFailed

from login.models import BlackList
# from django.contrib.auth.models 

# Google OAuth base configuration
GOOGLE_OAUTH_SERVER = 'www.google.com'
AUTHORIZATION_URL = 'https://www.google.com/accounts/OAuthAuthorizeToken'
REQUEST_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetRequestToken'
ACCESS_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetAccessToken'

# Google OAuth2 base configuration
GOOGLE_OAUTH2_SERVER = 'accounts.google.com'
GOOGLE_OATUH2_AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/auth'

# scope for user email, specify extra scopes in settings, for example:
# GOOGLE_OAUTH_EXTRA_SCOPE = ['https://www.google.com/m8/feeds/']
GOOGLE_OAUTH_SCOPE = ['https://www.googleapis.com/auth/userinfo#email']
GOOGLE_OAUTH2_SCOPE = ['https://www.googleapis.com/auth/userinfo.email',
                       'https://www.googleapis.com/auth/userinfo.profile']
GOOGLEAPIS_EMAIL = 'https://www.googleapis.com/userinfo/email'
GOOGLEAPIS_PROFILE = 'https://www.googleapis.com/oauth2/v1/userinfo'
GOOGLE_OPENID_URL = 'https://www.google.com/accounts/o8/id'


# Backends
class GoogleOAuthBackend(OAuthBackend):
    """Google OAuth authentication backend"""
    name = 'google-oauth'

    def get_user_id(self, details, response):
        """Use google email as unique id"""
        validate_whitelists(self, details['email'])
        return details['email']

    def get_user_details(self, response):
        """Return user details from Orkut account"""
        email = response.get('email', '')
        return {'username': email.split('@', 1)[0],
                'email': email,
                'fullname': '',
                'first_name': '',
                'last_name': ''}


class GoogleOAuth2Backend(GoogleOAuthBackend):
    """Google OAuth2 authentication backend"""
    name = 'google-oauth2'
    EXTRA_DATA = [
        ('refresh_token', 'refresh_token', True),
        ('expires_in', 'expires'),
        ('token_type', 'token_type', True)
    ]

    def get_user_id(self, details, response):
        """Use google email or id as unique id"""
        user_id = super(GoogleOAuth2Backend, self).get_user_id(details,
                                                               response)
        if setting('GOOGLE_OAUTH2_USE_UNIQUE_USER_ID', False):
            return response['id']
        return user_id

    def get_user_details(self, response):
        email = response.get('email', '')
        return {'username': email.split('@', 1)[0],
                'email': email,
                'fullname': response.get('name', ''),
                'first_name': response.get('given_name', ''),
                'last_name': response.get('family_name', '')}






# TODO: Remove this setting name check, keep for backward compatibility
_OAUTH2_KEY_NAME = setting('GOOGLE_OAUTH2_CLIENT_ID') and \
                   'GOOGLE_OAUTH2_CLIENT_ID' or \
                   'GOOGLE_OAUTH2_CLIENT_KEY'


class GoogleOAuth2(BaseOAuth2):
    """Google OAuth2 support"""
    AUTH_BACKEND = GoogleOAuth2Backend
    AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/auth'
    ACCESS_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
    REVOKE_TOKEN_URL = 'https://accounts.google.com/o/oauth2/revoke'
    REVOKE_TOKEN_METHOD = 'GET'
    SETTINGS_KEY_NAME = _OAUTH2_KEY_NAME
    SETTINGS_SECRET_NAME = 'GOOGLE_OAUTH2_CLIENT_SECRET'
    SCOPE_VAR_NAME = 'GOOGLE_OAUTH_EXTRA_SCOPE'
    DEFAULT_SCOPE = GOOGLE_OAUTH2_SCOPE
    REDIRECT_STATE = False

    def user_data(self, access_token, *args, **kwargs):
        """Return user data from Google API"""
        return googleapis_profile(GOOGLEAPIS_PROFILE, access_token)

    @classmethod
    def revoke_token_params(cls, token, uid):
        return {'token': token}

    @classmethod
    def revoke_token_headers(cls, token, uid):
        return {'Content-type': 'application/json'}




def googleapis_profile(url, access_token):
    """
    Loads user data from googleapis service, such as name, given_name,
    family_name, etc. as it's described in:
    https://developers.google.com/accounts/docs/OAuth2Login
    """
    data = {'access_token': access_token, 'alt': 'json'}
    request = Request(url + '?' + urlencode(data))
    try:
        return simplejson.loads(dsa_urlopen(request).read())
    except (ValueError, KeyError, IOError):
        return None


def validate_whitelists(backend, email):
    """
    Validates allowed domains and emails against the following settings:
        GOOGLE_WHITE_LISTED_DOMAINS
        GOOGLE_WHITE_LISTED_EMAILS

    All domains and emails are allowed if setting is an empty list.
    """
    emails = setting('GOOGLE_WHITE_LISTED_EMAILS', [])
    domains = setting('GOOGLE_WHITE_LISTED_DOMAINS', [])
    if not BlackList.objects.filter(email=email):
        if not emails and not domains:
            return True
        if email in set(emails):
            return True # you're good
        if email.split('@', 1)[1] in set(domains):
            return True
    raise AuthFailed(backend, 'User not allowed')


# Backend definition
BACKENDS = {
    'google-oauth2': GoogleOAuth2,
}