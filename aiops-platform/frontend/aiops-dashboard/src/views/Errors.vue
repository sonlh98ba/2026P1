<template>
  <AdminLayout>
    <div class="ops-panel p-5 mb-6">
      <h1 class="ops-title">Knowledge Base Giải pháp</h1>
      <p class="ops-subtitle">
        Lọc theo dữ liệu từ Kibana, so khớp với KB và cập nhật hướng xử lý tự
        động.
      </p>
    </div>
    <div class="ops-panel p-4">
      <div class="mb-4 flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <input
          v-model="filters.q"
          type="text"
          class="ops-input w-full lg:max-w-lg"
          placeholder="Tìm nhanh theo thông điệp lỗi"
          @keyup.enter="applyFilters"
        />
        <div ref="advancedFilterRef" class="relative flex justify-end gap-2">
          <button class="ops-btn inline-flex items-center gap-2" @click="toggleAdvancedFilter">
            <span>Lọc nâng cao</span>
            <span aria-hidden="true">{{ showAdvancedFilter ? "▲" : "▼" }}</span>
          </button>
          <button
            class="ops-btn ops-btn-primary disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="!hasAnyFilter"
            @click="applyFilters"
          >
            Lọc
          </button>
          <Transition name="advanced-filter">
            <div
              v-if="showAdvancedFilter"
              class="absolute right-0 top-[calc(100%+8px)] z-20 w-[min(90vw,800px)] rounded-lg border border-slate-700/80 bg-slate-900 p-4 shadow-2xl"
            >
              <div class="rounded-lg border border-slate-700/70 bg-slate-800/35 p-3">
                <div class="grid grid-cols-2 gap-3 border-b border-slate-700/70 pb-2 text-sm font-semibold text-slate-200">
                  <p>Điều kiện lọc</p>
                  <p>Giá trị lọc đã chọn</p>
                </div>
                <div class="mt-3 space-y-2">
                  <div
                    v-for="field in filterFieldOptions"
                    :key="`${field.key}-row`"
                    class="grid grid-cols-2 items-center gap-3"
                  >
                    <label class="flex items-center gap-2 text-sm text-slate-200">
                      <input
                        v-model="selectedFilterKeys"
                        type="checkbox"
                        :value="field.key"
                        class="h-4 w-4"
                      />
                      <span>{{ field.label }}</span>
                    </label>
                    <input
                      v-if="selectedFilterKeys.includes(field.key)"
                      v-model="filters[field.key]"
                      type="text"
                      class="ops-input"
                      :placeholder="field.placeholder"
                      @keyup.enter="applyFilters"
                    />
                    <div
                      v-else
                      class="ops-input opacity-50 cursor-not-allowed select-none"
                    >
                      Chưa chọn
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>
      <p v-if="isLoading" class="mb-3 text-sm text-slate-300">Đang tải dữ liệu lỗi...</p>
      <p v-if="fetchError" class="mb-3 text-sm text-rose-300">{{ fetchError }}</p>
      <div class="overflow-x-auto">
        <table class="ops-table min-w-[900px]">
          <thead>
            <tr>
              <th class="text-left">Thông điệp lỗi</th>
              <th class="text-center">Loại</th>
              <th class="text-center">Số lần</th>
              <th class="text-left">Hướng xử lý</th>
              <th class="text-center">Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in solutions"
              :key="item.id"
              class="cursor-pointer hover:bg-slate-800/35"
              @click="openDetail(item)"
            >
              <td>
                <div class="max-w-[360px] truncate" :title="item.message">
                  {{ item.message }}
                </div>
              </td>
              <td class="text-center">{{ item.type || "UNKNOWN" }}</td>
              <td class="text-center font-semibold">{{ item.count ?? 0 }}</td>
              <td>
                <div
                  class="max-w-[420px] truncate"
                  :title="item.solution || 'Chưa có solution cho lỗi này.'"
                >
                  {{ item.solution || "Chưa có solution cho lỗi này." }}
                </div>
              </td>
              <td class="text-center">
                <span :class="statusClass(item.status)">{{ item.status }}</span>
              </td>
            </tr>
            <tr v-if="!solutions.length">
              <td class="text-center text-slate-400 py-4" colspan="5">
                Không tìm thấy lỗi trong Knowledge Base theo trace.id này.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="mt-4 flex flex-col gap-3 text-sm text-slate-300 md:flex-row md:items-center md:justify-between">
        <p>
          Hiển thị {{ pageStart }}-{{ pageEnd }} / {{ totalItems }} kết quả
        </p>
        <div class="flex items-center gap-2 whitespace-nowrap">
          <button
            class="ops-btn disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="isLoading || currentPage <= 1"
            @click="goToPage(currentPage - 1)"
          >
            Trước
          </button>
          <span>Trang {{ currentPage }} / {{ safeTotalPages }}</span>
          <button
            class="ops-btn disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="isLoading || currentPage >= safeTotalPages"
            @click="goToPage(currentPage + 1)"
          >
            Sau
          </button>
          <label class="ml-2">Số dòng/trang</label>
          <select v-model.number="pageSize" class="ops-input w-24" @change="changePageSize">
            <option
              v-for="size in pageSizeOptions"
              :key="`page-size-${size}`"
              :value="size"
            >
              {{ size }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <div
      v-if="selectedError"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/65 p-4"
      @click.self="closeDetail"
    >
      <div class="ops-panel w-full max-w-5xl">
        <div
          class="flex items-center justify-between border-b border-slate-700/70 px-5 py-4"
        >
          <h2 class="text-xl font-semibold">Chi tiết lỗi</h2>
          <button class="ops-btn" @click="closeDetail">Đóng</button>
        </div>
        <div class="max-h-[75vh] overflow-y-auto p-5 space-y-4">
          <section>
            <div class="mb-1 flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-300">Thông tin chi tiết</p>
              <button class="ops-btn text-xs" @click="showMetaSection = !showMetaSection">
                {{ showMetaSection ? "▲" : "▼" }}
              </button>
            </div>
            <div
              v-if="showMetaSection"
              class="grid grid-cols-1 gap-3 rounded-lg border border-slate-700 bg-slate-900/40 p-3 md:grid-cols-2"
            >
              <div class="break-all"><strong>ID:</strong> {{ selectedError.id }}</div>
              <div class="break-all">
                <strong>Fingerprint:</strong>
                {{ selectedError.fingerprint || "-" }}
              </div>
              <div>
                <strong>Loại:</strong> {{ selectedError.type || "UNKNOWN" }}
              </div>
              <div>
                <strong>Mức độ:</strong> {{ selectedError.severity || "-" }}
              </div>
              <div>
                <strong>Service:</strong> {{ selectedError.service || "-" }}
              </div>
              <div class="break-all"><strong>API:</strong> {{ selectedError.api || "-" }}</div>
              <div><strong>Nhãn:</strong> {{ selectedError.label || "-" }}</div>
              <div><strong>Số lần:</strong> {{ selectedError.count ?? 0 }}</div>
              <div>
                <strong>Độ tin cậy:</strong> {{ selectedError.confidence ?? "-" }}
              </div>
              <div>
                <strong>Lần đầu xuất hiện:</strong>
                {{ formatTime(selectedError.first_seen) }}
              </div>
              <div>
                <strong>Lần gần nhất:</strong>
                {{ formatTime(selectedError.last_seen) }}
              </div>
              <div>
                <strong>Trạng thái:</strong
                ><span :class="statusClass(selectedError.status)" class="ml-2">{{
                  selectedError.status
                }}</span>
              </div>
            </div>
          </section>
          <section>
            <p class="mb-1 text-sm font-semibold text-slate-300">
              Thông điệp gốc
            </p>
            <div
              class="rounded-lg border border-slate-700 bg-slate-900/50 p-3 text-sm whitespace-pre-wrap break-words"
            >
              {{ selectedError.raw_message || selectedError.message || "-" }}
            </div>
          </section>
          <section>
            <p class="mb-1 text-sm font-semibold text-slate-300">
              Thông điệp chuẩn hóa
            </p>
            <div
              class="rounded-lg border border-slate-700 bg-slate-900/50 p-3 text-sm whitespace-pre-wrap break-words"
            >
              {{ selectedError.normalized_message || "-" }}
            </div>
          </section>
          <section>
            <div class="mb-1 flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-300">Hướng xử lý</p>
              <button class="ops-btn text-xs" @click="showSolutionSection = !showSolutionSection">
                {{ showSolutionSection ? "▲" : "▼" }}
              </button>
            </div>
            <textarea
              v-if="showSolutionSection"
              ref="solutionTextareaRef"
              v-model="form.solution"
              class="ops-input min-h-28 overflow-hidden resize-none"
              placeholder="Nhập hướng xử lý cho lỗi này"
              @input="autoResizeSolution"
            />
          </section>
          <section>
            <div class="mb-1 flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-300">
                Script tự động khắc phục
              </p>
              <button class="ops-btn text-xs" @click="showScriptSection = !showScriptSection">
                {{ showScriptSection ? "▲" : "▼" }}
              </button>
            </div>
            <div
              v-if="showScriptSection"
              class="space-y-3 rounded-lg border border-slate-700 bg-slate-900/40 p-3"
            >
              <div class="flex flex-wrap items-center gap-2">
                <button class="ops-btn text-xs" @click="addAutomationCard('call_api')">
                  + Call API
                </button>
                <button class="ops-btn text-xs" @click="addAutomationCard('send_email')">
                  + Send Email
                </button>
                <button class="ops-btn text-xs" @click="addAutomationCard('db_query')">
                  + Tác động database
                </button>
                <label class="ml-auto text-xs text-slate-300">
                  Timeout (s)
                  <input
                    v-model.number="automationTimeout"
                    min="1"
                    type="number"
                    class="ops-input mt-1 w-24"
                  />
                </label>
              </div>

              <div v-if="automationCards.length" class="space-y-2">
                <div
                  v-for="(card, idx) in automationCards"
                  :key="card.id"
                  draggable="true"
                  class="rounded-lg border border-slate-700 bg-slate-950/35 p-3"
                  @dragstart="onCardDragStart(idx)"
                  @dragover.prevent
                  @drop="onCardDrop(idx)"
                >
                  <div class="mb-2 flex items-center justify-between">
                    <div class="text-sm font-semibold text-slate-200">
                      {{ idx + 1 }}.
                      {{
                        card.action === "call_api"
                          ? "Call API"
                          : card.action === "send_email"
                            ? "Send Email"
                            : "Tác động database"
                      }}
                    </div>
                    <button class="ops-btn text-xs" @click="removeAutomationCard(card.id)">Xóa</button>
                  </div>

                  <div v-if="card.action === 'call_api'" class="grid grid-cols-1 gap-2 md:grid-cols-2">
                    <select v-model="card.method" class="ops-input">
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="PATCH">PATCH</option>
                      <option value="DELETE">DELETE</option>
                    </select>
                    <input v-model="card.url" class="ops-input" placeholder="https://example.com/hook" />
                    <div class="md:col-span-2 flex justify-start">
                      <button class="ops-btn text-xs" @click="toggleCardExpect(card)">
                        {{ card.hasExpect ? "Bỏ expect" : "Thêm expect" }}
                      </button>
                    </div>
                    <template v-if="card.hasExpect">
                      <div class="md:col-span-2 space-y-2">
                        <div
                          v-for="(expect, expectIdx) in card.expects"
                          :key="expect.id"
                          class="grid grid-cols-1 gap-2 md:grid-cols-12"
                        >
                          <input
                            v-model="expect.path"
                            class="ops-input md:col-span-5"
                            placeholder="Expect path (vd: data.status)"
                          />
                          <input
                            v-model="expect.equals"
                            class="ops-input md:col-span-5"
                            placeholder='Expect equals (vd: "SUCCESS" hoặc 200)'
                          />
                          <button
                            class="ops-btn text-xs md:col-span-2"
                            @click="removeExpect(card, expect.id)"
                            :disabled="card.expects.length <= 1"
                          >
                            Xóa
                          </button>
                        </div>
                        <button class="ops-btn text-xs" @click="addExpect(card)">+ Thêm expect</button>
                      </div>
                    </template>
                    <textarea
                      v-model="card.headersText"
                      class="ops-input min-h-24 font-mono text-xs md:col-span-2"
                      placeholder='Headers JSON, ví dụ: {"Authorization":"Bearer ..."}'
                    />
                    <textarea
                      v-model="card.bodyText"
                      class="ops-input min-h-24 font-mono text-xs md:col-span-2"
                      placeholder='Body JSON, ví dụ: {"error_id":"{error_id}"}'
                    />
                  </div>

                  <div v-else-if="card.action === 'send_email'" class="grid grid-cols-1 gap-2">
                    <input v-model="card.to" class="ops-input" placeholder="Email nhận, nhiều email cách nhau dấu phẩy" />
                    <input v-model="card.subject" class="ops-input" placeholder="Tiêu đề email" />
                    <textarea
                      v-model="card.body"
                      class="ops-input min-h-24"
                      placeholder="Nội dung email (có thể dùng {error_id}, {service}, {message}...)"
                    />
                  </div>

                  <div v-else-if="card.action === 'db_query'" class="grid grid-cols-1 gap-2">
                    <select v-model="card.database" class="ops-input">
                      <option value="default">default</option>
                      <option value="analytics">analytics</option>
                      <option value="reporting">reporting</option>
                    </select>
                    <textarea
                      v-model="card.sql"
                      class="ops-input min-h-24 font-mono text-xs"
                      placeholder="SQL cần thực thi, ví dụ: UPDATE incidents SET status='RESOLVED' WHERE id=:incident_id"
                    />
                    <textarea
                      v-model="card.paramsText"
                      class="ops-input min-h-24 font-mono text-xs"
                      placeholder='Params JSON, ví dụ: {\"incident_id\":\"{error_id}\"}'
                    />
                    <input
                      v-model.number="card.maxRows"
                      type="number"
                      min="1"
                      class="ops-input w-36"
                      placeholder="max_rows"
                    />
                  </div>
                </div>
              </div>
              <p v-else class="text-sm text-slate-400">
                Chưa có action nào. Thêm thẻ ở trên và kéo để sắp xếp thứ tự thực thi.
              </p>

              <p v-if="automationBuilderError" class="text-sm text-rose-300">
                {{ automationBuilderError }}
              </p>

              <textarea
                v-model="form.auto_fix_script"
                readonly
                class="ops-input min-h-28 font-mono text-xs opacity-80"
                placeholder="JSON script sẽ được sinh tự động từ các thẻ"
              />
            </div>
          </section>
          <section v-if="executeMessage" class="rounded-lg border border-slate-700 bg-slate-900/50 p-3 text-sm whitespace-pre-wrap break-words">
            {{ executeMessage }}
          </section>
          <div class="flex justify-end gap-2">
            <button
              class="ops-btn disabled:opacity-60"
              :disabled="executing || !form.auto_fix_script?.trim() || Boolean(automationBuilderError)"
              @click="executeScript"
            >
              {{ executing ? "Đang thực thi..." : "Thực thi tự động" }}
            </button>
            <button
              class="ops-btn ops-btn-primary disabled:opacity-60"
              :disabled="saving || Boolean(automationBuilderError)"
              @click="saveDetail"
            >
              {{ saving ? "Đang lưu..." : "Lưu thay đổi" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>
<script setup>
import { computed, ref, watch, nextTick, onBeforeUnmount, onMounted } from "vue";
import axios from "axios";
import AdminLayout from "../layouts/AdminLayout.vue";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";
const solutions = ref([]);
const selectedError = ref(null);
const saving = ref(false);
const executing = ref(false);
const isLoading = ref(false);
const fetchError = ref("");
const executeMessage = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);
const totalPages = ref(0);
const pageSizeOptions = [10, 20, 50, 100];
const showAdvancedFilter = ref(false);
const advancedFilterRef = ref(null);
const solutionTextareaRef = ref(null);
const showMetaSection = ref(false);
const showSolutionSection = ref(false);
const showScriptSection = ref(false);
const filters = ref({
  trace_id: "",
  type: "",
  status: "",
  severity: "",
  service: "",
  api: "",
  label: "",
  q: "",
});
const selectedFilterKeys = ref([]);
const filterTree = [
  {
    group: "Định danh",
    fields: [
      { key: "trace_id", label: "Trace ID", placeholder: "trace.id" },
      { key: "service", label: "Service", placeholder: "Service: auth,payment" },
      { key: "api", label: "API", placeholder: "API: /login,/checkout" },
    ],
  },
  {
    group: "Phân loại",
    fields: [
      { key: "type", label: "Loại lỗi", placeholder: "Loại: SYSTEM,BUSINESS" },
      {
        key: "status",
        label: "Trạng thái",
        placeholder: "Trạng thái: resolved,unresolved",
      },
      { key: "severity", label: "Mức độ", placeholder: "Mức độ: HIGH,MEDIUM" },
      { key: "label", label: "Nhãn", placeholder: "Nhãn: unconfirmed,known" },
    ],
  },
];
const filterFieldOptions = filterTree.flatMap((group) => group.fields);
const form = ref({ solution: "", auto_fix_script: "" });
const automationCards = ref([]);
const automationTimeout = ref(10);
const automationBuilderError = ref("");
const draggedCardIndex = ref(null);
let nextAutomationCardId = 1;
let nextExpectId = 1;

const createCard = (action) => {
  const id = `${action}-${nextAutomationCardId++}`;
  if (action === "db_query") {
    return {
      id,
      action: "db_query",
      database: "default",
      sql: "",
      paramsText: "{}",
      maxRows: 50,
    };
  }
  if (action === "send_email") {
    return {
      id,
      action: "send_email",
      to: "",
      subject: "",
      body: "",
    };
  }
  return {
    id,
    action: "call_api",
    method: "POST",
    url: "",
    hasExpect: false,
    expects: [],
    headersText: "{}",
    bodyText: "{}",
  };
};

const safeJsonParse = (text, fallbackValue = null) => {
  if (!String(text ?? "").trim()) return fallbackValue;
  return JSON.parse(String(text));
};

const syncScriptFromCards = () => {
  try {
    const actions = automationCards.value.map((card) => {
      if (card.action === "db_query") {
        return {
          action: "db_query",
          database: card.database || "default",
          sql: card.sql || "",
          params: safeJsonParse(card.paramsText, {}),
          max_rows: Number(card.maxRows) || 50,
        };
      }
      if (card.action === "send_email") {
        const toList = String(card.to || "")
          .split(",")
          .map((email) => email.trim())
          .filter(Boolean);
        return {
          action: "send_email",
          to: toList,
          subject: card.subject || "",
          body: card.body || "",
        };
      }
      const step = {
        action: "call_api",
        method: String(card.method || "POST").toUpperCase(),
        url: card.url || "",
        headers: safeJsonParse(card.headersText, {}),
        body: safeJsonParse(card.bodyText, {}),
      };
      if (card.hasExpect) {
        const expects = (card.expects || [])
          .filter((exp) => String(exp.path || "").trim())
          .map((exp) => {
            let expectValue = exp.equals;
            try {
              expectValue = JSON.parse(String(exp.equals ?? ""));
            } catch (err) {
              expectValue = String(exp.equals ?? "");
            }
            return {
              path: String(exp.path).trim(),
              equals: expectValue,
            };
          });
        if (expects.length === 1) {
          step.expect = expects[0];
        } else if (expects.length > 1) {
          step.expects = expects;
        }
      }
      return step;
    });

    form.value.auto_fix_script = JSON.stringify(
      {
        timeout_seconds: Number(automationTimeout.value) || 10,
        actions,
      },
      null,
      2,
    );
    automationBuilderError.value = "";
  } catch (err) {
    automationBuilderError.value = "Card cấu hình chưa hợp lệ JSON (headers/body/params).";
  }
};

const loadAutomationFromScript = (scriptText) => {
  automationBuilderError.value = "";
  if (!String(scriptText ?? "").trim()) {
    automationTimeout.value = 10;
    automationCards.value = [];
    syncScriptFromCards();
    return;
  }

  try {
    const parsed = JSON.parse(scriptText);
    const actions = Array.isArray(parsed?.actions) ? parsed.actions : [];
    automationTimeout.value = Number(parsed?.timeout_seconds) || 10;
    automationCards.value = actions.map((action) => {
      const type = String(action?.action || "").toLowerCase();
      if (type === "db_query" || type === "database") {
        return {
          id: `db_query-${nextAutomationCardId++}`,
          action: "db_query",
          database: String(action.database || "default"),
          sql: String(action.sql || ""),
          paramsText: JSON.stringify(action.params ?? {}, null, 2),
          maxRows: Number(action.max_rows) || 50,
        };
      }
      if (type === "send_email") {
        return {
          id: `send_email-${nextAutomationCardId++}`,
          action: "send_email",
          to: Array.isArray(action.to) ? action.to.join(", ") : String(action.to || ""),
          subject: String(action.subject || ""),
          body: String(action.body || ""),
        };
      }
      return {
        id: `call_api-${nextAutomationCardId++}`,
        action: "call_api",
        method: String(action.method || "POST"),
        url: String(action.url || ""),
        hasExpect: Boolean(action.expect) || (Array.isArray(action.expects) && action.expects.length > 0),
        expects: (
          Array.isArray(action.expects)
            ? action.expects
            : action.expect
              ? [action.expect]
              : []
        ).map((exp) => ({
          id: `expect-${nextExpectId++}`,
          path: String(exp?.path || ""),
          equals:
            exp && Object.prototype.hasOwnProperty.call(exp, "equals")
              ? JSON.stringify(exp.equals)
              : "",
        })),
        headersText: JSON.stringify(action.headers ?? {}, null, 2),
        bodyText: JSON.stringify(action.body ?? {}, null, 2),
      };
    });
    syncScriptFromCards();
  } catch (err) {
    automationCards.value = [];
    automationBuilderError.value = "Không parse được script cũ. Hãy tạo lại bằng thẻ.";
    form.value.auto_fix_script = scriptText;
  }
};

const addAutomationCard = (action) => {
  automationCards.value.push(createCard(action));
  syncScriptFromCards();
};

const removeAutomationCard = (cardId) => {
  automationCards.value = automationCards.value.filter((card) => card.id !== cardId);
  syncScriptFromCards();
};

const toggleCardExpect = (card) => {
  card.hasExpect = !card.hasExpect;
  if (!card.hasExpect) {
    card.expects = [];
  } else if (!Array.isArray(card.expects) || card.expects.length === 0) {
    card.expects = [{ id: `expect-${nextExpectId++}`, path: "", equals: "" }];
  }
  syncScriptFromCards();
};

const addExpect = (card) => {
  if (!Array.isArray(card.expects)) card.expects = [];
  card.expects.push({ id: `expect-${nextExpectId++}`, path: "", equals: "" });
  syncScriptFromCards();
};

const removeExpect = (card, expectId) => {
  if (!Array.isArray(card.expects)) return;
  card.expects = card.expects.filter((exp) => exp.id !== expectId);
  if (card.expects.length === 0) {
    card.expects = [{ id: `expect-${nextExpectId++}`, path: "", equals: "" }];
  }
  syncScriptFromCards();
};

const autoResizeSolution = async () => {
  await nextTick();
  const el = solutionTextareaRef.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
};

const onCardDragStart = (index) => {
  draggedCardIndex.value = index;
};

const onCardDrop = (targetIndex) => {
  const sourceIndex = draggedCardIndex.value;
  if (sourceIndex === null || sourceIndex === targetIndex) return;
  const items = [...automationCards.value];
  const [moved] = items.splice(sourceIndex, 1);
  items.splice(targetIndex, 0, moved);
  automationCards.value = items;
  draggedCardIndex.value = null;
  syncScriptFromCards();
};

watch(automationCards, syncScriptFromCards, { deep: true });
watch(automationTimeout, syncScriptFromCards);
watch(showSolutionSection, async (isShown) => {
  if (isShown) await autoResizeSolution();
});
const normalizeStatus = (status, hasSolution = false) => {
  const raw = String(status ?? "").trim().toLowerCase();
  if (raw === "resolved") return "resolved";
  if (raw === "unresolve" || raw === "unresolved" || raw === "open") return "unresolved";
  return hasSolution ? "resolved" : "unresolved";
};
const statusClass = (status) =>
  normalizeStatus(status) === "resolved"
    ? "ops-pill bg-emerald-500/20 text-emerald-100"
    : "ops-pill bg-amber-500/20 text-amber-100";
const formatTime = (value) => {
  if (!value) return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString();
};
const normalizeItem = (item) => ({
  ...item,
  api: item.api ?? item.endpoint ?? "-",
  first_seen: item.first_seen ?? item.firstSeen ?? item.created_at ?? null,
  last_seen: item.last_seen ?? item.lastSeen ?? item.updated_at ?? null,
  status: normalizeStatus(item.status, Boolean(item.solution)),
});
const buildActiveFilters = () => {
  const selected = new Set(selectedFilterKeys.value);
  return Object.fromEntries(
    Object.entries(filters.value).filter(
      ([key, value]) =>
        (selected.has(key) || key === "q") && String(value ?? "").trim(),
    ),
  );
};
const hasAnyFilter = computed(() => Object.keys(buildActiveFilters()).length > 0);
const safeTotalPages = computed(() => Math.max(totalPages.value || 0, 1));
const pageStart = computed(() => {
  if (!totalItems.value) return 0;
  return (currentPage.value - 1) * pageSize.value + 1;
});
const pageEnd = computed(() => {
  if (!totalItems.value) return 0;
  return Math.min(currentPage.value * pageSize.value, totalItems.value);
});
watch(
  selectedFilterKeys,
  (next, prev) => {
    const previousKeys = new Set(prev || []);
    for (const key of next || []) {
      if (!previousKeys.has(key) && Object.prototype.hasOwnProperty.call(filters.value, key)) {
        filters.value[key] = "";
      }
    }
  },
  { deep: false },
);
const fetchSolutions = async (activeFilters = {}, page = currentPage.value) => {
  isLoading.value = true;
  fetchError.value = "";
  try {
    const params = Object.fromEntries(
      Object.entries(activeFilters).filter(([, value]) => String(value ?? "").trim()),
    );
    params.page = page;
    params.page_size = pageSize.value;

    const res = await axios.get(`${API_BASE_URL}/api/dashboard/solutions`, {
      params,
    });
    const payload = res.data;
    const raw = Array.isArray(payload) ? payload : payload?.items || [];
    const apiTotal = Array.isArray(payload) ? raw.length : Number(payload?.total ?? raw.length);
    const apiPage = Array.isArray(payload) ? page : Number(payload?.page ?? page);
    const apiPageSize = Array.isArray(payload) ? pageSize.value : Number(payload?.page_size ?? pageSize.value);
    const apiTotalPages = Array.isArray(payload)
      ? (apiTotal ? Math.ceil(apiTotal / apiPageSize) : 0)
      : Number(payload?.total_pages ?? 0);

    solutions.value = raw.map(normalizeItem);
    totalItems.value = Number.isFinite(apiTotal) ? apiTotal : raw.length;
    currentPage.value = Number.isFinite(apiPage) && apiPage > 0 ? apiPage : 1;
    if (Number.isFinite(apiPageSize) && apiPageSize > 0) {
      pageSize.value = apiPageSize;
    }
    totalPages.value = Number.isFinite(apiTotalPages) ? apiTotalPages : 0;
  } catch (err) {
    solutions.value = [];
    totalItems.value = 0;
    totalPages.value = 0;
    fetchError.value = "Không tải được dữ liệu lỗi. Vui lòng thử lại.";
  } finally {
    isLoading.value = false;
  }
};
const applyFilters = async () => {
  currentPage.value = 1;
  if (!hasAnyFilter.value) {
    await fetchSolutions({}, 1);
    return;
  }
  await fetchSolutions(buildActiveFilters(), 1);
};
const goToPage = async (nextPage) => {
  if (isLoading.value) return;
  const target = Number(nextPage);
  if (!Number.isFinite(target)) return;
  if (target < 1 || target > safeTotalPages.value) return;
  currentPage.value = target;
  await fetchSolutions(hasAnyFilter.value ? buildActiveFilters() : {}, target);
};
const changePageSize = async () => {
  currentPage.value = 1;
  await fetchSolutions(hasAnyFilter.value ? buildActiveFilters() : {}, 1);
};
const toggleAdvancedFilter = () => {
  showAdvancedFilter.value = !showAdvancedFilter.value;
};
const handleDocumentClick = (event) => {
  if (!showAdvancedFilter.value) return;
  const root = advancedFilterRef.value;
  if (!root) return;
  if (!root.contains(event.target)) {
    showAdvancedFilter.value = false;
  }
};
const clearFilters = async () => {
  selectedFilterKeys.value = [];
  currentPage.value = 1;
  filters.value = {
    trace_id: "",
    type: "",
    status: "",
    severity: "",
    service: "",
    api: "",
    label: "",
    q: "",
  };
  await fetchSolutions({}, 1);
};
const openDetail = (item) => {
  const normalized = normalizeItem(item);
  selectedError.value = normalized;
  executeMessage.value = "";
  showMetaSection.value = false;
  showSolutionSection.value = false;
  showScriptSection.value = false;
  form.value = {
    solution: normalized.solution ?? "",
    auto_fix_script: normalized.auto_fix_script ?? "",
  };
  loadAutomationFromScript(form.value.auto_fix_script);
  autoResizeSolution();
};
const closeDetail = () => {
  selectedError.value = null;
  executeMessage.value = "";
  automationBuilderError.value = "";
};
const executeScript = async () => {
  if (!selectedError.value || executing.value || !form.value.auto_fix_script?.trim()) return;
  executing.value = true;
  executeMessage.value = "";
  try {
    await axios.put(`${API_BASE_URL}/api/dashboard/solutions/${selectedError.value.id}`, {
      auto_fix_script: form.value.auto_fix_script,
    });
    const res = await axios.post(
      `${API_BASE_URL}/api/dashboard/solutions/${selectedError.value.id}/execute`,
    );
    const execution = res.data?.execution;
    executeMessage.value = JSON.stringify(execution, null, 2);
  } catch (err) {
    const detail = err?.response?.data?.detail;
    executeMessage.value = typeof detail === "string" ? `Thực thi thất bại: ${detail}` : "Thực thi thất bại.";
  } finally {
    executing.value = false;
  }
};
const saveDetail = async () => {
  if (!selectedError.value || saving.value) return;
  saving.value = true;
  try {
    const payload = {
      solution: form.value.solution,
      auto_fix_script: form.value.auto_fix_script,
    };
    const res = await axios.put(
      `${API_BASE_URL}/api/dashboard/solutions/${selectedError.value.id}`,
      payload,
    );
    const updated = normalizeItem({
      ...selectedError.value,
      solution: res.data.solution,
      auto_fix_script: res.data.auto_fix_script,
      status: res.data.status,
    });
    selectedError.value = updated;
    solutions.value = solutions.value.map((item) =>
      item.id === updated.id ? updated : item,
    );
  } catch (err) {
    alert("Lưu thất bại. Vui lòng thử lại.");
  } finally {
    saving.value = false;
  }
};
onMounted(async () => {
  document.addEventListener("click", handleDocumentClick);
  await fetchSolutions();
});
onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
});
</script>
<style scoped>
.advanced-filter-enter-active,
.advanced-filter-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
  transform-origin: top right;
}

.advanced-filter-enter-from,
.advanced-filter-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}
</style>
