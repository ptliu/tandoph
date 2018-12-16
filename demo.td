:Num (1)
+
mov eax,1
-
:Num (10)
+
mov eax,10
-





:Var (x)
+
mov eax,[ebp-2]
-


:Swap (x) (y)
+
mov eax,[ebp-1]
mov ecx,[ebp-2]
mov [ebp-2],eax
mov [ebp-1],ecx
-


:Add (expr1) (expr2)
+
recurse {0}
mov @temp1,eax
recurse {1}
add eax,@temp1
-

:Let (a) (expr) (expr)
+
recurse {1}
mov [ebp-1],eax
recurse {2}
-
























