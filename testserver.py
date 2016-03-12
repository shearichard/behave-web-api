from bottle import Bottle, run, request

app = Bottle()


@app.route('/requests/echo', method='ANY')
def echo():
    try:
        body = request.body.read().encode('utf-8')
    except:
        body = None

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
