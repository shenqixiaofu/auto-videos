<template>
  <section v-if="canConfig" class="workspace-panel advanced-panel" aria-labelledby="advanced-title">
    <el-collapse v-model="activeNames" class="advanced-collapse">
      <el-collapse-item name="advanced">
        <template #title>
          <div class="advanced-title">
            <h3 id="advanced-title">高级设置</h3>
            <span class="advanced-title__hint">
              全局生效 · 仅管理员 · 当前 v{{ config?.version ?? "-" }}
            </span>
          </div>
        </template>

        <div v-loading="loading" class="advanced-body">
          <el-form label-position="top" size="small">
            <el-form-item label="封面生图通道">
              <el-select v-model="form.cover_image_provider" class="advanced-field">
                <el-option label="中转站（relay）" value="relay" />
                <el-option label="火山方舟（seedream）" value="seedream" />
              </el-select>
            </el-form-item>

            <el-form-item label="中转站生图模型">
              <el-select
                v-model="form.relay_image_model"
                class="advanced-field"
                filterable
                allow-create
                default-first-option
                :loading="modelsLoading"
                placeholder="选择或直接填写模型名"
              >
                <el-option
                  v-for="item in imageModels"
                  :key="item.name"
                  :label="item.name"
                  :value="item.name"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="中转站生图尺寸">
              <el-input
                v-model="form.relay_image_size"
                class="advanced-field"
                placeholder="1024x1536"
              />
            </el-form-item>

            <el-form-item label="封面策划模型">
              <el-input v-model="form.cover_summary_model" class="advanced-field" />
            </el-form-item>

            <el-form-item label="创意规划模型">
              <el-input v-model="form.creative_planner_model" class="advanced-field" />
            </el-form-item>

            <el-form-item label="封面生图提示词模板">
              <el-input
                v-model="form.cover_prompt_template"
                type="textarea"
                :rows="6"
                resize="vertical"
                placeholder="留空则使用内置默认模板"
              />
            </el-form-item>

            <el-form-item label="创意规划提示词模板">
              <el-input
                v-model="form.planner_prompt_template"
                type="textarea"
                :rows="8"
                resize="vertical"
                placeholder="留空则使用内置默认模板"
              />
            </el-form-item>
          </el-form>

          <div class="advanced-actions">
            <el-button :disabled="saving" @click="restoreDefaults">还原内置默认</el-button>
            <el-button :disabled="saving || loading" @click="loadConfig">重新加载</el-button>
            <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
          </div>

          <p v-if="config?.updated_time" class="advanced-meta">
            最近更新：{{ config.updated_time }}
            <span v-if="config?.updated_by">· {{ config.updated_by }}</span>
          </p>
        </div>
      </el-collapse-item>
    </el-collapse>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { ROLE_ROOT } from "@/constants";
import { useUserStore } from "@/store";
import {
  VideoProcessingAPI,
  type VideoCoverImageModel,
  type VideoCoverImageProvider,
  type VideoProcessingConfig,
  type VideoProcessingConfigUpdateParams,
} from "@/api/module_video/processing";

const PERMISSION = "module_video:processing:config";

const userStore = useUserStore();
const activeNames = ref<string[]>([]);
const loading = ref(false);
const saving = ref(false);
const modelsLoading = ref(false);
const config = ref<VideoProcessingConfig>();
const imageModels = ref<VideoCoverImageModel[]>([]);

const form = reactive<{
  cover_image_provider: VideoCoverImageProvider;
  relay_image_model: string;
  relay_image_size: string;
  cover_summary_model: string;
  creative_planner_model: string;
  cover_prompt_template: string;
  planner_prompt_template: string;
}>({
  cover_image_provider: "relay",
  relay_image_model: "",
  relay_image_size: "",
  cover_summary_model: "",
  creative_planner_model: "",
  cover_prompt_template: "",
  planner_prompt_template: "",
});

// 超级管理员默认持有全部权限，普通角色看后端下发的权限串。
const canConfig = computed(() => {
  const roleCodes = userStore.basicInfo.roles?.map((role) => role.code) ?? [];
  return (
    roleCodes.includes(ROLE_ROOT) ||
    userStore.prems.includes(PERMISSION) ||
    userStore.prems.includes("*:*:*")
  );
});

function fillForm(next: VideoProcessingConfig) {
  config.value = next;
  form.cover_image_provider = next.cover_image_provider;
  form.relay_image_model = next.relay_image_model;
  form.relay_image_size = next.relay_image_size;
  form.cover_summary_model = next.cover_summary_model;
  form.creative_planner_model = next.creative_planner_model;
  // 后端存的可能是 null（= 跟随代码默认），直接把内置原文铺进编辑框，
  // 否则管理员面对空框不知道该写什么。
  form.cover_prompt_template =
    next.cover_prompt_template ?? next.cover_prompt_template_default ?? "";
  form.planner_prompt_template =
    next.planner_prompt_template ?? next.planner_prompt_template_default ?? "";
}

/** 与内置原文一致（或清空）就当作「跟随默认」，提交 null，避免把默认值冻结成副本。 */
function normalizeTemplate(value: string, fallback?: string): string | null {
  const text = value.trim();
  if (!text) return null;
  return text === (fallback ?? "").trim() ? null : text;
}

async function loadConfig() {
  loading.value = true;
  try {
    const response = await VideoProcessingAPI.getProcessingConfig();
    fillForm(response.data.data);
  } finally {
    loading.value = false;
  }
}

/** 模型清单是便利功能，拉不到就退化成手填，不打断高级设置。 */
async function loadImageModels() {
  modelsLoading.value = true;
  try {
    const response = await VideoProcessingAPI.getCoverImageModels();
    imageModels.value = response.data.data ?? [];
  } catch {
    imageModels.value = [];
  } finally {
    modelsLoading.value = false;
  }
}

function restoreDefaults() {
  form.cover_prompt_template = config.value?.cover_prompt_template_default ?? "";
  form.planner_prompt_template = config.value?.planner_prompt_template_default ?? "";
  ElMessage.info("已还原为内置默认提示词，保存后生效");
}

async function handleSave() {
  const payload: VideoProcessingConfigUpdateParams = {
    cover_image_provider: form.cover_image_provider,
    relay_image_model: form.relay_image_model,
    relay_image_size: form.relay_image_size,
    cover_summary_model: form.cover_summary_model,
    creative_planner_model: form.creative_planner_model,
    // 没改过的模板仍回传 null，让它继续跟着代码默认走。
    cover_prompt_template: normalizeTemplate(
      form.cover_prompt_template,
      config.value?.cover_prompt_template_default
    ),
    planner_prompt_template: normalizeTemplate(
      form.planner_prompt_template,
      config.value?.planner_prompt_template_default
    ),
  };
  saving.value = true;
  try {
    const response = await VideoProcessingAPI.updateProcessingConfig(payload);
    fillForm(response.data.data);
    ElMessage.success("高级设置已保存");
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  if (!canConfig.value) return;
  loadConfig();
  loadImageModels();
});

// 权限是登录后才下发的，晚到一步时补一次加载，否则面板会一直空着。
watch(canConfig, (allowed) => {
  if (!allowed || config.value) return;
  loadConfig();
  loadImageModels();
});
</script>

<style scoped src="./VideoProcessingAdvancedSettings.scss" lang="scss"></style>
