### TO DO:
# parse_instruction when parse_code in Program class
# verify labels only once, when parse_instruction happens
# call and ret to implement

from collections import defaultdict

class Memory:
    def __init__(self):
        self.registers = defaultdict(int)
        self.return_value = -1

class Operator:
    def __init__(self, name, args, interpreter):
        self.name = name
        self.args = args
        self.interpreter = interpreter

    def __repr__(self):
        return f'OP: {self.name} ARGS: {self.args}'
    
    def write(self, val, target):
        self.interpreter.memory.registers[target] = val

class MathOperator(Operator):
    def get_params(self):
        left, right = self.args
        a = int(left) if left.isnumeric() else self.interpreter.memory.registers[left]
        b = int(right) if right.isnumeric() else self.interpreter.memory.registers[right]
        return a, b

    def calculate(self, a, b):
        raise NotImplementedError

    def execute(self):
        a, b = self.get_params()
        target = self.args[0]
        val = self.calculate(a, b)
        self.write(val, target)

class MOV(MathOperator):
    def calculate(self, a, b):
        return b

class ADD(MathOperator):
    def calculate(self, a, b):
        return a + b

class SUB(MathOperator):
    def calculate(self, a, b):
        return a - b

class MUL(MathOperator):
    def calculate(self, a, b):
        return a * b

class DIV(MathOperator):
    def calculate(self, a, b):
        return a // b

class INC(Operator):
    def execute(self):
        target = self.args[0]
        val = self.interpreter.memory.registers[target] + 1
        self.write(val, target)

class DEC(Operator):
    def execute(self):
        target = self.args[0]
        val = self.interpreter.memory.registers[target] - 1
        self.write(val, target)

class MSG(Operator):
    def get_params(self):
        params = []
        for arg in self.args:
            if arg[0] == "'" and arg[-1] == "'":
                params.append(arg[1:-1])
            else:
                params.append(str(self.interpreter.memory.registers[arg]))
        return params

    def execute(self):
        params = self.get_params()
        self.interpreter.memory.return_value = ''.join(params)

class LABEL(Operator):
    def execute(self):
        pass

class JumpOperator(Operator):
    def check_jump(self):
        raise NotImplementedError

    def execute(self):
        target = self.interpreter.program.label_table[self.args[0]]
        if self.check_jump():
            self.interpreter.instruction_ptr = target
            self.interpreter.last_op_jmp = False

class JMP(JumpOperator):
    def check_jump(self):
        return True

class JNE(JumpOperator):
    def check_jump(self):
        return not self.interpreter.last_cmp_equal

class JE(JumpOperator):
    def check_jump(self):
        return self.interpreter.last_cmp_equal

class JGE(JumpOperator):
    def check_jump(self):
        return self.interpreter.last_cmp_equal or self.interpreter.last_cmp_first_greater

class JG(JumpOperator):
    def check_jump(self):
        return self.interpreter.last_cmp_first_greater

class JLE(JumpOperator):
    def check_jump(self):
        return self.interpreter.last_cmp_equal or self.interpreter.last_cmp_second_greater

class JL(JumpOperator):
    def check_jump(self):
        return self.interpreter.last_cmp_second_greater

class CMP(Operator):
    def get_params(self):
        left, right = self.args
        a = int(left) if left.isnumeric() else self.interpreter.memory.registers[left]
        b = int(right) if right.isnumeric() else self.interpreter.memory.registers[right]
        return a, b

    def execute(self):
        a, b = self.get_params()
        if a == b:
            self.interpreter.last_cmp_equal = True
            self.interpreter.last_cmp_first_greater = False
            self.interpreter.last_cmp_second_greater = False
        elif a > b:
            self.interpreter.last_cmp_equal = False
            self.interpreter.last_cmp_first_greater = True
            self.interpreter.last_cmp_second_greater = False
        elif a < b:
            self.interpreter.last_cmp_equal = False
            self.interpreter.last_cmp_first_greater = False
            self.interpreter.last_cmp_second_greater = True

class END(Operator):
    def execute(self):
        self.interpreter.running = False


