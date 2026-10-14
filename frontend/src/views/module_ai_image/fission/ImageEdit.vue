<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { onBeforeUnmount } from "vue"; // 记得顶部引入这个
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import BgHistoryDialog from "./BgHistoryDialog.vue"; // 注意替换成你实际的相对路径
import { Setting, InfoFilled, MagicStick, Picture, Check } from "@element-plus/icons-vue";
import { ArrowLeft, ArrowRight, Collection, Avatar, Plus } from "@element-plus/icons-vue";
const isSaving = ref(false);
const fusionModel = ref("gpt");
// 引入咱们拆分好的前端 API
import { FissionTaskAPI } from "@/api/module_ai_image/task";
import { FissionBatchAPI } from "@/api/module_ai_image/fission"; // 引入批次接口
import { FileAPI } from "@/api/module_common/file";
const activeCollapse = ref(["scene", "character", "lighting"]); // 默认展开
const currentVersion = ref(1);
const paramForm = reactive({
  scene_detail: "",
  atmosphere_detail: "",
  clothing: "",
  face_description: "",
  lighting_detail: "",
  skin_texture: "", // 哪怕面板不展示，最好也带着传给后端
  hairstyle: "",
  action: "",
  view: "",
});

const previewIndex = ref(0);
let backupParams: any = {};
const echoParamsFromHistory = (history: any[], version: number) => {
  const currentV = history.find((i: any) => i.v === version);
  if (currentV && currentV.params_snapshot) {
    // 将快照数据响应式地合并到 paramForm 中
    Object.assign(paramForm, currentV.params_snapshot);
    // 深度拷贝一份作为备份
    backupParams = JSON.parse(JSON.stringify(currentV.params_snapshot));
  } else {
    // 容错：如果没有找到快照，清空表单
    Object.keys(paramForm).forEach((key) => ((paramForm as any)[key] = ""));
  }
};

const isInferring = ref(false);
const currentPollingVersion = ref<number | null>(null); // 🚀 记录当前正在等哪个版本的背景
let pollingTimer: any = null; // 🚀 存储定时器，方便随时清理
const isFusing = ref(false); // 路线 B：直接融合的 Loading
const fusedImageUrl = ref(""); // 存储路线 B 的融合结果预览

const siblingTasks = ref<any[]>([]); // 存储同批次的所有任务
const currentBatchId = ref<number | null>(null);

const route = useRoute();
const router = useRouter();

// --- 状态数据 ---
const pageLoading = ref(true);
const isSubmitting = ref(false);
const isUpscaling = ref(false); // 🚀 一键高清专属 loading

const taskId = ref<any>("");
const originalImageUrl = ref("");
const upscaledImageUrl = ref(""); // 🚀 存储超分后的高清图

// 🎭 换脸相关变量
const isSwapping = ref(false); // 换脸加载状态
const tempFaceUrl = ref(""); // 用户上传的人脸图预览（本地 blob）
const targetFaceFile = ref<File | null>(null); // 存储待上传的 File 对象
const swappedImageUrl = ref(""); // 后端回传的已存入 MinIO 的换脸图

const fusionCustomPrompt = ref(
  "一张照片级写实风格的图像，将图1中的主体人物自然、无缝地融入到图2所展示的环境中,必须保持人物与背景比例协调,锁定人物面貌不变，姿势动作根据背景重新设计一个合理的风格，并保持人物的表情 unchanged。"
);
const selectedDepthPrompt = ref("(subject in the middle ground:1.3)");
const selectedPositionPrompt = ref("subject centrally and dominant in the frame, prominent subject, classic portrait composition, subject occupies a large percentage of the frame");
// 原始数据备份（用于恢复）
let backupPrompt = "";

const showViewer = ref(false);
const previewList = computed(() => {
  // 把所有的 url 放进数组，利用 .filter(Boolean) 一键过滤掉所有空字符串
  return [
    originalImageUrl.value,
    upscaledImageUrl.value,
    swappedImageUrl.value,
    fusedImageUrl.value,
  ].filter(Boolean);
});
// 1. 当用户选择人脸图片时
const handleFaceSwapUpload = (file: any) => {
  const rawFile = file.raw;
  if (!rawFile) return;

  // 校验格式
  if (!["image/jpeg", "image/png", "image/jpg"].includes(rawFile.type)) {
    ElMessage.error("请上传 JPG/PNG 格式的图片");
    return;
  }

  // 预览用
  targetFaceFile.value = rawFile;
  tempFaceUrl.value = URL.createObjectURL(rawFile);
};

const historyDialog = reactive({
  visible: false,
  list: [] as any[],
});

const handleApplyHistoryBg = (url: string) => {
  fusedImageUrl.value = url; // 直接把历史图塞给主预览区的变量
  historyDialog.visible = false; // 关闭弹窗
  ElMessage.success("已调取历史版本！你可以在左侧对比，或者直接生成高清 4K。");
};

