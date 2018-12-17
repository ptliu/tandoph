import joblib
import asm_to_symbolic as patrick
import json
import re
import sys
from enum import Enum
import copy

class ArgType(Enum):
  REG = "REG"
  NAT = "NAT" 
  NAT_HOLE = "NAT_HOLE"
  NAT_DEP = "NAT_DEP" 
  REG_OFF = "REG_OFF"
  VAR_HOLE = "VAR_HOLE"
  VAR = "VAR"
  RECURSE = "RECURSE"
  LABEL = "LABEL"
  BRANCH = "BRANCH"
  NULL = "NULL"

class Function():
  def __init__(self,name):
    self.name = name
    self.examples = list()
    self.termExamples = list()
    self.isTerminal = False
    self.ordering = list()
    self.isCompilable = False
    self.skeleton = list()
    self.body = list()
    self.nArgs = 0
  def addExample(self,arguments,x86):
    example = (arguments,x86)
    self.examples.append(example)
             
  def inferTerminal(self):
    self.isTerminal = False
    for example in self.examples:
      if terminalArguments(example[0]) == False:
        return
    self.isTerminal = True

  def infer(self,functions):
    self.inferTerminal()
    if self.isTerminal == True:
      self.body,self.nArgs = examplesToBody(self.examples)
      self.isCompilable = True
      self.termExamples = self.examples
    else:
      self.isCompilable = True
      self.examples = constructTerminalExamples(self.examples,functions)      
      self.body,self.nArgs = examplesToBody(self.examples)
      self.termExamples = self.examples 

# "learn recursion"
def constructTerminalExamples(examples,functions):
  # look for the nonterminal arguments
  # and ensure that they line up
  # get the argument matrix 
  argCol = list()
  for example in examples:
    arguments = example[0]
    argCol.append(arguments)
  termArgsMat,recArgsMat = getTermArgsMat(argCol)
  # split into terminal arguments and recursive arugments
  numExamples = len(recArgsMat)
  ambiguous = dict() 
  concrete = list()
  
  # for each in the recArgsMat 
  for ex in range(len(recArgsMat)):
    recArgs = recArgsMat[ex] 
    for rec in recArgs:
      #rec = recArgs[r] 
      nonTerminalExpression, argIndex = rec[0],rec[1]
      fullInstructions = instrListToString(examples[ex][1]) # the full x86
      name, arguments, i = parseASTFromString(nonTerminalExpression,compiling=True)
      assert functions[name].isCompilable 
      
      filledBody = compileAST(nonTerminalExpression,dict(),0,functions)    
      instrList = bodyToInstrObject(filledBody)  
      instrString = instrListToString(instrList)
      #print(ex,fullInstructions)
      #print(ex,instrString)
      find = re.findall(instrString,fullInstructions)
      if len(find) > 1:
        #print(find)
        if ex not in ambiguous:
          ambiguous[ex] = list()
        ambi = [instrString,fullInstructions,argIndex]
        pile = ambiguous[ex]
        pile.append(ambi) 
        ambiguous[ex] = pile
        continue
      if len(find) == 0:
        print("Couldn't match the recursion")
        print(fullInstructions)
        print(instrString)
        assert False 
      filledInstruction = re.sub(instrString,'RECURSE,{' + str(argIndex) + '},_',fullInstructions)
      filledInstruction = '[' + filledInstruction + ']'
      #print(ex,filledInstruction)
      i = 0
      instr,i = parseASMFromString(filledInstruction,i)
      instr = tokenizeASM(instr)
      newExample = (examples[ex][0],instr)
      examples[ex] = newExample
      concrete.append(ex)
    if len(ambiguous) == rec:
      print("Ambiguous recursion in all examples")
      assert False
  
  # repairing ambiguous examples  
  for ex in ambiguous:
    ambi = ambiguous[ex]
    s = ambi[0][1]
    problemList = list()
    for t in range(len(ambi)):
      problem = list()
      currAmbi = ambi[t]
      problem.append(currAmbi[0]) # arg 1 is the pattern
      problem.append(currAmbi[2]) # arg 2 is the argIndex
      problemList.append(problem)
    sols = solutions(copy.deepcopy(problemList),s)
    # find the correct combination 
    good = examples[concrete[0]][1]
    for s in range(len(sols)):
      sol = sols[s]
      sol = '[' + sol + ']'
      solList,i = parseASMFromString(sol,0)
      instr = tokenizeASM(solList)
      if checkIfOkayRecursion(instr,good):
        break
      if s == (len(sols) - 1):
        print("Couldn't find a way to fit this example",ambi)
        assert False
    newExample = (examples[ex][0],instr)
    examples[ex] = newExample
  return examples

