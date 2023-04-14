from flask import Flask, request, jsonify
import requests
import json
import time

app = Flask(__name__)

def fetch_numbers(url):
    try:
        response = requests.get(url, timeout=0.5)
        if response.status_code == 200:
            data = json.loads(response.text)
            if "numbers" in data:
                return data["numbers"]
    except requests.exceptions.Timeout:
        pass
    except:
        pass
    return []

@app.route('/numbers')
def numbers():
    urls = request.args.getlist('url')
    all_numbers = []
    for url in urls:
        numbers = fetch_numbers(url)
        all_numbers += numbers

    all_numbers = list(set(all_numbers))
    all_numbers.sort()

    return jsonify({
        "numbers": all_numbers
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000)
