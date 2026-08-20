<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { subjectApi, knowledgeApi, knowledgeImportApi } from "@/api"
import type { Subject, KnowledgePoint } from "@/types"
import { ElMessage, ElMessageBox } from "element-plus"
import { Plus, Edit, Delete } from "@element-plus/icons-vue"

const subjects = ref<Subject[]>([])
const selectedSubjectId = ref("")
const treeData = ref<any[]>([])
const flatList = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref("")
const form = ref({ name: "", description: "", parent_id: "" as string | undefined })
const parentName = ref("")

async function loadSubjects() {
  const r = await subjectApi.list()
  subjects.value = r.data as any
  if (subjects.value.length > 0 && !selectedSubjectId.value) {
    selectedSubjectId.value = subjects.value[0].id
    loadKnowledgePoints()
  }
}

async function loadKnowledgePoints() {
  if (!selectedSubjectId.value) return
  loading.value = true
  try {
    const [treeRes, flatRes] = await Promise.all([
      knowledgeApi.getTree(selectedSubjectId.value),
      knowledgeApi.list(selectedSubjectId.value),
    ])
    treeData.value = treeRes.data
    flatList.value = flatRes.data
  } catch {
    ElMessage.error("加载知识点失败")
  } finally {
    loading.value = false
  }
}

function openCreate(parentId?: string) {
  editingId.value = ""
  form.value = { name: "", description: "", parent_id: parentId }
  const parent = flatList.value.find((k: any) => k.id === parentId)
  parentName.value = parent ? parent.name : "（顶层）"
  dialogVisible.value = true
}

function openEdit(kp: any) {
  editingId.value = kp.id
  form.value = { name: kp.name, description: kp.description, parent_id: kp.parent_id }
  const parent = flatList.value.find((k: any) => k.id === kp.parent_id)
  parentName.value = parent ? parent.name : "（顶层）"
  dialogVisible.value = true
}

async function save() {
  if (!form.value.name) {
    ElMessage.error("请输入知识点名称")
    return
  }
  try {
    if (editingId.value) {
      await knowledgeApi.update(editingId.value, form.value)
      ElMessage.success("更新成功")
    } else {
      await knowledgeApi.create({
        subject_id: selectedSubjectId.value,
        name: form.value.name,
        description: form.value.description,
        parent_id: form.value.parent_id,
      })
      ElMessage.success("创建成功")
    }
    dialogVisible.value = false
    await loadKnowledgePoints()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || "操作失败")
  }
}

async function remove(id: string, name: string) {
  await ElMessageBox.confirm(`确定删除知识点「${name}」及其下级知识点？`)
  await knowledgeApi.delete(id)
  ElMessage.success("已删除")
  await loadKnowledgePoints()
}

function renderTree(nodes: any[], level = 0): any[] {
  const result: any[] = []
  for (const node of nodes) {
    result.push({ ...node, _level: level })
    if (node.children?.length) {
      result.push(...renderTree(node.children, level + 1))
    }
  }
  return result
}

const flatTree = computed(() => renderTree(treeData.value))

// ===== 智能导入 =====
const importDialog = ref(false)
const importMode = ref("text")
const importSourceName = ref("")
const importTextContent = ref("")
const previewItems = ref<any[]>([])
const previewMeta = ref({ item_count: 0, exists_count: 0, duplicate_count: 0 })
const importLoading = ref(false)
const sourceDialog = ref(false)
const sources = ref<any[]>([])
const importFileName = ref("")

function openImportDialog() {
  importDialog.value = true
  importMode.value = "text"
  importSourceName.value = ""
  importTextContent.value = ""
  importFileName.value = ""
  previewItems.value = []
  previewMeta.value = { item_count: 0, exists_count: 0, duplicate_count: 0 }
}

async function onImportFile(file: File) {
  if (!file || !selectedSubjectId.value) return
  importFileName.value = file.name
  importLoading.value = true
  try {
    const res = importMode.value === "ai"
      ? await knowledgeImportApi.importAi(selectedSubjectId.value, file, importSourceName.value)
      : await knowledgeImportApi.importExcel(selectedSubjectId.value, file, importSourceName.value)
    applyPreview(res.data)
    ElMessage.success("解析完成，请核对预览后确认导入")
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || "解析失败")
  } finally {
    importLoading.value = false
  }
}

