__version__ = "1.8.5.26.dev5"

# NOTICE: only change the last number for our customized shapely packages


# suppress annoying ShapelyDeprecationWarning
import warnings

warnings.filterwarnings(action='ignore', category=FutureWarning)
