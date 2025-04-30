import argparse
import hashlib
from pyhanko.pdf_utils.reader import PdfFileReader # type: ignore

def print_sign_metadata(pdf_path):
    with open(pdf_path, 'rb') as f:
        reader = PdfFileReader(f)
        sigs = reader.embedded_signatures

        if not sigs:
            print("No signs found.")
            return

        for i, sig_obj in enumerate(sigs, start=1):
            try:
                # Retrieve the signer name
                signer_name = sig_obj.signer_cert.subject.native.get("common_name", "(Name not found)")

                # Try to get sign date and time, if available
                if sig_obj.self_reported_timestamp:
                    signing_time = sig_obj.self_reported_timestamp.isoformat()
                else:
                    signing_time = "(date is not available)"

                # Generate hash of the signed data
                signed_data = bytes(sig_obj.signed_data)
                signed_hash = hashlib.sha256(signed_data).hexdigest()

                print(f"Sign #{i}:")
                print(f"  Signer Name: {signer_name}")
                print(f"  Sign Date/Time: {signing_time}")
                print(f"  Hash (SHA-256): {signed_hash}\n")

            except Exception as e:
                print(f"Error processing sign #{i}: {e}")

def parse_args():
    parser = argparse.ArgumentParser('PDF PAdES sign checker')

    parser.add_argument('-i', '--input_file', required=True, help='File to verify')

    params = parser.parse_args()

    return params

def main() -> None:
    params = parse_args()
    print_sign_metadata(params.input_file)

    quit()
main()
