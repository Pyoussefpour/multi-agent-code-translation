from Agent_Class_M1 import AgentState, clean_generated_code
from langchain_core.messages import AnyMessage, SystemMessage
from langchain.prompts import PromptTemplate
import re

Check_Error_Type_Prompt = PromptTemplate(
    template = """You are an expert in {output_language} debugging and software engineering. 
    Your task is to analyze the error message and determine the type of error.
    You have to determine whether the error is cause by the function or the unit test.

    Note that:
        If there are mis matches in the function output and the expected output (Test FAILED), the error is cause by the function.
        If the script fails to run, the error can be caused by either the function or the unit test.
        Your task is to read the error message and determine which part of the code is causing the error.
    If the error is cause by the function, output "FUNCTION".
    If the error is cause by the unit test, output "UNIT TEST".
    You should only output the error type (FUNCTION or UNIT TEST) and no additional text or explanation.
    error message: {error_message}
    """,
    input_variables=["output_language", "error_message"])

def Check_error_type(state:AgentState):
    """
    Checks the type of error
    """
    print("Checking the type of error - Translator")
    model = state['model']
    messages = [
        SystemMessage(content=Check_Error_Type_Prompt.format(output_language=state['output_lang'], 
                                                             error_message=state['code_status']))
    ]
    response = model.invoke(messages)
    Translator_history = f"Check_error_type: {response.content} \n"
    return {"error_type": response.content, "Translator_history": state['Translator_history'] + Translator_history}

def Conditional_Error_Type(state: AgentState):
    """
    Checks the type of error for the UnitTest script
    """
    Error_type = state['error_type']
    print("Error_type",Error_type)

    if Error_type.upper() == "FUNCTION":
        return "Function"
    else:
        return "Unit Test"
    
def replace_python_function(script, new_function_code):
    """
    Replace the function named f_filled in the given script, 
    handling functions marked with ### markers.
    
    Args:
    script (str): The original Python script as a string
    new_function_code (str): The new implementation of f_filled
    
    Returns:
    str: The modified script with f_filled replaced
    """

    print("new_function_code",new_function_code)
    
    # Find the start of the f_filled function with ### markers
    function_start_pattern = re.compile(r'###.*?\n\s*def\s+f_filled\s*\(.*?###', re.DOTALL)
    
    # Search for the function with markers
    match = function_start_pattern.search(script)

    if match:
        # When ### markers are found
        indented_new_function = f"""
    ###
    {new_function_code}
    ###
    """
        # Replace the old function with the new one
        modified_script = script[:match.start()] + indented_new_function + script[match.end():]
        return modified_script
    
    else:
        # If no ### markers, look for regular function definition
        regular_function_pattern = re.compile(r'def\s+f_filled\s*\([^)]*\):.*?(?=\n\S|\Z)', re.DOTALL)
        match = regular_function_pattern.search(script)
        
        if not match:
            raise ValueError("Could not find f_filled function in the script")
        
        # Add markers to the new function
        indented_new_function = f"""
    ###
    {new_function_code}
    ###
    """
        
        # Replace the regular function with the marked one
        modified_script = script[:match.start()] + indented_new_function + script[match.end():]
        return modified_script


Regenerate_Function_Prompt = PromptTemplate(
    template = """You are an expert code translator and bug fixer.

### Objective
Your task is to fix a translated function that produced a runtime error.  
You will receive:
- The original function (`Input Code`) in the source language
- The translated version (`Translated Code`) in the target language. the code that is causing the error
- The error message (`Code Error`) that occurred during execution

Use the information from the original code and error to:
- Identify what is wrong in the translated code
- Modify the translated function to correct the error
- Preserve the function's intended logic and signature
- Ensure the output is correct, type-safe, and consistent with expected behavior

### Constraints
- Fix **only** the function `f_filled` — no test code, main method, or other wrapper logic
- Your output must be a complete, standalone function definition
- Do **not** include explanations, comments, or extra text — output only code
- Ensure the fixed function has no syntax errors and handles the error shown

### Input
**Input Code ({input_language})**
{input_code}

**Translated Code ({target_language})**
{translated_code}

**Code Error**
{code_status}


### Expected Output
```{target_language}
Corrected f_filled function
```
    """,
    input_variables=["input_language", "target_language", "input_code", "code_status", "translated_code"])

def Regenerate_Function_node(state: AgentState):
    """
    Regenerates the function code
    """
    model = state['model']
    messages = [
        SystemMessage(content=Regenerate_Function_Prompt.format(input_language=state['input_lang'], 
                                                                target_language=state['output_lang'], 
                                                                input_code=state['input_code'], 
                                                                code_status=state['code_status'], 
                                                                translated_code=state['output_code']))
    ]
    response = model.invoke(messages)
    function_code = clean_generated_code(response.content)

    if state['output_lang'] == "Python":
        script = replace_python_function(state['UnitTest_script'], function_code)
    else:
        script = state['UnitTest_script']
    #when is the java function updated (run test node)
    Translator_history = f"Regenerate_Function_node: {response.content} \n"
    return {"output_code": function_code, "num_iter": state['num_iter'] + 1, "UnitTest_script": script, "Translator_history": state['Translator_history'] + Translator_history}


Regenerate_Script_Prompt = PromptTemplate(
    template = """
    You are a software debugging assistant specialized in test infrastructure.

### Objective
You will receive:
- A **Code Error** (e.g., stack trace, exception message)
- A **Test Script** that runs a function called `f_filled`
- The function `f_filled` is assumed to be correct — do not change it

Your task is to:
- Identify the error in the test script logic
- Fix the test script so it runs correctly and passes inputs to `f_filled` properly
- Keep the structure and intent of the test logic, but ensure it executes without errors and handles inputs, outputs, and types correctly

### Output Requirements
- Only modify the **unit test script** — do not touch or reprint the function `f_filled`
- Output a complete, runnable test script in `{target_language}`
- Use only standard libraries available in `{target_language}` (e.g., `json`, `os`, `random`, `traceback` for Python)
- Do not include any explanation or extra comments — just output the fixed script inside a fenced code block
- Make sure to include the function `f_filled` is wrapped in ### markers

### Input
**Test Script**
{UnitTest_script}

**Code Error**
{code_status}

**Expected Output**
```{target_language}
Corrected Test Script
```
    """,
    input_variables=["target_language", "code_status", "UnitTest_script"]
)  

def Regenerate_Script_node(state: AgentState):
    """
    Regenerates the script code
    """
    model = state['model']
    messages = [
        SystemMessage(content=Regenerate_Script_Prompt.format(target_language=state['output_lang'], 
                                                               code_status=state['code_status'], 
                                                               UnitTest_script=state['UnitTest_script']))
    ]
    response = model.invoke(messages)
    script_code = clean_generated_code(response.content)
    Translator_history = f"Regenerate_Script_node: {response.content} \n"
    return {"UnitTest_script": script_code, "num_iter": state['num_iter'] + 1, "Translator_history": state['Translator_history'] + Translator_history}