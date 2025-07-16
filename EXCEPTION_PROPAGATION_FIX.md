# Fix for Error Messages Not Being Recorded

## Problem Identified

The issue was that error messages were not being recorded in chat messages with assistant role because:

1. **Exception Swallowing**: The `generate_llm_response()` function in `inference.py` was catching all exceptions and returning `None` instead of propagating them to the chat API layer.

2. **Error Flow Broken**: The chat API's error handling was never triggered because no exceptions were reaching it - they were being swallowed in the inference layer.

3. **Silent Failures**: When rate limit or other errors occurred, users saw no response and no error message was stored in the database.

## Root Cause

```python
# OLD CODE (Problem):
def generate_llm_response(...):
    try:
        # LLM invocation code
        return response
    except Exception as e:
        logger.error(f"Error invoking model: {str(e)}")
        return None  # ❌ This swallowed the exception!
```

The exception was logged but not propagated, so the chat API never knew an error occurred.

## Solution Implemented

### 1. Fixed Exception Propagation in inference.py

**Before:**
```python
except Exception as e:
    logger.error(f"Error invoking model: {str(e)}")
    return None
```

**After:**
```python
except Exception as e:
    logger.error(f"Error invoking model: {str(e)}")
    # Re-raise the exception so the chat API can handle it with user-friendly messages
    raise e
```

### 2. Applied Same Fix to All Inference Functions

Fixed both:
- `generate_llm_response()`
- `continue_conversation_after_tool()`

### 3. Enhanced Error Flow

Now the error flow works correctly:

```
1. Error occurs in inference layer (e.g., rate limit 413)
2. Error is logged in inference.py
3. Exception is re-raised
4. Chat API catches specific exception types
5. create_error_assistant_message() creates user-friendly message
6. Error message stored as assistant response in database
7. User sees helpful error message in chat
```

## Files Modified

1. **`/service/viki_ai/app/utils/inference.py`**
   - Changed exception handling to re-raise exceptions
   - Maintains logging but allows propagation

2. **`/test_exception_propagation.py`** (new)
   - Test script to verify the fix

## Expected Behavior Now

When the rate limit error occurs:

1. **Service Log** will show:
   ```
   [ERROR] Error invoking model: Error code: 413 - {'error': {'message': 'Request too large for model...'}}
   ```

2. **Chat Messages Table** will have new assistant message:
   ```sql
   INSERT INTO chat_messages (msg_role, msg_content, ...)
   VALUES ('assistant', 'I apologize, but I've encountered a rate limit error...')
   ```

3. **User Interface** will display:
   ```
   I apologize, but I've encountered a rate limit error. The request was too large for meta-llama/llama-4-maverick-17b-128e-instruct.

   **Error Details:**
   - **Limit:** 6000 tokens per minute
   - **Requested:** 12743 tokens
   - **Issue:** Your message or conversation context is too large

   **What you can try:**
   1. **Reduce message size:** Try sending a shorter message
   2. **Start a new conversation:** Begin a fresh chat session to reduce context size
   3. **Break down your request:** Split complex requests into smaller parts
   4. **Upgrade service tier:** Consider upgrading your plan for higher limits

   Please try again with a smaller message or start a new conversation.
   ```

## Testing the Fix

1. **Restart the service** to load the updated code
2. **Send a large message** that triggers the rate limit
3. **Check the chat interface** - should now see an assistant error message
4. **Check database**:
   ```sql
   SELECT msg_role, msg_content, creation_dt 
   FROM chat_messages 
   WHERE msg_role = 'assistant' 
   ORDER BY creation_dt DESC 
   LIMIT 5;
   ```

## Verification

The fix ensures that:
- ✅ Exceptions are properly propagated from inference to chat API
- ✅ User-friendly error messages are created and stored
- ✅ Error details are still logged for debugging
- ✅ Users receive helpful guidance instead of silent failures
- ✅ Chat history maintains complete conversation context including errors

This resolves the issue where error messages were not getting recorded in chat messages with assistant role.
