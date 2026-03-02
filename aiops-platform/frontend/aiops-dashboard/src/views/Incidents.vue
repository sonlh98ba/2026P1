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
        </tbody>
      </table>
    </div>
  </AdminLayout>
</template>
<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import AdminLayout from "../layouts/AdminLayout.vue";
const incidents = ref([]);
const loadIncidents = async () => {
  const res = await axios.get("http://localhost:8000/api/dashboard/incidents");
  incidents.value = res.data;
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
