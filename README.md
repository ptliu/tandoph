# Tandoph


Tandoph can generate compilers from a mix of **direct specifications** and **examples**. For instance, consider
given specifications for *Num*, *Var*, and *Add*:


![Image of Num](https://raw.githubusercontent.com/ptliu/tandoph/master/examples/num.png)

![Image of Var](https://raw.githubusercontent.com/ptliu/tandoph/master/examples/var.png)

![Image of Add](https://raw.githubusercontent.com/ptliu/tandoph/master/examples/add.png)






From specifications, Tandoph can compile arbitrary expressions in a CLI: 

![Image of exampleAdd](https://raw.githubusercontent.com/ptliu/tandoph/master/examples/addExample.png)





Tandoph can also learn from hard expressions, and by inferring the specifications from examples, using 
enumeration and program synthesis techniques:

![Image of banana](https://raw.githubusercontent.com/ptliu/tandoph/master/examples/banana.png)

And compile novel expressions:

![Image of for](https://raw.githubusercontent.com/ptliu/tandoph/master/examples/compileBananaFor.png)


Including very complex examples:

![Image of for](https://raw.githubusercontent.com/ptliu/tandoph/master/examples/foobar.png)







