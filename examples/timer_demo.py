"""
Timer demo — prints elapsed time and ratio to console.
"""
import pygame

pygame.init()

from pygkit.utils import Timer

t = Timer(2000)
print("Timer set for 2000ms")
print(f"  elapsed={t.elapsed():>4d}ms  ratio={t.ratio():.2f}  reached={t.reached()}")

pygame.time.delay(1000)
print(f"\nAfter 1000ms delay:")
print(f"  elapsed={t.elapsed():>4d}ms  ratio={t.ratio():.2f}  reached={t.reached()}")

pygame.time.delay(1000)
print(f"\nAfter another 1000ms:")
print(f"  elapsed={t.elapsed():>4d}ms  ratio={t.ratio():.2f}  reached={t.reached()}")

print(f"\nTimer reached: {t.reached()}")
t.reset()
print(f"Reset. elapsed={t.elapsed()}ms")

print("\nStale init example:")
t2 = Timer(2000, stale_init=True)
print(f"  elapsed={t2.elapsed():>4d}ms  ratio={t2.ratio():.2f}  reached={t2.reached()}")

pygame.quit()
