import sys
from collections import defaultdict, deque


class Memory:
    def __init__(self, cell_size_bits):
        self.registers = defaultdict(int)  # "unlimited" number of cells
        self.cell_size = 2 ** cell_size_bits # default setting: one unsigned byte per cell
        self.data_ptr = 0

    def move(self, n):
        self.data_ptr += n

    def increment(self):
        self.registers[self.data_ptr] = (self.registers[self.data_ptr] + 1) % self.cell_size

    def decrement(self):
        self.registers[self.data_ptr] = (self.registers[self.data_ptr] - 1) % self.cell_size

    def store(self, inp):
        self.registers[self.data_ptr] = ord(inp)
    
    def get_current(self):
        return self.registers[self.data_ptr]


class InStream:
    def __init__(self):
        self.buffer = deque()

    def add(self, inp):
        for val in list(inp):
            self.buffer.append(val)

    def get(self):
        return self.buffer.popleft() if self.buffer else None


class OutStream:
    def put(self, val):
        sys.stdout.write(chr(val))
        sys.stdout.flush()


class Program:
    def __init__(self, code=None):
        self.code = code
        self.i_ptr = 0
        self.jump_table = self.__calculate_jump_table()

    def __calculate_jump_table(self):
        loop_stack = []
        jump_table = [None] * len(code)
        for i, op in enumerate(code):
            if op == "[":
                loop_stack.append(i)
            elif op == "]":
                jump_table[i] = loop_stack.pop()
                jump_table[jump_table[i]] = i
        return jump_table

    def load_code(self, code):
        self.code = code
        self.jump_table = self.__calculate_jump_table()

    def get_opcode(self):
        return self.code[self.i_ptr]

    def current(self):
        return self.i_ptr

    def advance(self):
        self.i_ptr += 1

    def jump(self):
        self.i_ptr = self.jump_table[self.i_ptr]

    def eof(self):
        return self.i_ptr >= len(self.code)


class BrainfuckVM:
    def __init__(self, code=None, bits=8):
        self.bits = bits
        self.memory = Memory(cell_size_bits=bits)
        self.in_stream = InStream()
        self.out_stream = OutStream()
        self.program = Program(code) if code else None

        self.OPCODES = {
            ">": self.__increment_data_ptr,
            "<": self.__decrement_data_ptr,
            "+": self.__increment_value,
            "-": self.__decrement_value,
            ",": self.__input_value,
            ".": self.__output_value,
            "[": self.__jump_if_zero,
            "]": self.__jump_if_not_zero
        }

    def __increment_data_ptr(self):
        self.memory.move(+1)

    def __decrement_data_ptr(self):
        self.memory.move(-1)

    def __increment_value(self):
        self.memory.increment()

    def __decrement_value(self):
        self.memory.decrement()

    def __input_value(self):
        value = self.in_stream.get()
        if value:
            self.memory.store(value)

    def __output_value(self):
        self.out_stream.put(self.memory.get_current())

    def __jump_if_zero(self):
        if not self.memory.get_current():
            self.program.jump()

    def __jump_if_not_zero(self):
        if self.memory.get_current():
            self.program.jump()

    def __exec_opcode(self, opcode):
        self.OPCODES[opcode]()

    def reset(self, code=None):
        self.memory = Memory(cell_size_bits=self.bits)
        self.in_stream = InStream()
        self.out_stream = OutStream()
        self.program = Program(code) if code else None

    def load_code(self, code):
        self.program = Program(code)

    def load_input(self, inp):
        self.in_stream.add(inp)

    def run_program(self):
        while not self.program.eof():
            self.__exec_opcode(self.program.get_opcode())
            self.program.advance()
        return 0

if __name__ == "__main__":
    print("*" * 45)
    print("  My (very) simple Brainf*ck interpreter...")
    print("*" * 45)

    VM = BrainfuckVM()

    print("\nTEST 1: print Hello world!" + "\n" + 45 * "-")
    code = '++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.'
    print("The code is: {}\n".format(code))
    VM.load_code(code)
    VM.run_program()

    VM.reset()

    print("\nTEST 2: 5 + 2 = ?" + "\n" + 45 * "-")
    code = '++>+++++[<+>-]++++++++[<++++++>-]<.'
    print("The code is: {}\n".format(code))
    VM.load_code(code)
    VM.run_program()

    VM.reset()

    print("\n\nTEST 3: print H4X0R from input" + "\n" + 45 * "-")
    code = ',+[-.,+]'
    inp = "H4X0R" + chr(255)
    print("The code is: {}\n".format(code))
    print("Input is: 'H4X0R' + chr(255)\n")
    VM.load_code(code)
    VM.load_input(inp)
    VM.run_program()

    VM.reset()

    print("\n\nTEST 4: translate chars in base2 to ASCII" + "\n" + 45 * "-")
    code = ">,[>>>++++++++[<[<++>-]<+[>+<-]<-[-[-<]>]>[-<]<,>>>-]<.[-]<<]"
    inp = "0100100001100101011011000110110001101111"
    print("The code is: {}\n".format(code))
    print("Input is: {}\n".format(inp))
    VM.load_code(code)
    VM.load_input(inp)
    VM.run_program()
