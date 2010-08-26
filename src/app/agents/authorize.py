"""
    Authorization Agent
    
    Responsible for handling the authorization process
    with the user
    
    Messages Processed:
    - "start_authorize"
    - "start_verify"
    
    Messages Generated:
    - "error_requesttoken"
    - "error_webbrowser"
    - "error_accesstoken"
        
    Created on 2010-08-15
    @author: jldupont
"""
__all__=["AuthorizeAgent"]

import oauth.oauth as oauth
import httplib
import webbrowser

from app.system.base import AgentThreadedBase
from app.system.state import StateManager

class OauthClient(object):
    
    SERVER = 'services.systemical.com'
    PORT = 80
    BASE = "http://services.systemical.com/_ah/"
    REQUEST_TOKEN_URL = BASE+'OAuthGetRequestToken'
    ACCESS_TOKEN_URL =  BASE+'OAuthGetAccessToken'
    AUTHORIZATION_URL = BASE+'OAuthAuthorizeToken'
    
    def __init__(self):
        self.connection = httplib.HTTPConnection("%s:%d" % (self.SERVER, self.PORT))
        
    def fetch_request_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, self.REQUEST_TOKEN_URL, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())
        
    def fetch_access_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, self.ACCESS_TOKEN_URL, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def authorize_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, oauth_request.to_url()) 
        response = self.connection.getresponse()
        return response.read()
        

class AuthorizeAgent(AgentThreadedBase):

    CONSUMER_KEY="services.systemical.com"
    CONSUMER_SECRET="PkyFMaAhcPacERXjRWFv1a/U"
    CALLBACK_URL = "oob"
    
    def __init__(self, app_name):
        """
        @param interval: interval in seconds
        """
        AgentThreadedBase.__init__(self)
        self.app_name=app_name
        self.client=OauthClient()
        self.consumer=None
        self.signature_method_plaintext = oauth.OAuthSignatureMethod_PLAINTEXT()
        self.signature_method_hmac_sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.token=None
        self.sm=StateManager(self.app_name)

    def h_start_authorize(self, *_):
        try:
            self.token=None
            self.consumer = oauth.OAuthConsumer(self.CONSUMER_KEY, self.CONSUMER_SECRET)            
            oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, 
                                                                       callback=self.CALLBACK_URL, 
                                                                       http_url=self.client.REQUEST_TOKEN_URL)
            oauth_request.sign_request(self.signature_method_hmac_sha1, self.consumer, None)
            self.token = self.client.fetch_request_token(oauth_request)
            oauth_request = oauth.OAuthRequest.from_token_and_callback(token=self.token, 
                                                                       http_url=self.client.AUTHORIZATION_URL)
            url= oauth_request.to_url()
        except Exception,e:
            self.pub("error_requesttoken", e)
            self.pub("log", "warning", "Authorization: 'RequestToken' failed: "+str(e))
            return

        self.pub("log", "getting authorization from url: "+url)
        try:        
            webbrowser.open(url)
        except Exception,e:
            self.pub("log", "error", "Opening url(%s)" % url)
        
    def h_start_verify(self, verificationCode):
        """
        Got verification code from user
        
        Attempting to retrieve "access token"
        """
        try:
            self.consumer = oauth.OAuthConsumer(self.CONSUMER_KEY, self.CONSUMER_SECRET)
            oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=self.token, 
                                                                       verifier=verificationCode, 
                                                                       http_url=self.client.ACCESS_TOKEN_URL)
            oauth_request.sign_request(self.signature_method_hmac_sha1, self.consumer, self.token)
            self.atoken = self.client.fetch_access_token(oauth_request)
        except Exception,e:
            self.pub("oauth", None, None)
            self.pub("error_accesstoken", e)
            self.pub("log", "warning", "Verification: 'AccessToken' failed: "+str(e))
            return
        
        key=self.atoken.key
        secret=self.atoken.secret
        self.pub("oauth", key, secret)
        self.pub("log", "oauth: key: %s  secret: %s" % (key, secret))


"""
_=AuthorizeAgent()
_.start()
"""