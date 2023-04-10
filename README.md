# CS839 Intergrate Project - Chefmate

## Google Cloud Database
### How to use
* Rewrite `secret-template.json` to `secret.json` with proper values
* Set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to the path of the JSON file that contains your service account key. This variable only applies to your current shell session, so if you open a new session, set the variable again.
  * For macOS and Linux: `export GOOGLE_APPLICATION_CREDENTIALS="your-path-to-this-credential/service-account-file-name.json"`
  * For Windows command prompt: `set GOOGLE_APPLICATION_CREDENTIALS=your-path-to-this-credential/service-account-file-name.json`

## Bugs
1. aiohttp.client_exceptions.ClientConnectorCertificateError: Cannot connect to host sqladmin.googleapis.com:443 ssl:True [SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:992)')]

Solution: Please update the Python-certificate to latest version corresponding to which version of python you use, eg. If you use python 3.9, run the command in terminal as below:
open /Applications/Python\ 3.9/Install\ Certificates.command