"""Main runner for SQL Database Agent using Google Gemini"""
import os
import google.generativeai as genai
from agent import SQLAgent
from dotenv import load_dotenv
import time
from colorama import Fore, Style, init
init(autoreset=True)


load_dotenv()  # Load environment variables from .env file

def colorize_trace(block: str) -> str:
    """Colorize key sections in trace output"""
    return (
        block.replace("THOUGHT:", f"{Fore.GREEN}THOUGHT:{Style.RESET_ALL}")
        .replace("ACTION:", f"{Fore.YELLOW}ACTION:{Style.RESET_ALL}")
        .replace("OBSERVATION:", f"{Fore.CYAN}OBSERVATION:{Style.RESET_ALL}")
        .replace("FINAL ANSWER:", f"{Fore.RED}FINAL ANSWER:{Style.RESET_ALL}")
    )

def get_gemini_client():
    """Initialize Google Gemini client with better configuration"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found in environment variables. "
            "Please set it with: export GEMINI_API_KEY='your-api-key'"
        )
    
    genai.configure(api_key=api_key)

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
    print(Fore.CYAN + "=" * 60)
    print(Fore.MAGENTA + "SQL Database Agent - Powered by Google Gemini")
    print(Fore.CYAN + "=" * 60 + Style.RESET_ALL)
    print()
    
    # Initialize Gemini LLM
    try:
        llm_complete = get_gemini_client()
        print(f"{Fore.GREEN}✓ Gemini API initialized successfully{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to initialize Gemini: {e}{Style.RESET_ALL}")
        return
    
    # Initialize agent
    agent = SQLAgent(llm_complete, db_path="sample.sqlite", step_limit=6)
    print(f"{Fore.GREEN}✓ SQL Agent initialized{Style.RESET_ALL}\n")
    print()
    
    # Example queries to test
    queries = [
        # "What tables are in the database?",
        "Describe the sample table",
        "Describe the sample table",
        "Describe the sample table",
        # "How many rows are in the sample table?",
        # "Show me the first 5 rows from the sample table",
        # "What are the column names in the sample table?",
        # "List all unique cities in the sample table",
        # "How many women are in the database ?",
        # "What percentage of people have credit cards ?",
        # "How many first names start with 'A' ?",
        # "What is the most popular profession ?",
        "What is the sum of all ids in the sample table ?",
        "How many Brickmason have a Ford car?"
    ]
    
    # Run each query
    for i, query in enumerate(queries, 1):
        print(f"\n{Fore.BLUE}{'=' * 60}")
        print(f"QUERY {i}/{len(queries)}: {query}")
        print(f"{'=' * 60}{Style.RESET_ALL}")
        
        try:
            # Run the agent
            answer = agent.run(query)
            
            # Display final answer
            print(f"\n{Fore.MAGENTA}{'─' * 60}")
            print("FINAL ANSWER:")
            print(f"{'─' * 60}{Style.RESET_ALL}")
            print(Fore.LIGHTWHITE_EX + answer + Style.RESET_ALL)
            print()
            
            # Display full trace (optional - can be commented out)
            if agent.history_blocks:
                print(f"{Fore.YELLOW}{'─' * 60}")
                print("FULL TRACE:")
                print(f"{'─' * 60}{Style.RESET_ALL}")
                for step_num, block in enumerate(agent.history_blocks, 1):
                    print(f"\n{Fore.BLUE}--- Step {step_num} ---{Style.RESET_ALL}")
                    print(colorize_trace(block))
            
            # Display logs (optional)
            if agent.logs:
                print(f"\n{Fore.MAGENTA}{'─' * 60}")
                print("AGENT LOGS:")
                print(f"{'─' * 60}{Style.RESET_ALL}")
                for log in agent.logs:
                    print(Fore.LIGHTBLACK_EX + log + Style.RESET_ALL)

        
        except Exception as e:
            print(f"\n{Fore.RED}✗ Error processing query: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
        
        # Reset agent history for next query
        agent.history_blocks = []
        agent.logs = []
        
        print()

        time.sleep(10)  # brief pause between queries
    
    print(Fore.CYAN + "=" * 60)
    print(Fore.GREEN + "All queries completed!")
    print(Fore.CYAN + "=" * 60 + Style.RESET_ALL)


def interactive_mode():
    """Interactive mode - ask questions one by one"""
    print(Fore.CYAN + "=" * 60)
    print(Fore.MAGENTA + "SQL Database Agent - Interactive Mode")
    print(Fore.CYAN + "=" * 60 + Style.RESET_ALL)
    print()
    
    # Initialize
    try:
        llm_complete = get_gemini_client()
        agent = SQLAgent(llm_complete, db_path="sample.sqlite", step_limit=6)
        print(f"{Fore.GREEN}✓ Agent initialized. Type 'exit' or 'quit' to stop.{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to initialize: {e}{Style.RESET_ALL}")
        return
    
    while True:
        try:
            query = input(Fore.CYAN + "\n🔍 Your question: " + Style.RESET_ALL).strip()
            if query.lower() in ['exit', 'quit', 'q']:
                print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                break
            if not query:
                continue

            print(f"\n{Fore.MAGENTA}{'─' * 60}")
            print("Processing...")
            print(f"{'─' * 60}{Style.RESET_ALL}")

            answer = agent.run(query)

            print(f"\n{Fore.MAGENTA}{'─' * 60}")
            print("FINAL ANSWER:")
            print(f"{'─' * 60}{Style.RESET_ALL}")
            print(Fore.LIGHTWHITE_EX + answer + Style.RESET_ALL)
            print()
            
            # Display full trace
            if agent.history_blocks:
                print(f"{Fore.YELLOW}{'─' * 60}")
                print("FULL TRACE:")
                print(f"{'─' * 60}{Style.RESET_ALL}")
                for step_num, block in enumerate(agent.history_blocks, 1):
                    print(f"\n{Fore.BLUE}--- Step {step_num} ---{Style.RESET_ALL}")
                    print(colorize_trace(block))
            
            # Display logs
            if agent.logs:
                print(f"\n{Fore.MAGENTA}{'─' * 60}")
                print("AGENT LOGS:")
                print(f"{'─' * 60}{Style.RESET_ALL}")
                for log in agent.logs:
                    print(Fore.LIGHTBLACK_EX + log + Style.RESET_ALL)
            
            # Reset for next query
            agent.history_blocks = []
            agent.logs = []
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Interrupted. Goodbye!{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"\n{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    import sys
    
    # Check if interactive mode requested
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()