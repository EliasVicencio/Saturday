import { useCallback, useEffect, useState } from "react";
import { getVapidPublicKey, subscribePush, unsubscribePush } from "../services/api";

/** Convierte la clave VAPID (base64url) al formato Uint8Array que pide pushManager.subscribe */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export type PushStatus = "unsupported" | "disabled-backend" | "denied" | "unsubscribed" | "subscribed" | "loading";

export function usePushNotifications() {
  const [status, setStatus] = useState<PushStatus>("loading");

  const refreshStatus = useCallback(async () => {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setStatus("unsupported");
      return;
    }
    if (Notification.permission === "denied") {
      setStatus("denied");
      return;
    }
    try {
      const { enabled } = await getVapidPublicKey();
      if (!enabled) {
        setStatus("disabled-backend");
        return;
      }
      const registration = await navigator.serviceWorker.ready;
      const existing = await registration.pushManager.getSubscription();
      setStatus(existing ? "subscribed" : "unsubscribed");
    } catch {
      setStatus("disabled-backend");
    }
  }, []);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  const subscribe = useCallback(async () => {
    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setStatus("denied");
        return;
      }

      const { enabled, publicKey } = await getVapidPublicKey();
      if (!enabled || !publicKey) {
        setStatus("disabled-backend");
        return;
      }

      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey) as BufferSource,
      });

      await subscribePush(subscription.toJSON() as PushSubscriptionJSON);
      setStatus("subscribed");
    } catch (err) {
      console.warn("No se pudo suscribir a push:", err);
      setStatus("unsubscribed");
    }
  }, []);

  const unsubscribe = useCallback(async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await unsubscribePush(subscription.endpoint);
        await subscription.unsubscribe();
      }
      setStatus("unsubscribed");
    } catch (err) {
      console.warn("No se pudo desuscribir de push:", err);
    }
  }, []);

  const toggle = useCallback(() => {
    if (status === "subscribed") unsubscribe();
    else if (status === "unsubscribed") subscribe();
  }, [status, subscribe, unsubscribe]);

  return { status, subscribe, unsubscribe, toggle };
}