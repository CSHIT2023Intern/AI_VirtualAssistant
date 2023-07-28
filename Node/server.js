const express = require('express');
const bodyParser = require('body-parser');
const sdk = require("microsoft-cognitiveservices-speech-sdk");

const app = express();
app.use(bodyParser.json());
app.use(express.static('public'));  // 這應該放在路由定義之前

app.post('/synthesize', async (req, res) => {
    const text = req.body.text;
    const timestamp = Date.now();
    const audioFile = `public/audio/yourfile-${timestamp}.wav`;

    // Replace with your own subscription key and region identifier
    let speechConfig = sdk.SpeechConfig.fromSubscription("c9d3e6d440214af3bc175d4c31809a44", "eastasia");
    speechConfig.speechSynthesisLanguage = "zh-CN";
    let audioConfig = sdk.AudioConfig.fromAudioFileOutput(audioFile);

    let synthesizer = new sdk.SpeechSynthesizer(speechConfig, audioConfig);

    synthesizer.speakTextAsync(
        text,
        result => {
            if (result) {
                res.send({ audioFile: `/audio/yourfile-${timestamp}.wav` });
            }
            synthesizer.close();
        },
        error => {
            console.log(error);
            synthesizer.close();
        }
    );
});

app.listen(3000, () => console.log('Server is running on port 3000'));
