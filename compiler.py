#Georgios Balanos 5054
#Evangelos Chasanis 5058

import os
import pdb
import sys

# Lex #

ERROR = -1                      # Error

EOF_TOKEN = -2                  # eof

ADD_TOKEN = 25                   # +
MINUS_TOKEN = 26                 # -
MULT_TOKEN = 27                  # *
DIVISION_TOKEN = 28              # //
MODULO_TOKEN = 29                # %
LESS_TOKEN = 30                  # <
LESS_EQ_TOKEN = 31               # <=
GREATER_TOKEN = 32               # >
GREATER_EQ_TOKEN = 33            # >=
EQUAL_TOKEN = 34                 # = 
EQUAL_EQUAL_TOKEN = 35          # == 
EXCLAMATION_EQUAL_TOKEN = 36    # !=
COMMA_TOKEN = 37                # ,
COLON_TOKEN = 38                # : 
LEFT_PAR_TOKEN = 39             # (
RIGHT_PAR_TOKEN = 40            # )
LEFT_CURLY_TOKEN = 41           # #{
RIGHT_CURLY_TOKEN = 42          # #}
COMMENT_TOKEN = 43              # ##
IDENTIFIER_TOKEN = 44           # identifier
INTEGER_TOKEN = 45              # integer
TYPE_TOKEN = 46                 # type

#Preserved Keywords:

MAIN_KW = 47                    # main
DEF_KW = 48                     # def
HASH_DEF_KW = 49                # #def
HASH_INT_KW = 50                # #int
GLOBAL_KW = 51                  # global
IF_KW = 52                      # if
ELIF_KW = 53                    # elif
ELSE_KW = 54                    # else
WHILE_KW = 55                   # while
PRINT_KW = 56                   # print
RETURN_KW = 57                  # return
INPUT_KW = 58                   # input
INT_KW = 59                     # int
AND_KW = 60                     # and
OR_KW = 61                      # or
NOT_KW = 62                     # not

file = open('table.sym', 'w+')
assembly_file = open("final.asm","w+")
file_int = open('quads.int','w+')

global current_globals
current_globals = []

global par_length
par_length = []

global framelength
framelength = []

global nesting_level
nesting_level = 0

global record_arguments
record_arguments = []

global scopes
scopes = []

global made_main
made_main = False

global main_framelength
main_framelength = 12

global is_global
is_global = False

global is_declaration
is_declaration = False

newLine = 1 #Used to index the current "position" on the file.

temp_counter = 0

quad_counter = 0
quad_list = []

#class Token is used to produce token objects which contains it's family, current_string and line number
class Token:
    family = ""
    current_string = ""
    line_num = 0

    def __init__(self,family,current_string,line_num):
        self.family = family
        self.current_string = current_string
        self.line_num = line_num
    
    def __str__(self):
        return f"Family: {self.family}, String: {self.current_string}, Line Number: {self.line_num}"

class Quad:
    def __init__(self, quad_number, operation, x, y, z):
        self.quad = []

        self.quad.append(quad_number)
        self.quad.append(operation)
        self.quad.append(x)
        self.quad.append(y)
        self.quad.append(z)
    
    def __str__(self):
        string = "(Quad number: " + str(self.quad[0]) + " ,op: " + str(self.quad[1]) + " ,first operand: "+ str(self.quad[2]) +" ,second operand: "+ str(self.quad[3]) +" ,result: "+ str(self.quad[4]) +")"
        return string

class Entity:
    def __init__(self,name):
        self.name = name

    def __str__(self):
        return self.name

class Variable(Entity):
    def __init__(self,name,offset):
        super().__init__(name)
        self.offset = offset

    def __str__(self):
        return f"Name: {self.name}, Offset: {self.offset}, Instance: Variable"

class Function(Entity):
    def __init__(self, name, type, start_quad, arguments, frame_length):
        super().__init__(name)
        self.type = type 
        self.start_quad = start_quad
        self.arguments = arguments
        self.frame_length = frame_length

    def __str__(self):
        args_str = '\n'.join(self.arguments)  # Joining arguments with newline character
        return f"Name: {self.name}, Type: {self.type}, Start Quad: {self.start_quad},\nArguments:\n{args_str}\nFrame Length: {self.frame_length}, Instance: Function"

class Constant(Entity):
    def __init__(self, name, value):
        super().__init__(name)
        self.value = value

    def __str__(self):
        return f"Name: {self.name}, Value: {self.value}, Instance: Constant"
    
class Parameter(Entity):
    def __init__(self, name, par_mode, offset):
        super().__init__(name)
        self.par_mode = par_mode
        self.offset = offset

    def __str__(self):
        return f"Name: {self.name}, Parameter Mode: {self.par_mode}, Offset: {self.offset}, Instance: Parameter"

class TempVariable(Entity):
    def __init__(self, name, offset):
        super().__init__(name)
        self.offset = offset
    
    def __str__(self):
        return f"Name: {self.name}, Offset: {self.offset}, Instance: TempVariable"
    
class Scope:
    def __init__(self, entities, nesting_level):
        self.entities = entities
        self.nesting_level = nesting_level

    def __str__(self):
        entities_str = ', '.join(map(str, self.entities))
        return f"Nesting Level: {self.nesting_level}\nEntities:\n{entities_str}\n"

class Argument:
    def __init__(self, par_mode):
        self.par_mode = par_mode

    def __str__(self):
        return f"\tArgument Mode: {self.par_mode}, Instance: Argument"

def add_scope(scope):
    global nesting_level
    scopes.append(scope)
    nesting_level += 1

