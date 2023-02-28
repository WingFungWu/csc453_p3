from optparse import OptionParser
import sys, filecmp

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
    def __init__(self, page_number, frame):
        self.page_number = page_number
        self.frame = frame

class VirtualMemory:
    def __init__(self, pra, frames):
        self.frames = frames
        self.lookups = 0
        
        self.tlb = FIFOCache()
        self.tlb_hits = 0
        self.tlb_misses = 0
        self.tlb_lookups = 0
        
        if pra == 'FIFO':
            self.page_table = FIFOCache(frames)
        elif pra == 'LRU':
            self.page_table = LRUCache(frames)
        else:
            self.page_table = OPTCache(frames)
        
        self.page_faults = 0
        self.page_lookups = 0
        self.page_number = -1
    
    def translate_virtual_addr(self, logical_addr):
        self.lookups += 1
        page_number, offset = mask_logical_addr(logical_addr)
        page = self.page_table_lookup(page_number)
        byte_referenced = get_byte_referenced(page.frame, offset)
        self.print_addr(logical_addr, byte_referenced, page.page_number, page.frame)
        
    def tlb_lookup(self, page_number):
        self.tlb_lookups += 1
        page = self.tlb.lookup(page_number)
        if page:
            self.tlb_hits += 1
        else:
            self.tlb_misses +=1
        return page

    def page_table_lookup(self, page_number):
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
            
    def print_addr(self, addr, value, frame_number, entire_frame: bytes):
        print(f"{addr}, {value}, {frame_number}, {bytes.hex(entire_frame).upper()}")
    
    def print_stat(self):
        print(f"Number of Translated Addresses = {self.lookups}")
        print(f"Page Faults = {self.page_faults}")
        print("Page Fault Rate = {:3.3f}".format(self.page_faults/self.page_lookups))
        print(f"TLB Hits = {self.tlb_hits}")
        print(f"TLB Misses = {self.tlb_misses}")
        print("TLB Hit Rate = {:3.3f}".format(self.tlb_hits/self.tlb_lookups))

class FIFOCache:
    def __init__(self, size=16):
        self.size = size
        self.entries = {}
        self.queue = []

    def lookup(self, page_number):
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

class LRUCache:
    def __init__(self, size):
        self.size = size
        self.entries = {}
        self.used_list = []
        
    def lookup(self, page_number):
        if page_number in self.entries:
            self.used_list.remove(page_number)
            self.used_list.append(page_number)
            return self.entries[page_number]
        return None
        
    def insert(self, page_number, frame):
        if page_number in self.entries:
            self.used_list.remove(frame)
        elif len(self.entries) >= self.size:
            evict = self.used_list.pop(0)
            del self.entries[evict]
        self.entries[page_number] = frame
        self.used_list.append(frame)
        
class OPTCache:
    def __init__(self, size):
        self.size = size
        self.entries = []
        self.future_accesses = {}
        
    def refer(self, page):
        if page not in self.entries:
            if len(self.entries) == self.size:
                self.replace()
            self.entries.append(page)
            self.future_accesses[page] = self.find_future_accesses(page)
            
    def find_future_accesses(self):
        # simulate the future accesses of the page
        # this is where the OPT algorithm is not practical to implement in reality
        # since we cannot accurately predict the future access pattern
        return []
    
    def replace(self):
        # find the page that will not be used for the longest period of time
        # among the current cache pages and replace it with the new page
        max_future_accesses = -1
        max_future_accesses_page = None
        for page in self.entries:
            if self.future_accesses[page] == []:
                # if the page is not accessed in the future, we can replace it immediately
                self.entries.remove(page)
                del self.future_accesses[page]
                return
            if len(self.future_accesses[page]) > max_future_accesses:
                max_future_accesses = len(self.future_accesses[page])
                max_future_accesses_page = page
        self.entries.remove(max_future_accesses_page)
        del self.future_accesses[max_future_accesses_page]

def main():
    parser = OptionParser()
    parser.add_option("-f","--frames", default=256, help="memSim frames to use: an integer <= 256 and > 0", action="store", type="int", dest="frames")
    parser.add_option("-p","--PRA", default="FIFO", help="memSim page replacement algorithms to use: FIFO, LRU, OPT", action="store", type="string", dest="pra")
    (option, args) = parser.parse_args()
    if not len(args):
        print("No Input Detected")
        return
    
    frames = option.frames
    frames = 256 if frames < 0 or frames > 256 else frames
    expected = "addresses_output.txt"
    out_file = "out.txt"
    
    try:
        with open(args[0], "r") as in_file:
            virtual_addresses = in_file.read().split()
            virtual_addresses = [int(addr) for addr in virtual_addresses]
        vm = VirtualMemory(option.pra, option.frames)
        with open(out_file, "w") as sys.stdout:
            for addr in virtual_addresses:
                vm.translate_virtual_addr(addr)
            vm.print_stat()
        sys.stdout = sys.__stdout__
        assert filecmp.cmp(expected, out_file) == True
    except FileNotFoundError:
        print("Incorrect <reference-sequence-file.txt> Detected")
        return
    
if __name__ == '__main__':
    main()
    