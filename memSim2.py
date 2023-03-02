from optparse import OptionParser
from collections import OrderedDict

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

class Cache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}

    def get(self, key):
        pass

    def put(self, key, value):
        pass
    
class FIFOCache(Cache):
    def __init__(self, capacity):
        super().__init__(capacity)
        self.queue = []

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            return None

    def put(self, key, value):
        if len(self.cache) == self.capacity and key not in self.cache:
            evicted_key = self.queue.pop(0)
            del self.cache[evicted_key]
        self.cache[key] = value
        if key not in self.queue:
            self.queue.append(key)

class LRUCache(Cache):
    def __init__(self, capacity):
        super().__init__(capacity)
        self.queue = []

    def get(self, key):
        if key in self.cache:
            self.queue.remove(key)
            self.queue.append(key)
            return self.cache[key]
        else:
            return None

    def put(self, key, value):
        if len(self.cache) == self.capacity and key not in self.cache:
            evicted_key = self.queue.pop(0)
            del self.cache[evicted_key]
        self.cache[key] = value
        if key in self.queue:
            self.queue.remove(key)
        self.queue.append(key)

class OPTCache(Cache):
    def __init__(self, capacity):
        super().__init__(capacity)
        self.accesses = {}

    def get(self, key):
        if key in self.cache:
            self.accesses[key] = self.get_next_access(key)
            return self.cache[key]
        else:
            return None

    def put(self, key, value):
        if len(self.cache) == self.capacity and key not in self.cache:
            evict_key = max(self.accesses, key=self.accesses.get)
            del self.cache[evict_key]
            del self.accesses[evict_key]
        self.cache[key] = value
        self.accesses[key] = self.get_next_access(key)

    def get_next_access(self, key):
        if key not in self.cache:
            return float('inf')
        try:
            return self.accesses[key] + 1 + self.get_future_distance(key)
        except KeyError:
            return float('inf')

    def get_future_distance(self, key):
        try:
            return next(i for i, x in enumerate(self.future_accesses) if x == key) 
        except StopIteration:
            return float('inf')

    def set_future_accesses(self, future_accesses):
        self.future_accesses = future_accesses
        
class Page:
    def __init__(self, page_number, frame):
        self.page_number = page_number
        self.frame = frame

class VirtualMemory:
    def __init__(self, pra, frames, access_sequence):
        self.frames = frames
        self.lookups = 0
        
        self.tlb = FIFOCache(16)
        self.tlb_hits = 0
        self.tlb_misses = 0
        self.tlb_lookups = 0
        
        if pra == 'FIFO':
            self.page_table = FIFOCache(frames)
        elif pra == 'LRU':
            self.page_table = LRUCache(frames)
        else:
            self.page_table = OPTCache(frames)
            self.page_table.set_future_accesses(access_sequence)
        
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
        page = self.tlb.get(page_number)
        if page:
            self.tlb_hits += 1
        else:
            self.tlb_misses +=1
        return page

    def page_table_lookup(self, page_number):
        self.page_lookups += 1
        tlb_miss = 0
        
        page = self.tlb_lookup(page_number)
        page = None
        if not page:
            tlb_miss = 1
        else:
            return page
        
        page = self.page_table.get(page_number)
        if not page and tlb_miss: # TLB miss and page fault occurs
            self.page_number += 1
            self.page_faults += 1
            
            frame = read_physical_memory(page_number)
            page = Page(self.page_number, frame)
            self.tlb.put(page_number, page)
            self.page_table.put(page_number, page)
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
    
    try:
        with open(args[0], "r") as in_file:
            virtual_addresses = in_file.read().split()
            virtual_addresses = [int(addr) for addr in virtual_addresses]
        future_accesses = {virtual_addresses[i]: i for i in range(len(virtual_addresses)) if virtual_addresses[i] not in future_accesses}
        vm = VirtualMemory(option.pra, option.frames, future_accesses)
        for addr in virtual_addresses:
            vm.translate_virtual_addr(addr)
        vm.print_stat()
    except FileNotFoundError:
        print("Incorrect <reference-sequence-file.txt> Detected")
        return

if __name__ == '__main__':
    main()
    