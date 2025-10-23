import re

with open("test_03.txt", "r", encoding="utf-8") as f:
    content = f.read()
    lines = content.split("\n")

    for line in lines:
        if "blocked" in line:
            match = re.search(r"\b\d{10,15}\b", line)
            if match:
                print(match.group())

