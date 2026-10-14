<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import FissionAPI from "@/api/module_ai_image/fission";
import {
  Upload,
  Refresh,
  Loading,
  Clock,
  CircleClose,
  Edit,
  Search,
  RefreshRight,
} from "@element-plus/icons-vue";
import FissionUploadDialog from "./FissionUploadDialog.vue";

const showUpload = ref(false);
// 🚀 2. 添加点击编辑的处理逻辑
// --- 状态管理 ---
const form = reactive({
  location: "",
  gender: "年轻女性",
  age: 20,
});

const router = useRouter();

// 跳转到专家工作台
const goToExpertStudio = (batchId: number) => {
  // 这里的路由 path 请替换成你项目中实际的 expert-studio 路由地址
  router.push({
    path: "/InspirationLab", // 替换为你的真实路由
    query: { batchId: batchId.toString() },
  });
};

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

const filterOptions = reactive({
  locations: [] as string[],
  scenes: [] as string[],
  styles: [] as string[],
  themes: [] as string[],
});

const fetchFilterOptions = async () => {
  try {
    // 构造请求参数，如果 gender 有值就传给后端
    const params = {
      gender: queryParams.gender || undefined,
    };

    // 假设你的 FissionAPI.getAllFilterOptions 支持接收 params
    const res: any = await FissionAPI.getAllFilterOptions(params);
    const responseData = res.data || res;

    if (responseData.code === 200 || responseData.code === 0) {
      const data = responseData.data;
      // 接口返回该性别下过滤后的选项
      filterOptions.locations = data.locations || [];
      filterOptions.scenes = data.scenes || [];
      filterOptions.styles = data.styles || [];
      filterOptions.themes = data.themes || [];
    }
  } catch (error) {
    console.error("获取联动筛选项失败:", error);
  }
};

const submitting = ref(false); // 提交按钮状态
const loading = ref(false); // 全局列表加载状态
const tableData = ref<any[]>([]);
const total = ref(0);
const queryParams = reactive({
  page: 1,
  page_size: 10,
  input_location: "", // 新增：按地点搜索
  gender: "",
  selected_scene: "",
  status: "",
  selected_style: "",
  theme: "",
});

const handleSearch = () => {
  // 搜索时必须把页码重置为 1
  queryParams.page = 1;
  fetchData();
};

const handleDeleteBatch = async (batch: any) => {
  try {
    await FissionAPI.deleteBatch(batch.id);
    await fetchData();
    console.log("准备删除批次:", batch.batch_sn);
  } catch (error) {
    console.error("删除失败:", error);
  }
};

const resetSearch = () => {
  queryParams.input_location = "";
  queryParams.status = "";
  queryParams.selected_scene = "";
  queryParams.gender = "";
  queryParams.selected_style = "";
  queryParams.theme = "";
  queryParams.page = 1;
  fetchData();
};

// 监听查询参数中的性别
watch(
  () => queryParams.gender,
  (newGender) => {
    console.log(`检测到性别变更为: ${newGender}，开始联动查询...`);

    // 1. 性别变了，之前的筛选结果可能失效，建议清空部分已选值
    queryParams.selected_scene = "";
    queryParams.selected_style = "";
    queryParams.theme = "";

    // 2. 重新获取当前性别下的筛选项
    fetchFilterOptions();

    // 3. 重置页码并刷新表格数据
    queryParams.page = 1;
    fetchData(); // 假设这是你请求列表的方法
  }
);

// 🚨 核心变量：定时器句柄
let pollTimer: any = null;

// --- 图片预览辅助 ---
const getPreviewList = (tasks: any[]) => {
  if (!Array.isArray(tasks)) return [];
  return tasks.filter((t) => t && t.image_url).map((t) => t.image_url);
};

const getImageIndex = (tasks: any[], currentUrl: string) =>
  getPreviewList(tasks).findIndex((img) => img === currentUrl);

