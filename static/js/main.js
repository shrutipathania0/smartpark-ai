/**
 * SmartPark AI - Shared Client-Side Utility Library
 */

// Format ISO date/time string to human-readable format
function formatDateTime(isoStr) {
  if (!isoStr) return "--";
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch (e) {
    return isoStr;
  }
}

// Global Toast / Notice Helper
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `badge badge-${type === "error" ? "low" : (type === "success" ? "vacant" : "reserved")}`;
  toast.style.position = "fixed";
  toast.style.bottom = "24px";
  toast.style.right = "24px";
  toast.style.padding = "12px 20px";
  toast.style.fontSize = "0.95rem";
  toast.style.zIndex = "9999";
  toast.style.boxShadow = "0 8px 24px rgba(0,0,0,0.5)";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

