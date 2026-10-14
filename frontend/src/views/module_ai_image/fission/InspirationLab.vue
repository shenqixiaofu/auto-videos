<template>
  <div class="app-container pb-20">
    <el-page-header @back="goBack" class="mb-6 bg-white p-4 border border-gray-100 rounded-sm">
      <template #content>
        <span class="text-base font-bold flex items-center gap-2">
          <el-icon class="text-blue-500"><MagicStick /></el-icon>
          专家创作台 (ComfyUI 直通车)
        </span>
      </template>
      <template #extra>
        <el-tag type="warning" effect="light">手动创作模式</el-tag>
        <el-tag v-if="isPolling" type="success" class="ml-2" effect="dark">
          <el-icon class="is-loading mr-1"><Loading /></el-icon>
          正在云端生图...
        </el-tag>
      </template>
    </el-page-header>

    <el-row :gutter="24">
      <el-col :xs="24" :md="8" :lg="6">
        <el-card shadow="never" class="h-full border-gray-200 sticky top-4">
          <template #header>
            <div class="font-bold text-gray-700">1. 基础配置与参考</div>
          </template>

          <el-form label-position="top" :model="form" :rules="rules" ref="formRef">
            <el-form-item label="大地点 (必填)" prop="location">
              <el-input v-model="form.location" placeholder="例如：桂林阳朔、大理苍山" />
            </el-form-item>

            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="目标性别" prop="gender">
                  <el-select v-model="form.gender" placeholder="性别">
                    <el-option
                      v-for="item in genderOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="年龄" prop="age">
                  <el-input-number
                    v-model="form.age"
                    :min="1"
                    :max="100"
                    class="w-full"
                    controls-position="right"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="服装与画面风格 (高定参数)">
              <div
                class="p-3 bg-blue-50/50 border border-blue-100 rounded text-sm flex flex-col gap-3 w-full"
              >
                <div class="text-xs text-blue-500 font-bold mb-1 flex items-center justify-between">
                  <span class="flex items-center gap-1">
                    <el-icon><EditPen /></el-icon>
                    覆写底层参数
                  </span>
                </div>
                <el-input
                  key="custom-theme-name"
                  v-model="form.customTheme.theme"
                  size="small"
                  placeholder="如: 井冈山小红军"
                >
                  <template #prepend>
                    <span class="text-red-500 mr-1">*</span>
                    主题名称
                  </template>
                  <template #append>
                    <el-button
                      class="bg-blue-500 text-white border-none hover:bg-blue-600"
                      :loading="isGeneratingTheme"
                      @click="handleGenerateTheme"
                    >
                      AI 智能扩写
                    </el-button>
                  </template>
                </el-input>
                <el-input
                  key="custom-theme-material"
                  v-model="form.customTheme.material"
                  size="small"
                  placeholder="如: 水洗做旧亚麻"
                >
                  <template #prepend>主材质</template>
                </el-input>
                <el-input
                  key="custom-theme-style"
                  v-model="form.customTheme.clothing_style"
                  size="small"
                  placeholder="款式描述..."
                >
                  <template #prepend>款式描述</template>
                </el-input>
                <el-input
                  key="custom-theme-colors"
                  v-model="form.customTheme.colors"
                  size="small"
                  placeholder="如: 鼠尾草绿"
                >
                  <template #prepend>配色方案</template>
                </el-input>
                <el-input
                  key="custom-theme-vibe"
                  v-model="form.customTheme.vibe"
                  size="small"
                  placeholder="如: 自然、呼吸感"
                >
                  <template #prepend>气质氛围</template>
                </el-input>
              </div>
            </el-form-item>

            <el-form-item label="场景参考图 (上传将触发反推)">
              <el-upload
                class="w-full"
                drag
                action="#"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleImageUpload"
              >
                <div v-if="!form.bgUrl" class="flex flex-col items-center justify-center py-6">
                  <el-icon class="el-icon--upload text-gray-400"><UploadFilled /></el-icon>
                  <div class="el-upload__text">
                    拖拽图片到此处或
                    <em>点击上传</em>
                  </div>
                </div>
                <el-image v-else :src="form.bgUrl" class="w-full h-40 rounded" fit="cover" />
              </el-upload>
            </el-form-item>

            <el-form-item label="附加导演要求 (选填)">
              <el-input
                v-model="form.extraCommand"
                type="textarea"
                :rows="3"
                placeholder="例如：全部要赛博朋克风格..."
              />
            </el-form-item>

            <el-button
              type="primary"
              class="w-full h-12 text-base font-bold shadow-md"
              :icon="Cpu"
              :loading="isGenerating"
              @click="generatePrompts"
              :disabled="isPolling"
            >
              脑暴填满 15 组提示词
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16" :lg="18">
        <el-card shadow="never" class="h-full border-gray-200 bg-gray-50/50">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="font-bold text-gray-700">
                2. 提示词矩阵工作台 ({{ promptList.length }} 组)
              </span>
              <el-button
                type="info"
                link
                @click="initEmptyTemplates"
                icon="Refresh"
                :disabled="isPolling"
              >
                重置为空模板
              </el-button>
            </div>
          </template>

          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <div
              v-for="(item, index) in promptList"
              :key="index"
              class="bg-white border border-gray-200 rounded-md p-3 shadow-sm hover:shadow-md transition-shadow relative group flex flex-col"
            >
              <div class="flex justify-between items-center mb-2 pb-2 border-b border-gray-100">
                <div class="flex items-center gap-2">
                  <el-tag size="small" type="info" effect="dark">镜头 {{ index + 1 }}</el-tag>
                  <el-select
                    v-model="item.view_type"
                    size="small"
                    class="w-20"
                    :disabled="item.status !== 'idle'"
                  >
                    <el-option label="全景" value="全景" />
                    <el-option label="中景" value="中景" />
                    <el-option label="特写" value="特写" />
                  </el-select>
                  <el-tooltip content="修改指令后点击重绘此图" placement="top">
                    <el-button
                      type="primary"
                      icon="RefreshRight"
                      circle
                      plain
                      size="small"
                      :loading="item.status === 'processing'"
                      @click="handleSingleRegenerate(item)"
                    />
                  </el-tooltip>
                </div>
                <el-button
                  type="danger"
                  icon="Delete"
                  circle
                  plain
                  size="small"
                  class="opacity-0 group-hover:opacity-100 transition-opacity"
                  @click="removePrompt(index)"
                  :disabled="item.status !== 'idle'"
                />
              </div>

              <div
                v-if="item.status !== 'idle'"
                class="w-full aspect-square mb-3 bg-gray-100 rounded flex flex-col items-center justify-center overflow-hidden border border-gray-200 relative"
              >
                <el-image
                  v-if="item.status === 'success' && item.image_url"
                  :src="item.image_url"
                  class="w-full h-full object-cover"
                  :preview-src-list="[item.image_url]"
                  fit="cover"
                />
                <div
                  v-else-if="item.status === 'processing'"
                  class="flex flex-col items-center text-blue-500"
                >
                  <el-icon class="is-loading" :size="30"><Loading /></el-icon>
                  <span class="text-xs mt-2 font-bold tracking-widest">COMFYUI 生成中...</span>
                </div>
                <div
                  v-else-if="item.status === 'failed'"
                  class="flex flex-col items-center text-red-500"
                >
                  <el-icon :size="30"><CircleCloseFilled /></el-icon>
                  <span class="text-xs mt-2 font-bold">节点报错或断开</span>
                </div>
              </div>

              <div class="mb-2 flex-shrink-0">
                <div class="text-xs text-gray-400 mb-1 font-bold">动作剧本</div>
                <el-input
                  v-model="item.action_desc"
                  size="small"
                  placeholder="例如：双手捧起落叶..."
                />
              </div>

              <div class="flex-grow flex flex-col">
                <div class="text-xs text-gray-400 mb-1 font-bold">底层指令 (ComfyUI Prompt)</div>
                <el-input
                  v-model="item.positive_prompt"
                  type="textarea"
                  :rows="item.status === 'idle' ? 6 : 8"
                  class="text-xs flex-grow"
                  placeholder="在此输入发给 ComfyUI 的完整提示词..."
                />
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div
      v-if="promptList.length > 0"
      class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-50 flex justify-center items-center gap-4"
    >
      <div class="text-sm text-gray-500 mr-4">
        当前就绪
        <strong class="text-blue-600">{{ promptList.length }}</strong>
        组生图指令
      </div>
      <el-button size="large" @click="addCustomPrompt" :disabled="isPolling">
        + 手动新增一组
      </el-button>
      <el-button
        type="success"
        size="large"
        class="w-48 font-bold shadow-lg"
        :icon="VideoPlay"
        :loading="isSubmitting"
        @click="submitToComfyUI"
        :disabled="isPolling"
      >
        {{ isPolling ? "云端生图中..." : "投递至 ComfyUI 生图" }}
      </el-button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { useRouter, useRoute } from "vue-router"; // 🚀 引入 useRoute