// 2. 执行换脸逻辑 (调用火山引擎接口)
const onDoFaceSwap = async () => {
  if (!targetFaceFile.value) {
    ElMessage.warning("请先上传一张人脸图片");
    return;
  }

  isSwapping.value = true;
  try {
    // A. 先把用户的人脸图上传到 MinIO
    const formData = new FormData();
    formData.append("file", targetFaceFile.value);

    const uploadRes: any = await FileAPI.uploadFile(formData);
    const faceImageUrl = uploadRes.data.data.file_url;
    console.log("上传成功，faceImageUrl:", faceImageUrl);

    // 🚀 新增逻辑：判断当前应该用哪张图作为“底图”去换脸
    // 优先级：换背景后的图(fusedImageUrl) > 原始底片(originalImageUrl)
    const targetUrlToSwap = fusedImageUrl.value || originalImageUrl.value;

    // B. 调用换脸接口
    const res: any = await FissionTaskAPI.faceSwapTask({
      task_id: taskId.value,
      target_face_url: faceImageUrl,
      target_url: targetUrlToSwap, // 👈 核心：告诉后端用这张图作为底图
    });

    // 兼容不同的 Axios 返回层级
    let code = res.data?.code ?? res.code;
    let data = res.data?.data ?? res.data;

    if (code === 200 || code === 0) {
      ElMessage.success("换脸施法成功！");
      // C. 拿到后端持久化后的新图片
      swappedImageUrl.value = data.swapped_url;
    } else {
      ElMessage.error(res.data?.msg || res.msg || "换脸失败，可能是面部特征不明显");
    }
  } catch (error) {
    console.error("换脸异常:", error);
    ElMessage.error("换脸服务暂不可用，请稍后再试");
  } finally {
    isSwapping.value = false;
  }
};

/**
 * 背景融合
 * @param file
 */
const handleBackgroundFusion = async (file: any) => {
  isFusing.value = true;
  try {
    const formData = new FormData();
    formData.append("file", file.raw);
    const uploadRes: any = await FileAPI.uploadFile(formData);
    const bgUrl = uploadRes.data.data.file_url;

    const fusionRes: any = await FissionTaskAPI.backgroundFusionTask({
      task_id: taskId.value,
      bg_image_url: bgUrl,
      custom_prompt:
        fusionCustomPrompt.value + selectedDepthPrompt.value + selectedPositionPrompt.value, // 提示语，包含深度和位置,
      model: fusionModel.value,
    });

    if (fusionRes.data?.code === 0 || fusionRes.code === 200) {
      const fusionData = fusionRes.data?.data || fusionRes.data;

      // 🚀 1. 拿到后端立即返回的版本号
      currentPollingVersion.value = fusionData.v;
      ElMessage.info("背景融合指令已发送，AI 正在后台施法...");

      // 🚀 2. 启动轮询引擎！(注意这里不要把 isFusing 设为 false)
      startPollingFusion();
    } else {
      ElMessage.error("任务提交失败");
      isFusing.value = false; // 提交失败才关闭 loading
    }
  } catch (error) {
    ElMessage.error("请求异常");
    isFusing.value = false; // 请求崩了也关闭 loading
  }
};

// 3. 重置换脸状态
const resetFaceSwap = () => {
  tempFaceUrl.value = "";
  targetFaceFile.value = null;
  swappedImageUrl.value = "";
};

const depthOptions = [
  { label: "超近景", value: "extreme_close_up, macro shot" },
  { label: "近前", value: "(standing in the foreground:1.2)" },
  { label: "黄金中景", value: "(subject in the middle ground:1.3)" },
  { label: "融入环境", value: "standing in the mid-distance" },
  { label: "远景/大片", value: "standing in the far distance, tiny subject" },
  { label: "极简远视", value: "extreme_long_shot, tiny figure, vast scenery" },
];

const positionOptions = [
  // 1. 最经典、最稳的主角位（全身、半身皆可）
  {
    label: "经典中心（最突显人物）",
    value:
      "subject centrally and dominant in the frame, prominent subject, classic portrait composition, subject occupies a large percentage of the frame",
  },

  // 2. 也是中心位，但利用人体透视，让头部在视觉黄金点（全身、七分身）
  {
    label: "中心偏上（人体透视黄金点）",
    value:
      "prominent centered subject, but subject positioning slightly higher so the head is on a rule-of-thirds line, subject is dominant and sharp",
  },

  // 3. 左侧三分一，人物依然高大清晰，背景自然虚化
  {
    label: "左侧黄金位（三分法、突出人物）",
    value:
      "subject prominent on the left side, rule of thirds composition, subject is sharp and dominant, shallow depth of field, blurred background bokeh",
  },

  // 4. 右侧三分一，人物依然高大清晰，背景自然虚化
  {
    label: "右侧黄金位（三分法、突出人物）",
    value:
      "subject prominent on the right side, rule of thirds composition, subject is sharp and dominant, shallow depth of field, blurred background bokeh",
  },

  // 5. 将人物主体重心放在画面中下部，但头部依然清晰，产生一种向上的延伸感（多用于全身照）
  {
    label: "重心略微降低（延伸感）",
    value:
      "subject centrally lowered in the frame, prominent subject, full body composition, strong perspective looking slightly up, head is sharp",
  },

  // 6. 这是一个经典的人像特写位置，强制全图重绘聚焦在头部
  {
    label: "特写（头肩位）",
    value:
      "classic head and shoulders portrait, subject filling the frame, eye contact, minimal negative space",
  },
];

