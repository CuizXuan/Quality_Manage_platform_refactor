import { ElMessage, ElMessageBox } from 'element-plus'

const DEFAULT_DURATION = 1800

function normalizeMessage(message, fallback) {
  if (!message) return fallback
  if (typeof message === 'string') return message
  return fallback
}

export const feedback = {
  success(message, options = {}) {
    return ElMessage({
      type: 'success',
      message: normalizeMessage(message, '操作成功'),
      duration: DEFAULT_DURATION,
      ...options,
    })
  },

  error(message, options = {}) {
    return ElMessage({
      type: 'error',
      message: normalizeMessage(message, '操作失败'),
      duration: DEFAULT_DURATION,
      ...options,
    })
  },

  warning(message, options = {}) {
    return ElMessage({
      type: 'warning',
      message: normalizeMessage(message, '请检查输入内容'),
      duration: DEFAULT_DURATION,
      ...options,
    })
  },

  info(message, options = {}) {
    return ElMessage({
      type: 'info',
      message: normalizeMessage(message, '请关注提示信息'),
      duration: DEFAULT_DURATION,
      ...options,
    })
  },

  confirm(message, title = '确认操作', options = {}) {
    return ElMessageBox.confirm(message, title, options)
  },
}

export default feedback
