/**
 * requestParser.js - 词法拆分 + 结构解析
 * 支持 curl、fetch、XMLHttpRequest、纯 URL 自动识别
 */

/**
 * 通用工具函数
 */
function trimAndNormalize(str) {
  return str.trim().replace(/\\\n/g, ' ').replace(/\s+/g, ' ')
}

function findFirstUnquoted(str, char) {
  let inSingle = false, inDouble = false, escape = false
  for (let i = 0; i < str.length; i++) {
    const c = str[i]
    if (escape) { escape = false; continue }
    if (c === '\\') { escape = true; continue }
    if (c === "'" && !inDouble) inSingle = !inSingle
    if (c === '"' && !inSingle) inDouble = !inDouble
    if (c === char && !inSingle && !inDouble) return i
  }
  return -1
}

function splitOnce(str, delimiter) {
  const idx = findFirstUnquoted(str, delimiter)
  if (idx === -1) return [str, '']
  return [str.slice(0, idx), str.slice(idx + 1)]
}

function parseCookieString(cookieStr) {
  const cookies = []
  cookieStr.split(';').forEach(pair => {
    const [key, ...valueParts] = pair.trim().split('=')
    if (key) cookies.push({ key: key.trim(), value: valueParts.join('=').trim() })
  })
  return cookies
}

