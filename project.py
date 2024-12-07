import json
import numpy as np
import copy
from tabulate import tabulate
import reservation_station
from alu import Int_adder, FP_Adder, FP_Mult, LD_SD, NOP
from cdb import CommonDataBus
from timetable import timetable
from reorderbuffer import ReorderBuffer
from branchpredictor import BranchPredictor

input_file = 'input_6.json'

# Create Memory and Register arrays
Memory = [0] * 32
Int_Registers = [0] * 32
Float_Registers = [0.0] * 32
Instruction_Buffer = []
int_rs_size = 0
fp_adder_rs_size = 0
fp_mult_rs_size = 0
load_store_rs_size = 0
nop_rs_size = 0
int_rs = []
fp_adder_rs = []
fp_mult_rs = []
load_store_rs = []
nop_rs = []

# TODO: allow for dynamic size CDB
cdb = CommonDataBus(1)
rat = []
load_store_queue = []
cdb_queue = []

# These get passed to writeback stage
values          = []
values_p        = []
mem_value       = []
mem_value_p     = []

# Create time table
timeTable = timetable()

# Create ROB
rob = ReorderBuffer()

# Create Branch Predictor
bp = BranchPredictor()

# Copies for BP
int_rs_copy = []
fp_adder_rs_copy = []
fp_mult_rs_copy = []
load_store_rs_copy = []
rat_copy = []
Int_Registers_Copy = []
Float_Registers_Copy = []
PC_Copy = 0
rob_copy = None
timeTable_Copy = None
mispredict = False

# Program counter and program storage in memory
total_instructions = 0 # Used for nice formatting of time table
PC = 0
instruction_memory = []

# Creating headers for Output tables
Int_Registers_Names = [''] * 32
Float_Registers_Names = [''] * 32
i = 0
while i < 32:
    Int_Registers_Names[i] = "R" + str(i)
    Float_Registers_Names[i] = "F" + str(i)
    i = i + 1

def initalize():
    global Int_fu, int_rs_size, FP_adder_fu, fp_adder_rs_size, fp_mult_rs_size, FP_mult_fu, LD_SD_fu, load_store_rs_size, nop_rs, nop_rs_size, Nop_fu
    # Open test case file
    with open(f"TestCases/{input_file}") as test_file:
        specs = json.load(test_file)
        # Read in parameters for memory initlization and initialize
        for mem in specs["specifications"]["Memory"]:
            index = int(int(mem["name"]) / 4)
            value = float(mem["value"])
            Memory[index] = value
        # Read in parameters for Register initialization and initialize
        for reg in specs["specifications"]["Registers"]:
            name = reg["name"]
            # Check if register is Int or Float and load into appopriate register
            if "R" in name:
                value = int(reg["value"])   
                Int_Registers[int(name[1:])] = value
            if "F" in name:  
                value = float(reg["value"])
                Float_Registers[int(name[1:])] = value
        # Read in parameters for Operations
        for operation in specs["specifications"]["operations"]:
            if 'Integer Adder' in operation['name']:
                int_rs_size = operation['reservation_station_num']
                Int_fu = Int_adder(operation['EX cycles'], operation['FUs'])
            if 'FP Adder' in operation['name']:
                fp_adder_rs_size = operation['reservation_station_num']
                FP_adder_fu = FP_Adder(operation['EX cycles'], operation['FUs'])
            if 'FP Multiplier' in operation['name']:
                fp_mult_rs_size = operation['reservation_station_num']
                FP_mult_fu = FP_Mult(operation['EX cycles'], operation['FUs'])
            if 'Load/Store Unit' in operation['name']:
                load_store_rs_size = operation['reservation_station_num']
                LD_SD_fu = LD_SD(operation['EX cycles'], operation['mem_cycles'], operation['FUs'])
        Nop_fu = NOP()
        for instruction in specs["specifications"]["Instructions"]:
            instruction_memory.append(instruction["value"])
            #Instruction_Buffer.append(instruction["value"])

        #Initalize Time Table
        timeTable.resize(1000)

        #Initalize ROB to correct size
        rob.resize(specs["specifications"]["ROB entries"])

        #Initialize Branch Predictor
        bp.initializePredictions(instruction_memory)

    return
    

