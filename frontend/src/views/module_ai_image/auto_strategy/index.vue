<!-- AI 24小时自动化生图策略 -->
<template>
  <div class="app-container">
    <!-- 内容区域 -->
    <el-card class="data-table">
      <template #header>
        <div class="card-header">
          <span>
            AI 24小时自动化生图策略列表
            <el-tooltip content="AI 24小时自动化生图策略列表">
              <QuestionFilled class="w-4 h-4 mx-1" />
            </el-tooltip>
          </span>
        </div>

        <!-- 搜索区域 -->
        <div v-show="visible" class="search-container">
          <el-form
            ref="queryFormRef"
            :model="queryFormData"
            label-suffix=":"
            :inline="true"
            @submit.prevent="handleQuery"
          >
            <el-form-item label="策略名称" prop="strategy_name">
              <el-input
                v-model="queryFormData.strategy_name"
                placeholder="请输入策略名称"
                clearable
              />
            </el-form-item>
            <el-form-item label="目标地点" prop="location">
              <el-input v-model="queryFormData.location" placeholder="请输入目标地点" clearable />
            </el-form-item>
            <el-form-item label="目标性别" prop="gender">
              <el-select
                v-model="queryFormData.gender"
                placeholder="请选择目标性别"
                clearable
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="item in genderOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="执行优先级" prop="priority">
              <el-input v-model="queryFormData.priority" placeholder="请输入执行优先级" clearable />
            </el-form-item>
            <el-form-item prop="status" label="状态">
              <el-select
                v-model="queryFormData.status"
                placeholder="请选择状态"
                style="width: 170px"
                clearable
              >
                <el-option value="0" label="启用" />
                <el-option value="1" label="停用" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="isExpand" prop="created_time" label="创建时间">
              <DatePicker
                v-model="createdDateRange"
                @update:model-value="handleCreatedDateRangeChange"
              />
            </el-form-item>
            <el-form-item v-if="isExpand" prop="updated_time" label="更新时间">
              <DatePicker
                v-model="updatedDateRange"
                @update:model-value="handleUpdatedDateRangeChange"
              />
            </el-form-item>
            <el-form-item v-if="isExpand" prop="created_id" label="创建人">
              <UserTableSelect
                v-model="queryFormData.created_id"
                @confirm-click="handleConfirm"
                @clear-click="handleQuery"
              />
            </el-form-item>
            <el-form-item v-if="isExpand" prop="updated_id" label="更新人">
              <UserTableSelect
                v-model="queryFormData.updated_id"
                @confirm-click="handleConfirm"
                @clear-click="handleQuery"
              />
            </el-form-item>
            <!-- 查询、重置、展开/收起按钮 -->
            <el-form-item>
              <el-button
                v-hasPerm="['module_ai_image:ai_image_auto_strategy:query']"
                type="primary"
                icon="search"
                @click="handleQuery"
              >
                查询
              </el-button>
              <el-button
                v-hasPerm="['module_ai_image:ai_image_auto_strategy:query']"
                icon="refresh"
                @click="handleResetQuery"
              >
                重置
              </el-button>
              <!-- 展开/收起 -->
              <template v-if="isExpandable">
                <el-link
                  class="ml-3"
                  type="primary"
                  underline="never"
                  @click="isExpand = !isExpand"
                >
                  {{ isExpand ? "收起" : "展开" }}
                  <el-icon>
                    <template v-if="isExpand">
                      <ArrowUp />
                    </template>
                    <template v-else>
                      <ArrowDown />
                    </template>
                  </el-icon>
                </el-link>
              </template>
            </el-form-item>
          </el-form>
        </div>
      </template>

      <!-- 功能区域 -->
      <div class="data-table__toolbar">
        <div class="data-table__toolbar--left">
          <el-row :gutter="10">
            <el-col :span="1.5">
              <el-button
                v-hasPerm="['module_ai_image:ai_image_auto_strategy:create']"
                type="success"
                icon="plus"
                @click="handleOpenDialog('create')"
              >
                新增
              </el-button>
            </el-col>
            <el-col :span="1.5">
              <el-button
                v-hasPerm="['module_ai_image:ai_image_auto_strategy:delete']"
                type="danger"
                icon="delete"
                :disabled="selectIds.length === 0"
                @click="handleDelete(selectIds)"
              >
                批量删除
              </el-button>
            </el-col>
            <el-col :span="1.5">
              <el-dropdown
                v-hasPerm="['module_ai_image:ai_image_auto_strategy:batch']"
                trigger="click"
              >
                <el-button type="default" :disabled="selectIds.length === 0" icon="ArrowDown">
                  更多
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :icon="Check" @click="handleMoreClick('0')">
                      批量启用
                    </el-dropdown-item>
                    <el-dropdown-item :icon="CircleClose" @click="handleMoreClick('1')">
                      批量停用
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </el-col>
          </el-row>
        </div>
        <div class="data-table__toolbar--right">
          <el-row :gutter="10">
            <el-col :span="1.5">
              <el-tooltip content="导入">
                <el-button
                  v-hasPerm="['module_ai_image:ai_image_auto_strategy:import']"
                  type="success"
                  icon="upload"
                  circle
                  @click="handleOpenImportDialog"
                />
              </el-tooltip>
            </el-col>
            <el-col :span="1.5">
              <el-tooltip content="导出">
                <el-button
                  v-hasPerm="['module_ai_image:ai_image_auto_strategy:export']"
                  type="warning"
                  icon="download"
                  circle
                  @click="handleOpenExportsModal"
                />
              </el-tooltip>
            </el-col>
            <el-col :span="1.5">
              <el-tooltip content="搜索显示/隐藏">
                <el-button
                  v-hasPerm="['*:*:*']"
                  type="info"
                  icon="search"
                  circle
                  @click="visible = !visible"
                />
              </el-tooltip>
            </el-col>
            <el-col :span="1.5">
              <el-tooltip content="刷新">
                <el-button
                  v-hasPerm="['module_ai_image:ai_image_auto_strategy:query']"
                  type="primary"
                  icon="refresh"
                  circle
                  @click="handleRefresh"
                />
              </el-tooltip>
            </el-col>
            <el-col :span="1.5">
              <el-popover placement="bottom" trigger="click">
                <template #reference>
                  <el-button type="danger" icon="operation" circle></el-button>
                </template>
                <el-scrollbar max-height="350px">
                  <template v-for="column in tableColumns" :key="column.prop">
                    <el-checkbox v-if="column.prop" v-model="column.show" :label="column.label" />
                  </template>
                </el-scrollbar>
              </el-popover>
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 表格区域：系统配置列表 -->
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="pageTableData"
        highlight-current-row
        class="data-table__content"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <template #empty>
          <el-empty :image-size="80" description="暂无数据" />
        </template>
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'selection')?.show"
          type="selection"
          min-width="55"
          align="center"
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'index')?.show"
          fixed
          label="序号"
          min-width="60"
        >
          <template #default="scope">
            {{ (queryFormData.page_no - 1) * queryFormData.page_size + scope.$index + 1 }}
          </template>
        </el-table-column>
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'strategy_name')?.show"
          label="策略名称"
          prop="strategy_name"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'location')?.show"
          label="目标地点"
          prop="location"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'gender')?.show"
          label="目标性别"
          prop="gender"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'age_min')?.show"
          label="年龄下限"
          prop="age_min"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'age_max')?.show"
          label="年龄上限"
          prop="age_max"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'daily_batch_limit')?.show"
          label="每天最多生成几个Batch"
          prop="daily_batch_limit"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'priority')?.show"
          label="执行优先级"
          prop="priority"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'status')?.show"
          label="状态"
          prop="status"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'status')?.show"
          label="状态"
          prop="status"
          min-width="140"
          show-overflow-tooltip
        >
          <template #default="scope">
            <el-tag :type="scope.row.status == '0' ? 'success' : 'info'">
              {{ scope.row.status == "0" ? "启用" : "停用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'created_time')?.show"
          label="创建时间"
          prop="created_time"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'updated_time')?.show"
          label="更新时间"
          prop="updated_time"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'created_id')?.show"
          label="创建人ID"
          prop="created_id"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'created_id')?.show"
          label="创建人ID"
          prop="created_id"
          min-width="140"
          show-overflow-tooltip
        >
          <template #default="scope">
            <el-tag>{{ scope.row.created_by?.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'updated_id')?.show"
          label="更新人ID"
          prop="updated_id"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'updated_id')?.show"
          label="更新人ID"
          prop="updated_id"
          min-width="140"
          show-overflow-tooltip
        >
          <template #default="scope">
            <el-tag>{{ scope.row.updated_by?.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'operation')?.show"
          fixed="right"
          label="操作"
          align="center"
          min-width="180"
        >
          <template #default="scope">
            <el-button
              v-hasPerm="['module_ai_image:ai_image_auto_strategy:detail']"
              type="info"
              size="small"
              link
              icon="document"
              @click="handleOpenDialog('detail', scope.row.id)"
            >
              详情
            </el-button>
            <el-button
              v-hasPerm="['module_ai_image:ai_image_auto_strategy:update']"
              type="primary"
              size="small"
              link
              icon="edit"
              @click="handleOpenDialog('update', scope.row.id)"
            >
              编辑
            </el-button>
            <el-button
              v-hasPerm="['module_ai_image:ai_image_auto_strategy:delete']"
              type="danger"
              size="small"
              link
              icon="delete"
              @click="handleDelete([scope.row.id])"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页区域 -->
      <template #footer>
        <pagination
          v-model:total="total"
          v-model:page="queryFormData.page_no"
          v-model:limit="queryFormData.page_size"
          @pagination="loadingData"
        />
      </template>
    </el-card>

    <!-- 弹窗区域 -->
    <el-dialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      @close="handleCloseDialog"
    >
      <!-- 详情 -->
      <template v-if="dialogVisible.type === 'detail'">
        <el-descriptions :column="4" border>
          <el-descriptions-item label="主键ID" :span="2">
            {{ detailFormData.id }}
          </el-descriptions-item>
          <el-descriptions-item label="策略名称" :span="2">
            {{ detailFormData.strategy_name }}
          </el-descriptions-item>
          <el-descriptions-item label="目标地点" :span="2">
            {{ detailFormData.location }}
          </el-descriptions-item>
          <el-descriptions-item label="目标性别" :span="2">
            {{ detailFormData.gender }}
          </el-descriptions-item>
          <el-descriptions-item label="年龄下限" :span="2">
            {{ detailFormData.age_min }}
          </el-descriptions-item>
          <el-descriptions-item label="年龄上限" :span="2">
            {{ detailFormData.age_max }}
          </el-descriptions-item>
          <el-descriptions-item label="每天最多生成几个Batch" :span="2">
            {{ detailFormData.daily_batch_limit }}
          </el-descriptions-item>
          <el-descriptions-item label="执行优先级" :span="2">
            {{ detailFormData.priority }}
          </el-descriptions-item>
          <el-descriptions-item label="状态" :span="2">
            <el-tag :type="detailFormData.status == '0' ? 'success' : 'danger'">
              {{ detailFormData.status == "0" ? "启用" : "停用" }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ detailFormData.created_time }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间" :span="2">
            {{ detailFormData.updated_time }}
          </el-descriptions-item>
          <el-descriptions-item label="创建人" :span="2">
            {{ detailFormData.created_by?.name }}
          </el-descriptions-item>
          <el-descriptions-item label="更新人" :span="2">
            {{ detailFormData.updated_by?.name }}
          </el-descriptions-item>
        </el-descriptions>
      </template>

      <!-- 新增、编辑表单 -->
      <template v-else>
        <el-form
          ref="dataFormRef"
          :model="formData"
          :rules="rules"
          label-suffix=":"
          label-width="auto"
          label-position="right"
        >
          <el-form-item label="策略名称" prop="strategy_name" :required="false">
            <el-input v-model="formData.strategy_name" placeholder="请输入策略名称" />
          </el-form-item>
          <el-form-item label="目标地点" prop="location" :required="false">
            <el-input v-model="formData.location" placeholder="请输入目标地点" />
          </el-form-item>
          <el-form-item label="背景描述策略" prop="background_strategy" :required="false">
            <div class="w-full flex flex-col gap-2" style="width: 100%">
              <el-input
                v-model="formData.background_strategy"
                type="textarea"
                :rows="4"
                placeholder="请输入背景描述策略，或使用下方 AI 工具生成 (如：微泛金光的斑驳暗墙，丁达尔光柱中清晰跃动的细腻微尘...)"
              />

              <div style="display: flex; gap: 10px; align-items: center; margin-top: 5px">
                <el-button
                  type="primary"
                  plain
                  :loading="isGeneratingBg"
                  @click="generateBgFromLocation"
                >
                  <el-icon class="mr-1"><Location /></el-icon>
                  基于地点智能生成
                </el-button>

                <el-upload
                  action="#"
                  :auto-upload="false"
                  :show-file-list="false"
                  :on-change="handleBgImageUpload"
                  accept="image/jpeg,image/png,image/webp"
                  style="display: inline-block"
                >
                  <el-button type="success" plain :loading="isReversingBg">
                    <el-icon class="mr-1"><Picture /></el-icon>
                    上传参考图智能反推
                  </el-button>
                </el-upload>
              </div>
              <div class="el-form-item-msg text-xs text-gray-400 mt-1">
                提示: 若无参考图，可先填写【目标地点】后点击智能生成。传图反推会覆盖当前文本。
              </div>
            </div>
          </el-form-item>
          <el-form-item label="关联主题" prop="theme_ids" :required="true">
            <el-select
              v-model="formData.theme_ids"
              placeholder="请选择要自动生成的主题（可多选）"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              style="width: 100%"
              @focus="loadThemes(formData.gender)"
            >
              <el-option
                v-for="item in themeOptions"
                :key="item.id"
                :label="`${item.theme_name} (${item.gender})`"
                :value="item.id!"
              >
                <span style="float: left">{{ item.theme_name }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">{{ item.gender }}</span>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="目标性别" prop="gender" :required="true">
            <el-select
              v-model="formData.gender"
              placeholder="请选择目标性别"
              clearable
              style="width: 100%"
            >
              <el-option
                v-for="item in genderOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="年龄下限" prop="age_min" :required="false">
            <el-input v-model="formData.age_min" placeholder="请输入年龄下限" />
          </el-form-item>
          <el-form-item label="年龄上限" prop="age_max" :required="false">
            <el-input v-model="formData.age_max" placeholder="请输入年龄上限" />
          </el-form-item>
          <el-form-item label="每天最多生成几个Batch" prop="daily_batch_limit" :required="false">
            <el-input
              v-model="formData.daily_batch_limit"
              placeholder="请输入每天最多生成几个Batch"
            />
          </el-form-item>
          <el-form-item label="执行优先级" prop="priority" :required="false">
            <el-input v-model="formData.priority" placeholder="请输入执行优先级" />
          </el-form-item>
          <el-form-item label="状态" prop="status" :required="true">
            <el-radio-group v-model="formData.status">
              <el-radio value="0">启用</el-radio>
              <el-radio value="1">停用</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </template>

      <template #footer>
        <div class="dialog-footer">
          <!-- 详情弹窗不需要确定按钮的提交逻辑 -->
          <el-button @click="handleCloseDialog">取消</el-button>
          <el-button v-if="dialogVisible.type !== 'detail'" type="primary" @click="handleSubmit">
            确定
          </el-button>
          <el-button v-else type="primary" @click="handleCloseDialog">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <ImportModal
      v-model="importDialogVisible"
      :content-config="curdContentConfig"
      :loading="uploadLoading"
      @upload="handleUpload"
    />

    <!-- 导出弹窗 -->
    <ExportModal
      v-model="exportsDialogVisible"
      :content-config="curdContentConfig"
      :query-params="queryFormData"
      :page-data="pageTableData"
      :selection-data="selectionRows"
    />
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "AiImageAutoStrategy",
  inheritAttrs: false,
});