const route = useRoute();
import { ref, reactive, onMounted, watch, onBeforeUnmount } from "vue";

import { ElMessage } from "element-plus";
import {
  MagicStick,
  Cpu,
  UploadFilled,
  VideoPlay,
  Refresh,
  Delete,
  EditPen,
  Loading,
  CircleCloseFilled,
} from "@element-plus/icons-vue";
import FissionTaskAPI from "@/api/module_ai_image/task";
import { FileAPI } from "@/api/module_common/file";
import FissionBatchAPI from "@/api/module_ai_image/fission";
import AiStyleThemeAPI from "@/api/module_ai_image/style_theme";
// 独立控制风格生成的 loading 状态 (避免和底部生成15组提示词的 loading 冲突)
const isGeneratingTheme = ref(false);
const router = useRouter();
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
// 🚀 定义本地缓存的 Key
const CACHE_KEY = "expert_studio_draft_cache";

// === 1. 表单数据 ===
const formRef = ref();
const form = reactive({
  location: "",
  gender: "女孩",
  age: 20,
  bgUrl: "",
  bgFile: null as File | null,
  extraCommand: "",
  selected_scene: "",
  selected_style: "",
  customTheme: {
    theme: "清风森系 (Mori Girl Nature)",
    material: "水洗做旧亚麻与柔软纯棉",
    clothing_style: "宽松的多层次吊带裙叠穿，搭配粗棒针织开衫",
    colors: "鼠尾草绿、燕麦色、泥土棕",
    vibe: "自然、呼吸感、安静纯粹",
  },
});

