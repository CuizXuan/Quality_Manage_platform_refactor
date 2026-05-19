/**
 * requestParser.js
 * 终端调试台的粘贴解析器：
 * - curl
 * - fetch / window.fetch / await fetch
 * - XMLHttpRequest
 * - 纯 URL
 */

function normalizeInput(str) {
  return (str || '').trim().replace(/\\\r?\n/g, ' ')
}

function stripQuotes(str = '') {
  const value = str.trim()
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'")) ||
    (value.startsWith('`') && value.endsWith('`'))
  ) {
    return value.slice(1, -1)
  }
  return value
}

function decodeEscapedString(str = '') {
  try {
    return JSON.parse(`"${str.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`)
  } catch {
    return str
  }
}

function parseUrlParts(rawUrl = '') {
  const result = { url: rawUrl, query_params: {} }
  try {
    const parsed = new URL(rawUrl)
    result.url = `${parsed.origin}${parsed.pathname}`
    parsed.searchParams.forEach((value, key) => {
      result.query_params[key] = value
    })
  } catch {
    const queryIndex = rawUrl.indexOf('?')
    if (queryIndex > -1) {
      result.url = rawUrl.slice(0, queryIndex)
      const queryString = rawUrl.slice(queryIndex + 1)
      queryString.split('&').forEach((pair) => {
        const [key, value = ''] = pair.split('=')
        if (key) result.query_params[decodeURIComponent(key)] = decodeURIComponent(value)
      })
    }
  }
  return result
}

function splitTopLevelObject(source = '') {
  const pairs = []
  let current = ''
  let depthBrace = 0
  let depthBracket = 0
  let depthParen = 0
  let inSingle = false
  let inDouble = false
  let inTemplate = false
  let escape = false

  for (let i = 0; i < source.length; i++) {
    const char = source[i]
    if (escape) {
      current += char
      escape = false
      continue
    }
    if (char === '\\') {
      current += char
      escape = true
      continue
    }
    if (char === "'" && !inDouble && !inTemplate) inSingle = !inSingle
    if (char === '"' && !inSingle && !inTemplate) inDouble = !inDouble
    if (char === '`' && !inSingle && !inDouble) inTemplate = !inTemplate

    if (!inSingle && !inDouble && !inTemplate) {
      if (char === '{') depthBrace++
      if (char === '}') depthBrace--
      if (char === '[') depthBracket++
      if (char === ']') depthBracket--
      if (char === '(') depthParen++
      if (char === ')') depthParen--
      if (char === ',' && depthBrace === 0 && depthBracket === 0 && depthParen === 0) {
        if (current.trim()) pairs.push(current.trim())
        current = ''
        continue
      }
    }
    current += char
  }

  if (current.trim()) pairs.push(current.trim())
  return pairs
}

function splitKeyValue(pair = '') {
  let inSingle = false
  let inDouble = false
  let inTemplate = false
  let depthBrace = 0
  let depthBracket = 0
  let depthParen = 0
  let escape = false

  for (let i = 0; i < pair.length; i++) {
    const char = pair[i]
    if (escape) {
      escape = false
      continue
    }
    if (char === '\\') {
      escape = true
      continue
    }
    if (char === "'" && !inDouble && !inTemplate) inSingle = !inSingle
    if (char === '"' && !inSingle && !inTemplate) inDouble = !inDouble
    if (char === '`' && !inSingle && !inDouble) inTemplate = !inTemplate

    if (!inSingle && !inDouble && !inTemplate) {
      if (char === '{') depthBrace++
      if (char === '}') depthBrace--
      if (char === '[') depthBracket++
      if (char === ']') depthBracket--
      if (char === '(') depthParen++
      if (char === ')') depthParen--
      if (char === ':' && depthBrace === 0 && depthBracket === 0 && depthParen === 0) {
        return [pair.slice(0, i).trim(), pair.slice(i + 1).trim()]
      }
    }
  }
  return [pair.trim(), '']
}