import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { QuestionFilled, ArrowUp, ArrowDown, Check, CircleClose } from "@element-plus/icons-vue";
import { formatToDateTime } from "@/utils/dateUtil";
import { useDictStore } from "@/store";
import { ResultEnum } from "@/enums/api/result.enum";
import DatePicker from "@/components/DatePicker/index.vue";
import type { IContentConfig } from "@/components/CURD/types";
import ImportModal from "@/components/CURD/ImportModal.vue";
import ExportModal from "@/components/CURD/ExportModal.vue";
import AiImageAutoStrategyAPI, {
  AiImageAutoStrategyPageQuery,
  AiImageAutoStrategyTable,
  AiImageAutoStrategyForm,
} from "@/api/module_ai_image/auto_strategy";
import AiStyleThemeAPI, { AiStyleThemeTable } from "@/api/module_ai_image/style_theme";
import type { UploadFile } from "element-plus";
import { FileAPI } from "@/api/module_common/file";
import FissionTaskAPI from "@/api/module_ai_image/task";

const isGeneratingBg = ref(false);
const isReversingBg = ref(false);

const visible = ref(true);
const queryFormRef = ref();
const dataFormRef = ref();
const total = ref(0);
const selectIds = ref<number[]>([]);
const selectionRows = ref<AiImageAutoStrategyTable[]>([]);
const loading = ref(false);
const isExpand = ref(false);
const isExpandable = ref(true);

