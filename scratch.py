import os

files = {
    'ai-service/api/investigate.py': '"/investigate"',
    'ai-service/api/recommend.py': '"/recommend"',
    'ai-service/api/validate.py': '"/validate"'
}

for path, route in files.items():
    with open(path, 'r') as f:
        content = f.read()
    content = content.replace('@router.get("",', f'@router.get({route},')
    with open(path, 'w') as f:
        f.write(content)
print('Fixed routes')
