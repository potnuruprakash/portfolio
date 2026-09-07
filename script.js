/* ═══════════════════════════════════════════════════════════════
   POTNURU PRAKASH PORTFOLIO — script.js
   ═══════════════════════════════════════════════════════════════ */

"use strict";

/* ──────────────────────────────────────────────────────────────
   1. LOADING SCREEN & INTRO VIDEO CONTROLLER
   - Stage 1: Initializing loading screen ("PP" pulsating logo, progress bar, cycling messages)
   - Stage 2: Intro video playback (fullscreen, cinematic vignette, skip button)
   - Strict viewport scroll lock throughout both stages
   - Zero content leak from the portfolio underneath
   - Seamless transition when video ends or skip is clicked
────────────────────────────────────────────────────────────── */
(function initIntroFlow() {
  const loader     = document.getElementById("loading-screen");
  const loaderText = loader ? loader.querySelector(".loader-text") : null;
  const overlay    = document.getElementById("intro-overlay") || document.getElementById("video-overlay");
  const video      = document.getElementById("intro-video");
  const skip       = document.getElementById("video-skip");
  const portfolio  = document.getElementById("portfolio");

  let isIntroActive = true;
  let introFinished = false;

  // ── Immediate screen & scroll lock
  document.documentElement.classList.add("intro-active");
  document.body.classList.add("intro-active");
  window.scrollTo(0, 0);

  // ── Prevent all scrolling vectors while intro is active
  function preventScroll(e) {
    if (isIntroActive) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  }

  // ── Prevent keyboard navigation & scrolling during intro
  function preventScrollKeys(e) {
    if (!isIntroActive) return;
    const blockedKeys = [
      "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
      "PageUp", "PageDown", "Home", "End", " ", "Spacebar"
    ];
    if (blockedKeys.includes(e.key) || blockedKeys.includes(e.code)) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  }

  window.addEventListener("wheel", preventScroll, { passive: false });
  window.addEventListener("touchmove", preventScroll, { passive: false });
  window.addEventListener("keydown", preventScrollKeys, { passive: false });

  // ── Stage 1: Cycling loading screen messages
  const loaderMessages = [
    "Initializing...",
    "Loading assets...",
    "Compiling portfolio...",
    "Almost ready..."
  ];
  let msgIdx = 0;
  let msgInterval = null;

  if (loaderText) {
    msgInterval = setInterval(() => {
      msgIdx = (msgIdx + 1) % loaderMessages.length;
      loaderText.textContent = loaderMessages[msgIdx];
    }, 450);
  }

  // ── Stage 2: Start Video after loader finishes
  let videoStarted = false;
  function startVideo() {
    if (videoStarted || introFinished) return;
    videoStarted = true;

    if (msgInterval) {
      clearInterval(msgInterval);
      msgInterval = null;
    }

    // Fade out loading screen
    if (loader) {
      loader.classList.add("fade-out");
      setTimeout(() => {
        loader.classList.add("hidden");
        loader.style.display = "none";
      }, 600);
    }

    // Start video playback
    if (video) {
      video.currentTime = 0;
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.catch((err) => {
          console.warn("Autoplay policy or playback error:", err);
          // If video cannot autoplay, wait briefly then transition
          setTimeout(finishIntro, 1200);
        });
      }
    } else {
      finishIntro();
    }
  }

  // Run loader for ~1.9 seconds matching the CSS loader-progress bar
  const loaderTimer = setTimeout(() => {
    startVideo();
  }, 1900);

  // ── Finish intro transition
  function finishIntro() {
    if (introFinished) return;
    introFinished = true;
    isIntroActive = false;

    clearTimeout(loaderTimer);
    if (msgInterval) {
      clearInterval(msgInterval);
      msgInterval = null;
    }

    // Hide loader immediately if still showing
    if (loader) {
      loader.classList.add("fade-out", "hidden");
      loader.style.display = "none";
    }

    // Pause video
    if (video) {
      try { video.pause(); } catch (_) {}
    }

    // Remove scroll prevention listeners
    window.removeEventListener("wheel", preventScroll);
    window.removeEventListener("touchmove", preventScroll);
    window.removeEventListener("keydown", preventScrollKeys);

    // Reveal portfolio smoothly
    if (portfolio) {
      portfolio.style.visibility = "visible";
      portfolio.style.opacity = "1";
      portfolio.removeAttribute("aria-hidden");
    }

    // Start overlay fade-out
    if (overlay) {
      overlay.classList.add("fade-out");
    }

    // Unlock page scrolling
    document.documentElement.classList.remove("intro-active");
    document.body.classList.remove("intro-active");
    document.body.style.overflow = "";

    // Remove overlay from accessibility & DOM display after cinematic fade
    setTimeout(() => {
      if (overlay) {
        overlay.classList.add("hidden");
        overlay.style.display = "none";
      }
      if (typeof initCounters === "function") {
        initCounters();
      }
    }, 1200);
  }

  // ── Video Events
  if (video) {
    video.addEventListener("ended", finishIntro);
    video.addEventListener("error", () => {
      console.warn("Intro video error — transitioning to portfolio");
      setTimeout(finishIntro, 500);
    });
  }

  // ── Skip button
  if (skip) {
    skip.addEventListener("click", finishIntro);
  }

  // ── Safety timeout in case of unexpected video hang
  setTimeout(finishIntro, 25000);
})();

