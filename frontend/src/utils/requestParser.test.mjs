import { parseRequest } from './requestParser.js'

const sample = `fetch("http://localhost:3000/api/terminal/history?page=1&page_size=100", {
  "headers": {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "authorization": "Bearer test-token",
    "sec-ch-ua": "\\"Chromium\\";v=\\"148\\", \\"Google Chrome\\";v=\\"148\\", \\"Not/A)Brand\\";v=\\"99\\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\\"Windows\\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin"
  },
  "referrer": "http://localhost:3000/terminal",
  "body": null,
  "method": "GET",
  "mode": "cors",
  "credentials": "include"
});`

const result = parseRequest(sample)
console.log(JSON.stringify(result, null, 2))
