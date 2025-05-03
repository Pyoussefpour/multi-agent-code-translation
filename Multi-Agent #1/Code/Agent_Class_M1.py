from typing import TypedDict, Any

def clean_generated_code(generated_code):
    """
    Cleans the generated code by removing the first line and the triple backticks
    input:
        generated_code: the generated code to be cleaned
    output:
        cleaned_code: the cleaned code
    """
    # Split the string by triple backticks
    parts = generated_code.split("```")

    # If at least 2 parts exist, process further
    if len(parts) > 1:
        # Split the second part (actual code) by newline to remove the first line (program name)
        code_lines = parts[1].split("\n", 1)
        return code_lines[1].strip() if len(code_lines) > 1 else ""

    return generated_code.strip()


class AgentState(TypedDict, total=False):
    
    ### Models ###
    model: Any

    ### Inputs ###
    input_lang: str
    output_lang: str
    input_code: str
    example_input: str
    ### Unit Test Generator ###
    UnitTest_status: str
    sample_inputs: str
    code_state: str
    test_code: str
    JSON_dir: str
    
    ### Evaluator Tool ###
    UnitTest_script: str
    UnitTest: str
    code_status: str
    num_iter: int
    max_iter: int
    Merge_status: str

    ### Translator ###
    sample_inputs: str
    test_code: str
    code_state: str
    output_file_dir: str
    unit_test_status: str
    Merge_status: str
    UnitTests: str

    ### Output ###
    UnitTest_history: str
    Translator_history: str

    ##
    test_code_translation: str
    code_status: str
    output_code: str
    num_iter: int
    max_iter: int
    error_type: str
    Translator_status: str
    model: Any 