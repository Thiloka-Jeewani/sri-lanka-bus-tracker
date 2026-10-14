import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import L, { type Map as LeafletMap, type Marker } from "leaflet";
import "leaflet/dist/leaflet.css";
import "../../styles.css";

type Role = "passenger" | "driver" | "operator" | "authority" | "admin";
type AccountStatus = "pending" | "active" | "rejected" | "suspended";
type User = {
  id: string;
  email: string;
  name: string;
  role: Role;
  status: AccountStatus;
  organization: string | null;
  createdAt: string;
};
type Stop = { name: string; lat: number; lon: number };
type Route = { id: string; name: string; nameSi: string; nameTa: string; demo: boolean; stops: Stop[] };
type Vehicle = {
  vehicleId: string;
  routeId: string;
  lat: number;
  lon: number;
  accuracy: number | null;
  ageSeconds: number;
  status: "live" | "stale";
  demo: boolean;
};
type FleetVehicle = {
  vehicleId: string;
  routeId: string;
  createdAt: string;
  driverId: string | null;
  driverName: string | null;
  driverEmail: string | null;
  organization?: string | null;
  operatorName?: string;
  operatorEmail?: string;
  operatorStatus?: AccountStatus;
};
type Language = "en" | "si" | "ta";
type TranslationKey =
  | "community" | "headline" | "intro" | "routes" | "live" | "sharing"
  | "empty" | "driverTitle" | "driverSubtitle" | "vehicle" | "route"
  | "privacy" | "start" | "stop" | "mapTitle" | "mapSubtitle"
  | "legendLive" | "legendStale" | "accounts" | "signIn" | "email" | "password"
  | "createAccount" | "name" | "accountType" | "organization" | "register"
  | "consent" | "signOut" | "pending" | "adminSetup" | "adminPassword"
  | "createAdmin" | "driverReady" | "assigned" | "addVehicle" | "assignDriver"
  | "passengerInfo" | "authorityInfo" | "operatorInfo" | "adminInfo";

