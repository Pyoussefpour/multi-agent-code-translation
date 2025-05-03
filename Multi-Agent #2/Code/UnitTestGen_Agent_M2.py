from Agent_class_M2 import AgentState, clean_generated_code
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage
from langchain.prompts import PromptTemplate
import os
import subprocess

#TODO: This needs to change to include analysis
Create_Input_Prompt = PromptTemplate(
    template="""
You are a code analysis expert designed to generate safe, executable inputs for a given function. 
These inputs will be used to run the function and store output for downstream code translation translation validation from {input_language} to {output_language}.
Think step by step what is the function definition, what the inputs to the function should look like based on the function definition, think about number of parameters, types of parameters, and the range of values for each parameter.
use the Unit Test Analysis to guide and help you generate the inputs

### Objective
Given a raw function definition in {input_language}, generate **20 valid input sets** that:
- Match the function's expected parameter types and structure
- Will **not** cause runtime errors when passed into the function (e.g., no `TypeError`, `ZeroDivisionError`, `IndexError`)
- Cover diverse but realistic scenarios (e.g., positive/negative values, empty inputs, floats/ints)
- Cover edge cases (e.g., empty list, negative numbers)

These inputs will be used to run the function and store output for downstream code translation validation.

You can use the example input to help you generate the inputs, do not copy them exactly, just use them as a reference.

---

### Guidelines
- Analyze the code to identify:
  - The number and names of parameters
  - The expected data types and formats for each parameter (e.g., list of ints, string, dict)
  - Constraints (e.g., no empty lists if division is used, no nulls if iteration is involved)
- Avoid inputs that would trigger:
  - Type mismatches (e.g., strings where numbers are expected)
  - Invalid operations (e.g., division by zero, empty indexing)
  - Unhandled edge cases (e.g., `None`, mixed-type collections)
- Focus on inputs that work without any exception being thrown
- Inputs can include edge cases (e.g., empty list, negative numbers), but only if the function handles them gracefully

---
### Input Code
{input_code}

### Example Input
{example_inputs}

### Unit Test Analysis
{UnitTest_analysis}

### Output Format
Return a JSON array of 20 input sets. Each input set should be a list of arguments to be passed into the function:
Output the test inputs in the following format EXACTLY (the arguments can be of different types (e.g. int, float, string, list, dict, etc.)):
    [
        {{ "input": [arg1, arg2, ...]}},
        {{ "input": [arg1, arg2, ...]}},
        {{ "input": [arg1, arg2, ...]}}
    ]
```
    """, input_variables = ["input_language", "input_code", "output_language", "example_inputs", "UnitTest_analysis"])


def Create_Input_node(state: AgentState): 
    """
    Creates input values for the unit test, tries to cover all edge cases
    Output:
        sample_inputs: the input values for the unit test
        UnitTest_status: the status of the unit test set to "STARTED" used for the Merge node
    """
    print("Creating Unit Test Input - Unit Test Generator")
    model = state['model']
    messages = [
        SystemMessage(content=Create_Input_Prompt.format(input_language = state["input_lang"],
                                                          input_code = state["input_code"],
                                                          output_language = state["output_lang"],
                                                          example_inputs = state["example_inputs"],
                                                          UnitTest_analysis = state["UT_input_analysis"]))]
    response = model.invoke(messages)
    # print("response",response.content)
    UnitTest_history = f"sample_inputs: {response.content} \n"
    return {"sample_inputs": response.content, 
            "UnitTest_status": "STARTED", 
            "UnitTest_history": state['UnitTest_history'] + UnitTest_history}


