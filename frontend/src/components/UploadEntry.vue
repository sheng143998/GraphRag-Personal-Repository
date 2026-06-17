<template>
  <section class="panel">
    <div class="panel-header">
      <h2 class="panel-title">文档上传入口</h2>
      <p class="panel-subtitle">支持单篇、多篇和文件夹上传；提交后立即进入异步解析、切分和入库流程。</p>
    </div>
    <div class="panel-body">
      <form class="form-grid" @submit.prevent="handleSubmit">
        <div class="split-columns">
          <label class="form-row">
            <span class="form-label">目标知识库</span>
            <select v-model="knowledgeBaseId" class="select">
              <option
                v-for="item in store.knowledgeBases"
                :key="item.id"
                :value="item.id"
              >
                {{ item.name }}
              </option>
            </select>
          </label>

          <label class="form-row">
            <span class="form-label">文档类型</span>
            <select v-model="documentType" class="select">
              <option value="tech_note">技术笔记</option>
              <option value="development_experience">开发经验</option>
              <option value="project_experience">项目经验</option>
              <option value="interview_experience">面试经验</option>
              <option value="code_snippet">代码片段</option>
              <option value="job_description">招聘 JD</option>
            </select>
          </label>
        </div>

        <label class="form-row">
          <span class="form-label">上传模式</span>
          <select v-model="uploadMode" class="select" @change="clearSelectedFiles">
            <option value="single">单篇文档</option>
            <option value="multiple">多篇文档</option>
            <option value="folder">文件夹</option>
          </select>
        </label>

        <label class="form-row">
          <span class="form-label">文件</span>
          <div class="upload-dropzone">
            <strong>{{ uploadModeLabel }}</strong>
            <span>支持 Markdown、TXT、CSV、HTML、JSON、LOG、Word 和 PDF。上传成功后文档会先显示 PROCESSING。</span>

            <input
              v-if="uploadMode === 'single'"
              class="input"
              type="file"
              accept=".md,.txt,.csv,.html,.json,.log,.docx,.pdf"
              @change="handleSingleFileChange"
            />
            <input
              v-else-if="uploadMode === 'multiple'"
              class="input"
              type="file"
              accept=".md,.txt,.csv,.html,.json,.log,.docx,.pdf"
              multiple
              @change="handleBatchFileChange"
            />
            <input
              v-else
              ref="folderInput"
              class="input"
              type="file"
              multiple
              accept=".md,.txt,.csv,.html,.json,.log,.docx,.pdf"
              @change="handleBatchFileChange"
            />

            <input
              v-if="uploadMode === 'single'"
              v-model="fileName"
              class="input"
              type="text"
              placeholder="未选择文件时，可填写示例文件名"
            />

            <div v-if="selectedFiles.length" class="empty-state">
              已选择 {{ selectedFiles.length }} 个文件
              <div v-for="item in selectedFilesPreview" :key="item" class="muted-line">
                {{ item }}
              </div>
            </div>
          </div>
        </label>

        <label class="form-row">
          <span class="form-label">文档标题</span>
          <input
            v-model="title"
            class="input"
            type="text"
            :placeholder="uploadMode === 'single' ? '例如：Spring 事务传播笔记' : '批量上传时可留空，默认使用文件名'"
          />
        </label>

        <label v-if="uploadMode === 'single'" class="form-row">
          <span class="form-label">正文内容</span>
          <textarea
            v-model="content"
            class="textarea"
            placeholder="未选择文件时，可粘贴一段 Markdown、TXT 或其他文本内容。"
          />
        </label>

        <div class="button-row">
          <button class="button button-primary" type="submit" :disabled="!canSubmit">
            {{ store.uploadPending ? "提交中..." : submitButtonText }}
          </button>
          <button class="button button-secondary" type="button" @click="fillDemo">
            填充示例
          </button>
        </div>
        <div v-if="validationMessage" class="empty-state">{{ validationMessage }}</div>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useWorkbenchStore } from "../stores/workbench";

type UploadMode = "single" | "multiple" | "folder";

interface SelectedFileItem {
  file: File;
  relativePath: string;
}

const ALLOWED_FILE_TYPES = new Set(["md", "txt", "csv", "html", "json", "log", "docx", "pdf"]);
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024;

const store = useWorkbenchStore();
const knowledgeBaseId = ref(store.settings.defaultKnowledgeBaseId);
const documentType = ref("tech_note");
const uploadMode = ref<UploadMode>("single");
const fileName = ref("");
const title = ref("");
const content = ref("");
const selectedFile = ref<File | null>(null);
const selectedFiles = ref<SelectedFileItem[]>([]);
const folderInput = ref<HTMLInputElement | null>(null);
const validationMessage = ref("");

const canSubmit = computed(() => !store.uploadPending && !validateUpload());
const uploadModeLabel = computed(() => {
  if (uploadMode.value === "multiple") return "多篇文档入库";
  if (uploadMode.value === "folder") return "文件夹入库";
  return "单篇文档入库";
});
const submitButtonText = computed(() => {
  if (uploadMode.value === "single") return "提交上传任务";
  return `提交 ${selectedFiles.value.length} 个解析任务`;
});
const selectedFilesPreview = computed(() => selectedFiles.value.slice(0, 5).map((item) => item.relativePath || item.file.name));