def delete_scope():
    global nesting_level
    global current_globals

    current_scope = scopes.pop()
    write_scope_to_file(current_scope)
    nesting_level -= 1
    current_globals = []

def calculate_offset():
    global scopes

    if(scopes and scopes[-1].entities):
        for entity in reversed(scopes[-1].entities):
            if hasattr(entity, 'offset'):
                return entity.offset
        else:
            return 8
    else:
        return 8

def add_entity(entity):
    global scopes
    global framelength
    global main_framelength
    global made_main

    if(scopes and len(scopes[-1].entities) >= 0):
        scopes[-1].entities.append(entity)
        if not isinstance(entity, Function) and not isinstance(entity, Constant):  # Check if the entity is not a function
            if len(framelength) > 0:
                framelength[-1] += 4
            else:
                framelength.append(4)
        else:
            pass

    if(len(scopes) == 1 ):
        main_framelength += 4
    

def write_quads():
    for quad in quad_list:
        file_int.write(str(quad) + '\n')


def write_scope_to_file(scope):
    global current_globals

    current_nesting = scope.nesting_level
    current_entinies = scope.entities
    file.write("Nesting level: "+str(current_nesting) + '\nEntities:\n')

    for g in current_globals:
        file.write("Name of global: "+g+"\n")

    for e in current_entinies:
        file.write(str(e) + '\n')

    file.write("\n")

def search_by_name(name):
    global scopes

    for scope in reversed(scopes):  
        for entity in scope.entities:
            if entity.name == name:
                #print("Found: ",entity)
                return entity

    print("\033[91mError: Could not find entity " + name + "\033[0m")
    exit(0) 

try:
    if(len(sys.argv) != 2):
        print("\033[3m\033[91mLex:Error state encountered. Usage: python compiler.py (file_name.cpy)\033[0m")
        exit(0)

    inputFile = open(sys.argv[1], "r+") 

    inputFile.seek(0)
except Exception as e:
    print("An error occurred:", e)
    exit(0)


#Based on the current_token (current_string) the keyword (final state) is decided.
def check_keyword(current_token,state):
    if current_token == 'main':
        state = MAIN_KW
    elif current_token == 'def':
        state = DEF_KW
    elif current_token == '#def':
        state = HASH_DEF_KW
    elif current_token == '#int':
        state = HASH_INT_KW
    elif current_token == 'global':
        state = GLOBAL_KW
    elif current_token == 'if':
        state = IF_KW
    elif current_token == 'elif':
        state = ELIF_KW
    elif current_token == 'else':
        state = ELSE_KW
    elif current_token == 'while':
        state = WHILE_KW
    elif current_token == 'print':
        state = PRINT_KW
    elif current_token == 'return':
        state = RETURN_KW
    elif current_token == 'input':
        state = INPUT_KW
    elif current_token == 'int':
        state = INT_KW
    elif current_token == 'and':
        state = AND_KW
    elif current_token == 'or':
        state = OR_KW
    elif current_token == 'not':
        state = NOT_KW

    return state

#Used to find the token family based on the token's state.
def find_family(state):
    if state == IDENTIFIER_TOKEN:
        return 'identifier_family'
    elif state == INTEGER_TOKEN:
        return 'integer_family'
    elif state >= 47: #preserved keywords have a value greater than 47.
        return 'keyword_family' 
    elif state == ADD_TOKEN or state == MINUS_TOKEN:
        return 'addOper_family'
    elif state == MULT_TOKEN or state == DIVISION_TOKEN or state == MODULO_TOKEN:
        return 'mulOper_family'
    elif state == EQUAL_TOKEN:
        return 'assignment_family'
    elif state >= 30 and state <= 36:  #relOpers have a value between 30 and 36
        return 'relOper_family'
    elif state == COMMA_TOKEN or state == COLON_TOKEN:
        return 'delimiter_family'
    else:
        return 'group_family'
    
#Used to check the next character while reading the input file.
def peek(file, num_chars=1):
    current_position = file.tell()
    peeked_data = file.read(num_chars)
    file.seek(current_position)
    return peeked_data

#Based on the transition_table and the current input character the next state is evaluated.
def find_state(char,transition_table):
    state = 0
    if char.isspace():
        state = transition_table[state][0]
        #print("Whitespace encountered1")
    elif char.isalpha():
        #print("Alphabetic character encountered1")
        state = transition_table[state][1]
    elif char.isdigit():
        #print("Digit encountered1")
        state = transition_table[state][2]
    elif char == '+':
        #print("Plus sign encountered1")
        state = transition_table[state][3]
    elif char == '-':
        #print("Minus sign encountered1")
        state = transition_table[state][4]
    elif char == '*':
        #print("Multiplication symbol encountered1")
        state = transition_table[state][5]
    elif char == '/':
        #print("Division symbol encountered1")
        state = transition_table[state][6]
    elif char == '%':
        #print("Modulo symbol encountered1")
        state = transition_table[state][7]
    elif char == '<':
        #print("Less than symbol encountered1")
        state = transition_table[state][8]
    elif char == '>':
        #print("Greater than symbol encountered1")
        state = transition_table[state][9]
    elif char == '=':
        #print("Equal sign encountered1")
        state = transition_table[state][10]
    elif char == '!':
        #print("Exclamation mark encountered1")
        state = transition_table[state][11]
    elif char == ',':
        #print("Comma encountered1")
        state = transition_table[state][12]
    elif char == ':':
        #print("Colon encountered1")
        state = transition_table[state][13]
    elif char == '(':
        #print("Left parenthesis encountered1")
        state = transition_table[state][14]
    elif char == ')':
        #print("Right parenthesis encountered1")
        state = transition_table[state][15]
    elif char == '#':
        #print("Hash symbol encountered1")
        state = transition_table[state][16]
    elif not char:
        #print("EOF encountered1")
        state = transition_table[state][17]
        #print(state)
    elif char == '{':
        #print("Left curly brace encountered1")
        state = transition_table[state][18]
    elif char == '}':
        #print("Right curly brace encountered1")
        state = transition_table[state][19]
    else:
        state = ERROR
        print(f"\033[3m\033[91mLex:{newLine}:Invalid character encountered1.\033[0m")
        exit(0)
    return state

