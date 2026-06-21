const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const twilio = require("twilio");
const app = express();
const port = process.env.PORT || 5000;

app.use(cors());
app.use(bodyParser.json());

// prefix everything with /api
const router = express.Router();
app.use("/api", router);

// in-memory storage
let users = [
  { id: 1, name: "Admin User", email: "admin@care.com", password: "admin123", role: "admin", plan: "admin", carecoins: 0, completed_tasks: 0, rating: 0 },
  { id: 2, name: "Test User", email: "test@example.com", password: "test", role: "elderly", phone: "+1234567890", plan: "free", carecoins: 0, completed_tasks: 0, rating: 0 },
];

const PLAN_CONFIG = {
  free:   { limit: 3, categories: ["Grocery", "Medical"] },
  premium:{ limit: 15, categories: ["Grocery", "Medical", "Tutoring", "Transport", "Companion", "Other"] },
  gold:   { limit: 9999, categories: ["Grocery", "Medical", "Tutoring", "Transport", "Companion", "Other"] },
};

function getPlanInfo(user) {
  const plan = (user && user.plan) ? user.plan : "free";
  return PLAN_CONFIG[plan] || PLAN_CONFIG.free;
}

function getUserByEmail(email) {
  return users.find(u => u.email === email);
}

function getUserById(id) {
  return users.find(u => u.id === id);
}

function awardCareCoins(userEmail, amount, description) {
  var user = getUserByEmail(userEmail);
  if (!user) return false;
  user.carecoins = (user.carecoins || 0) + amount;
  if (user.carecoins < 0) user.carecoins = 0;
  if (amount > 0) user.completed_tasks = (user.completed_tasks || 0) + 1;
  carecoinTransactions.push({
    id: nextCarecoinTxId++,
    userId: user.id,
    email: user.email,
    type: amount > 0 ? "earn" : "spend",
    amount: amount,
    description: description || (amount > 0 ? "Task completion" : "Redeem reward"),
    balance_after: user.carecoins,
    created_at: new Date().toISOString(),
  });
  return true;
}

function getCareCoinHistory(userEmail) {
  return carecoinTransactions
    .filter(tx => tx.email === userEmail)
    .sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));
}

function getLeaderboard() {
  return users
    .filter(u => u.role === "volunteer")
    .map(u => ({
      id: u.id,
      name: u.name,
      completed_tasks: u.completed_tasks || 0,
      rating: u.rating || 0,
      carecoins: u.carecoins || 0,
    }))
    .sort((a,b)=>b.carecoins - a.carecoins)
    .slice(0, 25)
    .map((u,i)=>({ ...u, rank: i + 1 }));
}

let requests = [];
let sosList = [];
let volunteers = [];
let carecoinTransactions = [];
let nextUserId = 3;
let nextReqId = 1;
let nextSosId = 1;
let nextCarecoinTxId = 1;
let wellnessLogs = [];
let nextWellnessId = 1;

const accountSid = process.env.TWILIO_ACCOUNT_SID || 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx';
const authToken = process.env.TWILIO_AUTH_TOKEN || 'your_auth_token';
const twilioNumber = process.env.TWILIO_NUMBER || '+1234567890';
const client = twilio(accountSid, authToken);

function makeToken(user) {
  return `token-${user.id}`;
}

function authMiddleware(req, res, next) {
  const auth = req.headers.authorization || "";
  const token = auth.replace("Bearer ", "");
  if (!token) return res.status(401).json({ msg: "No token provided" });
  const user = users.find(u => makeToken(u) === token);
  if (!user) return res.status(401).json({ msg: "Invalid token" });
  req.user = user;
  next();
}

router.post("/auth/login", (req, res) => {
  console.log("POST /auth/login", req.body);
  let { email, password } = req.body;
  if (typeof email === "string") email = email.trim().toLowerCase();
  const user = users.find(u =>
    typeof u.email === "string" &&
    u.email.trim().toLowerCase() === email &&
    u.password === password
  );
  console.log("found user", user);
  if (!user) return res.status(401).json({ msg: "Invalid credentials" });
  const token = makeToken(user);
  res.json({ ...user, token });
});

router.post("/auth/register", (req, res) => {
  let { name, email, password, phone, location, role } = req.body;
  if (typeof email === "string") email = email.trim().toLowerCase();
  if (users.find(u => typeof u.email === "string" && u.email.trim().toLowerCase() === email)) {
    return res.status(400).json({ msg: "Email already exists" });
  }
  const newUser = { id: nextUserId++, name, email, password, phone, location, role, plan: "free", carecoins: 0, completed_tasks: 0, rating: 0 };
  users.push(newUser);
  // if the user registered as a volunteer, add to the volunteer list
  if (role === "volunteer") {
    volunteers.push({ id: newUser.id, name: newUser.name, email: newUser.email, phone: phone || "" });
  }
  const token = makeToken(newUser);
  res.json({ ...newUser, token });
});