const rules = {
  location: [{ required: true, message: "地点不能为空", trigger: "blur" }],
};

// === 2. 状态变量与预设 ===
const isGenerating = ref(false);
const isSubmitting = ref(false);
const promptList = ref<any[]>([]);

const isPolling = ref(false);
let pollingTimer: any = null;

// 🚀 新增：保存当前正在轮询的批次ID
const activeBatchId = ref<number | null>(null);

// 预设 15 个镜头的景别配比
const defaultViewTypes = [
  ...Array(5).fill("全景"),
  ...Array(7).fill("中景"),
  ...Array(3).fill("特写"),
];

const goBack = () => router.back();

// === 3. 初始化空模板 ===
const initEmptyTemplates = () => {
  promptList.value = defaultViewTypes.map((viewType) => ({
    id: "",
    view_type: viewType,
    action_desc: "",
    positive_prompt: "",
    status: "idle",
    image_url: "",
  }));
  activeBatchId.value = null; // 重置批次ID
};

// 🚀 从缓存中恢复数据 (带断点续传轮询)
// 🚀 从缓存或 URL 恢复数据
const restoreFromCache = async () => {
  // 1. 🌟 优先检查：页面 URL 是否传了 batchId (例如：/expert-studio?batchId=688)
  const urlBatchId = route.query.batchId ? Number(route.query.batchId) : null;

  const cached = localStorage.getItem(CACHE_KEY);
  let parsedCache = null;
  if (cached) {
    try {
      parsedCache = JSON.parse(cached);
    } catch (e) {
      console.error("缓存解析失败");
    }
  }

  // ==========================================
  // 场景 A：从外部页面传了 batchId 进来
  // ==========================================
  if (urlBatchId) {
    console.log("🚀 检测到 URL 传入的 BatchId:", urlBatchId);
    activeBatchId.value = urlBatchId;

    // ⚠️ 架构师防坑点：你需要根据情况决定怎么恢复表单和卡片
    // 情况 1：如果本地缓存里的 activeBatchId 刚好等于 url 传进来的，直接用本地的（最快）
    if (parsedCache && parsedCache.activeBatchId === urlBatchId) {
      if (parsedCache.promptList) promptList.value = parsedCache.promptList;
      if (parsedCache.form) Object.assign(form, parsedCache.form);
      if (parsedCache.form?.bgUrl?.startsWith("blob:")) form.bgUrl = "";

      ElMessage.success("正在为您恢复该批次的生图进度...");
      startPollingTasks(urlBatchId);
    } else {
      ElMessage.info("正在从云端同步该批次的历史数据...");

      try {
        const res: any = await FissionBatchAPI.getBatchDetail(urlBatchId);
        const code = res.data?.code ?? res.code;

        if (code === 200 || code === 0) {
          const remoteData = res.data?.data || res.data;

          // 1. 🌟 反填左侧主表单
          form.location = remoteData.location || "";
          form.gender = remoteData.gender || "女孩";
          form.age = remoteData.age || 20;
          form.selected_scene = remoteData.selected_scene || "";
          form.selected_style = remoteData.selected_style || "";
          // 如果你的主题是存在 customTheme.theme 里的
          form.customTheme.theme = remoteData.theme || "";

          // 2. 🌟 反填右侧 15 张卡片列表（核心：状态映射）
          promptList.value = (remoteData.tasks || []).map((task: any) => {
            // 解析后端 process_status 为前端 UI status
            let uiStatus = "idle"; // 默认空闲

            // 如果后端有 positive_prompt 说明已经提交过了，哪怕 process_status 是 null/0 也算 processing
            if (task.positive_prompt) {
              if (task.process_status === 2) {
                uiStatus = "success";
              } else if (task.process_status === 3) {
                uiStatus = "failed";
              } else {
                uiStatus = "processing"; // 0 或 1 都在排队或生成中
              }
            }

            return {
              id: task.id,
              view_type: task.view_type || "中景",
              action_desc: task.action_desc || "",
              positive_prompt: task.positive_prompt || "",
              status: uiStatus,
              image_url: task.image_url || "",
            };
          });

          // 3. 🌟 智能决策：是不是所有图都出完了？
          const hasProcessing = promptList.value.some((p) => p.status === "processing");

          if (hasProcessing) {
            ElMessage.success("数据恢复成功，有任务正在生成，已拉取最新进度！");
            startPollingTasks(urlBatchId); // 拉起轮询引擎继续监听
          } else {
            ElMessage.success("数据恢复成功，该批次所有图片已生成完毕！");
            // 不需要再拉起轮询了，静静地展示图就行
          }
        } else {
          throw new Error(res.data?.msg || "获取历史批次详情失败");
        }
      } catch (error: any) {
        console.error("同步历史批次异常:", error);
        ElMessage.error(error.message || "拉取批次数据失败，请检查网络或ID是否正确");
        // 如果拉取失败了，给个保底的空模板，防止页面白屏报错
        initEmptyTemplates();
      }
    }
    return; // 🚀 匹配到 URL 参数后，直接 return，不走下面的普通恢复逻辑
  }

  // ==========================================
  // 场景 B：正常打开页面，走你原本的本地缓存恢复逻辑
  // ==========================================
  if (parsedCache) {
    // 1. 恢复列表
    if (parsedCache.promptList && parsedCache.promptList.length > 0) {
      promptList.value = parsedCache.promptList;
    } else {
      initEmptyTemplates();
    }

    // 2. 恢复表单
    if (parsedCache.form) {
      Object.assign(form, parsedCache.form);
      if (form.bgUrl && form.bgUrl.startsWith("blob:")) {
        form.bgUrl = "";
      }
      form.bgFile = null;
    }

    // 3. 恢复批次 ID 并检测是否需要继续轮询
    if (parsedCache.activeBatchId) {
      activeBatchId.value = parsedCache.activeBatchId;

      const hasProcessing = promptList.value.some((p) => p.status === "processing");
      if (hasProcessing && activeBatchId.value) {
        ElMessage.success("正在为您恢复后台生图进度...");
        startPollingTasks(activeBatchId.value);
      } else {
        activeBatchId.value = null;
      }
    } else {
      ElMessage.success("已为您恢复上次未完成的草稿 📝");
    }
  } else {
    initEmptyTemplates();
  }
};
onMounted(() => {
  restoreFromCache();
});