def output():
    global Memory, int_rs, timeTable, total_instructions


    print(Instruction_Buffer)
    
    # Converting memory to numpy array to utilize nonzero() function
    mem = np.array(Memory)
    non_zero = np.nonzero(mem)

    # Create headers for memory output
    mem_headers = list(non_zero[0])
    mem_headers = ["Mem[" + str(i * 4) + "]" for i in mem_headers]

    # Output Memory
    print(tabulate([mem[non_zero]], mem_headers, tablefmt="simple_grid"))
    print(tabulate([Int_Registers], Int_Registers_Names, tablefmt="simple_grid"))
    print(tabulate([Float_Registers], Float_Registers_Names, tablefmt="simple_grid"))

    for rs in int_rs:
        print(rs)
    for rs in fp_adder_rs:
        print(rs)
    print(fp_mult_rs)
    # print(load_store_rs)
    for rs in load_store_rs:
        print(rs)
    print(nop_rs)
    print(rat)

    # Print timetable
    timeTable.resize(total_instructions)
    print(timeTable)

# RS are currently dyanically pushed and popped into a list
# in order to create a value which can allow an RS to be referenced
# I am using the cycle number... This may need to be change later 
def issue():
    global int_rs, fp_adder_rs, PC, instruction_memory, total_instructions
    global Int_fu, int_rs, fp_adder_rs, FP_adder_fu, nop_rs, fp_mult_rs, load_store_rs, Nop_fu, PC, bp, Instruction_Buffer, total_instructions, rat, Int_Registers, Float_Registers
    global int_rs_copy, fp_adder_rs_copy, fp_mult_rs_copy, load_store_rs_copy, rat_copy, Int_Registers_Copy, Float_Registers_Copy, PC_Copy, rob_copy, mispredict, timeTable, timeTable_Copy

    instruction_type = ""
    value1 = None
    value2 = None

    print('PC: ', PC)
    print(Instruction_Buffer)
    mispredict = False

    # Load instruction from memory and place onto instruction buffer for issuing
    if PC < len(instruction_memory):
        Instruction_Buffer.append(instruction_memory[PC])
        PC = PC + 1 # Increment program counter

    # If no instructions left - nothing to issue - exit
    if not Instruction_Buffer or len(Instruction_Buffer) == 0:
        return

    # Get next instruction for Instruction Buffers
    instruction = Instruction_Buffer[0].capitalize()
    instruction = instruction.replace(",", "")
    instruction_parts = instruction.split(" ")

    # Find Free Reservation Station
    operation = instruction_parts[0]

    if "Add.d" in operation or "Sub.d" in operation:
        instruction_type = "fp"
        if len(fp_adder_rs) <= fp_adder_rs_size:
            rs = reservation_station.Reservation_Station("AD", i)
        else:
            # Stall?
            return
    elif "Add" in operation or "Sub" in operation or "Addi" in operation:
        instruction_type = "int"
        if len(int_rs) < int_rs_size:
            rs = reservation_station.Reservation_Station("AI", i)
        else:
            # Stall?
            return
    elif "Mult.d" in operation:
        instruction_type = "fp"
        if len(fp_mult_rs) < fp_mult_rs_size:
            rs = reservation_station.Reservation_Station("ML", i)
        else:
            # Stall?
            return
    elif "Ld" in operation or "Sd" in operation:
        instruction_type = "fp"
        if len(load_store_rs) < load_store_rs_size:
            rs = reservation_station.Reservation_Station("LD", i)
        else:
            # Stall?
            return
    elif "Beq" in operation or "Bne" in operation:
        instruction_type = "br"
        if len(int_rs) < int_rs_size:
            rs = reservation_station.Reservation_Station("AI", i)
        else:
            # Stall?
            return
    elif "NOP" in operation:
        rs = reservation_station.Reservation_Station("NO", i)
        rob.insert(rs.id)
        rs.operation = "nop"
        nop_rs.append(rs)

        # Add to counter for table resizing later
        total_instructions = total_instructions + 1
        # Add issued instruction to the time table
        timeTable.add_instruction(rs.id, instruction, i)
        Instruction_Buffer.pop(0)
        return



    # Get Destination Register
    destination = instruction_parts[1]

    # Read Operands from Register File
    operand1 = instruction_parts[2]

    if 'Ld' not in operation and 'Sd' not in operation and 'Bne' not in operation and 'Beq' not in operation:
        operand2 = instruction_parts[3]

        #Search RAT for dependencies
        for entry in rat:
            if operand1 in entry[0]:
                value1 = entry[1]
            if operand2 in entry[0]:
                value2 = entry[1]
    
    if "Addi" in operation:
        if value1 is None:
            value1 = Int_Registers[int(operand1[1:])] 
        value2 = int(operand2)
    elif "Add.d" in operation or "Add" in operation or "Mult.d" in operation or "Sub.d" in operation or "Sub" in operation:
        if "int" in instruction_type:
            if value1 is None:
                value1 = Int_Registers[int(operand1[1:])] 
            if value2 is None:
                value2 = Int_Registers[int(operand2[1:])]

        if "fp" in instruction_type:
            if value1 is None:
                value1 = Float_Registers[int(operand1[1:])] 
            if value2 is None:
                value2 = Float_Registers[int(operand2[1:])] 
    elif "Ld" in operation:
        # Ld F4, 8(R1)
        parts = operand1.replace(')', '').split('(') 
        reg = parts[1]
        offset = int(parts[0])
        if value1 is None:
            value1 = Int_Registers[int(reg[1:])] 
    elif "Sd" in operation:
        # Ld F4, 8(R1)
        parts = operand1.replace(')', '').split('(') 
        reg = parts[1]
        offset = int(parts[0])
        if value1 is None:
            value1 = Int_Registers[int(reg[1:])] 
        if value2 is None:
            value2 = Float_Registers[int(destination[1:])] 
    elif "Bne" in operation or "Beq" in operation:
        operand1 = instruction_parts[1]
        operand2 = instruction_parts[2]
        branch_address = instruction_parts[3]
        #Search RAT for dependencies
        for entry in rat:
            if operand1 in entry[0]:
                value1 = entry[1]
            if operand2 in entry[0]:
                value2 = entry[1]

        if value1 is None:
            value1 = Int_Registers[int(operand1[1:])] 
        if value2 is None:
            value2 = Int_Registers[int(operand2[1:])]

    # Record Source of other operands

    # TODO: Might need to add logic for duplicate RAT entries (WAW)
    # Update source mapping (RAT)
    # (destination, rs_num)
    if 'br' not in instruction_type:
        rat.append((destination, rs.id))

    # Place values in RS
    rs.operation = operation

    if 'Ld' in operation:
        #TODO Register renaming for LD???
        rs.a = value1
        rs.vj = offset
    elif 'Sd' in operation:
        #TODO Register renaming for SD
        rs.a = value1
        rs.vj = offset
        #rs.vk = value2
        if type(value2) == type("value"):
            rs.qk = value2
        else:
            rs.vk = value2
    # Check if the value is a string or a number
    elif 'Beq' in operation or 'Bne' in operation:
        rs.a = branch_address
        if type(value1) == type("value"):
            rs.qj = value1
        else:
            rs.vj = value1
        if type(value2) == type("value"):
            rs.qk = value2
        else:
            rs.vk = value2

    else:
        # Check if the value is a string or a number
        if type(value1) == type("value"):
            rs.qj = value1
        else:
            rs.vj = value1
        if type(value2) == type("value"):
            rs.qk = value2
        else:
            rs.vk = value2

    if "Add.d" in operation or "Sub.d" in operation:
        fp_adder_rs.append(rs)
    elif "Add" in operation or "Sub" in operation or "Addi" in operation or "Bne" in operation or "Beq" in operation:
        int_rs.append(rs)
    elif "Mult.d" in operation:
        fp_mult_rs.append(rs)
    elif "Ld" in operation or "Sd" in operation:
        load_store_rs.append(rs)
    else:
        print('why are you here?')

    # Insert Instruction into the ROB
    rob.insert(rs.id)
    # Add to counter for table resizing later
    total_instructions = total_instructions + 1

    # Add issued instruction to the time table
    timeTable.add_instruction(rs.id, instruction, i)
    Instruction_Buffer.pop(0)

    # Branch predictor:
    if 'Beq' in operation or 'Bne' in operation:
        # Use branch predictor to predict result of branchinstruction
        bp.addBTB(instruction, PC-1)
        prediction = bp.predict(int(PC-1))
        print('prediction:', prediction, PC-1)
        bp.addHistory(rs.id, prediction)
        if prediction:
            # Copy RS, RAT, RF, etc
            # May want to append to list?
            int_rs_copy = copy.deepcopy(int_rs)
            fp_adder_rs_copy = copy.deepcopy(fp_adder_rs)
            fp_mult_rs_copy = copy.deepcopy(fp_mult_rs)
            load_store_rs_copy = copy.deepcopy(load_store_rs)
            rat_copy = copy.deepcopy(rat)
            Int_Registers_Copy = copy.deepcopy(Int_Registers)
            Float_Registers_Copy = copy.deepcopy(Float_Registers)
            PC_Copy = PC-1
            rob_copy = copy.deepcopy(rob)
                                     
            timeTable_Copy = copy.deepcopy(timeTable)

            # Update PC
            # Not sure if it should be PC or PC-1
            new_pc = (PC-1) + int(branch_address)
            PC = new_pc


        else:
            # Do thing
            pass

    return

