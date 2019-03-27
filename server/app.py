from flask import Flask, request, jsonify, send_from_directory
import os
import socket
import sys

app = Flask(__name__, static_folder='../frontend/build')

def exec_parser(doc):
    parsed_doc = ''

    read_doc, write_doc = os.pipe() 
    read_parse, write_parse = os.pipe()
    sys.stderr.write('{}\n'.format(doc))

    pid = os.fork()

    if pid == 0:
        # Child Process
        os.close(write_doc)
        os.close(read_parse)
        os.dup2(read_doc, 0)
        os.dup2(write_parse, 1)
        os.close(read_doc)
        os.close(write_parse)
        os.execl('/bin/bash', '-v', '/opt/tensorflow/syntaxnet/syntaxnet/parse.sh')

    else:
        # Parent Process
        os.close(read_doc)
        os.close(write_parse)
        os.write(write_doc, doc)
        os.close(write_doc)
        sys.stderr.write('before waitpid\n')
        os.waitpid(pid, 0)
        sys.stderr.write('finished waitpid\n')

        line = os.read(read_parse, 255)
        parsed_doc += line

        while(line != ''):
            line = os.read(read_parse, 255)
            sys.stderr.write(line)
            parsed_doc += line

        os.close(read_parse)

    return parsed_doc

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    sys.stderr.write(os.path.abspath('frontend/build/' + path))
    if path != "" and os.path.exists('frontend/build/' + path):
        return send_from_directory('../frontend/build', path)
    else:
        sys.stderr.write('Requested file not found, serving index.html')
        return send_from_directory('../frontend/build', 'index.html')


@app.route("/", methods=['POST'])
def parse():
    if request.method == 'POST':
        body = []

        data = request.form
        if 'doc' not in data:
            return jsonify(body=None)

        doc = data.get('doc')
        parsed_doc = exec_parser(doc)
        for line in parsed_doc.splitlines():
            body.append(line.split('\t'))

        return jsonify(body=body)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