Create_TestCode_Prompt_1 = PromptTemplate(
    template="""You are provided with this a {input_language} code as a string a list of input arguments in JSON format (not a JSON file), and a starter code for the test code. 
The {input_language} code defines a function (or set of functions) that we want to test. 
you may think step by step on how to create this test code, in the format of comments in the output code.
Use the Script Generation Analysis to guide and help you create the test code.

Given the code and the list of inputs, please produce a new, standalone {input_language} program that:

Includes all necessary imports and class definitions.
Incorporates the given {input_language} code snippet.
Implements a main method that:
Iterates over each provided set of arguments.
Calls the relevant function from the provided code with those arguments.
Prints out the returned result for each call, one per line.
Make Sure the code does not use unchecked or unsafe operations
Do not touch the inputted {input_language} code, just add to it
Make sure the code does not enter an infinite loop
IMPORTANT:
- Carefully inspect the provided function code.
- Ensure that all possible edge cases are safely handled, especially inputs that might cause infinite loops, division by zero, or invalid operations.
- In particular:
  - If the function involves arithmetic, handle special cases like both inputs being zero.
  - If the function uses loops, ensure there is always a clear condition that guarantees termination.
- Add explicit guard clauses if necessary to handle exceptional inputs safely (e.g., if both inputs are zero, immediately return a valid result).
- The goal is for the function to always terminate safely, regardless of the inputs provided.


IMPORTANT FOR JAVA CODE:
- When creating the JSON output, ensure all arrays are properly serialized to JSON array notation like [1,2,3,4,5] instead of memory references like [I@63407e56.
- Use a proper JSON library (like Jackson or Gson) to handle serialization correctly.
- For any complex objects or arrays in the input or output, ensure they are properly converted to JSON-compatible format.
- When preparing the inputs and outputs for JSON serialization:
  - Primitive arrays (e.g., int[], double[]) must be manually converted into JSON arrays element-by-element before serialization.
  - Do not directly serialize Java primitive arrays (e.g., int[], float[]) or collections that contain primitive arrays. Instead, create a JsonArray and add each element individually.


Make Sure the code does not use unchecked or unsafe operations
Do not touch the inputted {input_language} code, just add to it
IMPORTANT: Files should be saved at the following directory: {directory}
Output file name should be results.json
Make all the calsses are under the public class test_gen


IMPORTANT: Make sure to include all of the input arguments in the output JSON file, the arguments can be of different types (e.g. int, float, string, list, dict, etc.)
The output JSON file should be in the following format:
    [
        {{ "input": [arg1, arg2, ...], "result": result1}},
        {{ "input": [arg1, arg2, ...], "result": result2}},
        {{ "input": [arg1, arg2, ...], "result": result3}}
    ]
{additional_instruction}

Desired Output:

Just the complete {input_language} code that stores the arguments and the result of inputing the argument in the given function in a JSON file named results.json. With no further explanation.

{input_language} Code: {input_code}
input arguments: {sample_inputs}
Script Generation Analysis:
{Script_gen_analysis}
starter code: {init_script}

""",
input_variables=["input_language", "input_code", "sample_inputs", "additional_instruction","directory","Script_gen_analysis"])

