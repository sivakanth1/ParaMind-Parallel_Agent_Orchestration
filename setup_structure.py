import os

# Create directory structure
dirs = [
    'src', 'ui', 'tests', 'logs', 'config', 'data'
]

files = [
    'src/__init__.py',
    'src/controller.py',
    'src/agents.py',
    'src/aggregator.py',
    'src/llm_clients.py',
    'ui/__init__.py',
    'ui/streamlit_app.py',
    'tests/__init__.py',
    'tests/test_agents.py',
    'config/__init__.py',
    'config/settings.py',
    'data/test_prompts.json',
    '.env.example',
    '.gitignore',
    'requirements.txt',
    'README.md'
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    
for f in files:
    open(f, 'a').close()

print("✅ Project structure created successfully!")