// 🚀 定义目标性别的静态选项
const genderOptions = [
  { label: "女孩", value: "女孩" },
  { label: "男孩", value: "男孩" },
  { label: "年轻女性", value: "年轻女性" },
  { label: "年轻男性", value: "年轻男性" },
  { label: "中年女性", value: "中年女性" },
  { label: "中年男性", value: "中年男性" },
  { label: "老年女性", value: "老年女性" },
  { label: "老年男性", value: "老年男性" },
];

const ageMapping: Record<string, { min: number; max: number }> = {
  女孩: { min: 10, max: 15 },
  男孩: { min: 10, max: 15 },
  年轻女性: { min: 20, max: 30 },
  年轻男性: { min: 20, max: 30 },
  中年女性: { min: 35, max: 45 },
  中年男性: { min: 35, max: 45 },
  老年女性: { min: 50, max: 60 },
  老年男性: { min: 50, max: 60 },
};
// 分页表单
const pageTableData = ref<AiImageAutoStrategyTable[]>([]);

// 定义主题列表存储
const themeOptions = ref<AiStyleThemeTable[]>([]);

// 加载主题的方法
const loadThemes = async (gender?: string) => {
  // query 可以传性别，实现：选了“女”就只显示“年轻女性”的主题
  const { data } = await AiStyleThemeAPI.listAiStyleTheme({
    page_size: 1000,
    page_no: 1,
    gender: gender || "",
  });
  console.log("主题列表:", data);
  const items = data.data.items;
  themeOptions.value = items;
};