def Create_TestCode_node(state: AgentState): 
    """
    Creates the unit test code for the input code
    Output:
        test_code: the unit test code
        output_file_dir: the directory of the JSON file
    """
    current_dir = str(os.getcwd())
    print("Creating Test Code - Unit Test Generator")
    model = state['model']

    if state["input_lang"].upper() == "JAVA":
        additional_instruction = "Make the class name test_gen"
        init_script = f"""
import java.util.*;
import java.io.FileWriter;
import java.io.IOException;
import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

public class test_gen {{
    
    // === Insert your original function(s) here ===
    public static class YourFunctionClass {{
        // Example function signature to be called
        static int f_gold(int[] a, int n, int k) {{
            // Example logic
            return a.length + n + k;
        }}
    }}
    // =============================================

    public static void main(String[] args) {{
        // === Define your test inputs ===
        List<Object[]> inputs = Arrays.asList(
            new Object[]{{new int[]{{1, 2, 3}}, 3, 5}},
            new Object[]{{new int[]{{5, 5, 5}}, 3, 10}},
            new Object[]{{new int[]{{}}, 0, 0}}
        );
        // ================================

        // Prepare for output
        JsonArray resultsArray = new JsonArray();
        Gson gson = new Gson();

        // Iterate over all inputs
        for (Object[] inputSet : inputs) {{
            int[] arrayArg = (int[]) inputSet[0];
            int n = (int) inputSet[1];
            int k = (int) inputSet[2];

            JsonObject jsonObject = new JsonObject();
            JsonArray inputJsonArray = new JsonArray();

            // Serialize array properly
            JsonArray arrayJson = new JsonArray();
            for (int value : arrayArg) {{
                arrayJson.add(value);
            }}
            inputJsonArray.add(arrayJson);
            inputJsonArray.add(n);
            inputJsonArray.add(k);

            jsonObject.add("input", inputJsonArray);

            // Try running the function
            try {{
                int result = YourFunctionClass.f_gold(arrayArg, n, k);
                jsonObject.addProperty("result", result);
            }} catch (Exception e) {{
                jsonObject.addProperty("error", e.toString());
            }}

            resultsArray.add(jsonObject);
        }}

        // Save to results.json
        String directory = "{current_dir}";  //Do not change this line
        try (FileWriter writer = new FileWriter(directory + "results.json")) {{ //Do not change this line
            gson.toJson(resultsArray, writer);
        }} catch (IOException e) {{
            e.printStackTrace();
        }}
    }}
}}  

"""
    elif state['input_lang'].upper() == "PYTHON":
       additional_instruction = ""
       init_script = f"""
import json
import os

def generate_test_results(input_code, sample_inputs, directory):
    
    #Executes the input code with the provided sample inputs and 
    #saves results to a JSON file.
    
    #Args:
    #    input_code (str): The code containing the function to test
    #    sample_inputs (list): List of input arguments to test
    #   directory (str): Directory where to save results.json
    
    # Create results structure
    results = []
    
    # Execute code with each input and collect results
    # This is a placeholder - actual execution will depend on the language and function
    for inputs in sample_inputs:
        # Call the function with the inputs
        # result = function_to_test(*inputs)  # Replace with actual function call
        
        # Store input and result
        results.append({{
            "input": inputs,
            "result": "placeholder_result"  # Replace with actual result
        }})
    
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Write results to JSON file
    with open(os.path.join(directory, "results.json"), "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"Results saved to {{os.path.join(directory, 'results.json')}}")

# Example usage:
if __name__ == "__main__":
    # These would be replaced with actual inputs
    sample_code = "def example_function(x, y): return x + y" # change this to the input code
    sample_inputs = [[1, 2], [3, 4], [5, 6]] # change this to the sample inputs
    output_directory = "{current_dir}"
    
    generate_test_results(sample_code, sample_inputs, output_directory)
    """


    else:
        raise ValueError("Invalid input language")    

    messages = [
        SystemMessage(
            content=Create_TestCode_Prompt_1.format(input_language = state['input_lang'],
                                                   input_code=state['input_code'], 
                                                   sample_inputs=state['sample_inputs'],
                                                   additional_instruction = additional_instruction, 
                                                   directory = current_dir,
                                                   init_script = init_script,
                                                   Script_gen_analysis = state["UT_script_gen_analysis"]))]
    
    response = model.invoke(messages)

    UnitTest_history = f"test_code: {response.content} \n"
    return {"test_code": response.content, 
            "JSON_dir": current_dir, 
            "Regen_return_node": "Unit Test Generator",
            "UnitTest_history": state['UnitTest_history'] + UnitTest_history}


