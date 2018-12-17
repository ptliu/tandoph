:Num (nat)
+
mov eax,{0}
-

:Var (var)
+
mov eax, [ebp-@0]
-


:For (num) (expr)
+
mov ecx,{0}
loop:
recurse {1}
sub ecx,1
cmp 0,ecx
jne loop
-

:Add (expr1) (expr2)
+
recurse {0}
mov @temp1, eax
recurse {1}
add eax, @temp1
-

:Gumbo (number) (expr)
+
sub eax, {0}
recurse {1}
-

:Banana (Gumbo (3) (Var (x))) (Gumbo (4) (Add (Var (x)) (Var (8))))
+
sub eax, 3
mov eax, [ebp-1]
sub eax, 4
mov eax, [ebp-1]
mov [ebp-1], eax
mov eax, [ebp-2]
add eax, [ebp-1]
- 


