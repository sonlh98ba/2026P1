<template>
  <div class="kpi ops-panel">
    <div class="kpi-icon" :class="iconBg">{{ icon }}</div>
    <div>
      <div class="kpi-title">{{ title }}</div>
      <div class="kpi-value">{{ value ?? 0 }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: String,
  value: [String, Number],
  icon: String,
  color: {
    type: String,
    default: "blue",
  },
});

const iconBg =
  {
    red: "bg-red-500/20 text-red-200 border-red-300/30",
    amber: "bg-amber-500/20 text-amber-200 border-amber-300/30",
    blue: "bg-sky-500/20 text-sky-200 border-sky-300/30",
    gray: "bg-slate-500/20 text-slate-200 border-slate-300/30",
    green: "bg-emerald-500/20 text-emerald-200 border-emerald-300/30",
  }[props.color] || "bg-sky-500/20 text-sky-200 border-sky-300/30";
</script>

<style scoped>
.kpi {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
}

.kpi-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border-width: 1px;
  display: grid;
  place-items: center;
  font-size: 1.25rem;
}

.kpi-title {
  color: #a7b8d9;
  font-size: 0.82rem;
}

.kpi-value {
  font-size: 1.45rem;
  font-weight: 700;
  line-height: 1.1;
}
</style>
