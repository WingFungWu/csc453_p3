from optparse import OptionParser
from collections import deque

class VirtualMemory():
    
    def __init__(self, pages) -> None:
        self.pages = pages
        self.tlb = FIFO(pages)
        self.page_table = None
    
    def lookup(self, algo):
        if algo == 'FIFO':
            self.page_table = FIFO(self.pages, 256)
        # for each page:
        #   if page in self.tlb.pages_in_memory():
        #       physical addr = backing_store[frame number*256:(frame number+1)*256]
        #   elif page in self.page_table.pages_in_memory():
        #       physical addr = backing_store[frame number*256:(frame number+1)*256]

class FIFO():
    
    def __init__(self, pages, entries=16):
        self.entries = entries
        self.pages = pages
        self.frames = deque(maxlen=entries)
        self.pages_in_memory = set()
        
    def count(self):
        page_faults = 0
        page_hits = 0
        for page in self.pages:
            if page not in self.pages_in_memory:
                page_faults += 1

                if len(self.frames) == self.entries:
                    oldest_page = self.frames.popleft()
                    self.pages_in_memory.remove(oldest_page)
                
                self.frames.append(page)
                self.pages_in_memory.add(page)
            else:
                page_hits += 1
        return page_faults, page_hits

    def stat(self):
        page_faults, page_hits = self.count()
        total = page_faults + page_hits
        return page_faults/total*100, page_hits/total*100

def read_backing_store(frame):
    with open("BACKING_STORE.bin", "rb") as file:
        file.seek(256*frame)
        return file.read(256)

# @param addr: 32-bit int representing a logical addr
# @return page number, offset
def mask_logical_addr(addr):
    return (addr >> 8), (addr & 0xFF)

def main():
    parser = OptionParser()
    #parser.add_option("-f","--frames", default=256, help="memSim frames to use: an integer <= 256 and > 0", action="store", type="int", dest="frames")
    #parser.add_option("-pra","--PRA", default="FIFO", help="memSim page replacement algorithms to use: FIFO, LRU, OPT", action="store", type="string", dest="pra")
    (option, args) = parser.parse_args()
    if not len(args):
        print("No Input Detected")
        return
    
    print(mask_logical_addr(16916))
    #frames = option.frames
    #if frames < 0 or frames > 256:
        #frames = 256
    '''
    try:
        with open(args[0], 'r') as file:
            addrs = file.read()
            addrs = addrs.split()
            temp = []
            for addr in addrs:
                temp.append(mask_logical_addr(int(addr)))
        with open("test.txt", 'w') as out:
            for i in range(len(temp)):
                out.write(f'{temp[i][0]}, {i}\n')
    except FileNotFoundError:
        print("No Input File Detected")
        return
    '''
    
    
if __name__ == '__main__':
    main()
    