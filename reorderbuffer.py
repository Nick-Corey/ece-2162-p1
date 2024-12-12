import numpy as np
from tabulate import tabulate

class ReorderBuffer():
    # Reorder buffer inteded to represent a queue of instructions ready to be committed
    # Head instruction gets committed if ready

    # Each entry (row) has 4 fields (colums)
    # --- ID, Corresponding Register, Value, Finished

    # Indexing Locations
    id_loc      = 0
    reg_loc     = 1
    value_loc   = 2
    done_loc    = 3 
    entry_size  = 4

    # We will allocate the full space at once but only have access to what was written
    # Acts as a FIFO
    count       = 0

    def __init__(self):
        # Empty Constructor that exists only so we can init the object globally before knowinbg size
        pass

    def resize(self, size:int):
        
        self.max_size = size

        # Create the reorder buffer with given size
        self.rob = np.zeros([size, self.entry_size], dtype=object)
        self.rob[:, self.id_loc]    = None
        self.rob[:, self.reg_loc]   = None
        self.rob[:, self.value_loc] = None
        self.rob[:, self.done_loc]  = None

    def getrowindexfromID(self, id:str):
        # Return the row number that pairs with an instruction id and return the index
        row_index = np.where(self.rob[:,0] == id)[0][0]
        return row_index

    def insert(self, id:str):
        # Insert a new entry into the reorder buffer
        self.rob[self.count][self.id_loc]   = id
        self.rob[self.count][self.done_loc] = False
        self.count = self.count + 1

    def markComplete(self, id:str):
        # Marks an instruction as complete and ready to be written back
        row_index = self.getrowindexfromID(id)
        self.rob[row_index][self.done_loc] = True

    def commit(self):
        # Return instruction id and whether it was committed or not

        output_id = None
        success   = False

        # Cant commit nothing
        if not self.isEmpty():
        # We only commit if the head instruction is done
            if (self.rob[0][self.done_loc] == True):
                output_id = self.rob[0][self.id_loc]
                self.rob = np.delete(self.rob, (0,1,2,3))
                self.rob = np.resize(self.rob, (self.max_size, self.entry_size))
                self.count = self.count - 1
                success = True

        
        output = output_id, success
        return output

    def getSize(self):
        return self.count

    def hasSpace(self):
        return self.count < self.max_size

    def isEmpty(self):
        return self.count == 0

    def isNotEmpty(self):
        return not self.isEmpty()

    def pop(self):
        # Removes a row from the rob
        # Intended to be used when correcting a misprediction
        self.rob = np.delete(self.rob, 0, axis=0)
        self.count = self.count - 1

    def remove(self, id:str):
        # Remove entry from rob
        # Intended to be used when correcting a misprediction
        row_index = np.where(self.rob[:,0] == id)[0][0]
        self.rob = np.delete(self.rob, row_index, axis=0)
        self.count = self.count - 1

    def __str__(self):
        # Pretty string function
        headers = ["ID", "Register", "Value", "Done"]
        return tabulate(self.rob[0:self.count+1][:], headers, tablefmt="simple_grid")