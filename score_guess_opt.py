import ctypes
score_guess_opt = ctypes.CDLL("./score_guess_opt.so")

print(score_guess_opt.score_guess(b"54/9=6", b"4*7=28"))
