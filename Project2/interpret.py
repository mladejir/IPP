########    Projekt IPP 2.cast (interpret)#########   
#Jmeno: Jiri Mladek
#Login: xmlade01
################################################### 
import argparse as AP
import xml.etree.ElementTree as ET
import sys
import re

###################################################   
#############   Assisting functions  ##############
###################################################  
def handle_error(message, error_code):
    """Funkce pro osetreni erroru
    Args:
        message (string): error message
        error_code (int): error code 
    """
    print(message, file=sys.stderr)
    sys.exit(error_code)
    
def replace_escape(string):
    """Function for replacing escape sequence
    Args:
        string (string): string to replace
    Returns:
        new_string(string): replaced string
    """
    new_string = string
    for escape in re.finditer("\\\\\d\d\d", string):
        escape_number = escape.group()
        escape_number = escape_number.replace("\\", "") #delete backslash
        char = chr(int(escape_number))
        new_string = new_string.replace(escape.group(), char)
    return new_string

def store_to_var(data_type_towrite, value_towrite, var):
    """Function which stores data into variable in a frame
    Args:
        data_type_towrite (string): data type of variable
        value_towrite (string): value of variable
        var (list): variable to assign to
    """
    if(var[0] == "var"):
        if(var[1] == "GF"): 
            if(var[2] not in prog._global_frame):
                handle_error(f"Accessing non-existing variable '{var[2]}'in GF!", 54)
            else:
                prog._global_frame[var[2]] = [data_type_towrite, value_towrite]
        elif (var[1] == "LF"):
            prog.does_lf_exist() #check if lf exists
            lf_index = len(prog._local_frame) - 1
            if(var[2] not in prog._local_frame[lf_index]):
                handle_error(f"Accessing non-existing variable '{var[2]}'in LF!", 54)
            else:
                prog._local_frame[lf_index][var[2]] = [data_type_towrite, value_towrite]
        elif (var[1] == "TF"):
            prog.does_tf_exist() #check if TF exists
            if(var[2] not in prog._temp_frame):
                handle_error(f"Accessing non-existing variable '{var[2]}'in TF!", 54)
            else:
                prog._temp_frame[var[2]] = [data_type_towrite, value_towrite]
    else:
        handle_error("Expected 'var'!", 32)
    
def identify_symbol(symb):
    """Function to determine if symbol is a variable
    Args:
        symb: symbol to inspect
    Returns:
        is_var: true if is a symbol is a variable
    """
    if(re.match("^var$", symb)):
        is_var = True
    elif(re.match("^(int|bool|string|nil)$", symb)):
        is_var = False
    else:
        handle_error("Not a correct symbol 'type'!", 32)
    return is_var

def get_symbol_dtype_value(is_var, symb, ignore_inicialized):
    """Function to get data type and value of a symbol
    Args:
        is_var (bool): true if is a variale
        symb: symbol to inspect
        ignore_inicialized (bool): if inicialization of variable should be ignored
    Returns:
        data_type_to_write: data type of symbol
        value_to_write: value of symbol
    """
    if(is_var):
        if(symb[1]== "GF"): 
            try:
                towrite = prog._global_frame[symb[2]]
                #check if variable is inicialized
                if(towrite):
                    data_type_towrite = towrite[0]
                    value_towrite = towrite[1]
                else:
                    if(ignore_inicialized):
                        data_type_towrite = ""
                        value_towrite = ""
                    else:
                        handle_error("Missing value in variable!", 56)
            except KeyError:
                handle_error(f"Accessing non-existing variable '{symb[2]}'in GF!", 54)
        elif (symb[1] == "LF"):
            prog.does_lf_exist() #check if LF exists
            lf_index = len(prog._local_frame) - 1
            try:
                towrite = prog._local_frame[lf_index][symb[2]]
                if(towrite):
                    data_type_towrite = towrite[0]
                    value_towrite = towrite[1]
                else:
                    if(ignore_inicialized):
                        data_type_towrite = ""
                        value_towrite = ""
                    else:
                        handle_error("Missing value in variable!", 56)
            except KeyError:
                handle_error(f"Accessing non-existing variable '{symb[2]}'in LF!", 54)
        elif (symb[1] == "TF"):
            prog.does_tf_exist() #check if TF exists
            try:
                towrite = prog._temp_frame[symb[2]]
                #check if variable is initialized
                if(towrite):
                    data_type_towrite = towrite[0]
                    value_towrite = towrite[1]
                else:
                    if(ignore_inicialized):
                        data_type_towrite = ""
                        value_towrite = ""
                    else:
                        handle_error("Missing value in variable!", 56)
            except KeyError:
                handle_error(f"Accessing non-existing variable '{symb[2]}'in TF!", 54)
    else: #if symbol is a constant
        data_type_towrite = symb[0]
        value_towrite = symb[1]
    
    return data_type_towrite, value_towrite
    
