<template>
  <AdminLayout>
    <div class="ops-panel p-5 mb-6">
      <h1 class="ops-title">Tổng quan AIOps</h1>
      <p class="ops-subtitle">
        Theo dõi sức khỏe hệ thống, xu hướng lỗi và mức độ tự động hóa vận hành.
      </p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <Kpi
        title="Tổng lỗi"
        :value="stats.total_errors"
        color="blue"
        icon="TE"
      />
      <Kpi
        title="System"
        :value="stats.by_type?.SYSTEM"
        color="red"
        icon="SY"
      />
      <Kpi
        title="Business"
        :value="stats.by_type?.BUSINESS"
        color="amber"
        icon="BU"
      />
      <Kpi
        title="Chưa phân loại"
        :value="stats.by_type?.UNKNOWN"
        color="gray"
        icon="UN"
      />
    </div>
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <div class="ops-panel p-5 xl:col-span-2">
        <h2 class="text-lg font-semibold mb-4">Top lỗi</h2>
        <table class="ops-table">
          <thead>
            <tr>
              <th class="text-left">Thông điệp lỗi</th>
              <th class="text-center">Số lượng</th>
              <th class="text-center">Loại</th>
              <th class="text-center">Độ tin cậy</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in stats.top_errors" :key="e.message">
              <td>{{ e.message }}</td>
              <td class="text-center font-semibold">{{ e.count }}</td>
              <td class="text-center">
                <span :class="badge(e.type)">{{ e.type }}</span>
              </td>
              <td class="text-center">
                {{ (e.confidence * 100).toFixed(0) }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="ops-panel p-5">
        <h2 class="text-lg font-semibold mb-4">Chỉ số hệ thống</h2>
        <div class="space-y-4">
          <div class="row">
            <span>Độ ổn định</span><strong class="text-emerald-300">Tốt</strong>
          </div>
          <div class="row">
            <span>Tần suất sự cố</span
            ><strong class="text-amber-300">Trung bình</strong>
          </div>
          <div class="row">
            <span>Tự động hóa</span
            ><strong class="text-cyan-300">Đang tăng</strong>
          </div>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>
<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import AdminLayout from "../layouts/AdminLayout.vue";
import Kpi from "../components/KpiCard.vue";
const stats = ref({});
const badge = (type) =>
  ({
    SYSTEM: "ops-pill bg-red-500/20 text-red-100",
    BUSINESS: "ops-pill bg-amber-500/20 text-amber-100",
    VALIDATION: "ops-pill bg-blue-500/20 text-blue-100",
    UNKNOWN: "ops-pill bg-slate-500/20 text-slate-100",
  })[type] || "ops-pill bg-slate-500/20 text-slate-100";
onMounted(async () => {
  const res = await axios.get("http://localhost:8000/api/dashboard/overview");
  stats.value = res.data;
});
</script>
<style scoped>
.row {
  display: flex;
  justify-content: space-between;
  color: #c6d7f5;
  padding: 10px 12px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.32);
}
</style>