// 表格列配置
const tableColumns = ref([
  { prop: "selection", label: "选择框", show: true },
  { prop: "index", label: "序号", show: true },
  { prop: "strategy_name", label: "策略名称", show: true },
  { prop: "location", label: "目标地点", show: true },
  { prop: "gender", label: "目标性别", show: true },
  { prop: "age_min", label: "年龄下限", show: true },
  { prop: "age_max", label: "年龄上限", show: true },
  { prop: "daily_batch_limit", label: "每天最多生成几个Batch", show: true },
  { prop: "priority", label: "执行优先级(数字越大越先执行)", show: true },
  { prop: "status", label: "状态(0:启用 1:禁用)", show: true },
  { prop: "created_time", label: "创建时间", show: true },
  { prop: "updated_time", label: "更新时间", show: true },
  { prop: "created_id", label: "创建人ID", show: true },
  { prop: "updated_id", label: "更新人ID", show: true },
  { prop: "operation", label: "操作", show: true },
]);

// 导出列（不含选择/序号/操作）
const exportColumns = [
  { prop: "strategy_name", label: "策略名称" },
  { prop: "location", label: "目标地点" },
  { prop: "gender", label: "目标性别" },
  { prop: "age_min", label: "年龄下限" },
  { prop: "age_max", label: "年龄上限" },
  { prop: "daily_batch_limit", label: "每天最多生成几个Batch" },
  { prop: "priority", label: "执行优先级(数字越大越先执行)" },
  { prop: "status", label: "状态(0:启用 1:禁用)" },
  { prop: "created_time", label: "创建时间" },
  { prop: "updated_time", label: "更新时间" },
  { prop: "created_id", label: "创建人ID" },
  { prop: "updated_id", label: "更新人ID" },
];

