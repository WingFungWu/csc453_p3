from optparse import OptionParser

def read_backing_store(frame):
    with open("BACKING_STORE.bin", "rb") as file:
        file.seek(256*frame)
        return file.read(256)

# @param addr: 32-bit int representing a logical addr
# @return page, offset
def mask_logical_addr(addr):
    return (addr >> 8), (addr & 0xFF)

def main():
    parser = OptionParser()
    parser.add_option("-f","--frames", default=256, help="memSim frames to use: an integer <= 256 and > 0", action="store", type="int", dest="frames")
    parser.add_option("-pra","--PRA", default="FIFO", help="memSim page replacement algorithms to use: FIFO, LRU, OPT", action="store", type="string", dest="pra")
    (option, args) = parser.parse_args()
    if not len(args):
        print("No Input Detected")
        return
    
    frames = option.frames
    if frames < 0 or frames > 256:
        frames = 256

    try:
        with open(args[0], 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print("No Input File Detected")
        return
    