const openPreview = (url: string) => {
  // 在当前列表中找到被点击图片的索引
  console.log("点击的图片 URL:", url);
  const index = previewList.value.indexOf(url);
  previewIndex.value = index > -1 ? index : 0;
  console.log("点击的图片索引:", index);
  showViewer.value = true;
};
// 🚀 核心：切换任务逻辑
const switchTask = (item: any) => {
  if (item.id == taskId.value) return;

  upscaledImageUrl.value = "";

  router.replace({
    query: { ...route.query, taskId: item.id },
  });

  // 🚀 核心改动：切换任务时，为了保证参数快照准确回显，建议直接重新调一遍 initData
  // 因为列表接口通常不返回全量的 version_history JSON
  taskId.value = item.id;
  initData();
};

// 2. 声明 scrollbar 的 ref
const scrollbarRef = ref<any>(null);

// 3. 🚀 核心：左右滚动逻辑
const handleScroll = (offset: number) => {
  if (!scrollbarRef.value) return;

  // 获取 Element Plus 滚动条内部的原生 DOM 容器
  const wrap = scrollbarRef.value.wrapRef;
  if (wrap) {
    // 使用原生 API 进行平滑滚动，丝滑无比
    wrap.scrollTo({
      left: wrap.scrollLeft + offset,
      behavior: "smooth", // 开启平滑滑动动画
    });
  }
};

// 🚀 核心：背景融合轮询引擎
const startPollingFusion = () => {
  let maxRetries = 60; // 最大轮询 60 次 (即 3分钟超时)
  let attempts = 0;

  const poll = async () => {
    // 如果中途用户取消了加载，或者版本号没了，直接停止
    if (!isFusing.value || !currentPollingVersion.value) return;

    attempts++;
    if (attempts > maxRetries) {
      isFusing.value = false;
      ElMessage.warning("背景融合超时，请稍后再试或查看历史记录");
      return;
    }

    try {
      // 1. 重新获取任务详情
      const res: any = await FissionTaskAPI.getTaskDetail(taskId.value);
      const code = res.data?.code ?? res.code;

      if (code === 200 || code === 0) {
        const taskData = res.data?.data ?? res.data;
        const history = taskData.bg_version_history || [];
        historyDialog.list = [...(taskData.bg_version_history || [])]
          .filter((item: any) => item.status !== "failed") // 🚀 新增：过滤掉状态为 failed 的记录
          .reverse();
        // 2. 在历史记录里找到咱们正在等的那个版本
        const targetVersion = history.find((h: any) => h.v === currentPollingVersion.value);

        if (targetVersion) {
          if (targetVersion.status === "success" && targetVersion.result_url) {
            // 🎉 成功！拿到图片，停止轮询
            fusedImageUrl.value = targetVersion.result_url;
            isFusing.value = false;
            currentPollingVersion.value = null;
            ElMessage.success("🎉 背景融合成功！请检查预览效果");
            return;
          } else if (targetVersion.status === "failed") {
            // 🚨 失败！提取错误信息，停止轮询
            isFusing.value = false;
            currentPollingVersion.value = null;
            ElMessage.error(`融合失败: ${targetVersion.error_msg || "未知异常"}`);
            return;
          }
          // 如果状态还是 'processing'，啥也不做，继续往下走，等待下一次定时器执行
        }
      }
    } catch (error) {
      console.error("轮询请求异常:", error);
      // 网络偶尔波动不停止轮询，让它继续尝试
    }

    // 3. 如果没结束，设置 3 秒后再调一次自己
    pollingTimer = setTimeout(poll, 3000);
  };

  // 第一次执行：先等 3 秒再查，给后端一点生图的时间
  pollingTimer = setTimeout(poll, 3000);
};

