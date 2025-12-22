# Agent Hallucination Analysis & Root Causes

## Problem Summary

The agent exhibits hallucination behavior where it:
1. Initially lists "Dr. Anil Gupta from Max Hospital" in search results
2. When user selects "Dr. Anil", agent claims it can't find him
3. When confronted, agent apologizes and says it will "pull up his information now"
4. Responses lack clear guidance for next steps

## Root Causes Identified

### 1. **Missing `name` Parameter in search_doctors Tool** ⚠️ CRITICAL

**Issue:**
- The `search_doctors` tool definition does NOT include a `name` parameter
- The underlying `search_doctors()` function in `data_loader.py` DOES support `name` parameter
- When user says "I will go with Dr. Anil", the LLM cannot search by name

**Code Evidence:**
```python
# tool_definitions.py - MISSING name parameter
SEARCH_DOCTORS_TOOL = {
    "parameters": {
        "properties": {
            "specialty": {...},
            "max_fee": {...},
            "language": {...},
            "clinic_id": {...}
            # ❌ NO "name" parameter!
        }
    }
}

# data_loader.py - SUPPORTS name parameter
def search_doctors(
    name: Optional[str] = None,  # ✅ This exists but tool doesn't expose it!
    specialty: Optional[str] = None,
    ...
)
```

**Impact:**
- LLM cannot search for doctors by name when user mentions a specific doctor
- Agent must rely on conversation history to find doctor info
- Leads to confusion and hallucination

### 2. **No Explicit Tool Usage for Name-Based Searches**

**Issue:**
- System prompt says "ALWAYS use search tools" but doesn't specify:
  - When user mentions a doctor name, use `get_doctor_details` with doctor_id
  - Or search by name if that parameter existed
- Agent tries to find doctor info from conversation history instead of using tools

**Impact:**
- Agent makes up or misremembers information
- Inconsistent responses across turns

### 3. **Weak System Prompt Instructions**

**Current Issues:**
```python
# Current system prompt lacks:
- No instruction to verify information using tools
- No instruction to reference tool results explicitly
- No instruction to provide clear next steps
- No instruction on how to handle when user mentions specific doctor names
```

**Impact:**
- Agent doesn't know to re-verify information
- Agent doesn't provide clear guidance
- Responses feel apologetic rather than helpful

### 4. **No Structured Data Extraction**

**Issue:**
- Agent relies entirely on LLM parsing conversation history
- No explicit state tracking for:
  - Which doctors were found
  - Which doctor user selected
  - Doctor IDs and details
- Tool results are stored as JSON strings in conversation history

**Impact:**
- LLM may misremember or confuse information
- No reliable way to track selected doctor
- Inconsistent state across conversation turns

### 5. **Tool Result Formatting**

**Issue:**
- Tool results are stored as JSON strings in conversation history
- LLM must parse JSON to extract information
- No structured extraction of key fields (doctor_id, name, etc.)

**Current Flow:**
```
Tool Result → JSON String → Stored in messages → LLM parses → May misremember
```

**Better Flow:**
```
Tool Result → Structured Data → Explicitly referenced → Consistent
```

### 6. **No Guidance on Next Steps**

**Issue:**
- System prompt doesn't instruct agent to provide clear next steps
- Agent responses are reactive rather than proactive
- No template for guiding user through booking flow

**Impact:**
- User doesn't know what to do next
- Agent seems confused or apologetic
- Poor user experience

## Specific Conversation Flow Analysis

### Turn 1: Initial Search
```
User: "I am having a chest pain"
Agent: [Calls search_doctors(specialty="Cardiology")]
Tool Result: [List of 4 doctors including "Dr. Anil Gupta - Max Hospital - ₹2000"]
Agent Response: Lists all 4 doctors including Dr. Anil Gupta
```

**✅ This works correctly** - Tool is called, results are returned

### Turn 2: User Selection
```
User: "I will go with Dr. Anil"
Agent: [Tries to find Dr. Anil but...]
```

**❌ Problem:** Agent cannot search by name because:
1. `search_doctors` tool doesn't have `name` parameter
2. Agent doesn't know to use `get_doctor_details` with doctor_id from previous results
3. Agent relies on conversation history which may be incomplete

**Result:** Agent suggests wrong doctor (Dr. Rajesh Kumar)

### Turn 3: User Correction
```
User: "no i said i want to go with dr anil"
Agent: [Still can't find Dr. Anil]
```

**❌ Problem:** Agent still doesn't have mechanism to:
1. Extract doctor_id from previous tool results
2. Use `get_doctor_details` to verify
3. Reference previous conversation accurately

### Turn 4: User Reminder
```
User: "but you said dr. anil gupta is from max"
Agent: "You're absolutely right, and I apologize..."
```

**❌ Problem:** 
- Agent apologizes instead of taking action
- Response is reactive, not proactive
- No clear next step provided

## Solutions

### Fix 1: Add `name` Parameter to search_doctors Tool ✅

**File:** `backend/tools/tool_definitions.py`

Add `name` parameter to allow searching by doctor name.

### Fix 2: Enhance System Prompt ✅

**File:** `backend/api/websocket.py`

Add instructions for:
- Always verify information using tools
- When user mentions doctor name, search for that specific doctor
- Provide clear next steps
- Reference tool results explicitly

### Fix 3: Improve Tool Result Handling ✅

**File:** `backend/api/websocket.py`

- Ensure tool results are properly formatted
- Add explicit instructions to use tool results
- Guide agent to extract and reference doctor_id

### Fix 4: Add Guidance Instructions ✅

**File:** `backend/api/websocket.py`

Add to system prompt:
- Always provide clear next steps
- Guide user through booking process
- Be proactive, not reactive

## Expected Behavior After Fixes

### Turn 1: Initial Search (Same)
```
User: "I am having a chest pain"
Agent: [Calls search_doctors(specialty="Cardiology")]
Agent Response: "I found 4 cardiologists. Here are your options:
1. Dr. Nisha Kapoor - AIIMS OPD - ₹1400
2. Dr. Priya Sharma - Apollo Clinic - ₹1500
3. Dr. Anil Gupta - Max Hospital - ₹2000
4. Dr. Rajesh Malhotra - Fortis Hospital - ₹1800

Which doctor would you like to book with?"
```

### Turn 2: User Selection (Fixed)
```
User: "I will go with Dr. Anil"
Agent: [Calls search_doctors(name="Anil") OR get_doctor_details(doctor_id="...")]
Agent Response: "Great! I found Dr. Anil Gupta at Max Hospital Saket. 
He's a Cardiologist with 12 years of experience. Consultation fee is ₹2000.
He's available Monday-Saturday, 9am-5pm.

What date would you like to book for?"
```

**✅ Clear next step provided**

### Turn 3: User Provides Date (Fixed)
```
User: "i want to book for 18th dec 2025"
Agent Response: "Perfect! I have Dr. Anil Gupta for December 18th, 2025.
What time would you prefer? He's available 9am-5pm."
```

**✅ Clear guidance on next step**

## Implementation Priority

1. **HIGH:** Add `name` parameter to search_doctors tool
2. **HIGH:** Enhance system prompt with verification instructions
3. **MEDIUM:** Add guidance instructions for next steps
4. **MEDIUM:** Improve tool result handling
5. **LOW:** Consider structured data extraction (future enhancement)

