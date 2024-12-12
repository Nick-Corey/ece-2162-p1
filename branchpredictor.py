class BranchPredictor:
    """
    BP is the branch predictor
       - it is used to store states for 1-bit branch predictor
       - has unlimited entries and uses the full instruction address to index since the states and prediction are the main goal
       - Hardware wise this is okay for our use case as our instructions are limited in size and no more than 16 or so
       - Programmatically this is easy since we can dynamically add to a list
    
     BTB is the branch target buffer
       - it is used to store target for branch instructions when taken
       - Size of the BTB is very important and often limited in hardware so we will mimic it here
       - Size is limited to a max and we use 3 LSB of an address to index into it
       - Store the target as ( current address of program counter + the offset of the branch instruction)
    
     Intent is to populate the Branch Predictor with default values for all branches when loaded into memory to mimic middle of execution flow
     Use BTB when branch is taken (or predicted to be taken) then update it with new values after taking it, will overwrite or not change anything
     Call the predict and update prediction methods as needed in order
     Will only know if prediction is correct once the condition has been evaluatied in the execution phase
    """

    bp           = []     # 2D list for entries and their prediction  - uses full adddress
    btb          = {}     # Dictionary for address and target         - uses 3 LSB of address
    btb_max_size = 8      # Max Size of the btb
    default      = False  # Default initial prediction

    # Indexing variables
    id_index        = 0
    address_index   = 1
    prediction      = 2

    history      = []     # Stores previous predictions of branches 

    def __init__(self):
        # Will initialize a branch predictor object
        # Use this to create an empty btb before we know the size or instructions or anything
        pass

    def initializePredictions(self, instructions:str):
        # We will use this to populate the bp with instructions
        # Done so testing mimics picking up in the middle of code to keep test cases small
        # Could do these individually at runtime but in one fell swoop makes things easier as I don't know other guy's plans

        counter = 0
        print(f"Branch Predictor Default set to {self.default}")
        for address,instruction in enumerate(instructions):
            # Check if instruction is a branch instruction - may need more robust condition
            if "B" in instruction.split()[0]:

                # Add an entry to bp - id, address, prediction
                self.bp.append([f'B{counter}', address, self.default])
                counter = counter + 1

    def predict(self, value):
        # Will give the prediction from address or id

        # If the passed value is an int, else assume string
        if (type(value) == type(0)):
            address = value
        else:
            id = value

        # If we are given an address search for it, else us the reservation station id
        if address:
        # Find the entry and return associated prediction
            for entry in self.bp:
                if entry[self.address_index] == address:
                    return entry[self.prediction]
        else:
            for entry in self.bp:
                if entry[self.id_index] == id:
                    return entry[self.prediction]
            
            
        # Return none if not found    
        return None
    # def predict(self, address:int):
    #     # Will give the prediction from address
        
    #     # Find the entry and return associated prediction
    #     for entry in self.bp:
    #         if entry[self.address_index] == address:
    #             return entry[self.prediction]
            
    #     # Return none if not found    
    #     return None

    # def predict(self, id:str):
    #     # Will give the prediction from id
        
    #     # Find the entry and return associated prediction
    #     for entry in self.bp:
    #         if entry[self.id_index] == id:
    #             return entry[self.prediction]
            
    #     # Return none if not found    
    #     return None
    
    def updatePrediction(self, address:int, result:bool):
        # Will update the prediction based on prior result being correct or not using address

        # If prediction was good, do not change it
        if result == True:
            pass
        
        # If prediction was bad - flip
        if result == False:
            # Find the entry 
            for entry in self.bp:
                if entry[self.address_index] == address:
                    # Flip prediction
                    entry[self.prediction] = not entry[self.prediction]

    # def updatePrediction(self, id:str, result:bool):
    #     # Will update the prediction based on prior result being correct or not using id

    #     # If prediction was good, do not change it
    #     if result == True:
    #         pass
        
    #     # If prediction was bad - flip
    #     if result == False:
    #         # Find the entry 
    #         for entry in self.bp:
    #             if entry[self.id_index] == id:
    #                 # Flip prediction
    #                 entry[self.prediction] = not entry[self.prediction]

    def addBTB(self, instruction:str, current_address:int):
        # Add something to the branch target buffer
        offset = int(instruction.split()[-1])
        target = current_address + offset
        self.btb[current_address % self.btb_max_size] = target # % 8 to use last 3 bits as index

    def getBTB(self,  address:str):
        # Return the target for a BTB entry
        target = self.btb[address % self.btb_max_size]
        return target
    
    def addHistory(self, id:int, taken:bool):
        # Add a branch history entry
        self.history.append((id, taken))

    def searchHistory(self, id:int):
        for entry in self.history:
            if entry[0] == id:
                return entry[1]
            
    def removeHistory(self, id:int):
        for idx, entry in enumerate(self.history):
            if entry[0] == id:
                self.history.pop(idx)

    def __str__(self):
        out = ""
        for entry in self.bp:
            out += f"Branch Address-{entry[0]} Prediction-{entry[2]}\n"

        return out
