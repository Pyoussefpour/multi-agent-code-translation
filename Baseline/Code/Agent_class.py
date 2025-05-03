from typing import TypedDict, Any

class AgentState(TypedDict, total=False):
    ### Models ###
    model: Any

    input_lang: str
    output_lang: str
    input_code: str
    example_inputs: str




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
