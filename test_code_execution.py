#!/usr/bin/env python3
"""
Test script for the new code execution capabilities in CodeAIAgent
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import the agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.code_agent import CodeAIAgent

def test_basic_code_execution():
    """Test basic code execution functionality"""
    print("🧪 Testing Basic Code Execution...")
    
    try:
        # Initialize the agent
        agent = CodeAIAgent(interest="programming", language="python")
        
        # Test simple code execution
        simple_code = """
print("Hello, World!")
x = 5 + 3
print(f"5 + 3 = {x}")
"""
        
        result = agent.run_code(simple_code)
        print("✅ Basic Code Execution Result:")
        print(f"Output: {result['execution_output']}")
        print(f"Has Errors: {result['has_errors']}")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Basic Code Execution Test Failed: {e}")

def test_math_problem_solving():
    """Test math problem solving with code execution"""
    print("🧪 Testing Math Problem Solving...")
    
    try:
        agent = CodeAIAgent(interest="mathematics", language="python")
        
        # Test solving a math problem
        problem = "What is the sum of the first 50 prime numbers?"
        
        result = agent.solve_math_problem(problem)
        print("✅ Math Problem Solving Result:")
        print(f"Success: {result['success']}")
        print(f"Code: {result['code']}")
        print(f"Output: {result['output']}")
        if result['error']:
            print(f"Error: {result['error']}")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Math Problem Solving Test Failed: {e}")

def test_data_analysis():
    """Test data analysis with code execution"""
    print("🧪 Testing Data Analysis...")
    
    try:
        agent = CodeAIAgent(interest="data science", language="python")
        
        # Test data analysis
        data_description = "A list of numbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
        
        result = agent.analyze_data(data_description, "statistical")
        print("✅ Data Analysis Result:")
        print(f"Success: {result['success']}")
        print(f"Code: {result['code']}")
        print(f"Output: {result['output']}")
        if result['error']:
            print(f"Error: {result['error']}")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Data Analysis Test Failed: {e}")

def test_code_evaluation():
    """Test code evaluation with execution"""
    print("🧪 Testing Code Evaluation with Execution...")
    
    try:
        agent = CodeAIAgent(interest="programming", language="python")
        
        # Test code evaluation
        question = "Write a function that calculates the factorial of a number"
        user_code = """
def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n-1)

print(factorial(5))
"""
        
        result = agent.evaluate_code_with_execution(user_code, question)
        print("✅ Code Evaluation Result:")
        print(f"Score: {result['score']}")
        print(f"Has Errors: {result['has_errors']}")
        print(f"Evaluation: {result['evaluation']}")
        print(f"Execution Output: {result['execution_output']}")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Code Evaluation Test Failed: {e}")

def test_complex_code_execution():
    """Test complex code execution with the new API"""
    print("🧪 Testing Complex Code Execution...")
    
    try:
        agent = CodeAIAgent(interest="algorithms", language="python")
        
        # Test complex code execution
        complex_prompt = """
        Generate and run code to find all prime numbers between 1 and 100.
        Then calculate the sum of these prime numbers.
        """
        
        result = agent.execute_complex_code(complex_prompt)
        print("✅ Complex Code Execution Result:")
        print(f"Success: {result['success']}")
        print(f"Code: {result['code']}")
        print(f"Output: {result['output']}")
        if result['error']:
            print(f"Error: {result['error']}")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Complex Code Execution Test Failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Code Execution Tests...")
    print("=" * 60)
    
    # Check if API key is available
    load_dotenv()
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY environment variable is not set!")
        print("Please set your Gemini API key in the .env file")
        return
    
    # Run tests
    test_basic_code_execution()
    test_math_problem_solving()
    test_data_analysis()
    test_code_evaluation()
    test_complex_code_execution()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main() 