// --- 初始化逻辑 ---
const initData = async () => {
  taskId.value = route.query.taskId;
  if (!taskId.value) return router.back();

  pageLoading.value = true;
  try {
    const res: any = await FissionTaskAPI.getTaskDetail(taskId.value);
    const code = res.data?.code ?? res.code;

    if (code === 200 || code === 0) {
      const taskData = res.data?.data ?? res.data;
      swappedImageUrl.value = taskData.swapped_url;
      originalImageUrl.value = taskData.image_url;
      currentVersion.value = taskData.current_version || 1;
      fusedImageUrl.value = taskData.current_bg_url;
      console.log("当前任务版本：", currentVersion.value);

      historyDialog.list = [...(taskData.bg_version_history || [])]
        .filter((item: any) => item.status !== "failed") // 🚀 新增：过滤掉状态为 failed 的记录
        .reverse();
      // 🚀 核心：回显参数面板
      echoParamsFromHistory(taskData.version_history || [], currentVersion.value);
      console.log("当前任务参数快照：", paramForm);
      // 加载同批次数据...
      currentBatchId.value = taskData.batch_id;
      console.log("当前任务批次ID：", currentBatchId.value);
      if (currentBatchId.value && siblingTasks.value.length === 0) {
        const batchRes: any = await FissionBatchAPI.getBatchTasks(currentBatchId.value);
        siblingTasks.value = batchRes.data?.data ?? batchRes.data;
      }
    }
  } catch (error) {
    ElMessage.error("获取任务详情失败");
  } finally {
    pageLoading.value = false;
  }
};

const onSubmitEdit = async () => {
  // 简单的必填校验（按需调整）
  if (!paramForm.clothing && !paramForm.scene_detail) {
    return ElMessage.warning("请至少保留一些核心场景或服饰描述！");
  }

  isSubmitting.value = true;
  try {
    const payload = {
      task_id: taskId.value,
      params: { ...paramForm }, // 🚀 直接把整个表单对象传给后端
      is_new_version: true,
      // 删除了 denoising_strength
    };

    await FissionTaskAPI.regenerateTask(payload);
    ElMessage.success("重绘指令已发送，正在为您生成新版本！");
    router.back();
  } catch (error) {
    console.error(error);
  } finally {
    isSubmitting.value = false;
  }
};

const handleSaveUpscale = async () => {
  if (!upscaledImageUrl.value) return;

  isSaving.value = true;
  try {
    // 💡 这里的 updateTask 就是咱们刚才后端写的 PUT 接口
    // 后端 service 会自动识别 volcengine 域名并触发 MinIO 中转
    const res: any = await FissionTaskAPI.updateTask(taskId.value, {
      image_url: upscaledImageUrl.value,
      action_desc: "已完成 4K 高清重制",
    });

    const code = res.data?.code ?? res.code;
    if (code === 200 || code === 0) {
      ElMessage({
        message: "💎 高清原件已永久存入 MinIO 并更新数据库！",
        type: "success",
        duration: 5000,
      });
      // 保存成功后，可以考虑直接返回列表，或者刷新原图 URL
      originalImageUrl.value = upscaledImageUrl.value;
      upscaledImageUrl.value = ""; // 清空对比状态，回到单图模式
    }
  } catch (error) {
    console.error("保存失败:", error);
    ElMessage.error("同步至数据库失败，请检查网络");
  } finally {
    isSaving.value = false;
  }
};

// --- 操作方法 ---

// 🚀 核心：触发一键高清
const handleUpscale = async () => {
  isUpscaling.value = true;
  try {
    // 🚀 1. 精准判定当前需要高清的“目标图片”
    // 优先级：换背景预览 > 换脸预览 > 原始底片
    let targetUrlToUpscale = originalImageUrl.value;
    let currentMode = "original";

    if (fusedImageUrl.value) {
      targetUrlToUpscale = fusedImageUrl.value;
      currentMode = "fused";
    } else if (swappedImageUrl.value) {
      targetUrlToUpscale = swappedImageUrl.value;
      currentMode = "swapped";
    }

    // 🚀 2. 构造传参（重点注意这里多加了一个 target_url）
    const payload = {
      task_id: taskId.value,
      target_url: targetUrlToUpscale, // 告诉后端到底要高清哪张图
    };

    const res: any = await FissionTaskAPI.upscaleTask(payload);

    const code = res.data?.code ?? res.code;
    const resultData = res.data?.data ?? res.data;
    const new4KUrl = resultData.upscaled_url || resultData.image_url;

    if (code === 200 || code === 0) {
      // 🚀 3. 根据刚才的模式，把高清图“原路返回”覆盖
      if (currentMode === "fused") {
        fusedImageUrl.value = new4KUrl;
        ElMessage.success("🖼️ 背景瞬移效果已完成 4K 画质重构！");
      } else if (currentMode === "swapped") {
        swappedImageUrl.value = new4KUrl;
        ElMessage.success("🎭 换脸效果已完成 4K 细节强化！");
      } else {
        // 💎 只有在高清“原始底片”时，才赋值给 upscaledImageUrl 以唤起保存按钮
        upscaledImageUrl.value = new4KUrl;
        ElMessage.success("💎 底片 4K 高清放大成功！");
      }
    } else {
      ElMessage.error(res.data?.msg || res.msg || "高清处理失败");
    }
  } catch (error) {
    console.error("超分请求报错:", error);
    ElMessage.error("接口请求异常，请检查后端服务");
  } finally {
    isUpscaling.value = false;
  }
};

