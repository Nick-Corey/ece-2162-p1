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
        # a is for branch instructions exclusively
        a = rs.a
        self.buffer.append((operation, vj, vk, 0, id, a))
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
        address = None
        for i, inst in enumerate(self.buffer):
            inst = (inst[0], inst[1], inst[2], inst[3] + 1, inst[4], inst[5])
            self.buffer[i] = inst
            # For branch instructions
            address = inst[5]
            if (inst[3] == self.exec_cycles):
                if 'Add' in inst[0]:
                    return_value = inst[1] + inst[2]
                    rs_num = inst[4]
                    self.buffer.pop(i)
                elif 'Sub' in inst[0]:
                    return_value = inst[1] - inst[2]
                    rs_num = inst[4]
                    self.buffer.pop(i)
                elif 'Beq' in inst[0]:
                    return_value = (inst[1] == inst[2])
                    rs_num = inst[4]
                    self.buffer.pop(i)
                elif 'Bne' in inst[0]:
                    return_value = (inst[1] != inst[2])
                    rs_num = inst[4]
                    self.buffer.pop(i)
                else:
                    #return_value = None
                    #rs_num = None
                    pass
        if address is not None:
            return (return_value, rs_num, address)
        else:
            return (return_value, rs_num)
        
    def remove(self, id:str):
        # Remove an instruction from the alu
        for idx, entry in enumerate(self.buffer):
            if id in entry[4]:
                self.buffer.pop(idx)
                break

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
            self.buffer[i] = inst
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
    
    def remove(self, id:str):
    # Remove an instruction from the alu
        for idx, entry in enumerate(self.buffer):
            if id in entry[4]:
                self.buffer.pop(idx)
                break

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
            self.buffer[i] = inst
            if (inst[3] == self.exec_cycles):
                if 'Mult.d' in inst[0]:
                    return_value = inst[1] * inst[2]
                    rs_num = inst[4]
                    self.buffer.pop(i)
        return (return_value, rs_num)
    

    def remove(self, id:str):
        # Remove an instruction from the alu
        for idx, entry in enumerate(self.buffer):
            if id in entry[4]:
                self.buffer.pop(idx)
                break

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
        vk = rs.vk
        a = rs.a
        id = rs.id
        self.buffer.append((operation, vj, a, 0, id, vk))
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
        operation = None
        store_value = None
        for x, inst in enumerate(self.buffer):
            inst = (inst[0], inst[1], inst[2], inst[3] + 1, inst[4], inst[5])
            self.buffer[x] = inst
            if (inst[3] == self.exec_cycles):
                operation = inst[0]
                return_value = int(inst[1])
                rs_num = inst[4]
                store_value = inst[5]
                self.buffer.pop(x)
        return (return_value, rs_num, operation, store_value)

    def check_if_mem_space(self):
        # using the same fus values... not sure if right
        if len(self.mem_buffer) < self.fus:
            return True
        else:
            return False

    def mem_buffer_size(self):
        return len(self.mem_buffer)

    def mem_compute(self, a, id, oper, value):
        # (address, reservation station id, cycle number)
        self.mem_buffer.append((a, id, 0, oper, value))
        return

    def mem_cycle(self, memory, oper):
        return_value = None
        rs_num = None
        if 'Ld' in oper:
            for x, inst in enumerate(self.mem_buffer):
                if inst[3] == 'Ld':
                    inst = (inst[0], inst[1], inst[2] + 1, inst[3], inst[4])
                    self.mem_buffer[x] = inst
                    if (inst[2] == self.mem_cycles):
                        # Double check if should be divided by 4
                        return_value = memory[int(inst[0] / 4)]
                        rs_num = inst[1]
                        self.mem_buffer.pop(x)
                        return (return_value, rs_num, inst[3])
            #return (None, None, None)
        elif 'Sd' in oper:
            for x, inst in enumerate(self.mem_buffer):
                if inst[3] == 'Sd':
                    inst = (inst[0], inst[1], inst[2] + 1, inst[3], inst[4])
                    self.mem_buffer[x] = inst
                    if (inst[2] == self.mem_cycles):
                        memory[int(inst[0] / 4)] = inst[4]
                        rs_num = inst[1]
                        self.mem_buffer.pop(x)
                        return (memory, rs_num, inst[3])
            #return (None, None, None)
        else:
            return (None, None, None)
        
    def remove(self, id:str):
     # Remove an instruction from the alu
        for idx, entry in enumerate(self.mem_buffer):
            if id in entry[1]:
                self.mem_buffer.pop(idx)
                break

class NOP():

    def __init__(self):
        self.exec_cycles = 1
        self.fus = 1

        self.buffer = []

    def compute(self, rs):
        operation = rs.operation
        vj = None
        vk = None
        id = rs.id
        self.buffer.append((operation, vj, vk, 0, id))
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
            self.buffer[i] = inst
            if (inst[3] == self.exec_cycles):
                return_value = True
                rs_num = inst[4]
                self.buffer.pop(i)
        return (return_value, rs_num)
    
    def remove(self, id:str):
        # Remove an instruction from the alu
        for idx, entry in enumerate(self.buffer):
            if id in entry[4]:
                self.buffer.pop(idx)
                break