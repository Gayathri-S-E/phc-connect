import os
import re

for f in os.listdir('f:/github/phc connect/backend/alembic/versions'):
    if not f.endswith('.py'):
        continue
    path = os.path.join('f:/github/phc connect/backend/alembic/versions', f)
    with open(path, 'r') as fp:
        content = fp.read()
    
    new_content = re.sub(r"(name='[^']+_enum')\s*\)", r"\1, create_type=False)", content)
    
    if new_content != content:
        with open(path, 'w') as fp:
            fp.write(new_content)
        print('Fixed:', f)
