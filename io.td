:Num (1)
+
mov eax,1
- 

:Num (2)
+
mov eax,2
-







Num (5)
mov eax,10


Num (10)
mov eax,20
























:BiggerNum (3)
+
mov eax,3
add eax,1
-

:BiggerNum (2)
+
mov eax,2
add eax,1
-



















:Church (lambda f)
+
mov eax, 0
loop:
add eax, 1
cmp eax, {0}
jne loop
-























:HolyNum (not evil number)
+
trap:
mov eax,{0}
cmp eax, 666
je trap
-






























:Var (x)
+
mov eax, [ebp-1]
-






















:TwoVar (x) (y)
+
mov eax,[ebp-1]
mov ecx,[ebp-2]
-
























:Swap (x) (y)
+
mov eax,[ebp-1]
mov ecx,[ebp-2]
mov [ebp-1],ecx
mov [ebp-2],eax
- 




























































:Sub (expr) (expr)
+
recurse {0}
mov @temp1, eax
recurse {1}
sub @temp1, eax
-









:Let (x) (expr) (expr)
+
recurse {1}
mov [ebp-@0],eax
recurse {2}
-











:If (expr) (expr) (expr)
+
recurse {0}
cmp eax, 1
jne false
recurse {1}
jmp done
false:
recurse {2}
done:
-













:Add (expr) (expr)
+
recurse {0}
mov @temp1,eax
recurse {1}
add eax,@temp1
-















:Exp (exp) (exp)
+
recurse {0}
mov @temp1, eax
recurse {1}
mov @temp2, eax
mov ecx, 0
mov eax,1
loop:
mul eax, @temp1
add ecx, 1
cmp ecx, @temp2
jne loop
-







:Foobar (Let (a) (Num (3)) (Exp (Num (5)) (Add (Num (10)) (Var (a))))) (If (Var (a)) (Add (Var (a)) (Num (10))) (Add (Var (a)) (Num (10)))) (18)
+
mov eax,0
mov eax, 3
mov [ebp-1], eax
mov eax, 5
mov [ebp-2], eax
mov eax, 10
mov [ebp-3], eax
mov eax, [ebp-1]
add eax, [ebp-3]
mov [ebp-3], eax
mov ecx, 0
mov eax, 1
loop_f1:
mul eax, [ebp-2]
add ecx, 1
cmp ecx, [ebp-3]
jne loop_f1
add eax,ecx
cmp 0,ecx
mov eax, [ebp-1]
cmp eax, 1
jne false_f0
mov eax, [ebp-1]
mov [ebp-1], eax
mov eax, 10
add eax, [ebp-1]
jmp done_f0
false_f0:
mov eax, [ebp-1]
mov [ebp-1], eax
mov eax, 10
add eax, [ebp-1]
done_f0:
add eax, 18
-




















:Recurse (HolyNum (1)) (Var (x))
+
sub eax,4
mov eax,[ebp-3]
mov ecx, 25
label:
mov eax,1
cmp eax,666
je label
mul eax
-


























:Ambi (Num (1)) (Num (1))
+
mov eax,1
mov eax,1
-


:Ambi (Num (2)) (Num (3))
+
mov eax,2
mov eax,3
-






























:Def (expr) (expr)
+
!funcHandle:
push ebp
recurse {0}
pop ebp
recurse {1}
-