def lex():

    #Inputs(transition_table columns): "Space" , "Alpha" , "Digit" , "+" , "-" , "*" , "/" , "%" , "<" , ">" , "=" , "!" , "," , ":" , "(" , ")" , "#" , "EOF" , "{", "}"

    transition_table = [
        [0, 1, 2, ADD_TOKEN, MINUS_TOKEN, MULT_TOKEN, 3, MODULO_TOKEN,4, 5, 6, 7, COMMA_TOKEN, COLON_TOKEN, LEFT_PAR_TOKEN, RIGHT_PAR_TOKEN, 8, EOF_TOKEN, ERROR, ERROR], #State 0

        [IDENTIFIER_TOKEN, 1, 1, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN , IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, 
         IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN, IDENTIFIER_TOKEN],

        [INTEGER_TOKEN, ERROR, 2, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, 
         INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN, INTEGER_TOKEN],

        [ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, DIVISION_TOKEN, ERROR, 
         ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR],

        [LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, 
         LESS_TOKEN, LESS_EQ_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN, LESS_TOKEN],

        [GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, 
         GREATER_TOKEN, GREATER_EQ_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN, GREATER_TOKEN],

        [EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_EQUAL_TOKEN, 
         EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN, EQUAL_TOKEN],

        [ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, 
         ERROR, ERROR, EXCLAMATION_EQUAL_TOKEN, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR],

        [ERROR, 9, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, ERROR, 10, ERROR, LEFT_CURLY_TOKEN, RIGHT_CURLY_TOKEN],

        [TYPE_TOKEN, 9, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, 
         TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN, TYPE_TOKEN],

        [10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,11,ERROR,10,10],

        [10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,0,ERROR,10,10]
    ]

    global newLine
    
    state = 0 
    try:
        current_token = "" 
        char = inputFile.read(1)
        if char == '\n':
            newLine += 1

        while char.isspace():   #Skips white spaces.
            char = inputFile.read(1)

        current_token += char

        state = find_state(char,transition_table)

        #State value greater than 25 leads to final state.
        while state < 25:
            
            if(state == ERROR):
                #print(f"\033[3m\033[91mLex:{newLine}:Error state encountered.\033[0m")
                return Token('EOF','',newLine)

            next_char = peek(inputFile)

            if next_char.isspace():
                state = transition_table[state][0]
                #print("Whitespace encountered")
            elif next_char.isalpha():
                #print("Alphabetic character encountered")
                state = transition_table[state][1]
            elif next_char.isdigit():
                #print("Digit encountered")
                state = transition_table[state][2]
            elif next_char == '+':
                #print("Plus sign encountered")
                state = transition_table[state][3]
            elif next_char == '-':
                #print("Minus sign encountered")
                state = transition_table[state][4]
            elif next_char == '*':
                #print("Multiplication symbol encountered")
                state = transition_table[state][5]
            elif next_char == '/':  #   "//" found and reached final state.
                if char == '/':
                    #print("Division symbol encountered")
                    state = transition_table[state][6]
                    char = inputFile.read(1)
                    current_token += char
                    break
                #print("Division symbol encountered")
                state = transition_table[state][6]
            elif next_char == '%':
                #print("Modulo symbol encountered")
                state = transition_table[state][7]
            elif next_char == '<':
                #print("Less than symbol encountered")
                state = transition_table[state][8]
            elif next_char == '>':
                #print("Greater than symbol encountered")
                state = transition_table[state][9]
            elif next_char == '=':  #   ">=" or "<=" or "==" or "!=" found and reached final state.
                if char == '<' or char == '>' or char == '=' or char == '!':
                    #print("Equal sign encountered")
                    state = transition_table[state][10]
                    char = inputFile.read(1)
                    current_token += char
                    break
                #print("Equal sign encountered")
                state = transition_table[state][10]
            elif next_char == '!':
                #print("Exclamation mark encountered")
                state = transition_table[state][11]
            elif next_char == ',':
                #print("Comma encountered")
                state = transition_table[state][12]
            elif next_char == ':':
                #print("Colon encountered")
                state = transition_table[state][13]
            elif next_char == '(':
                #print("Left parenthesis encountered")
                state = transition_table[state][14]
            elif next_char == ')':
                #print("Right parenthesis encountered")
                state = transition_table[state][15]
            elif next_char == '#':
                #print("Hash symbol encountered")
                state = transition_table[state][16]
            elif not next_char:
                #print("EOF encountered")
                state = transition_table[state][17]
                #print(current_token)
            elif next_char == '{':  #   "#{" found and reached final state.
                if char == '#':
                    #print("Left curly brace encountered")
                    state = transition_table[state][18]
                    char = inputFile.read(1)
                    current_token += char
                    break
                #print("Left curly brace encountered")
                state = transition_table[state][18]
            elif next_char == '}':  #   "#}" found and reached final state.
                if char == '#':
                    #print("Right curly brace encountered")
                    state = transition_table[state][19]
                    char = inputFile.read(1)
                    current_token += char
                    break
                #print("Right curly brace encountered")
                state = transition_table[state][19]
            else:
                state = ERROR
                print(f"\033[3m\033[91mLex:{newLine}:Invalid character encountered.\033[0m")
                exit(0)
            
            #Already found final state and avoid consuming the next character from input file.
            if state < 25:
                char = inputFile.read(1)
                current_token += char


            #Handles comments.
            if(current_token == '##'):
                temp_token = ''
                inComment = True
                while inComment:

                    char = inputFile.read(1)
                    if char == '\n':
                        newLine += 1
                    temp_token += char

                    if(len(temp_token) >= 3 and temp_token[-2:] == '##'):   #Check for "comment closure".
                        char = inputFile.read(1)
                        while char.isspace():
                            if char == '\n':
                                newLine += 1
                            char = inputFile.read(1)
                        
                        state = find_state(char,transition_table)
                        current_token = char
                        inComment = False             
                    elif not char:
                        print(f"\033[3m\033[91mError: '##' delimiter found on line {newLine}.\nExpected '##' delimiter before end of file.\033[0m")
                        exit(0)

        
        #Ensure that the current_token(current_string) doesn't have white spaces at the start or the end, before create the token object.
        current_token = current_token.strip()

        if state == IDENTIFIER_TOKEN or state == TYPE_TOKEN:
            state = check_keyword(current_token,state)
        
        #If state is still "TYPE_TOKEN" the given type token is neither "#int" or "#def".
        if state == TYPE_TOKEN:
            print(f"\033[3m\033[91mFound invalid type token {current_token} in line {newLine}. Try valid tokens : 'int' and 'def'.\033[0m")
            exit(0)

        #Keep the first 30 characters of the current_token.
        if len(current_token) >= 30:
            current_token[:30]
        
        family = find_family(state)

        #If the current_token is an integer, check if it is in the given range [-32767,32767].
        if family == 'integer_family':
            if int(current_token) > 32767 or int(current_token) < -32767:
                print(f"\033[3m\033[91mNumbers should be between -32767 and 32767.\033[0m")
                exit(0)

        return Token(family,current_token,newLine)

    except Exception as e:
        print("An error occurred:", e)

