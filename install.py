"""Run this file once from IDLE (open it, then press F5).
Installs the libraries and creates the .env file."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

print("Python:", sys.version)
print("Installing libraries (5-15 minutes, please wait)...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

if not os.path.exists(".env"):
    with open(".env", "w", encoding="utf-8") as f:
        f.write("MOCK_MODE=true\nUSE_LLM=false\n")
    print("Created .env (MOCK_MODE=true)")

print("\nDone. Now open run_all.py and press F5.")
