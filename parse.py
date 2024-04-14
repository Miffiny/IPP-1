import sys
import re


class Token:
    def __init__(self, token_type, token_value):
        self.token_type = token_type
        self.token_value = token_value

class Stats:
    def __init__(self):
        self.loc = 0  # Number of instructions
        self.comments = 0  # Number of comments
        self.labels = {}  # Dictionary to hold labels and their order
        self.jumps = {}  # Dictionary to hold jump labels and their order
        self.used_instructions = {}  # Dictionary to hold used instructions and their occurrences
        self.eol = 0  # Number of EOL occurrences


stats = Stats()

# Define regex patterns as macros
INT_CONST = r'int@[-+]?\d+'
BOOL_CONST = r'bool@(true|false)'
STRING_CONST = r'string@[^#\s\\]*(?:\\[\d]{3}[^#\s\\]*)*'
NIL_CONST = r'nil@nil'
TYPE = r'(int|bool|string)'
VAR = r'(LF|TF|GF)@[a-zA-Z_\-&%*$!?][a-zA-Z0-9_\-&%*$!?]*'
LABEL = r'[a-zA-Z_\-&%*$!?][a-zA-Z0-9_\-&%*$!?]*'

instruction_dict = {
    # 0 argument instructions
    'RETURN': [],
    'CREATEFRAME': [],
    'PUSHFRAME': [],
    'POPFRAME': [],
    'BREAK': [],
    # 1 argument instructions
    'DEFVAR': ['var'],
    'POPS': ['var'],
    'CALL': ['label'],
    'LABEL': ['label'],
    'JUMP': ['label'],
    'PUSHS': ['symb'],
    'EXIT': ['symb'],
    'DPRINT': ['symb'],
    'WRITE': ['symb'],
    # 2 arguments instructions
    'MOVE': ['var', 'symb'],
    'NOT': ['var', 'symb'],
    'INT2CHAR': ['var', 'symb'],
    'READ': ['var', 'type'],
    'TYPE': ['var', 'symb'],
    'STRLEN': ['var', 'symb'],
    # 3 arguments instructions
    'ADD': ['var', 'symb', 'symb'],
    'SUB': ['var', 'symb', 'symb'],
    'MUL': ['var', 'symb', 'symb'],
    'IDIV': ['var', 'symb', 'symb'],
    'LT': ['var', 'symb', 'symb'],
    'GT': ['var', 'symb', 'symb'],
    'EQ': ['var', 'symb', 'symb'],
    'AND': ['var', 'symb', 'symb'],
    'OR': ['var', 'symb', 'symb'],
    'STRI2INT': ['var', 'symb', 'symb'],
    'CONCAT': ['var', 'symb', 'symb'],
    'GETCHAR': ['var', 'symb', 'symb'],
    'SETCHAR': ['var', 'symb', 'symb'],
    'JUMPIFEQ': ['label', 'symb', 'symb'],
    'JUMPIFNEQ': ['label', 'symb', 'symb']
}

order = 0   # global counter for output XML


def match_pattern(operand):
    # Combine regex patterns into a single pattern
    const_pattern = f'({NIL_CONST}|{INT_CONST}|{BOOL_CONST}|{STRING_CONST})'

    # Check if the operand matches any of the constant patterns
    if re.fullmatch(const_pattern, operand):
        return Token('const', operand)
    elif re.fullmatch(TYPE, operand):
        return Token('type', operand)
    elif re.fullmatch(VAR, operand):
        return Token('var', operand)
    elif re.fullmatch(LABEL, operand):
        return Token('label', operand)
    else:
        # No match found, raise error 23 to stderr
        print("Error: Operand pattern mismatch", file=sys.stderr)
        sys.exit(23)


def instruction_scan(instruction):
    global stats  # Access the stats object defined in the global scope
    # Check if the instruction doesn't start with "#" or EOL
    if instruction.startswith("#") or not instruction.strip():
        return

    # Split the instruction into parts before and after the "#" character
    parts = instruction.split("#", 1)
    instruction_part = parts[0].strip()

    # Increment stats.comments if there is a comment section on this line
    if len(parts) > 1:
        stats.comments += 1

    # Split the instruction part into the opcode and arguments
    opcode_args = instruction_part.split(maxsplit=1)
    opcode = opcode_args[0]
    args = opcode_args[1] if len(opcode_args) > 1 else ''

    # Check if the opcode exists in the instruction dictionary
    if opcode not in instruction_dict:
        # If not, raise an error to stderr with error code 22
        print(f"Error: Unknown opcode '{opcode}'", file=sys.stderr)
        sys.exit(22)

    # Parse the arguments and match their patterns
    instruction_array = [opcode]
    for arg in args.split():
        token = match_pattern(arg)
        instruction_array.append(token)

    # Call the parse_instruction function with the instruction array
    parse_instruction(instruction_array)

    # Return after processing the instruction
    return


