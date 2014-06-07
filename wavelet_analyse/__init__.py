try:
    from cuda_backend import *

except Exception:
    from numpy_backend import *
