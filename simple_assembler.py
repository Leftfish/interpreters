### TO DO:
# fib zle dziala # czasem sie zapetla - co jak jest call na callu? brakuje stosu :)
# przecinek w output źle działa z powodu parsowania przez split ','

import sys
from collections import defaultdict

class Memory:
    def __init__(self):
        self.registers = defaultdict(int)
        self.return_value = ['-1']

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

class JumpOperator(Operator):
    def check_jump(self):
        raise NotImplementedError

    def execute(self):
        target = self.interpreter.program.label_table2[self.args[0]]
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

class CALL(Operator):
    def execute(self):
        target = self.interpreter.program.label_table2[self.args[0]]
        self.interpreter.last_call = self.interpreter.instruction_ptr
        self.interpreter.instruction_ptr = target

class RET(Operator):
    def execute(self):
        self.interpreter.instruction_ptr = self.interpreter.last_call

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

class MSG(Operator):
    def get_params(self):
        params = []
        print(self.args)
        res = []
        stack = ''
        collect = False
        for char in self.args:
            if char == "'" and not collect:
                collect = True
            elif char == "'" and collect:
                collect = False
                res.append(''.join(stack))
                stack = []
            elif collect:
                stack += char
            elif char not in ', ':
                res.append(str(self.interpreter.memory.registers[char]))

        params = res
        return params

    def execute(self):
        params = self.get_params()
        self.interpreter.memory.return_value = ''.join(params)

class LABEL(Operator):
    def execute(self):
        pass

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
        "call": CALL,
        "ret": RET,
        "msg": MSG,
        "end": END
        }

class Program:
    def __init__(self, code, interpreter):
        self.interpreter = interpreter
        self.instructions2, self.label_table2 = self.other_parse_code(code)
    
    def other_parse_code(self, code:str) -> list[Operator]:
        instructions = []
        label_table = {}
        
        removed_comments = [line.split(';')[0].strip() for line in code.splitlines()]
        lines = [line for line in removed_comments if line]
        
        for ptr, line in enumerate(lines):
            if ':' in line:
                name, args = line[:-1], []
                instructions.append(LABEL(name, args, self.interpreter))
                label_table[name] = ptr
            elif line == 'end' or line == 'ret' or line == 'call':
                name, args = line, []
                instructions.append(OP_DICTIONARY[name](name, args, self.interpreter))
            elif line.startswith('msg'):
                name, args = line.split(maxsplit=1)
                instructions.append(OP_DICTIONARY[name](name, args, self.interpreter))        
            else:
                name, args = line.split(maxsplit=1)
                args = [arg.strip() for arg in args.split(',')]
                instructions.append(OP_DICTIONARY[name](name, args, self.interpreter))
        return instructions, label_table

class Interpreter:
    def __init__(self):
        self.memory = Memory()
        self.instruction_ptr = 0
        self.program = None
        self.running = False

        self.last_cmp_equal = None
        self.last_cmp_first_greater = None
        self.last_cmp_second_greater = None

        self.last_op_jmp = False
        self.last_call = None

    def load_code(self, code):
        self.program = Program(code, self)

    def naive_loop2(self, debug=True):
        self.running = True

        while self.running:
            try:
                self.last_op_jmp = False

                current_op = self.program.instructions2[self.instruction_ptr]
                current_op.execute()

                if debug: print(f'After executing {current_op}. \tRegisters: ' + str([f'{k}: {v}' for k, v in self.memory.registers.items()]) + f'\t Return: {str(self.memory.return_value)}')

                if not self.last_op_jmp:
                    self.instruction_ptr += 1

            except IndexError:
                self.running = False
                print('Reached end of program without END instruction. Stopping.')

program = """mov   a, 11           ; value1
mov   b, 3            ; value2
call  mod_func
msg   'mod(', a, ', ', b, ') = ', d        ; output
end

; Mod function
mod_func:
    mov   c, a        ; temp1
    div   c, b
    mul   c, b
    mov   d, a        ; temp2
    sub   d, c
    ret
"""
i = Interpreter()
i.load_code(program)
i.naive_loop2(debug=False)
print(''.join(i.memory.return_value))



s = "'mod(', a, ', ', b, ') = ', d'"

res = []
stack = ''
collect = False
for char in s:
    if char == "'" and not collect:
        collect = True
    elif char == "'" and collect:
        collect = False
        res.append(''.join(stack))
        stack = []
    elif collect:
        stack += char
    elif char not in ', ':
        res.append(char)    


# jak widzisz ' to otwórz i zbieraj wszystko, jak widzisz znowu ' to zamknij