// 导入/导出配置
const curdContentConfig = {
  permPrefix: "module_ai_image:ai_image_auto_strategy",
  cols: exportColumns as any,
  importTemplate: () => AiImageAutoStrategyAPI.downloadTemplateAiImageAutoStrategy(),
  exportsAction: async (params: any) => {
    const query: any = { ...params };
    query.status = "0";
    query.page_no = 1;
    query.page_size = 9999;
    const all: any[] = [];
    while (true) {
      const res = await AiImageAutoStrategyAPI.listAiImageAutoStrategy(query);
      const items = res.data?.data?.items || [];
      const total = res.data?.data?.total || 0;
      all.push(...items);
      if (all.length >= total || items.length === 0) break;
      query.page_no += 1;
    }
    return all;
  },
} as unknown as IContentConfig;

// 详情表单
const detailFormData = ref<AiImageAutoStrategyTable>({});
// 日期范围临时变量
const createdDateRange = ref<[Date, Date] | []>([]);
// 更新时间范围临时变量
const updatedDateRange = ref<[Date, Date] | []>([]);

// 处理创建时间范围变化
function handleCreatedDateRangeChange(range: [Date, Date]) {
  createdDateRange.value = range;
  if (range && range.length === 2) {
    queryFormData.created_time = [formatToDateTime(range[0]), formatToDateTime(range[1])];
  } else {
    queryFormData.created_time = undefined;
  }
}

