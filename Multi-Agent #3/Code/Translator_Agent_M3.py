from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage
from Agent_class_M3 import AgentState, clean_generated_code
### Code Translator Prompt ###

Translation_prompt = PromptTemplate(
    template="""
You are a senior software engineer who excels at translating code between programming languages.

**Task**
Translate the function below from {input_language} to {target_language}.  
Return **only** the translated code, inside a single fenced code block.  
The function in your output **must** be named `f_filled`.

**Guidelines & Pitfalls to Avoid**

1. **Semantic fidelity** : the translated function must do exactly what the original does for all inputs.
2. **I/O contract** : keep the same parameters and return a value (do not print).
3. **Language-specific gotchas**  
   - *Integer vs float division* (`/`, `//`, `int()` casting).  
   - *Indexing & slicing* differences (inclusive vs exclusive ranges, 0-based arrays).  
   - *Mutable default arguments* (Python) : use `None` + inside-function init if needed.  
   - *Overflow / large-int handling* (Java `int` ↔ Python unlimited-int).  
   - *Loop constructs* (`for … range` vs `for (int i=… )`).  
   - *Short-circuit logic* (`&&`, `||` ↔ `and`, `or`).  
   - *Collection APIs* (`len(x)` vs `x.length` / `x.size()` / `Arrays.*`).  
   - *Exception equivalence* : raise/throw an analogous error type.  
   - *Boolean naming* conventions (`is_…`, `has…` in Python).  
4. **Keep algorithmic complexity and data structures intact** (lists ↔ arrays, maps ↔ dictionaries, etc.).
5. **No extra output** : absolutely no comments, explanations, or blank lines outside the code block.
6. {additional_instruction}

**Original Function ({input_language})**
{input_code}

**Input Function Analysis**
{Code_analysis}

**AST Analysis**
{AST_analysis}


expected output:
```{target_language}
translated_code
```

    """, input_variables = ["input_language", "input_code", "target_language", "additional_instruction", "Code_analysis", "AST_analysis"]
)


def Translator_node(state: AgentState): 
    """
    LLM node responsible for the code translation
    Output:
        output_code: the translated code
        Translator_status: the status of the translator set to "DONE" for Merge node
    """

    print("Translating the code - Translator")

    model = state['model']

    if state['output_lang'].upper() == "JAVA":
        extra_instruction = "Make the main class name Main"
    else:
        extra_instruction = ""

    messages = [
        SystemMessage(content=Translation_prompt.format(input_language = state["input_lang"],
                                                        input_code = state['input_code'], 
                                                        target_language = state["output_lang"], 
                                                        additional_instruction = extra_instruction,
                                                        Code_analysis = state["Code_analysis"],
                                                        AST_analysis = state["AST_analysis"])), 
    ]
    response = model.invoke(messages)

    # clean the code by removing back ticks
    clean_code = clean_generated_code(response.content)
    Translator_history = f"Translator: {clean_code} \n"
    # print("Translated_code: ", clean_code)
    return {"translated_code": clean_code, "History": state['History'] + Translator_history}


Translator_alone_prompt = PromptTemplate(
    template=
"""
You are a senior software engineer who excels at translating code between programming languages.

**Task**
Translate the function below from {input_language} to {target_language}.  
Return **only** the translated code, inside a single fenced code block.  
The function in your output **must** be named `f_filled`.

**Guidelines & Pitfalls to Avoid**

1. **Semantic fidelity** : the translated function must do exactly what the original does for all inputs.
2. **I/O contract** : keep the same parameters and return a value (do not print).
3. **Language-specific gotchas**  
   - *Integer vs float division* (`/`, `//`, `int()` casting).  
   - *Indexing & slicing* differences (inclusive vs exclusive ranges, 0-based arrays).  
   - *Mutable default arguments* (Python) : use `None` + inside-function init if needed.  
   - *Overflow / large-int handling* (Java `int` ↔ Python unlimited-int).  
   - *Loop constructs* (`for … range` vs `for (int i=… )`).  
   - *Short-circuit logic* (`&&`, `||` ↔ `and`, `or`).  
   - *Collection APIs* (`len(x)` vs `x.length` / `x.size()` / `Arrays.*`).  
   - *Exception equivalence* : raise/throw an analogous error type.  
   - *Boolean naming* conventions (`is_…`, `has…` in Python).  
4. **Keep algorithmic complexity and data structures intact** (lists ↔ arrays, maps ↔ dictionaries, etc.).
5. **No extra output** : absolutely no comments, explanations, or blank lines outside the code block.
6. {additional_instruction}

**Original Function ({input_language})**
{input_code}

""", input_variables = ["input_language", "input_code", "target_language", "additional_instruction"])

def Translator_node_alone(state: AgentState):
    print("Translating the code - Translator")
    model = state['model']

    if state['output_lang'].upper() == "JAVA":
        extra_instruction = "Make the main class name Main"
    else:
        extra_instruction = ""

    messages = [
        SystemMessage(content=Translator_alone_prompt.format(input_language = state["input_lang"],
                                                        input_code = state['input_code'], 
                                                        target_language = state["output_lang"], 
                                                        additional_instruction = extra_instruction)), 
    ]
    response = model.invoke(messages)

    # clean the code by removing back ticks
    clean_code = clean_generated_code(response.content)
    Translator_history = f"Translator: {clean_code} \n"
    # print("Translated_code: ", clean_code)
    return {"translated_code": clean_code, "History": Translator_history}

