export const priorityOptions = ['P0', 'P1', 'P2', 'P3']

export const methodOptions = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']

export function getPriorityTagType(priority) {
  const map = {
    P0: 'danger',
    P1: 'warning',
    P2: 'primary',
    P3: 'info',
  }
  return map[priority] || 'info'
}

export function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  const pad = (number) => String(number).padStart(2, '0')
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
  ].join('-') + ` ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function stripHtml(value) {
  return String(value || '')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .trim()
}

export function normalizeRows(value) {
  if (Array.isArray(value)) return value
  if (!value || typeof value !== 'object') return []
  return Object.entries(value).map(([key, rowValue]) => ({
    key,
    value: String(rowValue ?? ''),
  }))
}

export function createDefaultApiCase() {
  return {
    method: 'GET',
    url: '',
    headers: [],
    params: [],
    body_type: 'none',
    body: '',
    auth_config: {},
    expected_status: 200,
    assertions: [],
  }
}

export function buildCaseCode(caseType, index) {
  const prefix = caseType === 'api' ? 'APICASE' : 'FUNCCASE'
  const dateText = formatCaseCodeDate(new Date())
  return `${prefix}-${dateText}${String(Math.max(index, 1)).padStart(2, '0')}`
}

export function nextCaseCode(caseType, rows = []) {
  const prefix = caseType === 'api' ? 'APICASE' : 'FUNCCASE'
  const dateText = formatCaseCodeDate(new Date())
  const pattern = new RegExp(`^${prefix}-${dateText}(\\d+)$`)
  const maxNumber = rows.reduce((max, row) => {
    const match = String(row.auto_case_id || '').match(pattern)
    if (!match) return max
    return Math.max(max, Number(match[1]))
  }, 0)
  return buildCaseCode(caseType, maxNumber + 1)
}

function formatCaseCodeDate(date) {
  const pad = (number) => String(number).padStart(2, '0')
  return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}`
}

export function createDefaultFunctionalCase() {
  return {
    steps: [],
    test_data: {},
    post_action: '',
    expected_result: '',
  }
}

export function createBaseCase(caseType, folderId = null) {
  return {
    name: '',
    description: '',
    folder_id: folderId,
    priority: 'P2',
    tags: [],
    pre_condition: '',
    is_automated: false,
    auto_script_path: '',
    auto_script_config: {
      runner: 'pytest',
      entrypoint: '',
      timeout_seconds: 300,
      failure_policy: 'stop',
      params: '',
    },
    auto_case_id: '',
    case_type: caseType,
    api_case: createDefaultApiCase(),
    functional_case: createDefaultFunctionalCase(),
  }
}

export function normalizeCaseForEdit(row, caseType, folderId = null) {
  const base = createBaseCase(caseType, folderId)
  if (!row?.id) return base
  const scriptConfig = row.auto_script_config || {}

  return {
    ...base,
    ...row,
    tags: row.tags || [],
    auto_script_config: {
      ...base.auto_script_config,
      ...scriptConfig,
      params: typeof scriptConfig.params === 'string'
        ? scriptConfig.params
        : JSON.stringify(scriptConfig.params || {}, null, 2),
    },
    api_case: {
      ...createDefaultApiCase(),
      ...(row.api_case || {}),
      headers: normalizeRows(row.api_case?.headers),
      params: normalizeRows(row.api_case?.params),
      assertions: row.api_case?.assertions || [],
    },
    functional_case: {
      ...createDefaultFunctionalCase(),
      ...(row.functional_case || {}),
      steps: row.functional_case?.steps || [],
      test_data: row.functional_case?.test_data || {},
    },
  }
}
