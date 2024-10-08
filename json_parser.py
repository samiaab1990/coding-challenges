# JSON parser for Python
# References:
## Lexer/parser understanding: https://dev.to/codingwithadam/introduction-to-lexers-parsers-and-interpreters-with-chevrotain-5c7b

import sys
import re

# create token class to store json regular expression patterns
class token:
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern

# all json regular expression patterns 
## opening bracket can be { or [ at beginning of object
opening_bracket = token('opening_bracket','^{|^\\[')

## key must be from first double quote to end of next double quote (for first key) or first quote to comma that precedes quote, insofar comma is not inside a nested JSON object list
key = token('key','(?<=^").+?(?=")|(?<=,(?![^{]*\\})").+?(?=")')

## colon must be outside of nested json object or list
colon = token('colon','(?<=(:(?![^{]*\\})))')

## value must be from colon to end of comma, insofar comma is not inside nested json object or list OR the end for last key value pair
value = token('value','(?<=:).+?(?=,(?![^{]*\\})".+?(?=")|$)')

## separator (,) must be outside of nested json object or list
separator = token('separator','(?<=(,(?![^{\\[]*[\\}\\]])))')

## closing bracket can be } or ] at end of object 
closing_bracket = token('closing_bracket','}$|//]$')

# full list of tokens as name, pattern dictionary 
tokens = [vars(opening_bracket), vars(colon), vars(separator), vars(key), vars(value), vars(closing_bracket)]

# checks of json file extension is a valid json file extension
def valid_json_file(arg):
    if len(arg) > 5:
        start = len(arg)-5
        end = len(arg)

        if arg[start:end] == '.json':
            return 0
    return 1 

# removes all whitespace from json to evaluate
def remove_whitespace(string):
    return re.sub('\\s+(?=(?:[^"]*"[^"]*")*[^"]*$)','', string)

# reads json file and checks if file is valid json file 
def read_json(arg):
    # return code for valid json file extension
    valid_json_file_return_code = valid_json_file(arg)

    if valid_json_file_return_code == 1:
        sys.exit("Error: File input is not a valid JSON file. Return code: " + str(valid_json_file_return_code))
    else:
        print("Valid JSON file. Return code: " + str(valid_json_file_return_code))

    # read json file and remove whitespace 
    f = open(arg, 'r')
    json_string = remove_whitespace(f.read())
    f.close()

    # if all checks pass, return json in string format
    return json_string 

# for lexer to interpret type of value token 
def check_type(string):

    # if string is digits, then numeric 
    if string.isdigit():
        value_type = 'numeric'
    
    # if string is a true or false value, then boolean 
    elif string.lower() in ('true','false'):
        value_type = 'boolean'

    # if length of string >= 2 and has {} brackets, then object 
    elif len(string) >= 2 and string[0] == '{' and string[len(string)-1] == '}':
        value_type = 'object'

    # if length of string >=2 and has [], then list
    elif len(string) >= 2 and string[0] == '[' and string[len(string)-1] == ']':
        value_type = 'list'

    # if null, then python type should be none 
    elif string.lower() == 'null': 
        value_type = 'none'

    # after aforementioned checks, if none left, then string 
    else:
        value_type = 'string'

    return value_type 

# create lexer class instantiated with tokens and string json output
## tokenize function creates a list with dictionary for each token containing value of token (string), token type, token pattern, value type (if token is value, otherwise blank), token start in string and token end in string (important for ordering)
class lexer:
    def __init__(self, tokens, json_input):
        self.tokens = tokens 
        self.json_input = json_input 
    
    def tokenize(self):
        tokenized_output = []
        index = 0
        value_type = ''
        bracket_pattern = ('|').join([token['pattern'] for token in tokens if token['name'] in ('opening_bracket','closing_bracket')])

        for token in tokens:  
            # start with brackets 
            if token['name'] in ('opening_bracket','closing_bracket'):
                match =  re.finditer(token['pattern'],self.json_input)
            # remove brackets for evaluation so that nested json objects and lists can be properly interpreted
            else:
                eval_string = re.sub(bracket_pattern,'',self.json_input)
                match = re.finditer(token['pattern'],  eval_string)
            for item in match:
                start, end = item.span()
                value = item.group()
                # add one to start and end to adjust for opening bracket not included in eval 
                if token['name'] not in ('opening_bracket','closing_bracket'):
                    start += 1
                    end += 1 

                if token['name'] == 'value':
                    value_type = check_type(value)
                # append result to tokenized result
                tokenized_result = {
                                    'string_value': item.group(),
                                    'token_type': tokens[index]['name'],
                                    'token_pattern': tokens[index]['pattern'],
                                    'value_type': value_type,
                                    'position_start': start,
                                    'position_end': end
                                    }

                tokenized_output.append(tokenized_result)
            # index += 1 for every token in tokens 
            index += 1

        # bubble sort to arrange tokens in original order by position start         
        for i in range(len(tokenized_output)): 
            for j in range(len(tokenized_output) - i - 1):
                if tokenized_output[j + 1]['position_start'] < tokenized_output[j]['position_start']:
                    temp = tokenized_output[j + 1]
                    tokenized_output[j + 1] = tokenized_output[j]
                    tokenized_output[j] = temp

        # tokenize returns a list of every token in the json string          
        return tokenized_output