function parseObjectLiteral(source = '') {
  const objectText = source.trim().replace(/^\{/, '').replace(/\}$/, '')
  const objectResult = {}
  for (const pair of splitTopLevelObject(objectText)) {
    const [rawKey, rawValue] = splitKeyValue(pair)
    if (!rawKey) continue
    const key = stripQuotes(rawKey)
    let value = rawValue
    if (!value) {
      objectResult[key] = ''
      continue
    }
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'")) ||
      (value.startsWith('`') && value.endsWith('`'))
    ) {
      value = stripQuotes(value)
      objectResult[key] = decodeEscapedString(value)
      continue
    }
    if (value === 'true' || value === 'false') {
      objectResult[key] = value
      continue
    }
    objectResult[key] = value
  }
  return objectResult
}

function findMatchingBracket(source, startIndex, openChar, closeChar) {
  let depth = 0
  let inSingle = false
  let inDouble = false
  let inTemplate = false
  let escape = false

  for (let i = startIndex; i < source.length; i++) {
    const char = source[i]
    if (escape) {
      escape = false
      continue
    }
    if (char === '\\') {
      escape = true
      continue
    }
    if (char === "'" && !inDouble && !inTemplate) inSingle = !inSingle
    if (char === '"' && !inSingle && !inTemplate) inDouble = !inDouble
    if (char === '`' && !inSingle && !inDouble) inTemplate = !inTemplate

    if (inSingle || inDouble || inTemplate) continue

    if (char === openChar) depth++
    if (char === closeChar) depth--
    if (depth === 0) return i
  }
  return -1
}

function parseHeadersEntries(source, result) {
  Object.entries(parseObjectLiteral(source)).forEach(([key, value]) => {
    result.headers.push({ key, value: String(value ?? '') })
  })
}

function parseHeadersArrayEntries(source, result) {
  const inner = source.trim().replace(/^\[/, '').replace(/\]$/, '')
  const entries = splitTopLevelObject(inner)
  for (const entry of entries) {
    const cleaned = entry.trim()
    if (!cleaned.startsWith('[')) continue
    const row = cleaned.replace(/^\[/, '').replace(/\]$/, '')
    const [rawKey, rawValue] = splitTopLevelObject(row)
    const key = decodeEscapedString(stripQuotes(rawKey || ''))
    const value = decodeEscapedString(stripQuotes(rawValue || ''))
    if (key) result.headers.push({ key, value })
  }
}

function parseFetchHeaders(code, result) {
  const headersIndex = code.indexOf('headers')
  if (headersIndex < 0) return
  const afterHeaders = code.slice(headersIndex)
  const colonIndex = afterHeaders.indexOf(':')
  if (colonIndex < 0) return
  const valueStart = headersIndex + colonIndex + 1
  const valueSource = code.slice(valueStart).trim()

  if (valueSource.startsWith('{')) {
    const start = code.indexOf('{', valueStart)
    const end = findMatchingBracket(code, start, '{', '}')
    if (end > start) parseHeadersEntries(code.slice(start, end + 1), result)
    return
  }

  if (valueSource.startsWith('new Headers')) {
    const parenStart = code.indexOf('(', valueStart)
    const parenEnd = findMatchingBracket(code, parenStart, '(', ')')
    if (parenStart < 0 || parenEnd < 0) return
    const payload = code.slice(parenStart + 1, parenEnd).trim()
    if (payload.startsWith('{')) {
      parseHeadersEntries(payload, result)
      return
    }
    if (payload.startsWith('[')) {
      parseHeadersArrayEntries(payload, result)
    }
  }
}

