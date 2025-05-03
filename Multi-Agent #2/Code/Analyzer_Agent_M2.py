from Agent_class_M2 import AgentState
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage
from langchain.prompts import PromptTemplate
import ast
import javalang

#redo this whole thing
Code_Analyzer_prompt = PromptTemplate(
    template="""
### System
You are an expert compiler engineer fluent in {input_language} and {target_language}.  
Your job is to **analyze {input_language} code** to help another agent translate it into {target_language} correctly and idiomatically.

### Instructions
1. Read the {input_language} code
2. Think step-by-step:  
  logic, control flow, data structures, language-specific concerns.
3. Output exactly four sections as specified below.
4. Do not perform a full translation. Write *pseudocode* instead.

### Output Format (markdown)

#### 1. Purpose
A short plain-English summary of what the code does (≤ 3 sentences).

#### 2. Detailed Walk-through
Numbered execution flow:  
- Key variables  
- Branches / loops  
- External calls / I/O  
- Time and memory complexity

#### 3. Translation Watch-list
Bullet list of pitfalls when converting {input_language} → {target_language}  
(e.g., division behavior, mutability, 0/1 indexing, overflow, checked exceptions, type handling).

#### 4. Pseudocode in {target_language}
Concise, properly indented pseudocode using {target_language} idioms.  
Guidelines:  
- No imports or boilerplate  
- Clear variable names  
- Use comments (`##`) to flag tricky spots (mutability, casting, etc.)  
- Preserve logic structure exactly

End your output with:  
`--- END OF ANALYSIS ---`

---

### input code:
{input_code}

""", 
input_variables=["input_language","target_language","input_code"])


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
                                                          input_code = state["input_code"]))]
    
    response = model.invoke(messages).content
    Translator_history = response
    return {"Code_analysis": response, "Translator_history": Translator_history}

Input_Analyzer_prompt = PromptTemplate(
    template="""
You are a senior compiler engineer and software tester.
You are tasked generating two reports: a unit test input analysis and a script generation analysis to help two other agents with generating unit tests, 
and a script to plug the generated inputs into the input function and store the inputs and the outputs of the function in a JSON file respectively.

You are given the following information:
 - The input function for which you will be generating the unit test for
 - The AST of the input function
 - A Sample of what the input to the input function looks like

### Instructions
When writing your analysis:

In the `Unit Test Input Analysis` section (Goal: How to generate valid and meaningful test inputs.):
- Describe the expected input types, shapes, and constraints.
- Think about what values should be included to test normal and edge behaviors.
- Mention any values that should be avoided to prevent runtime errors.
- Describe a step-by-step strategy for generating safe, meaningful, and diverse inputs.

In the `Script Generation Analysis` section (Goal: How to design a script that runs the function with these inputs and saves results to a JSON file):
- Explain how a script should run the generated inputs through the function.
- Describe how outputs should be captured and organized.
- Explain how to save the results (inputs + outputs) to a JSON file with a clean and consistent structure.
- Identify pitfalls to watch out for (e.g., serialization issues, exception handling, file safety).

Inputs and outputs must:
- Be runnable in both {input_language} and {target_language}.
- Be deterministic and not involve random or environment-dependent behavior.
- Avoid language-specific behaviors that could cause output mismatches.

---

### Input

Input Function:  
{input_code}

Input AST:
{AST_analysis}

Example Input:
{example_inputs}

# Expected output format:
Unit Test Input Analysis:

the generated analysis for the unit test input

`--- END OF ANALYSIS ---`
#####
Script Generation Analysis:

the generated analysis for the script generation
  
`--- END OF ANALYSIS ---`
""", input_variables=["input_language","target_language","input_code","example_inputs","AST_analysis"])

