from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os
import csv
from Agent_class_M3 import AgentState, clean_generated_code

from Analyzer_Agent_M3 import Analyze_code, Analyze_AST
from Translator_Agent_M3 import Translator_node, Translator_node_alone
from Evaluator_Agent_M3 import Evaluator_node, Conditional_Regenerator
from Regenerator_Agent_M3 import Regenerator_node
from Evaluation_M3 import eval_pipeline, extract_input_code

class CodeTranslator_Bonus:
    def __init__(self, input_lang: str, output_lang: str, model=None):
        self.input_lang = input_lang
        self.output_lang = output_lang
        self.model = model if model is not None else ChatOpenAI(model="gpt-4o", temperature=0)
        self.eval_model = ChatAnthropic(model="claude-3-7-sonnet-20250219")

    def translator_architecture(self):
        Translator = StateGraph(AgentState)

        Translator.add_node("Analyze_code",Analyze_code)
        Translator.add_node("Analyze_AST",Analyze_AST)
        Translator.add_node("Regenerate_code",Regenerator_node)
        Translator.add_node("Translator_node",Translator_node)
        Translator.add_node("Evaluator_node",Evaluator_node)

        Translator.set_entry_point("Analyze_AST")
        Translator.add_edge("Analyze_AST","Analyze_code")
        Translator.add_edge("Analyze_code", "Translator_node")
        Translator.add_edge("Translator_node", "Evaluator_node")
        Translator.add_conditional_edges("Evaluator_node",Conditional_Regenerator,
                                 {"Regen":"Regenerate_code", 
                                  "Done": END})
        Translator.add_edge("Regenerate_code","Evaluator_node")
       
        return Translator.compile()
    
    def Analyze_translator_architecture(self):
        """
        This is the architecture doesn't have the  Evaluator and Regenerator Agents, just the Analyzer and Translator Agents
        """
        Translator = StateGraph(AgentState)
        Translator.add_node("Analyze_code",Analyze_code)
        Translator.add_node("Analyze_AST",Analyze_AST)
        Translator.add_node("Translator_node",Translator_node)

        Translator.set_entry_point("Analyze_AST")
        Translator.add_edge("Analyze_AST","Analyze_code")
        Translator.add_edge("Analyze_code", "Translator_node")
        Translator.add_edge("Translator_node", END)
       
        return Translator.compile()

    def Regenerate_translator_architecture(self):
        """
        This is the architecture doesn't have the Analyzer Agent, just the Translator, Evaluator and Regenerator Agents
        """
        Translator = StateGraph(AgentState)
        Translator.add_node("Translator_node",Translator_node_alone)
        Translator.add_node("Regenerate_code",Regenerator_node)
        Translator.add_node("Evaluator_node",Evaluator_node)

        Translator.set_entry_point("Translator_node")
        Translator.add_edge("Translator_node","Evaluator_node")
        Translator.add_conditional_edges("Evaluator_node",Conditional_Regenerator,
                                 {"Regen":"Regenerate_code", 
                                  "Done": END})
        Translator.add_edge("Regenerate_code","Evaluator_node")
       
        return Translator.compile()
    
    def Evaluate_pipeline(self, input_dir: str, output_dir: str, max_iter: int):
        Translator = self.translator_architecture()
        correct = 0
        for i, filename in enumerate(sorted(os.listdir(input_dir))):
            # Check if file has already been evaluated
            result_file = f"Final_results_{self.input_lang}_{self.output_lang}.csv"
            already_evaluated = set()
            
            # Read the CSV file if it exists to get already evaluated files
            if os.path.exists(result_file) and os.path.getsize(result_file) > 0:
                with open(result_file, 'r') as csv_file:
                    reader = csv.reader(csv_file)
                    next(reader)  # Skip header row
                    for row in reader:
                        if row:  # Make sure row is not empty
                            already_evaluated.add(row[0])  # First column contains file name
            
            # Skip files that have already been evaluated
            file_name = filename.split(".")[0]
            if file_name in already_evaluated:
                print(f"Skipping {file_name} - already evaluated")
                continue
            # if filename == 'STEINS_ALGORITHM_FOR_FINDING_GCD.java':
            #     continue
            if filename.endswith(".java"):
                print("####file: ", i,filename)
                input_code, example_input = extract_input_code(os.path.join(input_dir, filename))
                result = Translator.invoke({
                    "model": self.model,
                    "eval_model": self.eval_model,
                    "input_lang": self.input_lang,
                    "output_lang": self.output_lang,
                    "input_code": input_code,
                    "sample_inputs": example_input,
                    "num_iter": 0,
                    "max_iter": max_iter
                    })
                translated_code = clean_generated_code(result["translated_code"])
                passed = eval_pipeline(os.path.join(output_dir, file_name + ".py"), 
                                       translated_code, 
                                       self.input_lang, 
                                       self.output_lang, 
                                       result["num_iter"], 
                                       result["num_iter"] == max_iter, 
                                       result["History"])
                # Remove results.json file if it exists
                results_json_path = os.path.join(os.getcwd(), "results.json")
                print("passed: ", passed)
                if passed:
                    correct += 1
                print("Accuracy: ", correct/i*100, "%")
                if os.path.exists(results_json_path):
                    try:
                        os.remove(results_json_path)
                        print(f"Removed existing results.json file")
                    except Exception as e:
                        print(f"Error removing results.json: {e}")



# Example Multi-Agent Evaluation
Python_dir = "/Users/parsayoussefpour/Desktop/Dataset/Selected_Tests/python"
Java_dir = "/Users/parsayoussefpour/Desktop/Dataset/Selected_Tests/java"

java2py = CodeTranslator_Bonus("Java","Python")

java2py.Evaluate_pipeline(Java_dir, Python_dir, 5)
