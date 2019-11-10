import os
from colorama import Fore, Back, Style 

test_command = "/Library/Frameworks/Python.framework/Versions/3.7/bin/python3 -m pytest -rA --tb=long src/tests"
os.system(test_command)
print(Fore.GREEN + 'Test suite finished')