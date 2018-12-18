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

Methodology
===========

Skeleton Code To Describe Compiler Algorithms
---------------------------------------------

A compiler is a collection of routines that translate specific operators
from a source language to a target language. The structure of a compiler
program is an outer conditional that maps operators to their specific
compilation routine.

For each operator in the users source language, we wish to learn these
sequences of steps that compile that operator into x86. It seems almost
natural to represent this “sequence of compilation steps” as assembly
instructions themselves.

This sounds abstract, but consider compiling the familiar **Add**
instruction:\

$$\begin{aligned}
\text{Add (Num (3)) (Num (7))} \rightarrow \:
&\text{mov eax, 3} \\ 
&\text{mov ecx, eax} \\ 
&\text{mov eax, 7} \\
&\text{add eax, ecx} \\\end{aligned}$$

\

A standard compilation for **Add** will compile the first expression
(such that its result is in eax), then move that result into some
intermediary register for storage, compile the second expression, and
then sum their results. We can represent the logic of this routine in a
concise, symbolic way:\

$$\begin{aligned}
\text{Add (Expr1) (Expr2)} \rightarrow \:
&\text{recurse \{0\}} \\ 
&\text{mov @temp1, eax} \\ 
&\text{recurse \{1\}} \\
&\text{add eax, @temp1} \\\end{aligned}$$

\

This sequence of symbolic instructions succinctly represents the
algorithm for compiling **Add**.\

1.  recurse {0} $\rightarrow$ Compile the expression in argument 0

2.  mov @temp1, eax $\rightarrow$ Mov eax into some temporary storage

3.  recurse {1} $\rightarrow$ Compile the expression in argument 1

4.  add eax, @temp1 $\rightarrow$ Add the temporary storage to eax\

We call this symbolic assembly . *Skeleton code* describes directly the
algorithm needed to compile an operator. It is, essentially, assembly
with holes. Our task of synthesizing a program to compile a language
reduces to discovering the skeleton code for each operator that the user
specifies. Obviously, the learning power of our synthesizer is limited
by the representational power of the skeleton code. We have already seen
that the **recurse {?}** hole tells the compiler to compile argument
[?], and that the **@temp** hole tells the compiler to use a temporary
storage register. While at this point there’s no reason the user should
know how these constructs are learned from hard examples, we will first
demonstrate the remaining skeleton constructs that will prove useful
later.\

Consider this skeleton input/output example of the strange operator
**Banana**:\

$$\begin{aligned}
\text{Banana} \: (\text{x}) \: (\text{Expr1}) \: (11) \rightarrow \:
&\text{mov [ebp-@0],\:\{2\}} \\ 
&\text{recurse \{1\}} \\ 
&\text{mov [ebp-\{2\}],\:eax} \\
&\text{mul [ebp-3]} \\\end{aligned}$$

\

The first instruction, **mov [ebp-@0], {2}** contains two holes. The
**{2}** hole, in this context, matches a direct constant in the 2nd
argument of the AST (in this case, 11). This is intuitive enough;
however, examine the three ebp stack register holes:

**[ebp-@0]** accesses the stack register ebp at the location where the
variable in the 0th position is stored (in this case, x). **[ebp-{2}]**
accesses the stack register ebp at the location numerically described by
the constant in the 2nd argument (11). **[ebp-3]** simply accesses the
stack in the third position.

This reveals two things about Tandoph. Firstly, Tandoph is hard coded to
understand the difference between numbers and variables. While we
eventually want greater flexibility here, for the simple programs
Tandoph is capable of learning, this representational power was
adequate. Secondly, Tandoph is capable of learning user languages that
both access the stack symbolically, and directly. While most languages
do not feature this, we support it for the sake of the generality of the
learning algorithm.\

Compiling a hard example of **Banana** could yield:

$$\begin{aligned}
\text{Banana} \: (\text{x}) \: (\text{Add (Var (x)) (Num (2))}) \: (11) \rightarrow \:
&\text{mov [ebp-1], 11}\\
&\text{mov eax, [ebp-1]}\\
&\text{mov [ebp-2], eax} \\
&\text{mov eax, 2}\\
&\text{add eax, [ebp-2]}\\
&\text{mov [ebp-11],eax}\\
&\text{mul [ebp-3]}\\\end{aligned}$$

