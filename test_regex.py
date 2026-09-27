import re

fake_response = "Here's the fix:\n```python\ndef add(a,b): return a+b\n```\nLet me know!"

pattern = r"```python(.*?)```"

match = re.search(pattern, fake_response, re.DOTALL)

code = match.group(1)

print(code)