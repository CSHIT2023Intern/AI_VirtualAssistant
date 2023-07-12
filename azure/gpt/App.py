from flask import Flask, request, jsonify, render_template
import openai

app = Flask(__name__, static_url_path='/static')

openai.api_type = "azure"
openai.api_base = "https://cshitinternopenai.openai.azure.com/"
openai.api_version = "2023-03-15-preview"

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
            response = openai.ChatCompletion.create(
                engine="CSHITIntern",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return jsonify(response['choices'][0]['message']['content'].strip())
        except openai.error.AuthenticationError:
            return jsonify({'error': 'Invalid API key.'})
    else:
        return jsonify({'error': 'Invalid request. Missing "prompt" parameter.'})

if __name__ == '__main__':
    app.run(debug=True)
