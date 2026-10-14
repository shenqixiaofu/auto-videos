<template>
  <el-dialog v-model="dialogVisible" title="🖼️ 背景瞬移历史记录" width="720px" destroy-on-close>
    <div v-if="historyList.length === 0" class="text-center text-gray-400 py-8">
      <el-empty description="暂无瞬移记录" :image-size="80" />
    </div>

    <el-timeline v-else class="mt-4 pr-4">
      <el-timeline-item
        v-for="item in historyList"
        :key="item.v"
        :timestamp="item.created_at"
        :type="
          item.status === 'success'
            ? 'success'
            : item.status === 'processing'
              ? 'primary'
              : 'danger'
        "
        placement="top"
      >
        <el-card shadow="hover" class="mb-2 border-gray-100">
          <div class="flex justify-between items-center mb-2">
            <span class="font-bold text-sm text-gray-700">版本 v{{ item.v }}</span>
            <el-tag
              size="small"
              effect="light"
              :type="
                item.status === 'success'
                  ? 'success'
                  : item.status === 'processing'
                    ? 'primary'
                    : 'danger'
              "
            >
              {{
                item.status === "success"
                  ? "融合成功"
                  : item.status === "processing"
                    ? "处理中..."
                    : "失败"
              }}
            </el-tag>
          </div>

          <div class="flex gap-4 mt-3">
            <div class="flex flex-col items-center w-1/3">
              <span class="text-xs text-gray-400 mb-1">目标背景</span>
              <el-image
                :src="item.target_bg_image"
                class="w-full h-24 rounded border border-gray-200"
                fit="cover"
                :preview-src-list="[item.target_bg_image]"
                :preview-teleported="true"
              />
            </div>

            <div class="flex flex-col items-center w-2/3">
              <span class="text-xs text-gray-400 mb-1">融合结果</span>
              <el-image
                v-if="item.status === 'success' && item.result_url"
                :src="item.result_url"
                class="w-full h-24 rounded shadow-sm border border-blue-200 cursor-pointer hover:opacity-90 transition-opacity"
                fit="cover"
                :preview-src-list="[item.result_url, item.target_bg_image]"
                :preview-teleported="true"
                title="点击放大预览对比"
              />
              <div
                v-else-if="item.status === 'processing'"
                class="w-full h-24 flex flex-col items-center justify-center bg-gray-50 border border-dashed rounded text-gray-400 text-xs"
              >
                <el-icon class="is-loading mb-1" :size="20"><Loading /></el-icon>
                正在生成中...
              </div>
              <div
                v-else
                class="w-full h-24 flex items-center justify-center bg-red-50 border border-red-100 rounded text-red-400 text-xs text-center px-2"
              >
                {{ item.error_msg || "融合失败" }}
              </div>
            </div>
          </div>

          <div class="mt-3 space-y-2 text-xs text-gray-600">
            <div class="flex items-start gap-2">
              <span class="shrink-0 text-gray-400">耗时</span>
              <span>{{ formatDuration(item) }}</span>
            </div>
            <div class="flex items-start gap-2">
              <span class="shrink-0 text-gray-400">提示词</span>
              <div
                class="min-w-0 flex-1 rounded border border-gray-100 bg-gray-50 px-2 py-1.5 whitespace-pre-wrap break-all max-h-24 overflow-y-auto"
              >
                {{ getPromptText(item) }}
              </div>
            </div>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Loading } from "@element-plus/icons-vue";

interface BgHistoryItem {
  v: number;
  status: string;
  created_at?: string;
  target_bg_image?: string;
  result_url?: string;
  error_msg?: string;
  custom_prompt?: string;
  final_prompt?: string;
  prompt?: string;
  duration?: number | string | null;
  duration_seconds?: number | string | null;
}

// 1. 定义父组件传进来的 Props
const props = defineProps<{
  modelValue: boolean; // 用于控制弹窗显隐的 v-model
  historyList: BgHistoryItem[]; // 历史记录数组
}>();

// 2. 🚀 核心修改：删除了冗余的 apply 事件，只保留弹窗开关控制
const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
}>();

// 3. 计算属性：实现双向绑定控制弹窗显隐
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const formatDuration = (item: BgHistoryItem) => {
  if (item.status === "processing") return "进行中";

  const rawSeconds = item.duration_seconds ?? item.duration;
  const seconds = Number(rawSeconds);
  if (!Number.isFinite(seconds) || seconds < 0) return "未记录";

  if (seconds < 60) {
    return `${seconds % 1 === 0 ? seconds.toFixed(0) : seconds.toFixed(1)} 秒`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainSeconds = seconds - minutes * 60;
  const secondText =
    remainSeconds % 1 === 0 ? remainSeconds.toFixed(0) : remainSeconds.toFixed(1);
  return `${minutes} 分 ${secondText} 秒`;
};

const getPromptText = (item: BgHistoryItem) =>
  item.custom_prompt || item.prompt || item.final_prompt || "未记录";
</script>

<style scoped>
/* 可以在这里放弹窗专属的局部样式 */
</style>
