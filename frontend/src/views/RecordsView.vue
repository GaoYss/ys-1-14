<template>
  <section>
    <PageHeader eyebrow="Stock Records" title="入库出库记录">
      <button class="primary-btn" @click="submitRecord">登记</button>
    </PageHeader>

    <section class="form-panel">
      <div class="form-grid">
        <label>
          原料
          <select v-model.number="form.ingredientId">
            <option disabled :value="null">选择原料</option>
            <option v-for="item in ingredients" :key="item.id" :value="item.id">
              {{ item.name }} / 库存 {{ item.stock }} {{ item.unit }}
            </option>
          </select>
        </label>
        <label>
          来源类型
          <select v-model="form.sourceType" @change="onSourceTypeChange">
            <option :value="null">请选择来源类型</option>
            <option v-for="opt in sourceTypes" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </label>
        <label>
          出入库类型
          <select v-model="form.recordType" :disabled="!recordTypeEditable">
            <option value="in">入库</option>
            <option value="out">出库</option>
          </select>
        </label>
        <label>
          数量
          <input v-model.number="form.quantity" type="number" min="1" />
        </label>
        <label>
          经办人
          <input v-model="form.operator" />
        </label>
        <label>
          {{ currentSourceLabel }}
          <input v-model="form.source" :placeholder="currentSourcePlaceholder" />
        </label>
        <label class="full-width">
          备注
          <input v-model="form.note" placeholder="选填，补充说明" />
        </label>
      </div>
      <p v-if="sourceTypeHint" class="hint-text">{{ sourceTypeHint }}</p>
    </section>

    <div class="toolbar">
      <select v-model="filterSourceType" @change="loadRecords">
        <option value="">全部来源</option>
        <option v-for="opt in sourceTypes" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <p v-if="error" class="error-text">{{ error }}</p>

    <DataTable :columns="columns" :rows="records">
      <template #recordType="{ row }">
        <StatusBadge
          :label="row.recordType === 'in' ? '入库' : '出库'"
          :variant="row.recordType === 'in' ? 'success' : 'warning'"
        />
      </template>
      <template #sourceTypeLabel="{ row }">
        <StatusBadge
          v-if="row.sourceTypeLabel"
          :label="row.sourceTypeLabel"
          :variant="sourceTypeVariant(row.sourceType)"
        />
        <span v-else class="text-muted">-</span>
      </template>
      <template #source="{ row }">
        <div class="source-cell">
          <div class="source-main">{{ row.source || '-' }}</div>
          <div v-if="row.note" class="source-note">{{ row.note }}</div>
        </div>
      </template>
      <template #quantity="{ row }">{{ row.quantity }} {{ row.unit }}</template>
      <template #createdAt="{ row }">{{ formatDateTime(row.createdAt) }}</template>
    </DataTable>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { inventoryApi } from '../api/inventory'
import { recordsApi } from '../api/records'
import DataTable from '../components/DataTable.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { formatDateTime } from '../utils/format'

const records = ref([])
const ingredients = ref([])
const sourceTypes = ref([])
const sourceTypeRules = ref({})
const filterSourceType = ref('')
const error = ref('')
const form = reactive({
  ingredientId: null,
  recordType: 'in',
  quantity: 1,
  operator: '系统管理员',
  sourceType: null,
  source: '',
  note: ''
})
const columns = [
  { key: 'createdAt', label: '时间' },
  { key: 'ingredientName', label: '原料' },
  { key: 'recordType', label: '类型' },
  { key: 'sourceTypeLabel', label: '来源类型' },
  { key: 'quantity', label: '数量' },
  { key: 'operator', label: '经办人' },
  { key: 'source', label: '来源详情' }
]

const currentRules = computed(() => {
  if (!form.sourceType || !sourceTypeRules.value[form.sourceType]) return null
  return sourceTypeRules.value[form.sourceType]
})

const recordTypeEditable = computed(() => {
  if (!currentRules.value) return true
  return currentRules.value.allowedRecordTypes.length > 1
})

const currentSourceLabel = computed(() => {
  return currentRules.value?.sourceLabel || '来源/用途'
})

const currentSourcePlaceholder = computed(() => {
  return currentRules.value?.sourcePlaceholder || '请输入来源信息'
})

const sourceTypeHint = computed(() => {
  if (!currentRules.value) return ''
  const types = currentRules.value.allowedRecordTypes
  if (types.length === 1) {
    return `提示：${form.sourceType === 'purchase' ? '采购入库' : form.sourceType === 'store_requisition' ? '门店领用' : '盘点调整'}仅支持${types[0] === 'in' ? '入库' : '出库'}操作`
  }
  return ''
})

function sourceTypeVariant(sourceType) {
  switch (sourceType) {
    case 'purchase': return 'info'
    case 'inventory_check': return 'warning'
    case 'store_requisition': return 'danger'
    default: return 'secondary'
  }
}

function onSourceTypeChange() {
  if (currentRules.value && currentRules.value.allowedRecordTypes.length === 1) {
    form.recordType = currentRules.value.allowedRecordTypes[0]
  }
}

async function loadRecords() {
  const params = {}
  if (filterSourceType.value) {
    params.sourceType = filterSourceType.value
  }
  const res = await recordsApi.list(params)
  records.value = res.data
}

async function loadOptions() {
  const [invRes, recRes] = await Promise.all([
    inventoryApi.options(),
    recordsApi.options()
  ])
  ingredients.value = invRes.data.ingredients
  sourceTypes.value = recRes.data.sourceTypes
  sourceTypeRules.value = recRes.data.sourceTypeRules
}

async function submitRecord() {
  error.value = ''
  try {
    const payload = { ...form }
    if (!payload.sourceType) {
      delete payload.sourceType
    }
    await recordsApi.create(payload)
    Object.assign(form, {
      ingredientId: null,
      recordType: 'in',
      quantity: 1,
      operator: '系统管理员',
      sourceType: null,
      source: '',
      note: ''
    })
    await Promise.all([loadRecords(), loadOptions()])
  } catch (err) {
    error.value = err.response?.data?.message || '登记失败'
  }
}

onMounted(async () => {
  await Promise.all([loadRecords(), loadOptions()])
})
</script>

<style scoped>
.full-width {
  grid-column: 1 / -1;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 20px 0 14px;
}

.toolbar select {
  padding: 8px 12px;
  border: 1px solid #d9dee4;
  border-radius: 6px;
  background: #fff;
  font-size: 14px;
}

.hint-text {
  margin: 12px 0 0;
  color: #64748b;
  font-size: 13px;
}

.source-cell {
  line-height: 1.4;
}

.source-main {
  color: #1e293b;
}

.source-note {
  color: #94a3b8;
  font-size: 12px;
  margin-top: 2px;
}

.text-muted {
  color: #cbd5e1;
}
</style>