def checkIfOkayRecursion(canidate,good):
  if len(canidate) != len(good):
    return False
  for i in range(len(canidate)):
    instrc = canidate[i]
    instrg = good[i]
    if instrc[0] != instrg[0]:
      return False
    if instrc[0] == 'RECURSE':
      if instrc[1] != instrg[1]:
        return False  
  return True

def solutions(problemList,s): 
  problem = problemList[0]
  problemList.pop(0)
  pattern = problem[0]
  nPlaces = len(re.findall(pattern,s))#problem[0]
  arg = 'RECURSE,{' + str(problem[1]) + '},_'
  sols = list()
  if len(problemList) == 0:
    for i in range(nPlaces):
      sols.append(replaceNth(s,pattern,arg,i+1))
  else:
    for i in range(nPlaces):
      canidate = (replaceNth(s,pattern,arg,i+1))
      canidates = solutions(copy.deepcopy(problemList),canidate)
      sols = sols + canidates
  return sols 
 
def replaceNth(s, source, target, n):
    inds = [i for i in range(len(s) - len(source)+1) if s[i:i+len(source)]==source]
    if len(inds) < n:
        return  # or maybe raise an error
    s = list(s)  # can't assign to string slices. So, let's listify
    s[inds[n-1]:inds[n-1]+len(source)] = target  # do n-1 because we start from the first occurrence of the string, not the 0-th
    return ''.join(s)

def bodyArgToString(arg):
  if arg[0] == ArgType.NAT:
    return arg[1]
  elif arg[0] == ArgType.REG:
    return arg[1] 
  elif arg[0] == ArgType.REG_OFF:
    if arg[2][0] == ArgType.NAT_DEP:
      assert False
    return '|' + arg[1][1] + '-' + (arg[2][1]) + '|' 
  elif arg[0] == ArgType.LABEL:
    return "label"
  elif arg[0] == ArgType.NULL:
    return "_"
  else:
    print(arg)
    assert False

def bodyToInstrObject(body):
  instrObjectList = list()
  for i in range(len(body)):
    instr = body[i] 
    command = instr[0]
    argStr1 = bodyArgToString(instr[1])
    argStr2 = bodyArgToString(instr[2]) 
    instrObject = (command,argStr1,argStr2)
    instrObjectList.append(instrObject)
  return instrObjectList
 
def generalize(argument,command,arg):
  if jumpable(command):
    if arg == 2:
      return '_'
    if arg == 1:
      return 'label' 
  if '|' in argument:
    return 'EBP'
  return argument
 
def instrListToString(instructions):
  string = ""
  for i in range(len(instructions)):
    instr = instructions[i]
    command = instr[0]
    string = string + command + ',' + generalize(instr[1],command,1) + ',' + generalize(instr[2],command,2)
    if i != len(instructions) - 1:
      string = string + ";"
  return string


def matchHole(arg,arguments):
  if arg[0] == ArgType.NAT:
    return arg
  elif arg[0] == ArgType.REG:
    return arg
  elif arg[0] == ArgType.NAT_HOLE:
    index = int(arg[1][1])
    arg[0] = ArgType.NAT
    arg[1] = arguments[index]
    return arg
  elif arg[0] == ArgType.REG_OFF:
    if arg[2][0] == ArgType.NAT:
      return arg
    elif arg[2][0] == ArgType.NAT_HOLE:
      arg[2][0] = ArgType.NAT
      index = int(arg[2][1][1])
      arg[2][1] = arguments[index]
    return arg
  print("not valid",arg)
  assert False 