# Syntax Analyzer #

def syntax_analyzer():
    global token 
    token = lex()
    start_rule()
    print("\033[3m\033[92mCompilation successfully completed\033[0m")

def start_rule():
    global token 
    global record_arguments
    global quad_counter
    global quad_list
    global scopes
    global main_framelength
    global framelength
    global temp_counter

    if token.current_string == '#int':
        declarations()  
    
    while token.current_string != '#def' and token.current_string != '':
        token = lex()

    call_main_part()
    inputFile.seek(0)

    token = lex()

    record_arguments.append([])

    if token.current_string == '#int':
        declarations()

    quad_counter = 0
    temp_counter = 0
    quad_list = []
    def_main_part()
    
    framelength = [main_framelength]

    temp_scopes = scopes[:]
    temp_main_framelength = framelength[0]

    delete_scope()
    scopes = temp_scopes
    call_main_part()
    main_framelength = temp_main_framelength
    make_final_code()
       
    
def def_main_part():    #Check/read file's functions(starting with "def").
    global token

    def_function()
    while token.current_string == 'def':
        def_function()

def call_main_part():   #Check/read the body of main function(starting with "#def").
    global token
    global nesting_level
    global scopes
    global framelength
    global record_arguments
    global par_length
    global made_main
    

    if token.current_string == '#def':
        token = lex()
        if token.current_string == 'main':
            token = lex()

            entinties = []
            current_scope = Scope(entinties,nesting_level)
            

            if not made_main:
                add_scope(current_scope)
                made_main = True
            else:
                file.write("Main framelength: " + str(main_framelength))
            
            declarations()
            globals_()
            genquad("begin_block","main","_","_")
            code_blocks()
            genquad("halt","main","_","_")
            genquad("end_block","main","_","_")
        else:
            print("\033[3;31mDid not find main function\033[0m")
            exit(0)
    else:
        print("\033[3;31mDid not find #def. Must be used to declare main.\033[0m")
        exit(0)
    
        
def def_function():
    global token
    global nesting_level
    global scopes
    global par_length
    global framelength
    global record_arguments
    

    if token.current_string == 'def':
        par_length.append(0)
        framelength.append(12)
        record_arguments.append([])

        token = lex()
        function_name = token.current_string

        print("\nStart of function: ",function_name)
        entinties = []
        current_scope = Scope(entinties,nesting_level)
        add_scope(current_scope)

        if token.family == 'identifier_family':
            token = lex()
            if token.current_string == '(':
                token = lex()
                id_list()   #Consumes 1 token
                temp_record_args = record_arguments[-1][:]
                record_arguments.pop()
                record_arguments.append([])

                if token.current_string == ')':
                    token = lex()
                    if token.current_string == ':':
                        token = lex()
                        if token.current_string == '#{':

                            temp_args = par_length[-1]

                            token = lex()
                            declarations()  #Consumes 1 token

                            def_function()  #Starts at "def" and doesn't consume any token.

                            globals_()  #Consumes 1 token

                            genquad("begin_block",function_name,"_","_")

                            start_quad = quad_counter-1

                            code_blocks()  #Consumes 1 token
                            genquad("end_block",function_name,"_","_")

                            print("\nEnd of function: ",function_name)

                            f_type = 1
                            if(temp_args == 0):
                                f_type = 0

                            function_entity = Function(function_name,f_type,start_quad,temp_record_args,framelength[-1])
                            add_entity(function_entity)

                            par_length.pop()
                            framelength.pop()
                            record_arguments.pop()
                            f_type = 1

                            make_final_code()
                            delete_scope()
                            add_entity(function_entity)

                            if token.current_string == '#}':
                                token = lex()
                            else:
                                print("\033[3;31m\033[4mDid not find token '#}'\033[0m")
                                exit(0)
                        else: 
                            print("\033[3;31m\033[4mDid not find token '#{'\033[0m")
                            exit(0)
                    else:
                        print("\033[3;31m\033[4mDid not find token ':'\033[0m")
                        exit(0)
                else:
                    print("\033[3;31m\033[4mDid not find token ')'\033[0m")
                    exit(0)
            else:
                print("\033[3;31m\033[4mDid not find token '('\033[0m")
                exit(0)
        else:
            print("\033[3;31m\033[4mDid not find token 'identifier'\033[0m")
            exit(0)
    else:
        return 0
    