onBeforeUnmount(() => {
  if (pollingTimer) clearInterval(pollingTimer);
});

/**
 * 🌟 AI 扩写高定风格参数
 */
const handleGenerateTheme = async () => {
  // 必须先填写主题名称
  if (!form.customTheme.theme || form.customTheme.theme.trim() === "") {
    ElMessage.warning("请先在输入框填写【主题名称】！");
    return;
  }

  try {
    isGeneratingTheme.value = true;

    // 组装参数，充分利用表单已有数据
    const params = {
      gender: form.gender || "any", // 关联顶部的性别选择
      theme_name: form.customTheme.theme,
      remark: form.extraCommand || "", // 可以把附加导演要求作为提示词发给AI
    };

    const res = await AiStyleThemeAPI.generateStyleParams(params);
    const code = res.data?.code;
    const aiData = res.data?.data;

    if (code === 0 && aiData) {
      // 回填数据
      form.customTheme.material = aiData.material || form.customTheme.material;
      form.customTheme.clothing_style = aiData.clothing_style || form.customTheme.clothing_style;
      form.customTheme.colors = aiData.colors || form.customTheme.colors;
      form.customTheme.vibe = aiData.vibe || form.customTheme.vibe;

      ElMessage.success("风格底层参数已智能补全！");
    } else {
      ElMessage.error(res.data?.msg || "AI 生成失败");
    }
  } catch (error) {
    console.error("AI 扩写参数报错:", error);
    ElMessage.error("网络或服务异常，请稍后再试");
  } finally {
    isGeneratingTheme.value = false;
  }
};

