class Int_adder():

    def __init__(self, exec_cycles, fus):
        self.exec_cycles = exec_cycles
        self.fus = fus

        self.buffer = []

    def compute(self, rs):
        operation = rs.operation
        vj = rs.vj
        vk = rs.vk
        id = rs.id
        # What is the zero???
        self.buffer.append((operation, vj, vk, 0, id))
        print(self.buffer)
        return

    def check_if_space(self):
        # This is maybe wrong? Probably not though
        if len(self.buffer) < self.fus:
            return True
        else:
            return False

    def cycle(self):
        return_value = None
        rs_num = None
        for i, inst in enumerate(self.buffer):
            inst = (inst[0], inst[1], inst[2], inst[3] + 1, inst[4])
            if (inst[3] == self.exec_cycles):
                if 'Add' in inst[0]:
                    return_value = inst[1] + inst[2]
                    rs_num = inst[4]
                    self.buffer.pop(i)
                elif 'Sub' in inst[0]:
                    return_value = inst[1] - inst[2]
                    rs_num = inst[4]
                    self.buffer.pop(i)
                else:
                    #Branch inststructions?
                    return_value = None
                    rs_num = None
                    pass
        return (return_value, rs_num)

class FP_Adder():

    def __init__(self, exec_cycles, fus):
        self.exec_cycles = exec_cycles
        self.fus = fus

        self.buffer = []

    def compute(self, rs):
        operation = rs.operation
        vj = rs.vj
        vk = rs.vk
        id = rs.id
        self.buffer.append((operation, vj, vk, 0, id))
        print(self.buffer)
        return

    def check_if_space(self):
        # This is wrong, needs to be pipelined
        if len(self.buffer) < self.fus:
            return True
        else:
            return False

    def cycle(self):
        return_value = None
        rs_num = None
        for i, inst in enumerate(self.buffer):
            inst = (inst[0], inst[1], inst[2], inst[3] + 1, inst[4])
            if (inst[3] == self.exec_cycles):
                if 'Add.d' in inst[0]:
                    return_value = inst[1] + inst[2]
                    rs_num = inst[4]
                    self.buffer.pop(i)
                elif 'Sub.d' in inst[0]:
                    return_value = inst[1] - inst[2]
                    rs_num = inst[4]
                    self.buffer.pop(i)
        return (return_value, rs_num)

class FP_Mult():

    def __init__(self, exec_cycles, fus):
        self.exec_cycles = exec_cycles
        self.fus = fus

        self.buffer = []

    def compute(self, rs):
        operation = rs.operation
        vj = rs.vj
        vk = rs.vk
        id = rs.id
        self.buffer.append((operation, vj, vk, 0, id))
        print(self.buffer)
        return

    def check_if_space(self):
        # This is wrong, needs to be pipelined
        if len(self.buffer) < self.fus:
            return True
        else:
            return False

    def cycle(self):
        return_value = None
        rs_num = None
        for i, inst in enumerate(self.buffer):
            inst = (inst[0], inst[1], inst[2], inst[3] + 1, inst[4])
            if (inst[3] == self.exec_cycles):
                if 'Mult.d' in inst[0]:
                    return_value = inst[1] * inst[2]
                    rs_num = inst[4]
                    self.buffer.pop(i)
        return (return_value, rs_num)