import json
import numpy as np
from tabulate import tabulate
import reservation_station
from alu import Int_adder

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

# Creating headers for Output tables
Int_Registers_Names = [''] * 32
Float_Registers_Names = [''] * 32
i = 0
while i < 32:
    Int_Registers_Names[i] = "R" + str(i)
    Float_Registers_Names[i] = "F" + str(i)
    i = i + 1


# TODO: rename from main() to something more specific
def main():
    global Int_fu, int_rs_size
    # Open test case file
    with open("input.json") as test_file:
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
            if 'FP Multiplier' in operation['name']:
                fp_mult_rs_size = operation['reservation_station_num']
            if 'Load/Store Unit' in operation['name']:
                load_store_rs_size = operation['reservation_station_num']
        for instruction in specs["specifications"]["Instructions"]:
            Instruction_Buffer.append(instruction["value"])
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

    print(int_rs)
    print(fp_adder_rs)
    print(fp_mult_rs)

def issue():
    global int_rs
    instruction_type = ""

    # Get next instruction for Instruction Buffers
    instruction = Instruction_Buffer.pop(0)
    instruction = instruction.replace(",", "")
    instruction_parts = instruction.split(" ")
    
    # Find Free Reservation Station
    operation = instruction_parts[0]

    # This is broken for some reason???
    # if "Add.d" or "Sub.d" in operation:
    #     instruction_type = "fp"
    #     if len(fp_adder_rs) <= fp_adder_rs_size:
    #         rs = reservation_station.Reservation_Station()
    #     else:
    #         # Stall?
    #         return
    if "Add" or "Sub" or "Addi" in operation:
        instruction_type = "int"
        if len(int_rs) < int_rs_size:
            rs = reservation_station.Reservation_Station()
        else:
            # Stall?
            return
    elif "Mult.d" in operation:
        instruction_type = "fp"
        if len(fp_mult_rs) < fp_mult_rs_size:
            rs = reservation_station.Reservation_Station()
        else:
            # Stall?
            return
    # TODO: Branch instructions & Load/Store Instructions

    # Read Operands from Register File
    operand1 = instruction_parts[2]
    operand2 = instruction_parts[3]

    if "Add.d" or "Add" or "Mult.d" or "Sub.d" or "Sub" in operation:
        if "int" in instruction_type:
            value1 = Int_Registers[int(operand1[1:])] 
            value2 = Int_Registers[int(operand2[1:])]

        if "fp" in instruction_type:
            value1 = Float_Registers[int(operand1[1:])] 
            value2 = Float_Registers[int(operand2[1:])] 
    
    if "Addi" in operation:
        value1 = Int_Registers[int(operand1[1:])] 
        value2 = operand2

    # Record Source of other operands



    # Update source mapping (RAT)


    # Place values in RS
    rs.operation = operation

    # Check if the value is a string or a number
    if type(value1) == type("value"):
        rs.qj = value1
    else:
        rs.vj = value1

    if type(value2) == type("value"):
        rs.qk = value2
    else:
        rs.vk = value2

    # For some reason this is super buggy? Had to remove Add.d
    if "Sub.d" in operation:
        fp_adder_rs.append(rs)
    elif "Add" in operation:
        int_rs.append(rs)
    elif "Mult.d" in operation:
        fp_mult_rs.append(rs)
    else:
        print('why are you here?')

    return

def execute():
    global Int_fu, int_rs
    # Execute in ALU when all operands available
    for rs in int_rs:
        if rs.busy == False and rs.vj != None and rs.vk != None:
            if Int_fu.check_if_space():
                Int_fu.compute(rs)
                rs.busy = True


    # Monitor Results from ALUs

    # Capture matching operands

    # compete for ALUs


    int_value = Int_fu.cycle()

    return

def memory():
    return

def write():

    # Broadcast on CDB

    # Writeback to RF

    # Updating Mapping

    # Free Reservation Station

    return

def commit():
    return

if __name__ == "__main__":
    main()
    for i in range(5):
        issue()
        execute()
    output()