/* ──────────────────────────────────────────────────────────────
   2. CUSTOM CURSOR
────────────────────────────────────────────────────────────── */
(function initCursor() {
  const glow = document.getElementById("cursor-glow");
  const dot = document.getElementById("cursor-dot");
  let mouseX = 0, mouseY = 0;
  let glowX = 0, glowY = 0;

  document.addEventListener("mousemove", (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    dot.style.left = mouseX + "px";
    dot.style.top  = mouseY + "px";
  });

  function animateGlow() {
    glowX += (mouseX - glowX) * 0.08;
    glowY += (mouseY - glowY) * 0.08;
    glow.style.left = glowX + "px";
    glow.style.top  = glowY + "px";
    requestAnimationFrame(animateGlow);
  }
  animateGlow();

  const hoverTargets = "a, button, .skill-chip, .project-card, .cert-card, .achievement-card, .about-card";
  document.addEventListener("mouseover", (e) => {
    if (e.target.closest(hoverTargets)) dot.classList.add("hovering");
  });
  document.addEventListener("mouseout", (e) => {
    if (e.target.closest(hoverTargets)) dot.classList.remove("hovering");
  });
})();

/* ──────────────────────────────────────────────────────────────
   3. PARTICLES CANVAS
────────────────────────────────────────────────────────────── */
(function initParticles() {
  const canvas = document.getElementById("particles-canvas");
  const ctx = canvas.getContext("2d");
  let W, H, particles = [];
  const COUNT = 60;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.r = Math.random() * 1.5 + 0.3;
      this.speedX = (Math.random() - 0.5) * 0.3;
      this.speedY = (Math.random() - 0.5) * 0.3;
      this.opacity = Math.random() * 0.5 + 0.1;
      this.color = Math.random() > 0.5 ? "0, 191, 255" : "0, 229, 255";
    }
    update() {
      this.x += this.speedX;
      this.y += this.speedY;
      if (this.x < -2 || this.x > W + 2 || this.y < -2 || this.y > H + 2) this.reset();
    }
    draw() {
      ctx.save();
      ctx.globalAlpha = this.opacity;
      ctx.fillStyle = `rgba(${this.color}, 1)`;
      ctx.shadowBlur = 6;
      ctx.shadowColor = `rgba(${this.color}, 0.8)`;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }

  for (let i = 0; i < COUNT; i++) particles.push(new Particle());

  // Draw connecting lines between nearby particles
  function drawConnections() {
    const maxDist = 100;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < maxDist) {
          ctx.save();
          ctx.globalAlpha = (1 - dist / maxDist) * 0.08;
          ctx.strokeStyle = "rgba(0, 191, 255, 1)";
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
          ctx.restore();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => { p.update(); p.draw(); });
    drawConnections();
    requestAnimationFrame(animate);
  }
  animate();
})();

// (Intro video controller is consolidated in Section 1 above)

