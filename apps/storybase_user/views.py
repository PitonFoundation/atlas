import oauth2 as oauth
import urllib

from django.shortcuts import redirect

from .models import OAuth2Provider

provider = OAuth2Provider.objects.get(name='Google')
client = oauth.Client2(provider.client_id, provider.client_secret, provider.base_url)

def google_login(request):
    scope = 'https://spreadsheets.google.com/feeds/'
    # TODO: Generate this dynamically
    redirect_uri = 'http://127.0.0.1:8000/storybase/user/google-oauth2-callback'
    params = {
        'scope': scope,
        'response_type': 'code',
    }
    oauth_url = client.authorization_url(redirect_uri=redirect_uri,
        params=params, endpoint='')

    return redirect(oauth_url)

def google_oauth2_callback(request):
    # TODO: Catch if code parameter is not provided
    code = request.GET['code']
    # TODO: Generate this dynamically
    redirect_uri = 'http://127.0.0.1:8000/storybase/user/google-oauth2-callback'
    params = {
        'grant_type': 'authorization_code'
    }
    resp_args = client.access_token(code, redirect_uri, params=params,
        endpoint='token')
        
    print resp_args 
    # BOOKMARK
    raise NotImplemented

def google_logout(request):
    raise NotImplemented

