<template>
  <div class="min-h-screen flex">
    <aside class="sidebar w-72 flex flex-col">
      <div class="px-6 py-6 border-b border-slate-800/80">
        <div class="brand-chip">
          <span class="dot"></span>
          <span>AIOps Command</span>
        </div>
        <p class="brand-sub">Giám sát hệ thống điều phối sự cố thông minh</p>
      </div>

      <nav class="flex-1 p-4 space-y-2">
        <RouterLink to="/dashboard" class="nav-link"
          ><span>[OV]</span><span>Tổng quan</span></RouterLink
        >
        <RouterLink to="/incidents" class="nav-link"
          ><span>[IN]</span><span>Sự cố</span></RouterLink
        >
        <RouterLink to="/errors" class="nav-link"
          ><span>[KB]</span><span>Giải pháp</span></RouterLink
        >
      </nav>

      <div
        class="px-5 py-4 border-t border-slate-800/80 text-xs text-slate-400"
      >
        v1.0 - Không gian vận hành AIOps
      </div>
    </aside>
    <main class="flex-1 p-5 md:p-7 overflow-x-hidden">
      <div class="page-enter"><slot /></div>
    </main>
  </div>
</template>

<style scoped>
.sidebar {
  background:
    linear-gradient(165deg, rgba(3, 7, 18, 0.92), rgba(10, 18, 32, 0.92)),
    radial-gradient(
      500px 220px at 20% -10%,
      rgba(56, 189, 248, 0.24),
      transparent 60%
    );
  border-right: 1px solid rgba(125, 211, 252, 0.16);
  backdrop-filter: blur(10px);
}
.brand-chip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(14, 116, 144, 0.25);
  border: 1px solid rgba(34, 211, 238, 0.35);
  color: #dff8ff;
  font-weight: 600;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22d3ee;
  box-shadow: 0 0 12px #22d3ee;
}
.brand-sub {
  margin: 10px 2px 0;
  color: #93accf;
  font-size: 0.82rem;
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  color: #c6d7f4;
  text-decoration: none;
  transition: 0.18s ease;
  border: 1px solid transparent;
}
.nav-link:hover {
  background: rgba(15, 23, 42, 0.8);
  border-color: rgba(125, 211, 252, 0.2);
}
.router-link-active.nav-link {
  background: linear-gradient(
    90deg,
    rgba(14, 116, 144, 0.34),
    rgba(59, 130, 246, 0.25)
  );
  border-color: rgba(56, 189, 248, 0.45);
  color: #e9f3ff;
}
</style>
