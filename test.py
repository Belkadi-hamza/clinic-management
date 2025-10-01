#!/usr/bin/env python3
from passlib.context import CryptContext
import sys

# Configure CryptContext (bcrypt is a good default)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

MENU = """\nChoose an option:
1) txt => encrypt (hash text)
2) encrypt => txt (verify text against a hash)
3) exit
Enter choice: """

def hash_text(plain: str) -> str:
    """Return hashed representation of plain text."""
    return pwd_ctx.hash(plain)

def verify_text(plain: str, hashed: str) -> bool:
    """Return True if plain matches the hashed value."""
    try:
        return pwd_ctx.verify(plain, hashed)
    except Exception:
        return False

def main():
    while True:
        try:
            choice = input(MENU).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

        if choice == "1":
            txt = input("Enter text to encrypt (visible): ")
            if txt == "":
                print("Empty input — nothing done.")
                continue
            hashed = hash_text(txt)
            print("\nHashed result (store this safely):\n")
            print(hashed)
            print("\nTip: use option 2 to verify this hash later.")

        elif choice == "2":
            hashed = input("Enter the hashed value: ").strip()
            if not hashed:
                print("No hash provided.")
                continue
            plain = input("Enter the plain text to verify (visible): ")
            if plain == "":
                print("Empty input — nothing to verify.")
                continue
            ok = verify_text(plain, hashed)
            if ok:
                print("✅ Match: the plain text corresponds to the hash.")
            else:
                print("❌ No match: the plain text DOES NOT correspond to the hash.")

        elif choice == "3":
            print("Goodbye.")
            sys.exit(0)
        else:
            print("Invalid choice. Select 1, 2, or 3.")

if __name__ == "__main__":
    main()