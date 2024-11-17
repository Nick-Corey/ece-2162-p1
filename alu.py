class Int_adder():

    def __init__(self, exec_cycles, fus):
        self.exec_cycles = exec_cycles
        self.fus = fus

        self.buffer = []

    def compute(self, rs):
        operation = rs.operation
        vj = rs.vj
        vk = rs.vk
        self.buffer.append((operation, vj, vk, 0))
        print(self.buffer)
        return

    def check_if_space(self):
        if len(self.buffer) < self.fus:
            return True
        else:
            return False

    def cycle(self):
        return_value = None
        for i, inst in enumerate(self.buffer):
            inst = (inst[0], inst[1], inst[2], inst[3] + 1)
            if (inst[3] == self.exec_cycles):
                if 'Add' in inst[0]:
                    return_value = inst[1] + inst[2]
                    self.buffer.pop(i)
                elif 'Sub' in inst[0]:
                    return_value = inst[1] - inst[2]
                    self.buffer.pop(i)
                else:
                    #Branch inststructions?
                    return_value = None
                    pass
        return return_value