OP_DICTIONARY = {
        "mov": MOV,
        "inc": INC,
        "dec": DEC,
        "add": ADD,
        "sub": SUB,
        "mul": MUL,
        "div": DIV,
        "jmp": JMP,
        "cmp": CMP,
        "jne": JNE,
        "je": JE,
        "jge": JGE,
        "jg": JG,
        "jle": JLE,
        "jl": JL,
        "call": None,
        "ret": None,
        "msg": MSG,
        "end": END
        }


class Program:
    def __init__(self, code, interpreter):
        self.instructions = self.__parse_code(code)
        self.label_table = self.__find_labels()
        self.interpreter = interpreter
        self.instructions2, self.label_table2 = self.other_parse_code(code)

    def __parse_code(self, code: str) -> list[str]:
        removed_comments = [line.split(';')[0].strip() for line in code.splitlines()]
        lines = [line for line in removed_comments if line]
        return lines
    
    def other_parse_code(self, code:str) -> list[Operator]:
        instructions = []
        label_table = {}
        
        removed_comments = [line.split(';')[0].strip() for line in code.splitlines()]
        lines = [line for line in removed_comments if line]
        
        for ptr, line in enumerate(lines):
            if ':' in line:
                name, args = 'label', []
                instructions.append(LABEL(name, args, self.interpreter))
                label_table[name] = ptr
            elif line == 'end' or line == 'ret':
                name, args = line, []
                instructions.append(OP_DICTIONARY[name](name, args, self.interpreter))
            else:
                name, args = line.split(maxsplit=1)
                args = [arg.strip() for arg in args.split(',')]
                instructions.append(OP_DICTIONARY[name](name, args, self.interpreter))
        
        return instructions, label_table
    
    def __find_labels(self):
        label_table = {}
        for ptr, instruction in enumerate(self.instructions):
            if ':' in instruction:
                label_table[instruction.split(':')[0]] = ptr
        return label_table


class Interpreter:
    def __init__(self):
        self.memory = Memory()
        self.instruction_ptr = 0
        self.program = None
        
        
        self.running = True

        self.last_cmp_equal = None
        self.last_cmp_first_greater = None
        self.last_cmp_second_greater = None

        self.last_op_jmp = False

    def load_code(self, code):
        self.program = Program(code, self)

    def __parse_instruction(self, instruction):
        if ':' in instruction:
            name, args = 'label', []
        elif instruction == 'end' or instruction == 'ret':
            name, args = instruction, []
        else:
            name, args = instruction.split(maxsplit=1)
            args = [arg.strip() for arg in args.split(',')]
        return name, args

    def naive_loop(self, debug=True):
        while self.running:
            try:
                instruction = self.program.instructions[self.instruction_ptr]
                name, args = self.__parse_instruction(instruction)
                self.last_op_jmp = False

                op = OP_DICTIONARY[name](name, args, self)
                op.execute()

                if debug: print(f'After executing {op}. \tRegisters: ' + str([f'{k}: {v}' for k, v in self.memory.registers.items()]))

                if not self.last_op_jmp:
                    self.instruction_ptr += 1

            except IndexError:
                self.running = False
                print('Reached end of program without END instruction. Stopping.')

    def naive_loop2(self, debug=True):
        while self.running:
            try:
                self.last_op_jmp = False

                current_op = self.program.instructions2[self.instruction_ptr]
                current_op.execute()

                if debug: print(f'After executing {current_op}. \tRegisters: ' + str([f'{k}: {v}' for k, v in self.memory.registers.items()]))

                if not self.last_op_jmp:
                    self.instruction_ptr += 1

            except IndexError:
                self.running = False
                print('Reached end of program without END instruction. Stopping.')

program = """
; My first program
mov  a, 5
mov  b, 10
add  a, 2
sub  b, a
mul  b, b
mov  c, 18
div  c, 3
mul  a, c
mul  b, c
div  a, c
cmp 3, 3
jl test
inc a
inc b
inc c
dec a
mul a, c
div b, a
test:
msg a, '^', b, ' = to jakas bzdura', c, 'lol'
end
"""
i = Interpreter()
i.load_code(program)
i.naive_loop2(debug=True)