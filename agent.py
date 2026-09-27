import os
import re 
import subprocess
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

import sys

source_file = sys.argv[1]
test_file = sys.argv[2]


command_list = ["pytest", test_file]
result = subprocess.run(command_list, capture_output=True, text=True)

print("Output: ",result.stdout)
print("Output: ",result.stderr)


max_attempts = 3
attempt = 0
passed = False

while attempt < max_attempts and not passed:
    attempt += 1
    print(f"--- Attempt {attempt} ---")

    
    with open(source_file, "r") as f:
        source_code = f.read()

    
    result = subprocess.run(["pytest", test_file], capture_output=True, text=True)

    #to check before if the code already works 
    if "1 passed" in result.stdout:
        passed = True
        print("Test passed! Fix successful.")
        break

    
    prompt = f"""
    You are a code-fixing agent. Here is a Python file with a bug:

```python
    {source_code}
```

    Here is the test failure when running this code:

    {result.stdout}

    Fix the bug. Return ONLY the corrected full file content inside a python code block, and nothing else.
    """
    response = model.generate_content(prompt)
    match = re.search(r"```python(.*?)```", response.text, re.DOTALL)
    fixed_code = match.group(1)

    
    with open(source_file, "w") as f:
        f.write(fixed_code)

    
    recheck = subprocess.run(["pytest", test_file], capture_output=True, text=True)
    if "1 passed" in recheck.stdout:
        passed = True 
        print("Test passed after fix! Fix successful.")

if not passed:
    print(f"Gave up after {max_attempts} attempts. Still failing.")


result2 = subprocess.run(["pytest", test_file], capture_output=True, text=True)
print("RE-TEST RESULT:")
print(result2.stdout)