async function parseTextImport() {
  if (!importTextContent.value.trim()) {
    ElMessage.warning("请粘贴教材/课标目录文本")
    return
  }
  importLoading.value = true
  try {
    const res = await knowledgeImportApi.importText(selectedSubjectId.value, importTextContent.value, importSourceName.value)
    applyPreview(res.data)
    ElMessage.success("解析完成，请核对预览后确认导入")
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || "解析失败")
  } finally {
    importLoading.value = false
  }
}

function applyPreview(data: any) {
  previewItems.value = data.items || []
  previewMeta.value = {
    item_count: data.item_count || 0,
    exists_count: data.exists_count || 0,
    duplicate_count: data.duplicate_count || 0,
  }
}

async function commitImport() {
  if (!previewItems.value.length) return
  importLoading.value = true
  try {
    const res = await knowledgeImportApi.commitPreview(
      selectedSubjectId.value,
      previewItems.value,
      importSourceName.value,
      importMode.value === "excel" ? "excel" : importMode.value === "ai" ? "textbook" : "curriculum",
      importMode.value === "ai" ? "ai" : importMode.value === "excel" ? "template" : "rules",
    )
    ElMessage.success(res.data?.message || "导入成功")
    importDialog.value = false
    await loadKnowledgePoints()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || "导入失败")
  } finally {
    importLoading.value = false
  }
}

function renderPreviewTree(nodes: any[], level = 0): any[] {
  const result: any[] = []
  for (const node of nodes) {
    result.push({ ...node, _level: level })
    if (node.children?.length) {
      result.push(...renderPreviewTree(node.children, level + 1))
    }
  }
  return result
}

const flatPreview = computed(() => renderPreviewTree(previewItems.value))

async function openSourceDialog() {
  sourceDialog.value = true
  await loadSources()
}

async function loadSources() {
  try {
    const res = await knowledgeImportApi.listSources(selectedSubjectId.value || undefined)
    sources.value = res.data
  } catch { /* ignore */ }
}

async function removeSource(id: string) {
  await ElMessageBox.confirm("删除来源将同时删除该批次导入的知识点，确认？")
  try {
    await knowledgeImportApi.deleteSource(id)
    ElMessage.success("已删除")
    await loadSources()
    await loadKnowledgePoints()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || "删除失败")
  }
}

