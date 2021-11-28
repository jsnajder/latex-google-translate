""" Translate a txt/LaTeX file via Google Cloud Translation API
    
    Sep 2021, Jan Šnajder

    LaTeX to txt conversion adapted from Arnaud Bodin:
    https://github.com/arnbod/latex-to-text
""" 

from google.cloud import translate
import argparse
import re

def parse_args():
    parser = argparse.ArgumentParser(
        description="Translate a txt/LaTeX file via "
                    "Google Cloud Translation API")
    parser.add_argument("input_file", 
        help="Text file to be translated, UTF-8 encoded")
    parser.add_argument("output_file", 
        help="File to write the translation to")
    parser.add_argument("--project-id", 
        help="Google Cloud Platform project ID")
    parser.add_argument("--input-language", 
        help="BCP-47 source language code")
    parser.add_argument("--output-language", 
        help="BCP-47 target language code")
    parser.add_argument('--chunk-size', 
        default=5000, type=int, 
        help="Maximum size of a text chunk in codepoints to be sent "
             "to Google Translation Service API (default=5000)")
    parser.add_argument("--latex", action='store_true', 
        help="Input is LaTeX")
    parser.add_argument("--test", action='store_true', 
        help="Don't send to Google Translation Service API")
    parser.add_argument("--save-input-output", action='store_true', 
        help="Save translation input and output texts into files")
    args=parser.parse_args()
    return args

def translate_text(input_text, project_id, input_language, output_language):
    """Translating Text."""

    client = translate.TranslationServiceClient()
    location = 'global'
    parent = f"projects/{project_id}/locations/{location}"

    response = client.translate_text(
        request={
            'parent': parent,
            'contents': [input_text],
            'mime_type': 'text/plain',
            'source_language_code': input_language,
            'target_language_code': output_language
        }
    )
    return response.translations[0].translated_text

list_env_discard = [
        'equation', 'equation*', 'align', 'align*', 'alignat', 'alignat*', 
        'lstlisting', 'eqnarray', 'comment'
        ]
list_cmd_arg_discard = [
        'usepackage', 'documentclass', 'begin', 'end', 'includegraphics', 
        'label', 'ref', 'cite', 'citep', 'citet', 'vspace', 'hspace', 
        'vspace*', 'hspace*', 'bibliography', 'url', 'href'
        ]

tag = '@'
count = 0
dictionary = {}

def func_repl(m):
    global count
    dictionary[count] = m.group(0)
    tag_str = tag+str(count)+tag
    count += 1   
    return tag_str

def chunk_text(text, chunk_size):
    chunks = []
    chunk = ""
    paragraphs = text.split("\n\n")
    for i, p in enumerate(paragraphs):
        if i < len(paragraphs) - 1:
            p += "\n\n"
        if len(p) > chunk_size:
            raise Exception(
                    f"Cannot chunk input because paragraph {i+1} has "
                    f"{len(p)} codepoints, which is longer than "
                    f"chunk size of {chunk_size}")
        l = len(chunk) + len(p)
        if l <= chunk_size:
            chunk += p
        else:
            chunks.append(chunk)
            chunk = p
    chunks.append(chunk)
    return chunks

