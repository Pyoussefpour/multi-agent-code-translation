from Agent_class_M2 import AgentState, clean_generated_code
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage
from langchain.prompts import PromptTemplate
import os
import subprocess
import json

def Check_testing_status(state: AgentState):
    """
    Checks the status of the unit test and the translator
    """
    # print("Checking the status of the unit test and the translator")

    if state["Translator_status"] == "DONE" and state["UnitTest_status"] == "DONE":
        print("Translator and UnitTest are done")
        return {"Merge_status": "Continue"}
    else:
        return {"Merge_status": "Wait"}
    

def conditional_merge_or_wait(state: AgentState):
    """
    Merge node
    Conditional edge to determine if the code should be merged or wait
    Decides if the unit test generator and the translation agent are ready to be merged
    """
    if state["Merge_status"] == "Continue":
        return "Continue"
    else:
        return "Wait"
    

UnitTest_Script_Prompt = PromptTemplate(
    template="""
You are a senior software {output_language} QA engineer.

### Task
You will be given:
2. A high-level **pseudocode** description of what the test-runner must do  
3. A **starter script** that closely resembles the final output, but may contain bugs or logic gaps  
4. A sample of the **test data JSON format** (used in both languages)

Your job is to:
- Modify the starter script so it fully implements the pseudocode logic
- Ensure it handles input types and shapes correctly
- Ensure it catches and logs any runtime errors or exceptions
- Print **only test failure messages and a final summary**
- Ensure the code runs without syntax or runtime errors
- Do not alter the body, logic, or definition of the `f_filled` function in any way.
- Only adjust how arguments are passed to `f_filled` if necessary.  
- Keep changes minimal and do not refactor or restructure the script beyond what is strictly needed. 
- Use the Test Data JSON file to understand what the shape and type of the inputs and outputs are, and correctly parse the result.json file and call and check the function.
{extra_information}

### Pseudocode (applies to both Python and Java)
1. Load test cases from 'results.json'
- Each case contains an 'input' and an 'output' (Python) or 'result' (Java)

2. Randomly sample 5 test cases

3. Initialize pass/fail counters

4. For each case: 
a. Pass 'input' to the function f_filled (Main.f_filled in Java) 
b. Compare return value with expected output/result - 
If both value and type match → count as pass - 
If value matches but type differs → count as fail, print type mismatch - 
If value differs → count as fail, print detailed mismatch 
c. Catch and print any exceptions/errors

5. Print final summary: "Passed X/Y tests"
- If all passed, print "TOTAL SUCCESS!"

### Starter Script
{script}

### Test Data JSON
{JSON_file}

### Expected Output (with no additional text or explanation, just the raw code):
```{output_language}
Modified Script
```
""",
input_variables=["output_language", "script", "JSON_file", "extra_information"])

