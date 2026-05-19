export const menuIconOptions = [
  { value: 'Monitor', label: '工作台', symbol: '▦' },
  { value: 'UserRound', label: '用户', symbol: '◎' },
  { value: 'ShieldCheck', label: '角色', symbol: '◇' },
  { value: 'Network', label: '组织', symbol: '⌘' },
  { value: 'PanelLeft', label: '菜单', symbol: '☰' },
  { value: 'Settings', label: '设置', symbol: '⚙' },
  { value: 'FileText', label: '文档', symbol: '□' },
  { value: 'ListChecks', label: '清单', symbol: '☑' },
  { value: 'BarChart3', label: '报表', symbol: '▥' },
  { value: 'Sparkles', label: 'AI', symbol: '✦' },
]

const menuIcons = new Map(menuIconOptions.map((item) => [item.value, item]))

export function getMenuIcon(value) {
  return menuIcons.get(value) || { value, label: value || '未设置', symbol: '□' }
}

export function formatMenuIcon(value) {
  const icon = getMenuIcon(value)
  return `${icon.symbol} ${icon.label}`
}
