"""Reuse the recorded literal-function parser and isolated Packaging test harness."""
import sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'gemma-feedback-v4'))
import evaluate_api as harness
harness.OUT=H
if __name__=='__main__':{'preflight':harness.preflight,'evaluate':harness.evaluate}[sys.argv[1]]()