const resetForm = () => {
  // 🚀 恢复到进入页面时的快照状态
  Object.assign(paramForm, backupParams);
  ElMessage.info("参数已重置为当前版本的初始状态");
};
const goBack = () => router.back();

onMounted(() => initData());
</script>
<template>
  <div class="app-container" v-loading="pageLoading">
    <BgHistoryDialog
      v-model="historyDialog.visible"
      :history-list="historyDialog.list"
      @apply="handleApplyHistoryBg"
    />
    <el-page-header @back="goBack" class="mb-6 bg-white p-4 border border-gray-100 rounded-sm">
      <template #content>
        <span class="text-base font-bold">✨ 图片精修室</span>
      </template>
      <template #extra>
        <el-tag type="info">任务 ID: {{ taskId }}</el-tag>
      </template>
    </el-page-header>

    <el-row :gutter="24">
      <el-col :xs="24" :md="14" :lg="16">
        <el-card shadow="never" class="h-full bg-gray-50 border-gray-200">
          <div
            v-if="!upscaledImageUrl && !swappedImageUrl && !fusedImageUrl"
            class="flex flex-col items-center justify-center min-h-[600px]"
          >
            <el-image
              v-if="originalImageUrl"
              :src="originalImageUrl"
              fit="contain"
              @click="openPreview(originalImageUrl)"
              class="max-w-full max-h-[700px] rounded-sm shadow-md transition-all hover:scale-[1.01]"
            />
            <el-empty v-else description="未获取到原图数据" />
          </div>

          <div v-else class="flex flex-col min-h-[600px] justify-center">
            <el-alert
              :title="
                fusedImageUrl
                  ? '🖼️ 背景瞬移成功！请检查人物与新环境的融合效果'
                  : swappedImageUrl
                    ? '🎭 换脸处理成功！已为您融合面部细节'
                    : '✨ 高清放大成功！点击图片可查看 4K 细节对比'
              "
              :type="fusedImageUrl ? 'info' : swappedImageUrl ? 'warning' : 'success'"
              show-icon
              :closable="false"
              class="mb-4"
            />

            <el-row :gutter="20" class="items-start">
              <el-col :span="12" class="text-center sticky top-0">
                <el-tag effect="dark" type="info" class="mb-2 w-24">🔍 原始底片</el-tag>
                <el-image
                  :src="originalImageUrl"
                  fit="contain"
                  @click="openPreview(originalImageUrl)"
                  class="w-full h-[600px] rounded-sm shadow-sm border border-gray-200 bg-white"
                />
              </el-col>

              <el-col
                :span="12"
                class="flex flex-col gap-6 max-h-[630px] overflow-y-auto custom-scrollbar pr-2"
              >
                <div
                  v-if="upscaledImageUrl"
                  class="text-center bg-green-50/30 p-2 rounded border border-green-100"
                >
                  <el-tag effect="dark" type="success" class="mb-2 w-32">💎 4K 高清重制</el-tag>
                  <el-image
                    :src="upscaledImageUrl"
                    fit="contain"
                    @click="openPreview(upscaledImageUrl)"
                    class="w-full h-[400px] rounded-sm shadow-md border-2 border-green-200 bg-white"
                  />
                </div>

                <div
                  v-if="swappedImageUrl"
                  class="text-center bg-purple-50/30 p-2 rounded border border-purple-100"
                >
                  <el-tag effect="dark" type="warning" class="mb-2 w-32">🎭 换脸效果</el-tag>
                  <el-image
                    :src="swappedImageUrl"
                    fit="contain"
                    @click="openPreview(swappedImageUrl)"
                    class="w-full h-[400px] rounded-sm shadow-md border-2 border-purple-200 bg-white"
                  />
                </div>

                <div
                  v-if="fusedImageUrl"
                  class="text-center bg-blue-50/30 p-2 rounded border border-blue-100"
                >
                  <el-tag effect="dark" type="primary" class="mb-2 w-32">🖼️ 背景瞬移预览</el-tag>
                  <el-image
                    :src="fusedImageUrl"
                    @click="openPreview(fusedImageUrl)"
                    fit="contain"
                    class="w-full h-[400px] rounded-sm shadow-md border-2 border-blue-200 bg-white"
                  />
                </div>

                <div
                  v-if="!upscaledImageUrl && !swappedImageUrl && !fusedImageUrl"
                  class="flex flex-col items-center justify-center h-[600px] border-2 border-dashed border-gray-200 rounded-sm text-gray-400 bg-gray-50/50"
                >
                  <el-icon size="40" class="mb-2"><Picture /></el-icon>
                  <span>请在右侧面板执行精修操作</span>
                  <span class="text-xs mt-1">处理结果将在此垂直展示</span>
                </div>
              </el-col>
            </el-row>
          </div>

          <div class="text-center text-gray-400 mt-4 text-sm">提示：点击图片可唤起大图全屏预览</div>

          <div class="batch-filmstrip-container mt-6 pt-4 border-t border-gray-100">
            <div class="flex items-center gap-2 mb-3 text-gray-500 text-xs font-bold px-1">
              <el-icon><Collection /></el-icon>
              <span>同批次底片 (共 {{ siblingTasks.length }} 张)</span>
            </div>

            <div class="flex items-center gap-2 w-full">
              <el-button
                circle
                :icon="ArrowLeft"
                class="scroll-btn"
                @click="handleScroll(-300)"
                :disabled="siblingTasks.length <= 0"
              />

              <el-scrollbar ref="scrollbarRef" class="flex-1 overflow-hidden">
                <div class="flex flex-nowrap gap-3 pb-2 px-1 w-max">
                  <div
                    v-for="item in siblingTasks"
                    :key="item.id"
                    class="filmstrip-item"
                    :class="{ 'is-active': item.id == taskId }"
                    @click="switchTask(item)"
                  >
                    <el-image
                      :src="item.image_url"
                      fit="cover"
                      class="w-20 h-28 rounded shadow-sm border-2 transition-all"
                    />
                    <div class="item-view-tag">{{ item.view_type || "预览" }}</div>
                  </div>
                </div>
              </el-scrollbar>

              <el-button
                circle
                :icon="ArrowRight"
                class="scroll-btn"
                @click="handleScroll(300)"
                :disabled="siblingTasks.length <= 0"
              />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10" :lg="8">
        <el-card
          shadow="hover"
          class="control-panel sticky top-4 w-full"
          :body-style="{
            maxHeight: 'calc(100vh - 120px)',
            overflowY: 'auto',
            paddingBottom: '30px',
          }"
        >
          <template #header>
            <div class="flex justify-between items-center">
              <span class="font-bold flex items-center gap-2">
                <el-icon><Setting /></el-icon>
                AI 视觉导演面板
              </span>
              <el-tag size="small" type="warning" v-if="currentVersion">
                Version: v{{ currentVersion }}
              </el-tag>
            </div>
          </template>

          <div class="mb-6 bg-blue-50/50 p-4 rounded-md border border-blue-100">
            <div class="font-bold text-blue-800 mb-2 flex items-center gap-1">
              <el-icon><Picture /></el-icon>
              画质极速提升
            </div>
            <div class="text-xs text-gray-500 mb-3">
              调用火山引擎视觉大模型，无损放大画质，补充发丝与皮肤毛孔细节。
            </div>
            <div class="flex flex-col gap-3 w-full items-stretch">
              <el-button
                type="primary"
                class="custom-btn"
                size="large"
                :icon="MagicStick"
                @click="handleUpscale"
                :loading="isUpscaling"
                :disabled="!!upscaledImageUrl"
              >
                {{ upscaledImageUrl ? "高清处理已完成" : "一键 4K 高清放大" }}
              </el-button>
              <el-collapse-transition>
                <el-button
                  v-if="upscaledImageUrl"
                  type="success"
                  class="custom-btn"
                  size="large"
                  :icon="Check"
                  :loading="isSaving"
                  @click="handleSaveUpscale"
                >
                  确认并保存高清图
                </el-button>
              </el-collapse-transition>
            </div>
          </div>

          <div class="mb-6 bg-purple-50/50 p-4 rounded-md border border-purple-100">
            <div class="font-bold text-purple-800 mb-2 flex items-center gap-1">
              <el-icon><User /></el-icon>
              一键 AI 换脸
            </div>
            <div class="text-xs text-gray-500 mb-3">
              上传一张面部清晰的照片，AI 将把五官精准融合到当前模特身上。
            </div>

            <div class="flex items-center gap-3">
              <el-upload
                class="face-upload"
                action="#"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleFaceSwapUpload"
              >
                <div v-if="!tempFaceUrl" class="face-upload-placeholder">
                  <el-icon><Plus /></el-icon>
                  <span class="text-xs">人脸图</span>
                </div>
                <el-image v-else :src="tempFaceUrl" class="face-preview-mini" fit="cover" />
              </el-upload>

              <div class="flex-1 flex flex-col gap-2">
                <el-button
                  type="primary"
                  class="w-full custom-btn face-btn"
                  :icon="Avatar"
                  :loading="isSwapping"
                  :disabled="!tempFaceUrl"
                  @click="onDoFaceSwap"
                >
                  开始执行换脸
                </el-button>
              </div>
            </div>
          </div>

          <el-divider border-style="dashed">
            <span class="text-gray-400 text-xs">微调重绘参数</span>
          </el-divider>

          <div class="mb-6 bg-white p-4 rounded-md border border-gray-100 shadow-sm">
            <div class="text-sm font-bold mb-4 flex items-center gap-2">
              <el-icon class="text-blue-500"><MagicStick /></el-icon>
              <span>背景辅助工具</span>
            </div>
            <el-button
              type="primary"
              link
              size="small"
              icon="Clock"
              @click="historyDialog.visible = true"
            >
              瞬移历史记录
            </el-button>

            <div class="mb-4 p-3 bg-gray-50 rounded border border-gray-200">
              <div class="text-xs font-bold text-gray-700 mb-2 flex items-center justify-between">
                <span>🪄 瞬移魔法指令 (Prompt)</span>
                <el-tooltip
                  content="AI 将严格按照此指令融合。你可以在此处自由添加如'赛博朋克风格'等要求，然后再点击下方上传参考图。"
                >
                  <el-icon class="text-gray-400 cursor-pointer"><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <el-input
                v-model="fusionCustomPrompt"
                type="textarea"
                :rows="4"
                class="text-xs"
                placeholder="请输入融合提示词..."
              />
            </div>

            <el-row :gutter="12" class="items-stretch mb-2">
              <el-col :span="8">
                <el-upload
                  class="bg-tool-upload w-full h-full"
                  action="#"
                  :auto-upload="false"
                  :on-change="handleBackgroundFusion"
                  :show-file-list="false"
                >
                  <div
                    v-loading="isFusing"
                    class="tool-card tool-fusion h-full flex flex-col items-center justify-center py-2 bg-orange-50/50 border border-orange-100 rounded cursor-pointer hover:bg-orange-100 transition-colors"
                  >
                    <el-icon size="20" class="text-orange-500 mb-1"><Files /></el-icon>
                    <div class="tool-label text-[10px] font-bold text-gray-700">🖼️ 上传并瞬移</div>
                  </div>
                </el-upload>
              </el-col>

              <el-col :span="8">
                <div
                  class="h-full bg-gray-50 border border-gray-200 rounded p-2 flex flex-col justify-center"
                >
                  <div class="text-[10px] font-bold text-gray-500 mb-1 flex items-center gap-1">
                    <el-icon><SetUp /></el-icon>
                    AI 融合引擎
                  </div>
                  <el-select v-model="fusionModel" size="small" class="w-full">
                    <el-option label="Nano Banana 2" value="banana_2" />
                    <el-option label="火山 Seedream" value="seedream" />
                    <el-option label="通义万象" value="wan2.7-image" />
                    <el-option label="GPT 2" value="gpt" />
                  </el-select>
                </div>
              </el-col>

              <el-col :span="8">
                <div
                  class="h-full bg-gray-50 border border-gray-200 rounded p-2 flex flex-col justify-center"
                >
                  <div class="text-[10px] font-bold text-gray-500 mb-1 flex items-center gap-1">
                    <el-icon><Compass /></el-icon>
                    构图深度
                  </div>
                  <el-select
                    v-model="selectedDepthPrompt"
                    size="small"
                    class="w-full"
                    placeholder="选择构图"
                  >
                    <el-option
                      v-for="item in depthOptions"
                      :key="item.label"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </div>
              </el-col>

              <el-col :span="6">
                <div
                  class="h-full bg-gray-50 border border-gray-200 rounded p-1.5 flex flex-col justify-center"
                >
                  <div class="text-[10px] font-bold text-gray-500 mb-1">人物位置</div>
                  <el-select v-model="selectedPositionPrompt" size="small" placeholder="位置">
                    <el-option
                      v-for="item in positionOptions"
                      :key="item.label"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </div>
              </el-col>
            </el-row>
          </div>

          <el-collapse v-model="activeCollapse" class="params-collapse">
            <el-collapse-item name="scene">
              <template #title><span class="font-bold text-blue-600">🌍 环境与背景</span></template>
              <el-form label-position="top">
                <el-form-item label="背景细节描述">
                  <el-input
                    v-model="paramForm.scene_detail"
                    type="textarea"
                    :rows="5"
                    placeholder="描述石阶、植被、建筑..."
                  />
                </el-form-item>
                <el-form-item label="空气氛围">
                  <el-input
                    v-model="paramForm.atmosphere_detail"
                    placeholder="如：丁达尔光、湿润、薄雾..."
                  />
                </el-form-item>
              </el-form>
            </el-collapse-item>

            <el-collapse-item name="character">
              <template #title><span class="font-bold text-purple-600">💃 人物精修</span></template>
              <el-form label-position="top">
                <el-form-item label="服饰细节">
                  <el-input v-model="paramForm.clothing" type="textarea" :rows="5" />
                </el-form-item>
                <el-form-item label="面部与神韵">
                  <el-input
                    v-model="paramForm.face_description"
                    type="textarea"
                    :rows="2"
                    placeholder="眼神、表情细微调整"
                  />
                </el-form-item>
              </el-form>
            </el-collapse-item>

            <el-collapse-item name="lighting">
              <template #title><span class="font-bold text-orange-600">🕯️ 光影重配</span></template>
              <el-form label-position="top">
                <el-form-item label="光影质感">
                  <el-input v-model="paramForm.lighting_detail" type="textarea" :rows="5" />
                </el-form-item>
              </el-form>
            </el-collapse-item>
          </el-collapse>

          <div class="mt-8 flex flex-col gap-3">
            <el-button
              type="warning"
              size="large"
              class="w-full font-bold custom-btn"
              @click="onSubmitEdit"
              :loading="isSubmitting"
            >
              🚀 生成新版本 (v{{ (currentVersion || 1) + 1 }})
            </el-button>
            <el-button @click="resetForm" plain class="custom-btn">重置所有参数</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-image-viewer
      v-if="showViewer"
      :key="previewIndex"
      :url-list="previewList"
      :initial-index="previewIndex"
      teleported
      @close="showViewer = false"
    />
  </div>
