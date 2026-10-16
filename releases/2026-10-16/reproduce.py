"""Replay the 102 frozen ECA-6 variants in a new local directory, without model inference."""
import argparse,sys,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);a=p.parse_args()
    if a.destination.exists():p.error('Destination must not already exist')
    source=ROOT/'outputs/gemma-importguard/reproduce_contract_resource.py';spec=importlib.util.spec_from_file_location('eca_reproduction',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.run(a.destination.resolve())
if __name__=='__main__':main()
