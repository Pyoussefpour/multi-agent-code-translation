from typing import TypedDict, Any

class AgentState(TypedDict, total=False):
    ### Models ###
    model: Any

    ### Inputs ###
    input_lang: str
    output_lang: str
    input_code: str
    example_inputs: str

    ### Analysis ###
    Code_analysis: str 
    UT_input_analysis: str
    UT_script_gen_analysis: str
    AST_analysis: str
    
    input_code_analysis: str
    error_message_analysis: str
    extra_info_analysis: str

    Regenerator_analysis: str
    Regen_return_node:str

    ### Translator ###
    translated_code: str
    Translator_status: str
    output_code: str

    ### Unit Test Generator ###
    sample_inputs: str
    UnitTest_status: str
    JSON_dir: str
    test_code: str
    code_state: str

    ### Evaluator ###
    Merge_status: str
    UnitTests: str
    UnitTest_script: str
    code_status: str
    UnitTests: str

    ### Regenerator ###
    error_type: str
    num_iter: int
    max_iter: int

    ### History ###
    Translator_history: str
    UnitTest_history: str



### General Functions ###

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