</template>

<style scoped>
.edit-form :deep(.el-form-item__label) {
  padding-bottom: 4px;
}
/* 给前后对比的图片加点平滑过渡效果 */
.el-image {
  transition: all 0.3s ease-in-out;
}
.custom-btn {
  width: 100% !important;
  margin-left: 0 !important; /* 消除 Element 按钮组自动带的左边距 */
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
}

.filmstrip-item {
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0 !important;
  width: 80px;
}

.scroll-btn {
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border-color: #e4e7ed;
}
.scroll-btn:hover {
  color: #409eff;
  border-color: #c6e2ff;
  background-color: #ecf5ff;
}

/* 🚀 隐藏丑陋的底部原生滚动条（因为我们有按钮了） */
:deep(.el-scrollbar__bar.is-horizontal) {
  display: none !important;
}

/* 确保 Flex 容器本身宽度由内容撑开 */
.w-max {
  width: max-content !important;
}
/* 确保父容器不换行 */
.flex.gap-3 {
  display: flex !important;
  flex-wrap: nowrap !important;
  /* 加上这一行，强制允许横向溢出 */
  overflow-x: visible !important;
  width: max-content; /* 核心：让容器宽度等于所有图片宽度之和 */
}

/* 隐藏横向滚动条的默认丑样式（可选，让界面更高级） */
:deep(.el-scrollbar__bar.is-horizontal) {
  height: 6px;
  bottom: 0;
}