router.get("/auth/me", authMiddleware, (req, res) => {
  res.json(req.user);
});

router.post("/admin/login", (req, res) => {
  let { email, password } = req.body;
  if (typeof email === "string") email = email.trim().toLowerCase();
  const user = users.find(u =>
    typeof u.email === "string" &&
    u.email.trim().toLowerCase() === email &&
    u.password === password &&
    u.role === "admin"
  );
  if (!user) return res.status(401).json({ msg: "Invalid credentials" });
  const token = makeToken(user);
  res.json({ ...user, token });
});

// admin endpoints - require auth and admin role
function adminOnly(req, res, next) {
  authMiddleware(req, res, () => {
    if (req.user.role !== "admin") return res.status(403).json({ msg: "Admins only" });
    next();
  });
}

router.get("/admin/stats", adminOnly, (req, res) => {
  res.json({
    total_requests: requests.length,
    open: requests.filter(r => r.status === "open").length,
    in_progress: requests.filter(r => r.status === "in-progress").length,
    delivered: requests.filter(r => r.status === "delivered").length,
    completed: requests.filter(r => r.status === "completed").length,
    active_sos: sosList.filter(s => s.status === "active").length,
    total_volunteers: volunteers.length,
    total_users: users.filter(u => u.role !== "admin").length,
  });
});

router.get("/admin/users", adminOnly, (req, res) => {
  res.json(users.filter(u => u.role !== "admin"));
});

router.get("/admin/volunteers", adminOnly, (req, res) => {
  res.json(volunteers);
});

router.get("/admin/requests", adminOnly, (req, res) => {
  res.json(requests);
});

router.get("/admin/sos", adminOnly, (req, res) => {
  res.json(sosList);
});

router.put("/admin/sos/resolve/:id", adminOnly, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const sos = sosList.find(s => s.id === id);
  if (sos) sos.status = "resolved";
  res.json({});
});

// public endpoints
router.post("/requests", authMiddleware, (req, res) => {
  try {
    console.log("POST /api/requests", req.body, req.user);
    const { title, category, urgency, description, latitude, longitude, source } = req.body;
    if (!title || !category || !description) {
      return res.status(400).json({ msg: "Missing required fields" });
    }
    const r = {
      id: nextReqId++,
      title,
      category,
      urgency,
      description,
      latitude,
      longitude,
      status: "open",
      source: source || "user",
      requester_name: req.user.name,
      requester_email: req.user.email,
      requester_phone: req.user.phone || "",
      requester_loc: req.user.location || "",
      volunteer_email: null,
      volunteer_name: null,
      created_at: new Date().toISOString(),
    };
    requests.push(r);
    res.json(r);
  } catch (e) {
    console.error("Error in /api/requests", e);
    res.status(500).json({ msg: "Internal server error" });
  }
});

router.post("/sos/trigger", authMiddleware, (req, res) => {
  const { lat, lng, message } = req.body;
  const s = {
    id: nextSosId++,
    lat,
    lng,
    message,
    status: "active",
    user: req.user.email,
    user_name: req.user.name || "Unknown User",
    user_phone: req.user.phone || "",
    created_at: new Date().toISOString(),
  };
  sosList.push(s);
  res.json(s);
});

// miscellaneous endpoints for user dashboard
router.get("/requests/", authMiddleware, (req, res) => {
  const own = requests.filter(r => r.requester_email === req.user.email);
  res.json(own);
});

router.get("/requests/history", authMiddleware, (req, res) => {
  const hist = requests.filter(r =>
    r.requester_email === req.user.email || r.volunteer_email === req.user.email
  ).map(r => ({
    ...r,
    requester: r.requester_name || r.requester || r.requester_email || "Unknown User",
    requester_phone: r.requester_phone || "",
    requester_loc: r.requester_loc || "",
  }));
  res.json(hist);
});

router.get("/requests/notifications/unread", authMiddleware, (req, res) => {
  res.json({ count: 0 });
});

router.get("/requests/notifications", authMiddleware, (req, res) => {
  res.json([]);
});

router.put("/requests/confirm/:id", authMiddleware, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const r = requests.find(r => r.id === id);
  if (r && r.requester_email === req.user.email) {
    r.status = "in-progress";
  }
  res.json({});
});

