const messagesEl = document.getElementById("messages");
const emptyStateEl = document.getElementById("empty-state");
const composerEl = document.getElementById("composer");
const chatPageEl = document.querySelector(".chat-page");
const inputEl = document.getElementById("message-input");
const sendButtonEl = document.getElementById("send-button");
const voiceSelectEl = document.getElementById("voice-select");
const voiceModeEl = document.getElementById("voice-mode");
const sidebarEl = document.getElementById("sidebar");
const sidebarToggleEl = document.getElementById("sidebar-toggle");

const voiceInputButtonEl = document.getElementById("voice-input-button");
const waveformOverlayEl = document.getElementById("waveform-overlay");
const recordingTimerEl = document.getElementById("recording-timer");

let busy = false;
let voiceMode = false;
let chatHistory = [];
const sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);

// Voice recording variables
let mediaRecorder = null;
let audioChunks = [];
let recordingTimerInterval = null;
let recordingSeconds = 0;
let isRecording = false;

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function activateConversation() {
  if (chatPageEl.classList.contains("empty")) {
    chatPageEl.classList.remove("empty");
    messagesEl.classList.remove("empty");
    emptyStateEl?.remove();
  }
}

function renderSlackCard(escalationData, messageEl) {
  const payload = escalationData.slack_payload || {};
  const status = escalationData.status || "mock_sent";
  const isReal = status === "slack_sent";
  
  const card = document.createElement("div");
  card.className = "slack-card";
  
  const header = document.createElement("div");
  header.className = "slack-card-header";
  header.innerHTML = `
      <div class="slack-logo-container">
          <i data-lucide="slack"></i>
          <span>SLACK HANDOFF ESCALATION</span>
      </div>
      <span class="slack-badge ${isReal ? 'real' : 'mock'}">${isReal ? 'Posted to Slack' : 'Mock Dispatched'}</span>
  `;
  
  const body = document.createElement("div");
  body.className = "slack-card-body";
  body.innerHTML = `Escalated to support channel <strong>${payload.channel || '#disputes'}</strong> via Mafita SlackBot.`;
  
  const fields = document.createElement("div");
  fields.className = "slack-card-fields";
  fields.innerHTML = `
      <div class="slack-field">
          <span class="slack-field-label">Ticket ID</span>
          <span class="slack-field-value">${payload.ticket_id || 'N/A'}</span>
      </div>
      <div class="slack-field">
          <span class="slack-field-label">Category</span>
          <span class="slack-field-value">${(payload.category || 'N/A').replace('_', ' ').toUpperCase()}</span>
      </div>
      <div class="slack-field">
          <span class="slack-field-label">Priority</span>
          <span class="slack-field-value" style="color: ${payload.priority === 'urgent' ? '#ef4444' : '#f59e0b'}">${(payload.priority || 'N/A').toUpperCase()}</span>
      </div>
      <div class="slack-field">
          <span class="slack-field-label">Customer ID</span>
          <span class="slack-field-value">${payload.customer_id || 'N/A'}</span>
      </div>
  `;
  if (payload.customer_phone) {
    fields.innerHTML += `
        <div class="slack-field">
            <span class="slack-field-label">Phone</span>
            <span class="slack-field-value">${payload.customer_phone}</span>
        </div>
    `;
  }
  if (payload.transaction_id) {
    fields.innerHTML += `
        <div class="slack-field">
            <span class="slack-field-label">Transaction ID</span>
            <span class="slack-field-value">${payload.transaction_id}</span>
        </div>
    `;
  }
  
  card.appendChild(header);
  card.appendChild(body);
  card.appendChild(fields);
  
  const textContainer = messageEl.querySelector(".message-text");
  if (textContainer) {
    textContainer.appendChild(card);
  }
  
  window.refreshIcons?.();
}

function renderTranscription(container, text) {
  container.innerHTML = "";
  // Split by whitespace tokens so we preserve spaces between spans
  const tokens = text.split(/(\s+)/);
  let wordIdx = 0;
  
  tokens.forEach(token => {
    if (token.trim().length === 0) {
      container.appendChild(document.createTextNode(token));
    } else {
      const span = document.createElement("span");
      span.className = "transcription-word";
      span.textContent = token;
      span.setAttribute("data-word-idx", wordIdx);
      container.appendChild(span);
      wordIdx++;
    }
  });
}