def code_blocks():
    global token

    
    code_block()
    
    while token.current_string == 'while' or token.current_string == 'return' or token.current_string == 'print' or token.family == 'identifier_family' or token.current_string == 'if':
        code_block()
    

def code_block():
    global token

    if token.current_string == 'return' or token.current_string == 'print' or token.family == 'identifier_family':
        simple_code_block()
    elif token.current_string == 'while' or token.current_string == 'if':
        structured_code_block()
    else:
        print(f"\033[3;31mSyntax:{token.line_num}:Unknown Token.\033[0m")
        exit(0)

def simple_code_block():
    global token 
    
    if token.family == 'identifier_family':
        assignment_code_block()
    elif token.current_string == 'print':
        print_code_block()
    elif token.current_string == 'return':
        return_code_block()
    else:
        print(f"\033[3;31mSyntax:{token.line_num}:Wrong simple code block structure.\033[0m")
        exit(0)

def assignment_code_block():
    global token
    
    ident = token.current_string

    token = lex()
    if token.current_string == '=':
        token = lex()
        if token.current_string != 'int':
            e_place = expression()
            genquad('=',e_place,'_',ident)
        elif token.current_string == 'int':
            genquad('inp',ident,'_','_')
            token = lex()
            if token.current_string == '(':
                token = lex()
                if token.current_string == 'input':
                    token = lex()
                    if token.current_string == '(':
                        token = lex()
                        if token.current_string == ')':
                            token = lex()
                            if token.current_string == ')':
                                token = lex()
                            else:
                                print(f"\033[3;31mSyntax:{token.line_num}:Expected ')'\033[0m")
                                exit(0)
                        else:
                            print(f"\033[3;31mSyntax:{token.line_num}:Expected ')'\033[0m")
                            exit(0)
                    else:
                        print(f"\033[3;31mSyntax:{token.line_num}:Expected '('\033[0m")
                        exit(0)
                else:
                    print(f"\033[3;31mSyntax:{token.line_num}:Expected 'input'\033[0m")
                    exit(0)
            else:
                print(f"\033[3;31mSyntax:{token.line_num}:Expected '('\033[0m")
                exit(0)
        else:
            print(f"\033[3;31mSyntax:{token.line_num}:Expected 'int'\033[0m")
            exit(0)
    else:
        print(f"\033[3;31mSyntax:{token.line_num}:Expected '='\033[0m")
        exit(0)

def expression():   #Consumes 1 token
    global token

    sign = optional_sign()
    is_signed = 1

    t1_place = term()

    while token.family == 'addOper_family':
        is_signed = 0

        if token.family == 'addOper_family':
            sign = token.current_string
            token = lex()

        t2_place = term()

        w = newtemp()
        genquad(sign,t1_place,t2_place,w)
        t1_place = w

    if is_signed == 1:
        return sign+t1_place
    return t1_place


def optional_sign():
    global token

    sign = token.current_string

    if token.family == 'addOper_family':
        token = lex()
        return sign
    return ""

def term():
    global token

    f1_place = factor()

    while token.family == 'mulOper_family':
        
        mul_op = token.current_string

        if token.family == 'mulOper_family':
            token = lex()

        f2_place = factor()
        
        w = newtemp()
        
        genquad(mul_op,f1_place,f2_place,w)
        f1_place = w
    
    return f1_place

def factor():
    global token

    f_place = ""

    if token.family == 'integer_family':

        f_place = token.current_string

        token = lex()

    elif token.current_string == '(':

        token = lex()

        f_place = expression()

        if token.current_string == ')':

            token = lex()

        else:

            print(f"\033[3;31mSyntax:{token.line_num}:Expected ')'\033[0m")

            exit(0)

    elif token.family == 'identifier_family': # fib(x+1)
        factor_string = token.current_string

        token = lex()

        f_place = idtail(factor_string)

    else:

        print(f"\033[3;31mSyntax:{token.line_num}:Expected factor\033[0m")

        exit(0)

    return f_place

def idtail(factor_string):
    global token

    if token.current_string == '(':
        token = lex()
        actual_param_list()

        w = newtemp()
        genquad('par',w,'ret','_')
        genquad('call',factor_string,'_','_')

        if token.current_string == ')':

            token = lex()

            return w

        else:

            print(f"\033[3;31mSyntax:{token.line_num}:Expected ')'\033[0m")
            exit(0)
    return factor_string
    

def actual_param_list(): #To expression 8a 3ekinaei apo to prwto token poy toy antistoixei.
    global token       

    e_place = expression()
    genquad('par',e_place,'cv','_')

    while token.current_string == ',':
        token = lex()

        e_place = expression()
        genquad('par',e_place,'cv','_')
       

def print_code_block():
    global token 

    token = lex()

    if token.current_string == '(':
        token = lex()

        e_place = expression()
        genquad('out',e_place,'_','_')

        if token.current_string == ')':
            token = lex()
        else:
            print(f"\033[3;31mSyntax:{token.line_num}:Expected ')'\033[0m")
            exit(0)