router.put("/requests/rate/:id", authMiddleware, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const r = requests.find(r => r.id === id);
  if (!r) return res.status(404).json({ msg: "Request not found" });

  const rating = Number(req.body.rating || 0);
  const carecoins = Number(req.body.carecoins || 0);

  r.rating = rating;
  r.carecoins = carecoins;
  r.rated_at = new Date().toISOString();

  if (r.volunteer_email && carecoins > 0) {
    awardCareCoins(r.volunteer_email, carecoins, "Rated reward from request #" + id);
  }

  res.json({ msg: "Rating saved", rating: rating, carecoins: carecoins });
});

router.get("/volunteer/requests", authMiddleware, (req, res) => {
  const open = requests.filter(r =>
    r.status === "open"
  ).map(r => ({
    ...r,
    requester: r.requester_name || r.requester || r.requester_email || "Unknown User",
    requester_phone: r.requester_phone || r.phone || "",
    requester_loc: r.requester_loc || r.requester_loc || r.location || (r.latitude && r.longitude ? "GPS " + r.latitude + ", " + r.longitude : ""),
    latitude: r.latitude || r.lat || null,
    longitude: r.longitude || r.lng || null,
  }));
  res.json(open);
});

router.get("/volunteer/my-tasks", authMiddleware, (req, res) => {
  const my = requests.filter(r => r.volunteer_email === req.user.email).map(r => ({
    ...r,
    requester: r.requester_name || r.requester || r.requester_email || "Unknown User",
    requester_phone: r.requester_phone || r.phone || "",
    requester_loc: r.requester_loc || r.requester_loc || r.location || (r.latitude && r.longitude ? "GPS " + r.latitude + ", " + r.longitude : ""),
    latitude: r.latitude || r.lat || null,
    longitude: r.longitude || r.lng || null,
  }));
  res.json(my);
});

router.get("/volunteer/sos", authMiddleware, (req, res) => {
  res.json(sosList);
});

router.get("/volunteer/performance", authMiddleware, (req, res) => {
  const user = req.user;
  const accepted = requests.filter(r => r.volunteer_email === user.email && (r.status === "in-progress" || r.status === "completed" || r.status === "delivered")).length;
  const completed = requests.filter(r => r.volunteer_email === user.email && (r.status === "completed" || r.status === "delivered")).length;
  res.json({
    accepted: accepted,
    completed_tasks: completed,
    carecoins: user.carecoins || 0,
    rating: user.rating || 0,
  });
});

router.get("/carecoins/balance", authMiddleware, (req, res) => {
  const user = req.user;
  res.json({
    balance: user.carecoins || 0,
    completed_tasks: user.completed_tasks || 0,
    rating: user.rating || 0,
  });
});

router.get("/carecoins/history", authMiddleware, (req, res) => {
  res.json(getCareCoinHistory(req.user.email));
});

router.get("/carecoins/rewards", authMiddleware, (req, res) => {
  res.json([
    { id: 1, icon: "🎟️", category: "Voucher", title: "₹100 Grocery Voucher", description: "Redeem for ₹100 off at partner grocery stores.", cost: 30 },
    { id: 2, icon: "⚡", category: "Service", title: "Priority Request Token", description: "Move your next request to the top of volunteer queue.", cost: 15 },
    { id: 3, icon: "🏅", category: "Subscription", title: "1-Month Premium Upgrade", description: "Unlock all categories and 20+ features for 1 month.", cost: 50 },
    { id: 4, icon: "🤖", category: "AI", title: "AI Wellness Check Session", description: "One free AI-powered voice wellness check call.", cost: 10 },
    { id: 5, icon: "💖", category: "Donation", title: "Donate to Community Fund", description: "Support elders who need assistance with no chess.", cost: 5 },
  ]);
});

router.post("/carecoins/redeem", authMiddleware, (req, res) => {
  const user = req.user;
  const { reward_id } = req.body;
  const rewards = [
    { id: 1, cost: 30, title: "₹100 Grocery Voucher" },
    { id: 2, cost: 15, title: "Priority Request Token" },
    { id: 3, cost: 50, title: "1-Month Premium Upgrade" },
    { id: 4, cost: 10, title: "AI Wellness Check Session" },
    { id: 5, cost: 5, title: "Donate to Community Fund" },
  ];
  const reward = rewards.find(r => r.id === Number(reward_id));
  if (!reward) {
    return res.status(400).json({ msg: "Invalid reward" });
  }
  if ((user.carecoins || 0) < reward.cost) {
    return res.status(400).json({ msg: "Insufficient CareCoins" });
  }
  awardCareCoins(user.email, -reward.cost, "Redeemed: " + reward.title);
  res.json({ msg: "Redeemed " + reward.title + " successfully.", new_balance: user.carecoins || 0 });
});

