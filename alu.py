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
        #print(self.buffer)
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
        #print(self.buffer)
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
        #print(self.buffer)
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
    
class LD_SD():

    def __init__(self, exec_cycles, mem_cycles, fus):
        self.exec_cycles = exec_cycles
        self.mem_cycles = mem_cycles
        self.fus = fus

        self.buffer = []
        self.mem_buffer = []

    def compute(self, rs):
        operation = rs.operation
        vj = rs.vj
        a = rs.a
        id = rs.id
        self.buffer.append((operation, vj, a, 0, id))
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
                if 'Ld' in inst[0]:
                    return_value = int(inst[1] / 4) + inst[2]
                    rs_num = inst[4]
                    self.buffer.pop(i)
        return (return_value, rs_num)
    
    def check_if_mem_space(self):
        # using the same fus values... not sure if right
        if len(self.mem_buffer) < self.fus:
            return True
        else:
            return False
        
    def mem_buffer_size(self):
        return len(self.mem_buffer)

    def mem_compute(self, a, id):
        # (address, reservation station id, cycle number)
        self.mem_buffer.append((a, id, 0))
        print(self.buffer)
        return
    
    def mem_cycle(self, memory):
        return_value = None
        rs_num = None
        for i, inst in enumerate(self.mem_buffer):
            inst = (inst[0], inst[1], inst[2] + 1)
            if (inst[2] == self.mem_cycles):
                return_value = memory[int(inst[0])]
                rs_num = inst[1]
                self.mem_buffer.pop(i)
        return (return_value, rs_num)