/**
 * 请求解析器 - 支持 cURL 和 Fetch 格式
 */

export function detectFormat(input) {
  const trimmed = input.trim()
  if (trimmed.startsWith('curl ') || trimmed.startsWith('curl\n')) return 'curl'
  if (trimmed.startsWith('fetch(') || trimmed.startsWith('fetch (')) return 'fetch'
  return 'unknown'
}

/**
 * 通用 kv 解析：支持 key: 'value' / key: "value" / key: value
 */
function parseKeyValue(line) {
  const colonIdx = line.indexOf(':')
  if (colonIdx === -1) return null
  let key = line.substring(0, colonIdx).trim()
  let value = line.substring(colonIdx + 1).trim()
  // 去掉 key 首尾引号
  if ((key.startsWith('"') && key.endsWith('"')) ||
      (key.startsWith("'") && key.endsWith("'"))) {
    key = key.slice(1, -1)
  }
  // 去掉 value 首尾引号
  if ((value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))) {
    value = value.slice(1, -1)
  }
  // 处理值末尾有引号但前面有空格的情况，如 "Bearer xxx"
  if ((value.endsWith('"') || value.endsWith("'")) && !value.startsWith('"') && !value.startsWith("'")) {
    value = value.slice(0, -1)
  }
  value = value.trim()
  if (!key) return null
  return { key, value }
}

/**
 * 解析 cURL 命令
 */
export function parseCurl(curlCommand) {
  const result = { method: 'GET', url: '', headers: {}, params: {}, body: null }
  const cleaned = curlCommand.replace(/\\\n/g, ' ').trim()

  const urlMatch = cleaned.match(/(https?:\/\/[^\s'"]+)/)
  if (urlMatch) result.url = urlMatch[1]

  const methodMatch = cleaned.match(/(?:-X|--request)\s+(\w+)/i)
  if (methodMatch) result.method = methodMatch[1].toUpperCase()

  const headerRegex = /-H\s+['"]([^:]+):\s*([^'"]*)['"]/gi
  let headerMatch
  while ((headerMatch = headerRegex.exec(cleaned)) !== null) {
    const key = (headerMatch[1] || '').trim()
    const value = (headerMatch[2] || '').trim()
    if (key) result.headers[key] = value
  }

  const bodyMatch = cleaned.match(/(?:-d|--data|--data-raw|--data-binary)\s+['"]([^'"]*)['"]/i)
  if (bodyMatch) {
    result.body = bodyMatch[1]
    if (result.method === 'GET') result.method = 'POST'
  }

  if (result.url && result.url.includes('?')) {
    const [baseUrl, queryString] = result.url.split('?')
    result.url = baseUrl
    queryString.split('&').forEach(pair => {
      const [k, ...vParts] = pair.split('=')
      if (k) result.params[decodeURIComponent(k)] = decodeURIComponent(vParts.join('=') || '')
    })
  }

  return result
}

/**
 * 解析 Fetch 代码 - 简化版：先提取 headers 块字符串，再逐行解析
 */
export function parseFetch(fetchCode) {
  const result = { method: 'GET', url: '', headers: {}, params: {}, body: null }
  const input = fetchCode.trim()

  // 1. 提取 URL
  const urlMatch = input.match(/fetch\s*\(\s*['"]([^'"]+)['"]/)
  if (urlMatch) result.url = urlMatch[1]

  // 2. 提取 method（支持单引号/双引号）
  const methodMatch = input.match(/method:\s*['"](\w+)['"]/i)
  if (methodMatch) result.method = methodMatch[1].toUpperCase()

  // 3. 提取 body
  const bodyMatch = input.match(/body:\s*JSON\.stringify\(([^)]+)\)/) ||
                    input.match(/body:\s*['"]([^'"]*)['"]/) ||
                    input.match(/body:\s*(\w+)/)
  if (bodyMatch) {
    const bodyVal = (bodyMatch[1] || '').trim()
    if (bodyVal && bodyVal !== 'null' && bodyVal !== 'undefined') {
      result.body = bodyVal.replace(/^["']|["']$/g, '')
    }
  }

  // 4. 提取 headers 块内容
  // 找 "headers": { ... } 块
  const headersMatch = input.match(/"headers":\s*\{([\s\S]*?)\}(?:\s*,\s*|\s*\})/i)
  if (headersMatch) {
    const headersBlock = headersMatch[1]
    // 逐行解析
    const lines = headersBlock.split('\n')
    for (const rawLine of lines) {
      const line = rawLine.trim().replace(/,\s*$/, '')
      if (!line) continue
      const kv = parseKeyValue(line)
      if (kv) {
        result.headers[kv.key] = kv.value
      }
    }
  }

  // 5. 从 URL 中分离 query params
  if (result.url && result.url.includes('?')) {
    const [baseUrl, queryString] = result.url.split('?')
    result.url = baseUrl
    queryString.split('&').forEach(pair => {
      const [k, ...vParts] = pair.split('=')
      if (k) result.params[decodeURIComponent(k)] = decodeURIComponent(vParts.join('=') || '')
    })
  }

  return result
}

/**
 * 主解析函数
 */
export function parseRequest(input) {
  if (!input || !input.trim()) {
    throw new Error('输入不能为空')
  }
  const format = detectFormat(input)
  switch (format) {
    case 'curl': return parseCurl(input)
    case 'fetch': return parseFetch(input)
    default:
      throw new Error(`不支持的格式 "${format}"，请输入 cURL 或 Fetch 格式的命令`)
  }
}
