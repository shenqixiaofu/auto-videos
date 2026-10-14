<template>
  <el-dialog v-model="visible" title="📸 手动补录策划底片" width="600px" append-to-body>
    <el-form :model="uploadForm" label-width="100px" ref="formRef" :rules="rules">
      <div class="grid grid-cols-2 gap-2">
        <el-form-item label="地点" prop="input_location">
          <el-input v-model="uploadForm.input_location" placeholder="如：阳朔西街" />
        </el-form-item>
        <el-form-item label="主题" prop="theme">
          <el-input v-model="uploadForm.theme" placeholder="如：古风旅拍" />
        </el-form-item>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <el-form-item label="性别" prop="gender">
          <el-select v-model="uploadForm.gender" class="w-full">
            <el-option
              v-for="item in genderOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄" prop="age">
          <el-input-number v-model="uploadForm.age" :min="1" :max="100" />
        </el-form-item>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <el-form-item label="具体场景" prop="selected_scene">
          <el-input v-model="uploadForm.selected_scene" placeholder="如：江边烟雨" />
        </el-form-item>
        <el-form-item label="具体风格" prop="selected_style">
          <el-input v-model="uploadForm.selected_style" placeholder="如：电影质感" />
        </el-form-item>
      </div>

      <el-form-item label="上传底片">
        <el-upload
          drag
          action="#"
          multiple
          :auto-upload="false"
          :on-change="handleFileChange"
          list-type="picture"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">可拖拽多张图片上传</div>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submitUpload">确认创建</el-button>
    </template>
  </el-dialog>
</template>
<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import { ElMessage, type UploadFile } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import { FileAPI } from "@/api/module_common/file";
import FissionAPI from "@/api/module_ai_image/fission";
const props = defineProps<{
  modelValue: boolean;
  genderOptions: any[];
}>();

const uploadedUrls = ref<string[]>([]);

const emit = defineEmits(["update:modelValue", "success"]);

// 弹窗可见性逻辑
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const submitting = ref(false);
const fileList = ref<UploadFile[]>([]);
const formRef = ref();

const uploadForm = reactive({
  input_location: "",
  theme: "",
  gender: "年轻女性",
  age: 20,
  selected_scene: "",
  selected_style: "",
});
const rules = {
  input_location: [{ required: true, message: "请输入地点", trigger: "blur" }],
  gender: [{ required: true, message: "请选择性别", trigger: "change" }],
};

const handleFileChange = async (file: UploadFile) => {
  if (file.status === "ready") {
    try {
      // 1. 立即调用你现有的 MinIO 上传接口
      const formData = new FormData();
      formData.append("file", file.raw as File);

      // 假设 FileAPI.uploadFile 返回的是 { data: { url: '...' } }
      const res: any = await FileAPI.uploadFile(formData);
      console.log("上传成功，res:", res);
      if (res.status === 200 || res.data.code === 0) {
        // 2. 拿到 MinIO 的地址，存起来
        uploadedUrls.value.push(res.data.data.file_url);
        ElMessage.success(`${file.name} 上传成功`);
      }
    } catch (error) {
      ElMessage.error(`${file.name} 上传到 MinIO 失败`);
    }
  }
};

const handleRemove = (file: UploadFile, files: UploadFile[]) => {
  fileList.value = files;
};

const handleClose = () => {
  formRef.value?.resetFields();
  fileList.value = [];
};

// 提交逻辑
const submitUpload = async () => {
  if (uploadedUrls.value.length === 0) return ElMessage.warning("还没传图呢");

  submitting.value = true;
  try {
    const payload = {
      ...uploadForm,
      image_urls: uploadedUrls.value, // 传的是 URL 数组，不是文件对象了
    };

    // 3. 调用你的业务接口：
    await FissionAPI.manualBatchCreate(payload);
    ElMessage.success("批次创建成功");
    emit("success");
    visible.value = false;
  } finally {
    submitting.value = false;
  }
};
</script>
