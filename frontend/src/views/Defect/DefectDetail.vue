<template>
  <div class="defect-detail" v-if="defect">
    <div class="detail-header">
      <div class="header-left">
        <button class="btn" @click="emit('close')">← 返回</button>
        <h2 class="defect-title">{{ defect.title }}</h2>
      </div>
      <div class="header-actions">
        <span class="status-badge" :class="'status-' + defect.status">{{ statusText(defect.status) }}</span>
        <button class="btn primary" @click="editing = !editing">{{ editing ? '取消编辑' : '编辑' }}</button>
      </div>
    </div>

    <div class="detail-body">
      <!-- 基本信息 -->
      <div class="info-section panel">
        <h3 class="section-title">// 基本信息</h3>
        <div class="info-grid" v-if="!editing">
          <div class="info-item">
            <span class="info-label">严重程度</span>
            <span class="severity-badge" :class="'sev-' + defect.severity">{{ severityText(defect.severity) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">优先级</span>
            <span class="priority-badge" :class="'pri-' + defect.priority">{{ priorityText(defect.priority) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">状态</span>
            <span class="status-badge" :class="'status-' + defect.status">{{ statusText(defect.status) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">缺陷类型</span>
            <span>{{ defectTypeText(defect.defect_type) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">指派人</span>
            <span>{{ defect.assignee || '未分配' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">报告人</span>
            <span>{{ defect.reporter }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">环境</span>
            <span>{{ defect.environment || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">创建时间</span>
            <span>{{ formatTime(defect.created_at) }}</span>
          </div>
        </div>

        <!-- 编辑表单 -->
        <div class="edit-form" v-else>
          <div class="form-row">
            <div class="form-group">
              <label>标题</label>
              <input v-model="form.title" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>严重程度</label>
              <select v-model="form.severity">
                <option value="critical">紧急</option>
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低</option>
              </select>
            </div>
            <div class="form-group">
              <label>优先级</label>
              <select v-model="form.priority">
                <option value="urgent">紧急</option>
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低</option>
              </select>
            </div>
            <div class="form-group">
              <label>状态</label>
              <select v-model="form.status">
                <option value="open">待处理</option>
                <option value="in_progress">处理中</option>
                <option value="resolved">已解决</option>
                <option value="closed">已关闭</option>
                <option value="reopened">重新打开</option>
              </select>
            </div>
            <div class="form-group">
              <label>指派人</label>
              <input v-model="form.assignee" />
            </div>
          </div>
          <div class="form-actions">
            <button class="btn" @click="editing = false">取消</button>
            <button class="btn primary" @click="saveEdit">保存</button>
          </div>
        </div>
      </div>

      <!-- 描述 -->
      <div class="desc-section panel">
        <h3 class="section-title">// 描述</h3>
        <p class="defect-desc">{{ defect.description || '暂无描述' }}</p>
      </div>

      <!-- 复现步骤 -->
      <div class="steps-section panel" v-if="defect.steps_to_reproduce">
        <h3 class="section-title">// 复现步骤</h3>
        <pre class="steps-content">{{ defect.steps_to_reproduce }}</pre>
      </div>

      <!-- 期望/实际结果 -->
      <div class="results-section panel">
        <h3 class="section-title">// 预期 vs 实际</h3>
        <div class="result-grid">
          <div class="result-item">
            <div class="result-label">期望结果</div>
            <pre class="result-content">{{ defect.expected_result || '-' }}</pre>
          </div>
          <div class="result-item">
            <div class="result-label">实际结果</div>
            <pre class="result-content">{{ defect.actual_result || '-' }}</pre>
          </div>
        </div>
      </div>

      <!-- 解决方案 -->
      <div class="resolution-section panel" v-if="defect.resolution">
        <h3 class="section-title">// 解决方案</h3>
        <pre class="resolution-content">{{ defect.resolution }}</pre>
      </div>

      <!-- 状态流转 -->
      <div class="status-flow-section panel">
        <h3 class="section-title">// 状态流转</h3>
        <div class="status-buttons">
          <button v-if="defect.status === 'open'" class="btn" @click="changeStatus('in_progress')">开始处理</button>
          <button v-if="defect.status === 'in_progress'" class="btn" @click="changeStatus('resolved')">标记已解决</button>
          <button v-if="defect.status === 'resolved'" class="btn" @click="changeStatus('closed')">关闭缺陷</button>
          <button v-if="['resolved', 'closed'].includes(defect.status)" class="btn" @click="changeStatus('reopened')">重新打开</button>
        </div>
      </div>

      <!-- 评论 -->
      <div class="comments-section panel">
        <h3 class="section-title">// 评论 ({{ comments.length }})</h3>
        <div class="comments-list">
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <div class="comment-header">
              <span class="comment-author">{{ c.author }}</span>
              <span class="comment-time">{{ formatTime(c.created_at) }}</span>
            </div>
            <div class="comment-body">{{ c.content }}</div>
          </div>
          <div v-if="comments.length === 0" class="empty-tip">// 暂无评论</div>
        </div>
        <div class="add-comment">
          <textarea v-model="newComment" placeholder="添加评论..." rows="3" class="cyber-input"></textarea>
          <button class="btn primary" @click="submitComment" :disabled="!newComment.trim()">发送</button>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="empty-detail">
    <span class="glitch">// 加载中...</span>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { defectApi } from '../../api/defect'

const props = defineProps({ defectId: Number })
const emit = defineEmits(['close', 'updated'])

const defect = ref(null)
const comments = ref([])
const editing = ref(false)
const newComment = ref('')
const form = ref({})

async function loadDefect() {
  const res = await defectApi.get(props.defectId)
  defect.value = res.data.defect
  comments.value = res.data.comments || []
  form.value = { ...defect.value }
}

watch(() => props.defectId, loadDefect, { immediate: true })

function severityText(s) {
  return { critical: '紧急', high: '高', medium: '中', low: '低' }[s] || s
}
function priorityText(p) {
  return { urgent: '紧急', high: '高', medium: '中', low: '低' }[p] || p
}
function statusText(s) {
  return { open: '待处理', in_progress: '处理中', resolved: '已解决', closed: '已关闭', reopened: '重新打开' }[s] || s
}
function defectTypeText(t) {
  return { functional: '功能', performance: '性能', security: '安全', UI: 'UI', compatibility: '兼容性' }[t] || t || '-'
}

function formatTime(ts) {
  if (!ts) return '-'
  return new Date(ts).toLocaleString('zh-CN', { hour12: false })
}

async function saveEdit() {
  const res = await defectApi.update(props.defectId, form.value)
  defect.value = res.data
  editing.value = false
  emit('updated')
}

async function changeStatus(status) {
  const res = await defectApi.update(props.defectId, { status })
  defect.value = res.data
  emit('updated')
}

async function submitComment() {
  if (!newComment.value.trim()) return
  const res = await defectApi.addComment(props.defectId, {
    content: newComment.value,
    author: '开发者',
  })
  comments.value.push(res.data)
  newComment.value = ''
}
</script>

<style scoped>
.defect-detail { padding: 16px; }
.detail-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px; gap: 16px;
}
.header-left { display: flex; align-items: center; gap: 16px; flex: 1; }
.defect-title {
  font-family: var(--font-title); font-size: 15px; font-weight: 700;
  color: var(--neon-cyan); letter-spacing: 1px;
}
.header-actions { display: flex; align-items: center; gap: 12px; }
.detail-body { display: flex; flex-direction: column; gap: 16px; }
.panel { padding: 16px; }
.section-title {
  font-family: var(--font-title); font-size: 12px; font-weight: 600;
  letter-spacing: 2px; color: var(--neon-cyan); margin: 0 0 12px 0;
}
.info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-label { font-size: 10px; color: var(--text-secondary); letter-spacing: 1px; font-family: var(--font-title); }
.severity-badge, .priority-badge, .status-badge {
  font-family: var(--font-title); font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 3px;
}
.sev-critical { background: rgba(255,0,0,0.2); color: #f00; border: 1px solid #f00; }
.sev-high { background: rgba(255,165,0,0.2); color: #ffa500; border: 1px solid #ffa500; }
.sev-medium { background: rgba(255,255,0,0.2); color: #ff0; border: 1px solid #ff0; }
.sev-low { background: rgba(0,255,0,0.2); color: var(--neon-green); border: 1px solid var(--neon-green); }
.pri-urgent { background: rgba(255,0,0,0.2); color: #f00; border: 1px solid #f00; }
.pri-high { background: rgba(255,165,0,0.2); color: #ffa500; border: 1px solid #ffa500; }
.pri-medium { background: rgba(255,255,0,0.2); color: #ff0; border: 1px solid #ff0; }
.pri-low { background: rgba(0,255,0,0.2); color: var(--neon-green); border: 1px solid var(--neon-green); }
.status-open { background: rgba(255,0,0,0.2); color: #f00; border: 1px solid #f00; }
.status-in_progress { background: rgba(255,165,0,0.2); color: #ffa500; border: 1px solid #ffa500; }
.status-resolved { background: rgba(0,255,0,0.2); color: var(--neon-green); border: 1px solid var(--neon-green); }
.status-closed { background: rgba(128,128,128,0.2); color: #888; border: 1px solid #888; }
.status-reopened { background: rgba(255,0,255,0.2); color: var(--neon-magenta); border: 1px solid var(--neon-magenta); }
.defect-desc { color: var(--text-primary); font-size: 13px; line-height: 1.6; white-space: pre-wrap; }
.steps-content, .result-content, .resolution-content {
  background: var(--bg-secondary); padding: 12px; border-radius: 4px;
  font-family: var(--font-mono); font-size: 12px; color: var(--neon-cyan); white-space: pre-wrap;
}
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.result-label { font-size: 11px; color: var(--text-secondary); font-family: var(--font-title); margin-bottom: 6px; }
.status-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.comments-list { margin-bottom: 12px; }
.comment-item { padding: 10px 0; border-bottom: 1px solid var(--border-default); }
.comment-header { display: flex; gap: 12px; margin-bottom: 6px; }
.comment-author { font-family: var(--font-title); font-size: 11px; font-weight: 600; color: var(--neon-cyan); }
.comment-time { font-size: 10px; color: var(--text-secondary); }
.comment-body { font-size: 13px; color: var(--text-primary); line-height: 1.5; white-space: pre-wrap; }
.add-comment { display: flex; flex-direction: column; gap: 8px; }
.cyber-input {
  width: 100%; padding: 10px 12px; background: var(--bg-secondary);
  border: 1px solid var(--border-default); color: var(--neon-cyan);
  font-family: var(--font-mono); font-size: 12px; outline: none; resize: vertical; box-sizing: border-box;
}
.empty-tip { color: var(--text-secondary); font-family: var(--font-mono); font-size: 12px; padding: 16px 0; }
.glich { animation: glitch 0.5s infinite; }
.edit-form .form-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.edit-form .form-group { display: flex; flex-direction: column; gap: 6px; }
.edit-form .form-group label { font-size: 10px; color: var(--text-secondary); font-family: var(--font-title); }
.edit-form .form-group input, .edit-form .form-group select {
  padding: 8px 10px; background: var(--bg-secondary); border: 1px solid var(--border-default);
  color: var(--neon-cyan); font-family: var(--font-mono); font-size: 12px; outline: none;
}
.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 12px; }
</style>
