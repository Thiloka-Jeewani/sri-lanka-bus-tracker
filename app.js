const translations = {
  en: {
    connected: "Connected", language: "Language", community: "COMMUNITY TRANSIT",
    headline: "Your bus.<br>Not a guess.", intro: "See community-shared bus locations and spend less time waiting.",
    routes: "Routes", live: "LIVE", "buses-sharing": "buses sharing", empty: "No buses are sharing their location yet. Invite a driver to get started.",
    "driver-title": "I'm driving a bus", "driver-subtitle": "Share your location with passengers", "bus-id": "Bus / vehicle ID",
    "choose-route": "Route", privacy: "Your location is shared only while you have sharing turned on. Stop sharing at any time.",
    "start-sharing": "Start sharing location", "stop-sharing": "Stop sharing location", "map-title": "Colombo, Sri Lanka",
    "map-subtitle": "Community bus network", "legend-live": "Sharing now", "legend-stale": "Last seen",
    "prototype-note": "Prototype: routes and locations depend on community contributions.", footer: "Built for people who ride.",
    "map-data": "Map data © OpenStreetMap", demo: "DEMO ROUTE · REAL DATA NOT VERIFIED",
    "no-vehicles": "No live buses on this route yet", "vehicles-label": "buses sharing", "last-seen": "Last seen",
    "now": "just now", "seconds": "s ago", "minutes": "min ago", sharing: "Sharing your location. Keep this page open.",
    stopped: "Location sharing stopped.", denied: "Location access was denied. Allow location access in your browser to share.",
    unavailable: "Location is unavailable. Check your device GPS and try again.", timeout: "GPS took too long. Check your signal and try again.",
    secure: "Location sharing requires HTTPS (or localhost). Open this app on a secure connection.",
    "enter-id": "Enter a bus or vehicle ID first.", sending: "Connecting and waiting for your first GPS fix…",
    sent: "Location shared successfully.", apiError: "Could not share location: ", leaflet: "Map could not load. Check your internet connection.",
    accounts: "Accounts", "sign-in": "Sign in", email: "Email", password: "Password",
    "create-account": "Create an account", "full-name": "Full name", "account-type": "Account type",
    "role-passenger": "Passenger", "role-driver": "Bus driver", "role-operator": "Bus operator",
    "role-authority": "Transport authority", organization: "Organization / agency", register: "Register",
    "account-consent": "I understand that GPS is collected only while a driver has explicitly started sharing and can be stopped at any time.",
    "sign-out": "Sign out", pending: "Your account is waiting for admin approval.",
    "admin-setup-title": "Set up the first administrator",
    "admin-setup-note": "One-time setup on this computer. Create and securely save your admin email and password.",
    "admin-password": "Admin password (16+ characters)",
    "create-admin": "Create admin and open dashboard",
    "role-dashboard": "Your account", "driver-ready": "Ask your operator to register and assign a vehicle to your account before sharing GPS.",
    "driver-assigned": "Assigned vehicle", "operator-fleet": "Operator fleet", "add-vehicle": "Register vehicle",
    "assign-driver": "Assign driver by registered email", "review-accounts": "Review stakeholder accounts",
    approve: "Approve", reject: "Reject", "authority-info": "Authority view: check published routes and live vehicle status. Route data is illustrative in this pilot.",
    "passenger-info": "Passenger account active. You can browse the public live map.",
    "admin-info": "Platform administrator", "operator-info": "Register vehicles for your approved operator account.",
    "routeLabel": "demo stops", meterAccuracy: "GPS accuracy ±", mapCenter: "Colombo, Sri Lanka"
  },
  si: {
    connected: "සම්බන්ධයි", language: "භාෂාව", community: "ප්‍රජා ප්‍රවාහනය",
    headline: "ඔබේ බසය.<br>අනුමානයක් නොවේ.", intro: "ප්‍රජාව බෙදාගන්නා බස් රථ ස්ථාන බලන්න. බලා සිටින කාලය අඩු කරගන්න.",
    routes: "මාර්ග", live: "සජීවී", "buses-sharing": "බස් ස්ථාන බෙදාගනී", empty: "තවම බස් රථ ස්ථාන බෙදාගෙන නැත. ආරම්භ කිරීමට රියදුරෙකුට ආරාධනා කරන්න.",
    "driver-title": "මම බස් රථයක් පදවනවා", "driver-subtitle": "ඔබේ ස්ථානය මගීන් සමඟ බෙදාගන්න", "bus-id": "බස් / වාහන අංකය",
    "choose-route": "මාර්ගය", privacy: "ස්ථාන බෙදාගැනීම ක්‍රියාත්මක විට පමණක් බෙදාගනී. ඕනෑම විටෙක නවත්වන්න.",
    "start-sharing": "ස්ථානය බෙදාගන්න", "stop-sharing": "බෙදාගැනීම නවත්වන්න", "map-title": "කොළඹ, ශ්‍රී ලංකාව",
    "map-subtitle": "ප්‍රජා බස් ජාලය", "legend-live": "දැන් බෙදාගනී", "legend-stale": "අවසන් වරට දුටුවේ",
    "prototype-note": "මූලාකෘතිය: මාර්ග සහ ස්ථාන ප්‍රජා දායකත්වය මත රඳා පවතී.", footer: "මගීන් වෙනුවෙන් නිර්මාණය කළා.",
    "map-data": "සිතියම් දත්ත © OpenStreetMap", demo: "ආදර්ශ මාර්ගය · සැබෑ දත්ත තහවුරු කර නැත",
    "no-vehicles": "මෙම මාර්ගයේ සජීවී බස් රථ නැත", "vehicles-label": "බස් ස්ථාන බෙදාගනී", "last-seen": "අවසන් වරට",
    "now": "දැන්", "seconds": "තත්පරයකට පෙර", "minutes": "මිනිත්තුකට පෙර", sharing: "ඔබේ ස්ථානය බෙදාගනී. මෙම පිටුව විවෘතව තබන්න.",
    stopped: "ස්ථාන බෙදාගැනීම නතර කළා.", denied: "ස්ථාන අවසරය ප්‍රතික්ෂේප විය. බ්‍රවුසරයේ අවසරය ලබා දෙන්න.",
    unavailable: "ස්ථානය ලබාගත නොහැක. GPS පරීක්ෂා කර නැවත උත්සාහ කරන්න.", timeout: "GPS ප්‍රතිචාරය ප්‍රමාදයි. සංඥාව පරීක්ෂා කරන්න.",
    secure: "ස්ථාන බෙදාගැනීමට HTTPS හෝ localhost අවශ්‍යයි.", "enter-id": "පළමුව බස් හෝ වාහන අංකය ඇතුළත් කරන්න.",
    sending: "සම්බන්ධ වෙමින් GPS ස්ථානය බලාපොරොත්තු වෙයි…", sent: "ස්ථානය සාර්ථකව බෙදාගත්තා.",
    apiError: "ස්ථානය බෙදාගත නොහැක: ", leaflet: "සිතියම පූරණය නොවීය. අන්තර්ජාල සම්බන්ධතාව පරීක්ෂා කරන්න.",
    accounts: "ගිණුම්", "sign-in": "පිවිසෙන්න", email: "විද්‍යුත් තැපෑල", password: "මුරපදය",
    "create-account": "ගිණුමක් සාදන්න", "full-name": "සම්පූර්ණ නම", "account-type": "ගිණුම් වර්ගය",
    "role-passenger": "මගියා", "role-driver": "බස් රියදුරු", "role-operator": "බස් මෙහෙයුම්කරු",
    "role-authority": "ප්‍රවාහන අධිකාරිය", organization: "ආයතනය / ඒජන්සිය", register: "ලියාපදිංචි වන්න",
    "account-consent": "රියදුරෙකු පැහැදිලිව ස්ථාන බෙදාගැනීම ආරම්භ කළ විට පමණක් GPS එකතු කරන අතර ඕනෑම වේලාවක නතර කළ හැකි බව මම තේරුම් ගනිමි.",
    "sign-out": "ඉවත් වන්න", pending: "ඔබගේ ගිණුම පරිපාලක අනුමැතිය සඳහා බලා සිටී.",
    "admin-setup-title": "පළමු පරිපාලක සකසන්න",
    "admin-setup-note": "මෙම පරිගණකයේ එක් වරක් පමණි. ඔබේ පරිපාලක ඊමේල් සහ මුරපදය සකසා සුරක්ෂිතව තබාගන්න.",
    "admin-password": "පරිපාලක මුරපදය (අක්ෂර 16+)",
    "create-admin": "පරිපාලක සාදා පාලක පුවරුවට යන්න",
    "role-dashboard": "ඔබගේ ගිණුම", "driver-ready": "GPS බෙදාගැනීමට පෙර ඔබේ මෙහෙයුම්කරු ඔබට වාහනයක් ලියාපදිංචි කර පැවරිය යුතුය.",
    "driver-assigned": "පවරා ඇති වාහනය", "operator-fleet": "මෙහෙයුම්කරු වාහන සමූහය", "add-vehicle": "වාහනය ලියාපදිංචි කරන්න",
    "assign-driver": "ලියාපදිංචි ඊමේල් මඟින් රියදුරු පවරන්න", "review-accounts": "පාර්ශ්වකරුවන්ගේ ගිණුම් සමාලෝචනය",
    approve: "අනුමත කරන්න", reject: "ප්‍රතික්ෂේප කරන්න",
    "authority-info": "අධිකාරි දසුන: ප්‍රකාශිත මාර්ග සහ සජීවී වාහන තත්ත්වය පරීක්ෂා කරන්න. මෙම නියමු අදියරේ මාර්ග දත්ත ආදර්ශයකි.",
    "passenger-info": "මගී ගිණුම සක්‍රියයි. ඔබට පොදු සජීවී සිතියම නැරඹිය හැක.",
    "admin-info": "වේදිකා පරිපාලක", "operator-info": "අනුමත මෙහෙයුම්කරු ගිණුමෙන් වාහන ලියාපදිංචි කරන්න.",
    routeLabel: "ආදර්ශ නැවතුම්", meterAccuracy: "GPS නිරවද්‍යතාව ±", mapCenter: "කොළඹ, ශ්‍රී ලංකාව"
  },
  ta: {
    connected: "இணைக்கப்பட்டது", language: "மொழி", community: "சமூகப் போக்குவரத்து",
    headline: "உங்கள் பேருந்து.<br>ஊகமல்ல.", intro: "சமூகம் பகிரும் பேருந்து இருப்பிடங்களைப் பார்த்து காத்திருக்கும் நேரத்தைக் குறையுங்கள்.",
    routes: "வழிகள்", live: "நேரலை", "buses-sharing": "பேருந்துகள் பகிர்கின்றன", empty: "பேருந்துகள் இன்னும் இருப்பிடத்தைப் பகிரவில்லை. தொடங்க ஓட்டுநரை அழைக்கவும்.",
    "driver-title": "நான் பேருந்து ஓட்டுநர்", "driver-subtitle": "உங்கள் இருப்பிடத்தைப் பயணிகளுடன் பகிரவும்", "bus-id": "பேருந்து / வாகன எண்",
    "choose-route": "வழி", privacy: "பகிர்வு இயக்கத்தில் இருக்கும்போது மட்டுமே உங்கள் இருப்பிடம் பகிரப்படும். எப்போது வேண்டுமானாலும் நிறுத்தலாம்.",
    "start-sharing": "இருப்பிடத்தைப் பகிரவும்", "stop-sharing": "பகிர்வை நிறுத்தவும்", "map-title": "கொழும்பு, இலங்கை",
    "map-subtitle": "சமூகப் பேருந்து வலைப்பின்னல்", "legend-live": "இப்போது பகிர்கிறது", "legend-stale": "கடைசியாகப் பார்த்தது",
    "prototype-note": "முன்மாதிரி: வழிகளும் இருப்பிடங்களும் சமூகப் பங்களிப்புகளைச் சார்ந்தவை.", footer: "பயணிகளுக்காக உருவாக்கப்பட்டது.",
    "map-data": "வரைபடத் தரவு © OpenStreetMap", demo: "மாதிரி வழி · உண்மைத் தரவு சரிபார்க்கப்படவில்லை",
    "no-vehicles": "இந்த வழியில் நேரலைப் பேருந்துகள் இல்லை", "vehicles-label": "பேருந்துகள் பகிர்கின்றன", "last-seen": "கடைசியாக",
    "now": "இப்போது", "seconds": "விநாடிகளுக்கு முன்", "minutes": "நிமிடங்களுக்கு முன்", sharing: "உங்கள் இருப்பிடம் பகிரப்படுகிறது. இந்தப் பக்கத்தைத் திறந்து வைக்கவும்.",
    stopped: "இருப்பிடப் பகிர்வு நிறுத்தப்பட்டது.", denied: "இருப்பிட அனுமதி மறுக்கப்பட்டது. உலாவியில் அனுமதி வழங்கவும்.",
    unavailable: "இருப்பிடத்தைக் கண்டறிய முடியவில்லை. GPS-ஐச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.", timeout: "GPS நேரம் கடந்தது. சிக்னலைச் சரிபார்க்கவும்.",
    secure: "இருப்பிடப் பகிர்வுக்கு HTTPS அல்லது localhost தேவை.", "enter-id": "முதலில் பேருந்து அல்லது வாகன எண்ணை உள்ளிடவும்.",
    sending: "இணைக்கப்பட்டு GPS இருப்பிடத்திற்காகக் காத்திருக்கிறது…", sent: "இருப்பிடம் வெற்றிகரமாகப் பகிரப்பட்டது.",
    apiError: "இருப்பிடத்தைப் பகிர முடியவில்லை: ", leaflet: "வரைபடத்தை ஏற்ற முடியவில்லை. இணைய இணைப்பைச் சரிபார்க்கவும்.",
    accounts: "கணக்குகள்", "sign-in": "உள்நுழைக", email: "மின்னஞ்சல்", password: "கடவுச்சொல்",
    "create-account": "கணக்கை உருவாக்கவும்", "full-name": "முழுப் பெயர்", "account-type": "கணக்கு வகை",
    "role-passenger": "பயணி", "role-driver": "பேருந்து ஓட்டுநர்", "role-operator": "பேருந்து இயக்குநர்",
    "role-authority": "போக்குவரத்து அதிகாரசபை", organization: "நிறுவனம் / முகமை", register: "பதிவு செய்க",
    "account-consent": "ஓட்டுநர் வெளிப்படையாகப் பகிரத் தொடங்கும்போது மட்டுமே GPS சேகரிக்கப்படும், எப்போது வேண்டுமானாலும் நிறுத்தலாம் என்பதைப் புரிந்துகொள்கிறேன்.",
    "sign-out": "வெளியேறு", pending: "உங்கள் கணக்கு நிர்வாக ஒப்புதலுக்காகக் காத்திருக்கிறது.",
    "admin-setup-title": "முதல் நிர்வாகியை அமைக்கவும்",
    "admin-setup-note": "இந்தக் கணினியில் ஒருமுறை மட்டுமே. நிர்வாக மின்னஞ்சல் மற்றும் கடவுச்சொல்லை உருவாக்கிப் பாதுகாப்பாக வைத்துக்கொள்ளுங்கள்.",
    "admin-password": "நிர்வாகக் கடவுச்சொல் (16+ எழுத்துகள்)",
    "create-admin": "நிர்வாகியை உருவாக்கி டாஷ்போர்டைத் திறக்கவும்",
    "role-dashboard": "உங்கள் கணக்கு", "driver-ready": "GPS பகிர்வதற்கு முன், உங்கள் இயக்குநர் வாகனத்தைப் பதிவு செய்து உங்கள் கணக்கிற்கு ஒதுக்க வேண்டும்.",
    "driver-assigned": "ஒதுக்கப்பட்ட வாகனம்", "operator-fleet": "இயக்குநர் வாகனங்கள்", "add-vehicle": "வாகனத்தைப் பதிவு செய்க",
    "assign-driver": "பதிவு செய்யப்பட்ட மின்னஞ்சல் மூலம் ஓட்டுநரை ஒதுக்கவும்", "review-accounts": "பங்குதாரர் கணக்குகளை மதிப்பாய்வு செய்க",
    approve: "ஒப்புதல்", reject: "நிராகரி",
    "authority-info": "அதிகாரசபை பார்வை: வெளியிடப்பட்ட வழிகளையும் நேரலை வாகன நிலையையும் பார்க்கவும். இங்கு வழித் தரவு மாதிரி மட்டுமே.",
    "passenger-info": "பயணி கணக்கு செயலில் உள்ளது. பொதுச் நேரலை வரைபடத்தைப் பார்க்கலாம்.",
    "admin-info": "தள நிர்வாகி", "operator-info": "அங்கீகரிக்கப்பட்ட இயக்குநர் கணக்கில் வாகனங்களைப் பதிவு செய்யவும்.",
    routeLabel: "மாதிரி நிறுத்தங்கள்", meterAccuracy: "GPS துல்லியம் ±", mapCenter: "கொழும்பு, இலங்கை"
  }
};