def argUsesVarHole(arg):
  if arg[0] == ArgType.REG_OFF:
    off = arg[2]
    if off[0] == ArgType.VAR_HOLE:
      return True
  return False 

def varHoleToVar(arg,arguments):
  assert arg[2][0] == ArgType.VAR_HOLE
  index = int(arg[2][1][1]) 
  variable = arguments[index]
  varArg = [ArgType.VAR,variable]
  arg[2] = varArg
  return arg 

def varToNat(arg,stack,frame):
  assert arg[2][0] == ArgType.VAR
  variable = arg[2][1]
  if "@TEMP" in variable:
    variable = variable + str(frame)
  if variable in stack:
    offset = stack[variable]
  else:
    offset = len(stack) + 1
    stack[variable] = str(offset)
  nattyArg = [ArgType.NAT,str(offset)]
  arg[2] = nattyArg
  return arg,stack
     
def argHasVar(arg):
  if arg[0] == ArgType.REG_OFF:
    off = arg[2]
    if off[0] == ArgType.VAR:
      return True
  return False 

def compileAST(expression,stack,frame,functions):  
  name, arguments, i = parseASTFromString(expression,compiling=True)
  if not functions[name].isCompilable:
    print(name,"is not compilable yet!")
    assert False
  if len(arguments) != functions[name].nArgs:
    print("Wrong number of arguments!")
    assert False
  body = functions[name].body
  filledBody = list()
  for instruction in body:
    command = instruction[0]
    arg1 = copy.deepcopy(instruction[1])
    arg2 = copy.deepcopy(instruction[2])
    if command == "RECURSE":
      index = int(instruction[1][1][1])
      recursed = compileAST(arguments[index],copy.deepcopy(stack),frame+1,functions)
      for rec in recursed:
        filledBody.append(rec)
      continue
    elif jumpable(command):
      lab = instruction[1][1]
      if '!' not in lab:
        lab = lab + "_f" + str(frame)
      newInstruction = copy.deepcopy(instruction)
      newInstruction[1][1] = lab
      filledBody.append(newInstruction)
      continue
    else:
      if argUsesVarHole(arg1):
        arg1 = varHoleToVar(copy.deepcopy(arg1),arguments)
      if argUsesVarHole(arg2):
        arg2 = varHoleToVar(copy.deepcopy(arg2),arguments)
      if argHasVar(arg1):
        arg1,stack = varToNat(copy.deepcopy(arg1),stack,frame)
      if argHasVar(arg2):
        arg2,stack = varToNat(copy.deepcopy(arg2),stack,frame) 
      arg1 = matchHole(copy.deepcopy(arg1),arguments)
      arg2 = matchHole(copy.deepcopy(arg2),arguments)
      filledBody.append([command,arg1,arg2])
  return filledBody

def terminalArguments(arguments):
  for arg in arguments:
    if "(" in arg:
      return False
  return True

# requires: that pivot i is on a "("
# ensures: that pivot i leaves on a ")"
def parseExpression(_input,i):
  assert _input[i] == "("
  stack = 1
  i += 1
  expr = ""
  while (stack > 0):
    char = _input[i]
    if char == "(":
      stack += 1
    elif char == ")":
      stack -= 1
    if stack != 0:
      expr += char
    i = i + 1
  i -= 1
  assert _input[i] == ")"
  return expr,i


# ensures: pivot i is on a "(" 
def parseFunctionName(_input):
  i = 0
  name = ""
  while (True):
    if _input[i] == " ":
      i += 1
      break
    name = name + _input[i]
    i += 1
  assert _input[i] == "("
  return name,i

