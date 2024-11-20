class CommonDataBus:

    def __init__(self, size):
        self.bus = []
        self.size = size
        return
    
    def broadcast(self, value, rs):
        if len(self.bus) < self.size:
            self.bus.append((value,rs))
            return True
        else:
            return False
        
    def read(self):
        return self.bus
    
    def pop(self, idx):
        self.bus.pop(idx)
        return
    
    def hasData(self):
        # Function to see if there is any good data on the CDB bus

        hasData = False

        # Loop through CDB, it theres data - find out
        for entry in range(len(self.bus)):
            if entry[0] is not None or entry[1] is not None:
                hasData = True

        return hasData 