# latex-google-translate
Translate a txt/LaTeX file via Google Cloud Translation API

A Python command-line tool for sending textual and LaTeX files to Google Cloud
Translation API. Splits the files into chunks to abide by the codepoints limit
set for synchronous calls, and then merges them back into a single file. For
LaTeX inputs, the tool replaces the LaTeX commands before sending the file and
then restores them in the received translation. This can break occasionally, so
fixing the LaTeX translation manually might be needed in some case.

Uses [Google Cloud Translation](https://googleapis.dev/python/translation/latest/index.html) client, also available from [`conda-forge`](https://anaconda.org/conda-forge/google-cloud-translate).

Requires a Google Cloud Platform (GCP) account with Cloud Translation service
activated. The GCP project ID needs to be supplied as a command line argument.

To manage GCP authentication, use [`gcloud`](https://cloud.google.com/sdk/gcloud).

## Usage

    usage: latex-google-translate.py [-h] [--project-id PROJECT_ID] [--input-language INPUT_LANGUAGE] [--output-language OUTPUT_LANGUAGE] [--chunk-size CHUNK_SIZE] [--latex] [--test] [--save-input-output] input_file output_file

    Translate a txt/LaTeX file via Google Cloud Translation API

    positional arguments:
      input_file            Text file to be translated, UTF-8 encoded
      output_file           File to write the translation to

    optional arguments:
      -h, --help            show this help message and exit
      --project-id PROJECT_ID
                            Google Cloud Platform project ID
      --input-language INPUT_LANGUAGE
                            BCP-47 source language code
      --output-language OUTPUT_LANGUAGE
                            BCP-47 target language code
      --chunk-size CHUNK_SIZE
                            Maximum size of a text chunk in codepoints to be sent to Google Translation Service API (default=5000)
      --latex               Input is LaTeX
      --test                Don't send to Google Translation Service API
      --save-input-output   Save translation input and output texts into files