def execute():
    global Int_fu, int_rs, fp_adder_rs, FP_adder_fu, nop_rs, fp_mult_rs, load_store_rs, Nop_fu, PC, bp, Instruction_Buffer, total_instructions, rat, Int_Registers, Float_Registers, timeTable, rob
    global int_rs_copy, fp_adder_rs_copy, fp_mult_rs_copy, load_store_rs_copy, rat_copy, Int_Registers_Copy, Float_Registers_Copy, PC_Copy, rob_copy, mispredict, timeTable_Copy

    
    # Execution Stage
    pass

    for rs in nop_rs:
        # Cannot execute and issue on same cycle - comapare with time table

        instruction_row = timeTable.getrowindexfromID(rs.id)
        if not (timeTable.table[instruction_row][timeTable.issue_loc] != i): continue
        if not (rs.busy == False)                                          : continue
        if not (Nop_fu.check_if_space())                                   : continue

        # All conditions met - begin execution
        rs.busy = True
        Nop_fu.compute(rs)


        # Record execution in timetable
        timeTable.add_execution(rs.id, i, 1)

    # Integer Reservation Stations
    for rs in int_rs:
        # Cannot execute and issue on same cycle - comapare with time table
        # Cannot execute without all operands ready
        # Cannot execute if functional unit is busy
        instruction_row = timeTable.getrowindexfromID(rs.id)
        if not (timeTable.table[instruction_row][timeTable.issue_loc] != i): continue
        if not (rs.busy == False and rs.vj != None and rs.vk != None)      : continue
        if not (Int_fu.check_if_space())                                   : continue

        # All conditions met - begin execution
        Int_fu.compute(rs)
        rs.busy = True

        # Record execution in timetable
        timeTable.add_execution(rs.id, i, Int_fu.exec_cycles)
                
    # FP Add Reservation Stations
    for rs in fp_adder_rs:
        # Cannot execute and issue on same cycle - comapare with time table
        # Cannot execute without all operands ready
        # Cannot execute if functional unit is busy #TODO - pipelined!!!!!
        instruction_row = timeTable.getrowindexfromID(rs.id)
        if not (timeTable.table[instruction_row][timeTable.issue_loc] != i): continue
        if not (rs.busy == False and rs.vj != None and rs.vk != None)      : continue
        if not (FP_adder_fu.check_if_space())                              : continue

        # Begin Execution
        FP_adder_fu.compute(rs)
        rs.busy = True

        # Record execution in timetable
        timeTable.add_execution(rs.id, i, FP_adder_fu.exec_cycles)

    # FP Mult Reservation Stations
    for rs in fp_mult_rs:
        # Cannot execute and issue on same cycle - comapare with time table
        # Cannot execute without all operands ready
        # Cannot execute if functional unit is busy #TODO - pipelined!!!!!
        instruction_row = timeTable.getrowindexfromID(rs.id)
        if not (timeTable.table[instruction_row][timeTable.issue_loc] != i): continue
        if not (rs.busy == False and rs.vj != None and rs.vk != None)      : continue
        if not (FP_mult_fu.check_if_space())                              : continue

        # Begin Execution
        FP_mult_fu.compute(rs)
        rs.busy = True

        # Record execution in timetable
        timeTable.add_execution(rs.id, i, FP_mult_fu.exec_cycles)

    # Load Store Reservation Stations
    for rs in load_store_rs:
        # Cannot execute and issue on same cycle - comapare with time table
        # Cannot execute without all operands ready
        # Cannot execute if functional unit is busy #TODO - pipelined!!!!!
        instruction_row = timeTable.getrowindexfromID(rs.id)
        if not (timeTable.table[instruction_row][timeTable.issue_loc] != i): continue
        if not (rs.busy == False and rs.vj != None and rs.a != None)      : continue
        if not (LD_SD_fu.check_if_space())                              : continue

        # Begin Execution
        LD_SD_fu.compute(rs)
        rs.busy = True

        # Record execution in timetable
        timeTable.add_execution(rs.id, i, LD_SD_fu.exec_cycles)

    # Cycle functional units
    int_value = Int_fu.cycle()
    fp_adder_value = FP_adder_fu.cycle()
    fp_mult_value = FP_mult_fu.cycle()
    ld_sd_value = LD_SD_fu.cycle()
    nop_value = Nop_fu.cycle()
    # TODO: add support for CDB of multiple sizes

    # Logic for branch instructions
    # If there is a return address 

    # When doing branches use timeTable.remove to remove mispredicted entry row in the table
    # Make sure to decrement the instruction counter, total_instructions = total_instructions - 1
    # We must delay a cycle as well and clean bad values
    # So when we take a branch - make a copy of registers, reservation stations, etc so that we can rollback
    # We can undo some values with logic or we can take a snap shot of everything and rollback (cant snapshot everything in hardware, but probably easier to implement in software)
    if len(int_value) > 2:

        result = int_value[0]
        rs_id = int_value[1]
        address = int_value[2]

        if result:
            #Update Predictor    
            # x = bp.getBTB(PC-1)
            # print('btb value: ', x)
            # print(PC, bp.btb)

            # Check if the branch predictor was correct and adjust accordingly
            taken = bp.searchHistory(rs_id)
            if taken:
                pass
            else:
                # Update PC to execute branch instruction
                PC = PC-1 + int(address)
                print(PC)
                # Update branch predictor    
                bp.updatePrediction(1, False)
                print(bp.bp)
        else:
            taken = bp.searchHistory(rs_id)
            if taken:
                print('before \n' ,rob)
                PC = PC_Copy
                print('MISPREDICT:', PC_Copy)
                int_rs = int_rs_copy
                fp_adder_rs = fp_adder_rs_copy
                fp_mult_rs = fp_mult_rs_copy
                load_store_rs = load_store_rs_copy
                rat = rat_copy
                Int_Registers = Int_Registers_Copy
                Float_Registers = Float_Registers_Copy
                PC_Copy = PC-1
                Instruction_Buffer = []
                total_instructions = total_instructions - 1
                timeTable = timeTable_Copy
                rob = rob_copy
                mispredict = True

                # Update branch predictor    
                bp.updatePrediction(1, False)

                print('after \n', rob)

            pass
        
        for idx, rs in enumerate(int_rs):
            if rs_id in rs.id:
                int_rs.pop(idx)
                rob.markComplete(rs_id)

        #Update Predictor
        

        int_value = (None, None)


    # print(nop_value)
    # for rs in nop_rs:
    #     print(rs)

    return [int_value, fp_adder_value, fp_mult_value, nop_value], ld_sd_value