const fallbackRoute = {
  id: "colombo-fort-pettah",
  name: "Colombo Fort – Pettah",
  nameSi: "කොළඹ කොටුව – පිටකොටුව",
  nameTa: "கொழும்பு கோட்டை – புறக்கோட்டை",
  demo: true,
  stops: [
    { name: "Colombo Fort", lat: 6.9344, lon: 79.8428 },
    { name: "Pettah", lat: 6.9388, lon: 79.85 }
  ]
};

const state = {
  language: localStorage.getItem("buslk-language") || "en",
  routes: [],
  vehicles: [],
  selectedRoute: null,
  map: null,
  routeLayer: null,
  vehicleMarkers: new Map(),
  watchId: null,
  sendingLocation: false,
  lastSentAt: 0,
  stream: null,
  user: null,
  csrfToken: null,
  driverVehicle: null
};

const $ = (selector) => document.querySelector(selector);
const translate = (key) => (translations[state.language] || translations.en)[key] || translations.en[key] || key;

function localize() {
  document.documentElement.lang = state.language;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    element.innerHTML = translate(key);
  });
  $("#language-select").value = state.language;
  $("#share-button").textContent = state.watchId === null ? translate("start-sharing") : translate("stop-sharing");
  renderDriverRouteOptions();
  renderRoutes();
  renderVehicles();
  drawRoutes();
}