function syncTranscriptionWords(wrapper, audio) {
  if (!audio.duration || isNaN(audio.duration)) return;
  
  const wordSpans = wrapper.querySelectorAll(".transcription-word");
  if (wordSpans.length === 0) return;
  
  let totalChars = 0;
  const wordLengths = Array.from(wordSpans).map(span => {
    const len = span.textContent.length;
    totalChars += len;
    return len;
  });
  
  if (totalChars === 0) return;
  
  let cumulativeTime = 0;
  const duration = audio.duration;
  const currentTime = audio.currentTime;
  
  wordSpans.forEach((span, idx) => {
    const wordLen = wordLengths[idx];
    const wordDuration = (wordLen / totalChars) * duration;
    const wordStart = cumulativeTime;
    const wordEnd = cumulativeTime + wordDuration;
    cumulativeTime = wordEnd;
    
    if (currentTime >= wordStart && currentTime <= wordEnd) {
      span.className = "transcription-word word-current";
    } else if (currentTime > wordEnd) {
      span.className = "transcription-word word-active";
    } else {
      span.className = "transcription-word";
    }
  });
}

function setAllWordsActive(wrapper) {
  const wordSpans = wrapper.querySelectorAll(".transcription-word");
  wordSpans.forEach(span => {
    span.className = "transcription-word word-active";
  });
}

function animateWordsWithoutAudio(wrapper) {
  const wordSpans = wrapper.querySelectorAll(".transcription-word");
  if (wordSpans.length === 0) return;
  // Reset all words to greyed out
  wordSpans.forEach(span => {
    span.className = "transcription-word";
  });
  const msPerWord = Math.max(30, Math.min(60, 2500 / wordSpans.length));
  let idx = 0;
  const interval = setInterval(() => {
    if (idx > 0) {
      wordSpans[idx - 1].className = "transcription-word word-active";
    }
    if (idx < wordSpans.length) {
      wordSpans[idx].className = "transcription-word word-current";
      idx++;
      scrollToBottom();
    } else {
      clearInterval(interval);
    }
  }, msPerWord);
}

function createMessage(role, text, options = {}) {
  activateConversation();
  const wrapper = document.createElement("article");
  wrapper.className = `message ${role}`;

  const content = document.createElement("div");
  content.className = "message-text";
  const copy = document.createElement("span");
  copy.className = "message-copy";
  
  if (role === "assistant" && !options.typing) {
    renderTranscription(copy, text);
  } else {
    copy.textContent = text;
  }
  
  content.appendChild(copy);
  if (options.typing) content.classList.add("typing");

  wrapper.appendChild(content);

  if (role === "assistant" && !options.typing) {
    const tools = document.createElement("div");
    tools.className = "message-tools";

    const listen = document.createElement("button");
    listen.type = "button";
    listen.className = "listen-button";
    listen.innerHTML = '<i data-lucide="play"></i><span>Listen</span>';
    
    const note = document.createElement("span");
    note.className = "tts-note";
    note.style.display = "none";

    tools.appendChild(listen);
    tools.appendChild(note);
    content.appendChild(tools);
    
    listen.addEventListener("click", () => playMessageAudio(text, listen, wrapper, options.audio || null));

    // Automatically trigger audio playback, or animate words if TTS is known broken
    const preAudio = options.audio || null;
    if (preAudio && preAudio.error && !preAudio.audio_url) {
      // TTS failed server-side — skip audio, animate words instead
      window.setTimeout(() => animateWordsWithoutAudio(wrapper), 100);
    } else {
      window.setTimeout(() => playMessageAudio(text, listen, wrapper, preAudio), 100);
    }
  }

  messagesEl.appendChild(wrapper);
  scrollToBottom();
  window.refreshIcons?.();
  return wrapper;
}