def memory(value):
    global load_store_queue

    new_value = []
    # Memory Stage 

    # if not (value[0] != None and value[1] != None and value[2] == "Ld"):
    #     if len(load_store_queue):
    #         value = load_store_queue.pop()
    if value[0] != None and value[1] != None and value[2] == "Ld":
        load_store_queue.append((value[0], value[1], 'Ld', value[3]))

    if len(load_store_queue):
        if LD_SD_fu.check_if_mem_space():
            # value equal to ???
            inst = load_store_queue[0]
            if inst[2] == 'Ld':
                LD_SD_fu.mem_compute(inst[0], inst[1], inst[2], inst[3])
                load_store_queue.pop()
    # elif value[0] != None and value[1] != None and value[2] == "Ld":
    #     if LD_SD_fu.check_if_mem_space():
    #         # value equal to ???
    #         LD_SD_fu.mem_compute(value[0], value[1], 'Ld', value[3])
    #     else:
    #         load_store_queue.append((value[0], value[1], 'Ld', value[3]))


    if LD_SD_fu.mem_buffer_size():
        new_value = LD_SD_fu.mem_cycle(Memory, 'Ld')
        if new_value and new_value[1]:
            timeTable.add_memory(new_value[1], i+2, LD_SD_fu.mem_cycles)
    if not new_value:
        new_value = []
    return new_value