def load_input_str():
    """Function which loads input for READ instruction
    Returns:
        input_str: one line from input
    """
    if(prog._input_file == sys.stdin): #if input should be read from stdin
        try:
            input_str = input()
        except EOFError:
            input_str = ""
    else: #if input should be read from file
        with open(prog._input_file) as f:
            lines = [line.rstrip('\n') for line in f] #delete new line character
        try:
            input_str = lines[prog._read_counter]
            prog._read_counter += 1
        except:
            input_str = ""
    return input_str
    
def are_eq(symb1, symb2):
    
    #Check if is a variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    if(re.match("^(int|bool|string)$", symb1_type) and re.match("^(int|bool|string)$", symb2_type) and symb1_type == symb2_type):
        if(symb1_type == "int"):
            result = (int(symb1_value) == int(symb2_value))
        else: #for bool and string
            result = (symb1_value == symb2_value)
    elif(symb1_type == "nil" and symb2_type == "nil"):
        result = True
    elif(symb1_type == "nil" or symb2_type == "nil"):
        result = False
    else:
        handle_error("Wrong types of operands!", 53)
    return result

def get_stats():
    """Function to print program statistics
    """
    print("Global frame:", file=sys.stderr)
    print(prog._global_frame, file=sys.stderr)
    print("Local frame:", file=sys.stderr)
    print(prog._local_frame, file=sys.stderr)
    print("Temporary frame:", file=sys.stderr)
    print(prog._temp_frame, file=sys.stderr)
    
        
def check_tag(elem, tag_str, allowed_attributes_list, required_attributes_list, tag_to_check):
    """Function which checks if xml tag is correct
    Args:
        elem: xml element
        tag_str (string): the tag
        allowed_attributes_list (list): attributes, which tag can have
        required_attributes_list (list): attributes, which tag must have
        tag_to_check (bool): true if tag should be checked
    """
    if(tag_to_check):
        if(elem.tag != tag_str):
            handle_error(f"Unexpected XML structure, '{elem.tag}' tag unexpected.", 32)
    
    attributes = list(elem.attrib) #current attributes of a tag
    allowed_attributes = allowed_attributes_list
    #check if tag has forbidden attributes
    flag = True
    for attribute in attributes:
        if(flag):
            flag = False
            for allowed_attribute in allowed_attributes:
                if(attribute == allowed_attribute):
                    flag = True
        else:
            handle_error(f"Tag '{elem.tag}' has forbidden attribute!", 32)
    #Check the last attribute
    if not flag:
        handle_error(f"Tag '{elem.tag}' has forbidden attribute!", 32)
    #Check compulsory attributes
    for required_attribute in required_attributes_list:
        if required_attribute not in attributes:
            handle_error(f"Required attributes of '{elem.tag}' are missing!", 32)
    
    
    
