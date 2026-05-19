import axios from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
})

// 请求代理接口
export const proxyApi = {
  // 单次请求
  send: (data) => client.post('/proxy/', data),
  // 批量请求
  batchSend: (data) => client.post('/proxy/batch', data),
}

export default client
