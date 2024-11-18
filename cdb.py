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