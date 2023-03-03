from random import randint, choice
import sys

if __name__ == '__main__':
    with open("random_addrs.txt", "w") as sys.stdout:
        for _ in range(256*3):
            print(randint(0, 256*256-1))
        sys.stdout = sys.__stdout__
    
    with open("sequential_addrs.txt", "w") as sys.stdout:
        for _ in range(256*3):
            print(choice([i for i in range(256, 256*40, 100)]))
        sys.stdout = sys.__stdout__