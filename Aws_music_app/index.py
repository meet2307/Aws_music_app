// Backend (Node.js with Express.js)
const express = require('express');
const AWS = require('aws-sdk');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();
const path = require('path');

const app = express();
const port = 3000;

// Configure AWS
AWS.config.update({ region: 'us-east-1' });
const s3 = new AWS.S3();
const dynamoDB = new AWS.DynamoDB.DocumentClient();
const upload = multer();

// Serve static files from Apache root directory
app.use(express.static(path.join(__dirname, 'public')));

// Upload music file to S3
app.post('/upload', upload.single('file'), async (req, res) => {
    const file = req.file;
    const fileKey = `music/${uuidv4()}-${file.originalname}`;

    const params = {
        Bucket: process.env.S3_BUCKET_NAME,
        Key: fileKey,
        Body: file.buffer,
        ContentType: file.mimetype
    };

    try {
        await s3.upload(params).promise();
        await dynamoDB.put({
            TableName: process.env.DYNAMODB_TABLE_NAME,
            Item: {
                id: uuidv4(),
                filename: file.originalname,
                fileKey: fileKey
            }
        }).promise();
        res.json({ message: 'File uploaded successfully', fileKey });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Retrieve music files from DynamoDB
app.get('/songs', async (req, res) => {
    const params = { TableName: process.env.DYNAMODB_TABLE_NAME };
    try {
        const data = await dynamoDB.scan(params).promise();
        res.json(data.Items);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});