"""
    Authorization Agent
    
    Responsible for handling the authorization process
    with the user
    
    Messages Processed:
    - "start_authorize"
    - "start_verify"
    - "oauth_error"
    - "oauth?"
    
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
    
    gREQUEST_TOKEN_URL = 'OAuthGetRequestToken'
    gACCESS_TOKEN_URL =  'OAuthGetAccessToken'
    gAUTHORIZATION_URL = 'OAuthAuthorizeToken'
    
    def __init__(self, server, port, base):
        self.server=server
        self.port=port
        self.base=base
        self.request_token_url=self.base+self.gREQUEST_TOKEN_URL
        self.access_token_url=self.base+self.gACCESS_TOKEN_URL
        self.authorize_token_url=self.base+self.gAUTHORIZATION_URL
        self.connection = httplib.HTTPConnection("%s:%d" % (self.server, self.port))
        
    def fetch_request_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, self.request_token_url, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())
        
    def fetch_access_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, self.access_token_url, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def authorize_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, oauth_request.to_url()) 
        response = self.connection.getresponse()
        return response.read()
        

class AuthorizeAgent(AgentThreadedBase):

    CALLBACK_URL = "oob"
    
    REQUEST_TOKEN="oauth_request_token"
    ACCESS_TOKEN_KEY="oauth_access_token_key"
    ACCESS_TOKEN_SECRET="oauth_access_token_secret"
    VERIFICATION_CODE="oauth_verification_code"
    
    def __init__(self, app_name, server, port, consumer_key, consumer_secret, base):
        """
        @param interval: interval in seconds
        """
        AgentThreadedBase.__init__(self)
        self.server=server
        self.port=port
        self.base=base
        
        self.consumer_key=consumer_key
        self.consumer_secret=consumer_secret
        self.app_name=app_name
        self.client=OauthClient(server, port, base)
        self.consumer=None
        self.signature_method_plaintext = oauth.OAuthSignatureMethod_PLAINTEXT()
        self.signature_method_hmac_sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.token=None
        self.sm=StateManager(self.app_name)

    def h_start_authorize(self, *_):
        try:
            self.token=None
            self.consumer = oauth.OAuthConsumer(self.consumer_key, self.consumer_secret)            
            oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, 
                                                                       callback=self.CALLBACK_URL, 
                                                                       http_url=self.client.request_token_url)
            oauth_request.sign_request(self.signature_method_hmac_sha1, self.consumer, None)
            self.token = self.client.fetch_request_token(oauth_request)
            oauth_request = oauth.OAuthRequest.from_token_and_callback(token=self.token, 
                                                                       http_url=self.client.authorize_token_url)
            url= oauth_request.to_url()
            self.sm.save(self.REQUEST_TOKEN, self.token)
        except Exception,e:
            self.pub("error_requesttoken", e)
            self.pub("log", "warning", "Authorization: 'RequestToken' failed: "+str(e))
            return

        self.pub("log", "getting authorization from url: "+url)
        try:        
            webbrowser.open(url)
            print url
        except Exception,e:
            self.pub("log", "error", "Opening url(%s)" % url)
        
    def h_start_verify(self, verificationCode):
        """
        Got verification code from user
        
        Attempting to retrieve "access token"
        """
        try:
            self.consumer = oauth.OAuthConsumer(self.consumer_key, self.consumer_secret)
            oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=self.token, 
                                                                       verifier=verificationCode, 
                                                                       http_url=self.client.access_token_url)
            oauth_request.sign_request(self.signature_method_hmac_sha1, self.consumer, self.token)
            self.atoken = self.client.fetch_access_token(oauth_request)
        except Exception,e:
            self.atoken=None
            self.sm.save(self.ACCESS_TOKEN_KEY, "")
            self.sm.save(self.ACCESS_TOKEN_SECRET, "")
            self.pub("oauth", None, None)
            self.pub("error_accesstoken", e)
            self.pub("log", "warning", "Verification: 'AccessToken' failed: "+str(e))
            return
        finally:
            self.sm.save(self.VERIFICATION_CODE, verificationCode)
            
        try:
            key=self.atoken.key
            secret=self.atoken.secret
            self.pub("oauth", key, secret)
            self.pub("log", "oauth: key: %s  secret: %s" % (key, secret))
            self.sm.save(self.ACCESS_TOKEN_KEY, key)
            self.sm.save(self.ACCESS_TOKEN_SECRET, secret)
        except:
            self.sm.save(self.ACCESS_TOKEN_KEY, "")
            self.sm.save(self.ACCESS_TOKEN_SECRET, "")            
            self.pub("log", "warning", "Verification: 'AccessToken' failed: "+str(e))            

    def h_oauth_error(self, *_):
        """
        An oauth level error occured - reset access token
        """
        self.sm.save(self.ACCESS_TOKEN, "")
        self.sm.save(self.VERIFICATION_CODE, "")

    def hq_oauth(self):
        key=self.sm.retrieve(self.ACCESS_TOKEN_KEY)
        secret=self.sm.retrieve(self.ACCESS_TOKEN_SECRET)
        self.pub("oauth", key, secret)
        

"""
_=AuthorizeAgent()
_.start()
"""