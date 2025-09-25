# (c) Fasihi-Rad
# (c) Fasihi-Rad
# Backward compatibility wrapper for old configuration system
# New code should use Adarsh.config instead

import warnings
from .config import config, Var as NewVar

# Issue deprecation warning
warnings.warn(
    "Adarsh.vars is deprecated. Use Adarsh.config instead.",
    DeprecationWarning,
    stacklevel=2
)

# For backward compatibility, expose the old interface
Var = NewVar