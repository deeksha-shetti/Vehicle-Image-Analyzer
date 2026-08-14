const cloudinary = require('cloudinary').v2;

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
  secure: true
});

const keyPrefix = process.env.CLOUDINARY_API_KEY ? process.env.CLOUDINARY_API_KEY.slice(0, 4) + '...' : 'N/A';
const keyLen = process.env.CLOUDINARY_API_KEY ? process.env.CLOUDINARY_API_KEY.length : 0;
const secretPresent = Boolean(process.env.CLOUDINARY_API_SECRET);
const secretLen = process.env.CLOUDINARY_API_SECRET ? process.env.CLOUDINARY_API_SECRET.length : 0;

console.log(`[Cloudinary Config] Cloud Name: '${process.env.CLOUDINARY_CLOUD_NAME}', API Key: ${keyPrefix} (len: ${keyLen}), API Secret Present: ${secretPresent} (len: ${secretLen})`);

module.exports = cloudinary;
