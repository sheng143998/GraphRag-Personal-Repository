<template>
  <section class="panel">
    <div class="panel-header">
      <h2 class="panel-title">文档上传入口</h2>
      <p class="panel-subtitle">先保留结构化字段，后端接好后可直接提交到 Spring Boot 上传接口。</p>
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
              <option value="技术笔记">技术笔记</option>
              <option value="开发经验">开发经验</option>
              <option value="项目经验">项目经验</option>
              <option value="面试经验">面试经验</option>
              <option value="代码片段">代码片段</option>
              <option value="招聘 JD">招聘 JD</option>
            </select>
          </label>
        </div>

        <label class="form-row">
          <span class="form-label">文件名占位</span>
          <div class="upload-dropzone">
            <strong>拖拽上传区域预留</strong>
            <span>当前先用逗号分隔文件名模拟上传，后续可替换为真实文件选择器与 FormData。</span>
            <input
              v-model="fileNamesInput"
              class="input"
              type="text"
              placeholder="例如：Spring事务.md, rag-retrospective.docx"
            />
          </div>
        </label>

        <label class="form-row">
          <span class="form-label">入库备注</span>
          <textarea
            v-model="notes"
            class="textarea"
            placeholder="记录文档来源、标签建议或解析说明。"
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
const documentType = ref("技术笔记");
const fileNamesInput = ref("");
const notes = ref("");

function normalizeFileNames(): string[] {
  return fileNamesInput.value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function fillDemo(): void {
  fileNamesInput.value = "spring-transaction-notes.md, rag-evaluation-retro.docx";
  notes.value = "首批导入材料，用于验证上传入口、文档分类和统一解析流程。";
}

async function handleSubmit(): Promise<void> {
  await store.submitUpload({
    knowledgeBaseId: knowledgeBaseId.value,
    documentType: documentType.value,
    notes: notes.value.trim(),
    fileNames: normalizeFileNames()
  });
}
</script>