const translations: Record<Language, Record<TranslationKey, string>> = {
  en: {
    community: "COMMUNITY TRANSIT", headline: "Your bus. Not a guess.",
    intro: "See community-shared bus locations and spend less time waiting.",
    routes: "Routes", live: "LIVE", sharing: "buses sharing", empty: "No buses are sharing their location yet. Invite a driver to get started.",
    driverTitle: "I'm driving a bus", driverSubtitle: "Share your location with passengers",
    vehicle: "Bus / vehicle ID", route: "Route", privacy: "Your location is shared only while sharing is turned on. Stop sharing at any time.",
    start: "Start sharing location", stop: "Stop sharing location", mapTitle: "Colombo, Sri Lanka",
    mapSubtitle: "Community bus network", legendLive: "Sharing now", legendStale: "Last seen",
    accounts: "Accounts", signIn: "Sign in", email: "Email", password: "Password",
    createAccount: "Create an account", name: "Full name", accountType: "Account type",
    organization: "Organization / agency", register: "Register",
    consent: "I understand that GPS is collected only while a driver has explicitly started sharing and can be stopped at any time.",
    signOut: "Sign out", pending: "Your account is waiting for admin approval.",
    adminSetup: "Set up the first administrator", adminPassword: "Admin password (16+ characters)",
    createAdmin: "Create admin and open dashboard",
    driverReady: "Ask your operator to register and assign a vehicle to your account before sharing GPS.",
    assigned: "Assigned vehicle", addVehicle: "Register vehicle", assignDriver: "Assign driver by registered email",
    passengerInfo: "Passenger account active. You can browse the public live map.",
    authorityInfo: "Authority view: check published routes and live vehicle status. Route data is illustrative in this pilot.",
    operatorInfo: "Register vehicles for your approved operator account.",
    adminInfo: "Manage approvals, accounts, and registered buses on your dedicated dashboard."
  },
  si: {
    community: "ප්‍රජා ප්‍රවාහනය", headline: "ඔබේ බසය. අනුමානයක් නොවේ.",
    intro: "ප්‍රජාව බෙදාගන්නා බස් රථ ස්ථාන බලන්න. බලා සිටින කාලය අඩු කරගන්න.",
    routes: "මාර්ග", live: "සජීවී", sharing: "බස් ස්ථාන බෙදාගනී", empty: "තවම බස් රථ ස්ථාන බෙදාගෙන නැත.",
    driverTitle: "මම බස් රථයක් පදවනවා", driverSubtitle: "ඔබේ ස්ථානය මගීන් සමඟ බෙදාගන්න",
    vehicle: "බස් / වාහන අංකය", route: "මාර්ගය", privacy: "ස්ථාන බෙදාගැනීම ක්‍රියාත්මක විට පමණක් බෙදාගනී. ඕනෑම විටෙක නවත්වන්න.",
    start: "ස්ථානය බෙදාගන්න", stop: "බෙදාගැනීම නවත්වන්න", mapTitle: "කොළඹ, ශ්‍රී ලංකාව",
    mapSubtitle: "ප්‍රජා බස් ජාලය", legendLive: "දැන් බෙදාගනී", legendStale: "අවසන් වරට",
    accounts: "ගිණුම්", signIn: "පිවිසෙන්න", email: "විද්‍යුත් තැපෑල", password: "මුරපදය",
    createAccount: "ගිණුමක් සාදන්න", name: "සම්පූර්ණ නම", accountType: "ගිණුම් වර්ගය",
    organization: "ආයතනය / ඒජන්සිය", register: "ලියාපදිංචි වන්න",
    consent: "රියදුරෙකු පැහැදිලිව ස්ථාන බෙදාගැනීම ආරම්භ කළ විට පමණක් GPS එකතු කරන බව මම දනිමි.",
    signOut: "ඉවත් වන්න", pending: "ඔබගේ ගිණුම පරිපාලක අනුමැතිය බලාපොරොත්තුවෙන් ඇත.",
    adminSetup: "පළමු පරිපාලක සකසන්න", adminPassword: "පරිපාලක මුරපදය (අක්ෂර 16+)",
    createAdmin: "පරිපාලක සාදා පුවරුව විවෘත කරන්න",
    driverReady: "GPS බෙදාගැනීමට පෙර වාහනයක් ලියාපදිංචි කර ඔබට පවරන ලෙස මෙහෙයුම්කරුගෙන් ඉල්ලන්න.",
    assigned: "පවරා ඇති වාහනය", addVehicle: "වාහනය ලියාපදිංචි කරන්න", assignDriver: "ලියාපදිංචි ඊමේල් අනුව රියදුරු පවරන්න",
    passengerInfo: "මගී ගිණුම සක්‍රියයි.", authorityInfo: "අධිකාරියේ දර්ශනය: ප්‍රකාශිත මාර්ග සහ වාහන තත්ත්වය බලන්න.",
    operatorInfo: "අනුමත මෙහෙයුම්කරු ගිණුම සඳහා වාහන ලියාපදිංචි කරන්න.",
    adminInfo: "පරිපාලක පුවරුවේ අනුමැති, ගිණුම් සහ බස් කළමනාකරණය කරන්න."
  },
  ta: {
    community: "சமூகப் போக்குவரத்து", headline: "உங்கள் பேருந்து. இனி யூகம் இல்லை.",
    intro: "சமூகம் பகிரும் பேருந்து இருப்பிடங்களைப் பார்த்துக் காத்திருக்கும் நேரத்தைக் குறைக்கவும்.",
    routes: "வழித்தடங்கள்", live: "நேரலை", sharing: "பேருந்துகள் பகிர்கின்றன", empty: "இன்னும் எந்தப் பேருந்தும் இருப்பிடத்தைப் பகிரவில்லை.",
    driverTitle: "நான் பேருந்து ஓட்டுநர்", driverSubtitle: "உங்கள் இருப்பிடத்தைப் பயணிகளுடன் பகிரவும்",
    vehicle: "பேருந்து / வாகன எண்", route: "வழித்தடம்", privacy: "பகிர்வு இயக்கத்தில் இருக்கும்போது மட்டுமே இருப்பிடம் பகிரப்படும். எப்போது வேண்டுமானாலும் நிறுத்தலாம்.",
    start: "இருப்பிடத்தைப் பகிரவும்", stop: "பகிர்வதை நிறுத்தவும்", mapTitle: "கொழும்பு, இலங்கை",
    mapSubtitle: "சமூகப் பேருந்து வலைப்பின்னல்", legendLive: "இப்போது பகிர்கிறது", legendStale: "கடைசியாகப் பார்த்தது",
    accounts: "கணக்குகள்", signIn: "உள்நுழைக", email: "மின்னஞ்சல்", password: "கடவுச்சொல்",
    createAccount: "கணக்கை உருவாக்கு", name: "முழுப் பெயர்", accountType: "கணக்கு வகை",
    organization: "அமைப்பு / நிறுவனம்", register: "பதிவு செய்",
    consent: "ஓட்டுநர் பகிர்வைத் தொடங்கியபோது மட்டுமே GPS சேகரிக்கப்படும் என்பதைப் புரிந்துகொள்கிறேன்.",
    signOut: "வெளியேறு", pending: "உங்கள் கணக்கு நிர்வாகி ஒப்புதலுக்காகக் காத்திருக்கிறது.",
    adminSetup: "முதல் நிர்வாகியை அமைக்கவும்", adminPassword: "நிர்வாகி கடவுச்சொல் (16+ எழுத்துகள்)",
    createAdmin: "நிர்வாகியை உருவாக்கி பலகையைத் திற",
    driverReady: "GPS பகிர்வதற்கு முன் வாகனத்தைப் பதிவு செய்து ஒதுக்குமாறு இயக்குநரிடம் கேளுங்கள்.",
    assigned: "ஒதுக்கப்பட்ட வாகனம்", addVehicle: "வாகனத்தைப் பதிவு செய்", assignDriver: "பதிவு செய்த மின்னஞ்சல் மூலம் ஓட்டுநரை ஒதுக்கு",
    passengerInfo: "பயணிகள் கணக்கு செயலில் உள்ளது.", authorityInfo: "அதிகாரப் பார்வை: வெளியிடப்பட்ட வழித்தடங்களையும் வாகன நிலையையும் பார்க்கவும்.",
    operatorInfo: "அங்கீகரிக்கப்பட்ட இயக்குநர் கணக்கில் வாகனங்களைப் பதிவு செய்யவும்.",
    adminInfo: "நிர்வாகப் பலகையில் ஒப்புதல்கள், கணக்குகள், பேருந்துகளை நிர்வகிக்கவும்."
  }
};

