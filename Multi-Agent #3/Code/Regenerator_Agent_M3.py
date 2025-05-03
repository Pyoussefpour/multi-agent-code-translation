from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage
from Agent_class_M3 import AgentState, clean_generated_code

Regenerator_prompt = PromptTemplate(
    template="""
You are a code regeneration agent. You are fluent in {input_language} and {target_language}.
You are helping with regenerating a function that was previously translated from {input_language} to {target_language}.

You are given:
- The original function in the source language.
- The previously translated function.
- A detailed evaluation report describing the mistakes and concerns.

Your task is to regenerate a **correct and faithful translation** of the original function into the target language, fully fixing the problems mentioned in the evaluation report.

Instructions:
1. Carefully read the evaluation report and understand what issues were found.
2. Use the original function as the source of truth for logic and structure.
3. Correct any mistakes or missing parts in the previous translation.
4. Preserve the meaning and logic of the original function.
5. Improve style or clarity if necessary, but stay faithful to the original behavior.

Output format:
- Only output the corrected translated function in clean code format.
- Do not output any explanations or comments.

Input format:

Original Function:
{input_code}

Previous (Incorrect) Translation:
{translated_code}

Evaluation Report:
{Evaluator_analysis}

Expected output:
```{target_language}
translated_code
```
""", input_variables=["input_language", "target_language", "input_code", "translated_code", "Evaluator_analysis"])


def Regenerator_node(state: AgentState):
    print("Regenerating the code - Regenerator")
    model = state['model']
    messages = [
        SystemMessage(content=Regenerator_prompt.format(input_language = state["input_lang"],
                                                        target_language = state["output_lang"],
                                                        input_code = state["input_code"],
                                                        translated_code = state["translated_code"],
                                                        Evaluator_analysis = state["Evaluator_analysis"]))]
    
    response = model.invoke(messages).content
    response = clean_generated_code(response)
    History = f"Regenerator: {response} \n"
    # print("Regnerated code: ", response)
    return {"translated_code": response, "History": state['History'] + History, 'num_iter': state['num_iter'] + 1}