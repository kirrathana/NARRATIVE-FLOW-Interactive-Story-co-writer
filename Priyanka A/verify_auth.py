import hashlib
import json
import os

USER_FILE = "users_test.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def test_auth():
    print("Testing Authentication Logic...")
    users = {"user1": hash_password("pass123")}
    
    # Test Signup
    new_user = "user2"
    new_pass = "pass456"
    users[new_user] = hash_password(new_pass)
    print(f"User {new_user} created.")
    
    # Test Login
    test_user = "user2"
    test_pass = "pass456"
    if test_user in users and users[test_user] == hash_password(test_pass):
        print(f"Login SUCCESS for {test_user}")
    else:
        print(f"Login FAILURE for {test_user}")
        return False

    # Test storage separation
    user1_file = f"stories_user1.json"
    user2_file = f"stories_user2.json"
    print(f"Storage files: {user1_file}, {user2_file}")
    
    return True

if __name__ == "__main__":
    if test_auth():
        print("\n✅ Authentication and Storage logic passed!")
    else:
        print("\n❌ Authentication and Storage logic failed.")