###################################################   
##################   Classes  #####################
###################################################  
#Class for whole program and managing memory, singleton design pattern
class Program:
    def __init__(self):
        self._global_frame = {}
        self._local_frame = []
        self._temp_frame = {}
        self._lf_exists = False
        self._tf_exists = False
        self._call_stack = []
        self._stack = []
        self._read_counter = 0
        
    def parse_args(self):
        """Function for parsing and checking program arguments
        Returns: program arguments
        """
        parse = AP.ArgumentParser()
        parse.add_argument("--source", help="Source file with XML representation", action="store", default=sys.stdin)
        parse.add_argument("--input", help="File with input for interpretation", action="store", default=sys.stdin)
        arguments = parse.parse_args()

        #check arguments
        if not (arguments.source or arguments.input):
            parse.error("At least 1 argument required!!");
            sys.exit(10); 
            
        #check if files exist
        if(arguments.source != sys.stdin):
            try:
                source_file = open(arguments.source, "r")
                source_file.close()
            except IOError:
                handle_error("Error when opening a file!", 11)
        if(arguments.input != sys.stdin):
            try:
                input_file = open(arguments.input, "r")
                input_file.close()
            except IOError:
                handle_error("Error when opening a file!", 11)
            
        self._input_file = arguments.input
        return arguments
    
    def parse_xml(self, arguments):
        """Function for parsing XML
        Args:
            arguments: program arguments
        Returns: root of XML
        """
        try:
            tree = ET.parse(arguments.source)
        except :
            handle_error("XML is not correctly formatted!", 31)
        root = tree.getroot()
        check_tag(root, "program", ["language", "name", "description"], ["language"], True) #check tag 'program'
        return root

    def load_instructions(self, root):
        """Function which loads instructions and their arguments
        Args:
            root: root XML tag
        """
        #looping over XML
        for index, instruction in enumerate(root):
            check_tag(instruction, "instruction", ["order", "opcode"], ["order", "opcode"], True) #Check instruction tag
            instruction_obj = Instruction(instruction.get('opcode'), instruction.get('order')) #Create instance of Instruction
            instruction_obj.load_check_order()
            #Load arguments
            for argument in instruction: 
                check_tag(argument, "", ["type"], ["type"], False)
                Instruction.get_instructions_list()[index].load_arguments(argument.tag, argument.get('type'), argument.text)
        
        #Check duplicity of 'order'
        if len(Instruction.get_orders()) != len(set(Instruction.get_orders())):
            handle_error("Duplicate instruction order!", 32)
        
    def store_labels(self):
        """Function to loop through instructions and find labels
        """
        for index, instruction in enumerate(Instruction.get_instructions_list()): 
            instruction.load_check_label(index)
            
            
    def execute_instructions(self, program_args):
        """Function for executing instructions
        Args:
            program_args: arguments of program
        """
        instructions = Instruction.get_instructions_list()
        instructions_length = len(instructions)
        index = 0
        #Looping over instructions
        while index < instructions_length:
            instruction = instructions[index]
            arguments = instruction.get_arguments()
            op_code = instruction.get_opcode().upper() #enable upper and lowercase
            ignore_increment = False
            index, ignore_increment = map_opcode[op_code](index, arguments, ignore_increment, instruction) #calls the appropriate function
            if not (ignore_increment): 
                index += 1 #move to next instruction
    
    def does_lf_exist(self):
        """Function to check if LF exists and handling possibble errors
        """
        if not self._lf_exists:
            handle_error("LF doesn't exist!",55)
        
    def does_tf_exist(self):
        """Function to check if TF exists and handling possibble errors
        """
        if not self._tf_exists:
            handle_error("TF doesn't exist!",55)
  
