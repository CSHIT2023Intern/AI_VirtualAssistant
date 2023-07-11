from flask import Flask, request, jsonify, render_template
import openai

app = Flask(__name__, static_url_path='/static')

api_key = None

@app.route('/')
def home():
    return render_template('your_file_name.html')

@app.route('/mac')

def mac():
    return render_template('mac.html')

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    prompt = data.get('prompt')
    api_key = request.headers.get('Authorization') 

    if not api_key:
        return jsonify({'error': 'Invalid request. Missing API key.'})

    if prompt:
        openai.api_key = api_key

        try:
            response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=4000)
            return jsonify(response['choices'][0]['text'].strip())
        except openai.error.AuthenticationError:
            return jsonify({'error': 'Invalid API key.'})
    else:
        return jsonify({'error': 'Invalid request. Missing "prompt" parameter.'})

if __name__ == '__main__':
    app.run(debug=True)