// 🚀 深度监听自动保存：移除了拦截，轮询拿到的图片也会实时存入缓存！
watch(
  () => ({ form, promptList: promptList.value, activeBatchId: activeBatchId.value }),
  (newVal) => {
    const dataToCache = {
      form: { ...newVal.form },
      promptList: newVal.promptList,
      activeBatchId: newVal.activeBatchId, // 🚀 存入当前批次ID
    };
    dataToCache.form.bgFile = null;

    localStorage.setItem(CACHE_KEY, JSON.stringify(dataToCache));
  },
  { deep: true }
);

// === 4. 上传背景图并自动反推 ===
const handleImageUpload = async (file: any) => {
  const rawFile = file.raw;
  if (!rawFile) return;

  form.bgUrl = URL.createObjectURL(rawFile);
  form.bgFile = rawFile;

  const loadingMsg = ElMessage({
    message: "正在上传参考图并呼叫大模型提取光影特征...",
    type: "info",
    duration: 0,
    icon: "Loading",
  });

  try {
    const formData = new FormData();
    formData.append("file", rawFile);

    const uploadRes: any = await FileAPI.uploadFile(formData);
    const remoteImageUrl = uploadRes.data?.data?.file_url || uploadRes.data?.file_url;

    if (!remoteImageUrl) throw new Error("上传未返回图片地址");

    const inferRes: any = await FissionTaskAPI.inferBackground({
      image_url: remoteImageUrl,
    });

    const code = inferRes.data?.code ?? inferRes.code;
    if (code === 200 || code === 0) {
      const inferData = inferRes.data?.data || inferRes.data;

      const scene = inferData.scene_detail || "";
      const lighting = inferData.lighting_detail || "";
      const atmosphere = inferData.atmosphere_detail || "";

      const aiExtracted = `[参考图提取特征] ${scene}。${lighting}。${atmosphere}\n`;
      form.extraCommand = aiExtracted + form.extraCommand;
      form.bgUrl = remoteImageUrl;

      loadingMsg.close();
      ElMessage.success("🎉 参考图特征提取完毕，已填入导演要求中！");
    } else {
      loadingMsg.close();
      ElMessage.warning("图片已上传，但特征反推失败，您可以手动填写指令。");
    }
  } catch (error) {
    console.error("上传或反推异常:", error);
    loadingMsg.close();
    ElMessage.error("网络或服务异常，图片处理失败");
  }
};
// 🚀 单图重绘逻辑
const handleSingleRegenerate = async (item: any) => {
  console.log("🚀 单图重绘", item);
  // 1. 基础校验：必须要有 task_id (说明已经提交过一次了)
  if (!item.id) {
    ElMessage.warning("请先点击下方的【投递至 ComfyUI】，产生任务 ID 后再进行重绘");
    return;
  }

  if (!item.positive_prompt.trim()) {
    ElMessage.warning("底层指令不能为空");
    return;
  }

  try {
    // 2. 切换卡片状态为“转圈圈”
    item.status = "processing";
    let finalPrompt = item.positive_prompt;

    // 1. 利用正则匹配固定的句式结构： "。[旧动作]，[旧景别]。画面呈现"
    // 解释：匹配句号开头，中间一堆非句号的词(即动作)，跟着逗号和景别，然后是句号和"画面呈现"
    const templateRegex = /。([^。]+)，(全景|中景|特写|特写景)。(画面呈现)/;
    const match = finalPrompt.match(templateRegex);

    if (match) {
      const oldAction = match[1];
      const oldView = match[2];

      // 只有当用户真的改了动作或景别时，才触发替换
      if (oldAction !== item.action_desc || oldView !== item.view_type) {
        finalPrompt = finalPrompt.replace(
          match[0],
          `。${item.action_desc}，${item.view_type}。${match[3]}`
        );
      }
    } else {
      // 💡 兜底策略：如果用户手动把底层提示词改得面目全非（比如删了"画面呈现"）
      // 导致正则找不到旧动作在哪，再退回强行追加模式，防止新动作丢失
      if (item.action_desc && !finalPrompt.includes(item.action_desc)) {
        finalPrompt = `(动作姿态: ${item.action_desc}:1.2), ` + finalPrompt;
      }
      // 景别兜底替换
      const fallbackViewRegex = /，(全景|中景|特写)。/g;
      if (fallbackViewRegex.test(finalPrompt)) {
        finalPrompt = finalPrompt.replace(fallbackViewRegex, `，${item.view_type}。`);
      }
    }

    // 把精准替换后的结果反写回 UI 输入框，让用户确认
    item.positive_prompt = finalPrompt;
    const payload = {
      task_id: item.id,
      positive_prompt: item.positive_prompt,
      // 这里的 params 传最新的表单快照，方便后端存入 version_history
      params: {
        ...form.customTheme,
        action: item.action_desc,
        view: item.view_type,
      },
    };

    const res: any = await FissionTaskAPI.regenerateExpertTask(payload);
    const code = res.data?.code ?? res.code;

    if (code === 200 || code === 0) {
      ElMessage.success(`镜头重绘任务已提交，Seed 已继承`);

      // 🚀 核心动作：如果当前没有在轮询，则立刻拉起轮询！
      // 假设 activeBatchId 已经存在（提交过一次就会有）
      console.log(activeBatchId.value);
      if (activeBatchId.value) {
        startPollingTasks(activeBatchId.value);
      }
    } else {
      item.status = "failed";
      throw new Error(res.data?.msg || "重绘发起失败");
    }
  } catch (error: any) {
    console.error(error);
    ElMessage.error(error.message || "网络异常");
  }
};

