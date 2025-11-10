"""Main runner for SQL Database Agent using Google Gemini"""
import os
import google.generativeai as genai
from agent import SQLAgent
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def get_gemini_client():
    """Initialize Google Gemini client with better configuration"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found in environment variables. "
            "Please set it with: export GEMINI_API_KEY='your-api-key'"
        )
    
    genai.configure(api_key=api_key)
    
    # Use gemini-1.5-pro for better instruction following
    # or stick with flash but with stricter settings
    
    # # Configure the API
    # genai.configure(api_key=api_key)
    
    # Create the model
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    def complete(prompt: str) -> str:
        """
        Send prompt to Gemini and get response
        
        Args:
            prompt: The prompt to send to Gemini
        
        Returns:
            The text response from Gemini
        """
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0,  # Deterministic outputs
                    max_output_tokens=2048,
                )
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            raise
    
    return complete


def main():
    """Main function to run the SQL Database Agent"""
    print("=" * 60)
    print("SQL Database Agent - Powered by Google Gemini")
    print("=" * 60)
    print()
    
    # Initialize Gemini LLM
    try:
        llm_complete = get_gemini_client()
        print("✓ Gemini API initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize Gemini: {e}")
        return
    
    # Initialize agent
    agent = SQLAgent(llm_complete, db_path="sample.sqlite", step_limit=6)
    print("✓ SQL Agent initialized")
    print()
    
    # Example queries to test
    queries = [
        # "What tables are in the database?",
        # "Describe the sample table",
        # "How many rows are in the sample table?",
        # "Show me the first 5 rows from the sample table",
        # "What are the column names in the sample table?",
        # "List all unique cities in the sample table",
        # "How many men in the database ?",
        # "What percentage of people have credit cards ?",
        # "How many first names start with 'A' ?",
        "What is the most popular profession ?",
        "How many plasterers have a Mitsubishi car?"
    ]
    
    # Run each query
    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 60}")
        print(f"QUERY {i}/{len(queries)}: {query}")
        print('=' * 60)
        
        try:
            # Run the agent
            answer = agent.run(query)
            
            # Display final answer
            print(f"\n{'─' * 60}")
            print("FINAL ANSWER:")
            print('─' * 60)
            print(answer)
            print()
            
            # Display full trace (optional - can be commented out)
            if agent.history_blocks:
                print(f"{'─' * 60}")
                print("FULL TRACE:")
                print('─' * 60)
                for step_num, block in enumerate(agent.history_blocks, 1):
                    print(f"\n--- Step {step_num} ---")
                    print(block)
            
            # Display logs (optional)
            if agent.logs:
                print(f"\n{'─' * 60}")
                print("AGENT LOGS:")
                print('─' * 60)
                for log in agent.logs:
                    print(log)
        
        except Exception as e:
            print(f"\n✗ Error processing query: {e}")
            import traceback
            traceback.print_exc()
        
        # Reset agent history for next query
        agent.history_blocks = []
        agent.logs = []
        
        print()
    
    print("=" * 60)
    print("All queries completed!")
    print("=" * 60)


def interactive_mode():
    """Interactive mode - ask questions one by one"""
    print("=" * 60)
    print("SQL Database Agent - Interactive Mode")
    print("=" * 60)
    print()
    
    # Initialize
    try:
        llm_complete = get_gemini_client()
        agent = SQLAgent(llm_complete, db_path="sample.sqlite", step_limit=6)
        print("✓ Agent initialized. Type 'exit' or 'quit' to stop.\n")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return
    
    while True:
        try:
            # Get user input
            query = input("\n🔍 Your question: ").strip()
            
            # Check for exit
            if query.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break
            
            if not query:
                continue
            
            # Run agent
            print(f"\n{'─' * 60}")
            print("Processing...")
            print('─' * 60)
            
            answer = agent.run(query)
            
            # Display final answer
            print(f"\n{'─' * 60}")
            print("FINAL ANSWER:")
            print('─' * 60)
            print(answer)
            print()
            
            # Display full trace
            if agent.history_blocks:
                print(f"{'─' * 60}")
                print("FULL TRACE:")
                print('─' * 60)
                for step_num, block in enumerate(agent.history_blocks, 1):
                    print(f"\n--- Step {step_num} ---")
                    print(block)
            
            # Display logs
            if agent.logs:
                print(f"\n{'─' * 60}")
                print("AGENT LOGS:")
                print('─' * 60)
                for log in agent.logs:
                    print(log)
            
            # Reset for next query
            agent.history_blocks = []
            agent.logs = []
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    import sys
    
    # Check if interactive mode requested
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()