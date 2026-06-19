class DocumentID(str):
    def __new__(cls, content, owner):
        # __new__ handles the string creation
        return super().__new__(cls, content)

    def __init__(self, content, owner):
        # __init__ handles extra state attributes
        self.owner = owner

# Usage
doc = DocumentID("abc-123", "Alice")
print(doc)        # Output: abc-123 (behaves like a string)
print(doc.owner)  # Output: Alice (custom attribute)
