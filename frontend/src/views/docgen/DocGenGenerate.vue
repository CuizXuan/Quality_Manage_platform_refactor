<template>
  <div class="docgen-generate-page page-shell page-shell--tech-grid">
    <!-- 页面标题区 -->
    <header class="docgen-generate-page__header">
      <div>
        <h1>生成文档</h1>
        <p>需求文档 · 数据库设计 · 接口设计 一站式生成</p>
      </div>
    </header>

    <!-- 生成区 -->
    <section class="docgen-generate-page__body">
      <div class="generate-area">
        <el-tabs v-model="genTab" tab-position="left" class="gen-sub-tabs">
          <!-- 需求文档生成 -->
          <el-tab-pane label="需求文档" name="requirement">
            <div class="gen-form">
              <el-form label-width="120px" class="gen-form__inner">
                <el-form-item label="数据源文件">
                  <div class="file-select">
                    <el-select v-model="reqForm.source_file_path" placeholder="选择文件" filterable class="form-select" @focus="loadUploads">
                      <el-option v-for="f in uploadFiles.filter(u => u.name.endsWith('.docx'))" :key="f.name" :label="f.name" :value="f.name" />
                    </el-select>
                    <el-upload :auto-upload="false" :limit="1" accept=".docx" :on-change="(file) => handleFileUpload(file, 'req')">
                      <el-button type="primary">上传</el-button>
                    </el-upload>
                  </div>
                </el-form-item>
                <el-form-item label="规则">
                  <el-select v-model="reqForm.rule_ids" multiple placeholder="选择规则（可选）" class="form-select">
                    <el-option v-for="r in docgenStore.rules" :key="r.id" :label="r.name" :value="r.id" />
                  </el-select>
                </el-form-item>
                <el-form-item label="模板">
                  <el-select v-model="reqForm.template_id" placeholder="选择模板（可选）" clearable class="form-select">
                    <el-option v-for="t in docgenStore.templates" :key="t.id" :label="t.name" :value="t.id" />
                  </el-select>
                </el-form-item>
                <el-form-item label="输出文件名">
                  <el-input v-model="reqForm.output_filename" placeholder="需求设计文档.docx" />
                </el-form-item>
                <el-form-item label="后台执行">
                  <el-switch v-model="useAsyncMode" />
                  <span class="form-hint">关闭则同步等待生成完成</span>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="docgenStore.generationLoading" @click="handlePreviewRequirement">预览</el-button>
                  <el-button type="success" :loading="docgenStore.generationLoading" @click="handleGenerateRequirement">生成</el-button>
                </el-form-item>
              </el-form>

              <div v-if="reqPreview" class="preview-result">
                <div class="preview-title">预览结果</div>
                <div class="preview-stat">共 {{ reqPreview.total_leaves }} 个叶子节点</div>
                <div class="preview-platforms">平台：{{ reqPreview.platforms.join('、') }}</div>
                <div v-for="(groups, section) in reqPreview.sections" :key="section" class="preview-section">
                  <div class="preview-section-name">{{ section }}</div>
                  <div class="preview-groups">{{ groups.join('、') }}</div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 数据库设计生成 -->
          <el-tab-pane label="数据库设计" name="database">
            <div class="gen-form">
              <el-form label-width="120px" class="gen-form__inner">
                <el-form-item label="数据库类型">
                  <el-select v-model="dbForm.db_type" class="form-select">
                    <el-option label="SQLite" value="sqlite" />
                  </el-select>
                </el-form-item>
                <el-form-item label="SQLite 文件">
                  <div class="file-select">
                    <el-select v-model="dbForm.file_path" placeholder="选择文件" filterable class="form-select" @focus="loadUploads">
                      <el-option v-for="f in uploadFiles.filter(u => u.name.endsWith('.db'))" :key="f.name" :label="f.name" :value="f.name" />
                    </el-select>
                    <el-upload :auto-upload="false" :limit="1" accept=".db" :on-change="(file) => handleFileUpload(file, 'db')">
                      <el-button type="primary">上传</el-button>
                    </el-upload>
                  </div>
                </el-form-item>
                <el-form-item label="输出文件名">
                  <el-input v-model="dbForm.output_filename" placeholder="数据库设计文档.docx" />
                </el-form-item>
                <el-form-item label="后台执行">
                  <el-switch v-model="useAsyncMode" />
                  <span class="form-hint">关闭则同步等待生成完成</span>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="docgenStore.generationLoading" @click="handlePreviewDatabase">预览</el-button>
                  <el-button type="success" :loading="docgenStore.generationLoading" @click="handleGenerateDatabase">生成</el-button>
                </el-form-item>
              </el-form>

              <div v-if="dbPreview" class="preview-result">
                <div class="preview-title">预览结果</div>
                <div class="preview-stat">共 {{ dbPreview.total_tables }} 张数据表</div>
                <el-table :data="dbPreview.tables" size="small">
                  <el-table-column prop="name" label="表名" />
                  <el-table-column prop="column_count" label="字段数" width="80" />
                  <el-table-column prop="index_count" label="索引数" width="80" />
                </el-table>
              </div>
            </div>
          </el-tab-pane>

          <!-- API 设计生成 -->
          <el-tab-pane label="接口设计" name="api">
            <div class="gen-form">
              <el-form label-width="120px" class="gen-form__inner">
                <el-form-item label="数据来源">
                  <el-select v-model="apiForm.source_type" class="form-select">
                    <el-option label="当前系统" value="system" />
                    <el-option label="URL" value="url" />
                    <el-option label="本地文件" value="file" />
                  </el-select>
                </el-form-item>
                <el-form-item v-if="apiForm.source_type === 'url'" label="OpenAPI URL">
                  <el-input v-model="apiForm.openapi_url" placeholder="https://petstore.swagger.io/v2/swagger.json" />
                </el-form-item>
                <el-form-item v-if="apiForm.source_type === 'file'" label="OpenAPI 文件">
                  <div class="file-select">
                    <el-select v-model="apiForm.openapi_file_path" placeholder="选择文件" filterable class="form-select" @focus="loadUploads">
                      <el-option v-for="f in uploadFiles.filter(u => u.name.endsWith('.json'))" :key="f.name" :label="f.name" :value="f.name" />
                    </el-select>
                    <el-upload :auto-upload="false" :limit="1" accept=".json" :on-change="(file) => handleFileUpload(file, 'api')">
                      <el-button type="primary">上传</el-button>
                    </el-upload>
                  </div>
                </el-form-item>
                <el-form-item label="输出格式">
                  <el-select v-model="apiForm.output_format" class="form-select">
                    <el-option label="Markdown" value="markdown" />
                  </el-select>
                </el-form-item>
                <el-form-item label="输出文件名">
                  <el-input v-model="apiForm.output_filename" placeholder="接口设计文档.md" />
                </el-form-item>
                <el-form-item label="后台执行">
                  <el-switch v-model="useAsyncMode" />
                  <span class="form-hint">关闭则同步等待生成完成</span>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="docgenStore.generationLoading" @click="handlePreviewApi">预览</el-button>
                  <el-button type="success" :loading="docgenStore.generationLoading" @click="handleGenerateApi">生成</el-button>
                </el-form-item>
              </el-form>

              <div v-if="apiPreview" class="preview-result">
                <div class="preview-title">预览结果</div>
                <div class="preview-stat">共 {{ apiPreview.total_endpoints }} 个接口</div>
                <div class="preview-tags">标签：{{ apiPreview.tags.join('、') }}</div>
                <el-table :data="apiPreview.endpoints" size="small" max-height="300">
                  <el-table-column prop="method" label="方法" width="70" />
                  <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
                  <el-table-column prop="summary" label="描述" min-width="160" show-overflow-tooltip />
                  <el-table-column prop="tag" label="标签" width="100" />
                  <el-table-column prop="param_count" label="参数数" width="70" />
                </el-table>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useDocgenStore } from '@/stores/docgenStore'