\

Where the compiler has chosen where to put the variable x, and where the
available temporary register in Add should go on the stack. The reader
may have noticed that Banana is an instance of the **Let** construct: a
variable is bound to a number, and used recursively in an expression.
The value of that expression is placed in a corresponding place on the
stack, and then multiplied by whatever is in the third location on the
stack.

Compiling hard examples of expressions, once the skeleton code is
learned, is simple. The list of skeleton instructions is applied
sequentially to produce a list of hard x86 instructions, with recursion
down non-terminal arguments when needed. A sketch of the compile
algorithm is as follows:

        def compileExpr (expression):
            operator = expression.name
            skeleton = operator.skeleton
            args = expression.arguments
            for instruction in skeleton:
                if instruction.command == recurse:
                    x86 = x86 +++ compileExpr(args[?])
                else:
                    x86 = x86 ++ fillSkeleton(instruction,args)
            return x86
        

The only method in this procedure that seems mysterious is
*fillSkeleton*, which takes in a non-recursive skeleton instruction
(like “mov @temp1, eax”) and, in conjunction with the arguments, as well
as the state of the current stack, turns it into a valid x86 instruction
(“mov [ebp-2], eax”). For the most part, this is simple pattern matching
and bookkeeping, and will not be described in detail.

As a final note, the Tandoph interpreter is able to take assembly input
as either hard assembly or skeleton code, in any combination. A user may
make half the instructions skeleton, and the rest of the instructions
hard, and Tandoph will perform unification and sort it out.\

Learning Holes: The Recursion Problem
-------------------------------------

Consider the problem of learning **Banana**’s skeleton code from the
previous section, given the hard example with Add. Forgetting about the
register access scheme, it would be very difficult to learn **Banana**
without knowing first knowing how Add is compiled. We would not know
which instructions “belonged” to **Banana** and which instructions
belonged to Add. Given examples with multiple nested operators, this
becomes intractable:

$$\begin{aligned}
\text{Belch (5) (Poodle (Zinger (Num (9)) (Num (2)))) (a)} \: \rightarrow \:
&\text{Mul [ebp-2]}\\
&\text{loop:}\\
&\text{Mov eax, [ebp-3]}\\
&\text{Add eax, ecx}\\
&\text{Mov eax, 9}\\
&\text{Sub eax, 9}\\
&\text{Mov eax, 2}\\
&\text{cmp ecx, eax}\\
&\text{bne loop}\\\end{aligned}$$

If we want to learn how to compile **Belch**, the only friend we can use
to decode this cryptic message is the familiar Num operator, which
intuitively will use 2 and 9 as direct constants and modify the eax
register. However, Tandoph does not possess such intuition about
predefined language constructs. To make matters worse, the flexibility
of the language space means that the variable “a”, and constants 5, 9,
and 2 need not appear in the assembly at all. An operator that takes in
thirty integer constants, and does nothing with any of them, is a silly
but valid operator that Tandoph should be able to learn, should Tandoph
be able to learn arbitrary language mappings.

One method of attacking this ambiguity is to employ enumerative search
over many examples of **Belch**, and to search for similarities. With
enough examples, surely the instructions associated with the top level
**Belch** can be isolated. However, this approach is inexact, and could
lead to incorrect compilers. We do not believe that an algorithm that
can synthesize an incorrect compiler is in anyway useful, so we opt for
a more deterministic algorithm by imposing a heavy constraint: Tandoph
can only learn top level expressions if its recursive arguments are
already inferred. That is, in order to compile **Belch**, Tandoph must
already know how to compile Poodle, Zinger and Num.

What remains here is pattern matching: When learning **Belch**, Poodle
can be recursively compiled and subtracted out from the examples,
leaving a non-recursive output example for **Belch**. This can be
implemented with string match: compile the recursive argument Poodle,
and then search the original instruction string for a match.

This is simple if the recursive argument matches exactly one substring,
in which case we simply snip it out and implant in its place a *recurse
{?}* instruction. However, what if there are multiple matches, or not
matches at all? What if the recursive substrings match different
arguments?