function parseFetchBody(code, result) {
  const bodyIndex = code.indexOf('body')
  if (bodyIndex < 0) return
  const afterBody = code.slice(bodyIndex)
  const colonIndex = afterBody.indexOf(':')
  if (colonIndex < 0) return
  const bodySource = afterBody.slice(colonIndex + 1).trim()
  const topLevel = splitTopLevelObject(bodySource)[0] || ''
  const bodyValue = topLevel.replace(/[,\s]+$/, '')

  if (!bodyValue || bodyValue === 'null' || bodyValue === 'undefined') return

  if (
    (bodyValue.startsWith('"') && bodyValue.endsWith('"')) ||
    (bodyValue.startsWith("'") && bodyValue.endsWith("'"))
  ) {
    result.body = decodeEscapedString(stripQuotes(bodyValue))
    try {
      JSON.parse(result.body)
      result.bodyType = 'json'
    } catch {
      result.bodyType = 'raw'
    }
    return
  }

  if (bodyValue.startsWith('JSON.stringify')) {
    const start = bodyValue.indexOf('(')
    const end = findMatchingBracket(bodyValue, start, '(', ')')
    if (start > -1 && end > start) {
      const jsonLiteral = bodyValue.slice(start + 1, end).trim()
      result.body = jsonLiteral
      result.bodyType = 'json'
    }
    return
  }

  if (bodyValue.startsWith('new URLSearchParams')) {
    const start = bodyValue.indexOf('(')
    const end = findMatchingBracket(bodyValue, start, '(', ')')
    if (start > -1 && end > start) {
      const formLiteral = bodyValue.slice(start + 1, end).trim()
      result.body = formLiteral
      result.bodyType = 'form'
    }
    return
  }

  if (bodyValue.startsWith('new FormData')) {
    result.body = bodyValue
    result.bodyType = 'multipart'
    result.warnings.push('FormData 含运行态数据，已保留原表达式')
    return
  }

  result.body = bodyValue
  result.bodyType = 'raw'
  result.warnings.push(`body 含动态内容: ${bodyValue.slice(0, 40)}`)
}

function parseCookieString(cookieStr = '') {
  const cookies = []
  cookieStr.split(';').forEach((pair) => {
    const [key, ...valueParts] = pair.trim().split('=')
    if (key) cookies.push({ key: key.trim(), value: valueParts.join('=').trim() })
  })
  return cookies
}

export function parseCurl(curlCommand) {
  const result = {
    method: 'GET',
    url: '',
    headers: [],
    cookies: [],
    query_params: {},
    body: '',
    bodyType: 'none',
    warnings: [],
  }

  let cmd = normalizeInput(curlCommand).replace(/^curl\s+/, '')
  const tokens = []
  let current = ''
  let inSingle = false
  let inDouble = false
  let escape = false

  for (let i = 0; i < cmd.length; i++) {
    const char = cmd[i]
    if (escape) {
      current += char
      escape = false
      continue
    }
    if (char === '\\') {
      escape = true
      continue
    }
    if (char === "'" && !inDouble) inSingle = !inSingle
    if (char === '"' && !inSingle) inDouble = !inDouble
    if (char === ' ' && !inSingle && !inDouble) {
      if (current) {
        tokens.push(current)
        current = ''
      }
      continue
    }
    current += char
  }
  if (current) tokens.push(current)

  const dataArgs = []
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i]
    const next = tokens[i + 1]
    if (token === '-X' || token === '--request') {
      if (next) {
        result.method = stripQuotes(next).toUpperCase()
        i++
      }
      continue
    }
    if (token === '-H' || token === '--header') {
      if (next) {
        const header = stripQuotes(next)
        const colonIndex = header.indexOf(':')
        if (colonIndex > -1) {
          result.headers.push({
            key: header.slice(0, colonIndex).trim(),
            value: header.slice(colonIndex + 1).trim(),
          })
        }
        i++
      }
      continue
    }
    if (['-d', '--data', '--data-raw', '--data-binary', '--data-urlencode'].includes(token)) {
      if (next) {
        dataArgs.push(stripQuotes(next))
        i++
      }
      continue
    }
    if (token === '-b' || token === '--cookie') {
      if (next) {
        result.cookies = parseCookieString(stripQuotes(next))
        i++
      }
      continue
    }
    if (!token.startsWith('-') && !result.url) {
      const urlParts = parseUrlParts(stripQuotes(token))
      result.url = urlParts.url
      result.query_params = urlParts.query_params
    }
  }

  if (dataArgs.length) {
    result.body = dataArgs.join('&')
    try {
      JSON.parse(result.body)
      result.bodyType = 'json'
    } catch {
      result.bodyType = result.body.includes('=') ? 'form' : 'raw'
    }
    if (result.method === 'GET') result.method = 'POST'
  }

  return result
}

