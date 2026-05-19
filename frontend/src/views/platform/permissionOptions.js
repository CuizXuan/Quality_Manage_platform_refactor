export const permissionActions = [
  { key: 'view', label: '查看' },
  { key: 'create', label: '新增' },
  { key: 'update', label: '编辑' },
  { key: 'delete', label: '删除' },
]

export const permissionResources = [
  { key: 'system', label: '系统设置', actions: ['view'] },
  { key: 'user', label: '用户管理', actions: ['view', 'create', 'update', 'delete'] },
  { key: 'role', label: '角色管理', actions: ['view', 'create', 'update', 'delete'] },
  { key: 'organization', label: '组织管理', actions: ['view', 'create', 'update', 'delete'] },
  { key: 'menu', label: '菜单管理', actions: ['view', 'create', 'update', 'delete'] },
  { key: 'terminal', label: '终端调试台', actions: ['view', 'debug'] },
  { key: 'case', label: '用例中心', actions: ['view', 'create', 'update', 'delete', 'run'] },
]

const actionLabels = new Map(permissionActions.map((item) => [item.key, item.label]))

export const permissionOptions = permissionResources.flatMap((resource) =>
  resource.actions.map((action) => ({
    value: `${resource.key}:${action}`,
    label: `${resource.label} / ${formatAction(action)}`,
  })),
)

const permissionLabels = new Map(permissionOptions.map((item) => [item.value, item.label]))

export function formatPermission(value) {
  return permissionLabels.get(value) || value
}

export function formatPermissions(values = []) {
  return values.map(formatPermission).join('，')
}

export function formatAction(value) {
  return actionLabels.get(value) || value
}
