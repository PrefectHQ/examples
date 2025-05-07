def greet(name: str) -> str:
    message = f"Hello, {name}!"
    print(message)
    return message


if __name__ == "__main__":
    greet("World")
