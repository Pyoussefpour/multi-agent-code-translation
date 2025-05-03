from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage
from Agent_class_M3 import AgentState, clean_generated_code

Evaluator_prompt = PromptTemplate(
    template="""
You are a professional code translation evaluator.

You are given:
- The original function ({input_language}).
- The translated function ({target_language}).

Follow these steps carefully:

1. Chain-of-Thought Analysis:
   - Think step-by-step through the logic of the original function.
   - Think step-by-step through the logic of the translated function.
   - Describe the purpose and key operations of each.

2. Self-Consistency Check:
   - If multiple reasonable evaluations are possible, generate them.
   - Choose the most logical and consistent evaluation.

3. Verification (Chain-of-Verification):
   - Systematically verify the following:
     - Input types match.
     - Output behavior matches.
     - Control flows (loops, conditionals) are preserved.
     - Variable manipulations (assignments, updates) match.
     - Error handling or exceptional cases are preserved.

4. Fill out the checklist:

| Checkpoint | Status (Pass/Fail) | Notes |
|------------|--------------------|-------|
| Input types match | | |
| Output behavior matches | | |
| All logic steps preserved | | |
| Control flows (loops, conditions) preserved | | |
| Error handling matches | | |
| Naming and structure are faithful | | |

5. Contrastive Thinking:
   - Imagine a wrong translation. Briefly describe what mistakes it could have.
   - Explain why the given translation avoids those mistakes (or not).

6. Final Verdict:
   - If the translation is correct, and would not benefit from any improvements and you are sure that it is correct, write "ALL GOOD!" at the end.
   - Otherwise, write a clear and concise report describing the concerns.

keep the reporrt as concise as possible, while giving clear and valuable feedback.
Original Function:
{input_code}

Translated Function:
{translated_code}
""" , input_variables=["input_language", "target_language", "input_code", "translated_code"])


def Evaluator_node(state: AgentState):
    """
    Evaluates the translated code
    """
    print("Evaluating the code - Evaluator")
    model = state['eval_model']
    prompt_content = Evaluator_prompt.format(
        input_language=state["input_lang"],
        target_language=state["output_lang"],
        input_code=state["input_code"],
        translated_code=state["translated_code"]
    )
    
    # messages = [
    #     SystemMessage(content=Evaluator_prompt.format(input_language = state["input_lang"],
    #                                                   target_language = state["output_lang"],
    #                                                   input_code = state["input_code"],
    #                                                   translated_code = state["translated_code"]))]
    
    response = model.invoke(prompt_content).content
    History = f"Evaluator: {response} \n"
    # print("Evaluator_analysis: ", response)
    print("done evaluating")
    return {"Evaluator_analysis": response, "History": state['History'] + History}


def Conditional_Regenerator(state: AgentState):
    if "ALL GOOD!" in state["Evaluator_analysis"]:
        return "Done"
    elif state['num_iter'] >= state['max_iter']:
        print("Max iterations reached")
        return "Done"
    else:
        return "Regen"
    
