# Test script for WriterBuddy Guardrails

def check_guardrails(text):
    if not text:
        return True, ""
        
    sensitive_keywords = ["sex", "harm", "violence", "porn", "blood", "kill", "death"]
    
    text_lower = text.lower()
    for word in sensitive_keywords:
        if word in text_lower:
            return False, "lets get into our topic"
            
    return True, ""

# Test Cases
tests = [
    ("Tell me a story about a kitten.", True),
    ("Let's talk about violence.", False),
    ("Something about sex.", False),
    ("A peaceful day at the beach.", True),
    ("He caused harm to others.", False)
]

print("Running Guardrails Tests...")
success = True
for text, expected_safe in tests:
    is_safe, msg = check_guardrails(text)
    status = "PASS" if is_safe == expected_safe else "FAIL"
    print(f"[{status}] Input: '{text}' -> Safe: {is_safe}, Msg: '{msg}'")
    if is_safe != expected_safe:
        success = False

if success:
    print("\n✅ All tests passed!")
else:
    print("\n❌ Some tests failed.")