def UnitTest_Script_node(state: AgentState): 

    """
    Node to create unit test script using the generate tests script
    Output:
        test_code_translation: the unit test script
    """
    

    model = state['model']
    translated_code = state["output_code"]
    output_lang = state['output_lang'].upper()
    base_dir = state['JSON_dir']

    print("translated_code",translated_code)

    if output_lang == "PYTHON":
            
            init_script = f"""
    ###
    {translated_code}
    ###

    import os
    import json
    with open(os.path.join({base_dir},'results.json'), 'r') as file:
        data = json.load(file)

    import random
    test_data = random.sample(data, 5)

    passed = 0
    total = len(test_data)

    for case in test_data:
        output = f_filled(*case['input'])
        if output != case['output']:
            print(f"Test FAILED for input {{*case['input']}}: expected {{*case['output']}}, got {{output}}")
        else:
            passed += 1
    
    print(f"\n{{passed}}/{{total}} tests passed.")
    if passed == total:
        print("TOTAL SUCCESS!")
            """
   
            extra_information = "Keep the f_filled function wrapped in ### as shown in the initial script"

    elif output_lang == "JAVA":
            
            init_script = f"""
    import java.io.FileReader;
    import java.io.IOException;
    import java.util.List;
    import java.util.Collections;
    import com. google.son.Gson;
    import com.google.gson.reflect.TypeToken;
    import com.google.gson.JsonElement;

    class TestCase {{
        int result;
        List<Object> input;
        
    }}

    public class unit_test {{
        public static void main(String[] args) {{

            String filePath = "{base_dir}/results.json"; // Do not change this path
            Gson gson = new Gson();
            int n_success = 0;

            try (FileReader reader = new FileReader(filePath)) {{
                List<TestCase> testCases = gson.fromJson(reader, new TypeToken<List<TestCase>>() {{}}.getType());
                
                // Shuffle the test cases to randomize their order
                Collections.shuffle(testCases);
                
                // Take 5 random test cases
                List<TestCase> selectedTestCases = testCases.subList(0, Math.min(5, testCases.size()));
                
                for (TestCase testCase : selectedTestCases) {{
                    int actualOutput = Main.f_filled(testCase.input);
                    
                    if (actualOutput == testCase.result) {{
                        n_success += 1;
                    }}
                    else {{
                        System.out.println("For input " + testCase.input + ", translated function outputted " + actualOutput + " but expected output was " + testCase.result);
                    }}
                }}
                
                System.out.println("#Results:" + n_success + ", " + selectedTestCases.size());
                if (n_success == selectedTestCases.size()){{
                    System. out.println("TOTAL SUCCESS!");
                }}
            }} catch (IOException e) {{
                System.err.println("Error reading JSON file: " + e.getMessage());
            }}
        }}
    }}

        """
            
            extra_information = f"""
Based on the type and shape of the inputs and results from the JSON file, modify the TestCase class to match the inputs and results.
f_filled function is in a seperated file, with the name of the file being "Main.java". 
This file is in the same directory as the unit test file, and can the f_filled function be imported from the Main file.
Make sure the indentation of the code is correct for evey line including the f_filled function, besides the indentaions (if needed) do not change the f_filled function.
Important, the result.json input is always a list of arguments that the f_filled function takes, so make sure to pass the arguments correctly, and deal with the list correctly.
Mkae sure the type are correct for the inputs and results, based on the JSON file.

Here is the Main file:
{translated_code}
"""
            
    elif output_lang == "CPP":
            init_script = f"""
        #include <iostream>
        #include <fstream>
        #include <vector>
        #include <nlohmann/json.hpp>
        #include <random>

        using json = nlohmann::json;
        using namespace std;

        // Structure to hold test case data
        struct TestCase {{
            int result;
            int input;
        }};

        {translated_code}

        int main() {{
            string filePath = "{base_dir}/results.json";
            int n_success = 0;

            // Read the JSON file
            ifstream file(filePath);
            if (!file) {{
                cerr << "Error reading JSON file: " << filePath << endl;
                return 1;
            }}

            json testCasesJson;
            file >> testCasesJson; // Parse JSON
            file.close();

            // Convert JSON into a vector of TestCase structs
            vector<TestCase> testCases;
            for (const auto& item : testCasesJson) {{
                testCases.push_back({{item["result"], item["input"]}});
            }}

            // Shuffle the test cases to pick random ones
            random_device rd;  // Obtain a random number from hardware
            mt19937 eng(rd()); // Seed the generator
            shuffle(testCases.begin(), testCases.end(), eng); // Shuffle the test cases

            size_t numTests = min(testCases.size(), size_t(5));
            // Run tests on the first 5 random test cases
            for (size_t i = 0; i < numTests; ++i) {{
                const auto& testCase = testCases[i];
                int actualOutput = f_filled(testCase.input);

                if (actualOutput == testCase.result) {{
                    n_success++;
                }} else {{
                    cout << "For input " << testCase.input << ", translated function outputted " 
                        << actualOutput << " but expected output was " << testCase.result << endl;
                }}
            }}

            // Print final results
            cout << "#Results: " << n_success << " / " << numTests << endl;
            if (n_success == numTests) {{
                cout << "TOTAL SUCCESS!" << endl;
            }}

            return 0;
        }}

    """
            extra_information = "None"
        
    # read the results.json file to get the unit tests and pass to the prompt
    with open(os.path.join(state['JSON_dir'],'results.json'), 'r') as file:
        unit_tests = json.load(file)
    
    #Pass the inputs to the prompt
    messages =[
        SystemMessage(
            content = UnitTest_Script_Prompt.format(
                output_language=state['output_lang'], 
                script=init_script, 
                JSON_file=unit_tests,
                extra_information=extra_information
            )
        )
    ]

    #Call the model with the prompt
    response = model.invoke(messages)
    script = clean_generated_code(response.content)
    Translator_history = f"UnitTest_Script_node: {response.content} \n"
    return {"UnitTest_script": script, "UnitTests": unit_tests, "Translator_history": state['Translator_history'] + Translator_history}


