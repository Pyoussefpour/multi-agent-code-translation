import os
import re
import subprocess
import re
import csv

def check_parallel_file(test_dir: str, input_file: str, output_language: str):
    """
    Checks if there is a parallel file in the test directory

    Input: 
        test_dir: the directory of the input files
        input_file: name of the input file (code that needs to be translated)
        output_language: target language for translation
    Output:
        if the parallel file exists, return the path to the test file, if not, return False
    """
    parent_dir = os.path.dirname(test_dir)

    if output_language.lower() == "python":
        test_file = input_file.split('.')[0] + ".py"
    elif output_language.lower() == "java":
        test_file = input_file.split('.')[0] + ".java"
    elif output_language.lower() == "cpp":
        test_file = input_file.split('.')[0] + ".cpp"
    else:
        print("Invalid output language")
        return False

    output_path = os.path.join(parent_dir, output_language.lower(), test_file)
    if os.path.exists(output_path):
        return output_path
    else:
        return False


def extract_input_code(input_file: str):
    """
    Extracts the function that needs to be translated from the input file
    Input: the file path to the input file (code that needs to be translated)
    Output: the function that needs to be translated, without the unit tests
    """

    with open(input_file, 'r') as file:
        input_code = file.read()
    
    split_code = input_code.split("TOFILL")

    # Remove first 6 lines by splitting on newlines and joining remaining lines
    split_code[0] = '\n'.join(split_code[0].split('\n')[6:])
    return split_code[0], split_code[1]


# TRANSLATE THE CODE -> MA
# OUTPUT THE TRANSLATED CODE

def extract_java_function(source_code, function_name="f_filled"):
    """
    Extracts the function definition of a function named function_name from Java source code.
    
    Parameters:
    - source_code (str): The full Java source code as a string.
    - function_name (str): The name of the function to extract (default is "f_filled").
    
    Returns:
    - str: The extracted function definition, or None if not found.
    """
    # More flexible regex pattern that handles different ordering of modifiers
    pattern_string = r"\s*(public|private|protected)?\s*(static)?\s*(public|private|protected)?\s*\w+(\[\])?\s+" + \
                     re.escape(function_name) + \
                     r"\s*\([^)]*\)\s*\{"
    
    match = re.search(pattern_string, source_code, re.DOTALL)

    if match:
        start_pos = match.start()
        open_braces = 1  # Since we start from `{`
        pos = source_code.find('{', match.start())  # Find the actual opening brace
        
        while pos < len(source_code) and pos != -1:
            pos += 1
            if pos >= len(source_code):
                break
                
            c = source_code[pos]
            
            if c == '{':
                open_braces += 1
            elif c == '}':
                open_braces -= 1
                if open_braces == 0:
                    # Found matching closing brace
                    return source_code[start_pos:pos + 1]
            
    return None  # Function not found