# checks if the order of opening bracket, closing bracket, key, colon, value, separator is in a valid JSON format. Otherwise a parse error will occur when parser is instantiated and used            
def parse_error(tokenized_output):
    for i in range(len(tokenized_output)):
        if tokenized_output[0]['token_type'] == 'opening_bracket' and tokenized_output[len(tokenized_output) - 1]['token_type'] == 'closing_bracket':
            return 0 

        if tokenized_output[i]['token_type'] == 'key':
            if tokenized_output[i - 1]['token_type'] in ('opening_bracket','separator') and tokenized_output[i + 1]['token_type'] == 'colon':
                return 0
            
            if tokenized_output[i]['token_type'] == 'value':
                if tokenized_output[i - 1]['token_type'] == 'colon' and tokenized_output[i + 1]['token_type'] in ('closing_bracket','separator'):
                    return 0
    return 1
    
# parse string to actual value type   
def parse_string(value, value_type):
    
    # if value is string, put double quotes around it 
    if value_type == 'string':
        output = re.sub('^"|"$','', value)
    
    # if value is numeric, try integer, if value error occurs, try float 
    elif value_type == 'numeric':
        try:
            output = int(value)
        except ValueError:
            output = float(value)

    # if value is true or false, turn to boolean 
    elif value_type == 'boolean':
        if value.lower() == 'true':
            output = True 
        else:
            output = False 
    
    # if value is object (nested JSON/dictionary)
    elif value_type =='object':
        if len(value) > 2:
            tokenized_string = lexer(tokens, remove_whitespace(value)).tokenize()
            dictionary = parser(tokenized_string).value_parse()
            
        # if object is empty, return empty dictionary object 
        else:
            dictionary = {}
        
        output = dictionary 

    # if value is list 
    elif value_type == 'list':
        
        # remove brackets
        string = value.strip("[]")

        # split string on comma
        split_string = string.split(',')

        # create list with actual value types
        new_list = []
        
        # if list has items 
        if len(split_string) > 0:
            
            # check type and use function recursively for list 
            for item in split_string:
                value = item 
                value_type = check_type(item)
                new_list.append(parse_string(value, value_type))
            
            
        output = new_list

    # remaining type is None (null)
    else:
       output = None

    return output

# create parser class instantiated on tokenized output from lexer 
class parser:
    def __init__(self, tokenized_output):
        self.tokenized_output = tokenized_output
   
   # parses json values into a python dictoinary format 
    def value_parse(self):
        # use parse error to check if json order of opening bracket, key, colon, value, comma separator (if more than one key, value) and closing bracket is correct
        error_code = parse_error(self.tokenized_output)

        if error_code == 1:
            sys.exit("Parse error: incorrect JSON format structure. Return code: " + str(error_code))
        else:
           print("Valid JSON object. Return code: "+ str(error_code))
        
        # for every value, get the value with correct value type 
        if len(self.tokenized_output) == 2:
            dictionary = {}
        else:
            for item in self.tokenized_output:
                if item['token_type'] == 'value':
                # input string value and value type to parse string function 
                    value = item['string_value']
                    value_type = item['value_type']
                    item['value'] = parse_string(value, value_type)
        
        # get keys and corresponding values and use zip to map key to value 
        keys = [item['string_value'] for item in self.tokenized_output if item['token_type'] == 'key']

        values = [item['value'] for item in self.tokenized_output if item['token_type'] == 'value']

        dictionary = dict(zip(keys,values))
        
        #returns json as python dictionary 
        return dictionary 

class JSON:
    def __init__(self,json_input):
        self.json_input = json_input 
        # if json_input is a json file
        if "." in json_input:
            self.json_read = read_json(self.json_input)
        # else if json_input is directly stored in python string, remove whitespace 
        else:
            self.json_read = remove_whitespace(self.json_input)

        self.tokenized_string = lexer(tokens, self.json_read).tokenize()
        self.parsed_json = parser(self.tokenized_string).value_parse()

    def tokens(self):
        return self.tokenized_string
    
    def parse_json(self):
        return self.parsed_json

# if script will be called directly, then use command line argument for json file    
if __name__ == "__main__":
    
    input = sys.argv[1]

    json_object = JSON(input)

    # prints tokens
    print(json_object.tokens())

    # print parsed JSON
    print(json_object.parse_json())

    


  
    
    