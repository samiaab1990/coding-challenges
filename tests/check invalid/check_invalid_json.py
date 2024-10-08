# Tests if input is a valid json format (must include at least one opening bracket, key, value, 
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from json_parser import read_json

file_input1 = 'correct.json'
file_input2 = 'incorrect.json'

read_json(file_input1)
read_json(file_input2)