Recursive Ambiguity, Noise, and Exponential Search 
---------------------------------------------------

In the case that there are no matches at all, Tandoph must loosen the
restrictions on its string match. The most common cause of a mismatch is
the stack accesses and branches. Those vary with the frame of
compilation, and Tandoph can reasonably whiten those in the case of 0
matches, and keep trying. However, if all examples continually fail to
find a match, or if the substrings match different arguments, Tandoph
must eventually declare that the example is inconsistent.

The more interesting case is when Tandoph faces multiple substring
matches, in which case Tandoph must be able to repair examples. Consider
the operator **Sunscreen**:

$$\begin{aligned}
\text{Sunscreen (Num (1)) (Add (Num (8)) (Num (1))) (8)} \: \rightarrow \:
&\text{mov eax, 1}\\
&\text{mov eax, 8}\\
&\text{mov [ebp-2],eax}\\
&\text{mov eax, 1}\\
&\text{add eax, [ebp-2]}\\
&\text{sub eax, 8}\\\end{aligned}$$

Given that Num (1) compiles to “mov eax,1”, we cannot cannot determine
how this expression should compile. It is ambiguous. Tandoph, when given
a single ambiguous example, will need another example to clarify the
structure. The second example:

$$\begin{aligned}
\text{Sunscreen (Num (1)) (Num 2) (9))} \: \rightarrow \:
&\text{mov eax, 2}\\
&\text{mov eax, 1}\\
&\text{sub eax, 9}\\\end{aligned}$$

Clarifies the structure of Sunscreen. However, our job is not finished.
We do not wish to simply discard the first example as ambiguous, because
in more complex situations, all examples contain valuable information.
Instead, after learning the recursive structure of Sunscreen, we must
backtrack and repair the other examples, in order to store them for
future use. This process of repair is unfortunately exponential in
scope. If a recursive argument matches $n$ substrings, then we must
recursively match $n$ terms to determine which one matches the
non-ambiguous example. If there are $m$ recursive arguments that each
match $n$ terms, there are a combinatorial number of possible matches to
search. This does not seem like a problem with these small examples, but
runtime is significantly affected if the examples are larger in scope.

Learning Non-Recursive Holes: Representation Based Search
---------------------------------------------------------

Tandoph uses a representation based approach to learning holes from
examples. Examples are processed and turned into a skeleton tree that
gives multiple solutions to the hole, and then are compared against each
other for pruning. Non-recursive examples are able to be put in
alignment, and pattern matched to create the best fit. Consider examples
of the unknown operator **Sanic**, which has had its recursive arguments
marginalized out, but the non-recursive skeleton code is so far unknown:

$$\begin{aligned}
\text{Sanic (expr) (2) (y) (7)} \: \rightarrow \:
&\text{mov eax, 2}\\
&\text{mov eax, 1}\\
&\text{recurse \{0\}}\\
&\text{sub [ebp-1], 9}\\
&\text{mov [ebp-7], 7}\\\end{aligned}$$

Given one example, Tandoph can create a representational model that
represents a skeleton code with multiple solutions:

$$\begin{aligned}
\text{Sanic (expr) (2) (y) (7)} \: \rightarrow \:
&\text{mov eax, 2; mov eax, \{1\}}\\
&\text{mov eax, 1}\\
&\text{recurse \{0\}}\\
&\text{sub [ebp-1], 9; sub [ebp-@2],9}\\
&\text{mov [ebp-7], 7; mov [ebp-\{3\}],7; mov [ebp-\{3\}],\{3\}}\\\end{aligned}$$

Notice that we cannot assume that both [ebp-1] and [ebp-7] refer to y,
since only one register can be referenced at a time. Thus, we must store
a completely second branch of the code to account for this:

$$\begin{aligned}
\text{Sanic (expr) (2) (y) (7)} \: \rightarrow \:
&\text{mov eax, 2; mov eax, \{1\}}\\
&\text{mov eax, 1}\\
&\text{recurse \{0\}}\\
&\text{sub [ebp-1], 9}\\
&\text{mov [ebp-7], 7; mov [ebp-\{3\}],7; mov [ebp-@2], ....}\\\end{aligned}$$

