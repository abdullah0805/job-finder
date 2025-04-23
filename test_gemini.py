from relevance_analyzer import test_gemini_api

def main():
    is_working, message = test_gemini_api()
    print(f"API Status: {'Working' if is_working else 'Not Working'}")
    print(f"Message: {message}")

if __name__ == "__main__":
    main() 