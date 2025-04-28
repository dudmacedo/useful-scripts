import argparse
import logging


def initialize():
    parser = argparse.ArgumentParser('PDF Batch Processor')

    parser.add_argument('-i', '--input_dir', default='in', help='Directory with input files')
    parser.add_argument('-o', '--output_dir', default='out', help='Directory to output files')
    parser.add_argument('-t', '--ocr', type=bool, default='False', action='store_true', help='Do OCR in the output file')

    params = parser.parse_args()



    return params

def check_requirements() -> None:
    logger.info("Checking requirements...")

def main() -> None:
    params = initialize()
    check_requirements()

    quit()
main()