def create_test_file(file_path: str, translated_code: str, output_language: str):
    """
    Create a test file with the translated code to evaluate the translated code
    Input:
        file_path: the file path to the test file
        translated_code: the translated code to be evaluated
        output_language: the language of the output file
    Output:
        the result of the evaluation
    """
    with open(file_path, 'r') as file:
        test_code = file.read()
    
    if output_language.upper() == "PYTHON":
        eval_code = re.sub(r"#TOFILL", translated_code, test_code)
        with open("eval_code.py", 'w') as file:
            file.write(eval_code)
        result = subprocess.run("python3 eval_code.py",capture_output=True, text=True, shell=True)
        
        #remove the eval_code.py file
        subprocess.run(["rm", "-f", "./eval_code.py"], check=True)

    elif output_language.upper() == "JAVA":
        function_code = extract_java_function(translated_code, "f_filled")
        if function_code is None:
            print(function_code)
            raise ValueError("Function f_filled not found in the translated code")
            
        eval_code = re.sub(r"//TOFILL", function_code, test_code)
        # Get the current directory to return to it later
        current_dir = os.getcwd()
        mvn_path = os.path.join(os.getcwd(), "Eval")
        file_name = file_path.split('/')[-1]
        java_file_path = os.path.join(mvn_path, "src", "main", "java", file_name)
        with open(java_file_path, 'w') as file:
            file.write(eval_code)
        
        # Change directory to maven project path
        os.chdir(mvn_path)
        class_name = file_name.split('.')[0].strip()
        print("class_name: ", class_name)
        command = f'mvn -q compile exec:java -Dexec.mainClass="{class_name}"'
        print("command: ", command)
        #run the java test file
        result = subprocess.run(command,capture_output=True, text=True, shell=True)
           
        subprocess.run(["rm", "-f", java_file_path], check=True)

        # Return to the original directory
        os.chdir(current_dir)


    elif output_language.upper() == "CPP":
        eval_code = re.sub(r"//TOFILL", translated_code, test_code)
        with open("eval_code.cpp", 'w') as file:
            file.write(eval_code)

        subprocess.run("g++ eval_code.cpp -I/opt/homebrew/include -std=c++17 -o eval_code",capture_output=True, text=True, shell=True)
        result = subprocess.run("./eval_code",capture_output=True, text=True, shell=True)   
        subprocess.run(["rm", "-f", "./eval_code"], check=True)
        subprocess.run(["rm", "-f", "./eval_code.cpp"], check=True)
    
    print("result: ", result)
    print("result.stdout: ", result.stdout)
    print("result.stderr: ", result.stderr)
    return result


def check_result(result: str):
    """
    Checks if the result of the evaluation is correct
    Input:
        result: the result of the evaluation
    Output:
        If passed all unit tests, return True, if not, return False
    """
    output_string = result.stdout
    match = re.search(r"#Results:\s*(\d+),\s*(\d+)", output_string)
    if match:
        n_success = int(match.group(1))
        n_tests = int(match.group(2))
        if n_success == n_tests:
            return True, result.stdout
        else:
            return False, result.stdout
    else:
        error_string = result.stderr + result.stdout
        return False, error_string
    

def write_result(input_file_name: str, translated_code: str, input_language: str, output_language: str, result: str, passed: bool, n_iterations: int, max_iter_reached: bool, output_file: str,code_status: str, Translator_history: str, UnitTest_history: str):
    """
    Writes the result to a csv file
    """
    file_exists = os.path.exists(output_file)
    with open(output_file, 'a') as file:
        writer = csv.writer(file)
        # Add headers if file is empty
        if not file_exists or os.path.getsize(output_file) == 0:
            writer.writerow(['Input File', 'Input Language', 'Output Language', 'Result', 'Passed All Tests', 'Number of Iterations','Max Iter Reached', 'Translated Code', 'Code Status', 'Translator History', 'UnitTest History'])

        writer.writerow([input_file_name, input_language, output_language, result, passed, n_iterations, max_iter_reached, translated_code, code_status, Translator_history, UnitTest_history])

    


def eval_pipeline(file_path: str, translated_code: str, input_language: str, output_language: str, num_iterations: int, max_iter_reached: bool, code_status: str, Translator_history: str, UnitTest_history: str):
    """
    Evaluates the pipeline for a given input file and output language
    
    Args:
        file_path: Path to the test file in output language
        translated_code: The translated code to evaluate
        input_language: Source language of the code
        output_language: Target language for translation
        num_iterations: Number of translation attempts made
        max_iter_reached: Whether max iterations was reached
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
    output_file = os.path.join(os.getcwd(), f"Final_2_results_{input_language}_{output_language}.csv")
    file_name = os.path.basename(file_path)
    print("result_string: ", result_string)
    write_result(file_name.split(".")[0], translated_code, input_language, output_language, 
                 result_string, passed, num_iterations, max_iter_reached, output_file, code_status, Translator_history, UnitTest_history)
                
    print(f"{file_name} has been evaluated")

    return passed