import { docgenApi } from '@/api/docgen'

const router = useRouter()
const docgenStore = useDocgenStore()

const genTab = ref('requirement')

const reqForm = reactive({
  source_file_path: '',
  rule_ids: [],
  template_id: null,
  output_filename: '',
})
const reqPreview = ref(null)
const useAsyncMode = ref(true)

const dbForm = reactive({
  db_type: 'sqlite',
  file_path: '',
  output_filename: '',
})
const dbPreview = ref(null)

const apiForm = reactive({
  source_type: 'system',
  openapi_url: '',
  openapi_file_path: '',
  output_format: 'markdown',
  output_filename: '',
})
const apiPreview = ref(null)
const uploadFiles = ref([])

onMounted(() => {
  docgenStore.fetchRules({ page: 1 })
  docgenStore.fetchTemplates({ page: 1 })
  loadUploads()
})

async function loadUploads() {
  try {
    const res = await docgenApi.listUploads()
    uploadFiles.value = res.data || []
  } catch {
    // ignore
  }
}

async function handleFileUpload(file, type) {
  try {
    const res = await docgenApi.uploadFile(file.raw)
    const filename = res.data?.path ? res.data.path.split(/[/\\]/).pop() : res.data?.name || file.name
    if (type === 'req') {
      reqForm.source_file_path = filename
    } else if (type === 'db') {
      dbForm.file_path = filename
    } else if (type === 'api') {
      apiForm.openapi_file_path = filename
    }
    ElMessage.success('上传成功')
    loadUploads()
  } catch (err) {
    ElMessage.error(err.message || '上传失败')
  }
}