# requires: pivot i is on a "("
# ensures: pivot i leaves on a "["
def parseFunctionArguments(_input,i,compiling=False):
  assert _input[i] == "("
  expressions = list()
  while (True):
    expr,i = parseExpression(_input,i)
    expressions.append(expr)
    if compiling == True:
      if i == len(_input) - 1:
        return expressions,i
    i += 1
    assert _input[i] == " "
    i += 1
    if _input[i] == "-":
      assert _input[i+1] == '>'
      assert _input[i+2] == " "
      i += 3
      break 
  assert _input[i] == "["
  return expressions, i 



# takes as input the user argument, and 
# attempts to parse out the AST. Returns
# function name, and the expressions that 
# function takes in as input arguments 
# requires: none
# ensures: pivot i is on a "["
def parseASTFromString(_input,compiling=False):
  name,i = parseFunctionName(_input)
  expressions, i = parseFunctionArguments(_input,i,compiling=compiling)
  return name,expressions,i


def parseForCompiling(_input):
  name,i = parseFunctionName(_input)
  


# parses out the assembly part of the user input 
# example
# requires: pivot "i" is on a "["
# ensures: pivot "i" is on a "]" 
def parseASMFromString(_input,i):
  assert _input[i] == "["
  instructions = list()
  instr = ""
  i += 1
  while (True):
    if _input[i] == ";":
      i += 1
      instructions.append(instr)
      instr = ""
      continue
    elif _input[i] == "]":
      instructions.append(instr)
      instr = ""
      break
    else:
      instr += _input[i]
      i += 1
  assert _input[i] == "]"
  return instructions,i

# turn a list of instructions into a list of (useful)
# tuples
def tokenizeASM(instructions):
  tokens = list()
  for instr in instructions:
    command, arg1, arg2 = instr.split(',')
    tokens.append((command,arg1,arg2))
  return tokens 


# returns the name, arguments and instructions for an example
# given as a formatted string
def parseExample(_input):
  name, expressions, i = parseASTFromString(_input)
  instructions, i = parseASMFromString(_input,i)
  instructions = tokenizeASM(instructions)
  return name, expressions, instructions

# processes an input and returns a dict that has updated 
# examples
def processExample(_input,functions):
  name, expressions, instructions = parseExample(_input)
  if name not in functions:
    newFunction = Function(name)
    functions[name] = newFunction
    newFunction.addExample(expressions,instructions)
  else:
    oldFunction = functions[name]
    oldFunction.addExample(expressions,instructions)
    functions[name] = oldFunction
  return functions


def examplesToSkeleton(examples):
  instCol = list()
  ninst = len(examples[0][1])
  for i in range(len(examples)):
    instructions = examples[i][1]
    assert ninst == len(instructions)
  skeleton = list()
  for i in range(ninst):
    instrCol = list()
    for e in range(len(examples)):
      instrCol.append(examples[e][1][i])
    skeleton.append(instrColToSkeleton(instrCol)) 
  return skeleton


def jumpable(command):
  if "JMP" in command:
    return True
  if "JNE" in command:
    return True
  if "JE" in command:
    return True
  if "LABEL" in command:
    return True
  return False 

# for single col!
def instrColToSkeleton(instructions):
  arg1list = list()
  arg2list = list()
  command = instructions[0][0]
  if command == "RECURSE":
    arg1 = [ArgType.RECURSE,instructions[0][1]] 
    arg2 = [ArgType.NULL]
    skeletonBlock = [command,arg1,arg2]
    return skeletonBlock
  if jumpable(command):
    arg1 = [ArgType.LABEL,instructions[0][1]]
    arg2 = [ArgType.NULL]
    skeletonBlock = [command,arg1,arg2]
    return skeletonBlock
  for instr in instructions:
    if instr[0] != command:
      assert False
    arg1list.append(instr[1])
    arg2list.append(instr[2])
  arg1 = inferArgument(arg1list)
  arg2 = inferArgument(arg2list)
  skeletonBlock = [command,arg1,arg2]
  return skeletonBlock    
 