function createThinkingMessage(steps = []) {
  activateConversation();
  const wrapper = document.createElement("div");
  wrapper.className = "thinking-indicator";

  wrapper.innerHTML = '<span class="thinking-dot"></span><span class="thinking-label">Thinking</span>';

  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

function removeMessage(node) {
  if (node && node.parentNode) node.parentNode.removeChild(node);
}

function setBusy(value) {
  busy = value;
  inputEl.disabled = value;
  sendButtonEl.disabled = value;
  updateSendState();
}

function resizeInput() {
  inputEl.style.height = "auto";
  inputEl.style.height = `${Math.min(inputEl.scrollHeight, 180)}px`;
}

function updateSendState() {
  sendButtonEl.classList.toggle("ready", inputEl.value.trim().length > 0 && !busy);
}

async function sendMessage(text) {
  const message = text.trim();
  if (!message || busy) return;

  createMessage("user", message);
  chatHistory.push({ role: "user", content: message });
  inputEl.value = "";
  resizeInput();
  setBusy(true);

  const typing = createThinkingMessage(["Kika ifiranṣẹ rẹ", "Ṣiṣayẹwo pẹlu Mafita backend..."]);
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: message, history: chatHistory, voice: voiceSelectEl.value, session_id: sessionId }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Something went wrong");
    removeMessage(typing);
    const msgWrapper = createMessage("assistant", result.reply, { audio: result.audio || null });
    chatHistory.push({ role: "assistant", content: result.reply });
    
    // Slack escalation handoff card detection
    const toolResults = result.plan_context?.execution?.tool_results || [];
    const escalationResult = toolResults.find(r => r.tool === "escalate_to_human");
    if (escalationResult && escalationResult.result) {
      renderSlackCard(escalationResult.result, msgWrapper);
    }
  } catch (error) {
    removeMessage(typing);
    createMessage("assistant", `Something went wrong. ${error.message}`);
  } finally {
    setBusy(false);
    inputEl.focus();
  }
}

async function playMessageAudio(text, button, wrapper, preloadedAudio = null) {
  const existingAudio = wrapper._audio;
  if (existingAudio && !existingAudio.paused) {
    existingAudio.pause();
    button.innerHTML = '<i data-lucide="play"></i><span>Listen</span>';
    window.refreshIcons?.();
    return;
  }

  button.disabled = true;
  button.innerHTML = '<span>...</span><span>Loading</span>';
  const note = wrapper.querySelector(".tts-note");
  if (note) note.textContent = preloadedAudio?.audio_url ? "Mura ohùn..." : "A n pèsè ohùn...";

  try {
    let result = preloadedAudio;
    if (result?.error || result?.fallback) {
      throw new Error(result.error || result.warning || "Ohùn ko wa");
    }
    if (!result || !result.audio_url) {
      const response = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice: voiceSelectEl.value }),
      });
      result = await response.json();
      if (!response.ok) throw new Error(result.error || "Voice failed");
      if (result.error || result.fallback || !result.audio_url) {
        throw new Error(result.error || result.warning || "Voice unavailable");
      }
    }

    let audio = wrapper._audio;
    if (!audio) {
      audio = new Audio();
      wrapper._audio = audio;
      audio.addEventListener("timeupdate", () => {
        syncTranscriptionWords(wrapper, audio);
      });
      audio.addEventListener("ended", () => {
        button.innerHTML = '<i data-lucide="play"></i><span>Listen</span>';
        window.refreshIcons?.();
        setAllWordsActive(wrapper);
      });
      audio.addEventListener("pause", () => {
        if (!audio.ended) {
          button.innerHTML = '<i data-lucide="play"></i><span>Listen</span>';
          window.refreshIcons?.();
        }
      });
      audio.addEventListener("play", () => {
        button.innerHTML = '<i data-lucide="pause"></i><span>Playing</span>';
        window.refreshIcons?.();
      });
    }
    audio.src = result.audio_url;
    if (note) note.textContent = `Ohùn ti mura: ${result.voice}`;
    await audio.play().catch(() => {});
    scrollToBottom();
  } catch (error) {
    if (note) note.textContent = "";
    animateWordsWithoutAudio(wrapper);
  } finally {
    button.disabled = false;
    if (!wrapper._audio || wrapper._audio.paused) {
      button.innerHTML = '<i data-lucide="play"></i><span>Listen</span>';
      window.refreshIcons?.();
    }
  }
}

