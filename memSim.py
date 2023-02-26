from optparse import OptionParser
from typing import Optional
# @param addr: 32-bit int representing a logical addr
# @return page number, offset
def mask_logical_addr(addr):
    return (addr >> 8), (addr & 0xff)

def get_byte_referenced(frame, offset):
    byte_referenced = -(256-frame[offset]) if frame[offset] >= 128 else frame[offset]
    return byte_referenced

def read_physical_memory(frame_num, frame_size=256):
    with open("BACKING_STORE.bin", "rb") as file:
        file.seek(frame_size*frame_num)
        return file.read(frame_size)

class Page:
    def __init__(self, page_number, frame) -> None:
        self.page_number = page_number
        self.frame = frame

class VirtualMemory:
    def __init__(self, pra='FIFO', frames=256) -> None:
        self.frames = frames
        self.lookups = 0
        
        self.tlb = TLB()
        self.tlb_hits = 0
        self.tlb_misses = 0
        self.tlb_lookups = 0
        
        self.page_table = PageTable()
        self.page_faults = 0
        self.page_lookups = 0
        self.page_number = -1
    
    def translate_virtual_addr(self, logical_addr) -> None:
        self.lookups += 1
        page_number, offset = mask_logical_addr(logical_addr)
        page = self.page_table_lookup(page_number)
        byte_referenced = get_byte_referenced(page.frame, offset)
        self.print_addr(logical_addr, byte_referenced, page.page_number, page.frame)
        
    def tlb_lookup(self, page_number) -> Optional[Page]:
        self.tlb_lookups += 1
        page = self.tlb.lookup(page_number)
        if page:
            self.tlb_hits += 1
        else:
            self.tlb_misses +=1
        return page

    def page_table_lookup(self, page_number) -> Optional[Page]:
        self.page_lookups += 1
        tlb_miss = 0
        
        page = self.tlb_lookup(page_number)
        if not page:
            tlb_miss = 1
        else:
            return page
        
        page = self.page_table.lookup(page_number)
        if not page and tlb_miss: # TLB miss and page fault occurs
            self.page_number += 1
            self.page_faults += 1
            
            frame = read_physical_memory(page_number)
            page = Page(self.page_number, frame)
            self.tlb.insert(self.page_number, page)
            self.page_table.insert(self.page_number, page)
        return page
            
    def print_addr(self, addr, value, frame_number, entire_frame: bytes) -> None:
        print(f"{addr}, {value}, {frame_number}, {bytes.hex(entire_frame)}")
    
    def print_stat(self) -> None:
        print(f"Number of Translated Addresses = {self.lookups}")
        print(f"Page Faults = {self.page_faults}")
        print("Page Fault Rate = {:3.3f}".format(self.page_faults/self.page_lookups))
        print(f"TLB Hits = {self.tlb_hits}")
        print(f"TLB Misses = {self.tlb_misses}")
        print("TLB Hit Rate = {:3.3f}".format(self.tlb_hits/self.tlb_lookups))

class TLB:
    def __init__(self, size=16):
        self.size = size
        self.entries = {}
        self.queue = []

    def lookup(self, page_number) -> Optional[Page]:
        try:
            return self.entries[page_number]
        except KeyError:
            return None
    
    def insert(self, page_number, frame): #FIFO implementation
        if page_number in self.entries:
            self.queue.remove(page_number)
        self.entries[page_number] = Page(page_number, frame)
        self.queue.append(frame)
        if len(self.queue) > self.size:
            del self.entries[self.queue.pop(0)]
    
class PageTable:
    def __init__(self, size=256) -> None:
        self.size = size
        self.entries = {}
        self.queue = []
    
    def lookup(self, page_number) -> Optional[Page]:
        try:
            return self.entries[page_number]
        except KeyError:
            return None
    
    def insert(self, page_number, frame): #FIFO implementation
        if page_number in self.entries:
            self.queue.remove(page_number)
        self.entries[page_number] = Page(page_number, frame)
        self.queue.append(frame)
        if len(self.queue) > self.size:
            del self.entries[self.queue.pop(0)]
        '''
        if len(self.queue) == self.size:
            oldest_page = self.queue.pop(0)
            self.entries[oldest_page] = None
        
        self.queue.append(page_number)
        self.entries[page_number] = Page(page_number, frame)
        '''
        
def main():
    virtual_addresses = [16916, 62493, 30198, 53683, 40185, 28781, 24462, 48399, 64815, 18295]
    
    vm = VirtualMemory()
    for addr in virtual_addresses:
        vm.translate_virtual_addr(addr)
    
    vm.print_stat()

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
    
    print(f"Virtual address: 0x{virtual_address:02X}")
    print(f"Page number: {page_number}")
    print(f"Offset: {offset}")
    print(f"Frame number: {frame}")
    print(f"Physical address: 0x{physical_address:02X}")
    print(f"Page fault rate: {page_table.get_page_fault_rate():.2%}")
'''
    
    
if __name__ == '__main__':
    main()
    