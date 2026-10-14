<template>
  <section class="workspace-panel creation-panel" aria-labelledby="creation-title">
    <div class="panel-header">
      <div>
        <h3 id="creation-title">批量导入</h3>
        <span class="panel-count">{{ batchSourceFiles.length }} 个视频</span>
      </div>
    </div>

    <div class="panel-body">
      <div class="batch-import-card">
        <div class="batch-import-header">
          <div>
            <h4>文件夹导入</h4>
            <span>每个视频会单独创建一个任务</span>
          </div>
          <el-button :disabled="batchSubmitting" @click="openBatchFolderPicker">
            选择文件夹
          </el-button>
        </div>

        <input
          ref="batchFolderInputRef"
          class="batch-folder-input"
          type="file"
          webkitdirectory
          multiple
          accept="video/*"
          @change="handleBatchFolderChange"
        />

        <div class="batch-style-card">
          <div class="batch-style-header">
            <div>
              <h4>剪辑风格</h4>
              <span>整批任务共用同一种风格</span>
            </div>
            <el-select v-model="stylePreset" class="batch-style-select" :disabled="batchSubmitting">
              <el-option
                v-for="item in VIDEO_STYLE_PRESET_OPTIONS"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </div>
        </div>

        <div v-if="batchSourceFiles.length" class="batch-file-preview">
          <span class="batch-file-count">{{ batchSourceFiles.length }} 个视频</span>
          <span class="batch-folder-name">{{ batchFolderName }}</span>
          <div class="batch-file-tags">
            <el-tag
              v-for="file in batchPreviewFiles"
              :key="file.webkitRelativePath || file.name"
              size="small"
              type="info"
            >
              {{ file.name }}
            </el-tag>
            <el-tag v-if="batchHiddenFileCount > 0" size="small" type="info">
              +{{ batchHiddenFileCount }}
            </el-tag>
          </div>
        </div>

        <div class="batch-ending-card">
          <div class="batch-ending-header">
            <div>
              <h4>共用片尾</h4>
              <span>整个批次共用一个片尾视频，可选</span>
            </div>
            <el-button :disabled="batchSubmitting" @click="openEndingPicker">
              选择片尾
            </el-button>
          </div>

          <input
            ref="endingInputRef"
            class="batch-ending-input"
            type="file"
            accept="video/*"
            @change="handleEndingChange"
          />

          <div v-if="endingFile" class="batch-ending-preview">
            <span class="batch-ending-name">{{ endingFile.name }}</span>
            <el-button :disabled="batchSubmitting" @click="clearEndingSelection">
              移除片尾
            </el-button>
          </div>
        </div>

        <div v-if="batchSourceFiles.length" class="batch-import-actions">
          <el-button :disabled="batchSubmitting" @click="clearBatchFolderSelection">
            清空选择
          </el-button>
          <el-button
            type="success"
            :loading="batchSubmitting"
            :disabled="batchSubmitting"
            @click="handleBatchImport"
          >
            开始批量导入
          </el-button>
        </div>

        <div v-if="batchSubmitting" class="submission-progress batch-progress">
          <div class="submission-progress__label">
            <span>{{ batchCurrentLabel }}</span>
            <strong>{{ batchCurrentPercent }}%</strong>
          </div>
          <el-progress :percentage="batchCurrentPercent" :show-text="false" :stroke-width="7" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  uploadVideoMultipart,
  VideoProcessingAPI,
  VIDEO_STYLE_PRESET_OPTIONS,
  type VideoStylePreset,
} from "@/api/module_video/processing";

const emit = defineEmits<{
  (event: "submitted"): void;
}>();

const batchFolderInputRef = ref<HTMLInputElement>();
const endingInputRef = ref<HTMLInputElement>();
const batchSourceFiles = ref<File[]>([]);
const endingFile = ref<File | null>(null);
const batchSubmitting = ref(false);
const batchCurrentLabel = ref("正在准备批量导入");
const batchCurrentPercent = ref(0);
const stylePreset = ref<VideoStylePreset>("vlog");

const batchFolderName = computed(() => {
  const firstFile = batchSourceFiles.value[0];
  if (!firstFile) return "";
  return firstFile.webkitRelativePath.split("/")[0] || "文件夹";
});
const batchPreviewFiles = computed(() => batchSourceFiles.value.slice(0, 4));
const batchHiddenFileCount = computed(
  () => Math.max(batchSourceFiles.value.length - batchPreviewFiles.value.length, 0)
);

function openBatchFolderPicker() {
  batchFolderInputRef.value?.click();
}

function clearBatchFolderSelection() {
  batchSourceFiles.value = [];
  batchCurrentLabel.value = "正在准备批量导入";
  batchCurrentPercent.value = 0;
  if (batchFolderInputRef.value) {
    batchFolderInputRef.value.value = "";
  }
  clearEndingSelection();
}

function openEndingPicker() {
  endingInputRef.value?.click();
}

function handleEndingChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("video/")) {
    ElMessage.error("片尾视频文件格式不正确");
    input.value = "";
    return;
  }
  endingFile.value = file;
  input.value = "";
}