Check_Code_Prompt = PromptTemplate(
    template="""

If the script does **not** fully meet the requirements, output a short but clear explanation describing:
- What is wrong with the code
- What must be changed to fix it

Be precise but concise. No suggestions if everything is correct.

---

### Requirements Checklist

1. **Code Handling**
   - The original f_gold function must be included exactly as provided, without modifications.
   - The code must correctly import any required libraries (e.g., `json`, `os`, `random` for Python; `Gson`, `Jackson` for Java).

2. **Function Invocation**
   - Iterate over all provided input sets
   - Correctly call the target function(s) with the input arguments
   - Handle unpacking arguments properly if needed (e.g., `*args` for Python)

3. **Result Capture**
   - Capture both the input arguments and the corresponding output/result
   - For each input, store the `input` list and the `result` value

4. **Error Handling**
   - Catch any runtime exceptions during function calls and handle them gracefully (store an `"error"` field if needed)
   - Ensure the script does not crash on bad inputs

5. **JSON Output**
   - Save the results in a JSON file named `results.json` located at `{directory}`
   - Ensure JSON objects are correctly formatted:
     ```json
     [
       {{"input": [...], "result": ...}},
       {{"input": [...], "result": ...}}
     ]
     ```

6. **Java-Specific Rules (if {input_language} == Java)**
   - Use a proper JSON serialization library (e.g., Gson, Jackson).
   - Arrays or collections must be serialized properly into JSON arrays (not memory addresses like `[I@63407e56]`).
   - No raw memory references in output.

7. **General Behavior**
   - No unsafe or unchecked operations
   - No printing of intermediate values (only file output)
   - No extra code beyond what is needed for this task

8. **Efficiency**
   - The code should be efficient
   - The code should not enter an infinite loop

---

### Input

**Script ({input_language})**
{test_code}

**Input Arguments**
{sample_inputs}

Expected Output:
Just "YES!" with no other comments or explanation if the code is correct, if the code is incorrect, output the error message
""",
input_variables=["input_language", "test_code", "sample_inputs", "directory"])

def Check_TestCode_node(state: AgentState):
    """
    Checks the generated test code for any syntax or semantic error
    Output:
        code_state: the state of the code set to "YES" if there is an error, "NO" if there is no error
    """

    # print("Checking the Unit Test Generated Code - Unit Test Generator")
    model = state['model']
    messages =[
        SystemMessage(
            content = Check_Code_Prompt.format(input_language = state['input_lang'], 
                                               test_code = state['test_code'],
                                               sample_inputs = state['sample_inputs'],
                                               directory = state['JSON_dir'])
        )
    ]

    response = model.invoke(messages)
    UnitTest_history = f"LLM Check: {response.content} \n"
    return {"code_state": response.content, 
            "error_message_analysis": response.content, 
            "input_code_analysis": state["test_code"], 
            "extra_info_analysis": "",
            "UnitTest_history": state['UnitTest_history'] + UnitTest_history}


def conditional_llm_check(state: AgentState):
    """
    Conditional edge to determine if the code needs to be regenerated
    """
    
    if "YES" in state["code_state"].upper():
        return "continue"
    else:
        print("Regenerating the code - Unit Test Generator - Before running the unit test")
        return "regenerate"


Regenerate_Code_Prompt = PromptTemplate(
    template="""You are an expert debugging assistant.

### Objective
You will receive:
- A script written in {input_language}
- An error message or feedback explaining why the script fails or cannot be run
- An analysis of the error to help you with fixing the error

Your job is to:
- Identify the problem described in the error
- Modify the script to fix the issue
- Output a corrected version of the script that is fully functional and safe to run

### Instructions
- Only modify the parts of the code that are required to fix the issue — do not alter unrelated logic
- Preserve the original functionality and structure of the script
- Do not modify the f_gold function
- Ensure that the final version runs without syntax errors and satisfies the original intent
- Include all necessary imports, boilerplate, or definitions if they are missing
- Do not explain your changes — just output the corrected script
- Make sure the code does not enter an infinite loop
IMPORTANT:
- Carefully inspect the provided function code.
- Ensure that all possible edge cases are safely handled, especially inputs that might cause infinite loops, division by zero, or invalid operations.
- In particular:
  - If the function involves arithmetic, handle special cases like both inputs being zero.
  - If the function uses loops, ensure there is always a clear condition that guarantees termination.
- Add explicit guard clauses if necessary to handle exceptional inputs safely (e.g., if both inputs are zero, immediately return a valid result).
- The goal is for the function to always terminate safely, regardless of the inputs provided.
- Make sure the code is efficient
- Make all the calsses are under the public class test_gen

### Input
**Script ({input_language})**
{test_code}

**Error or Feedback**
{code_state}

Error Analysis:
{Regenerator_analysis}

### Expected Output (Just the code with no comments or explanation)
```{input_language}
Corrected Script
```
""",
input_variables=["input_language", "code_state", "test_code", "Regenerator_analysis"])