// --- 核心逻辑：智能同步控制 ---

// 1. 检查是否还有“正在生图”的任务 (状态 0:待接入, 1:生图中)
const checkNeedPolling = () => {
  return tableData.value.some(
    (batch) =>
      batch.tasks &&
      batch.tasks.some((task: any) => task.process_status === 0 || task.process_status === 1)
  );
};

const handleEditImage = (task: any) => {
  console.log("准备编辑图片数据:", task);

  // 方案 B：路由跳转模式 (推荐，因为图片编辑面板一般比较复杂)
  router.push({
    path: "task/imageEdit", // 你的编辑页路由
    query: { taskId: task.id, imageUrl: task.image_url },
  });

  ElMessage.success(`进入编辑模式：${task.action_desc}`);
};

// 2. 开启轮询
const startPolling = () => {
  if (pollTimer) return; // 防止重复开启
  console.log("🚀 赛博导演：实时同步开启...");
  pollTimer = setInterval(() => {
    fetchData(true); // 传入 true 表示这是后台静默刷新
  }, 15000); // 5秒一刷，频率可以根据 z-image 的速度调
};

// 3. 停止轮询
const stopPolling = () => {
  if (pollTimer) {
    console.log("🛑 任务全部完成，自动进入休眠。");
    clearInterval(pollTimer);
    pollTimer = null;
  }
};

// 4. 获取数据（增量更新版）
const fetchData = async (isSilent = false) => {
  if (!isSilent) loading.value = true;

  try {
    const res: any = await FissionAPI.getBatchList(queryParams);
    const responseData = res.data || res;

    if (responseData.code === 0 || responseData.code === 200) {
      const dataContent = responseData.data || responseData;
      const newList = dataContent.items || dataContent.list || [];
      total.value = dataContent.total || 0;

      // ==========================================
      // 🚀 核心修复：引用复用重构法
      // 既保证当前页只显示 newList 的数据（修复分页）
      // 又保证正在轮询的老数据不触发 DOM 销毁重绘（修复闪烁）
      // ==========================================
      const nextTableData = newList.map((newItem: any) => {
        // 去当前的 tableData 里找，看有没有这个 ID
        const existingBatch = tableData.value.find((b: any) => b.id === newItem.id);

        if (existingBatch) {
          // 🎯 命中老数据（比如停留在第1页轮询时）：静默更新属性
          Object.assign(existingBatch, {
            batch_sn: newItem.batch_sn,
            input_location: newItem.input_location,
            selected_scene: newItem.selected_scene,
            selected_style: newItem.selected_style,
            created_time: newItem.created_time,
            status: newItem.status,
          });
          // 必须返回 existingBatch，保持内存地址不变，图片和组件就不会闪烁
          return existingBatch;
        } else {
          // 🎯 全新数据（比如翻到了第2页，或者别人刚建的新批次）：初始化新对象
          return {
            ...newItem,
            tasks: [],
            taskLoading: true,
          };
        }
      });

      // 直接覆盖！翻页时，上一页的老数据会在这里被干净利落地丢掉
      tableData.value = nextTableData;
    }

    // ==========================================
    // 往下是并发拉取子任务详情的逻辑 (保持不变)
    // ==========================================
    const taskPromises = tableData.value.map(async (batch) => {
      const isAllDone =
        batch.tasks.length > 0 && batch.tasks.every((t: any) => t.process_status >= 2);
      if (isSilent && isAllDone) return;

      try {
        const taskRes: any = await FissionAPI.getBatchTasks(batch.id);
        const taskResponse = taskRes.data || taskRes;

        if (taskResponse.code === 0 || taskResponse.code === 200) {
          const newTasks = taskResponse.data || taskResponse.items || [];

          if (batch.tasks.length === 0) {
            batch.tasks = newTasks;
          } else {
            newTasks.forEach((newTask: any) => {
              const existingTask = batch.tasks.find((t: any) => t.id === newTask.id);
              if (existingTask) {
                if (
                  existingTask.process_status !== newTask.process_status ||
                  existingTask.image_url !== newTask.image_url
                ) {
                  Object.assign(existingTask, newTask);
                }
              } else {
                batch.tasks.push(newTask);
              }
            });
          }
        }
      } catch (e) {
        console.error(`同步任务失败: ${batch.batch_sn}`, e);
      } finally {
        batch.taskLoading = false;
      }
    });

    await Promise.all(taskPromises);

    // 🛰️ 智能判断轮询
    if (checkNeedPolling()) {
      startPolling();
    } else {
      stopPolling();
    }
  } catch (error) {
    console.error("同步异常:", error);
  } finally {
    if (!isSilent) loading.value = false;
  }
};
// 5. 提交生图策划
const onSubmit = async () => {
  if (!form.location) return ElMessage.warning("老G，地点还没填呢！");

  submitting.value = true;
  try {
    const res: any = await FissionAPI.generateFissionTask(form);
    const response = res.data || res;

    if (response.code === 200 || response.code === 0) {
      ElMessage.success("AI 策划完成！10组黄金任务已下发，正在实时监控...");
      // 关键点：提交成功立刻手动刷一次，并开启轮询
      await fetchData();
      startPolling();
    } else {
      ElMessage.error(response.msg || "后端导演罢工了...");
    }
  } catch (error) {
    console.error("提交失败:", error);
    ElMessage.error("网络连接失败，请检查后端 API");
  } finally {
    submitting.value = false;
  }
};