#Class for instruction, also keeps ordered list of instructions  
class Instruction:
    _instructions_list = []
    _labels = {}
    _orders = []
    
    def __init__(self, op_code, order):
        self._opcode = op_code
        self._order = int(order)
        self._arguments = [ [], [], [] ]
        type(self)._instructions_list.append(self)
        
    def get_opcode(self):
        return self._opcode
    
    def get_arguments(self):
        return self._arguments
    
    def load_arguments(self, tag, type, value):
        """Function which loads arguments of instruction
        Args:
            tag (string): xml tag
            type (string): data type
            value (_type_): value of argument
        """
        if(tag == "arg1"):
            index = 0
        elif(tag == "arg2"):
            index = 1
        elif(tag == "arg3"):
            index = 2
        else:
            handle_error(f"Unexpected XML structure, '{tag}' tag unexpected.", 32)

        #Append type to list
        self._arguments[index].append(type)
        #If empty value of argument
        if(value == None):
            if(type == "string"):
                value = ""
            else:
                handle_error("Empty value in tag!", 56)
            
        if(re.match("^var$", type)): #if it is variable, then save her type, frame and value
            split = value.split("@", 1)
            self._arguments[index].append(split[0])
            self._arguments[index].append(split[1])
        elif(re.match("^(int|bool|string|nil|label|type)$", type)): #else save only type and value
            if(type == "string"):
                value = replace_escape(value)
            self._arguments[index].append(value)
        else:
            handle_error(f"Incorrect argument 'type' in tag '{tag}'.", 32)
    
    def load_check_order(self):
        """Function which loads and checks correct order of instruction
        """
        if(self._order <= 0):
            handle_error("Instruction with wrong order!", 32)
        self._orders.append(self._order)
        
    def load_check_label(self, index):
        """Function which loads and checks if label already exists
        Args:
            index (int): number of instruction, to which label will refer
        """
        if(self._opcode == "LABEL"):
            if self._arguments[0][1] not in self._labels:
                self._labels[self._arguments[0][1]] = index
            else:
                handle_error("Error: label with same name!", 52)
                
    @classmethod
    def get_instructions_list(cls):
        return cls._instructions_list
    
    @classmethod
    def sort_instructions(cls):
        cls._instructions_list.sort(key=lambda x: x._order)
    
    @classmethod
    def get_labels(cls):
        return cls._labels
    
    @classmethod
    def get_orders(cls):
        return cls._orders
    
    
###################################################   
##########  Functions for instructions ############
###################################################   
#All following functions have same arguments and return type, so I put comment only to first one

def do_move(index, arguments, ignore_increment, instruction):
    """Function for instruction with opcode "MOVE"
    Args:
        index (int): number of executing instruction (indexing in ordered list)
        arguments (list): arguments of instruction
        ignore_increment (bool): true if shouldn't be incremented
        instruction: instruction object
    Returns:
        index: possibly changed index of next instruction
        ignore_increment: if we should move to next instruction in loop
    """
    var = arguments[0]
    symb1 = arguments[1]
    
    is_var = identify_symbol(symb1[0])
    data_type_towrite, value_towrite = get_symbol_dtype_value(is_var, symb1, False)
    store_to_var(data_type_towrite, value_towrite, var)
    return index, ignore_increment


def do_createframe(index, arguments, ignore_increment, instruction):
    
    prog._tf_exists = True
    prog._temp_frame.clear()
    return index, ignore_increment

def do_pushframe(index, arguments, ignore_increment, instruction):
    prog.does_tf_exist() #check, if TF exists
    prog._lf_exists = True
    prog._local_frame.append(prog._temp_frame.copy()) #add TF to LF
    prog._temp_frame.clear()
    prog._tf_exists = False
    return index, ignore_increment
    
    
def do_popframe(index, arguments, ignore_increment, instruction):
    #if LF exists, its content is put into TF
    prog.does_lf_exist() #check if LF exists
    prog._temp_frame.clear()
    prog._temp_frame = prog._local_frame.pop()
    prog._tf_exists = True
    if not (len(prog._local_frame)):
        prog._lf_exists = False
    return index, ignore_increment

def do_defvar(index, arguments, ignore_increment, instruction):
    frame_type = arguments[0][1]
    var_value = arguments[0][2]
    
    if(frame_type == "GF"): 
        #check if variable exists already
        if(var_value not in prog._global_frame):
            prog._global_frame[var_value] = []
        else:
            handle_error("Variable redefinition in GF!", 52)
    elif (frame_type == "LF"):
        prog.does_lf_exist() #check, if LF exists
        lf_index = len(prog._local_frame) - 1 #for indexing
        if(var_value not in prog._local_frame[lf_index]):
            prog._local_frame[lf_index][var_value] = []
        else:
            handle_error("Variable redefinition in LF!", 52)
    elif (frame_type == "TF"):
        prog.does_tf_exist() #check if TF exists
        if(var_value not in prog._temp_frame):
            prog._temp_frame[var_value] = []
        else:
            handle_error("Variable redefinition in TF!", 52)
    return index, ignore_increment

def do_call(index, arguments, ignore_increment, instruction):
    next_instr_index = index + 1
    prog._call_stack.append(next_instr_index)
    index, ignore_increment = do_jump(index, arguments, ignore_increment, instruction)
    return index, ignore_increment

