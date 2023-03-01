import memSim, sys, filecmp
from optparse import OptionParser
from random import randint

def main():
    parser = OptionParser()
    parser.add_option("-f","--frames", default=256, help="memSim frames to use: an integer <= 256 and > 0", action="store", type="int", dest="frames")
    parser.add_option("-p","--PRA", default="FIFO", help="memSim page replacement algorithms to use: FIFO, LRU, OPT", action="store", type="string", dest="pra")
    parser.add_option("-w", default=0, action="store", type="int", dest="write")
    (option, args) = parser.parse_args()
    if not len(args):
        print("No Input Detected")
        return
    
    if option.write:
        with open("addrs.txt", 'w') as sys.stdout:
            for _ in range(256*150):
                print(randint(0, 256*255))
        sys.stdout = sys.__stdout__
    
    frames = option.frames
    frames = 256 if frames < 0 or frames > 256 else frames
    
    try:
        with open(args[0], "r") as in_file:
            virtual_addresses = in_file.read().split()
            virtual_addresses = [int(addr) for addr in virtual_addresses]
        vm = memSim.VirtualMemory(option.pra, option.frames)
        if option.pra == 'FIFO':
            out_file = "out_fifo.txt"
        elif option.pra == 'LRU':
            out_file = "out_lru.txt"
        if args[0] == "addresses.txt":
            out_file = "out.txt"
        with open(out_file, "w") as sys.stdout:
            for addr in virtual_addresses:
                vm.translate_virtual_addr(addr)
            vm.print_stat()
        sys.stdout = sys.__stdout__
        if args[0] == "addresses.txt":
            assert filecmp.cmp("out.txt", "addresses_output.txt") == True
    except FileNotFoundError:
        print("Incorrect <reference-sequence-file.txt> Detected")
        return
    
if __name__ == '__main__':
    main()
    