#!/usr/bin/env python3
"""
Fix vector casting in database queries
"""

import os
import re

def fix_database_queries():
    """Fix vector casting in database manager"""
    
    files_to_check = [
        "core/database_manager.py", 
        "database_manager.py"
    ]
    
    for filepath in files_to_check:
        if not os.path.exists(filepath):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix find_similar_conversations function
            old_pattern = r"""# Query with vector similarity
            query = \"\"\"
                SELECT id, user_message, alice_response, intent, 
                       \(embedding <-> %s\) as similarity
                FROM conversations 
                WHERE \(embedding <-> %s\) < 0\.8
            \"\"\""""
            
            new_pattern = """# Query with vector similarity using proper casting
            query = \"\"\"
                SELECT id, user_message, alice_response, intent, 
                       (embedding <-> %s::vector) as similarity
                FROM conversations 
                WHERE (embedding <-> %s::vector) < 0.8
            \"\"\""""
            
            content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)
            
            # Also fix template search
            content = re.sub(
                r'\(embedding <-> %s\)', 
                r'(embedding <-> %s::vector)', 
                content
            )
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Fixed vector casting in {filepath}")
                return True
            else:
                print(f"ℹ️ No changes needed in {filepath}")
                
        except Exception as e:
            print(f"❌ Error fixing {filepath}: {e}")
    
    return False

def main():
    print("🔧 Fixing vector casting for Alice...")
    print("=" * 50)
    
    if fix_database_queries():
        print("✅ Database queries fixed")
    
    print("\n🎉 Vector search should now work perfectly!")
    print("Run: python alice_full_verification.py")

if __name__ == "__main__":
    main()
