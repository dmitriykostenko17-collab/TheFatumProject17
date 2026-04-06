import sys
import os
sys.path.append(os.getcwd())

from rngs.qrng_provider import QRNGProvider

def test_qrng():
    try:
        print("Testing QRNG Provider...")
        provider = QRNGProvider()
        # Test 16 bytes
        data = provider.get_binary_data(16)
        print(f"Success! Received hex: {data.hex()}")
        
        # Test integer generation
        val = provider.next(100)
        print(f"Random number [0-99]: {val}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_qrng()
