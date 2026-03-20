import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.rag.retrieve import retrieve_context
from core.database.postgresDatabase import PostgresDatabase

async def main():
    print("Initializing Database...")
    db = PostgresDatabase()
    
    # You might need a valid project name from your DB
    project_name = "Mind-Trace" 
    query = "database schema"

    print(f"Retrieving context for query: '{query}' in project: '{project_name}'")
    
    try:
        docs = await retrieve_context(query, project_name)
        
        print(f"\nFound {len(docs)} documents:")
        for i, doc in enumerate(docs):
            print(f"\n[{i+1}] Source: {doc.metadata.get('source')} - Type: {doc.metadata.get('type')}")
            print(f"    Score: {doc.metadata.get('score')}")
            print(f"    Content Preview: {doc.page_content[:100]}...")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