// Media Recorder (Speech-to-Text) functions
function formatTime(secs) {
  const m = Math.floor(secs / 60).toString().padStart(2, '0');
  const s = (secs % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

async function startRecording() {
  if (busy || isRecording) return;
  
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    
    // Choose appropriate mime type
    let options = { mimeType: 'audio/webm' };
    if (!MediaRecorder.isTypeSupported('audio/webm')) {
      options = { mimeType: 'audio/ogg' };
    }
    if (!MediaRecorder.isTypeSupported('audio/ogg')) {
      options = {}; // Fallback default
    }
    
    mediaRecorder = new MediaRecorder(stream, options);
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };
    
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      
      // Stop all tracks in the stream
      stream.getTracks().forEach(track => track.stop());
      
      // Show transcribing state
      inputEl.placeholder = "Transcribing...";
      inputEl.disabled = true;
      
      try {
        const response = await fetch("/api/stt", {
          method: "POST",
          headers: { "Content-Type": audioBlob.type },
          body: audioBlob
        });
        const sttResult = await response.json();
        if (!response.ok) throw new Error(sttResult.error || "STT failed");
        
        if (sttResult.text && sttResult.text.trim()) {
          inputEl.value = sttResult.text.trim();
          resizeInput();
          updateSendState();
          // Automatically send the message
          sendMessage(inputEl.value);
        } else {
          alert("No speech detected. Please try again.");
        }
      } catch (err) {
        console.error("STT Error:", err);
        alert("STT failed: " + err.message);
      } finally {
        inputEl.placeholder = "Send a message...";
        inputEl.disabled = false;
        inputEl.focus();
      }
    };
    
    mediaRecorder.start();
    isRecording = true;
    voiceInputButtonEl.classList.add("recording");
    if (waveformOverlayEl) waveformOverlayEl.hidden = false;
    recordingSeconds = 0;
    if (recordingTimerEl) recordingTimerEl.textContent = "00:00";
    
    recordingTimerInterval = setInterval(() => {
      recordingSeconds++;
      if (recordingTimerEl) recordingTimerEl.textContent = formatTime(recordingSeconds);
      if (recordingSeconds >= 60) {
        stopRecording(); // Limit to 60s
      }
    }, 1000);
    
  } catch (err) {
    console.error("Mic access denied or error:", err);
    alert("MediaRecorder error: Could not access microphone. Ensure microphone permissions are allowed.");
  }
}

function stopRecording() {
  if (!isRecording) return;
  
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  
  isRecording = false;
  voiceInputButtonEl.classList.remove("recording");
  if (waveformOverlayEl) waveformOverlayEl.hidden = true;
  if (recordingTimerInterval) {
    clearInterval(recordingTimerInterval);
    recordingTimerInterval = null;
  }
}

voiceInputButtonEl.addEventListener("click", () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

window.addEventListener("keydown", (event) => {
  const isCtrlM = event.ctrlKey && (event.key === "m" || event.key === "M" || event.code === "KeyM");
  const isCtrlZero = event.ctrlKey && (event.key === "0" || event.code === "Digit0" || event.code === "Numpad0");
  if (isCtrlM || isCtrlZero) {
    event.preventDefault();
    event.stopPropagation();
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }
}, true);

composerEl.addEventListener("submit", (event) => {
  event.preventDefault();
  if (isRecording) {
    stopRecording();
  }
  sendMessage(inputEl.value);
});

inputEl.addEventListener("input", () => {
  resizeInput();
  updateSendState();
});

inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    if (isRecording) {
      stopRecording();
    }
    composerEl.requestSubmit();
  }
});

voiceModeEl.addEventListener("click", () => {
  voiceMode = !voiceMode;
  voiceModeEl.setAttribute("aria-pressed", String(voiceMode));
  voiceModeEl.querySelector("span").textContent = voiceMode ? "Voice mode enabled" : "Mú ohùn ṣiṣẹ́ (Voice Mode)";
});

sidebarToggleEl.addEventListener("click", () => {
  const expanded = !sidebarEl.classList.contains("expanded");
  sidebarEl.classList.toggle("expanded", expanded);
  sidebarToggleEl.setAttribute("aria-expanded", String(expanded));
  sidebarToggleEl.setAttribute("aria-label", expanded ? "Collapse sidebar" : "Expand sidebar");
});

// New Chat button reset
document.querySelector(".sidebar-nav button").addEventListener("click", () => {
  chatHistory = [];
  messagesEl.innerHTML = "";
  chatPageEl.classList.add("empty");
  
  const empty = document.createElement("div");
  empty.className = "empty-state";
  empty.id = "empty-state";
  empty.innerHTML = `
    <h1>Báwo ni, kí ni mo lè ràn ẹ́ lọ́wọ́ lónìí?</h1>
  `;
  messagesEl.appendChild(empty);
  window.location.reload(); // Refresh to reset session state
});

resizeInput();
updateSendState();
scrollToBottom();
window.refreshIcons?.();