// 处理更新时间范围变化
function handleUpdatedDateRangeChange(range: [Date, Date]) {
  updatedDateRange.value = range;
  if (range && range.length === 2) {
    queryFormData.updated_time = [formatToDateTime(range[0]), formatToDateTime(range[1])];
  } else {
    queryFormData.updated_time = undefined;
  }
}

// 分页查询参数
const queryFormData = reactive<AiImageAutoStrategyPageQuery>({
  page_no: 1,
  page_size: 10,
  strategy_name: undefined,
  location: undefined,
  gender: undefined,
  age_min: undefined,
  age_max: undefined,
  daily_batch_limit: undefined,
  priority: undefined,
  status: undefined,
  created_time: undefined,
  updated_time: undefined,
  created_id: undefined,
  updated_id: undefined,
});

// 编辑表单
const formData = reactive<AiImageAutoStrategyForm>({
  id: undefined,
  strategy_name: undefined,
  location: undefined,
  background_strategy: undefined,
  gender: undefined,
  theme_ids: [],
  age_min: undefined,
  age_max: undefined,
  daily_batch_limit: undefined,
  priority: undefined,
  status: undefined,
});

watch(
  () => formData.gender, // 直接访问属性，不需要 .value
  (newGender) => {
    // 这里的 ageMapping 记得要在外部定义好
    if (newGender && ageMapping[newGender]) {
      formData.age_min = ageMapping[newGender].min;
      formData.age_max = ageMapping[newGender].max;
    }
  }
);

// 字典仓库与需要加载的字典类型
const dictStore = useDictStore();
const dictTypes: any = [];

// 弹窗状态
const dialogVisible = reactive({
  title: "",
  visible: false,
  type: "create" as "create" | "update" | "detail",
});

// 表单验证规则
const rules = reactive({
  id: [{ required: false, message: "请输入主键ID", trigger: "blur" }],
  strategy_name: [{ required: false, message: "请输入策略名称", trigger: "blur" }],
  location: [{ required: false, message: "请输入目标地点", trigger: "blur" }],
  gender: [{ required: false, message: "请输入目标性别", trigger: "blur" }],
  age_min: [{ required: false, message: "请输入年龄下限", trigger: "blur" }],
  age_max: [{ required: false, message: "请输入年龄上限", trigger: "blur" }],
  daily_batch_limit: [
    { required: false, message: "请输入每天最多生成几个任务批次一个批次15张图", trigger: "blur" },
  ],
  priority: [{ required: true, message: "请输入执行优先级", trigger: "blur" }],
  status: [{ required: false, message: "请输入状态", trigger: "blur" }],
  created_time: [{ required: false, message: "请输入创建时间", trigger: "blur" }],
  updated_time: [{ required: false, message: "请输入更新时间", trigger: "blur" }],
  created_id: [{ required: true, message: "请输入创建人ID", trigger: "blur" }],
  updated_id: [{ required: true, message: "请输入更新人ID", trigger: "blur" }],
});

// 导入弹窗显示状态
const importDialogVisible = ref(false);
const uploadLoading = ref(false);

// 导出弹窗显示状态
const exportsDialogVisible = ref(false);

// 打开导入弹窗
function handleOpenImportDialog() {
  importDialogVisible.value = true;
}

// 打开导出弹窗
function handleOpenExportsModal() {
  exportsDialogVisible.value = true;
}

// 列表刷新
async function handleRefresh() {
  await loadingData();
}

