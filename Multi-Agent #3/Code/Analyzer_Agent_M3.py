from Agent_class_M3 import AgentState
from langchain_core.messages import AnyMessage, SystemMessage
from langchain.prompts import PromptTemplate
import ast
import javalang

#redo this whole thing
Code_Analyzer_prompt = PromptTemplate(
    template="""
You are an expert compiler engineer fluent in {input_language} and {target_language}.  
Your job is to analyze {input_language} code to help another agent translate it into {target_language} correctly and idiomatically.  
The goal is to create a faithful and high-quality translation of the function.

### Instructions
1. Read the {input_language} code and AST analysis carefully.
2. Think step-by-step:  
   - Logic flow  
   - Control structures (branches, loops)  
   - Data types and data structures  
   - Language-specific pitfalls  
   - Special cases (edge conditions, errors)
3. Use the provided sample inputs to better understand input expectations and output behaviors.
4. Perform a Self-Consistency Check:
   - Double-check that your logic matches the AST.
   - Check that the sample inputs align with your understanding.
5. Then output exactly four sections as described below.

**Important:**  
- Do not perform a full translation. Write *pseudocode* instead using {target_language} idioms.
- Think carefully about differences between languages (especially typing, indexing, mutability, and numerical operations).
- You may write your thoughts and reasoning in the output.

### Output Format (markdown)

#### 1. Purpose
- A plain-English summary (≤ 3 sentences) of what the code does.

#### 2. Detailed Walk-through
- Numbered execution flow:
  1. Key variables initialized.
  2. Branches, conditions, loops, and recursion.
  3. External calls, I/O behavior, exceptions.
  4. Time and memory complexity analysis.
- Perform a mini checklist:
  - Inputs handled?
  - Outputs assigned?
  - Branching behavior covered?
  - Edge cases or special handling noted?

#### 3. Translation Watch-list
- Bullet list of specific risks or pitfalls when translating from {input_language} to {target_language}.
- You must include concerns about:
  - Division and rounding
  - Indexing (0-based vs 1-based)
  - Type casting (e.g., int to float)
  - Overflow risks (bounded int types)
  - Collection handling differences
  - Mutability and default arguments

- (Optional but recommended)  
  Briefly mention what *could go wrong* if misunderstood.

#### 4. Pseudocode in {target_language}
- Properly indented pseudocode.
- Use {target_language} syntax and structure where natural.
- Keep variable names clear and logical.
- Use comments (`##`) to flag any tricky translation spots (mutability, indexing shift, etc.).
- Do not add imports, boilerplate, or extra explanations.

End your output with:
`--- END OF ANALYSIS ---`

---

### Provided Inputs:
- **Input Code**:  
{input_code}

- **AST Analysis**:  
{AST_analysis}

- **Sample Inputs**:  
{sample_inputs}

""", 
input_variables=["input_language","target_language","input_code", "AST_analysis", "sample_inputs"])


def Analyze_code(state: AgentState):
    """
    Analyzes the code and returns the analysis
    input:
        input_code: the Raw input code
        sample_inputs: the example inputs to the input code
        AST_analysis: the AST of the input code
    output:
        Code_analysis: the analysis of the code
    """
    model = state['model']
    
    messages = [
        SystemMessage(content=Code_Analyzer_prompt.format(input_language = state["input_lang"], 
                                                          target_language = state["output_lang"], 
                                                          input_code = state["input_code"],
                                                          AST_analysis = state["AST_analysis"],
                                                          sample_inputs = state["sample_inputs"]))]
    
    response = model.invoke(messages).content
    Translator_history = response
    # print("Code_analysis: ", response)
    return {"Code_analysis": response, "History": Translator_history}


    
def remove_imports(java_code: str):
    """
    Removes all 'import' statements from the given Java code string
    and adds a closing '}' at the end.
    """
    lines = java_code.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith('import')]
    result = "\n".join(filtered_lines)
    
    # Add closing brace if not already present
    if not result.strip().endswith('}'):
        result += '\n}'
    
    return result

def Analyze_AST(state: AgentState):
    """
    Analyzes the AST of the code
    input:
        input_code: the Raw input code
    output:
        AST_analysis: the string representation of the AST analysis
    """
    
    
    try:
        if state["input_lang"].upper() == "PYTHON":
            tree = ast.parse(state["input_code"])
            # Convert to string representation for better serialization
            return {"AST_analysis": ast.dump(tree, indent=2)}
        elif state["input_lang"].upper() == "JAVA":
            tree = javalang.parse.parse(remove_imports(state["input_code"]))
            # Convert to string representation
            return {"AST_analysis": str(tree)}
        else:
            raise ValueError(f"Unsupported language: {state['input_lang']}")
    except Exception as e:
        print("AST has failed")
        print(state["input_code"])
        print(remove_imports(state["input_code"]))
        print("tree: ", javalang.parse.parse(remove_imports(state["input_code"])))
        return {"AST_analysis": "No AST analysis"}


