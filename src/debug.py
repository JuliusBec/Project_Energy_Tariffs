import sys
import os

print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print("Files in current directory:")
for f in os.listdir():
    print(f"  - {f}")
print("\nEnvironment variables:")
for k, v in os.environ.items():
    print(f"  {k}={v}")