function renderDriverRouteOptions() {
  const select = $("#driver-route");
  if (!select) return;
  const selectedRoute = state.routes.some((route) => route.id === select.value)
    ? select.value
    : state.selectedRoute;
  select.replaceChildren();
  state.routes.forEach((route) => {
    const option = document.createElement("option");
    option.value = route.id;
    option.textContent = routeName(route);
    select.append(option);
  });
  if (selectedRoute) select.value = selectedRoute;
}

function routeName(route) {
  return state.language === "si" ? route.nameSi : state.language === "ta" ? route.nameTa : route.name;
}

function renderRoutes() {
  $("#route-count").textContent = String(state.routes.length);
  const list = $("#route-list");
  list.replaceChildren();
  state.routes.forEach((route) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `route-card${state.selectedRoute === route.id ? " selected" : ""}`;
    button.setAttribute("aria-pressed", String(state.selectedRoute === route.id));
    const symbol = document.createElement("span");
    symbol.className = "route-symbol";
    symbol.textContent = "↗";
    const details = document.createElement("span");
    details.className = "route-details";
    const name = document.createElement("span");
    name.className = "route-name";
    name.textContent = routeName(route);
    const meta = document.createElement("span");
    meta.className = "route-meta";
    meta.textContent = `${translate("demo")} · ${route.stops.length} ${translate("routeLabel")}`;
    details.append(name, meta);
    const arrow = document.createElement("span");
    arrow.className = "route-arrow";
    arrow.textContent = "›";
    button.append(symbol, details, arrow);
    button.addEventListener("click", () => {
      state.selectedRoute = route.id;
      $("#driver-route").value = route.id;
      renderRoutes();
      renderVehicles();
      drawRoutes();
    });
    list.append(button);
  });
}