async function handlePreviewRequirement() {
  if (!reqForm.source_file_path) {
    ElMessage.warning('请填写数据源文件路径')
    return
  }
  try {
    reqPreview.value = await docgenStore.previewRequirement(reqForm)
    ElMessage.success('预览成功')
  } catch (err) {
    ElMessage.error(err.message || '预览失败')
  }
}

async function handleGenerateRequirement() {
  if (!reqForm.source_file_path) {
    ElMessage.warning('请填写数据源文件路径')
    return
  }
  try {
    const action = useAsyncMode.value ? 'generateRequirementAsync' : 'generateRequirement'
    const task = await docgenStore[action](reqForm)
    ElMessage.success('任务已创建' + (useAsyncMode.value ? '，后台执行中' : ''))
    router.push('/docgen/tasks')
  } catch (err) {
    ElMessage.error(err.message || '生成失败')
  }
}

async function handlePreviewDatabase() {
  if (!dbForm.file_path) {
    ElMessage.warning('请填写 SQLite 文件路径')
    return
  }
  try {
    dbPreview.value = await docgenStore.previewDatabase(dbForm)
    ElMessage.success('预览成功')
  } catch (err) {
    ElMessage.error(err.message || '预览失败')
  }
}

async function handleGenerateDatabase() {
  if (!dbForm.file_path) {
    ElMessage.warning('请填写 SQLite 文件路径')
    return
  }
  try {
    const action = useAsyncMode.value ? 'generateDatabaseAsync' : 'generateDatabase'
    const task = await docgenStore[action](dbForm)
    ElMessage.success('任务已创建' + (useAsyncMode.value ? '，后台执行中' : ''))
    router.push('/docgen/tasks')
  } catch (err) {
    ElMessage.error(err.message || '生成失败')
  }
}

async function handlePreviewApi() {
  if (apiForm.source_type === 'url' && !apiForm.openapi_url) {
    ElMessage.warning('请填写 OpenAPI URL')
    return
  }
  if (apiForm.source_type === 'file' && !apiForm.openapi_file_path) {
    ElMessage.warning('请填写 OpenAPI 文件路径')
    return
  }
  try {
    apiPreview.value = await docgenStore.previewApi(apiForm)
    ElMessage.success('预览成功')
  } catch (err) {
    ElMessage.error(err.message || '预览失败')
  }
}

async function handleGenerateApi() {
  if (apiForm.source_type === 'url' && !apiForm.openapi_url) {
    ElMessage.warning('请填写 OpenAPI URL')
    return
  }
  if (apiForm.source_type === 'file' && !apiForm.openapi_file_path) {
    ElMessage.warning('请填写 OpenAPI 文件路径')
    return
  }
  try {
    const action = useAsyncMode.value ? 'generateApiAsync' : 'generateApi'
    const task = await docgenStore[action](apiForm)
    ElMessage.success('任务已创建' + (useAsyncMode.value ? '，后台执行中' : ''))
    router.push('/docgen/tasks')
  } catch (err) {
    ElMessage.error(err.message || '生成失败')
  }
}
</script>

<style scoped>
.docgen-generate-page {
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 10px;
}

.docgen-generate-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  padding: 14px 16px;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
}

.docgen-generate-page__header h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.docgen-generate-page__header p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.docgen-generate-page__body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
  padding: 16px;
  overflow: hidden;
}

.generate-area {
  height: 100%;
  overflow: hidden;
}

.gen-form {
  height: 100%;
  overflow: auto;
  padding: 4px 0;
}

.gen-form__inner {
  max-width: 600px;
}

.gen-form__inner :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  line-height: 34px;
}

.file-select {
  display: flex;
  gap: 8px;
  align-items: center;
}

.file-select .el-select {
  width: 280px;
  flex: none;
}

.form-select {
  width: 100%;
}

.form-hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--text-secondary);
}

.preview-result {
  margin-top: 16px;
  padding: 16px;
  border-radius: var(--border-radius-base);
  border: 1px solid var(--border-color);
  background: var(--bg-page);
  max-width: 600px;
}

.preview-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.preview-stat {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.preview-platforms,
.preview-tags {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.preview-section {
  margin-bottom: 8px;
}

.preview-section-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.preview-groups {
  font-size: 12px;
  color: var(--text-secondary);
  padding-left: 12px;
}
</style>