.filmstrip-item .el-image {
  border-color: transparent;
}

.filmstrip-item:hover .el-image {
  transform: translateY(-2px);
  border-color: #409eff;
}

/* 选中状态 */
.filmstrip-item.is-active .el-image {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* 景别小标签 */
.item-view-tag {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  font-size: 10px;
  padding: 0 4px;
  border-radius: 2px;
  transform: scale(0.8);
}

/* 容器滚动美化 */
.batch-filmstrip-container :deep(.el-scrollbar__bar.is-horizontal) {
  height: 4px;
}

:deep(.el-scrollbar__wrap) {
  overflow-x: auto !important;
  overflow-y: hidden !important;
}

.preview-main-image {
  max-width: 100%;
  max-height: 700px;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  cursor: zoom-in;
  /* 只针对 transform 和 opacity，防止干扰 Element 预览层的位移计算 */
  transition:
    transform 0.3s ease,
    opacity 0.3s ease;
}

.preview-main-image:hover {
  transform: scale(1.01);
}

/* 强制预览层在最顶层，防止被某些 card 的 z-index 挡住 */
:deep(.el-image-viewer__wrapper) {
  z-index: 9999 !important;
}

.params-collapse {
  border: none !important;
}
.params-collapse :deep(.el-collapse-item__header) {
  font-size: 14px;
}
.upload-trigger {
  height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}
.upload-trigger:hover {
  background-color: #f0f7ff;
  color: #409eff;
}
.control-panel {
  max-height: 90vh;
  overflow-y: auto;
}
/* 滚动条美化 */
.control-panel::-webkit-scrollbar {
  width: 4px;
}
.control-panel::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 10px;
}

.face-upload-placeholder {
  width: 60px;
  height: 60px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fff;
  cursor: pointer;
  color: #909399;
}
.face-preview-mini {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  border: 2px solid #a855f7; /* 紫色边框表示人脸识别中 */
}
.face-btn {
  background-color: #a855f7 !important;
  border-color: #a855f7 !important;
  color: white !important;
}
.face-btn:hover {
  background-color: #9333ea !important;
  opacity: 0.9;
}
</style>
