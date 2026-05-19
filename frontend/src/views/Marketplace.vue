<template>
  <div class="marketplace">
    <div class="page-header">
      <h1 class="page-title">插件市场</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="showMyPlugins = true">
          📦 我的插件
        </button>
        <button class="btn-primary" @click="showPublishDialog = true">
          + 发布插件
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">🛒</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalPlugins }}</span>
          <span class="stat-label">插件总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📥</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalInstalls }}</span>
          <span class="stat-label">总安装量</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.avgRating.toFixed(1) }}</span>
          <span class="stat-label">平均评分</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔑</div>
        <div class="stat-info">
          <span class="stat-value">{{ cliKeys.length }}</span>
          <span class="stat-label">CLI Keys</span>
        </div>
      </div>
    </div>

    <!-- 分类标签 -->
    <div class="category-tabs">
      <button
        :class="{ active: currentCategory === '' }"
        @click="currentCategory = ''; loadPlugins()"
      >
        全部
      </button>
      <button
        v-for="cat in categories"
        :key="cat.key"
        :class="{ active: currentCategory === cat.key }"
        @click="currentCategory = cat.key; loadPlugins()"
      >
        {{ cat.icon }} {{ cat.name }}
        <span class="cat-count">{{ cat.count }}</span>
      </button>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索插件名称或描述..."
        class="search-input"
        @keyup.enter="loadPlugins"
      />
      <button class="btn-search" @click="loadPlugins">搜索</button>
    </div>

    <!-- 插件列表 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!plugins.length" class="empty-state">
      <div class="empty-icon">🛒</div>
      <p>暂无插件</p>
      <button class="btn-primary" @click="showPublishDialog = true">成为首个插件开发者</button>
    </div>
    <div v-else class="plugins-grid">
      <div
        v-for="plugin in plugins"
        :key="plugin.id"
        class="plugin-card"
        @click="showPluginDetail(plugin)"
      >
        <div class="plugin-header">
          <div class="plugin-icon">{{ getCategoryIcon(plugin.category) }}</div>
          <div class="plugin-badges">
            <span v-if="plugin.is_official" class="badge official">官方</span>
            <span v-if="plugin.is_verified" class="badge verified">认证</span>
            <span v-if="plugin.price > 0" class="badge premium">¥{{ plugin.price }}</span>
          </div>
        </div>
        <h3 class="plugin-name">{{ plugin.name }}</h3>
        <p class="plugin-desc">{{ plugin.description || '暂无描述' }}</p>
        <div class="plugin-tags">
          <span v-for="tag in (plugin.tags || []).slice(0, 3)" :key="tag" class="tag">
            {{ tag }}
          </span>
        </div>
        <div class="plugin-footer">
          <div class="plugin-stats">
            <span class="stat">⭐ {{ plugin.rating.toFixed(1) }}</span>
            <span class="stat">📥 {{ plugin.install_count || 0 }}</span>
          </div>
          <span class="plugin-version">v{{ plugin.version }}</span>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalCount > pageSize" class="pagination">
      <button :disabled="page <= 1" @click="page--; loadPlugins()">上一页</button>
      <span>{{ page }} / {{ Math.ceil(totalCount / pageSize) }}</span>
      <button :disabled="page >= Math.ceil(totalCount / pageSize)" @click="page++; loadPlugins()">下一页</button>
    </div>

    <!-- 插件详情弹窗 -->
    <div v-if="selectedPlugin" class="modal-overlay" @click.self="selectedPlugin = null">
      <div class="modal plugin-detail-modal">
        <div class="modal-header">
          <h2>{{ selectedPlugin.name }}</h2>
          <button class="btn-close" @click="selectedPlugin = null">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-meta">
            <span class="badge" :class="'cat-' + selectedPlugin.category">{{ getCategoryName(selectedPlugin.category) }}</span>
            <span>作者: {{ selectedPlugin.author || '未知' }}</span>
            <span>v{{ selectedPlugin.version }}</span>
            <span>📥 {{ selectedPlugin.install_count || 0 }} 安装</span>
            <span>⭐ {{ selectedPlugin.rating.toFixed(1) }} ({{ selectedPlugin.rating_count }})</span>
          </div>
          <p class="detail-desc">{{ selectedPlugin.description }}</p>

          <div v-if="selectedPlugin.readme" class="detail-readme">
            <h4>README</h4>
            <pre>{{ selectedPlugin.readme }}</pre>
          </div>

          <div v-if="selectedPlugin.tags?.length" class="detail-tags">
            <h4>标签</h4>
            <span v-for="tag in selectedPlugin.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showPluginReviews">查看评论</button>
          <button class="btn-primary" @click="installPlugin(selectedPlugin.id)">
            {{ isPluginInstalled(selectedPlugin.id) ? '已安装' : '安装插件' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 发布插件弹窗 -->
    <div v-if="showPublishDialog" class="modal-overlay" @click.self="showPublishDialog = false">
      <div class="modal publish-modal">
        <div class="modal-header">
          <h2>发布插件</h2>
          <button class="btn-close" @click="showPublishDialog = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>插件名称 *</label>
            <input v-model="publishForm.name" type="text" placeholder="例如: gRPC 测试执行器" />
          </div>
          <div class="form-group">
            <label>插件标识 (slug) *</label>
            <input v-model="publishForm.slug" type="text" placeholder="例如: grpc-executor" />
            <small>唯一标识，将用于插件市场 URL</small>
          </div>
          <div class="form-group">
            <label>版本</label>
            <input v-model="publishForm.version" type="text" placeholder="1.0.0" />
          </div>
          <div class="form-group">
            <label>分类 *</label>
            <select v-model="publishForm.category">
              <option value="">请选择</option>
              <option value="executor">测试执行</option>
              <option value="assertion">断言插件</option>
              <option value="reporter">报告生成</option>
              <option value="integration">集成对接</option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="publishForm.description" rows="3" placeholder="简要描述插件功能..."></textarea>
          </div>
          <div class="form-group">
            <label>标签</label>
            <input v-model="publishForm.tagsInput" type="text" placeholder="grpc, authentication (逗号分隔)" />
          </div>
          <div class="form-group">
            <label>README</label>
            <textarea v-model="publishForm.readme" rows="5" placeholder="详细使用说明..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showPublishDialog = false">取消</button>
          <button class="btn-primary" @click="publishPlugin" :disabled="!publishForm.name || !publishForm.category">
            提交审核
          </button>
        </div>
      </div>
    </div>

    <!-- 我的插件弹窗 -->
    <div v-if="showMyPlugins" class="modal-overlay" @click.self="showMyPlugins = false">
      <div class="modal my-plugins-modal">
        <div class="modal-header">
          <h2>我的插件</h2>
          <button class="btn-close" @click="showMyPlugins = false">×</button>
        </div>
        <div class="modal-body">
          <div class="tabs">
            <button :class="{ active: myPluginTab === 'installed' }" @click="myPluginTab = 'installed'; loadMyPlugins()">
              已安装
            </button>
            <button :class="{ active: myPluginTab === 'published' }" @click="myPluginTab = 'published'; loadMyPublished()">
              我发布的
            </button>
            <button :class="{ active: myPluginTab === 'cli' }" @click="myPluginTab = 'cli'; loadCLIKeys()">
              CLI Keys
            </button>
          </div>

          <!-- 已安装插件 -->
          <div v-if="myPluginTab === 'installed'" class="plugin-list">
            <div v-if="!installedPlugins.length" class="empty-state small">
              暂无安装的插件
            </div>
            <div v-for="p in installedPlugins" :key="p.id" class="plugin-item">
              <div class="plugin-info">
                <strong>{{ p.name }}</strong>
                <span>v{{ p.installed_version || p.version }}</span>
              </div>
              <button class="btn-danger btn-small" @click="uninstallPlugin(p.id)">卸载</button>
            </div>
          </div>

          <!-- 我发布的 -->
          <div v-if="myPluginTab === 'published'" class="plugin-list">
            <div v-if="!publishedPlugins.length" class="empty-state small">
              暂无发布的插件
            </div>
            <div v-for="p in publishedPlugins" :key="p.id" class="plugin-item">
              <div class="plugin-info">
                <strong>{{ p.name }}</strong>
                <span class="badge" :class="'status-' + p.status">{{ p.status }}</span>
              </div>
              <span>{{ p.install_count || 0 }} 安装</span>
            </div>
          </div>

          <!-- CLI Keys -->
          <div v-if="myPluginTab === 'cli'">
            <div class="cli-key-list">
              <div v-if="!cliKeys.length" class="empty-state small">
                暂无 CLI Keys
              </div>
              <div v-for="k in cliKeys" :key="k.id" class="cli-key-item">
                <div class="cli-key-info">
                  <strong>{{ k.name }}</strong>
                  <code>{{ k.key_prefix }}****</code>
                  <span v-if="k.last_used_at">最后使用: {{ formatTime(k.last_used_at) }}</span>
                </div>
                <button class="btn-danger btn-small" @click="deleteCLIKey(k.id)">删除</button>
              </div>
            </div>
            <button class="btn-secondary" @click="showCreateKeyDialog = true">+ 创建 CLI Key</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建 CLI Key 弹窗 -->
    <div v-if="showCreateKeyDialog" class="modal-overlay" @click.self="showCreateKeyDialog = false">
      <div class="modal">
        <div class="modal-header">
          <h2>创建 CLI Key</h2>
          <button class="btn-close" @click="showCreateKeyDialog = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Key 名称 *</label>
            <input v-model="cliKeyForm.name" type="text" placeholder="例如: 本地开发 Key" />
          </div>
          <div class="form-group">
            <label>权限</label>
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input type="checkbox" value="read" v-model="cliKeyForm.permissions" />
                <span>读取</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" value="write" v-model="cliKeyForm.permissions" />
                <span>写入</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" value="execute" v-model="cliKeyForm.permissions" />
                <span>执行</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>有效期 (天)</label>
            <input v-model.number="cliKeyForm.expiresInDays" type="number" placeholder="不填则永不过期" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCreateKeyDialog = false">取消</button>
          <button class="btn-primary" @click="createCLIKey" :disabled="!cliKeyForm.name">创建</button>
        </div>
      </div>
    </div>

    <!-- API Key 展示弹窗 -->
    <div v-if="newCLIKey" class="modal-overlay" @click.self="newCLIKey = null">
      <div class="modal">
        <div class="modal-header">
          <h2>CLI Key 已创建</h2>
          <button class="btn-close" @click="newCLIKey = null">×</button>
        </div>
        <div class="modal-body">
          <div class="alert alert-warning">
            ⚠️ 请立即复制 Key，稍后无法再次查看
          </div>
          <div class="form-group">
            <label>API Key</label>
            <div class="key-display">
              <code>{{ newCLIKey.api_key }}</code>
              <button class="btn-secondary" @click="copyKey(newCLIKey.api_key)">复制</button>
            </div>
          </div>
          <p class="text-muted">前缀: {{ newCLIKey.key_prefix }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-primary" @click="newCLIKey = null">完成</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const API_BASE = '/api'

// State
const plugins = ref([])
const selectedPlugin = ref(null)
const showPublishDialog = ref(false)
const showMyPlugins = ref(false)
const showCreateKeyDialog = ref(false)
const newCLIKey = ref(null)
const loading = ref(false)
const currentCategory = ref('')
const searchQuery = ref('')
const page = ref(1)
const pageSize = 20
const totalCount = ref(0)
const myPluginTab = ref('installed')
const installedPlugins = ref([])
const publishedPlugins = ref([])
const cliKeys = ref([])

// Stats
const stats = ref({ totalPlugins: 0, totalInstalls: 0, avgRating: 0 })

// Categories
const categories = ref([
  { key: 'executor', name: '测试执行', icon: '⚡', count: 0 },
  { key: 'assertion', name: '断言插件', icon: '✅', count: 0 },
  { key: 'reporter', name: '报告生成', icon: '📊', count: 0 },
  { key: 'integration', name: '集成对接', icon: '🔗', count: 0 },
])

// Publish form
const publishForm = ref({
  name: '',
  slug: '',
  version: '1.0.0',
  category: '',
  description: '',
  tagsInput: '',
  readme: '',
})

// CLI Key form
const cliKeyForm = ref({
  name: '',
  permissions: ['read'],
  expiresInDays: null,
})

// Methods
async function loadPlugins() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (currentCategory.value) params.category = currentCategory.value
    if (searchQuery.value) params.search = searchQuery.value
    const res = await fetch(`${API_BASE}/marketplace/plugins?${new URLSearchParams(params)}`)
    const data = await res.json()
    plugins.value = data.items || []
    totalCount.value = data.total || 0
  } catch (e) {
    console.error('Load plugins failed:', e)
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const res = await fetch(`${API_BASE}/marketplace/categories`)
    const data = await res.json()
    const cats = data.categories || []
    categories.value = categories.value.map(c => {
      const found = cats.find(x => x.key === c.key)
      return { ...c, count: found?.count || 0 }
    })
    stats.value.totalPlugins = cats.reduce((s, c) => s + c.count, 0)
  } catch (e) {
    console.error('Load categories failed:', e)
  }
}

async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/marketplace/plugins?page_size=1`)
    const data = await res.json()
    stats.value.totalPlugins = data.total || 0
    stats.value.avgRating = 4.5 // 简化
    stats.value.totalInstalls = res.items?.reduce((s, p) => s + (p.install_count || 0), 0) || 0
  } catch (e) {
    console.error('Load stats failed:', e)
  }
}

function showPluginDetail(plugin) {
  selectedPlugin.value = plugin
}

function getCategoryIcon(cat) {
  return { executor: '⚡', assertion: '✅', reporter: '📊', integration: '🔗' }[cat] || '📦'
}

function getCategoryName(cat) {
  return { executor: '测试执行', assertion: '断言插件', reporter: '报告生成', integration: '集成对接' }[cat] || cat
}

function isPluginInstalled(id) {
  return installedPlugins.value.some(p => p.id === id)
}

async function installPlugin(id) {
  try {
    await fetch(`${API_BASE}/marketplace/plugins/${id}/install`, { method: 'POST' })
    await loadMyPlugins()
    alert('安装成功')
  } catch (e) {
    alert('安装失败: ' + (e.message || '未知错误'))
  }
}

async function uninstallPlugin(id) {
  if (!confirm('确定要卸载此插件吗？')) return
  try {
    await fetch(`${API_BASE}/marketplace/plugins/${id}/uninstall`, { method: 'POST' })
    await loadMyPlugins()
  } catch (e) {
    alert('卸载失败')
  }
}

async function publishPlugin() {
  try {
    const tags = publishForm.value.tagsInput
      ? publishForm.value.tagsInput.split(',').map(t => t.trim()).filter(Boolean)
      : []
    await fetch(`${API_BASE}/marketplace/plugins`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: publishForm.value.name,
        slug: publishForm.value.slug,
        version: publishForm.value.version,
        category: publishForm.value.category,
        description: publishForm.value.description,
        tags,
        readme: publishForm.value.readme,
      }),
    })
    alert('插件已提交审核')
    showPublishDialog.value = false
    loadPlugins()
  } catch (e) {
    alert('发布失败: ' + (e.message || '未知错误'))
  }
}

async function loadMyPlugins() {
  try {
    const res = await fetch(`${API_BASE}/marketplace/my-plugins`)
    const data = await res.json()
    installedPlugins.value = data.items || []
  } catch (e) {
    console.error('Load my plugins failed:', e)
  }
}

async function loadMyPublished() {
  try {
    const res = await fetch(`${API_BASE}/marketplace/my-published`)
    const data = await res.json()
    publishedPlugins.value = data.items || []
  } catch (e) {
    console.error('Load my published failed:', e)
  }
}

async function loadCLIKeys() {
  try {
    const res = await fetch(`${API_BASE}/marketplace/cli/keys`)
    const data = await res.json()
    cliKeys.value = data.items || []
  } catch (e) {
    console.error('Load CLI keys failed:', e)
  }
}

async function createCLIKey() {
  try {
    const res = await fetch(`${API_BASE}/marketplace/cli/keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: cliKeyForm.value.name,
        permissions: cliKeyForm.value.permissions,
        expires_in_days: cliKeyForm.value.expiresInDays,
      }),
    })
    const data = await res.json()
    newCLIKey.value = data
    showCreateKeyDialog.value = false
    loadCLIKeys()
  } catch (e) {
    alert('创建失败')
  }
}