Clearly, the number of skeleton representations is combinatorial, which
means hole matching is also an exponential problem. **Sanic** is also a
relatively simple operator; when you have multiple variable bindings,
the problem explodes even faster. These examples are stored in a tree
like structure, and upon receiving new examples, are pruned through
naive unification.

Not all sets of examples fully specify an exact skeleton code solution.
In this case, Tandoph uses some rules of thumb to prioritize its
compilation routine and to prune its search: if there are variables,
then they will be bound to stack registers given to it. If there are
constants, Tandoph will prefer to match instruction constants to
argument constants, unless additional examples require the alternative
to be consistent.

Admittedly, we considered the possibility of multiple variable bindings
late in the game, did not have time to implement the software to handle
a truly exponential case with multiple variable bindings. Tandoph at the
moment will only assume that multiple variable bindings are assigned in
the order in which variable arguments are presented in the AST. The
software was fragile by the time we got here, and a full redesign of the
interpreter would have been needed in the last two weeks to accommodate
building the representation tree recursively.

Evaluation
==========

Given the lack of strictly comparable work for modern architectures, we
decided to evaluate our work primarily on input expressions of
increasing difficulty. We now present a selected example of Tandoph
compiling a fairly complex program. The set of input/output examples
provided to Tandoph in this instance can be found in the appendix.

Challenges, Limitations, and Learning
=====================================

The scope of the project was larger than we originally intended. While
we had initially set out to be able to learn functions and lambda
constructs, we discovered that learning truly arbitrary language
constructs was already difficult. There is no reason why users should
not be able to specify examples such as Spicy:

$$\begin{aligned}
\text{Spicy (4) (2) (1) (y)} \: \rightarrow \:
&\text{mov eax, 9}\\
&\text{label:}\\\end{aligned}$$

Spicy takes in 4 non-terminals, does nothing with them, and moves 9 into
the working register. While this is absurd, it’s still a valid operator
a truly arbitrary compiler-compiler should be able to handle. While
Tandoph can learn the above absurd example, there are certain absurd
examples that Tandoph does not yet have the capacity to learn:

$$\begin{aligned}
\text{TimesThree (3)} \: \rightarrow \:
&\text{mov eax, 9}\\\end{aligned}$$

Tandoph Functions that map AST terminals to arbitrary functions, such as
times three, are not in the scope of Tandoph yet. However, Tandoph can
be extended to know them by adding the new hole type **@f(?)**, which
tells to learn a function. This extension; however, would spell trouble.
If Tandoph was given the ability to call another synthesizer to make an
example consistent, it would essentially lose the ability to declare
inconsistency, or generalize well. This mirrors exactly the problem of
overfitting in machine learning algorithms.

Not only was building exponential search algorithms for recursion and
hole-filling difficult, but a synthesizer that is completely agnostic to
language structure has a difficult time learning about very specific and
well structured concepts, such as function definitions, which are not
intuitive to compile. Compiler routines that handle function
definitions, in short, use tricks, and there are hundreds of routines
out there that are difficult enough for users to learn, let alone a
synthesizer. If Tandoph were to be able to handle functoins, it would
require some degree of hard coding to recognize them, which seemed
antithetical to the goal of a program that can learn arbitrary
compilation routines.

The restriction that we can only compile recursive arguments that have
already been inferred is probably our largest restriction. Tandoph needs
to be given input/output examples in order of complexity, which means it
is not applicable to assembly code found out in the wild, where a
compiler synthesizer would probably be of most use. Recall that the
problem with allowing for non-prior inferred arguments is that there
isn’t a strong guarantee that your array of small examples will contain
enough cribs to synthesize a correct compiler. If the Tandoph project
was to continue, it would abandon small scale user-guided examples, and
adopt the use of large corpuses of assembly. This might be the only way
around that limitation.

Future work and applications of Tandoph might be in decompiler
construction. Tandoph’s biggest strength is its ability to reason about
assembly recursively and cluster it, even with ambiguity: this
functionality could be extended to clustering large chunks of compilable
assembly into Abstract Syntax Trees.

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