def parse_instruction(instruction_array):
    # Read the opcode from the instruction_array
    opcode = instruction_array[0]

    # Check if the opcode exists in the instruction_dict
    if opcode not in instruction_dict:
        print(f"Error: Unknown opcode '{opcode}'", file=sys.stderr)
        sys.exit(23)

    # Get the argument patterns for the opcode
    arg_patterns = instruction_dict[opcode]

    # Check the argument types pattern
    num_args = len(instruction_array) - 1
    for i, pattern in enumerate(arg_patterns):
        if i >= num_args:
            # If there are fewer tokens than expected
            print("Error: Not enough arguments provided", file=sys.stderr)
            sys.exit(23)

        token = instruction_array[i + 1]  # Skip the opcode at index 0
        if pattern == 'var':
            if token.token_type != 'var':
                print(f"Error: Argument {i + 1} must be a variable", file=sys.stderr)
                sys.exit(23)
        elif pattern == 'symb':
            if token.token_type not in ['var', 'const']:
                print(f"Error: Argument {i + 1} must be a variable or constant", file=sys.stderr)
                sys.exit(23)
        elif pattern == 'type':
            if token.token_type != 'type':
                print(f"Error: Argument {i + 1} must be a type", file=sys.stderr)
                sys.exit(23)
        elif pattern == 'label':
            if token.token_type != 'label':
                print(f"Error: Argument {i + 1} must be a label", file=sys.stderr)
                sys.exit(23)

    # If there are more tokens than expected
    if num_args > len(arg_patterns):
        print("Error: Too many arguments provided", file=sys.stderr)
        sys.exit(23)

    # Call the print_XML function with the instruction_array
    print_xml(instruction_array)
    return


def print_xml(instruction_array):
    global order
    global stats

    # Increment the order for the next instruction
    order += 1

    # Update stats for used instructions
    opcode = instruction_array[0]
    if opcode in stats.used_instructions:
        stats.used_instructions[opcode] += 1
    else:
        stats.used_instructions[opcode] = 1

    # Check if the opcode is 'LABEL'
    if opcode == 'LABEL':
        label_name = instruction_array[1].token_value
        label_order = order
        if label_name in stats.labels:
            print("Error: Duplicate label.")
            sys.exit(23)
        else:
            stats.labels[label_name] = label_order

    # Check if the opcode is any of 'CALL', 'JUMP', 'JUMPIFEQ', 'JUMPIFNEQ'
    if opcode in ['CALL', 'JUMP', 'JUMPIFEQ', 'JUMPIFNEQ']:
        label_name = instruction_array[1].token_value
        stats.jumps[label_name] = order

    # Print the opening tag of the instruction
    print(f'<instruction order="{order}" opcode="{instruction_array[0]}">')

    # Initialize the argument counter
    arg_counter = 1

    # Iterate over each token in the instruction array
    for token in instruction_array[1:]:
        # Check if the token type is not 'const'
        if token.token_type == 'const':
            # Update token type based on the beginning of token value
            if token.token_value.startswith('string@'):
                token_type = 'string'
                # Skip the prefix 'string@' when printing token_value
                token_value = token.token_value[len('string@'):]
            elif token.token_value.startswith('bool@'):
                token_type = 'bool'
                # Skip the prefix 'bool@' when printing token_value
                token_value = token.token_value[len('bool@'):]
            elif token.token_value.startswith('int@'):
                token_type = 'int'
                # Skip the prefix 'int@' when printing token_value
                token_value = token.token_value[len('int@'):]
            elif token.token_value == 'nil':
                token_type = 'nil'
                token_value = token.token_value
        else:
            token_type = token.token_type
            token_value = token.token_value

        # Print the argument tag
        print(f'    <arg{arg_counter} type="{token_type}">{token_value}</arg{arg_counter}>')

        # Increment the argument counter
        arg_counter += 1

    # Print the closing tag of the instruction
    print('</instruction>')
    return