def do_return(index, arguments, ignore_increment, instruction):
    if(len(prog._call_stack)): 
        index = prog._call_stack.pop()
    else: #if call stack is empty
        handle_error("Empty call stack!", 56)
        
    ignore_increment = True 
    return index, ignore_increment

def do_pushs(index, arguments, ignore_increment, instruction):
    symb = arguments[0]
    is_var = identify_symbol(symb[0])
    symb_type, symb_value = get_symbol_dtype_value(is_var, symb, False)
    prog._stack.append([symb_type, symb_value]) #append to stack
    return index, ignore_increment

def do_pops(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    if(prog._stack): #If stack is not empty
        towrite = prog._stack.pop()
        store_to_var(towrite[0], towrite[1], var)
    else:
        handle_error("Data stack is empty!", 56)
    return index, ignore_increment
        
def do_add(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    #Check and count
    if(symb1_type == "int" and symb2_type == "int"):
        result = int(symb1_value) + int(symb2_value)
    else:
        handle_error("Wrong types of operands!", 53)

    store_to_var("int", result, var)
    return index, ignore_increment
        
def do_sub(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)

    #Check and count
    if(symb1_type == "int" and symb2_type == "int"):
        result = int(symb1_value) - int(symb2_value)
    else:
        handle_error("Wrong types of operands!", 53)

    store_to_var("int", result, var)
    return index, ignore_increment

def do_mul(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)

    #kontrola a vypocet
    if(symb1_type == "int" and symb2_type == "int"):
        result = int(symb1_value) * int(symb2_value)
    else:
        handle_error("Wrong types of operands!", 53)

    store_to_var("int", result, var)
    return index, ignore_increment

def do_idiv(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)

    #Check and count
    if(symb1_type == "int" and symb2_type == "int"):
        try:
            result = int(symb1_value) / int(symb2_value)
        except ZeroDivisionError:
            handle_error("Error: Division by zero!", 57)
    else:
        handle_error("Wrong types of operands!", 53)

    store_to_var("int", int(result), var)
    return index, ignore_increment

def do_lt(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    if(re.match("^(int|bool|string)$", symb1_type) and re.match("^(int|bool|string)$", symb2_type) and symb1_type == symb2_type):
        if(symb1_type == "int"):
            result = "true" if (int(symb1_value) < int(symb2_value)) else "false"
        else: #for bool and string
            result = "true" if (symb1_value < symb2_value) else "false"
    else:
        handle_error("Wrong types of operands!", 53)

    store_to_var("bool", result, var)
    return index, ignore_increment
        
        
def do_gt(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    if(re.match("^(int|bool|string)$", symb1_type) and re.match("^(int|bool|string)$", symb2_type) and symb1_type == symb2_type):
        if(symb1_type == "int"):
            result = "true" if (int(symb1_value) > int(symb2_value)) else "false"
        else: #pro bool a string
            result = "true" if (symb1_value > symb2_value) else "false"
    else:
        handle_error("Wrong types of operands!", 53)
        
    store_to_var("bool", result, var)
    return index, ignore_increment

def do_eq(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    if(re.match("^(int|bool|string)$", symb1_type) and re.match("^(int|bool|string)$", symb2_type) and symb1_type == symb2_type):
        if(symb1_type == "int"):
            result = "true" if (int(symb1_value) == int(symb2_value)) else "false"
        else: #for bool and string
            result = "true" if (symb1_value == symb2_value) else "false"
    elif(symb1_type == "nil" and symb2_type == "nil"):
        result = "true"
    elif(symb1_type == "nil" or symb2_type == "nil"):
        result = "false"
    else:
        handle_error("Wrong types of operands!", 53)

    store_to_var("bool", result, var)
    return index, ignore_increment

def do_and(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    if(symb1_type == "bool" and symb2_type == "bool"):
        result = "true" if (symb1_value == "true" and symb2_value == "true") else "false"
    else:
        handle_error("Wrong types of operands!", 53)

    store_to_var("bool", result, var)
    return index, ignore_increment

def do_or(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    if(symb1_type == "bool" and symb2_type == "bool"):
        result = "true" if (symb1_value == "true" or symb2_value == "true") else "false"
    else:
        handle_error("Wrong types of operands!", 53)

    store_to_var("bool", result, var)
    return index, ignore_increment

def do_not(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    
    if(symb1_type == "bool"):
        result = "true" if (symb1_value == "false") else "false"
    else:
        handle_error("Wrong types of operands!", 53)
        
    store_to_var("bool", result, var)
    return index, ignore_increment
    
def do_int2char(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    
    if(symb1_type == "int"):
        try:
            result = chr(int(symb1_value))
        except ValueError:
            handle_error("Not a valid ordinal value!", 58)
    else:
        handle_error("Wrong types of operands!", 53)
        
    store_to_var("string", result, var)
    return index, ignore_increment




def do_stri2int(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    if(symb1_type == "string" and symb2_type == "int"):
        if(int(symb2_value) < 0):
                handle_error("Index out of range!", 58)
        try:
            char = symb1_value[int(symb2_value)]
        except:
            handle_error("Index out of range!", 58)
        result = ord(char) #ordinal value of character
    else:
        handle_error("Wrong types of operands!", 53)
        
    store_to_var("int", result, var)
    return index, ignore_increment
            
def do_read(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    type = arguments[1]
    
    if(type[0] == "type" and re.match("^(int|string|bool)$", type[1])):
        input_str = load_input_str()
        if(input_str == ""):
            result_type = "nil"
            result_value = "nil"
    else:
        handle_error("Wrong type of operands!", 53)
    #data to be saved into variable
    result_type = type[1]
    result_value = input_str
    
    #edge cases
    if(result_type == "int"):
        if not (re.match("^\d+$", result_value)):
            result_type = "nil"
            result_value = "nil"
    elif(result_type == "bool"):
        if(result_value.lower() == "true"):
            result_value = "true"
        else:
            result_value = "false"
        
    store_to_var(result_type, result_value, var)
    return index, ignore_increment

def do_write(index, arguments, ignore_increment, instruction):
    symb = arguments[0]
    #Check, if variable or constant
    is_var = identify_symbol(symb[0])
    symb_type, symb_value = get_symbol_dtype_value(is_var, symb, False)
    #if type is nil, then store empty string
    if(symb_type == "nil"):
        symb_value = ""
        
    print(symb_value,end='')#print to stdout
    return index, ignore_increment    

def do_concat(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    if(symb1_type == "string" and symb2_type == "string"):
        result = symb1_value + symb2_value
    else:
        handle_error("Wrong type of operands!", 53)
        
    store_to_var("string", result, var)
    return index, ignore_increment



def do_strlen(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    
    if(symb1_type == "string"):
        result = len(symb1_value)
    else:
        handle_error("Wrong type of operands!", 53)
        
    store_to_var("int", result, var)
    return index, ignore_increment

def do_getchar(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    if(symb1_type == "string" and symb2_type == "int"):
        if(int(symb2_value) < 0):
            handle_error("Index out of range!", 58)
        try:
            result = symb1_value[int(symb2_value)]
        except:
            handle_error("Index out of range!", 58)
    else:
        handle_error("Wrong type of operands!", 53)
        
    store_to_var("string", result, var)
    return index, ignore_increment




def do_setchar(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    symb2 = arguments[2]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    is_var2 = identify_symbol(symb2[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, False)
    symb2_type, symb2_value = get_symbol_dtype_value(is_var2, symb2, False)
    
    var_type, var_value = get_symbol_dtype_value(True, var, False)
    
    if(symb1_type == "int" and symb2_type == "string"):
        if(int(symb1_value) < 0):
                handle_error("Index out of range!", 58)
        try:
            var_value_list = list(var_value)
            var_value_list[int(symb1_value)] = symb2_value[0]   
            result = "".join(var_value_list)
        except:
            handle_error("Index out of range!", 58)
    else:
        handle_error("Wrong type of operands!", 53)
        
    store_to_var("string", result, var)
    return index, ignore_increment

def do_type(index, arguments, ignore_increment, instruction):
    var = arguments[0]
    symb1 = arguments[1]
    #Check, if variable or constant
    is_var1 = identify_symbol(symb1[0])
    symb1_type, symb1_value = get_symbol_dtype_value(is_var1, symb1, True)
    
    result = symb1_type
    store_to_var("string", result, var)
    return index, ignore_increment
    
def do_label(index, arguments, ignore_increment, instruction):
    #labels are already taken care of, pass
    return index, ignore_increment

def do_jump(index, arguments, ignore_increment, instruction):
    current_lable = arguments[0]
    labels = Instruction.get_labels()
    if(current_lable[0] == "label"):
        if(current_lable[1] in labels):
            ignore_increment = True
            index = labels[current_lable[1]] #finds index of label in a dictionary
        else:
            handle_error("Jumping on non-existing label!", 52)
    else:
        handle_error("Argument is not a lable!", 32)
    return index, ignore_increment

def do_jumpifeq(index, arguments, ignore_increment, instruction):
    symb1 = arguments[1]
    symb2 = arguments[2]
    symbols_equal = are_eq(symb1, symb2) #true if symbols are equal
    if(symbols_equal):
        index, ignore_increment = do_jump(index, arguments, ignore_increment, instruction) 
    return index, ignore_increment

def do_jumpifneq(index, arguments, ignore_increment, instruction):
    symb1 = arguments[1]
    symb2 = arguments[2]
    symbols_equal = are_eq(symb1, symb2) #true if symbols are equal
    if not (symbols_equal):
        index, ignore_increment = do_jump(index, arguments, ignore_increment, instruction)
    return index, ignore_increment

def do_exit(index, arguments, ignore_increment, instruction):
    symb = arguments[0]
    #Check, if variable or constant
    is_var = identify_symbol(symb[0])
    symb_type, symb_value = get_symbol_dtype_value(is_var, symb, False)
    
    if(symb_type == "int"):
        if(int(symb_value) <= 49 and int(symb_value) >= 0):
            sys.exit(int(symb_value)) #exits program with required value
        else:
            handle_error("Not a correct exit value !", 57)
    else: 
        handle_error("Wrong type of operands!", 53) 
            
def do_dprint(index, arguments, ignore_increment, instruction):
    symb = arguments[0]
    #Check, if variable or constant
    is_var = identify_symbol(symb[0])
    symb_type, symb_value = get_symbol_dtype_value(is_var, symb, False)
    if(symb_type == "nil"):
        symb_value = ""
    print(symb_value, file=sys.stderr)
    return index, ignore_increment    

def do_break(index, arguments, ignore_increment, instruction):
    get_stats()
    return index, ignore_increment
###################################################   
########  End of instruction functions ############
###################################################   


#Dictionary, which maps operation code to functions
map_opcode = {
    "CREATEFRAME": do_createframe, "PUSHFRAME": do_pushframe, "POPFRAME": do_popframe, "DEFVAR": do_defvar, "MOVE": do_move, "CALL": do_call, "RETURN": do_return,
    "PUSHS": do_pushs, "POPS": do_pops,  
    "ADD": do_add, "SUB": do_sub, "MUL": do_mul, "IDIV": do_idiv, "LT": do_lt, "GT": do_gt, "EQ": do_eq, "AND": do_and, "OR": do_or, "NOT": do_not, "INT2CHAR": do_int2char, "STRI2INT": do_stri2int,
    "READ": do_read, "WRITE": do_write, 
    "CONCAT": do_concat, "STRLEN": do_strlen, "GETCHAR": do_getchar, "SETCHAR": do_setchar, "TYPE": do_type,
    "LABEL": do_label, "JUMP": do_jump, "JUMPIFEQ": do_jumpifeq, "JUMPIFNEQ": do_jumpifneq, "EXIT": do_exit, 
    "DPRINT": do_dprint, "BREAK": do_break,
}

#Main
if __name__ == '__main__':
    prog = Program() #class for whole program and managing memory
    arguments = prog.parse_args() #parse program arguments
    root = prog.parse_xml(arguments) #parse XML
    prog.load_instructions(root)
    Instruction.sort_instructions() #Sort instructions by order
    prog.store_labels() #Get all labels and their position
    prog.execute_instructions(arguments)
    sys.exit(0)

    

    


