# Python JSON Parser {}

A Python program that parses JSON string into a Python dictionary.

## From command-line

```bash
python json_parser.py file.json
```
## As module

```python
from json_parser import JSON

json_input = {}

json_object = JSON(json_input)

# returns tokens in the JSON string 
print(json_object.tokens())

# returns parsed JSON string into dictionary object in Python
print(json.object.parse_json())
```
Inspired by [Coding Challenges](https://codingchallenges.fyi/challenges/challenge-json-parser). 