function renderVehicles() {
  const list = $("#vehicle-list");
  list.replaceChildren();
  const shownVehicles = state.vehicles.filter((vehicle) => !state.selectedRoute || vehicle.routeId === state.selectedRoute);
  $("#vehicle-count").textContent = String(shownVehicles.filter((vehicle) => vehicle.status === "live").length);
  $("#empty-state").hidden = shownVehicles.length > 0;
  if (!shownVehicles.length) {
    $("#empty-state").textContent = state.vehicles.length
      ? translate("no-vehicles")
      : translate("empty");
  }

  shownVehicles.forEach((vehicle) => {
    const route = state.routes.find((item) => item.id === vehicle.routeId);
    const item = document.createElement("li");
    item.className = "vehicle-row";
    const badge = document.createElement("span");
    badge.className = "vehicle-badge";
    badge.textContent = "▣";
    const info = document.createElement("span");
    info.className = "vehicle-info";
    const id = document.createElement("strong");
    id.textContent = vehicle.vehicleId;
    const details = document.createElement("small");
    details.textContent = route ? routeName(route) : vehicle.routeId;
    info.append(id, details);
    const age = document.createElement("span");
    age.className = `vehicle-age${vehicle.status === "stale" ? " stale" : ""}`;
    age.textContent = formatAge(vehicle.ageSeconds);
    item.append(badge, info, age);
    list.append(item);
  });

  if (!state.map) return;
  const visibleIds = new Set(shownVehicles.map((vehicle) => vehicle.vehicleId));
  for (const [id, marker] of state.vehicleMarkers) {
    if (!visibleIds.has(id)) {
      marker.remove();
      state.vehicleMarkers.delete(id);
    }
  }
  shownVehicles.forEach((vehicle) => {
    const marker = state.vehicleMarkers.get(vehicle.vehicleId);
    const icon = L.divIcon({
      className: "",
      html: `<span class="bus-marker${vehicle.status === "stale" ? " stale" : ""}" aria-label="${escapeAttribute(vehicle.vehicleId)}">▣</span>`,
      iconSize: [34, 34],
      iconAnchor: [17, 17]
    });
    const popup = `<strong>${escapeHtml(vehicle.vehicleId)}</strong><br>${escapeHtml(formatAge(vehicle.ageSeconds))}<br><span>${escapeHtml(translate("demo"))}</span>`;
    if (marker) {
      marker.setLatLng([vehicle.lat, vehicle.lon]).setIcon(icon).setPopupContent(popup);
    } else {
      const newMarker = L.marker([vehicle.lat, vehicle.lon], { icon }).bindPopup(popup).addTo(state.map);
      state.vehicleMarkers.set(vehicle.vehicleId, newMarker);
    }
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, "&#96;");
}

function formatAge(seconds) {
  if (seconds < 10) return translate("now");
  if (seconds < 60) return `${seconds}${translate("seconds")}`;
  return `${Math.floor(seconds / 60)} ${translate("minutes")}`;
}

function drawRoutes() {
  if (!state.map) return;
  if (state.routeLayer) state.routeLayer.remove();
  const route = state.routes.find((item) => item.id === state.selectedRoute);
  if (!route) return;
  const points = route.stops.map((stop) => [stop.lat, stop.lon]);
  state.routeLayer = L.layerGroup([
    L.polyline(points, { color: "#148052", weight: 5, opacity: 0.78, dashArray: "9 8" }),
    ...route.stops.map((stop) => L.circleMarker([stop.lat, stop.lon], {
      radius: 5, color: "#fff", weight: 2, fillColor: "#116a48", fillOpacity: 1
    }).bindTooltip(stop.name))
  ]).addTo(state.map);
  state.map.fitBounds(L.latLngBounds(points).pad(1.25), { maxZoom: 15 });
}

function initializeMap() {
  if (!window.L) {
    $("#map-error").hidden = false;
    $("#map-error").textContent = translate("leaflet");
    return;
  }
  state.map = L.map("map", { zoomControl: false }).setView([6.9365, 79.8464], 15);
  L.control.zoom({ position: "bottomright" }).addTo(state.map);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(state.map);
  state.map.on("tileerror", () => {
    $("#map-error").hidden = false;
    $("#map-error").textContent = translate("leaflet");
  });
  state.map.on("tileload", () => { $("#map-error").hidden = true; });
  drawRoutes();
}

async function apiRequest(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.method === "POST") {
    headers.set("Content-Type", "application/json");
    if (state.csrfToken) headers.set("X-CSRF-Token", state.csrfToken);
  }
  const response = await fetch(url, { ...options, headers, credentials: "same-origin" });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status}).`);
  return result;
}

function showAuthMessage(message, isError = false) {
  $("#auth-message").textContent = message;
  $("#auth-message").style.color = isError ? "#a4453e" : "";
}

function dashboardMessage(message) {
  const paragraph = document.createElement("p");
  paragraph.className = "privacy-note";
  paragraph.textContent = message;
  return paragraph;
}

async function renderOperatorDashboard(container) {
  container.append(dashboardMessage(translate("operator-info")));
  const form = document.createElement("form");
  form.className = "dashboard-form";
  const vehicleLabel = document.createElement("label");
  vehicleLabel.textContent = translate("bus-id");
  const vehicleInput = document.createElement("input");
  vehicleInput.name = "vehicleId";
  vehicleInput.maxLength = 32;
  vehicleInput.required = true;
  vehicleInput.placeholder = "e.g. WP-NA-1234";
  const routeLabel = document.createElement("label");
  routeLabel.textContent = translate("choose-route");
  const routeSelect = document.createElement("select");
  routeSelect.name = "routeId";
  state.routes.forEach((route) => {
    const option = document.createElement("option");
    option.value = route.id;
    option.textContent = routeName(route);
    routeSelect.append(option);
  });
  const submit = document.createElement("button");
  submit.type = "submit";
  submit.className = "share-button";
  submit.textContent = translate("add-vehicle");
  form.append(vehicleLabel, vehicleInput, routeLabel, routeSelect, submit);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await apiRequest("/api/operator/fleet", {
        method: "POST",
        body: JSON.stringify({ vehicleId: vehicleInput.value.trim(), routeId: routeSelect.value })
      });
      vehicleInput.value = "";
      showAuthMessage("Vehicle registered.");
      await renderRoleDashboard();
    } catch (error) {
      showAuthMessage(error.message, true);
    }
  });
  container.append(form);

  const response = await apiRequest("/api/operator/fleet");
  const heading = document.createElement("h3");
  heading.textContent = translate("operator-fleet");
  container.append(heading);
  if (!response.vehicles.length) {
    container.append(dashboardMessage("No vehicles registered yet."));
    return;
  }
  response.vehicles.forEach((vehicle) => {
    const card = document.createElement("div");
    card.className = "fleet-item";
    const title = document.createElement("strong");
    title.textContent = `${vehicle.vehicleId} · ${routeName(state.routes.find((route) => route.id === vehicle.routeId) || fallbackRoute)}`;
    const detail = document.createElement("small");
    detail.textContent = vehicle.driverEmail || "No driver assigned";
    card.append(title, detail);
    const assignForm = document.createElement("form");
    assignForm.className = "assign-form";
    const emailInput = document.createElement("input");
    emailInput.type = "email";
    emailInput.placeholder = translate("assign-driver");
    emailInput.required = true;
    const assignButton = document.createElement("button");
    assignButton.type = "submit";
    assignButton.textContent = "Assign";
    assignForm.append(emailInput, assignButton);
    assignForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await apiRequest(`/api/operator/fleet/${encodeURIComponent(vehicle.vehicleId)}/assign`, {
          method: "POST",
          body: JSON.stringify({ email: emailInput.value.trim() })
        });
        showAuthMessage("Driver assigned.");
        await renderRoleDashboard();
      } catch (error) {
        showAuthMessage(error.message, true);
      }
    });
    card.append(assignForm);
    container.append(card);
  });
}

async function renderRoleDashboard() {
  const container = $("#role-dashboard");
  container.replaceChildren();
  const user = state.user;
  if (!user) return;
  const heading = document.createElement("h3");
  heading.textContent = translate("role-dashboard");
  container.append(heading);
  if (user.role === "passenger") {
    container.append(dashboardMessage(translate("passenger-info")));
  } else if (user.role === "driver") {
    const result = await apiRequest("/api/driver/vehicle");
    state.driverVehicle = result.vehicle;
    $("#driver-panel").hidden = false;
    if (state.driverVehicle) {
      $("#vehicle-id").value = state.driverVehicle.vehicleId;
      $("#driver-route").value = state.driverVehicle.routeId;
      $("#driver-assignment").textContent = `${translate("driver-assigned")}: ${state.driverVehicle.vehicleId} · ${routeName(state.routes.find((route) => route.id === state.driverVehicle.routeId) || fallbackRoute)}`;
      $("#share-button").disabled = false;
    } else {
      $("#vehicle-id").value = "";
      $("#driver-assignment").textContent = translate("driver-ready");
      $("#share-button").disabled = true;
    }
  } else if (user.role === "operator") {
    await renderOperatorDashboard(container);
  } else if (user.role === "authority") {
    container.append(dashboardMessage(translate("authority-info")));
  } else if (user.role === "admin") {
    container.append(dashboardMessage("Manage approvals, accounts, and registered buses on your dedicated dashboard."));
  }
}

async function refreshAccount() {
  try {
    const result = await apiRequest("/api/auth/me");
    state.user = result.user;
    state.csrfToken = result.csrfToken || null;
    const signedIn = Boolean(state.user);
    $("#auth-forms").hidden = signedIn;
    $("#account-session").hidden = !signedIn;
    $("#auth-status").textContent = state.user
      ? `${state.user.role} · ${state.user.status}`
      : "Sign in or create an account";
    $("#account-identity").textContent = state.user
      ? `${state.user.name} · ${state.user.email}`
      : "";
    $("#admin-dashboard-link").hidden = !state.user || state.user.role !== "admin";
    $("#admin-setup").hidden = true;
    $("#driver-panel").hidden = !state.user || state.user.role !== "driver";
    if (state.user) await renderRoleDashboard();
    else {
      state.driverVehicle = null;
      try {
        const setupStatus = await apiRequest("/api/auth/setup-status");
        $("#admin-setup").hidden = !setupStatus.available;
      } catch (error) {
        $("#admin-setup").hidden = true;
        console.info("First-admin setup is not available from this device:", error.message);
      }
      if (state.watchId !== null) {
        navigator.geolocation.clearWatch(state.watchId);
        state.watchId = null;
      }
    }
  } catch (error) {
    console.error("Could not restore account session:", error);
    state.user = null;
    state.csrfToken = null;
    $("#auth-status").textContent = "Account service unavailable.";
    showAuthMessage(error.message, true);
  }
}

async function loadInitialData() {
  try {
    const [routeResponse, vehicleResponse] = await Promise.all([
      fetch("/api/routes"),
      fetch("/api/vehicles")
    ]);
    if (!routeResponse.ok || !vehicleResponse.ok) throw new Error("Server returned an error.");
    const routeData = await routeResponse.json();
    const vehicleData = await vehicleResponse.json();
    state.routes = routeData.routes;
    state.vehicles = vehicleData.vehicles;
  } catch (error) {
    console.error("Could not load bus tracker data:", error);
    state.routes = [fallbackRoute];
    state.vehicles = [];
    showDriverMessage(translate("apiError") + "The bus tracker server may be unavailable.");
  }
  state.selectedRoute = state.routes[0]?.id || null;
  initializeMap();
  localize();
  connectStream();
}

function connectStream() {
  if (!window.EventSource) return;
  state.stream = new EventSource("/api/stream");
  state.stream.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      state.vehicles = data.vehicles;
      renderVehicles();
    } catch (error) {
      console.error("Could not read a bus location update:", error);
    }
  };
  state.stream.onerror = () => {
    $(".network-status span:last-child").textContent = "Reconnecting…";
  };
  state.stream.onopen = () => {
    $(".network-status span:last-child").textContent = translate("connected");
  };
}

function showDriverMessage(message, isError = false) {
  const element = $("#driver-message");
  element.textContent = message;
  element.style.color = isError ? "#a4453e" : "";
}

function locationError(error) {
  const messages = {
    1: translate("denied"),
    2: translate("unavailable"),
    3: translate("timeout")
  };
  showDriverMessage(messages[error.code] || translate("unavailable"), true);
}

async function sendLocation(position) {
  const now = Date.now();
  if (state.sendingLocation || now - state.lastSentAt < 4_000) return;
  state.sendingLocation = true;
  state.lastSentAt = now;
  const payload = {
    vehicleId: $("#vehicle-id").value.trim(),
    routeId: $("#driver-route").value,
    lat: position.coords.latitude,
    lon: position.coords.longitude,
    accuracy: Math.round(position.coords.accuracy)
  };
  try {
    const result = await apiRequest("/api/locations", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    showDriverMessage(`${translate("sent")} ${translate("meterAccuracy")}${payload.accuracy} m`);
  } catch (error) {
    console.error("Could not send driver location:", error);
    showDriverMessage(translate("apiError") + error.message, true);
  } finally {
    state.sendingLocation = false;
  }
}

function toggleSharing() {
  if (state.watchId !== null) {
    navigator.geolocation.clearWatch(state.watchId);
    state.watchId = null;
    $("#share-button").textContent = translate("start-sharing");
    $("#share-button").classList.remove("stop");
    showDriverMessage(translate("stopped"));
    return;
  }
  if (!window.isSecureContext) {
    showDriverMessage(translate("secure"), true);
    return;
  }
  if (!navigator.geolocation) {
    showDriverMessage(translate("unavailable"), true);
    return;
  }
  if (!state.user || state.user.role !== "driver" || !state.driverVehicle) {
    showDriverMessage("Sign in as an assigned driver before sharing.", true);
    return;
  }
  if (!$("#vehicle-id").reportValidity()) return;
  if (!$("#vehicle-id").value.trim()) {
    showDriverMessage(translate("enter-id"), true);
    return;
  }
  $("#share-button").textContent = translate("stop-sharing");
  $("#share-button").classList.add("stop");
  showDriverMessage(translate("sending"));
  state.watchId = navigator.geolocation.watchPosition(sendLocation, locationError, {
    enableHighAccuracy: true,
    maximumAge: 5_000,
    timeout: 20_000
  });
  showDriverMessage(translate("sharing"));
}

$("#language-select").addEventListener("change", (event) => {
  state.language = event.target.value;
  localStorage.setItem("buslk-language", state.language);
  localize();
});

$("#share-button").addEventListener("click", toggleSharing);
$("#driver-route").addEventListener("change", (event) => {
  state.selectedRoute = event.target.value;
  renderRoutes();
  renderVehicles();
  drawRoutes();
});
$("#locate-button").addEventListener("click", () => {
  if (state.map) state.map.setView([6.9365, 79.8464], 15);
});

$("#register-role").addEventListener("change", (event) => {
  const needsOrganization = ["operator", "authority"].includes(event.target.value);
  $("#organization-field").hidden = !needsOrganization;
  $("#register-organization").required = needsOrganization;
});

$("#register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const payload = Object.fromEntries(data.entries());
  payload.consent = $("#register-consent").checked;
  try {
    const result = await apiRequest("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    const message = result.user.status === "pending"
      ? `${translate("pending")} ${result.user.email}`
      : "Account created. Sign in to continue.";
    showAuthMessage(message);
    form.reset();
    $("#organization-field").hidden = true;
    $("#register-organization").required = false;
  } catch (error) {
    showAuthMessage(error.message, true);
  }
});

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  try {
    const result = await apiRequest("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(data.entries()))
    });
    state.csrfToken = result.csrfToken;
    form.reset();
    showAuthMessage("");
    await refreshAccount();
  } catch (error) {
    showAuthMessage(error.message, true);
  }
});

$("#admin-setup-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  try {
    const result = await apiRequest("/api/auth/setup-admin", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(data.entries()))
    });
    state.csrfToken = result.csrfToken;
    await refreshAccount();
    showAuthMessage("Admin account created. You are signed in.");
  } catch (error) {
    showAuthMessage(error.message, true);
    await refreshAccount();
  }
});

$("#logout-button").addEventListener("click", async () => {
  try {
    await apiRequest("/api/auth/logout", { method: "POST", body: "{}" });
    if (state.watchId !== null) navigator.geolocation.clearWatch(state.watchId);
    state.watchId = null;
    state.driverVehicle = null;
    showAuthMessage("Signed out.");
    await refreshAccount();
  } catch (error) {
    showAuthMessage(error.message, true);
  }
});

window.addEventListener("pagehide", () => {
  if (state.watchId !== null) navigator.geolocation.clearWatch(state.watchId);
  if (state.stream) state.stream.close();
});

loadInitialData().then(refreshAccount);
