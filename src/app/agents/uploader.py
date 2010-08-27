"""
    Uploader Agent
        
    Created on 2010-08-26
    @author: jldupont
"""
__all__=["UploaderAgent"]
import httplib
import oauth.oauth as oauth

from app.system.base import AgentThreadedBase

class UploaderAgent(AgentThreadedBase):
    
    def __init__(self, end_point, server, port, consumer_key, consumer_secret, debug=False):
        AgentThreadedBase.__init__(self, debug)
        self.server=server
        self.port=port
        self.consumer_key=consumer_key
        self.consumer_secret=consumer_secret
        self.end_point=end_point
        self.akey=None
        self.asecret=None
        self.token=None
        self.consumer = oauth.OAuthConsumer(self.consumer_key, 
                                            self.consumer_secret)
        self.signature_method_hmac_sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.connection = httplib.HTTPConnection("%s:%d" % (self.server, self.port))
        
    def h_oauth(self, key, secret):
        self.akey=key
        self.asecret=secret
        self.token=oauth.OAuthToken(key, secret)
        
    def h_ratings_to_upload(self, entries):
        """
        Rating entries to upload to web-service
        """
        if entries is None:
            self.dprint("!!! uploader: no entries...")
            return
        
        try:    c=len(entries)
        except: c=0
        
        if c==0:
            self.dprint("!!! uploader: no entries...")
            return

        ## can't do much without the required access token...
        ## @todo: rate limit this maybe? 
        if self.token is None:
            self.pub("oauth?")
            self.dprint("!! asking for oauth parameters...")
            return
            
        
        print "]]]] h_ratings_to_upload: entry[0]: %s" % entries[0]
            
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, 
                                                                   token=self.token, 
                                                                   http_method='POST', 
                                                                   http_url=self.end_point, 
                                                                   parameters=None)
        
        oauth_request.sign_request(self.signature_method_hmac_sha1, self.consumer, self.token)
        
        headers = {'Content-Type' :'application/x-www-form-urlencoded'}
        self.connection.request('POST', self.end_point, body=oauth_request.to_postdata(), headers=headers)
        response = self.connection.getresponse()
        rep=response.read()
        print rep

        
    
 