onMounted(loadSubjects)
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
          <span style="font-weight: 600">知识点库管理</span>
          <div style="display: flex; gap: 8px">
            <el-select
              v-model="selectedSubjectId"
              placeholder="选择科目"
              style="width: 180px"
              @change="loadKnowledgePoints"
            >
              <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
            <el-button type="primary" :icon="Plus" @click="openCreate()" :disabled="!selectedSubjectId">
              添加知识点
            </el-button>
            <el-button type="success" @click="openImportDialog" :disabled="!selectedSubjectId">智能导入</el-button>
            <el-button type="warning" plain @click="openSourceDialog" :disabled="!selectedSubjectId">来源管理</el-button>
          </div>
        </div>
      </template>

      <el-alert title="知识点按科目分类，可设置层级结构（上级→下级），用于考试命题细目表和知识点分析" type="info" show-icon :closable="false" style="margin-bottom: 12px" />

      <el-table :data="flatTree" v-loading="loading" stripe empty-text="暂无知识点，请先添加">
        <el-table-column label="知识点名称" min-width="300">
          <template #default="{ row }">
            <div :style="{ paddingLeft: row._level * 24 + 'px', display: 'flex', alignItems: 'center', gap: '6px' }">
              <el-icon v-if="row.children?.length" :size="16" color="#E6A23C"><FolderOpened /></el-icon>
              <el-icon v-else :size="14" color="#409EFF"><Document /></el-icon>
              <span :style="{ fontWeight: row._level === 0 ? 600 : 400 }">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Plus" @click="openCreate(row.id)">添加下级</el-button>
            <el-button size="small" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="remove(row.id, row.name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑知识点' : '添加知识点'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="上级知识点">
          <el-input :model-value="parentName" disabled />
        </el-form-item>
        <el-form-item label="知识点名称">
          <el-input v-model="form.name" placeholder="如：函数定义域" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="可选描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialog" title="知识点智能导入" width="860px" top="6vh">
      <el-form label-width="80px">
        <el-form-item label="导入方式">
          <el-radio-group v-model="importMode">
            <el-radio-button label="text">目录文本</el-radio-button>
            <el-radio-button label="excel">Excel 模板</el-radio-button>
            <el-radio-button label="ai">AI 抽取</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="来源名称">
          <el-input v-model="importSourceName" placeholder="如：人教版必修第一册 / 2022课标" style="width: 300px" />
        </el-form-item>
        <el-form-item v-if="importMode === 'text'" label="目录文本">
          <el-input v-model="importTextContent" type="textarea" :rows="8"
            placeholder="粘贴教材/课标目录文本，如：&#10;第一章 集合&#10;一、集合的含义与表示&#10;1. 集合的概念&#10;（1）元素的特性" />
        </el-form-item>
        <el-form-item v-if="importMode !== 'text'" label="选择文件">
          <el-upload :show-file-list="false" :auto-upload="false" :on-change="(f: any) => onImportFile(f.raw)"
            :accept="importMode === 'ai' ? '.docx,.pdf,.txt,.md' : '.xlsx,.xls'">
            <el-button type="primary" plain>{{ importMode === 'ai' ? '选择 Word/PDF/文本' : '选择 Excel 文件' }}</el-button>
          </el-upload>
          <span style="margin-left: 12px; color: #909399">{{ importFileName }}</span>
          <div style="width: 100%; margin-top: 4px">
            <el-link v-if="importMode === 'excel'" type="primary" :href="knowledgeImportApi.templateUrl()" target="_blank" :underline="false">下载导入模板</el-link>
            <span v-if="importMode === 'ai'" style="color: #909399; font-size: 12px">未配置 LLM 时自动回退规则解析；扫描版 PDF 暂不支持（OCR 接口预留）</span>
          </div>
        </el-form-item>
        <el-form-item v-if="importMode === 'text'" label=" ">
          <el-button type="primary" :loading="importLoading" @click="parseTextImport">解析预览</el-button>
        </el-form-item>
      </el-form>

      <div v-if="previewItems.length" style="margin-bottom: 8px; color: #606266; font-size: 13px">
        共识别 <b>{{ previewMeta.item_count }}</b> 条知识点；
        与现有库同名 <b style="color: #E6A23C">{{ previewMeta.exists_count }}</b> 条（将合并）；
        批次内重复 <b style="color: #F56C6C">{{ previewMeta.duplicate_count }}</b> 条
      </div>
      <el-table v-if="previewItems.length" :data="flatPreview" stripe border size="small" max-height="320">
        <el-table-column label="知识点（按层级）" min-width="320">
          <template #default="{ row }">
            <div :style="{ paddingLeft: row._level * 22 + 'px', display: 'flex', alignItems: 'center', gap: '6px' }">
              <span :style="{ fontWeight: row._level === 0 ? 600 : 400 }">{{ row.name }}</span>
              <el-tag v-if="row.exists" size="small" type="warning">库中已有-合并</el-tag>
              <el-tag v-else-if="row.duplicate_in_batch" size="small" type="danger">批次重复</el-tag>
              <el-tag v-else size="small" type="success">新增</el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="importDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!previewItems.length" :loading="importLoading" @click="commitImport">确认导入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="sourceDialog" title="导入来源管理" width="640px">
      <el-table :data="sources" stripe border size="small" empty-text="暂无导入记录">
        <el-table-column prop="source_name" label="来源名称" min-width="160" />
        <el-table-column prop="source_type" label="类型" width="90" />
        <el-table-column prop="import_mode" label="模式" width="90" />
        <el-table-column prop="created_at" label="导入时间" width="170" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="removeSource(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>