def tex_to_txt(input_tex):
    text_new = input_tex
 
    # Step 1: Replace \begin{env} and \end{env} and its contents
    for env in list_env_discard:
        str_env = (r'\\begin\{' + re.escape(env) 
                   + r'\}(.+?)\\end\{' + re.escape(env) + r'\}')
        text_new = re.sub(
                str_env, func_repl, text_new, flags=re.MULTILINE|re.DOTALL)
    
    # Step 2: Replacement of \\ and \\[..]
    text_new = re.sub(r'\\\\(\[(.+?)\])?', func_repl, text_new, 
                      flags=re.MULTILINE|re.DOTALL)

    # Step 3: Replacement of maths ###
    # $$ ... $$
    text_new = re.sub(r'\$\$(.+?)\$\$', func_repl, text_new, 
                      flags=re.MULTILINE|re.DOTALL)
    # \[ ... \]
    text_new = re.sub(r'\\\[(.+?)\\\]', func_repl, text_new, 
                      flags=re.MULTILINE|re.DOTALL)
    # $ ... $
    text_new = re.sub(r'\$(.+?)\$', func_repl, text_new, 
                      flags=re.MULTILINE|re.DOTALL)
    # \( ... \)
    text_new = re.sub(r'\\\((.+?)\\\)', func_repl, text_new, 
                      flags=re.MULTILINE|re.DOTALL)
    
    # Step 4: Replace begin/end environment commands, but not the content
    text_new = re.sub(r'\\begin\{(.+?)\}', func_repl, text_new, 
                      flags=re.MULTILINE|re.DOTALL)
    text_new = re.sub(r'\\end\{(.+?)\}', func_repl, text_new, 
                      flags=re.MULTILINE|re.DOTALL)

    # Step 5: Replace LaTeX commands alongside their argument
    for cmd in list_cmd_arg_discard:
        # Without opt arg, ex. \cmd{arg}
        str_env = r'\\' + re.escape(cmd) + r'\{(.+?)\}'
        text_new = re.sub(str_env, func_repl, text_new, 
                          flags=re.MULTILINE|re.DOTALL)
        # With opt arg, ex. \cmd[opt]{arg}
        str_env = r'\\' + re.escape(cmd) + r'\[(.*?)\]\{(.+?)\}'
        text_new = re.sub(str_env, func_repl, text_new, 
                          flags=re.MULTILINE|re.DOTALL)

    # Step 6: Replace remaining LaTeX commands, but not their arguments
    text_new = re.sub(r'\\[a-zA-Z]+\*?', func_repl, text_new, 
                      flags=re.MULTILINE|re.DOTALL)
    
    # Step 7: Replace non-empty line comments
    text_new = re.sub(r'[^\\](%.+?)$', func_repl, text_new, 
                      flags=re.MULTILINE)

    return text_new, len(dictionary)

def txt_to_tex(input_txt, trim_whitespaces=True):
    """ Converts a TXT with code labels back to LaTeX, using the dictionary 
        of code replacements.
    """
    text_new = input_txt
    text_old = ""
    while text_new != text_old:
        text_old = text_new
        for i, val in dictionary.items():
            val = val.replace('\\','\\\\')
            if trim_whitespaces:
                # NB: GCS Translation API inserts 3 whitespaces around codes 
                # (the third one sometimes omitted, but if followed by "{", 
                # it should be trimmed)
                tag_str1 = tag+' ?'+str(i)+' ?'+tag+' \{'
                text_new = re.sub(tag_str1, val+'{', text_new, 
                                  flags=re.MULTILINE|re.DOTALL)
                tag_str2 = tag+' ?'+str(i)+' ?'+tag
                text_new = re.sub(tag_str2, val, text_new, 
                                  flags=re.MULTILINE|re.DOTALL)
            else: 
                tag_str = tag+str(i)+tag
                text_new = re.sub(tag_str, val, text_new, 
                                  flags=re.MULTILINE|re.DOTALL)
    return text_new

def main():
    args = parse_args()
    with open(args.input_file, 'r', encoding='utf-8') as file:
        print(f"Opening file {args.input_file}.")
        input_string = file.read()
    if args.latex:
        print("LaTeX file indicated as input. Converting to txt.")
        input_text, rep = tex_to_txt(input_string)
        print(f"{rep} replacements made.")
    else:
        input_text = input_string
    if args.save_input_output:
        with open(args.input_file + ".input", "w", encoding='utf-8') as fi:
            fi.write(input_text)
    file_length = len(input_text)
    print(f'The file has {file_length} codepoints.')
    if file_length > args.chunk_size:
        print(f"Input is above {args.chunk_size} codepoints. Batch processing "
               "is recommended, but will proceed with a synchronous call on "
               "chunked input.")
    translated_text = ""
    chunks = chunk_text(input_text, args.chunk_size)
    for i, input_chunk in enumerate(chunks):
        print(f"Text chunk {i+1}/{len(chunks)} of "
              f"{len(input_chunk)} codepoints")
        if args.test:
            translated_chunk = input_chunk
        else:
            print(f"Sending to Google Cloud Translation API for translation "
                  f"from {args.input_language} to {args.output_language} with "
                  f"project_id={args.project_id}")
            translated_chunk = translate_text(
                    input_chunk, args.project_id, 
                    args.input_language, args.output_language)
        translated_text += translated_chunk
    if args.save_input_output:
        with open(args.output_file + ".output", "w", encoding='utf-8') as fo:
            fo.write(translated_text)
    if args.latex:
        print("Converting txt back to LaTeX.")
        translated_text = txt_to_tex(translated_text, 
                                     trim_whitespaces=not(args.test))
    with open(args.output_file, 'w', encoding='utf-8') as file:
        print(f"Writting to {args.output_file}")
        file.write(translated_text)

if __name__ == '__main__':
    main()