def write():
    global values_p, values, mem_value_p, mem_value
    # Values[n] corresponds to entries on the buffer
    # Values[n][0] is the entries' data
    # Values[n][1] is the entries' instruction id

    global Int_Registers, int_rs, rat, Float_Registers, fp_adder_rs, fp_mult_rs, load_store_rs, nop_rs, cdb, cdb_queue

    # Update these variables later
    writeBack = False
    writeback_instruction_id = None

    # Experimental

    for value in values:
        if value[0] is not None and value[1] is not None:
            cdb_queue.append(value)
    if mem_value:
        if mem_value[0] is not None and mem_value[1] is not None and mem_value[2] == 'Ld':
            cdb_queue.append(mem_value)

    #print(cdb_queue)
    # Broadcast on CDB
    # TODO -------------------------------------------------------- 
    # CDB should be updated
    # We should be able to append data items to item up until it is full via an insert function (looks like broadcast but the name is deceiving)
    # We should actaully broadcast the data to all the reservation stations and ROB entries when the singular writeback element is popped off
    # -- ie - insert data into the buffer, broadcast results to other structures when we pop the one off (it will only every be one at a time)
    # We can add multiple items to the buffer at a time (if they finish executing at the same time and there is space) but only one will ever be broadcasted


    # Checking if load/store forwarding occured
    if cdb.hasData():
        writeBack = True
    else:
        #TODO ---------------------------------------------------------
        #  we really shouldnt have this control loop right here - at most we will only every writeback one instruction
        # Our buffer has varying size, but we only ever writeback one instruction. Can discuss
        for idx, value in enumerate(cdb_queue):
            result = value[0]
            cdb_instruction_id = value[1]
            # if there is data to broadcast
            if result != None and cdb_instruction_id != None:
                writeBack = True
                if cdb.broadcast(result, cdb_instruction_id):
                    rob.markComplete(cdb_instruction_id)
                    cdb_queue.pop(idx)
                    
        # if mem_value:
        #     if mem_value[0] != None and mem_value[1] != None:
        #         if "Ld" in mem_value[2]:
        #             cdb.broadcast(mem_value[0], mem_value[1])
        #             rob.markComplete(mem_value[1])

    # WriteBack first piece of data on CDB from CDB
    if cdb.hasData():

        cdb_data_item = cdb.pop()
        result = cdb_data_item[0]
        cdb_instruction_id = cdb_data_item[1]

        # If NOP -------------------------------------
        if 'NO' in cdb_instruction_id:
            writeback_instruction_id = nop_rs[0].id
            nop_rs.pop(0)
            cdb.pop()



        # If Integer Add -------------------------------------
        if 'AI' in cdb_instruction_id:
            #Free Reservation Station
            for x, rs in enumerate(int_rs):
                if rs.id == cdb_instruction_id:
                    writeback_instruction_id = rs.id 

                    #Update register file and RAT
                    for j, entry in enumerate(rat):

                        register_name = entry[0]
                        instruction_id = entry[1]

                        # This is writing back when it should not be - must find why - check debug when i=6
                        if instruction_id == rs.id:
                            reg = register_name
                            # Its these functions here - they are replacing when shouldnt
                            # Intruction id  AI3 and rs.id == AI3 but it replaces value in AI5 reservation station
                            int_rs = searchRS(rs.id, result, int_rs)
                            fp_mult_rs = searchRS(rs.id, result, fp_mult_rs)
                            fp_adder_rs = searchRS(rs.id, result, fp_adder_rs)
                            rat.pop(j)
                            Int_Registers[int(reg[1:])] = result
                    int_rs.pop(x)
                    cdb.pop()

        # If FP Add      ----------------------------------------
        elif 'AD' in cdb_instruction_id:
            #Free Reservation Station
            for x, rs in enumerate(fp_adder_rs):
                if rs.id == cdb_instruction_id:
                    writeback_instruction_id = rs.id 

                    #Update register file and RAT
                    for j, entry in enumerate(rat):

                        register_name = entry[0]
                        instruction_id = entry[1]

                        if instruction_id == rs.id:
                            reg = register_name
                            fp_adder_rs = searchRS(rs.id, result, fp_adder_rs)
                            fp_mult_rs = searchRS(rs.id, result, fp_mult_rs)
                            rat.pop(j)
                            Float_Registers[int(reg[1:])] = result
                    fp_adder_rs.pop(x)
                    cdb.pop()

        # If FP Mult      ----------------------------------------
        elif 'ML' in cdb_instruction_id:
            #Free Reservation Station
            for x, rs in enumerate(fp_mult_rs): 
                if rs.id == cdb_instruction_id:
                    writeback_instruction_id = rs.id
                    #Update register file and RAT
                    for j, entry in enumerate(rat):

                        register_name = entry[0]
                        instruction_id = entry[1]

                        if instruction_id == rs.id:
                            reg = register_name
                            fp_mult_rs = searchRS(rs.id, result, fp_mult_rs)
                            fp_adder_rs = searchRS(rs.id, result, fp_adder_rs)
                            rat.pop(j)
                            Float_Registers[int(reg[1:])] = result
                    fp_mult_rs.pop(x)
                    cdb.pop()
        elif 'LD' in cdb_instruction_id:
            #Free Reservation Station
            for x, rs in enumerate(load_store_rs):

                if rs.id == cdb_instruction_id and rs.operation == "Ld":
                    writeback_instruction_id = rs.id
                    #Update register file and RAT
                    for j, entry in enumerate(rat):

                        register_name = entry[0]
                        instruction_id = entry[1]

                        if instruction_id == rs.id:
                            reg = register_name
                            fp_mult_rs = searchRS(rs.id, result, fp_mult_rs)
                            fp_adder_rs = searchRS(rs.id, result, fp_adder_rs)
                            rat.pop(j)
                            Float_Registers[int(reg[1:])] = result
                    load_store_rs.pop(x)
                    cdb.pop()
        pass            
    # Writeback to RF

    # Updating Mapping

    # Free Reservation Station

    # We pipeline data by a cycle so that execution and writeback occur on different cycles
    values    = values_p[:]
    mem_value = mem_value_p[:]

    # Update Timetable - only if good data on CDB
    if writeBack:
        timeTable.add_writeback(writeback_instruction_id, i)

    return

