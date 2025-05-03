from Agent_class import AgentState, clean_generated_code
from langchain_core.messages import AnyMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import os
import csv
from Evaluation import extract_input_code,check_result, create_test_file

Translator_prompt = PromptTemplate(
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

**Original Function ({input_language})**
{input_code}


expected output:
```{target_language}
translated_code
```

    """, input_variables = ["input_language", "input_code", "target_language"]
)

def Translator_node(state: AgentState):
    """
    Translates the input code to the target language
    Input:
        input_code: the raw code to be translated
        input_language: the language of the input code
        target_language: the language to translate the input code to
    Output:
        translated_code: the translated code
    """
    model = state['model']
    messages = [
        SystemMessage(content = Translator_prompt.format(input_code = state['input_code'], 
                                                         input_language = state['input_lang'], 
                                                         target_language = state['output_lang']))
    ]
    response = model.invoke(messages)
    return {"translated_code": response.content}

### Model ###

model = ChatOpenAI(model="gpt-4o", temperature=0)

### Graph ###

Translator = StateGraph(AgentState)

Translator.add_node("Translator", Translator_node)
Translator.set_entry_point("Translator")
Translator.add_edge("Translator", END)

Agent = Translator.compile()

# ### Run ###
input_lang = "python"
output_lang = "java"


Python_dir = "/Users/parsayoussefpour/Desktop/Dataset/Selected_Tests/python"  # Python directory
Java_dir = "/Users/parsayoussefpour/Desktop/Dataset/Selected_Tests/java"  # Java directory




def write_result(input_file_name: str, translated_code: str, input_language: str, output_language: str, result: str, passed: bool, output_file: str):
    """
    Writes the result to a csv file
    """
    file_exists = os.path.exists(output_file)
    with open(output_file, 'a') as file:
        writer = csv.writer(file)
        # Add headers if file is empty
        if not file_exists or os.path.getsize(output_file) == 0:
            writer.writerow(['Input File', 'Input Language', 'Output Language', 'Translated Code', 'Result', 'Passed All Tests'])
        writer.writerow([input_file_name, input_language, output_language, translated_code, result, passed])

    


def eval_pipeline(file_path: str, translated_code: str, input_language: str, output_language: str):
    """
    Evaluates the pipeline for a given input file and output language
    
    Args:
        file_path: Path to the test file in output language
        translated_code: The translated code to evaluate
        input_language: Source language of the code
        output_language: Target language for translation
    Returns:
        None, writes results to CSV file
    """
    # Validate inputs
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file {file_path} does not exist")
    if not translated_code:
        raise ValueError("Translated code cannot be empty")
        
    # Create and run test file
    result = create_test_file(file_path, translated_code, output_language)
    if result is None:
        raise RuntimeError("Failed to create test file")
        
    # Check test results
    passed, result_string = check_result(result)
    
    # Write results to CSV
    output_file = os.path.join(os.getcwd(), f"Baseline_results_{input_language}_{output_language}.csv")
    file_name = os.path.basename(file_path)
    print("result_string: ", result_string)
    write_result(file_name, translated_code, input_language, output_language, 
                 result_string, passed, output_file)
                
    print(f"{file_name} has been evaluated")

    return None

for file in os.listdir(Python_dir):
    if file.endswith(".py"):
        print("Evaluating: ", file)
        input_code = extract_input_code(os.path.join(Python_dir, file))
        result = Agent.invoke({"model":model,
                        "input_lang": input_lang, 
                        "output_lang": output_lang, 
                        "input_code": input_code})

        translated_code = clean_generated_code(result["translated_code"])
        eval_pipeline(os.path.join(Java_dir, file.split(".")[0] + ".java"), translated_code, input_lang, output_lang)
    



