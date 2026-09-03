/* Progressive Web App registration and explicit, authenticated push opt-in. */
(() => {
  let deferredInstallPrompt = null;
  let registration = null;
  const PUSH_ENDPOINT = "/api/push";

  const token = () => localStorage.getItem("access_token");
  const authFetch = (url, options = {}) => fetch(url, {
    ...options,
    headers: { Authorization: `Bearer ${token()}`, ...(options.headers || {}) },
  });
  const bytes = (base64) => {
    const padded = `${base64}${"=".repeat((4 - (base64.length % 4)) % 4)}`.replace(/-/g, "+").replace(/_/g, "/");
    const raw = atob(padded);
    return Uint8Array.from(raw, (character) => character.charCodeAt(0));
  };

  async function currentSubscription() {
    return registration?.pushManager.getSubscription();
  }

  async function saveSubscription(subscription) {
    const json = subscription.toJSON();
    const response = await authFetch(`${PUSH_ENDPOINT}/subscriptions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(json) });
    if (!response.ok) throw new Error("BloodLink could not save this device for notifications.");
  }

  async function enableNotifications() {
    if (!registration || !token()) throw new Error("Please sign in before enabling notifications.");
    if (!("PushManager" in window) || !("Notification" in window)) throw new Error("This browser does not support web push notifications.");
    const config = await authFetch(`${PUSH_ENDPOINT}/vapid-public-key`).then((response) => response.json());
    if (!config.configured || !config.public_key) throw new Error("Notifications are not configured by the BloodLink administrator yet.");
    const permission = await Notification.requestPermission();
    if (permission !== "granted") throw new Error("Notification permission was not granted. You can enable it later in browser settings.");
    const subscription = await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: bytes(config.public_key) });
    await saveSubscription(subscription);
    return subscription;
  }

  async function disableNotifications() {
    const subscription = await currentSubscription();
    if (!subscription || !token()) return;
    const response = await authFetch(`${PUSH_ENDPOINT}/subscriptions`, { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify(subscription.toJSON()) });
    if (!response.ok && response.status !== 401) throw new Error("BloodLink could not disable notifications.");
    await subscription.unsubscribe();
  }

  function installControl() {
    const control = document.querySelector("#pwaInstall");
    if (!control) return;
    if (deferredInstallPrompt) { control.hidden = false; control.textContent = "Install BloodLink"; }
    control.addEventListener("click", async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
      control.hidden = true;
    });
  }

  async function notificationControl() {
    const button = document.querySelector("#notificationToggle");
    const status = document.querySelector("#notificationStatus");
    if (!button || !status || !registration || !token()) return;
    const unsupported = !("PushManager" in window) || !("Notification" in window);
    const subscription = unsupported ? null : await currentSubscription();
    if (unsupported) { status.textContent = "Push notifications are not supported by this browser."; button.hidden = true; return; }
    if (Notification.permission === "denied") { status.textContent = "Notifications are blocked in browser settings."; button.hidden = true; return; }
    if (subscription) { status.textContent = "Notifications are enabled on this device."; button.textContent = "Disable notifications"; button.title = status.textContent; }
    else { status.textContent = "Receive compatible blood-request alerts even when this app is closed."; button.textContent = "Enable notifications"; button.title = status.textContent; }
    button.hidden = false;
    button.onclick = async () => {
      button.disabled = true;
      try {
        if (await currentSubscription()) await disableNotifications(); else await enableNotifications();
      } catch (error) { status.textContent = error.message || "Unable to update notification settings."; button.title = status.textContent; }
      finally { button.disabled = false; await notificationControl(); }
    };
  }

  function offlineNotice() {
    const notice = document.createElement("p");
    notice.id = "pwaOfflineNotice";
    notice.setAttribute("role", "alert");
    notice.textContent = "You are offline. Live blood-request and donor information may not be current.";
    document.body.prepend(notice);
    const update = () => { notice.hidden = navigator.onLine; };
    addEventListener("online", update); addEventListener("offline", update); update();
  }

  async function initialise() {
    offlineNotice();
    if (!("serviceWorker" in navigator)) return;
    registration = await navigator.serviceWorker.register("/sw.js", { scope: "/", updateViaCache: "none" });
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (!sessionStorage.getItem("bloodlink-sw-reloaded")) { sessionStorage.setItem("bloodlink-sw-reloaded", "1"); location.reload(); }
    });
    registration.update();
    setInterval(() => registration?.update(), 60 * 60 * 1000);
    installControl();
    await notificationControl();
  }

  addEventListener("beforeinstallprompt", (event) => { event.preventDefault(); deferredInstallPrompt = event; installControl(); });
  document.addEventListener("DOMContentLoaded", () => initialise().catch((error) => console.warn("PWA setup failed", error)));
})();