def Run_test_node(state: AgentState):
    """
    Run the unit test script

    Output:
        code_status: the result of the unit test
    """
    output_lang = state["output_lang"].upper()
    script = state["UnitTest_script"]
    
    if not script:
        raise ValueError("Error: No test code translation available")
    
    if output_lang == "PYTHON":
        with open("unit_test.py","w") as file:
            file.write(script)
    
        result = subprocess.run("python3 unit_test.py",capture_output=True, text=True, shell=True)

        UnitTest_result = f"""
RESULT: {result.stdout}

ERRORS: {result.stderr}
"""
        
    elif output_lang == "JAVA":
        translated_code = state["output_code"]
        current_dir = os.getcwd()
        java_file_dir = os.path.join(current_dir,"my-app", "src", "main", "java")

        with open(os.path.join(java_file_dir,"Main.java"),"w") as code_file:
            code_file.write(translated_code)
        
        with open(os.path.join(java_file_dir,"unit_test.java"),"w") as test_file:
            test_file.write(script)
        
        os.chdir(os.path.join(current_dir,"my-app"))
        result = subprocess.run("mvn -q compile exec:java -Dexec.mainClass=unit_test",capture_output=True, text=True, shell=True)
        os.chdir(current_dir)

        UnitTest_result = f"""
RESULT: {result.stdout}

ERRORS: {result.stderr}
"""
        subprocess.run(["rm", "-f", os.path.join(java_file_dir,"Main.java")], check=True)
        subprocess.run(["rm", "-f", os.path.join(java_file_dir,"unit_test.java")], check=True)

    elif output_lang == "CPP":
        with open("cpp_unit_test.cpp","w") as file:
            file.write(script)
        
        compile = subprocess.run("g++ cpp_unit_test.cpp -I/opt/homebrew/include -std=c++17 -o program",capture_output=True, text=True, shell=True)
        result = subprocess.run("./program",capture_output=True, text=True, shell=True)

        UnitTest_result = f"""
    RESULT: {result.stdout}

    Compilation Error: {compile.stderr}

    ERRORS: {result.stderr}
    """

        # remove the compile file when doing multiple tests
        file_path = "./program"
        try:
            subprocess.run(["rm", "-f", file_path], check=True)
            print(f"{file_path} has been removed.")
        except subprocess.CalledProcessError as e:
            print(f"Error removing {file_path}: {e}")

    Translator_history = f"\nRun TestGen result: {UnitTest_result} \n"
    return {"code_status": UnitTest_result, 
            "error_message_analysis": UnitTest_result, 
            "input_code_analysis": state["UnitTest_script"], 
            "extra_info_analysis": "", 
            "Translator_history": state['Translator_history'] + Translator_history}


def Conditional_output(state:AgentState):
    """
    Check if the translated code works properly and if it should be retranslated
    """
    if "TOTAL SUCCESS!" in state['code_status']:
        return "Continue"

    else:
        if state['num_iter'] > state['max_iter']:
            return "Max_reached"

        else:
            print(state['code_status'])
            return "Error"
        

def Output_node(state: AgentState):
    print("Translated Code:")
    print(state['output_code'])
    
    print("Code Status:")
    print(state["code_status"])
