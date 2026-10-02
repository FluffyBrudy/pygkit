import pygame

from pygkit.utils import Timer

pygame.init()

t = Timer(2.0)
print("Timer set for 2.0s")
print(f"  elapsed={t.elapsed():.2f}s  ratio={t.ratio():.2f}  reached={t.reached()}")

t.update(1.0)
print("\nAfter 1.0s update:")
print(f"  elapsed={t.elapsed():.2f}s  ratio={t.ratio():.2f}  reached={t.reached()}")

t.update(1.0)
print("\nAfter another 1.0s:")
print(f"  elapsed={t.elapsed():.2f}s  ratio={t.ratio():.2f}  reached={t.reached()}")

print(f"\nTimer reached: {t.reached()}")
t.reset()
print(f"Reset. elapsed={t.elapsed():.2f}s")

print("\nStart-finished example:")
t2 = Timer(2.0, start_finished=True)
print(f"  elapsed={t2.elapsed():.2f}s  ratio={t2.ratio():.2f}  reached={t2.reached()}")

print("\nPause example:")
t3 = Timer(1.0)
t3.pause()
t3.update(5.0)
print(f"  paused, after 5.0s update: elapsed={t3.elapsed():.2f}s reached={t3.reached()}")
t3.resume()
t3.update(1.0)
print(f"  resumed, after 1.0s update: elapsed={t3.elapsed():.2f}s reached={t3.reached()}")

pygame.quit()
