# latex-google-translate
Translate a txt/LaTeX file via Google Cloud Translation API

A command-line tool for sending textual and LaTeX files to Google Cloud
Translation API. Splits the files into chunks to abide by the codepoints limit
set for synchronous calls, and then merges them back into a single file. For
LaTeX inputs, the tool replaces the LaTeX commands before sending the file and
then restores them in the received translation. This can break occasionally, so
fixing the LaTeX translation manually might be needed in some case.

Uses [Google Cloud Translation](https://googleapis.dev/python/translation/latest/index.html) client, also available from [`conda-forge`](https://anaconda.org/conda-forge/google-cloud-translate).

Requires a Google Cloud Platform (GCP) account with Cloud Translation service
activated. The GCP project ID needs to be supplied as a command line argument.

To manage GCP authentication, use the [`gcloud` tool](https://cloud.google.com/sdk/gcloud).