/**
 * curl 命令解析
 * 处理：-H/--header, -X/--request, -d/--data/--data-raw, -b/--cookie, -u/--user
 * 处理引号保留、反斜杠转义、续行
 */
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

  // 预处理：合并续行，移除 curl 前缀
  let cmd = trimAndNormalize(curlCommand)
  cmd = cmd.replace(/^curl\s*/, '')

  const tokens = []
  let current = ''
  let inSingle = false, inDouble = false, escape = false

  // 简单词法分析器：按空格拆分但保留引号内容
  let i = 0
  while (i < cmd.length) {
    const c = cmd[i]
    if (escape) { current += c; escape = false; i++; continue }
    if (c === '\\') { escape = true; i++; continue }
    if (c === "'" && !inDouble) { inSingle = !inSingle; current += c; i++; continue }
    if (c === '"' && !inSingle) { inDouble = !inDouble; current += c; i++; continue }
    if (c === ' ' && !inSingle && !inDouble) {
      if (current) { tokens.push(current); current = '' }
      i++; continue
    }
    current += c
    i++
  }
  if (current) tokens.push(current)

  // 解析 tokens
  let urlFound = false
  let dataArgs = []

  for (let j = 0; j < tokens.length; j++) {
    const token = tokens[j]
    const next = tokens[j + 1]

    // method/option
    if (token === '-X' || token === '--request') {
      if (next) { result.method = next.toUpperCase(); j++ }
      continue
    }

    // header
    if (token === '-H' || token === '--header') {
      if (next) {
        // 提取 "key: value" - 按第一个冒号拆分，保留完整 value
        const colonIdx = findFirstUnquoted(next, ':')
        if (colonIdx > 0) {
          const key = next.slice(0, colonIdx).trim()
          const value = next.slice(colonIdx + 1).trim()
          // 去掉引号
          const cleanValue = value.replace(/^['"]|['"]$/g, '')
          result.headers.push({ key, value: cleanValue })
        }
        j++
      }
      continue
    }

    // data
    if (token === '-d' || token === '--data' || token === '--data-raw' || token === '--data-binary') {
      if (next) { dataArgs.push(next); j++ }
      continue
    }
    if (token === '--data-urlencode') {
      if (next) { dataArgs.push(next); j++ }
      continue
    }

    // cookie
    if (token === '-b' || token === '--cookie') {
      if (next) {
        if (!next.startsWith('@')) {
          result.cookies = parseCookieString(next)
        }
        j++
      }
      continue
    }

    // user/auth
    if (token === '-u' || token === '--user') {
      if (next) {
        const [user, pass] = next.split(':')
        result.headers.push({ key: 'Authorization', value: `Basic ${btoa(`${user}:${pass || ''}`)}` })
        result.authType = 'basic'
        j++
      }
      continue
    }

    // 其他 option 跳过
    if (token.startsWith('-')) continue

    // URL（第一个非 option 参数）
    if (!urlFound && (token.startsWith('http://') || token.startsWith('https://') || token.startsWith('/'))) {
      result.url = token
      urlFound = true
      // 拆分 query params
      const qIdx = token.indexOf('?')
      if (qIdx > 0) {
        const queryString = token.slice(qIdx + 1)
        result.url = token.slice(0, qIdx)
        queryString.split('&').forEach(pair => {
          const [k, v] = pair.split('=')
          if (k) result.query_params[decodeURIComponent(k)] = decodeURIComponent(v || '')
        })
      }
      continue
    }
  }

  // 处理 body
  if (dataArgs.length > 0) {
    const rawBody = dataArgs.join('&')
    result.body = rawBody

    // 检测 body 类型
    try {
      JSON.parse(rawBody)
      result.bodyType = 'json'
      if (!result.headers.find(h => h.key.toLowerCase() === 'content-type')) {
        result.headers.push({ key: 'Content-Type', value: 'application/json' })
      }
    } catch {
      if (rawBody.includes('=') && !rawBody.includes('{')) {
        result.bodyType = 'form'
        if (!result.headers.find(h => h.key.toLowerCase() === 'content-type')) {
          result.headers.push({ key: 'Content-Type', value: 'application/x-www-form-urlencoded' })
        }
      } else {
        result.bodyType = 'raw'
      }
    }

    // 如果没有指定 method，默认 POST
    if (!tokens.includes('-X') && !tokens.includes('--request')) {
      result.method = 'POST'
    }
  }

  // Authorization: Bearer xxx -> auth
  const authHeader = result.headers.find(h => h.key.toLowerCase() === 'authorization')
  if (authHeader && authHeader.value.startsWith('Bearer ')) {
    result.authType = 'bearer'
    result.authToken = authHeader.value.slice(7)
  }

  return result
}

/**
 * fetch / XMLHttpRequest 解析
 * 支持多行、多种 header 写法、template string
 */
export function parseFetchCode(code) {
  const result = {
    method: 'GET',
    url: '',
    headers: [],
    cookies: [],
    body: '',
    bodyType: 'none',
    authType: 'none',
    authToken: '',
    warnings: [],
  }

  let cmd = code.trim()

  // 提取 URL
  const fetchMatch = cmd.match(/fetch\s*\(\s*(.+?)\s*,\s*\{/)
  const fetchSingleMatch = cmd.match(/fetch\s*\(\s*(.+?)\s*\)/)
  if (fetchMatch) {
    result.url = extractStringValue(fetchMatch[1])
  } else if (fetchSingleMatch) {
    result.url = extractStringValue(fetchSingleMatch[1])
  }

  // 提取 method
  const methodMatch = cmd.match(/method\s*:\s*["'](\w+)["']/)
  if (methodMatch) result.method = methodMatch[1].toUpperCase()

  // 提取 headers 块
  const headersBlockMatch = cmd.match(/headers\s*:\s*\{([\s\S]*?)\s*\},/)
  if (headersBlockMatch) {
    parseHeadersBlock(headersBlockMatch[1], result)
  }

  // 支持 new Headers()
  const newHeadersMatch = cmd.match(/new Headers\s*\(\s*\{([\s\S]*?)\}\s*\)/)
  if (newHeadersMatch) {
    parseHeadersBlock(newHeadersMatch[1], result)
  }

  // 支持 new Headers([['a','b']])
  const newHeadersArrayMatch = cmd.match(/new Headers\s*\(\s*\[\s*([^\]]+)\]\s*\)/)
  if (newHeadersArrayMatch) {
    parseHeadersArray(newHeadersArrayMatch[1], result)
  }

  // 提取 body
  const bodyMatch = cmd.match(/body\s*:\s*(.+?)(?:,|\n|\})/)
  if (bodyMatch) {
    const bodyVal = bodyMatch[1].trim()
    if (bodyVal === 'null' || bodyVal === 'undefined' || bodyVal === '{}') {
      // no body
    } else if (bodyVal.startsWith('"') || bodyVal.startsWith("'")) {
      result.body = extractStringValue(bodyVal)
      try {
        JSON.parse(result.body)
        result.bodyType = 'json'
      } catch {
        result.bodyType = 'raw'
      }
    } else if (bodyVal.startsWith('JSON.stringify')) {
      const jsonMatch = bodyVal.match(/JSON\.stringify\s*\(\s*(\{[\s\S]*\})\s*\)/)
      if (jsonMatch) {
        result.body = jsonMatch[1]
        result.bodyType = 'json'
      }
    } else if (bodyVal.startsWith('new URLSearchParams')) {
      result.bodyType = 'form'
      result.body = bodyVal
    } else {
      result.warnings.push(`body 含动态内容: ${bodyVal.slice(0, 30)}`)
    }
  }

  // Authorization 转换 auth
  const authHeader = result.headers.find(h => h.key.toLowerCase() === 'authorization')
  if (authHeader && authHeader.value.startsWith('Bearer ')) {
    result.authType = 'bearer'
    result.authToken = authHeader.value.slice(7)
  }

  // credentials 警告
  if (cmd.includes('credentials') && cmd.includes('"include"')) {
    result.warnings.push('浏览器 Cookie 依赖运行态，未自动带入')
  }

  return result
}

function parseHeadersBlock(blockStr, result) {
  // 支持 "key": "value" 或 "key": value 或 key: "value"
  const kvRegex = /(?:["'])(\w[\w-]*)(?:["'])\s*:\s*(?:["']([^"']*?)["']|(\d+))/g
  let match
  while ((match = kvRegex.exec(blockStr)) !== null) {
    result.headers.push({ key: match[1], value: match[2] !== undefined ? match[2] : match[3] })
  }

  // 支持未加引号的 key: value（值不含逗号和引号）
  const simpleKvRegex = /([a-zA-Z_][\w-]*)\s*:\s*(?:["']([^"']*?)["']|([^,\s]+))/g
  while ((match = simpleKvRegex.exec(blockStr)) !== null) {
    if (!result.headers.find(h => h.key === match[1])) {
      result.headers.push({ key: match[1], value: match[2] || match[3] })
    }
  }
}

function parseHeadersArray(arrStr, result) {
  const itemRegex = /\[\s*["']([^"']+)["']\s*,\s*["']([^"']*?)["']\s*\]/g
  let match
  while ((match = itemRegex.exec(arrStr)) !== null) {
    result.headers.push({ key: match[1], value: match[2] })
  }
}

function extractStringValue(str) {
  str = str.trim()
  if ((str.startsWith('"') && str.endsWith('"')) || (str.startsWith("'") && str.endsWith("'"))) {
    return str.slice(1, -1)
  }
  return str
}

/**
 * XMLHttpRequest 解析
 */
export function parseXhrCode(code) {
  const result = {
    method: 'GET',
    url: '',
    headers: [],
    body: '',
    bodyType: 'none',
    warnings: [],
  }

  const methodUrlMatch = code.match(/open\s*\(\s*["'](\w+)["']\s*,\s*["']([^"']+)["']/)
  if (methodUrlMatch) {
    result.method = methodUrlMatch[1].toUpperCase()
    result.url = methodUrlMatch[2]
  }

  // setRequestHeader
  const headerRegex = /setRequestHeader\s*\(\s*["']([^"']+)["']\s*,\s*["']([^"']+)["']\s*\)/g
  let match
  while ((match = headerRegex.exec(code)) !== null) {
    result.headers.push({ key: match[1], value: match[2] })
  }

  // send(body)
  const sendMatch = code.match(/send\s*\(\s*(.*?)\s*\)/)
  if (sendMatch && sendMatch[1] && sendMatch[1] !== 'null' && sendMatch[1] !== 'undefined') {
    result.body = sendMatch[1].replace(/^["']|["']$/g, '')
    result.bodyType = result.body.includes('=') ? 'form' : 'raw'
  }

  return result
}

/**
 * 自动识别入口
 */
export function parseRequest(input) {
  const trimmed = input.trim()

  // 空输入
  if (!trimmed) {
    return { method: 'GET', url: '', headers: [], body: '', bodyType: 'none', sourceType: 'empty', warnings: [] }
  }

  // curl 检测
  if (trimmed.startsWith('curl ') || trimmed.startsWith('curl"') || trimmed.startsWith("curl'")) {
    return { ...parseCurl(trimmed), sourceType: 'curl' }
  }

  // fetch 检测
  if (trimmed.startsWith('fetch(') || trimmed.startsWith('await fetch(') || trimmed.startsWith('window.fetch(')) {
    return { ...parseFetchCode(trimmed), sourceType: 'fetch' }
  }

  // XMLHttpRequest 检测
  if (trimmed.includes('XMLHttpRequest') || trimmed.includes('xhr.open')) {
    return { ...parseXhrCode(trimmed), sourceType: 'xhr' }
  }

  // 纯 URL
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    const result = { method: 'GET', url: trimmed, headers: [], body: '', bodyType: 'none', sourceType: 'url', warnings: [] }
    const qIdx = trimmed.indexOf('?')
    if (qIdx > 0) {
      result.url = trimmed.slice(0, qIdx)
      result.query_params = {}
      trimmed.slice(qIdx + 1).split('&').forEach(pair => {
        const [k, v] = pair.split('=')
        if (k) result.query_params[decodeURIComponent(k)] = decodeURIComponent(v || '')
      })
    }
    return result
  }

  return { method: 'GET', url: '', headers: [], body: '', bodyType: 'none', sourceType: 'manual', warnings: [] }
}