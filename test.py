#!/bin/python3

import sys

#a0, a1, a2 = input().strip().split(' ')
#a0, a1, a2 = [int(a0), int(a1), int(a2)]
#b0, b1, b2 = input().strip().split(' ')
#b0, b1, b2 = [int(b0), int(b1), int(b2)]

a0, a1, a2 = [1,2,3]
b0, b1, b2 = [1,4,1]

aliceScore = 0
bobScore = 0


def compare(a, b):
    global aliceScore
    global bobScore
    if a > b:
        aliceScore += 1
    if b > a:
        bobScore += 1


compare(a0, b0)
compare(a1, b1)
compare(a2, b2)

print(str(aliceScore) + " " + str(bobScore))