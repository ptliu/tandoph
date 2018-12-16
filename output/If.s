recurse {0}
cmp eax,1
jne false
recurse {1}
jmp done
false:
recurse {2}
done:
