class Reservation_Station():

    def __init__(self, operation, vj ,vk, qj, qk, a):
        self.busy = False
        self.operation = operation
        self.vj = vj
        self.vk = vk
        self.qj = qj
        self.qk = qk
        self.a = a

    def __init__(self, type, num):
        self.busy = False
        self.operation = None
        self.vj = None
        self.vk = None
        self.qj = None
        self.qk = None
        self.a = None
        self.id = type + str(num)

    def __str__(self):
        return f'({self.busy}, {self.operation}, {self.vj}, {self.vk}, {self.qj}, {self.qk}, {self.a})' 