// --- 生命周期钩子 ---

onMounted(() => {
  fetchData();
  fetchFilterOptions();
});

// 🚨 离场清理：老G，这个最重要！否则你换个页面后台还在刷
onUnmounted(() => {
  stopPolling();
});
</script>
<template>
  <div class="app-container">
    <div
      style="
        background: #ffffff;
        border: 1px solid #ebeef5;
        padding: 20px;
        border-left: 4px solid #409eff;
        margin-bottom: 20px;
      "
    >
      <el-form :inline="true" :model="form">
        <el-form-item label="大地点">
          <el-input v-model="form.location" placeholder="例如：桂林" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select
            v-model="form.gender"
            placeholder="请选择目标性别"
            clearable
            collapse-tags
            collapse-tags-indicator
            style="width: 240px"
          >
            <el-option
              v-for="item in genderOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="年龄">
          <el-input v-model="form.age" placeholder="20" style="width: 100px" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="onSubmit">开始生成</el-button>
          <el-button type="success" plain @click="showUpload = true">手动上传</el-button>
        </el-form-item>
      </el-form>
      <FissionUploadDialog
        v-model="showUpload"
        :gender-options="genderOptions"
        @success="fetchData(false)"
      />
    </div>

    <div class="flex justify-between items-center mb-2 px-2">
      <div class="font-bold text-gray-700 text-lg">📸 历史策划底片台</div>
      <el-button :icon="Refresh" type="success" plain @click="fetchData(false)">
        手动刷新数据
      </el-button>
    </div>
    <div
      class="flex flex-wrap items-center gap-3 mb-4 px-2 bg-gray-50 p-3 rounded border border-gray-100"
    >
      <el-select
        v-model="queryParams.status"
        placeholder="完成状态"
        clearable
        style="width: 160px"
        @change="handleSearch"
      >
        <el-option label="全部状态" value="" />
        <el-option label="已完成 (100%)" value="done" />
        <el-option label="未完成/生图中" value="processing" />
      </el-select>
      <el-select
        v-model="queryParams.gender"
        placeholder="请选择目标性别"
        multiple
        clearable
        collapse-tags
        collapse-tags-indicator
        style="width: 240px"
      >
        <el-option
          v-for="item in genderOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select
        v-model="queryParams.input_location"
        placeholder="大地点"
        clearable
        filterable
        style="width: 160px"
        @change="handleSearch"
      >
        <el-option
          v-for="item in filterOptions.locations"
          :key="item"
          :label="item"
          :value="item"
        />
      </el-select>

      <el-select
        v-model="queryParams.selected_scene"
        placeholder="场景"
        clearable
        filterable
        style="width: 160px"
        @change="handleSearch"
      >
        <el-option v-for="item in filterOptions.scenes" :key="item" :label="item" :value="item" />
      </el-select>

      <el-select
        v-model="queryParams.selected_style"
        placeholder="光影风格"
        clearable
        filterable
        style="width: 160px"
        @change="handleSearch"
      >
        <el-option v-for="item in filterOptions.styles" :key="item" :label="item" :value="item" />
      </el-select>

      <el-select
        v-model="queryParams.theme"
        placeholder="服饰主题"
        clearable
        filterable
        style="width: 160px"
        @change="handleSearch"
      >
        <el-option v-for="item in filterOptions.themes" :key="item" :label="item" :value="item" />
      </el-select>

      <div class="flex gap-2 ml-2">
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button :icon="RefreshRight" @click="resetSearch">重置</el-button>
      </div>
    </div>

    <div v-loading="loading" class="batch-feed-container">
      <el-empty
        v-if="tableData.length === 0 && !loading"
        description="暂无策划数据，快去生成第一批吧！"
      />

      <el-card v-for="batch in tableData" :key="batch.id" class="mb-6 batch-card" shadow="hover">
        <template #header>
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-4">
              <el-tag size="large" effect="dark">{{ batch.batch_sn }}</el-tag>
              <span class="font-bold text-lg">📍 {{ batch.input_location }}</span>
              <span class="text-gray-500 text-sm">{{ batch.age }}岁 {{ batch.gender }}</span>
              <el-divider direction="vertical" />
              <el-tag size="small" type="info">场景: {{ batch.selected_scene }}</el-tag>
              <el-tag size="small" type="success">风格: {{ batch.selected_style }}</el-tag>
              <el-tag size="small" type="success">主题: {{ batch.theme }}</el-tag>
            </div>

            <div class="flex items-center gap-4">
              <div class="text-gray-400 text-sm">
                <el-icon class="mr-1"><Clock /></el-icon>
                {{ batch.created_time }}
              </div>

              <el-tooltip content="进入工作台查看详情与重绘" placement="top">
                <el-button
                  type="primary"
                  icon="Edit"
                  circle
                  plain
                  size="small"
                  @click="goToExpertStudio(batch.id)"
                />
              </el-tooltip>

              <el-popconfirm
                title="确定要删除这个批次及其下的所有图片吗？"
                confirm-button-text="确认"
                cancel-button-text="取消"
                confirm-button-type="danger"
                icon="InfoFilled"
                icon-color="#f56c6c"
                @confirm="handleDeleteBatch(batch)"
              >
                <template #reference>
                  <el-button type="danger" icon="Delete" circle plain size="small" />
                </template>
              </el-popconfirm>
            </div>
          </div>
        </template>
        <div class="grid-gallery" v-loading="batch.taskLoading">
          <div v-for="(task, index) in batch.tasks" :key="task.id" class="task-card">
            <div class="image-wrapper">
              <div class="status-badge">
                <el-tag v-if="task.process_status === 0" type="info" effect="dark" size="small">
                  等待接入
                </el-tag>
                <el-tag
                  v-else-if="task.process_status === 1"
                  type="warning"
                  effect="dark"
                  size="small"
                  class="animate-pulse"
                >
                  正在生图
                </el-tag>
                <el-tag
                  v-else-if="task.process_status === 3"
                  type="danger"
                  effect="dark"
                  size="small"
                >
                  失败
                </el-tag>
                <el-tag v-else type="success" effect="dark" size="small">
                  {{ task.view_type || "景别" }}
                </el-tag>
              </div>

              <el-image
                v-if="task.process_status === 2 && task.image_url"
                :src="task.image_url"
                :preview-src-list="getPreviewList(batch.tasks)"
                :initial-index="getImageIndex(batch.tasks, task.image_url)"
                fit="cover"
                class="full-image"
                :preview-teleported="true"
                :hide-on-click-modal="true"
                lazy
              />
              <div v-else class="placeholder-box">
                <el-icon
                  class="is-loading text-warning"
                  :size="40"
                  v-if="task.process_status === 0 || task.process_status === 1"
                >
                  <Loading />
                </el-icon>
                <el-icon class="text-danger" :size="30" v-else-if="task.process_status === 3">
                  <CircleClose />
                </el-icon>
              </div>
            </div>

            <div class="task-info">
              <div class="flex justify-between items-start mb-1">
                <div class="action-title truncate pr-2" :title="task.action_desc">
                  {{ task.action_desc || "动作待定" }}
                </div>

                <el-button
                  v-if="task.process_status === 2 && task.image_url"
                  type="primary"
                  link
                  size="small"
                  :icon="Edit"
                  @click="handleEditImage(task)"
                >
                  编辑
                </el-button>
              </div>

              <el-tooltip placement="top-start" :content="task.positive_prompt" :show-after="300">
                <div class="prompt-text">{{ task.positive_prompt }}</div>
              </el-tooltip>
            </div>
          </div>
        </div>
      </el-card>

      <div class="mt-4 flex justify-end pb-8">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @change="fetchData(false)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 基础工具类 */
