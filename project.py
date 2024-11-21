import json
import numpy as np
from tabulate import tabulate
import reservation_station
from alu import Int_adder, FP_Adder, FP_Mult, LD_SD
from cdb import CommonDataBus
from timetable import timetable
from reorderbuffer import ReorderBuffer

# Create Memory and Register arrays
Memory = [0] * 32
Int_Registers = [0] * 32
Float_Registers = [0.0] * 32
Instruction_Buffer = []
int_rs_size = 0
fp_adder_rs_size = 0
fp_mult_rs_size = 0
load_store_rs_size = 0

int_rs = []
fp_adder_rs = []
fp_mult_rs = []
load_store_rs = []

# TODO: allow for dynamic size CDB
cdb = CommonDataBus(1)
rat = []

# Create time table
timeTable = timetable()

# Create ROB
rob = ReorderBuffer()

# Creating headers for Output tables
Int_Registers_Names = [''] * 32
Float_Registers_Names = [''] * 32
i = 0
while i < 32:
    Int_Registers_Names[i] = "R" + str(i)
    Float_Registers_Names[i] = "F" + str(i)
    i = i + 1

def initalize():
    global Int_fu, int_rs_size, FP_adder_fu, fp_adder_rs_size, fp_mult_rs_size, FP_mult_fu, LD_SD_fu, load_store_rs_size
    # Open test case file
    with open("TestCases/input.json") as test_file:
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
        for instruction in specs["specifications"]["Instructions"]:
            Instruction_Buffer.append(instruction["value"])

        #Initalize Time Table
        timeTable.resize(len(Instruction_Buffer))

        #Initalize ROB to correct size
        rob.resize(specs["specifications"]["ROB entries"])

    return
    

def output():

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
    print(fp_adder_rs)
    print(fp_mult_rs)
    print(rat)

# RS are currently dyanically pushed and popped into a list
# in order to create a value which can allow an RS to be referenced
# I am using the cycle number... This may need to be change later 
def issue():
    global int_rs, fp_adder_rs
    instruction_type = ""
    # If no instructions left - nothing to issue - exit
    if not Instruction_Buffer:
        return

    # Get next instruction for Instruction Buffers
    instruction = Instruction_Buffer[0]
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
    elif "Ld" in operation:
        instruction_type = "fp"
        if len(load_store_rs) < load_store_rs_size:
            rs = reservation_station.Reservation_Station("LD", i)
        else:
            # Stall?
            return
    # TODO: Branch instructions & Store Instructions

    # Get Destination Register
    destination = instruction_parts[1]

    # Read Operands from Register File
    operand1 = instruction_parts[2]
    if 'Ld' not in operation:
        operand2 = instruction_parts[3]
    
    if "Addi" in operation:
        value1 = Int_Registers[int(operand1[1:])] 
        value2 = int(operand2)
    elif "Add.d" in operation or "Add" in operation or "Mult.d" in operation or "Sub.d" in operation or "Sub" in operation:
        if "int" in instruction_type:
            value1 = Int_Registers[int(operand1[1:])] 
            value2 = Int_Registers[int(operand2[1:])]

        if "fp" in instruction_type:
            value1 = Float_Registers[int(operand1[1:])] 
            value2 = Float_Registers[int(operand2[1:])] 
    elif "Ld" in operation:
        # Ld F4, 8(R1)
        parts = operand1.replace(')', '').split('(') 
        reg = parts[1]
        offset = int(parts[0])
        value1 = Int_Registers[int(reg[1:])] 
    # Record Source of other operands

    # TODO: Might need to add logic for duplicate RAT entries (WAW)
    # Update source mapping (RAT)
    # (destination, rs_num)
    rat.append((destination, rs.id))

    # Place values in RS
    rs.operation = operation

    # Check if the value is a string or a number
    if 'Ld' not in operation:
        # Check if the value is a string or a number
        if type(value1) == type("value"):
            rs.qj = value1
        else:
            rs.vj = value1
        if type(value2) == type("value"):
            rs.qk = value2
        else:
            rs.vk = value2
    else:
        #TODO Register renaming for LD???
        rs.a = value1
        rs.vj = offset 

    if "Add.d" in operation or "Sub.d" in operation:
        fp_adder_rs.append(rs)
    elif "Add" in operation or "Sub" in operation or "Addi" in operation:
        int_rs.append(rs)
    elif "Mult.d" in operation:
        fp_mult_rs.append(rs)
    elif "Ld" in operation:
        load_store_rs.append(rs)
    else:
        print('why are you here?')

    # Insert Instruction into the ROB
    rob.insert(rs.id)

    # Add issued instruction to the time table
    timeTable.add_instruction(rs.id, instruction, i)
    Instruction_Buffer.pop(0)

    return

