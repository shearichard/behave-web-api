import json
from bottle import Bottle, run, request

app = Bottle()


@app.route('/requests/echo', method='ANY')
def echo():
    try:
        body = request.body.read().decode('utf-8')
    except:
        body = None

    print(request.headers['Content-Type'])

    if request.headers['Content-Type'] == 'application/json':
        try:
            body = json.loads(body)
        except:
            pass

    result = {
        'method': request.method,
        'headers': dict(request.headers),
        'body': body,
        'files': [
            {'key': key, 'name': request.files[key].raw_filename}
            for key in request.files
        ]
    }

    return result


run(app, host='localhost', port='5000')