def Regenerate_code_node(state:AgentState):
    """
    Regenerates code if the code has errors identified by the llm or by running the unit test
    Output:
        test_code: the regenerated code
    """
    print("Regenerating unit test the code - Unit Test Generator")
    model = state['model']
    messages =[
        SystemMessage(
            content = Regenerate_Code_Prompt.format(input_language = state['input_lang'], 
                                                    code_state = state['code_state'],
                                                    test_code = state['test_code'],
                                                    Regenerator_analysis = state["Regenerator_analysis"])
        )
    ]

    response = model.invoke(messages)
    test_code = clean_generated_code(response.content)
    UnitTest_history = f"Regenerate Code: {response.content} \n"
    return {"test_code": test_code, "UnitTest_history": state['UnitTest_history'] + UnitTest_history}



def Run_TestGen_node(state: AgentState):
    """
    Runs the unit test code

    Output:
        JSON file in the current directory with the unit test inputs and outputs
        unit_test_status: the status of the unit test set to "DONE" for Merge node
    """
    # print("Running the testgen code - Unit Test Generator")

    script = clean_generated_code(state['test_code'])
    
    input_lang = state['input_lang'].upper()

    if input_lang == "PYTHON":
        with open ("test_gen.py","w") as file:
            file.write(script)
        
        result = subprocess.run("python3 test_gen.py",capture_output=True, text=True, shell=True)
        error = result.stderr

    elif input_lang == "JAVA":
        current_dir = os.path.dirname(os.path.abspath(__file__))
        java_file_dir = os.path.join(current_dir,"unit_test_gen", "src", "main", "java")

        with open(os.path.join(java_file_dir,"test_gen.java"),"w") as file:
            file.write(script)

        os.chdir(os.path.join(current_dir,"unit_test_gen"))
        result = subprocess.run("mvn compile exec:java -Dexec.mainClass=test_gen",capture_output=True, text=True, shell=True)
        os.chdir(current_dir)
        error = result.stderr + result.stdout
        if "BUILD SUCCESS" in error:
            error = ""
    
    elif input_lang == "CPP":
        with open("test_gen.cpp","w") as file:
            file.write(script)
        compile = subprocess.run("g++ test_gen.cpp -I/opt/homebrew/include -std=c++17 -o test_gen",capture_output=True, text=True, shell=True)
        result = subprocess.run("./test_gen",capture_output=True, text=True, shell=True)
        
        file_path = "./test_gen"
        try:
            subprocess.run(["rm", "-f", file_path], check=True)
            print(f"{file_path} has been removed.")
        except subprocess.CalledProcessError as e:
            print(f"Error removing {file_path}: {e}")
        error = result.stderr + compile.stderr

    
    # Check if results.json exists in the current directory
    if not os.path.exists("results.json"):
        error = f"results.json not found at {os.getcwd()}"
    print("error",error) 
    if not error:
        if not os.path.exists("results.json"):
            print("Error: results.json not found in the current directory")
            error = "FileNotFoundError: results.json is required but was not found"
            raise FileNotFoundError("results.json is required but was not found")   
        return {"UnitTest_status": "DONE"}
    else:

        UnitTest_history = f"Run TestGen error: {error} \n"
        return {"code_state": error, 
                "error_message_analysis": error, 
                "input_code_analysis": state["test_code"], 
                "extra_info_analysis": "", 
                "UnitTest_history": state['UnitTest_history'] + UnitTest_history}

# check the ouput of the run_testgen_node, if it is not empty, regenerate the code
def conditional_error_check(state: AgentState):
    if state["UnitTest_status"] == "DONE":
        print ("The unit tests have been generated successfully")
        return "continue"
    else:
        print("Regenerating the code - Unit Test Generator - After running the unit test")
        return "regenerate"