def Analyze_UnitTest(state: AgentState):
    """
    Analyzes the code and returns the analysis
    input:
        input_code: the Raw input code
        Code_analysis: the analysis of the code
    output:
        UnitTest_analysis: the analysis the inputs and the function for the unit test
    """
    model = state['model']
    messages = [
        SystemMessage(content=Input_Analyzer_prompt.format(input_language = state["input_lang"], 
                                                           target_language = state["output_lang"], 
                                                           input_code = state["input_code"],
                                                           example_inputs = state["example_inputs"],
                                                           AST_analysis = state["AST_analysis"] ))]
    response = model.invoke(messages)
    UT_input_analysis, UT_script_gen_analysis = response.content.split("#####")

    UnitTest_history = """
Unit Test Input Analysis:
{UT_input_analysis}


Script Generation Analysis:
{UT_script_gen_analysis}


"""
    return {"UT_input_analysis": UT_input_analysis, "UT_script_gen_analysis": UT_script_gen_analysis, "UnitTest_history": UnitTest_history}


Regenerator_Analysis_prompt = PromptTemplate(
    template="""
### System
You are a senior software engineer and code debugger.  
Your task is to quickly and clearly analyze a code error and suggest possible fixes.

You will be given:
- The problematic code.
- The error message encountered.
- Optional extra information (e.g., function description, AST, notes).

You must **think step-by-step**, **identify the likely cause**, and **propose solutions**, but keep your writing **concise and efficient**.

---

### Output Format

Write three sections separated by `#####` headers:

- `##### Error Diagnosis`
- `##### Step-by-Step Reasoning`
- `##### Proposed Solutions`

Use clear, short paragraphs or bullet points. Avoid unnecessary elaboration.

---

#### In `Error Diagnosis`:
- Summarize the error in 1 to 2 sentences.
- Identify the general error type (e.g., syntax error, type error, runtime exception).

#### In `Step-by-Step Reasoning`:
- Briefly explain why the error happens.
- Mention key mistakes or mismatches found in the code.

#### In `Proposed Solutions`:
- List 1 to 3 possible fixes. (if the solution to the error is obvious, then just list 1 fix)
- One short sentence each.
- Mention trade-offs only if critical.

---

### Input

Extra Information (only if relevant):
{extra_info}

Code Causing Error:
{script_code}

Error Message:
{error_message}

""", input_variables=["script_code","error_message","extra_info"])

def Analyze_Regenerator(state: AgentState):
    """
    Analyzes the regenerator
    input:
        input_code: the Raw input code
    output:
        Regenerator_analysis: the analysis of the regenerator
    """
    model = state['model']
    messages = [
        SystemMessage(content=Regenerator_Analysis_prompt.format(script_code = state["input_code_analysis"], 
                                                          error_message = state["error_message_analysis"], 
                                                          extra_info = state["extra_info_analysis"] ))]
    
    response = model.invoke(messages).content
    return {"Regenerator_analysis": response}

def conditional_next_regen_node(state: AgentState):
    if state["Regen_return_node"] == "Unit Test Generator":
        return "Regen_code_UTest"
    
    elif state["Regen_return_node"].upper() == "FUNCTION":
        return "Function"
    
    elif state["Regen_return_node"].upper() == "UNIT TEST":
        return "Unit Test"
    else:
        print(state["Regen_return_node"])
        raise ValueError("Invalid Regenerator return node")
    
def remove_imports(java_code: str) -> str:
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




Deep_Code_Analyzer_prompt = PromptTemplate(
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


def Deep_Analyze_code(state: AgentState):
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
        SystemMessage(content=Deep_Code_Analyzer_prompt.format(input_language = state["input_lang"], 
                                                          target_language = state["output_lang"], 
                                                          input_code = state["input_code"],
                                                          AST_analysis = state["AST_analysis"],
                                                          sample_inputs = state["example_inputs"]))]
    
    response = model.invoke(messages).content
    Translator_history = response
    # print("Code_analysis: ", response)
    return {"Code_analysis": response, "Translator_history": Translator_history}
