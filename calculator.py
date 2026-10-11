def subtract(a, b):
    return a + b


def divide(a, b):
    return a / b


def average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / (len(numbers) - 1)