async function deleteCLIKey(id) {
  if (!confirm('确定删除此 Key？')) return
  try {
    await fetch(`${API_BASE}/marketplace/cli/keys/${id}`, { method: 'DELETE' })
    loadCLIKeys()
  } catch (e) {
    alert('删除失败')
  }
}

function showPluginReviews() {
  alert('评论功能开发中')
}

function copyKey(key) {
  navigator.clipboard.writeText(key).then(() => alert('已复制'))
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(() => {
  loadPlugins()
  loadCategories()
  loadStats()
})
</script>

<style scoped>
.marketplace {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.stat-icon {
  font-size: 32px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #888;
}

.category-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.category-tabs button {
  padding: 8px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.category-tabs button:hover {
  border-color: #667eea;
  color: #667eea;
}

.category-tabs button.active {
  background: #667eea;
  color: #fff;
  border-color: #667eea;
}

.cat-count {
  background: rgba(0,0,0,0.1);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.search-input {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.btn-search {
  padding: 10px 24px;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.plugins-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.plugin-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.2s;
}

.plugin-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transform: translateY(-2px);
}

.plugin-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.plugin-icon {
  font-size: 40px;
}

.plugin-badges {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.badge.official { background: #e3f2fd; color: #1976d2; }
.badge.verified { background: #e8f5e9; color: #388e3c; }
.badge.premium { background: #fff3e0; color: #f57c00; }

.plugin-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px;
  color: #333;
}

.plugin-desc {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.plugin-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.tag {
  font-size: 12px;
  padding: 2px 8px;
  background: #f5f5f5;
  border-radius: 4px;
  color: #666;
}

.plugin-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.plugin-stats {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #888;
}

.plugin-version {
  font-size: 12px;
  color: #aaa;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #fff;
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #888;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-weight: 500;
  margin-bottom: 6px;
  color: #333;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.form-group small {
  font-size: 12px;
  color: #888;
}

.checkbox-group {
  display: flex;
  gap: 16px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.detail-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 16px;
  font-size: 14px;
  color: #666;
}

.detail-readme {
  margin-top: 16px;
}

.detail-readme h4,
.detail-tags h4 {
  font-size: 14px;
  margin: 0 0 8px;
  color: #333;
}

.detail-readme pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  overflow-x: auto;
  max-height: 200px;
}

.detail-tags {
  margin-top: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.plugin-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.plugin-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.plugin-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.plugin-info strong {
  font-size: 15px;
}

.cli-key-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.cli-key-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.cli-key-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cli-key-info code {
  font-size: 13px;
  color: #667eea;
}

.cli-key-info span {
  font-size: 12px;
  color: #888;
}

.key-display {
  display: flex;
  gap: 12px;
  align-items: center;
}

.key-display code {
  flex: 1;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 13px;
  word-break: break-all;
}

.alert {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.alert-warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeeba;
}

.text-muted {
  font-size: 13px;
  color: #888;
  margin-top: 8px;
}

/* Buttons */
.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  background: #fff;
  color: #667eea;
  border: 1px solid #667eea;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.btn-danger {
  padding: 6px 12px;
  background: #fff;
  color: #e53935;
  border: 1px solid #e53935;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.btn-small {
  padding: 4px 10px;
  font-size: 12px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading, .empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #888;
}

.empty-state p {
  font-size: 16px;
  margin: 16px 0;
}

.empty-state.small {
  padding: 30px;
  font-size: 14px;
}

.empty-icon {
  font-size: 48px;
}

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid #f0f0f0;
  margin-bottom: 16px;
}

.tabs button {
  padding: 8px 16px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.tabs button.active {
  color: #667eea;
  border-bottom-color: #667eea;
}
</style>