function clearEndingSelection() {
  endingFile.value = null;
  if (endingInputRef.value) {
    endingInputRef.value.value = "";
  }
}

function handleBatchFolderChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? [])
    .filter((file) => file.type.startsWith("video/"))
    .sort((left, right) =>
      (left.webkitRelativePath || left.name).localeCompare(right.webkitRelativePath || right.name)
    );
  if (!files.length) {
    batchSourceFiles.value = [];
    batchCurrentLabel.value = "批量导入已就绪";
    batchCurrentPercent.value = 0;
    ElMessage.warning("文件夹中没有可导入的视频");
    input.value = "";
    return;
  }
  batchSourceFiles.value = files;
  batchCurrentLabel.value = "批量导入已就绪";
  batchCurrentPercent.value = 0;
  input.value = "";
}

function buildTaskTitleFromFile(file: File) {
  const relativeName = file.webkitRelativePath || file.name;
  return relativeName.replace(/\.[^.]+$/, "").replaceAll("/", " - ").slice(0, 128).trim();
}

async function uploadTaskAsset(taskId: number, file: File, onProgress?: (percent: number) => void) {
  await uploadAssetByRole(taskId, "source", file, onProgress);
}

async function uploadEndingAsset(taskId: number, file: File, onProgress?: (percent: number) => void) {
  await uploadAssetByRole(taskId, "ending", file, onProgress);
}

async function uploadAssetByRole(
  taskId: number,
  assetRole: "source" | "ending",
  file: File,
  onProgress?: (percent: number) => void
) {
  const initiateResponse = await VideoProcessingAPI.initiateAsset(taskId, {
    asset_role: assetRole,
    file_name: file.name,
    content_type: file.type,
    file_size: file.size,
  });
  const session = initiateResponse.data.data;
  const parts = await uploadVideoMultipart(
    file,
    session,
    (progress) => {
      onProgress?.(progress.percent);
    },
    async (partNumbers) => {
      const response = await VideoProcessingAPI.refreshAssetParts(taskId, session.asset_id, {
        upload_id: session.upload_id,
        part_numbers: partNumbers,
      });
      return response.data.data;
    }
  );

  await VideoProcessingAPI.completeAsset(taskId, session.asset_id, {
    upload_id: session.upload_id,
    parts,
  });
}

async function handleBatchImport() {
  const files = [...batchSourceFiles.value];
  if (!files.length) {
    ElMessage.warning("请选择包含视频文件的文件夹");
    return;
  }

  batchSubmitting.value = true;
  batchCurrentPercent.value = 0;
  batchCurrentLabel.value = "正在批量导入";
  const failures: string[] = [];
  let batchSucceeded = false;

  try {
    try {
      const batchResponse = await VideoProcessingAPI.createBatch({
        batch_name: batchFolderName.value || "批量导入",
        batch_type: "folder",
        expected_count: files.length,
      });
      const batchId = batchResponse.data.data.id;

      for (const [index, file] of files.entries()) {
        const taskTitle = buildTaskTitleFromFile(file);
        batchCurrentLabel.value = `${index + 1}/${files.length} ${file.name}`;
        batchCurrentPercent.value = 0;
        let createdTaskId: number | undefined;

        try {
          const createResponse = await VideoProcessingAPI.createTask({
            title: taskTitle,
            aspect_ratio: "9:16",
            style_preset: stylePreset.value,
            batch_id: batchId,
            batch_index: index + 1,
          });
          createdTaskId = createResponse.data.data.id;

          await uploadTaskAsset(createdTaskId, file, (percent) => {
            batchCurrentPercent.value = percent;
          });
          if (endingFile.value) {
            batchCurrentLabel.value = `${index + 1}/${files.length} ${file.name} · 上传片尾`;
            await uploadEndingAsset(createdTaskId, endingFile.value, (percent) => {
              batchCurrentPercent.value = percent;
            });
          }
          await VideoProcessingAPI.submitTask(createdTaskId);
        } catch (error) {
          if (createdTaskId) {
            try {
              await VideoProcessingAPI.cancelTask(createdTaskId);
            } catch {
              ElMessage.error(`任务 ${taskTitle} 取消失败，请在列表中手动处理`);
            }
          }
          const message = error instanceof Error ? error.message : "批量导入失败";
          failures.push(`${file.name}: ${message}`);
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "批量导入失败";
      ElMessage.error(message);
      return;
    }

    if (failures.length === 0) {
      ElMessage.success(`批量导入完成，共 ${files.length} 个视频`);
    } else {
      ElMessage.warning(`批量导入完成，成功 ${files.length - failures.length}/${files.length}`);
    }
    clearBatchFolderSelection();
    emit("submitted");
    batchSucceeded = true;
  } finally {
    batchSubmitting.value = false;
    batchCurrentLabel.value = batchSucceeded ? "批量导入已完成" : "批量导入失败";
    batchCurrentPercent.value = 0;
  }
}
</script>

<style scoped src="./VideoProcessingImportPanel.scss" lang="scss"></style>
