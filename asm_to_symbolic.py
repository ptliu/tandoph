import sys
import string
import re
def asm_to_symbolic(f):
  outstring = []
  for line in f:
    if(line == "\n"):
      continue

    if(re.search(r":", line.strip())):
      outstring.append("LABEL," + line.strip()[:len(line.strip()) - 1].upper() + ",_")
    else:  
      no_whitespace = line.split()
      for i in range(len(no_whitespace)):
        no_whitespace[i] = no_whitespace[i].replace("[", "|")
        no_whitespace[i] = no_whitespace[i].replace("]", "|")
      no_bracket = ",".join(no_whitespace[0:2]).upper()
      if(len(no_whitespace) >= 3):
        no_bracket = no_bracket + no_whitespace[2].upper()
      parts = no_bracket.split(",")
      if(len(parts) == 2):
        parts.append("_")
      outstring.append(",".join(parts))
  return "[" + ";".join(outstring) + "]"


def asm_to_symbolic_string(_input):
  outstring = []
  for line in _input:
    if(line == "\n"):
      continue

    if(re.search(r":", line.strip())):
      outstring.append("LABEL," + line.strip()[:len(line.strip()) - 1].upper() + ",_")
    else:  
      no_whitespace = line.split()
      for i in range(len(no_whitespace)):
        no_whitespace[i] = no_whitespace[i].replace("[", "|")
        no_whitespace[i] = no_whitespace[i].replace("]", "|")
      no_bracket = ",".join(no_whitespace[0:2]).upper()
      if(len(no_whitespace) >= 3):
        no_bracket = no_bracket + no_whitespace[2].upper()
      parts = no_bracket.split(",")
      if(len(parts) == 2):
        parts.append("_")
      outstring.append(",".join(parts))
  return "[" + ";".join(outstring) + "]"



if __name__ == "__main__":
  #this sometimes leaves the trailing bracket wtf
  if(len(sys.argv) != 3):
    print("Expected exactly 2 arguments")
    sys.exit(1)
  infile = sys.argv[1]
  with open(infile, "r") as f:
    result = asm_to_symbolic(f)
  
  outfile = sys.argv[2]
  with open(outfile, "w") as f:
    
    f.write(result)
