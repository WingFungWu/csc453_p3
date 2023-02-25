from optparse import OptionParser

class VirtualMemory:
    def __init__(self, frames=256) -> None:
        self.frames = frames
        

class TLB:
    def __init__(self, size=16):
        self.size = size
        self.entries = [None]*size
        self.fifo_queue = []
        self.hits = 0
        self.misses = 0

    def lookup(self, page_number):
        if self.entries[page_number]:
            self.hits += 1
            return self.entries[page_number]
        self.misses += 1
        return None

    def insert(self, page_number, frame_number): #FIFO implementation
        if len(self.fifo_queue) == self.size:
            oldest_page = self.fifo_queue.pop(0)
            self.entries[oldest_page] = None
        
        self.fifo_queue.append(page_number)
        self.entries[page_number] = frame_number

    def hit_rate(self):
        # Compute the hit rate as the number of hits divided by the total number of accesses
        total = self.hits + self.misses
        return self.hits/total if total > 0 else 0

class PageTable:
    def __init__(self, size=256) -> None:
        self.size = size
        self.entries = [None]*size
        self.fifo_queue = []
        self.page_faults = 0
        self.lookups = 0
    
    def lookup(self, page_number):
        self.lookups += 1
        if self.entries[page_number]:
            return self.entries[page_number]
        self.page_faults += 1
        return None
    
    def insert(self, page_number, frame_number): #FIFO implementation
        if len(self.fifo_queue) == self.size:
            oldest_page = self.fifo_queue.pop(0)
            self.entries[oldest_page] = None
        
        self.fifo_queue.append(page_number)
        self.entries[page_number] = frame_number
    
    def get_num_page_faults(self):
        return self.page_faults
    
    def get_page_fault_rate(self):
        return self.page_faults/self.lookups if self.lookups > 0 else 0

# @param addr: 32-bit int representing a logical addr
# @return page number, offset
def mask_logical_addr(addr):
    return (addr >> 8), (addr & 0xff)
        
def main():
    
    page_table = PageTable()
    virtual_addresses = [16916, 62493, 30198, 53683, 40185, 28781, 24462, 48399, 64815, 18295]
    
    virtual_address = virtual_addresses[0]
    page_number, offset = mask_logical_addr(virtual_address)
    frame_number = page_table.lookup(page_number)
    if not frame_number:
        frame_number = len(page_table.fifo_queue)
        page_table.insert(page_number, frame_number)
    physical_address = (frame_number << 8) | offset

    print(f"Virtual address: 0x{virtual_address:02X}")
    print(f"Page number: {page_number}")
    print(f"Offset: {offset}")
    print(f"Frame number: {frame_number}")
    print(f"Physical address: 0x{physical_address:02X}")
    print(f"Page fault rate: {page_table.get_page_fault_rate():.2%}")

'''
def main():
    parser = OptionParser()
    parser.add_option("-f","--frames", default=256, help="memSim frames to use: an integer <= 256 and > 0", action="store", type="int", dest="frames")
    parser.add_option("-p","--PRA", default="FIFO", help="memSim page replacement algorithms to use: FIFO, LRU, OPT", action="store", type="string", dest="pra")
    (option, args) = parser.parse_args()
    if not len(args):
        print("No Input Detected")
        return
    
    #pageFrame, offset =mask_logical_addr(16916)
    
    #frames = option.frames
    #if frames < 0 or frames > 256:
        #frames = 256
'''
    
    
if __name__ == '__main__':
    main()
    