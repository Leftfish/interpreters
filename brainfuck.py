from collections import defaultdict


class BrainfuckVM():
    def __init__(self):
        self.memory = defaultdict(int) # "unlimited" number of cells, each with one unsigned byte
        self.i_ptr = 0
        self.data_ptr = 0
        self.output_result = []
        self.input_buffer = []
        self.code = None
        self.jump_table = None # pre-calculated jump table

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

    def reset(self):
        self.memory = defaultdict(int)
        self.i_ptr = 0
        self.data_ptr = 0
        self.output_result = []
        self.input_buffer = []
        self.code = None
        self.jump_table = None

    def load_code(self, code):
        self.code = code

    def load_input(self, inp):
        self.input_buffer = [a for a in list(inp)]

    def __increment_data_ptr(self):
        self.data_ptr += 1

    def __decrement_data_ptr(self):
        self.data_ptr -= 1

    def __increment_value(self):
        if self.memory[self.data_ptr] == 255:
            self.memory[self.data_ptr] = 0
        else:
            self.memory[self.data_ptr] += 1

    def __decrement_value(self):
        if self.memory[self.data_ptr] == 0:
            self.memory[self.data_ptr] = 255
        else:
            self.memory[self.data_ptr] -= 1

    def __input_value(self):
        if self.input_buffer:
            self.memory[self.data_ptr] = ord(self.input_buffer.pop(0))

    def __output_value(self):
        self.output_result.append(self.memory[self.data_ptr])

    def __jump_if_zero(self):
        if self.memory[self.data_ptr] == 0:
            self.i_ptr = self.jump_table[self.i_ptr]

    def __jump_if_not_zero(self):
        if self.memory[self.data_ptr] != 0:
            self.i_ptr = self.jump_table[self.i_ptr]

    def __calculate_jump_table(self, code):
        loop_stack = []
        jump_table = [None] * len(code)
        for i, op in enumerate(code):
            if op == "[":
                loop_stack.append(i)
            elif op == "]":
                jump_table[i] = loop_stack.pop()
                jump_table[jump_table[i]] = i
        return jump_table

    def __exec_opcode(self, opcode):
        self.OPCODES[opcode]()

    def __EOF(self):
        return self.i_ptr >= len(self.code) 

    def run_program(self):
        self.jump_table = self.__calculate_jump_table(self.code)
        while not self.__EOF() :
            self.__exec_opcode(self.code[self.i_ptr])
            self.i_ptr += 1

        return self.output_result

if __name__ == "__main__":
    print("*" * 45)
    print("  My (very) simple Brainf*ck interpreter...")
    print("*" * 45)

    VM = BrainfuckVM()

    print("\nTEST 1: Hello world!" + "\n" + 45 * "-")
    code = '++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.'
    print("The code is: {}\n".format(code))
    VM.load_code(code)
    print("".join(list(map(chr, VM.run_program()))))

    VM.reset()

    print("\nTEST 2: 5 + 2 = ?" + "\n" + 45 * "-")
    code = '++>+++++[<+>-]++++++++[<++++++>-]<.'
    print("The code is: {}\n".format(code))
    VM.load_code(code)
    print("".join(list(map(chr, VM.run_program()))))

    VM.reset()

    print("\nTEST 3: print H4X0R from input" + "\n" + 45 * "-")
    code = ',+[-.,+]'
    inp = "H4X0R" + chr(255)
    print("The code is: {}\n".format(code))
    print("Input is: 'H4X0R' + chr(255)\n")
    VM.load_code(code)
    VM.load_input(inp)
    print("".join(list(map(chr, VM.run_program()))))
  
    VM.reset()

    print("\nTEST 4: translate chars in base2 to ASCII" + "\n" + 45 * "-")
    code = ">,[>>>++++++++[<[<++>-]<+[>+<-]<-[-[-<]>]>[-<]<,>>>-]<.[-]<<]"
    inp = "0100100001100101011011000110110001101111"
    print("The code is: {}\n".format(code))
    print("Input is: {}\n".format(inp))
    VM.load_code(code)
    VM.load_input(inp)
    print("".join(list(map(chr, VM.run_program()))))