def return_code_block():
    global token
    token = lex()

    if token.current_string == '#}': # In case there is a "return" without any argument.
        return 
    
    e_place = expression()
    genquad('retv',e_place,'_','_')

def structured_code_block():
    global token 
    
    if token.current_string == 'if':
        if_code_block()
    elif token.current_string == 'while':
        while_code_block()
    else:
        print(f"\033[3;31mSyntax:{token.line_num}:Expected 'while' or 'if' token.\033[0m")
        exit(0)

#Recursion was used to check if there was an "elif" or "else".
def if_code_block():
    global token

    ifList = []
    b_place = []

    if token.current_string == 'if' or token.current_string == 'elif':
        token = lex()
        b_place = condition()
        if token.current_string == ':':
            token = lex()

            backpatch(b_place[0],nextquad())

            if token.current_string == '#{': #Statement_or_block
                token = lex()
                code_blocks()   #Consumes 1 token
                if token.current_string == '#}':
                    token = lex()

                    ifList = makelist(nextquad())
                    genquad('jump','_','_','_')
                    backpatch(b_place[1],nextquad())

                    if_code_block()
                else:
                    print("\033[3;31mSyntax:{}:Expected '#}'\033[0m {}".format(token.line_num, format.string))
                    exit(0)
            else:
                code_block()    #Consumes 1 token

                ifList = makelist(nextquad())
                genquad('jump','_','_','_')
                backpatch(b_place[1],nextquad())

                if_code_block()
        else:
            print(f"\033[3;31mSyntax:{token.line_num}:Expected ':'\033[0m")
            exit(0)
    elif token.current_string == 'else':
        token = lex()
        if token.current_string == ':':
            token = lex()
            if token.current_string == '#{':
                token = lex()
                code_blocks()   #Consumes 1 token
                if token.current_string == '#}':
                    token = lex()
                    if_code_block()
                else:
                    print("\033[3;31mSyntax:{}:Expected '#}'\033[0m {}".format(token.line_num, format.string))
                    exit(0)
            else:
                code_block()    #Consumes 1 token
                if_code_block()   
        else:
            print(f"\033[3;31mSyntax:{token.line_num}:Expected ':'\033[0m")
            exit(0)
        
    backpatch(ifList,nextquad())
    return b_place

def condition():
    global token

    b1_place = bool_term()

    c_true = b1_place[0]
    c_false = b1_place[1]

    while token.current_string == 'or':
        if token.current_string == 'or':
            token = lex()
            backpatch(c_false,nextquad())
    
        b2_place = bool_term()
        c_true = merge(c_true, b2_place[0])
        c_false = b2_place[1]
    
    return c_true,c_false

def bool_term():
    global token

    bf1_place = bool_factor()

    b_true = bf1_place[0]
    b_false = bf1_place[1]

    while token.current_string == 'and':
        if token.current_string == 'and':
            token = lex()
            backpatch(b_true,nextquad())

        bf2_place = bool_factor()
        b_false = merge(b_false,bf2_place[1])   
        b_true = bf2_place[0]
    
    return b_true,b_false


def bool_factor():
    global token

    if token.current_string == 'not':
        e1_place = expression()

        if token.family == 'relOper_family':
            rel_op = token.current_string

            token = lex()
            e2_place = expression()

            r_true = makelist(nextquad())
            genquad(rel_op,e1_place,e2_place,'_')
            r_false = makelist(nextquad())
            genquad('jump','_','_','_')

            return r_false, r_true
        else:
            print("\033[3;31mSyntax:{}:Expected expression relOper expression.\033[0m {}".format(token.line_num, format.string))
            exit(0)
    else:
        e1_place = expression()

        if token.family == 'relOper_family':
            rel_op = token.current_string

            token = lex()
            e2_place = expression()

            r_true = makelist(nextquad())
            genquad(rel_op,e1_place,e2_place,'_')
            r_false = makelist(nextquad())
            genquad('jump','_','_','_')

            return r_true, r_false
        else:
            print("\033[3;31mSyntax:{}:Expected expression relOper expression.\033[0m {}".format(token.line_num, format.string))
            exit(0)

def while_code_block():
    global token 

    first_quad = nextquad()

    token = lex()

    b_place = condition()
    
    if token.current_string == ':':
        backpatch(b_place[0],nextquad())

        token = lex()

        if token.current_string == '#{':
            token = lex()
            code_blocks()
            if token.current_string == '#}':
                token = lex()
            else:
                print("\033[3;31mSyntax:{}:Expected '#}'.\033[0m {}".format(token.line_num, format.string))
                exit(0)
        else:
            code_block()
        
        genquad('jump','_','_',first_quad)
        backpatch(b_place[1],nextquad())

        return b_place[0],b_place[1]

    else:
        print("\033[3;31mSyntax:{}:Expected ':'.\033[0m {}".format(token.line_num, format.string))
        exit(0)

