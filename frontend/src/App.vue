<template>
  <div style="font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 16px;">
    <h1>AcaLite MVP</h1>
    <nav style="display:flex; gap:12px; margin-bottom: 16px;">
      <RouterLink to="/">文献导入</RouterLink>
      <RouterLink to="/search">检索</RouterLink>
      <RouterLink to="/settings">设置</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>
