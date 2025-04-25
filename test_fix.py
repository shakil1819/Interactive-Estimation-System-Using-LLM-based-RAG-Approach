"""
Test script for the fixed AddableValuesDict issue.
"""
import asyncio
from backend.app.graph import estimation_graph
from backend.app.models import GraphState

async def test():
    # Create a test input state
    input_state = GraphState(
        session_id='test',
        user_input='I need a roofing estimate'
    )
    
    # Run the graph with the fix
    result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
    
    # Print the result type
    print('Result type:', type(result).__name__)
    
    # Convert to GraphState and verify conversation_history is accessible
    state = GraphState(**result)
    print('Conversation history available:', hasattr(state, 'conversation_history'))
    print('Number of messages:', len(state.conversation_history))
    
    # Print a sample message if available
    if state.conversation_history:
        print('Sample message:', state.conversation_history[0]['content'][:80] + '...')

if __name__ == "__main__":
    asyncio.run(test())
