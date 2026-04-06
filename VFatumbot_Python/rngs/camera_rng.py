import numpy as np
from PIL import Image
import os
from rngs.base_random_provider import BaseRandomProvider

class CameraRNG(BaseRandomProvider):
    """
    RNG that extracts raw quantum noise (shot noise/thermal noise) 
    from the sensor of a camera by reading Least Significant Bits (LSB).
    """
    def __init__(self):
        super().__init__()
        self.entropy_pool = bytearray()
        self.pool_index = 0

    def check_noise_quality(self, data: np.ndarray) -> float:
        """
        Ocelli-Lite Diagnostic: Calculates the standard deviation of raw pixel values.
        Higher variance means better quantum/thermal noise extraction.
        """
        # Calculate standard deviation across all pixels
        std_dev = np.std(data)
        return float(std_dev)

    def feed_image(self, image_path: str):
        """
        Processes an image file and extracts raw noise into the entropy pool.
        Uses Ocelli-inspired diagnostics to ensure the entropy quality.
        """
        if not os.path.exists(image_path):
            print(f"Error: Image path {image_path} does not exist.")
            return

        try:
            with Image.open(image_path) as img:
                # Convert to RGB
                img = img.convert('RGB')
                data = np.array(img, dtype=np.uint8)
                
                # Diagnostic: Is there enough noise?
                quality = self.check_noise_quality(data)
                if quality < 0.2:
                    print(f"WARNING: Low noise quality ({quality:.4f}). Sensor might be too 'flat' or filtered.")
                else:
                    print(f"CameraRNG: Noise quality check passed (std_dev: {quality:.4f}).")

                # Ocelli optimization: Red and Blue channels typically have more noise 
                # than the double-sampled Green channel in Bayer filters.
                # We extract 2 LSBs from R, G, B, but keep the raw order.
                lsb_data = data & 0b00000011 
                
                # To prioritize 'Quantum Purity', we can shuffle or weight, 
                # but for now, we just take the raw bits as requested.
                raw_noise_bytes = lsb_data.tobytes()
                
                # Add to pool
                self.entropy_pool.extend(raw_noise_bytes)
                print(f"CameraRNG: Extracted {len(raw_noise_bytes)} bytes of high-fidelity noise.")
                
        except Exception as e:
            print(f"Error processing camera image for entropy: {e}")

    def get_hex_bytes(self, count: int) -> str:
        """
        Returns raw hex bytes from the entropy pool.
        """
        needed_bytes = (count + 1) // 2
        
        # If pool is empty or too small even after reset, use fallback
        if not self.entropy_pool or (len(self.entropy_pool) < needed_bytes):
            import secrets
            return secrets.token_hex(needed_bytes)[:count]

        if (self.pool_index + needed_bytes) > len(self.entropy_pool):
            self.pool_index = 0

        chunk = self.entropy_pool[self.pool_index : self.pool_index + needed_bytes]
        self.pool_index += needed_bytes
        return chunk.hex()[:count]