def commit(mem_value):
    global load_store_rs, LD_SD_fu, Float_Registers, Memory, load_store_queue, cdb, timeTable, mispredict
    #Store instruction

    if mem_value[0] != None and mem_value[1] != None and mem_value[2] == "Sd":
        load_store_queue.append((mem_value[0], mem_value[1], mem_value[2], mem_value[3]))

    if len(load_store_queue):
        if LD_SD_fu.check_if_mem_space():
            
            inst = load_store_queue[0]
            index = rob.getrowindexfromID(inst[1])
            # Check if it is a store instruction and that it is next in line to be committed
            if inst[2] == 'Sd' and index == 0:
                LD_SD_fu.mem_compute(inst[0], inst[1], inst[2], inst[3])
                load_store_queue.pop(0)
    
    if LD_SD_fu.mem_buffer_size():
        value = LD_SD_fu.mem_cycle(Memory, 'Sd')
        if value and value[1]:
            Memory = value[0]
            for x, rs in enumerate(load_store_rs):
                if rs.id == value[1] and rs.operation == "Sd":
                    commit_id = rs.id

                    #Update register file and RAT
                    for j, entry in enumerate(rat):


                        register_name = entry[0]
                        instruction_id = entry[1]

                        if instruction_id == rs.id:
                            reg = register_name
                            rat.pop(j)
                    load_store_rs.pop(x)
                    rob.markComplete(commit_id)
                    instruction_id, commit_success = rob.commit()

                    if commit_success and instruction_id is not None:
                        # Must offset cycle since they technically execute in sequential order here but not in actuality
                        timeTable.add_store_commit(instruction_id, i+1, LD_SD_fu.mem_cycles)

                    # Needs to be able to access several hardware components, might be able to clean this up
                    load_store_rs, load_store_queue, cdb, timeTable = loadStoreForwarding(rs.a, rs.vj ,rs.vk, load_store_rs, load_store_queue, cdb, rob, timeTable)

    # If the ROB is empty then nothing can be done
    if rob.isEmpty(): return

    # Cannot commit and writeback on same cycle

    # Attempt to commit the head the entry
    instruction_id, commit_success = rob.commit()
    # If committed then update table -- If not, nothing occurs
    if commit_success and instruction_id is not None:
        # Must offset cycle since they technically execute in sequential order here but not in actuality
        timeTable.add_commit(instruction_id, i+1)