// === 5. 生成提示词 (覆盖空模板) ===
const generatePrompts = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return;

    isGenerating.value = true;
    try {
      const payload: any = {
        location: form.location,
        gender: form.gender,
        age: form.age,
        extra_command: form.extraCommand || undefined,
      };

      if (form.customTheme.theme.trim()) {
        payload.theme = { ...form.customTheme };
      }

      const res: any = await FissionTaskAPI.brainstormExpertPrompts(payload);
      const code = res.data?.code ?? res.code;
      if (code === 0 || code === 200) {
        const data = res.data?.data || res.data;

        form.selected_scene = data[0].selected_scene || "未命名场景";
        form.selected_style = data[0].selected_style || "未命名风格";

        promptList.value = data.map((item: any) => ({
          id: "",
          view_type: item.view_type,
          action_desc: item.action_desc,
          positive_prompt: item.positive_prompt,
          status: "idle",
          image_url: "",
        }));

        // 生成了新的提示词，以前的轮询作废
        activeBatchId.value = null;

        ElMessage.success("🎉 15组镜头剧本已填入模板，请检查微调！");
      } else {
        ElMessage.warning(res.data?.msg || "脑暴失败，请检查网络或配置");
      }
    } catch (error) {
      ElMessage.error("脑暴异常，请检查网络");
    } finally {
      isGenerating.value = false;
    }
  });
};

// === 6. 右侧卡片交互 ===
const removePrompt = (index: number) => {
  promptList.value.splice(index, 1);
};

