import time
import pandas as pd
import numpy as np
import os
from trading.signal import generate_signal

def simulate_live_trading():
    capital = 10000.0
    position = 0.0
    entry_price = 0.0
    threshold = 0.003  # 0.3%
    
    print("Starting Live Trading Simulation...")
    print(f"Initial Capital: ${capital:.2f}")
    
    last_current_price = 0.0  # Track for final close
    
    for i in range(20):
        try:
            print("\n" + "="*50)
            print(f"Iteration {i+1}/20")
            print("Fetching live signal...")
            
            signal_data = generate_signal()
            current_price = signal_data["current_price"]
            predicted_price = signal_data["predicted_price"]
            last_current_price = current_price
            
            # Generate smarter signal with threshold
            if predicted_price > current_price * (1 + threshold):
                signal = "BUY"
            elif predicted_price < current_price * (1 - threshold):
                signal = "SELL"
            else:
                signal = "HOLD"
            
            # Print details
            print(f"Current Price: ${current_price:.2f}")
            print(f"Predicted Price: ${predicted_price:.2f}")
            print(f"Signal: {signal}")
            print(f"Capital: ${capital:.2f}")
            print(f"Position: {position:.0f} shares")
            
            # Execute trade
            if signal == "BUY" and position == 0:
                position = capital / current_price
                entry_price = current_price
                print("Executing BUY trade...")
            elif signal == "SELL" and position > 0:
                capital = position * current_price
                position = 0.0
                print("Executing SELL trade...")
            else:
                if signal == "HOLD":
                    print("HOLD - Doing nothing.")
            
            print("Waiting for next cycle...")
            time.sleep(10)
            
        except Exception as e:
            print(f"Error in iteration {i+1}: {str(e)}")
            print("Skipping this cycle...")
            time.sleep(10)
    
    # Close any open position at last known price
    if position > 0:
        capital = position * last_current_price
        print("\nClosing final open position at last price...")
        print(f"Final SELL: {position:.0f} shares at ${last_current_price:.2f}")
        position = 0.0
    
    profit = capital - 10000.0
    result = {
        "final_capital": round(capital, 2),
        "profit": round(profit, 2)
    }
    
    print("\n" + "="*60)
    print("LIVE TRADING SIMULATION COMPLETE")
    print(f"Final Capital: ${capital:.2f}")
    print(f"Total Profit/Loss: ${profit:.2f} ({(profit/10000)*100:.1f}%)")
    
    return result

if __name__ == "__main__":
    result = simulate_live_trading()
    print("\nFinal Result:", result)