/* ──────────────────────────────────────────────────────────────
   5. NAVBAR SCROLL & ACTIVE LINKS
────────────────────────────────────────────────────────────── */
(function initNavbar() {
  const navbar  = document.getElementById("navbar");
  const links   = document.querySelectorAll(".nav-link");
  const toggle  = document.getElementById("nav-toggle");
  const navMenu = document.getElementById("nav-links");
  const sections = document.querySelectorAll("section[id]");

  window.addEventListener("scroll", () => {
    // Scrolled class
    if (window.scrollY > 50) navbar.classList.add("scrolled");
    else navbar.classList.remove("scrolled");

    // Active section
    let current = "";
    sections.forEach(sec => {
      const sTop = sec.offsetTop - 100;
      if (window.scrollY >= sTop) current = sec.id;
    });
    links.forEach(link => {
      link.classList.remove("active");
      if (link.dataset.section === current) link.classList.add("active");
    });

    // Back to top button
    const btt = document.getElementById("back-to-top");
    if (btt) {
      btt.style.opacity = window.scrollY > 400 ? "1" : "0";
      btt.style.pointerEvents = window.scrollY > 400 ? "auto" : "none";
    }
  });

  // Mobile toggle
  toggle.addEventListener("click", () => {
    const isOpen = toggle.classList.toggle("open");
    navMenu.classList.toggle("open");
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  // Close mobile menu on link click
  links.forEach(link => {
    link.addEventListener("click", () => {
      toggle.classList.remove("open");
      navMenu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });

  // Close mobile menu when clicking outside
  document.addEventListener("click", (e) => {
    if (navMenu.classList.contains("open") && !navbar.contains(e.target)) {
      toggle.classList.remove("open");
      navMenu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });

  // Close mobile menu on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && navMenu.classList.contains("open")) {
      toggle.classList.remove("open");
      navMenu.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });

  // Back to top
  const btt = document.getElementById("back-to-top");
  if (btt) {
    btt.style.opacity = "0";
    btt.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  }
})();

/* ──────────────────────────────────────────────────────────────
   6. TYPING ANIMATION
────────────────────────────────────────────────────────────── */
(function initTyping() {
  const el = document.getElementById("typing-text");
  if (!el) return;

  const words = [
    "Cybersecurity Enthusiast",
    "AI Developer",
    "Software Developer",
    "IoT Engineer",
    "Problem Solver",
  ];
  let wordIdx = 0, charIdx = 0, deleting = false;

  function type() {
    const currentWord = words[wordIdx];
    if (!deleting) {
      el.textContent = currentWord.slice(0, ++charIdx);
      if (charIdx === currentWord.length) {
        deleting = true;
        setTimeout(type, 2000);
        return;
      }
    } else {
      el.textContent = currentWord.slice(0, --charIdx);
      if (charIdx === 0) {
        deleting = false;
        wordIdx = (wordIdx + 1) % words.length;
      }
    }
    setTimeout(type, deleting ? 60 : 90);
  }
  type();
})();

/* ──────────────────────────────────────────────────────────────
   7. SCROLL REVEAL ANIMATIONS
────────────────────────────────────────────────────────────── */
(function initReveal() {
  const targets = document.querySelectorAll(".reveal, .reveal-left, .reveal-right");

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, idx) => {
        if (entry.isIntersecting) {
          // Stagger siblings in the same grid parent
          const siblings = [...(entry.target.parentElement?.children || [])].filter(el =>
            el.classList.contains("reveal") || el.classList.contains("reveal-left") || el.classList.contains("reveal-right")
          );
          const delay = siblings.indexOf(entry.target) * 80;
          setTimeout(() => entry.target.classList.add("visible"), delay);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
  );

  targets.forEach(el => observer.observe(el));
})();

/* ──────────────────────────────────────────────────────────────
   8. COUNTER ANIMATION
────────────────────────────────────────────────────────────── */
let countersAnimated = false;
function initCounters() {
  if (countersAnimated) return;
  countersAnimated = true;
  const counters = document.querySelectorAll(".stat-number");

  counters.forEach(counter => {
    const target = parseInt(counter.dataset.target, 10);
    const duration = 1800;
    const stepTime = 30;
    const steps = duration / stepTime;
    let current = 0;

    const timer = setInterval(() => {
      current += target / steps;
      if (current >= target) {
        counter.textContent = target;
        clearInterval(timer);
      } else {
        counter.textContent = Math.floor(current);
      }
    }, stepTime);
  });
}

/* ──────────────────────────────────────────────────────────────
   9. MAGNETIC BUTTONS
────────────────────────────────────────────────────────────── */
(function initMagneticButtons() {
  const buttons = document.querySelectorAll(".magnetic-btn");

  buttons.forEach(btn => {
    btn.addEventListener("mousemove", (e) => {
      const rect = btn.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top  + rect.height / 2;
      const dx = (e.clientX - cx) * 0.25;
      const dy = (e.clientY - cy) * 0.25;
      btn.style.transform = `translate(${dx}px, ${dy}px)`;
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.transform = "translate(0, 0)";
    });
  });
})();

/* ──────────────────────────────────────────────────────────────
   10. CONTACT FORM
────────────────────────────────────────────────────────────── */
(function initContactForm() {
  const form        = document.getElementById("contact-form");
  const success     = document.getElementById("form-success");
  const errorBanner = document.getElementById("form-error-banner");
  const errorText   = document.getElementById("form-error-text");
  if (!form) return;

  function showError(id, msg) {
    const el = document.getElementById(id);
    if (el) el.textContent = msg;
  }
  function clearErrors() {
    ["error-name", "error-email", "error-message"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = "";
    });
    if (errorBanner) errorBanner.classList.remove("show");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors();
    if (success) success.classList.remove("show");

    const name    = form.querySelector("#contact-name").value.trim();
    const email   = form.querySelector("#contact-email").value.trim();
    const subject = form.querySelector("#contact-subject") ? form.querySelector("#contact-subject").value.trim() : "";
    const message = form.querySelector("#contact-message").value.trim();
    let valid = true;

    if (!name) { showError("error-name", "Please enter your name."); valid = false; }
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showError("error-email", "Please enter a valid email."); valid = false;
    }
    if (!message) { showError("error-message", "Please enter a message."); valid = false; }
    if (!valid) return;

    const btn = document.getElementById("submit-btn");
    const originalBtnHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Sending...</span>';
    btn.disabled = true;

    try {
      const response = await fetch("https://formsubmit.co/ajax/prakashpotnuru7278@gmail.com", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({
          name: name,
          email: email,
          _subject: subject ? `Portfolio Inquiry: ${subject}` : `New Portfolio Message from ${name}`,
          message: message,
          _captcha: "false",
          _template: "table"
        })
      });

      const data = await response.json();

      if (response.ok && (data.success === "true" || data.success === true)) {
        form.reset();
        if (success) {
          success.classList.add("show");
          setTimeout(() => success.classList.remove("show"), 6000);
        }
      } else {
        throw new Error(data.message || "Failed to deliver message. Please try again.");
      }
    } catch (err) {
      console.error("Form submission error:", err);
      if (errorBanner) {
        if (errorText) {
          errorText.textContent = err.message || "Something went wrong. Please try emailing directly at prakashpotnuru7278@gmail.com";
        }
        errorBanner.classList.add("show");
        setTimeout(() => errorBanner.classList.remove("show"), 7000);
      }
    } finally {
      btn.innerHTML = originalBtnHtml;
      btn.disabled = false;
    }
  });
})();