def matchNat(natList,termArgsMat):
  nterms = len(termArgsMat[0])
  for i in range(nterms):
    argColNats = list()
    col = termArgsMat[0][i][1]
    for e in range(len(termArgsMat)):
      tup = termArgsMat[e][i]
      argColNats.append(tup[0])
    if argColNats == natList:
      return col
  assert False 
  
def parameterMatch(skelArg,termArgsMat,stack):
  argType = skelArg[0] 
  if argType == ArgType.NAT:
    return skelArg,stack
  elif argType == ArgType.REG:
    return skelArg,stack
  elif argType == ArgType.REG_OFF:
    if skelArg[2][0] == ArgType.NAT:
      natty = skelArg[2][1]
      inv_map = {v: k for k, v in stack.items()}
      if natty in inv_map:
        skelArg[2][0] = ArgType.VAR_HOLE
        skelArg[2][1] = '@' + str(inv_map[natty])
        return skelArg,stack     
      for ex in range(len(termArgsMat)):
        termies = termArgsMat[ex]
        for arg in range(len(termies)):
          var = termies[arg][0]
          index = termies[arg][1]
          chars = len(re.findall('[A-Za-z]',var))
          if chars > 0:
            if index not in stack:
              skelArg[2][0] = ArgType.VAR_HOLE
              skelArg[2][1] = '@' + str(index)
              stack[index] = natty
              break
      return skelArg,stack
    elif skelArg[2][0] == ArgType.NAT_DEP:
      natList = skelArg[2][1]
      col = matchNat(natList,termArgsMat)
      skelArg[2][1] = "{" + str(col) + "}"
      skelArg[2][0] = ArgType.NAT_HOLE;
      return skelArg,stack
    elif skelArg[2][0] == ArgType.NAT_HOLE:
      return skelArg,stack
    elif skelArg[2][0] == ArgType.VAR_HOLE:
      return skelArg,stack
    elif skelArg[2][0] == ArgType.VAR:
      return skelArg,stack
    else:
      assert False
  elif argType == ArgType.NAT_DEP:
    natList = skelArg[1]
    argParam = matchNat(natList,termArgsMat)
    skelArg[1] = "{" + str(argParam) + "}"
    skelArg[0] = ArgType.NAT_HOLE
    return skelArg,stack 
  elif argType == ArgType.NAT_HOLE:
    return skelArg,stack
  elif argType == ArgType.RECURSE:
    return skelArg,stack
  elif argType == ArgType.NULL:
    return skelArg,stack
  elif argType == ArgType.LABEL:
    return skelArg,stack
  assert False

def examplesToBody(examples):
  argCol = list()
  for example in examples:
    arguments = example[0]
    argCol.append(arguments)
  nArgs = 0
  for col in argCol[0]:
    nArgs += 1
  skeleton = examplesToSkeleton(examples) 
  body = list()
  stack = dict()
  for skeletonBlock in skeleton:
    #print("examplesToBody",skeletonBlock)
    bodyBlock,stack = skeletonBlockToBodyBlock(skeletonBlock,argCol,stack)
    body.append(bodyBlock)
  return body,nArgs



# takes in the arguments (of all examples)
# and gets a list of the terminal arguments, 
# with their indicies (i.e. which argument they
# are)
def getTermArgsMat(argCol):
  termArgsMat = list()
  recArgsMat = list()
  for example in argCol:
    termArgs = list()
    recArgs = list()
    for i in range(len(example)):
      argument = example[i]
      if "(" not in argument:
        termArgs.append((argument,i))
      else:
        recArgs.append((argument,i))
    recArgsMat.append(recArgs)
    termArgsMat.append(termArgs)
  # term args mat is now kind of a argCol of just terminals
  firstExample = termArgsMat[0]
  terminalIndices = list()
  for tup in firstExample:
    terminalIndices.append(tup[1]) 
  for example in termArgsMat:
    ti = list()
    for tup in example:
      ti.append(tup[1])
    assert ti == terminalIndices
  return termArgsMat,recArgsMat 

 