// 加载表格数据
async function loadingData() {
  loading.value = true;
  try {
    const response = await AiImageAutoStrategyAPI.listAiImageAutoStrategy(queryFormData);
    pageTableData.value = response.data.data.items;
    total.value = response.data.data.total;
  } catch (error: any) {
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// 查询（重置页码后获取数据）
async function handleQuery() {
  queryFormData.page_no = 1;
  loadingData();
}

// 选择创建人后触发查询
function handleConfirm() {
  handleQuery();
}

// 重置查询
async function handleResetQuery() {
  queryFormRef.value.resetFields();
  queryFormData.page_no = 1;
  // 重置日期范围选择器
  createdDateRange.value = [];
  updatedDateRange.value = [];
  queryFormData.created_time = undefined;
  queryFormData.updated_time = undefined;
  loadingData();
}

// 定义初始表单数据常量
const initialFormData: AiImageAutoStrategyForm = {
  id: undefined,
  strategy_name: undefined,
  location: undefined,
  gender: undefined,
  theme_ids: [],
  age_min: undefined,
  age_max: undefined,
  daily_batch_limit: undefined,
  priority: undefined,
  status: undefined,
};

// 重置表单
async function resetForm() {
  if (dataFormRef.value) {
    dataFormRef.value.resetFields();
    dataFormRef.value.clearValidate();
  }
  // 完全重置 formData 为初始状态
  Object.assign(formData, initialFormData);
}

// 行复选框选中项变化
async function handleSelectionChange(selection: any) {
  selectIds.value = selection.map((item: any) => item.id);
  selectionRows.value = selection;
}

// 关闭弹窗
async function handleCloseDialog() {
  dialogVisible.visible = false;
  resetForm();
}

// 打开弹窗
async function handleOpenDialog(type: "create" | "update" | "detail", id?: number) {
  dialogVisible.type = type;
  if (id) {
    const response = await AiImageAutoStrategyAPI.detailAiImageAutoStrategy(id);
    if (type === "detail") {
      dialogVisible.title = "详情";
      Object.assign(detailFormData.value, response.data.data);
    } else if (type === "update") {
      dialogVisible.title = "修改";
      Object.assign(formData, response.data.data);
    }
  } else {
    dialogVisible.title = "新增AiImageAutoStrategy";
    formData.id = undefined;
    formData.strategy_name = undefined;
    formData.location = undefined;
    formData.gender = undefined;
    formData.age_min = undefined;
    formData.age_max = undefined;
    formData.daily_batch_limit = undefined;
    formData.priority = undefined;
    formData.status = undefined;
  }
  dialogVisible.visible = true;
}

// 提交表单（防抖）
async function handleSubmit() {
  // 表单校验
  dataFormRef.value.validate(async (valid: any) => {
    if (valid) {
      loading.value = true;
      // 根据弹窗传入的参数(deatil\create\update)判断走什么逻辑
      const submitData = { ...formData };
      const id = formData.id;
      if (id) {
        try {
          await AiImageAutoStrategyAPI.updateAiImageAutoStrategy(id, { id, ...submitData });
          dialogVisible.visible = false;
          resetForm();
          handleCloseDialog();
          handleResetQuery();
        } catch (error: any) {
          console.error(error);
        } finally {
          loading.value = false;
        }
      } else {
        try {
          await AiImageAutoStrategyAPI.createAiImageAutoStrategy(submitData);
          dialogVisible.visible = false;
          resetForm();
          handleCloseDialog();
          handleResetQuery();
        } catch (error: any) {
          console.error(error);
        } finally {
          loading.value = false;
        }
      }
    }
  });
}

// 删除、批量删除
async function handleDelete(ids: number[]) {
  ElMessageBox.confirm("确认删除该项数据?", "警告", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(async () => {
      try {
        loading.value = true;
        await AiImageAutoStrategyAPI.deleteAiImageAutoStrategy(ids);
        handleResetQuery();
      } catch (error: any) {
        console.error(error);
      } finally {
        loading.value = false;
      }
    })
    .catch(() => {
      ElMessageBox.close();
    });
}

// 批量启用/停用
async function handleMoreClick(status: string) {
  if (selectIds.value.length) {
    ElMessageBox.confirm(`确认${status === "0" ? "启用" : "停用"}该项数据?`, "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    })
      .then(async () => {
        try {
          loading.value = true;
          await AiImageAutoStrategyAPI.batchAiImageAutoStrategy({ ids: selectIds.value, status });
          handleResetQuery();
        } catch (error: any) {
          console.error(error);
        } finally {
          loading.value = false;
        }
      })
      .catch(() => {
        ElMessageBox.close();
      });
  }
}

// 处理上传
const handleUpload = async (formData: FormData) => {
  try {
    uploadLoading.value = true;
    const response = await AiImageAutoStrategyAPI.importAiImageAutoStrategy(formData);
    if (response.data.code === ResultEnum.SUCCESS) {
      ElMessage.success(`${response.data.msg}，${response.data.data}`);
      importDialogVisible.value = false;
      await handleQuery();
    }
  } catch (error: any) {
    console.error(error);
  } finally {
    uploadLoading.value = false;
  }
};

onMounted(async () => {
  // 预加载字典数据
  if (dictTypes.length > 0) {
    await dictStore.getDict(dictTypes);
  }
  loadingData();
});

/**
 * 🌟 基于“目标地点”调用大模型进行纯文本的视觉脑暴
 */
const generateBgFromLocation = async () => {
  // 1. 拦截校验：必须先填写地点
  if (!formData.location || formData.location.trim() === "") {
    ElMessage.warning("请先在表单中填写【目标地点】，AI 才能开始脑暴！");
    return;
  }

  try {
    isGeneratingBg.value = true;

    // 2. 调用统一接口，这里只传 location，不传 image_url
    // 后端会自动走 LLM 的“地理脑暴模式”
    const res = await FissionTaskAPI.inferBackground({
      location: formData.location,
    });

    const code = res.data?.code;

    if (code === 200 || code === 0) {
      // 3. 解析双层数据结构
      const inferData = res.data?.data || res.data;

      // 4. 提取后端的三个视觉维度
      const scene = inferData.scene_detail || "";
      const lighting = inferData.lighting_detail || "";
      const atmosphere = inferData.atmosphere_detail || "";

      // 5. 组装成一句连贯的高级感描述（过滤掉空值并加上句号）
      const aiExtracted = [scene, lighting, atmosphere].filter(Boolean).join("。") + "。";

      // 6. 回填到文本域中
      formData.background_strategy = aiExtracted;

      ElMessage.success("🎉 场景特征脑暴完毕，已自动填入策略中！");
    } else {
      ElMessage.error(res.data?.msg || "AI 脑暴失败，请重试");
    }
  } catch (error) {
    console.error("基于地点生成背景异常:", error);
    ElMessage.error("网络或服务异常，请稍后重试");
  } finally {
    // 无论成功失败，必须重置按钮状态
    isGeneratingBg.value = false;
  }
};

/**
 * 🌟 上传参考图，利用多模态大模型反推背景描述
 */
const handleBgImageUpload = async (uploadFile: UploadFile) => {
  const rawFile = uploadFile.raw;
  if (!rawFile) return;

  // 1. 基础校验：限制只能传图片，且不超过 5MB (按需调整)
  const isImage = rawFile.type.startsWith("image/");
  const isLt5M = rawFile.size / 1024 / 1024 < 5;

  if (!isImage) {
    ElMessage.error("只能上传图片文件！");
    return;
  }
  if (!isLt5M) {
    ElMessage.error("图片大小不能超过 5MB！");
    return;
  }

  isReversingBg.value = true;
  // 开启全局遮罩式的加载提示
  const loadingMsg = ElMessage({
    message: "正在上传参考图并呼叫多模态大模型反推背景...",
    type: "info",
    duration: 0, // 0 表示不自动消失，直到手动 close
    icon: "Loading",
  });

  try {
    // ==========================================
    // 步骤 1：先调用文件系统，将图片传到 OSS / 服务器
    // ==========================================
    const uploadFormData = new FormData();
    uploadFormData.append("file", rawFile);

    const uploadRes: any = await FileAPI.uploadFile(uploadFormData);
    const remoteImageUrl = uploadRes.data?.data?.file_url || uploadRes.data?.file_url;

    if (!remoteImageUrl) throw new Error("上传未返回图片地址");

    // ==========================================
    // 步骤 2：拿着图片 URL 呼叫大模型进行反推
    // ==========================================
    const inferRes: any = await FissionTaskAPI.inferBackground({
      image_url: remoteImageUrl,
      // 如果目标地点有值，也可以一并传给大模型辅助识别
    });

    const code = inferRes.data?.code ?? inferRes.code;

    if (code === 200 || code === 0) {
      const inferData = inferRes.data?.data || inferRes.data;

      // 兼容两种后端返回格式：
      // 格式A：直接返回一整段 background_strategy
      // 格式B：像你之前的接口那样返回 scene_detail / lighting_detail 分段数据
      let aiExtracted = "";
      if (inferData.background_strategy) {
        aiExtracted = inferData.background_strategy;
      } else {
        const scene = inferData.scene_detail || "";
        const lighting = inferData.lighting_detail || "";
        const atmosphere = inferData.atmosphere_detail || "";
        // 拼接成一句完整的话
        aiExtracted = [scene, lighting, atmosphere].filter(Boolean).join("。") + "。";
      }

      // 将反推出来的绝美提示词赋值给表单
      formData.background_strategy = aiExtracted;

      loadingMsg.close();
      ElMessage.success("🎉 参考图背景特征提取完毕，已自动填入策略中！");
    } else {
      loadingMsg.close();
      ElMessage.warning("图片已上传，但特征反推失败，您可以尝试手动填写。");
    }
  } catch (error) {
    console.error("上传或背景反推异常:", error);
    loadingMsg.close();
    ElMessage.error("网络或服务异常，图片处理失败");
  } finally {
    // 无论成功失败，重置按钮的 loading 状态
    isReversingBg.value = false;
  }
};
</script>

<style lang="scss" scoped></style>
