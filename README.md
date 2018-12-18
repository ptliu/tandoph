**Abstract**: We propose Tandoph, a framework and tool for automating
the construction of compilers, from either I/O examples or constraints.
Our work introduces many of the problems of automating compiler
generation, and attempts to solve some of these issues by employing
program synthesis techniques such as representation based search and
pruning. As a tool, Tandoph is able generate compilers quickly from user
constraints specified in a new, intuitive language we call “Skeleton
Code”, and is also able to synthesize a compiler based on multiple
real-world input/output examples of how arbitrary Abstract Syntax Trees
should compile to x86. Tandoph is able to synthesize compilers for
Abstract Syntax Trees that employ integers, variables, looping, and
conditionals, but due to the variety of ways functions are compiled in
the real world, we could not devise an acceptable framework for learning
how to compile functions from examples.

Introduction
============

Compilers, in essence, are functions that take a string $s$ in a given
input language, and return a string $p$ in the target language, such
that the semantics of $s$ and $p$ are identical in their respective
languages. The field of compiler development is almost as old as the
idea of high-level languages, but for the most part, each compiler
targets a specific input language and a specific output language,
Noticeable exceptions exist, such as the Production-Quality
Compiler-compiler project, as well as the META II project, but recent
work seems to have forsaken generalized compilers in favor of optimizing
the output programs

We observe that the process of writing a generalized compiler suffers
from two issues. Firstly, the specification of input programming
languages often causes difficulty in parsing, such that non-identical
input programs can have the same semantics. Secondly, the implementation
of general rules converting input programming language constructs to
equivalent output constructs is a difficult problem to generalize to
multiple input languages. We chose not to focus on the first issue, as
it is better handled by specialized lexing and parsing tools, but
instead focus on the second: building a generalized framework to convert
arbitrary input language constructs to output language constructs.

Our goal was to apply programming synthesis techniques to synthesize a
compiler for arbitrary language constructs to x86 assembly while simply
given pairs of input-output examples, allowing the language designer to
simply provide instructive examples to our tool regarding how to compile
various language constructs, and let the tool generalize those examples
to the entire language.

Related Work
============

META II
-------

@meta The META II project is the project whose goals and technique most
closely match our work. META II gives the user the ability to write
syntax rules for converting arbitrary constructs in the input language
to assembly, and uses as its conversion method direct string search and
replacement. META II was targeted toward imperative languages similar to
the ALGOL family, but could target an arbitrary architecture. META II
also could be implemented using its own rule language, a first for a
compiler-compiler.

Tandoph uses string search ideas similar to those present in META II,
but in lieu of the user specifying explicit syntax rules, Tandoph can
infer those syntax rules from input-output examples. Additionally,
Tandoph will use any user-side assembly optimizations in its
input/output examples in its generated compiler. However, META II
supports user-defined functions and functions, a capapbility Tandoph
currently lacks.

Production Quality Compiler-compiler
------------------------------------

@pqcc The Production Quality Compiler-Compiler(PQCC) is a project whose
goals are similar, but wider than scope than ours. This project’s goal
was to build a tool that could generate a compiler from an arbitrary
unparsed input language to assembly for an arbitrary architecture, with
performance on par with a handwritten compiler.The project introduces
the idea of a division of duties between a parser of the input language
and a compiler to generate assembly, with abstract syntax tree(AST) as
an intermediary language. In our work, we borrow the idea of an AST to
use as our input language, and retain the idea of an arbitrary input
language. In contrast to the declarative descriptions of the input and
output language required by the PQCC, we require only input/output
examples, and in exchange only target one architecture.

Unfortunately, it seems that the PQCC project was not completed, and no
finished product was delivered.

MYTH
----

@osera MYTH is, unlike previous works, a tool that can synthesize
programs that handle recursive data structures containing algebraic
datatypes. It does so by using type annotations on synthesized functions
in conjunction with input-output examples, over an ML-like input
language. The most notable feature of MYTH is its ability to quickly
synthesize functions that require pattern matching, making it
well-suited for recursively processing data structures.

Because ASTs are a recursive data type, one could imagine applying MYTH
to the domain of compiler synthesis, by feeding it a function signature
of a compile function $f :: AST -> [x86asm]$ as well as our input-output
examples, and attempt to have it synthesize a compiler in this way. The
authors did not choose to pursue this route, but future work could
include using MYTH to synthesize compilers for comparison purposes.

We would like to thank Nadia Polikarpova for providing the impetus for
this project, as well as guidance along the way, Peter-Michael Osera for
providing us a working version of MYTH, and Ranjit Jhala for providing
guidance during the early planning phase of the project.

Appendix
========

The following is the set of input/output examples used for the
Evaluation section.


    :Num (1)
    +
    mov eax,1
    -

    :Num (2)
    +
    mov eax,2
    -

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

    :Num (nat)
    +
    mov eax,{0}
    -

    :Var (var)
    +
    mov eax,[ebp-@0]
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