router.get("/volunteer/profile", authMiddleware, (req, res) => {
  res.json(req.user);
});

router.get("/volunteer/notifications/unread", authMiddleware, (req, res) => {
  res.json({ count: 0 });
});

router.put("/volunteer/accept/:id", authMiddleware, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const r = requests.find(r => r.id === id);
  if (r && r.status === "open") {
    r.volunteer_email = req.user.email;
    r.volunteer_name = req.user.name;

    if (r.source === "wellness" || r.source === "twilio") {
      r.status = "completed";
      r.completed_at = new Date().toISOString();
      awardCareCoins(req.user.email, 1, "Completed wellness/twilio task");
    } else {
      r.status = "in-progress";
      // award on acceptance in demo workflow
      awardCareCoins(req.user.email, 1, "Accepted task");
    }
  }
  res.json({});
});

router.get("/volunteer/notifications", authMiddleware, (req, res) => {
  res.json([]);
});

router.put("/volunteer/reject/:id", authMiddleware, (req, res) => {
  // simply leave it open
  res.json({});
});

router.put("/volunteer/delivered/:id", authMiddleware, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const r = requests.find(r => r.id === id);
  if (r && r.volunteer_email === req.user.email && r.status === "in-progress") {
    r.status = "delivered";
  }
  res.json({});
});

router.get("/subscription/my", authMiddleware, (req, res) => {
  const plan = req.user.plan || "free";
  const config = getPlanInfo(req.user);
  res.json({ plan, features: { requests_per_month: config.limit, categories: config.categories } });
});

router.post("/subscription/upgrade", authMiddleware, (req, res) => {
  const { plan } = req.body;
  if (!PLAN_CONFIG[plan]) {
    return res.status(400).json({ msg: "Invalid plan" });
  }
  req.user.plan = plan;
  const config = getPlanInfo(req.user);
  res.json({ plan, features: { requests_per_month: config.limit, categories: config.categories } });
});

router.get("/subscription/check/request", authMiddleware, (req, res) => {
  const planInfo = getPlanInfo(req.user);
  const now = new Date();
  const used = requests.filter(r =>
    r.requester_email === req.user.email &&
    new Date(r.created_at || r.timestamp || Date.now()).getFullYear() === now.getFullYear() &&
    new Date(r.created_at || r.timestamp || Date.now()).getMonth() === now.getMonth()
  ).length;
  const allowed = used < planInfo.limit;
  res.json({ plan: req.user.plan || "free", limit: planInfo.limit, used, allowed, categories: planInfo.categories });
});

router.get("/volunteer/count", authMiddleware, (req, res) => {
  res.json({ count: volunteers.length });
});

// Wellness Check Routes
router.get("/wellness/logs", authMiddleware, (req, res) => {
  const userLogs = wellnessLogs.filter(log => log.userId === req.user.id);
  res.json(userLogs);
});

router.get("/wellness/stats", authMiddleware, (req, res) => {
  const userLogs = wellnessLogs.filter(log => log.userId === req.user.id);
  const total = userLogs.length;
  const distress = userLogs.filter(log => log.sentiment === 'distress').length;
  const positive = userLogs.filter(log => log.sentiment === 'positive').length;
  res.json({ total, distress, positive });
});

