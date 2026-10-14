<template>
  <div class="app-container video-processing-page">
    <header class="page-header">
      <div class="page-title">
        <el-icon><VideoCamera /></el-icon>
        <h2>自动剪辑</h2>
      </div>
      <el-tooltip content="刷新任务列表">
        <el-button
          :icon="Refresh"
          circle
          aria-label="刷新任务列表"
          :loading="listLoading"
          @click="loadBatches()"
        />
      </el-tooltip>
    </header>

    <main class="workspace-grid">
      <div class="workspace-column">
        <VideoProcessingImportPanel @submitted="loadBatches(false)" />
        <VideoProcessingAdvancedSettings />
      </div>

      <section class="workspace-panel task-panel" aria-labelledby="task-list-title">
        <div class="panel-header task-panel-header">
          <div>
            <h3 id="task-list-title">处理任务</h3>
            <span class="panel-count">{{ total }} 条</span>
          </div>
          <div class="task-filters">
            <el-select
              v-model="query.status"
              clearable
              placeholder="全部状态"
              class="status-filter"
              @change="handleFilterChange"
            >
              <el-option
                v-for="status in taskStatusOptions"
                :key="status.value"
                :label="status.label"
                :value="status.value"
              />
            </el-select>
          </div>
        </div>

        <VideoProcessingBatchTable
          :batches="batchList"
          :loading="listLoading"
          :clock-drift="clockDriftSeconds"
          @task-open="handleOpenDetail"
          @task-action="handleTaskAction"
        />

        <div class="pagination-row">
          <el-pagination
            v-model:current-page="query.page_no"
            v-model:page-size="query.page_size"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadBatches(false)"
            @size-change="handlePageSizeChange"
          />
        </div>
      </section>
    </main>

    <el-drawer v-model="detailVisible" title="任务详情" size="min(560px, 92vw)">
      <div v-loading="detailLoading" class="detail-content">
        <template v-if="currentDetail">
          <div class="detail-heading">
            <div>
              <h3>{{ currentDetail.title }}</h3>
              <span>{{ currentDetail.task_no }}</span>
            </div>
            <el-tag :type="getTaskStatusMeta(currentDetail.status).type">
              {{ getTaskStatusMeta(currentDetail.status).label }}
            </el-tag>
          </div>

          <el-progress
            :percentage="currentDetail.progress"
            :status="currentDetail.status === 'failed' ? 'exception' : undefined"
          />

          <el-descriptions :column="1" border class="detail-descriptions">
            <el-descriptions-item label="当前阶段">
              {{ getStageLabel(currentDetail.current_stage) }}
            </el-descriptions-item>
            <el-descriptions-item label="输出规格">
              {{ currentDetail.config.aspect_ratio }} ·
              {{ getStyleLabel(currentDetail.config.style_preset) }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatToDateTime(currentDetail.created_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="结束时间">
              {{ getTaskFinishedTimeLabel(currentDetail) }}
            </el-descriptions-item>
            <el-descriptions-item label="处理耗时">
              {{ getTaskDurationLabel(currentDetail) }}
            </el-descriptions-item>
            <el-descriptions-item v-if="currentDetail.error_message" label="失败原因">
              <el-text type="danger">{{ currentDetail.error_message }}</el-text>
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="detailStageTimings.length || detailStageProgress" class="debug-panel">
            <div class="debug-panel__heading">
              <h4>阶段耗时</h4>
              <span>合计 {{ detailStageTimingTotal }}</span>
            </div>
            <ul class="stage-timing">
              <!-- 进行中的阶段排在已完成的上面，耗时本地每秒自增，不用手动刷新。 -->
              <li
                v-if="detailStageProgress"
                class="stage-timing__item stage-timing__item--active"
              >
                <span class="stage-timing__label">
                  {{ detailStageProgress.label }}
                  <em class="stage-timing__badge">进行中</em>
                </span>
                <span class="stage-timing__track">
                  <i class="stage-timing__fill stage-timing__fill--active" />
                </span>
                <span class="stage-timing__value">{{ detailStageProgress.elapsed_text }}</span>
              </li>
              <li
                v-for="item in detailStageTimings"
                :key="item.stage"
                class="stage-timing__item"
                :class="{ 'stage-timing__item--parallel': item.parallel }"
              >
                <span class="stage-timing__label">{{ item.label }}</span>
                <span class="stage-timing__track">
                  <i class="stage-timing__fill" :style="{ width: `${item.percent}%` }" />
                </span>
                <span class="stage-timing__value">{{ item.elapsed_text }}</span>
              </li>
            </ul>
          </div>

          <div v-if="detailDebugRows.length || detailReviewAsset" class="debug-panel">
            <div class="debug-panel__heading">
              <h4>渲染变量</h4>
              <span>花字 · 贴纸 · BGM · 模型</span>
            </div>
            <el-descriptions v-if="detailDebugRows.length" :column="1" border size="small">
              <el-descriptions-item
                v-for="row in detailDebugRows"
                :key="row.label"
                :label="row.label"
              >
                {{ row.value }}
              </el-descriptions-item>
            </el-descriptions>
            <!-- 完整时间线 JSON 随详情一起下发太贵，展开时才按素材单独取。 -->
            <el-collapse
              v-if="detailReviewAsset"
              class="debug-panel__raw"
              @change="handleReviewMetadataExpand"
            >
              <el-collapse-item name="raw">
                <template #title>
                  <span class="debug-panel__raw-title">完整渲染元数据（JSON）</span>
                </template>
                <pre
                  v-if="detailReviewMetadata"
                  class="debug-panel__json"
                >{{ detailReviewMetadata }}</pre>
                <el-text v-else size="small" type="info">
                  {{ detailMetadataLoading ? "加载中…" : "展开以加载完整元数据" }}
                </el-text>
              </el-collapse-item>
            </el-collapse>
          </div>

          <div v-if="currentDetail" class="debug-panel">
            <div class="debug-panel__heading">
              <h4>提示词调试</h4>
              <span>创意规划 · 封面生图</span>
            </div>
            <!-- 提示词全文与参考帧地址都不随详情下发，展开时才按任务单独取。 -->
            <el-collapse
              v-model="debugActiveNames"
              class="debug-panel__raw"
              @change="handleDebugExpand"
            >
              <el-collapse-item name="prompts">
                <template #title>
                  <span class="debug-panel__raw-title">查看本次实际使用的提示词与生图原图</span>
                </template>
                <div v-if="debugLoading" class="debug-placeholder">加载中…</div>
                <template v-else-if="taskDebug">
                  <div class="debug-block">
                    <h5>创意规划</h5>
                    <el-descriptions :column="1" border size="small">
                      <el-descriptions-item label="模型">
                        {{ taskDebug.planner_model || "未记录" }}
                      </el-descriptions-item>
                    </el-descriptions>
                    <p class="debug-label">System 提示词</p>
                    <pre class="debug-panel__json">{{
                      taskDebug.planner_system_prompt || "该任务未记录"
                    }}</pre>
                    <p class="debug-label">User 提示词</p>
                    <pre class="debug-panel__json">{{
                      taskDebug.planner_user_prompt || "该任务未记录"
                    }}</pre>
                  </div>

                  <div class="debug-block">
                    <h5>封面生图</h5>
                    <el-descriptions :column="1" border size="small">
                      <el-descriptions-item label="通道">
                        {{ taskDebug.cover_image_provider || "未记录" }}
                      </el-descriptions-item>
                      <el-descriptions-item label="模型">
                        {{ taskDebug.cover_image_model || "未记录" }}
                      </el-descriptions-item>
                      <el-descriptions-item label="尺寸">
                        {{ taskDebug.cover_image_size || "未记录" }}
                      </el-descriptions-item>
                      <el-descriptions-item label="策划模型">
                        {{ taskDebug.cover_summary_model || "未记录" }}
                      </el-descriptions-item>
                    </el-descriptions>
                    <p class="debug-label">生图提示词</p>
                    <pre class="debug-panel__json">{{
                      taskDebug.cover_image_prompt || "该任务未记录"
                    }}</pre>
                    <template v-if="taskDebug.cover_reference_url">
                      <p class="debug-label">
                        生图原图{{
                          taskDebug.cover_reference_name
                            ? `（${taskDebug.cover_reference_name}）`
                            : ""
                        }}
                      </p>
                      <img
                        class="debug-reference"
                        :src="taskDebug.cover_reference_url"
                        alt="封面生图参考帧"
                      />
                    </template>
                    <div v-else class="debug-placeholder">该任务未记录生图原图</div>
                  </div>
                </template>
                <div v-else class="debug-placeholder">暂无调试信息</div>
              </el-collapse-item>
            </el-collapse>
          </div>

          <div v-if="detailCoverUrl" class="cover-preview">
            <div class="cover-preview__heading">
              <h4>AI 封面</h4>
              <el-button
                v-if="detailCoverAsset"
                v-hasPerm="['module_video:processing:download']"
                :icon="Download"
                size="small"
                @click="downloadAsset(currentDetail, detailCoverAsset)"
              >
                下载封面
              </el-button>
            </div>
            <img class="cover-preview__image" :src="detailCoverUrl" alt="AI 封面" />
          </div>

          <div class="asset-heading">
            <h4>素材与产物</h4>
            <span>{{ currentDetail.assets.length }} 项</span>
          </div>
          <el-table :data="currentDetail.assets" size="small" border>
            <el-table-column label="类型" width="82">
              <template #default="{ row }">{{ getAssetRoleLabel(row.asset_role) }}</template>
            </el-table-column>
            <el-table-column
              prop="file_name"
              label="文件名"
              min-width="180"
              show-overflow-tooltip
            />
            <el-table-column label="大小" width="94">
              <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="82">
              <template #default="{ row }">
                <el-tag :type="getAssetStatusType(row.upload_status)" size="small">
                  {{ getAssetStatusLabel(row.upload_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ row }">
                <el-tooltip v-if="isOutputAsset(row)" content="下载产物">
                  <el-button
                    v-hasPerm="['module_video:processing:download']"
                    :icon="Download"
                    link
                    type="primary"
                    aria-label="下载产物"
                    @click="downloadAsset(currentDetail, row)"
                  />
                </el-tooltip>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </div>
    </el-drawer>

    <el-dialog
      v-model="previewVisible"
      :title="previewTask?.title || '成片预览'"
      width="min(920px, 94vw)"
      destroy-on-close
      @closed="handlePreviewClosed"
    >
      <div v-loading="previewLoading" class="preview-body">
        <video
          v-if="previewUrl"
          class="video-preview"
          :src="previewUrl"
          :poster="previewCoverUrl || undefined"
          controls
          preload="metadata"
        />
        <el-empty v-else :image-size="72" description="暂无可预览的成片" />
      </div>
      <template #footer>
        <div class="preview-footer">
          <el-button @click="previewVisible = false">关闭</el-button>
          <el-button
            v-if="previewTask?.status === 'succeeded' && previewOutputAsset"
            v-hasPerm="['module_video:processing:download']"
            type="primary"
            :icon="Download"
            @click="downloadAsset(previewTask, previewOutputAsset)"
          >
            下载成片
          </el-button>
          <el-button
            v-if="previewTask?.status === 'reviewing'"
            v-hasPerm="['module_video:processing:create']"
            type="success"
            :icon="CircleCheck"
            @click="handleApproveReview(previewTask)"
          >
            审核通过
          </el-button>
          <el-button
            v-if="previewTask && canRegenerate(previewTask)"
            v-hasPerm="['module_video:processing:create']"
            :icon="RefreshRight"
            @click="handleRegenerateReview(previewTask)"
          >
            重新生成
          </el-button>
          <el-button
            v-if="previewTask && previewCoverAsset"
            v-hasPerm="['module_video:processing:download']"
            :icon="Download"
            @click="downloadAsset(previewTask, previewCoverAsset)"
          >
            下载封面
          </el-button>
          <el-button
            v-if="previewTask && previewSubtitleAsset"
            v-hasPerm="['module_video:processing:download']"
            :icon="Download"
            @click="downloadAsset(previewTask, previewSubtitleAsset)"
          >
            下载字幕
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  CircleCheck,
  Download,
  Refresh,
  RefreshRight,
  VideoCamera,
} from "@element-plus/icons-vue";
import { formatToDateTime } from "@/utils/dateUtil";
import VideoProcessingAPI, {
  type VideoAssetRole,
  type VideoBatchListParams,
  type VideoProcessingBatch,
  type VideoProcessingTask,
  type VideoProcessingTaskDetail,
  type VideoStylePreset,
  type VideoTaskAsset,
  type VideoTaskDebugInfo,
  type VideoTaskDebugSummary,
  type VideoTaskStatus,
} from "@/api/module_video/processing";
import VideoProcessingImportPanel from "./components/VideoProcessingImportPanel.vue";
import VideoProcessingAdvancedSettings from "./components/VideoProcessingAdvancedSettings.vue";
import VideoProcessingBatchTable from "./components/VideoProcessingBatchTable.vue";

type TagType = "primary" | "success" | "warning" | "info" | "danger";

const taskStatusOptions: Array<{ label: string; value: VideoTaskStatus }> = [
  { label: "待上传", value: "draft" },
  { label: "上传中", value: "uploading" },
  { label: "排队中", value: "queued" },
  { label: "处理中", value: "processing" },
  { label: "待审核", value: "reviewing" },
  { label: "已完成", value: "succeeded" },
  { label: "失败", value: "failed" },
  { label: "已取消", value: "cancelled" },
];

const statusMeta: Record<VideoTaskStatus, { label: string; type: TagType }> = {
  draft: { label: "待上传", type: "info" },
  uploading: { label: "上传中", type: "primary" },
  queued: { label: "排队中", type: "warning" },
  processing: { label: "处理中", type: "primary" },
  reviewing: { label: "待审核", type: "warning" },
  succeeded: { label: "已完成", type: "success" },
  failed: { label: "失败", type: "danger" },
  cancelled: { label: "已取消", type: "info" },
};

const stageLabels: Record<string, string> = {
  draft: "等待素材",
  uploading: "上传素材",
  queued: "等待处理",
  media_analysis: "媒体检测",
  transcription: "语音转写",
  editing: "剪辑编排",
  rendering: "渲染成片",
  quality_check: "成片质检",
  reviewing: "等待审核",
  completed: "处理完成",
};

const styleLabels: Record<VideoStylePreset, string> = {
  vlog: "日常 Vlog",
};

const assetRoleLabels: Record<VideoAssetRole, string> = {
  source: "源视频",
  cover: "封面",
  ending: "片尾",
  music: "配乐",
  review: "待审核稿",
  output: "成片",
  subtitle: "字幕",
};

const query = reactive<VideoBatchListParams>({
  page_no: 1,
  page_size: 10,
  status: undefined,
});

const listLoading = ref(false);
const batchList = ref<VideoProcessingBatch[]>([]);
const total = ref(0);

const detailVisible = ref(false);
const detailLoading = ref(false);
const currentDetail = ref<VideoProcessingTaskDetail>();
const detailCoverAsset = ref<VideoTaskAsset>();
// 封面预览地址详情接口已经签好（cover_preview_url），不用再单独换一次签名。
const detailCoverUrl = computed(() => currentDetail.value?.cover_preview_url ?? "");

const previewVisible = ref(false);
const previewLoading = ref(false);
const previewTask = ref<VideoProcessingTaskDetail>();
const previewOutputAsset = ref<VideoTaskAsset>();
const previewCoverAsset = ref<VideoTaskAsset>();
const previewSubtitleAsset = ref<VideoTaskAsset>();
const previewUrl = ref("");
// 同 detailCoverUrl：封面地址随详情一起返回，不用再单独换一次签名。
const previewCoverUrl = computed(() => previewTask.value?.cover_preview_url ?? "");

const debugModelLabels: Record<string, string> = {
  asr: "语音转写",
  creative_planner: "创意规划",
  cover_summary: "封面策划",
  cover_image: "封面生图",
};

const detailDebugSummary = computed<VideoTaskDebugSummary | undefined>(
  () => currentDetail.value?.config.debug_summary ?? undefined
);

// 数据取回来后本地继续走表：后端只给「取数那一刻」的已耗时，这里每秒自增
// 补上后续流逝，用户不用干等下一次轮询也能看到数字在涨。
const clockTick = ref(Date.now());
const clockBaseAt = ref(Date.now());
const clockDriftSeconds = computed(() =>
  Math.max((clockTick.value - clockBaseAt.value) / 1000, 0)
);

let clockTimer: number | undefined;

function hasLiveStage() {
  if (detailVisible.value && currentDetail.value?.config.stage_progress) return true;
  return batchList.value.some((batch) =>
    (batch.tasks ?? []).some((task) => task.config?.stage_progress)
  );
}

function startClock() {
  if (clockTimer !== undefined) return;
  clockTimer = window.setInterval(() => {
    if (!hasLiveStage()) {
      stopClock();
      return;
    }
    clockTick.value = Date.now();
  }, 1000);
}

function stopClock() {
  if (clockTimer === undefined) return;
  window.clearInterval(clockTimer);
  clockTimer = undefined;
}

/** 每次取数都把本地计时归零，否则会把两次轮询之间的间隔重复算进阶段耗时。 */
function resetClockBase() {
  clockBaseAt.value = Date.now();
  clockTick.value = clockBaseAt.value;
  startClock();
}

/** 进行中阶段。后端给的是取数那一刻的已耗时，本地补上之后流逝的部分。 */
const detailStageProgress = computed(() => {
  const progress = currentDetail.value?.config.stage_progress;
  if (!progress) return null;
  const elapsed = (progress.elapsed_seconds ?? 0) + clockDriftSeconds.value;
  return {
    label: progress.label || progress.stage,
    elapsedSeconds: elapsed,
    elapsed_text: formatDurationMs(elapsed * 1000),
  };
});

/** 阶段耗时按合计换算成占比条，一眼看出耗时集中在哪一段。 */
const detailStageTimings = computed(() => {
  const timings = currentDetail.value?.config.stage_timings ?? [];
  // 并行阶段不占主链时间，计进合计会让各阶段之和超过总耗时。
  const total = timings.reduce(
    (sum, item) => sum + (item.parallel ? 0 : item.elapsed_seconds ?? 0),
    0
  );
  return timings.map((item) => {
    const elapsed = item.elapsed_seconds ?? 0;
    const label = item.label || item.stage;
    return {
      stage: item.stage,
      label: item.parallel ? `${label}（并行）` : label,
      elapsed_text: formatDurationMs(elapsed * 1000),
      parallel: Boolean(item.parallel),
      // 给个最小宽度，秒级阶段也要能看见。
      percent:
        total > 0 && !item.parallel
          ? Math.max(Math.round((elapsed / total) * 100), 2)
          : 0,
    };
  });
});

// 进行中的阶段也计进合计，否则首个阶段跑到一半会同时显示「进行中 24 秒 / 合计 0 秒」。
const detailStageTimingTotal = computed(() => {
  const finished = (currentDetail.value?.config.stage_timings ?? []).reduce(
    (sum, item) => sum + (item.parallel ? 0 : item.elapsed_seconds ?? 0),
    0
  );
  const active = detailStageProgress.value?.elapsedSeconds ?? 0;
  return formatDurationMs((finished + active) * 1000);
});

/** 渲染变量按行铺开，方便在详情里逐项对照实际生效的值。 */
const detailDebugRows = computed(() => {
  const summary = detailDebugSummary.value;
  if (!summary) return [];
  const rows: Array<{ label: string; value: string }> = [];
  const push = (label: string, value: string | undefined) => {
    if (!value) return;
    rows.push({ label, value });
  };
  push("贴纸主题", summary.sticker_theme_id ?? "");
  push("贴纸模板", summary.sticker_templates?.join(" / "));
  push("贴纸 / 动画", `${summary.sticker_count ?? 0} 个贴纸 · ${summary.animation_count ?? 0} 个动画`);
  push(
    "图形贴纸",
    `${summary.graphic_sticker_count ?? 0} 个${
      summary.graphic_sticker_tones?.length ? `（${summary.graphic_sticker_tones.join(" / ")}）` : ""
    }`
  );
  push("转场", summary.transitions?.join(" / "));
  push(
    "字幕 / 高亮",
    `${summary.subtitle_count ?? 0} 条字幕 · ${summary.highlight_keyword_count ?? 0} 个高亮词`
  );
  push(
    "BGM",
    summary.bgm_title ? `${summary.bgm_title}（${summary.bgm_tag || "未标注"}）` : "未使用"
  );
  push("响度目标", formatAudioMix(summary.audio_mix));
  push("渲染通道", summary.render_provider ?? "");
  push("渲染任务", summary.render_id ?? "");
  push("模型", formatDebugModels(summary.models));
  return rows;
});

/** 详情里的待审核稿。完整时间线 JSON 太大，详情接口不下发，展开折叠区时再单独取。 */
const detailReviewAsset = computed(() => {
  const detail = currentDetail.value;
  return detail ? findLatestCompletedAsset(detail, "review") : undefined;
});

const detailReviewMetadata = ref("");
const detailMetadataLoading = ref(false);

/** 展开「完整渲染元数据」时才拉一次，拉过就缓存，收起再展开不重复请求。 */
async function handleReviewMetadataExpand(activeNames: string | number | (string | number)[]) {
  const names = Array.isArray(activeNames) ? activeNames : [activeNames];
  if (!names.includes("raw") || detailReviewMetadata.value) return;
  const detail = currentDetail.value;
  const asset = detailReviewAsset.value;
  if (!detail || !asset) return;
  detailMetadataLoading.value = true;
  try {
    const response = await VideoProcessingAPI.getAssetMetadata(detail.id, asset.id);
    detailReviewMetadata.value = JSON.stringify(response.data.data.file_metadata, null, 2);
  } finally {
    detailMetadataLoading.value = false;
  }
}

// 换任务或重新生成后 review 产物会变，缓存的 JSON 要跟着清掉。
watch(
  () => detailReviewAsset.value?.id,
  () => {
    detailReviewMetadata.value = "";
  }
);

/** 提示词全文与参考帧地址都不随详情下发，展开「提示词调试」时才按任务取一次。 */
const taskDebug = ref<VideoTaskDebugInfo>();
const debugLoading = ref(false);
// 受控展开态：换任务时要能主动收起，否则会留着上一条任务的内容。
const debugActiveNames = ref<string[]>([]);

async function handleDebugExpand(activeNames: string | number | (string | number)[]) {
  const names = Array.isArray(activeNames) ? activeNames : [activeNames];
  if (!names.includes("prompts") || taskDebug.value) return;
  const detail = currentDetail.value;
  if (!detail) return;
  debugLoading.value = true;
  try {
    const response = await VideoProcessingAPI.getTaskDebug(detail.id);
    taskDebug.value = response.data.data;
  } finally {
    debugLoading.value = false;
  }
}

function formatAudioMix(audioMix: VideoTaskDebugSummary["audio_mix"]) {
  if (!audioMix) return "";
  const parts: string[] = [];
  if (audioMix.voice_loudness_target !== undefined) {
    parts.push(`人声 ${audioMix.voice_loudness_target}`);
  }
  if (audioMix.bgm_loudness_target !== undefined) {
    parts.push(`BGM ${audioMix.bgm_loudness_target}`);
  }
  if (audioMix.true_peak !== undefined) parts.push(`峰值 ${audioMix.true_peak}`);
  return parts.join(" · ");
}

function formatDebugModels(models: VideoTaskDebugSummary["models"]) {
  if (!models) return "";
  return Object.entries(models)
    .map(([key, value]) => `${debugModelLabels[key] ?? key}: ${value}`)
    .join(" · ");
}

let pollTimer: number | undefined;

/** 详情抽屉开着时跟着列表轮询一起刷新。
 *
 * 详情只在打开抽屉那一刻取一次，而本地补间每次取数都会归零 —— 只归零不换数据，
 * 显示值就会每轮掉回打开抽屉时的快照（涨 6 秒掉一次）。
 */
async function refreshDetailIfOpen() {
  const detail = currentDetail.value;
  if (!detailVisible.value || !detail) return;
  try {
    const response = await VideoProcessingAPI.getTask(detail.id);
    // 请求期间可能已关抽屉或换到别的任务，比对 id 再写回。
    if (currentDetail.value?.id === detail.id) {
      currentDetail.value = response.data.data;
    }
  } catch {
    // 详情刷新失败不影响列表，下一轮再补。
  }
}

async function loadBatches(showLoading = true) {
  if (showLoading) listLoading.value = true;
  try {
    const response = await VideoProcessingAPI.getBatches(query);
    batchList.value = response.data.data.items;
    total.value = response.data.data.total;
    // 先换数据再归零计时，顺序反了会短暂显示旧值。
    await refreshDetailIfOpen();
    resetClockBase();
  } finally {
    if (showLoading) listLoading.value = false;
  }
}

function handleFilterChange() {
  query.page_no = 1;
  loadBatches();
}

function handlePageSizeChange() {
  query.page_no = 1;
  loadBatches();
}

async function handleOpenDetail(task: VideoProcessingTask) {
  detailVisible.value = true;
  detailLoading.value = true;
  currentDetail.value = undefined;
  detailCoverAsset.value = undefined;
  // 上一条任务的调试信息与展开态都不能留。
  taskDebug.value = undefined;
  debugActiveNames.value = [];
  try {
    const response = await VideoProcessingAPI.getTask(task.id);
    const detail = response.data.data;
    currentDetail.value = detail;
    resetClockBase();
    detailCoverAsset.value = findLatestCompletedAsset(detail, "cover");
  } finally {
    detailLoading.value = false;
  }
}

async function handleTaskAction(payload: {
  action: "cancel" | "retry" | "preview" | "approve" | "regenerate" | "download";
  task: VideoProcessingTask;
}) {
  if (payload.action === "cancel") {
    await handleCancelTask(payload.task);
    return;
  }
  if (payload.action === "retry") {
    await handleRetryTask(payload.task);
    return;
  }
  if (payload.action === "preview") {
    await handlePreview(payload.task);
    return;
  }
  if (payload.action === "approve") {
    await handleApproveReview(payload.task);
    return;
  }
  if (payload.action === "regenerate") {
    await handleRegenerateReview(payload.task);
    return;
  }
  await handleDownloadOutput(payload.task);
}

async function handleCancelTask(task: VideoProcessingTask) {
  await ElMessageBox.confirm(`确认取消任务“${task.title}”吗？`, "取消任务", {
    type: "warning",
    confirmButtonText: "确认取消",
    cancelButtonText: "返回",
  });
  await VideoProcessingAPI.cancelTask(task.id);
  await loadBatches(false);
}

async function handleRetryTask(task: VideoProcessingTask) {
  await VideoProcessingAPI.retryTask(task.id);
  await loadBatches(false);
}

async function handlePreview(task: VideoProcessingTask) {
  previewVisible.value = true;
  previewLoading.value = true;
  previewTask.value = undefined;
  previewOutputAsset.value = undefined;
  previewCoverAsset.value = undefined;
  previewSubtitleAsset.value = undefined;
  previewUrl.value = "";

  try {
    const detailResponse = await VideoProcessingAPI.getTask(task.id);
    const detail = detailResponse.data.data;
    const previewAsset = findLatestCompletedAsset(
      detail,
      detail.status === "reviewing" ? "review" : "output"
    );
    if (!previewAsset) {
      ElMessage.warning(detail.status === "reviewing" ? "当前任务没有待审核稿" : "当前任务没有成片");
      return;
    }

    const urlResponse = await VideoProcessingAPI.getAssetDownloadUrl(detail.id, previewAsset.id);
    previewTask.value = detail;
    previewOutputAsset.value = previewAsset;
    previewCoverAsset.value = findLatestCompletedAsset(detail, "cover");
    previewSubtitleAsset.value = findLatestCompletedAsset(detail, "subtitle");
    previewUrl.value = urlResponse.data.data.url;
  } finally {
    previewLoading.value = false;
  }
}

async function handleApproveReview(task: VideoProcessingTask) {
  await ElMessageBox.confirm(`确认通过任务“${task.title}”的待审核稿吗？`, "审核通过", {
    type: "success",
    confirmButtonText: "确认通过",
    cancelButtonText: "返回",
  });

  const response = await VideoProcessingAPI.reviewTask(task.id, { action: "approve" });
  ElMessage.success("待审核稿已确认为最终成片");
  await syncTaskAfterReview(response.data.data);
}

async function handleRegenerateReview(task: VideoProcessingTask) {
  const isFinished = task.status === "succeeded";
  const { value } = await ElMessageBox.prompt(
    isFinished
      ? "重新生成会按高级设置里当前的提示词与模型重跑一整条流水线。可以填写调整说明，例如“节奏更快一点，BGM 小一点”。不填写则直接重新随机生成。"
      : "可以填写调整说明，例如“节奏更快一点，BGM 小一点”。不填写则直接重新随机生成。",
    isFinished ? "重新生成（用最新配置）" : "重新生成",
    {
      confirmButtonText: "重新生成",
      cancelButtonText: "返回",
      inputType: "textarea",
      inputPlaceholder: "请输入调整说明（可选）",
    }
  );

  const response = await VideoProcessingAPI.reviewTask(task.id, {
    action: "regenerate",
    adjustment_prompt: value || undefined,
  });
  ElMessage.success("任务已重新进入处理队列");
  await syncTaskAfterReview(response.data.data);
}

async function syncTaskAfterReview(detail: VideoProcessingTaskDetail) {
  previewVisible.value = false;
  previewUrl.value = "";
  previewTask.value = undefined;
  previewOutputAsset.value = undefined;
  previewCoverAsset.value = undefined;
  previewSubtitleAsset.value = undefined;
  // 重新生成后本次记录的提示词与参考帧都作废，展开态一起收起。
  taskDebug.value = undefined;
  debugActiveNames.value = [];
  currentDetail.value = currentDetail.value?.id === detail.id ? detail : currentDetail.value;
  await loadBatches(false);
}

async function handleDownloadOutput(task: VideoProcessingTask) {
  const detailResponse = await VideoProcessingAPI.getTask(task.id);
  const detail = detailResponse.data.data;
  const outputAsset = findLatestCompletedAsset(detail, "output");
  if (!outputAsset) {
    ElMessage.warning("当前任务没有可下载的成片");
    return;
  }
  await downloadAsset(detail, outputAsset);
}

async function downloadAsset(task: VideoProcessingTask, asset: VideoTaskAsset) {
  const response = await VideoProcessingAPI.getAssetDownloadUrl(task.id, asset.id, true);
  const link = document.createElement("a");
  link.href = response.data.data.url;
  link.download = asset.file_name;
  link.rel = "noopener";
  link.target = "_blank";
  link.click();
}

function handlePreviewClosed() {
  previewUrl.value = "";
  previewTask.value = undefined;
  previewOutputAsset.value = undefined;
  previewCoverAsset.value = undefined;
  previewSubtitleAsset.value = undefined;
}

function getTaskStatusMeta(status: VideoTaskStatus) {
  return statusMeta[status];
}

function getStageLabel(stage: string) {
  return stageLabels[stage] || stage;
}

function getStyleLabel(style: VideoStylePreset) {
  return styleLabels[style];
}

function getAssetRoleLabel(role: VideoAssetRole) {
  return assetRoleLabels[role];
}

function findLatestCompletedAsset(
  task: VideoProcessingTaskDetail,
  role: VideoAssetRole
): VideoTaskAsset | undefined {
  return task.assets
    .filter((asset) => asset.asset_role === role && asset.upload_status === "completed")
    .sort((left, right) => right.id - left.id)[0];
}

function getAssetStatusLabel(status: VideoTaskAsset["upload_status"]) {
  return {
    pending: "待上传",
    uploading: "上传中",
    completed: "已完成",
    failed: "失败",
  }[status];
}

function getAssetStatusType(status: VideoTaskAsset["upload_status"]): TagType {
  return {
    pending: "info",
    uploading: "primary",
    completed: "success",
    failed: "danger",
  }[status] as TagType;
}

function isOutputAsset(asset: VideoTaskAsset) {
  return (
    (asset.asset_role === "review" ||
      asset.asset_role === "output" ||
      asset.asset_role === "subtitle" ||
      asset.asset_role === "cover" ||
      asset.asset_role === "ending") &&
    asset.upload_status === "completed"
  );
}

/** 已完成的任务也要能重跑：改完高级设置里的提示词 / 模型后按最新配置重出一版。 */
function canRegenerate(task: VideoProcessingTask) {
  return task.status === "reviewing" || task.status === "succeeded";
}

function getTaskFinishedTimeLabel(task: VideoProcessingTask) {
  return task.finished_time ? formatToDateTime(task.finished_time) : "处理中";
}

function getTaskDurationLabel(task: VideoProcessingTask) {
  if (!task.finished_time) return "未结束";
  const startedAt = parseTaskTimestamp(task.config.attempt_started_time ?? "");
  const finishedAt = parseTaskTimestamp(task.finished_time);
  if (startedAt === undefined || finishedAt === undefined) return "-";
  return formatDurationMs(Math.max(finishedAt - startedAt, 0));
}

function parseTaskTimestamp(value: string) {
  const timestamp = new Date(value.replace(" ", "T")).getTime();
  return Number.isNaN(timestamp) ? undefined : timestamp;
}

function formatDurationMs(milliseconds: number) {
  const totalSeconds = Math.round(milliseconds / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) return `${hours}小时${minutes}分${seconds}秒`;
  if (minutes > 0) return `${minutes}分${seconds}秒`;
  return `${seconds}秒`;
}

function formatFileSize(bytes: number) {
  if (!bytes || bytes <= 0) return "-";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let index = 0;
  // 用循环而不是 log 取档位，避免 1024 的整数次幂因浮点误差掉档。
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${index === 0 ? value : value.toFixed(1)} ${units[index]}`;
}

function startPolling() {
  if (pollTimer !== undefined) return;
  pollTimer = window.setInterval(() => {
    // 没有进行中的批次就不打接口，避免停留在已完成列表上空转。
    if (!hasActiveBatch()) return;
    loadBatches(false);
  }, 6000);
}

function stopPolling() {
  if (pollTimer === undefined) return;
  window.clearInterval(pollTimer);
  pollTimer = undefined;
}

function hasActiveBatch() {
  return batchList.value.some((batch) =>
    ["uploading", "queued", "processing", "reviewing"].includes(batch.status)
  );
}

function handleVisibilityChange() {
  // 标签页在后台时停掉轮询，回到前台立即补一次最新状态。
  if (document.hidden) {
    stopPolling();
    return;
  }
  loadBatches(false);
  startPolling();
}

onMounted(() => {
  loadBatches();
  startPolling();
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onBeforeUnmount(() => {
  stopPolling();
  stopClock();
  document.removeEventListener("visibilitychange", handleVisibilityChange);
});
</script>

<style scoped src="./index.scss" lang="scss"></style>
