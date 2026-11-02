/**
 * SmartPark AI - Shared Client-Side Utility & Interaction Library
 */

// Toast Notification Manager
function showToast(message, type = "info") {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  let icon = "ℹ️";
  if (type === "success") icon = "✅";
  else if (type === "warning") icon = "⚠️";
  else if (type === "error") icon = "❌";

  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    setTimeout(() => toast.remove(), 350);
  }, 4200);
}

// Modal Helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("active");
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("active");
  }
}

// Format ISO string to localized time
function formatDateTime(isoStr) {
  if (!isoStr) return "--";
  try {
    const d = new Date(isoStr);
    return d.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (e) {
    return isoStr;
  }
}

// Format seconds into minutes/hours
function formatDuration(seconds) {
  if (isNaN(seconds) || seconds <= 0) return "0m";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

// Auto-check system health for navbar indicator
async function checkGlobalSystemHealth() {
  try {
    const res = await fetch("/api/system/health");
    const data = await res.json();
    if (data.success) {
      const textEl = document.getElementById("systemStatusText");
      if (textEl) {
        textEl.textContent = "AI Facility Online";
      }
    }
  } catch (e) {
    const textEl = document.getElementById("systemStatusText");
    if (textEl) {
      textEl.textContent = "Facility Standby";
    }
  }
}

// 5. Lightweight Parallax Scroll Effect for Background
function initParallaxScroll() {
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (window.innerWidth < 768) return; // Disable on small mobile devices

  let ticking = false;
  window.addEventListener("scroll", function() {
    if (!ticking) {
      window.requestAnimationFrame(function() {
        const scrolled = window.pageYOffset || document.documentElement.scrollTop;
        document.body.style.backgroundPositionY = "calc(0px + " + (scrolled * 0.22) + "px)";
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}

document.addEventListener("DOMContentLoaded", () => {
  checkGlobalSystemHealth();
  initParallaxScroll();
  // Close modals on escape key or clicking backdrop
  document.querySelectorAll(".modal-overlay").forEach(modal => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("active");
      }
    });
  });
});