def id_list():  #Consumes 1 token
    global token
    global par_length
    global record_arguments
    global scopes

    current_scopes = scopes[:]

    if token.family == 'identifier_family':
        if is_global == False and is_declaration == False:
            par_var = Parameter(token.current_string,"cv",calculate_offset()+4)
            add_entity(par_var)

            if(len(par_length) > 0):
                par_length[-1] += 1
            else:
                par_length.append(0)
                par_length[-1] += 1

            record_arg = Argument("cv")
            if(len(record_arguments) > 0):
                record_arguments[-1].append(record_arg.__str__() + ", name:" + token.current_string)
            else:
                record_arguments[0].append(record_arg.__str__() + ", name:" + token.current_string)


        elif is_global == True:
            #var = Variable(token.current_string,calculate_offset()+4)
            search_by_name(token.current_string)
            current_globals.append(token.current_string)

        else:
            var = Variable(token.current_string,calculate_offset()+4)
            add_entity(var)


        token = lex()
        while token.current_string == ',':
            token = lex()

            if token.family == 'identifier_family':
                if is_global == False and is_declaration == False:
                    par_var = Parameter(token.current_string,"cv",calculate_offset()+4)
                    add_entity(par_var)

                    if(len(par_length) > 0):
                        par_length[-1] += 1
                    else:
                        par_length.append(0)
                        par_length[-1] += 1

                    record_arg = Argument("cv")
                    if(len(record_arguments) > 0):
                        record_arguments[-1].append(record_arg.__str__() + ", name:" + token.current_string)
                    else:
                        record_arguments[0].append(record_arg.__str__() + ", name:" + token.current_string)


                elif is_global == True:
                    #var = Variable(token.current_string,calculate_offset()+4)
                    search_by_name(token.current_string)
                    current_globals.append(token.current_string)
                else:

                    var = Variable(token.current_string,calculate_offset()+4)
                    add_entity(var)

                token = lex()
            else:
                print("Error")
                exit(0)

    scopes = current_scopes[:]

def declarations():
    global token
    global is_declaration

    is_declaration = True
    while token.current_string == "#int":
        declaration_line()
    is_declaration = False

def declaration_line():
    global token
    
    if token.current_string == "#int":
        token = lex()
        id_list()

def globals_():
    global token 
    global is_global
    
    is_global = True
    while token.current_string == 'global':
        globals_line()
    is_global = False

def globals_line():
    global token 
    
    if token.current_string == 'global':
        token = lex()
        id_list()


#Intermediate Code

def nextquad():
    global quad_counter

    return quad_counter

def genquad(op,x,y,z): # Have to make a quad List and append the current quad?
    global quad_counter
    global quad_list

    temp_quad = Quad(nextquad(),op,x,y,z)
    quad_list.append(temp_quad)

    quad_counter += 1

def emptylist():
    label_list = []

    return label_list

def makelist(x):
    x_list = [x]

    return x_list

def merge(list1, list2):
    return list1+list2

def newtemp():
    global temp_counter

    return_string = "T_" + str(temp_counter)
    temp_counter += 1

    temp_var = TempVariable(return_string,calculate_offset()+4)
    add_entity(temp_var)

    return return_string

def backpatch(lst,z):
    global quad_list

    for i in range(len(quad_list)):
        for j in range(len(lst)):
            if lst[j] == quad_list[i].quad[0] and quad_list[i].quad[4] == '_':
                quad_list[i].quad[4] = z
        
    del lst

#Final Code

def search_scope(name):
    global scopes

    scope_counter = len(scopes)-1

    for scope in reversed(scopes):  
        for entity in scope.entities:
            if entity.name == name:
                return (entity,scope_counter)
        scope_counter -= 1

def gnvlcode(name):
    global assembly_file
    global scopes

    assembly_file.write("lw t0,-4(sp)\n")

    search_result = search_scope(name)

    if search_result is not None:
        level_difference = scopes[len(scopes)-1].nesting_level - scopes[search_result[1]].nesting_level

        level_difference -= 1

        for i in range(level_difference):
            assembly_file.write("lw t0,-4(t0)\n")

        if isinstance(search_result[0],Variable) or isinstance(search_result[0],Parameter):

            temp_offset = search_result[0].offset
            assembly_file.write("addi t0,t0,-"+str(temp_offset)+"\n")

def loadvr(v,r):
    global assembly_file
    global scopes

    if v.lstrip('-').isdigit():
        assembly_file.write("li "+str(r)+", "+str(v) +"\n")
    
    else:

        search_result = search_scope(v)

        current_scope = scopes[search_result[1]]

        if current_scope.nesting_level == 0 and (isinstance(search_result[0],Variable) or isinstance(search_result[0],TempVariable)):
            assembly_file.write("lw "+str(r)+",-"+str(search_result[0].offset)+"(gp)\n")
        
        elif current_scope.nesting_level == scopes[len(scopes)-1].nesting_level and (isinstance(search_result[0],Variable) or isinstance(search_result[0],TempVariable) or isinstance(search_result[0],Parameter)):
            assembly_file.write("lw "+str(r)+",-"+str(search_result[0].offset)+"(sp)\n")
            
        elif current_scope.nesting_level < scopes[len(scopes)-1].nesting_level and (isinstance(search_result[0],Variable) or isinstance(search_result[0],Parameter)):
            gnvlcode(v)
            assembly_file.write("lw " +str(r) + "," + "0(t0)" + "\n")
    
def storerv(r,v):
    global assembly_file
    global scopes
    
    search_result = search_scope(v)

    current_scope = scopes[search_result[1]]

    if current_scope.nesting_level == 0 and (isinstance(search_result[0],Variable) or isinstance(search_result[0],TempVariable)):
        assembly_file.write("sw "+str(r)+",-"+str(search_result[0].offset)+"(gp)\n")
    
    elif current_scope.nesting_level == scopes[len(scopes)-1].nesting_level and (isinstance(search_result[0],Variable) or isinstance(search_result[0],TempVariable) or isinstance(search_result[0],Parameter)):
        assembly_file.write("sw "+str(r)+",-"+str(search_result[0].offset)+"(sp)\n")

    elif current_scope.nesting_level < scopes[len(scopes)-1].nesting_level and (isinstance(search_result[0],Variable) or isinstance(search_result[0],Parameter)):
        gnvlcode(v)
        assembly_file.write("sw " +str(r) + "," + "0(t0)" + "\n")


