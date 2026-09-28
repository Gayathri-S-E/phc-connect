import os
import re

for f in os.listdir('f:/github/phc connect/backend/alembic/versions'):
    if not f.endswith('.py'):
        continue
    path = os.path.join('f:/github/phc connect/backend/alembic/versions', f)
    with open(path, 'r') as fp:
        content = fp.read()
    
    # We will just comment out the line where `_enum.create(op.get_bind()` is called.
    new_content = re.sub(r"^(\s*)([a-zA-Z0-9_]+\.create\(op\.get_bind)", r"\1# \2", content, flags=re.MULTILINE)
    
    if new_content != content:
        with open(path, 'w') as fp:
            fp.write(new_content)
        print('Fixed:', f)
