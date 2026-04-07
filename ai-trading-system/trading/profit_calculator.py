import numpy as np

def calculate_profit(current, predicted, capital=10000):
    """
    Calculate expected profit percentage and absolute profit.
    
    Args:
        current (float): Current price
        predicted (float): Predicted future price  
        capital (float): Trading capital
    """
    percent = ((predicted - current) / current) * 100
    profit = capital * (percent / 100)
    
    return {
        "percent": round(percent, 2),
        "profit": round(profit, 2)
    }

if __name__ == "__main__":
    # Test
    result = calculate_profit(100, 105)
    print(result)