let csrfToken: string | null = null;

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (options.method && options.method !== "GET" && csrfToken) headers.set("X-CSRF-Token", csrfToken);
  const response = await fetch(path, { ...options, headers, credentials: "same-origin" });
  const result = await response.json() as { detail?: string | { msg: string }[]; error?: string };
  if (!response.ok) {
    const detail = Array.isArray(result.detail) ? result.detail.map((item) => item.msg).join("; ") : result.detail;
    throw new Error(detail || result.error || `Request failed (${response.status}).`);
  }
  return result as T;
}

function useTranslation(language: Language) {
  return useCallback((key: TranslationKey) => translations[language][key], [language]);
}

function ageLabel(seconds: number) {
  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  return `${Math.floor(seconds / 60)} min ago`;
}

function MapView({ route, vehicles }: { route: Route | null; vehicles: Vehicle[] }) {
  const mapElement = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const routeLayer = useRef<L.LayerGroup | null>(null);
  const markers = useRef<Map<string, Marker>>(new Map());

  useEffect(() => {
    if (!mapElement.current) return;
    const map = L.map(mapElement.current, { zoomControl: false }).setView([6.9365, 79.8464], 15);
    mapRef.current = map;
    L.control.zoom({ position: "bottomright" }).addTo(map);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    const centerMap = () => map.setView([6.9365, 79.8464], 15);
    window.addEventListener("center-map", centerMap);
    return () => {
      window.removeEventListener("center-map", centerMap);
      map.remove();
      mapRef.current = null;
      markers.current.clear();
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    routeLayer.current?.remove();
    if (route) {
      const points = route.stops.map((stop) => L.latLng(stop.lat, stop.lon));
      routeLayer.current = L.layerGroup([
        L.polyline(points, { color: "#148052", weight: 5, opacity: 0.78, dashArray: "9 8" }),
        ...route.stops.map((stop) =>
          L.circleMarker([stop.lat, stop.lon], { radius: 5, color: "#fff", weight: 2, fillColor: "#116a48", fillOpacity: 1 })
            .bindTooltip(stop.name)
        )
      ]).addTo(map);
      map.fitBounds(L.latLngBounds(points).pad(1.25), { maxZoom: 15 });
    }
  }, [route]);

  useEffect(() => {
    const shown = vehicles.filter((vehicle) => vehicle.routeId === route?.id);
    const visible = new Set(shown.map((vehicle) => vehicle.vehicleId));
    for (const [id, marker] of markers.current) {
      if (!visible.has(id)) {
        marker.remove();
        markers.current.delete(id);
      }
    }
    shown.forEach((vehicle) => {
      const icon = L.divIcon({
        className: "",
        html: `<span class="bus-marker${vehicle.status === "stale" ? " stale" : ""}">▣</span>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17]
      });
      const marker = markers.current.get(vehicle.vehicleId);
      if (marker) {
        marker.setLatLng([vehicle.lat, vehicle.lon]).setIcon(icon);
      } else if (mapRef.current) {
        const popup = document.createElement("div");
        const strong = document.createElement("strong");
        strong.textContent = vehicle.vehicleId;
        const age = document.createElement("div");
        age.textContent = ageLabel(vehicle.ageSeconds);
        const demo = document.createElement("small");
        demo.textContent = "Demo route · real data not verified";
        popup.append(strong, age, demo);
        markers.current.set(
          vehicle.vehicleId,
          L.marker([vehicle.lat, vehicle.lon], { icon }).bindPopup(popup).addTo(mapRef.current)
        );
      }
    });
  }, [route, vehicles]);

  return <div id="map" ref={mapElement} role="application" aria-label="Map showing routes and shared bus locations" />;
}

function App() {
  const [language, setLanguage] = useState<Language>(() => {
    const stored = localStorage.getItem("buslk-language");
    return stored === "si" || stored === "ta" ? stored : "en";
  });
  const t = useTranslation(language);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [setupAvailable, setSetupAvailable] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);
  const [vehicle, setVehicle] = useState<{ vehicleId: string; routeId: string } | null>(null);
  const [sharing, setSharing] = useState(false);
  const [driverMessage, setDriverMessage] = useState("");
  const [operatorFleet, setOperatorFleet] = useState<FleetVehicle[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const watchId = useRef<number | null>(null);
  const isAdminPage = window.location.pathname === "/admin";
  const selectedRouteData = useMemo(
    () => routes.find((route) => route.id === selectedRoute) || null,
    [routes, selectedRoute]
  );
  const shownVehicles = vehicles.filter((item) => item.routeId === selectedRoute);

  const setNotice = useCallback((text: string, isError = false) => {
    setMessage(text);
    setError(isError);
  }, []);

  const refreshUser = useCallback(async () => {
    const result = await api<{ user: User | null; csrfToken?: string }>("/api/auth/me");
    csrfToken = result.csrfToken || null;
    setUser(result.user);
    if (!result.user) {
      try {
        const setup = await api<{ available: boolean }>("/api/auth/setup-status");
        setSetupAvailable(setup.available);
      } catch {
        setSetupAvailable(false);
      }
    }
  }, []);

  useEffect(() => {
    let active = true;
    Promise.all([
      api<{ routes: Route[] }>("/api/routes"),
      api<{ vehicles: Vehicle[] }>("/api/vehicles"),
      refreshUser()
    ]).then(([routeResult, vehicleResult]) => {
      if (!active) return;
      setRoutes(routeResult.routes);
      setSelectedRoute(routeResult.routes[0]?.id || null);
      setVehicles(vehicleResult.vehicles);
    }).catch((reason: unknown) => {
      if (active) setNotice(reason instanceof Error ? reason.message : "Could not load the bus tracker.", true);
    });
    return () => { active = false; };
  }, [refreshUser]);

  useEffect(() => {
    if (user?.role === "driver") {
      api<{ vehicle: { vehicleId: string; routeId: string } | null }>("/api/driver/vehicle")
        .then((result) => setVehicle(result.vehicle))
        .catch((reason: unknown) => setNotice(reason instanceof Error ? reason.message : "Could not load your vehicle.", true));
    } else {
      setVehicle(null);
    }
    if (user?.role === "operator") {
      api<{ vehicles: FleetVehicle[] }>("/api/operator/fleet")
        .then((result) => setOperatorFleet(result.vehicles))
        .catch((reason: unknown) => setNotice(reason instanceof Error ? reason.message : "Could not load fleet.", true));
    }
  }, [user, refreshKey]);

  useEffect(() => {
    const stream = new EventSource("/api/stream");
    stream.onmessage = (event) => {
      try {
        setVehicles((JSON.parse(event.data) as { vehicles: Vehicle[] }).vehicles);
      } catch {
        setNotice("Received an invalid live location update.", true);
      }
    };
    return () => stream.close();
  }, []);

  const stopLocationSharing = useCallback(async () => {
    if (watchId.current !== null) {
      navigator.geolocation.clearWatch(watchId.current);
      watchId.current = null;
    }
    setSharing(false);
    if (user?.role === "driver") {
      await api("/api/driver/location/stop", { method: "POST", body: "{}" });
    }
  }, [user]);

  useEffect(() => {
    const stopOnClose = () => {
      if (watchId.current !== null) navigator.geolocation.clearWatch(watchId.current);
      if (watchId.current !== null && csrfToken) {
        void fetch("/api/driver/location/stop", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
          body: "{}",
          keepalive: true
        });
      }
    };
    window.addEventListener("pagehide", stopOnClose);
    return () => window.removeEventListener("pagehide", stopOnClose);
  }, []);

  async function handleForm(event: React.FormEvent<HTMLFormElement>, endpoint: string, success?: string) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      const result = await api<{ user: User; csrfToken?: string }>(endpoint, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      if (result.csrfToken) csrfToken = result.csrfToken;
      form.reset();
      if (result.user?.role === "admin" && endpoint.endsWith("setup-admin")) {
        setUser(result.user);
        setSetupAvailable(false);
        setNotice("Admin account created. You are signed in.");
      } else if (endpoint.endsWith("/login")) {
        await refreshUser();
        setNotice("");
      } else {
        setNotice(result.user?.status === "pending" ? `${t("pending")} ${result.user.email}` : success || "Account created. Sign in to continue.");
      }
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "The request could not be completed.", true);
    }
  }

  async function signOut() {
    try {
      if (user?.role === "driver" && sharing) await stopLocationSharing();
      await api("/api/auth/logout", { method: "POST", body: "{}" });
      csrfToken = null;
      setUser(null);
      setVehicle(null);
      setNotice("Signed out.");
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "Could not sign out.", true);
    }
  }

  async function toggleSharing() {
    if (sharing) {
      try {
        await stopLocationSharing();
        setDriverMessage("Sharing stopped and the last shared location was removed.");
      } catch (reason) {
        setDriverMessage(reason instanceof Error ? reason.message : "Could not stop sharing.",);
      }
      return;
    }
    if (!window.isSecureContext) {
      setDriverMessage("Location sharing requires HTTPS (or localhost).");
      return;
    }
    if (!navigator.geolocation || user?.role !== "driver" || !vehicle) {
      setDriverMessage(t("driverReady"));
      return;
    }
    setSharing(true);
    setDriverMessage("Sharing your location. Keep this page open.");
    watchId.current = navigator.geolocation.watchPosition(
      async (position) => {
        try {
          await api("/api/locations", {
            method: "POST",
            body: JSON.stringify({
              lat: position.coords.latitude,
              lon: position.coords.longitude,
              accuracy: Math.round(position.coords.accuracy)
            })
          });
          setDriverMessage(`Location shared · GPS accuracy ±${Math.round(position.coords.accuracy)} m`);
        } catch (reason) {
          setDriverMessage(reason instanceof Error ? reason.message : "Could not share location.");
        }
      },
      (reason) => setDriverMessage(reason.message || "Location is unavailable. Check your device GPS."),
      { enableHighAccuracy: true, maximumAge: 5_000, timeout: 20_000 }
    );
  }

  async function createVehicle(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      await api("/api/operator/fleet", { method: "POST", body: JSON.stringify(payload) });
      form.reset();
      setNotice("Vehicle registered.");
      setRefreshKey((value) => value + 1);
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "Could not register vehicle.", true);
    }
  }

  async function assignDriver(event: React.FormEvent<HTMLFormElement>, vehicleId: string) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      await api(`/api/operator/fleet/${encodeURIComponent(vehicleId)}/assign`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setNotice("Driver assigned.");
      setRefreshKey((value) => value + 1);
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "Could not assign driver.", true);
    }
  }

  function changeLanguage(value: string) {
    const next = value as Language;
    setLanguage(next);
    localStorage.setItem("buslk-language", next);
  }

  if (isAdminPage) {
    return user?.role === "admin"
      ? <AdminDashboard user={user} onSignOut={signOut} />
      : <main className="admin-shell"><p className="notice error">Sign in as an administrator to continue.</p><a href="/">Return to live map</a></main>;
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="SL Bus.lk home">
          <span className="brand-mark" aria-hidden="true">B</span><span>bus<span className="brand-accent">.lk</span></span>
        </a>
        <div className="topbar-right">
          <span className="network-status"><span className="status-dot" /><span>Connected</span></span>
          <label className="language-picker">
            <span className="sr-only">Language</span>
            <select value={language} onChange={(event) => changeLanguage(event.target.value)} aria-label="Language">
              <option value="en">English</option><option value="si">සිංහල</option><option value="ta">தமிழ்</option>
            </select>
          </label>
        </div>
      </header>
      <main className="main-layout">
        <aside className="sidebar">
          <div className="intro">
            <p className="eyebrow">{t("community")}</p>
            <h1>{t("headline")}</h1>
            <p className="intro-copy">{t("intro")}</p>
          </div>
          <section className="route-section" aria-labelledby="route-heading">
            <div className="section-heading"><h2 id="route-heading">{t("routes")}</h2><span className="count-badge">{routes.length}</span></div>
            <div className="route-list">
              {routes.map((item) => (
                <button key={item.id} type="button" className={`route-card${selectedRoute === item.id ? " selected" : ""}`}
                  aria-pressed={selectedRoute === item.id} onClick={() => setSelectedRoute(item.id)}>
                  <span className="route-symbol" aria-hidden="true">↗</span>
                  <span className="route-details"><span className="route-name">{language === "si" ? item.nameSi : language === "ta" ? item.nameTa : item.name}</span>
                    <span className="route-meta">DEMO ROUTE · {item.stops.length} stops</span></span><span className="route-arrow">›</span>
                </button>
              ))}
            </div>
          </section>
          <section className="live-card" aria-labelledby="live-heading">
            <div className="live-card-head"><div><p className="eyebrow">{t("live")}</p>
              <h2 id="live-heading"><span>{shownVehicles.filter((item) => item.status === "live").length}</span> {t("sharing")}</h2>
            </div><span className="live-indicator"><span />{t("live")}</span></div>
            {!shownVehicles.length && <p className="empty-state">{t("empty")}</p>}
            <ul className="vehicle-list">{shownVehicles.map((item) => (
              <li className="vehicle-row" key={item.vehicleId}>
                <span className="vehicle-badge">▣</span><span className="vehicle-info"><strong>{item.vehicleId}</strong><small>{selectedRouteData?.name}</small></span>
                <span className={`vehicle-age${item.status === "stale" ? " stale" : ""}`}>{ageLabel(item.ageSeconds)}</span>
              </li>
            ))}</ul>
          </section>
          <section className="account-panel" aria-labelledby="account-heading">
            <div className="account-heading"><span className="driver-icon">♙</span>
              <div><h2 id="account-heading">{t("accounts")}</h2><p role="status">{user ? `${user.role} · ${user.status}` : "Sign in or create an account"}</p></div>
            </div>
            {!user ? (
              <div>
                <form onSubmit={(event) => void handleForm(event, "/api/auth/login")}>
                  <h3>{t("signIn")}</h3>
                  <label htmlFor="login-email">{t("email")}</label><input id="login-email" name="email" type="email" maxLength={254} autoComplete="username" required />
                  <label htmlFor="login-password">{t("password")}</label><input id="login-password" name="password" type="password" maxLength={128} autoComplete="current-password" required />
                  <button className="share-button" type="submit">{t("signIn")}</button>
                </form>
                {setupAvailable && <details className="register-details">
                  <summary>{t("adminSetup")}</summary><p className="privacy-note">One-time setup on this computer. Save your admin credentials securely.</p>
                  <form onSubmit={(event) => void handleForm(event, "/api/auth/setup-admin")}>
                    <label>{t("name")}<input name="name" maxLength={80} required /></label>
                    <label>{t("email")}<input name="email" type="email" maxLength={254} required /></label>
                    <label>{t("adminPassword")}<input name="password" type="password" minLength={16} maxLength={128} required /></label>
                    <button className="share-button" type="submit">{t("createAdmin")}</button>
                  </form>
                </details>}
                <details className="register-details">
                  <summary>{t("createAccount")}</summary>
                  <form onSubmit={(event) => void handleForm(event, "/api/auth/register")}>
                    <label>{t("name")}<input name="name" maxLength={80} autoComplete="name" required /></label>
                    <label>{t("email")}<input name="email" type="email" maxLength={254} autoComplete="email" required /></label>
                    <label>{t("password")}<input name="password" type="password" minLength={12} maxLength={128} autoComplete="new-password" required /></label>
                    <label>{t("accountType")}<select name="role" onChange={(event) => {
                      const target = event.currentTarget.form?.querySelector<HTMLInputElement>("[name=organization]");
                      if (target) target.required = ["operator", "authority"].includes(event.target.value);
                    }}>
                      <option value="passenger">Passenger</option><option value="driver">Bus driver</option>
                      <option value="operator">Bus operator</option><option value="authority">Transport authority</option>
                    </select></label>
                    <label>{t("organization")}<input name="organization" maxLength={120} /></label>
                    <label className="consent-label"><input name="consent" type="checkbox" value="true" required /><span>{t("consent")}</span></label>
                    <button className="share-button" type="submit">{t("register")}</button>
                  </form>
                </details>
              </div>
            ) : (
              <div>
                <p className="account-identity">{user.name} · {user.email}</p>
                <RoleDashboard user={user} t={t} vehicle={vehicle} fleet={operatorFleet}
                  routes={routes} onCreateVehicle={createVehicle} onAssignDriver={assignDriver} />
                {user.role === "admin" && <a className="admin-dashboard-link" href="/admin">Open admin dashboard →</a>}
                <button className="secondary-button" type="button" onClick={() => void signOut()}>{t("signOut")}</button>
              </div>
            )}
            {message && <p className="driver-message" role="status" aria-live="polite" style={{ color: error ? "#a4453e" : undefined }}>{message}</p>}
          </section>
          {user?.role === "driver" && <details className="driver-panel" open>
            <summary><span className="driver-icon">↗</span><span><strong>{t("driverTitle")}</strong><small>{t("driverSubtitle")}</small></span></summary>
            <p className="privacy-note">{vehicle ? `${t("assigned")}: ${vehicle.vehicleId}` : t("driverReady")}</p>
            <p className="privacy-note">{t("privacy")}</p>
            <button className={`share-button${sharing ? " stop" : ""}`} disabled={!vehicle} type="button" onClick={() => void toggleSharing()}>
              {sharing ? t("stop") : t("start")}
            </button>
            <p className="driver-message" role="status" aria-live="polite">{driverMessage}</p>
          </details>}
          <p className="prototype-note">ⓘ Prototype: routes and locations depend on community contributions.</p>
        </aside>
        <section className="map-panel" aria-label="Live bus map">
          <div className="map-toolbar"><div className="map-title"><span className="map-pin">⌖</span>
            <div><strong>{t("mapTitle")}</strong><small>{t("mapSubtitle")}</small></div></div>
            <button className="locate-button" type="button" aria-label="Center map on Colombo" onClick={() => window.dispatchEvent(new Event("center-map"))}>◎</button>
          </div>
          <MapView route={selectedRouteData} vehicles={vehicles} />
          <div className="map-legend"><span><i className="legend-live" />{t("legendLive")}</span><span><i className="legend-stale" />{t("legendStale")}</span></div>
          <p className="map-attribution">© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors</p>
        </section>
      </main>
      <footer className="footer"><span>Built for people who ride.</span><span>·</span><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">Map data © OpenStreetMap</a></footer>
    </div>
  );
}

function RoleDashboard({
  user, t, vehicle, fleet, routes, onCreateVehicle, onAssignDriver
}: {
  user: User;
  t: (key: TranslationKey) => string;
  vehicle: { vehicleId: string; routeId: string } | null;
  fleet: FleetVehicle[];
  routes: Route[];
  onCreateVehicle: (event: React.FormEvent<HTMLFormElement>) => void;
  onAssignDriver: (event: React.FormEvent<HTMLFormElement>, vehicleId: string) => void;
}) {
  if (user.role === "passenger") return <p className="privacy-note">{t("passengerInfo")}</p>;
  if (user.role === "authority") return <p className="privacy-note">{t("authorityInfo")}</p>;
  if (user.role === "driver") return <p className="privacy-note">{vehicle ? `${t("assigned")}: ${vehicle.vehicleId}` : t("driverReady")}</p>;
  if (user.role === "admin") return <p className="privacy-note">{t("adminInfo")}</p>;
  return (
    <div className="operator-dashboard">
      <p className="privacy-note">{t("operatorInfo")}</p>
      <form className="dashboard-form" onSubmit={onCreateVehicle}>
        <label>{t("vehicle")}<input name="vehicleId" maxLength={32} pattern="[A-Za-z0-9_-]{1,32}" placeholder="e.g. WP-NA-1234" required /></label>
        <label>{t("route")}<select name="routeId" required>{routes.map((route) => <option value={route.id} key={route.id}>{route.name}</option>)}</select></label>
        <button className="share-button" type="submit">{t("addVehicle")}</button>
      </form>
      <h3>{t("addVehicle")}</h3>
      {!fleet.length && <p className="privacy-note">No vehicles registered yet.</p>}
      {fleet.map((item) => <article className="fleet-item" key={item.vehicleId}>
        <strong>{item.vehicleId} · {routes.find((route) => route.id === item.routeId)?.name || item.routeId}</strong>
        <small>{item.driverEmail || "No driver assigned"}</small>
        <form className="assign-form" onSubmit={(event) => onAssignDriver(event, item.vehicleId)}>
          <input name="email" type="email" placeholder={t("assignDriver")} required />
          <button type="submit">Assign</button>
        </form>
      </article>)}
    </div>
  );
}

function AdminDashboard({ user, onSignOut }: { user: User; onSignOut: () => void }) {
  useEffect(() => { void import("../../admin.css"); }, []);
  const [section, setSection] = useState("approvals");
  const [users, setUsers] = useState<User[]>([]);
  const [fleet, setFleet] = useState<FleetVehicle[]>([]);
  const [summary, setSummary] = useState({ users: 0, pending: 0, vehicles: 0, live: 0 });
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [noticeError, setNoticeError] = useState(false);
  const [email, setEmail] = useState(user.email);

  const load = useCallback(async () => {
    try {
      const [summaryResult, userResult, fleetResult] = await Promise.all([
        api<{ summary: typeof summary }>("/api/admin/summary"),
        api<{ users: User[] }>("/api/admin/users"),
        api<{ vehicles: FleetVehicle[] }>("/api/admin/fleet")
      ]);
      setSummary(summaryResult.summary);
      setUsers(userResult.users);
      setFleet(fleetResult.vehicles);
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "Could not load dashboard.",);
      setNoticeError(true);
    }
  }, []);
  useEffect(() => { void load(); }, [load]);

  async function setStatus(target: User, status: AccountStatus) {
    if (!window.confirm(`${status === "active" ? "Approve/reactivate" : status} ${target.name} (${target.email})?`)) return;
    try {
      await api(`/api/admin/users/${target.id}/status`, { method: "POST", body: JSON.stringify({ status }) });
      setNotice(`${target.name}'s account is now ${status}.`);
      setNoticeError(false);
      await load();
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "Could not update account.");
      setNoticeError(true);
    }
  }

  async function changeEmail(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form).entries());
    try {
      const result = await api<{ user: User }>("/api/admin/account/email", { method: "POST", body: JSON.stringify(values) });
      setEmail(result.user.email);
      setNotice("Admin sign-in email updated.");
      setNoticeError(false);
      form.reset();
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "Could not update admin email.");
      setNoticeError(true);
    }
  }

  const pending = users.filter((account) => account.status === "pending" && ["operator", "authority"].includes(account.role));
  const filtered = users.filter((account) =>
    `${account.name} ${account.email} ${account.role} ${account.organization || ""} ${account.status}`.toLowerCase().includes(query.toLowerCase())
  );
  const actions = (account: User) => {
    const choices: { title: string; status: AccountStatus; className: string }[] = account.role === "admin" ? []
      : account.status === "pending" ? [
          { title: "Approve", status: "active", className: "button button-approve" },
          { title: "Reject", status: "rejected", className: "button button-reject" }
        ]
      : ["operator", "authority"].includes(account.role) && account.status === "active"
        ? [{ title: "Suspend", status: "suspended" as const, className: "button button-reject" }]
        : ["suspended", "rejected"].includes(account.status)
          ? [{ title: "Reactivate", status: "active" as const, className: "button button-approve" }] : [];
    return choices.map((item) => <button key={item.title} className={item.className} type="button" onClick={() => void setStatus(account, item.status)}>{item.title}</button>);
  };

  return (
    <div className="admin-shell">
      <header className="admin-topbar">
        <a className="brand" href="/" aria-label="SL Bus.lk home"><span className="brand-mark">B</span><span>bus<span className="brand-accent">.lk</span></span></a>
        <div className="topbar-actions"><a className="back-link" href="/">← Back to live map</a><span className="admin-name">{user.name}</span>
          <button className="button button-light" type="button" onClick={onSignOut}>Sign out</button></div>
      </header>
      <main className="dashboard">
        <section className="welcome"><div><p className="eyebrow">PLATFORM CONTROL</p><h1>Admin dashboard</h1>
          <p className="welcome-copy">Review stakeholder access and keep the pilot network organized.</p></div><span className="admin-badge"><i />Administrator</span></section>
        <section className="metric-grid" aria-label="Network summary">
          {[["Total accounts", summary.users, "All account roles"], ["Awaiting review", summary.pending, "Operator and authority requests"],
            ["Registered buses", summary.vehicles, "Across operator fleets"], ["Sharing now", summary.live, "Recent driver GPS updates"]].map(([label, value, detail]) => (
            <article className="metric-card" key={String(label)}><span className="metric-icon green">◉</span><div><p>{label}</p><strong>{value}</strong><small>{detail}</small></div></article>
          ))}
        </section>
        <section className="workspace-card">
          <nav className="section-tabs" aria-label="Admin dashboard sections">
            {(["approvals", "accounts", "fleet", "account"] as const).map((tab) => (
              <button className={`tab-button${section === tab ? " active" : ""}`} type="button" key={tab}
                aria-current={section === tab ? "page" : undefined} onClick={() => setSection(tab)}>
                {tab === "approvals" ? <>Approvals <span className="tab-count">{pending.length}</span></> : tab === "accounts" ? "All accounts" : tab === "fleet" ? "Bus fleet" : "Admin account"}
              </button>
            ))}
          </nav>
          {notice && <div className={`notice${noticeError ? " error" : ""}`} role="status">{notice}</div>}
          {section === "approvals" && <section className="dashboard-section active">
            <div className="section-heading"><div><h2>Stakeholder approvals</h2><p>Verify operator and transport-authority requests before granting access.</p></div>
              <button className="button button-light" type="button" onClick={() => void load()}>↻ Refresh</button></div>
            <div className="record-list">{pending.length ? pending.map((account) => <article className="approval-card" key={account.id}>
              <div className="approval-main"><span className="approval-icon">{account.role === "operator" ? "▣" : "⌖"}</span>
                <div className="approval-details"><strong>{account.name}</strong><span>{account.email}</span>
                  <div className="approval-meta"><span className="role-chip">{account.role}</span><span className="role-chip">{account.organization}</span></div></div>
              </div><div className="approval-actions">{actions(account)}</div>
            </article>) : <p className="empty-state">You’re all caught up. No stakeholder accounts are waiting for approval.</p>}</div>
          </section>}
          {section === "accounts" && <section className="dashboard-section active"><div className="section-heading">
            <div><h2>All accounts</h2><p>Review account roles and access status.</p></div>
            <label className="search-box"><span>⌕</span><input type="search" placeholder="Search name or email" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
          </div><div className="table-wrap"><table><thead><tr><th>Name</th><th>Role</th><th>Organization</th><th>Status</th><th>Joined</th><th>Actions</th></tr></thead>
            <tbody>{filtered.map((account) => <tr key={account.id}><td>{account.name}</td><td>{account.role}</td><td>{account.organization || "—"}</td>
              <td><span className={`status-chip ${account.status}`}>{account.status}</span></td><td>{new Date(account.createdAt).toLocaleDateString()}</td><td>{actions(account)}</td></tr>)}</tbody></table></div>
            {!filtered.length && <p className="empty-state">No accounts match your search.</p>}
          </section>}
          {section === "fleet" && <section className="dashboard-section active"><div className="section-heading"><div><h2>Registered bus fleet</h2>
            <p>See which operator owns each bus and whether a driver is assigned.</p></div><button className="button button-light" type="button" onClick={() => void load()}>↻ Refresh</button></div>
            <div className="table-wrap"><table><thead><tr><th>Vehicle ID</th><th>Route</th><th>Operator</th><th>Operator status</th><th>Assigned driver</th></tr></thead>
              <tbody>{fleet.map((item) => <tr key={item.vehicleId}><td>{item.vehicleId}</td><td>{item.routeId}</td>
                <td>{item.organization || item.operatorName} ({item.operatorEmail})</td><td><span className={`status-chip ${item.operatorStatus}`}>{item.operatorStatus}</span></td>
                <td>{item.driverName ? `${item.driverName} (${item.driverEmail})` : "Unassigned"}</td></tr>)}</tbody></table></div>
          </section>}
          {section === "account" && <section className="dashboard-section active"><div className="section-heading"><div><h2>Admin account</h2><p>Change the email address you use to sign in.</p></div></div>
            <div className="account-settings"><p>Current email: <strong>{email}</strong></p>
              <p className="account-settings-note">Enter an email address you control and confirm with your current password.</p>
              <form className="admin-email-form" onSubmit={(event) => void changeEmail(event)}>
                <label>New email address<input name="email" type="email" maxLength={254} required /></label>
                <label>Current password<input name="password" type="password" autoComplete="current-password" required /></label>
                <button className="button button-approve" type="submit">Update admin email</button>
              </form>
            </div>
          </section>}
        </section>
        <p className="dashboard-footnote">Location tracking is opt-in. The Colombo demo route is illustrative, not verified.</p>
      </main>
    </div>
  );
}

export default App;
