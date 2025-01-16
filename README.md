
# GitHub metadata importer 

This tool imports GitHub metadata from repositories into the Software Observatory database. It identifies the GitHub repositories listed in the database entries, retrieves metadata for each repository using the [GitHub metadata API](https://github.com/inab/github-metadata-api), and stores the retrieved metadata back in the database.

If you are looking for a tool to import metadata from a GitHub repository, you can directly use the [GitHub metadata importer](https://github.com/inab/github-metadata-api) tool. More specifically, use [this endpoint](https://observatory.openebench.bsc.es/github-metadata-api/api-docs/#/Metadata%20Extractor%20for%20FAIRsoft/post_metadata_user).

## Installation

The tool is written in Python 3.12 and requires the packages in the file `requirements.txt`. You can install the required packages using the following command:

```bash
pip install -r requirements.txt
```

## Configuration
The tool requires the following environment variables to be set:

- `MONGO_HOST`: the hostname of the MongoDB server
- `MONGO_PORT`: the port of the MongoDB server
- `MONGO_USER`: the username for the MongoDB server
- `MONGO_PWD`: the password for the MongoDB server
- `MONGO_AUTH_SRC`: the authentication source for the MongoDB server
- `MONGO_DB`: the name of the MongoDB database
- `ALAMBIQUE`: the name of the Alambique database.The metadata gathered wilb be stored in this database.
- `PRETOOLS`: the name of the Pretools database. The tool will read the list of repositories from this database.
- `GITHUB_TOKEN`: the user GitHub token to use for the GitHub metadata API. The token must have `read:packages` enabled.

Put these environment variables in a `.env` file in the root directory of the project.

## Usage

To run the tool, execute the following command:

```bash
python3 main.py
```