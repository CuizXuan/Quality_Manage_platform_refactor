export const statusOptions = [
  { value: 'active', label: '启用' },
  { value: 'disabled', label: '停用' },
]

const statusLabels = new Map(statusOptions.map((item) => [item.value, item.label]))

export function formatStatus(value) {
  return statusLabels.get(value) || value || '-'
}
