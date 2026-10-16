import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
(ROOT/'work').mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'outputs/gemma-importguard'))
sys.path.insert(0,str(ROOT))
