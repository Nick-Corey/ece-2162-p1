import numpy as np
from tabulate import tabulate

class timetable():

    # Constants to index into table
    id_loc          = 0
    instruction_loc = 1
    issue_loc       = 2
    execute_loc     = 3
    mem_loc         = 4
    writeback_loc   = 5
    commit_loc      = 6

    # Used for modulus into the array 
    entry_size      = 7

    # Dynamic Counter for num of instructions
    count           = 0

    def __init__(self):
        # Empty Constructor - only exists so we can init structure globally before knowing size values
        pass

    def resize(self, num_entries:int):
        # Must init somewhere but we dont know the size, use this once we do know the size
        self.table = np.zeros((num_entries, self.entry_size), dtype=object)

        # Set all memory stage to default NA (~)
        self.table[:, self.mem_loc] = "~"
        
    def getrowindexfromID(self, id:str):
        # Return the row number that pairs with an instruction id and return the index
        row_index = np.where(self.table[:,0] == id)[0][0]
        return row_index

    def add_instruction(self, id:str, instruction:str, issue_cycle:int):
        # Add a single instruction to the time table
        self.table[self.count][self.id_loc]          = id
        self.table[self.count][self.instruction_loc] = instruction
        self.table[self.count][self.issue_loc]       = issue_cycle
        self.count = self.count + 1

    def add_execution(self, id:str, cycle_start:int, cycle_span:int):
        # Add execution stage to timetable
        row_index = self.getrowindexfromID(id)
        # Execution Span = start + cycles to execute - 1 (since we could the first cycle)

        # Nice Formatting
        if cycle_span == 1:
            msg = f"{cycle_start}"
        else:
            msg = f"{cycle_start}-{cycle_start+cycle_span-1}"

        # Add to table
        self.table[row_index][self.execute_loc] = msg

    def add_memory(self, id:str, cycle:int, cycle_span):
        # Update table with memory instructions
        # Only load has a memory stage, - everything else is NA by default (~)

        # Havent made the Load/Store module so cant set the execution time so tempory fix
        #TODO - set the time to read from memory module
        if cycle_span is None:
            cycle_span = 4

        row_index = self.getrowindexfromID(id)
        self.table[row_index][self.mem_loc] = f"{cycle}-{cycle+cycle_span-1}"

    def add_writeback(self, id:str, cycle:int):
        # Writeback cycle to the timetable
        # Only one instruction may writeback at a time
        # Writeback takes 1 cycle - constant

        row_index = self.getrowindexfromID(id)
        self.table[row_index][self.writeback_loc] = cycle

    def add_commit(self, id:str, cycle:int):
        # Writes the commit cycle for an instruction into the table
        # This method is only called when a succesful commit occurs (or should be anyway)

        row_index = self.getrowindexfromID(id)

        # Cannot commit on the same cycle as we writeback - problem with sequential software - offset by 1 to show this
        if self.table[row_index][self.writeback_loc] == cycle:
            self.table[row_index][self.commit_loc] = cycle + 1
        else:
            self.table[row_index][self.commit_loc] = cycle 


    def __str__(self):
        # Pretty table format
        headers = ["ID", "Instruction", "Issue", "Execute", "Memory", "Writeback", "Commit"]
        return(tabulate(self.table, headers, tablefmt="simple_grid"))