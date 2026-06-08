<template>
  <section class="panel">
    <div class="panel-header">
      <h2 class="panel-title">文档上传入口</h2>
      <p class="panel-subtitle">选择单篇文本文件，提交到 Spring Boot，再由 AI 服务完成解析、切块和入库。</p>
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
          <span class="form-label">文件</span>
          <div class="upload-dropzone">
            <strong>单篇文件入库</strong>
            <span>当前适合 Markdown、TXT、CSV、HTML 等文本文件；PDF / Word 真实解析后续接入。</span>
            <input
              class="input"
              type="file"
              accept=".md,.txt,.csv,.html,.json,.log"
              @change="handleFileChange"
            />
            <input
              v-model="fileName"
              class="input"
              type="text"
              placeholder="未选择文件时，可填写示例文件名"
            />
          </div>
        </label>

        <label class="form-row">
          <span class="form-label">文档标题</span>
          <input
            v-model="title"
            class="input"
            type="text"
            placeholder="例如：Spring 事务传播笔记"
          />
        </label>

        <label class="form-row">
          <span class="form-label">正文内容</span>
          <textarea
            v-model="content"
            class="textarea"
            placeholder="未选择文件时，可粘贴一段 Markdown、TXT 或其他文本内容。"
          />
        </label>

        <div class="button-row">
          <button class="button button-primary" type="submit" :disabled="store.uploadPending">
            {{ store.uploadPending ? "提交中..." : "提交上传任务" }}
          </button>
          <button class="button button-secondary" type="button" @click="fillDemo">
            填充示例
          </button>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useWorkbenchStore } from "../stores/workbench";

const store = useWorkbenchStore();
const knowledgeBaseId = ref(store.settings.defaultKnowledgeBaseId);
const documentType = ref("tech_note");
const fileName = ref("");
const title = ref("");
const content = ref("");
const selectedFile = ref<File | null>(null);

function fillDemo(): void {
  selectedFile.value = null;
  fileName.value = "spring-transaction-notes.md";
  title.value = "Spring 事务传播笔记";
  content.value = "Spring 事务传播行为中，REQUIRES_NEW 会挂起当前事务并开启一个新事务。";
}

function handleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  selectedFile.value = file;

  if (file) {
    fileName.value = file.name;
    if (!title.value.trim()) {
      title.value = file.name.replace(/\.[^.]+$/, "");
    }
  }
}

function inferFileType(name: string): string {
  const parts = name.trim().split(".");
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : "txt";
}

async function handleSubmit(): Promise<void> {
  await store.submitUpload({
    knowledgeBaseId: knowledgeBaseId.value,
    title: title.value.trim(),
    documentType: documentType.value,
    fileName: fileName.value.trim(),
    fileType: inferFileType(fileName.value),
    file: selectedFile.value ?? undefined,
    sourceType: "LOCAL_UPLOAD",
    content: selectedFile.value ? undefined : content.value.trim(),
    summary: content.value.trim().slice(0, 160),
    metadata: {
      source: selectedFile.value ? "frontend-multipart" : "frontend-demo"
    }
  });

  if (!store.lastError) {
    selectedFile.value = null;
    content.value = "";
  }
}
</script>
