<template>
  <div class="table-shell">
    <el-table v-loading="props.loading" :data="props.batches" stripe class="batch-table" row-key="id">
      <template #empty>
        <el-empty :image-size="72" description="暂无自动剪辑批次" />
      </template>

      <el-table-column type="expand" width="52">
        <template #default="{ row }">
          <div class="batch-expand">
            <el-table :data="row.tasks" size="small" border class="task-table">
              <el-table-column label="封面" width="96" align="center">
                <template #default="{ row: task }">
                  <div class="task-cover-cell">
                    <img
                      v-if="task.cover_preview_url"
                      class="task-cover-thumb"
                      :src="task.cover_preview_url"
                      alt="封面"
                    />
                    <span v-else class="task-cover-placeholder">生成中</span>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="任务" min-width="220">
                <template #default="{ row: task }">
                  <button class="task-name-button" type="button" @click="emit('task-open', task)">
                    <span class="task-name">{{ task.title }}</span>
                    <span class="task-number">{{ task.task_no }} · #{{ task.batch_index }}</span>
                  </button>
                </template>
              </el-table-column>

              <el-table-column label="当前阶段" min-width="160">
                <template #default="{ row: task }">
                  <div class="stage-cell">
                    <span>{{ getStageLabel(task.current_stage) }}</span>
                    <span v-if="getTaskStageProgressText(task)" class="stage-cell__progress">
                      {{ getTaskStageProgressText(task) }}
                    </span>
                    <el-progress
                      :percentage="task.progress"
                      :stroke-width="6"
                      :status="task.status === 'failed' ? 'exception' : undefined"
                    />
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="渲染变量" min-width="210">
                <template #default="{ row: task }">
                  <div class="task-debug-cell">
                    <span v-if="getTaskDebugLabel(task)">{{ getTaskDebugLabel(task) }}</span>
                    <span v-else class="task-debug-empty">暂无记录</span>
                    <span class="task-debug-model">{{ getTaskDebugModel(task) }}</span>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="状态" width="96" align="center">
                <template #default="{ row: task }">
                  <el-tooltip v-if="task.error_message" :content="task.error_message" placement="top">
                    <el-tag :type="getTaskStatusMeta(task.status).type" size="small">
                      {{ getTaskStatusMeta(task.status).label }}
                    </el-tag>
                  </el-tooltip>
                  <el-tag v-else :type="getTaskStatusMeta(task.status).type" size="small">
                    {{ getTaskStatusMeta(task.status).label }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column label="操作" width="250" fixed="right" align="center">
                <template #default="{ row: task }">
                  <div class="table-actions">
                    <el-tooltip content="查看详情">
                      <el-button
                        v-hasPerm="['module_video:processing:query']"
                        :icon="View"
                        circle
                        aria-label="查看任务详情"
                        @click="emit('task-open', task)"
                      />
                    </el-tooltip>
                    <el-tooltip v-if="canCancel(task)" content="取消任务">
                      <el-button
                        v-hasPerm="['module_video:processing:cancel']"
                        :icon="CircleClose"
                        type="danger"
                        plain
                        circle
                        aria-label="取消任务"
                        @click="emit('task-action', { action: 'cancel', task })"
                      />
                    </el-tooltip>
                    <el-tooltip v-if="canRetry(task)" content="重试任务">
                      <el-button
                        v-hasPerm="['module_video:processing:retry']"
                        :icon="RefreshRight"
                        type="warning"
                        plain
                        circle
                        aria-label="重试任务"
                        @click="emit('task-action', { action: 'retry', task })"
                      />
                    </el-tooltip>
                    <el-tooltip v-if="canPreview(task)" :content="getPreviewActionLabel(task)">
                      <el-button
                        v-hasPerm="['module_video:processing:download']"
                        :icon="VideoPlay"
                        type="primary"
                        plain
                        circle
                        aria-label="预览成片"
                        @click="emit('task-action', { action: 'preview', task })"
                      />
                    </el-tooltip>
                    <el-tooltip v-if="task.status === 'reviewing'" content="审核通过">
                      <el-button
                        v-hasPerm="['module_video:processing:create']"
                        :icon="CircleCheck"
                        type="success"
                        plain
                        circle
                        aria-label="审核通过"
                        @click="emit('task-action', { action: 'approve', task })"
                      />
                    </el-tooltip>
                    <el-tooltip v-if="canRegenerate(task)" :content="getRegenerateLabel(task)">
                      <el-button
                        v-hasPerm="['module_video:processing:create']"
                        :icon="RefreshRight"
                        type="warning"
                        plain
                        circle
                        aria-label="重新生成"
                        @click="emit('task-action', { action: 'regenerate', task })"
                      />
                    </el-tooltip>
                    <el-tooltip v-if="task.status === 'succeeded'" content="下载成片">
                      <el-button
                        v-hasPerm="['module_video:processing:download']"
                        :icon="Download"
                        type="success"
                        plain
                        circle
                        aria-label="下载成片"
                        @click="emit('task-action', { action: 'download', task })"
                      />
                    </el-tooltip>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="批次" min-width="240">
        <template #default="{ row }">
          <div class="batch-name-cell">
            <img
              v-if="row.cover_preview_url"
              class="batch-cover-thumb"
              :src="row.cover_preview_url"
              alt="批次封面"
            />
            <div class="batch-name-copy">
              <span class="batch-name">{{ row.batch_name }}</span>
              <span class="batch-number">{{ row.batch_no }}</span>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="任务数" min-width="118">
        <template #default="{ row }">
          <div class="count-cell">
            <strong>{{ row.task_count }}</strong>
            <span>/ {{ row.expected_count }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="当前阶段" min-width="180">
        <template #default="{ row }">
          <div class="stage-cell">
            <span>{{ getStageLabel(row.current_stage) }}</span>
            <el-progress
              :percentage="row.progress"
              :stroke-width="6"
              :status="row.status === 'failed' ? 'exception' : undefined"
            />
          </div>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="96" align="center">
        <template #default="{ row }">
          <el-tooltip v-if="row.error_message" :content="row.error_message" placement="top">
            <el-tag :type="getTaskStatusMeta(row.status).type" size="small">
              {{ getTaskStatusMeta(row.status).label }}
            </el-tag>
          </el-tooltip>
          <el-tag v-else :type="getTaskStatusMeta(row.status).type" size="small">
            {{ getTaskStatusMeta(row.status).label }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="创建时间" min-width="155">
        <template #default="{ row }">
          <span class="time-cell">{{ formatToDateTime(row.created_time) }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { formatToDateTime } from "@/utils/dateUtil";
import {
  CircleCheck,
  CircleClose,
  Download,
  RefreshRight,
  View,
  VideoPlay,
} from "@element-plus/icons-vue";
import type {
  VideoProcessingBatch,
  VideoProcessingTask,
  VideoTaskStatus,
} from "@/api/module_video/processing";

type TagType = "primary" | "success" | "warning" | "info" | "danger";

const props = defineProps<{
  batches: VideoProcessingBatch[];
  loading: boolean;
  /** 自上次取数以来流逝的秒数，父组件每秒推进，用来把阶段耗时补成实时值。 */
  clockDrift?: number;
}>();

const emit = defineEmits<{
  (event: "task-open", task: VideoProcessingTask): void;
  (
    event: "task-action",
    payload: {
      action: "cancel" | "retry" | "preview" | "approve" | "regenerate" | "download";
      task: VideoProcessingTask;
    }
  ): void;
}>();

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

function getTaskStatusMeta(status: VideoTaskStatus) {
  return statusMeta[status];
}

function getStageLabel(stage: string) {
  return stageLabels[stage] || stage;
}

/** 细粒度阶段 + 已耗时。后端给的是取数那刻的数值，加上本地流逝补间。 */
function getTaskStageProgressText(task: VideoProcessingTask) {
  const progress = task.config?.stage_progress;
  if (!progress) return "";
  const elapsed = (progress.elapsed_seconds ?? 0) + (props.clockDrift ?? 0);
  return `${progress.label || progress.stage} · 已用 ${formatElapsed(elapsed)}`;
}

function formatElapsed(seconds: number) {
  const total = Math.max(Math.floor(seconds), 0);
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return minutes > 0 ? `${minutes}分${rest}秒` : `${rest}秒`;
}

function canCancel(task: VideoProcessingTask) {
  return ["draft", "uploading", "queued", "processing", "reviewing"].includes(task.status);
}

function canRetry(task: VideoProcessingTask) {
  return task.status === "failed" || task.status === "cancelled";
}

/** 已完成的任务也要能重跑：改完高级设置里的提示词 / 模型后按最新配置重出一版。 */
function canRegenerate(task: VideoProcessingTask) {
  return task.status === "reviewing" || task.status === "succeeded";
}

function getRegenerateLabel(task: VideoProcessingTask) {
  return task.status === "succeeded" ? "用最新配置重新生成" : "重新生成";
}

function canPreview(task: VideoProcessingTask) {
  return task.status === "reviewing" || task.status === "succeeded";
}

function getPreviewActionLabel(task: VideoProcessingTask) {
  return task.status === "reviewing" ? "预览待审核稿" : "预览成片";
}

/** 列表里只铺一行核心变量，完整信息在任务详情的渲染变量面板。 */
function getTaskDebugLabel(task: VideoProcessingTask) {
  const summary = task.config?.debug_summary;
  if (!summary) return "";
  return [
    summary.sticker_theme_id,
    `${summary.sticker_count ?? 0} 贴纸`,
    summary.bgm_title ? `BGM ${summary.bgm_title}` : "无 BGM",
  ]
    .filter(Boolean)
    .join(" · ");
}

function getTaskDebugModel(task: VideoProcessingTask) {
  const models = task.config?.debug_summary?.models;
  if (!models) return "";
  return `创意规划 ${models.creative_planner ?? "-"} · 转写 ${models.asr ?? "-"}`;
}
</script>

<style scoped src="./VideoProcessingBatchTable.scss" lang="scss"></style>