def make_final_code():
    global quad_list
    global scopes
    global assembly_file

    parameter_counter = -1
    parameter_f = True
    function_name = ""

    for i in range(len(quad_list)):
        
        quad = quad_list[i]

        assembly_file.write("\nlabel"+str(quad.quad[0])+": \n")

        if quad.quad[1] == 'inp':
            assembly_file.write("li a7,63\n")
            assembly_file.write("ecall\n")
            storerv("a0", quad.quad[2])

        elif quad.quad[1] == 'out':
            loadvr(quad.quad[2],"a0")
            assembly_file.write("li a7,1\n")
            assembly_file.write("ecall\n")
            assembly_file.write("li a0, 10\n")  # ASCII value for newline character ('\n' is 10)
            assembly_file.write("li a7, 11\n")  # Syscall number for print character
            assembly_file.write("ecall\n")  # Perform the syscall

        elif quad.quad[1] == 'halt':
            assembly_file.write("li a0,0\n")
            assembly_file.write("li a7,93\n")
            assembly_file.write("ecall\n")

        elif quad.quad[1] == 'jump':
            assembly_file.write("j label"+str(quad.quad[4])+"\n")

        elif quad.quad[1] == ">":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("bgt,t1,t2,label"+str(quad.quad[4])+"\n")

        elif quad.quad[1] == ">=":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("bge,t1,t2,label"+str(quad.quad[4])+"\n")

        elif quad.quad[1] == "<":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("blt,t1,t2,label"+str(quad.quad[4])+"\n")

        elif quad.quad[1] == "<=":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("ble,t1,t2,label"+str(quad.quad[4])+"\n")

        elif quad.quad[1] == "!=":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("bne,t1,t2,label"+str(quad.quad[4])+"\n")

        elif quad.quad[1] == "==":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("beq,t1,t2,label"+str(quad.quad[4])+"\n")

        elif quad.quad[1] == '=':
            loadvr(quad.quad[2],"t1")
            storerv("t1",quad.quad[4])
        
        elif quad.quad[1] == "//":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("div t1,t1,t2"+"\n")
            storerv("t1",quad.quad[4])

        elif quad.quad[1] == "*":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("mul t1,t1,t2"+"\n")
            storerv("t1",quad.quad[4])

        elif quad.quad[1] == "-":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("sub t1,t1,t2"+"\n")
            storerv("t1",quad.quad[4])

        elif quad.quad[1] == "+":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("add t1,t1,t2"+"\n")
            storerv("t1",quad.quad[4])

        elif quad.quad[1] == "%":
            loadvr(quad.quad[2],"t1")
            loadvr(quad.quad[3],"t2")
            assembly_file.write("rem t1,t1,t2"+"\n")
            storerv("t1",quad.quad[4])

        elif quad.quad[1] == "retv":
            loadvr(quad.quad[2],"t1")
            assembly_file.write("lw t0,-8(sp)\n")
            assembly_file.write("sw t1,0(t0)\n")
            assembly_file.write("lw ra,0(sp)\n")
            assembly_file.write("jr ra\n")
        
        elif quad.quad[1] == "par":

            if parameter_f == False:
                temp_index = i
                temp_quad = quad_list[temp_index]

                while temp_quad.quad[1] != "call":
                    temp_index += 1
                    temp_quad = quad_list[temp_index]

                function_name = temp_quad.quad[2]

                search_result = search_scope(function_name)
                assembly_file.write("addi s0,sp,"+str(search_result[0].frame_length)+"\n")
                
            if quad.quad[3] == "cv":
                parameter_f = True

                if parameter_f == True:
                    parameter_counter += 1

                loadvr(quad.quad[2],"t0")
                assembly_file.write("sw t0,-"+str(12+4*parameter_counter)+"(s0)\n")
                continue
            
            elif quad.quad[3] == "ret":
                search_result = search_scope(quad.quad[2])
                assembly_file.write("addi t0, sp, -" + str(search_result[0].offset) + "\n")
                assembly_file.write("sw t0, -8(s0) \n")
        
        elif quad.quad[1] == "call":

            search_result = search_scope(quad.quad[2])

            current_scope = scopes[search_result[1]]

            if scopes[len(scopes) - 1].nesting_level == current_scope.nesting_level:
                assembly_file.write("lw t0,-4(sp)\n")
                assembly_file.write("sw t0,-4(s0)\n")
            else:
                assembly_file.write("sw sp,-4(s0)\n")
            
            assembly_file.write("addi sp,sp,"+str(search_result[0].frame_length)+"\n")
            assembly_file.write("jal"+" label"+str(search_result[0].start_quad)+"\n")
            assembly_file.write("addi sp,sp,-"+str(search_result[0].frame_length)+"\n")

        elif quad.quad[1] == 'begin_block':

            if quad.quad[2] == "main":
                assembly_file.seek(0)
                assembly_file.write("j label"+str(quad.quad[0])+"\n")
                assembly_file.seek(0, os.SEEK_END)
                assembly_file.write("addi sp,sp,"+str(main_framelength)+"\n")
                assembly_file.write("mv gp,sp\n")
            else:
                assembly_file.write("sw ra,0(sp)\n")

        elif (quad.quad[1] == "end_block"):
            if(quad.quad[2] != "main"):
                assembly_file.write("lw ra,0(sp)\n")
                assembly_file.write("jr ra\n")

        parameter_f = False
        parameter_counter = -1
        function_name = ""
    
    write_quads()

    quad_list = []
            

syntax_analyzer()

file.close()
assembly_file.close()
file_int.close()