def execute():
    global Int_fu, int_rs, fp_adder_rs, FP_adder_fu
    
    # Execution Stage
    
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

    # FP Mult Reservation Stations
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

    # Monitor Results from ALUs

    # Capture matching operands

    # compete for ALUs

    # TODO: add suport for fp and ld/sd
    int_value = Int_fu.cycle()
    #print(int_value)
    #print(int_value)
    fp_adder_value = FP_adder_fu.cycle()
    fp_mult_value = FP_mult_fu.cycle()
    ld_sd_value = LD_SD_fu.cycle()
    #print(fp_adder_value)
    # TODO: add support for CDB of multiple sizes

    # TODO ------------------------------------------
    # We need a method of passing finished data directly to the cdb from this stage.
    # Should not return anything from the execute function - more comments in main loop
    # CDB buffer can have dynamic number of elements, but we must have a condition to make sure it has space
    # Additionally we must also have some way of checking if there is enough space in FU and its buffer before we pass the data to begin executing

    return [int_value, fp_adder_value, fp_mult_value], ld_sd_value

def memory(value):
    # Memory Stage 

    if value[0] != None and value[1] != None and LD_SD_fu.check_if_mem_space():
        # value equal to ???
        value = LD_SD_fu.mem_compute(value[0], value[1])

    if LD_SD_fu.mem_buffer_size():
        value = LD_SD_fu.mem_cycle(Memory)

    #timeTable.add_memory(id, cycle)

    return value

def write(values, mem_value):
    # Values[n] corresponds to entries on the buffer
    # Values[n][0] is the entries' data
    # Values[n][1] is the entries' instruction id

    global Int_Registers, int_rs, rat, Float_Registers, fp_adder_rs

    # Update these variables later
    writeBack = False
    writeback_instruction_id = None

    # Broadcast on CDB
    # TODO -------------------------------------------------------- 
    # CDB should be updated
    # We should be able to append data items to item up until it is full via an insert function (looks like broadcast but the name is deceiving)
    # We should actaully broadcast the data to all the reservation stations and ROB entries when the singular writeback element is popped off
    # -- ie - insert data into the buffer, broadcast results to other structures when we pop the one off (it will only every be one at a time)
    # We can add multiple items to the buffer at a time (if they finish executing at the same time and there is space) but only one will ever be broadcasted

    #TODO ---------------------------------------------------------
    #  we really shouldnt have this control loop right here - at most we will only every writeback one instruction
    # Our buffer has varying size, but we only ever writeback one instruction. Can discuss
    for value in values:

        result = value[0]
        cdb_instruction_id = value[1]

        if result != None and cdb_instruction_id != None:
            writeBack = True
            cdb.broadcast(result, cdb_instruction_id)
            rob.markComplete(cdb_instruction_id)

    if mem_value[0] != None and mem_value[1] != None:
        
        print(mem_value)
        cdb.broadcast(mem_value[0], mem_value[1])
        rob.markComplete(mem_value[1])

    # WriteBack first piece of data on CDB from CDB
    if cdb.hasData():

        cdb_data_item = cdb.pop()
        result = cdb_data_item[0]
        cdb_instruction_id = cdb_data_item[1]

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

                        if instruction_id == rs.id:
                            reg = register_name
                            #print(reg)
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
                            #print(reg)
                            rat.pop(j)
                            Float_Registers[int(reg[1:])] = result
                    fp_adder_rs.pop(x)
                    cdb.pop()
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
                            #print(reg)
                            rat.pop(j)
                            Float_Registers[int(reg[1:])] = result
                    fp_mult_rs.pop(x)
                    cdb.pop()
        elif 'LD' in value[1]:
            #Free Reservation Station
            for x, rs in enumerate(load_store_rs):
                if rs.id == value[1]:
                    writeback_instruction_id = rs.id
                    #Update register file and RAT
                    for j, entry in enumerate(rat):


                        register_name = entry[0]
                        instruction_id = entry[1]

                        if instruction_id == rs.id:
                            reg = register_name
                            #print(reg)
                            rat.pop(j)
                            Float_Registers[int(reg[1:])] = result
                    load_store_rs.pop(x)
                    cdb.pop()
        pass            

    # Writeback to RF

    # Updating Mapping

    # Free Reservation Station

    # Update Timetable - only if good data on CDB
    if writeBack:
        timeTable.add_writeback(writeback_instruction_id, i+1)

    return

def commit():

    # If the ROB is empty then nothing can be done
    if rob.isEmpty(): return

    # Cannot commit and writeback on same cycle

    # Attempt to commit the head the entry
    instruction_id, commit_success = rob.commit()
    # If committed then update table -- If not, nothing occurs
    if commit_success and instruction_id is not None:
        # Must offset cycle since they technically execute in sequential order here but not in actuality
        timeTable.add_commit(instruction_id, i+2)

if __name__ == "__main__":
    
    # Begin
    initalize()
    stuff_to_be_done = True
    i = 0

    # Main loop, every iteration is a cycle
    while stuff_to_be_done:
        issue()

        # TODO -------------------------------------------------------------------------------- 
        # Need to remove this value here - data from FUs needs to pass directly to CDB when done executing and if space is avaiable
        # This approach is independant of the cdb object and functional units, we should cut this out
        values, mem = execute()
        mem_value = memory(mem)
        write(values, mem_value)
        commit()

        # Run as long as there are instructions to issue or instruction waiting to commit
        stuff_to_be_done = (Instruction_Buffer) or (rob.isNotEmpty())
        i = i + 1
        #print(rob)
    output()
    print(timeTable)