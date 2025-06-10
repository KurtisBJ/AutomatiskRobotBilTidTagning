from machine import ADC
import time
import hivemq


class PicoWallfollow:
    def __init__(self):
        self.solcelle = ADC(26)
        self.program_start = time.ticks_ms()
        self.last_lap_time = self.program_start
        self.runde = 0
        self.måler_tid = False

    def read_tid(self):
        lys = self.solcelle.read_u16()
        volt = (lys / 65535) * 3.3
        now = time.ticks_ms()
        
        if volt > 1 and not self.måler_tid:
            self.måler_tid = True
            print("Klar til ny omgang...")
            

        elif volt < 0.8 and self.måler_tid:
            self.runde += 1
            lap_time = time.ticks_diff(now, self.last_lap_time) / 1000  
            
            self.last_lap_time = now
            self.måler_tid = False
            print(f"Lab {self.runde}: {lap_time:.2f} sekunder")
            

            return f"{lap_time:.2f}"

        return None