# for single col!
def skeletonBlockToBodyBlock(skeletonBlock,argCol,stack):
  #print("Block to match: \t",skeletonBlock)
  # process for terminal arguments
  termArgsMat,recArgsMat = getTermArgsMat(argCol)
  skelArg1 = skeletonBlock[1]
  skelArg2 = skeletonBlock[2]
  #stack = dict()
  skelArg1Update,stack = parameterMatch(skelArg1,termArgsMat,stack)
  skelArg2Update,stack = parameterMatch(skelArg2,termArgsMat,stack)
  skeletonBlock[1] = skelArg1Update
  skeletonBlock[2] = skelArg2Update
  return skeletonBlock,stack


def isRegThing(string):

  registers = list()
  registers.append("EAX")
  registers.append("EBP")
  registers.append("ECI")
  registers.append("ESP")
  registers.append("ECX")

  for reg in registers:
    if reg in string:
      return True
  else:
    return False


def inferArgument(tokens):
  # tokens is a column of strings 
  # is the first one a number thing 
   
  # assert consistency  
  isReg = isRegThing(tokens[0])
  for token in tokens:
    assert isReg == isRegThing(tokens[0])

  if "@TEMP" in tokens[0]:
    tempName = tokens[0]
    for token in tokens:
      assert tempName == token
    return [ArgType.REG_OFF,[ArgType.REG,'EBP'],[ArgType.VAR,tempName]]
 

  # number things are easy- either a constant, or param
  if not isReg:
    
    # can be a:
    # constant -> NAT
    # constant inferable hole -> NAT_DEP
    # explict hole

    # check to see if it's an explict hole 
    isExplicitHole = '{' in tokens[0]
    if isExplicitHole:
      for token in tokens:
        assert token == tokens[0]
      return [ArgType.NAT_HOLE, tokens[0]]  
         

    # is a hole, or a nat 
    # check to see if it's a constant
    isNumConst = True
    for token in tokens:
      if token != tokens[0]:
        isNumConst = False
    if isNumConst:
      return [ArgType.NAT,tokens[0]]
    else:
      return [ArgType.NAT_DEP,tokens]
  else:
    # else it's a register thing, or a variable 
    if "|" == tokens[0][0]:
      # it's a stack access
      # we know it's [REG-NUM]
      reg = tokens[0][1:4]
      numList = list()
      for token in tokens:
        assert token[1:4] == reg 
        assert token[4] == "-"
        i = 5
        num = ""
        while token[i] != "|":
          num = num + token[i]
          i+= 1
        numList.append(num)     
      isNumConst = True
      numBoy = numList[0]
      for token in numList:
        if token != numBoy:
          isNumConst = False
      if not isNumConst:
        if '@' in numBoy:
          assert False
        if reg != "EBP":
          assert False
        return [ArgType.REG_OFF,[ArgType.REG,reg],[ArgType.NAT_DEP,numList]] 
      if '@' in numBoy:
        if reg != "EBP":
          assert False
        return [ArgType.REG_OFF,[ArgType.REG,reg],[ArgType.VAR_HOLE,numBoy]]
      if '{' in numBoy:
        if reg != "EBP":
          assert False
        return [ArgType.REG_OFF,[ArgType.REG,reg],[ArgType.NAT_HOLE,numBoy]] 
      return [ArgType.REG_OFF,[ArgType.REG,reg],[ArgType.NAT,numBoy]] 
    else:
      for token in tokens:
        if token != tokens[0]:
          assert False 
      return [ArgType.REG,tokens[0]]


def getPrettyArg(arg,delim1='[',delim2=']'):
  pretty = ""
  if arg[0] == ArgType.NULL:
    return pretty
  elif arg[0] == ArgType.REG_OFF:
    regArg = arg[1]
    pretty += delim1 + regArg[1] + '-'
    numArg = arg[2]
    pretty += numArg[1] + delim2
    return pretty
  else:
    pretty += arg[1]
    return pretty