/* ──────────────────────────────────────────────────────────────
   11. FOOTER YEAR
────────────────────────────────────────────────────────────── */
(function setYear() {
  const el = document.getElementById("current-year");
  if (el) el.textContent = new Date().getFullYear();
})();

/* ──────────────────────────────────────────────────────────────
   12. SMOOTH SECTION TRANSITIONS (FADE ON SCROLL)
────────────────────────────────────────────────────────────── */
(function initSectionFade() {
  const sections = document.querySelectorAll(".section");

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "none";
      }
    });
  }, { threshold: 0.05 });

  sections.forEach(sec => {
    observer.observe(sec);
  });
})();

/* ──────────────────────────────────────────────────────────────
   13. SKILL CHIP HOVER GLOW RIPPLE
────────────────────────────────────────────────────────────── */
(function initSkillChips() {
  document.querySelectorAll(".skill-chip").forEach(chip => {
    chip.addEventListener("click", function(e) {
      const ripple = document.createElement("span");
      ripple.style.cssText = `
        position: absolute; border-radius: 50%;
        background: rgba(0,191,255,0.3);
        width: 10px; height: 10px;
        left: ${e.offsetX - 5}px; top: ${e.offsetY - 5}px;
        animation: ripple-out 0.6s linear forwards;
        pointer-events: none;
      `;
      this.style.position = "relative";
      this.style.overflow = "hidden";
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 700);
    });
  });

  // Add ripple keyframe
  const style = document.createElement("style");
  style.textContent = `
    @keyframes ripple-out {
      to { transform: scale(20); opacity: 0; }
    }
  `;
  document.head.appendChild(style);
})();

/* ──────────────────────────────────────────────────────────────
   14. SCROLL-INDICATOR HIDE ON SCROLL
────────────────────────────────────────────────────────────── */
(function initScrollIndicator() {
  const indicator = document.getElementById("scroll-indicator");
  if (!indicator) return;
  window.addEventListener("scroll", () => {
    indicator.style.opacity = window.scrollY > 80 ? "0" : "1";
  });
})();

/* ──────────────────────────────────────────────────────────────
   15. NAVBAR LOGO — scroll to top
────────────────────────────────────────────────────────────── */
document.getElementById("nav-logo-link")?.addEventListener("click", (e) => {
  e.preventDefault();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

/* ──────────────────────────────────────────────────────────────
   16. PROJECT CARD — TILT EFFECT (desktop only)
────────────────────────────────────────────────────────────── */
(function initTilt() {
  if (window.innerWidth < 768) return;

  document.querySelectorAll(".project-card, .cert-card, .achievement-card").forEach(card => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top)  / rect.height - 0.5;
      card.style.transform = `perspective(600px) rotateX(${-y * 6}deg) rotateY(${x * 6}deg) translateY(-4px)`;
    });
    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });
  });
})();
