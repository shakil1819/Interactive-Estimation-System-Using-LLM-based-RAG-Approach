"""
Comprehensive test script for all fixed issues in the Interactive Estimation System.
"""
import asyncio
import warnings
from backend.app.graph import process_user_message, estimation_graph
from backend.app.models import GraphState

async def test_recursion_fix():
    """Test that we can run the graph with an increased recursion limit"""
    print("\n=== Testing Recursion Fix ===")
    
    # Create a test input state
    input_state = GraphState(
        session_id='test_recursion',
        user_input='I need a roofing estimate'
    )
    
    try:
        # Run the graph with the fix using ainvoke
        result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
        print('✅ Graph executed successfully with increased recursion limit')
        return True
    except RecursionError:
        print('❌ Still encountering recursion issues')
        return False

async def test_addable_values_conversion():
    """Test that we can properly convert Langgraph's AddableValuesDict to GraphState"""
    print("\n=== Testing AddableValuesDict Conversion ===")
    
    # Create a test input state
    input_state = GraphState(
        session_id='test_conversion',
        user_input='I need a roofing estimate for a 2000 sq ft house in the northeast'
    )
    
    # Run the graph with the fix
    result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
    
    try:
        # Convert to GraphState
        state = GraphState(**result)
        print('✅ Successfully converted to GraphState')
        print(f'  - Conversation history length: {len(state.conversation_history)}')
        
        if len(state.conversation_history) > 0:
            print(f'  - First message: {state.conversation_history[0]["content"][:50]}...')
        
        return True
    except Exception as e:
        print(f'❌ Conversion failed: {e}')
        return False

async def test_infinite_recursion_fix():
    """Test that the graph properly ends and doesn't loop indefinitely"""
    print("\n=== Testing Infinite Recursion Fix ===")
    
    # Create a test input state
    input_state = GraphState(
        session_id='test_infinite',
        user_input='I need a roofing estimate for a 2000 sq ft house in the northeast with asphalt shingles on a standard timeline'
    )
    
    try:
        # This should provide all needed info in one shot, so should process and end
        result = await estimation_graph.ainvoke(input_state, {"recursion_limit": 100})
        state = GraphState(**result)
        
        # Check if we got a response
        if state.conversation_history and len(state.conversation_history) > 0:
            print('✅ Graph properly terminated')
            last_message = state.conversation_history[-1]["content"]
            print(f'  - Last message: {last_message[:50]}...')
            return True
        else:
            print('❌ No response generated')
            return False
    except Exception as e:
        print(f'❌ Test failed: {e}')
        return False

async def test_repetitive_response_fix():
    """Test that the system doesn't repeat 'I have all the information I need' after an estimate"""
    print("\n=== Testing Repetitive Response Fix ===")
    
    # Create a session for a multi-turn conversation
    session_id = 'test_repetitive'
    
    # First message with complete information
    state1 = await process_user_message(session_id, "I need a roofing estimate for a 2000 sq ft house in the northeast with asphalt shingles on a standard timeline")
    
    # Print first response
    print(f"First response: {state1.conversation_history[-1]['content'][:50]}...")
    
    # Second message - a follow-up question
    state2 = await process_user_message(session_id, "Thank you! Do you offer any warranty?", state1)
    
    # Check if the second response is different from the first
    if "I have all the information I need" not in state2.conversation_history[-1]["content"]:
        print('✅ System provided a contextual response instead of repeating')
        print(f'  - Follow-up response: {state2.conversation_history[-1]["content"][:50]}...')
        return True
    else:
        print('❌ System is still repeating the same message')
        return False

async def test_contextual_responses():
    """Test that the system provides contextual responses for different follow-up questions"""
    print("\n=== Testing Contextual Responses ===")
    
    # Create a session for a multi-turn conversation
    session_id = 'test_contextual'
    
    # First message with complete information
    state1 = await process_user_message(session_id, "I need a roofing estimate for a 2000 sq ft house in the northeast with asphalt shingles on a standard timeline")
    
    # Array of follow-up questions to test
    follow_ups = [
        "Hello",
        "What kind of materials do you use?",
        "How long will it take?",
        "Do you offer any warranty?",
        "Thank you for the information"
    ]
    
    all_passed = True
    for question in follow_ups:
        state1 = await process_user_message(session_id, question, state1)
        response = state1.conversation_history[-1]["content"]
        print(f"\nQ: {question}")
        print(f"A: {response[:100]}...")
        
        # Check if response is contextually relevant
        if "I have all the information I need" in response:
            print('❌ Non-contextual response detected')
            all_passed = False
    
    if all_passed:
        print('✅ All responses were contextually appropriate')
    
    return all_passed

async def run_all_tests():
    """Run all test cases and report results"""
    test_results = {
        "Recursion Fix": await test_recursion_fix(),
        "AddableValuesDict Conversion": await test_addable_values_conversion(),
        "Infinite Recursion Fix": await test_infinite_recursion_fix(),
        "Repetitive Response Fix": await test_repetitive_response_fix(),
        "Contextual Responses": await test_contextual_responses()
    }
    
    print("\n=== Test Results Summary ===")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(test_results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

if __name__ == "__main__":
    # Suppress warnings for cleaner output
    warnings.filterwarnings("ignore", category=UserWarning)
    asyncio.run(run_all_tests())
