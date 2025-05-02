
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

class CALL(Operator):
    def execute(self):
        target = self.interpreter.program.label_table[self.args[0]]
        self.interpreter.call_stack.append(self.interpreter.instruction_ptr)
        self.interpreter.instruction_ptr = target

class RET(Operator):
    def execute(self):
        self.interpreter.instruction_ptr = self.interpreter.call_stack.pop()

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
        i = 0
        n = len(self.args)

        while i < n:
            if self.args[i] == "'":
                i += 1
                literal = ''
                while i < n and self.args[i] != "'":
                    literal += self.args[i]
                    i += 1
                i += 1
                params.append(literal)
            else:
                register = ''
                while i < n and self.args[i] != ',':
                    register += self.args[i]
                    i += 1
                if register:
                    params.append(str(self.interpreter.memory.registers[''.join(register)]))
            while i < n and (self.args[i] == ',' or self.args[i] == ' '):
                i += 1
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
        self.instructions, self.label_table = self.other_parse_code(code)

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
        self.call_stack = []

    def load_code(self, code):
        self.program = Program(code, self)

    def reset(self):
        self.memory = Memory()
        self.instruction_ptr = 0
        self.program = None
        self.running = False

        self.last_cmp_equal = None
        self.last_cmp_first_greater = None
        self.last_cmp_second_greater = None

        self.last_op_jmp = False
        self.call_stack = []

    def run_program(self, debug=True):
        self.running = True

        while self.running:
            try:
                self.last_op_jmp = False

                current_op = self.program.instructions[self.instruction_ptr]
                current_op.execute()

                if debug: print(f'After executing {current_op}. \tRegisters: ' +\
                                 str([f'{k}: {v}' for k, v in self.memory.registers.items()]) +\
                                      f'\t Stack: {str(self.call_stack)}')

                if not self.last_op_jmp:
                    self.instruction_ptr += 1

            except IndexError:
                if debug: print('Reached end of program without END instruction. Stopping.')
                self.running = False
                self.memory.return_value = ['-1']

TESTS = [
    
("Any program...",
'''
; My first program
mov  a, 5
inc  a
call function
msg  '(5+1)/2 = ', a    ; output message
end

function:
    div  a, 2
    ret
''', '(5+1)/2 = 3'),
    

("Factorial",
'''
mov   a, 5
mov   b, a
mov   c, a
call  proc_fact
call  print
end

proc_fact:
    dec   b
    mul   c, b
    cmp   b, 1
    jne   proc_fact
    ret

print:
    msg   a, '! = ', c ; output text
    ret
''', '5! = 120'),

("Fibonacci", '''
mov   a, 8            ; value
mov   b, 0            ; next
mov   c, 0            ; counter
mov   d, 0            ; first
mov   e, 1            ; second
call  proc_fib
call  print
end

proc_fib:
    cmp   c, 2
    jl    func_0
    mov   b, d
    add   b, e
    mov   d, e
    mov   e, b
    inc   c
    cmp   c, a
    jle   proc_fib
    ret

func_0:
    mov   b, c
    inc   c
    jmp   proc_fib

print:
    msg   'Term ', a, ' of Fibonacci series is: ', b        ; output text
    ret
''', 'Term 8 of Fibonacci series is: 21'),

('Modulo', '''
mov   a, 11           ; value1
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
''', 'mod(11, 3) = 2'),

('gcd', '''
mov   a, 81         ; value1
mov   b, 153        ; value2
call  init
call  proc_gcd
call  print
end

proc_gcd:
    cmp   c, d
    jne   loop
    ret

loop:
    cmp   c, d
    jg    a_bigger
    jmp   b_bigger

a_bigger:
    sub   c, d
    jmp   proc_gcd

b_bigger:
    sub   d, c
    jmp   proc_gcd

init:
    cmp   a, 0
    jl    a_abs
    cmp   b, 0
    jl    b_abs
    mov   c, a            ; temp1
    mov   d, b            ; temp2
    ret

a_abs:
    mul   a, -1
    jmp   init

b_abs:
    mul   b, -1
    jmp   init

print:
    msg   'gcd(', a, ', ', b, ') = ', c
    ret
''','gcd(81, 153) = 9'),

('Failing', '''
call  func1
call  print
end

func1:
    call  func2
    ret

func2:
    ret

print:
    msg 'This program should return -1'
''', -1),

('Power', '''
mov   a, 2            ; value1
mov   b, 10           ; value2
mov   c, a            ; temp1
mov   d, b            ; temp2
call  proc_func
call  print
end

proc_func:
    cmp   d, 1
    je    continue
    mul   c, a
    dec   d
    call  proc_func

continue:
    ret

print:
    msg a, '^', b, ' = ', c
    ret
''', '2^10 = 1024')
]

def tests():
    for test in (TESTS[2],):
        name, code, output = test
        print(f'Testing program called {name}.')
        comp = Interpreter()
        comp.load_code(code)
        comp.run_program(debug=True)
        res = ''.join(comp.memory.return_value)
        print(f'Expected: {output} Got: {res}. {output == res}')

tests()