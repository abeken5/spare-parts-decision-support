def test_environment_smoke():
    import numpy as np
    import pandas as pd
    import scipy
    assert np.__version__ is not None
    assert pd.__version__ is not None
