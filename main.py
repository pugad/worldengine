#!/usr/bin/env python3
'''
This script serves as the server app that interacts with the Worldengine CLI
It generates a map using the CLI, then obtains the saved map from /tmp and sends it back
'''

import flask
from flask import jsonify, request
import numpy as np
from PIL import Image
import json
import base64
import os
import subprocess
from subprocess import Popen, PIPE
import traceback


app = flask.Flask(__name__)

app.logger.setLevel('DEBUG')


@app.route("/")
def hello():
    return "<p>Worldengine is running</p>"

@app.route('/generate', methods=['POST'])
def generate_world():
    app.logger.info('request received, params: {}'.format(request.args.to_dict()))
    args = request.args.to_dict()

    worldengine_args = ['python','worldengine']
    if 'width' in args and 'height' in args:
        worldengine_args.append('--width={}'.format(args['width']))
        worldengine_args.append('--height={}'.format(args['height']))
    else:
        return jsonify(success=False, logs='width and/or height values are incomplete')
    
    if 'seed' in args:
        worldengine_args.append('--seed={}'.format(args['seed']))

    if 'name' in args:
        name = args['name'].split()[0]
    else:
        name = 'map_' + str(np.random.randint(0,np.iinfo(np.uint16).max))

    worldengine_args.append('--worldname={}'.format(name))
    worldengine_args.append('-o /tmp/{}'.format(name))
    worldengine_args.append('--stream-output')




    process = Popen(worldengine_args,stderr=PIPE, stdout=PIPE)
    stdout, stderr = process.communicate()    
    worldengine_request_logs = stdout
    if stderr:
        app.logger.warning('WORLDENGINE ERROR:\n'+stderr)


    stream_output = json.loads(worldengine_request_logs.split('\n')[-4])

    # save the files in tmp
    output_dir = os.path.join('.','tmp',name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


    content = {}
    for key in stream_output:
        encoded = stream_output[key].encode('utf-8')
        bdec = base64.b64decode(encoded)
        
        with open(os.path.join(output_dir,key), 'wb+') as f:
            f.write(bdec)

        if '.png' in key:

            with open(os.path.join(output_dir,key), 'rb') as f:
                biome_img = Image.open(f)
                content[key.split('.png')[0]] = np.array(biome_img).tolist()

    
    return jsonify(
        success=True,
        content=content
    )

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port='8080'
    )