def justOnePlease(arg):
  if arg == "RECURSE":
    return True
  if arg == "PUSH":
    return True
  if arg == "MUL":
    return True
  if jumpable(arg):
    return True
  if arg == "POP":
    return True
  return False

def prettyPrintBody(body,asm=False):
  for instr in body:
    command = instr[0]
    arg1 = instr[1]
    arg2 = instr[2]
    if jumpable(command):
      if command == "LABEL":
        print(getPrettyArg(arg1).lower() + ":") 
      else:
        print(command.lower(),getPrettyArg(arg1).lower())
    elif justOnePlease(command):
        print(command.lower(),getPrettyArg(arg1).lower())
    else: 
      print(command.lower(),getPrettyArg(arg1).lower() + ', ' + getPrettyArg(arg2).lower())

def x86ToUglyString(body):
  output = "["
  for i in range (len(body)):
    instr = body[i]
    command = instr[0]
    arg1 = instr[1]
    arg2 = instr[2]
    if jumpable(command):
      output = output + command + "," + arg1[1] + ",_"
    else:
      pretty1 = getPrettyArg(arg1,delim1='|',delim2='|')
      pretty2 = getPrettyArg(arg2,delim1='|',delim2='|')
      output = output + command + "," + pretty1 + "," + pretty2
    if i != len(body) - 1:
      output = output + ';'
  output += "]"
  return output


def learnExamples(jfile):
  functions = dict()

  with open(jfile,"r") as f:
    examples = json.loads(f.read()) 
    for example in examples:
      # get output symbolic ASM
      _output = example["output"]
      if _output == "file":
        with open(example["outFile"]) as outfile:
          symbASM = patrick.asm_to_symbolic(outfile)
      else:
        symbASM = patrick.asm_to_symbolic(_output) 
            
      # get input AST
      _input = example["input"]
      if _input == "file":
        with open(example["inFile"]) as infile:
          ast = infile.read().strip()
      else:
        ast = _input
      ex = ast + " -> " + symbASM       
      functions = processExample(ex,functions)
  for name in functions:
    functions[name].infer(functions)
  joblib.dump(functions,"obj/functions.o")   

def learnEasy(inputFile):
  functions = dict()
  f = open(inputFile,"r")
  _input = ''
  asmList = list()
  for line in f:
    chars = len(re.findall('[A-Za-z]',line))
    if line[0] == '$':
      break
    if line[0] == '+':
      asmList = list()
    elif line[0] == '-':
      x86 = patrick.asm_to_symbolic_string(asmList)
      ex = _input + ' -> ' + x86
      functions = processExample(ex,functions)
    elif (line[0] == ':'):
      _input = line[1:len(line)-1].strip()
    elif line[0] == '_':
      sys.exit(-1)
    elif chars == 0:
      continue
    else:
      asmList.append(line.strip())
  for name in functions:
    functions[name].infer(functions)
  joblib.dump(functions,"obj/functions.o")   
   
     

def compileInput(inputFile):
  functions = joblib.load("obj/functions.o")
  f = open(inputFile,"r")
  _input = f.read().strip()
  x86 = compileAST(_input,dict(),0,functions)
  prettyPrintBody(x86)

def compileEasy(expr):
  functions = joblib.load("obj/functions.o")
  x86 = compileAST(expr,dict(),0,functions)
  prettyPrintBody(x86)


if __name__ == "__main__":
  if len(sys.argv) != 3:
    print("Not enough input arguments")
    sys.exit(-1)
  if sys.argv[1] == "--learn":
    learnEasy(sys.argv[2])
  elif sys.argv[1] == "--compile":
    compileEasy(sys.argv[2]) 
  elif sys.argv[1] == "--check":
    name = sys.argv[2]
    functions = joblib.load('obj/functions.o')
    prettyPrintBody(functions[name].body)
  elif sys.argv[1] == "--examples":
    functions = joblib.load("obj/functions.o")
    for ex in functions[sys.argv[2]].examples:
      print("Input: ",ex[0],'\t','Output: ',ex[1])
  else:
    print("Please specify a flag")
    sys.exit(-1) 