const addCustomPrompt = () => {
  promptList.value.push({
    id: "",
    view_type: "中景",
    action_desc: "",
    positive_prompt: "",
    status: "idle",
    image_url: "",
  });
  setTimeout(() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }), 100);
};

// === 7. 🚀 轮询引擎 ===
// === 7. 🚀 轮询引擎 ===
const startPollingTasks = (batchSn: number) => {
  isPolling.value = true;
  if (pollingTimer) clearInterval(pollingTimer);

  pollingTimer = setInterval(async () => {
    try {
      const res: any = await FissionBatchAPI.getBatchTasks(batchSn);
      const code = res.data?.code ?? res.code;
      console.log("🚀 轮询结果", res);
      if (code === 200 || code === 0) {
        // 🚀 核心修复1：兼容多层解构，保证拿到的绝对是一个数组
        let remoteTasks = res.data?.data || res.data || [];
        console.log("🚀 轮询结果", remoteTasks);
        // 如果后端包在了 tasks 字段里

        let allFinished = true;
        let validIndex = 0;

        promptList.value.forEach((card) => {
          if (card.positive_prompt.trim() !== "") {
            // 🚀 核心修复2：优先用 ID 精准找人！解决重绘后后端数组乱序的问题
            const serverTask = card.id
              ? remoteTasks.find((t: any) => t.id === card.id)
              : remoteTasks[validIndex]; // 只有第一次刚提交没 ID 时，才退化为按索引盲猜
            console.log("🚀 serverTask", serverTask);
            if (serverTask) {
              // 回填真实的后端 ID 给卡片
              if (!card.id) {
                card.id = serverTask.id;
              }

              // 状态机流转
              if (serverTask.process_status === 2) {
                card.status = "success";
                card.image_url = serverTask.image_url;
              } else if (serverTask.process_status === 3) {
                card.status = "failed";
              } else {
                card.status = "processing";
                allFinished = false; // 确实还在生图，不能停
              }
            } else {
              // 🚀 核心修复3：如果后端还没查到这单（比如延迟），绝不能默认 allFinished = true！
              card.status = "processing";
              allFinished = false;
            }
            validIndex++;
          }
        });

        // 只有当所有有效卡片都明确拿到 success 或 failed 时，才终结定时器
        if (allFinished) {
          clearInterval(pollingTimer);
          pollingTimer = null;
          isPolling.value = false;
          ElMessage.success("🎉 当前批次 ComfyUI 渲染已全部结束！");
        }
      }
    } catch (e) {
      console.error("轮询网络波动或解析异常:", e);
      // 报错不改变 allFinished 状态，下个 5 秒继续顽强轮询！
    }
  }, 5000);
};
// === 8. 终极提交至 ComfyUI ===
const submitToComfyUI = async () => {
  const validPrompts = promptList.value.filter((p) => p.positive_prompt.trim() !== "");

  if (validPrompts.length === 0) {
    ElMessage.warning("请至少填写一组完整的底层指令！");
    return;
  }

  isSubmitting.value = true;
  try {
    const payload = {
      location: form.location,
      gender: form.gender,
      age: form.age,
      theme: form.customTheme.theme || "专家高定模式",
      selected_scene: form.selected_scene || "专家自定义场景",
      selected_style: form.selected_style || "专家自定义风格",
      tasks: validPrompts,
    };

    const res: any = await FissionTaskAPI.submitExpertTask(payload);
    const code = res.data?.code ?? res.code;

    if (code === 200 || code === 0) {
      const batchSn = res.data?.data?.batch_sn;
      console.log("当前批次ID：", batchSn);
      activeBatchId.value = batchSn; // 🚀 记录下来，它会触发 watch 自动存入 localStorage

      ElMessage.success(`🚀 批次投递成功，开始监听生图进度！`);

      validPrompts.forEach((p) => {
        p.status = "processing";
      });

      startPollingTasks(batchSn);
    } else {
      throw new Error(res.data?.msg || "服务器返回异常");
    }
  } catch (error: any) {
    ElMessage.error(error.message || "投递失败，请检查网络");
  } finally {
    isSubmitting.value = false;
  }
};
</script>
<style scoped>
/* 隐藏 el-input-number 默认的按钮，让它居左对齐看起来更清爽 */
:deep(.el-input-number .el-input__inner) {
  text-align: left;
}
</style>
