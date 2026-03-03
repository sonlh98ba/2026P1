<template>
  <AdminLayout>
    <div class="ops-panel p-5 mb-6">
      <h1 class="ops-title">Sự cố đang hoạt động</h1>
      <p class="ops-subtitle">
        Theo dõi số lượng sự cố và phạm vi ảnh hưởng dịch vụ theo thời gian
        thực.
      </p>
    </div>
    <div class="ops-panel p-4">
      <p v-if="isLoading" class="mb-3 text-sm text-slate-300">Đang tải dữ liệu sự cố...</p>
      <p v-if="fetchError" class="mb-3 text-sm text-rose-300">{{ fetchError }}</p>
      <table class="ops-table">
        <thead>
          <tr>
            <th class="text-left">Thời gian</th>
            <th class="text-left">Lỗi</th>
            <th class="text-center">Loại</th>
            <th class="text-center">Trạng thái</th>
            <th class="text-center">Số lần</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in incidents" :key="i.id">
            <td>{{ formatTime(i.created_at) }}</td>
            <td>{{ i.message }}</td>
            <td class="text-center">
              <span :class="['ops-pill', kindClass(i.error_type)]">{{
                i.error_type || "UNKNOWN"
              }}</span>
            </td>
            <td class="text-center">
              <span :class="['ops-pill', statusClass(i.status)]">{{
                i.status || "OPEN"
              }}</span>
            </td>
            <td class="text-center font-semibold">{{ i.count }}</td>
          </tr>
          <tr v-if="!incidents.length">
            <td class="py-4 text-center text-slate-400" colspan="5">Không có sự cố.</td>
          </tr>
        </tbody>
      </table>
      <div class="mt-4 flex flex-col gap-3 text-sm text-slate-300 md:flex-row md:items-center md:justify-between">
        <p>Hiển thị {{ pageStart }}-{{ pageEnd }} / {{ totalItems }} kết quả</p>
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
            <option v-for="size in pageSizeOptions" :key="`incident-page-size-${size}`" :value="size">
              {{ size }}
            </option>
          </select>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>
<script setup>
import { computed, ref, onMounted } from "vue";
import axios from "axios";
import AdminLayout from "../layouts/AdminLayout.vue";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";
const incidents = ref([]);
const isLoading = ref(false);
const fetchError = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);
const totalPages = ref(0);
const pageSizeOptions = [10, 20, 50, 100];

const safeTotalPages = computed(() => Math.max(totalPages.value || 0, 1));
const pageStart = computed(() => {
  if (!totalItems.value) return 0;
  return (currentPage.value - 1) * pageSize.value + 1;
});
const pageEnd = computed(() => {
  if (!totalItems.value) return 0;
  return Math.min(currentPage.value * pageSize.value, totalItems.value);
});

const loadIncidents = async () => {
  isLoading.value = true;
  fetchError.value = "";
  try {
    const res = await axios.get(`${API_BASE_URL}/api/dashboard/incidents`, {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
      },
    });
    const payload = res.data;
    const items = Array.isArray(payload) ? payload : payload?.items || [];
    incidents.value = items;
    totalItems.value = Array.isArray(payload) ? items.length : Number(payload?.total ?? items.length);
    totalPages.value = Array.isArray(payload)
      ? (totalItems.value ? Math.ceil(totalItems.value / pageSize.value) : 0)
      : Number(payload?.total_pages ?? 0);
    currentPage.value = Array.isArray(payload) ? currentPage.value : Number(payload?.page ?? currentPage.value);
  } catch (err) {
    incidents.value = [];
    totalItems.value = 0;
    totalPages.value = 0;
    fetchError.value = "Không tải được dữ liệu sự cố. Vui lòng thử lại.";
  } finally {
    isLoading.value = false;
  }
};

const goToPage = async (nextPage) => {
  if (isLoading.value) return;
  const target = Number(nextPage);
  if (!Number.isFinite(target)) return;
  if (target < 1 || target > safeTotalPages.value) return;
  currentPage.value = target;
  await loadIncidents();
};

const changePageSize = async () => {
  currentPage.value = 1;
  await loadIncidents();
};

onMounted(loadIncidents);
const formatTime = (t) => new Date(t).toLocaleString();
const kindClass = (type) =>
  ({
    SYSTEM: "bg-red-500/20 text-red-100",
    BUSINESS: "bg-emerald-500/20 text-emerald-100",
    VALIDATION: "bg-amber-500/20 text-amber-100",
    UNKNOWN: "bg-slate-500/20 text-slate-100",
  })[type] || "bg-slate-500/20 text-slate-100";
const statusClass = (status) =>
  status === "OPEN"
    ? "bg-cyan-500/20 text-cyan-100"
    : "bg-emerald-500/20 text-emerald-100";
</script>
