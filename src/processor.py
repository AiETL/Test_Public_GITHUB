#!/usr/bin/python3

# src/processor.py

import time
import random

def create_fireworks():
    # Create a fireworks show in 1 minute
    for i in range(60):
        print("  ", end="")
        if i % 10 == 0:
            print("*", end=" ")
        else:
            print(".", end=" ")
        time.sleep(random.uniform(0.05, 0.1))
    print()

create_fireworks()