def searchRS(id, value, rs_list):

    for idx, rs in enumerate(rs_list):
        if rs.qj is not None:
            for entry in rat:
                 if entry[1] == id and entry[1] == rs.qj:
                        rs.qj = None
                        rs.vj = value
        if rs.qk is not None:
            for entry in rat:
                 if entry[1] == id and entry[1] == rs.qk:
                        rs.qk = None
                        rs.vk = value
        
        rs_list[idx] = rs
    return rs_list

# Loop thorugh the load store reservation stations and find RS entries with the same memory address and forward the value
def loadStoreForwarding(address, offset ,value, rs_list, queue, cdb, rob, timeTable):
    real_address = address + offset
    for idx, rs in enumerate(rs_list):
        # Checking for load instructions
        if rs.a is not None and rs.vj is not None and rs.vk is None:
            if (rs.a + rs.vj) == real_address:
                cdb.broadcast(value, rs.id)
                rob.markComplete(rs.id)
                timeTable.add_memory(rs.id, i+1, 1)

                for j, entry in enumerate(queue):
                    if entry[1] == rs.id:
                        queue.pop(j)
    return rs_list, queue, cdb, timeTable


if __name__ == "__main__":

    # Begin
    initalize()
    stuff_to_be_done = True
    i = 1

    # Main loop, every iteration is a cycle
    while stuff_to_be_done:
        issue()

        # TODO -------------------------------------------------------------------------------- 
        # Need to remove this value here - data from FUs needs to pass directly to CDB when done executing and if space is avaiable
        # This approach is independant of the cdb object and functional units, we should cut this out
        values_p, mem = execute()
        mem_value_p = memory(mem)
        write()
        commit(mem)
        # Run as long as there are instructions to issue or instruction waiting to commit or loop just moved the PC back
        stuff_to_be_done = (Instruction_Buffer) or (rob.isNotEmpty()) or (PC < len(instruction_memory))
        i = i + 1
        if i > 20:
            break



    output()