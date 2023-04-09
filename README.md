# CS839 Intergrate Project - Chefmate

## Google Cloud Database
### How to use
* Rewrite `secret-template.json` to `secret.json` with proper values
* Set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to the path of the JSON file that contains your service account key. This variable only applies to your current shell session, so if you open a new session, set the variable again.
  * For macOS and Linux: `export GOOGLE_APPLICATION_CREDENTIALS="your-path-to-this-credential/service-account-file-name.json"`
  * For Windows command prompt: `set GOOGLE_APPLICATION_CREDENTIALS=your-path-to-this-credential/service-account-file-name.json`