.mb-4 {
  margin-bottom: 1rem;
}
.mb-6 {
  margin-bottom: 1.5rem;
}
.mt-4 {
  margin-top: 1rem;
}
.pb-8 {
  padding-bottom: 2rem;
}
.border-l-4 {
  border-left-width: 4px;
}
.border-l-primary {
  border-left-color: var(--el-color-primary);
}
.flex {
  display: flex;
}
.justify-between {
  justify-content: space-between;
}
.justify-end {
  justify-content: flex-end;
}
.items-center {
  align-items: center;
}
.gap-4 {
  gap: 1rem;
}
.mr-1 {
  margin-right: 0.25rem;
}
.text-sm {
  font-size: 0.875rem;
}
.text-lg {
  font-size: 1.125rem;
}
.text-gray-500 {
  color: #6b7280;
}
.text-gray-400 {
  color: #9ca3af;
}
.text-gray-300 {
  color: #d1d5db;
}
.text-warning {
  color: #e6a23c;
}
.text-danger {
  color: #f56c6c;
}
.font-bold {
  font-weight: bold;
}

/* 卡片样式强化 */
.batch-card {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #ebeef5;
}
:deep(.el-card__header) {
  background-color: #fafafa;
  padding: 12px 20px;
}

/* 核心网格布局 */
.grid-gallery {
  display: grid;
  /* 调整列宽：让大卡片轻松塞下 5 列，正好 5x2 排布 */
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  padding: 8px;
}

.task-card {
  background: #fff;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #ebeef5;
  transition: all 0.2s;
}
.task-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px 0 rgba(0, 0, 0, 0.1);
  border-color: #c0c4cc;
}

.image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 9 / 16;
  background-color: #f3f4f6;
  border-bottom: 1px solid #ebeef5;
}

.status-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  z-index: 10;
}

.full-image {
  width: 100%;
  height: 100%;
  display: block;
}

.placeholder-box {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f9fafb;
}

.task-info {
  padding: 10px;
}

.action-title {
  font-size: 13px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.prompt-text {
  font-size: 11px;
  color: #909399;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  cursor: help;
  line-height: 1.4;
}

/* 动画效果 */
.el-button.is-loading .el-icon {
  animation: rotating 1.5s linear infinite;
}
@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
.animate-pulse {
  animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
