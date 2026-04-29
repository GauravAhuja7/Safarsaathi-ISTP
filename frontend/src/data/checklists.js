export const PRE_TRIP = [
  {
    id: "weather",
    en: "Check today's weather before leaving",
    hi: "निकलने से पहले आज का मौसम जांचें",
    detail: "Use SafarSathi or call a local on the route",
    audio: "audio/checklist_weather.mp3",
  },
  {
    id: "road",
    en: "Verify road is open — call a local contact",
    hi: "रास्ता खुला है या नहीं — किसी स्थानीय को कॉल करें",
    detail: "For Parashar: call Baggi Dhaba. For Barot: call Ghatasani taxi stand.",
    audio: "audio/checklist_road.mp3",
  },
  {
    id: "tell_someone",
    en: "Tell someone your route and expected return time",
    hi: "किसी को अपना रास्ता और वापसी का समय बताएं",
    detail: "If you don't return on time, they should call 100",
    audio: "audio/checklist_tell.mp3",
  },
  {
    id: "water",
    en: "Carry at least 2 litres of water per person",
    hi: "प्रत्येक व्यक्ति के लिए कम से कम 2 लीटर पानी ले जाएं",
    detail: "Mountain routes may have no shops for 30-40 km",
    audio: "audio/checklist_water.mp3",
  },
  {
    id: "warm",
    en: "Pack a warm layer even in summer",
    hi: "गर्मियों में भी गर्म कपड़े रखें",
    detail: "Parashar is at 2,730m — temperature drops sharply after sunset",
    audio: "audio/checklist_warm.mp3",
  },
  {
    id: "fuel",
    en: "Fill fuel before leaving Mandi town",
    hi: "मंडी शहर से निकलने से पहले पेट्रोल भरवाएं",
    detail: "No petrol pumps on Parashar or Barot routes after Mandi",
    audio: "audio/checklist_fuel.mp3",
  },
  {
    id: "phone",
    en: "Save emergency numbers offline before leaving",
    hi: "निकलने से पहले इमर्जेंसी नंबर ऑफ़लाइन सेव करें",
    detail: "108 Ambulance, 100 Police, 01905-226201 District Control Room",
    audio: "audio/checklist_phone.mp3",
  },
  {
    id: "daylight",
    en: "Plan to return before dark — no mountain driving at night",
    hi: "अंधेरे से पहले वापस आने की योजना बनाएं — रात को पहाड़ पर गाड़ी न चलाएं",
    detail: "Night adds +2 to risk score on all mountain routes",
    audio: "audio/checklist_daylight.mp3",
  },
];

export const ALTITUDE = [
  {
    id: "hydrate",
    en: "Drink 4–6 litres of water daily starting the day before",
    hi: "एक दिन पहले से रोज़ 4-6 लीटर पानी पिएं",
    audio: "audio/alt_hydrate.mp3",
  },
  {
    id: "no_alcohol",
    en: "No alcohol for first 24 hours at altitude",
    hi: "ऊंचाई पर पहले 24 घंटे शराब न पिएं",
    audio: "audio/alt_alcohol.mp3",
  },
  {
    id: "slow",
    en: "Move slowly — don't exert yourself for the first hour",
    hi: "धीरे चलें — पहले घंटे में कोई भारी काम न करें",
    audio: "audio/alt_slow.mp3",
  },
  {
    id: "diamox",
    en: "Carry Diamox (125mg) if going above 2,500m — consult doctor first",
    hi: "2,500m से ऊपर जाने पर Diamox (125mg) साथ रखें — पहले डॉक्टर से पूछें",
    audio: "audio/alt_diamox.mp3",
  },
];

export const AMS_MILD = [
  {
    id: "headache",
    en: "Headache",
    hi: "सिरदर्द",
    action: "Rest, drink water, do not go higher",
    actionHi: "आराम करें, पानी पिएं, और ऊपर न जाएं",
  },
  {
    id: "nausea",
    en: "Nausea or dizziness",
    hi: "मतली या चक्कर",
    action: "Rest. If it doesn't improve in 1 hour, descend",
    actionHi: "आराम करें। 1 घंटे में ठीक न हो तो नीचे उतरें",
  },
  {
    id: "breathless",
    en: "Breathlessness at rest",
    hi: "आराम में भी सांस फूलना",
    action: "Stop all activity. Monitor closely",
    actionHi: "सारा काम रोकें। ध्यान से देखते रहें",
  },
];

export const AMS_EMERGENCY = [
  { en: "Confusion or cannot think clearly", hi: "भ्रम या साफ सोच न पाना" },
  { en: "Cannot walk straight", hi: "सीधे न चल पाना" },
  { en: "Blue or grey lips / fingernails", hi: "नीले या भूरे होंठ / नाखून" },
  { en: "Coughing pink or bloody sputum", hi: "गुलाबी या खून वाली खांसी" },
  { en: "Severe headache that won't go away", hi: "बहुत तेज़ सिरदर्द जो नहीं जाता" },
];
