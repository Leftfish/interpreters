from collections import defaultdict, deque

POSITIONAL_MODE = 0
IMMEDIATE_MODE = 1
RELATIVE_MODE = 2


class Operator:
    OP_CODE = 0
    OP_LEN = 0

    def __init__(self, computer):
        self.computer = computer
        self.ptr = computer.ptr
        self.args = [self.computer.memory[self.ptr+1+i] for i in range(self.OP_LEN-1)]
        self.modes = self.get_modes(self.args)

    def __repr__(self):
        status = ''
        status += f'Code: {self.OP_CODE}\n'
        status += f'Args: {self.args}\n'
        status += f'Modes: {self.modes}\n'
        return status

    def get_modes(self, args):
        raw_opcode = self.computer.memory[self.ptr]
        full_opcode = str(raw_opcode).zfill(5)
        params = list(map(int, full_opcode[:-2]))[::-1]
        return params

    def get_param(self, i):
        mode = self.modes[i]
        if mode == POSITIONAL_MODE:
            return self.computer.memory[self.args[i]]
        elif mode == IMMEDIATE_MODE:
            return self.args[i]
        elif mode == RELATIVE_MODE:
            return self.computer.memory[self.args[i] + self.computer.relative_base]

    def write(self, val):
        mode = self.modes[0] if self.OP_CODE == 3 else self.modes[-1]

        if mode == POSITIONAL_MODE:
            target = self.args[-1]
            self.computer.memory[target] = val
        elif mode == IMMEDIATE_MODE:
            raise ValueError('Cannot write in immediate mode!')
        elif mode == RELATIVE_MODE:
            target = self.args[-1]
            self.computer.memory[target + self.computer.relative_base] = val


class MathOperator(Operator):
    OP_LEN = 4

    def calculate(self, a, b):
        raise NotImplementedError

    def execute(self):
        a, b = self.get_param(0), self.get_param(1)
        val = self.calculate(a, b)
        self.write(val)


class OperatorAdd(MathOperator):
    OP_CODE = 1

    def calculate(self, a, b):
        return a + b


class OperatorMul(MathOperator):
    OP_CODE = 2

    def calculate(self, a, b):
        return a * b


class OperatorInp(Operator):
    OP_CODE = 3
    OP_LEN = 2

    def execute(self):
        val = self.computer.input.get()
        self.write(val)


class OperatorOut(Operator):
    OP_CODE = 4
    OP_LEN = 2

    def execute(self):
        val = self.get_param(0)
        self.computer.output.put(val)
        self.computer.last_operation_output = True


class OperatorJIT(Operator):
    OP_CODE = 5
    OP_LEN = 3

    def execute(self):
        if self.get_param(0):
            self.computer.ptr = self.get_param(1)
            self.computer.last_operation_jump = True


class OperatorJIF(Operator):
    OP_CODE = 6
    OP_LEN = 3

    def execute(self):
        if not self.get_param(0):
            self.computer.ptr = self.get_param(1)
            self.computer.last_operation_jump = True


class OperatorComp(Operator):
    OP_CODE = 7
    OP_LEN = 4

    def execute(self):
        a = self.get_param(0)
        b = self.get_param(1)
        if a < b:
            self.write(1)
        else:
            self.write(0)


class OperatorEquals(Operator):
    OP_CODE = 8
    OP_LEN = 4

    def execute(self):
        a = self.get_param(0)
        b = self.get_param(1)
        if a == b:
            self.write(1)
        else:
            self.write(0)


class OperatorChangeRelativeBase(Operator):
    OP_CODE = 9
    OP_LEN = 2

    def execute(self):
        val = self.get_param(0)
        self.computer.relative_base += val


class OperatorEOF(Operator):
    OP_CODE = 99
    OP_LEN = 1

    def execute(self):
        raise StopIteration


class InStream:
    def __init__(self):
        self.buffer = deque()

    def add(self, inp):
        self.buffer.append(inp)

    def get(self):
        if self.buffer:
            return self.buffer.popleft()
        else:
            raise RuntimeError('Cannot read from empty input.')


class OutStream:
    def __init__(self):
        self.buffer = []

    def put(self, val):
        self.buffer.append(val)

    def get(self):
        if self.buffer:
            return self.buffer.pop()
        else:
            raise RuntimeError('Cannot output from empty output stream.')


OP_DICTIONARY = {1: OperatorAdd,
                 2: OperatorMul,
                 3: OperatorInp,
                 4: OperatorOut,
                 5: OperatorJIT,
                 6: OperatorJIF,
                 7: OperatorComp,
                 8: OperatorEquals,
                 9: OperatorChangeRelativeBase,
                 99: OperatorEOF
                 }


class Computer():
    def __init__(self):
        self.memory = defaultdict(int)
        self.ptr = 0
        self.relative_base = 0
        self.last_operation_jump = False
        self.input = InStream()
        self.output = OutStream()
        self.running = False
        self.pause_at_output = False

    def __repr__(self):
        status = ''
        status += 'Pointer: {}\n'.format(self.ptr)
        status += 'Relative base: {}\n'.format(self.relative_base)
        status += 'InStream: {}\n'.format(self.input.buffer)
        status += 'Output: {}\n'.format(self.output.buffer)
        status += 'Memory dump: {}\n'.format(self.memory.values())
        if self.memory:
            status += str(self._get_current_op())
        return status

    def _get_current_op(self):
        opcode = self.memory[self.ptr] % 100
        return OP_DICTIONARY[opcode](self)

    def advance(self, op):
        self.ptr += op.OP_LEN

    def load_code(self, code):
        for i, val in enumerate(code):
            self.memory[i] = val

    def read_input(self, val):
        self.input.add(val)

    def get_output(self):
        return self.output.get()

    def reset(self):
        self.memory = defaultdict(int)
        self.ptr = 0
        self.relative_base = 0
        self.last_operation_jump = False
        self.input = InStream()
        self.output = OutStream()
        self.running = False
        self.pause_at_output = False

    def run(self, noun=0, verb=0, pause_at_output=False, debug=False):
        if noun:
            self.memory[1] = noun
        if verb:
            self.memory[2] = verb

        self.running = True

        while self.running:
            try:
                if debug:
                    print(self.__repr__())
                op = self._get_current_op()
                self.last_operation_jump = False
                self.last_operation_output = False
                op.execute()
                if not self.last_operation_jump:
                    self.advance(op)
                if pause_at_output and self.last_operation_output:
                    break

            except StopIteration:
                self.running = False