router.post("/wellness/check", authMiddleware, (req, res) => {
  try {
    // Validate user exists
    if (!req.user || !req.user.id) {
      return res.status(400).json({ msg: "User not found" });
    }

    // Simulate speech analysis
    const mockTranscription = "I am feeling a bit dizzy today"; // placeholder
    const sentiment = analyzeSentiment(mockTranscription);
    const isDistress = sentiment === 'distress';

    // Create wellness log
    wellnessLogs.push({
      id: nextWellnessId++,
      userId: req.user.id,
      type: 'completed',
      timestamp: new Date().toISOString(),
      transcription: mockTranscription,
      sentiment: sentiment,
      callSid: 'simulated-' + Date.now()
    });

    // Create a Twilio call request
    const twilioRequest = {
      id: nextReqId++,
      title: '📞 Twilio Voice Call Request',
      category: 'Medical',
      urgency: 'high',
      description: `User initiated wellness check via Twilio. Transcription: "${mockTranscription}"`,
      status: 'open',
      source: 'twilio',
      requester_name: req.user.name || 'Unknown User',
      requester_email: req.user.email || '',
      requester_phone: req.user.phone || '',
      requester_loc: req.body.location || req.user.location || '',
      latitude: req.body.latitude || req.user.latitude || null,
      longitude: req.body.longitude || req.user.longitude || null,
      volunteer_email: null,
      volunteer_name: null,
      created_at: new Date().toISOString(),
    };
    requests.push(twilioRequest);

    // Create distress alert if needed
    if (isDistress) {
      const distressRequest = {
        id: nextReqId++,
        title: '🤖 AI Wellness Distress Alert',
        category: 'Medical',
        urgency: 'critical',
        description: `AI Wellness Check detected distress: "${mockTranscription}"`,
        status: 'open',
        source: 'wellness',
        requester_name: req.user.name || 'Unknown User',
        requester_email: req.user.email || '',
        requester_phone: req.user.phone || '',
        requester_loc: req.body.location || req.user.location || '',
        latitude: req.body.latitude || req.user.latitude || null,
        longitude: req.body.longitude || req.user.longitude || null,
        volunteer_email: null,
        volunteer_name: null,
        created_at: new Date().toISOString(),
      };
      requests.push(distressRequest);
    }

    // Send success response
    res.json({ 
      msg: "✅ Wellness call completed successfully! Twilio call request created and sent to volunteers.",
      requestsCreated: isDistress ? 2 : 1,
      sentiment: sentiment
    });

  } catch (error) {
    console.error("Error in /wellness/check:", error);
    res.status(500).json({ msg: "Failed to process wellness check. Please try again." });
  }
});

router.post("/wellness/process-voice", (req, res) => {
  const recordingUrl = req.body.RecordingUrl;
  const callSid = req.body.CallSid;

  // For demo, simulate speech analysis
  // In real implementation, use speech-to-text API
  const mockTranscription = "I am feeling good today"; // placeholder
  const sentiment = analyzeSentiment(mockTranscription);

  // Find the log and update
  const logIndex = wellnessLogs.findIndex(log => log.callSid === callSid);
  if (logIndex !== -1) {
    wellnessLogs[logIndex].transcription = mockTranscription;
    wellnessLogs[logIndex].sentiment = sentiment;
    wellnessLogs[logIndex].type = 'completed';
  } else {
    wellnessLogs.push({
      id: nextWellnessId++,
      userId: null, // would need to map from callSid
      type: 'completed',
      timestamp: new Date().toISOString(),
      transcription: mockTranscription,
      sentiment: sentiment,
      callSid: callSid
    });
  }

  // If distress, create a request
  if (sentiment === 'distress') {
    const distressKeywords = ['pain', 'dizzy', 'help', 'sick'];
    const hasKeyword = distressKeywords.some(kw => mockTranscription.toLowerCase().includes(kw));
    if (hasKeyword) {
      requests.push({
        id: nextReqId++,
        userId: null, // placeholder
        category: 'Medical',
        description: `AI Wellness Check detected distress: "${mockTranscription}"`,
        status: 'open',
        timestamp: new Date().toISOString(),
        location: 'Auto-detected'
      });
    }
  }

  res.send('<Response><Say>Thank you for your response. Your wellness check is complete.</Say></Response>');
});

function analyzeSentiment(text) {
  const distressWords = ['pain', 'dizzy', 'sick', 'hurt', 'bad', 'help'];
  const positiveWords = ['good', 'fine', 'well', 'great', 'happy'];

  const lowerText = text.toLowerCase();
  const hasDistress = distressWords.some(word => lowerText.includes(word));
  const hasPositive = positiveWords.some(word => lowerText.includes(word));

  if (hasDistress) return 'distress';
  if (hasPositive) return 'positive';
  return 'neutral';
}

router.post("/wellness/simulate", authMiddleware, (req, res) => {
  const { speech } = req.body;
  const sentiment = analyzeSentiment(speech);

  wellnessLogs.push({
    id: nextWellnessId++,
    userId: req.user.id,
    type: 'simulation',
    timestamp: new Date().toISOString(),
    transcription: speech,
    sentiment: sentiment
  });

  res.json({
    transcription: speech,
    sentiment: sentiment,
    action: sentiment === 'distress' ? 'High-priority request created' : 'No action needed'
  });
});

app.listen(port, () => {
  console.log(`Mock API server listening on port ${port}`);
  console.log('Available users:', users.map(u=>u.email).join(', '));
});