def main():
    # Process command-line arguments
    args = sys.argv[1:]
    stats_files = set()

    # Check for --help argument
    if '--help' in args:
        # Check if there are any other arguments before or after --help
        help_index = args.index('--help')
        if help_index != 0 or len(args) > 1:
            print("Error: The --help parameter cannot be combined with other parameters.", file=sys.stderr)
            sys.exit(10)
        print(
            "Usage: python3 parser.py [--stats=<filename>]"
            " [--loc] [--comments] [--labels] [--jumps] [--print=<string>]"
            " [--eol] [--fwjumps] [--backjumps] [--badjumps] [--frequent]\n"
            " --help prints help message\n"
            " --stats=<file> prints stats to the specified file\n"
            " --loc prints number of lines with instructions\n"
            " --comments prints number of lines with comments\n"
            " --labels prints number of unique labels\n"
            " --jumps prints number of jumps\n"
            " --backjumps prints number of back jumps\n"
            " --fwjumps prints number of forward jumps\n"
            " --badjumps prints number of jumps to the missing label\n"
            " --print=<string> prints the specified string\n"
            " --frequent prints in alphabetical order the most frequent instructions\n"
            " --eol prints number of EOLs\n"
            " Note: any of the arguments except the --help would require --stats=<file> argument first\n"
        )
        sys.exit(0)

    # Check for --stats arguments and collect statistics file names
    for arg in args:
        if arg.startswith('--stats='):
            filename = arg.split('=')[1]
            stats_files.add(filename)
        elif arg == '--stats':
            print("Error: Missing file name after --stats.", file=sys.stderr)
            sys.exit(10)

    # Check for duplicate stats file names
    if len(stats_files) != len(set(stats_files)):
        print("Error: Attempting to write multiple groups of statistics to the same file.", file=sys.stderr)
        sys.exit(12)

    # Print XML header
    print('<?xml version="1.0" encoding="UTF-8"?>')
    print('<program language="IPPcode24">')

    # Initialize flag for first line
    first_line = True

    for line in sys.stdin:
        line = line.strip()
        stats.eol += 1  # Increment End-of-Line count for every line

        if first_line:
            if line != '.IPPcode24':
                print("Error: Missing or incorrect '.IPPcode24' header.", file=sys.stderr)
                sys.exit(22)
            first_line = False
            continue

        if line.startswith('#'):
            stats.comments += 1  # Increment comment count for lines starting with '#'
            continue

        if not line:
            continue

        stats.loc += 1  # Increment instruction count for non-empty lines
        instruction_scan(line)

    # Print XML footer
    print('</program>')

    if len(args) > 0 and not args[0].startswith('--help'):
        fwjumps = 0
        backjumps = 0
        badjumps = 0
        # Count forward, backward, and bad jumps
        for label, order in stats.jumps.items():
            if label in stats.labels:
                label_order = stats.labels[label]
                if order < label_order:
                    fwjumps += 1
                elif order > label_order:
                    backjumps += 1
                else:
                    badjumps += 1
    # Print statistics to files
    if len(args) > 0 and args[0].startswith('--stats='):
        filename = args[0].split('=')[1]
        with open(filename, 'w') as f:
            # Loop through the arguments starting from the second one
            for arg in args[1:]:
                # Check if the argument is a --stats= argument
                if arg.startswith('--stats='):
                    # Close the current file and open the new one
                    f.close()
                    filename = arg.split('=')[1]
                    f = open(filename, 'w')
                elif arg == '--loc':
                    f.write(str(stats.loc) + '\n')
                elif arg == '--comments':
                    f.write(str(stats.comments) + '\n')
                elif arg == '--labels':
                    f.write(str(len(stats.labels)) + '\n')
                elif arg == '--jumps':
                    f.write(str(len(stats.jumps)) + '\n')
                elif arg.startswith('--print='):
                    print_value = arg.split('=')[1]
                    f.write(print_value + '\n')
                elif arg == '--eol':
                    f.write(str(stats.eol) + '\n')
                elif arg == '--fwjumps':
                    f.write(str(fwjumps) + '\n')
                elif arg == '--backjumps':
                    f.write(str(backjumps) + '\n')
                elif arg == '--badjumps':
                    f.write(str(badjumps) + '\n')
                elif arg == '--frequent':
                    buffer = []  # Local buffer array to store frequent instructions
                    threshold = stats.loc * 0.35  # Calculate threshold
                    current_capacity = 0  # Current capacity of frequent instructions

                    # Find frequent instructions
                    while current_capacity < threshold:
                        max_usage = max(stats.used_instructions.values())
                        frequent_instr = [k for k, v in stats.used_instructions.items() if v == max_usage][0]
                        buffer.append(frequent_instr)
                        current_capacity += max_usage
                        del stats.used_instructions[frequent_instr]  # Remove the instruction from stats

                    # Write frequent instructions to the file in alphabetical order
                    buffer.sort()
                    f.write(','.join(buffer))
                    f.write('\n')
                else:
                    print("Error: Unknown argument.", file=sys.stderr)
                    sys.exit(10)


if __name__ == "__main__":
    main()
