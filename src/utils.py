successfully downloaded text file (SHA: 96f5bfec814bf6d06a010a7a41d5b35a7fdcd8)
# -*- coding:utf-8 -*-
import time
import os

def create_fireworks():
    # Set the terminal width to a reasonable value
    os.system('stty -F std2 115')

    for i in range(60):
        print("\033[2K\r")
        for j in range(i+1):
            print("*", end="")
            if (j + 1) % 5 == 0:
                print(" ", end="")  # Print spaces to avoid printing extra stars
        print()
        time.sleep(0.01)

create_fireworks()