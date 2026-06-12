import urllib.request
import json
endpoints = ['/health', '/ai/cluster', '/ai/investigate', '/ai/recommend', '/ai/validate']
base_url = 'http://localhost:8000'
for ep in endpoints:
    url = base_url + ep
    print(f'\n--- Testing {url} ---')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            body = response.read().decode('utf-8')
            status = response.getcode()
            print(f'Status: {status}')
            try:
                data = json.loads(body)
                if isinstance(data, list):
                    print(f'Item Count: {len(data)}')
                else:
                    print('Item Count: Not a list')
            except Exception:
                print(f'Body: {body[:100]}')
    except Exception as e:
        if hasattr(e, 'read'):
            print(f'Error: {e} - {e.read().decode("utf-8")}')
        else:
            print(f'Error: {e}')
