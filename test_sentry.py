import urllib.request
import json
import ssl

def main():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 1. Login to get token
    login_data = json.dumps({
        'email': 'operator@example.com',
        'password': 'Password123!'
    }).encode('utf-8')
    
    login_req = urllib.request.Request(
        'http://localhost:8000/api/v1/auth/login/',
        data=login_data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        login_res = urllib.request.urlopen(login_req, context=ctx)
        token_data = json.loads(login_res.read())
        token = token_data.get('access') or token_data.get('key') or token_data.get('token')
        print(f"Got token: {token}")
        
        if not token:
            print("Failed to get token!")
            return
            
        # 2. Trigger Sentry with token
        sentry_req = urllib.request.Request(
            'http://localhost:8000/sentry-debug/',
            headers={
                'Authorization': f'Token {token}',
                'Content-Type': 'application/json'
            }
        )
        
        # It's expected to fail with 500
        urllib.request.urlopen(sentry_req, context=ctx)
        print("Sentry debug succeeded (unexpected)")
        
    except urllib.error.HTTPError as e:
        print(f"Request failed with {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