export function parseFetchCode(code) {
  const result = {
    method: 'GET',
    url: '',
    headers: [],
    cookies: [],
    query_params: {},
    body: '',
    bodyType: 'none',
    authType: 'none',
    authToken: '',
    warnings: [],
  }

  const normalized = normalizeInput(code)
  const fetchStart = normalized.indexOf('fetch(')
  const urlMatch = normalized.slice(fetchStart).match(/fetch\s*\(\s*(['"`])([\s\S]*?)\1/)
  if (urlMatch) {
    const urlParts = parseUrlParts(urlMatch[2])
    result.url = urlParts.url
    result.query_params = urlParts.query_params
  }

  const methodMatch = normalized.match(/method\s*:\s*['"`](\w+)['"`]/)
  if (methodMatch) result.method = methodMatch[1].toUpperCase()

  parseFetchHeaders(normalized, result)
  parseFetchBody(normalized, result)

  const authHeader = result.headers.find((header) => header.key.toLowerCase() === 'authorization')
  if (authHeader?.value.startsWith('Bearer ')) {
    result.authType = 'bearer'
    result.authToken = authHeader.value.slice(7)
  }

  if (/credentials\s*:\s*['"`]include['"`]/.test(normalized)) {
    result.warnings.push('浏览器 Cookie 依赖运行态，未自动带入')
  }

  return result
}

export function parseXhrCode(code) {
  const result = {
    method: 'GET',
    url: '',
    headers: [],
    body: '',
    bodyType: 'none',
    query_params: {},
    warnings: [],
  }

  const normalized = normalizeInput(code)
  const methodUrlMatch = normalized.match(/open\s*\(\s*['"`](\w+)['"`]\s*,\s*['"`]([^'"`]+)['"`]/)
  if (methodUrlMatch) {
    result.method = methodUrlMatch[1].toUpperCase()
    const urlParts = parseUrlParts(methodUrlMatch[2])
    result.url = urlParts.url
    result.query_params = urlParts.query_params
  }

  const headerRegex = /setRequestHeader\s*\(\s*['"`]([^'"`]+)['"`]\s*,\s*['"`]([^'"`]*)['"`]\s*\)/g
  let match
  while ((match = headerRegex.exec(normalized)) !== null) {
    result.headers.push({ key: match[1], value: match[2] })
  }

  const sendMatch = normalized.match(/send\s*\(\s*(.*?)\s*\)/)
  if (sendMatch && sendMatch[1] && !['null', 'undefined'].includes(sendMatch[1])) {
    result.body = stripQuotes(sendMatch[1])
    result.bodyType = result.body.includes('=') ? 'form' : 'raw'
  }

  return result
}

export function parseRequest(input) {
  const trimmed = normalizeInput(input)
  if (!trimmed) {
    return { method: 'GET', url: '', headers: [], body: '', bodyType: 'none', sourceType: 'empty', warnings: [] }
  }
  if (trimmed.startsWith('curl ') || trimmed.startsWith('curl"') || trimmed.startsWith("curl'")) {
    return { ...parseCurl(trimmed), sourceType: 'curl' }
  }
  if (trimmed.startsWith('fetch(') || trimmed.startsWith('await fetch(') || trimmed.startsWith('window.fetch(')) {
    return { ...parseFetchCode(trimmed), sourceType: 'fetch' }
  }
  if (trimmed.includes('XMLHttpRequest') || trimmed.includes('.open(')) {
    return { ...parseXhrCode(trimmed), sourceType: 'xhr' }
  }
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    const urlParts = parseUrlParts(trimmed)
    return {
      method: 'GET',
      url: urlParts.url,
      query_params: urlParts.query_params,
      headers: [],
      body: '',
      bodyType: 'none',
      sourceType: 'url',
      warnings: [],
    }
  }
  return { method: 'GET', url: '', headers: [], body: '', bodyType: 'none', sourceType: 'manual', warnings: [] }
}