watch(() => store.settings.defaultKnowledgeBaseId, (value) => {
  if (!knowledgeBaseId.value) {
    knowledgeBaseId.value = value;
  }
});

watch([knowledgeBaseId, documentType, uploadMode, fileName, title, content, selectedFile, selectedFiles], () => {
  validationMessage.value = validateUpload();
}, { immediate: true, deep: true });

watch(uploadMode, async (value) => {
  if (value === "folder") {
    await nextTick();
    folderInput.value?.setAttribute("webkitdirectory", "");
    folderInput.value?.setAttribute("directory", "");
  }
});

function fillDemo(): void {
  uploadMode.value = "single";
  selectedFile.value = null;
  selectedFiles.value = [];
  fileName.value = "spring-transaction-notes.md";
  title.value = "Spring 事务传播笔记";
  content.value = "Spring 事务传播行为中，REQUIRES_NEW 会挂起当前事务并开启一个新事务。";
}

function handleSingleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  selectedFile.value = file;
  selectedFiles.value = file ? [toSelectedFileItem(file)] : [];

  if (file) {
    fileName.value = file.name;
    if (!title.value.trim()) {
      title.value = file.name.replace(/\.[^.]+$/, "");
    }
  }
}

function handleBatchFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  selectedFile.value = null;
  selectedFiles.value = Array.from(input.files ?? []).map(toSelectedFileItem);
  if (selectedFiles.value.length === 1 && !title.value.trim()) {
    title.value = selectedFiles.value[0].file.name.replace(/\.[^.]+$/, "");
  }
}

function clearSelectedFiles(): void {
  selectedFile.value = null;
  selectedFiles.value = [];
  fileName.value = "";
  content.value = "";
}

function toSelectedFileItem(file: File): SelectedFileItem {
  const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
  return {
    file,
    relativePath
  };
}

function inferFileType(name: string): string {
  const parts = name.trim().split(".");
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : "txt";
}

function validateUpload(): string {
  if (!knowledgeBaseId.value) {
    return "上传前请选择目标知识库。";
  }

  if (!documentType.value) {
    return "请选择文档类型。";
  }

  if (uploadMode.value === "single") {
    return validateSingleUpload();
  }

  if (!selectedFiles.value.length) {
    return uploadMode.value === "folder" ? "请选择一个文件夹。" : "请选择至少一个文件。";
  }

  const invalidFile = selectedFiles.value.find((item) => !ALLOWED_FILE_TYPES.has(inferFileType(item.file.name)));
  if (invalidFile) {
    return `不支持的文件类型：${invalidFile.file.name}`;
  }

  const oversizedFile = selectedFiles.value.find((item) => item.file.size > MAX_FILE_SIZE_BYTES);
  if (oversizedFile) {
    return `文件不能超过 50 MB：${oversizedFile.file.name}`;
  }

  return "";
}

function validateSingleUpload(): string {
  const resolvedFileName = selectedFile.value?.name || fileName.value.trim();
  const fileType = inferFileType(resolvedFileName);

  if (!title.value.trim()) {
    return "请输入文档标题。";
  }

  if (!resolvedFileName) {
    return "请选择文件，或为粘贴内容填写文件名。";
  }

  if (!ALLOWED_FILE_TYPES.has(fileType)) {
    return `不支持的文件类型：${fileType}`;
  }

  if (selectedFile.value && selectedFile.value.size > MAX_FILE_SIZE_BYTES) {
    return "文件大小不能超过 50 MB。";
  }

  if (!selectedFile.value && !content.value.trim()) {
    return "未选择文件时，请粘贴正文内容。";
  }

  return "";
}

async function handleSubmit(): Promise<void> {
  validationMessage.value = validateUpload();
  if (validationMessage.value) {
    return;
  }

  if (uploadMode.value === "single") {
    await submitSingleUpload();
  } else {
    await submitBatchUpload();
  }

  if (!store.lastError) {
    selectedFile.value = null;
    selectedFiles.value = [];
    content.value = "";
  }
}

async function submitSingleUpload(): Promise<void> {
  const resolvedFileName = selectedFile.value?.name || fileName.value.trim();
  await store.submitUpload({
    knowledgeBaseId: knowledgeBaseId.value,
    title: title.value.trim(),
    documentType: documentType.value,
    fileName: resolvedFileName,
    fileType: inferFileType(resolvedFileName),
    file: selectedFile.value ?? undefined,
    sourceType: "LOCAL_UPLOAD",
    sourcePath: selectedFile.value ? selectedFile.value.name : resolvedFileName,
    content: selectedFile.value ? undefined : content.value.trim(),
    summary: content.value.trim().slice(0, 160),
    metadata: {
      source: selectedFile.value ? "frontend-multipart" : "frontend-demo"
    }
  });
}

async function submitBatchUpload(): Promise<void> {
  await store.submitBatchUpload({
    knowledgeBaseId: knowledgeBaseId.value,
    title: title.value.trim() || undefined,
    documentType: documentType.value,
    sourceType: uploadMode.value === "folder" ? "LOCAL_FOLDER_UPLOAD" : "LOCAL_BATCH_UPLOAD",
    files: selectedFiles.value,
    metadata: {
      source: uploadMode.value === "folder" ? "frontend-folder" : "frontend-batch",
      uploadMode: uploadMode.value
    }
  });
}
</script>
