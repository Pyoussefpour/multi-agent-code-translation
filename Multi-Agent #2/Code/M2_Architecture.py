from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import os
import csv
import subprocess

from Agent_class_M2 import AgentState, clean_generated_code
from Analyzer_Agent_M2 import Analyze_code, Analyze_UnitTest, Analyze_AST, Analyze_Regenerator, conditional_next_regen_node, Deep_Analyze_code
from UnitTestGen_Agent_M2 import Create_Input_node, Create_TestCode_node, Check_TestCode_node, conditional_llm_check, Regenerate_code_node, Run_TestGen_node, conditional_error_check
from Translator_Agent_M2 import Translator_node
from Evaluator_Tool_M2 import Check_testing_status, conditional_merge_or_wait, UnitTest_Script_node, Run_test_node, Conditional_output, Output_node
from Regenerator_Agent_M2 import Check_error_type, Regenerate_Function_node, Regenerate_Script_node
from Evaluation_M2 import  extract_input_code, eval_pipeline

class CodeTranslator:
    def __init__(self, input_lang: str, output_lang: str, model=None):
        self.input_lang = input_lang
        self.output_lang = output_lang
        self.model = model if model is not None else ChatOpenAI(model="gpt-4o", temperature=0)

    def generate_unit_test(self, code:str):
        UnitTestGen = StateGraph(AgentState)

        UnitTestGen.add_node("Input_test",Create_Input_node)
        UnitTestGen.add_node("Create_code",Create_TestCode_node)
        UnitTestGen.add_node("Check_code",Check_TestCode_node)
        UnitTestGen.add_node("Regen_code",Regenerate_code_node)
        UnitTestGen.add_node("Run_code",Run_TestGen_node)


        UnitTestGen.set_entry_point("Input_test")
        UnitTestGen.add_edge("Input_test","Create_code")
        UnitTestGen.add_edge("Create_code", "Check_code")
        UnitTestGen.add_conditional_edges("Check_code",conditional_llm_check,
                                          {
                                              "continue": "Run_code",
                                              "regenerate": "Regen_code"
                                          })
        UnitTestGen.add_conditional_edges("Run_code",conditional_error_check,
                                          {
                                              "continue": END,
                                              "regenerate": "Regen_code"
                                          })
        UnitTestGen.add_edge("Regen_code","Run_code")

        UnitTest = UnitTestGen.compile()
        result = UnitTest.invoke({"model":self.model,
                                  "input_lang":self.input_lang,
                                  "output_lang":self.output_lang,
                                  "input_code":code})
        return result
    
    def translator_architecture(self):
        Translator = StateGraph(AgentState)

        #Analyzer
        Translator.add_node("Analyze_code",Analyze_code)
        Translator.add_node("Analyze_UnitTest",Analyze_UnitTest)
        Translator.add_node("Analyze_AST",Analyze_AST)
        Translator.add_node("Analyze_Regenerator",Analyze_Regenerator)

        #Unit Test Generator
        Translator.add_node("Input_test_UTest",Create_Input_node)
        Translator.add_node("Create_code_UTest",Create_TestCode_node)
        Translator.add_node("Check_code_UTest",Check_TestCode_node)
        Translator.add_node("Regen_code_UTest",Regenerate_code_node)
        Translator.add_node("Run_code_UTest",Run_TestGen_node)

        #Translator
        Translator.add_node("Input_code_Translate",Translator_node)

        #Evaluator
        Translator.add_node("Merge_check",Check_testing_status)
        Translator.add_node("Create_UT_script",UnitTest_Script_node)
        Translator.add_node("Run_UT_script",Run_test_node)
        Translator.add_node("MA_Output",Output_node)

        #Regenerator
        Translator.add_node("Error_Analysis",Check_error_type)
        Translator.add_node("Regen_function",Regenerate_Function_node)
        Translator.add_node("Regen_test_script",Regenerate_Script_node)

        #Architecture
        
        Translator.set_entry_point("Analyze_AST")
        Translator.add_edge("Analyze_AST","Analyze_UnitTest")
        Translator.add_edge("Analyze_UnitTest","Input_test_UTest")
        Translator.add_edge("Input_test_UTest","Create_code_UTest")
        Translator.add_edge("Create_code_UTest","Check_code_UTest")
        Translator.add_conditional_edges("Check_code_UTest",conditional_llm_check,
                                        {
                                            "continue": "Run_code_UTest",
                                            "regenerate": "Analyze_Regenerator"
                                        })
        Translator.add_edge("Regen_code_UTest","Run_code_UTest")
        Translator.add_conditional_edges("Run_code_UTest",conditional_error_check,
                                        {
                                            "continue": "Merge_check",
                                            "regenerate": "Analyze_Regenerator"
                                        })
        
        
        Translator.add_edge("Analyze_AST", "Analyze_code")
        Translator.add_edge("Analyze_code","Input_code_Translate")
        Translator.add_edge("Input_code_Translate","Merge_check")
        Translator.add_conditional_edges("Merge_check", conditional_merge_or_wait,
                                        {
                                            "Continue": "Create_UT_script",
                                            "Wait": "Merge_check"
                                        })
        
        Translator.add_edge("Create_UT_script","Run_UT_script")
        Translator.add_conditional_edges("Run_UT_script",Conditional_output,
                                        {
                                            "Continue": "MA_Output",
                                            "Max_reached": "MA_Output",
                                            "Error": "Error_Analysis"
                                        })
        Translator.add_edge("Error_Analysis","Analyze_Regenerator")

        Translator.add_conditional_edges("Analyze_Regenerator",conditional_next_regen_node,
                                        {
                                            "Regen_code_UTest": "Regen_code_UTest",
                                            "Function": "Regen_function",
                                            "Unit Test": "Regen_test_script"
                                        })
       
        Translator.add_edge("Regen_function","Run_UT_script")
        Translator.add_edge("Regen_test_script","Run_UT_script")
        Translator.add_edge("MA_Output",END)
        return Translator.compile()
    
    def Deep_Analyzer_architecture(self):
        Translator = StateGraph(AgentState)

        #Analyzer
        Translator.add_node("Analyze_UnitTest",Analyze_UnitTest)
        Translator.add_node("Analyze_AST",Analyze_AST)
        Translator.add_node("Analyze_Regenerator",Analyze_Regenerator)
        Translator.add_node("Deep_Analyze_code",Deep_Analyze_code)

        #Unit Test Generator
        Translator.add_node("Input_test_UTest",Create_Input_node)
        Translator.add_node("Create_code_UTest",Create_TestCode_node)
        Translator.add_node("Check_code_UTest",Check_TestCode_node)
        Translator.add_node("Regen_code_UTest",Regenerate_code_node)
        Translator.add_node("Run_code_UTest",Run_TestGen_node)

        #Translator
        Translator.add_node("Input_code_Translate",Translator_node)

        #Evaluator
        Translator.add_node("Merge_check",Check_testing_status)
        Translator.add_node("Create_UT_script",UnitTest_Script_node)
        Translator.add_node("Run_UT_script",Run_test_node)
        Translator.add_node("MA_Output",Output_node)

        #Regenerator
        Translator.add_node("Error_Analysis",Check_error_type)
        Translator.add_node("Regen_function",Regenerate_Function_node)
        Translator.add_node("Regen_test_script",Regenerate_Script_node)

        #Architecture
        
        Translator.set_entry_point("Analyze_AST")
        Translator.add_edge("Analyze_AST","Analyze_UnitTest")
        Translator.add_edge("Analyze_UnitTest","Input_test_UTest")
        Translator.add_edge("Input_test_UTest","Create_code_UTest")
        Translator.add_edge("Create_code_UTest","Check_code_UTest")
        Translator.add_conditional_edges("Check_code_UTest",conditional_llm_check,
                                        {
                                            "continue": "Run_code_UTest",
                                            "regenerate": "Analyze_Regenerator"
                                        })
        Translator.add_edge("Regen_code_UTest","Run_code_UTest")
        Translator.add_conditional_edges("Run_code_UTest",conditional_error_check,
                                        {
                                            "continue": "Merge_check",
                                            "regenerate": "Analyze_Regenerator"
                                        })
        
        
        Translator.add_edge("Analyze_AST", "Deep_Analyze_code")
        Translator.add_edge("Deep_Analyze_code","Input_code_Translate")
        Translator.add_edge("Input_code_Translate","Merge_check")
        Translator.add_conditional_edges("Merge_check", conditional_merge_or_wait,
                                        {
                                            "Continue": "Create_UT_script",
                                            "Wait": "Merge_check"
                                        })
        
        Translator.add_edge("Create_UT_script","Run_UT_script")
        Translator.add_conditional_edges("Run_UT_script",Conditional_output,
                                        {
                                            "Continue": "MA_Output",
                                            "Max_reached": "MA_Output",
                                            "Error": "Error_Analysis"
                                        })
        Translator.add_edge("Error_Analysis","Analyze_Regenerator")

        Translator.add_conditional_edges("Analyze_Regenerator",conditional_next_regen_node,
                                        {
                                            "Regen_code_UTest": "Regen_code_UTest",
                                            "Function": "Regen_function",
                                            "Unit Test": "Regen_test_script"
                                        })
       
        Translator.add_edge("Regen_function","Run_UT_script")
        Translator.add_edge("Regen_test_script","Run_UT_script")
        Translator.add_edge("MA_Output",END)
        return Translator.compile()

    def Evaluate_pipeline(self, input_dir: str, output_dir: str, max_iter: int):
        Translator = self.translator_architecture()
        correct = 0
        for i, filename in enumerate(sorted(os.listdir(input_dir))):
            # Check if file has already been evaluated
            result_file = f"Final_2_results_{self.input_lang}_{self.output_lang}.csv"
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
  
            if filename.endswith(".py"):
                print("####file: ", i,filename)
                input_code, example_input = extract_input_code(os.path.join(input_dir, filename))
                result = Translator.invoke({
                    "model": self.model,
                    "input_lang": self.input_lang,
                    "output_lang": self.output_lang,
                    "input_code": input_code,
                    "example_inputs": example_input,
                    "num_iter": 0,
                    "max_iter": max_iter
                    })
                translated_code = clean_generated_code(result["output_code"])
                passed = eval_pipeline(os.path.join(output_dir, file_name + ".java"), 
                                       translated_code, 
                                       self.input_lang, 
                                       self.output_lang, 
                                       result["num_iter"], 
                                       result["num_iter"] == max_iter, 
                                       result["code_status"], 
                                       result["Translator_history"], 
                                       result["UnitTest_history"])
                if passed:
                    correct += 1
                print("Accuracy: ", correct/i*100, "%")
                results_json_path = os.path.join(os.getcwd(), "results.json")
                if os.path.exists(results_json_path):
                    try:
                        os.remove(results_json_path)
                        print(f"Removed existing results.json file")
                    except Exception as e:
                        print(f"Error removing results.json: {e}")



# Example Multi-Agent Evaluation
Python_dir = "/Users/parsayoussefpour/Desktop/Dataset/Selected_Tests/python"
Java_dir = "/Users/parsayoussefpour/Desktop/Dataset/Selected_Tests/java"

java2py = CodeTranslator("Python","Java")

java2py.Evaluate_pipeline(Python_dir, Java_dir, 2)
