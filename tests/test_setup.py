import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    import streamlit as st
    print(f"✅ Streamlit version: {st.__version__}")
except ImportError as e:
    print(f"❌ Streamlit import failed: {e}")

try:
    import openai
    print(f"✅ OpenAI version: {openai.__version__}")
except ImportError as e:
    print(f"❌ OpenAI import failed: {e}")

try:
    import groq
    print(f"✅ Groq installed")
except ImportError as e:
    print(f"❌ Groq import failed: {e}")

try:
    import numpy as np
    print(f"✅ NumPy version: {np.__version__}")
except ImportError as e:
    print(f"❌ NumPy import failed: {e}")

import os
from dotenv import load_dotenv
load_dotenv()
print(f"✅ Environment variables loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

print("\n🎉 Setup verification complete!")