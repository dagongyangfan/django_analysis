import sys
import os

print("Step 1: Start", flush=True)

try:
    import pandas as pd
    print("Step 2: Pandas imported", flush=True)
except Exception as e:
    print(f"Error importing pandas: {e}", flush=True)

try:
    import matplotlib.pyplot as plt
    print("Step 3: Matplotlib imported", flush=True)
except Exception as e:
    print(f"Error importing matplotlib: {e}", flush=True)

try:
    import seaborn as sns
    print("Step 4: Seaborn imported", flush=True)
except Exception as e:
    print(f"Error importing seaborn: {e}", flush=True)

data_path = 'data/django_bugs_filtered.csv'
if os.path.exists(data_path):
    print(f"Step 5: File found at {data_path}", flush=True)
else:
    print(f"Step 5: File NOT found at {data_path}. CWD is {os.getcwd()}", flush=True)
    # Check if it's in current dir
    if os.path.exists('django_bugs_filtered.csv'):
        print("But found in current directory.", flush=True)
        
print("Step 6: Done", flush=True)
