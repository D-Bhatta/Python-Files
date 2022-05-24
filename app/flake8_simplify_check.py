"""Trigger flake8-simplify warning SIM108

SIM108 Use ternary operator 'b = c if a else d' instead of if-else-block'
"""


a = None
b = 2
c = 3
d = 4

if a:
    b = c
else:
    b = d
