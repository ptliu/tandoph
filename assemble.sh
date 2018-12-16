#!/bin/bash

if [ $# -eq 1 ]; then
  echo "Assembling $1"
  nasm -f aout -o "$1.o" "$1.s"
  clang -g -m32 -o $1 "$1.o" starter.c
  rm "$1.o"
else
  echo "Incorrect number of command line arguments, expected 1"
fi
